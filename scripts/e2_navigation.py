"""Bounded test-input navigation; observations never write recovered game state.

The bridge supplies observe/apply/release/record. It owns SDL input and liveness.
Same-height local steering is deliberately conservative, not a pathfinding oracle.
"""
from dataclasses import dataclass
import math
import time


def distance(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


class NavigationFailure(RuntimeError):
    pass


class _ReplanSceneRoute(Exception):
    pass


@dataclass(frozen=True)
class Limits:
    updates: int = 2400
    replans: int = 6
    seconds: float = 55
    height: int = 300
    reach: int = 240
    window: int = 90
    water_window: int = 180


class Navigator:
    def __init__(self, bridge, goal, allowed, fixed=None, limits=Limits(), clock=time.monotonic):
        if not allowed or fixed is not None and fixed not in allowed:
            raise ValueError('Goal needs explicitly eligible actor identities')
        self.bridge, self.goal = bridge, goal
        self.allowed, self.fixed, self.limits = tuple(sorted(allowed)), fixed, limits
        self.clock, self.started = clock, clock()
        self.updates = self.replans = 0
        self.target = None
        self.pointer = None
        self.history = []
        self.detour = None
        self.phase = 'select'
        self.water_stroke=None
        self.replan_scene=False

    def record(self, **row):
        self.bridge.record(dict(goal=self.goal, phase=self.phase, target=self.target,
                                updates=self.updates, replans=self.replans, bounds=vars(self.limits), **row))

    def fail(self, reason, **evidence):
        self.record(outcome='FAIL', reason=reason, **evidence)
        raise NavigationFailure(reason)

    def observe(self):
        if self.clock() - self.started >= self.limits.seconds:
            self.fail('host-time budget exhausted')
        observation = self.bridge.observe()
        if observation['player']['health'] <= 0:
            self.fail('player did not survive', observation=observation)
        return observation

    def candidates(self,observation):
        player = observation['player']['position']
        choices, rejected = [], []
        for identity in self.allowed:
            actor = observation['actors'].get(identity)
            reason = self.invalid_goal(actor)
            if not reason and self.goal=='receive_one_hit' and not any(slot>=0 for slot in actor.get('attack_slots',[])):
                reason = 'no original NPC attack slots available'
            if self.fixed is not None and identity != self.fixed:
                reason = 'fixed target forbids substitution'
            if not reason and abs(actor['position'][1] - player[1]) > self.limits.height:
                reason = 'height mismatch; no connected route established'
            if reason:
                rejected.append(dict(identity=identity, reason=reason))
            else:
                # Only established local same-height approaches have finite cost.
                choices.append((distance(player, actor['position']), identity, actor['pointer']))
        return choices,rejected

    def select(self, observation):
        choices,rejected=self.candidates(observation)
        if not choices:
            self.fail('no eligible local encounter', rejected=rejected, observation=observation)
        cost, self.target, self.pointer = min(choices)
        self.phase = 'approach'
        self.record(route_cost=cost, reachability='same-height local candidate; approach still unproved',
                    rejected=rejected, observation=observation)

    def encounter_available(self,observation):
        choices,_=self.candidates(observation)
        return any(cost<=1800 and observation['actors'][identity]['position'][1]==observation['player']['position'][1]
                   for cost,identity,_ in choices)

    @staticmethod
    def invalid(actor):
        if not actor or not actor.get('identity_valid') or not actor.get('active'):
            return 'target disappeared or left active table'
        if actor['health'] <= 0 or actor['state'] in (5, 11) or not actor['representation']:
            return 'target dead or temporarily unavailable'
        return None

    def invalid_goal(self,actor):
        reason=self.invalid(actor)
        # Original 0x428725..0x428742 cannot leave retreat for attack
        # while the signed readiness word at +0xea is <= 0x3000.
        if (not reason and self.goal=='receive_one_hit' and actor['state']==2 and
                actor.get('ai_readiness',0x7fff)<=0x3000):
            reason='original retreat state lacks attack readiness'
        return reason

    def target_in(self, observation):
        actor = observation['actors'].get(self.target)
        reason = self.invalid_goal(actor)
        if reason and self.goal == 'receive_one_hit' and self.fixed is None:
            if self.replans >= self.limits.replans:
                self.fail('replan budget exhausted', trigger=reason, observation=observation)
            self.replans += 1
            self.record(action='reselect eligible opponent', reason=reason, observation=observation)
            phase = self.phase
            self.select(observation)
            self.phase = phase
            self.detour = None
            self.history.clear()
            actor = observation['actors'][self.target]
            reason = self.invalid_goal(actor)
        if reason or actor['pointer'] != self.pointer:
            self.fail(reason or 'target instance changed', observation=observation)
        if abs(actor['position'][1] - observation['player']['position'][1]) > self.limits.height:
            self.fail('height mismatch; connected route required', observation=observation)
        return actor

    def contact_point(self, target, player=None):
        # Stand in front of the observed opponent for its original melee node.
        # A center chase can follow behind it or circle outside the strike.
        position = target['position']
        radius=0
        if self.goal=='receive_one_hit':
            target_radius=max(0,target.get('radius',0))
            player_radius=max(0,(player or target).get('radius',0))
            radius=(target_radius+player_radius)*3/4+64 if target_radius or player_radius else 0
        heading = target.get('heading', 0) * 2 * math.pi / 65536
        return [position[0] + math.sin(heading) * radius, position[1],
                position[2] + math.cos(heading) * radius]

    def contact_aim(self,observation,target):
        destination=self.contact_point(target,observation['player'])
        if self.goal!='receive_one_hit':return destination
        player=observation['player']
        radii=max(0,player.get('radius',0))+max(0,target.get('radius',0))
        if not radii:return destination
        clearance=radii*3/4
        dx=player['position'][0]-target['position'][0]
        dz=player['position'][2]-target['position'][2]
        separation=math.hypot(dx,dz)
        heading=target.get('heading',0)*2*math.pi/65536
        angle=math.atan2(dx,dz) if separation else heading
        turn=(heading-angle+math.pi)%(2*math.pi)-math.pi
        if separation>=clearance+256 or abs(turn)<=math.pi/4:return destination
        # The offset contact point can lie inside the opponent's collision
        # disc. Move around its outside before closing on the front arc.
        if separation<clearance+32:
            radius=clearance+128
        else:
            radius=max(clearance+64,separation)
            angle+=max(-math.pi/4,min(math.pi/4,turn))
        return [target['position'][0]+math.sin(angle)*radius,target['position'][1],
                target['position'][2]+math.cos(angle)*radius]

    def step(self, observation, wait=False, waypoint=None, updates=3):
        if type(updates) is not int or not 1<=updates<=3:
            raise ValueError('Navigation step needs one to three updates')
        if self.updates + updates > self.limits.updates:
            self.fail('game-update budget exhausted', observation=observation)
        target = self.target_in(observation) if waypoint is None else dict(position=waypoint)
        player = observation['player']
        destination = self.contact_point(target,player) if waypoint is None else target['position']
        separation = distance(player['position'], destination)
        reach = self.limits.reach
        wait_reach = reach + 100
        if self.goal == 'receive_one_hit' and waypoint is None:
            radius=max(0,player.get('radius',0))
            if radius:
                reach=min(reach,max(32,radius//4))
                wait_reach=reach+min(100,max(16,radius//8))
            forward_x = destination[0] - target['position'][0]
            forward_z = destination[2] - target['position'][2]
            if ((player['position'][0] - target['position'][0]) * forward_x +
                    (player['position'][2] - target['position'][2]) * forward_z < 0):
                wait_reach = reach
        if self.detour and distance(player['position'], self.detour) < 100:
            self.detour = None
            self.history.clear()
            self.record(action='rejoin live target')
        contact_aim=self.contact_aim(observation,target) if waypoint is None else destination
        aim = self.detour or contact_aim
        dx, dz = aim[0] - player['position'][0], aim[2] - player['position'][2]
        desired = int(math.atan2(dx, dz) * 65536 / (2 * math.pi))
        difference = (desired - player['heading'] + 32768) % 65536 - 32768
        swimming=player.get('representation_id') in (10,13)
        backwards=swimming and abs(difference)>16384
        if backwards:difference=(difference+65536)%65536-32768
        forward = (not wait or separation > wait_reach) and abs(difference) < 5000
        keys = []
        turn_band=2000 if swimming else 600
        if difference < -turn_band: keys.append(0x25)
        if difference > turn_band: keys.append(0x27)
        if forward: keys.append(0x28 if backwards else 0x26)
        if swimming:
            # A backwards stroke initially moves forwards. Minor corrections
            # must not restart it before its actual propulsive part completes.
            stroke=self.water_stroke
            if stroke:
                action=player.get('action_id');progress=player.get('progress',0)&65535
                wrapped=stroke['progress'] is not None and action==stroke['action'] and progress<stroke['progress']
                if wrapped or self.updates-stroke['started']>=180:
                    self.water_stroke=None
                else:
                    if action==stroke['action']:stroke['progress']=progress
                    keys=[stroke['key']];forward=True
            if self.water_stroke is None:
                if abs(difference)<=turn_band:
                    key=0x28 if backwards else 0x26
                    self.water_stroke=dict(key=key,action=1480 if backwards else 1073,
                                           progress=None,started=self.updates)
                    keys=[key];forward=True
                else:
                    keys=[0x25 if difference<0 else 0x27];forward=False
        if wait and separation <= wait_reach:
            keys = []  # Release all attack and movement controls; let original AI act.
        self.history.append((self.updates, player['position'], distance(player['position'],aim), forward,
                             contact_aim if contact_aim!=destination else destination))
        window=self.limits.water_window if swimming else self.limits.window
        self.history = [row for row in self.history if self.updates - row[0] <= window]
        if len(self.history) > 1 and self.updates - self.history[0][0] >= window:
            first = self.history[0]
            displacement = distance(first[1], player['position'])
            progress = first[2] - distance(player['position'],aim)
            moving = sum(row[3] for row in self.history)
            if moving >= len(self.history) // 2 and progress < 25 and (not wait or separation > wait_reach):
                target_motion=distance(first[4],destination)
                if not self.detour and target_motion>100 and displacement>100:
                    self.record(action='track moving target', target_displacement=target_motion,
                                displacement=displacement, progress=progress, observation=observation)
                    self.history.clear()
                else:
                    reason = 'stuck' if displacement < 35 else 'circling without progress'
                    self.replan(observation, reason, displacement, progress, destination)
        self.record(action='released observation' if not keys else 'steer', keys=keys,
                    distance=separation, reach=reach, wait_reach=wait_reach,
                    target_position=target['position'], aim=aim, sample_updates=updates,
                    contact_policy='outside encounter collision disc' if contact_aim!=destination else 'direct',
                    progress_window=window,stroke=self.water_stroke.copy() if self.water_stroke else None,
                    locomotion='swim backwards' if swimming and 0x28 in keys else
                               'swim forwards' if swimming and 0x26 in keys else 'swim turn' if swimming else 'ground',
                    observation=observation)
        self.bridge.apply(keys, updates)
        self.updates += updates

    def replan(self, observation, reason, displacement, progress, destination=None):
        if self.replans >= self.limits.replans:
            self.fail('replan budget exhausted', blocker='unknown blocker', trigger=reason,
                      displacement=displacement, progress=progress, observation=observation)
        self.replans += 1
        if self.replan_scene:
            self.record(action='refresh scene plan after stalled movement',trigger=reason,
                        displacement=displacement,progress=progress,observation=observation)
            raise _ReplanSceneRoute()
        player = observation['player']['position']
        destination = destination or observation['actors'][self.target]['position']
        dx, dz = destination[0] - player[0], destination[2] - player[2]
        length = max(1, math.hypot(dx, dz))
        side = -1 if self.detour and displacement < 35 else 1
        clearance = 320 + 160 * (self.replans - 1)
        self.detour = [int(player[0] + dz / length * clearance * side + dx / length * 120),
                       player[1], int(player[2] - dx / length * clearance * side + dz / length * 120)]
        nearby = [actor for identity, actor in sorted(observation['actors'].items())
                  if identity not in (self.target,observation['player']['identity']) and
                  actor.get('active') and distance(player, actor['position']) < 500]
        self.record(action='local detour', trigger=reason, blocker='nearby actors observed' if nearby else 'unknown blocker',
                    nearby=nearby, path=self.detour, displacement=displacement, progress=progress, observation=observation,
                    rejected_actions=['attack blocker: scenario has no interaction permission'])
        self.history.clear()

    def await_actor(self, identity, updates=300):
        """Wait for the audited scene actor to enter its represented AI state."""
        if identity not in self.allowed:
            raise ValueError('Readiness target is outside the declared goal')
        self.phase = 'scene-readiness'
        pointer = None
        end = self.updates + updates
        try:
            while True:
                observation = self.observe()
                actor = observation['actors'].get(identity)
                if not actor or not actor['identity_valid'] or not actor['active'] or actor['health'] <= 0:
                    self.fail('scene actor absent or dead before encounter', observation=observation)
                if pointer is not None and actor['pointer'] != pointer:
                    self.fail('scene actor instance changed', observation=observation)
                pointer = actor['pointer']
                if not self.invalid(actor):
                    self.record(outcome='READY', identity=identity, observation=observation)
                    return
                if self.updates + 3 > min(end,self.limits.updates):
                    self.fail('scene actor readiness budget exhausted', observation=observation)
                self.record(action='release and observe original scene activation', identity=identity, observation=observation)
                self.bridge.apply([],3)
                self.updates += 3
        except BaseException as error:
            self.record(outcome='INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'STOPPED', reason=str(error))
            raise
        finally:
            self.bridge.release()

    def follow_route(self, points, provenance, tolerance=160, height_ranges=None, node_tolerances=None,
                     swimming_representation=None,stop_on_swimming_at=None,stop_on_encounter=False):
        """Connected human corridor guidance; verify actual height at each node."""
        height_ranges=height_ranges or {}
        node_tolerances=node_tolerances or {}
        if stop_on_encounter and self.goal!='receive_one_hit':
            raise ValueError('Encounter handoff requires the receive-hit goal')
        if any(type(index) is not int or not 0<=index<len(points) or
               not isinstance(bounds,(list,tuple)) or len(bounds)!=2 or
               any(type(value) is not int for value in bounds) or
               not -32768<=bounds[0]<=bounds[1]<=32767 for index,bounds in height_ranges.items()):
            raise ValueError('Invalid explicit route height range')
        if any(type(index) is not int or not 0<=index<len(points) or
               type(radius) is not int or not 0<radius<=tolerance for index,radius in node_tolerances.items()):
            raise ValueError('Invalid explicit route node tolerance')
        self.phase = 'route'
        previous=None
        try:
            self.record(action='follow connected corridor', path=points, provenance=provenance,
                        height_ranges=height_ranges,node_tolerances=node_tolerances,max_step_distance=1024)
            for index, point in enumerate(points):
                self.history.clear()
                self.detour = None
                self.water_stroke=None
                while True:
                    observation = self.observe()
                    position = observation['player']['position']
                    if stop_on_encounter and self.encounter_available(observation):
                        self.record(outcome='ENCOUNTER',route_node=index,observation=observation)
                        return observation
                    if stop_on_swimming_at is not None and position[1]==stop_on_swimming_at and observation['player'].get('representation_id') in (10,13):
                        self.record(outcome='SWIMMING',route_node=index,observation=observation)
                        return observation
                    if swimming_representation is not None and observation['player'].get('representation_id')!=swimming_representation:
                        self.fail('water traversal left swimming representation',node=index,observation=observation)
                    if previous is not None and distance(previous,position)>1024:
                        self.fail('route movement discontinuity',previous=previous,node=index,observation=observation)
                    previous=position
                    radius=node_tolerances.get(index,tolerance)
                    separation=distance(position,point)
                    if separation < radius:
                        bounds=height_ranges.get(index)
                        height_matches=bounds[0]<=position[1]<=bounds[1] if bounds else abs(position[1]-point[1])<=self.limits.height
                        if not height_matches:
                            self.fail('route node height mismatch',node=index,height_range=bounds,observation=observation)
                        self.record(outcome='WAYPOINT', node=index, observation=observation)
                        break
                    # Observe each update near an explicitly narrow corner instead
                    # of cutting it at the ordinary actor-radius waypoint band.
                    updates=1 if index in node_tolerances and separation<radius*2 else 3
                    self.step(observation, waypoint=point,updates=updates)
        except _ReplanSceneRoute:
            raise
        except BaseException as error:
            self.record(outcome='INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'STOPPED', reason=str(error))
            raise
        finally:
            self.bridge.release()

    @staticmethod
    def actor_clearance(observation,excluded=()):
        player=observation['player']
        # Original 0x448cb4 considers flag 0x1000, state != 11 and a
        # three-quarter sum of actor radii. Add half a lattice step for steering.
        return [dict(identity=identity,position=actor['position'],
                     clearance=((max(0,actor.get('radius',0))+max(0,player.get('radius',0)))*3>>2)+64)
                for identity,actor in sorted(observation['actors'].items())
                if identity not in (player['identity'],*excluded) and actor.get('active') and
                actor.get('identity_valid') and actor.get('flags',0)&0x1000 and actor.get('state')!=11]

    def navigate(self,scene,goal,water=False,swimming_representation=None,avoid_actors=False):
        """Plan from the current scene snapshot, then verify real input traversal."""
        if avoid_actors and (water or swimming_representation is not None):
            raise ValueError('Observed actor avoidance is qualified for ground approaches only')
        self.replan_scene=avoid_actors
        try:
            if avoid_actors:
                floor_connected=False
                while True:
                    observation=self.observe()
                    obstacles=self.actor_clearance(observation,() if self.fixed is None else (self.fixed,))
                    try:
                        plan=scene.plan(observation['player']['position'],goal,obstacles=obstacles)
                    except ValueError as error:
                        if not obstacles or str(error)!='No connected scene-floor plan within declared movement policy':raise
                        if not floor_connected:
                            scene.plan(observation['player']['position'],goal)
                            floor_connected=True
                        if self.replans>=self.limits.replans:
                            self.fail('replan budget exhausted',trigger='observed actors disconnect floor route',observation=observation)
                        if self.updates+30>self.limits.updates:
                            self.fail('game-update budget exhausted',observation=observation)
                        self.replans+=1
                        self.record(action='release and await observed actor clearance',
                                    obstacles=obstacles,observation=observation)
                        self.bridge.apply([],30);self.updates+=30
                        continue
                    self.record(action='plan from observed scene floors',plan=plan)
                    try:
                        self.follow_route(plan['path'],plan['source'],tolerance=60)
                        return
                    except _ReplanSceneRoute:
                        continue
            observation=self.observe()
            plan=scene.plan(observation['player']['position'],goal,water=water,only_water=swimming_representation is not None)
            self.record(action='plan from observed scene floors',plan=plan)
            if water and swimming_representation is None:
                self.follow_route(plan['path'],plan['source'],tolerance=100,
                                  height_ranges={index:[bounds[0]-256,bounds[1]] for index,bounds in plan['height_ranges'].items()},
                                  stop_on_swimming_at=goal[1])
                self.phase='water-entry'
                end=min(self.updates+180,self.limits.updates)
                while True:
                    observation=self.observe();player=observation['player']
                    if player.get('representation_id') in (10,13) and player['position'][1]==goal[1]:
                        self.record(outcome='SWIMMING',observation=observation)
                        swimming_representation=player['representation_id'];break
                    if self.updates+3>end:self.fail('water entry transition budget exhausted',observation=observation)
                    self.record(action='release and await actual water entry',observation=observation)
                    self.bridge.apply([],3);self.updates+=3
                plan=scene.plan(player['position'],goal,water=True,only_water=True)
                self.record(action='replan from actual swimming position',plan=plan)
                self.follow_route(plan['path'],plan['source'],tolerance=180,
                                  swimming_representation=swimming_representation)
            else:
                self.follow_route(plan['path'],plan['source'],tolerance=180 if swimming_representation is not None else 100,
                                  swimming_representation=swimming_representation)
        except BaseException:
            self.bridge.release()
            raise
        finally:
            self.replan_scene=False

    def cross_opening(self, identity, center, normal, half_width=256, clearance=640):
        """Cross a scenario-declared opening; never bypass its required gate.

        The caller must have verified the permitted destructive interaction.
        Geometry is frozen scene guidance, not a query into recovered physics.
        """
        if identity not in self.allowed or self.fixed not in (None,identity):
            raise ValueError('Opening is outside the declared goal')
        length=math.hypot(*normal)
        if length==0 or half_width<=0 or clearance<=100:
            raise ValueError('Invalid opening guidance')
        normal=[component/length for component in normal]
        tangent=[-normal[1],normal[0]]
        self.phase='cross-opening'
        self.target=identity
        def coordinates(position):
            dx,dz=position[0]-center[0],position[2]-center[2]
            return dx*normal[0]+dz*normal[1],dx*tangent[0]+dz*tangent[1]
        crossed=False
        previous=None
        try:
            self.record(action='align and cross required opening',center=center,normal=normal,
                        half_width=half_width,clearance=clearance)
            points=[[center[0]-normal[0]*384,center[1],center[2]-normal[1]*384],
                    list(center),
                    [center[0]+normal[0]*clearance,center[1],center[2]+normal[1]*clearance]]
            for index,point in enumerate(points):
                self.detour=None
                self.history.clear()
                while True:
                    observation=self.observe()
                    position=observation['player']['position']
                    forward,lateral=coordinates(position)
                    if abs(position[1]-center[1])>self.limits.height:
                        self.fail('opening height mismatch',observation=observation)
                    if previous is None and forward>=0:
                        self.fail('opening crossing not observed from approach side',observation=observation)
                    if previous is not None:
                        last_forward,last_lateral=coordinates(previous)
                        if last_forward<=0<forward:
                            fraction=-last_forward/(forward-last_forward)
                            gate_lateral=last_lateral+fraction*(lateral-last_lateral)
                            gate_height=previous[1]+fraction*(position[1]-previous[1])-center[1]
                            if abs(gate_lateral)>half_width or abs(gate_height)>self.limits.height:
                                self.fail('crossed outside required opening',lateral=gate_lateral,
                                          height=gate_height,observation=observation)
                            crossed=True
                            self.record(outcome='CROSSED',lateral=gate_lateral,height=gate_height,
                                        previous=previous,observation=observation)
                    previous=position
                    if distance(position,point)<80:
                        self.record(outcome='WAYPOINT',node=index,forward=forward,lateral=lateral,observation=observation)
                        break
                    self.step(observation,waypoint=point)
            if not crossed or forward<=100:
                self.fail('required opening crossing not completed',observation=observation)
            self.record(outcome='PASS',forward=forward,lateral=lateral,observation=observation)
            return dict(actor=identity,center=center,normal=normal,half_width=half_width,
                        crossed=crossed,forward=forward,lateral=lateral)
        except BaseException as error:
            self.record(outcome='INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'STOPPED',reason=str(error))
            raise
        finally:
            self.bridge.release()

    def approach(self, before=None, hit_evidence=None, completed=None):
        if completed is not None and (self.goal!='kill_enemy' or self.fixed is None):
            raise ValueError('Completion observation requires an explicit fixed kill goal')
        try:
            observation = self.observe()
            self.phase = 'approach'
            self.history.clear()
            while True:
                candidate=observation['actors'].get(self.fixed) if completed else None
                if (candidate and candidate.get('identity_valid') and candidate.get('active') and
                        (self.pointer is None or candidate['pointer']==self.pointer) and completed(observation)):
                    self.target=self.fixed;self.pointer=candidate['pointer']
                    self.record(outcome='REACHED',reason='observed fixed-target kill during approach',observation=observation)
                    return self.target
                if self.target is None:self.select(observation)
                actor = self.target_in(observation)
                if before is not None and observation['player']['health'] < before:
                    evidence=hit_evidence(self.target) if hit_evidence else None
                    if not evidence:self.fail('health loss without attributed eligible enemy hit', observation=observation)
                    self.record(outcome='REACHED', reason='attributed hit during approach', hit=evidence, observation=observation)
                    return self.target
                point = self.contact_point(actor,observation['player'])
                reach=self.limits.reach
                if self.goal=='receive_one_hit' and observation['player'].get('radius',0)>0:
                    reach=min(reach,max(32,observation['player']['radius']//4))
                if distance(observation['player']['position'], point) <= reach:
                    self.record(outcome='REACHED', reach=reach, aim=point, observation=observation)
                    return self.target
                self.step(observation)
                observation = self.observe()
        except BaseException as error:
            self.record(outcome='INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'STOPPED', reason=str(error))
            raise
        finally:
            self.bridge.release()

    def receive(self, before, hit_evidence):
        self.phase = 'receive-one-hit'
        try:
            while True:
                observation = self.observe()
                if observation['player']['health'] < before:
                    evidence = hit_evidence(self.target)
                    if not evidence:
                        self.fail('health loss without attributed eligible enemy hit', observation=observation)
                    self.record(outcome='PASS', hit=evidence, observation=observation)
                    return observation['player']['health']
                self.step(observation, wait=True)
        except BaseException as error:
            self.record(outcome='INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'STOPPED', reason=str(error))
            raise
        finally:
            self.bridge.release()
