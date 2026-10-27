#!/usr/bin/env python3
"""Deterministic navigation decisions, bounds, release and failure evidence."""
import copy
import math
import json
from pathlib import Path
import struct
import unittest
from e2_navigation import Navigator, Limits, NavigationFailure
from e2_scene_navigation import SceneMap,navigation_scripts


def actor(identity, position, pointer=None):
    return dict(identity=identity,pointer=pointer or identity+100,identity_valid=True,
                active=True,health=100,state=4,representation=1,position=position,heading=0)


class Bridge:
    def __init__(self, target=None, step=None):
        self.state=dict(player=actor(0,[0,0,0]),actors={602:target or actor(602,[0,0,600])})
        self.rows=[];self.keys=[];self.released=0;self.step=step
    def observe(self):return copy.deepcopy(self.state)
    def record(self,row):self.rows.append(copy.deepcopy(row))
    def release(self):self.released+=1
    def apply(self,keys,updates):
        self.keys.append(keys)
        if self.step:self.step(self,keys,updates)


class Contracts(unittest.TestCase):
    def test_receive_settling_stays_outside_collision_clearance_and_rejects_off_axis_wait(self):
        guard=actor(284,[6936,4096,-17526]);guard.update(radius=256,heading=-18429,attack_slots=[344])
        b=Bridge(guard);b.state['actors']={284:guard}
        b.state['player'].update(position=[6574,4096,-17303],radius=256)
        n=Navigator(b,'receive_one_hit',[284],fixed=284,limits=Limits(updates=3))
        point=n.contact_point(guard,b.state['player'])
        self.assertAlmostEqual(math.hypot(point[0]-guard['position'][0],point[2]-guard['position'][2]),448)
        with self.assertRaisesRegex(NavigationFailure,'game-update'):n.approach()
        self.assertTrue(b.keys[0])
        self.assertFalse(any(row.get('outcome')=='REACHED' for row in b.rows))
        b=Bridge(guard);b.state['actors']={284:guard}
        b.state['player'].update(position=point,radius=256)
        n=Navigator(b,'receive_one_hit',[284],fixed=284,limits=Limits(updates=3))
        n.approach()
        with self.assertRaisesRegex(NavigationFailure,'game-update'):n.receive(100,lambda _:[])
        self.assertEqual(b.keys,[[]])
        self.assertEqual(next(row['wait_reach'] for row in b.rows if row.get('action')=='released observation'),96)
        self.assertFalse(any(row.get('outcome')=='PASS' for row in b.rows))

    def test_encounter_corridor_hands_over_at_first_same_floor_eligible_local_opponent(self):
        def step(b,keys,updates):
            b.state['player']['position'][1]=256
            b.state['player']['position'][2]+=30
        b=Bridge(step=step);b.state['actors']={284:actor(284,[0,256,800])}
        b.state['actors'][284].update(state=7,attack_slots=[344],ai_readiness=0)
        n=Navigator(b,'receive_one_hit',[284],limits=Limits(updates=9))
        n.follow_route([[0,0,2000]],'declared corridor',stop_on_encounter=True)
        self.assertEqual(n.updates,3)
        self.assertEqual(b.rows[-1]['outcome'],'ENCOUNTER')
        self.assertFalse(any(row.get('outcome')=='PASS' for row in b.rows))
        self.assertEqual(b.released,1)
        b.state['actors'][284].update(state=2,ai_readiness=0)
        self.assertFalse(n.encounter_available(b.observe()))
        b.state['actors'][284].update(state=7,position=[0,256,3000])
        self.assertFalse(n.encounter_available(b.observe()))
        n=Navigator(b,'reach_sword',[284])
        with self.assertRaises(ValueError):n.follow_route([[0,0,0]],'corridor',stop_on_encounter=True)

    def test_receive_contact_goes_around_collision_disc_and_keeps_known_front_geometry(self):
        guard=actor(284,[0,0,0]);guard.update(radius=256,heading=0)
        b=Bridge(guard);b.state['actors']={284:guard}
        b.state['player']['radius']=256
        n=Navigator(b,'receive_one_hit',[284])
        for position in ([0,0,-512],[-512,0,0],[512,0,0]):
            b.state['player']['position']=position
            aim=n.contact_aim(b.observe(),guard)
            self.assertGreaterEqual(math.hypot(aim[0],aim[2]),448)
            for index in range(101):
                fraction=index/100
                point=[position[0]+fraction*(aim[0]-position[0]),position[2]+fraction*(aim[2]-position[2])]
                self.assertGreaterEqual(math.hypot(*point),384)
        b.state['player']['position']=[0,0,-378]
        aim=n.contact_aim(b.observe(),guard)
        self.assertAlmostEqual(aim[0],0);self.assertEqual(aim[1:], [0,-512])
        b.state['player']['position']=[0,0,379]
        self.assertEqual(n.contact_aim(b.observe(),guard),n.contact_point(guard))
        n=Navigator(b,'reach_sword',[284])
        self.assertEqual(n.contact_aim(b.observe(),guard),guard['position'])

    def test_receive_rejects_original_unready_retreat_without_excluding_ready_guard_identity(self):
        b=Bridge();b.state['actors']={i:actor(i,[0,0,z]) for i,z in ((284,600),(293,100))}
        for t in b.state['actors'].values():t.update(attack_slots=[344],ai_readiness=0)
        b.state['actors'][284]['state']=7;b.state['actors'][293]['state']=2
        n=Navigator(b,'receive_one_hit',[284,293]);n.select(b.observe())
        self.assertEqual(n.target,284)
        self.assertIn('attack readiness',b.rows[-1]['rejected'][0]['reason'])
        b.state['actors'][293]['ai_readiness']=0x3001
        n=Navigator(b,'receive_one_hit',[284,293]);n.select(b.observe())
        self.assertEqual(n.target,293)
        b.state['actors'][293]['ai_readiness']=0
        n=Navigator(b,'receive_one_hit',[284,293],fixed=293)
        with self.assertRaises(NavigationFailure):n.select(b.observe())

    def test_actor_disconnected_plan_waits_within_existing_budget_and_never_walks_floor_only_plan(self):
        from types import SimpleNamespace
        for condition in ('clears','blocked','no floor route'):
            b=Bridge();b.state['actors']={12:actor(12,[0,0,100])}
            b.state['actors'][12].update(radius=256,flags=0x1000)
            b.state['player']['radius']=256
            calls=[]
            def plan(start,goal,obstacles=()):
                calls.append(bool(obstacles))
                if condition=='no floor route' or obstacles and not (condition=='clears' and b.keys):
                    raise ValueError('No connected scene-floor plan within declared movement policy')
                return dict(path=[goal],source='observed scene')
            n=Navigator(b,'reach_potion',[537],fixed=537,limits=Limits(replans=2,updates=90))
            with self.subTest(condition=condition):
                if condition=='clears':n.navigate(SimpleNamespace(plan=plan),[0,0,0],avoid_actors=True)
                elif condition=='blocked':
                    with self.assertRaisesRegex(NavigationFailure,'replan budget'):n.navigate(SimpleNamespace(plan=plan),[0,0,0],avoid_actors=True)
                else:
                    with self.assertRaises(ValueError):n.navigate(SimpleNamespace(plan=plan),[0,0,0],avoid_actors=True)
            self.assertEqual(calls.count(False),1)
            self.assertTrue(all(keys==[] for keys in b.keys))
            self.assertLessEqual(n.updates,60);self.assertLessEqual(n.replans,2)
            self.assertFalse(n.replan_scene)
            if condition=='clears':self.assertEqual(n.updates,30)
            if condition=='no floor route':self.assertEqual(n.updates,0)

    def test_fixed_kill_can_complete_during_pursuit_without_accepting_unattributed_or_replaced_targets(self):
        for condition in ('pass','unattributed','replaced','absent'):
            evidence=[]
            def finish(b,keys,updates):
                target=b.state['actors'][602]
                target.update(health=-20,state=8)
                if condition!='unattributed':evidence.append(dict(attacker=0))
                if condition=='replaced':target['pointer']+=1
                if condition=='absent':b.state['actors'].clear()
            b=Bridge(step=finish)
            n=Navigator(b,'kill_enemy',[602],fixed=602,limits=Limits(updates=9))
            def completed(observation):
                target=observation['actors'].get(602)
                return target and target['health']<=0 and bool(evidence)
            with self.subTest(condition=condition):
                if condition=='pass':
                    self.assertEqual(n.approach(completed=completed),602)
                    self.assertEqual(b.rows[-1]['outcome'],'REACHED')
                    self.assertFalse(any(row.get('outcome')=='FAIL' for row in b.rows))
                else:
                    with self.assertRaises(NavigationFailure):n.approach(completed=completed)
            self.assertEqual(n.updates,3)
            self.assertEqual(b.released,1)
            self.assertFalse(any(0x11 in keys or 32 in keys for keys in b.keys))
        for goal,fixed in (('reach_sword',602),('kill_enemy',None)):
            n=Navigator(Bridge(),goal,[602],fixed=fixed)
            with self.assertRaises(ValueError):n.approach(completed=lambda _:True)

    def test_readonly_floor_decoder_matches_original_fixture_inputs(self):
        cases=json.loads((Path(__file__).parent/'fixtures/e2-courtyard-steering.json').read_text())
        count=0
        for case in cases:
            for floor in case['floors']:
                x,y,z=floor['coord'];cell=floor['cell'];chain=floor['descriptors']
                grid=bytearray(b'\xff'*32768)
                struct.pack_into('<H',grid,(((z>>9)+64)*128+(x>>9)+64)*2,cell)
                descriptors=bytes(cell*12)+bytes(value for row in chain for value in row)
                flags=bytearray(256)
                surface=chain[floor['selected']-cell][6]
                flags[surface*2]=floor['terrain_flags']
                scene=SceneMap(grid,descriptors,flags,floor['shift'])
                row=scene.floor(x,y,z)
                self.assertEqual(row['position'][1],floor['floor'])
                self.assertEqual(row['descriptor'],floor['selected']);count+=1
        self.assertEqual(count,56)

    def test_scene_planner_respects_cliffs_scripts_missing_floor_and_node_bound(self):
        def scene(grid=None,row=None,flags=None):
            return SceneMap(grid or bytes(32768),row or bytes([128,1,0,128,0,0,0,128,1,0,1,0]),flags or bytes(256),7)
        plan=scene().plan([0,0,0],[800,0,0])
        self.assertGreater(len(plan['path']),1)
        self.assertEqual(plan['source'],'live scene grid; original 0x448744/0x448a48 layout')
        with self.assertRaisesRegex(ValueError,'node budget'):scene().plan([0,0,0],[800,0,0],max_nodes=1)
        with self.assertRaisesRegex(ValueError,'start floor'):scene(grid=b'\xff'*32768).plan([0,0,0],[800,0,0])
        self.assertIsNone(scene(row=bytes([128,1,1,128,0,0,0,128,1,0,1,0])).safe(0,0,0,False))
        self.assertIsNone(scene(row=bytes([128,1,0,128,0,0,0,120,1,0,1,0])).safe(0,0,0,False))

    def test_scene_plan_avoids_observed_actor_discs_and_can_leave_crowded_start(self):
        scene=SceneMap(bytes(32768),bytes([128,1,0,128,0,0,0,128,1,0,1,0]),bytes(256),7)
        obstacles=[dict(identity=27,position=[384,0,0],clearance=256)]
        original=copy.deepcopy(obstacles)
        plan=scene.plan([0,0,0],[1024,0,0],obstacles=obstacles)
        self.assertEqual(plan['observed_actor_clearance'],original)
        for a,b in zip(plan['path'],plan['path'][1:]):
            for index in range(21):
                x=a[0]+(b[0]-a[0])*index/20;z=a[2]+(b[2]-a[2])*index/20
                self.assertGreaterEqual(math.hypot(x-384,z),256)
        self.assertEqual(obstacles,original)
        escape=scene.plan([384,0,0],[1024,0,0],obstacles=obstacles)
        self.assertGreater(math.dist(escape['path'][-1],[384,0,0]),256)
        self.assertLessEqual(escape['expanded'],escape['max_nodes'])

    def test_actor_clearance_uses_collision_fields_and_stalled_refresh_remains_bounded(self):
        from types import SimpleNamespace
        b=Bridge();b.state['player']['radius']=256
        for identity,flags,state in ((27,0x1000,7),(601,0x829,7),(28,0x1000,11),(3717,0x1000,7)):
            b.state['actors'][identity]=actor(identity,[0,0,300])
            b.state['actors'][identity].update(flags=flags,state=state,radius=256)
        original=copy.deepcopy(b.state)
        obstacles=Navigator.actor_clearance(b.observe(),(3717,))
        self.assertEqual(obstacles,[dict(identity=27,position=[0,0,300],clearance=448)])
        calls=[]
        def plan(start,goal,obstacles):
            calls.append(copy.deepcopy(obstacles))
            b.state['actors'][27]['position'][0]+=10
            return dict(path=[goal],source='observed scene',observed_actor_clearance=obstacles)
        n=Navigator(b,'reach_sword',[3717],fixed=3717,limits=Limits(window=9,replans=2,updates=600))
        with self.assertRaisesRegex(NavigationFailure,'replan budget'):
            n.navigate(SimpleNamespace(plan=plan),[0,0,600],avoid_actors=True)
        self.assertEqual(len(calls),3)
        self.assertEqual([row[0]['position'][0] for row in calls],[0,10,20])
        self.assertEqual(n.replans,2)
        self.assertLessEqual(n.updates,600)
        self.assertGreaterEqual(b.released,3)
        self.assertFalse(n.replan_scene)
        self.assertFalse(any(0x11 in keys or 32 in keys for keys in b.keys))
        self.assertEqual(b.state['player'],original['player'])

    def test_script_policy_decodes_instructions_without_trusting_labels(self):
        def resource(rows):
            data=bytearray(b'FANT\x007\0\0'+bytes(26+11+30)+struct.pack('>H',len(rows)))
            for identity,tokens in enumerate(rows):
                data+=struct.pack('>'+str(len(tokens)+3)+'H',identity,*tokens,0,0)
            return bytes(data)
        policy=navigation_scripts(resource([[0x25,0xf05a,0x70,0x6f,0xa001,0xf001,0xf002,0xf003],
                                             [7,0x4001],[0x54,0xf001],[0x25,0x4001]]))
        self.assertEqual(set(policy['allowed']),{1,2})
        self.assertEqual(policy['allowed'][1]['effects'],[0x25,0x6f,0x70])
        with self.assertRaisesRegex(ValueError,'Unsupported'):navigation_scripts(b'bad')

    def test_water_route_requires_representation_throughout_every_sample(self):
        def leave(b,keys,updates):
            b.state['player']['position'][2]+=60
            b.state['player']['representation_id']=12
        b=Bridge(step=leave);b.state['player']['representation_id']=13
        n=Navigator(b,'traverse water',[0])
        with self.assertRaisesRegex(NavigationFailure,'left swimming'):
            n.follow_route([[0,0,600]],'live scene',swimming_representation=13)
        self.assertEqual(b.released,1)
        self.assertEqual(len(b.keys),1)

    def test_swimming_can_approach_a_point_behind_without_turning_in_circles(self):
        def move(b,keys,updates):
            if 0x28 in keys:b.state['player']['position'][2]-=60
        b=Bridge(step=move);b.state['player']['representation_id']=13
        n=Navigator(b,'water return',[0])
        n.follow_route([[0,0,-600]],'live water',tolerance=180,swimming_representation=13)
        self.assertTrue(all(keys==[0x28] for keys in b.keys))
        self.assertTrue(any(row.get('locomotion')=='swim backwards' for row in b.rows))
        self.assertEqual(b.state['player']['heading'],0)
        self.assertEqual(b.released,1)

    def test_open_water_plan_smooths_lattice_bends_without_crossing_dry_tiles(self):
        row=bytes([88,1,0,128,0,0,7,88,31,2,31,2])
        scene=SceneMap(bytes(32768),row,bytes(256),7)
        plan=scene.plan([0,5120,0],[1600,5120,768],water=True,only_water=True)
        self.assertEqual(len(plan['path']),2)
        self.assertEqual(plan['path'][-1],[1600,5120,768])
        grid=bytearray(32768)
        # A dry cell on the direct line must force a water detour.
        struct.pack_into('<H',grid,((64*128)+65)*2,1)
        dry=bytes([88,1,0,128,0,0,0,88,31,2,31,2])
        scene=SceneMap(grid,row+dry,bytes(256),7)
        plan=scene.plan([0,5120,0],[1600,5120,768],water=True,only_water=True)
        self.assertGreater(len(plan['path']),2)

    def test_swimming_stroke_can_initially_recede_before_making_progress(self):
        elapsed=0
        def stroke(b,keys,updates):
            nonlocal elapsed
            if keys==[0x28]:
                elapsed+=updates
                b.state['player']['position'][2]+=(5 if elapsed<60 else -15)*updates
                b.state['player'].update(action_id=1480,progress=int(elapsed*65536/120)%65536)
        b=Bridge(step=stroke);b.state['player'].update(representation_id=13,action_id=1481,progress=0)
        n=Navigator(b,'water return',[0])
        n.follow_route([[0,0,-600]],'live water',tolerance=180,swimming_representation=13)
        self.assertEqual(n.replans,0)
        self.assertTrue(all(keys==[0x28] for keys in b.keys))
        self.assertTrue(all(row.get('progress_window')==180 for row in b.rows if row.get('action')=='steer'))

    def test_directional_floor_probes_allow_forward_water_drop_but_reject_a_wall(self):
        scene=object.__new__(SceneMap);scene.policy=dict(allowed={})
        def terrain(x,y,z):
            height=5120 if x>=128 else 4096
            return dict(position=[x,height,z],surface=7 if height==5120 else 0,script=0)
        scene.step_floor=terrain
        self.assertIsNotNone(scene.safe(128,4096,0,True,direction=(128,0)))
        self.assertIsNone(scene.safe(128,4096,0,False,direction=(128,0)))
        blocked=object.__new__(SceneMap);blocked.policy=dict(allowed={})
        blocked.step_floor=lambda x,y,z:dict(position=[x,3712 if x>=256 else 4096,z],surface=0,script=0)
        self.assertIsNone(blocked.safe(128,4096,0,False,direction=(128,0)))

    def test_planned_shore_transition_waits_for_real_swimming_and_has_its_own_bound(self):
        from types import SimpleNamespace
        scene=SimpleNamespace(plan=lambda *_a,**kwargs:dict(path=[[0,1024,600]],
            source='live scene',height_ranges={} if kwargs.get('only_water') else {0:[0,1024]}))
        for transition in (True,False):
            def move(b,keys,updates):
                if not keys and transition:
                    b.state['player'].update(position=[0,1024,0],representation_id=13)
                elif 0x26 in keys:b.state['player']['position'][2]+=60
            b=Bridge(step=move);b.state['player']['representation_id']=12
            b.state['player']['position']=[0,0,600]
            n=Navigator(b,'reach water',[0])
            with self.subTest(transition=transition):
                if transition:
                    n.navigate(scene,[0,1024,600],water=True)
                    self.assertEqual(b.keys[0],[])
                    self.assertTrue(any(row.get('outcome')=='SWIMMING' for row in b.rows))
                else:
                    with self.assertRaisesRegex(NavigationFailure,'transition budget'):n.navigate(scene,[0,1024,600],water=True)
                    self.assertEqual(n.updates,180)
                    self.assertTrue(all(not keys for keys in b.keys))
                self.assertGreater(b.released,0)

    def test_moving_target_is_observed_and_fixed_identity_retained(self):
        def step(b,keys,_):
            b.state['player']['position'][2]+=60
            b.state['actors'][602]['position'][2]+=10
        b=Bridge(step=step);n=Navigator(b,'contact',[602],fixed=602)
        self.assertEqual(n.approach(),602)
        self.assertGreater(n.updates,0)
        self.assertEqual(b.released,1)
        self.assertTrue(all(0x11 not in keys for keys in b.keys))
        self.assertGreater(b.rows[-1]['observation']['actors'][602]['position'][2],600)

    def test_height_mismatch_and_fixed_target_cannot_switch(self):
        b=Bridge(actor(602,[0,768,10]));b.state['actors'][284]=actor(284,[0,0,10])
        n=Navigator(b,'contact',[284,602],fixed=602)
        with self.assertRaisesRegex(NavigationFailure,'no eligible'):n.approach()
        self.assertEqual(b.keys,[])
        self.assertEqual(b.rows[0]['rejected'][1]['reason'],'height mismatch; no connected route established')
        self.assertEqual(b.released,1)

    def test_stuck_unknown_blocker_bounded_detours_never_attack(self):
        def turn(b,keys,_):
            b.state['player']['heading'] += (1000 if 0x27 in keys else -1000 if 0x25 in keys else 0)
        b=Bridge(step=turn);b.state['actors'][0]=b.state['player']
        n=Navigator(b,'receive',[602],limits=Limits(window=9,replans=2,updates=600))
        with self.assertRaisesRegex(NavigationFailure,'replan budget'):n.approach()
        detours=[row for row in b.rows if row.get('action')=='local detour']
        self.assertEqual(len(detours),2)
        self.assertNotEqual(detours[0]['path'],detours[1]['path'])
        self.assertEqual(detours[0]['blocker'],'unknown blocker')
        self.assertEqual(detours[0]['nearby'],[])
        self.assertNotIn('progression-locked',str(b.rows))
        self.assertEqual(b.released,1)

    def test_circling_and_dynamic_obstruction_are_evidence_not_guessed_causes(self):
        angles=iter([.1,.2,.3,.4,.5])
        def move(b,keys,_):
            angle=next(angles)
            position=[int(600*math.sin(angle)),0,int(600*math.cos(angle))]
            b.state['player']['position']=position
            b.state['player']['heading']=int(math.atan2(-position[0],-position[2])*65536/(2*math.pi))
            b.state['actors'][284]['position']=[position[0]+50,0,position[2]+20]
        b=Bridge(actor(602,[0,0,0]),step=move)
        b.state['player']['position']=[0,0,600];b.state['player']['heading']=32768
        b.state['actors'][284]=actor(284,[50,0,620])
        n=Navigator(b,'reach',[602],limits=Limits(window=9,replans=1,updates=15))
        with self.assertRaises(NavigationFailure):n.approach()
        row=next(row for row in b.rows if row.get('action')=='local detour')
        self.assertEqual(row['blocker'],'nearby actors observed')
        self.assertEqual(row['trigger'],'circling without progress')
        self.assertEqual(row['nearby'][0]['identity'],284)
        self.assertGreater(row['displacement'],35)

    def test_steady_pursuit_does_not_guess_an_obstacle_from_target_motion(self):
        def move(b,keys,_):
            b.state['player']['position'][2]+=50
            b.state['actors'][602]['position'][2]+=50
        b=Bridge(step=move)
        n=Navigator(b,'reach',[602],limits=Limits(window=9,updates=15))
        with self.assertRaisesRegex(NavigationFailure,'game-update'):n.approach()
        self.assertTrue(any(row.get('action')=='track moving target' for row in b.rows))
        self.assertFalse(any(row.get('action')=='local detour' for row in b.rows))

    def test_connected_route_requires_height_and_retains_unreached_nodes(self):
        b=Bridge();n=Navigator(b,'reach',[602])
        with self.assertRaisesRegex(NavigationFailure,'node height'):
            n.follow_route([[0,768,0]],'published corridor')
        self.assertFalse(any(row.get('outcome')=='WAYPOINT' for row in b.rows))
        self.assertEqual(b.released,1)
        b=Bridge();n=Navigator(b,'reach',[602],limits=Limits(updates=3))
        with self.assertRaisesRegex(NavigationFailure,'game-update'):
            n.follow_route([[0,0,0],[0,0,600]],'published corridor')
        self.assertEqual([row['node'] for row in b.rows if row.get('outcome')=='WAYPOINT'],[0])

    def test_route_height_interval_is_explicit_and_does_not_relax_other_nodes(self):
        for height,allowed in ((4096,True),(4132,True),(5120,True),(6000,False)):
            b=Bridge();b.state['player']['position']=[0,height,0]
            n=Navigator(b,'water approach',[0])
            with self.subTest(height=height):
                if allowed:n.follow_route([[0,4460,0]],'recorded water transition',height_ranges={0:[4096,5120]})
                else:
                    with self.assertRaisesRegex(NavigationFailure,'height mismatch'):
                        n.follow_route([[0,4460,0]],'recorded water transition',height_ranges={0:[4096,5120]})
        b=Bridge();b.state['player']['position']=[0,4132,0]
        n=Navigator(b,'water approach',[0])
        with self.assertRaisesRegex(NavigationFailure,'height mismatch'):
            n.follow_route([[0,4460,0],[0,4460,600]],'ordinary node stays strict',height_ranges={1:[4096,5120]})
        with self.assertRaisesRegex(ValueError,'height range'):
            n.follow_route([[0,4460,0]],'bad declaration',height_ranges={1:[4096,5120]})

    def test_narrow_route_corner_is_reached_before_turn_with_short_samples(self):
        samples=[]
        def move(b,keys,updates):
            samples.append(updates)
            b.state['player']['position'][2]+=30*updates
        b=Bridge(step=move);n=Navigator(b,'water approach',[0])
        n.follow_route([[0,0,150],[0,0,400]],'recorded bank',tolerance=180,node_tolerances={0:80})
        nodes=[row for row in b.rows if row.get('outcome')=='WAYPOINT']
        self.assertEqual([row['node'] for row in nodes],[0,1])
        self.assertEqual(nodes[0]['observation']['player']['position'],[0,0,90])
        self.assertEqual(samples,[1,1,1,3,3])
        self.assertEqual(n.updates,9)
        self.assertEqual(b.released,1)
        for overrides in ({2:80},{0:0},{0:181}):
            with self.assertRaisesRegex(ValueError,'node tolerance'):
                n.follow_route([[0,0,150]],'invalid',tolerance=180,node_tolerances=overrides)

    def test_route_discontinuity_stops_before_steering_from_unproved_position(self):
        def jump(b,keys,updates):b.state['player']['position']=[7000,0,0]
        b=Bridge(step=jump);n=Navigator(b,'water approach',[0])
        with self.assertRaisesRegex(NavigationFailure,'movement discontinuity'):
            n.follow_route([[0,0,600]],'recorded bank')
        self.assertEqual(len(b.keys),1)
        self.assertEqual(b.released,1)
        failure=next(row for row in b.rows if row.get('outcome')=='FAIL')
        self.assertEqual(failure['previous'],[0,0,0])
        self.assertEqual(failure['observation']['player']['position'],[7000,0,0])
        self.assertFalse(any(row.get('outcome')=='WAYPOINT' for row in b.rows))

    def test_equal_observations_have_deterministic_ties_and_attack_eligibility(self):
        choices=[]
        for _ in range(2):
            b=Bridge(actor(602,[0,0,100]));b.state['actors'][284]=actor(284,[0,0,100])
            n=Navigator(b,'reach',[602,284]);choices.append(n.approach())
        self.assertEqual(choices,[284,284])
        b=Bridge(actor(602,[0,0,100]));n=Navigator(b,'receive_one_hit',[602])
        with self.assertRaisesRegex(NavigationFailure,'eligible'):n.approach()
        self.assertEqual(b.rows[0]['rejected'][0]['reason'],'no original NPC attack slots available')

    def test_fixed_instance_survives_repeated_approach_without_reselection(self):
        b=Bridge(actor(602,[0,0,100]));n=Navigator(b,'contact',[602],fixed=602)
        n.approach();b.state['actors'][602]['pointer']+=1
        with self.assertRaisesRegex(NavigationFailure,'instance changed'):n.approach()
        self.assertEqual(b.released,2)

    def test_disappeared_dead_replaced_and_height_changed_targets_fail(self):
        for change in ('missing','dead','replaced','height'):
            def step(b,keys,updates):
                if change=='missing':del b.state['actors'][602]
                elif change=='dead':b.state['actors'][602]['health']=0
                elif change=='replaced':b.state['actors'][602]['pointer']+=1
                else:b.state['actors'][602]['position'][1]=768
            b=Bridge(step=step);n=Navigator(b,'reach',[602])
            with self.subTest(change=change),self.assertRaises(NavigationFailure):n.approach()
            self.assertEqual(b.released,1)

    def test_update_host_and_interruption_bounds_release(self):
        b=Bridge();n=Navigator(b,'reach',[602],limits=Limits(updates=3))
        with self.assertRaisesRegex(NavigationFailure,'game-update'):n.approach()
        b=Bridge();times=iter([0,100]);n=Navigator(b,'reach',[602],clock=lambda:next(times))
        with self.assertRaisesRegex(NavigationFailure,'host-time'):n.approach()
        self.assertEqual(b.released,1)
        def interrupt(*_):raise KeyboardInterrupt()
        b=Bridge(step=interrupt);n=Navigator(b,'reach',[602])
        with self.assertRaises(KeyboardInterrupt):n.approach()
        self.assertEqual(b.rows[-1]['outcome'],'INTERRUPTED')
        self.assertEqual(b.released,1)

    def test_receive_releases_attack_and_requires_attributed_hit(self):
        for attributed in (True,False):
            def step(b,keys,updates):b.state['player']['health']=95
            b=Bridge(actor(602,[0,0,180]),step=step);n=Navigator(b,'receive',[602])
            n.approach()
            if attributed:self.assertEqual(n.receive(100,lambda _:[dict(attacker=602)]),95)
            else:
                with self.assertRaisesRegex(NavigationFailure,'without attributed'):n.receive(100,lambda _:[])
            self.assertEqual(b.keys,[[]]);self.assertEqual(b.released,2)

    def test_approach_stops_on_attributed_hit_outside_distance_threshold(self):
        def hit(b,keys,_):b.state['player']['health']=95
        b=Bridge(step=hit);n=Navigator(b,'receive',[602])
        n.approach(100,lambda _:[dict(attacker=602)])
        self.assertEqual(n.updates,3)
        self.assertEqual(b.rows[-1]['reason'],'attributed hit during approach')
        self.assertGreater(b.rows[-1]['observation']['actors'][602]['position'][2],n.limits.reach)
        self.assertEqual(b.released,1)

    def test_known_original_hit_geometry_can_complete_approach_with_real_attribution(self):
        # Successful ASan C geometry: centers are 379 units apart, in front
        # of the west-facing guard. The original node can hit from this pose.
        guard=actor(284,[6880,4096,-17450]);guard.update(radius=256,heading=-18429,attack_slots=[344,354])
        def hit(b,keys,_):
            self.assertFalse(0x11 in keys or 32 in keys)
            b.state['player']['health']=95
        b=Bridge(guard,step=hit);b.state['actors']={284:guard}
        b.state['player'].update(position=[6519,4096,-17334],radius=256)
        n=Navigator(b,'receive_one_hit',[284],fixed=284)
        self.assertEqual(n.approach(100,lambda identity:[dict(attacker=identity)]),284)
        self.assertEqual(n.updates,3)
        self.assertLess(next(row['aim'][0] for row in b.rows if row.get('aim')),guard['position'][0])
        self.assertEqual(n.receive(100,lambda identity:[dict(attacker=identity)]),95)
        self.assertEqual(len(b.keys),1)
        self.assertEqual(b.released,2)

    def test_contact_radius_alone_cannot_credit_failed_pursuit_geometry(self):
        guard=actor(284,[7023,4096,-17574]);guard.update(radius=256,heading=-18429,attack_slots=[344,354])
        b=Bridge(guard);b.state['actors']={284:guard}
        b.state['player'].update(position=[7126,4096,-17215],radius=256)
        n=Navigator(b,'receive_one_hit',[284],fixed=284,limits=Limits(updates=3))
        with self.assertRaisesRegex(NavigationFailure,'game-update'):n.approach()
        self.assertFalse(any(row.get('outcome')=='REACHED' for row in b.rows))
        self.assertTrue(b.keys[0])

    def test_facing_guidance_only_changes_receive_hit_and_keeps_real_hit_required(self):
        for goal in ('receive_one_hit','contact'):
            guard=actor(602,[0,0,400]);guard.update(radius=256,heading=32768,attack_slots=[344])
            b=Bridge(guard);b.state['player']['radius']=256
            n=Navigator(b,goal,[602],fixed=602,limits=Limits(updates=3))
            if goal=='receive_one_hit':
                n.approach()
                with self.assertRaisesRegex(NavigationFailure,'game-update'):n.receive(100,lambda _:[])
                self.assertEqual(b.keys,[[]])
            else:
                with self.assertRaisesRegex(NavigationFailure,'game-update'):n.approach()
                self.assertEqual(next(row['reach'] for row in b.rows if row.get('action')=='steer'),240)
            self.assertFalse(any(row.get('outcome')=='PASS' for row in b.rows))

    def test_receive_hit_does_not_wait_behind_moving_opponent(self):
        guard=actor(602,[0,0,0]);guard.update(radius=256,attack_slots=[344])
        b=Bridge(guard);b.state['player'].update(position=[0,0,-50],radius=256)
        n=Navigator(b,'receive_one_hit',[602],fixed=602)
        n.select(b.observe())
        n.step(b.observe(),wait=True)
        self.assertTrue(b.keys[-1])
        self.assertEqual(b.rows[-1]['contact_policy'],'outside encounter collision disc')
        self.assertLess(b.rows[-1]['aim'][2],-50)
        self.assertEqual(b.rows[-1]['reach'],64)
        self.assertEqual(b.rows[-1]['wait_reach'],64)

    def test_receive_hit_can_select_other_audited_guard_on_same_floor(self):
        b=Bridge();b.state['actors']={293:actor(293,[0,0,100])}
        b.state['actors'][293]['attack_slots']=[344]
        n=Navigator(b,'receive_one_hit',[284,293])
        self.assertEqual(n.approach(),293)
        self.assertEqual(b.rows[0]['rejected'],[dict(identity=284,reason='target disappeared or left active table')])
        b.state['actors'][293]['position'][1]=512
        n=Navigator(b,'receive_one_hit',[284,293])
        with self.assertRaisesRegex(NavigationFailure,'eligible'):n.approach()

    def test_receive_hit_reselects_only_with_permission_and_remaining_budget(self):
        for fixed,replans,expected in ((None,1,293),(284,1,None),(None,0,None)):
            b=Bridge();b.state['actors']={identity:actor(identity,[0,0,100]) for identity in (284,293)}
            for guard in b.state['actors'].values():guard['attack_slots']=[344]
            n=Navigator(b,'receive_one_hit',[284,293],fixed=fixed,limits=Limits(replans=replans))
            n.approach();self.assertEqual(n.target,284)
            del b.state['actors'][284]
            if expected:
                self.assertEqual(n.approach(),expected)
                self.assertEqual(n.replans,1)
                self.assertTrue(any(row.get('action')=='reselect eligible opponent' for row in b.rows))
                self.assertFalse(any(row.get('outcome')=='PASS' for row in b.rows))
            else:
                with self.assertRaises(NavigationFailure):n.approach()

    def test_receive_hit_does_not_reuse_replaced_instance(self):
        guard=actor(284,[0,0,100]);guard['attack_slots']=[344]
        b=Bridge(guard);b.state['actors']={284:guard}
        n=Navigator(b,'receive_one_hit',[284,293]);n.approach()
        b.state['actors'][284]['pointer']+=1
        with self.assertRaisesRegex(NavigationFailure,'instance changed'):n.approach()

    def test_detour_progress_does_not_use_distance_to_the_enemy(self):
        def step(b,keys,_):
            b.state['player']['position'][0]+=50
        b=Bridge(actor(602,[0,0,600]),step=step)
        b.state['player']['heading']=16384
        n=Navigator(b,'reach',[602],limits=Limits(window=9,updates=12))
        n.select(b.observe());n.detour=[1000,0,0]
        with self.assertRaisesRegex(NavigationFailure,'game-update'):n.approach()
        self.assertFalse(any(row.get('action')=='local detour' for row in b.rows))

    def test_scene_actor_must_become_represented_before_enemy_eligibility(self):
        def ready(b,keys,_):b.state['actors'][602]['representation']=1
        b=Bridge(step=ready);b.state['actors'][602]['representation']=0
        n=Navigator(b,'contact',[602],fixed=602)
        n.await_actor(602)
        self.assertEqual(b.keys,[[]])
        self.assertEqual(b.rows[-1]['outcome'],'READY')
        b=Bridge();b.state['actors'][602]['representation']=0
        n=Navigator(b,'contact',[602],fixed=602)
        with self.assertRaisesRegex(NavigationFailure,'readiness budget'):n.await_actor(602,updates=3)
        self.assertFalse(any(row.get('outcome')=='READY' for row in b.rows))
        self.assertEqual(b.released,1)
        b=Bridge();b.state['actors'][602]['active']=False
        n=Navigator(b,'contact',[602],fixed=602)
        with self.assertRaisesRegex(NavigationFailure,'absent or dead'):n.await_actor(602)
        self.assertEqual(b.keys,[])

    def test_opening_crossing_corrects_heading_and_requires_the_gate(self):
        def move(b,keys,_):
            player=b.state['player']
            if 0x25 in keys:player['heading']-=2500
            if 0x27 in keys:player['heading']+=2500
            if 0x26 in keys:player['position'][2]-=60
        b=Bridge(step=move);b.state['player'].update(position=[0,0,400],heading=16384)
        n=Navigator(b,'cross_destroyed_door',[980],fixed=980)
        result=n.cross_opening(980,[0,0,0],(0,-1))
        self.assertTrue(result['crossed']);self.assertGreater(result['forward'],100)
        self.assertTrue(any(0x25 in keys or 0x27 in keys for keys in b.keys))
        self.assertTrue(any(row.get('outcome')=='CROSSED' for row in b.rows))
        self.assertFalse(any(0x11 in keys for keys in b.keys))
        self.assertEqual(b.released,1)

    def test_opening_bypass_and_wrong_floor_cannot_pass(self):
        for destination,reason in (([1000,0,-400],'outside required opening'),
                                   ([0,768,-400],'height mismatch')):
            def move(b,keys,_):b.state['player']['position']=destination
            b=Bridge(step=move);b.state['player'].update(position=[0,0,400],heading=32768)
            n=Navigator(b,'cross_destroyed_door',[980],fixed=980)
            with self.subTest(reason=reason),self.assertRaisesRegex(NavigationFailure,reason):
                n.cross_opening(980,[0,0,0],(0,-1))
            self.assertFalse(any(row.get('outcome')=='PASS' for row in b.rows))
            self.assertEqual(b.released,1)

    def test_opening_stuck_and_interruption_preserve_failure_and_release(self):
        b=Bridge();b.state['player'].update(position=[0,0,400],heading=32768)
        n=Navigator(b,'cross_destroyed_door',[980],fixed=980,limits=Limits(updates=6))
        with self.assertRaisesRegex(NavigationFailure,'game-update'):
            n.cross_opening(980,[0,0,0],(0,-1))
        self.assertEqual(b.released,1)
        def interrupt(*_):raise KeyboardInterrupt()
        b=Bridge(step=interrupt);b.state['player'].update(position=[0,0,400],heading=32768)
        n=Navigator(b,'cross_destroyed_door',[980],fixed=980)
        with self.assertRaises(KeyboardInterrupt):n.cross_opening(980,[0,0,0],(0,-1))
        self.assertEqual(b.rows[-1]['outcome'],'INTERRUPTED');self.assertEqual(b.released,1)

    def test_opening_cannot_substitute_identity_or_credit_unobserved_crossing(self):
        b=Bridge();b.state['player']['position']=[0,0,-500]
        n=Navigator(b,'cross_destroyed_door',[980],fixed=980)
        with self.assertRaisesRegex(ValueError,'outside the declared goal'):
            n.cross_opening(981,[0,0,0],(0,-1))
        with self.assertRaisesRegex(NavigationFailure,'not observed from approach side'):
            n.cross_opening(980,[0,0,0],(0,-1))
        self.assertEqual(b.keys,[]);self.assertEqual(b.released,1)

    def test_receive_keeps_failure_when_player_dies(self):
        def step(b,keys,updates):b.state['player']['health']=0
        b=Bridge(actor(602,[0,0,180]),step=step);n=Navigator(b,'receive',[602]);n.approach()
        with self.assertRaisesRegex(NavigationFailure,'survive'):n.receive(100,lambda _:[1])
        self.assertEqual(b.released,2)


if __name__=='__main__':unittest.main()
