#!/usr/bin/env python3
"""Compare twelve original box faces, transformed vertices and live references.

Original Q14 matrix instructions execute. Camera projection is intercepted with
an identical explicit fixture transform; flat/textured rasterizers are observed.
Texture loading and editor-only viewport adjustments remain outside this check.
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
harness = support() + r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;typedef uint16_t ushort,undefined2;typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;
#define __fastcall
#define CONCAT22(a,b) (((uint)(ushort)(a)<<16)|(ushort)(b))
#define E2R_READ2(p,o) (*(ushort*)((uint)(p)+(o)))
#define DAT_0047a279 (*(int*)0x47a279)
#define DAT_0047a3e0 (*(int*)0x47a3e0)
#define DAT_0047a434 (*(int*)0x47a434)
#define DAT_0047a34a (*(int*)0x47a34a)
#define DAT_0047a34c (*(int*)0x47a34c)
#define DAT_0047a366 (*(int*)0x47a366)
#define DAT_0047a37c (*(int*)0x47a37c)
static int _DAT_00636588,_DAT_006401c8,_DAT_006401cc,_DAT_006401d4,
 _DAT_006401ec,_DAT_006401fc,_DAT_0064020c,sRam0047a380;
#define DAT_0047a2b4 (*(int*)0x47a2b4)
#define DAT_0047a2b8 (*(int*)0x47a2b8)
#define DAT_0047a2e4 (*(int*)0x47a2e4)
#define DAT_0047a2e8 (*(int*)0x47a2e8)
#define DAT_0047a314 (*(int*)0x47a314)
#define DAT_0047a318 (*(int*)0x47a318)
static int E2R_UseProxyMesh(int actor,int ellipsoids){return 0;}
static int IsBadReadPtr(const void *p,int size){return !p;}
struct Face {int mode;ushort flags;int owner;short material,light;short vertices[3][6],reference[3][6];};
static struct Face calls[12];static int count;
__attribute__((regparm(2),noinline,used)) static void project(uint out,uint input){
 short *dest=(short*)out,*src=(short*)input;
 dest[0]=(src[0]-37)/2;dest[1]=(src[1]+79)/3;dest[2]=src[2]+1024;
}
static void FUN_00422fd8(uint out,int input){project(out,input);}
__attribute__((naked)) static void projection_hook(void){__asm__("pushal; call project; popal; ret");}
__attribute__((regparm(3),noinline,used)) static void raster(uint polygon,uint mode,uint reference){
 assert(count<12);struct Face *f=&calls[count++];memset(f,0,sizeof *f);
 f->mode=mode;f->flags=*(ushort*)(polygon+2);f->owner=*(uint*)(polygon+0x22);
 f->material=*(short*)(polygon+0x10);f->light=*(short*)(polygon+0x26);
 for(int i=0;i<3;i++){
  memcpy(f->vertices[i],(void*)(*(uint*)(polygon+4+i*4)+0x10),12);
  memcpy(f->reference[i],(void*)(*(uint*)(reference+4+i*4)+0x10),12);
 }
}
static void FUN_00431a7c(int polygon,int mode,int reference){raster(polygon,mode,reference);}
__attribute__((naked)) static void raster_hook(void){__asm__("pushal; mov %ebx,%ecx; call raster; popal; ret");}
static undefined8 FUN_004525f0(int a,int b){abort();}
static void FUN_00433e9c(int a,int b){abort();}
'''
harness += function(source, 'E2R_TransformVector14') + '\n' + function(source, 'FUN_00425018') + '\n'
for label, start, end in [('box', 0x425018, 0x425536), ('vector', 0x45de8b, 0x45df0e),
                           ('faces', 0x47a2b8, 0x47a348)]:
    harness += f'static const byte {label}_code[]={{' + ','.join(map(str,image.code(start,end))) + '};\n'
harness += r'''
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void hook(uint at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(uint)fn-at-5;}
static void setup(int seed,int flags,int high){
 memset((void*)0x900000,0,0x1000);memset(calls,0,sizeof calls);count=0;
 *(uint*)0x900022=0x900400;*(short*)0x9000ce=seed%12;*(short*)0x9000d0=seed*97;
 *(short*)0x900156=-1;*(byte*)0x900403=flags;DAT_0047a279=high<<24;
 double a=seed*0.193;short c=cos(a)*16384,s=sin(a)*16384;
 short matrix[9]={c,0,s,0,16384,0,-s,0,c};memcpy((void*)0x900006,matrix,18);
 for(int i=0;i<3;i++){
  *(short*)(0x900068+i*2)=seed*7%500+i*29;
  *(short*)(0x900080+i*2)=seed*3-500+i*719;
 }
}
int main(void){
 map(0x420000,0x20000);map(0x450000,0x10000);map(0x470000,0x10000);map(0x900000,0x1000);
 memcpy((void*)0x425018,box_code,sizeof box_code);memcpy((void*)0x45de8b,vector_code,sizeof vector_code);
 memcpy((void*)0x47a2b8,faces_code,sizeof faces_code);
 hook(0x422fd8,projection_hook);hook(0x431a7c,raster_hook);
 struct Face expected[12];int cases=0;
 for(int seed=0;seed<256;seed++)for(int flags=0;flags<=4;flags+=4)for(int high=0;high<2;high++){
  setup(seed,flags,high);struct E2R_Registers regs={.eax=0x900000};e2r_original_call(0x425018,&regs);
  assert(count==12);memcpy(expected,calls,sizeof expected);
  setup(seed,flags,high);FUN_00425018(0x900000);
  if(count!=12 || memcmp(expected,calls,sizeof expected)){
   fprintf(stderr,"FAIL box seed=%d flags=%d high=%d\n",seed,flags,high);
   e2r_memory_equal("box faces",expected,calls,sizeof expected);return 1;
  }
  cases++;
 }
 printf("PASS: %d original-x86 box cases, %d faces with Q14/world/projected vertices and references\n",cases,cases*12);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image, libraries=('-lm',),
            dependencies=('Camera projection intercepted identically', 'Flat raster input observed, not rasterized',
                          'No texture/editor viewport path'))
