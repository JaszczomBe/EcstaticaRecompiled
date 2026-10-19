#!/usr/bin/env python3
"""Probe diagnostic Joe input/action/motion after the observed courtyard release.

Uses the four experimental flags, a zero-logo-delay crash-probe shortcut and
WndProc press/release input. Actor state is only read. Exit zero means the probe
completed, not that movement, collisions or gameplay acceptance passed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--output', type=Path, default=Path('/tmp/e2-player-motion'))
parser.add_argument('--frames', type=int, default=60)
parser.add_argument('--timeout', type=int, default=90)
parser.add_argument('--turn-forward', choices=('left','right'),
                    help='Press this turn key before the selected movement key')
parser.add_argument('--move-key', choices=('up','down'), default='up',
                    help='Movement key to add during --turn-forward (default: up)')
parser.add_argument('--release-turn-first', action='store_true',
                    help='Release the turn key before pressing the movement key')
parser.add_argument('--sdl-events', action='store_true',
                    help='Send SDL keyboard events through the real backend pump')
args = parser.parse_args()
if args.frames < 1 or args.timeout < 1:
    parser.error('frames and timeout must be positive')
prefix = str(args.output.resolve())
Path(prefix).parent.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.pop('DISPLAY', None)
env.update(SDL_VIDEODRIVER='dummy', E2R_STARTUP_LOGO_DELAY_MS='0',
           E2R_ACTION_INDEX_PROBE='1', E2R_ACTOR_CYLINDERS='1',
           E2R_PROXY_MESH_BYPASS='1', E2R_DEFER_BACKGROUND_SPAWNS='1')
env['ASAN_OPTIONS'] = env.get('ASAN_OPTIONS', '') + ':detect_leaks=0'
commands = r'''
set pagination off
set confirm off
python
import gdb,json
prefix=PREFIX
frames=FRAMES
use_sdl=SDL_EVENTS
value=lambda expression:int(gdb.parse_and_eval(expression))
def require(condition,message):
    if not condition:raise gdb.GdbError(message)
ready=gdb.Breakpoint('FUN_00415d40',internal=True)
ready.condition='DAT_0047a76c == 0 && _DAT_0073cc3c == 0x67da4c && DAT_0047a470 != 0'
gdb.execute('run --inject-key-sequence-surfaces ' + json.dumps(prefix+'-startup') +
            ' space 3 250 PROCESS_SECONDS',to_string=True)
require(gdb.selected_frame().name()=='FUN_00415d40','Missing courtyard release checkpoint')
ready.delete()
actor=value('DAT_0047a470')
require(value(f'*(short*){actor}')==0,'Current actor is not Joe')
frame=gdb.Breakpoint('FUN_00415d40',internal=True)
def advance(count):
    for i in range(count):
        gdb.execute('continue',to_string=True)
        if gdb.selected_frame().name()!='FUN_00415d40':
            gdb.execute('bt 16')
            raise gdb.GdbError('Unexpected runtime stop')
def field(offset,kind='short'):
    return value(f'*({kind}*)({actor}+{offset})')
def snapshot(label):
    rep=field(0x11e,'unsigned int');action=field(0xa6,'unsigned int')
    position=[field(0x84+i*2) for i in range(3)]
    cell_address=0x684d68+((position[0]>>9)+64)*2+((position[2]>>9)+64)*256
    floor_cell=value(f'*(unsigned short*){cell_address}')
    data=dict(phase=label,actor=actor,scene=value('_DAT_0073cc3c'),
              wait=value('DAT_0047a76c'),modal=value('_DAT_00643650'),
              position=position,facing=field(0x92),
              queued_action=field(0x162),floor_cell=floor_cell,
              elapsed_ticks=value('_DAT_00637378'),motion_distance=field(0x170),
              representation=rep,representation_id=value(f'*(short*){rep}') if rep else -1,
              forward_slot=value(f'*(short*)({rep}+2+39*2)') if rep else -1,
              action=action,action_id=value(f'*(short*){action}') if action else -1,
              progress=field(0xac,'unsigned short'),duration=field(0xaa,'unsigned short'),
              previous_slot=field(0x96),input_direction=value('_DAT_00479e78'),
              actor_state=field(0x82),motion_flags=field(0x146,'unsigned char'),
              held_keys={name:value(f'*(unsigned char*)({0x4c3a90}+{scan})')
                         for name,scan in [('up',0x48),('down',0x50),('left',0x4b),('right',0x4d)]})
    packet=prefix+'-'+label
    expression='e2r_write_visibility_packet((HWND)_DAT_00ac4dac,'+json.dumps(packet)+')'
    require(value(expression)==1,'Visibility packet failed')
    return data
def key(vk,pressed):
    scan={0x26:0x48,0x28:0x50,0x25:0x4b,0x27:0x4d}[vk]
    if use_sdl:
        sdl_scan={0x26:82,0x28:81,0x25:80,0x27:79}[vk]
        gdb.execute('set $key_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
        gdb.execute(f'set $key_event->key.type={0x300 if pressed else 0x301}',to_string=True)
        gdb.execute(f'set $key_event->key.down={int(pressed)}',to_string=True)
        gdb.execute(f'set $key_event->key.key={0x40000000|sdl_scan}',to_string=True)
        gdb.execute(f'set $key_event->key.scancode={sdl_scan}',to_string=True)
        gdb.execute('set $key_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
        require(value('SDL_PushEvent($key_event)')==1,'SDL keyboard injection failed')
        gdb.execute('call (void)free($key_event)',to_string=True)
        gdb.execute('call e2r_poll_host_events("player-motion-probe")',to_string=True)
    else:
        # Arrow releases must target the same extended scan-code table as presses.
        lparam=1|(scan<<16)|(1<<24)|(0 if pressed else 0xc0000000)
        gdb.execute(f'call E2R_WndProc((HWND)_DAT_00ac4dac,{0x100 if pressed else 0x101},{vk},(LPARAM)0x{lparam:x})',to_string=True)
    require(value(f'*(unsigned char*)({0x4c3a90}+{scan})')==int(pressed),
            'WndProc did not update the requested held-key byte')
states=[]
def checkpoint(label):
    states.append(snapshot(label))
    # Retain completed phases even when a later input exposes a runtime fault.
    with open(prefix+'.json','w') as out:
        json.dump(dict(probe_complete=False,frames_per_phase=frames,states=states,
                       combined_turn=TURN_FORWARD,turn_calls=globals().get('turn_calls',[]),
                       sdl_events=use_sdl,release_turn_first=RELEASE_TURN,move_key=MOVE_KEY,
                       gameplay_acceptance=False),out,indent=2)
advance(3)
checkpoint('before')
turn_calls=[]
if TURN_FORWARD:
    class TurnGuard(gdb.Breakpoint):
        def stop(self):
            actual=value('param_1')
            turn_calls.append(dict(actor=actual,angle=value('param_2'),
                                   elapsed_ticks=value('_DAT_00637378'),motion_distance=field(0x170),
                                   caller=gdb.newest_frame().older().name()))
            return actual!=actor
    turn_guard=TurnGuard('FUN_0042b074',internal=True)
    name=TURN_FORWARD
    vk=0x25 if name=='left' else 0x27
    key(vk,True);advance(frames);checkpoint(name+'-pressed')
    if RELEASE_TURN:
        key(vk,False);advance(frames);checkpoint(name+'-released')
    move_vk=0x26 if MOVE_KEY=='up' else 0x28
    key(move_vk,True);advance(frames);checkpoint(name+'-'+MOVE_KEY+'-pressed')
    if MOVE_KEY=='up' and not RELEASE_TURN:require(len(turn_calls)>0,'Combined-input turn caller was not reached')
    key(move_vk,False)
    if not RELEASE_TURN:key(vk,False)
    advance(frames);checkpoint('released')
    turn_guard.delete()
else:
    for name,vk in [('up',0x26),('down',0x28),('left',0x25),('right',0x27)]:
        key(vk,True);advance(frames);checkpoint(name+'-pressed')
        key(vk,False);advance(frames);checkpoint(name+'-released')
report=dict(probe_complete=True,frames_per_phase=frames,states=states,
            combined_turn=TURN_FORWARD,move_key=MOVE_KEY,turn_calls=turn_calls,
            sdl_events=use_sdl,release_turn_first=RELEASE_TURN,
            position_changed=any(s['position']!=states[0]['position'] for s in states[1:]),
            facing_changed=any(s['facing']!=states[0]['facing'] for s in states[1:]),
            gameplay_acceptance=False)
with open(prefix+'.json','w') as out:json.dump(report,out,indent=2)
print('PROBE COMPLETE: position_changed='+str(report['position_changed'])+
      ' facing_changed='+str(report['facing_changed'])+'; gameplay acceptance remains open')
end
quit
'''.replace('PREFIX', json.dumps(prefix)).replace('FRAMES', str(args.frames)).replace(
    'PROCESS_SECONDS', str(args.timeout + 10)).replace('TURN_FORWARD', repr(args.turn_forward)).replace(
    'MOVE_KEY', repr(args.move_key)).replace('SDL_EVENTS',repr(args.sdl_events)).replace(
    'RELEASE_TURN',repr(args.release_turn_first))
with tempfile.TemporaryDirectory(prefix='e2-player-motion-') as tmp:
    script = Path(tmp) / 'probe.gdb'
    script.write_text(commands)
    try:
        result = subprocess.run(['gdb', '-q', '-batch', '-x', str(script),
                                 str(args.exe.resolve())], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or b''
        Path(prefix + '.log').write_bytes(output if isinstance(output, bytes) else output.encode())
        raise SystemExit(f'FAIL: probe timeout; see {prefix}.log')
    Path(prefix + '.log').write_text(result.stdout)
    if (result.returncode or 'PROBE COMPLETE:' not in result.stdout or
            'ERROR: AddressSanitizer' in result.stdout or 'SUMMARY: AddressSanitizer' in result.stdout):
        raise SystemExit(f'FAIL: unexpected runtime/debugger stop; see {prefix}.log')
    report = json.loads(Path(prefix + '.json').read_text())
    for state in report['states']:
        print(f"{state['phase']}: position={state['position']} facing={state['facing']} "
              f"rep={state['representation_id']} action={state['action_id']} "
              f"progress={state['progress']} slot={state['previous_slot']}")
    print(f"Probe complete: position_changed={report['position_changed']} "
          f"facing_changed={report['facing_changed']}; gameplay acceptance remains open")
    print(f'Evidence: {prefix}.json, {prefix}.log and per-phase visibility packets')
