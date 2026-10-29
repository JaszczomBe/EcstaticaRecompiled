#!/usr/bin/env python3
"""Compare original combat damage scaling, including its zero-power SIGFPE.

This extracts the production health-write branch. Collision, attacker damage
calculation, sounds and scripts are outside the fixture; no save is modified.
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
production = function(Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text(),
                      'FUN_0042efdc')
start = production.index('          iVar5 = (*(int *)0x0047ab28);')
end = production.index('\n        }\n        else if ', start)
branch = production[start:end]
harness = support() + r'''
#include <assert.h>
#include <signal.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
typedef unsigned short ushort;
typedef unsigned uint,undefined4;
#define DAT_0047a470 (*(ushort**)0x47a470)
#define DAT_0047a4a4 (*(int*)0x47a4a4)
const char *__asan_default_options(void) {
    return "detect_leaks=0:handle_sigfpe=0";
}
static void native_damage(ushort *puVar3,int iVar6) {
    int iVar5,iVar7;
''' + branch + '\n}\n'
code = image.code(0x42f396, 0x42f429)
harness += 'static const unsigned char code[]={' + ','.join(map(str, code)) + '};\n'
harness += r'''
static void map(unsigned at,unsigned bytes) {
    assert(mmap((void*)at,bytes,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,
                -1,0)==(void*)at);
}
static void original_damage(ushort *target,int damage) {
    struct E2R_Registers regs={.ebx=(unsigned)damage,.esi=(unsigned)target};
    e2r_original_call(0x42f396,&regs);
}
static void setup(ushort *target,int health,int power,int difficulty) {
    memset((void*)0x900000,0,0x2000);
    DAT_0047a470=(ushort*)0x900000;
    DAT_0047a4a4=difficulty;
    *(int*)0x47ab28=power;
    target[0x76]=health;
}
static void zero_power(int native,int difficulty,int damage) {
    pid_t child=fork();
    assert(child>=0);
    if(!child) {
        struct rlimit limit={0,0};
        assert(!setrlimit(RLIMIT_CORE,&limit));
        signal(SIGFPE,SIG_DFL);
        alarm(2);
        setup((ushort*)0x900000,53,0,difficulty);
        if(native)native_damage((ushort*)0x900000,damage);
        else original_damage((ushort*)0x900000,damage);
        _exit(91);
    }
    int status;
    assert(waitpid(child,&status,0)==child);
    assert(WIFSIGNALED(status)&&WTERMSIG(status)==SIGFPE);
}
int main(void) {
    map(0x420000,0x10000);map(0x470000,0x10000);map(0x900000,0x2000);
    memcpy((void*)0x42f396,code,sizeof code);
    /* Intercept only the continuation after the original health write. */
    *(unsigned char*)0x42f429=0xc3;
    int health[]={1,53,100,171,30000,-200};
    int damage[]={-37,0,1,2,10,40,201};
    int fault_damage[]={2,10};
    int power[]={50,100,150,200,-100,32767,0};
    int difficulty[]={0,1,2,9};
    unsigned char expected[0x2000];unsigned cases=0;
    for(unsigned who=0;who<2;who++)for(unsigned h=0;h<6;h++)
    for(unsigned d=0;d<7;d++)for(unsigned p=0;p<7;p++)
    for(unsigned level=0;level<4;level++) {
        if(!who&&!power[p])continue;
        ushort *target=(ushort*)(0x900000+who*0x1000);
        setup(target,health[h],power[p],difficulty[level]);
        original_damage(target,damage[d]);memcpy(expected,(void*)0x900000,sizeof expected);
        setup(target,health[h],power[p],difficulty[level]);
        native_damage(target,damage[d]);
        assert(e2r_memory_equal("combat power",expected,(void*)0x900000,sizeof expected));
        cases++;
    }
    for(unsigned level=0;level<4;level++)for(unsigned hit=0;hit<2;hit++) {
        zero_power(0,difficulty[level],fault_damage[hit]);
        zero_power(1,difficulty[level],fault_damage[hit]);
    }
    printf("PASS: %u original-x86 combat-power health writes; "
           "16 original/native zero-power SIGFPE cases (no guard or save repair)\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('Original branch continuation intercepted with ret at 0x42f429',
                          'Mapped player/target, power and difficulty; supplied attacker damage',
                          'Collision, sound, script dispatch and persistence not executed'))
