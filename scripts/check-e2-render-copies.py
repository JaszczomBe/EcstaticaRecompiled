#!/usr/bin/env python3
"""Compare explicit background/redraw pixel and depth copies with original x86.

Cursor leaves are intercepted with the cursor hidden; original copy loops and
surface-selector ownership execute. Physical-to-physical COM blits are excluded.
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
harness = support()+r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint32_t uint;
#define _DAT_00636668 (*(uint*)0x636668)
#define _DAT_0063666c (*(uint*)0x63666c)
#define _DAT_00636670 (*(uint*)0x636670)
#define DAT_0047a279 (*(int*)0x47a279)
#define _DAT_006401ec (*(int*)0x6401ec)
static unsigned pitches[4];static int locks[16],unlocks[16],nl,nu;
__attribute__((regparm(2),noinline,used)) static uint lock(uint surface,uint *pitch){
 assert(surface<4);locks[nl++]=surface;*pitch=pitches[surface];return 0x910000+surface*0x10000;
}
__attribute__((regparm(2),noinline,used)) static void unlock(uint surface,uint base){
 assert(base==0x910000+surface*0x10000);unlocks[nu++]=surface;
}
static uint FUN_00418a04(uint surface,uint *pitch){return lock(surface,pitch);}
static void FUN_00418b00(uint surface,uint base){unlock(surface,base);}
__attribute__((naked)) static void lock_hook(void){__asm__("pushal; call lock; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void unlock_hook(void){__asm__("pushal; call unlock; popal; ret");}
static int width,height,dx,dy;
__attribute__((noinline)) static void copy_original(int source,int destination,int sx,int sy){
 __asm__ volatile("push $0xc0; push height; push width; push dy; push dx; call *%%edi"
  : "+a"(source),"+c"(destination),"+d"(sx),"+b"(sy):"D"(0x417b20):"memory","cc");
}
__attribute__((noinline)) static void depth_original(int source,int destination,int x,int y){
 __asm__ volatile("push height; push width; call *%%edi"
  : "+a"(source),"+d"(destination),"+b"(x),"+c"(y):"D"(0x41868c):"memory","cc");
}
'''
for name in ('E2R_CopyGameRect', 'E2R_CopyDepthRect', 'FUN_00424b48'):
    harness += function(source, name)+'\n'
for start, end in [(0x417b20, 0x417d3c), (0x41868c, 0x4186f8), (0x424b48, 0x424bd8)]:
    harness += f'static const byte code_{start:x}[]={{'+','.join(map(str, image.code(start, end)))+'};\n'
harness += r'''
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void hook(uint at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(uint)fn-at-5;}
static void setup(int seed){
 for(int i=0;i<0x80000;i++)*(byte*)(0x900000+i)=(byte)(i*173+(i>>8)*19+seed*31);
 for(int i=0;i<4;i++)pitches[i]=64+i*4;
 *(int*)0x47a279=(seed&1)<<24;*(short*)0x479e8e=*(short*)0x479e90=-1;
 _DAT_006401ec=64;_DAT_00636668=0x950000;_DAT_0063666c=0x960000;_DAT_00636670=0x970000;
 // The original depth table is contiguous in mapped memory.
 nl=nu=0;
}
int main(void){
 map(0x410000,0x10000);map(0x420000,0x10000);map(0x470000,0x10000);map(0x630000,0x20000);map(0x900000,0x80000);
 memcpy((void*)0x417b20,code_417b20,sizeof code_417b20);memcpy((void*)0x41868c,code_41868c,sizeof code_41868c);
 memcpy((void*)0x424b48,code_424b48,sizeof code_424b48);
 hook(0x418a04,lock_hook);hook(0x418b00,unlock_hook);
 *(byte*)0x41c884=*(byte*)0x41bd1c=*(byte*)0x41c518=0xc3;
 static byte expected[0x80000];int cases=0;
 for(int source=0;source<4;source++)for(int destination=0;destination<4;destination++){
  if(source<2&&destination<2)continue;
  for(int seed=0;seed<128;seed++){
   int sx=seed%11,sy=seed%7;dx=(seed*3)%13;dy=(seed*5)%17;width=1+seed%21;height=1+seed%19;
   setup(seed);copy_original(source,destination,sx,sy);memcpy(expected,(void*)0x900000,sizeof expected);
   int lc=nl,uc=nu,ls[16],us[16];memcpy(ls,locks,sizeof ls);memcpy(us,unlocks,sizeof us);
   setup(seed);E2R_CopyGameRect(source,destination,sx,sy,dx,dy,width,height);
   if(nl!=lc||nu!=uc||memcmp(ls,locks,lc*4)||memcmp(us,unlocks,uc*4)||
      !e2r_memory_equal("pixel copy",expected,(void*)0x900000,sizeof expected)){
    fprintf(stderr,"copy source=%d destination=%d seed=%d\n",source,destination,seed);return 1;
   }
   cases++;
  }
 }
 printf("PASS: %d original-x86 pixel copy/pitch/overlap/selector ownership cases\n",cases);
 cases=0;
 for(int source=0;source<3;source++)for(int destination=0;destination<3;destination++)for(int seed=0;seed<128;seed++){
  int x=seed%13,y=seed%7;width=1+seed%21;height=1+seed%19;
  setup(seed);depth_original(source,destination,x,y);memcpy(expected,(void*)0x900000,sizeof expected);
  setup(seed);E2R_CopyDepthRect(source,destination,x,y,width,height);
  if(!e2r_memory_equal("depth copy",expected,(void*)0x900000,sizeof expected))return 1;
  cases++;
 }
 printf("PASS: %d original-x86 depth copy/odd-width/alias/rectangle cases\n",cases);
 cases=0;
 for(int page=0;page<2;page++)for(int seed=0;seed<128;seed++){
  setup(seed);DAT_0047a279=page<<24;
  for(int p=0;p<2;p++){
   *(int*)(0x47a29c+p*4)=1+seed%6;
   for(int i=0;i<6;i++){
    short *r=(short*)(0x6368e0+p*0x4b0+i*8);
    r[0]=(seed+i*3)%23;r[1]=r[0]+1+seed%17;
    r[2]=(seed+i)%7;r[3]=r[2]+seed%13;
    if((seed+i)%5==0)r[1]=r[0]-1;
    if((seed+i)%7==0)r[3]=r[2]-1;
   }
  }
  static byte initial[0x80000];memcpy(initial,(void*)0x900000,sizeof initial);
  ((void(*)(void))0x424b48)();memcpy(expected,(void*)0x900000,sizeof expected);
  memcpy((void*)0x900000,initial,sizeof initial);FUN_00424b48();
  if(!e2r_memory_equal("dirty depth restore",expected,(void*)0x900000,sizeof expected))return 1;
  cases++;
 }
 printf("PASS: %d original-x86 dirty depth list/page/invalid-rectangle cases\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('surface locks return independent padded fixture buffers',
                          'cursor hidden, cursor update/drawing leaves intercepted'))
