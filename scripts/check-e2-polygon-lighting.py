#!/usr/bin/env python3
"""Compare the bounded flat-polygon lighting recovery with original i386 code.

Requires original E2WIN95.EXE, clang -m32 and Linux/i386 execution. Original
angle-table initialization, angle lookup, rotation and lighting instructions run
in a temporary harness. This verifies arithmetic/indices, not rasterization.
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
sections = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]


def original(start, end):
    for i in range(sections):
        off = header + 24 + optional + 40 * i
        _, va, size, raw = struct.unpack_from('<IIII', pe, off + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(f'Unmapped original range {start:x}..{end:x}')


source = (Path(__file__).resolve().parent.parent /
          'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
functions = []
for name in ('E2R_TransformVector14', 'E2R_PolygonAngle16',
             'E2R_RotatePolygonNormal', 'E2R_PolygonLightingIndices'):
    match = re.search(r'(?:static )?(?:void|short) ' + name + r'\([^\n]*\)\s*\{.*?\n\}', source, re.S)
    if not match:
        raise ValueError(f'Missing recovered function {name}')
    functions.append(match.group())

harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
typedef uint8_t byte;
typedef uint16_t ushort;
typedef uint32_t uint;
static void map(uintptr_t address, unsigned size) {
    if(mmap((void*)address,size,PROT_READ|PROT_WRITE|PROT_EXEC,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==MAP_FAILED) {
        perror("mmap original image"); exit(2);
    }
}
static void jump(uintptr_t at,void (*target)(void)) {
    *(byte*)at=0xe9; *(int32_t*)(at+1)=(intptr_t)target-at-5;
}
/* Fragments use their original stack offsets; tail hooks return through these
 * adapters. The complete original callees retain their register conventions. */
void table_done(void), lighting_done(void);
__attribute__((naked)) void original_table_entry(int i) {
    __asm__("push %ebp; push %ebx; push %esi; push %edi;"
            "mov 20(%esp),%eax; sub $0x38,%esp; mov %eax,0x20(%esp); fninit;"
            "mov $0x414f5d,%eax; jmp *%eax;"
            ".global table_done; table_done: fninit; add $0x38,%esp;"
            "pop %edi; pop %esi; pop %ebx; pop %ebp; ret");
}
__attribute__((naked)) void original_indices(const short *normal,int *out) {
    __asm__("push %ebp; push %ebx; push %esi; push %edi;"
            "mov 20(%esp),%esi; mov 24(%esp),%edi; sub $0x108,%esp;"
            "movswl (%esi),%ebx; movswl 2(%esi),%ecx; movswl 4(%esi),%eax;"
            "mov $0x431f2d,%edx; jmp *%edx;"
            ".global lighting_done; lighting_done: mov %ebx,(%edi); mov %eax,4(%edi);"
            "add $0x108,%esp; pop %edi; pop %esi; pop %ebx; pop %ebp; ret");
}
__attribute__((noinline)) short original_angle(short x,short z) {
    int result=x, denominator=z;
    __asm__ volatile("call *%%esi" : "+a"(result),"+d"(denominator) : "S"(0x432c64) : "cc","memory");
    return (short)result;
}
__attribute__((naked)) void original_rotate(short *normal,short angle,int axis) {
    __asm__("push %ebp; push %ebx; push %esi; push %edi;"
            "mov 20(%esp),%eax; mov 24(%esp),%edx; cmpl $0,28(%esp);"
            "jne 1f; mov $0x422674,%esi; jmp 2f;"
            "1: mov $0x4226bc,%esi; 2: call *%esi;"
            "pop %edi; pop %esi; pop %ebx; pop %ebp; ret");
}
static uint32_t rng=0x432c64;
static uint32_t next(void) { rng=rng*1664525u+1013904223u; return rng; }
'''
harness += '\n'.join(functions)
ranges = [(0x414f5d, 0x414fde), (0x422330, 0x422366),
          (0x422674, 0x422703), (0x4228b8, 0x422a47),
          (0x431f2d, 0x432007), (0x432c64, 0x432de4),
          (0x45dd04, 0x45df0e), (0x45f556, 0x45f573),
          (0x471339, 0x4713b9)]
for i, (start, end) in enumerate(ranges):
    harness += f'\nconst byte code_{i}[]={{' + ','.join(map(str, original(start, end))) + '};\n'
harness += 'int main(void) {\nmap(0x410000,0x220000);\n'
for i, (start, _) in enumerate(ranges):
    harness += f'memcpy((void*)0x{start:x},code_{i},sizeof(code_{i}));\n'
harness += r'''
    jump(0x414fde,table_done); jump(0x432007,lighting_done);
    for(int i=0;i<256;i++) original_table_entry(i);
    for(int i=0;i<65536;i++) {
        double phase=i*6.28318/65536.0;
        *(short*)(0x59b590+2*i)=(short)(sin(phase)*16384.5);
        *(short*)(0x5de590+2*i)=(short)(cos(phase)*16384.5);
    }
    unsigned angle_cases=0, normal_cases=0;
    /* Every reachable fine/coarse entry and threshold, in all quadrants. */
    for(int scale=4;scale<=64;scale*=16) for(int i=0;i<256;i++)
    for(int sx=-1;sx<=1;sx+=2) for(int sz=-1;sz<=1;sz+=2) {
        short x=sx*i*scale, z=sz*256;
        if(E2R_PolygonAngle16(x,z)!=original_angle(x,z)) {
            fprintf(stderr,"FAIL lookup x=%d z=%d\n",x,z); return 1;
        }
        angle_cases++;
    }
    for(int trial=0;trial<8192;trial++) {
        short n[3], a[3], b[3];
        for(int k=0;k<3;k++) n[k]=(short)((int)(next()%32769)-16384);
        if(trial<27) {
            int t=trial;
            for(int k=0;k<3;k++) { n[k]=(t%3-1)*16384; t/=3; }
        }
        short angle=(short)next();
        for(int axis=0;axis<2;axis++) {
            memcpy(a,n,6); memcpy(b,n,6);
            E2R_RotatePolygonNormal(a,angle,axis); original_rotate(b,angle,axis);
            if(memcmp(a,b,6)) {
                fprintf(stderr,"FAIL rotation trial=%d axis=%d angle=%d\n",trial,axis,angle); return 1;
            }
        }
        short lookup=E2R_PolygonAngle16(n[0],n[2]);
        if(lookup!=original_angle(n[0],n[2])) {
            fprintf(stderr,"FAIL angle x=%d z=%d\n",n[0],n[2]); return 1;
        }
        angle_cases++;
        int got[2],expected[2];
        E2R_PolygonLightingIndices(n[0],n[1],n[2],&got[0],&got[1]);
        original_indices(n,expected);
        if(memcmp(got,expected,sizeof got)) {
            fprintf(stderr,"FAIL indices trial=%d normal=%d,%d,%d recovered=%d,%d original=%d,%d\n",
                    trial,n[0],n[1],n[2],got[0],got[1],expected[0],expected[1]); return 1;
        }
        normal_cases++;
    }
    puts("PASS: original x87 atan-table initializer used as lookup reference");
    printf("PASS: %u angle cases, %u axis rotations and %u flat-polygon lighting-index cases\n",
           angle_cases,normal_cases*2,normal_cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-polygon-lighting-') as tmp:
    c = Path(tmp) / 'lighting.c'
    exe = Path(tmp) / 'lighting'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', *flags,
                    str(c), '-lm', '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
