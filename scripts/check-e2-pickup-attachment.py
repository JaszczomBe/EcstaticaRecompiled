#!/usr/bin/env python3
"""Compare pickup attachment links, leaf arguments and event handoff with x86.

Pose, polar, floor, script and HUD leaves are intercepted. This bounds the node,
owner, replacement and callback contract; gameplay completion needs a live run.
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
body = function(source, 'FUN_0042deb8')
caller = re.search(r'FUN_0042deb8\([^;]+;', function(source, 'FUN_0042b880')).group()
harness = support()+r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;typedef uint64_t undefined8;
#define CONCAT22(a,b) (((uint)(ushort)(a)<<16)|(ushort)(b))
static int E2R_actor_calc_context;static short DAT_0047a34a;static uint DAT_0047a470;
static int calls,trace[16][3],floor_height;
static volatile uint script_seen[5] __attribute__((used));
static void record(int leaf,int x,int y){assert(calls<16);trace[calls][0]=leaf;trace[calls][1]=x;trace[calls++][2]=y;}
__attribute__((regparm(2),used,noinline)) static void pose(int owner,int unused){record(1,owner,0);}
__attribute__((regparm(2),used,noinline)) static void root(int actor,int node){record(2,actor,node);memcpy((void*)(actor+0x84),(void*)(node+0x80),6);}
__attribute__((regparm(2),used,noinline)) static int floor_query(int point,int actor){record(3,point,actor);return floor_height;}
__attribute__((regparm(2),used,noinline)) static void copy(int to,int from){record(4,to,from);memcpy((void*)to,(void*)from,6);}
__attribute__((used,noinline)) static uint hud(void){record(5,0,0);return 0;}
__attribute__((used,noinline)) static void script_trace(void){record(6,script_seen[0],script_seen[1]);}
__attribute__((used,noinline)) static void polar(short *angle,short *distance,short x,short z){record(7,x,z);*angle=17;*distance=173;}
static void FUN_00424318(void){pose(E2R_actor_calc_context,0);}
static void FUN_00420ec4(uint actor,short *node){root(actor,(int)node);}
static int FUN_00448a3c(uint point,uint actor){return floor_query(point,actor);}
static void FUN_00422aa0(uint to,undefined2 *from){copy(to,(int)from);}
static uint FUN_004559bc(void){return hud();}
static void E2R_NpcPolar16(short *a,short *d,short x,short z){polar(a,d,x,z);}
static void E2R_DispatchScriptRecord(ushort *code,ushort *actor,ushort *other,ushort *child,ushort *node){
 script_seen[0]=(uint)code;script_seen[1]=(uint)other;script_seen[2]=(uint)actor;
 script_seen[3]=(uint)node;script_seen[4]=(uint)child;script_trace();
}
// Missing-code diagnostics are outside this valid-record fixture.
static uint FUN_00441890(uint a,uint b){assert(0);return 0;}
static uint FUN_00442128(uint a,uint b){assert(0);return 0;}
static uint FUN_0045f0a1(uint a,byte *b,...){assert(0);return 0;}
static uint FUN_0043cbd0(uint a){assert(0);return 0;}
static byte *s_Actor___s_004721b0,*s_Code___s_004721bc;
__attribute__((naked)) static void pose_hook(void){__asm__("pushal; call pose; popal; ret");}
__attribute__((naked)) static void root_hook(void){__asm__("pushal; call root; popal; mov %eax,%ecx; ret");}
__attribute__((naked)) static void floor_hook(void){__asm__("pushal; call floor_query; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void copy_hook(void){__asm__("pushal; call copy; popal; ret");}
__attribute__((naked)) static void hud_hook(void){__asm__("pushal; call hud; popal; ret");}
__attribute__((naked)) static void polar_hook(void){__asm__("pushal; push %ecx; push %ebx; push %edx; push %eax; call polar; add $16,%esp; popal; ret");}
__attribute__((naked)) static void script_hook(void){__asm__(
 "mov %eax,script_seen; mov %edx,script_seen+4; mov %ecx,script_seen+8; mov %ebx,script_seen+12;"
 "push %eax; mov 8(%esp),%eax; mov %eax,script_seen+16; pop %eax;"
 "pushal; call script_trace; popal; ret $4");}
static uint seen_node;
__attribute__((regparm(1),used,noinline)) static uint capture_pickup(uint node){seen_node=node;return 0;}
__attribute__((naked)) static void pickup_hook(void){__asm__("pushal; call capture_pickup; popal; ret");}
'''+body+r'''
#define FUN_0042deb8 capture_pickup
static void caller_native(short *unaff_ESI){
'''+caller+r'''
}
#undef FUN_0042deb8
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void hook(uint at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(int)fn-(int)at-5;}
static void setup(uint seed){
 memset((void*)0x900000,0,0x8000);memset(trace,0,sizeof trace);memset((void*)script_seen,0,sizeof script_seen);calls=0;
 int node=0x900100,owner=0x901000,target=0x902000,attached=0x903000;
 *(int*)(node+0x22)=owner;*(int*)(owner+0x12e)=seed&1?target:0;
 *(int*)(node+0x13a)=seed&2?attached:0;*(int*)(attached+0xf2)=node;
 *(int*)(node+0x48)=0x12345678;
 for(int i=0;i<(int)((seed>>2)&3);i++){
  int cursor=node+i*0x200;*(int*)(cursor+0x44)=cursor+0x200;*(int*)(cursor+0x248)=0x1234+i;
 }
 for(int i=0;i<3;i++){
  *(short*)(node+0x18+i*2)=seed*7919+i*1237;
  *(short*)(node+0x80+i*2)=seed*181+i*171;
  *(short*)(owner+0x84+i*2)=seed*971+i*1237;
  *(short*)(target+0x84+i*2)=seed*193+i*7919;
  *(short*)(attached+0x90+i*2)=seed*379+i*917;
 }
 static const int deltas[]={0,1,63,64,65,-63,-64,-65};
 floor_height=*(short*)(node+0x82)+30+deltas[(seed>>4)&7];
 *(short*)(owner+0xf0)=(seed>>7)&7;
 short code=(seed>>12)&1?10:-1;
 *(short*)(target+0x13c)=code;*(int*)(0x6297c0+10*4)=0x907000;
 DAT_0047a34a=*(short*)0x47a34a=(seed>>10)&1;
 DAT_0047a470=*(uint*)0x47a470=seed&2048?owner:0x906000;
 E2R_actor_calc_context=0x908000;
}
'''
for label, start, end in [('pickup', 0x42deb8, 0x42e0d6), ('caller', 0x42c414, 0x42c421)]:
    harness += f'static const byte {label}_code[]={{'+','.join(map(str, image.code(start, end)))+'};\n'
harness += r'''
int main(void){
 map(0x420000,0x10000);map(0x440000,0x20000);map(0x470000,0x10000);map(0x620000,0x10000);map(0x900000,0x10000);
 memcpy((void*)0x42deb8,pickup_code,sizeof pickup_code);
 memcpy((void*)0x42c414,caller_code,sizeof caller_code);*(byte*)0x42c421=0xc3;
 hook(0x424318,pose_hook);hook(0x420ec4,root_hook);hook(0x448a3c,floor_hook);
 hook(0x422aa0,copy_hook);hook(0x4559bc,hud_hook);hook(0x427160,polar_hook);hook(0x44f32c,script_hook);
 static byte expected[0x8000];int expected_trace[16][3];uint expected_script[5];
 for(uint test=0;test<16384;test++){
  setup(test);struct E2R_Registers regs={.eax=0x900100};e2r_original_call(0x42deb8,&regs);
  memcpy(expected,(void*)0x900000,sizeof expected);memcpy(expected_trace,trace,sizeof trace);memcpy(expected_script,(void*)script_seen,sizeof script_seen);int count=calls;
  setup(test);FUN_0042deb8(0x900100);
  if(calls!=count||memcmp(trace,expected_trace,sizeof trace)||memcmp((void*)script_seen,expected_script,sizeof script_seen)||
     !e2r_memory_equal("pickup attachment",expected,(void*)0x900000,sizeof expected)||E2R_actor_calc_context!=0x908000){
   fprintf(stderr,"pickup attachment mismatch seed=%u calls=%d/%d\n",test,calls,count);return 1;
  }
 }
 hook(0x42deb8,pickup_hook);
 for(uint test=0;test<256;test++){
  *(uint*)0x909004=test*7919;
  struct E2R_Registers regs={.esi=0x900100,.edi=0x909000};e2r_original_call(0x42c414,&regs);
  assert(seen_node==0x900100);seen_node=0;
  caller_native((short*)0x900100);assert(seen_node==0x900100);
 }
 puts("PASS: 16384 original pickup attachment link/replacement/pose/polar/callback/HUD cases and 256 event node handoffs");
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('pose', 'polar', 'attached root', 'floor', 'copy', 'script callback', 'HUD'))
