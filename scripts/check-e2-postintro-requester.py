#!/usr/bin/env python3
"""Check the default post-intro error dialog, OK dismissal and Escape routing.

Requires GDB, an SDL/i386 Debug (optionally ASan) build, and original game data.
Captures the real message surface; injects input through the existing WndProc.
Does not enable action indexing, change actor state or prove playable gameplay.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--output', type=Path, default=Path('/tmp/e2-postintro-requester'))
parser.add_argument('--timeout', type=int, default=90)
parser.add_argument('--empty',action='store_true',help='Inject an empty list at the real message boundary and verify hosted fallback text')
args = parser.parse_args()
prefix = str(args.output.resolve())
env = os.environ.copy()
env["E2R_RECORD"] = "off"
env.update(SDL_VIDEODRIVER='dummy', E2R_STARTUP_LOGO_DELAY_MS='0',
           E2R_ACTOR_CUES='1', E2R_ACTION_INDEX_PROBE='0')
# LeakSanitizer cannot run under ptrace. AddressSanitizer remains enabled.
env['ASAN_OPTIONS'] = env.get('ASAN_OPTIONS', '') + ':detect_leaks=0'

commands = r'''
set pagination off
set confirm off
python
import gdb
def val(expression):
    return int(gdb.parse_and_eval(expression))
def require(condition, message):
    if not condition:
        raise gdb.GdbError(message)
def stopped_in(name):
    require(gdb.selected_frame().name() == name, "Unexpected stop; expected " + name)
ready = gdb.Breakpoint("FUN_0041ba7c", internal=True)
ready.condition = "*(unsigned short*)((char*)&DAT_0047a45e+2) == 0x2e"
gdb.execute("run")
stopped_in("FUN_0041ba7c")
ready.delete()
actor = val("DAT_0047a470")
require(actor != 0, "Missing Joe")
progress = val("*(unsigned short*)(DAT_0047a470+0xac)")
duration = val("*(unsigned short*)(DAT_0047a470+0xaa)")
require(progress == duration and duration == 1102, "Sub-intro has not completed")
require(val("*(unsigned int*)(DAT_0047a470+0xa6)") == 0, "Unexpected loaded action")
require(val("E2R_requester_probe_b384_last_ptr") == 0x47a630, "Wrong message record")
require(gdb.parse_and_eval("(char*)0x64403a").string() == "Can't load action:", "Wrong message title")
require("384" in gdb.parse_and_eval("(char*)0x64406d").string(), "Missing action id")
gdb.execute("call e2r_present_current_frame((HWND)_DAT_00ac4dac,1)")
require(val(OUTPUT_EXPRESSION) == 1,
        "Failed to capture SDL message presentation")
gdb.execute("set $click_x = (*(short*)0x643dfa + *(short*)0x643dfc) / 2")
gdb.execute("set $click_y = (*(short*)0x643dfe + *(short*)0x643e00) / 2")
gdb.execute("call E2R_WndProc((HWND)_DAT_00ac4dac,0x201,1,($click_y << 16) | $click_x)")
require(val("_DAT_006443d0") == 1, "OK did not close the modal")
require(val("*(unsigned short*)((char*)&DAT_0047a45e+2)") == 0, "Message id remained active")
update = gdb.Breakpoint("FUN_00415d40", internal=True)
gdb.execute("continue")
stopped_in("FUN_00415d40")
update.delete()
print("CHECK: game update resumed; camera slot", (val("_DAT_0073cc3c") - 0x67c728) // 28)
gdb.execute("call E2R_WndProc((HWND)_DAT_00ac4dac,0x100,0x1b,0)")
require(val("DAT_00636844") == 1, "Idle Escape was not latched")
menu = gdb.Breakpoint("FUN_0043ce58", internal=True)
gdb.execute("continue")
stopped_in("FUN_0043ce58")
require(val("param_1") == 0x28 and val("_DAT_00643650") == 5,
        "Escape did not reach the main menu")
print("PASS: completed sub-intro, visible action error, OK dismissal, game update and Escape menu entry")
end
quit
'''.replace('OUTPUT_EXPRESSION', json.dumps(
    'e2r_write_visibility_packet((HWND)_DAT_00ac4dac,' + json.dumps(prefix) + ')'))

with tempfile.TemporaryDirectory(prefix='e2-requester-check-') as tmp:
    if args.empty:
        commands=commands.replace('gdb.execute("run")', '''empty = gdb.Breakpoint("E2R_ResolveMenuStringList",internal=True)
gdb.execute("run")
stopped_in("E2R_ResolveMenuStringList")
gdb.execute("finish")
gdb.execute("next")  # Finish storing the helper return before replacing the local list.
empty.delete()
gdb.execute("set in_EAX = (int*)calloc(2,4)")
gdb.execute("continue")''')
        commands=commands.replace('"Can\'t load action:"','"Internal game error. See the session log."')
        commands=commands.replace('require("384" in gdb.parse_and_eval("(char*)0x64406d").string(), "Missing action id")',
                                  'require(gdb.parse_and_eval("(char*)0x64406d").string() == "", "Unexpected second line")')
    script = Path(tmp) / 'check.gdb'
    script.write_text(commands)
    try:
        result = subprocess.run(
            ['gdb', '-q', '-batch', '-x', str(script), '--args', str(args.exe.resolve()),
             '--inject-key-sequence-surfaces', prefix + '-raw', 'space', '3', '250',
             str(args.timeout + 10)], env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or b''
        Path(prefix + '.log').write_bytes(output if isinstance(output, bytes) else output.encode())
        raise SystemExit(f'FAIL: timed out; see {prefix}.log')
    Path(prefix + '.log').write_text(result.stdout)
    if (result.returncode or 'PASS: completed sub-intro' not in result.stdout or
            'ERROR: AddressSanitizer' in result.stdout or
            'SUMMARY: AddressSanitizer' in result.stdout):
        raise SystemExit(f'FAIL: unexpected runtime/debugger stop; see {prefix}.log')
    state = Path(prefix + '-state.txt')
    if not state.is_file() or 'host_dumps=2' not in state.read_text():
        raise SystemExit(f'FAIL: missing SDL presentation captures; see {prefix}.log')
    for suffix in ('-sdl-present.ppm', '-sdl-window.ppm'):
        if not Path(prefix + suffix).is_file():
            raise SystemExit(f'FAIL: missing capture {prefix}{suffix}')
    for line in result.stdout.splitlines():
        if line.startswith(('CHECK:', 'PASS:')):
            print(line)
    print(f'Evidence: {prefix}.log and {prefix}-state.txt')
