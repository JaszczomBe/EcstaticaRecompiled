#!/usr/bin/env python3
"""Compare explicit background/redraw pixel and depth copies with original x86.

Cursor leaves are intercepted with the cursor hidden; original copy loops and
surface-selector ownership execute. Physical-to-physical COM blits are excluded.
Static-owner promotion executes its original caller with raster leaves
intercepted to supply a bounded rectangle.
"""
import argparse
import re
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
typedef uint8_t byte,undefined1;typedef uint16_t undefined2;typedef uint32_t uint,undefined4;
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
# The real static-owner caller must retain both coordinates and depth banks.
static_caller = function(source, 'FUN_00421a14')
for name in sorted(set(re.findall(r'\b_?DAT_[0-9a-f]+\b', static_caller))):
    if '#define ' + name + ' ' not in harness:
        harness += f'#define {name} (*(int*)0x{name[-8:]})\n'
harness += r'''
#define CONCAT22(a,b) (((uint)(uint16_t)(a)<<16)|(uint16_t)(b))
static short fixture_rect[4];
__attribute__((regparm(1),noinline,used)) static void render_static(uint actor) {
 memcpy((void*)(actor+0x112),fixture_rect,sizeof fixture_rect);
}
static void FUN_004249f4(uint actor){}
static void FUN_00424d58(uint actor){}
static void FUN_00424d14(uint actor){}
static void FUN_00424dd8(uint unused,uint actor){}
static void FUN_00424d98(uint actor){render_static(actor);}
static void FUN_00418484(int surface,int x,int y,int w,int h){}
static void FUN_0041760c(int a,int b,int c,int d,void *e,int f){abort();}
static void FUN_0041868c(int a,int b,int c,int d){abort();}
static void FUN_00426f70(void){abort();}
static void FUN_00455094(void){abort();}
static void FUN_0041b078(int a,int b){abort();}
static void FUN_004194a8(int a,int b){abort();}
__attribute__((naked)) static void render_static_hook(void){__asm__("pushal;call render_static;popal;ret");}
__attribute__((naked)) static void ignore_pixel_copy(void){__asm__("ret $4");}
'''
harness += static_caller + '\n'
for start, end in [(0x417b20, 0x417d3c), (0x41868c, 0x4186f8), (0x424b48, 0x424bd8), (0x421a14, 0x421f54)]:
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
 map(0x410000,0x10000);map(0x420000,0x10000);map(0x470000,0x10000);map(0x630000,0x50000);map(0x900000,0x80000);
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
 memcpy((void*)0x421a14,code_421a14,sizeof code_421a14);
 *(byte*)0x4249f4=*(byte*)0x424d58=*(byte*)0x424d14=*(byte*)0x424dd8=0xc3;
 hook(0x424d98,render_static_hook);hook(0x418484,ignore_pixel_copy);
 cases=0;
 for(int page=0;page<2;page++)for(int seed=0;seed<128;seed++) {
  fixture_rect[0]=seed%19;fixture_rect[1]=fixture_rect[0]+1+seed%20;
  fixture_rect[2]=seed%7;fixture_rect[3]=fixture_rect[2]+seed%13;
  static byte initial[0x80000];
  setup(seed);memset((void*)0x900000,0,0x1000);memset((void*)0x47aa00,0,0x200);
  DAT_0047a279=page<<24;DAT_0047a43c=1;DAT_0047a34a=DAT_0047a3e0=DAT_0047a760=0;
  _DAT_0063726c=0x900000;*(short*)0x900002=0x408;
  _DAT_00640124=_DAT_0064012c=0;_DAT_00640144=64;_DAT_00640120=64;
  *(int*)0x47a29c=*(int*)0x47a2a0=0;
  memcpy(initial,(void*)0x900000,sizeof initial);
  ((void(*)(void))0x421a14)();memcpy(expected,(void*)0x900000,sizeof expected);
  short original_list[4];memcpy(original_list,(void*)(0x6368e0+(1-page)*0x4b0),8);
  memcpy((void*)0x900000,initial,sizeof initial);*(int*)0x47a29c=*(int*)0x47a2a0=0;
  FUN_00421a14();
  if(!e2r_memory_equal("static owner depth/rectangle",expected,(void*)0x900000,sizeof expected)||
     memcmp(original_list,(void*)(0x6368e0+(1-page)*0x4b0),8))return 1;
  cases++;
 }
 printf("PASS: %d original-x86 static-owner depth promotion/coordinates/dirty rectangles (raster leaves intercepted)\n",cases);

}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('surface locks return independent padded fixture buffers',
                          'cursor hidden, cursor update/drawing leaves intercepted'))
