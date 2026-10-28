#!/usr/bin/env python3
"""Bounded native chunk rotation, corruption, crash-tail and export contracts."""
import argparse
import csv
import os
import resource
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from e2_replay_storage import digest, inventory, event_rows
from e2_bundle import publish, verify

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--large', action='store_true', help='Also write/replay more than 256 MiB in each stream')
args = parser.parse_args()
exe = args.exe.resolve()
env = os.environ.copy()
for name in list(env):
    if name.startswith('E2R_'):
        env.pop(name)
env.update(ASAN_OPTIONS='detect_leaks=0', E2R_REPLAY_CHUNK_BYTES='512')
with tempfile.TemporaryDirectory(prefix='e2-replay-chunks-') as temporary:
    root = Path(temporary)
    fixture = root/'original'

    def run(mode, path, code):
        result = subprocess.run([str(exe), mode, str(path)], env=env,
                                capture_output=True, text=True, timeout=180 if mode.endswith('volume') else 30)
        assert result.returncode == code, (mode, code, result.returncode, result.stderr)
        assert 'ERROR: AddressSanitizer' not in result.stderr, result.stderr
        return result.stderr

    def rows(path):
        with path.open(newline='') as stream:
            return list(csv.reader(stream, strict=True))

    def write(path, records):
        with path.open('w', newline='') as stream:
            csv.writer(stream, lineterminator='\n').writerows(records)

    def case(name):
        destination = root/name
        shutil.copytree(fixture, destination)
        return destination, destination/'session/replay'

    run('record-chunks', fixture, 0)
    assert 'MATCHED' in run('play-chunks', fixture, 0)
    source = fixture/'session/replay'
    files, streams = inventory(source)
    assert len(streams['events']) > 10 and len(streams['checkpoints']) > 100
    assert all(path.stat().st_size <= 512 for paths in streams.values() for path in paths)
    events = list(event_rows(source))
    assert events[-1]['kind'] == 'end'
    print(f"PASS: exact replay across {len(streams['events'])} event and "
          f"{len(streams['checkpoints'])} state chunks, split/quoted checkpoints and nested pumps")

    destination, replay = case('legacy-flattened')
    for name, paths in streams.items():
        records = []
        for index, path in enumerate(paths):
            part = rows(replay/path.name)
            records.extend(part if index == 0 else part[1:])
        for path in paths:
            (replay/path.name).unlink()
        write(replay/f'{name}.csv', records)
    write(replay/'metadata.csv', [row for row in rows(replay/'metadata.csv') if row[0] != 'storage'])
    (replay/'chunks.csv').unlink()
    assert 'MATCHED' in run('play-chunks', destination, 0)
    print('PASS: legacy single-file replay with quoted rows across reader-buffer boundaries')

    for name, mutation in (
        ('missing-middle', lambda replay: (replay/streams['events'][1].name).unlink()),
        ('corrupt-sealed', lambda replay: (replay/streams['checkpoints'][1].name).write_bytes(b'bad\n')),
        ('missing-manifest', lambda replay: (replay/'chunks.csv').unlink()),
        ('orphan', lambda replay: (replay/'events.999999.csv').write_text('orphan\n')),
        ('symlink', lambda replay: ((replay/streams['events'][1].name).unlink(),
                                   (replay/streams['events'][1].name).symlink_to('/etc/passwd'))),
    ):
        destination, replay = case(name)
        mutation(replay)
        run('play-chunks', destination, 73)
    destination, replay = case('order')
    records = rows(replay/'chunks.csv')
    records[1], records[2] = records[2], records[1]
    write(replay/'chunks.csv', records)
    run('play-chunks', destination, 73)

    destination, replay = case('crash-tail')
    (replay/'recording.incomplete').write_text('interrupted')
    records = rows(replay/'chunks.csv')
    tails = {name: paths[-1].name for name, paths in streams.items()}
    write(replay/'chunks.csv', [row for row in records if len(row) < 3 or row[2] not in tails.values()])
    tail = replay/tails['events']
    write(tail, rows(tail)[:-1])  # End was not published before the crash.
    with tail.open('ab') as stream:
        stream.write(b'999999,1,"unfinished')
    with (replay/'chunks.csv').open('ab') as stream:
        stream.write(b'events,999')  # Interrupted publication is recoverable too.
    assert 'INCOMPLETE' in run('play-chunks', destination, 75)
    inventory(replay)
    with tail.open('ab') as stream:
        stream.write(b'"x\n')
    run('play-chunks', destination, 73)

    # A crash immediately after sealing can leave a zero-byte next chunk.
    destination, replay = case('empty-rotation-tail')
    (replay/'recording.incomplete').write_text('interrupted')
    (replay/f"events.{len(streams['events']):06}.csv").touch()
    assert 'INCOMPLETE' in run('play-chunks', destination, 75)
    destination, replay = case('partial-rotation-header')
    (replay/'recording.incomplete').write_text('interrupted')
    tail = replay/streams['events'][-1].name
    write(tail, rows(tail)[:-1])
    records = rows(replay/'chunks.csv')
    for row in records[1:]:
        if row[2] == tail.name:
            row[3:5] = [str(tail.stat().st_size), digest(tail)]
    write(replay/'chunks.csv', records)
    (replay/f"events.{len(streams['events']):06}.csv").write_bytes(b'seq,repeat,ki')
    assert 'INCOMPLETE' in run('play-chunks', destination, 75)
    print('PASS: missing/order/corruption/symlink rejection, interrupted manifest and CSV tails, empty rotation tail')

    exported = root/'export'
    subprocess.run([sys.executable, str(Path(__file__).with_name('replay-e2.py')),
                    'export', str(source), str(exported)], check=True, env=env, timeout=30,
                   stdout=subprocess.DEVNULL)
    assert set(p.name for p in files) == set(p.name for p in exported.iterdir())-{'SHA256SUMS'}
    for line in (exported/'SHA256SUMS').read_text().splitlines():
        checksum, name = line.split('  ', 1)
        assert digest(exported/name) == checksum
    bundle = root/'bundle'
    publish(bundle, exe, fixture/'session', context=False)
    assert verify(bundle)['replay'] == 'session/replay'
    assert (bundle/'tools/e2_replay_storage.py').is_file()
    print('PASS: chunk-complete replay export and portable investigation bundle integrity')

    if args.large:
        env.pop('E2R_REPLAY_CHUNK_BYTES')
        large = root/'large'
        run('record-volume', large, 0)
        _, streams = inventory(large/'session/replay')
        sizes = {name: sum(path.stat().st_size for path in paths) for name, paths in streams.items()}
        assert all(size > 256 * 1024 * 1024 for size in sizes.values()), sizes
        assert all(path.stat().st_size <= 16 * 1024 * 1024 for paths in streams.values() for path in paths)
        assert 'MATCHED' in run('play-volume', large, 0)
        print(f'PASS: large exact replay, bytes={sizes}, '
              f'peak_child_rss_kib={resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}')
