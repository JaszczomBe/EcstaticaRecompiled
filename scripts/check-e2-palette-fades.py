#!/usr/bin/env python3
"""Compare palette fade intensities and timing against original i386 routines.

Clock and DirectDraw palette submission leaves are intercepted. Palette bytes,
protected entries, repeated-tick/cache behavior and fade flags are compared.
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
typedef uint8_t byte,undefined1;
typedef uint16_t undefined2;
typedef uint64_t ulonglong;
typedef int32_t int3;
#define CONCAT31(a,b) (((uint32_t)(a)<<8)|(uint8_t)(b))
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
typedef uint64_t undefined8;
#define __fastcall
static int DAT_0047ab30,DAT_0047ab34,DAT_0047ab38,DAT_0047ab3c;
static int _DAT_00ac4ae4,_DAT_00ac4a54,_DAT_00ac4a58;
static int tick,submits;
static uint32_t DAT_0047a786,DAT_0047a2a8,DAT_0047a279,DAT_00479e14,DAT_0047a43c,DAT_00479de8;
static uint32_t _DAT_0073cc3c,E2R_start_game_probe_last_mode;
static int E2R_ShouldForceScene785Fallback(void) { return 0; }
static void E2R_SelectSceneRecord(int scene) { assert(0); }
undefined8 FUN_0045fc10(undefined4 a,undefined4 b) { return 0; }
undefined4 FUN_00458094(undefined4 a,undefined4 b) { return 0; }
undefined8 FUN_004146c0(undefined4 a,undefined4 b) { return 0; }
__attribute__((naked)) static void present_hook(void) { __asm__("ret"); }
static uint32_t submitted;
undefined8 FUN_0041cf5c(undefined4 a,undefined4 b) { return (uint)tick; }
undefined4 FUN_0041af88(undefined4 a,undefined4 b) { submitted=a;submits++;return 0; }
__attribute__((naked)) static void clock_hook(void) { __asm__("mov tick,%eax; ret"); }
__attribute__((naked)) static void palette_hook(void) { __asm__("mov %eax,submitted; incl submits; ret"); }
void FUN_00457994(int level);
void FUN_00457a34(int level);
"""
for name in ('FUN_00457818','FUN_00457994','FUN_00457a34'):
    match=re.search(r'^void (?:__fastcall )?'+name+r'\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
    assert match,name
    harness+=match.group()+'\n'
frame=re.search(r'^undefined8 __fastcall FUN_00422238\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
assert frame;harness+=frame.group()+'\n'
frame_code=original(0x422238,0x422330)
harness+='static unsigned char frame_code[]={'+','.join(map(str,frame_code))+'};\n'
code=original(0x457818,0x457ad8)
harness+='static unsigned char original_code[]={'+','.join(map(str,code))+'};\n'
harness+=r"""
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void setup(int mode,int reverse,int elapsed,int duration,int repeated,int cached,int seed) {
    DAT_0047ab30=*(int*)0x47ab30=mode==1||mode==3;
    DAT_0047ab34=*(int*)0x47ab34=mode==2||mode==3;
    DAT_0047ab38=*(int*)0x47ab38=reverse;
    DAT_0047ab3c=*(int*)0x47ab3c=cached;
    _DAT_00ac4a54=*(int*)0xac4a54=1000;
    _DAT_00ac4a58=*(int*)0xac4a58=duration;
    tick=1000+elapsed;
    _DAT_00ac4ae4=*(int*)0xac4ae4=tick-(repeated?0:1);
    for(int i=0;i<768;i++) ((byte*)0x61c730)[i]=(i*17+seed*29)&63;
    memset((void*)0xab9fac,0x95,768);submits=0;submitted=0;
}
static void run_original(int fn,int input) {
    int b=0,c=0,d=0;
    __asm__ volatile("call *%%edi" : "+a"(input),"+b"(b),"+c"(c),"+d"(d) : "D"(fn) : "memory","cc");
}
int main(void) {
    map(0x410000,0x20000);map(0x450000,0x10000);map(0x470000,0x10000);
    map(0x61c000,0x2000);map(0xab9000,0x2000);map(0xac4000,0x2000);
    memcpy((void*)0x457818,original_code,sizeof original_code);
    *(byte*)0x41cf5c=0xe9;*(int*)(0x41cf5d)=(intptr_t)clock_hook-0x41cf61;
    *(byte*)0x41af88=0xe9;*(int*)(0x41af89)=(intptr_t)palette_hook-0x41af8d;
    memcpy((void*)0x422238,frame_code,sizeof frame_code);
    *(byte*)0x458094=0xe9;*(int*)0x458095=(intptr_t)present_hook-0x458099;
    *(byte*)0x4146c0=0xe9;*(int*)0x4146c1=(intptr_t)present_hook-0x4146c5;
    byte expected[768];unsigned cases=0;
    for(int mode=0;mode<4;mode++) for(int reverse=0;reverse<2;reverse++)
    for(int duration=0;duration<=30;duration+=10) for(int elapsed=0;elapsed<=40;elapsed+=5)
    for(int repeat=0;repeat<2;repeat++) for(int cached=-1;cached<=100;cached+=101) {
        setup(mode,reverse,elapsed,duration,repeat,cached,elapsed);
        run_original(0x457818,0);
        memcpy(expected,(void*)0xab9fac,768);
        int expected_state[]={*(int*)0x47ab30,*(int*)0x47ab34,*(int*)0x47ab38,
            *(int*)0x47ab3c,*(int*)0xac4ae4,submits,(int)submitted};
        setup(mode,reverse,elapsed,duration,repeat,cached,elapsed);
        FUN_00457818(0,0);
        int state[]={DAT_0047ab30,DAT_0047ab34,DAT_0047ab38,DAT_0047ab3c,_DAT_00ac4ae4,submits,(int)submitted};
        assert(!memcmp(expected,(void*)0xab9fac,768));assert(!memcmp(state,expected_state,sizeof state));cases++;
    }
    for(int mode=0;mode<2;mode++) for(int level=0;level<=100;level++) {
        setup(0,0,0,0,0,-1,level);run_original(mode?0x457a34:0x457994,level);
        memcpy(expected,(void*)0xab9fac,768);
        setup(0,0,0,0,0,-1,level);
        if(mode) FUN_00457a34(level);else FUN_00457994(level);
        assert(DAT_0047ab3c==level && submits==1 && submitted==0xab9fac);
        assert(!memcmp(expected,(void*)0xab9fac,768));cases++;
    }
    for(int mode=0;mode<4;mode++) for(int level=-1;level<=100;level++) for(int dirty=0;dirty<2;dirty++) {
        setup(mode,0,0,10,0,level,level);
        DAT_0047a786=*(short*)0x47a786=dirty;
        DAT_0047a2a8=*(int*)0x47a2a8=0;
        DAT_0047a279=*(int*)0x47a279=0;
        DAT_0047a43c=*(int*)0x47a43c=4;
        DAT_00479e14=*(int*)0x479e14=0;
        run_original(0x422238,0);
        memcpy(expected,(void*)0xab9fac,768);
        int expected_submits=submits;uint32_t expected_source=submitted;
        int expected_cached=*(int*)0x47ab3c;
        setup(mode,0,0,10,0,level,level);
        DAT_0047a786=dirty;DAT_0047a279=0;
        FUN_00422238(0,0);
        assert(!memcmp(expected,(void*)0xab9fac,768));
        assert(submits==expected_submits && submitted==expected_source && DAT_0047ab3c==expected_cached);
        assert(DAT_0047a279==0x01000000 && DAT_0047a786==0);cases++;
    }
    printf("PASS: %u original-x86 palette fade byte/timing/cache/flag and frame-caller cases\n",cases);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-fade-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    if args.keep_harness:
        import shutil
        shutil.copyfile(c,args.keep_harness.with_suffix('.c'));shutil.copy2(exe,args.keep_harness)
    subprocess.run([str(exe)],check=True,timeout=20)
