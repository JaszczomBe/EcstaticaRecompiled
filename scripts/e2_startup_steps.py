"""Observe presented startup logos and skip each with a separate SDL Space tap.

Runs inside GDB. Horseback input belongs to the caller. Original executables have
five-second logo waits; key skipping here exercises the reconstructed host wait.
"""
import json
from pathlib import Path
import time

import gdb


def start(command, prefix, watch=False, title='Regression', skip=True):
    value = lambda expression: int(gdb.parse_and_eval(expression))
    rows = []
    pending = []
    path = Path(prefix + '-logos.json')

    def save():
        path.write_text(json.dumps(rows, indent=2) + '\n')

    class Show(gdb.Breakpoint):
        def stop(self):
            pointer = value('param_1')
            for name in ('gbnklogo', 'psyglogo', 'aasglogo'):
                # Both psyg literals denote the same actual logo.
                symbols = {'gbnklogo': ('s_gbnklogo_raw_00470500',),
                           'psyglogo': ('s_psyglogo_raw_00470510', 's_psyglogo_raw_00472f98'),
                           'aasglogo': ('s_aasglogo_raw_00470520', 's_aasglogo_raw_00472fa8')}[name]
                if any(pointer == value('(uintptr_t)' + symbol) for symbol in symbols):
                    pending.append(name + '.raw')
                    return False
            raise gdb.GdbError('Unrecognized startup logo resource')

    def key(down):
        gdb.execute('set $logo_event=(SDL_Event*)calloc(1,sizeof(SDL_Event))', to_string=True)
        for member, number in [('type', 0x300 if down else 0x301), ('down', int(down)),
                               ('key', 32), ('scancode', 44)]:
            gdb.execute(f'set $logo_event->key.{member}={number}', to_string=True)
        gdb.execute('set $logo_event->key.windowID=SDL_GetWindowID(e2r_sdl_backend.window)', to_string=True)
        if value('SDL_PushEvent($logo_event)') != 1:
            raise gdb.GdbError('Logo SDL Space injection failed')
        gdb.execute('call (void)free($logo_event)', to_string=True)
        gdb.execute('call e2r_poll_host_events("suite-logo-space")', to_string=True)

    show = Show('FUN_00414998', internal=True)
    wait = gdb.Breakpoint('E2R_WaitStartupLogo', internal=True)
    try:
        gdb.execute(command, to_string=True)
        while gdb.selected_inferior().pid and gdb.selected_frame().name() == 'E2R_WaitStartupLogo':
            if len(rows) >= 3 or len(pending) != len(rows) + 1:
                raise gdb.GdbError('Unexpected startup logo/wait sequence')
            row = dict(name=pending[-1], presented=True, policy='space' if skip else 'natural', inputs=[])
            rows.append(row);save()
            print('[ LOGO     ] ' + row['name'] + ('; Space tap' if skip else '; natural wait'), flush=True)
            if watch:
                gdb.execute('call (bool)SDL_SetWindowTitle(e2r_sdl_backend.window,' +
                            json.dumps(title + ' | logo ' + row['name']) + ')', to_string=True)
                time.sleep(.5)
            started = time.monotonic()
            if skip:
                if value('DAT_00636850') or value('DAT_00636844'):
                    raise gdb.GdbError('Unexpected held input before logo tap')
                key(True);row['inputs'].append(dict(key='space', down=True));save()
            wait.enabled = False
            gdb.execute('finish', to_string=True)
            if gdb.selected_frame().name() != 'FUN_00410a48':
                raise gdb.GdbError('Startup logo wait was interrupted')
            if skip:
                if value('DAT_00636850') or value('DAT_00636844'):
                    raise gdb.GdbError('Logo wait did not consume skip input')
                key(False);row['inputs'].append(dict(key='space', down=False))
            row.update(completed=True, seconds=time.monotonic()-started)
            save();wait.enabled = True
            gdb.execute('continue', to_string=True)
        if [row['name'] for row in rows] not in (['psyglogo.raw', 'aasglogo.raw'],
                ['gbnklogo.raw', 'psyglogo.raw', 'aasglogo.raw']):
            raise gdb.GdbError('Required startup logos were not observed')
    finally:
        show.delete();wait.delete()
    return rows
