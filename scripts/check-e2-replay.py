#!/usr/bin/env python3
"""Record real SDL events under GDB, then replay in independent processes.

Debugger only schedules host events and observes update entry; never forces game
state. The capture ends through the normal process-exit service, for a bounded
route rather than a full playthrough. Requires native i386 and ptrace access.
"""
import argparse
import csv
import json
import os
import re
from pathlib import Path
import subprocess
import time
from e2_replay_storage import event_rows

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path)
p.add_argument('--inventory',action='store_true',help='Include real Enter/Escape status transitions after player release')
p.add_argument('--released-player',action='store_true',help='Wait for release before movement; broader gameplay fidelity gate')
p.add_argument('--background-spawns',action='store_true',help='Also exercise populated gameplay; divergence is a failing fidelity check')
p.add_argument('--inspect',action='store_true',help='Also verify observational capture and replay with inspection disabled')
p.add_argument('--chunk-bytes', type=int, help='Exercise physical chunk rotation during the route')
p.add_argument('--object-mesh-ids', type=int, nargs='+', default=[])
p.add_argument('--object-mesh-reps', type=int, nargs='+', default=[])
p.add_argument('--character-meshes', action='store_true', help='Record/replay with original player and NPC rendering')
p.add_argument('--music',action='store_true',help='Verify original music resource/start/stop sequence and isolated PCM across strict replay')
p.add_argument('--audio', action='store_true', help='Verify original sound requests, captured PCM and device-disabled replay')
p.add_argument('--output',type=Path,default=Path('/tmp/e2-replay-route'))
a=p.parse_args()
if a.inventory:a.released_player=True
exe=a.exe.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
if any(v <= 0 or v >= 5000 for v in a.object_mesh_ids):p.error('actor IDs must be 1..4999')
if any(v <= 0 or v >= 500 for v in a.object_mesh_reps):p.error('representation IDs must be 1..499')
env=os.environ.copy()
for key in list(env):
    if key.startswith('E2R_'):env.pop(key)
env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',E2R_STARTUP_LOGO_DELAY_MS='0',E2R_ACTOR_CYLINDERS='1',E2R_ACTION_INDEX_PROBE='1',E2R_PROXY_MESH_BYPASS='1',E2R_DEFER_BACKGROUND_SPAWNS='0' if a.background_spawns else '1',ASAN_OPTIONS='detect_leaks=0')
env['E2R_AUDIO']='on' if a.audio or a.music else 'off'
if a.object_mesh_ids:env['E2R_OBJECT_MESH_IDS']=','.join(map(str,a.object_mesh_ids))
if a.object_mesh_reps:env['E2R_OBJECT_MESH_REPS']=','.join(map(str,a.object_mesh_reps))
if a.character_meshes:env.update(E2R_PLAYER_MESH='1',E2R_NPC_MESH='1')
if a.audio:env['E2R_AUDIO_TRACE']='1'
if a.inspect:env['E2R_INSPECT']='1'
if a.chunk_bytes:
    env['E2R_REPLAY_CHUNK_BYTES'] = str(a.chunk_bytes)
