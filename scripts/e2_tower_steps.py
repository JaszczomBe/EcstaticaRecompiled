"""Bounded tower journeys inside GDB. Game state is observation-only."""
import json
import math
from pathlib import Path

import gdb

from e2_save_load_steps import PersistenceJourney
from e2_object_render import observe, watch_rasters

OWNERS = (259, 264, 265, 266, 443)
RENDER_OWNERS = (259, 264, 265, 266, 2628)
SCENES = (65, 68, 83, 84, 86, 2004)


class TowerJourney(PersistenceJourney):
    def __init__(self, prefix, runtime, game_data):
        super().__init__(prefix, {'checks': ['Menus.Gameplay.SaveDialog']}, False,
                         'tower progression', game_data, 0, False)
        self.runtime = runtime
        self.held = {}
        self.samples = []

    def key(self, key, down):
        if self.held.get(key, False) != down:
            super().key(key, down)
            self.held[key] = down

    def release(self):
        for key in list(self.held):
            self.key(key, False)

    def pointer(self, identity):
        return self.value(f'*(unsigned int*)({0x630b60 + identity * 4})')

    def field(self, identity, offset):
        pointer = self.pointer(identity)
        self.require(pointer != 0, 'Missing original tower actor ' + str(identity))
        return self.value(f'*(short*)({pointer}+{offset})')

    def world(self):
        result = super().world()
        result['tower_scenes'] = {str(i): self.value(f'*(unsigned short*)({0x670c38 + i * 2})')
                                  for i in SCENES}
        return result

    def compare_world(self, expected, actual):
        super().compare_world(expected, actual)
        self.require(expected['tower_scenes'] == actual['tower_scenes'],
                     'Tower scene phases changed across Save/Load')

    def sample(self, label):
        result = self.world()
        result.update(label=label, updates=self.updates)
        self.samples.append(result)
        Path(self.prefix + '-states.json').write_text(json.dumps(self.samples, indent=2) + '\n')
        observe(self.prefix, label, [0, *OWNERS, 2628])
        print('TOWER ' + label + ': ' + json.dumps(result['player']), flush=True)
        return result

    def face(self, x, z):
        for _ in range(150):
            player = self.state('face')['position']
            angle = int(math.atan2(x - player[0], z - player[2]) * 65536 / (2 * math.pi))
            delta = (angle - self.field(0, 0x92) + 32768) % 65536 - 32768
            if abs(delta) < 700:
                self.release()
                return
            self.key(37, delta < 0)
            self.key(39, delta > 0)
            self.step()
        raise gdb.GdbError('Tower facing input exceeded its bound')

    def walk(self, x, z, tolerance=130):
        for _ in range(220):
            player = self.state('walk')['position']
            if math.hypot(x - player[0], z - player[2]) < tolerance:
                self.release()
                self.step(4)
                return
            angle = int(math.atan2(x - player[0], z - player[2]) * 65536 / (2 * math.pi))
            delta = (angle - self.field(0, 0x92) + 32768) % 65536 - 32768
            self.key(37, delta < -800)
            self.key(39, delta > 800)
            self.key(38, abs(delta) < 4500)
            self.step()
        self.sample('failed-waypoint')
        raise gdb.GdbError(f'Tower waypoint {(x, z)} was not reached: {player}')

    def load_initial(self, slot, expected=None):
        if expected is not None:
            self.menu_load(slot, expected)
            return
        self.open()
        self.click(0x643cc4)
        self.pump()
        self.requester(0x29)
        self.click(0x642fb0 + slot * 30)
        self.pump()
        self.require(self.value('_DAT_0064353c') == slot, 'Wrong initial tower slot')
        entry = gdb.Breakpoint('FUN_004544a4', internal=True)
        self.click(0x643de4)
        self.menu.enabled = self.frame.enabled = False
        gdb.execute('continue', to_string=True)
        self.require(gdb.selected_frame().name() == 'FUN_004544a4', 'Initial loader was not reached')
        entry.delete()
        finished = gdb.FinishBreakpoint(internal=True)
        gdb.execute('continue', to_string=True)
        self.require(not finished.is_valid(), 'Initial loader did not return')
        self.menu.enabled = self.frame.enabled = True
        for _ in range(12):
            gdb.execute('continue', to_string=True)
            if (self.value('_DAT_00643650') == 0 and
                    self.value('*(unsigned short*)((char*)&DAT_0047a45e+2)') == 0):
                break
        else:
            raise gdb.GdbError('Initial Load did not dismiss its requester')
        self.menu.delete()
        self.menu = None
        self.step(3)

    def capture(self, label):
        self.present()
        gdb.execute('call (int)e2r_write_surface_set(' + json.dumps(self.prefix + '-' + label) + ')',
                    to_string=True)

    def require_stage(self, stage):
        state = self.world()
        key = state['actors'].get('264')
        attachment = key['attachment'] if key else None
        if stage == 'before':
            self.require(attachment is None and self.field(264, 0x86) == -3776,
                         'Original pre-acquisition key state differs')
            self.require(self.field(443, 0x86) == -3328, 'Closed blocker was displaced')
        elif stage == 'key':
            self.require(attachment and attachment['owner'] == 0 and attachment['node'] == 7
                         and attachment['reciprocal'], 'Key was not acquired in Joe\'s original hand')
            self.require(state['tower_scenes']['83'] & 4, 'Key-drop scene did not finish')
            self.require(self.field(443, 0x86) == -3328, 'Door opened before key use')
        elif stage == 'door':
            self.require(attachment and attachment['owner'] == 266 and attachment['node'] == 8
                         and attachment['reciprocal'], 'Key did not transfer to the authored door socket')
            self.require(state['tower_scenes']['68'] & 4, 'Original door scene did not finish')
            self.require(self.field(443, 0x86) == -4032, 'Original blocker track did not move')
            self.require(self.field(0, 0x84) < -19550, 'Joe did not actually pass the door')
        self.require(self.field(0, 0xec) > 0 and state['player']['modal'] == 0,
                     'Tower stage lost living, nonmodal control')
        self.sample('accepted-' + stage)

    def persistence(self, stage, slot):
        self.release()
        self.require_stage(stage)
        expected_path = Path(self.prefix).parent / (stage + '-expected.json')
        expected = self.menu_save(slot, 'E2RTOWER', expected_path)
        saved = Path(self.runtime) / 'Saved' / f'{slot:04d}.ECS'
        (Path(self.prefix).parent / (stage + '.ECS')).write_bytes(saved.read_bytes())
        self.menu_load(slot, expected)
        self.require_stage(stage)


