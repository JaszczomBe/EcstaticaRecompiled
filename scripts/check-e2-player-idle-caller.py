#!/usr/bin/env python3
"""Compare the queued idle-action caller with original i386.

The loader is intercepted; compare its ID, table result and untouched actor bytes.
This isolates the caller that formerly passed a representation pointer on release.
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
harness = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint8_t undefined1;
static int captured_id,calls;
__attribute__((used)) static volatile int original_action;
__attribute__((used,noinline)) static void FUN_00451880(uint unused,int id) {
    captured_id=id;calls++;
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
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
"""
harness += 'static const unsigned char original_code[]={' + ','.join(map(str, original(0x429bcc,0x429bed))) + '};\n'
harness += r"""
int main(void) {
    map(0x420000,0x10000);map(0x450000,0x10000);
    map(0x620000,0x50000);map(0x900000,0x10000);
    memcpy((void*)0x429bcc,original_code,sizeof original_code);*(char*)0x429bed=0xc3;
    *(char*)0x451880=0xe9;*(int*)0x451881=(int)loader_hook-0x451885;
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
}
"""
with tempfile.TemporaryDirectory(prefix='e2-player-idle-caller-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    if args.keep_harness:args.keep_harness.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=20)
