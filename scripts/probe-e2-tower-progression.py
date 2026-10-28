#!/usr/bin/env python3
"""Bounded SDL tower key/door journey from private copies of a supplied save set.

Uses normal menu and keyboard input. Original/user saves are read-only sources;
only a confirmed empty private slot and later probe-owned contents may be written.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess

from e2_probe_diagnostics import communicate

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('executable', type=Path)
parser.add_argument('--game-data', type=Path, required=True)
parser.add_argument('--saves', type=Path, required=True)
parser.add_argument('--load-slot', type=int, required=True, choices=range(10))
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--timeout', type=int, default=240)
args = parser.parse_args()
if not 30 <= args.timeout <= 600:
    parser.error('--timeout must be 30..600 seconds per bounded process')
executable = args.executable.resolve(strict=True)
game = args.game_data.resolve(strict=True)
saves = args.saves.resolve(strict=True)
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)


def hashes(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob('*.ECS'))}


installed, supplied = hashes(game / 'Saved'), hashes(saves)
if f'{args.load_slot:04d}.ECS' not in supplied:
    raise SystemExit('Selected load slot is absent from the supplied fixture')
files = {p.name: p for p in (game / 'Saved').glob('*.ECS')}
files.update({p.name: p for p in saves.glob('*.ECS')})
free = [i for i in range(9) if f'{i:04d}.ECS' in files and files[f'{i:04d}.ECS'].read_bytes() == b'\r\n\r\n']
if not free:
    raise SystemExit('No confirmed empty private menu slot available')
slot = free[0]
launch = json.loads((ROOT / '.vscode/launch.json').read_text())['configurations'][0]
env = os.environ.copy()
for key in list(env):
    if key.startswith('E2R_'):
        env.pop(key)
for item in launch['environment']:
    env[item['name']] = re.sub(r'\$\{env:([^}]+)\}', lambda m: os.environ.get(m[1], ''), item['value'])
env.update(E2R_RECORD='off', E2R_INSPECT='1', E2R_INSPECT_MAX_FRAMES='20',
           E2R_STARTUP_LOGO_DELAY_MS='0', SDL_VIDEODRIVER='dummy', ASAN_OPTIONS='detect_leaks=0')
env.pop('DISPLAY', None)
report = dict(probe_complete=False, recording='off', load_slot=args.load_slot, private_save_slot=slot,
              executable=dict(path=str(executable), sha256=hashlib.sha256(executable.read_bytes()).hexdigest()),
              supplied_saves=supplied, installed_saves=installed, processes=[])
try:
    for mode in ('locked', 'main', 'fresh-before', 'fresh-key', 'fresh-door'):
        destination = output / mode
        destination.mkdir()
        runtime = destination / 'runtime'
        private = runtime / 'Saved'
        private.mkdir(parents=True)
        for name, path in files.items():
            shutil.copyfile(path, private / name)
        expected_path = None
        load_slot = args.load_slot
        if mode.startswith('fresh-'):
            stage = mode.removeprefix('fresh-')
            shutil.copyfile(output / 'main' / (stage + '.ECS'), private / f'{slot:04d}.ECS')
            expected_path = output / 'main' / (stage + '-expected.json')
            load_slot = slot
        private_before = hashes(private)
        prefix = str(destination / 'tower')
        commands = '''set pagination off
set confirm off
python
import sys,gdb
sys.path.insert(0,SCRIPTS)
from e2_probe_diagnostics import install
install(PREFIX)
class SaveOwnership(gdb.Breakpoint):
    def stop(self):
        if MODE != 'main' or int(gdb.parse_and_eval('param_1')) != SLOT:
            print('FAIL: unowned save write',flush=True)
            return True
        return False
ownership=SaveOwnership('FUN_00453920',internal=True)
from e2_tower_steps import run
run(PREFIX,RUNTIME,GAME,LOAD,SLOT,MODE,EXPECTED)
end
quit
'''
        values = dict(SCRIPTS=str(ROOT / 'scripts'), PREFIX=prefix, RUNTIME=str(runtime), GAME=str(game),
                      LOAD=load_slot, SLOT=slot, MODE=mode, EXPECTED=str(expected_path) if expected_path else None)
        commands = re.sub(r'\b(' + '|'.join(values) + r')\b', lambda m: repr(values[m[0]]), commands)
        command_file = destination / 'probe.gdb'
        command_file.write_text(commands)
        process = subprocess.Popen(['gdb', '-nx', '-batch', '-x', str(command_file), str(executable)],
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, start_new_session=True)
        try:
            text, stalled = communicate(process, prefix, args.timeout, stall_timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            text, _ = process.communicate()
            (destination / 'gdb.log').write_text(text)
            raise RuntimeError(mode + ' exceeded its bounded timeout')
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        (destination / 'gdb.log').write_text(text)
        after = hashes(private)
        preserved = {name: after.get(name) == digest for name, digest in private_before.items()
                     if mode != 'main' or name != f'{slot:04d}.ECS'}
        report.setdefault('private_save_preservation', {})[mode] = preserved
        if not all(preserved.values()):
            raise RuntimeError('An unowned private save changed')
        result_path = Path(prefix + '.json')
        if (process.returncode or stalled or not result_path.exists() or
                'ERROR: AddressSanitizer' in text or 'runtime error:' in text):
            print(text[-7000:])
            raise RuntimeError(mode + ' did not complete')
        result = json.loads(result_path.read_text())
        report['processes'].append(result)
        if not result.get('probe_complete') or result.get('native_exit_code') != 0:
            raise RuntimeError(mode + ' did not reach a clean native exit')
        print('PASS: ' + mode, flush=True)
    report['probe_complete'] = True
finally:
    report['supplied_saves_unchanged'] = hashes(saves) == supplied
    report['installed_saves_unchanged'] = hashes(game / 'Saved') == installed
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    if not report['supplied_saves_unchanged'] or not report['installed_saves_unchanged']:
        raise RuntimeError('Read-only save sources changed')
print('PASS: tower acquisition, locked/keyed passage, three same/fresh-process persistence stages, original pixels, F3 and HUD')
