#!/usr/bin/env python3
"""Compare terminal/interpolated action motion with original i386.

Root reset, world query and visibility are intercepted leaves. Production event
ownership, translation accumulation and Q14 transform are compared, including
attached owners and reset context restoration. This does not prove gameplay.
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
    raise ValueError(start)
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
def function(name):
    m = re.search(r'^(?:static )?(?:void|short|undefined4) (?:__fastcall )?' + name +
                  r'\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
    assert m, name
    return m.group()
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort,undefined2;
typedef uint8_t byte;
#define __fastcall
static int E2R_actor_calc_context;
static int reset_actor,query_actor,visible_actor;
static short queried[3];
__attribute__((used,noinline)) static void reset(int actor) { reset_actor=actor; }
static void FUN_0042b0f4(void) { reset(E2R_actor_calc_context); }
__attribute__((used,noinline)) static void FUN_00448c1c(uint actor,int *vector) {
    query_actor=actor;memcpy(queried,vector,6);
    // Nested services must not replace the event's retained actor.
    E2R_actor_calc_context=0x905000;
}
__attribute__((used,noinline)) static uint FUN_0044d2b4(uint actor) {visible_actor=actor;return 0;}
__attribute__((naked)) static void reset_hook(void) {
    __asm__("pushal; push %eax; call reset; add $4,%esp; popal; ret");
}
__attribute__((naked)) static void query_hook(void) {
    __asm__("pushal; push %edx; push %eax; call FUN_00448c1c; add $8,%esp; popal; ret");
}
__attribute__((naked)) static void visibility_hook(void) {
    __asm__("pushal; push %eax; call FUN_0044d2b4; add $4,%esp; popal; ret");
}
'''
harness += function('E2R_TransformVector14') + '\n' + function('E2R_ApplyActionMotion13') + '\n'
for start,end in ((0x42b71c,0x42ce70),(0x45de8b,0x45df0e)):
    harness += f'static const byte code_{start:x}[]={{'+','.join(map(str,original(start,end)))+'};\n'
harness += r'''
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void hook(int address,void *fn) {
    *(byte*)address=0xe9;*(int*)(address+1)=(int)fn-address-5;
}
static void run_original(int interpolate,int factor) {
    int actor=0x900000,event=0x904000,action=0x903000;
    if(interpolate) {
        __asm__ volatile("call *%%edi" : "+a"(event),"+d"(factor),"+b"(actor),"+c"(action)
                         : "D"(0x42c790) : "memory","cc");
    } else {
        __asm__ volatile("call *%%edi" : "+a"(event),"+d"(actor),"+b"(action)
                         : "D"(0x42b880) : "ecx","memory","cc");
    }
}
static void setup(int attached,int flags,int seed) {
    memset((void*)0x900000,0,0x10000);
    reset_actor=query_actor=visible_actor=0;memset(queried,0,sizeof queried);
    E2R_actor_calc_context=0x903000;
    *(int*)0x9000f2=attached?0x902000:0;*(int*)0x902022=0x900200;
    *(byte*)0x900146=flags?0x20:0;
    *(byte*)0x900346=(attached==2?1:0)|(flags?0x20:0);
    *(short*)0x904000=-1;*(short*)0x904002=0x13;
    for(int j=0;j<2;j++)for(int i=0;i<3;i++) {
        *(short*)(0x90002c+j*0x200+i*2)=(short)(seed*4171+i*1031+j*7919);
        for(int k=0;k<3;k++)
            *(short*)(0x9000c6+j*0x200+i*6+k*2)=(short)(seed*1013+j*7919+i*721+k*1999);
        *(short*)(0x904004+i*2)=(short)(seed*7919+i*3169);
    }
}
int main(void) {
    map(0x420000,0x10000);map(0x440000,0x10000);map(0x450000,0x10000);
    map(0x470000,0x10000);map(0x630000,0x10000);map(0x900000,0x10000);
    memcpy((void*)0x42b71c,code_42b71c,sizeof code_42b71c);
    memcpy((void*)0x45de8b,code_45de8b,sizeof code_45de8b);
    hook(0x42b0f4,reset_hook);hook(0x448c1c,query_hook);hook(0x44d2b4,visibility_hook);
    static byte expected[0x10000];int factors[]={0,1,8192,16383,16384};unsigned cases=0;
    for(int interpolate=0;interpolate<2;interpolate++)for(int attached=0;attached<3;attached++)
    for(int flags=0;flags<2;flags++)for(int seed=0;seed<32;seed++)for(int f=0;f<5;f++) {
        setup(attached,flags,seed);run_original(interpolate,factors[f]);
        memcpy(expected,(void*)0x900000,sizeof expected);
        int er=reset_actor,eq=query_actor,ev=visible_actor;short vector[3];memcpy(vector,queried,6);
        setup(attached,flags,seed);E2R_ApplyActionMotion13(0x900000,(short*)0x904000,factors[f],interpolate);
        if(memcmp(expected,(void*)0x900000,sizeof expected)||er!=reset_actor||eq!=query_actor||
           ev!=visible_actor||memcmp(vector,queried,6)) {
            fprintf(stderr,"event mismatch interpolate=%d attached=%d reset=%d seed=%d factor=%d\n",
                    interpolate,attached,flags,seed,factors[f]);abort();
        }
        assert(E2R_actor_calc_context==0x905000);cases++;
    }
    printf("PASS: %u original-i386 terminal/interpolated motion vector/owner cases (query/reset/visibility intercepted)\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-action-motion-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    if args.keep_harness:args.keep_harness.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=20)
