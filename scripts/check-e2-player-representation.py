#!/usr/bin/env python3
"""Compare Joe's representation selection and transition action with original i386.

Actor/held-item/terrain inputs, loader ownership and live packed keyboard reads are covered. The action load
is intercepted; this fixture does not establish movement, asset or query fidelity.
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
header = struct.unpack_from('<I', pe, 60)[0]
sections = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]
def original(start,end):
    for i in range(sections):
        at = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(start)
code = original(0x4575c4,0x45777f)
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
match = re.search(r'^static void E2R_SelectPlayerRepresentation\(void\)\s*\{.*?\n\}', source, re.M | re.S)
assert match
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint8_t byte;
static uintptr_t DAT_0047a470;
static int DAT_0047a7ec;
static byte DAT_0047a738,DAT_00670c44;
static int calls,load_id;
__attribute__((used,noinline)) static void FUN_00451880(int unused,int id) {
    assert(unused==0);calls++;load_id=id;
    // A nested loader may change the global current actor. The selector must
    // retain its original actor, as EDX does across original 0x451880.
    DAT_0047a470=*(int*)0x47a470=0x903000;
}
__attribute__((naked)) static void loader_hook(void) {
    __asm__("pushal; push %eax; push $0; call FUN_00451880; add $8,%esp; popal; ret");
}
'''
harness += match.group() + '\n'
# Extract the production keyboard branch, before the shared arithmetic shifts.
keyboard = re.search(r'        iVar7 = \*\(int \*\)0x004c3ad8;.*?iVar9 = \*\(int \*\)0x004c3ad5;', source, re.S)
assert keyboard
harness += 'static void keyboard_native(int out[4]) { int iVar7,iVar17,local_38,iVar9;\n'
harness += keyboard.group() + '\n'
harness += 'out[0]=iVar7>>24;out[1]=iVar17>>24;out[2]=local_38;out[3]=iVar9>>24;}\n'
harness += 'static const byte keyboard_code[]={' + ','.join(map(str, original(0x429005,0x42904f))) + '};\n'

harness += 'static const byte original[]={' + ','.join(map(str, code)) + '};\n'
harness += r'''
static int keyboard_result[4];
__attribute__((naked)) static void keyboard_original(void) {
    __asm__("pushal; sub $128,%esp; mov %esp,%ebp; mov $0x429005,%eax; call *%eax; "
            "mov %ecx,keyboard_result; mov %ebx,keyboard_result+4; "
            "mov 0x5e(%ebp),%eax; mov %eax,keyboard_result+8; mov %edx,keyboard_result+12; "
            "add $128,%esp; popal; ret");
}
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void setup(int owner,int held,int stance,int terrain,int height,int shift,int bit,int loaded) {
    memset((void*)0x900000,0x5a,0x10000);
    DAT_0047a470=*(int*)0x47a470=owner==0?0:0x900000;
    *(short*)0x900000=owner==2?1:0;
    *(short*)0x900002=0x29; // flags are not part of the actor ID
    *(int*)0x900054=0x900800;
    *(int*)0x900820=held?0x901000:0;
    *(int*)0x90113a=held>1?0x902000:0;
    *(byte*)0x902002=held>=3?0x10:0;
    *(short*)0x902184=held==4?1:held==5?-1:0;
    *(short*)0x900184=stance;
    *(short*)0x900086=height;
    *(int*)0x9000a6=0x904000;
    *(int*)0x900126=0x905000;
    DAT_0047a7ec=*(int*)0x47a7ec=terrain;
    DAT_0047a738=*(byte*)0x47a738=shift;
    *(byte*)0x670c44=bit?8:0;
    DAT_00670c44=bit?0:8; // Independent generated label must not hide live scene updates.
    *(int*)0x62ba2c=*(int*)0x62ba30=loaded==0?0:loaded==1?0x904000:0x906000;
    calls=0;load_id=-1;
}
int main(void) {
    map(0x420000,0x10000);map(0x4c0000,0x10000);
    map(0x450000,0x10000);map(0x470000,0x10000);map(0x62b000,0x1000);
    map(0x670000,0x1000);map(0x900000,0x10000);
    memcpy((void*)0x4575c4,original,sizeof original);
    *(byte*)0x451880=0xe9;*(int*)0x451881=(intptr_t)loader_hook-0x451885;
    static byte expected[0x10000];unsigned cases=0;
    int heights[]={-100,39,40,41,5119,5120,5121,32767};
    for(int owner=0;owner<3;owner++)for(int held=0;held<6;held++)
    for(int stance=-1;stance<=1;stance++)for(int terrain=6;terrain<=7;terrain++)
    for(int h=0;h<8;h++)for(int shift=0;shift<=7;shift+=7)
    for(int bit=0;bit<2;bit++)for(int loaded=0;loaded<3;loaded++) {
        setup(owner,held,stance,terrain,heights[h],shift,bit,loaded);
        int a=0;
        __asm__ volatile("call *%%edi" : "+a"(a) : "D"(0x4575c4) : "memory","cc");
        memcpy(expected,(void*)0x900000,sizeof expected);
        int expected_calls=calls,expected_id=load_id,current=*(int*)0x47a470;
        setup(owner,held,stance,terrain,heights[h],shift,bit,loaded);
        E2R_SelectPlayerRepresentation();
        assert(!memcmp(expected,(void*)0x900000,sizeof expected));
        assert(calls==expected_calls && load_id==expected_id && DAT_0047a470==(uintptr_t)current);
        cases++;
    }
    printf("PASS: %u original-x86 player representation/queue/owner cases\n",cases);
    memcpy((void*)0x429005,keyboard_code,sizeof keyboard_code);*(byte*)0x42904f=0xc3;
    int values[]={0,1,0x80,0xff};unsigned keyboards=0;
    for(int l=0;l<4;l++)for(int r=0;r<4;r++)for(int d=0;d<4;d++)for(int f=0;f<4;f++) {
        memset((void*)0x4c3a90,0xa5,0x200);
        *(byte*)0x4c3adb=values[l];*(byte*)0x4c3add=values[r];
        *(byte*)0x4c3ae0=values[d];*(byte*)0x4c3ad8=values[f];
        keyboard_original();int observed[4];keyboard_native(observed);
        assert(!memcmp(observed,keyboard_result,sizeof observed));keyboards++;
    }
    printf("PASS: %u original-x86 packed keyboard direction cases\n",keyboards);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-player-representation-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie',
                    *flags, str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=20)
