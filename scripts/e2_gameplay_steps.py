"""Bounded gameplay journeys executed inside GDB by probe-e2-player-motion.py.

All game changes go through SDL input. Actor positions, actions, health, resource
identity, clocks and RNG are observation-only. There are no saved-state shortcuts.
"""
from contextlib import contextmanager, nullcontext
import json
import copy
import math
import struct
from pathlib import Path
import time

import gdb

WORKSHOP = [
    (9736,-16910),(8936,-16518),(8260,-16259),(7554,-15990),
    (7170,-15558),(6878,-14734),(6637,-14338),(6267,-14015),
    (5486,-13551),(4671,-13485),(4023,-13434),(3269,-13375),
    (2796,-13337),(2314,-12892),(1836,-12592),(1970,-11896),
    (2154,-11361),(2350,-10889),
]
SWORD = [(2007,-10465),(1555,-10499),(833,-10493),(378,-10244),
         (-125,-9845),(-789,-9781),(-1278,-9756),(-837,-10021),(-871,-10006)]
POTION = [(2000,-11100),(1350,-11250),(700,-11480),(300,-11580)]


def potion_failure(potion):
    """Judge the naturally selected outcome; branch coverage is informational."""
    # FUN_00451880 consumes (short)param_2. Its upper word is not an action ID.
    actions={action & 0xffff for action in potion['actions']}
    branches={156:'healing',183:'poison',157:'invisibility',1803:'noop'}
    selected={identity for identity in potion['scripts'] if identity in branches}
    if 189 not in potion['scripts'] or len(selected)!=1:
        return 'Potion branch not uniquely observed'
    branch=branches[next(iter(selected))]
    if branch!=potion['branch']:
        return 'Potion observation disagrees with selected script'
    if 369 not in actions or not any(row['attached_to_joe'] for row in potion['samples']):
        return 'Potion pickup and drinking not observed'
    last=potion['samples'][-1]
    if last['attachment'] or last['representation']:
        return 'Consumed bottle remains attached or represented'
    timers={row['action'] for row in potion['timers']}
    if branch=='healing':
        if 391 not in actions or potion['after_health']!=100:
            return 'Healing action/maximum health not observed'
    elif branch=='poison':
        if 409 not in actions or 5 not in timers:
            return 'Poison action/death timer missing'
    elif branch=='invisibility':
        if 383 not in actions or 387 not in timers:
            return 'Invisibility action/fade timer missing'
    elif potion['before_health']!=potion['after_health'] or timers & {5,387}:
        return 'Unafflicted conditional no-op changed health/effects'
    return None