body=r'''
import gdb
value=lambda s:int(gdb.parse_and_eval(s))
def event(scan,down,key=None):
    gdb.execute('set $event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
    for member,v in [('type',0x300 if down else 0x301),('down',int(down)),('key',key if key is not None else 0x40000000|scan),('scancode',scan)]:
        gdb.execute(f'set $event->key.{member}={v}',to_string=True)
    gdb.execute('set $event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
    assert value('SDL_PushEvent($event)')==1
    gdb.execute('call (void)free($event)',to_string=True)
intro=gdb.Breakpoint('FUN_00415d40',internal=True)
intro.condition='DAT_0047a470 != 0 && _DAT_0073cc3c != 0 && _DAT_0073cc3c != 0x67da4c && *(int*)((int)DAT_0047a470+0xa6) != 0'
gdb.execute('run',to_string=True)
assert gdb.selected_frame().name()=='FUN_00415d40'
event(44,True,32)
intro.condition='DAT_00636850 != 0'
gdb.execute('continue',to_string=True)
intro.condition=None
gdb.execute('continue',to_string=True)
event(44,False,32)
intro.condition=READY_CONDITION
gdb.execute('continue',to_string=True)
assert gdb.selected_frame().name()=='FUN_00415d40'
intro.condition=None
def advance(n):
    intro.ignore_count=n-1
    gdb.execute('continue',to_string=True)
    assert gdb.selected_frame().name()=='FUN_00415d40'
event(82,True);advance(16)
event(80,True);advance(12)
event(82,True);advance(8) # repeated keydown is intentionally preserved
event(80,False);advance(8)
event(82,False);advance(12)
# Enter and leave the original Escape menu through delivered SDL input.
intro.enabled=False
pump=gdb.Breakpoint('e2r_poll_host_events',internal=True)
def pump_advance(n):
    pump.ignore_count=n-1
    gdb.execute('continue',to_string=True)
    assert gdb.selected_frame().name()=='e2r_poll_host_events'
event(41,True,27);pump_advance(128)
event(41,False,27);pump_advance(64)
print('ROUTE CAPTURE COMPLETE')
try:gdb.execute('call PostQuitMessage(0)',to_string=True)
except gdb.error:
    assert gdb.selected_inferior().pid==0
'''
# A private Python namespace avoids symbols overwritten by shared-library helpers.
if not a.released_player:
    begin=body.index('event(82,True);advance(16)')
    end=body.index("print('ROUTE CAPTURE COMPLETE')",begin)
    body=body[:begin]+"""intro.enabled=False
pump=gdb.Breakpoint('e2r_poll_host_events',internal=True)
def pump_advance(n):
    pump.ignore_count=n-1
    gdb.execute('continue',to_string=True)
    assert gdb.selected_frame().name()=='e2r_poll_host_events'
event(41,True,27);pump_advance(128)
event(41,False,27);pump_advance(64)
event(82,True);pump_advance(64)
event(80,True);pump_advance(64)
event(82,True);pump_advance(64)
event(80,False);pump_advance(64)
event(82,False);pump_advance(64)
"""+body[end:]
if a.inventory:
    transition="""# Enter and leave the status page using delivered input only.
intro.enabled=False
inventory_pump=gdb.Breakpoint('FUN_0041ba7c',internal=True)
event(40,True,13)
for attempt in range(16):
    gdb.execute('continue',to_string=True)
    if value('E2R_InventoryPageActive()'):break
else:raise AssertionError('Enter status page did not open within bounded pumps')
event(40,False,13)
inventory_pump.ignore_count=3
gdb.execute('continue',to_string=True)
event(41,True,27);event(41,False,27)
inventory_pump.delete();intro.enabled=True
advance(4)
assert value('E2R_InventoryPageActive()')==0
"""
    body=body.replace('# Enter and leave the original Escape menu through delivered SDL input.',
                      transition+'\n# Enter and leave the original Escape menu through delivered SDL input.')
