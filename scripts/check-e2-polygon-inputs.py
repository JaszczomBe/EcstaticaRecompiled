#!/usr/bin/env python3
"""Compare polygon routing against original i386 code, without rasterizing.

Requires E2WIN95.EXE, clang with -m32 support and Linux/i386 execution. Original
bytes are copied only into a temporary harness. Rendering leaves are intercepted
so this checks arguments, quad splitting/restoration and mode selection, not pixels.
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
parser.add_argument('--asan', action='store_true', help='Instrument recovered C and fixture storage')
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
count = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]


def original(start, end):
    for i in range(count):
        off = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, off + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(f'Unmapped code: {start:x}')


source = (Path(__file__).resolve().parent.parent /
          'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
functions = []
for name in ('FUN_00433d30', 'FUN_00424e44', 'FUN_00425018'):
    match = re.search(r'void (?:__fastcall )?' + name + r'\([^\n]*\)\s*\{.*?\n\}', source, re.S)
    if not match:
        raise ValueError(f'Missing function {name}')
    functions.append(match.group())

harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte, undefined1;
typedef uint64_t undefined8, ulonglong;
typedef uint16_t ushort, undefined2;
typedef uint32_t uint, undefined4;
#define __fastcall
#define DAT_0047a279 (*(uint32_t*)0x47a279)
#define DAT_0047a3e0 (*(uint32_t*)0x47a3e0)
#define DAT_0047a434 (*(uint32_t*)0x47a434)
static int IsBadReadPtr(const void *p, unsigned n) { return !p || !n; }
struct Call { int polygon, mode, reference, textured; unsigned char bytes[0x40]; };
static struct Call calls[12];
static int box_fixture;
static int count;
void record(int polygon, int mode, int reference, int textured) {
    if (count >= 12) abort();
    if (box_fixture) {
        /* Inspect stack-backed inputs while their lifetime is active. */
        if(reference != polygon-0x44 || mode!=1 || textured) abort();
        uintptr_t vertices=polygon-0x194;
        static uintptr_t previous[3];
        for(int i=0;i<3;i++) {
            uintptr_t point=*(uint32_t*)(polygon+4+4*i);
            uintptr_t plane=*(uint32_t*)(reference+4+4*i);
            if(point<vertices || point>=vertices+8*0x2a || (point-vertices)%0x2a) abort();
            if(plane != ((count&1)?previous[i]:point)) abort();
            previous[i]=point;
        }
        if(*(uint32_t*)(polygon+0x22)!=0x900100 ||
           *(short*)(polygon+0x10)!=5 || *(short*)(polygon+0x26)!=0x4000) abort();
    }
    struct Call *c = &calls[count++];
    c->polygon=polygon; c->mode=mode; c->reference=reference; c->textured=textured;
    memcpy(c->bytes,(void*)polygon,0x40);
}
void FUN_00431a7c(int p,int mode,int reference) { record(p,mode,reference,0); }
void FUN_00437ae4(int p,int mode,int reference) { record(p,mode,reference,1); }
/* Original register ABI preserves ECX, ESI, EDI and EBP; preserve all here. */
__attribute__((naked)) void flat(void) {
    __asm__("pushal; push $0; push %ebx; push %edx; push %eax; call record; add $16,%esp; popal; ret");
}
__attribute__((naked)) void textured(void) {
    __asm__("pushal; push $1; push %ebx; push %edx; push %eax; call record; add $16,%esp; popal; ret");
}
__attribute__((noinline)) void run_original(int polygon) {
    __asm__ volatile("pushal; mov %%esi,%%eax; call *%%edi; popal"
                     : : "S"(polygon), "D"(0x424e44) : "memory", "cc");
}
static void map(uintptr_t p, unsigned size, int exec) {
    if(mmap((void*)p,size,PROT_READ|PROT_WRITE|(exec?PROT_EXEC:0),
            MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==MAP_FAILED) {
        perror("mmap"); exit(2);
    }
}
static void hook(uintptr_t at, void (*fn)(void)) {
    *(byte*)at=0xe9;
    *(int32_t*)(at+1)=(intptr_t)fn-at-5;
}
'''
# The temporary-polygon fixture supplies valid original face-index tables and
# intercepts projection/rendering. It proves record layout/lifetime, not geometry.
box_globals = ('DAT_0047a2b4 DAT_0047a2b8 DAT_0047a2e4 DAT_0047a2e8 '
               'DAT_0047a314 DAT_0047a318 DAT_0047a34a DAT_0047a34c '
               'DAT_0047a366 DAT_0047a37c').split()
for name in box_globals:
    harness += f'#define {name} (*(uint32_t*)0x{name[-8:]})\n'
harness += r'''
static int _DAT_00636588, _DAT_006401c8, _DAT_006401cc, _DAT_006401d4,
           _DAT_006401ec, _DAT_006401fc, _DAT_0064020c, sRam0047a380;
#define CONCAT22(a,b) (((uint32_t)(uint16_t)(a)<<16)|(uint16_t)(b))
#define E2R_READ2(p,off) (*(uint16_t*)((uintptr_t)(p)+(off)))
void FUN_0045de8b(void) {} /* Existing unrecovered transform remains a stub. */
void FUN_00422fd8(uint32_t out,int in) { memset((void*)out,0,6); }
undefined8 FUN_004525f0(void *unused,int texture) { abort(); }
void FUN_00433e9c(int texture,int mode) { abort(); }
'''
data = original(0x47a2b8, 0x47a348)
harness += 'const unsigned char face_indices[]={' + ','.join(map(str, data)) + '};\n'
for i, (start, end) in enumerate(((0x424e44, 0x424e96), (0x433d30, 0x433e9b))):
    data = original(start, end)
    harness += f'const unsigned char original_{i}[]={{' + ','.join(map(str, data)) + '};\n'
harness += '\n'.join(functions)
harness += r'''
int main(void) {
    unsetenv("E2R_PROXY_MESH_BYPASS");
    map(0x420000,0x20000,1); map(0x47a000,0x1000,0); map(0x900000,0x1000,0);
    memcpy((void*)0x424e44,original_0,sizeof original_0);
    memcpy((void*)0x433d30,original_1,sizeof original_1);
    hook(0x431a7c,flat); hook(0x437ae4,textured);
    byte *p=(byte*)0x900000, *owner=(byte*)0x900100;
    uint32_t *table=(uint32_t*)0x900200;
    table[0]=0x900300; table[1]=0x900340;
    *(uint32_t*)(owner+0xdc)=(uintptr_t)table;
    unsigned cases=0;
    for(int ref=-1;ref<2;ref++) for(int quad=0;quad<2;quad++)
    for(int texture=0;texture<2;texture++) for(int disable=0;disable<3;disable++)
    for(int special=0;special<2;special++) for(int high=0;high<2;high++)
    for(int flags=0;flags<4;flags++) {
        memset(p,0,0x40);
        *(ushort*)(p+2)=0x41 | (flags<<8);
        *(uint32_t*)(p+4)=0x900400; *(uint32_t*)(p+8)=0x900440;
        *(uint32_t*)(p+0xc)=0x900480; *(short*)(p+0x1c)=ref;
        *(uint32_t*)(p+0x22)=(uintptr_t)owner;
        *(uint32_t*)(p+0x28)=quad?0x9004c0:0;
        *(short*)(p+0x2c)=texture?7:-1;
        for(int i=0;i<8;i++) *(short*)(p + 0x2e + 2*i)=31+i;
        owner[3]=special?4:0;
        DAT_0047a279=high<<24; DAT_0047a3e0=disable==1; DAT_0047a434=disable==2;
        byte before[0x40]; memcpy(before,p,sizeof before);
        count=0; run_original((int)p);
        struct Call expected[12]; memcpy(expected,calls,sizeof expected);
        int expected_count=count;
        if(memcmp(before,p,sizeof before)) { puts("Original did not restore polygon"); return 1; }
        count=0; memset(calls,0,sizeof calls);
        FUN_00424e44(0,(int)p);
        if(count!=expected_count || memcmp(calls,expected,count*sizeof calls[0]) ||
           memcmp(before,p,sizeof before)) {
            fprintf(stderr,"counts: original=%d recovered=%d; restored=%d\n",expected_count,count,!memcmp(before,p,sizeof before));
            for(int k=0;k<count && k<expected_count;k++) {
                fprintf(stderr,"call %d original=%x,%d,%x,%d recovered=%x,%d,%x,%d\n",k,
                    expected[k].polygon,expected[k].mode,expected[k].reference,expected[k].textured,
                    calls[k].polygon,calls[k].mode,calls[k].reference,calls[k].textured);
                for(int b=0;b<0x40;b++) if(expected[k].bytes[b]!=calls[k].bytes[b])
                    fprintf(stderr,"byte %x original=%x recovered=%x\n",b,expected[k].bytes[b],calls[k].bytes[b]);
            }
            fprintf(stderr,"FAIL case %u: ref=%d quad=%d texture=%d disable=%d special=%d high=%d flags=%d\n",
                    cases,ref,quad,texture,disable,special,high,flags); return 1;
        }
        cases++;
    }
    byte polygon_before[0x40]; memcpy(polygon_before,p,sizeof polygon_before);
    setenv("E2R_PROXY_MESH_BYPASS","1",1);
    count=0; FUN_00424e44(0,(int)p);
    if(count || memcmp(polygon_before,p,sizeof polygon_before)) abort();
    unsetenv("E2R_PROXY_MESH_BYPASS");
    puts("PASS: opt-in polygon bypass omits raster dispatch without changing the polygon");
    memcpy((void*)0x47a2b8,face_indices,sizeof face_indices);
    byte *box=(byte*)0x900500;
    *(uint32_t*)(box+0x22)=(uintptr_t)owner;
    *(short*)(box+0x68)=100; *(short*)(box+0x6a)=200; *(short*)(box+0x6c)=300;
    *(short*)(box+0xce)=5; *(short*)(box+0xd0)=0x4000; *(short*)(box+0x156)=-1;
    owner[3]=0; DAT_0047a279=0;
    count=0; box_fixture=1; FUN_00425018((int)box);
    if(count!=12) abort();
    puts("PASS: 12 temporary polygon records with live vertex/reference storage (projection intercepted)");
    printf("PASS: %u original-x86 polygon argument, mode, quad-split and restoration cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-polygon-inputs-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', *flags,
                    str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
