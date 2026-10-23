#!/usr/bin/env python3
"""Compare the recovered eight-direction reaction branch with original x86."""
import argparse
from pathlib import Path
import re
from e2_original import OriginalImage, run_fixture, support
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path);p.add_argument('--asan',action='store_true');p.add_argument('--keep-harness',type=Path)
a=p.parse_args();image=OriginalImage(a.exe)
source=Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
at=source.index('        /* Original 0x42980e..0x42981e')
end=source.index('        if (-1 < local_6c[0x76])',at)
branch=source[at:end]
harness=r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint;typedef uint16_t ushort;typedef uint64_t ulonglong;
static uint random_value;
static uint64_t FUN_0045fc10(uint a,uint b){(void)a;return ((uint64_t)b<<32)|random_value;}
__attribute__((naked)) static void random_hook(void){__asm__("mov random_value,%eax;ret");}
'''+support()+r'''
static ushort native(short *actor){
 short *local_6c=actor,*psVar8=actor,sVar18;
 int *piVar22,*piVar26,iVar7,local_fc[8];
 uint uVar25;ushort uVar20,uVar6,uVar19;uint64_t uVar27;
'''+branch+r'''
 return uVar19;
}
static void map(uint address,uint size){assert(mmap((void*)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)address);}
int main(void){
 map(0x420000,0x10000);map(0x450000,0x10000);map(0x900000,0x10000);
CODE
 *(unsigned char*)0x4298d0=0xc3;
 *(unsigned char*)0x45fc10=0xe9;*(uint*)0x45fc11=(uint)random_hook-0x45fc15;
 short *actor=(short*)0x900000;uint frame=0x908000;
 *(uint*)(frame+0x2a)=(uint)actor;
 unsigned cases=0;
 for(int posture=0;posture<2;posture++)for(int facing=0;facing<8;facing++)for(unsigned rng=0;rng<32768;rng++){
  actor[0x49]=(short)(facing*8192);actor[0xb2]=0;actor[0x76]=posture?-1:0;
  random_value=rng;
  struct E2R_Registers registers={.ebp=frame};
  e2r_original_call(0x42980e,&registers);
  unsigned expected=(ushort)registers.esi,actual=native(actor);
  if(expected!=actual){fprintf(stderr,"reaction mismatch facing=%d rng=%u posture=%d expected=%u actual=%u\n",facing,rng,posture,expected,actual);return 1;}
  assert(actual<180);cases++;
 }
 printf("PASS: %u original-x86 directional reaction cases across all directions, random results and postures\n",cases);
}
'''
code=''
for start,end in [(0x427140,0x427160),(0x42980e,0x4298d0)]:
 data=image.code(start,end);code+='memcpy((void*)'+hex(start)+',(unsigned char[]){'+','.join(map(str,data))+'},'+str(len(data))+');\n'
harness=harness.replace('CODE',code)
run_fixture(harness,asan=a.asan,keep=a.keep_harness,image=image,dependencies=['random return intercepted; selected actor and copied direction table are original'])