body=body.replace('READY_CONDITION',repr(('DAT_0047a76c == 0 && ' if a.released_player else '')+'_DAT_0073cc3c == 0x67da4c && DAT_0047a470 != 0'))
(out/'record.py').write_text(body)
(out/'record.gdb').write_text('set pagination off\nset confirm off\npython\nexec(compile(open('+repr(str(out/'record.py'))+').read(),"replay-route","exec"),{"__name__":"__replay_route__"})\nend\n')
sound_requests=[]
music_requests=[]
def run(name,command,timeout=100,expected=0):
    if a.music:env.update(E2R_MUSIC_TRACE=str(out/(name+'.music.trace')),E2R_MUSIC_TAP=str(out/(name+'.music.s16')))
    if a.audio:env['E2R_AUDIO_TAP']=str(out/(name+'.s16'))
    start=time.monotonic()
    result=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout,cwd=exe.parent)
    (out/(name+'.log')).write_text(result.stdout)
    assert result.returncode==expected,(name,result.returncode,result.stdout[-2500:])
    assert 'ERROR: AddressSanitizer' not in result.stdout,(name,result.stdout[-2500:])
    if a.audio:
        requests=re.findall(r'sound play: id=(\d+) bytes=(\d+) volume=(\d+)',result.stdout)
        assert requests,(name,'No original sound events reached playback')
        if name=='record':sound_requests.extend(requests)
        else:assert requests==sound_requests,(name,'Sound identity/length/volume sequence changed')
        if env.get('E2R_AUDIO')!='off':
            pcm=(out/(name+'.s16')).read_bytes()
            assert any(pcm),(name,'No nonzero backend PCM')
    if a.music:
        requests=(out/(name+'.music.trace')).read_text().splitlines()
        assert any(x.startswith('play ') and 'result=0' in x for x in requests),(name,'No natural music playback')
        if name=='record':music_requests.extend(requests)
        else:assert requests==music_requests,(name,'Music resource/start/stop sequence changed')
        if env.get('E2R_AUDIO')!='off':assert any((out/(name+'.music.s16')).read_bytes()),(name,'No isolated music PCM')
    return dict(seconds=time.monotonic()-start,exit=result.returncode)
run('record',['gdb','--nx','-q','--batch','-x',str(out/'record.gdb'),'--args',str(exe),'--record','auto','--data-dir',str(out/'capture'),'--run-recon'],timeout=150)
source=max((out/'capture/logs').glob('session_*/replay'),key=lambda p:p.parent.name)
rows=list(event_rows(source))
assert rows[-1]['kind']=='end'
if a.inventory:
    assert any(x['kind']=='input' and x['message_or_result']=='256' and x['wparam']=='13' for x in rows)
    assert any(x['kind']=='input' and x['message_or_result']=='256' and x['wparam']=='27' for x in rows)
inputs=[x for x in rows if x['kind']=='input']
assert sum(x['message_or_result']=='256' and x['wparam']=='38' for x in inputs)>=2
command=[str(exe),'--data-dir',str(out/'playback'),'--replay',str(source),'--run-recon']
results=[run('play-'+str(i),command) for i in range(3)]
if a.inspect:
    from e2_inspection import Inspection
    capture=Inspection(source.parent)
    assert capture.complete and any(e['kind']=='frame_written' for e in capture.events)
    env.pop('E2R_INSPECT')
    results.append(run('play-inspection-off',command))
    env['E2R_INSPECT']='1'
# Pause after a real checkpoint; wall time must not influence game-visible clocks.
(out/'pause.gdb').write_text('set pagination off\nset confirm off\nbreak E2R_ReplayPumpBegin\nignore 1 100\nrun\npython\nimport time\ntime.sleep(2)\nend\ndisable 1\ncontinue\n')
results.append(run('pause',['gdb','--nx','-q','--batch','-x',str(out/'pause.gdb'),'--args',*command]))
if a.audio or a.music:
    env['E2R_AUDIO']='off'
    results.append(run('play-audio-off',command))
    env['E2R_AUDIO']='on'
report=dict(source=str(source),object_mesh_ids=a.object_mesh_ids,object_mesh_reps=a.object_mesh_reps,
            character_meshes=a.character_meshes,sound_requests=sound_requests,music_requests=music_requests,replays=results,inputs=len(inputs),checkpoints=sum(x['kind']=='checkpoint' for x in rows),clock_calls=sum(int(x['repeat']) for x in rows if x['kind']=='clock'),clock_rows=sum(x['kind']=='clock' for x in rows),bytes=sum(x.stat().st_size for x in source.iterdir()))
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
