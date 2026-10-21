#!/usr/bin/env python3
"""Compare preloaded-object placement, visibility and activation with original x86.

Uses the supplied original executable. Resource loading, pose calculation and
script/action execution are intercepted; this fixture checks their arguments,
ordering and surrounding memory, not complete gameplay or pickup behavior.
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
root = Path(__file__).resolve().parent.parent
source = (root/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
count = struct.unpack_from('<H', pe, header+6)[0]
optional = struct.unpack_from('<H', pe, header+20)[0]

def original(start, end):
    for i in range(count):
        at = header+24+optional+i*40
        _, va, size, raw = struct.unpack_from('<IIII', pe, at+8)
        va += 0x400000
        if va <= start < end <= va+size:
            return pe[raw+start-va:raw+end-va]
    raise ValueError(hex(start))

def function(name):
    match = re.search(r'^(?:void|undefined4) (?:__fastcall )?'+name+r'\([^\n]*\)\s*\{.*?\n\}', source, re.M|re.S)
    assert match, name
    return match.group()

harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8;
#define __fastcall
#define DAT_0047a470 (*(int*)0x47a470)
#define DAT_0047a7e0 (*(int*)0x47a7e0)
#define _DAT_00636588 (*(int*)0x636588)
#define _DAT_00637248 (*(int*)0x637248)
static int E2R_actor_calc_context;
static int target_id,loaded,visible_cell;
static unsigned events[128][3],event_count;
__attribute__((force_align_arg_pointer,used))
static void observe(unsigned stage,unsigned a,unsigned b) {
    assert(event_count<128);
    events[event_count][0]=stage;events[event_count][1]=a;events[event_count++][2]=b;
    if(stage==1) {
        *(int*)(0x630b60+a*4)=loaded?(a==target_id?0x900000:0x908000):0;
        DAT_0047a470=0x900000;
    }
    if(stage==8) (*(short*)(a+0x122))++;
}
static void FUN_00414e68(void) { assert(!"unexpected original error path"); }
static void E2R_LoadPopulationActor(int id) { observe(1,id,0); }
static void FUN_00420dcc(void) { observe(2,E2R_actor_calc_context,0); }
static void FUN_00426c3c(void) { observe(3,E2R_actor_calc_context,0); }
static void E2R_DispatchScriptRecord(ushort *code,ushort *actor,ushort *other,ushort *child,ushort *node) {
    assert(actor==other && !child && !node);observe(4,(uintptr_t)code,(uintptr_t)actor);
}
static undefined8 FUN_0045233c(int unused,int id) { observe(5,id,0);return (uint64_t)(uint)id<<32; }
static void FUN_0042b0f4(void) { observe(6,E2R_actor_calc_context,0); }
static void FUN_00426a80(void) { observe(7,E2R_actor_calc_context+0xa6,0); }
static void FUN_00426010(int actor) { observe(8,actor,0); }
static void FUN_0042b004(int *slot,short *actor) { observe(9,(uintptr_t)slot,(uintptr_t)actor); }
static undefined8 FUN_00451880(int unused,int id) { observe(10,id,0);return (uint64_t)(uint)id<<32; }
static int E2R_TraceCurrentActorWrite(const char *site,uintptr_t current) { return current; }
static void FUN_00422aa0(uint destination,undefined2 *src) { memcpy((void*)destination,src,6); }
static int IsBadReadPtr(const void *p,unsigned size) { return !p; }
static undefined8 FUN_004488a4(uint pos,uint unused) { observe(11,pos,0);return (uint)visible_cell; }
static void FUN_0044d608(int unused,int link) { observe(12,*(uint*)(link+0x13a),0); }
'''
# Record only defined inputs; original callees preserve the surrounding registers.
for stage, expression_a, expression_b in (
    (1, '%eax', '$0'), (2, '%eax', '$0'), (3, '%eax', '$0'),
    (4, '%eax', '%edx'), (5, '%eax', '$0'), (6, '%eax', '$0'),
    (7, '%eax', '$0'), (8, '%eax', '$0'), (9, '%eax', '%edx'),
    (10, '%eax', '$0'), (12, '%eax', '$0')):
    harness += f'__attribute__((naked)) static void hook_{stage}(void) {{ __asm__("pushfl; pushal; push {expression_b}; push {expression_a}; push ${stage}; call observe; add $12,%esp; popal; popfl; ret"); }}\n'
harness += r'''
__attribute__((naked)) static void hook_11(void) {
    __asm__("pushfl; pushal; push $0; push %eax; push $11; call observe; add $12,%esp; popal; popfl; mov visible_cell,%eax; ret");
}
static void FUN_0044d634(int actor_id);
'''
harness += function('FUN_0044d634')+'\n'
harness += function('FUN_0044d4b4').replace('FUN_0044d4b4','visibility_native').replace('FUN_0044d634(actor_id);','observe(13,actor_id,0);')+'\n'
harness += '__attribute__((naked)) static void hook_13(void) { __asm__("pushfl; pushal; push $0; push %eax; push $13; call observe; add $12,%esp; popal; popfl; ret"); }\n'
# Extract the actual production placement branch, not a parallel implementation.
a = source.index('                  if (puVar18[1] == 0x16) {', source.index('      case 0x4d:', source.index('void __fastcall FUN_0044f508(')))
b = source.index('                  else if ', a)
harness += 'static void preload_native(short *psVar16,ushort *puVar18) {\n'+source[a:b]+'}\n'
for start, end in ((0x44d634,0x44d991),(0x44d4b4,0x44d608),(0x44f8a7,0x44f8d8),(0x422aa0,0x422ab9)):
    data = original(start,end)
    harness += f'static unsigned char code_{start:x}[]={{'+','.join(map(str,data))+'};\n'
harness += r'''
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void jump(int address,void *fn) { *(byte*)address=0xe9;*(int*)(address+1)=(intptr_t)fn-address-5; }
static void original_call(int address,int actor) {
    __asm__ volatile("call *%%edi" : "+a"(actor) : "D"(address) : "ecx","edx","memory","cc");
}
static void setup(int id,int mode,int seed) {
    memset((void*)0x620000,0,0x70000);memset((void*)0x900000,0,0x10000);
    memset((void*)0x470000,0,0x10000);
    target_id=id;loaded=!(mode&1);event_count=0;
    DAT_0047a470=0x90f000;_DAT_00636588=123456;
    E2R_actor_calc_context=0;
    *(short*)0x900000=id;
    *(short*)0x900122=seed&1?-2:seed;
    *(int*)(0x630b60+id*4)=0x900000;
    *(short*)(0x65feb0+id*2)=mode&2?7:-1;
    *(int*)(0x630b60+7*4)=0x908000;
    *(int*)0x908054=0x909000;*(int*)0x90900c=0x90a000;
    *(short*)(0x6648e8+id*2)=3;
    *(short*)(0x671fc0+id*2)=seed&2?-2:seed+17;
    *(short*)(0x647a68+id*2)=71;*(char*)(0x64c950+id)=0x81;
    for(int j=0;j<3;j++) {
        *(short*)(0x669708+id*6+j*2)=seed*3-100+j;
        *(short*)(0x658980+id*6+j*2)=seed*7+100-j;
    }
    *(byte*)(0x64a178+id*2)=mode&4?4:0;
    *(short*)0x90013a=mode&8?5:-1;*(int*)(0x6297c0+5*4)=0x906000;
    ushort tracks[]={0,1,0x8001,0xc001};
    *(ushort*)(0x666ff8+id*2)=tracks[(mode>>4)&3];
    *(int*)0x62e450=0x901000;*(int*)0x901004=0x902000;
    *(short*)0x901000=0;*(byte*)0x901096=seed&4?1:0;
    *(short*)0x902000=id;*(int*)0x902006=0x903000;
    *(short*)0x903000=seed&8?3:0;
    *(int*)0x62ba20=0x904000;
    _DAT_00637248=seed&16?0x905000:0;
    *(int*)0x9050a6=0x904000;
}
int main(void) {
    map(0x420000,0x10000);map(0x440000,0x20000);map(0x470000,0x10000);
    map(0x620000,0x70000);map(0x900000,0x10000);
    memcpy((void*)0x44d634,code_44d634,sizeof code_44d634);
    memcpy((void*)0x44d4b4,code_44d4b4,sizeof code_44d4b4);
    memcpy((void*)0x44f8a7,code_44f8a7,sizeof code_44f8a7);
    memcpy((void*)0x422aa0,code_422aa0,sizeof code_422aa0);
    *(byte*)0x44f90d=0xc3;
    jump(0x451f5c,hook_1);jump(0x420dcc,hook_2);jump(0x426c3c,hook_3);
    jump(0x44f310,hook_4);jump(0x45233c,hook_5);jump(0x42b0f4,hook_6);
    jump(0x426a80,hook_7);jump(0x426010,hook_8);jump(0x42b004,hook_9);
    jump(0x451880,hook_10);jump(0x4488a4,hook_11);jump(0x44d608,hook_12);
    byte expected[0x10000],tables[0x70000],globals[0x10000];
    unsigned expected_events[128][3];int ids[]={3,177,3717,4999};unsigned cases=0;
    for(int n=0;n<4;n++) for(int mode=0;mode<64;mode++) for(int seed=0;seed<32;seed++) {
        setup(ids[n],mode,seed);
        if(mode&2)*(byte*)(0x64a178+7*2)=2;
        original_call(0x44d634,ids[n]);
        memcpy(expected,(void*)0x900000,sizeof expected);memcpy(tables,(void*)0x620000,sizeof tables);
        memcpy(globals,(void*)0x470000,sizeof globals);unsigned calls=event_count;
        memcpy(expected_events,events,sizeof events);
        setup(ids[n],mode,seed);
        if(mode&2)*(byte*)(0x64a178+7*2)=2;
        FUN_0044d634(ids[n]);
        assert(!memcmp(expected,(void*)0x900000,sizeof expected));
        assert(!memcmp(tables,(void*)0x620000,sizeof tables));
        assert(!memcmp(globals,(void*)0x470000,sizeof globals));
        assert(calls==event_count && !memcmp(expected_events,events,calls*sizeof events[0]));
        assert(E2R_actor_calc_context==0);cases++;
    }
    printf("PASS: %u original-x86 object activation field/callback/action cases\n",cases);
    jump(0x44d634,hook_13);cases=0;
    for(int n=0;n<4;n++) for(int mode=0;mode<256;mode++) {
        setup(ids[n],0,0);int actor=mode&1?0x900000:0;
        *(int*)(0x630b60+ids[n]*4)=actor;
        *(ushort*)(0x666ff8+ids[n]*2)=mode&2?0xc001:0;
        *(short*)(0x65feb0+ids[n]*2)=mode&4?7:-1;
        *(int*)0x9000f2=mode&8?0x909000:0;
        DAT_0047a470=mode&16?actor:0x90f000;
        *(int*)0x9000a6=mode&32?0x904000:0;
        *(byte*)0x90400c=mode&64?2:0;
        visible_cell=mode&128?0:-1;*(ushort*)0x68cd6a=0x4000;
        byte initial[0x10000];memcpy(initial,(void*)0x900000,sizeof initial);
        original_call(0x44d4b4,ids[n]);
        memcpy(expected,(void*)0x900000,sizeof expected);unsigned calls=event_count;
        memcpy(expected_events,events,sizeof events);
        memcpy((void*)0x900000,initial,sizeof initial);event_count=0;
        visibility_native(ids[n]);
        assert(!memcmp(expected,(void*)0x900000,sizeof expected));
        assert(calls==event_count && !memcmp(expected_events,events,calls*sizeof events[0]));cases++;
    }
    printf("PASS: %u original-x86 cached/live visibility selection cases\n",cases);
    cases=0;
    for(int n=0;n<4;n++) for(int present=0;present<2;present++) for(int seed=0;seed<128;seed++) {
        setup(ids[n],0,seed);*(int*)(0x630b60+ids[n]*4)=present?0x900000:0;
        *(short*)0x902000=ids[n];*(short*)0x906002=22;
        for(int j=0;j<3;j++) *(short*)(0x906004+j*2)=seed*577-32000+j*59;
        int child=0x902000,event=0x906000;
        __asm__ volatile("call *%%edi" : "+S"(child),"+b"(event) : "D"(0x44f8a7) : "eax","ecx","edx","memory","cc");
        memcpy(expected,(void*)0x900000,sizeof expected);memcpy(tables,(void*)0x620000,sizeof tables);
        setup(ids[n],0,seed);*(int*)(0x630b60+ids[n]*4)=present?0x900000:0;
        *(short*)0x902000=ids[n];*(short*)0x906002=22;
        for(int j=0;j<3;j++) *(short*)(0x906004+j*2)=seed*577-32000+j*59;
        preload_native((short*)0x902000,(ushort*)0x906000);
        assert(!memcmp(expected,(void*)0x900000,sizeof expected));
        assert(!memcmp(tables,(void*)0x620000,sizeof tables));cases++;
    }
    printf("PASS: %u original-x86 preload position/cache/live actor cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-object-activation-') as tmp:
    c=Path(tmp)/'check.c'; exe=Path(tmp)/'check'; c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=60)
