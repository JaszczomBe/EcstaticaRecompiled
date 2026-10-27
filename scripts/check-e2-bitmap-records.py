#!/usr/bin/env python3
"""Compare bitmap record publication, mapped pool reuse and eviction with original x86."""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe',type=Path)
parser.add_argument('--asan',action='store_true')
parser.add_argument('--keep-harness',type=Path)
args=parser.parse_args()
image=OriginalImage(args.exe)
source=Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define _DAT_00637264 (*(int**)0x637264)
#define _DAT_00636588 (*(int*)0x636588)
#define _DAT_006365a8 (*(int*)0x6365a8)
#define DAT_00479e48 (*(int*)0x479e48)
static int E2R_cleanup_context;
static void FUN_00414e68(void) { abort(); }
'''+support()
for name in ('FUN_00452a94','FUN_00453210','FUN_0045384c','FUN_00426a04'):
    harness+=function(source,name)+'\n'
for start,end in ((0x452a94,0x452b6d),(0x453210,0x453263),(0x45384c,0x4538b5),(0x426a04,0x426a2e)):
    harness+=f'static const byte code_{start:x}[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
harness+=r'''
static void map(uint at,uint size) {
 assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);
}
static uint random_state;
static uint next(void) { random_state=random_state*1664525+1013904223;return random_state; }
static void setup(unsigned seed,int allocated,int free_slot,int payload) {
 random_state=seed;
 memset((void*)0x620000,0,0x20000);
 memset((void*)0x860000,0xa5,0x10000);
 memset((void*)0x900000,0x6b,0x40000);
 for(int offset=0;offset<400;offset+=20) {
  memset((void*)(0x86916c+offset),0,20);
  *(ushort*)(0x86917a+offset)=0x8000;
 }
 _DAT_00636588=1000;
 _DAT_006365a8=0x920000;
 DAT_00479e48=0;
 for(int index=0;index<allocated;index++) {
  uint node=0x86916c+index*20;
  *(short*)node=index;
  *(short*)(node+2)=payload?3+index%4:0;
  *(short*)(node+4)=payload?2+index%3:0;
  int bytes=*(short*)(node+2) * *(short*)(node+4);
  *(int*)(node+6)=payload?0x920000+DAT_00479e48:0;
  for(int i=0;i<bytes;i++) *(byte*)(0x920000+DAT_00479e48+i)=next()>>24;
  DAT_00479e48+=bytes;
  *(uint*)(node+10)=index+1<(uint)allocated?node+20:0;
  *(ushort*)(node+14)=1;
  *(int*)(node+16)=seed&1?900+(next()%100):900;
  *(uint*)(0x62b700+index*4)=node;
 }
 _DAT_00637264=allocated?(int*)0x86916c:NULL;
 if(free_slot>=0) *(ushort*)(0x86917a+free_slot*20)=0x8000;
 E2R_cleanup_context=0x903000;
}
static byte expected_pool[0x10000],expected_tables[0x20000],expected_arena[0x40000];
static int expected_used;
static void save(void) {
 memcpy(expected_pool,(void*)0x860000,sizeof expected_pool);
 memcpy(expected_tables,(void*)0x620000,sizeof expected_tables);
 memcpy(expected_arena,(void*)0x900000,sizeof expected_arena);
 expected_used=DAT_00479e48;
}
static void compare(void) {
 assert(e2r_memory_equal("bitmap pool",expected_pool,(void*)0x860000,sizeof expected_pool));
 assert(e2r_memory_equal("bitmap tables",expected_tables,(void*)0x620000,sizeof expected_tables));
 assert(e2r_memory_equal("bitmap arena/stream",expected_arena,(void*)0x900000,sizeof expected_arena));
 assert(DAT_00479e48==expected_used);
 assert(E2R_cleanup_context==0x903000);
}
static uint allocate(int original,uint preserved) {
 if(original) {
  struct E2R_Registers regs={.eax=0x906000,.edx=preserved};
  e2r_original_call(0x426a04,&regs);
  assert(regs.edx==preserved);
  return regs.eax;
 }
 return FUN_00426a04(0x906000,preserved);
}
static void lifecycle(int original,unsigned seed) {
 setup(seed,0,-1,0);
 for(int i=0;i<180;i++) {
  uint node=allocate(original,0x89abcdef);
  assert(node>=0x86916c && node<0x8692fc && (node-0x86916c)%20==0);
  assert(node!=0x906000 && *(short*)node==-1 && *(short*)(node+14)==1);
  int identity=i%200;
  *(short*)node=identity;
  *(uint*)(0x62b700+identity*4)=node;
  _DAT_00636588++;
  int count=0;
  for(uint at=(uint)_DAT_00637264;at;at=*(uint*)(at+10)) {
   assert(++count<=20);
   assert(*(uint*)(0x62b700+*(short*)at*4)==at);
  }
  assert(count==(i<20?i+1:20));
 }
}
int main(void) {
 map(0x410000,0x10000);map(0x420000,0x10000);map(0x450000,0x10000);
 map(0x470000,0x10000);map(0x620000,0x20000);map(0x860000,0x10000);map(0x900000,0x40000);
 memcpy((void*)0x452a94,code_452a94,sizeof code_452a94);
 memcpy((void*)0x453210,code_453210,sizeof code_453210);
 memcpy((void*)0x45384c,code_45384c,sizeof code_45384c);
 memcpy((void*)0x426a04,code_426a04,sizeof code_426a04);
 *(byte*)0x414e68=0xe9;*(int*)0x414e69=(uint)FUN_00414e68-0x414e6d;
 unsigned cases=0;
 for(unsigned seed=1;seed<=64;seed++) {
  for(int slot=0;slot<20;slot++) {
   setup(seed,20,slot,0);
   struct E2R_Registers regs={.eax=0x906000,.edx=0x89abcdef};
   e2r_original_call(0x45384c,&regs);uint expected=regs.eax;save();
   setup(seed,20,slot,0);
   uint64_t actual=FUN_0045384c(0x906000,0x89abcdef);
   assert((uint)actual==expected && actual>>32==0x89abcdef);compare();cases++;
   setup(seed,20,slot,0);expected=allocate(1,0x89abcdef);save();
   setup(seed,20,slot,0);assert(allocate(0,0x89abcdef)==expected);compare();cases++;
  }
  for(int payload=0;payload<2;payload++) {
   setup(seed,6,-1,payload);
   struct E2R_Registers regs={.edx=0x89abcdef};
   e2r_original_call(0x453210,&regs);uint expected=regs.eax;save();
   setup(seed,6,-1,payload);
   uint64_t actual=FUN_00453210(0,0x89abcdef);
   assert((uint)actual==expected && actual>>32==0x89abcdef);compare();cases++;
  }
  lifecycle(1,seed);save();lifecycle(0,seed);compare();cases+=180;
 }
 setup(1,0,-1,0);assert((uint)FUN_00453210(0,0)==0);
 printf("PASS: %u original-x86 bitmap allocation/publication/eviction/reuse cases; pool, name table, payload, stream canaries and context\n",cases);
}
'''
run_fixture(harness,asan=args.asan,keep=args.keep_harness,image=image,
            dependencies=['fatal path intercepted; valid mapped records only',
                          'bitmap payload reservation/parser integration remain native qualification'])
