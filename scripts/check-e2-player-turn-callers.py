#!/usr/bin/env python3
"""Compare the two player forward/turn caller contracts with original i386.

The turn leaf is intercepted to compare actor and signed angle arguments. Actual
turn matrices are covered by check-e2-motion-query.py. This is not gameplay proof.
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
calls = re.findall(r'FUN_0042b074\([^;]*local_6c \+ 0xb7[^;]*\);', source)
assert len(calls) == 2, 'Expected exactly two forward/turn calls'
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
static uint captured_actor;
static short captured_angle;
__attribute__((used,noinline)) static void FUN_0042b074(uint actor,short angle) {
    captured_actor=actor;captured_angle=angle;
}
__attribute__((naked)) static void turn_hook(void) {
    __asm__("pushal; push %edx; push %eax; call FUN_0042b074; add $8,%esp; popal; ret");
}
__attribute__((naked)) static void run_original(int address,void *frame) {
    __asm__("pushal; mov 36(%esp),%edi; mov 40(%esp),%ebp; call *%edi; popal; ret");
}
'''
for direction, call in enumerate(calls):
    harness += f'static void native_{direction}(short *local_6c,uint uVar25) {{\n{call}\n}}\n'
for start,end in ((0x42967b,0x429692),(0x429645,0x42965e)):
    harness += f'static const unsigned char code_{start:x}[]={{'+','.join(map(str,original(start,end)))+'};\n'
harness += r'''
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
int main(void) {
    map(0x420000,0x10000);map(0x900000,0x10000);
    memcpy((void*)0x42967b,code_42967b,sizeof code_42967b);*(char*)0x429692=0xc3;
    memcpy((void*)0x429645,code_429645,sizeof code_429645);*(char*)0x42965e=0xc3;
    *(char*)0x42b074=0xe9;*(int*)0x42b075=(int)turn_hook-0x42b079;
    short rates[]={-32768,-32767,-2049,-1,0,1,16,2048,32767};
    uint poisons[]={0,1,0x80,0xff,0xffff,0xdeadbeef};
    unsigned cases=0;
    for(int direction=0;direction<2;direction++)for(int owner=0;owner<3;owner++)
    for(int r=0;r<9;r++)for(int p=0;p<6;p++)for(int low=0;low<4;low++) {
        int actor=0x900000+owner*0x200;
        *(short*)(actor+0x170)=rates[r];
        *(short*)(actor+0x16e)=(short)(low*7919); // unrelated neighboring word
        *(int*)0x90402a=actor;
        captured_actor=0;captured_angle=0;
        run_original(direction?0x429645:0x42967b,(void*)0x904000);
        uint expected_actor=captured_actor;short expected_angle=captured_angle;
        if(direction)native_1((short*)actor,poisons[p]);else native_0((short*)actor,poisons[p]);
        assert(expected_actor==(uint)actor);
        if(captured_actor!=expected_actor||captured_angle!=expected_angle) {
            fprintf(stderr,"turn caller mismatch direction=%d actor=%x poison=%x rate=%d expected=%x/%d actual=%x/%d\n",
                direction,actor,poisons[p],rates[r],expected_actor,expected_angle,captured_actor,captured_angle);abort();
        }
        cases++;
    }
    printf("PASS: %u original-i386 forward/turn actor and signed angle caller cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-player-turn-callers-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    if args.keep_harness:args.keep_harness.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=20)
