#!/usr/bin/env python3
"""Inspect/export a CSV recording, or run a bounded fresh-process replay.

Examples:
  replay-e2.py run EXE SESSION/replay --timeout 120 --stop-before 100000
  replay-e2.py export SESSION/replay /absolute/path/bug-bundle
"""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from e2_replay_storage import digest, event_rows, inventory, metadata

parser=argparse.ArgumentParser(description=__doc__)
sub=parser.add_subparsers(dest='command',required=True)
run=sub.add_parser('run');run.add_argument('exe',type=Path);run.add_argument('source',type=Path)
run.add_argument('--timeout',type=float,default=120);run.add_argument('--stop-before',type=int)
run.add_argument('--stop-checkpoint',type=int);run.add_argument('--compatible',action='store_true')
run.add_argument('--data-dir',type=Path);run.add_argument('--pause',action='store_true')
run.add_argument('--inspect',action='store_true',help='Write a separate observational timeline and bounded frames')
run.add_argument('--video-driver',choices=('dummy','x11','wayland'),help='Override the recorded SDL video driver')
export=sub.add_parser('export');export.add_argument('source',type=Path);export.add_argument('destination',type=Path)
inspect=sub.add_parser('inspect');inspect.add_argument('source',type=Path)
a=parser.parse_args()
source=a.source.resolve(strict=True)
if source.name=='events.csv':source=source.parent

@contextmanager
def protected_source():
    files=[]
    try:
        session=source.parent
        if session.name.startswith('session_') and (session/'session.meta').exists():
            for path,blocking in [(session.parent/'.retention.lock',True),(session/'session.active.lock',False)]:
                fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);files.append(fd)
                fcntl.flock(fd,fcntl.LOCK_EX|(0 if blocking else fcntl.LOCK_NB))
        yield
    finally:
        for fd in reversed(files):os.close(fd)

def copy_input(destination):
    destination.mkdir()
    files, _ = inventory(source)
    for path in files:
        shutil.copyfile(path, destination/path.name)

if a.command=='export':
    destination=a.destination.absolute()
    if destination.exists():parser.error('Export destination must not exist')
    # Publish only a complete frozen directory; never overwrite evidence.
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.e2-export-',dir=destination.parent) as temporary:
        staging=Path(temporary)/'bundle'
        with protected_source():
            copy_input(staging)
            for path in source.parent.glob('e2recomp*.log'):shutil.copyfile(path,staging/path.name)
            if (source.parent/'session.meta').is_file():shutil.copyfile(source.parent/'session.meta',staging/'session.meta')
        hashes={p.name:digest(p) for p in staging.iterdir()}
        (staging/'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(hashes.items())))
        for path in staging.iterdir():path.chmod(0o444)
        staging.rename(destination);destination.chmod(0o555)
    print(destination)
elif a.command=='inspect':
    with protected_source():
        meta=metadata(source)
        count = 0
        last = None
        for row in event_rows(source):
            count += 1
            last = row
    print(json.dumps(dict(metadata=meta, physical_rows=count,
                         last_sequence=last['seq'] if last else None,
                         completion='end-marker-present; native parser verifies integrity'
                         if last and last['kind']=='end' else 'incomplete'), indent=2))
else:
    if a.timeout<=0:parser.error('--timeout must be positive')
    # Snapshot before starting any executable, including future startup cleanup.
    with tempfile.TemporaryDirectory(prefix='e2-replay-run-') as temporary:
        frozen=Path(temporary)/'input'
        with protected_source():copy_input(frozen)
        meta=metadata(frozen);env=os.environ.copy()
        for key in list(env):
            if key.startswith('E2R_') or key in ('SDL_VIDEODRIVER','SDL_AUDIODRIVER','ASAN_OPTIONS','TZ'):env.pop(key)
        env.update({k[4:]:v for k,v in meta.items() if k.startswith('env.')})
        if a.video_driver:env['SDL_VIDEODRIVER']=a.video_driver
        env['E2R_RECORD']='off'
        if a.inspect:env['E2R_INSPECT']='1'
        if a.pause:env['E2R_REPLAY_PAUSE']='1'
        command=[str(a.exe.resolve(strict=True)),'--data-dir',str(a.data_dir.absolute() if a.data_dir else Path(temporary)/'output'),
                 '--game-data-dir',meta['game_data_path'],'--replay',str(frozen)]
        if a.compatible:command+=['--replay-compatible']
        if a.stop_before:command+=['--replay-stop-before',str(a.stop_before)]
        if a.stop_checkpoint:command+=['--replay-stop-checkpoint',str(a.stop_checkpoint)]
        command+=['--run-recon']
        try:result=subprocess.run(command,env=env,timeout=a.timeout)
        except subprocess.TimeoutExpired:raise SystemExit('TIMEOUT: replay did not complete within the host-time limit')
        if result.returncode < 0:
            print(f"NATIVE CRASH: signal {-result.returncode}; replay did not reach completion", file=__import__("sys").stderr)
            raise SystemExit(128-result.returncode)
        raise SystemExit(result.returncode)
