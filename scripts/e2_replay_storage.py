"""Inventory legacy/chunked replay files without loading recordings into memory."""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

CHUNK_HEADER = ['stream', 'index', 'file', 'bytes', 'sha256']


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Expected regular replay file: {path}')
    return path


def metadata(directory):
    path = regular(directory/'metadata.csv')
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('Replay metadata exceeds 1 MiB')
    with path.open(newline='') as stream:
        rows = list(csv.reader(stream, strict=True))
    if not rows or rows[0] != ['key', 'value'] or any(len(row) != 2 for row in rows[1:]):
        raise ValueError('Invalid metadata header/columns')
    result = dict(rows[1:])
    if len(result) != len(rows)-1 or result.get('schema') != 'e2replay.csv.1':
        raise ValueError('Duplicate metadata or unsupported schema')
    return result


def chunk_name(stream, index):
    return f'{stream}.{index:06}.csv' if index else f'{stream}.csv'


def inventory(directory):
    """Validate the ordered physical inventory and sealed checksums under a lease.

    Native preparation additionally validates all logical rows and signatures.
    Only each stream's final unsealed chunk may survive an incomplete manifest.
    """
    meta = metadata(directory)
    files = [directory/'metadata.csv']
    streams = {'events': [], 'checkpoints': []}
    incomplete = (directory/'recording.incomplete').exists()
    if incomplete:
        files.append(regular(directory/'recording.incomplete'))
    if 'storage' not in meta:
        for name in streams:
            streams[name].append(regular(directory/f'{name}.csv'))
    else:
        if meta['storage'] != 'chunked.csv.1':
            raise ValueError('Unsupported replay storage')
        manifest = regular(directory/'chunks.csv')
        files.append(manifest)
        with manifest.open('rb') as source:
            if source.readline(65537) != b'stream,index,file,bytes,sha256\n':
                raise ValueError('Invalid replay manifest header')
            while line := source.readline(65537):
                if len(line) > 65536 or b'\0' in line:
                    raise ValueError('Invalid replay manifest record')
                if not line.endswith(b'\n'):
                    if incomplete:
                        break
                    raise ValueError('Truncated replay manifest')
                row = next(csv.reader([line.decode('ascii')], strict=True))
                if len(row) != 5 or row[0] not in streams:
                    raise ValueError('Invalid replay manifest columns/stream')
                stream, index, name, size, checksum = row
                expected = len(streams[stream])
                if int(index) != expected or name != chunk_name(stream, expected):
                    raise ValueError('Replay manifest order/name mismatch')
                path = regular(directory/name)
                if int(size) <= 0 or path.stat().st_size != int(size) or digest(path) != checksum:
                    raise ValueError(f'Replay chunk checksum/size mismatch: {name}')
                streams[stream].append(path)
        for stream, paths in streams.items():
            tail = directory/chunk_name(stream, len(paths))
            if tail.exists() or tail.is_symlink():
                if not incomplete:
                    raise ValueError('Unsealed chunk in complete replay')
                paths.append(regular(tail))
            if not paths:
                raise ValueError('Missing initial replay chunk')
            known = {p.name for p in paths}
            if any(p.name not in known for p in directory.glob(f'{stream}.*.csv')):
                raise ValueError('Orphan or misnamed replay chunk')
    for paths in streams.values():
        files.extend(paths)
    return files, streams


def event_rows(directory):
    """Stream inspect-only rows; native replay remains the integrity authority."""
    _, streams = inventory(directory)
    incomplete = (directory/'recording.incomplete').exists()
    for path in streams['events']:
        def complete_lines(source):
            for line in source:
                if line.endswith('\n'):
                    yield line
                elif not incomplete:
                    raise ValueError('Truncated event record')
        with path.open(newline='') as source:
            rows = csv.DictReader(complete_lines(source), strict=True)
            try:
                yield from rows
            except csv.Error as error:
                if not incomplete or 'unexpected end of data' not in str(error):
                    raise
