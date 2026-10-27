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
parser.add_argument('--game-data', type=Path)
parser.add_argument('--suite-scenario', choices=('menu-matrix','shared','startup','movement','courtyard','workshop','sword','attacks','unarmed','unarmed-contact','enemy','damage','door','potion','potion-damaged','potion-sword','swimming','water-traversal','water-combat','armed-swimming','armed-water-traversal','armed-water-combat','menus','stability'))
parser.add_argument('--suite-options', type=json.loads, default={})
parser.add_argument('--output', type=Path, default=Path('/tmp/e2-player-motion'))
parser.add_argument('--intro-skip-action', type=int, default=None,
                    help='Send SDL Space at the Nth observed horseback action (default: first; --natural-intro sends none)')
parser.add_argument('--intro-skip-progress', type=int, default=0,
                    help='Wait for this action-progress tick before the selected horseback Space tap')
parser.add_argument('--natural-intro', action='store_true',
                    help='Let the horseback intro finish without the diagnostic Space shortcut')
parser.add_argument('--logo-policy', choices=('skip','natural'), default='skip',
                    help='Observe actual presented logos, with separate Space taps or natural waits')
parser.add_argument('--startup-logo-delay-ms', type=int, default=5000,
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
parser.add_argument('--watch', action='store_true',
                    help='Pace updates for watching in a real SDL window (at most 60 updates/s)')
parser.add_argument('--window-title', default='Ecstatica regression probe')
parser.add_argument('--hold-through-release', action='store_true',
                    help='With --pedestal-guards and --simultaneous-turn, hold both keys while Joe is still restrained')
parser.add_argument('--tap-modifiers', nargs='+', choices=('shift','ctrl','alt'), default=[],
                    help='Tap and release these modifiers through SDL before the input route')
parser.add_argument('--gameplay-menu-exit', action='store_true',
                    help='After the input route, verify Escape, Cancel, reopened Quit and Yes through SDL input')
parser.add_argument('--sword-attacks', action='store_true',
                    help='After --sword-pickup, hold SDL Ctrl and exercise all four attack directions, then verify released movement')
parser.add_argument('--bash-workshop-door', action='store_true',
                    help='After --sword-pickup, approach left door 980 and bash it using bounded SDL Ctrl/Up input')
parser.add_argument('--sword-pickup', action='store_true',
                    help='Walk the recorded workshop route using SDL arrows, pick up actor 3717 with Space, then verify equipped movement')
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
parser.add_argument('--population-profile', choices=('live','noncombat-opening'), default='live',
                    help='Explicit opening-route fixture; live preserves original actor creation')
parser.add_argument('--background-spawns', action='store_true',
                    help='Run the original population scheduler from startup without the population-probe flag')
parser.add_argument('--require-background-population', action='store_true',
                    help='Require the script population gate open and a live terrain-generated actor in the census')
parser.add_argument('--inspect-object-scene', type=int, default=-1,
                    help='After release, select the preloaded script scene\'s camera for an activation/presentation check, then restore the original view; this is not traversal')
parser.add_argument('--inspect-approach-cameras', type=int, nargs='+', default=[],
                    help='Select these original views before --inspect-object-scene to exercise neighbouring object initialization; no actor coordinates are assigned')
args = parser.parse_args()
if args.intro_skip_action is None:args.intro_skip_action=0 if args.natural_intro else 1
if not args.intro_skip_action and not args.natural_intro and args.startup_logo_delay_ms:
    parser.error('Legacy --intro-skip-action 0 requires --startup-logo-delay-ms 0; use --natural-intro for no horseback skip')
if args.intro_skip_action < 0 or (args.intro_skip_action and args.natural_intro):
    parser.error('intro skip action must be nonnegative and separate from --natural-intro')
if args.intro_skip_progress < 0 or (args.intro_skip_progress and not args.intro_skip_action):
    parser.error('intro-skip-progress requires an intro-skip-action and must be nonnegative')
if args.frames < 1 or args.timeout < 1 or args.release_delay < 0:
    parser.error('frames/timeout must be positive and release-delay nonnegative')
if args.watch and args.video_driver=='dummy':
    parser.error('--watch requires a desktop video driver')
if args.startup_logo_delay_ms < 0:
    parser.error('startup logo delay must be nonnegative')
if args.population_only and (not args.population_frames or args.camera_round_trip or args.turn_forward):
    parser.error('--population-only requires --population-frames and a separate input route')
if args.require_background_population and (not args.background_spawns or not args.population_frames):
    parser.error('--require-background-population requires --background-spawns and --population-frames')
if args.population_profile=='noncombat-opening' and (args.background_spawns or args.pedestal_guards or args.population_frames):
    parser.error('noncombat-opening cannot require or enable live population')
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
if args.bash_workshop_door and not args.sword_pickup:
    parser.error('--bash-workshop-door requires --sword-pickup')
if args.sword_attacks and not args.sword_pickup:
    parser.error('--sword-attacks requires --sword-pickup')
if args.sword_pickup and (args.camera_round_trip or args.turn_forward or args.population_only or
        args.inspect_object_scene >= 0 or args.hold_through_release):
    parser.error('--sword-pickup requires a separate input route without camera selection')
if args.population_profile=='noncombat-opening' and args.suite_scenario:
    from e2_population_profile import profile_for
    if profile_for(args.suite_scenario,args.suite_options.get('checks',[]))=='live':
        parser.error('Selected checkpoints require live population')
prefix = str(args.output.resolve())
Path(prefix).parent.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
if args.suite_scenario:
    for key_name in list(env):
        if key_name.startswith("E2R_"):
            env.pop(key_name)
    env.update(E2R_INSPECT="1", E2R_INSPECT_MAX_FRAMES="8")
env["E2R_RECORD"] = "off"
# Agent probes own their sessions; keep normal human log retention independent.
env["E2R_DATA_DIR"] = prefix + "-runtime"
if args.video_driver == 'dummy':env.pop('DISPLAY', None)
env.update(SDL_VIDEODRIVER=args.video_driver, E2R_STARTUP_LOGO_DELAY_MS=str(args.startup_logo_delay_ms),
           E2R_ACTION_INDEX_PROBE='1', E2R_ACTOR_CYLINDERS='1',
           E2R_PROXY_MESH_BYPASS='1', E2R_DEFER_BACKGROUND_SPAWNS='1')
# Preserve the existing intro resources; recovery is enabled at the checkpoint.
env['E2R_POPULATION_PROBE'] = '0'
if args.background_spawns:env['E2R_DEFER_BACKGROUND_SPAWNS'] = '0'
if args.population_profile=='noncombat-opening':env['E2R_TEST_POPULATION']='noncombat-opening'
else:env.pop('E2R_TEST_POPULATION',None)
env['ASAN_OPTIONS'] = env.get('ASAN_OPTIONS', '') + ':detect_leaks=0'
commands = r'''
set pagination off
set confirm off
python
import gdb,json,time,re,sys
sys.path.insert(0,SCRIPT_DIRECTORY)
prefix=PREFIX
from e2_probe_diagnostics import install
install(prefix)
game_data_root=GAME_DATA_ROOT
frames=FRAMES
use_sdl=SDL_EVENTS
camera_route=CAMERA_ROUTE
pickup_result=None
door_result=None
query_limit=QUERY_LIMIT
observe_seconds=OBSERVE_SECONDS
population_frames=POPULATION_COUNT
check_guards=CHECK_GUARDS
natural_intro=NATURAL_INTRO
intro_skip_action=INTRO_SKIP_ACTION
population_only=POPULATION_ONLY
population_samples=[]
value=lambda expression:int(gdb.parse_and_eval(expression))
startup_logos=[]
def start_runtime(command):
    global startup_logos
    if LOGO_DELAY:
        from e2_startup_steps import start
        startup_logos=start(command,prefix,WATCH_MODE,WINDOW_TITLE,LOGO_SKIP)
        return startup_logos
    gdb.execute(command,to_string=True)
exit_status=[]
gdb.events.exited.connect(lambda event:exit_status.append(getattr(event,'exit_code',None)))
def require(condition,message):
    if not condition:raise gdb.GdbError(message)
ready=gdb.Breakpoint('FUN_00415d40',internal=True)
ready.condition='DAT_0047a76c == 0 && _DAT_0073cc3c == 0x67da4c && DAT_0047a470 != 0'
if natural_intro and not check_guards:
    ready.enabled=False
    class Released(gdb.Breakpoint):
        def stop(self):
            return value('DAT_0047a76c')==0 and value('_DAT_0073cc3c')==0x67da4c and value('DAT_0047a470')!=0
    released=Released('DAT_0047a76c',type=gdb.BP_WATCHPOINT,internal=True)

if check_guards:
    ready.condition='DAT_0047a76c != 0 && _DAT_0073cc3c == 0x67da4c && DAT_0047a470 != 0 && *(int*)(0x630b60+284*4) != 0 && *(int*)(0x630b60+293*4) != 0'
intro_actions=[]
if intro_skip_action:
    intro=gdb.Breakpoint('FUN_00415d40',internal=True)
    base_condition='DAT_0047a470 != 0 && _DAT_0073cc3c != 0 && _DAT_0073cc3c != 0x67da4c && *(int*)((int)DAT_0047a470+0xa6) != 0'
    intro.condition=base_condition
    start_runtime('run --run-recon')
    for ordinal in range(intro_skip_action):
        require(gdb.selected_frame().name()=='FUN_00415d40','Stopped before horseback skip checkpoint')
        pointer=value('*(unsigned int*)((int)DAT_0047a470+0xa6)')
        intro_actions.append(dict(action=pointer,camera=(value('_DAT_0073cc3c')-0x67c728)//28))
        with open(prefix+'-intro-actions.json','w') as out:json.dump(intro_actions,out,indent=2)
        if ordinal+1<intro_skip_action:
            intro.condition=base_condition+f' && *(unsigned int*)((int)DAT_0047a470+0xa6) != {pointer}'
            gdb.execute('continue',to_string=True)
    if INTRO_SKIP_PROGRESS:
        require(INTRO_SKIP_PROGRESS<value('*(unsigned short*)((int)DAT_0047a470+0xaa)'),
                'Requested skip progress is outside the selected action')
        intro.condition=base_condition+f' && *(unsigned int*)((int)DAT_0047a470+0xa6) == {pointer} && *(unsigned short*)((int)DAT_0047a470+0xac) >= INTRO_SKIP_PROGRESS'
        gdb.execute('continue',to_string=True)
        require(gdb.selected_frame().name()=='FUN_00415d40','Missing delayed skip checkpoint')
    intro_actions[-1]['skip_progress']=value('*(unsigned short*)((int)DAT_0047a470+0xac)')
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
    start_runtime('run --run-recon')
    if not check_guards:
        released.delete()
        ready.enabled=True
        gdb.execute('continue',to_string=True)
else:
    gdb.execute('run --inject-key-sequence-surfaces ' + json.dumps(prefix+'-startup') +
                ' space 3 250 PROCESS_SECONDS',to_string=True)
if gdb.selected_frame().name()!='FUN_00415d40':gdb.execute('bt 32')
require(gdb.selected_frame().name()=='FUN_00415d40','Missing courtyard release checkpoint')
def set_phase_title(phase):
    if WATCH_MODE:
        title=WINDOW_TITLE+' | '+phase
        gdb.execute('call (bool)SDL_SetWindowTitle(e2r_sdl_backend.window,'+json.dumps(title)+')',to_string=True)
        time.sleep(.25)
set_phase_title('startup released')
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
    names=bytes(inf.read_memory(value('_DAT_006366b4'),40000)).split(b'\0')
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
    remaining=count
    while remaining:
        batch=min(remaining,3) if WATCH_MODE and BURST_FRAMES else remaining if BURST_FRAMES else 1
        started=time.monotonic()
        frame.ignore_count=batch-1
        gdb.execute('continue',to_string=True)
        if gdb.selected_frame().name()!='FUN_00415d40':
            if population_frames:population_census('runtime-stop')
            gdb.execute('bt 16')
            raise gdb.GdbError('Unexpected runtime stop')
        remaining-=batch
        if WATCH_MODE:time.sleep(max(0,batch/60-(time.monotonic()-started)))
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
              health=field(0xec),actor_state=field(0x82),motion_flags=field(0x146,'unsigned char'),
              modifiers={name:value(symbol) for name,symbol in
                         [('shift','DAT_00636846'),('ctrl','DAT_00636852'),('alt','DAT_0063684a')]},
              held_keys={name:value(f'*(unsigned char*)({0x4c3a90}+{scan})')
                         for name,scan in [('up',0x48),('down',0x50),('left',0x4b),('right',0x4d)]})
    packet=prefix+'-'+label
    expression='e2r_write_visibility_packet((HWND)_DAT_00ac4dac,'+json.dumps(packet)+')'
    if not SUITE_SCENARIO:
        require(value(expression)==1,'Visibility packet failed')
    return data
states=[]
camera_samples=[]
def observe_camera():
    require(value('DAT_0047a470')==actor,'Traversal changed the current actor')
    require(value('_DAT_00643650')==0,'Traversal opened a requester')
    require(value('DAT_0047a76c')==0,'Traversal restored the script wait')
    require(field(0xec)>0 and field(0x82) not in (5,8,11),'Traversal entered a death state')
    camera=(value('_DAT_0073cc3c')-0x67c728)//28
    camera_samples.append(dict(camera=camera,position=[field(0x84+i*2) for i in range(3)]))
    return camera
def checkpoint(label):
    from e2_population_profile import observe
    observe(prefix,label)
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
suite_result=None
if SUITE_SCENARIO:
    import sys
    sys.path.insert(0,SCRIPT_DIRECTORY)
    from e2_gameplay_steps import run as run_suite_journey
    watch_mode=WATCH_MODE
    suite_result=run_suite_journey(globals(),SUITE_SCENARIO,SUITE_OPTIONS)
elif population_only:
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
elif SWORD_PICKUP:
    import math
    # Waypoints sampled from human session 20261024_115718_697; input only.
    waypoints=[
        [9988, 3328, -17408], [9736, 3328, -16910], [8936, 3840, -16518],
        [8260, 4096, -16259], [7554, 4096, -15990], [7170, 4096, -15558],
        [6878, 4096, -14734], [6637, 4096, -14338], [6267, 4096, -14015],
        [5486, 4096, -13551], [4671, 4096, -13485], [4023, 4096, -13434],
        [3269, 4096, -13375], [2796, 4096, -13337], [2314, 4096, -12892],
        [1836, 4096, -12592], [1970, 4096, -11896], [2154, 4096, -11361],
        [2350, 4096, -10889], [2007, 4096, -10465], [1555, 4096, -10499],
        [833, 4096, -10493], [378, 4096, -10244], [-125, 4096, -9845],
        [-789, 4096, -9781], [-1278, 4096, -9756], [-837, 4096, -10021],
        [-871, 4096, -10006],
    ]
    held={0x26:False,0x25:False,0x27:False}
    def setkey(vk,on):
        if held[vk]!=on:key(vk,on);held[vk]=on
    travel=[]
    for waypoint_index,waypoint in enumerate(waypoints[1:]):
        for attempt in range(180):
            pos=[field(0x84+i*2) for i in range(3)]
            distance=math.hypot(waypoint[0]-pos[0],waypoint[2]-pos[2])
            row=dict(waypoint=waypoint_index,position=pos,yaw=field(0x92),health=field(0xec),state=field(0x82))
            travel.append(row)
            with open(prefix+'-travel.json','w') as out:json.dump(travel,out)
            require(row['health']>0 and row['state'] not in (5,8,11),'Player died during sword traversal')
            require(value('_DAT_00643650')==0,'Sword traversal opened a requester')
            if distance<160:break
            desired=int(math.atan2(waypoint[0]-pos[0],waypoint[2]-pos[2])*65536/(2*math.pi))
            difference=(desired-field(0x92)+32768)%65536-32768
            setkey(0x25,difference < -800);setkey(0x27,difference > 800)
            setkey(0x26,abs(difference)<5000)
            advance(1 if abs(difference)>800 or distance<450 else 3)
        else:raise gdb.GdbError('Sword traversal missed waypoint '+str(waypoint_index))
    sword=value('*(unsigned int*)(0x630b60+3717*4)')
    require(sword!=0,'Original sword is absent at workshop')
    target=[value(f'*(short*)({sword}+0x84+{i}*2)') for i in range(3)]
    for approach in range(180):
        pos=[field(0x84+i*2) for i in range(3)]
        distance=math.hypot(target[0]-pos[0],target[2]-pos[2])
        desired=int(math.atan2(target[0]-pos[0],target[2]-pos[2])*65536/(2*math.pi))
        difference=(desired-field(0x92)+32768)%65536-32768
        setkey(0x25,difference < -400);setkey(0x27,difference > 400)
        setkey(0x26,distance>220 and abs(difference)<5000)
        if distance<=220 and abs(difference)<=400:break
        advance(1)
    else:raise gdb.GdbError('Could not approach/facing sword')
    for vk in held:setkey(vk,False)
    advance(8);checkpoint('sword-before-space')
    def space(pressed):
        gdb.execute('set $interaction_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
        gdb.execute(f'set $interaction_event->key.type={0x300 if pressed else 0x301}',to_string=True)
        gdb.execute(f'set $interaction_event->key.down={int(pressed)}',to_string=True)
        gdb.execute('set $interaction_event->key.key=32',to_string=True)
        gdb.execute('set $interaction_event->key.scancode=44',to_string=True)
        gdb.execute('set $interaction_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
        require(value('SDL_PushEvent($interaction_event)')==1,'SDL Space input failed')
        gdb.execute('call (void)free($interaction_event)',to_string=True)
        gdb.execute('call e2r_poll_host_events("sword-interaction")',to_string=True)
    space(True);advance(12);checkpoint('sword-space-pressed')
    space(False)
    advance(150);checkpoint('sword-after-pickup')
    owner=value(f'*(unsigned int*)({sword}+0xf2)')
    require(owner!=0 and value(f'*(unsigned int*)({owner}+0x22)')==actor,'Sword is not attached to Joe')
    require(value(f'*(unsigned int*)({owner}+0x13a)')==sword,'Pickup node does not own the sword')
    require(field(0xf0)==3,'Pickup did not equip the sword')
    sword_before=[value(f'*(short*)({sword}+0x84+{i}*2)') for i in range(3)]
    attacks=[]
    if SWORD_ATTACKS:
        key(0x11,True)
        for direction_index,(direction,vk) in enumerate([('up',0x26),('left',0x25),('right',0x27),('down',0x28)]):
            key(vk,True)
            for attack_wait in range(12):
                advance(30)
                slot=field(0x96)
                if 0xb8<=slot<=0xd3 and (slot-0xb8)%4==direction_index:break
            else:raise gdb.GdbError('Requested sword attack direction did not start: '+direction)
            checkpoint('sword-attack-'+direction)
            sample=states[-1]
            require(0xb8<=sample['previous_slot']<=0xd3,'Ctrl/arrow did not select a sword attack')
            require(sample['modifiers']['ctrl']==1,'Sword attack lost Ctrl input')
            attacks.append(dict(direction=direction,action=sample['action_id'],slot=sample['previous_slot']))
            key(vk,False);advance(30)
        key(0x11,False);advance(90)
    before_move=[field(0x84+i*2) for i in range(3)]
    key(0x28,True);advance(30);key(0x28,False);advance(30)
    checkpoint('sword-equipped-movement')
    require(before_move!=[field(0x84+i*2) for i in range(3)],'Joe cannot move after pickup')
    require(value(f'*(unsigned int*)({sword}+0xf2)')==owner,'Movement lost the sword attachment')
    sword_after=[value(f'*(short*)({sword}+0x84+{i}*2)') for i in range(3)]
    require(sword_after!=target,'Picked-up sword remained at its original placement')
    require(sword_after!=sword_before,'Attached sword did not follow Joe movement')
    require(states[-1]['modifiers']['ctrl']==0,'Sword attack left Ctrl held')
    observe_camera()
    require(field(0xec)==100 and field(0x82)==4,'Pickup changed Joe health/control')
    require(all(v==0 for v in states[-1]['held_keys'].values()),'Pickup route left a key held')
    pickup_result=dict(sword=sword,node=owner,owner=actor,kind=field(0xf0),
                       representation=states[-1]['representation_id'],health=field(0xec),attacks=attacks,
                       sword_position_before=sword_before,sword_position_after=sword_after,
                       movement_before=before_move,movement_after=[field(0x84+i*2) for i in range(3)])
    if BASH_WORKSHOP_DOOR:
        door=value('*(unsigned int*)(0x630b60+980*4)')
        require(door!=0,'Left workshop door is absent')
        door_samples=[]
        def door_sample(label):
            rep=value(f'*(unsigned int*)({door}+0x11e)')
            action=value(f'*(unsigned int*)({door}+0xa6)')
            row=dict(phase=label,health=value(f'*(short*)({door}+0xec)'),
                     state=value(f'*(short*)({door}+0x82)'),flags=value(f'*(unsigned short*)({door}+2)'),
                     representation=value(f'*(short*){rep}') if rep else -1,
                     action=value(f'*(short*){action}') if action else -1,
                     position=[value(f'*(short*)({door}+0x84+{i}*2)') for i in range(3)],
                     player_position=[field(0x84+i*2) for i in range(3)],player_health=field(0xec))
            door_samples.append(row)
            with open(prefix+'-door.json','w') as out:json.dump(door_samples,out,indent=2)
            return row
        door_sample('before-approach')
        # Approach the human strike position using arrows; actor state is read only.
        for waypoint in [(-1800,-9800),(-2200,-10100),(-2571,-10545)]:
            for attempt in range(240):
                dx,dz=waypoint[0]-field(0x84),waypoint[1]-field(0x88)
                if math.hypot(dx,dz)<100:break
                desired=int(math.atan2(dx,dz)*65536/(2*math.pi))
                difference=(desired-field(0x92)+32768)%65536-32768
                setkey(0x25,difference < -600);setkey(0x27,difference > 600)
                setkey(0x26,abs(difference)<5000)
                advance(1)
            else:raise gdb.GdbError('Could not reach door strike approach')
        for vk in held:setkey(vk,False)
        for attempt in range(180):
            dx=value(f'*(short*)({door}+0x84)')-field(0x84)
            dz=value(f'*(short*)({door}+0x88)')-field(0x88)
            desired=int(math.atan2(dx,dz)*65536/(2*math.pi))
            difference=(desired-field(0x92)+32768)%65536-32768
            setkey(0x25,difference < -400);setkey(0x27,difference > 400)
            if abs(difference)<=400:break
            advance(1)
        else:raise gdb.GdbError('Could not face left door')
        for vk in held:setkey(vk,False)
        checkpoint('door-before-strikes');door_sample('before-strikes')
        key(0x11,True);key(0x26,True)
        for batch in range(40):
            advance(30)
            sample=door_sample('strike-'+str(batch))
            require(field(0xec)>0 and field(0x82)!=11,'Player died while bashing door')
            if sample['state']==11:break
        key(0x26,False);key(0x11,False);advance(150)
        checkpoint('door-after-strikes')
        final=door_sample('after-strikes')
        require(final['health']<=0 and final['state']==11 and final['representation']==-1,
                'Bounded strikes did not finish the left door collapse/deactivation')
        approach=final['player_position']
        dx,dz=final['position'][0]-approach[0],final['position'][2]-approach[2]
        key(0x26,True);advance(60);key(0x26,False);advance(30)
        checkpoint('door-passage-released')
        passage=door_sample('passage-released')
        beyond=((field(0x84)-final['position'][0])*dx+
                (field(0x88)-final['position'][2])*dz)/math.hypot(dx,dz)
        door_result=dict(actor=980,samples=door_samples,final=final,passage=passage,
                         distance_beyond_door=beyond)
        print('DOOR RESULT '+json.dumps(door_result),flush=True)
        require(beyond>100,'Joe did not pass through the collapsed door opening')
        require(field(0xec)>0 and field(0x82)==4 and value('_DAT_00643650')==0,
                'Door passage lost living player control')
        require(all(v==0 for v in states[-1]['held_keys'].values()) and
                states[-1]['modifiers']['ctrl']==0,'Door route left keys held')
    print('PICKUP COMPLETE '+json.dumps(pickup_result),flush=True)
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
if GAMEPLAY_MENU_EXIT:
    from contextlib import nullcontext, ExitStack
    menu_phase=suite_journey.phase('menus.cancel-resume-quit',observe=False) if SUITE_SCENARIO else nullcontext()
    with ExitStack() as menu_stack:
        if SUITE_SCENARIO=='shared':
            menu_stack.enter_context(suite_journey.checkpoint('Menus.CancelResumeQuit'))
        menu_stack.enter_context(menu_phase)
        def menu_escape(pressed):
            gdb.execute('set $menu_key=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
            gdb.execute(f'set $menu_key->key.type={0x300 if pressed else 0x301}',to_string=True)
            gdb.execute(f'set $menu_key->key.down={int(pressed)}',to_string=True)
            gdb.execute('set $menu_key->key.key=27',to_string=True)
            gdb.execute('set $menu_key->key.scancode=41',to_string=True)
            gdb.execute('set $menu_key->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
            require(value('SDL_PushEvent($menu_key)')==1,'SDL Escape input failed')
            gdb.execute('call (void)free($menu_key)',to_string=True)
            gdb.execute('call e2r_poll_host_events("gameplay-menu")',to_string=True)
        frame.enabled=False
        menu=gdb.Breakpoint('FUN_0041ba7c',internal=True)
        menu_escape(True)
        gdb.execute('continue',to_string=True)
        gdb.execute('call e2r_present_current_frame((HWND)_DAT_00ac4dac,1)',to_string=True)
        menu_escape(False)
        snapshot('escape-menu')
        for n in range(3):gdb.execute('continue',to_string=True)
        gdb.execute('call e2r_present_current_frame((HWND)_DAT_00ac4dac,1)',to_string=True)
        snapshot('escape-menu-pumped')
        if WATCH_MODE:time.sleep(.75)
        menu_escape(True)
        menu_escape(False)
        menu.delete();frame.enabled=True;advance(3)
        checkpoint('escape-menu-cancelled')
        require(value('_DAT_00643650')==0,'Escape cancellation did not resume gameplay')
        if SUITE_SCENARIO:
            resume_position=[field(0x84+i*2) for i in range(3)]
            # The pedestal can block backward movement. Exercise both travel
            # directions before deciding whether menu cancellation lost control.
            for resume_key in (0x26,0x28):
                key(resume_key,True);advance(30);key(resume_key,False);advance(90)
                if [field(0x84+i*2) for i in range(3)]!=resume_position:break
            checkpoint('menus-resumed-movement')
            require([field(0x84+i*2) for i in range(3)]!=resume_position,'Menu cancellation did not restore movement')
        frame.enabled=False
        menu=gdb.Breakpoint('FUN_0041ba7c',internal=True)
        menu_escape(True)
        for n in range(3):gdb.execute('continue',to_string=True)
        menu_escape(False)
        # Use the original item's computed hit rectangle through the SDL mouse path.
        def click_item(address):
            x=(value(f'*(short*)({address}+22)')+value(f'*(short*)({address}+24)'))//2
            y=(value(f'*(short*)({address}+26)')+value(f'*(short*)({address}+28)'))//2
            gdb.execute(f'call SetCursorPos({x},{y})',to_string=True)
            gdb.execute('set $menu_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))',to_string=True)
            gdb.execute('set $menu_event->button.type=0x401',to_string=True)
            gdb.execute('set $menu_event->button.down=1',to_string=True)
            gdb.execute('set $menu_event->button.button=1',to_string=True)
            gdb.execute(f'set $menu_event->button.x={x}',to_string=True)
            gdb.execute(f'set $menu_event->button.y={y+80}',to_string=True)
            gdb.execute('set $menu_event->button.windowID=SDL_GetWindowID(e2r_sdl_backend.window)',to_string=True)
            require(value('SDL_PushEvent($menu_event)')==1,'SDL menu click failed')
            gdb.execute('call (void)free($menu_event)',to_string=True)
        click_item(0x643ca4)
        menu.condition='*(unsigned short*)((char*)&DAT_0047a45e+2)==0x14'
        gdb.execute('continue',to_string=True)
        require(value('*(unsigned short*)((char*)&DAT_0047a45e+2)')==0x14,'Quit did not open confirmation')
        for n in range(2):gdb.execute('continue',to_string=True)
        gdb.execute('call e2r_present_current_frame((HWND)_DAT_00ac4dac,1)',to_string=True)
        snapshot('quit-confirmation')
        if WATCH_MODE:time.sleep(.75)
        click_item(0x643dc4)
        menu.delete()
        gdb.execute('continue',to_string=True)
        require(gdb.selected_inferior().pid==0,'Confirmed Quit did not terminate the game')
        if SUITE_SCENARIO:require(exit_status and exit_status[-1]==0,'Game exited with a nonzero/unknown native status')
        print('MENU EXIT COMPLETE',flush=True)
report=dict(probe_complete=True,native_exit_code=exit_status[-1] if exit_status else None,suite_result=suite_result,frames_per_phase=frames,states=states,sword_pickup=pickup_result,workshop_door=door_result,gameplay_menu_exit=GAMEPLAY_MENU_EXIT,
            watch=WATCH_MODE,window_title=WINDOW_TITLE,
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
'''.replace('WATCH_MODE',repr(args.watch)).replace('WINDOW_TITLE',repr(args.window_title)).replace('SUITE_SCENARIO',repr(args.suite_scenario)).replace('SUITE_OPTIONS',repr(args.suite_options)).replace('SCRIPT_DIRECTORY',repr(str(Path(__file__).resolve().parent))).replace('GAMEPLAY_MENU_EXIT',repr(args.gameplay_menu_exit)).replace('BASH_WORKSHOP_DOOR',repr(args.bash_workshop_door)).replace('SWORD_ATTACKS',repr(args.sword_attacks)).replace('SWORD_PICKUP',repr(args.sword_pickup)).replace('APPROACH_CAMERAS',repr(args.inspect_approach_cameras)).replace('OBJECT_SCENE',str(args.inspect_object_scene)).replace('GAME_DATA_ROOT',repr(str(args.game_data.resolve()) if args.game_data else None)).replace('PREFIX', json.dumps(prefix)).replace('RELEASE_DELAY',str(args.release_delay)).replace('BURST_FRAMES',repr(args.burst_frames)).replace('FRAMES', str(args.frames)).replace(
    'PROCESS_SECONDS', str(args.timeout + 10)).replace('LOGO_DELAY',str(args.startup_logo_delay_ms)).replace('LOGO_SKIP',repr(args.logo_policy=='skip')).replace('TURN_FORWARD', repr(args.turn_forward)).replace(
    'MOVE_KEY', repr(args.move_key)).replace('SDL_EVENTS',repr(args.sdl_events or args.camera_round_trip or args.sword_pickup or args.gameplay_menu_exit or args.suite_scenario or bool(args.tap_modifiers))).replace('TAP_MODIFIERS',repr(args.tap_modifiers)).replace(
    'RELEASE_TURN',repr(args.release_turn_first)).replace('SIMULTANEOUS_TURN',repr(args.simultaneous_turn)).replace('HOLD_THROUGH_RELEASE',repr(args.hold_through_release)).replace('VIDEO_DRIVER',repr(args.video_driver)).replace('CAMERA_ROUTE',repr(args.camera_round_trip)).replace(
    'QUERY_LIMIT',str(args.trace_queries)).replace('OBSERVE_SECONDS',str(args.observe_seconds)).replace(
    'POPULATION_COUNT',str(args.population_frames)).replace('POPULATION_ONLY',repr(args.population_only)).replace('REQUIRE_POPULATION',repr(args.require_background_population)).replace('BACKGROUND_SPAWNS',repr(args.background_spawns)).replace('CHECK_GUARDS',repr(args.pedestal_guards)).replace('NATURAL_INTRO',repr(args.natural_intro)).replace('INTRO_SKIP_ACTION',str(args.intro_skip_action)).replace('INTRO_SKIP_PROGRESS',str(args.intro_skip_progress))
if args.game_data:
    commands = commands.replace(repr('run --run-recon'),repr('run --game-data-dir '+json.dumps(str(args.game_data.resolve()))+' --run-recon'))
if args.suite_scenario=='menu-matrix':
    commands='set pagination off\nset confirm off\npython\nimport sys\n'
    commands+='sys.path.insert(0,'+repr(str(Path(__file__).resolve().parent))+')\n'
    commands+='from e2_probe_diagnostics import install\ninstall('+repr(prefix)+')\n'
    commands+='from e2_menu_steps import run\n'
    commands+='run('+repr(prefix)+','+repr(args.suite_options)+','+repr(args.watch)+','+repr(args.window_title)+','+repr(str(args.game_data.resolve()) if args.game_data else None)+','+repr(args.startup_logo_delay_ms)+','+repr(args.logo_policy=='skip')+')\nend\nquit\n'
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
    # GDB can put its inferior in another process group. Stop descendants too
    # before GDB disappears, both on the local bound and suite interruption.
    from e2_suite import stop_process
    from e2_probe_diagnostics import communicate
    process = subprocess.Popen(['gdb', '-q', '-batch', '-x', str(script),
                                str(args.exe.resolve())], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, start_new_session=True)
    try:
        stdout, stalled = communicate(process, prefix, args.timeout)
    except subprocess.TimeoutExpired:
        stop_process(process)
        stdout, _ = process.communicate(timeout=5)
        Path(prefix + '.log').write_text(stdout)
        raise SystemExit(f'FAIL: probe timeout; see {prefix}.log')
    except BaseException:
        stop_process(process)
        raise
    result = subprocess.CompletedProcess(process.args, process.returncode, stdout)
    Path(prefix + '.log').write_text(result.stdout)
    if stalled:
        raise SystemExit(f'FAIL: probe stopped after missing progress; see {prefix}-stall.json and {prefix}-stopped.json')
    if (result.returncode or 'PROBE COMPLETE:' not in result.stdout or
            'ERROR: AddressSanitizer' in result.stdout or 'SUMMARY: AddressSanitizer' in result.stdout):
        raise SystemExit(f'FAIL: unexpected runtime/debugger stop; see {prefix}.log')
    report = json.loads(Path(prefix + '.json').read_text())
    if args.suite_scenario=='menu-matrix':
        print('Menu stages complete; native exit='+str(report['native_exit_code']))
        print(f'Evidence: {prefix}.json, {prefix}.log, {prefix}-journey.json')
        raise SystemExit(0)
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
