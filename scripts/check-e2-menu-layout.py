#!/usr/bin/env python3
"""Compare original high-resolution font pixels and requester layout with recovered C."""
import argparse
import json
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
compat = Path('E2Recomp/platform/e2recomp_win32_compat.c').read_text()
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
typedef uint8_t byte;
typedef uint16_t undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8;
#define WORD(a) (*(uint32_t *)(a))
#define SHORT(a) (*(uint16_t *)(a))
#define DAT_0047a43c WORD(0x47a43c)
#define DAT_0047a279 WORD(0x47a279)
#define DAT_0047a408 SHORT(0x47a408)
#define DAT_0047a40c WORD(0x47a40c)
#define _DAT_006401ec WORD(0x6401ec)
#define _DAT_006401d4 WORD(0x6401d4)
static byte expected[704*480],pages[2][704*480];
static int IsBadReadPtr(const void *p,unsigned n) { return !p; }
static int E2R_IsBadWritePtr(void *p,unsigned n) { return !p; }
static unsigned FUN_00418a04(unsigned surface,int *pitch) {
    assert(surface==2 || surface==3);*pitch=704;return (unsigned)pages[surface-2];
}
'''
harness += support()
harness += function(compat, 'E2R_ReadOriginalImageData') + '\n'
for name in ('E2R_OriginalMenuGlyph', 'E2R_HostedGlyphRows', 'E2R_DrawHostedText'):
    harness += function(source, name) + '\n'
# Isolate the original straight-line record/title arithmetic; retain absolute
# branch destinations and intercept only the final cursor-position service.
record = function(source, 'FUN_0043b384')
geometry = record[record.index('  if (DAT_0047a43c == 0) {'):record.index('  FUN_0041760c(')]
title_call = re.search(r'    FUN_0041b078\(in_EAX\[8\].*?;', record, re.S).group()
redraw = function(source, 'FUN_0043af98')
redraw_title_call = re.search(r'    FUN_0041b078\(puVar3\[8\].*?;', redraw, re.S).group()
redraw_title_call = redraw_title_call.replace('puVar3','in_EAX').replace('sVar5','sVar6')
start=source.index('static void E2R_InitRequesterRecord(')
harness += source[start:source.index('\n}',start)+2] + '\n'
harness += 'static int title_x,title_y;static void FUN_0041b078(int x,int y) {title_x=x;title_y=y;}\n'
# Extract each live decision block rather than reimplementing its comparisons.
def if_block(at):
    start=record.index('if (',at)
    brace=record.index('{',start)
    depth=1
    end=brace+1
    while depth:
        depth += (record[end]=='{') - (record[end]=='}')
        end+=1
    following=record[end:].lstrip()
    if following.startswith('else {'):
        brace=record.index('{',end)
        depth=1
        end=brace+1
        while depth:
            depth += (record[end]=='{') - (record[end]=='}')
            end+=1
    return record[start:end],end
key_branch,end=if_block(record.index('if (_DAT_0064342c == 0)',record.index('mouse_state = (int)uVar11;')))
mouse_branch,end=if_block(record.index('if (_DAT_0064342c != 0)',end))
harness += r'''
#define _DAT_0064342c WORD(0x64342c)
#define _DAT_00643430 ((short *)WORD(0x643430))
static unsigned event_bits,redraws,keys,presents,redraw_state;
__attribute__((used,noinline)) static undefined8 FUN_0043b9bc(unsigned record,short *item) {
    redraws++;redraw_state=_DAT_0064342c;return 0;
}
__attribute__((used,noinline)) static undefined8 FUN_0043bd4c(unsigned record,short *item) { keys++;return 0; }
__attribute__((used,noinline)) static undefined8 FUN_0041cfc0(void) { presents++;return 0; }
__attribute__((used,noinline)) static unsigned pump(void) {
    SHORT(0x6443d0)=1;return event_bits;
}
__attribute__((naked)) static void pump_hook(void) {
    __asm__("pushal; call pump; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void redraw_hook(void) {
    __asm__("pushal; push %edx; push %eax; call FUN_0043b9bc; add $8,%esp; popal; ret");
}
__attribute__((naked)) static void key_hook(void) {
    __asm__("pushal; push %edx; push %eax; call FUN_0043bd4c; add $8,%esp; popal; ret");
}
__attribute__((naked)) static void present_hook(void) {
    __asm__("pushal; call FUN_0041cfc0; popal; ret");
}
static void decision(unsigned state) {
    short *in_EAX=(short *)0x47a588;
    unsigned mouse_state=state,uVar11,iVar2;
'''
harness += 'if (state & 2) {' + mouse_branch + '} else {' + key_branch + '}\n}\n'
action = function(source, 'E2R_InvokeRequesterAction')
start = action.index('  if (action == (uintptr_t)&LAB_0043d47c) {')
end = action.index('  if (action == (uintptr_t)&LAB_0043d490)',start)
harness += r'''
#define DAT_0047a76c WORD(0x47a76c)
#define _DAT_006443d0 SHORT(0x6443d0)
#define _DAT_00643650 WORD(0x643650)
#define LAB_0043d47c (*(byte *)0x43d47c)
static unsigned _DAT_0073cc3c=1,DAT_0047a470=1;
static int E2R_IsReadableCurrentPointer(unsigned value) {return value!=0;}
static unsigned E2R_TraceRequesterState(const char *site,unsigned value) {return value;}
static int save_dispatch(uintptr_t action) {
'''
harness += action[start:end] + 'return 0;\n}\n'
harness += 'static void geometry(short *in_EAX) {short sVar6;\n' + geometry + '\n}\n'
harness += 'static void title(short *in_EAX,const char *text) {short sVar6=strlen(text)*DAT_0047a408;\n' + title_call + '\n}\n'
harness += 'static void title_redraw(short *in_EAX,const char *text) {short sVar6=strlen(text)*DAT_0047a408;\n' + redraw_title_call + '\n}\n'
for i, (start, end) in enumerate(((0x419af4, 0x41ab4c), (0x477068, 0x479caa),
                                 (0x47a588, 0x47a5c0), (0x43b3c3, 0x43b46d),
                                 (0x43b58b, 0x43b5dd), (0x43b660, 0x43b6ce),
                                 (0x43b8b4,0x43b8cd), (0x43d47c,0x43d490), (0x43b09f,0x43b0f4))):
    data = image.code(start, end)
    harness += f'static const byte data{i}[]={{' + ','.join(map(str, data)) + '};\n'
harness += r'''
__attribute__((naked)) static void title_hook(void) {
    __asm__("mov %edx,title_x; mov %ebx,title_y; ret");
}
static void map(unsigned address,unsigned size) {
    assert(mmap((void *)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)address);
}
__attribute__((naked)) static void lock_hook(void) {
    __asm__("movl $704,(%edx); mov $expected,%eax; ret");
}
__attribute__((naked)) static void unlock_hook(void) { __asm__("ret"); }
__attribute__((naked)) static void original_font(const byte *text) {
    __asm__("pushal; mov 36(%esp),%edx; push $0; push $0; mov $2,%eax; mov $1,%ecx; "
            "xor %ebx,%ebx; mov $0x419af4,%edi; call *%edi; popal; ret");
}
static void hook(unsigned address,void *target) {
    *(byte *)address=0xe9;*(int32_t *)(address+1)=(int32_t)target-address-5;
}
int main(int argc,char **argv) {
    assert(argc==2 && !chdir(argv[1]));
    map(0x410000,0x10000);map(0x430000,0x10000);map(0x470000,0x10000);
    map(0x630000,0x10000);map(0x640000,0x10000);
    memcpy((void *)0x419af4,data0,sizeof data0);
    memcpy((void *)0x477068,data1,sizeof data1);
    hook(0x418a04,lock_hook);hook(0x418b00,unlock_hook);
    memcpy((void *)0x43b3c3,data3,sizeof data3);*(byte *)(0x43b3c3+sizeof data3)=0xc3;
    memcpy((void *)0x43b58b,data4,sizeof data4);*(byte *)(0x43b58b+sizeof data4)=0xc3;
    hook(0x41b078,title_hook);
    memcpy((void *)0x43b09f,data8,sizeof data8);*(byte *)(0x43b09f+sizeof data8)=0xc3;
    memcpy((void *)0x43b660,data5,sizeof data5);*(byte *)(0x43b660+sizeof data5)=0xc3;
    hook(0x41ba7c,pump_hook);hook(0x43b9bc,redraw_hook);
    hook(0x43bd4c,key_hook);hook(0x41cfc0,present_hook);
    for(unsigned state=0;state<8;state++)for(unsigned edit=0;edit<3;edit++) {
        event_bits=state;_DAT_0064342c=edit;SHORT(0x6443d0)=0;
        redraws=keys=presents=redraw_state=0;
        struct E2R_Registers regs={.esi=0x47a588};
        e2r_original_call(0x43b660,&regs);
        unsigned expected[]={redraws,keys,presents,redraw_state,_DAT_0064342c};
        _DAT_0064342c=edit;redraws=keys=presents=redraw_state=0;
        decision(state);
        unsigned actual[]={redraws,keys,presents,redraw_state,_DAT_0064342c};
        if(memcmp(expected,actual,sizeof expected)) {
            fprintf(stderr,"state=%u edit=%u expected=%u,%u,%u,%u,%u actual=%u,%u,%u,%u,%u\n",
                state,edit,expected[0],expected[1],expected[2],expected[3],expected[4],
                actual[0],actual[1],actual[2],actual[3],actual[4]);abort();
        }
    }
    puts("PASS: 24 original-x86 mouse/edit-state decisions; mouse flags never enable the fixed-label caret");
    memcpy((void *)0x43b8b4,data6,sizeof data6);*(byte *)(0x43b8b4+sizeof data6)=0xc3;
    memcpy((void *)0x43d47c,data7,sizeof data7);hook(0x43adc0,unlock_hook);
    SHORT(0x643cb4)=0x2000;_DAT_006443d0=0;_DAT_00643650=5;DAT_0047a76c=0;
    struct E2R_Registers save_regs={.esi=0x47a588,.ebx=0x643ca4};
    e2r_original_call(0x43b8b4,&save_regs);e2r_original_call(0x43d47c,&save_regs);
    unsigned expected_exit=_DAT_006443d0,expected_state=_DAT_00643650;
    _DAT_006443d0=0;_DAT_00643650=5;
    assert(save_dispatch(0x43d47c));
    assert(_DAT_006443d0==expected_exit && _DAT_00643650==expected_state);
    puts("PASS: original closing Save-button contract transfers requester ownership to state 3");
    short *record=(short *)0x47a588;unsigned geometry_cases=0;
    for(unsigned mode=0;mode<2;mode++)for(unsigned kind=0;kind<2;kind++)
    for(unsigned position=0;position<3;position++)for(unsigned length=0;length<50;length++) {
        char label[51];memset(label,'X',length);label[length]=0;
        DAT_0047a43c=mode;DAT_0047a408=mode?12:6;DAT_0047a40c=mode?12:8;
        _DAT_006401ec=mode?640:320;_DAT_006401d4=mode?480:240;
        memcpy(record,data2+kind*28,28);record[0]=position==0?-1:10;
        record[1]=position==1?-1:20;*(char **)(record+4)=label;
        struct E2R_Registers registers={.esi=(unsigned)record};
        e2r_original_call(0x43b3c3,&registers);
        short expected_bounds[14];memcpy(expected_bounds,record,28);
        e2r_original_call(0x43b58b,&registers);
        int x=title_x,y=title_y;
        E2R_InitRequesterRecord((uintptr_t)record,position==0?-1:10,position==1?-1:20,
                               WIDTH(kind),HEIGHT(kind),(uintptr_t)label,0);
        geometry(record);
        assert(!memcmp(record,expected_bounds,8));
        assert(!memcmp(record+8,expected_bounds+8,12));
        title(record,label);assert(title_x==x && title_y==y);
        e2r_original_call(0x43b09f,&registers);x=title_x;y=title_y;
        title_redraw(record,label);assert(title_x==x && title_y==y);geometry_cases++;
    }
    printf("PASS: %u original-x86 requester bounds/initial and repainted title-position cases using original static main/slot dimensions\n",geometry_cases);
    DAT_0047a43c=1;DAT_0047a408=12;_DAT_006401ec=640;_DAT_006401d4=480;
    byte loaded[sizeof data1];
    assert(E2R_ReadOriginalImageData(0x477068,loaded,sizeof loaded));
    assert(!memcmp(loaded,data1,sizeof loaded));
    assert(!E2R_ReadOriginalImageData(0x3fffff,loaded,sizeof loaded));
    assert(!E2R_ReadOriginalImageData(0xffffffff,loaded,sizeof loaded));
    assert(!E2R_ReadOriginalImageData(0x477068,loaded,0));
    unsigned cases=0;
    for(unsigned style=0;style<2;style++)for(unsigned mode=1;mode<=2;mode++)
    for(unsigned color=0;color<16;color+=5)for(unsigned ch=32;ch<127;ch++) {
        byte text[2]={ch,0};DAT_0047a279=style<<24;
        memset(expected,0xa5,sizeof expected);memset(pages,0xa5,sizeof pages);
        SHORT(0x6366a8+style*2)=mode;SHORT(0x6366dc+style*2)=color;
        SHORT(0x6366e8+style*2)=15;
        /* Original EAX=2, production routes the same style to both hosted pages. */
        SHORT(0x6366a8+4)=mode;SHORT(0x6366dc+4)=color;SHORT(0x6366e8+4)=15;
        SHORT(0x6366c4+4)=12;SHORT(0x6366d0+4)=20;
        original_font(text);
        unsigned cursor=SHORT(0x6366c4+4);
        SHORT(0x6366c4+(style+2)*2)=12;SHORT(0x6366d0+(style+2)*2)=20;
        E2R_DrawHostedText(text);
        for(unsigned page=0;page<2;page++)
            assert(e2r_memory_equal("original high-resolution font/pitch/canaries",expected,pages[page],sizeof expected));
        assert(SHORT(0x6366c4+(style+2)*2)==cursor);cases++;
    }
    printf("PASS: %u original-x86 ASCII glyph/color/mode/style cases on both hosted pages; original font asset reads and invalid ranges\n",cases);
}
'''
# run_fixture runs without arguments: supply the installation directory in main.
dimensions=[]
for address in ('0047a588','0047a5a4'):
    match=re.search(r'E2R_InitRequesterRecord\(0x'+address+r',-1,-1,(0x[0-9a-f]+),(0x[0-9a-f]+),',source)
    dimensions.append(tuple(int(value,16) for value in match.groups()))
harness=harness.replace('WIDTH(kind)',f'(kind?{dimensions[1][0]}:{dimensions[0][0]})')
harness=harness.replace('HEIGHT(kind)',f'(kind?{dimensions[1][1]}:{dimensions[0][1]})')
harness = harness.replace('assert(argc==2 && !chdir(argv[1]));',
                          'assert(!chdir(' + json.dumps(str(image.path.parent)) + '));')
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('font surface lock/unlock; isolated 704-byte pitch pages',
                          'installed PE font data read only; preserved-ECX event pump and draw/key services intercepted'))
