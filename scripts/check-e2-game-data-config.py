#!/usr/bin/env python3
"""Check CMake game-data resolution without a compiler, game install or GUI."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='e2-game-data-config-') as directory:
    temporary = Path(directory)
    config = temporary / 'game-data-dir'
    result = temporary / 'resolved.txt'
    harness = temporary / 'resolve.cmake'
    harness.write_text(f'include("{root}/cmake/E2RGameData.cmake")\n'
                       f'file(WRITE "{result}" "${{ECSTATICA2_DATA_DIR}}")\n')
    cases = 0

    def check(expected, cache=None, environment=None, text=None):
        global cases
        if config.exists():
            config.unlink()
        if text is not None:
            config.write_text(text)
        env = os.environ.copy()
        env.pop('ECSTATICA2_DATA_DIR', None)
        if environment is not None:
            env['ECSTATICA2_DATA_DIR'] = environment
        command = ['cmake', f'-DECSTATICA2_DATA_CONFIG={config}']
        if cache is not None:
            command.append(f'-DECSTATICA2_DATA_DIR={cache}')
        command += ['-P', str(harness)]
        subprocess.run(command, env=env, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
        assert result.read_text() == expected, (expected, result.read_text())
        cases += 1

    # Persisted configuration survives fresh and already-empty editor caches.
    check('/configured/game', text='/configured/game\n')
    check('/configured/game', cache='', text='/configured/game\n')
    check('/env/game', environment='/env/game', text='/configured/game\n')
    check('/env/game', cache='', environment='/env/game', text='/configured/game\n')
    check('/cache/game', cache='/cache/game', environment='/env/game', text='/configured/game\n')
    check('/missing/cache/game', cache='/missing/cache/game', text='/configured/game\n')
    check('/game with spaces', text='  /game with spaces\r\n')
    check('', cache='', text='\n')
    check('', cache='')
    check('/env/game', environment='/env/game')
    print(f'PASS: {cases} CMake game-data configuration cases')
