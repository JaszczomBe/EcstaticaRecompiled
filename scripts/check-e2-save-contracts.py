#!/usr/bin/env python3
"""Compare save word byte order and column-major matrix traversal against original x86."""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
image = OriginalImage(args.exe)
source = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4,DWORD;typedef uint64_t undefined8,ulonglong;
typedef void *HANDLE;
#define __fastcall
#define E2R_STREAM_MAGIC 0xe25eed01u
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define CONCAT22(a,b) (((uint32_t)(uint16_t)(a)<<16)|(uint16_t)(b))
#define CONCAT11(a,b) (((uint16_t)(uint8_t)(a)<<8)|(uint8_t)(b))
static int *E2R_fan_parse_stream;
static int IsBadReadPtr(const void *p,unsigned n) { return !p; }
static byte output[256];static unsigned count,fail_after;
static int WriteFile(HANDLE h,const void *p,unsigned n,unsigned *written,void *ov) {
    assert(n==1);*written=0;if(count==fail_after)return 0;
    output[count++]=*(const byte *)p;*written=1;return 1;
}
static uint FUN_0045f5d6(void) { assert(!"Non-hosted stream in production writer");return 0; }
static int E2R_ReadFanWordByte(int *stream) {
    if(stream[1]<=0)return -1;int v=*(byte *)(uintptr_t)stream[0];stream[0]++;stream[1]--;return v;
}
static undefined8 FUN_0045f38a(uint unused,int *stream) { return CONCAT44(stream,E2R_ReadFanWordByte(stream)); }
'''
harness += support()
for name in ('E2R_WriteHostedStreamByte', 'FUN_00417248', 'FUN_00417308', 'FUN_004173c8', 'FUN_00454fe4', 'FUN_00455034'):
    harness += function(source, name) + '\n'
for index, (start, end) in enumerate(((0x417248, 0x4173c7), (0x4173c8, 0x41745b), (0x454fe4, 0x455034), (0x455034,0x45507c))):
    harness += f'static const byte code{index}[]={{' + ','.join(map(str,image.code(start,end))) + '};\n'
harness += r'''
__attribute__((used,noinline)) static int original_write(unsigned value,int *stream) {
    assert(count<sizeof output);output[count++]=(byte)value;return value&255;
}
__attribute__((naked)) static void write_hook(void) {
    __asm__("pushal; push %edx; push %eax; call original_write; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((used,noinline)) static int original_read(int *stream) { return E2R_ReadFanWordByte(stream); }
__attribute__((naked)) static void read_hook(void) {
    __asm__("pushal; push %eax; call original_read; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
static void hook(unsigned address,void *target) { *(byte *)address=0xe9;*(int32_t *)(address+1)=(unsigned)target-address-5; }
static void map(unsigned address,unsigned size) { assert(mmap((void *)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)address); }
int main(void) {
    map(0x410000,0x10000);map(0x450000,0x10000);
    memcpy((void *)0x417248,code0,sizeof code0);memcpy((void *)0x4173c8,code1,sizeof code1);memcpy((void *)0x454fe4,code2,sizeof code2);memcpy((void *)0x455034,code3,sizeof code3);
    hook(0x45f5d6,write_hook);hook(0x45f38a,read_hook);
    int stream[7]={0,0,0,0x400,0,0,0};byte expected[256];unsigned word_cases=0,matrix_cases=0;
    fail_after=~0u;
    for(unsigned order=0;order<2;order++)for(unsigned value=0;value<65536;value++) {
        count=0;stream[3]=0x400;stream[6]=0;
        struct E2R_Registers regs={.eax=value|0x98760000u,.edx=(unsigned)stream};
        e2r_original_call(order ? 0x417308 : 0x417248,&regs);assert(count==2);memcpy(expected,output,2);
        count=0;stream[3]=0x42;stream[6]=E2R_STREAM_MAGIC;
        if(order)FUN_00417308(value|0x98760000u,stream);else FUN_00417248(value|0x98760000u,stream);
        assert(count==2 && !memcmp(expected,output,2));word_cases++;
        if(order) {
            stream[0]=(int)output;stream[1]=2;stream[3]=0x41;
            regs.eax=(unsigned)stream;e2r_original_call(0x4173c8,&regs);assert((regs.eax&65535)==value && stream[1]==0);
            stream[0]=(int)output;stream[1]=2;
            assert((uint)FUN_004173c8((uint)stream,0x1234)==value && stream[1]==0);
        }
    }
    for(unsigned trial=0;trial<256;trial++) {
        short matrix[9];for(unsigned i=0;i<9;i++)matrix[i]=trial*257+i*1031;
        stream[3]=0x400;stream[6]=0;count=0;
        struct E2R_Registers regs={.eax=(unsigned)matrix,.edx=(unsigned)stream};
        e2r_original_call(0x454fe4,&regs);assert(count==18);memcpy(expected,output,18);
        stream[3]=0x42;stream[6]=E2R_STREAM_MAGIC;count=0;
        FUN_00454fe4((uint)matrix,(uint)stream);assert(count==18 && !memcmp(expected,output,18));
        short original_matrix[11],recovered_matrix[11];
        memset(original_matrix,0x35,sizeof original_matrix);memset(recovered_matrix,0x35,sizeof recovered_matrix);
        stream[0]=(uint)output;stream[1]=18;stream[3]=0x40;
        regs.eax=(uint)(original_matrix+1);regs.edx=(uint)stream;e2r_original_call(0x455034,&regs);assert(stream[1]==0);
        stream[0]=(uint)output;stream[1]=18;stream[3]=0x41;stream[6]=E2R_STREAM_MAGIC;
        FUN_00455034((uint)(recovered_matrix+1),(uint)stream);
        assert(stream[1]==0 && !memcmp(original_matrix,recovered_matrix,sizeof original_matrix));matrix_cases++;
    }
    for(unsigned limit=0;limit<2;limit++) {
        stream[3]=0x42;count=0;fail_after=limit;FUN_00417308(0x1234,stream);
        assert(count==limit && (stream[3]&0x20));
    }
    printf("PASS: %u original-x86 endian/width cases (65536 LE reads), %u matrix traversals, sticky write failure checks\n",word_cases,matrix_cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('original CRT byte I/O intercepted; production hosted writes captured',))
