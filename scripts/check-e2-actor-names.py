#!/usr/bin/env python3
"""Compare actor-name byte bounds, lookup and slot ownership with original x86.

The installed name directory stays external. Original strcmp is intercepted with
libc while preserving the original register contract. Scene/script execution is
outside this fixture.
"""
import argparse
import re
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
for group in range(2):
    begin = cursor
    names = []
    while data[cursor]:
        end = data.index(0, cursor)
        names.append(data[cursor:end])
        cursor = end + 1
    cursor += 1
actor_pool = data[begin:cursor]
assert names[0] == b'Joe' and len(names) == 4120
assert 10000 < len(actor_pool) < 40000
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
static char *_DAT_006366b4,*_DAT_00636698,*_DAT_006366b8;
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
__attribute__((naked)) static void compare_hook(void) {
    __asm__("pushal; push %edx; push %eax; call strcmp; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
'''+support()
for name in ('E2R_InternPackedName', 'E2R_FindPackedNameIndex', 'FUN_004418fc'):
    harness += function(source, name)+'\n'
# The generated helper retains unreachable historical decompilation below its return.
entry = function(source, 'FUN_004466c4')
harness += entry.split('\n  local_1c = 0;', 1)[0]+'\n}\n'
for label, start, end in [('intern', 0x4466c4, 0x44679c), ('lookup', 0x4418fc, 0x441958)]:
    code = image.code(start, end)
    harness += f'static const byte {label}_code[]={{'+','.join(map(str, code))+'};\n'
harness += 'static const char names[]={' + ','.join(str(v) for v in actor_pool) + '};\n'
literal_helper = function(source, 'E2R_MirrorStartupActorNames')
assert 'E2R_MirrorStartupActorNames();' in function(source, 'E2R_MirrorStartupPartNames')
literal_cases = re.findall(r'\{0x([0-9a-f]+),"([^"\n]+)"\}', literal_helper)
assert len(literal_cases) == 108
harness += literal_helper+'\n'
harness += 'static void check_startup_literals(void) { char expected[0x10000]; memset(expected,0xa5,sizeof expected); memset((void*)0x470000,0xa5,sizeof expected);\n'
for address, name in literal_cases:
    address = int(address, 16)
    raw = image.code(address, address + len(name) + 1)
    assert raw == name.encode('ascii') + b'\0'
    harness += '{ static const byte expected_name[]={' + ','.join(map(str, raw)) + '};'
    harness += f'memcpy(expected+{address - 0x470000},expected_name,sizeof expected_name);'+'}\n'
harness += 'E2R_MirrorStartupActorNames(); assert(!memcmp((void*)0x470000,expected,sizeof expected)); E2R_MirrorStartupActorNames(); assert(!memcmp((void*)0x470000,expected,sizeof expected)); }\n'

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
    map(0x630000,0x10000); map(0x900000,0x10000);
    map(0x470000,0x10000); check_startup_literals();
    _DAT_006366b4=(char*)0x900000;
    *(uint*)0x6366b4=(uint)_DAT_006366b4;
    memcpy((void*)0x4466c4,intern_code,sizeof intern_code);
    memcpy((void*)0x4418fc,lookup_code,sizeof lookup_code);
    *(byte*)0x45fae0=0xe9;
    *(int32_t*)0x45fae1=(intptr_t)compare_hook-0x45fae5;
    char before[40000],expected[40000];
    unsigned count=0,late=0;
    for(const char *name=names;*name;name+=strlen(name)+1) {
        memcpy(before,_DAT_006366b4,sizeof before);
        *(uint*)(0x630b60+count*4)=0x12345678;
        short result=original(0x4466c4,name);
        assert(result==count && *(uint*)(0x630b60+count*4)==0);
        memcpy(expected,_DAT_006366b4,sizeof expected);
        memcpy(_DAT_006366b4,before,sizeof before);
        *(uint*)(0x630b60+count*4)=0x12345678;
        short actual=(short)FUN_004466c4((uint)name,0x87654321);
        if(actual!=result) { fprintf(stderr,"Actor %u (%s): native %d, original %d\n",count,name,actual,result);return 1; }
        assert(!memcmp(expected,_DAT_006366b4,sizeof expected));
        assert(*(uint*)(0x630b60+count*4)==0);
        // Reusing names must preserve existing actors and the surrounding pool.
        *(uint*)(0x630b60+count*4)=0x12345678;
        assert((short)FUN_004466c4((uint)name,0)==count);
        assert(*(uint*)(0x630b60+count*4)==0x12345678);
        assert(!memcmp(expected,_DAT_006366b4,sizeof expected));
        assert(original(0x4418fc,name)==(short)FUN_004418fc((uint)name,0));
        if(name-names>=10000)late++;
        count++;
    }
    assert(count==4120 && late>0);
    assert(original(0x4418fc,"absent-actor")==-1);
    assert((short)FUN_004418fc((uint)"absent-actor",0)==-1);
    printf("PASS: %u installed original-x86 actor-name append/lookup/reuse cases (%u beyond byte 10000), pool memory, actor-slot ownership and 108 original startup literals\n",count,late);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('strcmp register bridge', 'external installed actor-name directory'))
