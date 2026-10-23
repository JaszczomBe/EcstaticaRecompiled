#!/usr/bin/env python3
"""Check immutable bundles, active leases, PE bounds, source queries and reverse execution."""
import argparse
import csv
import fcntl
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
from e2_bundle import digest, publish, verify, execute, capture_workspace
from e2_original import OriginalImage, function
from e2_recovery import index
from e2_reverse import prepare

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--native', action='store_true', help='Also execute a bounded i386 GDB reverse-debugging pilot')
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='e2-debug-tools-test-') as tmp:
    root = Path(tmp)
    executable = root/'e2recomp'
    executable.write_bytes(b'ELF fixture with debug information')
    session = root/'logs/session_1'
    replay = session/'replay'
    replay.mkdir(parents=True)
    (session/'session.meta').write_text('{}')
    with (replay/'metadata.csv').open('w', newline='') as stream:
        csv.writer(stream).writerows([['key','value'],['schema','e2replay.csv.1'],
                                     ['executable_sha256',digest(executable)],['game_data_path','/external/game']])
    for name in ('events.csv','checkpoints.csv'):
        (replay/name).write_text('fixture\n')
    bundle = root/'bundle'
    publish(bundle, executable, session, context=False)
    assert verify(bundle)['replay'] == 'session/replay'
    reverse = prepare(bundle, root/'reverse', 'FUN_0042db74', 2)
    assert 'record full' in Path(reverse['launcher']).with_name('window.gdb').read_text()
    bad = root/'wrong-executable'
    bad.write_bytes(b'wrong')
    try:
        publish(root/'mismatched', bad, session, context=False)
    except ValueError:
        assert not (root/'mismatched').exists()
    else:
        raise AssertionError('Mismatched executable accepted')
    lock = (session/'session.active.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        publish(root/'active', executable, session, context=False)
    except BlockingIOError:
        pass
    else:
        raise AssertionError('Active capture accepted')
    lock.close()
    evidence = bundle/'session/replay/events.csv'
    evidence.chmod(0o644)
    evidence.write_text('tampered\n')
    try:
        verify(bundle)
    except ValueError:
        pass
    else:
        raise AssertionError('Tampered evidence accepted')
    pe = bytearray(512)
    pe[:2] = b'MZ'
    struct.pack_into('<I',pe,60,64)
    pe[64:68] = b'PE\0\0'
    struct.pack_into('<HH',pe,68,0x14c,2)
    struct.pack_into('<H',pe,84,32)
    struct.pack_into('<H',pe,88,0x10b)
    struct.pack_into('<I',pe,116,0x400000)
    struct.pack_into('<8sIIII',pe,120,b'.text',16,0x1000,16,256)
    struct.pack_into('<8sIIII',pe,160,b'.bss',0,0x2000,0x100000,0)
    path=root/'original.exe';path.write_bytes(pe)
    image=OriginalImage(path)
    assert image.code(0x401000,0x401010) == bytes(16)
    try:image.code(0x402000,0x402010)
    except ValueError:pass
    else:raise AssertionError('Unbacked .bss accepted as executable bytes')
    assert 'return 1' in function('int recovered(void)\n{\n return 1;\n}\n','recovered')
    recovered = next(r for r in index()['functions'] if r['name']=='FUN_0042db74')
    assert recovered['fixtures'] and recovered['generator_mentions']
    result = execute(['python3','-c','import time;time.sleep(5)'],os.environ.copy(),0.05,root/'timeout.log')
    assert result['status']=='timeout' and result['returncode'] is None
    import contextlib,io
    retained = None
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            with capture_workspace(root) as retained:
                (retained/'raw-evidence').write_text('preserve me')
                raise ValueError('simulated export failure')
        except ValueError:
            pass
    assert retained and (retained/'raw-evidence').read_text()=='preserve me'
    if args.native:
        from e2_bundle import capture
        crash_source = root/'crash.c'
        crash_source.write_text('#include <signal.h>\nint main(void){raise(SIGSEGV);return 0;}\n')
        crash_exe = root/'crash-pilot'
        subprocess.run(['clang-21','-m32','-g',str(crash_source),'-o',str(crash_exe)],check=True)
        crash_bundle = root/'crash-bundle'
        result = capture(crash_exe,crash_bundle,timeout=10,dummy=True,gdb=True)
        assert result['result']['status']=='signal' and result['result']['signal']==11,result
        assert 'main' in (crash_bundle/'debugger.log').read_text()
        verify(crash_bundle)
        source=root/'reverse.c'
        source.write_text('volatile int tracked;\n__attribute__((noinline)) void mutate(void) {\n tracked=41;\n tracked=42;\n}\nint main(void){mutate();return tracked!=42;}\n')
        native=root/'reverse-pilot'
        subprocess.run(['clang-21','-m32','-g','-O0','-fno-pie','-no-pie',str(source),'-o',str(native)],check=True)
        commands=root/'pilot.gdb'
        commands.write_text('''set pagination off
set confirm off
break mutate
run
record full
next
next
python
assert int(gdb.parse_and_eval('tracked'))==42
end
reverse-next
python
assert int(gdb.parse_and_eval('tracked'))==41
print('REVERSE WRITE VERIFIED')
end
record stop
continue
''')
        result=subprocess.run(['gdb','--nx','-q','--batch','-x',str(commands),str(native)],
                              capture_output=True,text=True,timeout=20)
        assert result.returncode==0 and 'REVERSE WRITE VERIFIED' in result.stdout,(result.stdout,result.stderr)
print('PASS: bundle identity/checksums, active lease rejection, PE ranges, recovery index, timeout classification'+
      ('; i386 GDB reversed a memory write' if args.native else ''))