def run(prefix, runtime, game_data, load_slot, save_slot, mode, expected_path=None):
    journey = TowerJourney(prefix, runtime, game_data)
    journey.frame = gdb.Breakpoint('FUN_00415d40', internal=True)
    journey.frame.condition = journey.HORSE
    gdb.execute('run --game-data-dir ' + json.dumps(game_data) + ' --data-dir ' +
                json.dumps(runtime) + ' --record off --run-recon', to_string=True)
    journey.require(gdb.selected_frame().name() == 'FUN_00415d40', 'Opening boundary not reached')
    journey.frame.condition = None
    expected = json.loads(Path(expected_path).read_text()) if expected_path else None
    journey.load_initial(load_slot, expected)
    journey.require(journey.state('loaded')['camera'] == 28, 'Save did not restore tower camera 28')
    journey.sample('loaded')
    if mode.startswith('fresh-'):
        journey.require_stage(mode.removeprefix('fresh-'))
        # Resume ordinary input after the independent load, preserving puzzle ownership.
        before = journey.field(0, 0x92)
        journey.key(37, True)
        journey.step(8)
        journey.release()
        journey.step(8)
        journey.require(journey.field(0, 0x92) != before, 'Fresh Load did not resume turning')
    elif mode == 'locked':
        journey.walk(-18600, -1700)
        journey.walk(-19032, -1792)
        journey.face(-19456, -1792)
        journey.key(38, True)
        journey.step(45)
        journey.release()
        state = journey.sample('locked-attempt')
        journey.require(not state['tower_scenes']['68'] & 2 and journey.field(443, 0x86) == -3328
                         and journey.field(0, 0x84) > -19456,
                         'Door permitted passage without the original key')
    else:
        from e2_geometry_steps import check_modes
        from e2_hud_steps import HudChecks
        hud = HudChecks(journey)
        hud.check_default()
        journey.persistence('before', save_slot)
        rasters = watch_rasters(prefix, list(RENDER_OWNERS))
        journey.step(5)
        journey.capture('before')
        check_modes(prefix, 'tower-before')
        journey.face(-18468, -534)
        journey.key(17, True)
        journey.key(38, True)
        journey.step(40)
        journey.release()
        journey.step(90)
        journey.require(journey.field(264, 0x84) == -18292 and journey.field(264, 0x86) == -3328,
                         'Striking the head did not complete the original key-drop track')
        journey.sample('key-dropped')
        journey.capture('key-dropped')
        journey.walk(-18292, -1088, tolerance=280)
        journey.face(-18292, -1088)
        journey.key(32, True)
        journey.step(3)
        journey.key(32, False)
        journey.step(90)
        journey.persistence('key', save_slot)
        journey.walk(-18600, -1700)
        journey.walk(-19032, -1792)
        journey.face(-19456, -1792)
        journey.key(38, True)
        for _ in range(450):
            journey.step()
            if journey.field(0, 0x84) < -19550:
                break
        else:
            journey.sample('door-passage-failed')
            raise gdb.GdbError('Ordinary input did not pass the keyed door')
        journey.release()
        journey.step(3)
        journey.capture('door-open')
        journey.persistence('door', save_slot)
        check_modes(prefix, 'tower-door-open')
        hud.switches('tower-door-open')
        for breakpoint in rasters:
            breakpoint.delete()
        pixels = json.loads(Path(prefix + '-raster.json').read_text())
        journey.require(all(pixels.get(str(i), {}).get('writes') for i in RENDER_OWNERS),
                         'An enabled tower owner has no observed original pixel writes')
    journey.stage = 'Gameplay'
    journey.quit()
    journey.complete = True
    journey.save()
    result = dict(probe_complete=True, mode=mode, updates=journey.updates,
                  native_exit_code=journey.exit_codes[-1], details=journey.details)
    Path(prefix + '.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: tower ' + mode, flush=True)
