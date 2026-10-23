#!/usr/bin/env python3
"""Check process-kill recovery, pre-cleanup source freezing and capture failure."""
import argparse
import csv
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
import time
p=argparse.ArgumentParser(description=__doc__);p.add_argument('exe',type=Path);a=p.parse_args();exe=a.exe.resolve()
env=os.environ.copy()
for key in list(env):
    if key.startswith('E2R_'):env.pop(key)
env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',E2R_STARTUP_LOGO_DELAY_MS='0',E2R_ACTOR_CYLINDERS='1',E2R_ACTION_INDEX_PROBE='1',E2R_PROXY_MESH_BYPASS='1',E2R_DEFER_BACKGROUND_SPAWNS='1',ASAN_OPTIONS='detect_leaks=0')
with tempfile.TemporaryDirectory(prefix='e2-replay-lifecycle-') as directory:
    root=Path(directory)
    with (root/'capture.log').open('w') as log:
        process=subprocess.Popen([str(exe),'--data-dir',str(root/'data'),'--run-recon'],env=env,stdout=log,stderr=log)
        time.sleep(2);assert process.poll() is None,'capture did not remain alive';process.kill();process.wait()
    source=next((root/'data/logs').glob('*/replay'))
    assert (source/'recording.incomplete').exists()
    with (source/'events.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    assert not rows or rows[-1]['kind']!='end'
    # Appending an unfinished CSV row emulates an interrupted write at the tail.
    with (source/'events.csv').open('ab') as f:f.write(b'99999999,1,"unfinished')
    limited=env|{'E2R_LOG_MAX_SESSIONS':'1'}
    # Retention always keeps the newest five; make this source older than them.
    for index in range(5):
        newer=root/f'data/logs/session_20990101_000000_{index:03}'
        newer.mkdir();(newer/'session.meta').write_text('{}')
    result=subprocess.run([str(exe),'--data-dir',str(root/'data'),'--replay',str(source),'--run-recon'],env=limited,capture_output=True,text=True,timeout=20)
    assert result.returncode==75,(result.returncode,result.stderr[-1500:])
    assert 'INCOMPLETE' in result.stderr and 'last_matching_checkpoint=' in result.stderr
    assert not source.exists(),'old source was not collected; retention test did not exercise freezing'
    assert not list((root/'data/logs').glob('*/replay')),'nested replay recording'
    # A host probe remains opt-out by default, regardless of severity filtering.
    result=subprocess.run([str(exe),'--data-dir',str(root/'probe'),'--host-backend-key-probe'],env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode==0 and not list((root/'probe/logs').glob('*/replay'))
    def disk_limit():
        signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE,(2000,2000))
    process=subprocess.Popen([str(exe),'--data-dir',str(root/'failure'),'--run-recon'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,preexec_fn=disk_limit)
    try:
        process.communicate(timeout=2)
        raise AssertionError('capture failure terminated gameplay')
    except subprocess.TimeoutExpired:
        process.kill();output=process.communicate()[0].decode(errors='replace')
    assert 'RECORDING INCOMPLETE' in output,output[-2000:]
    failure=next((root/'failure/logs').glob('*/replay'))
    assert (failure/'recording.incomplete').exists()
    assert b',end,' not in (failure/'events.csv').read_bytes()
    print('PASS: abrupt kill and partial tail, immutable input before retention, no nested/probe capture, disk-write failure continues gameplay with incomplete status')
