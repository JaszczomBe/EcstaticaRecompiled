#!/usr/bin/env python3
"""Compare original tower scene, facing and held-key conditions against x86.

The production condition interpreter executes with an explicit cursor and mapped
actor/node data. Resource loading, script dispatch and gameplay are separate gates.
"""
import argparse
from pathlib import Path
import re

from e2_original import OriginalImage, function, run_fixture, support

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
image = OriginalImage(args.exe)
production = function(Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text(), 'FUN_0044e810')
harness = support() + r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;typedef uint16_t ushort;
typedef uint32_t uint;typedef uint64_t undefined8,ulonglong;
#define __fastcall
#define CONCAT22(a,b) (((uint)(ushort)(a)<<16)|(ushort)(b))
static void FUN_00414e68(void) { assert(!"unqualified condition"); }
static undefined8 FUN_0043cac0(ushort *actor, uint token) { assert(!"unexpected diagnostic");return 0; }
'''
for name in sorted(set(re.findall(r'\b_?DAT_[0-9a-f]+\b', production))):
    address = int(name.rsplit('_', 1)[1], 16)
    harness += f'#define {name} (*(uint*)0x{address:x})\n'
harness += production + '\n'
harness += 'static const byte original[]={' + ','.join(map(str, image.code(0x44e810, 0x44f2fc))) + '};\n'
harness += r'''
/* Original EAX=cursor, EDX/ECX=actors, EBX=node, two callee-popped stack args. */
__attribute__((naked)) static void original_condition(void) {
    __asm__("push $0; push $0; call 0x44e810; ret");
}
static void map(uint at,uint size) {
    assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);
}
static unsigned cases;
static void compare(short opcode,short operand,int invert) {
    short tokens[4]={opcode,operand,0,0};
    if(invert) { tokens[2]=operand;tokens[1]=opcode;tokens[0]=0x19; }
    int original_cursor=(int)tokens,native_cursor=original_cursor;
    struct E2R_Registers regs={.eax=(uint)&original_cursor};
    e2r_original_call((uint)original_condition,&regs);
    uint native=FUN_0044e810(NULL,0,NULL,0,&native_cursor,NULL);
    assert(native==regs.eax && native_cursor==original_cursor);
    cases++;
}
int main(void) {
    map(0x440000,0x10000);map(0x470000,0x10000);
    map(0x630000,0x50000);map(0x900000,0x4000);
    memcpy((void*)0x44e810,original,sizeof original);
    DAT_0047a470=0x900000;*(uint*)0x900054=0x901000;
    for(int flags=0;flags<16;flags++)for(int invert=0;invert<2;invert++) {
        *(ushort*)(0x670c38+83*2)=flags;
        for(int op=8;op<=11;op++)compare(op,0x4053,invert);
    }
    for(unsigned yaw=0;yaw<65536;yaw+=257)for(int invert=0;invert<2;invert++) {
        *(short*)0x900092=yaw;
        for(int op=0xd;op<=0x11;op++)compare(op,0,invert);
    }
    for(int hand=0;hand<2;hand++)for(int node=0;node<2;node++)
    for(int attached=0;attached<2;attached++)for(int key=0;key<2;key++)for(int invert=0;invert<2;invert++) {
        *(uint*)(0x90101c+hand*4)=node?0x902000:0;
        *(uint*)0x90213a=attached?0x903000:0;
        *(short*)0x903000=key?264:3717;
        compare(hand?0x16:0x17,0x2108,invert);
        *(uint*)(0x90101c+hand*4)=0;
    }
    printf("PASS: %u original-x86 tower conditions: scene phase/negation, all facing quadrants, held key versus sword/empty hand; exact cursor advancement\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('Explicit original stack-argument adapter',
                          'Mapped scene flags and authored hand-node attachments',
                          'No resource, script-dispatch or gameplay execution'))
