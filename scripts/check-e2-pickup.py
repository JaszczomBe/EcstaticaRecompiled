#!/usr/bin/env python3
"""Compare pickup model origins, selection and actor caller with original i386.

Executes original polar/angle helpers on synthetic live lists, including range,
height, candidate flags and nearest/tie selection. Animation and script execution
remain integration acceptance, outside this query fixture.
"""
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
source = (Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t ulonglong;
typedef int64_t longlong;
int E2R_IsCharacterActor(uintptr_t actor){return 0;}
#define __fastcall
#define CONCAT22(a,b) (((uint)(ushort)(a)<<16)|(ushort)(b))
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define _DAT_0063726c (*(int*)0x63726c)
'''+support()
for name in ('E2R_TransformVector14', 'E2R_PolygonAngle16', 'E2R_NpcPolar16', 'FUN_0042dc9c'):
    harness += function(source, name)+'\n'
pose = function(source, 'FUN_00423858')
start = pose.index('  int node = *(int *)(parent + 0x1e);')
end = pose.index('    if (proxy) return;', start) + len('    if (proxy) return;')
harness += function(source, 'E2R_UseProxyMesh') + '\n'
harness += 'static void model_origin_native(int parent,int param_2) {\n' + pose[start:end] + '\n}\n}\n'
for label, start, end in [('model', 0x423858, 0x423a64), ('vector', 0x45de8b, 0x45df0e), ('query', 0x42dc9c, 0x42deb8), ('polar', 0x427160, 0x427214),
                           ('angle', 0x432c64, 0x432de4), ('caller', 0x4290c4, 0x4290cc)]:
    code = image.code(start, end)
    harness += f'static const byte {label}_code[]={{'+','.join(map(str, code))+'};\n'
caller = re.search(r'lVar28 = FUN_0042dc9c\([^;]+;', function(source, 'FUN_00427584')).group()
harness += 'static uint caller_native(uint local_6c,uint uVar16) { longlong lVar28; '+caller+' return (uint)lVar28; }\n'
harness += r'''
static void map(uint at,unsigned size) {
    assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);
}
static uint next(uint *state) { *state=*state*1664525+1013904223;return *state; }
static void setup(unsigned seed,unsigned kind) {
    memset((void*)0x900000,0,0x10000);
    uint owner=0x900000;
    *(short*)(owner+0x84)=-900;*(short*)(owner+0x86)=4096;*(short*)(owner+0x88)=-10100;
    *(short*)(owner+0x92)=seed*997;
    *(short*)(owner+0x9a)=256+seed%257;
    *(uint*)(owner+0x4c)=owner+0x200;
    _DAT_0063726c=owner;
    uint angle=*(ushort*)(owner+0x92),radius=*(short*)(owner+0x9a);
    short x=*(short*)(owner+0x84)+(*(short*)(0x59b590+angle*2)*(int)radius>>14);
    short z=*(short*)(owner+0x88)+(*(short*)(0x5de590+angle*2)*(int)radius>>14);
    static const int heights[]={-201,-200,-199,99,100,399,400,401,700,701,0,200};
    for(int i=1;i<=4;i++) {
        uint actor=owner+i*0x200,model=0x904000+i*0x100;
        *(short*)actor=i;
        *(uint*)(actor+0x4c)=i<4?actor+0x200:0;
        *(uint*)(actor+0x1e)=model;
        *(ushort*)(actor+2)=0x20|(seed&1?4:0);
        *(short*)(actor+0x84)=x+(int)(next(&seed)%1601)-800;
        *(short*)(actor+0x88)=z+(int)(next(&seed)%1601)-800;
        *(short*)(model+0x1a)=4096-heights[(seed+i)%12];
    }
    uint candidate=owner+0x200,model=0x904100;
    *(short*)(candidate+0x84)=x;
    *(short*)(candidate+0x88)=z;
    *(short*)(model+0x1a)=4096-heights[kind%12];
    switch(kind/12) {
        case 0: break;
        case 1: *(ushort*)(candidate+2)=0;break;
        case 2: *(uint*)(candidate+0xf2)=0x905000;break;
        case 3: *(uint*)(candidate+0x1e)=0;break;
        case 4: *(short*)(candidate+0x84)=x+radius;break;
        case 5: *(short*)(candidate+0x84)=x+radius+1;break;
        case 6: *(short*)(candidate+0x88)=z+(radius*7)/2;break;
        case 7: *(short*)(candidate+0x88)=z+(radius*7)/2+1;break;
    }
}
int main(void) {
    map(0x420000,0x20000);map(0x450000,0x10000);map(0x470000,0x10000);map(0x590000,0x80000);
    map(0x630000,0x10000);map(0x900000,0x10000);
    memcpy((void*)0x423858,model_code,sizeof model_code);
    // Stop after the first model origin/matrix, before articulation at 0x423a64.
    *(byte*)0x423a64=0xe9;*(int*)0x423a65=0x423947-0x423a64-5;
    memcpy((void*)0x45de8b,vector_code,sizeof vector_code);
    memcpy((void*)0x42dc9c,query_code,sizeof query_code);
    memcpy((void*)0x427160,polar_code,sizeof polar_code);
    memcpy((void*)0x432c64,angle_code,sizeof angle_code);
    memcpy((void*)0x4290c4,caller_code,sizeof caller_code);*(byte*)0x4290cc=0xc3;
    for(int i=0;i<65536;i++) {
        double phase=i*6.28318/65536.0;
        *(short*)(0x59b590+i*2)=sin(phase)*16384.5;
        *(short*)(0x5de590+i*2)=cos(phase)*16384.5;
    }
    for(int i=0;i<256;i++) {
        *(byte*)(0x5fe990+i)=atan(i*0.015625)*64.0*2.0*0.3183101550488765+0.5;
        *(byte*)(0x5fe890+i)=atan(i*0.25)*64.0*2.0*0.3183101550488765+0.5;
    }
    static byte expected[0x10000];unsigned cases=0,selected=0;
    setenv("E2R_PROXY_MESH_BYPASS","1",1);
    for(uint test=0;test<4096;test++) {
        uint seed=test;
        memset((void*)0x900000,0,0x10000);
        int root=0x900000,first=0x902000,second=0x903000;
        *(short*)(root+4)=test&1?7:0;
        *(int*)(root+0x1e)=test%7?first:0;
        *(int*)(first+0xca)=test%11?second:0;
        for(int i=0;i<9;i++)*(short*)(root+6+i*2)=next(&seed)>>16;
        for(int i=0;i<3;i++) {
            *(short*)(root+0x18+i*2)=next(&seed)>>16;
            *(short*)(root+0x6e + i*2)=next(&seed)>>16;
        }
        for(int node=first;node<=second;node+=0x1000) {
            *(byte*)(node+2)=test&2?0x10:0;
            for(int i=0;i<9;i++)*(short*)(node+0xec+i*2)=next(&seed)>>16;
            for(int i=0;i<3;i++)*(short*)(node+0x2c+i*2)=next(&seed)>>16;
        }
        static byte before[0x10000];memcpy(before,(void*)root,sizeof before);
        struct E2R_Registers regs={.eax=root,.edx=(test>>2)&1};
        // Original mode 1 requires a first model before reading its sibling.
        if(!*(int*)(root+0x1e))regs.edx=0;
        e2r_original_call(0x423858,&regs);
        memcpy(expected,(void*)root,sizeof expected);
        memcpy((void*)root,before,sizeof before);
        // The existing root-reference prefix marks non-type-7 roots separately.
        if(*(short*)(root+4)!=7)*(byte*)(root+3)|=0x80;
        model_origin_native(root,(test>>2)&1);
        assert(e2r_memory_equal("first model origin",expected,(void*)root,sizeof expected));
    }
    puts("PASS: 4096 original first-model origin/matrix cases, including type 7, alternate matrix, sibling and overflow");
    for(unsigned kind=0;kind<96;kind++)for(unsigned seed=0;seed<128;seed++) {
        setup(seed,kind);
        struct E2R_Registers regs={.eax=0x900000,.edx=0x89abcdef};
        e2r_original_call(0x42dc9c,&regs);
        uint result=regs.eax;memcpy(expected,(void*)0x900000,sizeof expected);
        selected+=*(uint*)0x90012e!=0;
        setup(seed,kind);
        ulonglong actual=FUN_0042dc9c(0x900000,0x89abcdef);
        assert((uint)actual==result && (uint)(actual>>32)==0x89abcdef);
        assert(e2r_memory_equal("pickup query",expected,(void*)0x900000,sizeof expected));
        setup(seed,kind);*(uint*)0x90802a=0x900000;
        regs=(struct E2R_Registers){.ebp=0x908000,.edx=0x89abcdef};
        e2r_original_call(0x4290c4,&regs);
        result=regs.eax;
        setup(seed,kind);
        assert(caller_native(0x900000,0x89abcdef)==result);
        cases++;
    }
    printf("PASS: %u original-x86 pickup query/caller cases (%u selected), height/range/filter/nearest ownership and full actor memory\n",cases,selected);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, libraries=('-lm',), image=image,
            dependencies=('synthetic actor lists and trigonometric tables',))
