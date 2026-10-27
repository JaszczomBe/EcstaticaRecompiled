#!/usr/bin/env python3
"""Compare original high-resolution ellipsoid pixels, depth and dirty rectangles.

The original self-modifying column drawers execute with the original shade map.
Only DirectDraw Lock/Unlock are intercepted with bounded fixture-owned surfaces.
"""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
image = OriginalImage(args.exe)
source = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
shade_map = args.exe.parent / 'SHADEMAP.DAT'
shape = shade_map.read_bytes()
assert len(shape) == 0xc000
harness = support() + r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint16_t ushort;typedef uint32_t uint,undefined4;
#define __fastcall
#define DAT_0047a2a4 (*(int*)0x47a2a4)
#define DAT_0047a3b4 (*(int*)0x47a3b4)
#define _DAT_00636668 (*(uint*)0x636668)
#define _DAT_0063666c (*(uint*)0x63666c)
#define _DAT_00640114 (*(int*)0x640114)
#define _DAT_00640118 (*(int*)0x640118)
#define _DAT_00640120 (*(int*)0x640120)
#define _DAT_00640124 (*(int*)0x640124)
#define _DAT_0064012c (*(int*)0x64012c)
#define _DAT_00640144 (*(int*)0x640144)
static int locked,unlocked;static uint pixel_pitch;
__attribute__((regparm(2),noinline,used)) static uint lock(uint surface,uint *pitch){
 assert(surface<3);*pitch=pixel_pitch;locked=surface+1;return 0x910000;
}
__attribute__((regparm(2),noinline,used)) static void unlock(uint surface,uint pixels){
 assert(pixels==0x910000);unlocked=surface+1;
}
static uint FUN_00418a04(uint surface,uint *pitch){return lock(surface,pitch);}
static void FUN_00418b00(uint surface,uint pixels){unlock(surface,pixels);}
__attribute__((naked)) static void lock_hook(void){__asm__("pushal; call lock; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void unlock_hook(void){__asm__("pushal; call unlock; popal; ret");}
'''
harness += function(source, 'FUN_00430fd8') + '\n'
ranges = [(0x430fd8, 0x431776), (0x45d10e, 0x45d17e),
          (0x45d2cc, 0x45d35c), (0x45d482, 0x45d4fc), (0x45d5f8, 0x45d65b)]
for start, end in ranges:
    harness += f'static const byte code_{start:x}[]={{' + ','.join(map(str, image.code(start, end))) + '};\n'
harness += 'static const byte shape[]={'+','.join(map(str, shape))+'};\n'
harness += r'''
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void hook(uint at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(uint)fn-at-5;}
static uint rng=0x430fd8;
static uint next(void){rng=rng*1664525u+1013904223u;return rng;}
static void setup(int seed,int flags,int surface){
 rng=seed+0x430fd8;memset((void*)0x900000,0,0x1000);
 memset((void*)0x910000,0x5a,0x4d000);memset((void*)0x960000,0xa5,0x1000);
 for(int i=0;i<640*480;i++)*(short*)(0x980000+i*2)=1000+next()%8000;
 pixel_pitch=640+(seed%3)*4;
 DAT_0047a2a4=0x180000;DAT_0047a3b4=seed&1;
 _DAT_00636668=_DAT_0063666c=0x980000;
 _DAT_00640114=240;_DAT_00640118=320;
 _DAT_00640120=480-(seed%7);_DAT_00640124=seed%9;
 _DAT_0064012c=seed%11;_DAT_00640144=640-seed%5;
 *(short*)0x900096=seed%31?1024+next()%6000:0;
 *(short*)0x900092=(int)(next()%14000)-7000;
 *(short*)0x900094=(int)(next()%11000)-5500;
 *(short*)0x9000da=10+next()%1400;
 *(short*)0x9000dc=10+next()%1400;
 *(short*)0x9000de=(int)(next()%1000)-500;
 *(short*)0x900122=(int)(next()%100)-50;
 *(short*)0x900124=(int)(next()%100)-50;
 *(short*)0x900126=10+next()%500;
 *(short*)0x9000ce=seed%4;*(short*)0x9000d0=0x4000;
 *(byte*)0x900002=flags;*(uint*)0x900022=0x900400;
 *(uint*)0x9004e4=0x900600;
 *(short*)0x900600=*(short*)0x900604=0x7fff;
 *(short*)0x900602=*(short*)0x900606=-0x7fff;
 locked=unlocked=0;
}
int main(void){
 map(0x430000,0x10000);map(0x450000,0x10000);map(0x470000,0x10000);
 map(0x500000,0x150000);map(0x900000,0x120000);
'''
for start, _ in ranges:
    harness += f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness += r'''
 hook(0x418a04,lock_hook);hook(0x418b00,unlock_hook);
 for(int i=0;i<0xc000;i++)*(byte*)(0x507590+i)=(byte)(i*173+(i>>8)*13);
 for(int i=0;i<0x4000;i++){
  *(byte*)(0x61d030+i)=shape[i*3];
  *(short*)(0x621630+i*2)=(shape[i*3+1]<<8)|shape[i*3+2];
 }
 for(int i=0;i<0x3000;i++)*(byte*)(0x5bb590+i)=i*31+(i>>8)*17;
 static byte expected[0x112000];int cases=0,drawn=0;
 for(int flags=0;flags<4;flags++)for(int seed=0;seed<256;seed++)for(int surface=0;surface<3;surface++){
  int bits=(flags&1?2:0)|(flags&2?0x40:0);
  setup(seed,bits,surface);struct E2R_Registers regs={.eax=0x900000,.edx=surface};e2r_original_call(0x430fd8,&regs);
  memcpy(expected,(void*)0x900000,sizeof expected);int locks=locked,unlocks=unlocked;
  for(int i=0;i<640*480;i++)if(*(byte*)(0x910000+i)!=0x5a){drawn++;break;}
  setup(seed,bits,surface);FUN_00430fd8(0x900000,surface);
  if(locked!=locks||unlocked!=unlocks||!e2r_memory_equal("ellipsoid raster",expected,(void*)0x900000,sizeof expected)){
   fprintf(stderr,"ellipsoid raster flags=%x seed=%d surface=%d lock=%d/%d unlock=%d/%d\n",bits,seed,surface,locked,locks,unlocked,unlocks);return 1;
  }
  cases++;
 }
 assert(drawn>100);printf("PASS: %d original-x86 ellipsoid pixel/depth/rectangle/lock cases (%d draw pixels)\n",cases,drawn);
}
'''
# Original Lock/Unlock code is intercepted at its own fixed addresses.
harness = harness.replace('map(0x430000,0x10000);', 'map(0x410000,0x10000);map(0x430000,0x10000);')
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('DirectDraw Lock/Unlock return fixture-owned pixels and pitch',))
