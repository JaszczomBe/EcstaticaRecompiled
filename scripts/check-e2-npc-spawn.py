#!/usr/bin/env python3
"""Compare NPC range selection and placement with original i386 code.

RNG, queries, actor loading and activation are intercepted. Verifies call inputs,
terrain routing, overlap rejection, nine floor samples and persistent fields;
does not validate asset loading, AI, rendering or the full population update.
"""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe',type=Path)
parser.add_argument('--cc',default='clang-21')
parser.add_argument('--asan',action='store_true')
parser.add_argument('--keep-harness',type=Path)
args=parser.parse_args()
pe=args.exe.read_bytes();h=struct.unpack_from('<I',pe,60)[0];n=struct.unpack_from('<H',pe,h+6)[0];opt=struct.unpack_from('<H',pe,h+20)[0]
def original(a,z):
    for i in range(n):
        _,va,size,raw=struct.unpack_from('<IIII',pe,h+24+opt+i*40+8);va+=0x400000
        if va<=a<z<=va+size:return pe[raw+a-va:raw+z-va]
    raise ValueError(a)
source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
def function(name):
    start=source.rfind('\n',0,source.index(name+'(',source.index('/* '+name[4:]+' */')))+1
    return source[start:source.index('\n}',start)+2]
harness=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort;
typedef uint8_t byte;
#define __fastcall
static uintptr_t DAT_0047a470,_DAT_0063726c;
static int E2R_actor_calc_context,E2R_actor_load_id_override=-1;
static int rng_calls,query_calls,load_calls,unlinks,activations,poses;
static int range_first,range_count,range_calls,load_id;
static int visibility,cell_missing,terrain,spawn_mode,selector_mode,random_value;
static short queries[32][3];
static int record_query(uint coord) {
    assert(query_calls<32);memcpy(queries[query_calls],(void*)coord,6);
    int count=query_calls++;
    return spawn_mode==3 && count>4?110:100;
}
static uint64_t FUN_0045fc10(uint a,uint b) { rng_calls++;return ((uint64_t)b<<32)|(uint)random_value; }
static int FUN_00448a3c(uint coord,uint actor) { assert(actor==0);return record_query(coord); }
static int64_t FUN_0044d28c(uint coord,uint actor) { assert(actor==0);return visibility; }
static uint64_t FUN_00448744(uint coord,ushort *actor) { assert(!actor);return cell_missing?-1:0; }
static void FUN_00451f5c(void) {
    assert(E2R_actor_load_id_override>=0);load_id=E2R_actor_load_id_override;load_calls++;
    E2R_actor_load_id_override=-1;
}
static void FUN_00426ca4(void) { assert(E2R_actor_calc_context==0x901000);unlinks++; }
static void FUN_00420dcc(void) { assert(E2R_actor_calc_context==0x901000);poses++; }
static void FUN_00426c3c(void) { assert(E2R_actor_calc_context==0x901000);activations++; }
static uint choose_range(uint first,uint count) {
    range_first=first;range_count=count;range_calls++;
    return spawn_mode?0x901000:0;
}
'''
harness+=function('FUN_0044db80').replace('FUN_0044db80(', 'native_range(')+'\n'
harness+='static uint FUN_0044db80(uint first,uint count) { return choose_range(first,count); }\n'
harness+=function('FUN_0044dca4')+'\n'
harness+=r'''
__attribute__((used,noinline)) static uint rand_hook(void) { rng_calls++;return random_value; }
__attribute__((used,noinline)) static uint load_hook(uint actor) { load_id=actor;load_calls++;return 0; }
__attribute__((used,noinline)) static uint unlink_hook(uint actor) { assert(actor==0x901000);unlinks++;return 0; }
__attribute__((used,noinline)) static uint pose_hook(uint actor) { assert(actor==0x901000);poses++;return 0; }
__attribute__((used,noinline)) static uint activate_hook(uint actor) { assert(actor==0x901000);activations++;return 0; }
__attribute__((used,noinline)) static uint floor_hook(uint coord) { return record_query(coord); }
__attribute__((used,noinline)) static uint visible_hook(uint coord) { return visibility; }
__attribute__((used,noinline)) static uint cell_hook(uint coord) { return cell_missing?-1:0; }
#define HOOK(name,fn) __attribute__((naked)) static void name(void) { __asm__("pushal; push %eax; call " #fn "; add $4,%esp; mov %eax,28(%esp); popal; ret"); }
HOOK(random_entry,rand_hook)
HOOK(load_entry,load_hook)
HOOK(unlink_entry,unlink_hook)
HOOK(pose_entry,pose_hook)
HOOK(activate_entry,activate_hook)
HOOK(floor_entry,floor_hook)
HOOK(visible_entry,visible_hook)
HOOK(cell_entry,cell_hook)
__attribute__((naked)) static void range_entry(void) {
    __asm__("pushal; push %edx; push %eax; call choose_range; add $8,%esp; mov %eax,28(%esp); popal; ret");
}
static void map(int a,int size) { assert(mmap((void*)a,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED); }
static void jump(int a,void *fn) { *(byte*)a=0xe9;*(int*)(a+1)=(intptr_t)fn-a-5; }
static void setup(int t,int flags,int mode,int vis,int missing,int variant) {
    memset((void*)0x640000,0,0x20000);memset((void*)0x660000,0xa5,0x10000);memset((void*)0x670000,0,0x4000);
    memset((void*)0x900000,0,0x10000);
    DAT_0047a470=*(uint*)0x47a470=0x900000;
    short *joe=(short*)0x900000,*spawn=(short*)0x901000;
    joe[0x42]=variant==2?-5:variant?32760:9000;joe[0x43]=3300;joe[0x44]=variant?-32760:-17000;
    spawn[0]=64;spawn[0x4d]=200;spawn[0x43]=150;
    *(ushort*)0x64a1f8=0x40;*(byte*)0x670c42=flags?8:0;
    *(uint*)0x630c60=mode?0x901000:0;
    for(int i=0;i<256;i++)*(uint*)(0x630b60+i*4)=0x901000;
    _DAT_0063726c=*(uint*)0x63726c=mode==2?0x902000:0;
    short *neighbor=(short*)0x902000;
    neighbor[0x4d]=30000;neighbor[0x42]=joe[0x42];neighbor[0x44]=joe[0x44];
    terrain=t;*(byte*)0x68cd6c=t;spawn_mode=mode;visibility=vis;cell_missing=missing;
    random_value=variant?0x4001:0x4000;
    rng_calls=query_calls=load_calls=unlinks=activations=poses=range_calls=0;
    range_first=range_count=load_id=-1;memset(queries,0,sizeof queries);
    E2R_actor_calc_context=0x903000;E2R_actor_load_id_override=-1;
}
struct Snapshot { byte actor[0x200],flags[0x20000],state[0x4000],saved[0x10000];short points[32][3];int r,q,l,u,a,p,rf,rc,rr,id; };
static void snapshot(struct Snapshot *s) {
    memset(s,0,sizeof(*s));memcpy(s->saved,(void*)0x660000,sizeof s->saved);
    memcpy(s->actor,(void*)0x901000,sizeof s->actor);memcpy(s->flags,(void*)0x640000,sizeof s->flags);
    memcpy(s->state,(void*)0x670000,sizeof s->state);memcpy(s->points,queries,sizeof queries);
    s->r=rng_calls;s->q=query_calls;s->l=load_calls;s->u=unlinks;s->a=activations;s->p=poses;
    s->rf=range_first;s->rc=range_count;s->rr=range_calls;s->id=load_id;
}
static void run_original(void) { uint a=0;__asm__ volatile("call *%%edi" : "+a"(a) : "D"(0x44dca4),"c"(0),"d"(0) : "memory","cc"); }
int main(void) {
    unsetenv("E2R_DEFER_BACKGROUND_SPAWNS");
    map(0x420000,0x10000);map(0x440000,0x10000);map(0x450000,0x10000);map(0x470000,0x10000);
    map(0x630000,0x4000);map(0x637000,0x1000);map(0x640000,0x20000);map(0x660000,0x10000);
    map(0x670000,0x4000);map(0x68c000,0x2000);map(0x900000,0x10000);
    memcpy((void*)0x422aa0,copy_code,sizeof copy_code);
    memcpy((void*)0x44db80,range_code,sizeof range_code);memcpy((void*)0x44dbf4,spawn_code,sizeof spawn_code);
    jump(0x45fc10,random_entry);jump(0x451f5c,load_entry);jump(0x426ca4,unlink_entry);
    jump(0x420dcc,pose_entry);jump(0x426c3c,activate_entry);
    jump(0x448a3c,floor_entry);jump(0x44d28c,visible_entry);jump(0x448744,cell_entry);
    unsigned ranges=0,placements=0;
    // Range selector: intercept actual actor loading, retain real table/flag logic.
    for(int first=9;first<16;first++)for(int count=0;count<=15;count++)for(int active=0;active<4;active++) {
        setup(0,0,0,0,0,0);random_value=first*1973;
        for(int j=0;j<count;j++)*(byte*)(0x64a178+(first+j)*2)=(active==3 || (active==1 && !(j%2)) || (active==2 && j%2))?2:0;
        byte before[10000],expected[10000];memcpy(before,(void*)0x64a178,10000);
        uint a=first,d=count;__asm__ volatile("call *%%edi" : "+a"(a),"+d"(d) : "D"(0x44db80) : "memory","cc");
        memcpy(expected,(void*)0x64a178,10000);int calls=load_calls,id=load_id;
        memcpy((void*)0x64a178,before,10000);load_calls=0;load_id=-1;
        assert(native_range(first,count)==a && load_calls==calls && load_id==id);
        assert(!memcmp(expected,(void*)0x64a178,10000));ranges++;
    }
    jump(0x44db80,range_entry);
    for(int t=0;t<44;t++)for(int flags=0;flags<2;flags++)for(int mode=0;mode<4;mode++)for(int variant=0;variant<3;variant++) {
        setup(t,flags,mode,0,0,variant);run_original();struct Snapshot expected,actual;snapshot(&expected);
        setup(t,flags,mode,0,0,variant);FUN_0044dca4(0,0);snapshot(&actual);
        if(memcmp(&expected,&actual,sizeof expected)) { fprintf(stderr,"mismatch terrain=%d flag=%d mode=%d variant=%d q=%d/%d range=%d/%d\n",t,flags,mode,variant,expected.q,actual.q,expected.rf,actual.rf);assert(0); }
        assert(E2R_actor_calc_context==0x903000 && E2R_actor_load_id_override==-1);placements++;
    }
    for(int vis=0;vis<2;vis++)for(int missing=0;missing<2;missing++) {
        setup(0,0,0,vis,missing,0);run_original();struct Snapshot expected,actual;snapshot(&expected);
        setup(0,0,0,vis,missing,0);FUN_0044dca4(0,0);snapshot(&actual);
        assert(!memcmp(&expected,&actual,sizeof expected));placements++;
    }
    setup(35,0,1,0,0,0);struct Snapshot before,after;snapshot(&before);
    setenv("E2R_DEFER_BACKGROUND_SPAWNS","1",1);FUN_0044dca4(0,0);snapshot(&after);
    assert(!memcmp(&before,&after,sizeof before));unsetenv("E2R_DEFER_BACKGROUND_SPAWNS");
    printf("PASS: %u original-x86 NPC range cases; %u terrain/placement/overlap/floor-sampling cases\n",ranges,placements);
}
'''
at=harness.index('int main(void)')
code='static byte copy_code[]={'+','.join(map(str,original(0x422aa0,0x422ab9)))+'};\nstatic byte range_code[]={'+','.join(map(str,original(0x44db80,0x44dbf1)))+'};\nstatic byte spawn_code[]={'+','.join(map(str,original(0x44dbf4,0x44e237)))+'};\n'
harness=harness[:at]+code+harness[at:]
# The range assembly hook refers to this C symbol by name.
harness=harness.replace('static uint choose_range','__attribute__((used,noinline)) static uint choose_range')
with tempfile.TemporaryDirectory(prefix='e2-npc-spawn-') as tmp:
    c=Path(tmp)/'check.c';binary=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(binary)],check=True)
    if args.keep_harness:
        import shutil
        shutil.copyfile(c,args.keep_harness.with_suffix('.c'));shutil.copy2(binary,args.keep_harness)
    subprocess.run([str(binary)],check=True,timeout=25)
