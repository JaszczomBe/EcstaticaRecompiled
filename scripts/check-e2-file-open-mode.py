#!/usr/bin/env python3
"""Compare both CRT open-mode output destinations against original i386 code."""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--asan', action='store_true')
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 60)[0]
sections = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]
for i in range(sections):
    at = header + 24 + optional + i * 40
    _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
    va += 0x400000
    if va <= 0x4605bc < 0x4605e8 <= va + size:
        code = pe[raw + 0x4605bc - va:raw + 0x4605e8 - va]
        break
else:
    raise ValueError('Missing original helper')
root = Path(__file__).resolve().parent.parent
source = (root / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
function = re.search(r'^void __fastcall FUN_004605bc\([^\n]*\)\s*\{.*?^\}', source, re.M | re.S).group()
assert 'FUN_004605bc(uVar6,&local_20,&local_1c);' in source
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef uint32_t undefined4;
#define __fastcall
''' + function + '\nstatic const unsigned char original_code[]={' + ','.join(map(str, code)) + r'''};
static void invoke(void *fn, uint32_t mode, uint32_t *access, uint32_t *attributes) {
    __asm__ volatile("call *%3" : "+a"(mode), "+d"(access), "+b"(attributes)
                     : "r"(fn) : "ecx", "cc", "memory");
}
int main(void) {
    void *code=mmap(0,4096,7,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    assert(code!=MAP_FAILED); memcpy(code,original_code,sizeof original_code);
    uint32_t modes[]={0,1,2,3,4,7,0x80,0x200,0xffffffff,0x80000000};
    unsigned cases=0;
    for(unsigned k=0;k<sizeof(modes)/sizeof(modes[0]);k++)
    for(unsigned a=1;a<7;a++) for(unsigned b=1;b<7;b++) {
        uint32_t expected[8],actual[8];
        for(unsigned i=0;i<8;i++)expected[i]=actual[i]=0xa5a50000+i;
        invoke(code,modes[k],expected+a,expected+b);
        FUN_004605bc(modes[k],actual+a,actual+b);
        assert(!memcmp(actual,expected,sizeof actual));cases++;
    }
    printf("PASS: %u original-i386 access/attributes/alias/canary cases; caller retains EBX output\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-file-open-mode-') as directory:
    c = Path(directory) / 'check.c'
    exe = Path(directory) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', *flags, str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=20)
