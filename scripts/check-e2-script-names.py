#!/usr/bin/env python3
"""Compare script-name interning beyond 6000 bytes with the original i386 helper.

Also checks production name-cache refresh after appending to the same pool.
Original strcmp's calling convention is intercepted; ASCII comparisons use libc.
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
    if va <= 0x44694c < 0x446a27 <= va + size:
        original = pe[raw + 0x44694c - va:raw + 0x446a27 - va]
assert original is not None
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8;
typedef uint16_t ushort,undefined2;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
static char *_DAT_00636698,*_DAT_006366b4,*_DAT_006366b8;
static char *E2R_action_name_cache[0x4000], *E2R_action_name_cache_base;
static int E2R_action_name_cache_ready;
static int action_probe_enabled = 1;
static int E2R_ActionIndexProbeEnabled(void) { return action_probe_enabled; }
__attribute__((naked)) static void compare_hook(void) {
    __asm__("pushal; push %edx; push %eax; call strcmp; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
'''
for name in ('E2R_InternPackedName', 'E2R_PrimeActionNameCache', 'E2R_ActionNameByIndex'):
    match = re.search(r'^static (?:short|void|char \*)\s*' + name + r'\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
    assert match, name
    harness += match.group() + '\n'
match = re.search(r'^undefined8 __fastcall FUN_0044694c\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
assert match
# This function retains unreachable decompiler output after its recovered return.
prefix = match.group().split('\n  local_1c = 0;', 1)[0] + '\n}\n'
harness += prefix
harness += 'static const unsigned char original[]={' + ','.join(map(str, original)) + '};\n'
harness += r'''
static void map(int address,int n) {
    assert(mmap((void*)address,n,PROT_READ|PROT_WRITE|PROT_EXEC,
                MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static short intern_original(const char *name) {
    uintptr_t result=(uintptr_t)name;
    __asm__ volatile("call *%%edi" : "+a"(result) : "D"(0x44694c) : "memory","cc");
    return (short)result;
}
int main(void) {
    map(0x440000,0x10000); map(0x450000,0x10000);
    map(0x629000,0x3000); map(0x636000,0x1000); map(0x900000,0x6000);
    _DAT_00636698=(char*)0x900000; *(uint32_t*)0x636698=(uintptr_t)_DAT_00636698;
    memcpy((void*)0x44694c,original,sizeof original);
    *(unsigned char*)0x45fae0=0xe9;
    *(int32_t*)0x45fae1=(intptr_t)compare_hook-0x45fae5;
    char text[32];
    for(int i=0;i<900;i++) {
        snprintf(text,sizeof text,"fixture-%04d",i);
        assert(E2R_InternPackedName(text,_DAT_00636698,24000,2000)==i);
    }
    assert(!strcmp(E2R_ActionNameByIndex(899),"fixture-0899"));
    unsigned char before[24000], expected[24000];
    // Preserve the earlier incomplete baseline only outside the explicit route.
    memcpy(before,_DAT_00636698,sizeof before);
    action_probe_enabled=0;
    assert((short)FUN_0044694c((uintptr_t)"outside-baseline-limit",0)==-1);
    assert(!memcmp(before,_DAT_00636698,sizeof before));
    action_probe_enabled=1;
    for(int i=0;i<256;i++) {
        snprintf(text,sizeof text,"fixture-%04d",900+i);
        memcpy(before,_DAT_00636698,sizeof before);
        *(uint32_t*)(0x6297c0+(900+i)*4)=0x12345678;
        short index=intern_original(text);
        assert(*(uint32_t*)(0x6297c0+index*4)==0);
        memcpy(expected,_DAT_00636698,sizeof expected);
        memcpy(_DAT_00636698,before,sizeof before);
        *(uint32_t*)(0x6297c0+index*4)=0x12345678;
        assert((short)FUN_0044694c((uintptr_t)text,0)==index && index==900+i);
        assert(*(uint32_t*)(0x6297c0+index*4)==0);
        assert(!memcmp(expected,_DAT_00636698,sizeof expected));
        assert(!strcmp(E2R_ActionNameByIndex(index),text));
        // Reusing a name must preserve both the index and the packed bytes.
        memcpy(before,_DAT_00636698,sizeof before);
        assert((short)FUN_0044694c((uintptr_t)text,0)==index);
        assert(!memcmp(before,_DAT_00636698,sizeof before));
    }
    puts("PASS: 256 original-x86 script-name appends beyond byte 6000, duplicate lookup and mutable-pool cache refresh; baseline capacity gate");
}
'''
with tempfile.TemporaryDirectory(prefix='e2-script-names-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', *flags,
                    str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=20)
