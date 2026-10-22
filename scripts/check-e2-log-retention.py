#!/usr/bin/env python3
"""Check periodic cleanup and active/crashed session leases across real processes."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
args = parser.parse_args()
exe = args.exe.resolve()


def eventually(predicate, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.05)
    raise AssertionError('Timed out waiting for session maintenance')


with tempfile.TemporaryDirectory(prefix='e2-periodic-retention-') as directory:
    root = Path(directory)
    env = os.environ | dict(E2R_DATA_DIR=directory, SDL_VIDEODRIVER='dummy',
                            E2R_STARTUP_LOGO_DELAY_MS='0', E2R_LOG_LEVEL='Warning',
                            E2R_LOG_DISABLE_MODULES='', E2R_LOG_MAX_SESSIONS='1',
                            E2R_LOG_MAX_TOTAL_MB='1', E2R_LOG_CLEANUP_INTERVAL_SECONDS='1')
    with (root / 'active-console.txt').open('w') as output:
        active = subprocess.Popen([str(exe), '--dump-frame', str(root / 'frame.pgm'), '10'],
                                  cwd=exe.parent, env=env, stdout=output, stderr=output)
        try:
            def active_session():
                for meta in (root / 'logs').glob('session_*/session.meta'):
                    if json.loads(meta.read_text())['pid'] == active.pid:
                        return meta.parent
            eventually(active_session)
            first = active_session()
            result = subprocess.run([str(exe), '--host-backend-present-probe'], cwd=exe.parent,
                                    env=env, capture_output=True, text=True, timeout=15)
            assert result.returncode == 0, result.stderr
            assert 'budget exceeded' in result.stderr
            assert first.exists() and active.poll() is None
            # The still-running process cleans up the now-completed second session.
            eventually(lambda: list((root / 'logs').glob('session_*')) == [first])
            assert active.poll() is None
            # Test a pre-lease session owned by a still-running older build too.
            legacy = root / 'logs/session_20000101_000000_000'
            legacy.mkdir()
            (legacy / 'session.meta').write_text(json.dumps({'pid': active.pid}))
            time.sleep(1.3)
            assert legacy.exists()
        finally:
            active.kill()  # Intentionally bypass shutdown; the OS must release its lease.
            active.wait(timeout=5)
        result = subprocess.run([str(exe), '--host-backend-present-probe'], cwd=exe.parent,
                                env=env, capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr
        assert not first.exists() and not legacy.exists()
        assert len(list((root / 'logs').glob('session_*'))) == 1
        print('PASS: periodic cleanup, concurrent active protection, legacy PID protection and crash lease release')
