#!/usr/bin/env python3
"""Compare the FAN-55 floor-entry decoder with original i386 instructions.

Exercises every byte value, including embedded CR/0x1a, with a real high-address
hosted stream. Byte/word file services are intercepted in binary mode; this is
not coverage of the full FAN parser, CRT text mode or gameplay.
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
for i in range(count):
    at = header + 24 + optional + i * 40
    _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
    va += 0x400000
    if va <= 0x4476e6 < 0x4479de <= va + size:
        original = pe[raw + 0x4476e6 - va:raw + 0x4479de - va]
        break
else:
    raise ValueError('Original floor decoder not found')
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()

def function(name):
    # Start at the declaration, avoiding preceding unrelated text.
    start = source.rfind('\n', 0, source.index(name+'(', source.index('/* '+name[4:]+' */')))
    end = source.index('\n}', start)+2
    return source[start+1:end]

floor_start = source.index('void __fastcall FUN_00447638(')
body = source[floor_start:source.index('\n}', floor_start)+2]
declarations = body[body.index('{')+1:body.index('  in_EAX =')]
start = body.index('  iVar14 = 0;\n  e2r_entry_start = E2R_FanStreamOffset();')
end = body.index('  if (E2R_fan_parse_stream !=', start)
loop = body[start:end]
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort,undefined2;
typedef int16_t short_alias;
typedef uint8_t byte,undefined1;
typedef uint32_t uint3;
typedef uint64_t undefined8,ulonglong;
typedef int32_t int3;
typedef void code(void);
#define __fastcall
#define E2R_STREAM_MAGIC 0xe25eed01u
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define CONCAT22(a,b) (((uint32_t)(uint16_t)(a)<<16)|(uint16_t)(b))
#define CONCAT31(a,b) (((uint32_t)(a)<<8)|(uint8_t)(b))
#define CONCAT11(a,b) (((uint16_t)(uint8_t)(a)<<8)|(uint8_t)(b))
#define PTR_FUN_0047d3a0 noop
#define PTR_FUN_0047d3a4 noop
#define FUN_0046055c(...) assert(0)
#define FUN_0045f428(...) ((uint64_t)0)
static void noop(void) { assert(0); }
static int *E2R_fan_parse_stream;
static unsigned E2R_fan_phase_diag_count=100;
static int DAT_0047a77c,_DAT_0067bc92,_DAT_00ac4ae8,_DAT_00ac4af0;
static int IsBadReadPtr(const void *p,unsigned size) { return (uintptr_t)p<0x10000u; }
static int E2R_ActionIndexProbeEnabled(void) { return 1; }
static uint E2R_FanStreamOffset(void) { return E2R_fan_parse_stream[0]-E2R_fan_parse_stream[5]; }
'''
harness += re.search(r'static int E2R_ReadHostedStreamByte\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S).group()+'\n'
harness += function('FUN_0045f38a')+'\n'
harness += r'''
static uint raw_word(int *stream) {
    uint a=E2R_ReadHostedStreamByte((undefined4*)stream);
    uint b=E2R_ReadHostedStreamByte((undefined4*)stream);
    return (a&255)|((b&255)<<8);
}
static undefined8 FUN_004173c8(undefined4 unused,undefined4 retained) {
    return CONCAT44(E2R_fan_parse_stream,raw_word(E2R_fan_parse_stream));
}
static undefined8 FUN_004171b8(undefined4 unused,undefined4 retained) { assert(0);return 0; }
static void native_entries(void) {
'''+declarations+r'''
    piVar11=E2R_fan_parse_stream;uVar16=0;iVar8=0;
'''+loop+r'''
}
__attribute__((used,noinline)) static uint hook_word(int *stream) { return raw_word(stream); }
__attribute__((used,noinline)) static uint hook_byte(int *stream) { return E2R_ReadHostedStreamByte((undefined4*)stream); }
__attribute__((naked)) static void word_entry(void) {
    __asm__("pushal; push %eax; call hook_word; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void byte_entry(void) {
    __asm__("pushal; push %eax; call hook_byte; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void original_entries(int *stream) {
    __asm__("pushal; mov 36(%esp),%edx; sub $4,%esp; mov $0x4476d0,%eax; call *%eax; add $4,%esp; popal; ret");
}
static void map(int address,int size) {
    assert(mmap((void*)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void jump(int address,void *target) { *(byte*)address=0xe9;*(int*)(address+1)=(intptr_t)target-address-5; }
static void word(byte *p,int v) { p[0]=v;p[1]=v>>8; }
int main(void) {
    map(0x410000,0x10000);map(0x440000,0x10000);map(0x450000,0x10000);
    map(0x470000,0x10000);map(0x670000,0x30000);
    memcpy((void*)0x4476e6,original,sizeof original);memcpy((void*)0x4479de,"\x83\xc4\x04\xc3",4);
    memcpy((void*)0x4476d0,"\x83\xec\x04\xe9",4);*(int*)0x4476d4=0x4476e6-0x4476d8;
    jump(0x4173c8,word_entry);jump(0x45f38a,byte_entry);
    byte *high=mmap(NULL,0x10000,3,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    assert(high!=MAP_FAILED && (uintptr_t)high>=0x70000000u);
    int *stream=(int*)high;byte *input=high+0x1000;E2R_fan_parse_stream=stream;
    unsigned entries=0;
    for(int sample=0;sample<16;sample++) {
        for(int i=0;i<0x4000;i++) *(ushort*)(0x6769f8+i*2)=(i*13+sample)&0x3fff;
        for(int i=0;i<256;i++) {
            byte *record=input+i*36;
            for(int k=0;k<36;k++)record[k]=(i+k*17+sample*31)&255;
            record[0]=i;record[1]=(i*7+sample)&255;
            word(record+2,(i*997+sample)&65535);word(record+4,(i*563+sample)&65535);
            word(record+13,i%19?((i*41+sample)&65535):65535);
        }
        memset(stream,0,28);stream[0]=(intptr_t)input;stream[1]=256*36;
        stream[5]=(intptr_t)input;stream[6]=E2R_STREAM_MAGIC;stream[3]=0x41;
        _DAT_0067bc92=*(short*)0x67bc92=55;DAT_0047a77c=*(int*)0x47a77c=256;
        memset((void*)0x68cd68,0xcc,256*12);original_entries(stream);
        byte expected[256*12];memcpy(expected,(void*)0x68cd68,sizeof expected);
        int cursor=stream[0],remaining=stream[1];assert(cursor==(intptr_t)input+256*36 && !remaining);
        stream[0]=(intptr_t)input;stream[1]=256*36;stream[3]=0x41;
        memset((void*)0x68cd68,0xcc,256*12);native_entries();
        assert(stream[0]==cursor && stream[1]==remaining);
        assert(!memcmp(expected,(void*)0x68cd68,sizeof expected));entries+=256;
    }
    // Direct provider contract: binary CR/0x1a consume exactly one byte.
    for(int value=0;value<256;value++) {
        input[0]=value;input[1]=0xa5;stream[0]=(intptr_t)input;stream[1]=2;stream[3]=0x41;
        uint64_t result=FUN_0045f38a(0,(intptr_t)stream);
        assert((uint)result==(uint)value && (uint)(result>>32)==(uintptr_t)stream);
        assert(stream[0]==(intptr_t)input+1 && stream[1]==1);
    }
    printf("PASS: %u original-x86 FAN-55 floor entries; 256 high-address hosted binary-byte cases\n",entries);
}
'''
harness=harness.replace('original,sizeof original','original_code,sizeof original_code')
at=harness.index('static void map(')
harness=harness[:at]+'static unsigned char original_code[]={'+','.join(map(str,original))+'};\n'+harness[at:]
with tempfile.TemporaryDirectory(prefix='e2-floor-decoder-') as tmp:
    c=Path(tmp)/'check.c';binary=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie','-Wno-int-conversion',*flags,str(c),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True,timeout=20)
