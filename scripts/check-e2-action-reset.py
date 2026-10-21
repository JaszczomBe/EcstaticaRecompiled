#!/usr/bin/env python3
"""Compare action reset's retained slot/actor and event order with original i386.

Nested event fixtures deliberately clear the reconstruction's hidden actor
context. Original instruction bytes stay in a temporary harness. Requires
E2WIN95.EXE, clang -m32 support and Linux/i386 execution.
"""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--asan', action='store_true')
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
count = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]
original = None
for i in range(count):
    at = header + 24 + optional + i * 40
    _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
    va += 0x400000
    if va <= 0x42b004 < 0x42b071 <= va + size:
        original = pe[raw + 0x42b004 - va:raw + 0x42b071 - va]
assert original is not None
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
function = re.search(r'^void FUN_0042b004\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
assert function
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <assert.h>
typedef uint16_t ushort,undefined2;
typedef uint8_t byte;
static int E2R_actor_calc_context, E2R_action_event_context, _DAT_0073cc3c;
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
static void E2R_GameStateLog(const char *format,...) { (void)format; }
struct Event { int action,event,actor; };
static struct Event events[8];
static int event_count, pose_actor;
void record(int action,int event,int actor) {
    assert(event_count<8);
    events[event_count++]=(struct Event){action,event,actor};
}
short *FUN_0042b880(int action,short *actor) {
    record(action,E2R_action_event_context,(int)actor);
    E2R_actor_calc_context=0; // real nested event helpers clear this context
    return NULL;
}
static void FUN_0042b0f4(void) { pose_actor=E2R_actor_calc_context; }
__attribute__((naked)) void event_hook(void) {
    __asm__("pushal; push %edx; push %eax; push %ecx; call record; add $12,%esp; popal; ret");
}
__attribute__((naked)) void pose_hook(void) {
    __asm__("mov %eax,pose_actor; ret");
}
'''
harness += function.group() + '\n'
harness += 'static const unsigned char original[]={' + ','.join(map(str, original)) + '};\n'
harness += r'''
static void map(int address,int size,int exec) {
    assert(mmap((void*)address,size,PROT_READ|PROT_WRITE|(exec?PROT_EXEC:0),
                MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void hook(int address,void (*fn)(void)) {
    *(byte*)address=0xe9; *(int32_t*)(address+1)=(intptr_t)fn-address-5;
}
static void run_original(int *slot,short *actor) {
    __asm__ volatile("call *%%edi" : "+a"(slot), "+d"(actor) : "D"(0x42b004) : "memory","cc");
}
int main(void) {
    map(0x420000,0x10000,1); map(0x900000,0x4000,0);
    memcpy((void*)0x42b004,original,sizeof original);
    hook(0x42b880,event_hook); hook(0x42b0f4,pose_hook);
    unsigned cases=0;
    for(int keys=0;keys<=3;keys++) for(int per_key=0;per_key<=2;per_key++)
    for(int pose=0;pose<2;pose++) for(int offset=0;offset<4;offset++) {
        memset((void*)0x900000,0,0x4000);
        int *slot=(int*)0x900000; int action=0x900100, first=keys?0x900200:0;
        short *actor=(short*)(0x901000+offset*0x200);
        slot[0]=action; slot[2]=first; *(ushort*)((byte*)slot+6)=999;
        *(int*)(action+4)=first; *(byte*)(action+0xc)=pose?4:0;
        for(int k=0;k<keys;k++) {
            int key=0x900200+k*0x40;
            *(ushort*)key=k;
            *(int*)(key+2)=k+1<keys?key+0x40:0;
            *(int*)(key+6)=per_key?0x900400+k*0x80:0;
            for(int e=0;e<per_key;e++) {
                int event=0x900400+k*0x80+e*0x20;
                *(int*)(event+10)=e+1<per_key?event+0x20:0;
            }
        }
        int before[5]; memcpy(before,slot,sizeof before);
        memset(events,0,sizeof events); event_count=0; pose_actor=0;
        run_original(slot,actor);
        struct Event expected[8]; memcpy(expected,events,sizeof expected);
        int expected_count=event_count, expected_pose=pose_actor, expected_slot[5];
        memcpy(expected_slot,slot,sizeof expected_slot); memcpy(slot,before,sizeof before);
        memset(events,0,sizeof events); event_count=0; pose_actor=0;
        E2R_actor_calc_context=0x12345678;
        FUN_0042b004(slot,actor);
        assert(event_count==expected_count && pose_actor==expected_pose);
        assert(!memcmp(events,expected,sizeof events) && !memcmp(slot,expected_slot,sizeof expected_slot));
        assert(E2R_actor_calc_context==0x12345678 && E2R_action_event_context==0);
        cases++;
    }
    printf("PASS: %u original-x86 action-reset order/slot/actor cases with nested context clobber\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-action-reset-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', *flags,
                    str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=20)
