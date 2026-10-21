#!/usr/bin/env python3
"""Compare scene-grid, camera and terrain-script selection with original i386.

Includes high ceiling bytes, linked descriptors, shape masks, grid boundaries,
cached camera hints, background dispatch and the terrain script's code/actor.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path, help='Retain fixture source/executable for debugger inspection')
parser.add_argument('--replay', type=Path, action='append', default=[],
                    help='Compare recorded terrain chains/floors (default: saved courtyard samples)')
args = parser.parse_args()
if not args.replay:
    args.replay=[Path(__file__).with_name('fixtures')/'e2-courtyard-steering.json']
world=[]
for path in args.replay:
    for query in json.loads(path.read_text()):
        for floor in query['floors']:
            chain=floor['descriptors'];selected=floor['selected']
            if selected!=0xffffffff:
                desc=chain[selected-floor['cell']]
                assert not floor['actor'] or ((desc[2]|desc[3]<<8)&0x3fff)==0, 'Scripted floor requires code-pool capture'
            world.append(floor)
def c_array(value):
    return '{'+','.join(c_array(v) if isinstance(v,list) else str(v) for v in value)+'}'
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
count = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]


def original(start, end):
    for i in range(count):
        at = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(start)


source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness=r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort,undefined2;
typedef uint8_t byte,undefined1,bool;
typedef uint64_t undefined8,ulonglong;
#define __fastcall
#define true 1
#define false 0
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define CONCAT22(a,b) (((uint32_t)(uint16_t)(a)<<16)|(uint16_t)(b))
static int DAT_0047a738,DAT_0047a77c,DAT_0047a470,_DAT_0073cc3c;
static int _DAT_0047a778,DAT_0047a778;
static int DAT_0047a788,_DAT_0073ccba,resource_calls;
static volatile int transition_order __attribute__((used));
static int DAT_0047a438,DAT_0047a7ec;
static uintptr_t _DAT_006366a0;
static volatile int trigger_lookup __attribute__((used));
static volatile uint trigger_code __attribute__((used)),trigger_actor __attribute__((used)),trigger_calls __attribute__((used));
static uint64_t fixture_lookup(uint coord,uintptr_t actor) { return (uint)trigger_lookup; }
static void FUN_0044f320(uint code,ushort *actor,ushort *node) {
    assert(!node);trigger_code=code;trigger_actor=(uintptr_t)actor;trigger_calls++;
}
__attribute__((naked)) static void lookup_hook(void) { __asm__("mov trigger_lookup,%eax; ret"); }
__attribute__((naked)) static void trigger_hook(void) {
    __asm__("mov %eax,trigger_code; mov %edx,trigger_actor; incl trigger_calls; ret");
}
static void E2R_SyncSceneViewId(void) { }
static void FUN_0044c6bc(void) { transition_order=transition_order*10+1; }
static uint64_t FUN_00449b4c(uint a,uint b) { transition_order=transition_order*10+2;return 0; }
static int E2R_ActivateSelectedSceneRecord(short id) { resource_calls++;return 0; }
__attribute__((naked)) static void install_hook(void) {
    __asm__("imull $10,transition_order,%eax; incl %eax; mov %eax,transition_order; ret");
}
__attribute__((naked)) static void background_hook(void) {
    __asm__("imull $10,transition_order,%eax; add $2,%eax; mov %eax,transition_order; xor %eax,%eax; ret");
}
static int DAT_0047a34a,DAT_0064a178,_DAT_0063726c;
static int fallback_resource,fallback_calls;
static uint64_t FUN_0043a6e0(uint32_t resource,uint32_t retained) { fallback_resource=resource;fallback_calls++;return 0; }
__attribute__((naked)) static void fallback_hook(void) { __asm__("mov %eax,fallback_resource; incl fallback_calls; ret"); }
static unsigned E2R_actor_loop_diag_count,E2R_scene_lookup_diag_count;
static int E2R_RuntimeDiagEnabled(void) { return 0; }
static int E2R_ActionIndexProbeEnabled(void) { return 1; }
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
static void E2R_LogSceneGridProbe(const char *s,int x,int z) { }
"""
for name in ('FUN_00448744','FUN_004488a4'):
    match=re.search(r'^undefined8 __fastcall '+name+r'\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
    assert match,name;harness+=match.group()+'\n'
match=re.search(r'^int __fastcall FUN_00448a48\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
assert match
harness+=match.group().replace('FUN_00448744(param_1,param_2)',
    'FUN_00448744(param_1,(ushort *)(uintptr_t)param_2)').replace(
    'psVar6 != DAT_0047a470','(uintptr_t)psVar6 != (uintptr_t)DAT_0047a470')+'\n'
match=re.search(r'^undefined4 __fastcall FUN_00448a3c\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
assert match
harness+=match.group()+'\n'
floor_code=original(0x448a3c,0x448bdd)
harness+='static unsigned char floor_code[]={'+','.join(map(str,floor_code))+'};\n'
at=source.index('  if (sVar2 < 1) {',source.index('void __fastcall FUN_0044c224('))
end=source.index('  DAT_0047a788 = 1;',at)
branch=source[at:end]
# Keep only the no-view branch; the following matching-view reset is outside it.
branch=branch[:branch.rfind('  }')+3]
harness+='static void no_view_native(void) { int iVar1; short sVar2=0; uint uVar3=0;\n'+branch+'\njoined_r0x0044c464: return; }\n'
at=source.index('  if ((int)uVar7 < 0) {',source.index('void __fastcall FUN_0044c224('))
end=source.index('  sVar2 = (short)uVar3;',at)
harness+='static short camera_native(int lookup) { int iVar1; uint uVar3; undefined2 extraout_var=0; undefined8 uVar7=(uint)lookup;\n'+source[at:end]+'\nreturn (short)uVar3; }\n'
camera_code=original(0x44c243,0x44c2ba)
harness+='static unsigned char camera_code[]={'+','.join(map(str,camera_code))+'};\n'
at=source.index('  DAT_0047a788 = 1;',end)
end=source.index('  if ((int)lVar8 != 0) {',at)
harness+='static void transition_native(short sVar2) { uint extraout_ECX=0,extraout_EDX=0; uint64_t lVar8;\n'+source[at:end]+'\n}\n'
transition_code=original(0x44c2e5,0x44c302)
harness+='static unsigned char transition_code[]={'+','.join(map(str,transition_code))+'};\n'
match=re.search(r'^void __fastcall FUN_0044c164\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
assert match
trigger=re.sub(r'#if defined\(__SANITIZE_ADDRESS__\).*?#endif\n','',match.group(),flags=re.S)
harness+=trigger.replace('FUN_00448744(', 'fixture_lookup(')+'\n'
trigger_code=original(0x44c164,0x44c221)
harness+='static unsigned char trigger_code_bytes[]={'+','.join(map(str,trigger_code))+'};\n'
fallback_code=original(0x44c440,0x44c45d)
harness+='static unsigned char fallback_code[]={'+','.join(map(str,fallback_code))+'};\n'
code=original(0x44872c,0x4489ec)
harness+='static unsigned char original_code[]={'+','.join(map(str,code))+'};\n'
harness+=r"""
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static uint64_t run_original(int fn,uintptr_t coord,uintptr_t actor) {
    __asm__ volatile("call *%%edi" : "+a"(coord),"+d"(actor) : "D"(fn) : "memory","cc");
    return ((uint64_t)actor<<32)|coord;
}
static uint32_t rng=0x7412;
static unsigned next(void) { rng=rng*1664525+1013904223;return rng; }
static short camera_original(int lookup) {
    uint selected=0x12345678,scratch1,scratch2;
    __asm__ volatile("call *%%edi" : "+a"(lookup),"+c"(selected),"=d"(scratch1),"=b"(scratch2)
                     : "D"(0x44c243) : "memory","cc");
    return (short)selected;
}
static void transition_original(short id) {
    uint a,b,c=(ushort)id,d;
    __asm__ volatile("call *%%edi" : "=a"(a),"=b"(b),"+c"(c),"=d"(d)
                     : "D"(0x44c2e5) : "memory","cc");
}
static int floor_original(uint coord,uint actor,int *surface) {
    uint scratch;
    __asm__ volatile("call *%%edi" : "+a"(coord),"+d"(actor),"+b"(surface),"=c"(scratch)
                     : "D"(0x448a48) : "memory","cc");
    return (int)coord;
}
int main(void) {
    map(0x430000,0x20000);map(0x470000,0x10000);map(0x680000,0xb0000);map(0x640000,0x10000);map(0x620000,0x20000);map(0x730000,0x10000);map(0x900000,0x1000);
    memcpy((void*)0x44872c,original_code,sizeof original_code);
    memcpy((void*)0x44c243,camera_code,sizeof camera_code);*(byte*)0x44c2ba=0xc3;
    memcpy((void*)0x44c2e5,transition_code,sizeof transition_code);*(byte*)0x44c302=0xc3;
    *(byte*)0x44c6bc=0xe9;*(int*)0x44c6bd=(intptr_t)install_hook-0x44c6c1;
    *(byte*)0x449b4c=0xe9;*(int*)0x449b4d=(intptr_t)background_hook-0x449b51;
    memcpy((void*)0x44c440,fallback_code,sizeof fallback_code);*(byte*)0x44c45d=0xc3;
    *(byte*)0x43a6e0=0xe9;*(int*)0x43a6e1=(intptr_t)fallback_hook-0x43a6e5;
    for(int mode=0;mode<2;mode++) for(int dead=0;dead<2;dead++) {
        DAT_0047a34a=*(short*)0x47a34a=mode;
        DAT_0064a178=*(byte*)0x64a178=dead?4:0;
        fallback_calls=0;fallback_resource=-1;
        run_original(0x44c440,0,0);
        int expected_calls=fallback_calls,expected_resource=fallback_resource;
        fallback_calls=0;fallback_resource=-1;no_view_native();
        assert(fallback_calls==expected_calls && fallback_resource==expected_resource);
        if(!mode && !dead)assert(fallback_resource==7);
    }
    unsigned cases=0,high=0;short *coord=(short*)0x900000;
    memset((void*)0x684d68,0xff,0x8000);
    for(int sample=0;sample<8192;sample++) {
        coord[0]=(short)next();coord[1]=(short)next();coord[2]=(short)next();
        if(sample<16) { coord[0]=sample&1?-32768:32767;coord[2]=sample&2?-32768:32767; }
        DAT_0047a738=*(int*)0x47a738=sample%9;
        uintptr_t cell=0x684d68+((coord[0]>>9)+64)*2+((coord[2]>>9)+64)*256;
        *(ushort*)cell=sample%17?0:0xffff;
        for(int i=0;i<8;i++) {
            byte *desc=(byte*)0x68cd68+i*12;
            memset(desc,0,12);desc[0]=next()>>24;desc[1]=sample%64;
            desc[5]=next()>>24;desc[7]=next()>>24;
            if(desc[5]>=128)high++;
            if(i==7)desc[3]=0x80;
        }
        for(int mode=0;mode<2;mode++) {
            uint64_t expected=run_original(mode?0x4488a4:0x448744,(uintptr_t)coord,0x900100);
            uint64_t actual=mode?FUN_004488a4((uintptr_t)coord,0x900100):FUN_00448744((uintptr_t)coord,(ushort*)0x900100);
            assert(actual==expected);cases++;
        }
        *(ushort*)cell=0xffff;
    }
    unsigned cameras=0;
    DAT_0047a470=*(int*)0x47a470=0x900100;
    for(int sample=0;sample<16384;sample++) {
        int lookup=sample%17?sample%8:-1;
        *(short*)0x900186=(short)next();
        DAT_0047a738=*(int*)0x47a738=sample%9;
        byte *desc=(byte*)0x68cd68+(lookup<0?0:lookup)*12;
        desc[0]=next()>>24;
        *(ushort*)(desc+8)=next()>>16;
        *(ushort*)(desc+10)=next()>>16;
        int hint=sample%4==0?-1:(sample%4==1?175:(int)next());
        _DAT_0047a778=*(int*)0x47a778=hint;
        /* Ghidra's word alias is separate generated storage: poison it so
         * this fixture catches reads that do not use the real cached dword. */
        DAT_0047a778=~hint;
        short expected=camera_original(lookup);
        int expected_hint=*(int*)0x47a778;
        short actual=camera_native(lookup);
        assert(actual==expected && _DAT_0047a778==expected_hint);cameras++;
    }
    for(int id=1;id<1200;id++) {
        transition_order=0;*(ushort*)0x47a788=0;*(ushort*)0x73ccba=0;
        transition_original(id);
        int expected_order=transition_order;
        assert(expected_order==12 && *(ushort*)0x47a788==1 && *(ushort*)0x73ccba==id);
        transition_order=0;DAT_0047a788=0;_DAT_0073ccba=0;resource_calls=0;
        transition_native(id);
        assert(transition_order==expected_order && DAT_0047a788==1 && _DAT_0073ccba==id && resource_calls==0);
    }
    memcpy((void*)0x44c164,trigger_code_bytes,sizeof trigger_code_bytes);
    *(byte*)0x448744=0xe9;*(int*)0x448745=(intptr_t)lookup_hook-0x448749;
    *(byte*)0x44f310=0xe9;*(int*)0x44f311=(intptr_t)trigger_hook-0x44f315;
    unsigned triggers=0,triggered=0;
    for(int sample=0;sample<16384;sample++) {
        DAT_0047a470=*(int*)0x47a470=sample%19?0x900100:0;
        *(short*)0x900182=sample%13?0:11;
        DAT_0047a438=*(int*)0x47a438=sample%23?0:1;
        *(short*)0x900186=(short)next();
        DAT_0047a738=*(int*)0x47a738=sample%9;
        trigger_lookup=sample%17?sample%8:-1;
        byte *desc=(byte*)0x68cd68+(trigger_lookup<0?0:trigger_lookup)*12;
        desc[0]=next()>>24;*(ushort*)(desc+2)=next()>>16;desc[6]=next()>>24;
        int code_index=(*(ushort*)(desc+2)&0x3fff)-1;
        if(code_index>=0)*(uint*)(0x6297c0+code_index*4)=sample%7?0x900200+sample*2:0;
        trigger_calls=trigger_code=trigger_actor=0;*(int*)0x47a7ec=0x1234;
        run_original(0x44c164,0,0);
        uint expected_calls=trigger_calls,expected_code=trigger_code,expected_actor=trigger_actor;
        int expected_flags=*(int*)0x47a7ec;
        trigger_calls=trigger_code=trigger_actor=0;DAT_0047a7ec=0x1234;
        FUN_0044c164(0);
        assert(trigger_calls==expected_calls && trigger_code==expected_code && trigger_actor==expected_actor && DAT_0047a7ec==expected_flags);
        triggers++;triggered+=trigger_calls;
    }
    assert(triggered>1000);
    memcpy((void*)0x44872c,original_code,sizeof original_code);
    memcpy((void*)0x448a3c,floor_code,sizeof floor_code);
    memset((void*)0x684d68,0xff,0x8000);
    WORLD_REPLAY
    printf("PASS: %u original-x86 scene-grid selection cases (%u high ceiling descriptors); %u camera/hint cases; 1199 camera/background dispatch cases; %u grid-script cases (%u dispatched); 4 no-view fallback routing cases; %u recorded floor cases\n",cases,high,cameras,triggers,triggered,WORLD_COUNT);
}
"""
world_code=[]
for floor in world:
    p=floor['coord'];chain=floor['descriptors'];cell=floor['cell'];shift=floor['shift']
    world_code.append('{\nshort coord[3]='+c_array(p)+';\n')
    world_code.append(f'DAT_0047a738=*(int*)0x47a738={shift};\n')
    world_code.append('DAT_0047a470=*(int*)0x47a470=0x900100;\n')
    cell_addr=0x684d68+((p[0]>>9)+64)*2+((p[2]>>9)+64)*256
    world_code.append(f'*(ushort*){cell_addr}={cell};\n')
    if chain:
        world_code.append('const byte chain[]='+c_array([b for d in chain for b in d])+';\n')
        world_code.append(f'memcpy((void*){0x68cd68+cell*12},chain,sizeof chain);\n')
    if floor['selected']!=0xffffffff:
        desc=chain[floor['selected']-cell];terrain=desc[6] if desc[6]<128 else desc[6]-256
        world_code.append(f'*(byte*){0x636624+terrain*2}={floor["terrain_flags"]};\n')
    owner='0x900100' if floor['actor'] else '0'
    surface='&surface' if floor['terrain'] else 'NULL'
    world_code.append(f'undefined8 lookup=run_original(0x448744,(uintptr_t)coord,{owner});\n')
    world_code.append(f'assert((uint)lookup=={floor["selected"]}u && lookup==FUN_00448744((uintptr_t)coord,(ushort*){owner}));\n')
    world_code.append(f'int surface=-123;int expected=floor_original((uintptr_t)coord,{owner},{surface});\n')
    world_code.append(f'assert(expected=={floor["floor"]});\n')
    if floor['terrain']:world_code.append(f'assert(surface=={floor["surface"]});\n')
    world_code.append('surface=-123;\n')
    world_code.append(f'int actual=FUN_00448a48((uintptr_t)coord,{owner},{surface});assert(actual==expected);\n')
    if floor['terrain']:world_code.append(f'assert(surface=={floor["surface"]});\n')
    world_code.append(f'assert((int)run_original(0x448a3c,(uintptr_t)coord,{owner})==expected);\n')
    world_code.append(f'assert((int)FUN_00448a3c((uintptr_t)coord,{owner})==expected);\n')
    world_code.append(f'*(ushort*){cell_addr}=0xffff;\n}}\n')
harness=harness.replace('WORLD_REPLAY',''.join(world_code)).replace('WORLD_COUNT',str(len(world)))
with tempfile.TemporaryDirectory(prefix='e2-grid-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie','-Wno-shift-op-parentheses',*flags,str(c),'-o',str(exe)],check=True)
    if args.keep_harness:
        import shutil
        shutil.copyfile(c,args.keep_harness.with_suffix('.c'));shutil.copy2(exe,args.keep_harness)
    subprocess.run([str(exe)],check=True,timeout=20)
