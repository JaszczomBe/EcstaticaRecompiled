"""Bounded gameplay journeys executed inside GDB by probe-e2-player-motion.py.

All game changes go through SDL input. Actor positions, actions, health, resource
identity, clocks and RNG are observation-only. There are no saved-state shortcuts.
"""
from contextlib import contextmanager
import json
import math
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


class Journey:
    def __init__(self, context, name, options):
        if not isinstance(options,dict) or any(key not in ('potion_wait','stability_batches') for key in options):
            raise ValueError('Unsupported journey options')
        for key,low,high in (('potion_wait',0,1000),('stability_batches',1,60)):
            if key in options and (type(options[key]) is not int or not low<=options[key]<=high):
                raise ValueError('Invalid bounded option '+key)
        self.c, self.name, self.options = context, name, options
        self.value, self.field = context['value'], context['field']
        self.actor, self.prefix = context['actor'], context['prefix']
        self.held, self.updates, self.phases, self.inputs = {}, 0, [], []
        self.details = {}
        self.complete = False
        self.save()

    def save(self):
        target = Path(self.prefix + '-journey.json')
        report = dict(schema='e2suite.journey.1', scenario=self.name,
                      phases=self.phases, inputs=self.inputs, updates=self.updates,
                      details=self.details, complete=self.complete)
        temporary = target.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(report, indent=2)+'\n')
        temporary.replace(target)

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

    def key(self, vk, down):
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
        self.inputs.append(dict(update=self.updates, key=vk, down=down))
        self.save()

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

    def walk(self, points, tolerance=160, attempts=240):
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
        with self.phase('traversal.courtyard-outward'):
            self.require(self.camera()==175, 'Expected starting courtyard camera 175')
            crossed = False
            for vk, batches in ((0x26,4),(0x28,24)):
                self.key(vk,True)
                for _ in range(batches):
                    self.advance(30)
                    if self.camera()!=175:
                        crossed=True
                        break
                self.release(); self.advance(90)
                if crossed:
                    break
            self.require(self.camera()==166, 'Did not cross into camera 166')
            return_key = 0x28 if vk==0x26 else 0x26
        with self.phase('traversal.courtyard-return'):
            self.key(return_key,True)
            for _ in range(24):
                self.advance(30)
                if self.camera()==175 and self.field(0x86)==3328:
                    break
            self.release(); self.advance(90)
            self.require(self.camera()==175 and self.field(0x86)==3328,
                         'Did not return to camera 175 / floor 3328')

    def workshop(self):
        with self.phase('traversal.workshop'):
            self.walk(WORKSHOP)
            # These are guidance points around props, not exact-position assertions.
            # Allow one actor radius; pickup has its own tighter reach/attachment gate.
            self.walk(SWORD,tolerance=260)
            self.require(self.camera()==347, 'Workshop traversal did not reach camera 347')
            for identity in (3717,537,980):
                self.actor_by_id(identity)

    def sword(self, traverse=True):
        if traverse:
            self.workshop()
        with self.phase('interaction.sword-pickup'):
            sword = self.actor_by_id(3717)
            original = self.position(sword)
            self.walk([(original[0],original[2])], tolerance=220)
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

    def unarmed_contact(self):
        self.workshop()
        with self.phase('traversal.unarmed-contact'):
            self.require(self.field(0xf0)==0, 'Contact test must not equip a sword')
            target=self.actor_by_id(602)
            self.face(target)
        with self.phase('combat.unarmed-contact'):
            before=self.value(f'*(short*)({target}+0xec)')
            self.require(before>0, 'Unarmed target already dead')
            samples=[]
            self.details['unarmed_contact']=dict(actor=602,before=before,samples=samples)
            # The smith moves during combat. Follow live positions between bouts;
            # holding one heading for the whole encounter can punch empty space.
            for _ in range(12):
                for _ in range(20):
                    position,destination=self.position(),self.position(target)
                    if math.hypot(position[0]-destination[0],position[2]-destination[2])<200:break
                    self.face(target)
                    self.key(0x26,True);self.advance(3);self.release()
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

    def strike(self, identity, death=False):
        target = self.actor_by_id(identity)
        samples = []
        def sample():
            row = dict(health=self.value(f'*(short*)({target}+0xec)'),
                       state=self.value(f'*(short*)({target}+0x82)'),
                       representation=self.value(f'*(unsigned int*)({target}+0x11e)'))
            samples.append(row)
            self.details['target'] = dict(identity=identity, samples=samples)
            self.save()
            return row
        with self.phase('traversal.strike-position'):
            if identity==980:
                self.walk([(-1800,-9800),(-2200,-10100),(-2571,-10545)], tolerance=100)
            else:
                pos = self.position(target)
                self.walk([(pos[0],pos[2])], tolerance=380)
            self.face(target)
        with self.phase('combat.kill-enemy' if death else 'interaction.break-door'):
            initial = sample()
            self.require(initial['health']>0 and initial['representation']!=0, 'Target already inactive')
            self.key(0x11,True); self.key(0x26,True)
            for _ in range(40):
                self.advance(30); self.alive()
                if sample()['state']==11:
                    break
            self.release(); self.advance(150)
            final = sample()
            self.require(final['health']<initial['health'] and final['health']<=0 and
                         final['state']==11 and final['representation']==0,
                         'Strikes did not finish damage/death/deactivation')
        if not death:
            with self.phase('traversal.door-passage'):
                target_pos, player = self.position(target), self.position()
                dx,dz=target_pos[0]-player[0],target_pos[2]-player[2]
                self.require(math.hypot(dx,dz)>0, 'Invalid door approach')
                self.key(0x26,True); self.advance(60); self.key(0x26,False); self.advance(30)
                pos = self.position()
                beyond=((pos[0]-target_pos[0])*dx+(pos[2]-target_pos[2])*dz)/math.hypot(dx,dz)
                self.require(beyond>100, 'Joe did not pass through the broken door')

    def damage(self):
        with self.phase('combat.take-natural-damage'):
            route=json.loads((Path(__file__).parent/'scenarios/potion-damage-inputs.json').read_text())['inputs']
            for _ in range(1200):
                action=self.field(0xa6,'unsigned int')
                if action and self.value(f'*(short*){action}') in (11,12) and self.field(0x82)==4:
                    break
                self.advance(1)
            else:
                raise gdb.GdbError('Idle control not reached before damage route')
            before=self.field(0xec)
            previous=0
            for due,vk,on in route:
                self.advance(due-previous); previous=due
                self.key(vk,on)
                self.alive()
            self.release(); self.advance(30)
            # Live NPC timing can differ from the historical input schedule.
            # Approach the two actual pedestal guards using their observed positions;
            # stop as soon as a real hit lands, without assigning health or actor state.
            encounters=[]
            for identity in (284,293):
                if self.field(0xec)<before:break
                target=self.value(f'*(unsigned int*)(0x630b60+{identity}*4)')
                if not target or self.value(f'*(short*)({target}+0xec)')<=0:continue
                for _ in range(120):
                    if self.field(0xec)<before:break
                    destination,position=self.position(target),self.position()
                    dx,dz=destination[0]-position[0],destination[2]-position[2]
                    desired=int(math.atan2(dx,dz)*65536/(2*math.pi))
                    difference=(desired-self.field(0x92)+32768)%65536-32768
                    self.key(0x25,difference < -600);self.key(0x27,difference > 600)
                    self.key(0x26,math.hypot(dx,dz)>180 and abs(difference)<5000)
                    self.advance(3);self.alive()
                self.release()
                encounters.append(dict(actor=identity,health=self.field(0xec),position=self.position()))
            self.details['damage_encounters']=encounters
            self.require(0<self.field(0xec)<before, 'Bounded route/contact did not produce an observed enemy hit')
            self.details['damage']=dict(before=before, after=self.field(0xec))

    def potion(self, damaged=False):
        if damaged:
            self.damage()
        with self.phase('traversal.potion'):
            position=self.position()
            from_stairs=damaged and position[0]<8000 and position[2]>-16500
            self.walk(WORKSHOP[4:] if from_stairs else WORKSHOP)
            self.walk(POTION)
            potion=self.actor_by_id(537)
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
                    observations.append(dict(health=self.field(0xec),
                        attachment=value(f'*(unsigned int*)({potion}+0xf2)'),
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
                    scripts=scripts, samples=observations)
                self.save()
                self.require(observations[-1]['attachment']==0 and observations[-1]['representation']==0,
                             'Consumed bottle remains attached or represented')
                if branch=='healing':
                    self.require(391 in actions, 'Healing action not dispatched')
                    self.require(self.field(0xec)==100, 'Healing did not restore maximum health')
                elif branch=='poison':
                    self.require(409 in actions and any(t['action']==5 for t in timers),
                                 'Poison action/death timer missing')
                elif branch=='invisibility':
                    self.require(383 in actions and any(t['action']==387 for t in timers),
                                 'Invisibility action/fade timer missing')
                else:
                    self.require(before==self.field(0xec) and not timers,
                                 'Unafflicted conditional no-op changed health/timers')
        finally:
            script.delete();action.delete()
        self.release()

    def swimming(self):
        with self.phase('traversal.water'):
            points=json.loads((Path(__file__).parent/'scenarios/water-waypoints.json').read_text())['waypoints']
            self.walk([(p['position'][0],p['position'][2]) for p in points[1:]], tolerance=180)
            self.require(self.camera()==543, 'Water approach did not reach camera 543')
        with self.phase('movement.swimming'):
            before=self.position()
            self.key(0x26,True)
            for _ in range(30):
                self.advance(15)
                rep=self.field(0x11e,'unsigned int')
                if rep and self.value(f'*(short*){rep}')==13 and self.position()!=before:
                    break
            self.release();self.advance(30)
            rep=self.field(0x11e,'unsigned int')
            self.require(rep and self.value(f'*(short*){rep}')==13 and self.position()!=before,
                         'Swimming representation and displacement not observed')

    def run(self):
        with self.phase('startup.released-player'):
            self.require(self.field(0x82)==4 and self.field(0xec)==100,
                         'Startup did not produce healthy controllable Joe')
            self.require(self.camera()==175 and self.field(0x86)==3328,
                         'Startup did not reach the expected courtyard/floor')
        name=self.name
        if name=='movement': self.movement()
        elif name=='courtyard': self.courtyard()
        elif name=='damage': self.damage()
        elif name=='unarmed': self.unarmed()
        elif name=='unarmed-contact': self.unarmed_contact()
        elif name in ('workshop','sword','attacks','enemy','door','stability'):
            self.workshop()
            if name!='workshop': self.sword(traverse=False)
            if name in ('attacks','enemy','door','stability'): self.attacks()
            if name=='enemy': self.strike(602,death=True)
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
                self.walk([(-125,-9845),(-789,-9781),(-1278,-9756),(-837,-10021)])
                self.sword(traverse=False);self.attacks()
                bottle=self.actor_by_id(537)
                self.require(self.value(f'*(unsigned int*)({bottle}+0xf2)')==0 and
                             self.value(f'*(unsigned int*)({bottle}+0x11e)')==0,
                             'Sword use restored the consumed bottle')
        elif name=='swimming': self.swimming()
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
    return journey.run()
