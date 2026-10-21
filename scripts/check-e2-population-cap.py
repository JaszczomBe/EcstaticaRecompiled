#!/usr/bin/env python3
"""Compare the unchanged original population cap and scheduler interval with x86."""
import argparse
from pathlib import Path
import struct,subprocess,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('exe',type=Path);p.add_argument('--asan',action='store_true');p.add_argument('--cc',default='clang-21');a=p.parse_args()
src=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
start=src.index('      iVar5 = 0;',src.index('undefined4 FUN_0044e354(void)'));end=src.index('    }\n  }\n  return;',start);branch=src[start:end]
pe=a.exe.read_bytes();h=struct.unpack_from('<I',pe,60)[0];n=struct.unpack_from('<H',pe,h+6)[0];opt=struct.unpack_from('<H',pe,h+20)[0]
def original(start,end):
 for i in range(n):
  _,va,size,raw=struct.unpack_from('<IIII',pe,h+24+opt+i*40+8);va+=0x400000
  if va<=start<end<=va+size:return pe[raw+start-va:raw+end-va]
 raise ValueError(hex(start))
harness=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint8_t undefined1;typedef uint16_t ushort;
#define _DAT_0063726c (*(short**)0x63726c)
static int spawn_calls,spawn_count;
__attribute__((used,noinline)) static void FUN_0044dca4(int unused,int count) { spawn_calls++;spawn_count=count; }
__attribute__((naked)) static void spawn_hook(void) {
 __asm__("pushal;push %edx;push $0;call FUN_0044dca4;add $8,%esp;popal;ret");
}
static void native_count(void) { int iVar3=0,iVar5;short *psVar2;
'''+branch+r'''
}
static void map(int at,int size) { assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED); }
'''
for start,end in [(0x44e572,0x44e5a6),(0x44e35c,0x44e376)]:harness+=f'static unsigned char code_{start:x}[]={{'+','.join(map(str,original(start,end)))+'};\n'
harness+=r'''
int main(void) {
 map(0x440000,0x10000);map(0x470000,0x10000);map(0x630000,0x20000);map(0x900000,0x10000);
 memcpy((void*)0x44e572,code_44e572,sizeof code_44e572);*(unsigned char*)0x44e5a6=0xc3;
 memcpy((void*)0x44e35c,code_44e35c,sizeof code_44e35c);
 *(unsigned char*)0x44e376=0xb8;*(int*)0x44e377=1;*(unsigned char*)0x44e37b=0xc3;
 // The early return in the cadence slice uses this patched terminal.
 *(unsigned char*)0x44e5a6=0x31;*(unsigned char*)0x44e5a7=0xc0;*(unsigned char*)0x44e5a8=0xc3;
 *(unsigned char*)0x44dca4=0xe9;*(int*)0x44dca5=(int)spawn_hook-0x44dca9;
 unsigned cases=0;
 for(int length=0;length<=16;length++)for(int pattern=0;pattern<256;pattern++) {
  memset((void*)0x900000,0,0x10000);_DAT_0063726c=length?(short*)0x900000:NULL;
  for(int i=0;i<length;i++) {
   int actor=0x900000+i*0x200;*(short*)actor=i+1;
   *(int*)(actor+0x4c)=i+1<length?actor+0x200:0;
   *(short*)(actor+0x82)=(pattern>>(i%4))&1?11:3;
   *(ushort*)(0x64a178+(i+1)*2)=(pattern>>(4+i%4))&1?8:0;
  }
  spawn_calls=0;spawn_count=-1;
  __asm__ volatile("call *%%edi"::"D"(0x44e572):"eax","edx","ecx","ebx","memory","cc");
  int calls=spawn_calls,count=spawn_count;spawn_calls=0;spawn_count=-1;
  native_count();assert(spawn_calls==calls && spawn_count==count);
  if(calls)assert(count<4);cases++;
 }
 printf("PASS: %u original generated-actor/dead-state counting and four-actor cap cases\n",cases);
 cases=0;
 int lasts[]={0,1,1000,100000};
 for(int i=0;i<4;i++)for(int delta=-4;delta<=104;delta++) {
  int last=lasts[i],now=last+delta;*(int*)0x47b7f0=last;*(int*)0x636588=now;
  int result;__asm__ volatile("call *%%edi":"=a"(result):"D"(0x44e35c):"edx","memory","cc");
  assert(result==(last==0||0x31<now-last));cases++;
 }
 printf("PASS: %u original scheduler 50-tick interval cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-population-cap-') as tmp:
 c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
 flags=['-fsanitize=address','-fno-omit-frame-pointer'] if a.asan else []
 subprocess.run([a.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,timeout=30)
