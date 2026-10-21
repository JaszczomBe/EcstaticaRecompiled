#!/usr/bin/env python3
"""Compare object durability and its script callers with original i386 code.

Action loading and HUD redraws are intercepted; actor fields, queued action,
callback order, signed opcode operands and cursor advances are compared.
"""
import argparse
from pathlib import Path
import re,struct,subprocess,tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path);p.add_argument('--asan',action='store_true');p.add_argument('--cc',default='clang-21')
a=p.parse_args();src=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
pe=a.exe.read_bytes();h=struct.unpack_from('<I',pe,60)[0];n=struct.unpack_from('<H',pe,h+6)[0];opt=struct.unpack_from('<H',pe,h+20)[0]
def original(start,end):
 for i in range(n):
  _,va,size,raw=struct.unpack_from('<IIII',pe,h+24+opt+i*40+8);va+=0x400000
  if va<=start<end<=va+size:return pe[raw+start-va:raw+end-va]
 raise ValueError(hex(start))
f=re.search(r'void __fastcall FUN_00456924\([^\n]+\)\s*\{.*?\n\}',src,re.S).group()
harness=r'''
#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;typedef uint16_t ushort;typedef uint32_t uint,undefined4,int3;
#define __fastcall
#define _DAT_00630b60 (*(int*)0x630b60)
#define _DAT_00ac4a54 0
#define CONCAT31(a,b) (((uint)(a)<<8)|(byte)(b))
#define CONCAT44(a,b) (((uint64_t)(uint)(a)<<32)|(uint)(b))
static uint events[16][3],calls;
__attribute__((used,force_align_arg_pointer)) static void observe(uint tag,uint actor,uint amount) {
 assert(calls<16);events[calls][0]=tag;events[calls][1]=actor;events[calls++][2]=amount;
}
static void FUN_00451880(uint unused,int id) { observe(1,id,0); }
static void FUN_00456f94(void) { observe(2,0,0); }
static void FUN_00457410(void) { observe(3,0,0); }
static void FUN_004559bc(void) { observe(4,0,0); }
'''+f.replace('FUN_00456924(','durability_native(')+'\n'
for tag in (1,2,3,4,5):
 aa='%eax' if tag in (1,5) else '$0';bb='%edx' if tag==5 else '$0'
 harness+=f'__attribute__((naked)) static void hook{tag}(void) {{ __asm__("pushfl; pushal; push {bb}; push {aa}; push ${tag}; call observe; add $12,%esp; popal; popfl; ret"); }}\n'
harness+='static void FUN_00456924(uint actor,int amount) { observe(5,actor,amount); }\n'
for op in ('0x66','0x68'):
 start=src.index('      case '+op+':',src.index('void __fastcall FUN_0044f508('));end=src.index('      case ',start+10)
 branch=src[start:end]
 harness+='static int opcode_'+op+'(ushort *param_2,int *local_2c) {\nuint uVar19;uint64_t uVar25;ushort *puVar13=(ushort*)0xdeadbeef;ushort *extraout_ECX_57=0,*extraout_ECX_58=0;uint extraout_EDX_32=0,extraout_EDX_33=0;switch(1){case 1:\n'+branch.split(':\n',1)[1]+'}return (int)local_2c;}\n'
for start,end in [(0x456924,0x456a3c),(0x450869,0x45089c),(0x45089c,0x4508e3)]:
 harness+=f'static byte code_{start:x}[]={{'+','.join(map(str,original(start,end)))+'};\n'
harness+=r'''
static void map(int at,int size) { assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED); }
static void hook(int at,void *fn) { *(byte*)at=0xe9;*(int*)(at+1)=(int)fn-at-5; }
static void run_durability(int actor,int amount) {
 __asm__ volatile("call *%%edi" : "+a"(actor),"+d"(amount) : "D"(0x456924) : "ecx","memory","cc");
}
__attribute__((naked)) static int run_opcode(int cursor,int actor,int fn) {
 __asm__("push %ebp;push %ebx;push %esi;push %edi;sub $0x70,%esp;mov 0x84(%esp),%eax;mov %eax,0x44(%esp);mov 0x88(%esp),%ebp;call *0x8c(%esp);mov 0x44(%esp),%eax;add $0x70,%esp;pop %edi;pop %esi;pop %ebx;pop %ebp;ret");
}
static void setup(int owner,int initial,int action,int loaded) {
 memset((void*)0x900000,0,0x10000);memset(events,0,sizeof events);calls=0;
 _DAT_00630b60=0x900000;int actor=owner==0?0x900000:0x901000;
 *(short*)(actor+0x184)=initial;*(short*)(actor+0x188)=action;
 *(int*)(0x62ba20+5*4)=loaded?0x905000:0;
 if(owner>1) { *(int*)(actor+0xf2)=0x902000;*(int*)0x902022=owner==2?0x900000:0x903000; }
}
int main(void) {
 map(0x450000,0x10000);map(0x620000,0x20000);map(0x900000,0x10000);
 memcpy((void*)0x456924,code_456924,sizeof code_456924);
 memcpy((void*)0x450869,code_450869,sizeof code_450869);
 memcpy((void*)0x45089c,code_45089c,sizeof code_45089c);*(byte*)0x450c58=0xc3;
 hook(0x451880,hook1);hook(0x456f94,hook2);hook(0x457410,hook3);hook(0x4559bc,hook4);
 short starts[]={-32768,-2,0,1,12,24,100,101,32760};int amounts[]={-32768,-3000,-100,-1,0,1,24,25,100,999,32767};
 byte expected[0x10000];uint log[16][3],cases=0;
 for(int owner=0;owner<4;owner++)for(int i=0;i<9;i++)for(int j=0;j<11;j++)for(int action=-1;action<=5;action+=6)for(int loaded=0;loaded<2;loaded++) {
  int actor=owner==0?0x900000:0x901000;setup(owner,starts[i],action,loaded);
  run_durability(actor,amounts[j]);memcpy(expected,(void*)0x900000,sizeof expected);memcpy(log,events,sizeof log);uint count=calls;
  setup(owner,starts[i],action,loaded);durability_native(actor,amounts[j]);
  assert(!memcmp(expected,(void*)0x900000,sizeof expected));assert(calls==count && !memcmp(log,events,sizeof log));cases++;
 }
 printf("PASS: %u original durability field/queue/HUD callback cases\n",cases);
 hook(0x456924,hook5);cases=0;
 for(int op=0;op<2;op++)for(int encoded=0;encoded<4096;encoded++)for(int present=0;present<2;present++) {
  int actor=present?0x901000:0;*(int*)(0x630b60+608*4)=actor;
  ushort *words=(ushort*)0x906000;words[0]=op?0x68:0x66;words[1]=op?608:(0xf000|encoded);words[2]=0xf000|encoded;
  calls=0;memset(events,0,sizeof events);
  int cursor=run_opcode((int)words,actor,op?0x45089c:0x450869);memcpy(log,events,sizeof log);uint count=calls;
  calls=0;memset(events,0,sizeof events);
  int actual=op?opcode_0x68((ushort*)actor,(int*)words):opcode_0x66((ushort*)actor,(int*)words);
  assert(cursor==actual);assert(calls==count && !memcmp(log,events,sizeof log));cases++;
 }
 printf("PASS: %u original script durability actor/signed-operand/cursor cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-durability-') as tmp:
 c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
 flags=['-fsanitize=address','-fno-omit-frame-pointer'] if a.asan else []
 subprocess.run([a.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,timeout=30)
