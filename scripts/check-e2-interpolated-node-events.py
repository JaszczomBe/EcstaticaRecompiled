#!/usr/bin/env python3
"""Compare interpolated node offset/extent events and metadata ownership to x86."""
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
harness = support() + r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint16_t ushort,undefined2;typedef uint32_t uint,undefined4;
#define __fastcall
#define DAT_0047a7e0 (*(int*)0x47a7e0)
#define DAT_0047a34a (*(short*)0x47a34a)
#define DAT_0047a366 (*(short*)0x47a366)
#define CONCAT22(a,b) (((uint)(ushort)(a)<<16)|(ushort)(b))
static int E2R_actor_calc_context;
static int IsBadReadPtr(const void *p,unsigned n){return !p||!n;}
static void FUN_0042b0f4(void){abort();}
static void FUN_0042d860(void){abort();}
static void FUN_0042d7c0(void){abort();}
static void FUN_0042d72c(void){abort();}
static void E2R_ApplyActionMotion13(int actor,short *event,int factor,int interpolated){abort();}
'''
for name in ('FUN_00432e08', 'FUN_0042ce70', 'FUN_00442954', 'FUN_004429e0', 'FUN_0042b490', 'FUN_0042b5fc', 'FUN_0042c790'):
    harness += function(source, name).replace('  return;','  return 0;') + '\n' if name in ('FUN_0042ce70', 'FUN_00442954', 'FUN_004429e0') else function(source, name) + '\n'
for start, end in [(0x42b490, 0x42b71c), (0x42c790, 0x42cf02), (0x442954, 0x442a2c), (0x432e08, 0x432ecc)]:
    harness += f'static const byte code_{start:x}[]={{' + ','.join(map(str, image.code(start, end))) + '};\n'
harness += r'''
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static void setup(int event,int seed){
 memset((void*)0x900000,0x5a,0x10000);*(int*)0x47a7e0=0;
 *(byte*)(0x63679e + event*2)=0x10;*(byte*)(0x63679f+event*2)=0;
 *(uint*)0x900054=0x904000;*(uint*)0x904000=0x905000;
 *(uint*)0x90501e=0;*(uint*)0x9000e4=0x900112;*(uint*)0x905044=0x906000;
 *(short*)0x906004=seed&1?7:0;
 *(short*)0x907000=0;*(short*)0x907002=event;
 for(int i=0;i<3;i++){
  *(short*)(0x90502c+i*2)=seed*17+i*131;
  *(short*)(0x90506e + i*2)=seed*11+i*197;
  *(short*)(0x905068+i*2)=seed%7==0?0:127+(seed*71+i*97)%10000;
  *(short*)(0x906068+i*2)=seed%11==0?0:199+(seed*173+i*37)%12000;
  *(short*)(0x907004+i*2)=(short)(seed*7919+i*1327);
 }
 E2R_actor_calc_context=seed%3==0?0:seed%3==1?0x900000:0x908000;
}
int main(void){
 map(0x420000,0x10000);map(0x430000,0x10000);map(0x440000,0x10000);map(0x470000,0x10000);
 map(0x630000,0x10000);map(0x900000,0x10000);
 memcpy((void*)0x42c790,code_42c790,sizeof code_42c790);memcpy((void*)0x42b490,code_42b490,sizeof code_42b490);memcpy((void*)0x432e08,code_432e08,sizeof code_432e08);memcpy((void*)0x442954,code_442954,sizeof code_442954);
 static byte expected[0x10000];int cases=0;
 for(int opcode=2;opcode<=5;opcode+=3)for(int seed=0;seed<4096;seed++){
  int factor=(seed*8191)%16385;
  setup(opcode,seed);struct E2R_Registers regs={.eax=0x907000,.edx=factor,.ebx=0x900000,.ecx=0};
  e2r_original_call(0x42c790,&regs);memcpy(expected,(void*)0x900000,sizeof expected);
  setup(opcode,seed);int context=E2R_actor_calc_context;
  FUN_0042c790(0,factor,(short*)0x907000,0x900000);
  if(!e2r_memory_equal("interpolated node event",expected,(void*)0x900000,sizeof expected)){
   fprintf(stderr,"node event opcode=%d seed=%d\n",opcode,seed);return 1;
  }
  assert(E2R_actor_calc_context==context);assert(*(uint*)0x9000e4==0x900112);cases++;
 }
 for(int terminal=0;terminal<2;terminal++)for(int flags=0;flags<64;flags++)for(int seed=0;seed<32;seed++){
  int factor=(seed*8191)%16385;
  setup(5,seed);*(uint*)0x90001e=0x905000;*(uint*)0x90504c=0;
  *(ushort*)0x905136=seed&flags;*(ushort*)0x905138=flags;
  struct E2R_Registers regs={.eax=0x900000,.edx=factor};
  e2r_original_call(terminal?0x42b5fc:0x42b490,&regs);memcpy(expected,(void*)0x900000,sizeof expected);
  setup(5,seed);*(uint*)0x90001e=0x905000;*(uint*)0x90504c=0;
  *(ushort*)0x905136=seed&flags;*(ushort*)0x905138=flags;int context=E2R_actor_calc_context;
  if(terminal)FUN_0042b5fc(0x900000);else FUN_0042b490(0x900000,factor);
  if(!e2r_memory_equal("node action reset",expected,(void*)0x900000,sizeof expected)){
   fprintf(stderr,"node reset terminal=%d flags=%x seed=%d\n",terminal,flags,seed);return 1;
  }
  assert(E2R_actor_calc_context==context);assert(*(uint*)0x9000e4==0x900112);
 }
 puts("PASS: 4096 original-x86 node reset/interpolation mask, factor and ownership cases");
 printf("PASS: %d original-x86 interpolated node offset/extent, metadata, actor rectangle and context cases\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('unrelated event branches abort if reached',))
