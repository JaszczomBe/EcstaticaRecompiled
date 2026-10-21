#!/usr/bin/env python3
"""Compare node hit-query filtering and direct contact effects with original i386.

Actor records use the reported stable coordinates and synthetic nearby candidates.
The original polar/angle instructions run directly. Sound, scripted contacts and
weapon-charge callbacks remain outside this bounded comparison.
"""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
source = (Path(__file__).resolve().parent.parent /
          'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
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
    raise ValueError(hex(start))


def function(name):
    match = re.search(r'^(?:static )?(?:void|short) ' + name +
                      r'\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
    assert match, name
    return match.group()


harness = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte,bool;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;
#define true 1
#define false 0
#define _DAT_0063726c (*(ushort **)0x63726c)
#define DAT_0047a470 (*(ushort **)0x47a470)
#define DAT_0047a4a0 (*(int *)0x47a4a0)
#define DAT_00479dd0 (*(int *)0x479dd0)
#define DAT_00670c48 (*(byte *)0x670c48)
#define DAT_0047a44c (*(int *)0x47a44c)
#define DAT_0047a4a4 (*(int *)0x47a4a4)
#define DAT_0047ab28 (*(int *)0x47ab28)
#define CONCAT22(a,b) (((uint)(ushort)(a)<<16)|(ushort)(b))
static int hud_calls;
static undefined8 FUN_0045fc10(int a,int b) { assert(0);return 0; }
static void FUN_0042fce0(int a,int b,int c,int d,int e) { assert(0); }
static void FUN_00456924(int a,int b) { assert(0); }
static undefined8 FUN_00442128(int a,int b) { assert(0);return 0; }
static void FUN_00441890(int a,int b) { assert(0); }
static void FUN_0043cbd0(int a) { assert(0); }
static void FUN_0044f32c(ushort *a,ushort *b,ushort *c) { assert(0); }
__attribute__((used,noinline)) static void FUN_00456a3c(void) { hud_calls++; }
__attribute__((naked)) static void hud_hook(void) {
 __asm__("pushal; call FUN_00456a3c; popal; ret");
}
'''
for name in ('E2R_PolygonAngle16', 'E2R_NpcPolar16', 'FUN_0042efdc'):
    harness += function(name) + '\n'
for start, end in ((0x42efdc, 0x42f49c), (0x427160, 0x427214), (0x432c64, 0x432de4)):
    harness += f'static const byte code_{start:x}[]={{' + ','.join(map(str, original(start, end))) + '};\n'
harness += r'''
static void map(int at,int size) {
 assert(mmap((void *)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void hook(int at,void *fn) { *(byte *)at=0xe9;*(int *)(at+1)=(int)fn-at-5; }
static void run_original(int node) {
 __asm__ volatile("call *%%edi" : "+a"(node) : "D"(0x42efdc) : "ecx","edx","memory","cc");
}
static uint rng;
static uint next(void) { rng=rng*1664525+1013904223;return rng; }
static void setup(int seed,int kind) {
 memset((void *)0x900000,0,0x10000);
 rng=seed;
 // The screenshot places Joe at 2986,4096,-6646 in camera 177.
 int node=0x902000,owner=0x901000,linked=0x901200;
 *(int *)(node+0x22)=owner;
 *(short *)owner=106;*(short *)linked=117;
 *(short *)(owner+0x138)=*(short *)(linked+0x138)=-1;
 *(short *)(owner+0x182)=40+seed%160;
 *(short *)(linked+0x182)=30+seed%80;
 *(int *)(owner+0x54)=0x903000;
 if(seed&1) { *(int *)(owner+0xf2)=0x902400;*(int *)0x902422=linked; }
 *(short *)(owner+0x18a)=seed%7==0?1:-1;
 *(short *)(owner+0x84)=2800;*(short *)(owner+0x86)=4096;*(short *)(owner+0x88)=-6800;
 *(short *)(node+0x18)=2986;*(short *)(node+0x1a)=4096;*(short *)(node+0x1c)=-6646;
 _DAT_0063726c=(ushort *)0x900000;
 DAT_0047a470=(ushort *)0x900000;
 DAT_00670c48=seed&2;
 DAT_0047a44c=(seed/4)%2;
 DAT_0047a4a4=(seed/8)%3;
 DAT_0047ab28=50+seed%151;
 DAT_0047a4a0=DAT_00479dd0=0;
 for(int j=0;j<5;j++) {
  int actor=0x900000+j*0x200,rep=0x904000+j*0x100;
  *(short *)actor=j;
  *(int *)(actor+0x4c)=j<4?actor+0x200:0;
  *(short *)(actor+0x84)=2986+(int)(next()%2401)-1200;
  *(short *)(actor+0x86)=4096+(int)(next()%3401)-700;
  *(short *)(actor+0x88)=-6646+(int)(next()%2401)-1200;
  *(short *)(actor+0x9a)=400+next()%800;
  *(int *)(actor+0x11e)=rep;
  *(short *)(rep+8)=seed%5?-1:1;
  *(short *)(rep+0x46)=1;
  *(short *)(actor+0x136)=-1;
  *(short *)(actor+0xec)=300;
 }
 int actor=0x900000,rep=0x904000;
 // Isolate rejection boundaries and accepted direct contacts on the first actor.
 *(short *)(actor+0x84)=2986;
 *(short *)(actor+0x86)=4096;
 *(short *)(actor+0x88)=-6646;
 switch(kind) {
  case 0: break; // coincident XZ, accepted
  case 1: *(int *)(actor+0x11e)=0;break;
  case 2: *(short *)(rep+0x46)=-1;break;
  case 3: *(int *)(actor+0xf2)=0x902600;*(int *)0x902622=owner;break;
  case 4: *(short *)(owner+0x18a)=0;break;
  case 5: *(short *)(actor+0x9a)=0;break; // equality rejects (zero radius)
  case 6: *(short *)(actor+0x86)=4096+0xa00;break;
  case 7: *(short *)(actor+0x86)=4096-0x200;break;
  case 8: *(short *)(actor+0x86)=4096+0xa00-1;break;
  case 9: *(short *)(actor+0x86)=4096-0x200+1;break;
  case 10: *(short *)(actor+0x82)=5;break;
  case 11: *(short *)(actor+0x82)=11;break;
  case 12: *(byte *)(actor+3)=0x20;break;
  case 13: *(int *)(actor+0x132)=0x905000;break;
  case 14: *(int *)(actor+0xa6)=0x905000;*(byte *)(actor+0xb2)=0x80;break;
  case 15: *(short *)(actor+0x84)=2986+1200;*(short *)(actor+0x9a)=1200;break;
 }
 hud_calls=0;
}
int main(void) {
 map(0x420000,0x20000);map(0x450000,0x20000);map(0x470000,0x10000);
 map(0x590000,0x80000);map(0x620000,0x20000);map(0x670000,0x10000);map(0x900000,0x10000);
'''
for start in (0x42efdc, 0x427160, 0x432c64):
    harness += f'memcpy((void *)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness += r'''
 hook(0x456a3c,hud_hook);
 for(int i=0;i<65536;i++) {
  double phase=i*6.28318/65536.0;
  *(short *)(0x59b590+i*2)=sin(phase)*16384.5;
  *(short *)(0x5de590+i*2)=cos(phase)*16384.5;
 }
 for(int i=0;i<256;i++) {
  *(byte *)(0x5fe990+i)=atan(i*0.015625)*64.0*2.0*0.3183101550488765+0.5;
  *(byte *)(0x5fe890+i)=atan(i*0.25)*64.0*2.0*0.3183101550488765+0.5;
 }
 static byte expected[0x10000];int contacts=0;
 for(int kind=0;kind<16;kind++)for(int seed=0;seed<1024;seed++) {
  setup(seed,kind);run_original(0x902000);
  int expected_hud=hud_calls;
  for(int j=0;j<5;j++)contacts+=*(short *)(0x900166+j*0x200)==1;
  memcpy(expected,(void *)0x900000,sizeof expected);
  setup(seed,kind);FUN_0042efdc(0x902000);
  if(expected_hud!=hud_calls || memcmp(expected,(void *)0x900000,sizeof expected)) {
   fprintf(stderr,"hit-query mismatch seed=%d kind=%d hud=%d/%d\n",seed,kind,expected_hud,hud_calls);
   for(int i=0;i<sizeof expected;i++)if(expected[i]!=*(byte *)(0x900000+i)) {
    fprintf(stderr,"offset=%x original=%02x recovered=%02x\n",i,expected[i],*(byte *)(0x900000+i));break;
   }
   abort();
  }
 }
 assert(contacts>1000);
 printf("PASS: 16384 original node hit-query/filter/contact cases, %d contacts; mapped actor memory and player HUD handoffs match\n",contacts);
}
'''
if args.keep_harness:
    args.keep_harness.write_text(harness)
with tempfile.TemporaryDirectory(prefix='e2-node-hit-query-') as tmp:
    src, exe = Path(tmp) / 'check.c', Path(tmp) / 'check'
    src.write_text(harness)
    subprocess.run(['clang-21', '-m32', '-O1', '-Wno-int-conversion', '-fno-pie', '-no-pie',
                    *(['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []),
                    str(src), '-lm', '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=30)
