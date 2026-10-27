#!/usr/bin/env python3
"""Compare repaired menu storage, restart identity and save-slot labels with original x86."""
import argparse
from pathlib import Path
import re

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
#include <string.h>
#include <stdlib.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;typedef long long longlong;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define WORD(address) (*(uint32_t *)(address))
static int IsBadReadPtr(const void *p,unsigned n) { return !p; }
static int E2R_IsReadableCurrentPointer(const void *p) { return p!=0; }
static uintptr_t _DAT_006439a0,_DAT_00643a00,_DAT_00643960;
static byte DAT_006439a8,DAT_00643a08;
static short *DAT_0047a470;
'''
for address in (0x479e00, 0x479dbc, 0x47a49c, 0x47a4a0, 0x47a4a4, 0x47a43c, 0x47a279,
                0x60ae24, 0x60ae28, 0x60ae2c, 0x60ae30, 0x60af14, 0x60af18, 0x60af1c):
    name = ('_' if address >= 0x600000 else '') + f'DAT_{address:08x}'
    harness += f'#define {name} WORD(0x{address:x})\n'
for name, address in [
    ('s_Music_ON_00472aa4', 0x472aa4), ('s_Music_OFF_00472ac0', 0x472ac0),
    ('s_Sound_effects_ON_00472adc', 0x472adc), ('s_Sound_effects_OFF_00472af8', 0x472af8),
    ('s_Difficulty_level_EASY_00472b14', 0x472b14),
    ('s_Difficulty_level_MEDIUM_00472b30', 0x472b30),
    ('s_Difficulty_level_HARD_00472b4c', 0x472b4c),
    ('s_saved_XXXX_ecs_00472744', 0x472744),
]:
    harness += f'#define {name} ((char *)0x{address:x})\n'
harness += '#define DAT_004727c4 (*(char *)0x4727c4)\n' + support()
for name in ('FUN_0043d934', 'FUN_0043d9a0', 'FUN_0043da04'):
    harness += function(source, name) + '\n'
restart = function(source, 'FUN_0043a39c')
restart = restart[restart.index('  if (DAT_0047a470 !='):restart.index('  FUN_0043a1fc();')]
harness += 'static void mark_player(void) {\n' + restart + '\n}\n'
requester = function(source, 'FUN_0043ce58')
loop = requester[requester.index('        for (sStack_1c = 0;'):requester.index('        _DAT_0064353c = 0xffffffff;')]
# Check the live builder's text pointers as well as the label-reading loop.
builder = function(source, 'FUN_0043fea4')
assert '(char *)0x00643540 + iVar4 * 0x1a' in builder
assert '(char *)0x00643434 + iVar4 * 0x1a' in builder
assert 'action.restart_intro",7' not in function(source, 'E2R_InvokeRequesterAction')

ranges = [(0x43ce58, 0x43d458), (0x43d934, 0x43da80), (0x43a3f0, 0x43a404),
          (0x43c1b8, 0x43c4ad)]
for i, (start, end) in enumerate(ranges):
    code = image.code(start, end) + (b'\xc3' if i == 2 else b'')
    harness += f'static const byte code{i}[]={{' + ','.join(map(str, code)) + '};\n'
filename = image.code(0x472744, 0x472753)
harness += 'static const byte filename[]={' + ','.join(map(str, filename)) + '};\n'
harness += r'''
static unsigned opens,closes,mode,original_mode,unlocks;
static int streams[10][7];
static byte contents[10][4828];
static char filenames[10][15];
static byte pixels[704*480];
static byte hosted[2][704*480];
__attribute__((used,noinline)) static unsigned open_stream(const char *path,const char *kind) {
    assert(opens<10 && !strcmp(kind,"rb"));
    unsigned slot=opens++;
    memcpy(filenames[slot],path,15);
    char expected[15];snprintf(expected,sizeof expected,"saved\\%04u.ecs",slot);
    assert(!strcmp(path,expected));
    if(mode==0 || (mode==1 && slot%3==0))return 0;
    memset(streams[slot],0,sizeof streams[slot]);
    memset(contents[slot],'.',26);
    snprintf((char *)contents[slot],26,"Slot %u",slot);
    if(mode==2 && slot%3==0)contents[slot][0]='\r';
    for(unsigned i=26;i<4828;i++)contents[slot][i]=(byte)(i*37+slot);
    streams[slot][0]=(int)contents[slot];streams[slot][1]=4828;
    streams[slot][3]=original_mode ? 0x40 : 0;
    return (unsigned)streams[slot];
}
__attribute__((used,noinline)) static int read_stream(int *stream) {
    if(stream[1]<=0)return -1;
    int value=*(byte *)stream[0];stream[0]++;stream[1]--;
    if(!(stream[3]&0x40)) {
        if(value=='\r' && stream[1]>0) { value=*(byte *)stream[0];stream[0]++;stream[1]--; }
        if(value==0x1a)return -1;
    }
    return value;
}
__attribute__((used,noinline)) static int unread_stream(int value,int *stream) {
    stream[0]--;stream[1]++;assert(*(byte *)stream[0]==(byte)value);return value;
}
__attribute__((used,noinline)) static int close_stream(int *stream) {
    assert(stream>=(int *)streams && stream<(int *)(streams+10));closes++;return 0;
}
__attribute__((naked)) static void open_hook(void) {
    __asm__("pushal; push %edx; push %eax; call open_stream; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void read_hook(void) {
    __asm__("pushal; push %eax; call read_stream; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void unread_hook(void) {
    __asm__("pushal; push %edx; push %eax; call unread_stream; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void close_hook(void) {
    __asm__("pushal; push %eax; call close_stream; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void requester_hook(void) { __asm__("xor %eax,%eax; ret"); }
__attribute__((used,noinline)) static unsigned lock_surface(unsigned surface,int *pitch) {
    *pitch=704;
    if(original_mode) { assert(surface==0);return (unsigned)pixels; }
    assert(surface==2 || surface==3);return (unsigned)hosted[surface-2];
}
__attribute__((used,noinline)) static void unlock_surface(unsigned surface,unsigned base) {
    assert(original_mode ? surface==0 && base==(unsigned)pixels :
           (surface==2 || surface==3) && base==(unsigned)hosted[surface-2]);unlocks++;
}
__attribute__((used,noinline)) static void clear_surface(unsigned surface,int x,int y,int right,int bottom) {
    assert(surface==0);
    for(unsigned page=0;page<(original_mode ? 1 : 2);page++)
        for(int row=y;row<=bottom;row++)memset((original_mode ? pixels : hosted[page])+row*704+x,0,right-x+1);
}
__attribute__((naked)) static void lock_hook(void) {
    __asm__("pushal; push %edx; push %eax; call lock_surface; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void unlock_hook(void) {
    __asm__("pushal; push %edx; push %eax; call unlock_surface; add $8,%esp; popal; ret");
}
__attribute__((naked)) static void clear_hook(void) {
    __asm__("pushal; push 36(%esp); push %ecx; push %ebx; push %edx; push %eax; call clear_surface; add $20,%esp; popal; ret $4");
}
__attribute__((used,noinline)) static unsigned read_word(int *stream) {
    unsigned a=read_stream(stream),b=read_stream(stream);return (a&255)|((b&255)<<8);
}
__attribute__((naked)) static void word_hook(void) {
    __asm__("pushal; push %eax; call read_word; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
static unsigned FUN_004173c8(unsigned stream,unsigned unused) { return read_word((int *)stream); }
static unsigned FUN_00418a04(unsigned surface,int *pitch) { return lock_surface(surface,pitch); }
static void FUN_00418b00(unsigned surface,unsigned base) { unlock_surface(surface,base); }
static void E2R_FillHostedRect(int x,int y,int right,int bottom) { clear_surface(0,x,y,right,bottom); }
static void out(unsigned port,short value) { assert(port==0x3c4); }
static unsigned FUN_0045eb05(unsigned path,unsigned kind) { return open_stream((char *)path,(char *)kind); }
static undefined8 FUN_0045f38a(unsigned unused,unsigned stream) { return CONCAT44(stream,read_stream((int *)stream)); }
static void FUN_0045ec6c(unsigned unused,unsigned stream) { close_stream((int *)stream); }
'''
harness += function(source, 'E2R_ReadFanTextByte') + '\n'
harness += function(source, 'FUN_0043c1b8') + '\n'
harness += 'static void slot_labels(void) { short sStack_1c;char acStack_50[15],cVar1;int *piVar3;\n' + loop + '\n}\n'
harness += r'''
static void hook(unsigned address,void *target) {
    *(byte *)address=0xe9;*(int32_t *)(address+1)=(int32_t)target-address-5;
}
static void original(unsigned address,unsigned eax) {
    __asm__ volatile("call *%%edi" : "+a"(eax) : "D"(address) : "ecx","edx","memory","cc");
}
static void map(unsigned address,unsigned size) {
    assert(mmap((void *)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)address);
}
int main(void) {
    map(0x410000,0x10000);map(0x430000,0x10000);map(0x450000,0x10000);map(0x630000,0x10000);
    map(0x470000,0x10000);map(0x600000,0x10000);map(0x640000,0x10000);
    memcpy((void *)0x43ce58,code0,sizeof code0);memcpy((void *)0x43d934,code1,sizeof code1);
    memcpy((void *)0x43a3f0,code2,sizeof code2);memcpy((void *)0x472744,filename,15);
    memcpy((void *)0x43c1b8,code3,sizeof code3);
    memcpy((void *)0x472754,"rb",3);
    hook(0x45eb05,open_hook);hook(0x45f38a,read_hook);hook(0x45fdc4,unread_hook);
    hook(0x45ec6c,close_hook);hook(0x43b384,requester_hook);
    hook(0x418a04,lock_hook);hook(0x418b00,unlock_hook);hook(0x41ab4c,clear_hook);hook(0x4173c8,word_hook);
    unsigned label_cases=0;
    for(unsigned language=0;language<4;language++)
    for(unsigned backend=0;backend<8;backend++)
    for(unsigned value=0;value<4;value++)
    for(unsigned flags=0;flags<256;flags+=85) {
        DAT_00479e00=language;DAT_00479dbc=backend;
        DAT_0047a49c=DAT_0047a4a0=DAT_0047a4a4=value;
        _DAT_0060ae24=0x1234;_DAT_0060ae28=0x2345;
        _DAT_0060ae2c=0x3456;_DAT_0060ae30=0x4567;
        _DAT_0060af14=0x5678;_DAT_0060af18=0x6789;_DAT_0060af1c=0x789a;
        memset((void *)0x643900,0x5a,0x200);
        *(byte *)0x6439a8=*(byte *)0x643a08=flags;
        byte expected[0x200];
        original(0x43d934,0);original(0x43d9a0,0);original(0x43da04,0);
        memcpy(expected,(void *)0x643900,sizeof expected);
        memset((void *)0x643900,0x5a,0x200);
        *(byte *)0x6439a8=DAT_006439a8=flags;*(byte *)0x643a08=DAT_00643a08=flags;
        FUN_0043d934();FUN_0043d9a0();FUN_0043da04();
        assert(!memcmp(expected,(void *)0x643900,sizeof expected));label_cases++;
    }
    unsigned identity_cases=0;uint32_t player;
    int identities[]={-1,0,1,284,3717,4119};
    for(unsigned id=0;id<sizeof identities/sizeof *identities;id++)
    for(unsigned flags=0;flags<0x10000;flags+=0x1111) {
        player=(flags<<16)|(uint16_t)identities[id];DAT_0047a470=(short *)&player;
        WORD(0x47a470)=(uint32_t)&player;
        memset((void *)0x64a000,0xa5,0x3000);
        original(0x43a3f0,0);byte expected[0x3000];memcpy(expected,(void *)0x64a000,sizeof expected);
        memset((void *)0x64a000,0xa5,0x3000);mark_player();
        assert(!memcmp(expected,(void *)0x64a000,sizeof expected));identity_cases++;
    }
    unsigned slot_cases=0;
    for(mode=0;mode<3;mode++)for(unsigned rid=0x29;rid<=0x2a;rid++) {
        DAT_00479e00=0;WORD(0x47ab30)=WORD(0x47ab34)=0;
        memset((void *)0x642fb0,0xa5,0x800);opens=closes=0;
        original_mode=1;original(0x43ce58,rid);
        assert(opens==10);unsigned expected_closes=closes;
        /* Selection is finalized after the extracted production label loop. */
        WORD(0x64353c)=0xa5a5a5a5;
        byte expected[0x800];char expected_names[10][15];
        memcpy(expected,(void *)0x642fb0,sizeof expected);memcpy(expected_names,filenames,sizeof filenames);
        memset((void *)0x642fb0,0xa5,0x800);opens=closes=0;
        original_mode=0;slot_labels();
        assert(opens==10 && closes==expected_closes);
        assert(!memcmp(expected_names,filenames,sizeof filenames));
        assert(e2r_memory_equal("save-slot storage",expected,(void *)0x642fb0,sizeof expected));slot_cases++;
    }
    unsigned preview_cases=0;DAT_0047a43c=1;DAT_0047a279=0;
    for(mode=0;mode<3;mode++)for(unsigned slot=0;slot<10;slot++) {
        memset(pixels,0xa5,sizeof pixels);opens=slot;closes=unlocks=0;original_mode=1;
        original(0x43c1b8,slot);
        unsigned expected_closes=closes,expected_unlocks=unlocks;
        static byte expected[sizeof pixels];memset(expected,0xa5,sizeof expected);
        /* Source-backed 80x60 oracle; intentional display-only 2x enlargement. */
        for(unsigned y=0;y<120;y++)for(unsigned x=0;x<160;x++)
            expected[(162+y)*704+72+x]=pixels[(162+y/2)*704+116+x/2];
        memset(pixels,0xa5,sizeof pixels);memset(hosted,0xa5,sizeof hosted);opens=slot;closes=unlocks=0;original_mode=0;
        FUN_0043c1b8(slot,0);
        for(unsigned page=0;page<2;page++)
            assert(e2r_memory_equal("original thumbnail in hosted menu page/pitch/canaries",expected,hosted[page],sizeof pixels));
        for(unsigned i=0;i<sizeof pixels;i++)assert(pixels[i]==0xa5);
        assert(closes==expected_closes && unlocks==2*expected_unlocks);preview_cases++;
    }
    printf("PASS: %u original-x86 option storage cases, %u word-identity/canary cases and %u ten-slot missing/named/CR save-label scans; native serialization is outside this fixture\n",
           label_cases,identity_cases,slot_cases);
    printf("PASS: %u original-x86 high-resolution thumbnail/blank cases mapped to both hosted menu pages, padded pitch/full-surface canaries and unchanged physical game page\n",preview_cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('CRT open/read/ungetc/close register bridges with synthetic slot bytes',
                          'requester draw interception; original labels and slot metadata only'))

