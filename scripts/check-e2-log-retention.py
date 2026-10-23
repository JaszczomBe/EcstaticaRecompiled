#!/usr/bin/env python3
"""Check newest-five retention, older-byte budgets and investigation/active leases."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
args = parser.parse_args()
exe = args.exe.resolve()


def eventually(predicate, seconds=6):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.05)
    raise AssertionError('Timed out waiting for session maintenance')


def seed(root, year, number, size=0):
    session = root/f'logs/session_{year}0101_000000_{number:03}'
    session.mkdir(parents=True)
    (session/'session.meta').write_text('{}')
    with (session/'evidence').open('wb') as output:
        output.truncate(size)  # Sparse files exercise accounting without filling disk.
    return session


def run(root, **overrides):
    env = os.environ | dict(E2R_DATA_DIR=str(root), SDL_VIDEODRIVER='dummy',
        E2R_RECORD='off', E2R_INSPECT='0', E2R_LOG_LEVEL='Warning',
        E2R_LOG_MAX_SESSIONS='4294967295', E2R_LOG_MAX_TOTAL_MB='1',
        E2R_LOG_CLEANUP_INTERVAL_SECONDS='1') | overrides
    result = subprocess.run([str(exe), '--host-backend-present-probe'], cwd=exe.parent,
        env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    return result


with tempfile.TemporaryDirectory(prefix='e2-retention-') as directory:
    root = Path(directory)
    floor = root/'floor'
    newest = [seed(floor,2099,i,300*1024*1024) for i in range(4)]
    run(floor,E2R_LOG_MAX_SESSIONS='1')
    assert all(p.exists() for p in newest)
    assert len(list((floor/'logs').glob('session_*'))) == 5
    # 1.2 GiB of newest data must not reduce the separate 1 MiB older budget.
    budget = root/'budget'
    newest = [seed(budget,2099,i,300*1024*1024) for i in range(5)]
    older = [seed(budget,2000,i,400*1024) for i in range(3)]
    run(budget)
    assert not older[0].exists() and all(p.exists() for p in older[1:]+newest)
    kept = seed(budget,1998,0,2*1024*1024)
    (kept/'investigation.keep').write_text('pending/crashed investigation')
    active = seed(budget,1999,0,2*1024*1024)
    legacy = seed(budget,1997,0)
    (legacy/'session.meta').write_text(json.dumps({'pid':os.getpid()}))
    with (active/'session.active.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX)
        result = run(budget)
        assert all(p.exists() for p in [kept,active,legacy])
        assert 'budget exceeded' in result.stderr
    run(budget)
    assert not active.exists() and kept.exists() and legacy.exists()
    (kept/'investigation.keep').unlink()
    run(budget)
    assert not kept.exists() and all(p.exists() for p in newest)
    # Exercise the periodic worker, not only startup cleanup.
    periodic = root/'periodic'
    for i in range(5): seed(periodic,2099,i)
    env=os.environ | dict(E2R_DATA_DIR=str(periodic),SDL_VIDEODRIVER='dummy',
        E2R_RECORD='off',E2R_INSPECT='0',E2R_LOG_MAX_TOTAL_MB='1',
        E2R_LOG_CLEANUP_INTERVAL_SECONDS='1')
    with (root/'console').open('w') as console:
        process=subprocess.Popen([str(exe),'--dump-frame',str(root/'frame.pgm'),'10'],
            cwd=exe.parent,env=env,stdout=console,stderr=console)
        try:
            eventually(lambda:list((periodic/'logs').glob('session_202*')))
            time.sleep(.3)  # Let startup cleanup finish before testing the worker.
            candidate=seed(periodic,1990,0,2*1024*1024)
            eventually(lambda:not candidate.exists())
            assert process.poll() is None
        finally:
            process.kill();process.wait(timeout=5)
    print('PASS: newest-five floor despite count/size limits; separate older-byte budget; oldest-first purge; retained investigations, active/legacy leases and periodic cleanup')
