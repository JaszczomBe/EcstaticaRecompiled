#!/usr/bin/env python3
"""Compare node detach and its action-event caller with original i386 code.

Pose/root/floor/HUD leaves are intercepted. Original reverse-link construction,
placement branches, field widths and unlinking execute without game-state guards.
"""
import argparse
from pathlib import Path
import re
from e2_original import OriginalImage, run_fixture, support
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path);p.add_argument('--asan',action='store_true');p.add_argument('--keep-harness',type=Path)
a=p.parse_args()
s=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
image=OriginalImage(a.exe)
original=image.code
body=re.search(r'^undefined4 __fastcall FUN_0042db74\([^\n]*\)\s*\{.*?\n\}',s,re.M|re.S).group()
call=re.search(r'FUN_0042db74\([^;]*& 2\)\);',s).group()
c=support()+r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint16_t ushort,undefined2;typedef uint32_t uint,undefined4;
#define __fastcall
static int E2R_actor_calc_context;static uintptr_t DAT_0047a470;static short DAT_0047a34a;
static int floor_height,calls;static int trace[16][3];
static void record(int leaf,int x,int y) {
 assert(calls<16);trace[calls][0]=leaf;trace[calls][1]=x;trace[calls++][2]=y;
}
__attribute__((regparm(2),used,noinline)) static void pose(int owner,int node) {record(1,owner,0);}
__attribute__((regparm(2),used,noinline)) static void root(int actor,int node) {record(2,actor,node);memcpy((void*)(actor+0x84),(void*)(node+0x80),6);}
__attribute__((regparm(2),used,noinline)) static int floor_query(int point,int actor) {record(3,point,actor);return floor_height;}
__attribute__((regparm(2),used,noinline)) static void copy(int to,int from) {record(4,to,from);memcpy((void*)to,(void*)from,6);}
__attribute__((used,noinline)) static void hud(void) {record(5,0,0);}
static void FUN_00424318(void){pose(E2R_actor_calc_context,0);}
static void FUN_00420ec4(uint actor,short *node){root(actor,(int)node);}
static int FUN_00448a3c(uint point,uint actor){return floor_query(point,actor);}
static void FUN_00422aa0(uint to,undefined2 *from){copy(to,(int)from);}
static void FUN_004559bc(void){hud();}
__attribute__((naked)) static void pose_hook(void){__asm__("pushal; call pose; popal; ret");}
// Original 0x420ec4 returns the attached actor in ECX and preserves EDX node.
__attribute__((naked)) static void root_hook(void){__asm__("pushal; call root; popal; mov %eax,%ecx; ret");}
__attribute__((naked)) static void floor_hook(void){__asm__("pushal; call floor_query; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void copy_hook(void){__asm__("pushal; call copy; popal; ret");}
__attribute__((naked)) static void hud_hook(void){__asm__("pushal; call hud; popal; ret");}
static uint seen_node,seen_mode;
__attribute__((regparm(2),used,noinline)) static uint capture_detach(uint node,int mode){seen_node=node;seen_mode=mode;return 0;}
__attribute__((naked)) static void detach_hook(void){__asm__("pushal; call capture_detach; popal; ret");}
static void run_original(uint node,int mode){struct E2R_Registers regs={.eax=node,.edx=mode};e2r_original_call(0x42db74,&regs);}
static void run_event(uint action,uint node){struct E2R_Registers regs={.ecx=action,.esi=node};e2r_original_call(0x42c42b,&regs);}
'''+body+r'''
#define FUN_0042db74 capture_detach
static void native_event(uint param_1,short *unaff_ESI){
'''+call+r'''
}
#undef FUN_0042db74
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);}
static void hook(uint at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(int)fn-(int)at-5;}
static void setup(uint seed) {
 memset((void*)0x900000,0,0x4000);calls=0;memset(trace,0,sizeof trace);E2R_actor_calc_context=0x907000;
 int node=0x900100,owner=0x901000,attached=0x902000;
 *(int*)(node+0x22)=owner;*(int*)(node+0x13a)=(seed&1)?attached:0;
 *(int*)(attached+0xf2)=node;*(int*)(node+0x48)=0x12345678;
 int chain=(seed>>3)&3;
 for(int i=0;i<chain;i++) {
  int prior=node+i*0x200,child=prior+0x200;
  *(int*)(prior+0x44)=child;*(int*)(child+0x48)=0x1234+i;
 }
 for(int i=0;i<3;i++) {
  *(short*)(node+0x80+i*2)=(short)(seed*7919+i*131);
  *(short*)(owner+0x84+i*2)=(short)(seed*173+i*337);
  *(short*)(attached+0x84+i*2)=(short)(seed*379+i*917);
  *(short*)(attached+0x90+i*2)=(short)(seed*1973+i*1237);
 }
 static const int delta[]={0,1,63,64,65,-63,-64,-65};
 floor_height=*(short*)(node+0x82)+30+delta[(seed>>10)&7];
 *(short*)(owner+0xf0)=(seed>>7)&7;
 DAT_0047a34a=*(short*)0x47a34a=(seed>>5)&1;
 DAT_0047a470=*(uint*)0x47a470=(seed&64)?owner:0x903000;
}
'''
for name,start,end in [('code',0x42db74,0x42dc9c),('caller',0x42c42b,0x42c43f)]:
 c+='static const byte '+name+'[]={'+','.join(map(str,original(start,end)))+'};\n'
c+=r'''
int main(void){
 map(0x420000,0x10000);map(0x440000,0x20000);map(0x470000,0x10000);map(0x900000,0x10000);
 memcpy((void*)0x42db74,code,sizeof code);memcpy((void*)0x42c42b,caller,sizeof caller);*(byte*)0x42c43f=0xc3;
 hook(0x424318,pose_hook);hook(0x420ec4,root_hook);hook(0x448a3c,floor_hook);hook(0x422aa0,copy_hook);hook(0x4559bc,hud_hook);
 static byte expected[0x4000];int expected_trace[16][3];
 for(uint test=0;test<16384;test++) {
  int mode=(test>>1)%3;
  setup(test);run_original(0x900100,mode);memcpy(expected,(void*)0x900000,sizeof expected);
  int count=calls;memcpy(expected_trace,trace,sizeof trace);
  setup(test);FUN_0042db74(0x900100,mode);
  if(calls!=count||memcmp(trace,expected_trace,sizeof trace)||!e2r_memory_equal("detach memory",expected,(void*)0x900000,sizeof expected)||E2R_actor_calc_context!=0x907000) {
   fprintf(stderr,"detach mismatch test=%u mode=%d calls=%d/%d\n",test,mode,count,calls);abort();
  }
 }
 hook(0x42db74,detach_hook);
 for(uint flags=0;flags<65536;flags++) {
  *(ushort*)0x90300c=flags;run_event(0x903000,0x900100);
  assert(seen_node==0x900100&&seen_mode==(flags&2));
  seen_node=seen_mode=0xffffffff;native_event(0x903000,(short*)0x900100);
  assert(seen_node==0x900100&&seen_mode==(flags&2));
 }
 puts("PASS: 16384 original detach link/pose/floor/rotation/HUD cases; 65536 original event node/placement-flag handoffs");
}
'''
run_fixture(c, asan=a.asan, timeout=20, keep=a.keep_harness, image=image,
            dependencies=('pose', 'root', 'floor query', 'vector copy', 'HUD'))
