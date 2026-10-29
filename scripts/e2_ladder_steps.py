"""Fresh-game, input-only stables/kitchen ladder regression inside GDB."""
import json
import math
from pathlib import Path

import gdb

from e2_save_load_steps import PersistenceJourney
from e2_gameplay_steps import Journey


class LadderJourney(PersistenceJourney):
    def __init__(self, prefix, runtime, game_data, watch=False):
        super().__init__(prefix, {'checks':['Menus.Gameplay.SaveDialog']}, watch,
                         'Stables ladder down/up', game_data, 0, False)
        self.runtime = runtime
        self.held = {}
        self.route = []

    def state(self, label):
        if label not in ('navigation','descent','ascent'):
            return super().state(label)
        # Hot navigation observations do not rewrite the full population census.
        # Every reached waypoint and each completed climb records/checks it.
        actor = self.value('DAT_0047a470')
        field = lambda offset:self.value(f'*(short*)({actor}+{offset})')
        return dict(label=label,actor=actor,health=field(0xec),state=field(0x82),
                    position=[field(offset) for offset in (0x84,0x86,0x88)],
                    camera=(self.value('_DAT_0073cc3c')-0x67c728)//28,
                    modal=self.value('_DAT_00643650'),wait=self.value('DAT_0047a76c'))

    def key(self, key, down):
        if self.held.get(key, False) != down:
            super().key(key, down)
            self.held[key] = down

    def release(self):
        for key in list(self.held):
            self.key(key, False)

    def heading(self, x, z):
        state = self.state('navigation')
        if state['health'] <= 0 or state['state'] in (5,8,11):
            self.details['navigation_failure'] = state
            self.save()
            raise gdb.GdbError('Ladder route did not retain a living player: '+str(state))
        position = state['position']
        actor = state['actor']
        yaw = self.value(f'*(short*)({actor}+0x92)')
        target = round(math.atan2(x-position[0], z-position[2])*65536/(2*math.pi))
        return state, (target-yaw+32768)%65536-32768

    def traverse(self):
        route = json.loads((Path(__file__).parent/'scenarios/stables-ladder-waypoints.json').read_text())
        self.details['navigation_source'] = route['source']
        actor = self.value('DAT_0047a470')
        field = lambda offset,kind='short':self.value(f'*({kind}*)({actor}+{offset})')
        context = dict(value=self.value,field=field,actor=actor,prefix=self.prefix+'-traversal',
                       advance=self.step,key=self.key)
        traversal = Journey(context,'stables-ladder',{})

        def reached(index):
            state = self.state('waypoint')
            state.update(source_snapshot=route['waypoints'][index]['snapshot'],update=self.updates,
                         held=dict(self.held))
            self.route.append(state)
            self.details['route'] = self.route
            self.save()

        # One connected route through the shared walker: keep held movement
        # across intermediate points; release only at the ladder approach.
        points = [(row.get('target',row['position'])[0],row.get('target',row['position'])[2])
                  for row in route['waypoints']]
        try:
            traversal.walk(points,tolerance=110,on_waypoint=reached)
        except BaseException:
            self.details['navigation_failure'] = self.state('traversal-failure')
            self.save()
            raise
        traversal.complete = True
        traversal.save()

    def face(self, x, z):
        self.release()
        for _ in range(150):
            _, delta = self.heading(x, z)
            if abs(delta) < 700:
                self.release();self.step(3)
                return
            self.key(37, delta < 0)
            self.key(39, delta > 0)
            self.step()
        raise gdb.GdbError('Ladder facing exceeded its input bound')

    def climb(self, direction, camera, height, expected_scenes):
        self.release()
        starting_health = self.state(direction+'-start')['health']
        self.key(32,True);self.step(4);self.key(32,False)
        seen = []
        samples = []
        for _ in range(700):
            state = self.state(direction)
            owner = self.value('*(unsigned int*)(DAT_0047a470+0x132)')
            scene = self.value(f'*(short*){owner}') if owner else -1
            if scene >= 0 and scene not in seen:
                seen.append(scene)
            sample = dict(camera=state['camera'],scene=scene,height=state['position'][1],wait=state['wait'])
            if not samples or sample != samples[-1]:
                samples.append(sample)
            if state['camera']==camera and state['position'][1]==height and scene==-1 and not state['wait']:
                break
            self.step()
        else:
            self.details[direction] = dict(scenes=seen,samples=samples,last=state)
            self.save()
            raise gdb.GdbError('Ladder '+direction+' did not complete within 700 updates')
        self.require(all(identity in seen for identity in expected_scenes),
                     f'Ladder {direction} missed original scenes {expected_scenes}: {seen}')
        self.require(state['health']==starting_health and starting_health>0 and not state['modal'],
                     'Ladder lost living nonmodal control or changed health')
        before = self.value('*(short*)(DAT_0047a470+0x92)')
        self.key(37,True);self.step(8);self.release();self.step(4)
        self.require(self.value('*(short*)(DAT_0047a470+0x92)') != before,
                     'Ladder completion did not restore turning control')
        self.details[direction] = dict(passed=True,scenes=seen,samples=samples,landing=state,
                                      starting_health=starting_health,control_resumed=True)
        self.state(direction+'-complete')
        self.save()


def run(prefix, runtime, game_data, watch=False):
    journey = LadderJourney(prefix,runtime,game_data,watch)
    journey.frame = gdb.Breakpoint('FUN_00415d40',internal=True)
    journey.frame.condition = journey.HORSE
    gdb.execute('run --game-data-dir '+json.dumps(game_data)+' --data-dir '+json.dumps(runtime)+
                ' --record off --run-recon',to_string=True)
    journey.require(gdb.selected_frame().name()=='FUN_00415d40','Opening boundary not reached')
    journey.frame.condition = None
    journey.initial = journey.state('initial')
    journey.reach_pedestal();journey.reach_gameplay()
    journey.require(journey.value('*(int*)0x47ab28')==100,'Fresh game did not initialize original power100')
    journey.details['seed'] = 'fresh game; no Load, save patch or actor-state assignment'
    journey.traverse()
    journey.require(journey.state('upper-landing')['camera']==725,'Did not reach original upper ladder landing')
    journey.face(-18392,-14300)
    journey.climb('descent',723,6656,(761,762))
    journey.face(-18800,-14112)
    journey.climb('ascent',725,4096,(763,764))
    journey.require(journey.value('E2R_audio_frames')==journey.value('E2R_music_frames')==0,
                    'Non-audio ladder regression produced audio output')
    journey.details['audio_output'] = 'off'
    journey.release();journey.stage='Gameplay';journey.quit()
    journey.complete=True;journey.save()
    result = dict(probe_complete=True,native_exit_code=journey.exit_codes[-1],updates=journey.updates,
                  population_profile='noncombat-ladder',recording='off',details=journey.details)
    Path(prefix+'.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: fresh-game ladder descent/ascent, original scene sequences, both landings and resumed control; silent clean exit',flush=True)
