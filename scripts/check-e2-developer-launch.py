#!/usr/bin/env python3
"""Exercise the SDL developer executable with VS Code's environment and cwd.

Uses bounded host probes and GDB input dispatch in place of interactive play.
Checks key transitions, severity/tags, sessions, CLI/env precedence and failures.
Run both the SDL Debug and SDL Debug+ASan executables after building their presets.
"""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
exe = args.exe.resolve()
launch = json.loads((root / '.vscode/launch.json').read_text())['configurations'][0]
assert launch['program'] == '${command:cmake.launchTargetPath}'
assert launch['cwd'] == '${command:cmake.getLaunchTargetDirectory}'
assert launch['args'] == ['--run-recon']
assert 'preLaunchTask' not in launch
env = os.environ.copy()
env["E2R_RECORD"] = "off"
env.update({item['name']: re.sub(r'\$\{env:([^}]+)\}',
                               lambda match: os.environ.get(match[1], ''), item['value'])
            for item in launch['environment']})
env['E2R_RECORD'] = 'off'  # Agent probes override the human F5 recording policy.
env.update(SDL_VIDEODRIVER='dummy')
assert 'detect_leaks=0' in env['ASAN_OPTIONS']
env.pop('DISPLAY', None)
env.pop('E2R_LOG_LEVEL', None)
env.pop('E2R_LOG_DISABLE_MODULES', None)
env.pop('NO_COLOR', None)
env.pop('E2R_INPUT_DIAG_VERBOSE', None)
env['E2R_INPUT_DIAG'] = '1'