class Journey:
    def __init__(self, context, name, options):
        if not isinstance(options,dict) or any(key not in ('potion_wait','stability_batches','checks','observe_seconds','courtyard_stair_clearance','observe_door_health','displaced_door_start') for key in options):
            raise ValueError('Unsupported journey options')
        if type(options.get('courtyard_stair_clearance',False)) is not bool:
            raise ValueError('courtyard_stair_clearance must be a boolean input-path selector')
        if type(options.get('observe_door_health',False)) is not bool:
            raise ValueError('observe_door_health must be a boolean observer selector')
        if type(options.get('displaced_door_start',False)) is not bool:
            raise ValueError('displaced_door_start must be a boolean input-path selector')
        if name=='shared':
            from e2_suite import SHARED_ROUTES
            allowed={check for checks in SHARED_ROUTES.values() for check in checks}
            checks=options.get('checks')
            if not isinstance(checks,list) or not checks or len(set(checks))!=len(checks) or any(check not in allowed for check in checks):
                raise ValueError('Invalid shared checkpoints')
        for key,low,high in (('potion_wait',0,1000),('stability_batches',1,60),('observe_seconds',0,120)):
            if key in options and (type(options[key]) is not int or not low<=options[key]<=high):
                raise ValueError('Invalid bounded option '+key)
        self.c, self.name, self.options = context, name, options
        self.value, self.field = context['value'], context['field']
        self.actor, self.prefix = context['actor'], context['prefix']
        self.held, self.updates, self.phases, self.inputs = {}, 0, [], []
        from e2_population_profile import observe
        self.details = dict(population=observe(self.prefix,'journey-start'),logos=context.get('startup_logos',[]))
        self.checkpoints = []
        self.checkpoint_stack = []
        self.local = set()
        self.complete = False
        self.health_watches = []
        self.save()

    def save(self):
        target = Path(self.prefix + '-journey.json')
        report = dict(schema='e2suite.journey.1', scenario=self.name,
                      phases=self.phases, checkpoints=self.checkpoints, inputs=self.inputs, updates=self.updates,
                      details=self.details, complete=self.complete)
        temporary = target.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(report, indent=2)+'\n')
        temporary.replace(target)

    @contextmanager
    def checkpoint(self, name):
        started=time.monotonic()
        row=dict(name=name,status='RUNNING',phase_start=len(self.phases),started_monotonic=started,
                 parent=self.checkpoint_stack[-1] if self.checkpoint_stack else None)
        self.checkpoints.append(row)
        self.checkpoint_stack.append(name)
        self.save()
        try:
            yield
            row['status']='PASS'
            self.local.add(name)
        except BaseException as error:
            row.update(status='FAIL',reason=str(error) or type(error).__name__)
            raise
        finally:
            row.update(phase_end=len(self.phases),seconds=time.monotonic()-started,
                       details=copy.deepcopy(self.details))
            self.checkpoint_stack.pop()
            self.save()

    def require(self, condition, message):
        if not condition:
            raise gdb.GdbError(message)

    def alive(self):
        self.require(self.value('DAT_0047a470') == self.actor, 'Joe identity changed')
        self.require(self.field(0xec) > 0 and self.field(0x82) not in (5,8,11),
                     'Joe died during gameplay')
        self.require(self.value('_DAT_00643650') == 0, 'Unexpected modal requester')

    @contextmanager
    def phase(self, name, observe=True):
        row = dict(name=name, status='RUNNING', update=self.updates)
        self.phases.append(row)
        self.complete=False
        self.save()
        print('[ PHASE    ] '+name, flush=True)
        try:
            self.c['set_phase_title'](name)
            yield
            if observe:
                self.alive()
                self.c['checkpoint'](name)
                from e2_population_profile import observe as observe_population
                self.details['population']=observe_population(self.prefix,name)
            row['status'] = 'PASS'
            if not observe:self.complete=True
        except Exception as error:
            row.update(status='FAIL', reason=str(error))
            try:
                self.c['checkpoint']('failure')
                gdb.execute('thread apply all bt')
                gdb.execute('info registers')
            except gdb.error:
                pass
            raise
        finally:
            row['end_update'] = self.updates
            self.save()

    def advance(self, count):
        self.require(0 <= count <= 6000 and self.updates+count <= 30000,
                     'Journey exceeded its update bound')
        self.c['advance'](count)
        self.updates += count

    def key(self, vk, down, save=True):
        if self.held.get(vk, False) == down:
            return
        if vk == 32:
            gdb.execute('set $suite_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))', to_string=True)
            for member, number in [('type',0x300 if down else 0x301),('down',int(down)),
                                   ('key',32),('scancode',44)]:
                gdb.execute(f'set $suite_event->key.{member}={number}', to_string=True)
            gdb.execute('set $suite_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)', to_string=True)
            self.require(self.value('SDL_PushEvent($suite_event)') == 1, 'SDL Space failed')
            gdb.execute('call (void)free($suite_event)', to_string=True)
            gdb.execute('call e2r_poll_host_events("suite-space")', to_string=True)
        else:
            self.c['key'](vk, down)
        self.held[vk] = down
        event=dict(update=self.updates,key=vk,down=down)
        self.inputs.append(event)
        with Path(self.prefix+'-inputs.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
        if save:self.save()

    def release(self):
        for vk in list(self.held):
            self.key(vk, False)

    def position(self, actor=None):
        pointer = self.actor if actor is None else actor
        return [self.value(f'*(short*)({pointer}+{offset})') for offset in (0x84,0x86,0x88)]

    def actor_by_id(self, identity):
        actor = self.value(f'*(unsigned int*)(0x630b60+{identity}*4)')
        self.require(actor and self.value(f'*(short*){actor}') == identity,
                     f'Original actor {identity} absent or misidentified')
        return actor

    def camera(self):
        return self.c['observe_camera']()

    def walk(self, points, tolerance=160, attempts=240, on_waypoint=None):
        for index, (x,z) in enumerate(points):
            for _ in range(attempts):
                self.alive()
                position = self.position()
                distance = math.hypot(x-position[0], z-position[2])
                if distance < tolerance:
                    break
                angle = int(math.atan2(x-position[0], z-position[2])*65536/(2*math.pi))
                difference = (angle-self.field(0x92)+32768)%65536-32768
                self.key(0x25, difference < -800)
                self.key(0x27, difference > 800)
                self.key(0x26, abs(difference) < 5000)
                self.advance(1 if abs(difference)>800 or distance<450 else 3)
            else:
                # The last permitted update can itself enter the waypoint radius.
                position=self.position()
                if math.hypot(x-position[0],z-position[2])>=tolerance:
                    raise gdb.GdbError(f'Traversal missed waypoint {index}: ({x},{z}); actual {position}')
            if on_waypoint:on_waypoint(index)
        self.release()
        self.advance(8)

    def face(self, actor, threshold=400):
        for _ in range(180):
            target, position = self.position(actor), self.position()
            angle = int(math.atan2(target[0]-position[0],target[2]-position[2])*65536/(2*math.pi))
            difference = (angle-self.field(0x92)+32768)%65536-32768
            if abs(difference) <= threshold:
                break
            self.key(0x25, difference < 0)
            self.key(0x27, difference > 0)
            self.advance(1)
        else:
            raise gdb.GdbError('Could not face interaction target')
        self.release()

    def movement(self):
        with self.phase('movement.turn-and-release'):
            before = self.field(0x92)
            self.key(0x25,True); self.advance(30)
            self.key(0x25,False); self.advance(120)
            self.require(self.field(0x92) != before, 'Left input did not turn Joe')
            settled = self.field(0x92)
            self.advance(60)
            self.require(self.field(0x92) == settled, 'Turning continued after settling')
            before=self.field(0x92)
            self.key(0x27,True);self.advance(30);self.key(0x27,False);self.advance(120)
            self.require(self.field(0x92)!=before,'Right input did not turn Joe')
            for vk in (0x10,0x11,0x12):
                self.key(vk,True); self.advance(1); self.key(vk,False)
            self.advance(3)
            self.require(all(self.value(symbol)==0 for symbol in
                             ('DAT_00636846','DAT_00636852','DAT_0063684a')), 'Modifier stayed held')
        with self.phase('movement.forward-backward'):
            for vk in (0x26,0x28):
                before = self.position()
                self.key(vk,True); self.advance(60); self.key(vk,False); self.advance(120)
                self.require(self.position() != before, f'Input {vk} produced no displacement')
            state = self.c['snapshot']('movement-released')
            self.require(not any(state['held_keys'].values()), 'Arrow remained held')
            position = self.position()
            self.advance(90)
            self.require(self.position() == position, 'Released movement did not settle')

    def courtyard(self):
        route=json.loads((Path(__file__).parent/'scenarios/courtyard-waypoints.json').read_text())
        self.require(route.get('schema')=='e2suite.courtyard-waypoints.1','Unsupported courtyard route')
        self.details['courtyard']=dict(source=route['source'],outward=[],returning=[])
        def follow(leg):
            def walk_rows(rows):
                def observe(index):
                    observation=dict(snapshot=rows[index]['snapshot'],camera=self.camera(),position=self.position())
                    self.details['courtyard'][leg].append(observation)
                    self.save()
                # Keep walking between samples, with normal actor-radius guidance.
                self.walk([(row['position'][0],row['position'][2]) for row in rows],on_waypoint=observe)
            rows=route[leg]
            if leg=='returning':
                clearance=route['stair_clearance']
                prefix=[row for row in rows if row['snapshot']<clearance['gate_snapshot']]
                walk_rows(prefix);rows=rows[len(prefix):]
                guard=self.value(f'*(unsigned int*)(0x630b60+{clearance["actor"]}*4)')
                position=self.position(guard) if guard else None
                occupied=position is not None and math.hypot(position[0]-clearance['region'][0],
                                                           position[2]-clearance['region'][1])<clearance['radius']
                diagnostic=self.options.get('courtyard_stair_clearance',False)
                self.details['courtyard']['stair_clearance']=dict(actor=clearance['actor'],position=position,
                    occupied=occupied,diagnostic=diagnostic,used=occupied or diagnostic)
                if occupied or diagnostic:rows=[dict(snapshot=None,position=[x,0,z]) for x,z in clearance['waypoints']]
            walk_rows(rows)
            return self.position()
        if self.camera()!=175 or self.field(0x86)!=3328:
            with self.phase('traversal.pedestal-approach'):
                start=route['outward'][0]['position'];position=self.position()
                self.require(math.hypot(position[0]-start[0],position[2]-start[2])<2500,
                             'Movement left Joe outside the bounded pedestal approach')
                self.details['courtyard']['approach']=dict(camera=self.camera(),position=position)
                # Movement assertions can finish on the steps. Walk around the
                # same live obstruction and back up; never restore actor state.
                self.walk(route['stair_clearance']['waypoints'])
        with self.phase('traversal.courtyard-outward'):
            self.require(self.camera()==175 and self.field(0x86)==3328,
                         'Expected starting pedestal camera 175 / floor 3328')
            position=follow('outward')
            self.require(any(row['camera']==166 for row in self.details['courtyard']['outward']),
                         'Recorded route did not cross camera 166')
            self.require(self.camera()==125 and position[1]==4096,
                         'Did not reach central courtyard camera 125 / floor 4096')
        with self.phase('traversal.courtyard-return'):
            follow('returning')
            self.release(); self.advance(90)
            self.require(self.camera()==175 and self.field(0x86)==3328,
                         'Did not return to camera 175 / floor 3328')
            start=route['outward'][0]['position']
            position=self.position()
            self.require(math.hypot(position[0]-start[0],position[2]-start[2])<500,
                         'Return stopped outside the pedestal starting area')

    def workshop_corridor(self,navigator):
        points=[[x,3328 if i==0 else 3840 if i==1 else 4096,z]
                for i,(x,z) in enumerate(WORKSHOP)]
        position=self.position()
        candidates=[i for i,p in enumerate(points) if abs(p[1]-position[1])<=300]
        self.require(bool(candidates),'No observed floor connects to the workshop corridor')
        start=min(candidates,key=lambda i:math.hypot(points[i][0]-position[0],points[i][2]-position[2]))
        join_distance=math.hypot(points[start][0]-position[0],points[start][2]-position[2])
        self.details['workshop_entry']=dict(position=position,node=start,distance=join_distance,
            policy='bounded local corridor join; live scene-floor plan beyond local bound',
            scene_join=join_distance>=4000)
        self.save()
        if join_distance>=4000:
            navigator.navigate(self.scene_map(),points[start])
        navigator.follow_route(points[start:],'session_20261024_115718_697 workshop samples')

    def workshop(self):
        with self.phase('traversal.workshop'):
            navigator=self.navigator('reach_workshop',(3717,),fixed=3717)
            self.workshop_corridor(navigator)
            # Prop clearance is guidance; actual pickup retains its tighter gate.
            navigator.follow_route([[x,4096,z] for x,z in SWORD],
                                   'session_20261024_115718_697 workshop prop corridor',tolerance=260)
            self.require(self.camera()==347, 'Workshop traversal did not reach camera 347')
            for identity in (3717,537,980):
                self.actor_by_id(identity)
            if self.options.get('observe_door_health') and not self.health_watches:
                self.observe_door_health()

    def observe_door_health(self):
        journey=self
        target=self.actor_by_id(980)
        rows=self.details.setdefault('door_health_observations',[])
        class Health(gdb.Breakpoint):
            def stop(self):
                if len(rows)<64:
                    row=dict(identity=980,health=journey.value(f'*(short*)({target}+0xec)'),
                        update=journey.updates,phase=journey.phases[-1]['name'],
                        player=journey.position(),equipment=journey.field(0xf0),
                        stack=gdb.execute('bt 16',to_string=True))
                    rows.append(row)
                    with Path(journey.prefix+'-door-health.jsonl').open('a') as stream:
                        stream.write(json.dumps(row)+'\n')
                    journey.save()
                return False
        self.health_watches.append(Health(f'*(short*)({target}+0xec)',type=gdb.BP_WATCHPOINT,
                                         wp_class=gdb.WP_WRITE,internal=True))

    def sword(self, traverse=True):
        if traverse:
            self.workshop()
        with self.phase('interaction.sword-pickup'):
            sword = self.actor_by_id(3717)
            original = self.position(sword)
            # Original 0x42dc9c selects within Joe's radius of a point one
            # radius ahead. Leave steering/rounding clearance inside 2R.
            radius=self.field(0x9a)
            self.require(radius>64,'Invalid original pickup radius')
            reach=radius*2-64
            navigator=self.navigator('reach_sword',(3717,),fixed=3717,reach=reach)
            if not self.value(f'*(unsigned int*)({sword}+0x11e)'):
                navigator.follow_route([original],'original sword scene position; pickup eligibility pending',tolerance=reach)
            navigator.await_actor(3717)
            navigator.approach()
            self.face(sword)
            self.advance(8); self.key(32,True); self.advance(12); self.key(32,False)
            self.advance(150)
            node = self.value(f'*(unsigned int*)({sword}+0xf2)')
            self.require(node and self.value(f'*(unsigned int*)({node}+0x22)')==self.actor,
                         'Sword not attached to Joe')
            self.require(self.value(f'*(unsigned int*)({node}+0x13a)')==sword,
                         'Sword attachment is not reciprocal')
            self.require(self.field(0xf0)==3, 'Sword not equipped')
        with self.phase('interaction.sword-follows-movement'):
            before, player = self.position(sword), self.position()
            self.key(0x28,True); self.advance(30); self.key(0x28,False); self.advance(90)
            self.require(self.position()!=player, 'Cannot move after Space release')
            self.require(self.position(sword)!=before and self.position(sword)!=original,
                         'Sword remains at its previous world position')
            self.require(self.value(f'*(unsigned int*)({sword}+0xf2)')==node,
                         'Movement lost sword attachment')
            self.details['sword'] = dict(identity=3717, position=self.position(sword))

    def attacks(self):
        if self.name=='enemy' or 'Combat.KillSmith' in self.options.get('checks',[]) or self.options.get('displaced_door_start'):
            self.observe_smith_health()
        for index,(name,vk) in enumerate((('up',0x26),('left',0x25),('right',0x27),('down',0x28))):
            with self.phase('combat.attack-'+name):
                self.key(0x11,True); self.key(vk,True)
                for _ in range(12):
                    self.advance(30)
                    slot = self.field(0x96)
                    if 0xb8<=slot<=0xd3 and (slot-0xb8)%4==index:
                        break
                else:
                    raise gdb.GdbError('Requested attack did not start: '+name)
                self.release(); self.advance(90)

    def unarmed(self):
        with self.phase('combat.unarmed-ready'):
            self.require(self.field(0xf0)==0, 'Joe must be unarmed')
            representation=self.field(0x11e,'unsigned int')
            self.require(representation, 'Unarmed representation absent')
            # Original 0x429c22..0x429c9c selects six idle categories, not only
            # actions 11/12. Read the signed slot at rep+0x26+category*2.
            idle_actions=[self.value(f'*(short*)({representation}+0x26+{i}*2)') for i in range(6)]
            for _ in range(1200):
                action=self.field(0xa6,'unsigned int')
                if action and self.value(f'*(short*){action}') in idle_actions:break
                self.advance(1)
            else:raise gdb.GdbError('Unarmed idle not reached')
            self.details['unarmed_ready']=dict(idle_actions=idle_actions,action=self.value(f'*(short*){action}'))
        samples=[]
        for advanced in (False,True):
            for index,(name,vk) in enumerate((('up',0x26),('left',0x25),('right',0x27),('down',0x28))):
                with self.phase('combat.unarmed-'+('advanced-' if advanced else 'basic-')+name):
                    self.key(0x11,True)
                    if advanced:self.key(0x12,True)
                    self.key(vk,True)
                    low,high=(0xcc,0xd3) if advanced else (0xb8,0xc3)
                    for _ in range(24):
                        self.advance(15)
                        slot=self.field(0x96)
                        if low<=slot<=high and (slot-low)%4==index:break
                    else:raise gdb.GdbError('Unarmed attack did not start: '+name)
                    action=self.field(0xa6,'unsigned int')
                    self.require(action and self.field(0xf0)==0, 'Unarmed attack lost its action/equipment contract')
                    representation=self.field(0x11e,'unsigned int')
                    expected=self.value(f'*(short*)({representation}+2+{slot}*2)')
                    self.require(self.value(f'*(short*){action}')==expected,
                                 'Selected unarmed animation did not become the live action')
                    samples.append(dict(advanced=advanced,direction=name,slot=slot,
                        action=self.value(f'*(short*){action}'),expected_action=expected,progress=self.field(0xac)))
                    self.details['unarmed_attacks']=samples
                    self.release();self.advance(120)
        with self.phase('combat.unarmed-release-and-move'):
            self.require(all(self.value(symbol)==0 for symbol in ('DAT_00636852','DAT_0063684a')),
                         'Unarmed attack modifier remained held')
            before=self.position()
            for vk in (0x26,0x28):
                self.key(vk,True);self.advance(45);self.release();self.advance(120)
                if self.position()!=before:break
            self.require(self.position()!=before, 'Movement did not resume after unarmed attacks')

    def unarmed_contact(self, traverse=True):
        if traverse:self.workshop()
        navigator=self.navigator('damage_enemy_unarmed',(602,),fixed=602,reach=420)
        with self.checkpoint('setup.UnarmedEncounter') if self.name=='shared' else nullcontext():
            with self.phase('traversal.unarmed-contact'):
                self.require(self.field(0xf0)==0, 'Contact test must not equip a sword')
                scene_target=self.actor_by_id(602)
                if not self.value(f'*(unsigned int*)({scene_target}+0x11e)'):
                    navigator.follow_route([self.position(scene_target)],
                        'original blaksmit child 602 scene position; opponent eligibility pending',tolerance=320)
                navigator.await_actor(602)
                navigator.approach()
                target=self.actor_by_id(602)
        with self.phase('combat.unarmed-contact'):
            before=self.value(f'*(short*)({target}+0xec)')
            self.require(before>0, 'Unarmed target already dead')
            samples=[]
            self.details['unarmed_contact']=dict(actor=602,before=before,samples=samples)
            # The smith moves during combat. Follow live positions between bouts;
            # holding one heading for the whole encounter can punch empty space.
            for _ in range(12):
                navigator.approach()
                self.require(self.actor_by_id(602)==target,'Unarmed target instance changed')
                self.face(target)
                self.key(0x11,True);self.key(0x26,True);self.advance(60)
                self.release();self.advance(45)
                samples.append(dict(health=self.value(f'*(short*)({target}+0xec)'),
                    player=self.position(),target=self.position(target),heading=self.field(0x92)))
                self.save()
                if samples[-1]['health']<before:break
            self.release();self.advance(120)
            self.details['unarmed_contact']=dict(actor=602,before=before,samples=samples)
            self.require(samples[-1]['health']<before and self.field(0xf0)==0,
                         'Unarmed strikes did not cause observed enemy damage')

    def observe_smith_health(self):
        if 'smith_melee' in self.details:return
        journey=self
        target=self.actor_by_id(602)
        trace=dict(pointer=target,before=self.value(f'*(short*)({target}+0xec)'),hits=[],truncated=False)
        self.details['smith_melee']=trace
        previous=trace['before']
        class Health(gdb.Breakpoint):
            def stop(self):
                nonlocal previous
                health=journey.value(f'*(short*)({target}+0xec)')
                attacker=None;frames=[];frame=gdb.newest_frame()
                while frame and len(frames)<16:
                    name=frame.name();frames.append(name)
                    if name=='FUN_0042efdc':
                        node=int(frame.read_var('node'))
                        owner=journey.value(f'*(unsigned int*)({node}+0x22)')
                        attacker=journey.value(f'*(short*){owner}')
                    frame=frame.older()
                if len(trace['hits'])<64:
                    row=dict(before=previous,health=health,attacker=attacker,stack=frames,
                        update=journey.updates,phase=journey.phases[-1]['name'])
                    trace['hits'].append(row)
                    with Path(journey.prefix+'-smith-health.jsonl').open('a') as stream:
                        stream.write(json.dumps(row)+'\n')
                else:trace['truncated']=True
                previous=health
                journey.save()
                return False
        self.health_watches.append(Health(f'*(short*)({target}+0xec)',type=gdb.BP_WATCHPOINT,
                                         wp_class=gdb.WP_WRITE,internal=True))
        self.save()

    def displaced_door_start(self):
        with self.phase('traversal.door-displaced-start'):
            # Joe's observed post-smith position in run_20261027_160429_746159.
            # Reach it with real input; never restore coordinates, RNG or actors.
            goal=[4790,4096,-11985]
            before=self.position()
            navigator=self.navigator('reach_displaced_door_start',(980,))
            navigator.navigate(self.scene_map(),goal,avoid_actors=True)
            self.release()
            actual=self.position()
            self.details['displaced_door_start']=dict(before=before,goal=goal,actual=actual,
                source='run_20261027_160429_746159 debug post-smith observation')
            self.save()
            self.require(actual[1]==goal[1] and math.hypot(actual[0]-goal[0],actual[2]-goal[2])<240,
                         'Did not reach the required displaced door start')

    def strike(self, identity, death=False):
        target = self.actor_by_id(identity)
        navigator = self.navigator('kill_enemy',(identity,),fixed=identity,reach=380) if death else None
        trace=self.details.get('smith_melee',{}) if identity==602 and death else {}
        def observed_kill():
            return (trace.get('pointer')==target and trace.get('before',0)>0 and
                    not trace.get('truncated',False) and any(
                        hit['before']>0 and hit['health']<=0 and hit['attacker']==0 and
                        'FUN_0042efdc' in hit['stack'] for hit in trace.get('hits',[])))
        def completed(observation):
            actor=observation['actors'].get(identity)
            return actor and actor['pointer']==target and actor['health']<=0 and observed_kill()
        def finished():
            return observed_kill() and self.value(f'*(short*)({target}+0xec)')<=0
        prior_kill=finished()
        samples = []
        def sample():
            row = dict(health=self.value(f'*(short*)({target}+0xec)'),
                       state=self.value(f'*(short*)({target}+0x82)'),
                       representation=self.value(f'*(unsigned int*)({target}+0x11e)'),
                       player=self.position(),target=self.position(target),heading=self.field(0x92))
            samples.append(row)
            self.details['target'] = dict(identity=identity, samples=samples)
            self.save()
            return row
        with self.phase('traversal.strike-position'):
            if identity==980:
                # A retreating smith can leave Joe across the workshop. Plan
                # the connection before entering the audited local door route.
                navigator=self.navigator('reach_door_strike',(identity,),fixed=identity)
                entry=[-1800,self.position(target)[1],-9800]
                self.details['door_approach']=dict(before=self.position(),entry=entry)
                self.save()
                navigator.navigate(self.scene_map(),entry,avoid_actors=True)
                self.walk([(-1800,-9800),(-2200,-10100),(-2571,-10545)], tolerance=100)
                self.details['door_approach']['after']=self.position()
            elif not prior_kill:
                pos = self.position(target)
                self.walk([(pos[0],pos[2])], tolerance=380)
                if not finished():
                    navigator.await_actor(identity)
                    navigator.approach(completed=completed)
            if not finished():self.face(target)
        with self.phase('combat.kill-enemy' if death else 'interaction.break-door'):
            initial = sample()
            starting_health=trace['before'] if finished() else initial['health']
            self.require(starting_health>0 and (initial['representation']!=0 or finished()), 'Target already inactive')
            if prior_kill:trace['satisfied_during_prerequisites']=True
            if death:
                # A live smith can retreat after a hit. Track the same actor
                # between bouts rather than striking one stale heading.
                current=initial
                for _ in range(20):
                    if current['state']==11:break
                    if current['health']>0:
                        navigator.approach(completed=completed)
                        self.require(self.actor_by_id(identity)==target,'Strike target instance changed')
                        if not finished():self.face(target)
                        if not finished():
                            self.key(0x11,True);self.key(0x26,True)
                    self.advance(60);self.alive();self.release()
                    current=sample()
            else:
                self.key(0x11,True); self.key(0x26,True)
                for _ in range(40):
                    self.advance(30); self.alive()
                    if sample()['state']==11:
                        break
            self.release(); self.advance(150)
            final = sample()
            self.require(final['health']<starting_health and final['health']<=0 and
                         final['state']==11 and final['representation']==0,
                         'Strikes did not finish damage/death/deactivation')
        if not death:
            with self.phase('traversal.door-passage'):
                target_pos, player = self.position(target), self.position()
                dx,dz=target_pos[0]-player[0],target_pos[2]-player[2]
                self.require(math.hypot(dx,dz)>0, 'Invalid door approach')
                self.require(identity==980,'No audited passage guidance for this door')
                # Original cyd_dor8/kdorr placement; the retained native route
                # crosses its opening toward negative Z (347 -> 164).
                # A tight gate prevents a local detour from bypassing the door.
                navigator=self.navigator('cross_destroyed_door',(identity,),fixed=identity)
                result=navigator.cross_opening(identity,target_pos,(0,-1))
                self.release();self.advance(30)
                pos=self.position()
                beyond=((pos[0]-target_pos[0])*dx+(pos[2]-target_pos[2])*dz)/math.hypot(dx,dz)
                result.update(before=player,after=pos,distance_beyond_door=beyond,camera=self.camera())
                self.details['door_passage']=result
                self.save()
                self.require(beyond>100,'Joe did not pass through the broken door')
                self.require(pos[1]==target_pos[1],'Door passage finished on a different floor')

    def navigator(self, goal, allowed, fixed=None, reach=240,updates=2400):
        from e2_navigation import Navigator, Limits
        journey=self
        rows=self.details.setdefault('navigation',[])
        class Bridge:
            def __init__(self):self.last_saved=-30
            def observe(self):
                journey.alive()
                inferior=gdb.selected_inferior()
                def read(pointer,active):
                    data=bytes(inferior.read_memory(pointer,0x194))
                    short=lambda offset:struct.unpack_from('<h',data,offset)[0]
                    word=lambda offset:struct.unpack_from('<I',data,offset)[0]
                    identity=short(0)
                    action=word(0xa6);rep=word(0x11e)
                    return dict(identity=identity,pointer=pointer,active=active,
                        action_id=struct.unpack('<h',inferior.read_memory(action,2))[0] if action else None,
                        attack_slots=list(struct.unpack('<6h',inferior.read_memory(rep+2+109*2,12))) if rep else [],
                        identity_valid=0<=identity<5000 and journey.value(f'*(unsigned int*)(0x630b60+{identity}*4)')==pointer,
                        position=[short(offset) for offset in (0x84,0x86,0x88)],
                        heading=short(0x92),health=short(0xec),state=short(0x82),
                        motion_node=word(0x1e),ai_readiness=short(0xea),
                        representation=word(0x11e),action=word(0xa6),progress=short(0xac),
                        representation_id=struct.unpack('<h',inferior.read_memory(rep,2))[0] if rep else None,
                        attachment=word(0xf2),flags=word(2),radius=short(0x9a))
                actors={};cursor=journey.value('_DAT_0063726c');seen=set()
                while cursor:
                    journey.require(cursor not in seen and len(seen)<256,'Navigation actor-list cycle/bound')
                    seen.add(cursor)
                    row=read(cursor,True)
                    actors[row['identity']]=row
                    cursor=journey.value(f'*(unsigned int*)({cursor}+0x4c)')
                return dict(player=read(journey.actor,journey.actor in seen),
                            actors=actors,camera=journey.camera())
            def apply(self, keys, updates):
                for vk in (0x10,0x11,0x12,0x25,0x26,0x27,0x28,32):
                    journey.key(vk,vk in keys,save=False)
                journey.advance(updates)
            def release(self):journey.release()
            def record(self,row):
                rows.append(row)
                path=Path(journey.prefix+'-navigation.jsonl')
                with path.open('a') as stream:stream.write(json.dumps(row)+'\n')
                journey.details['navigation_evidence']=dict(events=path.name,
                    inputs=Path(journey.prefix+'-inputs.jsonl').name,publication_updates=30)
                if row.get('outcome') or row.get('action') not in ('steer','released observation') or row['updates']-self.last_saved>=30:
                    journey.save();self.last_saved=row['updates']
        host_allowance=3 if self.c.get('watch_mode',False) else 1
        return Navigator(Bridge(),goal,allowed,fixed,Limits(updates=updates,reach=reach,seconds=55*host_allowance))

    def encounter_corridor(self,navigator):
        route=json.loads((Path(__file__).parent/'scenarios/courtyard-waypoints.json').read_text())
        points=[row['position'] for row in route['outward'][:10]]
        position=self.position()
        candidates=[i for i,p in enumerate(points) if abs(p[1]-position[1])<=300]
        self.require(bool(candidates),'No observed floor connects to the encounter corridor')
        start=min(candidates,key=lambda i:(abs(points[i][1]-position[1]),
            math.hypot(points[i][0]-position[0],points[i][2]-position[2])))
        separation=math.hypot(points[start][0]-position[0],points[start][2]-position[2])
        self.details['encounter_entry']=dict(position=position,node=start,distance=separation,
                                             scene_join=separation>=1800)
        self.save()
        if separation>=1800:
            navigator.navigate(self.scene_map(),points[start])
        navigator.follow_route(points[start:],route['source'],stop_on_encounter=True)

    def damage(self):
        # Audited original St_gobsc actors (see check-e2-test-population.py).
        # Terrain actors and presentation labels do not confer attack eligibility.
        eligible=(284,293)
        hits=[]
        self.details['enemy_hits']=hits
        melee=dict(attempts=0,samples=[],by_actor={})
        self.details['enemy_melee']=melee
        journey=self
        class Melee(gdb.Breakpoint):
            def stop(self):
                node=journey.value('node')
                owner=journey.value(f'*(unsigned int*)({node}+0x22)')
                identity=journey.value(f'*(short*){owner}')
                if identity in eligible:
                    melee['attempts']+=1
                    opponent=melee['by_actor'].setdefault(str(identity),dict(attempts=0,samples=[]))
                    opponent['attempts']+=1
                    strike=[journey.value(f'*(short*)({node}+{offset})') for offset in (0x18,0x1a,0x1c)]
                    opponent['samples'].append(dict(strike=strike,player=journey.position(),
                        opponent=journey.position(owner),update=journey.updates))
                    if len(opponent['samples'])>32:opponent['samples'].pop(0)
                    if len(melee['samples'])<64:
                        strike=[journey.value(f'*(short*)({node}+{offset})') for offset in (0x18,0x1a,0x1c)]
                        melee['samples'].append(dict(node=node,owner=owner,strike=strike,
                            player=journey.position(),opponent=journey.position(owner),
                            heading=journey.value(f'*(short*)({owner}+0x92)'),update=journey.updates))
                return False
        class Health(gdb.Breakpoint):
            def stop(self):
                frames=[];attacker=None;frame=gdb.newest_frame()
                while frame and len(frames)<16:
                    name=frame.name();frames.append(name)
                    if name=='FUN_0042efdc':
                        node=int(frame.read_var('node'))
                        owner=journey.value(f'*(unsigned int*)({node}+0x22)')
                        attacker=journey.value(f'*(short*){owner}')
                    frame=frame.older()
                hits.append(dict(health=journey.field(0xec),attacker=attacker,stack=frames,
                                 position=journey.position(),update=journey.updates))
                journey.save()
                return False
        watch=Health(f'*(short*)({self.actor}+0xec)',type=gdb.BP_WATCHPOINT,wp_class=gdb.WP_WRITE,internal=True)
        contact=Melee('FUN_0042efdc',internal=True)
        before=self.field(0xec)
        navigator=self.navigator('receive_one_hit',eligible)
        try:
            with self.checkpoint('setup.ReceiveHitEncounter') if self.name=='shared' else nullcontext():
                with self.phase('navigation.receive-hit-approach'):
                    # Published courtyard samples connect the stairs to guard
                    # the audited guards' encounter region. The navigator rejects
                    # a guard on another ledge rather than guessing connectivity.
                    self.encounter_corridor(navigator)
                    navigator.approach(before,lambda identity:[hit for hit in hits
                        if hit['attacker']==identity and 0<hit['health']<before])
            with self.phase('combat.take-natural-damage'):
                after=navigator.receive(before,lambda identity:[hit for hit in hits
                    if hit['attacker']==identity and 0<hit['health']<before])
                self.require(0<after<before,'Eligible enemy did not cause surviving health loss')
                self.details['damage']=dict(before=before,after=after,target=navigator.target)
        finally:
            contact.delete()
            watch.delete()
            self.release()

    def potion(self, damaged=False):
        if damaged and 'Combat.TakeDamage' not in self.local:
            with self.checkpoint('setup.Combat.TakeDamage') if self.name=='shared' else nullcontext():
                self.damage()
                self.local.add('Combat.TakeDamage')
        with self.phase('traversal.potion'):
            navigator=self.navigator('reach_potion',(537,),fixed=537)
            self.workshop_corridor(navigator)
            potion=self.actor_by_id(537)
            navigator.navigate(self.scene_map(),self.position(potion),avoid_actors=True)
            self.face(potion,500)
            self.advance(20+self.options.get('potion_wait',0))
        scripts, actions, observations = [], [], []
        value=self.value
        class Script(gdb.Breakpoint):
            def stop(self):
                code=value('E2R_action_dispatch_node')
                if code:
                    identity=value(f'*(short*){code}')
                    if identity in (189,156,183,157,1803):
                        scripts.append(identity)
                return False
        class Action(gdb.Breakpoint):
            def stop(self):
                actions.append(value('param_2'))
                return False
        script=Script('FUN_0044f508',internal=True)
        action=Action('FUN_00451880',internal=True)
        before=self.field(0xec)
        try:
            with self.phase('interaction.drink-and-remove-bottle'):
                self.key(32,True); self.advance(12); self.key(32,False)
                for _ in range(30):
                    self.advance(15)
                    node=value(f'*(unsigned int*)({potion}+0xf2)')
                    observations.append(dict(health=self.field(0xec),
                        attachment=node,attached_to_joe=bool(node and
                            value(f'*(unsigned int*)({node}+0x22)')==self.actor and
                            value(f'*(unsigned int*)({node}+0x13a)')==potion),
                        representation=value(f'*(unsigned int*)({potion}+0x11e)')))
                branches={156:'healing',183:'poison',157:'invisibility',1803:'noop'}
                selected=[identity for identity in scripts if identity in branches]
                self.require(189 in scripts and len(set(selected))==1, 'Potion branch not uniquely observed')
                timers=[];cursor=self.field(0x17c,'unsigned int')
                while cursor and len(timers)<32:
                    self.require(cursor not in [t['address'] for t in timers], 'Potion timer list cycle')
                    timers.append(dict(address=cursor, action=value(f'*(short*){cursor}'),
                                       deadline=value(f'*(int*)({cursor}+2)')))
                    cursor=value(f'*(unsigned int*)({cursor}+6)')
                branch=branches[selected[0]]
                self.details['potion']=dict(branch=branch, before_health=before,
                    after_health=self.field(0xec), actions=actions, timers=timers,
                    scripts=scripts, samples=observations,identity=537,
                    selection='original live RNG; no required outcome')
                self.save()
                failure=potion_failure(self.details['potion'])
                self.require(failure is None,failure)
        finally:
            script.delete();action.delete()
            self.release()

    def potion_then_sword(self):
        with self.checkpoint('setup.PotionSwordApproach') if self.name=='shared' else nullcontext():
            with self.phase('traversal.potion-to-sword'):
                navigator=self.navigator('reach_sword',(3717,),fixed=3717)
                # The bottle action can release Joe on either side of the
                # workshop props. Plan from that observed floor instead of
                # forcing every historical corridor point to be occupied.
                navigator.navigate(self.scene_map(),[SWORD[-1][0],4096,SWORD[-1][1]],avoid_actors=True)
        self.sword(traverse=False);self.attacks()
        with self.phase('interaction.bottle-remains-removed'):
            bottle=self.actor_by_id(537)
            self.require(self.value(f'*(unsigned int*)({bottle}+0xf2)')==0 and
                         self.value(f'*(unsigned int*)({bottle}+0x11e)')==0,
                         'Sword use restored the consumed bottle')

    def swimming(self,armed=False):
        with self.checkpoint('setup.WaterApproach') if self.name=='shared' else nullcontext():
            with self.phase('traversal.water'):
                scene=self.scene_map()
                goal=scene.region_goal(self.position(),543,7,5120,entry=True)
                self.details['water_approach']=dict(source='live scene-floor planner',before=self.position(),goal=goal)
                self.save()
                navigator=self.navigator('reach_water',(0,),updates=3200)
                navigator.navigate(scene,goal,water=True)
                self.require(self.camera()==543,'Water approach did not reach camera 543')
                self.details['water_approach'].update(after=self.position(),camera=self.camera())
        with self.phase('movement.swimming'):
            before=self.position()
            self.key(0x26,True)
            for _ in range(30):
                self.advance(15)
                rep=self.field(0x11e,'unsigned int')
                if rep and self.value(f'*(short*){rep}')==(10 if armed else 13) and self.position()!=before:
                    break
            self.release();self.advance(30)
            rep=self.field(0x11e,'unsigned int')
            self.require(rep and self.value(f'*(short*){rep}')==(10 if armed else 13) and self.position()!=before,
                         'Swimming representation and displacement not observed')

    def require_swimming(self,armed=False):
        self.alive()
        rep=self.field(0x11e,'unsigned int')
        self.require(rep and self.value(f'*(short*){rep}')==(10 if armed else 13) and
                     self.value('DAT_0047a7ec')==7 and self.field(0x86)==5120,
                     'Joe is not in the required swimming state')
        self.require(self.field(0xf0)==(3 if armed else 0),'Water checkpoint has the wrong equipment state')
        if armed:
            sword=self.actor_by_id(3717)
            node=self.value(f'*(unsigned int*)({sword}+0xf2)')
            self.require(node and self.value(f'*(unsigned int*)({node}+0x22)')==self.actor and
                         self.value(f'*(unsigned int*)({node}+0x13a)')==sword,'Swimming lost reciprocal sword attachment')
        return rep

    def ensure_water(self,armed=False):
        check='Movement.ArmedSwimming' if armed else 'Movement.Swimming'
        if check in self.local:return
        if armed and 'Interaction.SwordPickup' not in self.local:
            with self.checkpoint('setup.Interaction.SwordPickup'):
                self.sword(traverse='Traversal.Workshop' not in self.local)
        with self.checkpoint('setup.'+check):self.swimming(armed)
        self.local.add(check)

    def water_traversal(self,armed=False):
        self.require_swimming(armed)
        scene=self.scene_map();start=self.position();start_camera=self.camera()
        self.require(start_camera>0,'Swimming traversal has no actual starting camera')
        target_camera=543 if start_camera==545 else 545
        goal=scene.region_goal(start,target_camera,7,5120,minimum_distance=1200)
        return_goal=scene.region_goal(start,start_camera,7,5120)
        navigator=self.navigator('traverse_water',(0,))
        with self.phase('traversal.water-outward'):
            navigator.navigate(scene,goal,water=True,swimming_representation=10 if armed else 13)
            self.require_swimming(armed)
            self.require(self.camera()==target_camera and math.hypot(self.position()[0]-start[0],self.position()[2]-start[2])>600,
                         'Water traversal did not cross into the other water camera with displacement')
        with self.phase('traversal.water-return'):
            navigator.navigate(scene,return_goal,water=True,swimming_representation=10 if armed else 13)
            self.release();self.advance(30);self.require_swimming(armed)
            self.require(self.camera()==start_camera,'Water traversal did not return to its starting water camera')
        self.details['water_traversal']=dict(start=start,goal=goal,return_goal=return_goal,after=self.position(),armed=armed,
                                           start_camera=start_camera,target_camera=target_camera)

    def water_combat(self,armed=False):
        try:
            samples=[]
            for index,(name,vk) in enumerate((('up',0x26),('left',0x25),('right',0x27),('down',0x28))):
                with self.phase('combat.swimming-'+name):
                    rep=self.require_swimming(armed)
                    self.key(0x11,True);self.key(vk,True)
                    for _ in range(24):
                        self.advance(15);slot=self.field(0x96)
                        if 0xb8<=slot<=0xc3 and (slot-0xb8)%4==index:break
                    else:raise gdb.GdbError('Swimming attack did not start: '+name)
                    action=self.field(0xa6,'unsigned int')
                    expected=self.value(f'*(short*)({rep}+2+{slot}*2)')
                    self.require(action and self.value(f'*(short*){action}')==expected and expected>=0,
                                 'Swimming attack did not use its original representation action')
                    self.require_swimming(armed)
                    samples.append(dict(direction=name,slot=slot,action=expected,position=self.position(),armed=armed))
                    self.details['water_combat']=samples
                    self.release();self.advance(120)
                    self.require_swimming(armed)
            with self.phase('combat.swimming-release-and-move'):
                before=self.position();self.key(0x26,True);self.advance(30);self.release();self.advance(30)
                self.require_swimming(armed)
                self.require(self.position()!=before and not any(self.held.values()),'Swimming controls did not resume after attacks')
        finally:
            self.release()

    def scene_map(self):
        from e2_scene_navigation import SceneMap, navigation_scripts
        inferior=gdb.selected_inferior()
        count=self.value('DAT_0047a77c');shift=self.value('DAT_0047a738')
        self.require(0<count<=65536 and 0<=shift<=7,'Invalid bounded scene grid')
        blobs=dict(grid=bytes(inferior.read_memory(0x684d68,32768)),
                   descriptors=bytes(inferior.read_memory(0x68cd68,count*12)),
                   flags=bytes(inferior.read_memory(0x636624,256)))
        policy=navigation_scripts((Path(self.c['game_data_root'])/'Code/ECSTATIC.FAN').read_bytes())
        scene=SceneMap(**blobs,shift=shift,policy=policy)
        folder=Path(self.prefix+'-scene-maps')/scene.identity;folder.mkdir(parents=True,exist_ok=True)
        for name,data in blobs.items():(folder/(name+'.bin')).write_bytes(data)
        (folder/'script-policy.json').write_text(json.dumps(policy,indent=2)+'\n')
        (folder/'map.json').write_text(json.dumps(dict(shift=shift,count=count,sha256=scene.identity),indent=2)+'\n')
        return scene

    def shared_step(self, name):
        def workshop():
            if 'Traversal.Workshop' not in self.local:
                with self.checkpoint('setup.Traversal.Workshop') if name!='Traversal.Workshop' else nullcontext():
                    self.workshop();self.local.add('Traversal.Workshop')
        def sword():
            workshop()
            if 'Interaction.SwordPickup' not in self.local:
                with self.checkpoint('setup.Interaction.SwordPickup') if name!='Interaction.SwordPickup' else nullcontext():
                    self.sword(traverse=False);self.local.add('Interaction.SwordPickup')
        def attacks():
            sword()
            if 'Combat.FourDirections' not in self.local:
                with self.checkpoint('setup.Combat.FourDirections') if name!='Combat.FourDirections' else nullcontext():
                    self.attacks();self.local.add('Combat.FourDirections')
        if name=='Movement.ControlsAndRelease':self.movement()
        elif name=='Combat.UnarmedDirections':self.unarmed()
        elif name=='Traversal.CourtyardReturn':self.courtyard()
        elif name=='Traversal.Workshop':workshop()
        elif name=='Combat.UnarmedContact':
            workshop();self.unarmed_contact(traverse=False)
        elif name=='Interaction.SwordPickup':sword()
        elif name=='Combat.FourDirections':attacks()
        elif name=='Combat.KillSmith':
            attacks();self.strike(602,death=True)
        elif name=='Interaction.DoorPassage':
            attacks();self.strike(980)
        elif name=='Interaction.DoorPassageDisplaced':
            if 'Movement.ControlsAndRelease' not in self.local:
                with self.checkpoint('setup.Movement.ControlsAndRelease'):self.movement()
            attacks()
            if 'Combat.KillSmith' not in self.local:
                with self.checkpoint('setup.Combat.KillSmith'):self.strike(602,death=True)
            self.displaced_door_start();self.strike(980)
        elif name=='Combat.TakeDamage':self.damage()
        elif name.startswith('Potion.Trial'):
            self.potion(damaged=name[-1] in 'CD')
        elif name=='Interaction.PotionThenSword':
            self.potion_then_sword()
        elif name=='Movement.Swimming':self.swimming();self.local.add('Movement.Swimming')
        elif name in ('Traversal.Water','Combat.SwimmingDirections'):
            self.ensure_water()
            if name=='Traversal.Water':self.water_traversal()
            else:self.water_combat()
        elif name in ('Movement.ArmedSwimming','Combat.ArmedSwimmingDirections','Traversal.ArmedWater'):
            self.ensure_water(True)
            if name=='Combat.ArmedSwimmingDirections':self.water_combat(True)
            elif name=='Traversal.ArmedWater':self.water_traversal(True)
        elif name=='Stability.MixedJourney':
            attacks()
            if 'Interaction.DoorPassage' not in self.local:
                with self.checkpoint('setup.Interaction.DoorPassage'):self.strike(980)
            with self.phase('stability.active-input'):
                for _ in range(self.options.get('stability_batches',24)):
                    self.key(0x25,True);self.advance(30);self.release()
                    self.key(0x26,True);self.advance(30);self.release()
                    self.key(0x28,True);self.advance(30);self.release()
                self.advance(300)
            with self.phase('stability.released-observation'):
                started=time.monotonic()
                while time.monotonic()-started<self.options.get('observe_seconds',60):
                    self.advance(30);self.alive();self.camera()
                self.details['observed_seconds']=time.monotonic()-started
                state=self.c['snapshot']('observed-released')
                self.require(not any(state['held_keys'].values()),'Observation left a key held')
        else:raise ValueError('Unknown shared checkpoint '+name)

    def startup(self):
        with self.phase('startup.released-player'):
            population=self.details['population']
            if population['profile']=='noncombat-opening':
                self.require(population['blocked_requests_mask'] & 3 == 3,
                             'Fixture did not intercept both original guard creation requests')
            self.require(self.field(0x82)==4 and self.field(0xec)==100,
                         'Startup did not produce healthy controllable Joe')
            self.require(self.camera()==175 and self.field(0x86)==3328,
                         'Startup did not reach the expected courtyard/floor')

    def run(self):
        if self.name=='shared':
            checks=self.options['checks']
            startup=next((name for name in checks if name.startswith('Startup.')),None)
            if startup:
                with self.checkpoint(startup):self.startup()
            else:
                with self.checkpoint('setup.Startup'):self.startup()
            for name in checks:
                if name.startswith('Startup.') or name=='Menus.CancelResumeQuit':continue
                with self.checkpoint(name):self.shared_step(name)
            with self.checkpoint('setup.ReleasedInput'):
                with self.phase('journey.released-input'):
                    self.release();self.advance(30);self.alive()
            self.save()
            return dict(scenario=self.name,phases=self.phases,details=self.details,
                        checkpoints=self.checkpoints,updates=self.updates,inputs=self.inputs)
        self.startup()
        name=self.name
        if name=='movement': self.movement()
        elif name=='courtyard': self.courtyard()
        elif name=='damage': self.damage()
        elif name=='unarmed': self.unarmed()
        elif name=='unarmed-contact': self.unarmed_contact()
        elif name in ('workshop','sword','attacks','enemy','door','stability'):
            if name=='door' and self.options.get('displaced_door_start'):self.movement()
            self.workshop()
            if name!='workshop': self.sword(traverse=False)
            if name in ('attacks','enemy','door','stability'): self.attacks()
            if name=='enemy': self.strike(602,death=True)
            if name=='door' and self.options.get('displaced_door_start'):
                self.strike(602,death=True);self.displaced_door_start()
            if name in ('door','stability'): self.strike(980)
            if name=='stability':
                with self.phase('stability.active-input'):
                    for _ in range(self.options.get('stability_batches',12)):
                        self.key(0x25,True);self.advance(30);self.release()
                        self.key(0x26,True);self.advance(30);self.release()
                        self.key(0x28,True);self.advance(30);self.release()
                    self.advance(300)
        elif name in ('potion','potion-damaged','potion-sword'):
            self.potion(damaged=name=='potion-damaged')
            if name=='potion-sword':
                self.potion_then_sword()
        elif name=='swimming': self.swimming()
        elif name in ('water-traversal','water-combat'):
            self.swimming()
            if name=='water-traversal':self.water_traversal()
            else:self.water_combat()
        elif name in ('armed-swimming','armed-water-traversal','armed-water-combat'):
            self.sword();self.swimming(True)
            if name=='armed-water-traversal':self.water_traversal(True)
            elif name=='armed-water-combat':self.water_combat(True)
        elif name not in ('startup','menus'): raise ValueError('Unknown journey '+name)
        self.release();self.advance(30)
        self.alive()
        self.complete=True
        self.save()
        return dict(scenario=name, phases=self.phases, details=self.details,
                    updates=self.updates, inputs=self.inputs)


def run(context, name, options):
    journey=Journey(context,name,options)
    context['suite_journey']=journey
    try:
        return journey.run()
    finally:
        for watch in journey.health_watches:watch.delete()
