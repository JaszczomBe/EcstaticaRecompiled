"""Bounded SDL display selections and pixel checks at stopped native frame boundaries."""
import hashlib
import json
from pathlib import Path

import gdb


class HudChecks:
    def __init__(self, journey):
        self.journey = journey
        self.rows = journey.details.setdefault('hud', [])

    def value(self, expression):
        return self.journey.value(expression)

    def check_mode(self, mode):
        self.journey.require(self.value('E2R_DebugOverlaySelected()') == mode,
                             'Presentation selection changed across menu/Save/Load')

    def check_default(self):
        self.check_mode(0)
        self.rows.append(dict(default_original=True))
        self.journey.save()


    def select(self, mode, label, geometry=False):
        # Real SDL scancodes, including repeated key-down and a final release.
        key = 0x40000000 | (60 if geometry else (59 if mode else 58))
        for down, repeat in ((True, False), (True, True), (False, False)):
            gdb.execute('set $hud_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))', to_string=True)
            for member, number in [('type', 0x300 if down else 0x301), ('down', int(down)),
                                   ('repeat', int(repeat)), ('key', key), ('scancode', key & 0xffff)]:
                gdb.execute(f'set $hud_event->key.{member}={number}', to_string=True)
            gdb.execute('set $hud_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)', to_string=True)
            self.journey.require(self.value('SDL_PushEvent($hud_event)') == 1, 'HUD SDL event rejected')
            gdb.execute('call (void)free($hud_event)', to_string=True)
            gdb.execute('call e2r_poll_host_events("hud-check")', to_string=True)
            if down and not repeat:
                for event_type in (0x20f, 0x20e):  # SDL focus lost, then gained before key release.
                    gdb.execute('set $hud_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))', to_string=True)
                    gdb.execute(f'set $hud_event->window.type={event_type}', to_string=True)
                    gdb.execute('set $hud_event->window.windowID=SDL_GetWindowID(e2r_sdl_backend.window)', to_string=True)
                    self.journey.require(self.value('SDL_PushEvent($hud_event)') == 1, 'HUD focus event rejected')
                    gdb.execute('call (void)free($hud_event)', to_string=True)
                    gdb.execute('call e2r_poll_host_events("hud-focus")', to_string=True)
        if geometry:
            self.journey.require(self.value('E2R_GeometryMode()') == mode,
                                 'F3 repeated or failed to cycle geometry')
        else:
            self.check_mode(mode)

    def page_bytes(self):
        pages = []
        size = self.value('_DAT_006401ec * _DAT_006401d4')
        for surface in range(4):
            base = self.value(f'e2r_surface_framebuffer({surface})')
            pages.append(bytes(gdb.selected_inferior().read_memory(base, size)))
        return pages

    def capture(self, label, gameplay=True):
        self.journey.present()
        gdb.execute('set $hud_state=(E2R_HudState*)calloc(1,sizeof(E2R_HudState))', to_string=True)
        gdb.execute('call E2R_GetOriginalHudState($hud_state)', to_string=True)
        if gameplay:
            self.journey.require(self.value('$hud_state->visible') == 1, 'Original HUD visibility gate is closed during gameplay')
        print('HUD native snapshot: '+gdb.execute('p *$hud_state', to_string=True), flush=True)
        print('HUD gates: '+str({name:self.value(name) for name in ('*(unsigned int*)0x630b60','_DAT_00630b60','DAT_0047a76c','DAT_0047a448','DAT_0047a34a','DAT_0047a45e')}), flush=True)
        gdb.execute('call (void)free($hud_state)', to_string=True)
        prefix = self.journey.prefix + '-hud-' + label
        gdb.execute('call (int)e2r_write_surface_set(' + json.dumps(prefix) + ')', to_string=True)
        gdb.execute('call (int)E2R_HostDumpPresentation(&e2r_sdl_backend,' + json.dumps(prefix) + ')', to_string=True)
        surface = gdb.parse_and_eval('e2r_sdl_backend.present_surface').dereference()
        width, height, pitch = [int(surface[field]) for field in ('w', 'h', 'pitch')]
        pixels = bytes(gdb.selected_inferior().read_memory(int(surface['pixels']), height * pitch))
        if gameplay and not self.value('E2R_DebugOverlaySelected()'):
            self.journey.require(self.value('e2r_hud_pixels != 0'), 'Original HUD was not composed during gameplay')
            indexed = bytes(gdb.selected_inferior().read_memory(self.value('e2r_hud_pixels'), width * height))
            Path(prefix + '-composed.pgm').write_bytes(f'P5\n{width} {height}\n255\n'.encode() + indexed)
            actor = self.value('*(unsigned int*)0x630b60')
            life = self.value(f'*(short*)({actor}+0xec)')
            maximum = self.value(f'*(short*)({actor}+0xee)')
            scale = maximum // 100
            if scale in (1, 2, 3) and 0 <= life <= maximum and not self.value('DAT_0047ab2c'):
                y = 22 if scale == 3 else 24
                row = indexed[y * width + 69:y * width + 169]
                expected = bytes([11]) * (life // scale) + bytes([13]) * (100 - life // scale)
                self.journey.require(row == expected, 'Composed life pixels differ from original life/max scaling')
        return pixels

    def switches(self, label):
        before = self.journey.state('hud-before')
        pages = self.page_bytes()
        self.select(0, label)
        original = self.capture(label + '-original')
        self.select(1, label)
        debug = self.capture(label + '-debug')
        self.select(0, label)
        restored = self.capture(label + '-restored')
        self.journey.require(original == restored and original != debug,
                             'HUD switching left stale/ghost pixels or failed to change presentation')
        self.journey.require(before == self.journey.state('hud-before') and pages == self.page_bytes(),
                             'Display input/presentation changed gameplay state or indexed game pages')
        self.rows.append(dict(label=label, original=hashlib.sha256(original).hexdigest(),
                              debug=hashlib.sha256(debug).hexdigest(), restored_identically=True,
                              gameplay_and_pages_unchanged=True))
        self.journey.save()

    def menu_switches(self):
        self.journey.open()
        first = self.capture('menu-original', False)
        self.select(1, 'menu')
        second = self.capture('menu-debug', False)
        self.select(0, 'menu')
        third = self.capture('menu-restored', False)
        self.journey.require(first == second == third, 'Display keys obscured or changed the active requester')
        for mode in (1, 2, 0):
            self.select(mode, 'menu-geometry', geometry=True)
            frame = self.capture('menu-geometry-' + str(mode), False)
            self.journey.require(frame == first, 'F3 obscured the active requester')
        self.journey.close()
        self.check_mode(0)
        self.rows.append(dict(menu_switches=True, geometry_switches=True, identical_modal_pixels=True))
        self.journey.save()


def observe_frame(context, label):
    """Observe real damage/healing routes without modifying game state or RNG."""
    from types import SimpleNamespace
    adapter = SimpleNamespace(prefix=context['prefix'], details={}, value=context['value'],
                              require=context['require'], save=lambda: None,
                              present=lambda: gdb.execute('call e2r_present_current_frame((HWND)_DAT_00ac4dac,1)', to_string=True))
    checks = HudChecks(adapter)
    checks.capture(label)
    actor = context['actor']
    row = dict(label=label, life=context['value'](f'*(short*)({actor}+0xec)'),
               maximum_life=context['value'](f'*(short*)({actor}+0xee)'),
               poison_duration=context['value']('DAT_0047ab2c'))
    with Path(context['prefix'] + '-hud-observations.jsonl').open('a') as stream:
        stream.write(json.dumps(row) + '\n')
