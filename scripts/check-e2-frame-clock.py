#!/usr/bin/env python3
"""Compare the frame clock wait and elapsed-tick bookkeeping with original i386.

The clock leaf is scripted, including more than 65536 unchanged polls.
No real-time cadence or full runtime acceptance is inferred.
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
source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
a=source.index('  iVar7 = _DAT_0063737c;',source.index('undefined8 __fastcall FUN_0042a70c('))
b=source.index('  E2R_TraceFrameStage("42a70c.before-debug-fps");',a)
fragment=source[a:b]
harness=r"""
#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;
static int _DAT_0063737c,_DAT_00637374,_DAT_006365a4,_DAT_00636588,_DAT_00637378,DAT_0047ab20;
static short DAT_0047a428,DAT_0047a788;
static int _DAT_00640194;
static int polls,unchanged,start_tick,new_tick;
static void E2R_TraceFrameStage(const char *stage) { }
__attribute__((used,noinline)) static uint clock_value(void) {
    assert(polls<=unchanged+1);return polls++<unchanged?start_tick:new_tick;
}
__attribute__((naked)) static void clock_hook(void) {
    __asm__("pushal; call clock_value; mov %eax,28(%esp); popal; ret");
}
static undefined8 FUN_0041cf5c(uint unused,uint retained) {return clock_value();}
static void native(void) {
    int iVar7;uint param_1=0,uVar13,uVar4;undefined8 uVar14;
"""+fragment+r"""
}
static void original(void) {
    __asm__ volatile("pushal; mov $0x42a720,%%eax; call *%%eax; popal" : : : "memory","cc");
}
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void setup(int slowdown,int reload,int delay,int delta,int pending) {
    polls=0;unchanged=delay;start_tick=12345;new_tick=start_tick+delta;
    _DAT_0063737c=*(int*)0x63737c=start_tick;
    _DAT_00637374=*(int*)0x637374=100;
    _DAT_006365a4=*(int*)0x6365a4=slowdown;
    _DAT_00636588=*(int*)0x636588=1000;
    _DAT_00637378=*(int*)0x637378=0xcccc;
    DAT_0047ab20=*(int*)0x47ab20=pending;
    DAT_0047a788=*(short*)0x47a788=reload;
    DAT_0047a428=*(short*)0x47a428=7;
}
"""
harness+='static const unsigned char original_code[]={'+','.join(map(str,original(0x42a720,0x42a7d2)))+'};\n'
harness+=r"""
int main(void) {
    map(0x410000,0x20000);map(0x470000,0x10000);map(0x630000,0x10000);
    memcpy((void*)0x42a720,original_code,sizeof original_code);*(char*)0x42a7d2=0xc3;
    *(char*)0x41cf5c=0xe9;*(int*)0x41cf5d=(int)clock_hook-0x41cf61;
    int delays[]={0,1,16,65535,65536,65537,100000},deltas[]={1,2,3,20},pending[]={0,1,3,20,-1};
    unsigned cases=0;
    for(int slow=0;slow<2;slow++)for(int load=0;load<2;load++)for(int wait=0;wait<7;wait++)
    for(int step=0;step<4;step++)for(int p=0;p<5;p++) {
        setup(slow,load,delays[wait],deltas[step],pending[p]);original();
        int ep=polls,et=*(int*)0x637378,ec=*(int*)0x63737c,elapsed=*(int*)0x636588,request=*(int*)0x47ab20;
        setup(slow,load,delays[wait],deltas[step],pending[p]);native();
        assert(polls==ep&&polls==delays[wait]+1&&_DAT_0063737c==ec&&_DAT_00637378==et);
        assert(_DAT_00636588==elapsed&&DAT_0047ab20==request&&DAT_0047a788==0&&DAT_0047a428==0&&_DAT_00637374==0);
        if(!load)assert(_DAT_00637378>0);cases++;
    }
    printf("PASS: %u original-i386 clock wait/tick/reload/slowdown cases, through 100000 unchanged polls\n",cases);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-frame-clock-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    if args.keep_harness:args.keep_harness.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=30)
