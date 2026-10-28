#!/usr/bin/env python3
"""Exercise the native CSV parser, checksums, recovery and divergence contracts."""
import argparse
import csv
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('exe',type=Path);a=p.parse_args();exe=a.exe.resolve()
env=os.environ|{'ASAN_OPTIONS':'detect_leaks=0'}
with tempfile.TemporaryDirectory(prefix='e2-replay-contracts-') as temporary:
    root=Path(temporary);fixture=root/'original'
    def run(mode,path,code):
        r=subprocess.run([str(exe),mode,str(path)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15)
        assert r.returncode==code,(mode,path,r.returncode,r.stdout)
        assert 'ERROR: AddressSanitizer' not in r.stdout,r.stdout
        return r.stdout
    print(run('record',fixture,0).strip());print(run('play',fixture,0).strip())
    crash=root/'clock-crash'
    assert 'reached crash-triggering changed clock' in run('record-clock-crash',crash,42)
    assert (crash/'session/replay/recording.incomplete').exists()
    assert 'reached crash-triggering changed clock' in run('play-clock-crash',crash,42)
    print('PASS: changed clock retained before abrupt exit without a following pump')
    # The same logical schema remains readable from legacy single-file captures.
    legacy = fixture/'session/replay'
    with (legacy/'metadata.csv').open(newline='') as stream:
        rows = [row for row in csv.reader(stream) if row[0] != 'storage']
    with (legacy/'metadata.csv').open('w', newline='') as stream:
        csv.writer(stream, lineterminator='\n').writerows(rows)
    (legacy/'chunks.csv').unlink()
    print(run('play', fixture, 0).strip())
    meta=dict(list(csv.reader((fixture/'session/replay/metadata.csv').open()))[1:])
    assert meta['executable_sha256']==hashlib.sha256(exe.read_bytes()).hexdigest()
    data=(fixture/'session/replay/events.csv').read_bytes()
    lines=data.splitlines(keepends=True)
    assert list(csv.reader([lines[-1].decode()]))[0][-1]==hashlib.sha256(b''.join(lines[:-1])).hexdigest()
    assert 'expected=0 actual=actor[0].x=99' in run('diverge',fixture,74)
    def case(name):
        dest=root/name;shutil.copytree(fixture,dest);return dest,dest/'session/replay'
    def edit(path,transform):
        with path.open(newline='') as f:rows=list(csv.reader(f))
        transform(rows)
        with path.open('w',newline='') as f:csv.writer(f,lineterminator='\n').writerows(rows)
    dest,replay=case('malformed');(replay/'events.csv').write_text('invalid\n');run('play',dest,73)
    dest,replay=case('integer');edit(replay/'events.csv',lambda r:r[1].__setitem__(1,'0'));run('play',dest,73)
    dest,replay=case('unknown');edit(replay/'events.csv',lambda r:r[1].__setitem__(2,'unknown'));run('play',dest,73)
    dest,replay=case('gap');edit(replay/'events.csv',lambda r:r[1].__setitem__(0,'2'));run('play',dest,73)
    dest,replay=case('checksum');edit(replay/'events.csv',lambda r:r[1].__setitem__(4,'125'));run('play',dest,73)
    dest,replay=case('state');edit(replay/'checkpoints.csv',lambda r:r[1].__setitem__(4,'5'));run('play',dest,73)
    dest,replay=case('missing-identity');edit(replay/'metadata.csv',lambda r:r.__setitem__(slice(None),[x for x in r if x[0]!='executable_sha256']));run('play',dest,73)
    dest,replay=case('incompatible');edit(replay/'metadata.csv',lambda r:[x.__setitem__(1,'bad') for x in r if x[0]=='executable_sha256']);run('play',dest,73)
    dest,replay=case('truncated');data=(replay/'events.csv').read_bytes();(replay/'events.csv').write_bytes(data[:data.rfind(b'\n',0,-1)+1]+b'2000017,1,"unterminated');run('play',dest,75)
    dest,replay=case('unpublished');(replay/'recording.incomplete').write_text('incomplete');run('play',dest,75)
    dest,replay=case('corrupt-middle');data=(replay/'events.csv').read_bytes();(replay/'events.csv').write_bytes(data.replace(b',clock,',b',"clock"x,',1));run('play',dest,73)
    dest,replay=case('tail-after-end')
    with (replay/'events.csv').open('ab') as f:f.write(b'9999999,1,"unfinished')
    run('play',dest,73)
    print('PASS: ordered clocks/repeats/services, first field divergence, malformed input, identity, both checksums, truncated-tail recovery')
