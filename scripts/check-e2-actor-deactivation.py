#!/usr/bin/env python3
"""Compare actor deactivation fields and callback ownership against original i386.

The callback entry is intercepted; formatting/error branches and full death
presentation are outside this fixture.
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
parser.add_argument('--keep-harness', type=Path, help='Retain fixture source/executable for debugger inspection')
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


source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness=r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort;
typedef uint8_t byte,undefined1;
#define __fastcall
#define FUN_00441890(...) assert(0)
#define FUN_0045f0a1(...) assert(0)
#define FUN_00442128(...) assert(0)
#define FUN_0043cbd0(...) assert(0)
static short *DAT_0047a470;
static int DAT_0047ab18,DAT_0047a3b4;
static uint32_t callback_code,callback_actor;
static unsigned callbacks;
undefined4 FUN_0044f320(uint code,ushort *actor,ushort *node) {
    assert(!node);callback_code=code;callback_actor=(uintptr_t)actor;callbacks++;return 0;
}
__attribute__((naked)) static void callback_hook(void) {
    __asm__("mov %eax,callback_code; mov %edx,callback_actor; incl callbacks; ret");
}
"""
match=re.search(r'^void __fastcall FUN_004273cc\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
assert match;harness+=match.group()+'\n'
code=original(0x4273cc,0x4274c4)
harness+='static unsigned char original_code[]={'+','.join(map(str,code))+'};\n'
harness+=r"""
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void setup(int rep,int reward,int current,int rendering,int callback,int seed) {
    memset((void*)0x900000,0,0x10000);memset((void*)0x64a178,0,128);
    *(short*)0x900000=seed;
    *(int*)0x90011e=rep?0x901000:0;
    *(short*)0x9010a2=reward?0:-1;*(short*)0x901014=-1;*(byte*)0x9011aa=0xff;
    *(short*)0x90013e=callback?5:-1;
    *(int*)(0x6297c0+20)=0x904000;
    *(byte*)0x900003=seed;*(short*)0x900122=16;*(short*)0x9000e8=0;
    DAT_0047ab18=*(int*)0x47ab18=3;
    DAT_0047a3b4=*(int*)0x47a3b4=rendering;
    DAT_0047a470=(short*)(*(int*)0x47a470=current?0x900000:0x902000);
    callbacks=0;callback_code=0;callback_actor=0;
}
int main(void) {
    map(0x420000,0x10000);map(0x440000,0x10000);map(0x470000,0x10000);
    map(0x629000,0x3000);map(0x640000,0x10000);map(0x900000,0x10000);
    memcpy((void*)0x4273cc,original_code,sizeof original_code);
    *(byte*)0x44f310=0xe9;*(int*)0x44f311=(intptr_t)callback_hook-0x44f315;
    byte expected[0x10000],flags[128];unsigned cases=0;
    for(int rep=0;rep<2;rep++) for(int reward=0;reward<2;reward++) for(int current=0;current<2;current++)
    for(int rendering=0;rendering<2;rendering++) for(int callback=0;callback<2;callback++) for(int seed=0;seed<8;seed++) {
        setup(rep,reward,current,rendering,callback,seed);
        uintptr_t actor=0x900000;
        __asm__ volatile("call *%%edi" : "+a"(actor) : "D"(0x4273cc) : "ecx","edx","memory","cc");
        memcpy(expected,(void*)0x900000,sizeof expected);memcpy(flags,(void*)0x64a178,128);
        int count=*(int*)0x47ab18;unsigned calls=callbacks;uint32_t code=callback_code,owner=callback_actor;
        setup(rep,reward,current,rendering,callback,seed);FUN_004273cc(0x900000);
        assert(!memcmp(expected,(void*)0x900000,sizeof expected));assert(!memcmp(flags,(void*)0x64a178,128));
        assert(DAT_0047ab18==count && callbacks==calls && callback_code==code && callback_actor==owner);cases++;
    }
    printf("PASS: %u original-x86 actor deactivation field/owner/callback cases\n",cases);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-deactivation-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    if args.keep_harness:
        import shutil
        shutil.copyfile(c,args.keep_harness.with_suffix('.c'));shutil.copy2(exe,args.keep_harness)
    subprocess.run([str(exe)],check=True,timeout=20)