def check(output):
    cases = 0

    def run(name, options=(), overrides=None, cwd=None, success=True,
            command=('--host-backend-present-probe',), under_gdb=False, gdb_script=None):
        nonlocal cases
        case_env = env | {'E2R_DATA_DIR': str(output / name)} | (overrides or {})
        invocation = [str(exe), *options, *command]
        if under_gdb or gdb_script:
            commands = ['-x', str(gdb_script)] if gdb_script else ['-ex', 'run']
            invocation = ['gdb', '--nx', '--quiet', '--batch', *commands, '--args', *invocation]
        result = subprocess.run(invocation,
                                cwd=cwd or exe.parent, env=case_env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=60)
        (output / (name + '.txt')).write_text(result.stdout)
        assert (result.returncode == 0) == success, (name, result.returncode, result.stdout)
        assert 'ERROR: AddressSanitizer' not in result.stdout, (name, result.stdout)
        cases += 1
        return result.stdout

    def records(directory):
        sessions = list((directory / 'logs').glob('session_*'))
        assert sessions, f'No session directory under {directory}'
        for session in sessions:
            metadata = json.loads((session / 'session.meta').read_text())
            assert metadata['appId'] == 'EcstaticaRecompiled'
            assert metadata['sessionId'] == session.name
            assert metadata['pid'] > 0
        files = list((directory / 'logs').glob('session_*/e2recomp*.log'))
        assert files, f'No log file under {directory}'
        log = ''.join(path.read_text() for path in files)
        assert '\x1b[' not in log, 'ANSI colors leaked into session files'
        return log

    # No logger CLI switches: this is how F5 starts the selected executable.
    console = run('f5')
    log = records(output / 'f5')
    assert '[Runtime.Startup]' in log
    assert 'host backend presentation probe passed' in console
    assert 'host backend presentation probe passed' in log
    assert console.count('host backend presentation probe passed') == 1
    assert '[INFO]' in console and '\x1b[' in console
    assert '[INFO]' in log
    assert 'Log session: ' in console
    run('f5')
    assert len(list((output / 'f5' / 'logs').glob('session_*'))) == 2
    assert records(output / 'f5').count('host backend presentation probe passed') == 2
    plain = run('no-color', overrides={'NO_COLOR': '1'})
    assert '[INFO]' in plain and '\x1b[' not in plain
    assert '[INFO]' in records(output / 'no-color')
    warning = run('invalid-level', ['--log-level', 'not-a-level'])
    assert '[WARN]' in warning and 'unrecognized logLevel' in warning
    assert '[WARN]' in records(output / 'invalid-level')
    warning = run('warning-only', ['--log-level', 'Warning'],
                  overrides={'SDL_VIDEODRIVER': 'e2r-missing-driver'}, success=False)
    assert '[WARN]' in warning and 'warning: SDL video init failed:' in warning
    assert '[INFO]' not in warning
    assert '[WARN]' in records(output / 'warning-only')
    debug_console = run('debugger-exit', under_gdb=True)
    assert 'exited normally' in debug_console
    assert 'LeakSanitizer' not in debug_console

    # Exercise the production dispatcher/legacy key handler, including enough
    # repeats to exhaust the old diagnostic caps. Folding must not drop inputs.
    input_script = output / 'input.gdb'
    input_script.write_text(r'''
set pagination off
break e2r_run_host_backend_key_probe
run
set e2r_window_proc = E2R_WndProc
set $e2r_msg = (MSG *)calloc(1, sizeof(MSG))
python
before = int(gdb.parse_and_eval('E2R_input_probe_keydown_count'))
def key(msg, vk):
    gdb.execute('set $e2r_msg->message = %d' % msg)
    gdb.execute('set $e2r_msg->wParam = %d' % vk)
    gdb.execute('call (void)DispatchMessageA($e2r_msg)', to_string=True)
key(0x100, 0x26)  # Up pressed, followed by one held record despite 600 repeats.
for repeat in range(600):
    key(0x100, 0x26)
key(0x100, 0x28)  # An overlapping key has independent state.
key(0x100, 0x10)  # Shift receives no autorepeat; release duration still exists.
key(0x101, 0x26)
key(0x101, 0x26)  # Redundant release creates no new record.
key(0x100, 0x28)
key(0x101, 0x28)
key(0x101, 0x10)
key(0x100, 0x41)  # Later events remain visible after legacy diagnostic caps.
key(0x101, 0x41)
after = int(gdb.parse_and_eval('E2R_input_probe_keydown_count'))
assert after - before == 605, (before, after)
print('PASS: all 605 keydowns reached the legacy handler')
end
call (void)free($e2r_msg)
call (void)E2R_LogDiagnostic("game state: sound archive missing ignored id=43 archive=0xffffffff")
call (void)E2R_LogDiagnostic("game state: 15d40.enter input esc=0 space=0")
continue
''')
    expected = [('Up', 'pressed'), ('Up', 'held'), ('Down', 'pressed'),
                ('Shift', 'pressed'), ('Up', 'released'), ('Down', 'held'),
                ('Down', 'released'), ('Shift', 'released'),
                ('A', 'pressed'), ('A', 'released'), ('Space', 'pressed')]
    for level, verbose in [('Debug', False), ('Info', False), ('Trace', False), ('Debug', True)]:
        name = f'input-{level.lower()}' + ('-verbose' if verbose else '')
        console = run(name, ['--log-level', level],
                      {'E2R_INPUT_DIAG_VERBOSE': '1' if verbose else '0'},
                      command=('--host-backend-key-probe',), gdb_script=input_script)
        log = records(output / name)
        assert 'PASS: all 605 keydowns reached the legacy handler' in console
        assert 'exited normally' in console
        for text in (console, log):
            transitions = re.findall(r'\[Runtime.Input\]\[DEBUG\] input: key=(\S+) state=(\w+)', text)
            assert transitions == ([] if level == 'Info' else expected), (name, transitions)
            assert ('[Runtime.MissingSound][TRACE]' in text) == (level == 'Trace')
            assert ('game input:' in text) == verbose
            assert ('host input event:' in text) == verbose
            assert ('game state: 15d40.enter input' in text) == verbose

    # Run the game long enough to use its variadic/fragmented state logger.
    # This catches missing vfprintf bodies that a startup-only smoke test misses.
    startup = run('game-startup', overrides={'E2R_GAME_STATE_LOG': '1'},
        command=('--dump-frame', str(output / 'startup.pgm'), '2'))
    startup_log = records(output / 'game-startup')
    assert 'game state: startup logo show begin name=psyglogo.raw' in startup_log
    # These probes call _exit; their last queued record must still be drained.
    assert 'input state:' in startup and 'input state:' in startup_log
    error = run('dump-error', success=False,
                command=('--dump-frame', str(output / 'absent-parent' / 'frame.pgm'), '1'))
    error_log = records(output / 'dump-error')
    assert '[ERROR]' in error and 'failed to write frame dump:' in error
    assert '[ERROR]' in error_log and 'failed to write frame dump:' in error_log
    error = run('off-still-errors', ['--log-level', 'Off'], success=False,
                command=('--dump-frame', str(output / 'absent-parent' / 'off.pgm'), '1'))
    assert '[ERROR]' in error and '[INFO]' not in error
    assert '[ERROR]' in records(output / 'off-still-errors')

    # Activate the logger's existing retention policy against disposable sparse
    # files: meet the byte budget and leave old flat logs untouched.
    retained_logs = output / 'retention' / 'logs'
    retained_logs.mkdir(parents=True)
    for index in range(11):
        session = retained_logs / f'session_20000101_000000_{index:03}'
        session.mkdir()
        (session / 'session.meta').write_text('{}')
    oldest = retained_logs / 'session_20000101_000000_000'
    with (oldest / 'oversize.log').open('wb') as sparse:
        sparse.truncate(128 * 1024 * 1024 + 1)
    legacy = retained_logs / 'e2recomp_legacy.log'
    legacy.write_text('retain legacy logs')
    cleanup = run('retention')
    assert 'Log cleanup:' in cleanup and 'removed=1' in cleanup
    assert not oldest.exists()
    assert len(list(retained_logs.glob('session_*'))) == 11
    assert legacy.read_text() == 'retain legacy logs'
    for setting, value in [('E2R_LOG_MAX_SESSIONS', '0'), ('E2R_LOG_MAX_TOTAL_MB', '-1'),
                           ('E2R_LOG_CLEANUP_INTERVAL_SECONDS', 'invalid')]:
        error = run('invalid-' + setting.lower(), overrides={setting: value}, success=False)
        assert setting in error and 'positive integer' in error

    # The same output root works from outside the build tree, even after chdir
    # into the original game data. Relative CLI overrides resolve before chdir.
    run('other-cwd', cwd=output)
    assert '[Runtime.Startup]' in records(output / 'other-cwd')
    run('relative-env', overrides={'E2R_DATA_DIR': 'relative-env'}, cwd=output)
    assert '[Runtime.Startup]' in records(output / 'relative-env')
    run('cli-wins', ['--data-dir', 'relative-cli'], cwd=output)
    assert '[Runtime.Startup]' in records(output / 'relative-cli')
    assert not (output / 'cli-wins').exists()

    assert not run('level-off', overrides={'E2R_LOG_LEVEL': 'Off'})
    assert not records(output / 'level-off')
    assert not run('module-off', ['--log-disable-modules', 'Runtime'])
    assert not records(output / 'module-off')
    run('cli-level', ['--log-level', 'Info'], {'E2R_LOG_LEVEL': 'Off'})
    assert '[Runtime.Startup]' in records(output / 'cli-level')
    run('cli-clear-modules', ['--log-disable-modules', ''], {'E2R_LOG_DISABLE_MODULES': 'Runtime'})
    assert '[Runtime.Startup]' in records(output / 'cli-clear-modules')

    collision = output / 'not-a-directory'
    collision.write_text('retain me')
    run('file-collision', ['--data-dir', str(collision)], success=False)
    assert collision.read_text() == 'retain me'
    run('parent-collision', ['--data-dir', str(collision / 'child')], success=False)
    run('missing-value', ['--data-dir'], success=False)
    run('empty-value', ['--data-dir', ''], success=False)
    run('missing-game', ['--game-data-dir', str(output / 'absent-game')], success=False)

    # Opening the root can succeed while its log subdirectory is invalid.
    bad_logs = output / 'bad-logs'
    bad_logs.mkdir(exist_ok=True)
    (bad_logs / 'logs').write_text('retain me too')
    run('bad-log-directory', ['--data-dir', str(bad_logs)], success=False)
    assert (bad_logs / 'logs').read_text() == 'retain me too'
    print(f'PASS: {cases} developer launch/logging cases for {exe}')

if args.output:
    args.output.mkdir(parents=True, exist_ok=True)
    check(args.output.resolve())
else:
    with tempfile.TemporaryDirectory(prefix='e2-developer-launch-') as directory:
        check(Path(directory))
