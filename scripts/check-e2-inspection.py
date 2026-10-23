#!/usr/bin/env python3
"""Exercise the production observer and its reader, including abrupt exit recovery."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
from e2_inspection import Inspection, differences, write_report
from e2_scenarios import evaluate

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--asan', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
source = r'''
#include "EcstaticaInspect.h"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <cassert>
extern "C" { volatile uint64_t E2R_replay_sequence = 10, E2R_replay_last_checkpoint = 2; }
int x=1; bool active=true;
void sample() {
  E2R_InspectField("world",0,"camera",175);
  if(active) E2R_InspectField("actor",0,"x",x);
}
int main(int argc,char **argv) {
  E2R_InspectStart(argv[1],sample);
  E2R_InspectUpdate(0);x=3;E2R_InspectUpdate(1);
  E2R_InspectObserve("input_before",256,38);
  const char *prefix=E2R_InspectPresent();
  if(argc>2 && std::string(argv[2])=="no-frames") {
    E2R_InspectFrameResult(-1);assert(!E2R_InspectPresent());
    x=5;E2R_InspectObserve("bookmark",0,0);E2R_InspectFinish();return 0;
  }
  if(prefix) { std::ofstream image(std::string(prefix)+".ppm",std::ios::binary); image<<"P6\n1 1\n255\n";image.write("\0\0\0",3);image.close();E2R_InspectFrameResult(1); }
  if(prefix) for(int i=0;i<3;i++) {
    auto frame=E2R_InspectPresent();assert(frame);
    std::ofstream image(std::string(frame)+".ppm",std::ios::binary);image<<"P6\n1 1\n255\n";image.write("\0\0\0",3);image.close();E2R_InspectFrameResult(1);
  }
  if(argc>2) std::_Exit(42);
  active=false;E2R_InspectObserve("bookmark",0,0);
  E2R_InspectFinish();
}
'''
with tempfile.TemporaryDirectory(prefix='e2-inspection-test-') as tmp:
    temporary = Path(tmp)
    src, exe = temporary / 'contract.cpp', temporary / 'contract'
    src.write_text(source)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run(['clang++-21', '-std=c++20', '-DE2R_ENABLE_RUNTIME_OPTIONS=1', '-Wall', '-Wextra',
                    *flags, '-I'+str(root/'src/inspect/include'), '-I'+str(root/'src/replay/include'),
                    str(src), str(root/'src/inspect/src/Inspect.cpp'), '-o', str(exe)], check=True)
    env = os.environ | {'E2R_INSPECT': '1', 'E2R_INSPECT_INTERVAL': '1',
                        'E2R_INSPECT_MAX_FRAMES': '1', 'E2R_INSPECT_FRAME_INTERVAL':'1', 'ASAN_OPTIONS': 'detect_leaks=0'}
    for mode in ('clean', 'crash', 'disabled', 'no-frames'):
        dest = temporary / mode
        dest.mkdir()
        result = subprocess.run([str(exe), str(dest)] + ([mode] if mode in ('crash','no-frames') else []),
                                env=env | ({'E2R_INSPECT': '0'} if mode == 'disabled' else {}), timeout=20)
        assert result.returncode == (42 if mode == 'crash' else 0)
        if mode == 'disabled':
            assert not (dest/'inspection').exists()
            continue
        capture = Inspection(dest)
        if mode == 'no-frames':
            assert capture.complete and capture.state(scope='actor')[0]['value']==5
            assert any(e['kind']=='frame_unavailable' for e in capture.events)
            continue
        assert len(list((dest/'inspection').glob('*.ppm'))) == 1
        assert capture.complete == (mode == 'clean')
        assert capture.state(1, 'actor', 0)[0]['value'] == 1
        assert capture.state(3, 'actor', 0)[0]['value'] == 3
        assert differences(capture.state(1), capture.state(3))[0]['after'] == 3
        assert all(e['replay_sequence'] == 10 and e['replay_checkpoint'] == 2 for e in capture.events)
        if mode == 'clean':
            assert capture.state(scope='actor') == []
            checks = evaluate(capture, dict(schema='e2debug.scenario.1', assertions=[
                dict(scope='actor',entity_id=0,field='x',when='changes'),
                dict(scope='world',entity_id=0,field='camera',when='always',value=175),
                dict(scope='actor',entity_id=0,field='x',when='final',value=3)]))
            assert [c['passed'] for c in checks] == [True, True, False]
        else:
            with (dest/'inspection/timeline.csv').open('ab') as f:
                f.write(b'999,unfinished')
            assert not Inspection(dest).complete
        write_report(capture, dest/'report.html')
        assert 'data:image/png;base64,' in (dest/'report.html').read_text()
    malformed = temporary/'clean/inspection/state.csv'
    with malformed.open('a') as f:
        f.write('bad,row\n')
    try:
        Inspection(temporary/'clean')
    except ValueError:
        pass
    else:
        raise AssertionError('Malformed complete state row accepted')
print('PASS: native snapshots/deletion, update/frame correlation, frame bound, disabled capture, crash prefix, malformed rows, HTML report')
