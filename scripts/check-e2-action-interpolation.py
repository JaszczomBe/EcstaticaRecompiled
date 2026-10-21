#!/usr/bin/env python3
"""Compare bounded actor/node interpolation branches with original i386 code.

Exercises recovered event/factor/actor/action inputs. Transform-helper branches
are outside this fixture; it does not establish full animation or gameplay.
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
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
count = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]


def original(start, end):
    for i in range(count):
        at = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(start)


source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <assert.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort,undefined2;
typedef uint8_t byte,undefined1;
#define __fastcall
static uint32_t DAT_0047a7e0,DAT_0047a34a,DAT_0047a366;
static void E2R_ApplyActionMotion13(int actor,const short *event,int factor,int interpolate) {
    assert(!"motion transform belongs to check-e2-action-motion.py");
}
"""
match = re.search(r'^void __fastcall FUN_0042c790\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
assert match
for name in sorted(set(re.findall(r'\b(FUN_\w+)\(',match.group())) - {'FUN_0042c790'}):
    params = 'uint32_t a, int *b' if name == 'FUN_00448c1c' else 'uint32_t a' if name == 'FUN_0044d2b4' else 'void'
    harness += f'void {name}({params}) {{ assert(!"unexpected helper branch"); }}\n'
harness += match.group() + '\n'
code=original(0x42c790,0x42ce70)
harness += 'static unsigned char original_code[]={' + ','.join(map(str,code)) + '};\n'
harness += r"""
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void run_original(short *event,int factor,int actor,int action) {
    __asm__ volatile("call *%%edi" : "+a"(event),"+d"(factor),"+b"(actor),"+c"(action) : "D"(0x42c790) : "memory","cc");
}
static void setup(int opcode,int seed) {
    memset((void*)0x900000,0,0x10000);
    *(int*)0x900054=0x902000; *(int*)(0x902000+12)=0x901000;
    *(short*)0x903000=3; *(short*)0x903002=opcode;
    for(int i=0;i<3;i++) {
        ((short*)0x903004)[i]=(seed*971+i*283)%32000-16000;
        *(short*)(0x901026+i*2)=seed*13+i*31-200;
        *(short*)(0x901056+i*2)=seed*5+i*17-123;
        *(short*)(0x901110+i*2)=seed*9+i*23-567;
        *(short*)(0x900084+i*2)=seed*11+i*19-222;
        *(short*)(0x900090+i*2)=seed*7+i*3-121;
    }
    *(short*)(0x63679e + opcode*2)=(opcode==1||opcode==0xd||opcode==0xe||opcode==0x1f)?0x10:0;
}
int main(void) {
    map(0x420000,0x10000);map(0x470000,0x10000);map(0x630000,0x10000);map(0x900000,0x10000);
    memcpy((void*)0x42c790,original_code,sizeof original_code);
    static unsigned char expected[0x10000];
    int ops[]={1,0xd,0xe,0x16,0x17,0x1f},factors[]={0,1,2048,8192,16383,16384};
    unsigned cases=0;
    for(int i=0;i<6;i++) for(int j=0;j<6;j++) for(int seed=0;seed<16;seed++) {
        setup(ops[i],seed);run_original((short*)0x903000,factors[j],0x900000,0x904000);
        memcpy(expected,(void*)0x900000,sizeof expected);
        setup(ops[i],seed);FUN_0042c790(0x904000,factors[j],(short*)0x903000,0x900000);
        assert(!memcmp(expected,(void*)0x900000,sizeof expected));cases++;
    }
    printf("PASS: %u original-x86 interpolated actor/node state cases\n",cases);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-interpolation-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-Wno-deprecated-non-prototype','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=20)
