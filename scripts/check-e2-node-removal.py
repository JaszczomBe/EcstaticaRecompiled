#!/usr/bin/env python3
"""Compare node unlinking/cleanup with original E2WIN95 i386 code.

Fixtures cover root/child/sibling lists, node tables, parent flags, recursive
children, vertex-dependent polygon removal and retained deletion marks. The
original message leaf is intercepted; no executable bytes are stored in the repo.
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
    raise ValueError(f'Unmapped original: {start:x}')


source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <assert.h>
typedef uint32_t undefined4;
typedef uint64_t undefined8;
typedef uint16_t ushort;
typedef uint8_t byte;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
static uint32_t message;
undefined8 FUN_0043cac0(undefined4 text,undefined4 unused) { message=text; return 0x1234; }
void FUN_0043a9a8(int polygon);
__attribute__((naked)) static void original_message(void) {
    __asm__("mov %eax,message; mov $0x1234,%eax; ret");
}
'''
for name in ('FUN_0043a8f8', 'FUN_0043a9a8', 'FUN_0043ab74'):
    match = re.search(r'^(?:void|undefined[48]) (?:__fastcall )?' + name + r'\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
    if not match:
        raise ValueError(f'Missing function {name}')
    harness += match.group() + '\n'
for at, end in ((0x43a8f8, 0x43aa13), (0x43ab74, 0x43ac5d),
                (0x453264, 0x45326b), (0x453508, 0x45350f), (0x45366c, 0x453673)):
    code = original(at, end)
    harness += f'static const unsigned char code_{at:x}[]={{' + ','.join(map(str, code)) + '};\n'
harness += r'''
static void map(uintptr_t at,size_t n,int exec) {
    assert(mmap((void*)at,n,PROT_READ|PROT_WRITE|(exec?PROT_EXEC:0),
                MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void w32(int base,int off,int value) { *(int*)(base+off)=value; }
static void w16(int base,int off,int value) { *(short*)(base+off)=value; }
static int setup(int list,int flags,int children,int polygons) {
    memset((void*)0x900000,0,0x10000);
    int actor=0x900000, sentinel=0x900200, target=0x900400;
    int parent=0x900600, grand=0x900800, child=0x900a00, sibling=0x900c00;
    int nodes[]={sentinel,target,parent,grand,child,sibling};
    w32(actor,0x54,0x902000); w32(actor,0xdc,0x903000);
    for(int i=0;i<6;i++) {
        w16(nodes[i],0,i); w32(nodes[i],0x22,actor);
        w32(0x902000,i*4,nodes[i]);
    }
    w32(target,0x44,parent); w32(parent,0x44,grand);
    w16(parent,4,flags&1?7:0); w16(grand,4,flags&2?7:0);
    w16(parent,2,0x20); w16(grand,2,0x20);
    w32(parent,0x1e,flags&4?target:sentinel);
    w32(grand,0x1e,parent);
    w32(actor,0x1e,list==0?target:sentinel);
    w32(sentinel,0x4c,target);
    if(list==0) w32(target,0xca,sentinel);
    if(list==1) w32(sentinel,0xca,target);
    if(list==2) w32(sentinel,0x1e,target);
    if(children) {
        w32(target,0x1e,child); w32(child,0xca,sibling);
        w32(child,0x44,target); w32(sibling,0x44,target);
    }
    int vertex=0x904000;
    w32(target,0x11e,vertex); w32(vertex,0x26,vertex+0x40);
    w32(actor,0xd8,0x905000);
    for(int i=0;i<4;i++) {
        int polygon=0x905000+i*0x40;
        w16(polygon,0,i); w32(polygon,0x22,actor);
        w32(polygon,0x1e,i<3?polygon+0x40:0);
        w32(0x903000,i*4,polygon);
        // Exercise all four vertex-reference slots, including an unreferenced face.
        if(polygons & (1<<i)) w32(polygon,i<3?4+i*4:0x28,vertex+(i&1)*0x40);
    }
    return target;
}
static uint32_t run_original(int node) {
    uint32_t result=node;
    __asm__ volatile("call *%%edi" : "+a"(result) : "D"(0x43ab74) : "memory","cc");
    return result;
}
int main(void) {
    map(0x430000,0x10000,1); map(0x453000,0x1000,1); map(0x900000,0x10000,0);
    memcpy((void*)0x43a8f8,code_43a8f8,sizeof code_43a8f8);
    memcpy((void*)0x43ab74,code_43ab74,sizeof code_43ab74);
    memcpy((void*)0x453264,code_453264,sizeof code_453264);
    memcpy((void*)0x453508,code_453508,sizeof code_453508);
    memcpy((void*)0x45366c,code_45366c,sizeof code_45366c);
    *(unsigned char*)0x43cac0=0xe9;
    *(int32_t*)0x43cac1=(intptr_t)original_message-0x43cac5;
    unsigned char before[0x10000],expected[0x10000];
    unsigned cases=0;
    for(int list=0;list<3;list++) for(int flags=0;flags<8;flags++)
    for(int children=0;children<2;children++) for(int polygons=0;polygons<16;polygons++) {
        int node=setup(list,flags,children,polygons);
        memcpy(before,(void*)0x900000,sizeof before);
        message=0; uint32_t eax=run_original(node), error=message;
        memcpy(expected,(void*)0x900000,sizeof expected);
        memcpy((void*)0x900000,before,sizeof before);
        message=0; uint32_t actual=FUN_0043ab74(node,0);
        if(actual!=eax || error!=message || memcmp(expected,(void*)0x900000,sizeof expected)) {
            fprintf(stderr,"FAIL case %u list=%d flags=%d children=%d polygons=%x return=%x/%x error=%x/%x\n",
                    cases,list,flags,children,polygons,eax,actual,error,message);
            for(int i=0;i<0x10000;i++) if(expected[i]!=*(unsigned char*)(0x900000+i)) {
                fprintf(stderr,"first byte mismatch %x: %x/%x\n",0x900000+i,expected[i],*(unsigned char*)(0x900000+i)); break;
            }
            return 1;
        }
        cases++;
    }
    message=0; uint32_t eax=run_original(0), error=message;
    message=0; assert((uint32_t)FUN_0043ab74(0,0)==eax && message==error);
    printf("PASS: %u original-x86 node/child/polygon unlink and mark cases, plus null/error routing\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-node-removal-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', *flags,
                    str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=20)
