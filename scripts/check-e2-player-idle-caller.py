#!/usr/bin/env python3
"""Compare queued/random idle and landing-action selection with original i386.

The loader is intercepted; compare its ID, table result and untouched actor bytes.
Includes absent idle slots and landing callers that formerly lost their action ID.
"""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 60)[0]
sections = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]
def original(start, end):
    for i in range(sections):
        at = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(start)
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
start = source.index('    else {\n      FUN_00451880(', source.index('27584.check-before-default-51880'))
end = source.index('\n    if (iVar17 == 0)', start)
branch = source[start:end].removeprefix('    else {').removesuffix('\n    }')
default_start = source.index('      iVar17 = 0;\n', source.index('if (local_6c[0xb1] < 0)'))
default_end = source.index('    }\n    else {', default_start)
default_branch = source[default_start:default_end]
landing_start = source.index('    if (-1 < iVar3) {', source.index('undefined4 __fastcall FUN_00449680('))
landing_end = source.index('    *(undefined2 *)(iVar5 + 0x5a)', landing_start)
landing_branch = source[landing_start:landing_end]
harness = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;
typedef uint16_t ushort;
typedef uint8_t undefined1;
static int captured_id,calls;
static uint queued_actor,queued_action,queued_calls;
__attribute__((used,noinline)) static void FUN_0045186c(uint actor,uint action,int immediate) {
    assert(!immediate);queued_actor=actor;queued_action=action;queued_calls++;
}
__attribute__((naked)) static void queue_hook(void) {
    __asm__("pushal; push %ebx; push %edx; push %eax; call FUN_0045186c; add $12,%esp; popal; ret");
}
static volatile int random_input __attribute__((used));
static undefined8 FUN_0045fc10(uint unused,int unused2) { return random_input; }
#define E2R_TraceActorUpdateExit(...) ((void)0)
__attribute__((naked)) static void random_hook(void) { __asm__("mov random_input,%eax; ret"); }
__attribute__((used)) static volatile int original_action;
__attribute__((used,noinline)) static undefined8 FUN_00451880(uint unused,int id) {
    captured_id=id;calls++;return (uint64_t)(uint)id<<32;
}
__attribute__((naked)) static void loader_hook(void) {
    __asm__("pushal; push %eax; push $0; call FUN_00451880; add $8,%esp; popal; ret");
}
__attribute__((naked)) static void run_original(void *frame) {
    __asm__("pushal; mov 36(%esp),%ebp; mov $0x429bcc,%edi; call *%edi; "
            "mov %ecx,original_action; popal; ret");
}
static int native(short *local_6c,uint uVar25,int iVar7) {
    int iVar17;
""" + branch + r"""
    return iVar17;
}
static int native_default(short *local_6c) {
    int iVar17,iVar7=0,extraout_ECX_44=0x12345678;
    uint uVar19=1000,uVar25;undefined8 uVar27;
""" + default_branch + r"""
    return iVar17;
}
__attribute__((naked)) static void run_default_original(void *frame) {
    __asm__("pushal; mov 36(%esp),%ebp; mov 0x2a(%ebp),%eax; mov $0x429bf2,%edi; call *%edi; "
            "mov %ecx,original_action; popal; ret");
}
static void native_landing(int in_EAX,int iVar3,int iVar4) {
    int iVar5=in_EAX;
""" + landing_branch + r"""
}
static void original_landing(int actor,int id,int poison) {
    __asm__ volatile("call *%%edi" : "+c"(actor),"+b"(id),"+d"(poison) : "D"(0x449847) : "eax","memory","cc");
}
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
"""
harness += 'static const unsigned char original_code[]={' + ','.join(map(str, original(0x429bcc,0x429bed))) + '};\n'
harness += 'static const unsigned char default_code[]={' + ','.join(map(str, original(0x429bf2,0x429ca3))) + '};\n'
harness += 'static const unsigned char landing_code[]={' + ','.join(map(str, original(0x449847,0x449866))) + '};\n'
harness += r"""
int main(void) {
    map(0x420000,0x10000);map(0x440000,0x20000);
    map(0x620000,0x50000);map(0x900000,0x10000);
    memcpy((void*)0x429bcc,original_code,sizeof original_code);*(char*)0x429bed=0xc3;
    *(char*)0x451880=0xe9;*(int*)0x451881=(int)loader_hook-0x451885;
    memcpy((void*)0x429bf2,default_code,sizeof default_code);*(char*)0x429ca3=0xc3;
    *(char*)0x45fc10=0xe9;*(int*)0x45fc11=(int)random_hook-0x45fc15;
    memcpy((void*)0x449847,landing_code,sizeof landing_code);*(char*)0x449866=0xc3;
    *(char*)0x45186c=0xe9;*(int*)0x45186d=(int)queue_hook-0x451871;
    int ids[]={0,3,4,8,11,13,338,871,1999,32767};
    uint poisons[]={0,1,0x80,0xffff,0xeeb96008,0xdeadbeef};
    unsigned cases=0;
    for(int owner=0;owner<3;owner++)for(int id=0;id<10;id++)
    for(int p=0;p<6;p++)for(int neighbor=0;neighbor<4;neighbor++)for(int loaded=0;loaded<2;loaded++) {
        int actor=0x900000+owner*0x200;
        memset((void*)actor,0xa5,0x200);
        *(short*)(actor+0x160)=(short)(neighbor*7919);
        *(short*)(actor+0x162)=ids[id];
        *(uint*)(actor+0x11e)=poisons[p];
        *(int*)0x90402a=actor;
        *(int*)(0x62ba20+ids[id]*4)=loaded?0x905000+ids[id]*2:0;
        unsigned char saved[0x200];memcpy(saved,(void*)actor,sizeof saved);
        calls=0;captured_id=-1;original_action=-1;
        run_original((void*)0x904000);
        int expected_id=captured_id,expected_calls=calls,expected_action=original_action;
        calls=0;captured_id=-1;
        int action=native((short*)actor,poisons[p],poisons[p]);
        assert(captured_id==expected_id && captured_id==ids[id]);
        assert(calls==expected_calls && calls==1 && action==expected_action);
        assert(!memcmp(saved,(void*)actor,sizeof saved));cases++;
    }
    printf("PASS: %u original-i386 queued idle-action ID/table/actor cases (loader intercepted)\n",cases);
    cases=0;
    for(int rep=0;rep<2;rep++)for(int slot=0;slot<3;slot++)
    for(int last=0;last<6;last++)for(int random=0;random<32768;random+=257) {
        int actor=0x900000,representation=0x906000;
        memset((void*)actor,0,0x200);memset((void*)representation,0,0x100);
        *(int*)(actor+0x11e)=rep?representation:0;
        *(short*)(actor+0x168)=last;
        for(int j=0;j<6;j++) *(short*)(representation+0x26+j*2)=slot==0?-1:338+j;
        for(int j=0;j<6;j++) *(int*)(0x62ba20+(338+j)*4)=slot==2?0x908000+j*32:0;
        *(int*)0x90402a=actor;random_input=random;
        calls=0;captured_id=-1;run_default_original((void*)0x904000);
        int expected_action=original_action,expected_id=captured_id,expected_calls=calls;
        short category=*(short*)(actor+0x168);*(short*)(actor+0x168)=last;
        calls=0;captured_id=-1;
        assert(native_default((short*)actor)==expected_action);
        assert(*(short*)(actor+0x168)==category);
        assert(captured_id==expected_id && calls==expected_calls);cases++;
    }
    printf("PASS: %u original-i386 random idle-action absent/present slot cases\n",cases);
    cases=0;
    for(int id=-1;id<512;id+=8)for(int loaded=0;loaded<2;loaded++)for(int poison=0;poison<6;poison++) {
        if(id>=0)*(int*)(0x62ba20+id*4)=loaded?0x908000:0;
        calls=queued_calls=0;captured_id=-1;queued_actor=queued_action=0;
        original_landing(0x900000,id,poisons[poison]);
        int expected_id=captured_id,expected_calls=calls;
        uint owner=queued_actor,action=queued_action,queues=queued_calls;
        calls=queued_calls=0;captured_id=-1;queued_actor=queued_action=0;
        native_landing(0x900000,id,poisons[poison]);
        assert(captured_id==expected_id && calls==expected_calls);
        assert(queued_actor==owner && queued_action==action && queued_calls==queues);cases++;
    }
    printf("PASS: %u original-i386 landing-action loader/queue argument cases\n",cases);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-player-idle-caller-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    if args.keep_harness:args.keep_harness.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=20)
