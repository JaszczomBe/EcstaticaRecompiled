#!/usr/bin/env python3
"""Bounded real-menu save/load in private storage, followed by fresh-process restoration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

from e2_probe_diagnostics import communicate

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('executable',type=Path)
parser.add_argument('--game-data',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--timeout',type=int,default=240)
parser.add_argument('--equipment',action='store_true')
parser.add_argument('--object-mesh-ids',type=int,nargs='+',default=[])
parser.add_argument('--object-mesh-reps',type=int,nargs='+',default=[])
parser.add_argument('--hud',action='store_true',help='Verify original/debug selection and repainting during both persistence processes')
parser.add_argument('--failure-case',choices=('empty','save-open','unsupported','truncated','missing'))
parser.add_argument('--population-profile',choices=('live','noncombat-opening'),default='live')
parser.add_argument('--video-driver',choices=('dummy','x11','wayland'),default='dummy')
args=parser.parse_args()
if any(identity<=0 or identity>=5000 for identity in args.object_mesh_ids):
    parser.error('object mesh IDs must be original actor IDs from 1 to 4999')
if any(identity<=0 or identity>=500 for identity in args.object_mesh_reps):
    parser.error('object mesh representation IDs must be from 1 to 499')
if not 30<=args.timeout<=600:parser.error('--timeout must be 30..600 seconds per bounded process')
executable=args.executable.resolve(strict=True);game=args.game_data.resolve(strict=True);original_game=game
output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
runtime=output/'runtime';slots=runtime/'Saved';slots.mkdir(parents=True)
originals={path.name:dict(size=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
           for path in sorted((game/'Saved').glob('*.ECS'))}
free=[i for i in range(9) if (game/'Saved'/f'{i:04d}.ECS').is_file() and
      (game/'Saved'/f'{i:04d}.ECS').read_bytes()==b'\r\n\r\n']
if not free:raise SystemExit('No confirmed empty original menu slot; no files copied or overwritten')
slot=free[0]
for name in originals:shutil.copy2(game/'Saved'/name,slots/name)
if args.failure_case in ('unsupported','truncated','missing'):
    version=3 if args.failure_case=='unsupported' else 4
    (slots/f'{slot:04d}.ECS').write_bytes(b'E2R INVALID'.ljust(26,b'\0')+version.to_bytes(2,'little')+bytes(4800)+b'\0')
if args.failure_case=='save-open':
    (slots/f'{slot:04d}.ECS').unlink();(slots/f'{slot:04d}.ECS').mkdir()
if args.failure_case=='missing':
    # Remove the read fallback only in a private installation facade. Assets
    # remain read-only symlink references; no original entry is changed.
    game=output/'game';game.mkdir()
    for entry in original_game.iterdir():
        if entry.name!='Saved':(game/entry.name).symlink_to(entry,target_is_directory=entry.is_dir())
    shutil.copytree(original_game/'Saved',game/'Saved')
    (game/'Saved'/f'{slot:04d}.ECS').unlink()
(output/'save-preservation-before.json').write_text(json.dumps(originals,indent=2)+'\n')
expected=output/'expected-state.json'
env=os.environ.copy()
for key in list(env):
    if key.startswith('E2R_'):env.pop(key)
env.update(E2R_RECORD='off',E2R_DATA_DIR=str(runtime),E2R_STARTUP_LOGO_DELAY_MS='0',
           E2R_ACTION_INDEX_PROBE='1',E2R_ACTOR_CYLINDERS='1',E2R_PROXY_MESH_BYPASS='1',
           E2R_PLAYER_MESH='1',E2R_NPC_MESH='1',E2R_DEFER_BACKGROUND_SPAWNS='0',
           E2R_POPULATION_PROBE='1',SDL_VIDEODRIVER=args.video_driver,ASAN_OPTIONS='detect_leaks=0')
if args.video_driver=='dummy':env.pop('DISPLAY',None)
if args.object_mesh_ids:env['E2R_OBJECT_MESH_IDS']=','.join(map(str,args.object_mesh_ids))
if args.object_mesh_reps:env['E2R_OBJECT_MESH_REPS']=','.join(map(str,args.object_mesh_reps))
if args.population_profile!='live':env['E2R_TEST_POPULATION']=args.population_profile
report=dict(probe_complete=False,slot=slot,initially_empty_slots=free,recording='off',
            object_mesh_ids=args.object_mesh_ids,object_mesh_reps=args.object_mesh_reps,
            failure_case=args.failure_case,
            population_profile=args.population_profile,
            executable=dict(path=str(executable),sha256=hashlib.sha256(executable.read_bytes()).hexdigest()),
            runtime=str(runtime),processes=[])
try:
    for mode in (('failure',) if args.failure_case else ('same','fresh')):
        prefix=str(output/mode)
        code='''set pagination off
set confirm off
python
import sys,gdb
sys.path.insert(0,SCRIPTS)
from e2_probe_diagnostics import install
install(PREFIX)
# Stop before any unexpected write can enter the serializer.
class SaveOwnership(gdb.Breakpoint):
    def stop(self):
        actual=int(gdb.parse_and_eval('param_1'))
        if MODE not in ('same','failure') or actual!=SLOT:
            print('FAIL: attempted write outside the test-owned empty slot: '+str(actual),flush=True)
            return True
        return False
ownership=SaveOwnership('FUN_00453920',internal=True)
from e2_save_load_steps import run,run_failure
if FAILURE:run_failure(PREFIX,RUNTIME,GAME,SLOT,FAILURE)
else:run(PREFIX,RUNTIME,GAME,SLOT,MODE,EQUIPMENT,EXPECTED,HUD)
end
quit
'''
        values=dict(SCRIPTS=str(ROOT/'scripts'),PREFIX=prefix,RUNTIME=str(runtime),GAME=str(game),
                    SLOT=slot,MODE=mode,EQUIPMENT=args.equipment,EXPECTED=str(expected),FAILURE=args.failure_case,HUD=args.hud)
        # Substitute tokens as Python literals, without shell interpolation.
        import re
        code=re.sub(r'\b('+ '|'.join(values) +r')\b',lambda match:repr(values[match.group()]),code)
        commands=output/(mode+'.gdb');commands.write_text(code)
        process=subprocess.Popen(['gdb','-nx','-batch','-x',str(commands),str(executable)],
                                 stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env,start_new_session=True)
        try:
            text,stalled=communicate(process,prefix,args.timeout,stall_timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);text,_=process.communicate()
            (output/(mode+'.log')).write_text(text)
            raise RuntimeError(f'{mode} persistence probe exceeded its bounded timeout')
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
        (output/(mode+'.log')).write_text(text)
        result_path=Path(prefix+'.json')
        if process.returncode or stalled or not result_path.is_file():
            print(text[-8000:])
            raise RuntimeError(f'{mode} persistence probe did not complete (GDB exit {process.returncode})')
        result=json.loads(result_path.read_text());report['processes'].append(result)
        if not result.get('probe_complete') or (result.get('native_exit_code')!=0 and
                not (args.failure_case in ('truncated','missing') and result.get('stopped_before_unqualified_fatal_cleanup'))):
            raise RuntimeError(f'{mode} persistence report has no clean native completion')
    if not args.failure_case:
        saved=(slots/f'{slot:04d}.ECS').read_bytes()
        if saved[:26].split(b'\0')[0]!=b'E2RTEST' or saved[26:28]!=b'\x04\x00' or saved[-2:]!=b'4\x12':
            raise RuntimeError('Actual saved bytes lack the original label/version/trailer')
        report['save']=dict(bytes=len(saved),sha256=hashlib.sha256(saved).hexdigest())
    report['probe_complete']=True
finally:
    unchanged={name:hashlib.sha256((original_game/'Saved'/name).read_bytes()).hexdigest()==metadata['sha256']
               for name,metadata in originals.items()}
    private={name:hashlib.sha256((slots/name).read_bytes()).hexdigest()==metadata['sha256']
             for name,metadata in originals.items() if name!=f'{slot:04d}.ECS'}
    report.update(installed_saves_unchanged=unchanged,unowned_private_slots_unchanged=private)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not all(unchanged.values()) or not all(private.values()):
        raise RuntimeError('Save preservation verification failed')
print(f'PASS: {args.failure_case or "real menu save/load cycles and fresh-process restore"}; private slot {slot}; all installed saves unchanged')
