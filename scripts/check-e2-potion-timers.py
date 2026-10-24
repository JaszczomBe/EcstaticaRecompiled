#!/usr/bin/env python3
"""Compare delayed-effect word decoding, timer insertion and allocator with x86.

Uses original instructions and extracted production C with fixed mapped fixture
actors. The error requester is intercepted; scene/gameplay logic is outside this
bounded comparison. Original assets remain external.
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
harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define _DAT_00636588 (*(uint*)0x636588)
#define DAT_0047ab2c (*(int*)0x47ab2c)
static uintptr_t _DAT_009373dc,DAT_009373dc,DAT_009373e6;
static void FUN_00414e68(void) { abort(); }
'''+support()
for name in ('FUN_004538c0','FUN_00457cf0'):
    harness += function(source,name)+'\n'
# Test the production script decoder itself, rather than a parallel copy.
start = source.index('        /* Original 0x44fb4f..0x44fb84')
end = source.index('        uVar25 =',start)
harness += 'static void native_opcode(ushort *words) { int *local_2c=(int*)words; ushort uVar7;\n'+source[start:end]+'\n}\n'
# Compare the actual production priority/deadline selection block as well.
start = source.index('  iVar17 = *(int *)(local_6c + 0x93);')
end = source.index('  uVar12 =',start)
harness += r'''
static int load_count,load_id,selected_action,selected_kind;
__attribute__((used,noinline)) static void observe_load(int action) { load_count++;load_id=action; }
static void FUN_00451880(int unused,int action) { observe_load(action); }
static void native_select(int actor) {
 short *local_6c=(short*)actor,*psVar15=NULL;
 int iVar17,iVar7,extraout_ECX_07=0;uint uVar25;
'''+source[start:end]+r'''
 selected_action=iVar17;selected_kind=uVar25;
}
__attribute__((naked)) static void load_hook(void) {
 __asm__("pushal; push %eax; call observe_load; add $4,%esp; popal; ret");
}
'''
for label,start,end in [('timer',0x457cf0,0x457ddc),('alloc',0x4538c0,0x45391d),('opcode',0x44fb4f,0x44fb8e),('select',0x4279b2,0x427a06)]:
    harness += f'static const byte {label}_code[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
harness += r'''
static void map(uint at,uint size) { assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at); }
static void hook(uint at,void *fn) { *(byte*)at=0xe9;*(int*)(at+1)=(int)fn-at-5; }
__attribute__((naked)) static void original_opcode(ushort *words) {
 __asm__("pushal; sub $80,%esp; mov 116(%esp),%eax; mov %eax,68(%esp); mov $0x44fb4f,%eax; call *%eax; add $80,%esp; popal; ret");
}
static volatile int captured[3] __attribute__((used));
__attribute__((naked)) static void capture(void) {
 __asm__("mov %eax,captured; mov %edx,captured+4; mov %ebx,captured+8; ret");
}
static void setup(uint seed,int count) {
 memset((void*)0x900000,0,0x4000);memset((void*)0x9373dc,0,1000);
 for(int i=0;i<100;i++)*(short*)(0x9373dc+i*10)=-1;
 int id=seed%5000;*(int*)(0x630b60+id*4)=seed&1024?0:0x900000;
 _DAT_00636588=(int)(seed*7919u + (seed&512?0x7ffff000u:0));
 DAT_0047ab2c=0x12345678;
 *(int*)0x90017c=count?0x901000:0;
 for(int n=0;n<count;n++) {
  int node=0x901000+n*16;*(short*)node=100+n;
  *(int*)(node+2)=(uint)_DAT_00636588+(n-2)*35u;
  *(int*)(node+6)=n+1<count?node+16:0;
 }
}
static byte expected_actor[0x4000],expected_pool[1000];
int main(void) {
 map(0x410000,0x10000);map(0x420000,0x10000);map(0x440000,0x20000);map(0x470000,0x10000);map(0x620000,0x20000);
 map(0x900000,0x4000);map(0x930000,0x10000);
 memcpy((void*)0x457cf0,timer_code,sizeof timer_code);
 memcpy((void*)0x4538c0,alloc_code,sizeof alloc_code);
 hook(0x414e68,FUN_00414e68); // Never reached: the fixture has free records.
 int delays[]={-20,-1,0,1,5,10,20,1500,4095};
 for(uint seed=0;seed<4096;seed++) {
  int id=seed%5000,action=seed%17==0?2000:seed%3==0?5:409;
  int delay=delays[seed%9],count=seed%6;
  setup(seed,count);
  struct E2R_Registers regs={.eax=id,.edx=action,.ebx=delay};
  e2r_original_call(0x457cf0,&regs);
  memcpy(expected_actor,(void*)0x900000,sizeof expected_actor);
  memcpy(expected_pool,(void*)0x9373dc,sizeof expected_pool);int expected_duration=DAT_0047ab2c;
  setup(seed,count);FUN_00457cf0(id,action,delay);
  assert(e2r_memory_equal("timer actor/list",expected_actor,(void*)0x900000,sizeof expected_actor));
  assert(e2r_memory_equal("timer allocator",expected_pool,(void*)0x9373dc,sizeof expected_pool));
  assert(DAT_0047ab2c==expected_duration);
 }
 memcpy((void*)0x4279b2,select_code,sizeof select_code);*(byte*)0x427a06=0xc3;
 hook(0x451880,load_hook);
 for(uint seed=0;seed<4096;seed++) {
  setup(seed,1);
  *(int*)0x900126=seed&1?0x902000:0;
  *(int*)0x90012a=seed&2?0x902100:0;
  *(int*)0x90302a=0x900000;*(short*)0x901000=409;
  int difference=(int)(seed%7)-3;
  *(uint*)0x901002=(uint)_DAT_00636588-difference;
  *(int*)(0x62ba20+409*4)=seed&4?0:0x902200;
  load_count=0;load_id=-1;
  struct E2R_Registers regs={.ebp=0x903000};
  e2r_original_call(0x4279b2,&regs);
  int expected_loads=load_count,expected_id=load_id;
  load_count=0;load_id=-1;native_select(0x900000);
  assert((uint)selected_action==regs.ebx && (uint)selected_kind==regs.edi);
  assert(load_count==expected_loads && load_id==expected_id);
 }
 // Compare raw opcode decoding via the original register handoff. Use real
 // scheduler records as an independent observable on the recovered side.
 memcpy((void*)0x44fb4f,opcode_code,sizeof opcode_code);*(byte*)0x44fb89=0xc3;
 hook(0x457cf0,capture);
 for(uint seed=0;seed<4096;seed++) {
  ushort words[]={0x50,(ushort)(0x2000+seed%5000),(ushort)(0x3000+(seed%2?409:5)),(ushort)(0xf000+seed%4096)};
  original_opcode(words);
  int original_args[3];memcpy(original_args,(void*)captured,sizeof captured);
  setup(seed,0);*(int*)(0x630b60+(seed%5000)*4)=0x900000;
  FUN_00457cf0(original_args[0],original_args[1],original_args[2]);
  memcpy(expected_actor,(void*)0x900000,sizeof expected_actor);
  memcpy(expected_pool,(void*)0x9373dc,sizeof expected_pool);int expected_duration=DAT_0047ab2c;
  setup(seed,0);*(int*)(0x630b60+(seed%5000)*4)=0x900000;native_opcode(words);
  assert(!memcmp(expected_actor,(void*)0x900000,sizeof expected_actor));
  assert(!memcmp(expected_pool,(void*)0x9373dc,sizeof expected_pool));
  assert(DAT_0047ab2c==expected_duration);
 }
 puts("PASS: 4096 original delayed-effect timer/list/allocator cases and 4096 original script word/argument cases; 4096 signed deadline/priority selections");
}
'''
run_fixture(harness,asan=args.asan,keep=args.keep_harness,image=image,
            dependencies=('error requester (unreached)',))
