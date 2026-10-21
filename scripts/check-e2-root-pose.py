#!/usr/bin/env python3
"""Compare root-pose matrices, saved positions and ownership with original i386.

Includes attached roots and untransformed child bookkeeping. The child world-to-
local conversion (0x42d860) is deliberately excluded. This is a helper fixture,
not full action-event, movement or runtime sanitizer acceptance.
"""
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
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 60)[0]
sections = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]


def original(start, end):
    for i in range(sections):
        at = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(f'Unmapped original {start:x}')


source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()


def function(name):
    match = re.search(r'^(?:static )?(?:void|undefined4) (?:__fastcall )?' + name +
                      r'\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
    assert match, name
    return match.group()


harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort,undefined2;
typedef uint8_t byte;
#define __fastcall
static int E2R_actor_calc_context;
static short DAT_0047a34a,DAT_0047a366;
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
static int E2R_IsBadWritePtr(void *p,unsigned n) { return !p || !n; }
static void FUN_0042d860(void) { assert(!"child conversion outside fixture"); }
'''
for name in ('FUN_00422368', 'FUN_00422460', 'FUN_00422538',
             'E2R_SetIdentityMatrix', 'E2R_ApplyEulerMatrix',
             'FUN_00422aa0', 'FUN_0042b0f4'):
    harness += function(name) + '\n'
for at, end in ((0x422330, 0x422628), (0x422aa0, 0x422ab9), (0x42b0f4, 0x42b337)):
    harness += f'static const byte code_{at:x}[]={{' + ','.join(map(str, original(at, end))) + '};\n'
harness += r'''
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void setup(int flags,int attached,int children,int mode,int seed) {
    memset((void*)0x900000,0x5a,0x10000);
    DAT_0047a34a=*(short*)0x47a34a=mode!=0;
    DAT_0047a366=*(short*)0x47a366=mode==2;
    for(int root=0;root<2;root++) {
        int actor=0x900000+root*0x200;
        *(int*)(actor+0x1e)=children?0x901000+root*0x400:0;
        *(int*)(actor+0xf2)=root==0 && attached?0x904000:0;
        *(byte*)(actor+0x146)=root?attached==2:flags;
        for(int i=0;i<3;i++) {
            *(short*)(actor+0x90+i*2)=seed==0?0:(short)(seed*7919+i*1327);
            *(short*)(actor+0x84+i*2)=(short)(seed*971+root*32701+i*1723);
        }
        for(int j=0;j<2;j++) {
            int child=0x901000+root*0x400+j*0x200;
            *(int*)(child+0x4c)=j==0?child+0x200:0;
            *(byte*)(child+3)=0xfd; // exclude only world-to-local flag 2
            *(ushort*)(child+0x136)=seed*47;
            *(ushort*)(child+0x138)=seed*17;
        }
    }
    *(int*)0x904022=0x900200;
    // The terminal event and its link must survive root-pose work unchanged.
    *(short*)0x906002=0x17;*(int*)0x90600a=0x90600e;
    E2R_actor_calc_context=0x900000;
}
static void run_original(void) {
    int actor=0x900000;
    __asm__ volatile("call *%%edi" : "+a"(actor) : "D"(0x42b0f4) : "memory","cc");
}
int main(void) {
    map(0x420000,0x10000);map(0x470000,0x10000);
    map(0x590000,0x80000);map(0x900000,0x10000);
    memcpy((void*)0x422330,code_422330,sizeof code_422330);
    memcpy((void*)0x422aa0,code_422aa0,sizeof code_422aa0);
    memcpy((void*)0x42b0f4,code_42b0f4,sizeof code_42b0f4);
    for(int i=0;i<65536;i++) {
        *(short*)(0x59b590+i*2)=(short)lrint(sin(i*6.283185307179586/65536)*16384);
        *(short*)(0x5de590+i*2)=(short)lrint(cos(i*6.283185307179586/65536)*16384);
    }
    static byte expected[0x10000];
    unsigned cases=0;
    for(int flags=0;flags<2;flags++)for(int attached=0;attached<3;attached++)
    for(int children=0;children<2;children++)for(int mode=0;mode<3;mode++)
    for(int seed=0;seed<32;seed++) {
        setup(flags,attached,children,mode,seed);run_original();
        memcpy(expected,(void*)0x900000,sizeof expected);
        setup(flags,attached,children,mode,seed);FUN_0042b0f4();
        if(memcmp(expected,(void*)0x900000,sizeof expected)) {
            fprintf(stderr,"mismatch flags=%d attached=%d children=%d mode=%d seed=%d\n",
                    flags,attached,children,mode,seed);abort();
        }
        assert(*(int*)0x90600a==0x90600e);
        assert(E2R_actor_calc_context==0x900000);cases++;
    }
    printf("PASS: %u original-x86 root-pose matrix/position/ownership cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-root-pose-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    if args.keep_harness:
        args.keep_harness.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', '-Wno-return-type', '-Wno-int-conversion',
                    *flags, str(c), '-lm', '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=20)
