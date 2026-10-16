#!/usr/bin/env python3
"""Compare unsigned scene-grid descriptor selection with original i386 code.

Includes high ceiling bytes, linked descriptors, shape masks, grid boundaries,
missing cells and preservation of the caller's actor argument.
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
typedef uint8_t byte,undefined1,bool;
typedef uint64_t undefined8;
#define __fastcall
#define true 1
#define false 0
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
static int DAT_0047a738,DAT_0047a77c,DAT_0047a470,_DAT_0073cc3c;
static int DAT_0047a34a,DAT_0064a178,_DAT_0063726c;
static int fallback_resource,fallback_calls;
static uint64_t FUN_0043a6e0(uint32_t resource,uint32_t retained) { fallback_resource=resource;fallback_calls++;return 0; }
__attribute__((naked)) static void fallback_hook(void) { __asm__("mov %eax,fallback_resource; incl fallback_calls; ret"); }
static unsigned E2R_actor_loop_diag_count,E2R_scene_lookup_diag_count;
static int E2R_RuntimeDiagEnabled(void) { return 0; }
static int E2R_ActionIndexProbeEnabled(void) { return 1; }
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
static void E2R_LogSceneGridProbe(const char *s,int x,int z) { }
"""
for name in ('FUN_00448744','FUN_004488a4'):
    match=re.search(r'^undefined8 __fastcall '+name+r'\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
    assert match,name;harness+=match.group()+'\n'
at=source.index('  if (sVar2 < 1) {',source.index('void __fastcall FUN_0044c224('))
end=source.index('  DAT_0047a788 = 1;',at)
branch=source[at:end]
# Keep only the no-view branch; the following matching-view reset is outside it.
branch=branch[:branch.rfind('  }')+3]
harness+='static void no_view_native(void) { int iVar1; short sVar2=0; uint uVar3=0;\n'+branch+'\njoined_r0x0044c464: return; }\n'
fallback_code=original(0x44c440,0x44c45d)
harness+='static unsigned char fallback_code[]={'+','.join(map(str,fallback_code))+'};\n'
code=original(0x44872c,0x4489ec)
harness+='static unsigned char original_code[]={'+','.join(map(str,code))+'};\n'
harness+=r"""
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static uint64_t run_original(int fn,uintptr_t coord,uintptr_t actor) {
    __asm__ volatile("call *%%edi" : "+a"(coord),"+d"(actor) : "D"(fn) : "memory","cc");
    return ((uint64_t)actor<<32)|coord;
}
static uint32_t rng=0x7412;
static unsigned next(void) { rng=rng*1664525+1013904223;return rng; }
int main(void) {
    map(0x430000,0x20000);map(0x470000,0x10000);map(0x680000,0x10000);map(0x640000,0x10000);map(0x900000,0x1000);
    memcpy((void*)0x44872c,original_code,sizeof original_code);
    memcpy((void*)0x44c440,fallback_code,sizeof fallback_code);*(byte*)0x44c45d=0xc3;
    *(byte*)0x43a6e0=0xe9;*(int*)0x43a6e1=(intptr_t)fallback_hook-0x43a6e5;
    for(int mode=0;mode<2;mode++) for(int dead=0;dead<2;dead++) {
        DAT_0047a34a=*(short*)0x47a34a=mode;
        DAT_0064a178=*(byte*)0x64a178=dead?4:0;
        fallback_calls=0;fallback_resource=-1;
        run_original(0x44c440,0,0);
        int expected_calls=fallback_calls,expected_resource=fallback_resource;
        fallback_calls=0;fallback_resource=-1;no_view_native();
        assert(fallback_calls==expected_calls && fallback_resource==expected_resource);
        if(!mode && !dead)assert(fallback_resource==7);
    }
    unsigned cases=0,high=0;short *coord=(short*)0x900000;
    memset((void*)0x684d68,0xff,0x8000);
    for(int sample=0;sample<8192;sample++) {
        coord[0]=(short)next();coord[1]=(short)next();coord[2]=(short)next();
        if(sample<16) { coord[0]=sample&1?-32768:32767;coord[2]=sample&2?-32768:32767; }
        DAT_0047a738=*(int*)0x47a738=sample%9;
        uintptr_t cell=0x684d68+((coord[0]>>9)+64)*2+((coord[2]>>9)+64)*256;
        *(ushort*)cell=sample%17?0:0xffff;
        for(int i=0;i<8;i++) {
            byte *desc=(byte*)0x68cd68+i*12;
            memset(desc,0,12);desc[0]=next()>>24;desc[1]=sample%64;
            desc[5]=next()>>24;desc[7]=next()>>24;
            if(desc[5]>=128)high++;
            if(i==7)desc[3]=0x80;
        }
        for(int mode=0;mode<2;mode++) {
            uint64_t expected=run_original(mode?0x4488a4:0x448744,(uintptr_t)coord,0x900100);
            uint64_t actual=mode?FUN_004488a4((uintptr_t)coord,0x900100):FUN_00448744((uintptr_t)coord,(ushort*)0x900100);
            assert(actual==expected);cases++;
        }
        *(ushort*)cell=0xffff;
    }
    printf("PASS: %u original-x86 scene-grid selection cases (%u high ceiling descriptors); 4 no-view fallback routing cases\n",cases,high);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-grid-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    if args.keep_harness:
        import shutil
        shutil.copyfile(c,args.keep_harness.with_suffix('.c'));shutil.copy2(exe,args.keep_harness)
    subprocess.run([str(exe)],check=True,timeout=20)
