#!/usr/bin/env python3
"""Compare terminal pose events 0x16/0x17 actor ownership with original x86."""
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
dispatch = function(source, 'FUN_0042b880')
branch = dispatch[dispatch.index('  case 0x16:'):dispatch.index('  case 0x18:')]
assert 'return E2R_ApplyActionPose16_17((int)(uintptr_t)param_2,in_EAX);' in branch
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;
static int E2R_actor_calc_context,observed_actor;
static short DAT_0047a34a,DAT_0047a366;
__attribute__((used,noinline)) static uintptr_t pose_leaf(int actor) {
    observed_actor=actor;
    E2R_actor_calc_context=0; /* Nested helpers may discard their hidden context. */
    return 0x12345678;
}
static uintptr_t FUN_0042b0f4(void) { return pose_leaf(E2R_actor_calc_context); }
__attribute__((naked)) static void pose_hook(void) {
    __asm__("pushal; push %eax; call pose_leaf; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
'''
harness += support() + '\n' + function(source, 'E2R_ApplyActionPose16_17') + '\n'
code = image.code(0x42b71c, 0x42c790)
harness += 'static const byte original_code[]={' + ','.join(map(str, code)) + '};\n'
harness += r'''
static void map(unsigned address,unsigned size) {
    assert(mmap((void *)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)address);
}
static void setup(int opcode,int preview,int mode,int seed) {
    memset((void *)0x900000,0x5a,0x5000);
    DAT_0047a34a=*(short *)0x47a34a=preview;
    DAT_0047a366=*(short *)0x47a366=mode;
    *(int *)0x47a7e0=0;
    *(short *)0x903000=0;*(short *)0x903002=opcode;
    for(int i=0;i<3;i++)((short *)0x903004)[i]=(short)(seed*971+i*19727-32768);
    *(int *)0x90300a=0x904000;
    *(int *)(0x900000+0x1e)=0x902000;
    *(int *)(0x902000+0x1e)=1; /* A stale context must never masquerade as this actor. */
    observed_actor=0;
}
int main(void) {
    map(0x420000,0x10000);map(0x470000,0x10000);
    map(0x630000,0x10000);map(0x900000,0x5000);
    memcpy((void *)0x42b71c,original_code,sizeof original_code);
    *(byte *)0x42b0f4=0xe9;*(int32_t *)0x42b0f5=(intptr_t)pose_hook-0x42b0f9;
    unsigned cases=0;
    for(int opcode=0x16;opcode<=0x17;opcode++)for(int preview=0;preview<2;preview++)
    for(int mode=0;mode<3;mode++)for(int seed=0;seed<128;seed++)for(int foreign=0;foreign<2;foreign++) {
        setup(opcode,preview,mode,seed);
        struct E2R_Registers regs={.eax=0x903000,.edx=0x900000,.ebx=0x900000,.ecx=0x904000};
        e2r_original_call(0x42b880,&regs);
        byte expected[0x5000];memcpy(expected,(void *)0x900000,sizeof expected);
        int expected_actor=observed_actor;
        setup(opcode,preview,mode,seed);int context=foreign?0x902000:0;
        E2R_actor_calc_context=context;
        E2R_ApplyActionPose16_17(0x900000,(short *)0x903000);
        assert(expected_actor==0x900000 && observed_actor==expected_actor);
        assert(E2R_actor_calc_context==context);
        assert(e2r_memory_equal("terminal pose coordinates/link/canaries",expected,(void *)0x900000,sizeof expected));
        cases++;
    }
    printf("PASS: %u original-x86 terminal position/rotation events, preview guards, unshifted actor ownership, context restoration and event-link canaries; pose leaf intercepted\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('root-pose leaf intercepted to observe the original EAX actor',
                          'real root matrices/bookkeeping covered by check-e2-root-pose.py'))

