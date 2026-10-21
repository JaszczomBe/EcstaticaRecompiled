#!/usr/bin/env python3
"""Exercise the SDL developer executable with VS Code's environment and cwd.

Uses the bounded host presentation command in place of the interactive game.
Checks automatic logging, CLI/environment precedence, filters and path failures.
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
env.update({item['name']: re.sub(r'\$\{env:([^}]+)\}',
                               lambda match: os.environ.get(match[1], ''), item['value'])
            for item in launch['environment']})
env.update(SDL_VIDEODRIVER='dummy')
assert 'detect_leaks=0' in env['ASAN_OPTIONS']
env.pop('DISPLAY', None)
env.pop('E2R_LOG_LEVEL', None)
env.pop('E2R_LOG_DISABLE_MODULES', None)

def check(output):
    cases = 0

    def run(name, options=(), overrides=None, cwd=None, success=True,
            command=('--host-backend-present-probe',), under_gdb=False):
        nonlocal cases
        case_env = env | {'E2R_DATA_DIR': str(output / name)} | (overrides or {})
        invocation = [str(exe), *options, *command]
        if under_gdb:
            invocation = ['gdb', '--nx', '--quiet', '--batch', '-ex', 'run', '--args', *invocation]
        result = subprocess.run(invocation,
                                cwd=cwd or exe.parent, env=case_env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=30)
        (output / (name + '.txt')).write_text(result.stdout)
        assert (result.returncode == 0) == success, (name, result.returncode, result.stdout)
        assert 'ERROR: AddressSanitizer' not in result.stdout, (name, result.stdout)
        cases += 1
        return result.stdout

    def records(directory):
        files = list((directory / 'logs').glob('e2recomp*.log'))
        assert files, f'No log file under {directory}'
        return ''.join(path.read_text() for path in files)

    # No logger CLI switches: this is how F5 starts the selected executable.
    console = run('f5')
    log = records(output / 'f5')
    assert '[Runtime.Startup]' in log
    assert 'host backend presentation probe passed' in console
    assert 'host backend presentation probe passed' in log
    assert console.count('host backend presentation probe passed') == 1
    debug_console = run('debugger-exit', under_gdb=True)
    assert 'exited normally' in debug_console
    assert 'LeakSanitizer' not in debug_console

    # Run the game long enough to use its variadic/fragmented state logger.
    # This catches missing vfprintf bodies that a startup-only smoke test misses.
    run('game-startup', overrides={'E2R_GAME_STATE_LOG': '1'},
        command=('--dump-frame', str(output / 'startup.pgm'), '2'))
    assert 'game state: startup logo show begin name=psyglogo.raw' in records(output / 'game-startup')

    # The same output root works from outside the build tree, even after chdir
    # into the original game data. Relative CLI overrides resolve before chdir.
    run('other-cwd', cwd=output)
    assert '[Runtime.Startup]' in records(output / 'other-cwd')
    run('relative-env', overrides={'E2R_DATA_DIR': 'relative-env'}, cwd=output)
    assert '[Runtime.Startup]' in records(output / 'relative-env')
    run('cli-wins', ['--data-dir', 'relative-cli'], cwd=output)
    assert '[Runtime.Startup]' in records(output / 'relative-cli')
    assert not (output / 'cli-wins').exists()

    run('level-off', overrides={'E2R_LOG_LEVEL': 'Off'})
    assert not records(output / 'level-off')
    run('module-off', ['--log-disable-modules', 'Runtime'])
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
