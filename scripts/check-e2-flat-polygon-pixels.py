#!/usr/bin/env python3
"""Compare original high-resolution flat polygon pixels/depth/dirty rectangles.

Lighting indices are fixed in both implementations (their arithmetic has a
separate original-x86 fixture). Palette ownership and DirectDraw Lock/Unlock are
intercepted. Original column raster instructions execute, including pitch patch.
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
source = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
body = function(source, 'FUN_00431a7c')
harness = support() + r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint16_t ushort;typedef uint32_t uint,undefined4;
#define __fastcall
static int IsBadReadPtr(const void *p,int n){return !p;}
static void FUN_00457818(uint p,int mode){}
static void E2R_PolygonLightingIndices(int x,int y,int z,int *a,int *b){*a=64;*b=64;}
static int locked,unlocked;static uint pixel_pitch;
__attribute__((regparm(2),noinline,used)) static uint lock(uint surface,uint *pitch){
 assert(surface<3);*pitch=pixel_pitch;locked=surface+1;return 0x910000;
}
__attribute__((regparm(2),noinline,used)) static void unlock(uint surface,uint pixels){
 assert(surface<3 && pixels==0x910000);unlocked=surface+1;
}
static uint FUN_00418a04(uint surface,uint *pitch){return lock(surface,pitch);}
static void FUN_00418b00(uint surface,uint pixels){unlock(surface,pixels);}
__attribute__((naked)) static void lock_hook(void){__asm__("pushal; call lock; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void unlock_hook(void){__asm__("pushal; call unlock; popal; ret");}
__attribute__((naked)) static void lighting_hook(void){__asm__("mov $64,%ebx; mov $64,%eax; push $0x432007; ret");}
'''
for symbol in sorted(set(re.findall(r'\b_?DAT_[0-9a-f]{8}\b', body))):
    address = int(symbol[-8:], 16)
    harness += f'#define {symbol} (*(int*)0x{address:x})\n'
harness += body + '\n'
ranges = [(0x431a7c, 0x432bd7), (0x45d92a, 0x45d954)]
for start, end in ranges:
    harness += f'static const byte code_{start:x}[]={{' + ','.join(map(str, image.code(start, end))) + '};\n'
harness += r'''
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void hook(uint at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(uint)fn-at-5;}
static uint rng;
static uint next(void){rng=rng*1664525u+1013904223u;return rng;}
static void setup(int seed,int flags,int surface){
 rng=seed+0x431a7c;memset((void*)0x900000,0,0x1000);
 memset((void*)0x910000,0x5a,0x4d000);
 for(int i=0;i<640*480;i++)*(short*)(0x980000+i*2)=2000+next()%8000;
 pixel_pitch=640+(seed%3)*4;
 DAT_0047a43c=1;DAT_0047a3b4=seed&1;
 *(uint*)0x636668=*(uint*)0x63666c=0x980000;
 _DAT_00640114=240;_DAT_00640118=320;_DAT_006401ec=640;_DAT_006401d4=480;
 _DAT_00640120=480-seed%7;_DAT_00640124=seed%9;
 _DAT_0064012c=seed%11;_DAT_00640144=640-seed%5;
 *(ushort*)0x900002=flags;*(short*)0x900010=seed%4;*(short*)0x900012=(seed+1)%4;
 *(short*)0x900026=0x4000;*(uint*)0x900022=0x900400;*(uint*)0x9004e4=0x900600;
 *(short*)0x900600=*(short*)0x900604=0x7fff;
 *(short*)0x900602=*(short*)0x900606=-0x7fff;
 for(int i=0;i<3;i++){
  uint vertex=0x900100+i*0x40;*(uint*)(0x900004+4*i)=vertex;
  for(int j=0;j<3;j++)*(short*)(vertex+0x10+j*2)=(int)(next()%16000)-8000;
  *(short*)(vertex+0x16)=(int)(next()%14000)-7000;
  *(short*)(vertex+0x18)=(int)(next()%11000)-5500;
  *(short*)(vertex+0x1a)=3000+next()%4000;
 }
 /* Equal-X and zero-depth cases exercise original early-exit/edge splits. */
 if(seed%8==0)*(short*)0x900156=*(short*)0x900116;
 if(seed%13==0)*(short*)0x90019a=0;
 if(seed%17==0)*(short*)0x900196=*(short*)0x900156=*(short*)0x900116;
 locked=unlocked=0;
}
int main(void){
 map(0x410000,0x10000);map(0x430000,0x10000);map(0x450000,0x10000);
 map(0x470000,0x10000);map(0x500000,0x150000);map(0x900000,0x120000);
'''
for start, _ in ranges:
    harness += f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness += r'''
 *(byte*)0x457818=0xc3;hook(0x431f2d,lighting_hook);
 hook(0x418a04,lock_hook);hook(0x418b00,unlock_hook);
 for(int i=0;i<0x40000;i++)*(byte*)(0x507590+i)=(byte)(i*173+(i>>8)*13);
 memset((void*)0x61d030,64,0x4000);
 static byte expected[0x112000];int cases=0,drawn=0;
 for(int flags=0;flags<4;flags++)for(int seed=0;seed<256;seed++)for(int surface=0;surface<3;surface++){
  int bits=(flags&1?1:0)|(flags&2?16:0);
  uint reference=seed&1?0x900000:0;
  setup(seed,bits,surface);struct E2R_Registers regs={.eax=0x900000,.edx=surface,.ebx=reference};e2r_original_call(0x431a7c,&regs);
  memcpy(expected,(void*)0x900000,sizeof expected);int locks=locked,unlocks=unlocked;
  for(int i=0;i<640*480;i++)if(*(byte*)(0x910000+i)!=0x5a){drawn++;break;}
  setup(seed,bits,surface);FUN_00431a7c(0x900000,surface,reference);
  if(locked!=locks||unlocked!=unlocks||!e2r_memory_equal("flat polygon raster",expected,(void*)0x900000,sizeof expected)){
   fprintf(stderr,"flat polygon flags=%x seed=%d surface=%d lock=%d/%d unlock=%d/%d\n",bits,seed,surface,locked,locks,unlocked,unlocks);return 1;
  }
  cases++;
 }
 assert(drawn>100);printf("PASS: %d original-x86 flat polygon pixel/depth/rectangle/lock cases (%d draw pixels)\n",cases,drawn);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('Palette ownership intercepted', 'Lighting indices fixed at 64/64; separate arithmetic fixture',
                          'DirectDraw Lock/Unlock return fixture-owned pixels and variable pitch'))
