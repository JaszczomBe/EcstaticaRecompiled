"""Bounded SDL F3 checks at a stopped native gameplay frame; no simulation edits."""
import hashlib
import json
from pathlib import Path

import gdb


def check_modes(prefix, label):
    value = lambda expression: int(gdb.parse_and_eval(expression))
    inferior = gdb.selected_inferior()
    size = value('_DAT_006401ec * _DAT_006401d4')

    def game_bytes():
        data = bytearray()
        cursor = value('_DAT_0063726c')
        seen = set()
        while cursor:
            if cursor in seen or len(seen) >= 256:
                raise gdb.GdbError('Invalid geometry-check actor chain')
            seen.add(cursor)
            data.extend(inferior.read_memory(cursor, 0x18c))
            node = value(f'*(unsigned int*)({cursor}+0x1e)')
            nodes = set()
            while node:
                if node in nodes or len(nodes) >= 256:
                    raise gdb.GdbError('Invalid geometry-check node chain')
                nodes.add(node)
                data.extend(inferior.read_memory(node, 0x15a))
                node = value(f'*(unsigned int*)({node}+0x4c)')
            cursor = value(f'*(unsigned int*)({cursor}+0x4c)')
        for page in range(4):
            data.extend(inferior.read_memory(value(f'e2r_surface_framebuffer({page})'), size))
        for bank in ('_DAT_00636668', '_DAT_0063666c', '_DAT_00636670'):
            data.extend(inferior.read_memory(value(bank), size * 2))
        return hashlib.sha256(data).hexdigest()

    def event(down, repeat=False):
        gdb.execute('set $geometry_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))', to_string=True)
        for member, number in (('type', 0x300 if down else 0x301), ('down', int(down)),
                               ('repeat', int(repeat)), ('key', 0x4000003c), ('scancode', 60)):
            gdb.execute(f'set $geometry_event->key.{member}={number}', to_string=True)
        gdb.execute('set $geometry_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)', to_string=True)
        if value('SDL_PushEvent($geometry_event)') != 1:
            raise gdb.GdbError('F3 SDL event rejected')
        gdb.execute('call (void)free($geometry_event)', to_string=True)
        gdb.execute('call e2r_poll_host_events("geometry-check")', to_string=True)

    if value('E2R_GeometryMode()') != 0:
        raise gdb.GdbError('F3 default should select original models with fallbacks')
    original_hud = value('E2R_DebugOverlaySelected()')
    before = game_bytes()
    rows = []
    for mode in (0, 1, 2, 0):
        if rows:
            event(True)
            for kind in (0x20f, 0x20e):  # Focus loss releases the host latch.
                gdb.execute('set $geometry_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))', to_string=True)
                gdb.execute(f'set $geometry_event->window.type={kind}', to_string=True)
                gdb.execute('set $geometry_event->window.windowID=SDL_GetWindowID(e2r_sdl_backend.window)', to_string=True)
                if value('SDL_PushEvent($geometry_event)') != 1:
                    raise gdb.GdbError('F3 focus event rejected')
                gdb.execute('call (void)free($geometry_event)', to_string=True)
                gdb.execute('call e2r_poll_host_events("geometry-focus")', to_string=True)
            event(True, repeat=True)
            event(False)
        if value('E2R_GeometryMode()') != mode or value('E2R_DebugOverlaySelected()') != original_hud:
            raise gdb.GdbError('F3 repeated or changed F1/F2 selection')
        if value('e2r_present_current_frame((HWND)_DAT_00ac4dac,1)') != 1:
            raise gdb.GdbError('F3 presentation failed')
        base = value('e2r_surface_framebuffer((DAT_0047a279>>24)&1)')
        selected = value(f'e2r_geometry_pixels((const unsigned char*){base},{size})')
        if selected != (value('_DAT_0063615c') if mode == 2 else base):
            raise gdb.GdbError('F3 selected an incorrect scene pixel source')
        if game_bytes() != before:
            raise gdb.GdbError('F3 presentation modified actors, poses, game pixels or depth')
        target = prefix + '-geometry-' + label + '-' + str(len(rows))
        gdb.execute('call (int)E2R_HostDumpPresentation(&e2r_sdl_backend,' + json.dumps(target) + ')', to_string=True)
        surface = gdb.parse_and_eval('e2r_sdl_backend.present_surface').dereference()
        data = bytes(inferior.read_memory(int(surface['pixels']), int(surface['h']) * int(surface['pitch'])))
        rows.append(dict(mode=mode, sha256=hashlib.sha256(data).hexdigest(), game_unchanged=True))
    if rows[0]['sha256'] != rows[-1]['sha256']:
        raise gdb.GdbError('F3 original mode did not restore the same frame')
    path = Path(prefix + '-geometry.json')
    evidence = json.loads(path.read_text()) if path.exists() else []
    evidence.append(dict(label=label, modes=rows))
    path.write_text(json.dumps(evidence, indent=2) + '\n')
