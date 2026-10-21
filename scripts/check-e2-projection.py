#!/usr/bin/env python3
"""Compare camera arithmetic and event metadata against E2WIN95 i386 routines.

Requires the original executable, a compiler with -m32 support, and Linux/i386
execution. All generated harness files live in a temporary directory. No game
assets or executable bytes are checked into the repository.
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
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
count = struct.unpack_from('<H', pe, header + 6)[0]
optional_size = struct.unpack_from('<H', pe, header + 20)[0]
sections = []
for i in range(count):
    offset = header + 24 + optional_size + i * 40
    _, va, size, raw = struct.unpack_from('<IIII', pe, offset + 8)
    sections.append((va + 0x400000, size, raw))


def original(start, end):
    for address, size, raw in sections:
        if address <= start < end <= address + size:
            return pe[raw + start - address:raw + end - address]
    raise ValueError(f'Unmapped original routine {start:x}')


source = (root / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
routines = ['FUN_00422368', 'FUN_00422460', 'FUN_00422538',
            'E2R_TransformVector14', 'E2R_Perspective14']
functions = []
for name in routines:
    match = re.search(r'void (?:__fastcall )?' + name + r'\([^\n]*\)\s*\{.*?\n\}', source, re.S)
    if not match:
        raise ValueError(f'Missing recovered routine: {name}')
    functions.append(match.group())

harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
typedef unsigned int uint;
typedef uintptr_t undefined4;
#define __fastcall
/* Harness buffers are allocated here, not supplied by a game caller. */
static int E2R_IsBadWritePtr(const void *p, unsigned n) { return !p || !n; }
'''
harness += '\n'.join(functions)
metadata = re.search(r'static const ushort metadata\[\] = \{(.*?)\};', source, re.S)
if not metadata:
    raise ValueError('Missing recovered event metadata')
harness += '\nstatic const unsigned short metadata[] = {' + metadata.group(1) + '};\n'
for i, (start, end) in enumerate([(0x422368, 0x42245d), (0x422460, 0x422538),
                                 (0x422538, 0x422628), (0x45de8b, 0x45df0e),
                                 (0x423070, 0x423126), (0x416cb4, 0x4171b8)]):
    data = original(start, end)
    harness += f'\nstatic const unsigned char original_{i}[] = {{{",".join(map(str,data))}}};\n'
harness += r'''
static void *code(const void *data, size_t n) {
    void *p=mmap(NULL,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(p==MAP_FAILED) { perror("mmap code"); exit(2); }
    memcpy(p,data,n);
    if(mprotect(p,4096,PROT_READ|PROT_EXEC)) { perror("mprotect"); exit(2); }
    return p;
}
static void rotation(void *fn, short *m, uint angle) {
    __asm__ volatile("call *%%ecx" : "+a"(m), "+d"(angle) : "c"(fn) : "memory","cc");
}
static void vector(void *fn, short *out, short *in, short *m) {
    __asm__ volatile("call *%%eax" : "+a"(fn) : "b"(in),"S"(m),"D"(out) : "ecx","edx","memory","cc");
}
static void perspective(void *fn, short *p) {
    __asm__ volatile("call *%%ecx" : "+a"(p) : "c"(fn) : "memory","cc");
}
static uint32_t seed=0xE2;
static uint32_t next(void) { seed=seed*1664525u+1013904223u; return seed; }
static void equal(const char *name,int iteration,const short *a,const short *b,int n) {
    if(memcmp(a,b,n*2)) {
        fprintf(stderr,"%s mismatch, case %d\n",name,iteration);
        for(int i=0;i<n;i++) fprintf(stderr," %d:%d",a[i],b[i]);
        fputc('\n',stderr); exit(1);
    }
}
int main(void) {
    /* The original routines contain these absolute data addresses. */
    void *data=mmap((void*)0x470000,0x190000,PROT_READ|PROT_WRITE,
                   MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    if(data==MAP_FAILED) { perror("mmap original data"); return 2; }
    for(int i=0;i<65536;i++) {
        double phase=i*6.28318/65536.0;
        *(short*)(0x59b590+i*2)=(short)(sin(phase)*16384.5);
        *(short*)(0x5de590+i*2)=(short)(cos(phase)*16384.5);
    }
    void *originals[]={code(original_0,sizeof(original_0)),code(original_1,sizeof(original_1)),
                      code(original_2,sizeof(original_2)),code(original_3,sizeof(original_3)),
                      code(original_4,sizeof(original_4))};
    void (*recovered[])(undefined4,uint)={FUN_00422368,FUN_00422460,FUN_00422538};
    for(int trial=0;trial<4096;trial++) {
        short m[9], a[9], b[9], in[3];
        for(int i=0;i<9;i++) m[i]=(short)((int)(next()%32769)-16384);
        for(int axis=0;axis<3;axis++) {
            memcpy(a,m,sizeof(m));memcpy(b,m,sizeof(m));uint angle=next()&65535;
            recovered[axis]((uintptr_t)a,angle);rotation(originals[axis],b,angle);
            equal("rotation",trial,a,b,9);
        }
        for(int i=0;i<3;i++) in[i]=(short)next();
        E2R_TransformVector14(a,in,m);vector(originals[3],b,in,m);
        equal("transform",trial,a,b,3);
        /* In-place operation must retain the original input vector. */
        memcpy(a,in,6);E2R_TransformVector14(a,a,m);equal("in-place transform",trial,a,b,3);
        in[2]=(short)(128+next()%32640);
        memcpy(a,in,6);memcpy(b,in,6);
        int focal=(1+next()%32767)*4096, hires=trial&1;
        *(int*)0x47a2a4=focal;*(int*)0x47a43c=hires;
        E2R_Perspective14(a,focal,hires);perspective(originals[4],b);
        /* Original preserves partially written X when Y overflows; invalid
         * projected coordinates have no meaning when depth is zero. */
        if(a[2] || b[2]) equal("perspective",trial,a,b,3);

    }
    data=mmap((void*)0x636000,4096,PROT_READ|PROT_WRITE,
              MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    if(data==MAP_FAILED) { perror("mmap event metadata"); return 2; }
    void (*init)(void)=code(original_5,sizeof(original_5));
    init();
    equal("event metadata",0,(const short*)metadata,(const short*)0x636700,sizeof(metadata)/2);
    puts("PASS: 4096 original-x86 math cases, in-place transform, and original event metadata initializer");
}
'''
with tempfile.TemporaryDirectory(prefix='e2-projection-test-') as tmp:
    c = Path(tmp) / 'projection.c'
    exe = Path(tmp) / 'projection'
    c.write_text(harness)
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', str(c), '-lm', '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
