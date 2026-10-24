#!/usr/bin/env python3
"""Compare attack target-height selection and both player callers with original x86.

Synthetic live lists exercise angle priority, eligibility, distance and model
height boundaries. Trigonometric code runs directly; damage/contact is separate.
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
source = (Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = support()+r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;typedef uint64_t undefined8;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint)(a)<<32)|(uint)(b))
#define _DAT_0063726c (*(short**)0x63726c)
'''
for name in ('E2R_PolygonAngle16', 'FUN_0042e7dc'):
    harness += function(source, name)+'\n'
player = function(source, 'FUN_00427584')
assert player.count('lVar28 = FUN_0042e7dc((uint)(uintptr_t)local_6c,uVar16);') == 2
assert not re.search(r'lVar28 = FUN_0042e7dc[^;]+;\s*uVar25 =', player)
harness += r'''
static uint next(uint *state){*state=*state*1664525+1013904223;return *state;}
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void setup(uint test){
 memset((void*)0x900000,0,0x10000);memset((void*)0x64a178,0,32);
 uint seed=test,owner=0x900000;
 *(uint*)(owner+0x54)=owner+0x800;*(uint*)(owner+0x808)=owner+0x900;
 *(short*)(owner+0x92)=test*997;
 *(short*)(owner+0x84)=-900;*(short*)(owner+0x86)=4096;*(short*)(owner+0x88)=-10000;
 *(short*)(owner+0x91a)=4096;
 *(uint*)(owner+0x11e)=owner+0x400;
 *(short*)(owner+0x400+0x172)=*(short*)(owner+0x400+0x1a2)=1;
 *(uint*)(owner+0x4c)=owner+0x1000;_DAT_0063726c=(short*)owner;
 static const int delta[]={0,1,-1,299,300,301,-299,-300,-301,1279,1280,1281,-1279,-1280,-1281};
 for(int i=1;i<=5;i++){
  uint actor=owner+i*0x1000,rep=actor+0x400,model=actor+0x900;
  *(short*)actor=i;*(uint*)(actor+0x4c)=i<5?actor+0x1000:0;
  *(uint*)(actor+0x11e)=rep;*(short*)(rep+0x46)=0;*(short*)(rep+0x14)=0;
  *(uint*)(actor+0x54)=actor+0x800;*(uint*)(actor+0x808)=model;*(uint*)(actor+0x1e)=model;
  for(int j=0;j<3;j++)*(short*)(actor+0x84+j*2)=*(short*)(owner+0x84+j*2)+(int)(next(&seed)%3001)-1500;
  *(short*)(model+0x1a)=4096+delta[next(&seed)%15];
  switch(next(&seed)%8){
   case 0:*(uint*)(actor+0x11e)=0;break;
   case 1:*(short*)(rep+0x46)=-1;break;
   case 2:*(byte*)(0x64a178+i*2)=4;break;
   case 3:*(byte*)(actor+3)=2;break;
   case 4:*(short*)(rep+0x14)=-1;break;
   case 5:*(uint*)(actor+0x808)=0;break;
   case 6:*(uint*)(actor+0x808)=*(uint*)(actor+0x1e)=0;break;
  }
 }
 // Keep one eligible candidate at explicit range/height boundaries.
 uint first=owner+0x1000;
 *(uint*)(first+0x11e)=first+0x400;*(short*)(first+0x446)=0;*(byte*)(0x64a178+2)=0;
 *(short*)(first+0x84)=-900+delta[test%15];
 *(short*)(first+0x86)=4096+delta[(test/15)%15];
 *(short*)(first+0x88)=-10000+delta[(test/225)%15];
 *(uint*)(first+0x808)=*(uint*)(first+0x1e)=first+0x900;
 *(short*)(first+0x91a)=4096+delta[(test/3375)%15];
 if(test%23==0)_DAT_0063726c=0;
 if(test%29==0)*(uint*)(owner+0x808)=0;
}
'''
for label, start, end in [('query', 0x42e7dc, 0x42ea00), ('angle', 0x432c64, 0x432de4),
                           ('caller_low', 0x429191, 0x4291b1), ('caller_mid', 0x429307, 0x429327)]:
    harness += f'static const byte {label}_code[]={{'+','.join(map(str, image.code(start, end)))+'};\n'
harness += r'''
int main(void){
 map(0x420000,0x20000);map(0x590000,0x80000);map(0x630000,0x20000);map(0x900000,0x10000);
 memcpy((void*)0x42e7dc,query_code,sizeof query_code);memcpy((void*)0x432c64,angle_code,sizeof angle_code);
 memcpy((void*)0x429191,caller_low_code,sizeof caller_low_code);*(byte*)0x4291b1=0xc3;
 memcpy((void*)0x429307,caller_mid_code,sizeof caller_mid_code);*(byte*)0x429327=0xc3;
 for(int i=0;i<65536;i++){
  double phase=i*6.28318/65536.0;
  *(short*)(0x59b590+i*2)=sin(phase)*16384.5;*(short*)(0x5de590+i*2)=cos(phase)*16384.5;
 }
 for(int i=0;i<256;i++){
  *(byte*)(0x5fe990+i)=atan(i*0.015625)*64.0*2.0*0.3183101550488765+0.5;
  *(byte*)(0x5fe890+i)=atan(i*0.25)*64.0*2.0*0.3183101550488765+0.5;
 }
 static byte before[0x10000];uint selected[3]={0};
 for(uint test=0;test<65536;test++){
  setup(test);memcpy(before,(void*)0x900000,sizeof before);
  struct E2R_Registers regs={.eax=0x900000,.edx=test^0x89abcdef,.ecx=test^0xfeedcafe};
  e2r_original_call(0x42e7dc,&regs);
  uint expected=regs.eax;
  uint64_t actual=FUN_0042e7dc(0x900000,test^0x89abcdef);
  if((uint)actual!=expected||(uint)(actual>>32)!=(test^0x89abcdef)||regs.ecx!=(test^0xfeedcafe)){
   fprintf(stderr,"attack target mismatch test=%u expected=%d actual=%d\n",test,(int)expected,(int)actual);return 1;
  }
  assert(!memcmp(before,(void*)0x900000,sizeof before));selected[(int)expected+1]++;
  *(uint*)0x90f02a=0x900000;
  for(int i=0;i<2;i++){
   struct E2R_Registers call={.ebp=0x90f000,.edx=test^0x89abcdef,.ecx=test^0xfeedcafe};
   e2r_original_call(i?0x429307:0x429191,&call);
   assert(call.eax==expected&&call.edx==(test^0x89abcdef)&&call.ecx==(test^0xfeedcafe));
  }
 }
 printf("PASS: 65536 original attack-height selections (%u low/%u level/%u high), eligibility/range/facing/priority/model fallback; both actor/direction-preserving callers\n",selected[0],selected[1],selected[2]);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, libraries=('-lm',), image=image,
            dependencies=('synthetic live actor lists and trigonometric tables',))
