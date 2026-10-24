#!/usr/bin/env python3
"""Compare attached rendering ownership and proxy-chain handoff with original x86.

Palette, bone posing and angle extraction are intercepted; attached-root math and
original owner recursion execute. Existing pose fixtures cover the bone math.
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
source = (Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = support()+r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint16_t ushort,undefined2;typedef uint32_t uint,undefined4;
#define __fastcall
#define _DAT_00637240 (*(int*)0x637240)
#define _DAT_006368d8 (*(int*)0x6368d8)
#define DAT_006368d8 (*(byte*)0x6368d8)
static int E2R_actor_calc_context,calls,queue_remaining,trace[64][3];
static int IsBadReadPtr(const void *p,int n){return !p||!n;}
static int E2R_IsBadWritePtr(void *p,int n){return !p||!n;}
static void E2R_TraceActorLoopStage(const char *site,uintptr_t actor,int count){}
static void record(int kind,int x,int y){assert(calls<64);trace[calls][0]=kind;trace[calls][1]=x;trace[calls++][2]=y;}
__attribute__((regparm(1),used,noinline)) static void palette(uint actor){record(1,actor,0);}
__attribute__((regparm(2),used,noinline)) static void bones(uint actor,uint mode){
 record(2,actor,mode);
 for(int i=0;i<3;i++)*(short*)(actor+0x880+i*2)=*(short*)(actor+0x84+i*2)+31+i*71;
 memcpy((void*)(actor+0x806),(void*)(actor+6),18);
 if(queue_remaining>0){
  --queue_remaining;*(int*)(0x6368d8+_DAT_00637240*4)=0x908000;
  *(int*)0x908044=0x905000;*(int*)0x908132=0;
 }
}
__attribute__((regparm(2),used,noinline)) static void angles(uint dest,uint matrix){
 record(3,dest,matrix);*(short*)dest=1234;*(short*)(dest+2)=-2345;*(short*)(dest+4)=3456;
}
__attribute__((regparm(1),used,noinline)) static void chain_pose(uint actor){record(4,actor,0);}
static void FUN_00457818(uint actor,uint unused){palette(actor);}
static void FUN_00423858(uint actor,uint mode){bones(actor,mode);}
static void FUN_0042d46c(uint dest,ushort *matrix){angles(dest,(uint)matrix);}
static void FUN_00424318(void){chain_pose(E2R_actor_calc_context);}
__attribute__((naked)) static void palette_hook(void){__asm__("pushal; call palette; popal; ret");}
__attribute__((naked)) static void bones_hook(void){__asm__("pushal; call bones; popal; ret");}
__attribute__((naked)) static void angles_hook(void){__asm__("pushal; call angles; popal; ret");}
__attribute__((naked)) static void chain_pose_hook(void){__asm__("pushal; call chain_pose; popal; ret");}
'''
for name in ('FUN_00422368', 'FUN_00422460', 'FUN_00422538', 'E2R_SetIdentityMatrix',
             'E2R_ApplyEulerMatrix', 'E2R_TransformVector14', 'FUN_00420ec4',
             'E2R_PoseAttachmentForProxy', 'FUN_00421074'):
    harness += function(source, name)+'\n'
for label, start, end in [('render', 0x421074, 0x4211c8), ('root', 0x420ec4, 0x421074),
                           ('rotate', 0x422330, 0x422628), ('vector', 0x45de8b, 0x45df0e),
                           ('chain', 0x42dec4, 0x42deeb)]:
    harness += f'static const byte {label}_code[]={{'+','.join(map(str, image.code(start, end)))+'};\n'
harness += r'''
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void hook(uint at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(int)fn-(int)at-5;}
static void setup(uint seed){
 memset((void*)0x900000,0,0x10000);memset((void*)trace,0,sizeof trace);calls=0;queue_remaining=seed%8;E2R_actor_calc_context=0x909000;
 _DAT_00637240=seed&1;_DAT_006368d8=0;
 for(int i=0;i<3;i++){
  uint actor=0x900000+i*0x1000,node=actor+0x800;
  *(short*)actor=i+1;*(byte*)(actor+2)=seed&(2<<i)?8:0;
  *(byte*)(actor+3)=seed&(16<<i)?4:0;
  *(byte*)(actor+0x146)=seed&(128<<i)?0x80:0;
  *(uint*)(actor+0x1e)=node;*(uint*)(node+0x22)=actor;
  *(uint*)(actor+0xf2)=i?actor-0x1000+0x800:0;
  *(short*)node=seed&1024?7:0;
  for(int j=0;j<3;j++){
   *(short*)(actor+0x84+j*2)=seed*7919+i*1237+j*173;
   *(short*)(actor+0x90+j*2)=seed*1973+i*719+j*577;
   *(short*)(node+0x80+j*2)=seed*199+i*971+j*1237;
   *(short*)(actor+0xf6+j*2)=seed*17+i*71+j*131;
   *(short*)(actor+0xfc+j*2)=seed*271+i*997+j*619;
   *(short*)(actor+0x102+j*2)=seed*31+i*191+j*157;
   *(short*)(actor+0x108+j*2)=seed*197+i*653+j*139;
  }
  for(int j=0;j<9;j++)*(short*)(node+6+j*2)=seed*619+i*1973+j*997;
 }
}
int main(void){
 map(0x420000,0x10000);map(0x450000,0x10000);map(0x590000,0x80000);
 map(0x630000,0x40000);map(0x900000,0x10000);
 memcpy((void*)0x421074,render_code,sizeof render_code);memcpy((void*)0x420ec4,root_code,sizeof root_code);
 memcpy((void*)0x422330,rotate_code,sizeof rotate_code);memcpy((void*)0x45de8b,vector_code,sizeof vector_code);
 memcpy((void*)0x42dec4,chain_code,sizeof chain_code);*(byte*)0x42deeb=0xc3;
 hook(0x457818,palette_hook);hook(0x423858,bones_hook);hook(0x42d46c,angles_hook);hook(0x424318,chain_pose_hook);
 for(int i=0;i<65536;i++){
  double phase=i*6.28318/65536.0;
  *(short*)(0x59b590+i*2)=sin(phase)*16384.5;*(short*)(0x5de590+i*2)=cos(phase)*16384.5;
 }
 unsetenv("E2R_PROXY_MESH_BYPASS");
 static byte expected[0x10000];int expected_trace[64][3];
 for(uint test=0;test<4096;test++){
  setup(test);struct E2R_Registers regs={.eax=0x902000,.edx=0x13579bdf};e2r_original_call(0x421074,&regs);
  memcpy(expected,(void*)0x900000,sizeof expected);memcpy(expected_trace,trace,sizeof trace);int count=calls,work=_DAT_00637240;
  setup(test);FUN_00421074(0x902000,0x13579bdf);
  if(calls!=count||memcmp(trace,expected_trace,sizeof trace)||_DAT_00637240!=work||
     !e2r_memory_equal("attached rendering",expected,(void*)0x900000,sizeof expected)){
   fprintf(stderr,"attached render mismatch test=%u calls=%d/%d\n",test,calls,count);return 1;
  }
 }
 setenv("E2R_PROXY_MESH_BYPASS","1",1);
 for(uint test=0;test<1024;test++){
  setup(test);int node=0x903000;
  for(int i=0;i<5;i++){
   int cursor=node+i*0x200;*(int*)(cursor+0x22)=0x900000;
   *(int*)(cursor+0x44)=i<(int)(test%5)?cursor+0x200:0;*(int*)(cursor+0x48)=0xdeadbeef;
  }
  struct E2R_Registers regs={.eax=node,.esi=node};e2r_original_call(0x42dec4,&regs);
  memcpy(expected,(void*)0x900000,sizeof expected);memcpy(expected_trace,trace,sizeof trace);int count=calls;
  setup(test);
  for(int i=0;i<5;i++){
   int cursor=node+i*0x200;*(int*)(cursor+0x22)=0x900000;
   *(int*)(cursor+0x44)=i<(int)(test%5)?cursor+0x200:0;*(int*)(cursor+0x48)=0xdeadbeef;
  }
  E2R_PoseAttachmentForProxy(node);
  assert(calls==count&&!memcmp(trace,expected_trace,sizeof trace)&&E2R_actor_calc_context==0x909000);
  assert(e2r_memory_equal("proxy attachment chain",expected,(void*)0x900000,sizeof expected));
 }
 puts("PASS: 4096 original attached-render owner/root/recursion/memory cases; 1024 original reverse-chain/pose-owner handoffs for proxy attachments");
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, libraries=('-lm',), image=image,
            dependencies=('palette', 'full bone posing', 'matrix angle extraction'))
