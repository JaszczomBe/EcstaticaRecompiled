#!/usr/bin/env python3
"""Compare target-facing selection and its player caller with original i386.

Runs the original selection/distance/interpolation instructions and production C.
Actor-list and representation metadata are synthetic; no gameplay is inferred.
"""
import argparse
from pathlib import Path
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
    raise ValueError(start)
import re
source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
def function(name):
    m=re.search(r'^(?:static )?(?:void|short) (?:__fastcall )?'+name+r'\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
    assert m,name
    return m.group()
call=re.search(r'^        FUN_0042ed6c\([^;]+;',source,re.M).group()
harness=r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort;
typedef uint8_t byte,undefined1;
typedef uint8_t bool;
#define false 0
#define true 1
#define __fastcall
static short *_DAT_0063726c;
"""+function('E2R_PolygonAngle16')+'\n'+function('FUN_0042ed6c')+r"""
static void native_call(short *local_6c,int local_64,uint uVar25) {
"""+call+r"""
}
__attribute__((naked)) static void original_call(void *frame) {
    __asm__("pushal; mov 36(%esp),%ebp; mov $0x429b1f,%edi; call *%edi; popal; ret");
}
static void original_helper(int actor,int elapsed,int distance) {
    __asm__ volatile("call *%%edi" : "+a"(actor),"+d"(elapsed),"+b"(distance) : "D"(0x42ed6c) : "ecx","memory","cc");
}
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
"""
for start,end in ((0x429b1f,0x429b2f),(0x42ed6c,0x42efdc),(0x432c64,0x432de4)):
    harness+='static const byte code_'+hex(start)[2:]+'[]={'+','.join(map(str,original(start,end)))+'};\n'
harness+=r"""
static uint rng=0x12345678;
static uint next(void) {rng=rng*1664525+1013904223;return rng;}
static void setup(int seed,int actors,int elapsed) {
    rng=seed;memset((void*)0x900000,0,0x10000);memset((void*)0x64a178,0,128);
    _DAT_0063726c=*(short**)0x63726c=actors?(short*)0x900000:0;
    int px=(seed%3-1)*15000,pz=((seed/3)%3-1)*15000;
    for(int i=0;i<5;i++) {
        int a=0x900000+i*0x200,r=0x902000+i*0x200;
        *(short*)a=i;
        *(int*)(a+0x11e)=seed%7==i?0:r;
        *(int*)(a+0x4c)=i+1<actors?a+0x200:0;
        *(byte*)(a+2)=next()&8;*(byte*)(a+3)=next()&2;
        *(short*)(a+0x84)=px+(i?(int)(next()%4001)-2000:0);
        *(short*)(a+0x86)=3328+(i?(int)(next()%2049)-1024:0);
        *(short*)(a+0x88)=pz+(i?(int)(next()%4001)-2000:0);
        *(short*)(a+0x92)=next();
        *(short*)(r+0x14)=next()%5?8:-1;
        *(short*)(r+0x46)=next()%5?11:-1;
        *(byte*)(0x64a178+i*2)=next()%7?0:4;
    }
    int a=0x900000;
    *(int*)(a+0xa6)=seed%7?0x904000:0;
    *(ushort*)(a+0xac)=(ushort[]){0,1,10000,32768,65534,65535}[seed%6];
    *(ushort*)0x904002=(ushort[]){0,1,34,366}[seed%4];
    *(int*)0x90602a=a;*(int*)0x906032=elapsed;
}
int main(void) {
    map(0x420000,0x20000);map(0x590000,0x80000);
    map(0x630000,0x20000);map(0x900000,0x10000);
"""
for start in (0x429b1f,0x42ed6c,0x432c64):
    harness+=f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness+=r"""
    *(byte*)0x429b2f=0xc3;
    for(int i=0;i<65536;i++) {
        *(short*)(0x59b590+i*2)=(short)lrint(sin(i*6.283185307179586/65536)*16384);
        *(short*)(0x5de590+i*2)=(short)lrint(cos(i*6.283185307179586/65536)*16384);
    }
    for(int i=0;i<256;i++) {
        *(byte*)(0x5fe990+i)=(byte)(atan(i*0.015625)*64.0*2.0*0.3183101550488765+0.5);
        *(byte*)(0x5fe890+i)=(byte)(atan(i*0.25)*64.0*2.0*0.3183101550488765+0.5);
    }
    static byte expected[0x10000];unsigned cases=0;
    for(int seed=0;seed<512;seed++)for(int actors=0;actors<=5;actors++)
    for(int time=0;time<4;time++)for(int range=0;range<4;range++) {
        int elapsed=(int[]){0,1,6,20}[time],distance=(int[]){0,512,1280,4096}[range];
        setup(seed,actors,elapsed);original_helper(0x900000,elapsed,distance);
        memcpy(expected,(void*)0x900000,sizeof expected);
        setup(seed,actors,elapsed);FUN_0042ed6c(0x900000,elapsed,distance);
        if(memcmp(expected,(void*)0x900000,sizeof expected)) {
            fprintf(stderr,"target mismatch seed=%d actors=%d elapsed=%d range=%d\n",seed,actors,elapsed,distance);abort();
        }
        if(distance==1280) {
            setup(seed,actors,elapsed);original_call((void*)0x906000);memcpy(expected,(void*)0x900000,sizeof expected);
            setup(seed,actors,elapsed);native_call((short*)0x900000,elapsed,0xdeadbeef);
            assert(!memcmp(expected,(void*)0x900000,sizeof expected));
        }
        cases++;
    }
    printf("PASS: %u original-i386 target selection/distance/interpolation cases; %u player actor/time/range calls\n",cases,cases/4);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-target-facing-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    if args.keep_harness:args.keep_harness.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-lm','-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=60)
