#!/usr/bin/env python3
"""Bounded input-only sound, Settings, HUD/F3, inventory and Quit verification."""
import argparse
import hashlib
import os,sys,re,subprocess,json
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('executable',type=Path)
parser.add_argument('--game-data',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--music',action='store_true',help='Verify original music data, independent toggle, MIDI activity and isolated PCM')
parser.add_argument('--audio-driver',default='dummy',help='SDL driver, or default for system output')
args=parser.parse_args()
root=Path(__file__).resolve().parent.parent
d=args.output.resolve();d.mkdir(parents=True,exist_ok=False)
runtime=d/'runtime';runtime.mkdir()
binary=args.executable.resolve(strict=True)
body='''set pagination off
set confirm off
python
import sys,gdb,json
sys.path.insert(0,SCRIPTS)
from e2_probe_diagnostics import install
install(PREFIX)
from e2_tower_steps import TowerJourney
from e2_inventory_steps import check
from e2_hud_steps import HudChecks
j=TowerJourney(PREFIX,RUNTIME,GAME)
j.frame=gdb.Breakpoint('FUN_00415d40',internal=True);j.frame.condition=j.HORSE
gdb.execute('run --game-data-dir '+json.dumps(GAME)+' --data-dir '+json.dumps(RUNTIME)+' --record off --run-recon',to_string=True)
j.frame.condition=None;j.initial=j.state('initial')
# Observe naturally delivered sound requests without changing game state.
sounds=[]
class Sounds(gdb.Breakpoint):
 def stop(self):
  resource=j.value('param_1');identity=j.value('*(short*)'+str(resource))
  count=j.value('*(int*)('+str(resource)+'+12)')
  index=Path(GAME)/'OFFSETS';archive=Path(GAME)/'Files/ECSTATIC'
  with index.open('rb') as f:
   f.seek((2500+5000+2000+500+identity)*4);offset=int.from_bytes(f.read(4),'big')
  with archive.open('rb') as f:
   f.seek(offset+89+32);expected=bytes((v+128)&255 for v in f.read(count))
  buffer=j.value('*(unsigned*)('+str(resource)+'+56)')
  pointer=j.value('((SoundBuffer*)'+str(buffer)+')->pcm')
  actual=bytes(gdb.selected_inferior().read_memory(pointer,count))
  j.require(actual==expected,'Naturally requested PCM differs from original archive conversion')
  sounds.append(dict(id=identity,bytes=count,volume=j.value('param_2')))
  return False
from pathlib import Path
watch=Sounds('FUN_00458c24',internal=True)
j.reach_pedestal();j.reach_gameplay()
check(j,'sound-inventory');HudChecks(j).switches('sound-hud')
j.move();j.interact()
j.settings();j.click(0x6439f8);j.pump()
j.require(j.value('DAT_0047a4a0')==0,'Settings did not disable sound')
j.close_settings();muted=len(sounds);j.move();j.step(30)
j.require(len(sounds)==muted,'Sound requests passed the original off gate')
j.settings();j.click(0x6439f8);j.pump()
j.require(j.value('DAT_0047a4a0')==1,'Settings did not enable sound')
j.close_settings();j.move();j.step(30)
j.require(len(sounds)>muted,'Natural sounds did not resume after Settings enabled sound')
if MUSIC:
 j.require(j.value('DAT_00479dbc')==1,'General MIDI port not selected')
 j.require(j.value('DAT_0047ab0c')==j.value('*(int*)0x47ab0c'),'Current track/save ownership differs')
 resource=j.value('registered_id');length=j.value('registered_bytes')
 j.require(resource>0 and length>0,'No natural music resource loaded')
 with (Path(GAME)/'OFFSETS').open('rb') as f:
  f.seek((2500+5000+2000+500+700+resource-1)*4);offset=int.from_bytes(f.read(4),'big')
 with (Path(GAME)/'Files/ECSTATIC').open('rb') as f:
  f.seek(offset);expected=f.read(int.from_bytes(f.read(4),'big'))
 actual=bytes(gdb.selected_inferior().read_memory(j.value('registered'),length))
 j.require(actual==expected,'Natural music bytes differ from the original GM resource')
 original_sfx=j.value('DAT_0047a4a0')
 j.settings();j.click(0x643998);j.pump()
 j.require(j.value('DAT_0047a49c')==0,'Music did not disable')
 j.require(sum(j.value('sequence.tracks[%d].active'%i) for i in range(16))==0,'Original StopTune did not deactivate tracks')
 messages=j.value('E2R_music_messages')
 gdb.execute('call (void)SDL_Delay(300)',to_string=True)
 j.require(j.value('E2R_music_messages')==messages,'Music events continued after stop')
 j.click(0x643998);j.pump()
 j.require(j.value('DAT_0047a49c')==1 and j.value('sequence.tune')==1,'Music did not restart')
 j.require(j.value('DAT_0047a4a0')==original_sfx,'Music toggle changed sound setting')
 j.close_settings()
 before_nonzero=j.value('E2R_music_nonzero_frames')
 gdb.execute('call (void)SDL_Delay(1000)',to_string=True)
 j.require(j.value('E2R_music_nonzero_frames')>before_nonzero,'Restarted gameplay cue did not produce new music PCM')
 j.details['music']=dict(resource=resource,bytes=length,frames=j.value('E2R_music_frames'),nonzero_frames=j.value('E2R_music_nonzero_frames'),messages=j.value('E2R_music_messages'))
 j.require(j.details['music']['nonzero_frames']>0,'No isolated nonzero music output')
else:j.check('MusicToggle')
j.details['audio_requests']=sounds
watch.delete()
j.open();j.close()
gdb.execute('call (void)SDL_Delay(300)',to_string=True)
j.details['audio_frames']=j.value('E2R_audio_frames')
j.details['audio_nonzero_frames']=j.value('E2R_audio_nonzero_frames')
j.require(j.details['audio_nonzero_frames']>0,'No nonzero device output')
print('AUDIO COUNTERS',j.details['audio_frames'],j.details['audio_nonzero_frames'],flush=True)
j.stage='Gameplay';j.quit();j.complete=True;j.save()
end
quit
'''
vals=dict(SCRIPTS=str(root/'scripts'),PREFIX=str(d/'probe'),RUNTIME=str(runtime),GAME=str(args.game_data.resolve(strict=True)),MUSIC=args.music)
body=re.sub(r'\b('+'|'.join(vals)+r')\b',lambda m:repr(vals[m[0]]),body)
(d/'probe.gdb').write_text(body)
env={k:v for k,v in os.environ.items() if not k.startswith('E2R_')}
env.update(E2R_AUDIO_TRACE='1',E2R_AUDIO_TAP=str(d/'mix.s16'),E2R_RECORD='off',E2R_STARTUP_LOGO_DELAY_MS='0',E2R_DEFER_BACKGROUND_SPAWNS='0',E2R_ACTION_INDEX_PROBE='1',E2R_PROXY_MESH_BYPASS='1',E2R_PLAYER_MESH='1',E2R_NPC_MESH='1',E2R_ACTOR_CYLINDERS='1',SDL_VIDEODRIVER='dummy',ASAN_OPTIONS='detect_leaks=0')
if args.music:env.update(E2R_MUSIC_TRACE=str(d/'music.trace'),E2R_MUSIC_TAP=str(d/'music.s16'))
if args.audio_driver!='default':env['SDL_AUDIODRIVER']=args.audio_driver
else:env.pop('SDL_AUDIODRIVER',None)
r=subprocess.run(['gdb','-nx','-batch','-x',str(d/'probe.gdb'),str(binary)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
(d/'probe.log').write_text(r.stdout);print(r.returncode,r.stdout[-2400:],flush=True)
(d/'binary.json').write_text(json.dumps(dict(path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest()),indent=2))
if args.music and r.returncode==0:
 pcm=(d/'music.s16').read_bytes()
 assert pcm and any(pcm),'No isolated music PCM'
 trace=(d/'music.trace').read_text()
 assert 'play resource=' in trace and 'result=0' in trace,'No successful natural music playback'
 assert 'ERROR: AddressSanitizer' not in r.stdout
sys.exit(r.returncode)
