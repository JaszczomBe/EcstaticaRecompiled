#!/usr/bin/env python3
"""Compare the complete recovered save writer with original x86 using private memory streams."""
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
typedef uint32_t uint,undefined4;typedef uint64_t undefined8,ulonglong;
#define __fastcall
#define E2R_STREAM_MAGIC 0xe25eed01u
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define WORD(a) (*(int32_t *)(a))
static byte output[512000],expected[512000];static unsigned count,opens,closes;
static int stream[7];static int opening_fails;
static uint FUN_0045f5d6(void) { assert(!"Nonhosted production stream");return 0; }
static int E2R_WriteHostedStreamByte(uint *s,int value) { assert(s==(uint *)stream && count<sizeof output);output[count++]=(byte)value;return value&255; }
static uint E2R_OpenWriteStream(const char *path) { assert(!strcmp(path,"saved\\0005.ecs"));opens++;return opening_fails ? 0 : (uint)stream; }
static undefined8 FUN_0045ec6c(uint unused,uint s) { assert(s==(uint)stream);closes++;return 0; }
__attribute__((used,noinline)) static void FUN_00414e68(void) { assert(!"Unexpected fatal path"); }
static undefined8 FUN_0043cac0(uint text,uint unused) { assert(opening_fails);return 0; }
static void FUN_0041ca90(uint page) { assert(!"Cursor hiding is excluded"); }
static void FUN_0041c518(uint page) { assert(!"Cursor restoration is excluded"); }
__attribute__((used,noinline)) static uint FUN_00418a04(uint page,uint *pitch) { assert(page==0);*pitch=672;return 0x710000; }
__attribute__((used,noinline)) static void FUN_00418b00(uint page,uint pixels) { assert(page==0 && pixels==0x710000); }
void FUN_00417248(uint,int *);void FUN_00417308(uint,int *);
void FUN_00441600(uint,int *);void FUN_00454fe4(uint,uint);void FUN_00443dbc(uint,uint);
'''
for address in (0x47a279,0x47a43c,0x47ab20,0x47ab24,0x47ab40,0x47a49c,0x47a4a0,0x47a498,0x47a440,
                0x6401ec,0x6401d4,0x63726c,0x637254,0x637260,0x636588,0x637248,0x637268):
    name = ('_' if address >= 0x600000 else '') + f'DAT_{address:08x}'
    harness += f'#define {name} WORD(0x{address:x})\n'
harness += support()
for name in ('FUN_00417248','FUN_00417308','FUN_00454fe4','FUN_00441600',
             'E2R_WriteSaveRecord','E2R_WriteSaveVectorRecord','FUN_00443dbc','FUN_004437f0','FUN_00453920'):
    harness += function(source,name) + '\n'
ranges = [(0x417248,0x4173c7),(0x4412f8,0x4413b5),(0x441600,0x44161c),
          (0x4437f0,0x44432e),(0x453920,0x454430),(0x454fe4,0x455034),(0x422aa0,0x422ab9)]
for index, (start,end) in enumerate(ranges):
    harness += f'static const byte code{index}[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
harness += r'''
__attribute__((used,noinline)) static uint open_original(const char *path,const char *mode) {
    assert(!strcmp(mode,"wb"));return E2R_OpenWriteStream(path);
}
__attribute__((used,noinline)) static uint close_original(uint s) { return FUN_0045ec6c(0,s); }
__attribute__((used,noinline)) static uint byte_original(uint value,uint s) { return E2R_WriteHostedStreamByte((uint *)s,value); }
__attribute__((used,noinline)) static void copy_original(char *dst,const char *src) { strcpy(dst,src); }
__attribute__((used,noinline)) static void name_original(char *dst,const char *src,uint size) { strncpy(dst,src,size); }
__attribute__((naked)) static void open_hook(void) { __asm__("pushal; push %edx; push %eax; call open_original; add $8,%esp; mov %eax,28(%esp); popal; ret"); }
__attribute__((naked)) static void close_hook(void) { __asm__("pushal; push %eax; call close_original; add $4,%esp; mov %eax,28(%esp); popal; ret"); }
__attribute__((naked)) static void byte_hook(void) { __asm__("pushal; push %edx; push %eax; call byte_original; add $8,%esp; mov %eax,28(%esp); popal; ret"); }
__attribute__((naked)) static void copy_hook(void) { __asm__("pushal; push %edx; push %eax; call copy_original; add $8,%esp; popal; ret"); }
__attribute__((naked)) static void name_hook(void) { __asm__("pushal; push %ebx; push %edx; push %eax; call name_original; add $12,%esp; popal; ret"); }
__attribute__((naked)) static void ret_hook(void) { __asm__("ret"); }
__attribute__((naked)) static void error_hook(void) { __asm__("pushal; call FUN_00414e68; popal; ret"); }
__attribute__((naked)) static void lock_hook(void) { __asm__("pushal; push %edx; push %eax; call FUN_00418a04; add $8,%esp; mov %eax,28(%esp); popal; ret"); }
__attribute__((naked)) static void unlock_hook(void) { __asm__("pushal; push %edx; push %eax; call FUN_00418b00; add $8,%esp; popal; ret"); }
static void hook(uint address,void *target) { *(byte *)address=0xe9;WORD(address+1)=(uint)target-address-5; }
static void map(uint address,uint size) { assert(mmap((void *)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)address); }
static void seed(unsigned trial) {
    memset((void *)0x630000,0,0x420000);
    uint rng=trial+1;
    for(uint at=0x647a68;at<0x68cd68;at++) { rng=rng*1664525u+1013904223u;*(byte *)at=rng>>24; }
    DAT_0047a279=1u<<24;DAT_0047a43c=trial&1;
    _DAT_006401ec=DAT_0047a43c ? 640 : 320;_DAT_006401d4=DAT_0047a43c ? 480 : 200;
    WORD(0x636150)=0x710000;*(short *)0x479e8e=-1;
    for(uint i=0;i<672*480;i++)*(byte *)(0x710000+i)=(byte)(i*13+trial);
    _DAT_00636588=0x10100+trial;
    _DAT_0063726c=_DAT_00637248=trial%3 ? 0x700000 : 0;
    if(_DAT_0063726c) {
        uint actor=0x700000,other=0x700200;
        for(uint i=0;i<0x400;i+=2)*(short *)(actor+i)=trial*31+i;
        WORD(actor+0x4c)=other;WORD(actor+0x50)=other;WORD(other+0x4c)=WORD(other+0x50)=0;
        *(short *)actor=0;*(short *)other=4;
        WORD(actor+0x1e)=WORD(other+0x1e)=0;
        WORD(actor+0xd8)=WORD(other+0xd8)=0;
        WORD(actor+0x126)=WORD(actor+0x12a)=WORD(other+0x126)=WORD(other+0x12a)=0;
        WORD(actor+0xa6)=0x701000;*(short *)0x701000=37;*(byte *)0x70100c=0;
        WORD(other+0xa6)=0;
        WORD(actor+0x17c)=0x701100;*(short *)0x701100=23;WORD(0x701102)=_DAT_00636588-100;WORD(0x701106)=0;
        WORD(other+0x17c)=0;
        WORD(actor+0xf2)=0x701200;*(short *)0x701200=3;WORD(0x701222)=other;
        WORD(other+0xf2)=0;
    }
    if(_DAT_0063726c && trial%4) {
        uint actor=0x700000,part=0x701400,child=0x701600,point=0x701800,link=0x701a00;
        for(uint at=part;at<0x701c00;at+=2)*(short *)at=at*3+trial;
        WORD(actor+0x1e)=part;WORD(part+0xca)=0;WORD(part+0x1e)=child;WORD(part+0x4c)=0;
        WORD(part+0x11e)=point;WORD(part+0x12e)=0x700200;
        WORD(child+0xca)=WORD(child+0x1e)=WORD(child+0x11e)=0;
        WORD(point+0x26)=0;
        WORD(actor+0xd8)=link;WORD(link+0x1e)=0;
        WORD(link+4)=part;WORD(link+8)=part;WORD(link+0xc)=child;WORD(link+0x28)=0x700200;
        *(short *)(link+0x2c)=trial%2 ? 2 : -1;
        if(trial%2) {
            WORD(actor+0xa6)=0x701c02;*(short *)0x701c00=0;*(short *)0x701c02=55;*(byte *)0x701c0e=2;WORD(0x701c18)=0;
            _DAT_00637260=0x701d00;*(short *)0x701d00=44;WORD(0x701d04)=0x701c00;WORD(0x701d9c)=0;
        }
        _DAT_00637254=0x701e00;*(short *)0x701e00=13;*(byte *)0x701faa=2;WORD(0x701fa6)=0;
        _DAT_00637268=0x702000;*(short *)0x702000=7;WORD(0x702016)=0;
        for(uint i=0;i<10;i++)*(short *)(0x702002+i*2)=i<2 ? i+1 : -1;
    }
    for(uint i=0;i<150;i++)*(byte *)(0xac4b00+i)=(byte)(i+trial);
    DAT_0047ab20=0x12345678;DAT_0047ab24=0x9abcdef0;DAT_0047ab40=trial%3;
    const uint globals[]={0x47ab0c,0x47ab28,0x47ab18,0x47ab14,0x47ab2c,0x47a4a4,0x47a49c,0x47a4a0,0x47a498,0x47a440};
    for(uint i=0;i<sizeof globals/sizeof globals[0];i++)WORD(globals[i])=i*3901+trial;
    for(int i=0;i<DAT_0047ab40;i++) {
        WORD(0xac493c+i*4)=i+5;WORD(0xaba2ac+i*4)=i+10;WORD(0xac48ec+i*4)=i+20;WORD(0xaa69fc+i*4)=i+30;
    }
    memset(stream,0,sizeof stream);stream[3]=0x400;opens=closes=count=0;
}
int main(void) {
    map(0x410000,0x10000);map(0x420000,0x10000);map(0x440000,0x10000);map(0x450000,0x10000);map(0x470000,0x10000);
    map(0x630000,0x420000);map(0xaa0000,0x30000);
'''
for i,(start,end) in enumerate(ranges):
    harness += f'    memcpy((void *)0x{start:x},code{i},sizeof code{i});\n'
harness += r'''
    memcpy((void *)0x475c00,"saved\\XXXX.ecs",15);memcpy((void *)0x475c10,"wb",3);
    hook(0x45fd2c,copy_hook);hook(0x45eb05,open_hook);hook(0x45f22f,name_hook);hook(0x45f5d6,byte_hook);hook(0x45ec6c,close_hook);
    hook(0x45cf02,ret_hook);hook(0x414e68,error_hook);hook(0x418a04,lock_hook);hook(0x418b00,unlock_hook);
    for(unsigned trial=0;trial<24;trial++) {
        char label[26];memset(label,'A'+trial%26,25);label[trial%26]=0;label[25]=0;
        seed(trial);struct E2R_Registers regs={.eax=5,.edx=(uint)label};
        e2r_original_call(0x453920,&regs);assert(opens==1 && closes==1);
        unsigned size=count;memcpy(expected,output,size);
        seed(trial);stream[6]=0xe25eed01u;stream[3]=0x42;
        assert((uint)FUN_00453920(5,label)==0 && opens==1 && closes==1);
        if(size!=count) { fprintf(stderr,"trial=%u size original=%u recovered=%u\n",trial,size,count);return 1; }
        assert(e2r_memory_equal("complete original save bytes",expected,output,count));
    }
    puts("PASS: 24 complete original-x86 writer byte comparisons: both thumbnail branches, root records, actor state, relative timers, attachment IDs, cached fields and trailer; output captured in memory only");
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('original CRT open/byte/close/name/copy and hardware/surface providers intercepted',
                          'private synthetic world; no disk save files, menu input or loader exercised'))
