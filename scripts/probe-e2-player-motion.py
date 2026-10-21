#!/usr/bin/env python3
"""Probe diagnostic Joe input/action/motion after the observed courtyard release.

Uses the four experimental flags, configurable logo delays and SDL/WndProc
press/release input. Actor state is only read. Exit zero means the probe
completed, not that movement, collisions or gameplay acceptance passed.
Optional object inspection selects an original camera and runs its visibility
sweep, which can load/activate objects; it never assigns actor coordinates.
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
parser.add_argument('--intro-skip-action', type=int, default=0,
                    help='Send SDL Space at the Nth distinct horseback action using the real --run-recon path')
parser.add_argument('--natural-intro', action='store_true',
                    help='Let the horseback intro finish without the diagnostic Space shortcut')
parser.add_argument('--startup-logo-delay-ms', type=int, default=0,
                    help='Wait per startup logo; use 5000 to match the default F5 launch')
parser.add_argument('--frames', type=int, default=60)
parser.add_argument('--release-delay', type=int, default=3,
                    help='Frames to wait after the script first releases Joe before sending input')
parser.add_argument('--timeout', type=int, default=90)
parser.add_argument('--turn-forward', choices=('left','right'),
                    help='Press this turn key before the selected movement key')
parser.add_argument('--move-key', choices=('up','down'), default='up',
                    help='Movement key to add during --turn-forward (default: up)')
parser.add_argument('--release-turn-first', action='store_true',
                    help='Release the turn key before pressing the movement key')
parser.add_argument('--simultaneous-turn', action='store_true',
                    help='Press movement and turn together, recording heading and motion each frame')
parser.add_argument('--burst-frames', action='store_true',
                    help='Run each input phase without per-frame Python/turn breakpoints')
parser.add_argument('--sdl-events', action='store_true',
                    help='Send SDL keyboard events through the real backend pump')
parser.add_argument('--video-driver', choices=('dummy','x11','wayland'), default='dummy',
                    help='SDL video driver; x11/wayland use the current desktop display')
parser.add_argument('--hold-through-release', action='store_true',
                    help='With --pedestal-guards and --simultaneous-turn, hold both keys while Joe is still restrained')
parser.add_argument('--tap-modifiers', nargs='+', choices=('shift','ctrl','alt'), default=[],
                    help='Tap and release these modifiers through SDL before the input route')
parser.add_argument('--camera-round-trip', action='store_true',
                    help='Try SDL Up, then Down if needed, to cross into camera 166 and reverse to the pedestal')
parser.add_argument('--trace-queries', type=int, default=0,
                    help='Record this many motion queries with real floor/descriptor inputs for original-code replay')
parser.add_argument('--observe-seconds', type=int, default=0,
                    help='Observe released input for this many seconds after completing the route')
parser.add_argument('--pedestal-guards', action='store_true',
                    help='Require the two original pedestal guard tracks before release and during the route')
parser.add_argument('--population-frames', type=int, default=0,
                    help='After observed release, enable experimental actor lookup/spawning and census this many frames before the input route')
parser.add_argument('--population-only', action='store_true',
                    help='End after the post-release population census; do not run the arrow route')
parser.add_argument('--background-spawns', action='store_true',
                    help='Run the original population scheduler from startup without the population-probe flag')
parser.add_argument('--require-background-population', action='store_true',
                    help='Require the script population gate open and a live terrain-generated actor in the census')
parser.add_argument('--inspect-object-scene', type=int, default=-1,
                    help='After release, select the preloaded script scene\'s camera for an activation/presentation check, then restore the original view; this is not traversal')
parser.add_argument('--inspect-approach-cameras', type=int, nargs='+', default=[],
                    help='Select these original views before --inspect-object-scene to exercise neighbouring object initialization; no actor coordinates are assigned')
args = parser.parse_args()
if args.intro_skip_action < 0 or (args.intro_skip_action and args.natural_intro):
    parser.error('intro skip action must be nonnegative and separate from --natural-intro')
if args.frames < 1 or args.timeout < 1 or args.release_delay < 0:
    parser.error('frames/timeout must be positive and release-delay nonnegative')
if args.startup_logo_delay_ms < 0:
    parser.error('startup logo delay must be nonnegative')
if args.population_only and (not args.population_frames or args.camera_round_trip or args.turn_forward):
    parser.error('--population-only requires --population-frames and a separate input route')
if args.require_background_population and (not args.background_spawns or not args.population_frames):
    parser.error('--require-background-population requires --background-spawns and --population-frames')
if args.camera_round_trip and args.turn_forward:
    parser.error('--camera-round-trip and --turn-forward are separate routes')
if args.simultaneous_turn and (not args.turn_forward or args.release_turn_first):
    parser.error('--simultaneous-turn requires --turn-forward with the turn held')
if args.hold_through_release and (not args.pedestal_guards or not args.simultaneous_turn):
    parser.error('--hold-through-release requires --pedestal-guards and --simultaneous-turn')
if args.trace_queries < 0 or args.observe_seconds < 0 or args.population_frames < 0:
    parser.error('query count and observation seconds must be nonnegative')
if args.inspect_object_scene < -1 or args.inspect_object_scene >= 2500:
    parser.error('object scene must be an original script resource ID below 2500')
if args.inspect_approach_cameras and (args.inspect_object_scene < 0 or
        any(v < 0 or v >= 1200 for v in args.inspect_approach_cameras)):
    parser.error('approach cameras require --inspect-object-scene and camera IDs below 1200')
prefix = str(args.output.resolve())
Path(prefix).parent.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
if args.video_driver == 'dummy':env.pop('DISPLAY', None)
env.update(SDL_VIDEODRIVER=args.video_driver, E2R_STARTUP_LOGO_DELAY_MS=str(args.startup_logo_delay_ms),
           E2R_ACTION_INDEX_PROBE='1', E2R_ACTOR_CYLINDERS='1',
           E2R_PROXY_MESH_BYPASS='1', E2R_DEFER_BACKGROUND_SPAWNS='1')
# Preserve the existing intro resources; recovery is enabled at the checkpoint.
env['E2R_POPULATION_PROBE'] = '0'
if args.background_spawns:env['E2R_DEFER_BACKGROUND_SPAWNS'] = '0'
env['ASAN_OPTIONS'] = env.get('ASAN_OPTIONS', '') + ':detect_leaks=0'
commands = r'''
set pagination off
set confirm off
python
import gdb,json,time,re
prefix=PREFIX
frames=FRAMES
use_sdl=SDL_EVENTS
camera_route=CAMERA_ROUTE
query_limit=QUERY_LIMIT
observe_seconds=OBSERVE_SECONDS
population_frames=POPULATION_COUNT
check_guards=CHECK_GUARDS
natural_intro=NATURAL_INTRO
intro_skip_action=INTRO_SKIP_ACTION
population_only=POPULATION_ONLY
population_samples=[]
value=lambda expression:int(gdb.parse_and_eval(expression))
def require(condition,message):
    if not condition:raise gdb.GdbError(message)
ready=gdb.Breakpoint('FUN_00415d40',internal=True)
ready.condition='DAT_0047a76c == 0 && _DAT_0073cc3c == 0x67da4c && DAT_0047a470 != 0'
if check_guards:
    ready.condition='DAT_0047a76c != 0 && _DAT_0073cc3c == 0x67da4c && DAT_0047a470 != 0 && *(int*)(0x630b60+284*4) != 0 && *(int*)(0x630b60+293*4) != 0'
intro_actions=[]
if intro_skip_action:
    intro=gdb.Breakpoint('FUN_00415d40',internal=True)
    base_condition='DAT_0047a470 != 0 && _DAT_0073cc3c != 0 && _DAT_0073cc3c != 0x67da4c && *(int*)((int)DAT_0047a470+0xa6) != 0'
    intro.condition=base_condition
    gdb.execute('run --run-recon',to_string=True)
    for ordinal in range(intro_skip_action):
        require(gdb.selected_frame().name()=='FUN_00415d40','Stopped before horseback skip checkpoint')
        pointer=value('*(unsigned int*)((int)DAT_0047a470+0xa6)')
        intro_actions.append(dict(action=pointer,camera=(value('_DAT_0073cc3c')-0x67c728)//28))
        with open(prefix+'-intro-actions.json','w') as out:json.dump(intro_actions,out,indent=2)
        if ordinal+1<intro_skip_action:
            intro.condition=base_condition+f' && *(unsigned int*)((int)DAT_0047a470+0xa6) != {pointer}'
            gdb.execute('continue',to_string=True)
    # Queue a real SDL Space tap, retaining it through one update frame.
    gdb.execute('set $skip_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
    gdb.execute('set $skip_event->key.type=0x300',to_string=True)
    gdb.execute('set $skip_event->key.down=1',to_string=True)
    gdb.execute('set $skip_event->key.key=32',to_string=True)
    gdb.execute('set $skip_event->key.scancode=44',to_string=True)
    gdb.execute('set $skip_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
    require(value('SDL_PushEvent($skip_event)')==1,'Intro SDL Space injection failed')
    gdb.execute('call e2r_poll_host_events("intro-action-skip")',to_string=True)
    intro.condition=None
    gdb.execute('continue',to_string=True)
    require(gdb.selected_frame().name()=='FUN_00415d40','Space handoff crashed')
    gdb.execute('set $skip_event->key.type=0x301',to_string=True)
    gdb.execute('set $skip_event->key.down=0',to_string=True)
    require(value('SDL_PushEvent($skip_event)')==1,'Intro SDL Space release failed')
    gdb.execute('call e2r_poll_host_events("intro-action-release")',to_string=True)
    gdb.execute('call (void)free($skip_event)',to_string=True)
    intro.delete()
    gdb.execute('continue',to_string=True)
elif natural_intro:
    gdb.execute('run --run-recon',to_string=True)
else:
    gdb.execute('run --inject-key-sequence-surfaces ' + json.dumps(prefix+'-startup') +
                ' space 3 250 PROCESS_SECONDS',to_string=True)
if gdb.selected_frame().name()!='FUN_00415d40':gdb.execute('bt 32')
require(gdb.selected_frame().name()=='FUN_00415d40','Missing courtyard release checkpoint')
def key(vk,pressed):
    scan={0x26:0x48,0x28:0x50,0x25:0x4b,0x27:0x4d,0x10:0x2a,0x11:0x1d,0x12:0x38}[vk]
    extended=vk in (0x26,0x28,0x25,0x27)
    if use_sdl:
        sdl_scan={0x26:82,0x28:81,0x25:80,0x27:79,0x10:225,0x11:224,0x12:226}[vk]
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
        lparam=1|(scan<<16)|(int(extended)<<24)|(0 if pressed else 0xc0000000)
        gdb.execute(f'call E2R_WndProc((HWND)_DAT_00ac4dac,{0x100 if pressed else 0x101},{vk},(LPARAM)0x{lparam:x})',to_string=True)
    table=0x4c3a90 if extended else 0x4c3b90
    require(value(f'*(unsigned char*)({table}+{scan})')==int(pressed),
            'WndProc did not update the requested held-key byte')
guard_checkpoints=[]
def guard_checkpoint(label):
    active=[];node=value('_DAT_0063726c')
    for i in range(128):
        if not node:break
        require(node not in active,'Actor list cycle')
        active.append(node);node=value(f'*(unsigned int*)({node}+0x4c)')
    guards=[]
    for identifier in (284,293):
        pointer=value(f'*(unsigned int*)(0x630b60+{identifier}*4)')
        if label in ('restrained','release','before'):
            require(pointer in active,f'Original guard {identifier} is absent from update list')
        if not pointer:
            guards.append(dict(id=identifier,pointer=0,active=False));continue
        require(value(f'*(short*){pointer}')==identifier,'Guard constructor lost original identity')
        guards.append(dict(id=identifier,pointer=pointer,active=pointer in active,position=[value(f'*(short*)({pointer}+0x84+{j}*2)') for j in range(3)],
                           state=value(f'*(short*)({pointer}+0x82)'),action=value(f'*(unsigned int*)({pointer}+0xa6)')))
    packet=prefix+'-guards-'+label
    require(value('e2r_write_visibility_packet((HWND)_DAT_00ac4dac,'+json.dumps(packet)+')')==1,'Guard visibility packet failed')
    if label in ('restrained','release','before'):
        with open(packet+'-state.txt') as stream:visibility=stream.read()
        for guard in guards:
            match=re.search(r'actor_cue\[(\d+)\] id='+str(guard['id'])+r' ',visibility)
            require(match is not None,'Guard missing from presentation snapshot')
            index=match.group(1)
            points=[tuple(map(int,p)) for p in re.findall(r'actor_cylinder\['+index+r'\]\.point\[\d+\]=(-?\d+),(-?\d+),(-?\d+)',visibility)]
            front=[p for p in points if p[2]>0]
            eligible=re.search(r'actor_cue\['+index+r'\] id=.*visible_in_view=1',visibility)
            visible=bool(eligible and front) and min(p[0] for p in front)<640 and max(p[0] for p in front)>=0 and min(p[1] for p in front)<480 and max(p[1] for p in front)>=0
            require(visible,'Guard cylinder is outside the pedestal view')
            guard['projected_on_screen']=visible
    guard_checkpoints.append(dict(phase=label,wait=value('DAT_0047a76c'),guards=guards))
    with open(prefix+'-guards.json','w') as out:json.dump(guard_checkpoints,out,indent=2)
if check_guards:
    # Let the real renderer present frames after the first loaded-guard checkpoint.
    for i in range(3):gdb.execute('continue',to_string=True)
    require(value('DAT_0047a76c')!=0,'Missed restrained Joe checkpoint')
    guard_checkpoint('restrained')
    if HOLD_THROUGH_RELEASE:
        key(0x25 if TURN_FORWARD=='left' else 0x27,True)
        key(0x26 if MOVE_KEY=='up' else 0x28,True)
    ready.condition='DAT_0047a76c == 0 && _DAT_0073cc3c == 0x67da4c && DAT_0047a470 != 0'
    gdb.execute('continue',to_string=True)
    if gdb.selected_frame().name()!='FUN_00415d40':gdb.execute('bt 32')
    require(gdb.selected_frame().name()=='FUN_00415d40','Guard route failed before Joe release')
    guard_checkpoint('release')
ready.delete()
actor=value('DAT_0047a470')
require(value(f'*(short*){actor}')==0,'Current actor is not Joe')
def population_census(label):
    import struct
    inf=gdb.selected_inferior()
    table=struct.unpack('<5000I',bytes(inf.read_memory(0x630b60,20000)))
    names=bytes(inf.read_memory(value('_DAT_006366b4'),10000)).split(b'\0')
    actors=[]
    for index,pointer in enumerate(table):
        if not pointer:continue
        data=bytes(inf.read_memory(pointer,0x188))
        h=lambda offset:struct.unpack_from('<h',data,offset)[0]
        u=lambda offset:struct.unpack_from('<I',data,offset)[0]
        actors.append(dict(index=index,pointer=pointer,id=h(0),
            table_flags=value(f'*(unsigned short*)({0x64a178}+{index}*2)'),
            name=names[index].decode('ascii','replace') if index<len(names) else None,
            flags=data[2:4].hex(),position=[h(0x84+i*2) for i in range(3)],
            state=h(0x82),representation=u(0x11e),action=u(0xa6),
            action_progress=struct.unpack_from('<H',data,0xac)[0],next=u(0x4c)))
    active=[];node=value('_DAT_0063726c')
    while node and len(active)<256:
        require(node not in active,'Cycle in active actors')
        active.append(node);node=value(f'*(unsigned int*)({node}+0x4c)')
    sample=dict(label=label,current=value('DAT_0047a470'),active=active,actors=actors,
                population_disabled=value('DAT_0047a450'),ticks=value('_DAT_00636588'),
                scheduler_last_tick=value('DAT_0047b7f0'),random_seed=value('E2R_rand_seed_fallback'),
                camera=(value('_DAT_0073cc3c')-0x67c728)//28)
    sample['generated_active']=[a['id'] for a in actors
                                if a['pointer'] in active and a['table_flags']&8]
    sample['generated_counted']=[a['id'] for a in actors
                                if a['pointer'] in active and a['table_flags']&8 and a['state']!=11]
    population_samples.append(sample)
    with open(prefix+'-population.json','w') as out:json.dump(population_samples,out,indent=2)
    return sample
frame=gdb.Breakpoint('FUN_00415d40',internal=True)
def advance(count):
    if count == 0:return
    if BURST_FRAMES:frame.ignore_count=count-1
    for i in range(1 if BURST_FRAMES else count):
        gdb.execute('continue',to_string=True)
        if gdb.selected_frame().name()!='FUN_00415d40':
            if population_frames:population_census('runtime-stop')
            gdb.execute('bt 16')
            raise gdb.GdbError('Unexpected runtime stop')
        if globals().get('trace_heading',False):
            heading_samples.append(dict(position=[field(0x84+j*2) for j in range(3)],
                angles=[field(0x90+j*2) for j in range(3)],
                render=[field(6+j*2) for j in range(9)],
                motion=[field(0xc6+j*2) for j in range(9)],flags=field(0x146,'unsigned char')))
            with open(prefix+'-heading.json','w') as out:json.dump(heading_samples,out)
def field(offset,kind='short'):
    return value(f'*({kind}*)({actor}+{offset})')
def snapshot(label):
    rep=field(0x11e,'unsigned int');action=field(0xa6,'unsigned int')
    position=[field(0x84+i*2) for i in range(3)]
    cell_address=0x684d68+((position[0]>>9)+64)*2+((position[2]>>9)+64)*256
    floor_cell=value(f'*(unsigned short*){cell_address}')
    data=dict(phase=label,actor=actor,scene=value('_DAT_0073cc3c'),
              wait=value('DAT_0047a76c'),modal=value('_DAT_00643650'),
              population_disabled=value('DAT_0047a450'),ticks=value('_DAT_00636588'),
              scheduler_last_tick=value('DAT_0047b7f0'),
              position=position,facing=field(0x92),
              render_matrix=[field(6+i*2) for i in range(9)],
              motion_matrix=[field(0xc6+i*2) for i in range(9)],
              actor_flags=field(2,'unsigned short'),
              attachment=field(0xf2,'unsigned int'),
              angles=[field(0x90),field(0x92),field(0x94)],
              queued_action=field(0x162),floor_cell=floor_cell,
              elapsed_ticks=value('_DAT_00637378'),motion_distance=field(0x170),
              representation=rep,representation_id=value(f'*(short*){rep}') if rep else -1,
              forward_slot=value(f'*(short*)({rep}+2+39*2)') if rep else -1,
              action=action,action_id=value(f'*(short*){action}') if action else -1,
              progress=field(0xac,'unsigned short'),duration=field(0xaa,'unsigned short'),
              previous_slot=field(0x96),input_direction=value('_DAT_00479e78'),
              actor_state=field(0x82),motion_flags=field(0x146,'unsigned char'),
              modifiers={name:value(symbol) for name,symbol in
                         [('shift','DAT_00636846'),('ctrl','DAT_00636852'),('alt','DAT_0063684a')]},
              held_keys={name:value(f'*(unsigned char*)({0x4c3a90}+{scan})')
                         for name,scan in [('up',0x48),('down',0x50),('left',0x4b),('right',0x4d)]})
    packet=prefix+'-'+label
    expression='e2r_write_visibility_packet((HWND)_DAT_00ac4dac,'+json.dumps(packet)+')'
    require(value(expression)==1,'Visibility packet failed')
    return data
states=[]
camera_samples=[]
def observe_camera():
    require(value('DAT_0047a470')==actor,'Traversal changed the current actor')
    require(value('_DAT_00643650')==0,'Traversal opened a requester')
    require(value('DAT_0047a76c')==0,'Traversal restored the script wait')
    camera=(value('_DAT_0073cc3c')-0x67c728)//28
    camera_samples.append(dict(camera=camera,position=[field(0x84+i*2) for i in range(3)]))
    return camera
def checkpoint(label):
    states.append(snapshot(label))
    if check_guards:guard_checkpoint(label)
    if population_frames:population_census(label)
    # Retain completed phases even when a later input exposes a runtime fault.
    with open(prefix+'.json','w') as out:
        json.dump(dict(probe_complete=False,frames_per_phase=frames,states=states,
                       combined_turn=TURN_FORWARD,turn_calls=globals().get('turn_calls',[]),
                       simultaneous_turn=SIMULTANEOUS_TURN,burst_frames=BURST_FRAMES,
                       background_spawns=BACKGROUND_SPAWNS,
                       hold_through_release=HOLD_THROUGH_RELEASE,video_driver=VIDEO_DRIVER,
                       tapped_modifiers=TAP_MODIFIERS,
                       startup_logo_delay_ms=LOGO_DELAY,
                       sdl_events=use_sdl,release_turn_first=RELEASE_TURN,move_key=MOVE_KEY,
                       camera_round_trip=camera_route,camera_samples=camera_samples,
                       gameplay_acceptance=False),out,indent=2)
advance(RELEASE_DELAY)
checkpoint('before')
object_view_sample=None
if OBJECT_SCENE >= 0:
    import struct
    inf=gdb.selected_inferior()
    scene=value(f'*(unsigned int*)(0x62e450+{OBJECT_SCENE}*4)')
    require(scene!=0,'Requested object scene was not preloaded by the original startup script')
    camera=value(f'*(short*)({scene}+2)')
    original_camera=observe_camera()
    original_position=[field(0x84+i*2) for i in range(3)]
    for approach in APPROACH_CAMERAS:
        gdb.execute(f'call FUN_0044be20({approach})',to_string=True)
        require(value('DAT_0047a470')==actor,'Approach view changed Joe ownership')
        require([field(0x84+i*2) for i in range(3)]==original_position,'Approach view moved Joe')
        require(value('e2r_present_current_frame((HWND)_DAT_00ac4dac,1)')==1,'Approach view SDL presentation failed')
        snapshot('approach-view-'+str(approach))
    gdb.execute(f'call FUN_0044be20({camera})',to_string=True)
    require(value('DAT_0047a470')==actor,'Object view changed Joe ownership')
    require([field(0x84+i*2) for i in range(3)]==original_position,'Object view moved Joe')
    active=[];node=value('_DAT_0063726c')
    while node and len(active)<256:
        require(node not in active,'Cycle after object activation')
        active.append(node);node=value(f'*(unsigned int*)({node}+0x4c)')
    children=[];child=value(f'*(unsigned int*)({scene}+4)')
    while child and len(children)<128:
        identifier=value(f'*(short*){child}')
        flags=value(f'*(unsigned char*)({child}+14)')
        if identifier>=0 and not flags&0x20:
            pointer=value(f'*(unsigned int*)(0x630b60+{identifier}*4)')
            cached=[value(f'*(short*)(0x669708+{identifier}*6+{axis}*2)') for axis in range(3)]
            position=[value(f'*(short*)({pointer}+0x84+{axis}*2)') for axis in range(3)] if pointer else None
            children.append(dict(id=identifier,actor=pointer,active=pointer in active,
                                 cached=cached,position=position))
        child=value(f'*(unsigned int*)({child}+24)')
    require(any(c['active'] for c in children),'No child activated through the original visibility sweep')
    require(value('e2r_present_current_frame((HWND)_DAT_00ac4dac,1)')==1,'Object view SDL presentation failed')
    view_state=snapshot('object-view')
    with open(prefix+'-object-view-state.txt') as stream:visibility=stream.read()
    for child_state in children:
        match=re.search(r'actor_cue\[(\d+)\] id='+str(child_state['id'])+r' ',visibility)
        points=[]
        if match:
            points=[tuple(map(int,p)) for p in re.findall(
                r'actor_cylinder\['+match.group(1)+r'\]\.point\[\d+\]=(-?\d+),(-?\d+),(-?\d+)',visibility)]
        front=[p for p in points if p[2]>0]
        eligible=match and re.search(r'actor_cue\['+match.group(1)+r'\] id=.*visible_in_view=1',visibility)
        child_state['projected_on_screen']=bool(eligible and front) and min(p[0] for p in front)<640 and max(p[0] for p in front)>=0 and min(p[1] for p in front)<480 and max(p[1] for p in front)>=0
    require(any(c['active'] and c['projected_on_screen'] for c in children),
            'No active scene child has an on-screen diagnostic cylinder')
    object_view_sample=dict(scene_id=OBJECT_SCENE,camera=camera,record=scene,
                            approach_cameras=APPROACH_CAMERAS,
                            diagnostic_view_selection=True,children=children,
                            joe_position=original_position,state=view_state)
    with open(prefix+'-object-view.json','w') as out:json.dump(object_view_sample,out,indent=2)
    gdb.execute(f'call FUN_0044be20({original_camera})',to_string=True)
    require(observe_camera()==original_camera,'Object view did not restore the original camera')
    require([field(0x84+i*2) for i in range(3)]==original_position,'Object view return moved Joe')
for modifier in TAP_MODIFIERS:
    modifier_vk={'shift':0x10,'ctrl':0x11,'alt':0x12}[modifier]
    key(modifier_vk,True);key(modifier_vk,False)
if TAP_MODIFIERS:checkpoint('modifiers-released')
turn_calls=[]
queries=[]
active_query=None
class QueryEnd(gdb.FinishBreakpoint):
    def __init__(self,entry):
        super().__init__(internal=True);self.entry=entry
    def stop(self):
        global active_query
        self.entry['after']=[field(0x84+i*2) for i in range(3)]
        self.entry['after_facing']=field(0x92)
        active_query=None
        with open(prefix+'-queries.json','w') as out:json.dump(queries,out,indent=2)
        return False
class QueryStart(gdb.Breakpoint):
    def stop(self):
        global active_query
        if len(queries)>=query_limit or value('param_1')!=actor:return False
        vector=value('param_2')
        active_query=dict(position=[field(0x84+i*2) for i in range(3)],facing=field(0x92),
                          radius=field(0x9a),slot=field(0x96),flags=field(0x146,'unsigned char'),
                          vector=[value(f'*(short*)({vector}+{i*2})') for i in range(3)],
                          ticks=value('_DAT_00637378'),state=field(0x82),gravity=field(0x5a),
                          actor_flags=field(3,'unsigned char'),angles=[field(0x90),field(0x94)],
                          actor_head=value('_DAT_0063726c'),actor_next=field(0x4c,'unsigned int'),floors=[])
        queries.append(active_query);QueryEnd(active_query)
        return False
class FloorEnd(gdb.FinishBreakpoint):
    def __init__(self,entry,surface):
        super().__init__(internal=True);self.entry=entry;self.surface=surface
    def stop(self):
        self.entry['floor']=int(self.return_value)
        self.entry['surface']=value(f'*(int*){self.surface}') if self.surface else -1
        return False
class FloorStart(gdb.Breakpoint):
    def stop(self):
        if active_query is None:return False
        coord=value('param_1');owner=value('param_2');surface=value('surface_id')
        position=[value(f'*(short*)({coord}+{i*2})') for i in range(3)]
        cell=value(f'*(unsigned short*)({0x684d68}+{((position[0]>>9)+64)*2+((position[2]>>9)+64)*256})')
        chain=[]
        if cell!=0xffff:
            for i in range(256):
                record=list(bytes(gdb.selected_inferior().read_memory(0x68cd68+(cell+i)*12,12)))
                chain.append(record)
                if record[3]&0x80:break
            else:raise gdb.GdbError('Unterminated terrain descriptor chain')
        selected=value(f'(unsigned int)FUN_00448744({coord},(ushort*){owner})')
        terrain_flags=0
        if selected!=0xffffffff:
            terrain=value(f'*(signed char*)({0x68cd68}+{selected}*12+6)')
            terrain_flags=value(f'*(unsigned char*)({0x636624}+{terrain}*2)')
        entry=dict(coord=position,actor=owner,terrain=bool(surface),cell=cell,descriptors=chain,
                   shift=value('DAT_0047a738'),terrain_flags=terrain_flags,selected=selected)
        active_query['floors'].append(entry);FloorEnd(entry,surface)
        return False
if query_limit:
    query_bp=QueryStart('FUN_00448cb4',internal=True)
    floor_bp=FloorStart('FUN_00448a48',internal=True)
if population_frames:
    # Configuration changes only: the original scheduler selects and places actors.
    if not BACKGROUND_SPAWNS:
        gdb.execute('call (int)setenv("E2R_POPULATION_PROBE","1",1)',to_string=True)
        gdb.execute('call (int)setenv("E2R_DEFER_BACKGROUND_SPAWNS","0",1)',to_string=True)
    for elapsed in range(0,population_frames,30):
        advance(min(30,population_frames-elapsed))
        sample=population_census('population-'+str(min(elapsed+30,population_frames)))
        require(actor in sample['active'],'Population removed Joe from active updates')
        require(value('DAT_0047a470')==actor,'Population changed the current actor')
    checkpoint('population-enabled')
    if REQUIRE_POPULATION:
        require(population_samples[-1]['population_disabled']==0,'Script still disables terrain population')
        require(bool(population_samples[-1]['generated_active']),'No terrain-generated actor is active')
if population_only:
    pass
elif camera_route:
    require(observe_camera()==175,'Missing pedestal camera at readiness')
    # Debug and ASan can take different obstacle-steering paths. Record the
    # actual input route; never alter Joe's coordinates, facing or camera.
    for outward_vk,limit in [(0x26,4),(0x28,24)]:
        key(outward_vk,True)
        for i in range(limit):
            advance(30)
            if observe_camera()!=175:break
        crossed=camera_samples[-1]['camera']!=175
        checkpoint('courtyard-held' if crossed else 'outward-attempt')
        key(outward_vk,False);advance(90)
        if crossed:break
    require(camera_samples[-1]['camera']==166,'Movement did not reach the adjacent courtyard camera')
    checkpoint('courtyard-released')
    return_vk=0x28 if outward_vk==0x26 else 0x26
    key(return_vk,True)
    for i in range(24):
        advance(30)
        if observe_camera()==175 and field(0x86)==3328:break
    if camera_samples[-1]['camera']!=175 or field(0x86)!=3328:checkpoint('return-attempt')
    require(camera_samples[-1]['camera']==175 and field(0x86)==3328,
            'Reverse input did not return to pedestal camera and floor level')
    checkpoint('pedestal-held')
    key(return_vk,False);advance(90);checkpoint('pedestal-released')
    require(observe_camera()==175,'Camera changed after releasing movement')
    require(all(held==0 for held in states[-1]['held_keys'].values()),'Traversal left a key held')
elif TURN_FORWARD:
    class TurnGuard(gdb.Breakpoint):
        def stop(self):
            actual=value('param_1')
            turn_calls.append(dict(actor=actual,angle=value('param_2'),
                                   elapsed_ticks=value('_DAT_00637378'),motion_distance=field(0x170),
                                   caller=gdb.newest_frame().older().name()))
            return actual!=actor
    turn_guard=TurnGuard('FUN_0042b074',internal=True)
    if BURST_FRAMES:turn_guard.enabled=False
    name=TURN_FORWARD
    vk=0x25 if name=='left' else 0x27
    move_vk=0x26 if MOVE_KEY=='up' else 0x28
    heading_samples=[];trace_heading=True
    if not HOLD_THROUGH_RELEASE:
        key(vk,True)
        if SIMULTANEOUS_TURN:key(move_vk,True)
    advance(frames);checkpoint(name+'-pressed')
    if RELEASE_TURN:
        key(vk,False);advance(frames);checkpoint(name+'-released')
    if not SIMULTANEOUS_TURN:key(move_vk,True)
    advance(frames);checkpoint(name+'-'+MOVE_KEY+'-pressed')
    if MOVE_KEY=='up' and not RELEASE_TURN and not BURST_FRAMES:require(len(turn_calls)>0,'Combined-input turn caller was not reached')
    key(move_vk,False)
    if not RELEASE_TURN:key(vk,False)
    advance(frames);checkpoint('released')
    trace_heading=False
    turn_guard.delete()
else:
    for name,vk in [('up',0x26),('down',0x28),('left',0x25),('right',0x27)]:
        key(vk,True);advance(frames);checkpoint(name+'-pressed')
        key(vk,False);advance(frames);checkpoint(name+'-released')
if query_limit:
    query_bp.delete();floor_bp.delete()
    require(len(queries)>0,'No motion queries were recorded')
observed_seconds=0
npc_observation=None
if observe_seconds:
    npc_samples=[]
    if REQUIRE_POPULATION:npc_samples.append(population_census('observation-start'))
    started=time.monotonic()
    while time.monotonic()-started<observe_seconds:
        advance(30)
        observe_camera()
        if REQUIRE_POPULATION:npc_samples.append(population_census('observation-update'))
    observed_seconds=time.monotonic()-started
    checkpoint('observed-released')
    require(all(held==0 for held in states[-1]['held_keys'].values()),'Observation left a key held')
    if REQUIRE_POPULATION:
        moved=set();changed=set();active_windows=0
        for before,after in zip(npc_samples,npc_samples[1:]):
            old={a['pointer']:a for a in before['actors'] if a['pointer'] in before['active']}
            window_changed=False
            for a in after['actors']:
                if not a['table_flags']&8 or a['id']==0 or a['pointer'] not in after['active']:continue
                prior=old.get(a['pointer'])
                if not prior:continue
                if a['position']!=prior['position']:moved.add(a['id'])
                if any(a[key]!=prior[key] for key in ('position','state','action','action_progress')):
                    changed.add(a['id']);window_changed=True
            active_windows+=int(window_changed)
        require(bool(npc_samples[-1]['generated_active']),'Observation lost all generated NPCs')
        require(bool(moved) and bool(changed),'Generated NPCs did not continue moving/updating')
        npc_observation=dict(samples=len(npc_samples),active_windows=active_windows,
                             moved_ids=sorted(moved),changed_ids=sorted(changed))
report=dict(probe_complete=True,frames_per_phase=frames,states=states,
            object_view_sample=object_view_sample,
            combined_turn=TURN_FORWARD,move_key=MOVE_KEY,turn_calls=turn_calls,
            simultaneous_turn=SIMULTANEOUS_TURN,burst_frames=BURST_FRAMES,
            background_spawns=BACKGROUND_SPAWNS,
            hold_through_release=HOLD_THROUGH_RELEASE,video_driver=VIDEO_DRIVER,
            tapped_modifiers=TAP_MODIFIERS,
            startup_logo_delay_ms=LOGO_DELAY,
            sdl_events=use_sdl,release_turn_first=RELEASE_TURN,
            camera_round_trip=camera_route,camera_samples=camera_samples,
            recorded_queries=len(queries),observed_seconds=observed_seconds,npc_observation=npc_observation,
            population_frames=population_frames,population_samples=len(population_samples),
            guard_checkpoints=guard_checkpoints,natural_intro=natural_intro,intro_actions=intro_actions,
            position_changed=any(s['position']!=states[0]['position'] for s in states[1:]),
            facing_changed=any(s['facing']!=states[0]['facing'] for s in states[1:]),
            gameplay_acceptance=False)
with open(prefix+'.json','w') as out:json.dump(report,out,indent=2)
print('PROBE COMPLETE: position_changed='+str(report['position_changed'])+
      ' facing_changed='+str(report['facing_changed'])+'; gameplay acceptance remains open')
end
quit
'''.replace('APPROACH_CAMERAS',repr(args.inspect_approach_cameras)).replace('OBJECT_SCENE',str(args.inspect_object_scene)).replace('PREFIX', json.dumps(prefix)).replace('RELEASE_DELAY',str(args.release_delay)).replace('BURST_FRAMES',repr(args.burst_frames)).replace('FRAMES', str(args.frames)).replace(
    'PROCESS_SECONDS', str(args.timeout + 10)).replace('LOGO_DELAY',str(args.startup_logo_delay_ms)).replace('TURN_FORWARD', repr(args.turn_forward)).replace(
    'MOVE_KEY', repr(args.move_key)).replace('SDL_EVENTS',repr(args.sdl_events or args.camera_round_trip or bool(args.tap_modifiers))).replace('TAP_MODIFIERS',repr(args.tap_modifiers)).replace(
    'RELEASE_TURN',repr(args.release_turn_first)).replace('SIMULTANEOUS_TURN',repr(args.simultaneous_turn)).replace('HOLD_THROUGH_RELEASE',repr(args.hold_through_release)).replace('VIDEO_DRIVER',repr(args.video_driver)).replace('CAMERA_ROUTE',repr(args.camera_round_trip)).replace(
    'QUERY_LIMIT',str(args.trace_queries)).replace('OBSERVE_SECONDS',str(args.observe_seconds)).replace(
    'POPULATION_COUNT',str(args.population_frames)).replace('POPULATION_ONLY',repr(args.population_only)).replace('REQUIRE_POPULATION',repr(args.require_background_population)).replace('BACKGROUND_SPAWNS',repr(args.background_spawns)).replace('CHECK_GUARDS',repr(args.pedestal_guards)).replace('NATURAL_INTRO',repr(args.natural_intro)).replace('INTRO_SKIP_ACTION',str(args.intro_skip_action))
with tempfile.TemporaryDirectory(prefix='e2-player-motion-') as tmp:
    script = Path(tmp) / 'probe.gdb'
    # Desktop drivers load GDB Python helpers from shared libraries. Their
    # top-level names (including `prefix`) must not overwrite this probe's state.
    preamble, body = commands.split('\npython\n', 1)
    body, trailing = body.rsplit('\nend\n', 1)
    python_script = Path(tmp) / 'probe.py'
    python_script.write_text(body)
    source_path = repr(str(python_script))
    script.write_text(preamble + '\npython\nexec(compile(open(' + source_path +
                      ').read(), ' + source_path + ', "exec"), '
                      '{"__name__": "__e2_motion_probe__"})\nend\n' + trailing)
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
    if report['population_frames']:
        print(f"Experimental population: {report['population_frames']} frames; {prefix}-population.json")
    if report['recorded_queries']:
        print(f"Recorded motion queries: {report['recorded_queries']} ({prefix}-queries.json)")
    if report['observed_seconds']:
        print(f"Released-input observation after route: {report['observed_seconds']:.2f} seconds")
    print(f'Evidence: {prefix}.json, {prefix}.log and per-phase visibility packets')
