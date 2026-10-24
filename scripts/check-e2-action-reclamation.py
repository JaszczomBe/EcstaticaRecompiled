#!/usr/bin/env python3
"""Compare cache selection, action/keyframe disposal and pool reuse with original x86.

Name/format diagnostics, scene disposal and heap freeing are intercepted. The real
original action/keyframe/event unlinking and record allocator execute directly.
"""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('exe', type=Path)
p.add_argument('--asan', action='store_true')
p.add_argument('--keep-harness', type=Path)
a = p.parse_args()
image = OriginalImage(a.exe)
source = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
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
typedef void *HLOCAL;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(uintptr_t)(a)<<32)|(uint32_t)(uintptr_t)(b))
#define _DAT_00637270 (*(short**)0x637270)
#define _DAT_0063725c (*(short**)0x63725c)
#define _DAT_00637248 (*(int*)0x637248)
#define _DAT_00636588 (*(int*)0x636588)
#define DAT_0047b7f4 (*(int*)0x47b7f4)
static int E2R_cleanup_context;
static short *E2R_fan_parse_record;
static int selected_action,selected_scene,select_only,free_count;
static uintptr_t freed[32];
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
static int E2R_NormalizeSceneListNode(int p) { return p; }
static int E2R_SceneListNext(int p) { return *(int*)(p+8); }
__attribute__((used,noinline)) static HLOCAL LocalFree(HLOCAL p) { assert(free_count<32);freed[free_count++]=(uintptr_t)p;return NULL; }
static void FUN_00452738(int p,int ignored) { selected_scene=p; }
static void FUN_0045374c(void) { *(byte*)(E2R_cleanup_context+0xe)=0x80; }
static void FUN_0043aa14(int);
static void FUN_0043ab38(void);
'''+support()
for name in ('FUN_00453264', 'FUN_0043ab38', 'FUN_0043aa14', 'FUN_00452c70'):
    harness += function(source, name)+'\n'
# Keep the recovered selection independent of the actual disposal comparison.
body = function(source, 'FUN_00452f18').replace('FUN_00452c70(iVar6,iVar2);', 'select_action(iVar6);')
harness += 'static void select_action(int p) { selected_action=p; }\n'+body+'\n'
harness += function(source, 'FUN_0045328c')+'\n'
ranges = [(0x452f18,0x452fe8),(0x452c70,0x452d3c),(0x43aa14,0x43aa80),
          (0x43ab38,0x43ab74),(0x453264,0x45326b),(0x453330,0x453337),
          (0x45374c,0x453754),(0x45328c,0x453330)]
for start, end in ranges:
    harness += f'static const byte code_{start:x}[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
harness += r'''
__attribute__((naked)) static void noop(void) { __asm__("ret"); }
__attribute__((naked)) static void action_hook(void) { __asm__("mov %eax,selected_action; ret"); }
__attribute__((naked)) static void scene_hook(void) { __asm__("mov %eax,selected_scene; ret"); }
__attribute__((naked)) static void free_hook(void) {
 __asm__("pushal; push %eax; call LocalFree; add $4,%esp; popal; ret");
}
__attribute__((naked)) static void fatal_hook(void) { __asm__("ud2"); }
static void map(uint at,uint size) { assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=(void*)-1); }
static void hook(uint at,void *fn) { *(byte*)at=0xe9;*(int*)(at+1)=(uint)fn-at-5; }
static uint rng;
static uint next(void) { rng=rng*1664525+1013904223;return rng; }
static void selection_setup(int seed) {
 memset((void*)0x900000,0,0x10000);rng=seed;
 _DAT_00636588=1000;_DAT_00637270=(short*)0x901000;
 _DAT_0063725c=(short*)0x902000;_DAT_00637248=0x903000;
 for(int n=0;n<6;n++) {
  uint act=0x901000+n*0x40;
  *(int*)(act+8)=n<5?act+0x40:0;
  *(ushort*)(act+0xc)=next()%4;*(int*)(act+0x12)=800+next()%250;
 }
 for(int n=0;n<2;n++) {
  uint sc=0x902000+n*0x100,actor=0x903000+n*0x200;
  *(int*)(sc+8)=n?0:sc+0x100;*(byte*)(sc+0x96)=next()%2;
  *(int*)(sc+0xa0)=800+next()%250;
  *(int*)(actor+0x50)=n?0:actor+0x200;
  *(int*)(actor+0xa6)=0x901000+(next()%6)*0x40;
 }
 selected_action=selected_scene=0;
}
static void disposal_setup(int seed) {
 memset((void*)0x900000,0,0x10000);memset((void*)0x73fb9c,0x80,560000);
 _DAT_00637270=(short*)0x901000;_DAT_00636588=1000;
 *(int*)0x63726c=0;free_count=0;memset(freed,0,sizeof freed);
 int keys=seed%6,events=(seed/6)%6,heaps=(seed/36)%3;
 for(int n=0;n<3;n++) {
  uint act=0x901000+n*0x40;*(short*)act=100+n;
  *(uint*)(act+8)=n<2?act+0x40:0;*(uint*)(act+0x12)=800;
  *(uint*)(0x62ba20+(100+n)*4)=act;
 }
 uint target=0x901000+(seed%3)*0x40;
 *(int*)(target+4)=keys?0x904000:0;
 for(int k=0;k<keys;k++) {
  uint key=0x904000+k*0x40;*(int*)(key+2)=k+1<keys?key+0x40:0;
  *(int*)(key+6)=events?0x73fb9c+k*6*14:0;
  *(int*)(key+10)=heaps?0x908000+k*0x80:0;
  for(int j=0;j<events;j++) {
   uint rec=0x73fb9c+(k*6+j)*14;memset((void*)rec,0,14);*(short*)(rec+2)=j+1;
   *(int*)(rec+10)=j+1<events?rec+14:0;
  }
  for(int j=0;j<heaps;j++) {
   uint hp=0x908000+k*0x80+j*0x20;*(int*)(hp+0xd)=j+1<heaps?hp+0x20:0;
  }
 }
 E2R_cleanup_context=0x909000;
}
int main(void) {
 map(0x430000,0x40000);map(0x470000,0x10000);map(0x620000,0x20000);
 map(0x730000,0xa0000);map(0x900000,0x10000);
'''
for start, _ in ranges:
    harness += f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness += r'''
 hook(0x441b24,noop);hook(0x45f0a1,noop);hook(0x414e68,fatal_hook);
 hook(0x452738,scene_hook);hook(0x452c70,action_hook);hook(0x45f9b5,free_hook);
 byte expected[0x10000],expected_pool[560000];uintptr_t expected_free[32];
 for(int seed=0;seed<4096;seed++) {
  selection_setup(seed);struct E2R_Registers r={0};e2r_original_call(0x452f18,&r);
  int selected=selected_action,scene=selected_scene,ret=r.eax;
  memcpy(expected,(void*)0x900000,sizeof expected);
  selection_setup(seed);int result=FUN_00452f18(0,77);
  assert(result==ret && selected_action==selected && selected_scene==scene);
  assert(!memcmp(expected,(void*)0x900000,sizeof expected));
 }
 memcpy((void*)0x452c70,code_452c70,sizeof code_452c70);
 for(int seed=0;seed<1024;seed++) {
  disposal_setup(seed);uint target=0x901000+(seed%3)*0x40;
  struct E2R_Registers r={.eax=target};e2r_original_call(0x452c70,&r);
  memcpy(expected,(void*)0x900000,sizeof expected);memcpy(expected_pool,(void*)0x73fb9c,sizeof expected_pool);
  memcpy(expected_free,freed,sizeof freed);int count=free_count;short *head=_DAT_00637270;
  disposal_setup(seed);FUN_00452c70(target,0);
  assert(_DAT_00637270==head && *(uint*)(0x62ba20+(100+seed%3)*4)==0);
  assert(!memcmp(expected,(void*)0x900000,sizeof expected));
  assert(!memcmp(expected_pool,(void*)0x73fb9c,sizeof expected_pool));
  assert(free_count==count && !memcmp(expected_free,freed,sizeof freed));
  assert(E2R_cleanup_context==0x909000);
  // Simulate a full record pool with only the disposed event records free.
  if(seed%6 && (seed/6)%6) {
   DAT_0047b7f4=40001;r=(struct E2R_Registers){0};e2r_original_call(0x45328c,&r);
   uint address=r.eax;int cursor=DAT_0047b7f4;byte record[14];memcpy(record,(void*)address,14);
   memcpy((void*)0x73fb9c,expected_pool,sizeof expected_pool);DAT_0047b7f4=40001;
   assert((uint)FUN_0045328c(0,0)==address && DAT_0047b7f4==cursor);
   assert(!memcmp(record,(void*)address,14));
  }
 }
 puts("PASS: 4096 original cache-selection cases; 1024 action/keyframe/event disposal cases with heap handoffs, nested context and full-pool record reuse");
}
'''
# The fatal hook address is outside the contiguous cache code range.
harness = harness.replace('map(0x430000,0x40000);', 'map(0x410000,0x10000);map(0x430000,0x40000);')
run_fixture(harness, asan=a.asan, keep=a.keep_harness, image=image,
            dependencies=['name/format diagnostics','scene disposal','heap free observer'])
