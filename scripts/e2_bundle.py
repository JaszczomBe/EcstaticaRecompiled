"""Freeze replay evidence and native debugging output without copying game assets."""
from __future__ import annotations
from contextlib import contextmanager
import csv
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
MAX_FILE = 256 * 1024 * 1024
MAX_BUNDLE = 768 * 1024 * 1024


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


@contextmanager
def source_lock(session):
    locks = []
    try:
        if session.name.startswith('session_') and (session/'session.meta').is_file():
            for path, blocking in [(session.parent/'.retention.lock', True), (session/'session.active.lock', False)]:
                fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
                locks.append(fd)
                fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield
    finally:
        for fd in reversed(locks):
            os.close(fd)


def session_path(source):
    source = source.resolve(strict=True)
    return source.parent if source.name in ('replay', 'inspection') else source


def copy_file(source, destination, budget):
    if source.is_symlink() or not source.is_file():
        raise ValueError(f'Expected regular evidence file: {source}')
    size = source.stat().st_size
    if size > MAX_FILE or size > MAX_BUNDLE-budget[0]:
        raise ValueError(f'Evidence exceeds bundle limit: {source}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    budget[0] += size


def freeze_session(source, destination, budget):
    with source_lock(source):
        paths = [p for p in source.iterdir() if p.name == 'session.meta' or p.name.startswith('e2recomp') and p.suffix == '.log']
        for directory in ('replay', 'inspection', 'investigation'):
            parent = source/directory
            if parent.is_symlink():
                raise ValueError('Symlinked evidence directory')
            if parent.is_dir():
                if directory == 'investigation':
                    for path in parent.rglob('*'):
                        if path.is_symlink():
                            raise ValueError('Symlinked investigation artifact')
                        if path.is_file():
                            paths.append(path)
                else:
                    paths.extend(parent.iterdir())
        for path in paths:
            copy_file(path, destination/path.relative_to(source), budget)


def source_context(destination, budget):
    """Working-tree evidence is context, never a claim of build provenance."""
    destination.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=15)
    head = git('rev-parse', 'HEAD').decode().strip()
    (destination/'revision.txt').write_text(head+'\n')
    patch = git('diff', '--binary', 'HEAD')
    if len(patch) > 16 * 1024 * 1024:
        raise ValueError('Working-tree patch exceeds context limit')
    (destination/'working-tree.patch').write_bytes(patch)
    paths = set(git('diff', '--name-only', '-z', 'HEAD').split(b'\0'))
    paths.update(git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0'))
    for name in sorted(paths):
        if not name:
            continue
        relative = Path(os.fsdecode(name))
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid source context path')
        path = ROOT/relative
        if path.is_file() and not path.is_symlink():
            copy_file(path, destination/'changed-files'/relative, budget)
    return head


def publish(destination, executable, session=None, result=None, diagnostic=None, context=True, build=None):
    destination = destination.absolute()
    if destination.exists():
        raise ValueError('Bundle destination must be new')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.e2-bundle-', dir=destination.parent) as temp:
        stage = Path(temp)/'bundle'
        stage.mkdir()
        budget = [0]
        executable = executable.resolve(strict=True)
        executable_hash = digest(executable)
        copy_file(executable, stage/'executable/e2recomp', budget)
        (stage/'executable/e2recomp').chmod(0o555)
        manifest = dict(schema='e2debug.bundle.1', executable_sha256=executable_hash,
                        result=result or dict(status='exported-evidence'),
                        source_context='working tree at export time; verify against build identity',
                        original_assets='external; not included', replay=None)
        if session:
            session = session_path(session)
            freeze_session(session, stage/'session', budget)
            if diagnostic is None and (session/'investigation/debugger.log').is_file():
                diagnostic = session/'investigation/debugger.log'
            meta_path = stage/'session/replay/metadata.csv'
            if meta_path.is_file():
                with meta_path.open(newline='') as stream:
                    reader = csv.reader(stream, strict=True)
                    if next(reader, None) != ['key', 'value']:
                        raise ValueError('Invalid replay metadata')
                    metadata = dict(reader)
                if metadata.get('executable_sha256') != executable_hash:
                    raise ValueError('Executable does not match the recording; preserve the matching binary')
                manifest['replay'] = 'session/replay'
                manifest['build_revision'] = metadata.get('revision')
        if diagnostic:
            copy_file(diagnostic, stage/'debugger.log', budget)
        if context:
            manifest['context_revision'] = source_context(stage/'context', budget)
        build = build or executable.parent
        for name in ('CMakeCache.txt', 'compile_commands.json'):
            path = build/name
            if path.is_file():
                copy_file(path, stage/'context/build'/name, budget)
        copy_file(ROOT/'scripts/replay-e2.py', stage/'tools/replay-e2.py', budget)
        (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        sums = []
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                sums.append(f'{digest(path)}  {path.relative_to(stage).as_posix()}\n')
        (stage/'SHA256SUMS').write_text(''.join(sums))
        for path in stage.rglob('*'):
            if path.is_file() and path != stage/'executable/e2recomp':
                path.chmod(0o444)
        for path in stage.rglob('*'):
            if path.is_dir():
                path.chmod(0o555)
        stage.rename(destination)
        destination.chmod(0o555)
    return manifest


def verify(source):
    source = source.resolve(strict=True)
    expected = set()
    for line in (source/'SHA256SUMS').read_text().splitlines():
        value, name = line.split('  ', 1)
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or name in expected or not name or name == '.':
            raise ValueError('Invalid bundle checksum path')
        expected.add(name)
        path = source/relative
        if any(part.is_symlink() for part in [path, *path.parents] if part != source.parent):
            raise ValueError('Symlink in evidence path')
        if digest(path) != value:
            raise ValueError(f'Bundle checksum mismatch: {name}')
    actual = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    if actual != expected | {'SHA256SUMS'}:
        raise ValueError('Bundle file inventory mismatch')
    manifest = json.loads((source/'manifest.json').read_text())
    if (not isinstance(manifest,dict) or manifest.get('schema') != 'e2debug.bundle.1'
            or digest(source/'executable/e2recomp') != manifest.get('executable_sha256')
            or manifest.get('replay') not in (None,'session/replay')):
        raise ValueError('Bundle identity mismatch')
    return manifest


def execute(command, env, timeout, output):
    """Bound the whole debugger/inferior process group, retaining output on timeout."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Timeout must be positive')
    start = time.monotonic()
    with output.open('wb') as stream:
        process = subprocess.Popen(command, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
            status = 'signal' if code < 0 else 'exited'
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            code, status = None, 'timeout'
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
    return dict(status=status, returncode=code, seconds=time.monotonic()-start)


@contextmanager
def capture_workspace(parent):
    parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='.e2-capture-', dir=parent))
    try:
        yield root
    except BaseException:
        print(f'Raw capture retained after export/interruption failure: {root}', file=sys.stderr)
        raise
    else:
        shutil.rmtree(root)


def capture(executable, destination, *, timeout=90, game_data=None, dummy=False, gdb=False):
    executable = executable.resolve(strict=True)
    if destination.exists():
        raise ValueError('Bundle destination must be new')
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('E2R_'):
            env.pop(key)
    env.update(E2R_RECORD='auto', E2R_INSPECT='1', E2R_ACTOR_CYLINDERS='1',
               E2R_ACTION_INDEX_PROBE='1', E2R_PROXY_MESH_BYPASS='1', E2R_DEFER_BACKGROUND_SPAWNS='0')
    if dummy:
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    with capture_workspace(destination.absolute().parent) as root:
        pinned = root/'e2recomp'
        shutil.copy2(executable, pinned)
        pinned.chmod(0o555)
        command = [str(pinned), '--data-dir', str(root/'runtime')]
        if game_data:
            command += ['--game-data-dir', str(game_data.resolve(strict=True))]
        command += ['--run-recon']
        if gdb:
            debugger = shutil.which('gdb')
            if not debugger:
                raise ValueError('GDB is unavailable')
            script = root/'capture.gdb'
            script.write_text('''set pagination off
set confirm off
set print elements 64
run
python
import gdb
pid=gdb.selected_inferior().pid
if pid:
    gdb.execute('thread apply all bt full')
    gdb.execute('info registers')
    for name in ('E2R_replay_sequence','E2R_replay_last_checkpoint'):
        try: print(name+'='+str(gdb.parse_and_eval(name)))
        except gdb.error: pass
    try: sig=int(gdb.parse_and_eval('$_siginfo.si_signo'))
    except (gdb.error,ValueError): sig=11
    print('E2R_DEBUG_SIGNAL='+str(sig))
    gdb.execute('quit '+str(128+sig))
else:
    try: code=int(gdb.parse_and_eval('$_exitcode'))
    except (gdb.error,ValueError): code=1
    gdb.execute('quit '+str(code))
end
''')
            command = [debugger, '--nx', '-q', '--batch', '-x', str(script), '--args', *command]
        log = root/'debugger.log'
        result = execute(command, env, timeout, log)
        import re
        stopped = re.search(r'^E2R_DEBUG_SIGNAL=(\d+)$', log.read_text(errors='replace'), re.M)
        if stopped and result['status'] != 'timeout':
            result.update(status='signal', signal=int(stopped[1]))
        sessions = sorted((root/'runtime/logs').glob('session_*'))
        manifest = publish(destination, pinned, sessions[-1] if sessions else None,
                           result, log, build=executable.parent)
    return manifest
