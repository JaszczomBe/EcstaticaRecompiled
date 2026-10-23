"""Prepare bounded GDB recording windows or pilot rr on an immutable replay bundle."""
import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from e2_bundle import execute, verify


def capabilities():
    return dict(gdb=shutil.which('gdb'), rr=shutil.which('rr'),
                rr_status='available; CPU/kernel/ptrace compatibility requires a pilot' if shutil.which('rr')
                else 'unavailable: rr is not installed',
                gdb_status='record full can be enabled at a selected function; instruction/device support is limited')


def replay_command(bundle, output):
    manifest = verify(bundle)
    if not manifest['replay']:
        raise ValueError('Bundle contains no replay')
    source = bundle/manifest['replay']
    with (source/'metadata.csv').open(newline='') as stream:
        reader = csv.reader(stream)
        next(reader)
        metadata = dict(reader)
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('E2R_') or key in ('SDL_VIDEODRIVER', 'SDL_AUDIODRIVER', 'ASAN_OPTIONS', 'TZ'):
            env.pop(key)
    env.update({k[4:]:v for k,v in metadata.items() if k.startswith('env.')})
    env['E2R_RECORD'] = 'off'
    command = [str(bundle/'executable/e2recomp'), '--data-dir', str(output/'runtime'),
               '--game-data-dir', metadata['game_data_path'], '--replay', str(source), '--run-recon']
    return command, env


def prepare(bundle: Path, output: Path, function: str, ignore=0):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', function) or ignore < 0:
        raise ValueError('A function identifier and nonnegative hit count are required')
    bundle, output = bundle.resolve(strict=True), output.absolute()
    if output.exists():
        raise ValueError('Reverse-debug output must be new')
    command, env = replay_command(bundle, output)
    output.mkdir(parents=True)
    script = output/'window.gdb'
    script.write_text(f'''set pagination off
set confirm off
set breakpoint pending off
break {function}
ignore 1 {ignore}
run
record full
echo Recording begins at the selected function. Use continue/next, then reverse-next or reverse-continue.\\n
''')
    invocation = ['gdb', '--nx', '-q', '-x', str(script), '--args', *command]
    # Save an executable launcher with a JSON payload, avoiding shell/GDB quoting
    # of recorded environment values. It restores the recorded startup identity.
    launcher = output/'launch.py'
    payload = json.dumps(dict(command=invocation, environment={k:v for k,v in env.items()
                         if k.startswith('E2R_') or k in ('SDL_VIDEODRIVER','SDL_AUDIODRIVER','ASAN_OPTIONS','TZ')}))
    launcher.write_text('import json,os\npayload=json.loads('+repr(payload)+')\n'
                       'for key in list(os.environ):\n'
                       '    if key.startswith("E2R_") or key in ("SDL_VIDEODRIVER","SDL_AUDIODRIVER","ASAN_OPTIONS","TZ"):os.environ.pop(key)\n'
                       'os.environ.update(payload["environment"])\n'
                       'os.execvp(payload["command"][0],payload["command"])\n')
    return dict(launcher=str(launcher), function=function, ignored_hits=ignore, capabilities=capabilities())


def pilot(bundle: Path, output: Path, timeout=120):
    rr = shutil.which('rr')
    if not rr:
        raise ValueError('rr is not installed; use reverse --backend gdb --function FUNCTION to prepare a recording window')
    bundle, output = bundle.resolve(strict=True), output.absolute()
    if output.exists():
        raise ValueError('rr pilot output must be new')
    command, env = replay_command(bundle, output)
    output.mkdir(parents=True)
    env['_RR_TRACE_DIR'] = str(output/'traces')
    result = execute([rr, 'record', *command], env, timeout, output/'rr.log')
    result['trace_root'] = str(output/'traces')
    result['note'] = 'Inspect rr.log for recorder errors; only a replayed trace establishes rr compatibility'
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    return result
