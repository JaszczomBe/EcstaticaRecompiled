#!/usr/bin/env python3
"""Compare animation/representation names, byte bounds and slot ownership with x86.

The installed name directory stays external. Original strcmp is intercepted with
libc while preserving the original register contract. Scene/script execution is
outside this fixture.
"""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('names', type=Path, help='Installed Code/ECSTATIC.FAN')
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
image = OriginalImage(args.exe)
data = args.names.read_bytes()
cursor = 34
for group in range(8):
    begin = cursor
    names = []
    while data[cursor]:
        end = data.index(0, cursor)
        names.append(data[cursor:end])
        cursor = end + 1
    cursor += 1
    if group == 2:
        animation_pool = data[begin:cursor]
        assert names[0] == b'BulletC' and len(names) == 1800
representation_pool = data[begin:cursor]
assert names[424] == b'w_pot' and len(names) == 488
assert 1000 < len(representation_pool) < 4000
assert 0x1117 < len(animation_pool) < 0x445c
source = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
static char *_DAT_006366b4,*_DAT_00636698,*_DAT_006366b8,*_DAT_0063668c;
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
__attribute__((naked)) static void compare_hook(void) {
    __asm__("pushal; push %edx; push %eax; call strcmp; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
'''+support()
for name in ('E2R_InternPackedName', 'E2R_FindPackedNameIndex', 'FUN_00441ac8'):
    harness += function(source, name)+'\n'
# The generated helper retains unreachable historical decompilation below its return.
entry = function(source, 'FUN_0044679c')
harness += entry.split('\n  local_1c = 0;', 1)[0]+'\n}\n'
harness += function(source, 'FUN_00441a10')+'\n'
entry = function(source, 'FUN_00446a24')
harness += entry.split('\n  local_1c = 0;', 1)[0]+'\n}\n'
for label, start, end in [('rep_intern', 0x446a24, 0x446afc), ('rep_lookup', 0x441a10, 0x441a69), ('intern', 0x44679c, 0x446874), ('lookup', 0x441ac8, 0x441b24)]:
    code = image.code(start, end)
    harness += f'static const byte {label}_code[]={{'+','.join(map(str, code))+'};\n'
harness += 'static const char names[]={' + ','.join(str(v) for v in animation_pool) + '};\n'
harness += 'static const char rep_names[]={' + ','.join(str(v) for v in representation_pool) + '};\n'
harness += r'''
static void map(uint address,unsigned size) {
    assert(mmap((void*)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)address);
}
static short original(uint fn,const char *name) {
    uintptr_t result=(uintptr_t)name;
    __asm__ volatile("call *%%edi" : "+a"(result) : "D"(fn) : "memory","cc");
    return (short)result;
}
int main(void) {
    map(0x440000,0x10000); map(0x450000,0x10000);
    map(0x630000,0x10000); map(0x620000,0x10000); map(0x900000,0x10000);
    _DAT_006366b8=(char*)0x900000;
    *(uint*)0x6366b8=(uint)_DAT_006366b8;
    memcpy((void*)0x44679c,intern_code,sizeof intern_code);
    memcpy((void*)0x441ac8,lookup_code,sizeof lookup_code);
    *(byte*)0x45fae0=0xe9;
    *(int32_t*)0x45fae1=(intptr_t)compare_hook-0x45fae5;
    char before[0x445c],expected[0x445c];
    unsigned count=0,late=0;
    for(const char *name=names;*name;name+=strlen(name)+1) {
        memcpy(before,_DAT_006366b8,sizeof before);
        *(uint*)(0x62ba20+count*4)=0x12345678;
        short result=original(0x44679c,name);
        assert(result==count && *(uint*)(0x62ba20+count*4)==0);
        memcpy(expected,_DAT_006366b8,sizeof expected);
        memcpy(_DAT_006366b8,before,sizeof before);
        *(uint*)(0x62ba20+count*4)=0x12345678;
        short actual=(short)FUN_0044679c((uint)name,0x87654321);
        if(actual!=result) { fprintf(stderr,"Animation %u (%s): native %d, original %d\n",count,name,actual,result);return 1; }
        assert(!memcmp(expected,_DAT_006366b8,sizeof expected));
        assert(*(uint*)(0x62ba20+count*4)==0);
        // Reusing names must preserve loaded animations and the surrounding pool.
        *(uint*)(0x62ba20+count*4)=0x12345678;
        assert((short)FUN_0044679c((uint)name,0)==count);
        assert(*(uint*)(0x62ba20+count*4)==0x12345678);
        assert(!memcmp(expected,_DAT_006366b8,sizeof expected));
        assert(original(0x441ac8,name)==(short)FUN_00441ac8((uint)name,0));
        if(name-names>=0x1117)late++;
        count++;
    }
    assert(count==1800 && late>0);
    assert(original(0x441ac8,"absent-animation")==-1);
    assert((short)FUN_00441ac8((uint)"absent-animation",0)==-1);
    printf("PASS: %u installed original-x86 animation-name append/lookup/reuse cases (%u beyond byte 0x1117), pool memory and animation-slot ownership\n",count,late);

    _DAT_0063668c=(char*)0x905000;*(uint*)0x63668c=(uint)_DAT_0063668c;
    memcpy((void*)0x446a24,rep_intern_code,sizeof rep_intern_code);
    memcpy((void*)0x441a10,rep_lookup_code,sizeof rep_lookup_code);
    count=late=0;
    for(const char *name=rep_names;*name;name+=strlen(name)+1) {
        memcpy(before,_DAT_0063668c,4000);
        *(uint*)(0x635980+count*4)=0x12345678;
        short result=original(0x446a24,name);
        assert(result==count && *(uint*)(0x635980+count*4)==0);
        memcpy(expected,_DAT_0063668c,4000);memcpy(_DAT_0063668c,before,4000);
        *(uint*)(0x635980+count*4)=0x12345678;
        short actual=(short)FUN_00446a24((uint)name,0);
        if(actual!=result) { fprintf(stderr,"Representation %u (%s): native %d, original %d\n",count,name,actual,result);return 1; }
        assert(!memcmp(expected,_DAT_0063668c,4000));
        assert(*(uint*)(0x635980+count*4)==0);
        *(uint*)(0x635980+count*4)=0x12345678;
        assert((short)FUN_00446a24((uint)name,0)==count);
        assert(*(uint*)(0x635980+count*4)==0x12345678);
        assert(!memcmp(expected,_DAT_0063668c,4000));
        assert(original(0x441a10,name)==(short)FUN_00441a10((uint)name,0));
        if(name-rep_names>=1000)late++;
        count++;
    }
    assert(count==488 && (short)FUN_00441a10((uint)"w_pot",0)==424);
    printf("PASS: %u installed original-x86 representation-name append/lookup/reuse cases (%u beyond byte 1000), including dropped w_pot and slot ownership\n",count,late);

}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('strcmp register bridge', 'external installed animation/representation-name directories'))
