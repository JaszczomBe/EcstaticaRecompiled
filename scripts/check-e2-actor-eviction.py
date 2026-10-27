#!/usr/bin/env python3
"""Compare actor eviction, attached-owner recursion and pool reuse with original x86."""
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
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define _DAT_00637248 (*(int*)0x637248)
#define _DAT_0063726c (*(int*)0x63726c)
#define _DAT_00636588 (*(int*)0x636588)
#define DAT_0047a470 (*(short**)0x47a470)
#define DAT_0047a34a (*(short*)0x47a34a)
static int IsBadReadPtr(const void *p,unsigned n) { (void)p;(void)n;return 0; }
static char name[]="fixture_actor",error[100],label[100];
static jmp_buf fatal_jump;
__attribute__((used)) static void fatal(const char *text,const char *actor) {
 snprintf(error,sizeof error,"%s",text);snprintf(label,sizeof label,"%s",actor);
 longjmp(fatal_jump,1);
}
static void FUN_00414e5c(uint lines) { uint *p=(uint*)lines;assert(!p[2]);fatal((char*)p[0],(char*)p[1]); }
static void FUN_00414e68(void) { abort(); }
static undefined8 FUN_0043cac0(uint a,uint b) { (void)a;(void)b;abort(); }
static undefined8 FUN_00441890(uint a,uint b) { (void)a;return CONCAT44(b,name); }
__attribute__((naked)) static void names_hook(void) { __asm__("mov $name,%eax; ret"); }
__attribute__((used)) static void format_label(char *dest,const char *value) { snprintf(dest,52,"Actor '%s'",value); }
__attribute__((naked)) static void format_hook(void) {
 __asm__("pushal; mov %esp,%ebx; mov 44(%ebx),%eax; mov 36(%ebx),%edx; "
         "and $-16,%esp; sub $8,%esp; push %eax; push %edx; "
         "call format_label; mov %ebx,%esp; popal; ret");
}
__attribute__((naked)) static void fatal_hook(void) {
 __asm__("and $-16,%esp; sub $8,%esp; push %edx; push %eax; call fatal");
}
undefined8 FUN_0045282c(uint,uint);
'''+support()
for name in ('FUN_0043a800', 'FUN_0045282c', 'FUN_0045311c', 'FUN_00453510'):
    harness += function(source, name)+'\n'
for start, end in ((0x45282c, 0x452956), (0x45311c, 0x4531bc),
                   (0x453510, 0x45357c), (0x43a800, 0x43a8f7),
                   (0x453264, 0x45326b), (0x453508, 0x45350f),
                   (0x45366c, 0x453673), (0x475748, 0x4757f8)):
    harness += f'static const byte code_{start:x}[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
harness += r'''
static void map(uint at,uint size) {
 assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);
}
static void jump(uint at,void *target) { *(byte*)at=0xe9;*(uint*)(at+1)=(uint)target-at-5; }
static void w32(uint at,uint off,uint value) { *(uint*)(at+off)=value; }
static const uint actors[]={0xaa6a4c,0xaa6bd8,0xaa6d64,0xaa6ef0,0xaa707c};
static uint setup(int position,int attachment,int vertices) {
 memset((void*)0x620000,0,0x20000);memset((void*)0x900000,0,0x1c0000);
 _DAT_00636588=1000;DAT_0047a34a=0;DAT_0047a470=(short*)0x905000;
 for(int i=0;i<5;i++) {
  uint actor=actors[i],node=0x950d3c+i*350,vertex=0x910000+i*0x100,polygon=0x920000+i*0x100;
  *(short*)actor=i+10;*(short*)(actor+4)=4;w32(actor,0x11a,900+i*10);
  w32(0x630b60,(i+10)*4,actor);w32(actor,0x50,i<4?actors[i+1]:0);
  w32(actor,0x1e,node);w32(node,0x22,actor);*(short*)(node+4)=4;
  w32(node,0x11e,vertices?vertex:0);w32(vertex,0x26,vertex+0x30);
  w32(actor,0xd8,polygon);w32(polygon,0x1e,polygon+0x44);
 }
 _DAT_00637248=actors[0];
 uint target=actors[position];
 // Keep one unrelated active actor; exercise marking without evicting it.
 int active=position==0?4:0;
 _DAT_0063726c=actors[active];w32(actors[active],0x4c,0);
 if(attachment==1 || attachment==3) {
  uint child=actors[3],bone=*(uint*)(target+0x1e);
  w32(bone,0x13a,child);w32(child,0xf2,bone);
 }
 if(attachment==2 || attachment==3) {
  uint owner=actors[4],bone=*(uint*)(owner+0x1e);
  // Actor 4 must not be active when recursively removing its attached child.
  if(active==4) _DAT_0063726c=0;
  w32(target,0xf2,bone);w32(bone,0x13a,target);
 }
 error[0]=label[0]=0;return target;
}
static byte expected_pool[0x1c0000],expected_tables[0x20000];
static void save(void) {
 memcpy(expected_pool,(void*)0x900000,sizeof expected_pool);
 memcpy(expected_tables,(void*)0x620000,sizeof expected_tables);
}
static void compare(void) {
 assert(e2r_memory_equal("actor/node/vertex/polygon pools",expected_pool,(void*)0x900000,sizeof expected_pool));
 assert(e2r_memory_equal("actor table and list heads",expected_tables,(void*)0x620000,sizeof expected_tables));
}
static uint run(int original,int entry,uint actor) {
 if(original) {
  struct E2R_Registers r={.eax=actor,.edx=0x89abcdef};
  e2r_original_call(entry,&r);assert(r.edx==0x89abcdef);return r.eax;
 }
 undefined8 result=entry==0x45282c?FUN_0045282c(actor,0x89abcdef):
                   entry==0x45311c?FUN_0045311c(0,0x89abcdef):FUN_00453510(0,0x89abcdef);
 assert(result>>32==0x89abcdef);return (uint)result;
}
static void pressure_setup(void) {
 memset((void*)0x620000,0,0x20000);memset((void*)0x900000,0,0x1c0000);
 _DAT_00636588=1000;DAT_0047a470=(short*)0x905000;
 uint a=actors[0],b=actors[1];
 _DAT_00637248=a;_DAT_0063726c=a;w32(a,0x50,b);w32(a,0x11a,999);w32(b,0x11a,10);
 *(short*)a=10;*(short*)b=11;w32(0x630b60,40,a);w32(0x630b60,44,b);
 // Every slot is occupied. The oldest inactive root owns two nodes.
 w32(b,0x1e,0x950d3c+350);w32(0x950d3c+350,0x4c,0x950d3c+700);
 for(uint offset=0;offset<0x155cc0;offset+=350) *(short*)(0x950d3c+offset+4)=4;
}
int main(void) {
 map(0x410000,0x10000);map(0x430000,0x10000);map(0x440000,0x20000);
 map(0x470000,0x10000);map(0x620000,0x20000);map(0x900000,0x1c0000);
'''
for start in (0x45282c, 0x45311c, 0x453510, 0x43a800, 0x453264, 0x453508, 0x45366c, 0x475748):
    harness += f' memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness += r'''
 jump(0x441890,names_hook);jump(0x45f0a1,format_hook);jump(0x414e5c,fatal_hook);jump(0x414e68,FUN_00414e68);
 unsigned cases=0;
 for(int position=0;position<3;position++) for(int attached=0;attached<4;attached++)
 for(int vertices=0;vertices<2;vertices++) {
  uint actor=setup(position,attached,vertices);
  uint expected=run(1,0x45282c,actor);save();setup(position,attached,vertices);
  assert(run(0,0x45282c,actor)==expected);compare();cases++;
 }
 for(int seed=0;seed<128;seed++) {
  setup(1,0,seed&1);
  for(int i=0;i<5;i++) w32(actors[i],0x11a,1000-((i*17+seed)%101));
  if(seed&2) w32(actors[2],0xf2,0x906000),w32(0x906000,0x22,(uint)DAT_0047a470);
  uint expected=run(1,0x45311c,0);save();
  setup(1,0,seed&1);
  for(int i=0;i<5;i++) w32(actors[i],0x11a,1000-((i*17+seed)%101));
  if(seed&2) w32(actors[2],0xf2,0x906000),w32(0x906000,0x22,(uint)DAT_0047a470);
  assert(run(0,0x45311c,0)==expected);compare();cases++;
 }
 for(int kind=0;kind<5;kind++) for(int original=0;original<2;original++) {
  uint actor=setup(1,0,0);
  if(kind==0) _DAT_0063726c=actor;
  if(kind==1) *(short*)actor=-1;
  if(kind==2) DAT_0047a470=(short*)actor;
  if(kind==3) w32(0x630b60,*(short*)actor*4,0);
  if(kind==4) w32(actor,0x11a,1000);
  if(!setjmp(fatal_jump)) { run(original,0x45282c,actor);abort(); }
  const char *messages[]={"Can't remove Actor in active list","Can't remove Actor without name",
   "Can't remove main Actor","Can't remove Actor not in ThingTab","Can't remove Actor with current Time"};
  assert(!strcmp(error,messages[kind]));assert(!strcmp(label,"Actor 'fixture_actor'"));cases++;
 }
 pressure_setup();uint expected=run(1,0x453510,0);save();
 pressure_setup();assert(run(0,0x453510,0)==expected);compare();
 assert(expected==0x950d3c+350 && *(uint*)(0x630b60+44)==0);cases++;
 printf("PASS: %u original-x86 actor eviction/list/attachment/error/pool-pressure cases; memory and preserved EDX\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=['name lookup and formatting intercepted with a fixed name',
                          'fatal presentation intercepted; five original rejection branches compared',
                          'actual actor/node/vertex/polygon cleanup and full node-pool reuse executed'])
