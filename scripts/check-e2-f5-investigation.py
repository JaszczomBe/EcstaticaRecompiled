#!/usr/bin/env python3
"""Verify F5 executable pinning, stop evidence, active leases and report finalization."""
import fcntl
import argparse
import json
import os
from pathlib import Path
import tempfile
import subprocess
import shutil
import e2_f5
from e2_bundle import digest,publish,verify

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--native',action='store_true',help='Also verify GDB signal-stop observation on an i386 fixture')
args=parser.parse_args()

with tempfile.TemporaryDirectory(prefix='e2-f5-contract-') as temporary:
    root=Path(temporary)
    e2_f5.INDEX=root/'pending'
    session=root/'logs/session_fixture'
    inspection=session/'inspection'
    inspection.mkdir(parents=True)
    (session/'session.meta').write_text('{}')
    (inspection/'timeline.csv').write_text('event_id,replay_sequence,replay_checkpoint,update_id,present_id,snapshot_id,kind,a,b\n1,0,0,0,0,1,start,0,0\n2,0,0,1,0,2,end,0,0\n')
    (inspection/'state.csv').write_text('snapshot_id,scope,entity_id,field,value,present\n1,world,0,camera,175,1\n')
    selected=root/'selected-program'
    selected.write_bytes(b'a rebuilt path does not identify the running process')
    record=e2_f5.begin(session,selected,os.getpid())
    assert (session/'investigation.keep').is_file()
    pinned=session/'investigation/e2recomp'
    assert digest(pinned)==digest(Path('/proc/self/exe')) and digest(pinned)!=digest(selected)
    e2_f5.append(record,'signal','fixture stack and registers',signal='SIGSEGV',E2R_replay_sequence=123)
    e2_f5.ended(record,dict(status='exited',returncode=0))
    with (session/'session.active.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX)
        try:e2_f5.finalize(record)
        except BlockingIOError:pass
        else:raise AssertionError('Active F5 session finalized')
    result=e2_f5.finalize(record)
    assert result['state']=='finalized' and result['inspection_complete']
    assert result['retention_protected'] and not result['replay_complete']
    assert json.loads(record.read_text())['last_signal']=='SIGSEGV'
    assert 'fixture stack' in record.with_suffix('.signal.log').read_text()
    assert 'SIGSEGV' in (session/'investigation/debugger.log').read_text()
    report=Path(result['report']);before=digest(report)
    e2_f5.finalize(record);assert digest(report)==before
    bundle=root/'bundle'
    publish(bundle,pinned,session,context=False)
    assert (bundle/'debugger.log').is_file() and (bundle/'session/investigation/report.html').is_file()
    verify(bundle)
    clean=root/'logs/session_clean'
    shutil.copytree(inspection,clean/'inspection')
    (clean/'session.meta').write_text('{}')
    (clean/'replay').mkdir();(clean/'replay/events.csv').write_text('fixture completed replay')
    (clean/'replay/recording.incomplete').write_text('file limit reached')
    clean_record=e2_f5.begin(clean,selected,os.getpid())
    e2_f5.ended(clean_record,dict(status='exited',returncode=0))
    clean_state=e2_f5.finalize(clean_record)
    assert not clean_state['retention_protected'] and not clean_state['replay_complete']
    assert not (clean/'investigation.keep').exists()
    shutil.rmtree(clean)
    assert e2_f5.finalize(clean_record)['state']=='expired'
    if args.native:
        native_session=root/'logs/session_native'
        native_inspection=native_session/'inspection';native_inspection.mkdir(parents=True)
        (native_session/'session.meta').write_text('{}')
        for name in ('timeline.csv','state.csv'):
            (native_inspection/name).write_bytes((inspection/name).read_bytes())
        source=root/'native.c'
        source.write_text('''#include <signal.h>
__attribute__((noinline)) void E2R_SampleInspection(void){__asm__ volatile("");}
volatile unsigned long long E2R_replay_sequence=0,E2R_replay_last_checkpoint=0;
__attribute__((noinline)) void FUN_0043cbf0(void){__asm__ volatile("");}
__attribute__((noinline)) void E2R_InspectStart(const char *session){E2R_SampleInspection();__asm__ volatile(""::"r"(session));}
int main(int argc,char **argv){E2R_InspectStart(argv[1]);FUN_0043cbf0();raise(SIGSEGV);return 0;}
''')
        executable=root/'native'
        subprocess.run(['clang-21','-m32','-g','-O0',str(source),'-o',str(executable)],check=True)
        script=Path(__file__).with_name('e2-vscode-investigation.py').resolve()
        result=subprocess.run(['gdb','--nx','-q','--batch','-ex','source '+str(script),'-ex','run',
                               '-ex','python assert gdb.selected_inferior().pid > 0','-ex','quit',
                               '--args',str(executable),str(native_session)],capture_output=True,text=True,timeout=20)
        log=native_session/'investigation/debugger.log'
        assert result.returncode==0 and log.exists(),(result.stdout,result.stderr)
        assert 'SIGSEGV' in log.read_text() and 'main' in log.read_text()
        assert 'requester' in log.read_text() and 'FUN_0043cbf0' in log.read_text()
        assert (native_session/'investigation.keep').is_file()
        assert digest(native_session/'investigation/e2recomp')==digest(executable)
print('PASS: kernel image pinning, stop evidence, active-session rejection, idempotent report finalization, F5 bundle export'
      + ('; native i386 GDB signal evidence and preserved stop' if args.native else ''))
