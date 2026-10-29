#!/usr/bin/env python3
"""Bounded fresh-game stables ladder down/up; silent and without unrelated enemies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess

from e2_probe_diagnostics import communicate

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('executable',type=Path)
parser.add_argument('--game-data',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--timeout',type=int,default=300)
parser.add_argument('--video-driver',choices=('dummy','x11','wayland'),default='dummy')
args = parser.parse_args()
if not 30 <= args.timeout <= 600:
    parser.error('--timeout must be 30..600 seconds')
executable = args.executable.resolve(strict=True)
game = args.game_data.resolve(strict=True)
output = args.output.resolve()
output.mkdir(parents=True,exist_ok=False)
runtime = output/'runtime'
(runtime/'Saved').mkdir(parents=True)
prefix = str(output/'ladder')

def hashes():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((game/'Saved').glob('*.ECS'))}

before = hashes()
env = {k:v for k,v in os.environ.items() if not k.startswith('E2R_')}
env.update(E2R_RECORD='off',E2R_AUDIO='off',E2R_STARTUP_LOGO_DELAY_MS='0',
           E2R_TEST_POPULATION='noncombat-ladder',E2R_DEFER_BACKGROUND_SPAWNS='0',
           E2R_ACTION_INDEX_PROBE='1',E2R_PLAYER_MESH='1',E2R_NPC_MESH='1',
           E2R_MENU_DIAG='1',
           E2R_PROXY_MESH_BYPASS='1',E2R_ACTOR_CYLINDERS='1',
           SDL_VIDEODRIVER=args.video_driver,ASAN_OPTIONS='detect_leaks=0')
if args.video_driver=='dummy':
    env.pop('DISPLAY',None)
commands = '''set pagination off
set confirm off
python
import sys,gdb
sys.path.insert(0,SCRIPTS)
from e2_probe_diagnostics import install
install(PREFIX)
class RejectSavedState(gdb.Breakpoint):
    def stop(self):
        print('FAIL: fresh ladder regression attempted Save/Load',flush=True)
        return True
save_guard=RejectSavedState('FUN_00453920',internal=True)
load_guard=RejectSavedState('FUN_004544a4',internal=True)
from e2_ladder_steps import run
run(PREFIX,RUNTIME,GAME,WATCH)
end
quit
'''
values = dict(SCRIPTS=str(ROOT/'scripts'),PREFIX=prefix,RUNTIME=str(runtime),
              GAME=str(game),WATCH=args.video_driver!='dummy')
commands = re.sub(r'\b('+'|'.join(values)+r')\b',lambda m:repr(values[m[0]]),commands)
command_file = output/'probe.gdb'
command_file.write_text(commands)
report = dict(probe_complete=False,seed='fresh game',recording='off',audio_output='off',
              population_profile='noncombat-ladder',
              executable=dict(path=str(executable),sha256=hashlib.sha256(executable.read_bytes()).hexdigest()))
process = subprocess.Popen(['gdb','-nx','-batch','-x',str(command_file),str(executable)],
                           env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
try:
    try:
        text,stalled = communicate(process,prefix,args.timeout,stall_timeout=45)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL)
        text,_ = process.communicate()
        (output/'gdb.log').write_text(text)
        raise RuntimeError('Ladder regression exceeded its bounded timeout')
    (output/'gdb.log').write_text(text)
    result_file = Path(prefix+'.json')
    if (process.returncode or stalled or not result_file.is_file() or
            'ERROR: AddressSanitizer' in text or 'runtime error:' in text):
        print(text[-7000:])
        raise RuntimeError('Ladder regression did not complete; see gdb.log')
    result = json.loads(result_file.read_text())
    if not result.get('probe_complete') or result.get('native_exit_code')!=0:
        raise RuntimeError('Ladder regression lacks a clean native exit')
    if not all(result.get('details',{}).get(leg,{}).get('passed') for leg in ('descent','ascent')):
        raise RuntimeError('Both ladder directions must pass')
    report.update(probe_complete=True,result=result)
finally:
    if process.poll() is None:
        os.killpg(process.pid,signal.SIGKILL);process.wait()
    report['installed_saves_unchanged'] = hashes()==before
    report['no_save_files_created'] = not list((runtime/'Saved').iterdir())
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['installed_saves_unchanged'] or not report['no_save_files_created']:
        raise RuntimeError('Ladder regression violated its save ownership boundary')
print('PASS: silent fresh-game ladder descent/ascent; controlled population; source saves unchanged')
