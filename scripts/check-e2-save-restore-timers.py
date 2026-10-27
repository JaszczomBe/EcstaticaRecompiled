#!/usr/bin/env python3
"""Compare the loader's signed relative-timer reconstruction with its original instruction block."""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe',type=Path)
parser.add_argument('--asan',action='store_true')
parser.add_argument('--keep-harness',type=Path)
args=parser.parse_args()
image=OriginalImage(args.exe)
source=Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
loader=function(source,'FUN_004544a4')
a=loader.index('    int timers = (short)E2R_ReadSaveWord(stream);')
b=loader.index('    E2R_actor_calc_context = actor;',a)
harness=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;typedef uint16_t ushort;
typedef uint32_t uint,undefined4;typedef uint64_t undefined8,ulonglong;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define WORD(a) (*(uint *)(a))
#define _DAT_00636588 WORD(0x636588)
static void FUN_00414e68(void) { assert(!"Timer pool exhausted"); }
static ushort E2R_ReadSaveWord(int *stream) {
    assert(stream[1]>=2);byte *p=(byte *)(uintptr_t)stream[0];
    stream[0]+=2;stream[1]-=2;return p[0]|p[1]<<8;
}
'''
harness+=support()+function(source,'FUN_004538c0')+'\n'
harness+='static void restore(uintptr_t actor,int *stream) {\n'+loader[a:b]+'}\n'
for i,(start,end) in enumerate(((0x4544a4,0x4544b0),(0x454934,0x4549a5),(0x4173c8,0x41745b),(0x4538c0,0x453920))):
    harness+=f'static const byte code{i}[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
harness+=r'''
__attribute__((used,noinline)) static uint read_byte(int *stream) { assert(stream[1]);uint v=*(byte *)(uintptr_t)stream[0];stream[0]++;stream[1]--;return v; }
__attribute__((naked)) static void read_hook(void) { __asm__("pushal; push %eax; call read_byte; add $4,%esp; mov %eax,28(%esp); popal; ret"); }
static void jump(uint address,uint target) { *(byte *)address=0xe9;WORD(address+1)=target-address-5; }
static void map(uint address,uint size) { assert(mmap((void *)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)address); }
static void pool(void) { memset((void *)0x9373dc,0,1000);for(uint at=0x9373dc;at<0x9377c4;at+=10)*(ushort *)at=65535;WORD(0x70017c)=0; }
int main(void) {
    map(0x410000,0x10000);map(0x450000,0x10000);map(0x630000,0x10000);map(0x700000,0x1000);map(0x930000,0x10000);
    memcpy((void *)0x4544a4,code0,sizeof code0);memcpy((void *)0x454934,code1,sizeof code1);
    memcpy((void *)0x4173c8,code2,sizeof code2);memcpy((void *)0x4538c0,code3,sizeof code3);
    /* Keep the original loader prologue and timer block. The fixture adapter
     * supplies only its established ESI stream and +0x148 actor local. */
    const byte adapter[]={0x89,0xc6,0x89,0x94,0x24,0x48,0x01,0,0};
    memcpy((void *)0x4544b0,adapter,sizeof adapter);jump(0x4544b9,0x454934);
    const byte epilogue[]={0x81,0xc4,0x4c,0x01,0,0,0x5d,0x5f,0x5e,0x5a,0x59,0x5b,0xc3};
    memcpy((void *)0x4549a5,epilogue,sizeof epilogue);jump(0x45f38a,(uint)read_hook);
    const uint clocks[]={0,1,12345,0x7fffffff,0x80000000u,0xfffffffeu};
    const short deltas[]={-32768,-12345,-1,0,1,12345,32767};
    const unsigned counts[]={0,1,2,5,99};unsigned cases=0;
    for(unsigned c=0;c<6;c++)for(unsigned d=0;d<7;d++)for(unsigned n=0;n<5;n++) {
        byte contents[402];unsigned at=0;unsigned total=counts[n];
        contents[at++]=total;contents[at++]=total>>8;
        for(unsigned i=0;i<total;i++) {
            unsigned action=1000+i;ushort delta=deltas[(d+i)%7];
            contents[at++]=action;contents[at++]=action>>8;contents[at++]=delta;contents[at++]=delta>>8;
        }
        int stream[7]={(uint)contents,at,0,0x40};byte expected[1000];
        pool();_DAT_00636588=clocks[c];struct E2R_Registers regs={.eax=(uint)stream,.edx=0x700000};
        e2r_original_call(0x4544a4,&regs);assert(stream[1]==0);uint head=WORD(0x70017c);memcpy(expected,(void *)0x9373dc,1000);
        pool();stream[0]=(uint)contents;stream[1]=at;restore(0x700000,stream);
        assert(stream[1]==0 && WORD(0x70017c)==head && e2r_memory_equal("restored timers",expected,(void *)0x9373dc,1000));cases++;
    }
    printf("PASS: %u original loader timer-block cases; empty/multiple chains, signed 16-bit deltas and 32-bit tick wrap; resource/menu reconstruction excluded\n",cases);
}
'''
run_fixture(harness,asan=args.asan,keep=args.keep_harness,image=image,
            dependencies=('original loader timer block with explicit established stream/actor adapter',
                          'original binary CRT byte refill intercepted; resource/menu restoration excluded'))
