"""Shared, bounded original-PE fixture support. The original binary stays external."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile


class OriginalImage:
    def __init__(self, path: Path):
        self.path = path.resolve(strict=True)
        self.data = self.path.read_bytes()
        self.sha256 = hashlib.sha256(self.data).hexdigest()
        if len(self.data) < 64 or self.data[:2] != b'MZ':
            raise ValueError('Original fixture requires a DOS/PE image')
        offset = struct.unpack_from('<I', self.data, 60)[0]
        if offset + 24 > len(self.data) or self.data[offset:offset+4] != b'PE\0\0':
            raise ValueError('Invalid PE header')
        machine, count = struct.unpack_from('<HH', self.data, offset+4)
        size = struct.unpack_from('<H', self.data, offset+20)[0]
        if machine != 0x14c or size < 32 or offset+24+size+count*40 > len(self.data):
            raise ValueError('Fixture requires bounded i386 PE32 sections')
        if struct.unpack_from('<H', self.data, offset+24)[0] != 0x10b:
            raise ValueError('Fixture requires PE32')
        self.base = struct.unpack_from('<I', self.data, offset+24+28)[0]
        self.sections = []
        self.ranges = []
        for i in range(count):
            at = offset+24+size+i*40
            virtual_size, rva, raw_size, raw = struct.unpack_from('<IIII', self.data, at+8)
            # Watcom's original .bss advertises a large SizeOfRawData with a
            # zero file pointer. It has no executable/file-backed bytes.
            if not raw:
                continue
            if raw+raw_size > len(self.data):
                raise ValueError('PE section extends beyond file')
            self.sections.append((self.base+rva, raw_size, raw, virtual_size))

    def code(self, start: int, end: int) -> bytes:
        for address, size, raw, _ in self.sections:
            if address <= start < end <= address+size:
                self.ranges.append((start,end))
                return self.data[raw+start-address:raw+end-address]
        raise ValueError(f'Original range is not backed by one PE section: {start:#x}..{end:#x}')


def function(source: str, name: str) -> str:
    # Exported/reconstructed definitions have column-zero closing braces.
    match = re.search(r'^(?:static )?[^\n;{}=]+\b'+re.escape(name)+
                      r'\([^;\n]*\)\s*\{.*?^\}', source, re.M | re.S)
    if not match:
        raise ValueError(f'Cannot extract production function: {name}')
    return match.group()


def support() -> str:
    return (Path(__file__).with_name('e2_original_fixture.h')).read_text()


def run_fixture(source: str, *, cc='clang-21', asan=False, timeout=30,
                keep: Path | None = None, keep_executable=False, libraries=(),
                image: OriginalImage | None = None, dependencies=()):
    """Compile real extracted C and executable x86; propagate any failed case."""
    with tempfile.TemporaryDirectory(prefix='e2-original-fixture-') as temporary:
        root = Path(temporary)
        src, exe = root/'fixture.c', root/'fixture'
        src.write_text(source)
        if keep:
            target = keep.with_suffix('.c') if keep_executable else keep
            target.write_text(source)
            provenance = dict(schema='e2debug.original-fixture.1',
                              source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                              original_sha256=image.sha256 if image else None,
                              original_ranges=image.ranges if image else [],
                              intercepted_dependencies=list(dependencies), compiler=cc, asan=asan,
                              limit='Dependency interceptions bound the behavior verified by this fixture')
            keep.with_name(keep.name+'.fixture.json').write_text(json.dumps(provenance,indent=2)+'\n')
        flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if asan else []
        subprocess.run([cc, '-m32', '-O1', '-g', '-fno-pie', '-no-pie',
                        '-Wno-int-conversion', *flags, str(src), *libraries, '-o', str(exe)],
                       check=True, timeout=60)
        if keep and keep_executable:
            shutil.copy2(exe, keep)
        subprocess.run([str(exe)], check=True, timeout=timeout)
