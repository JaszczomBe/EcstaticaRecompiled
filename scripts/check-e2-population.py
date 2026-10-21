#!/usr/bin/env python3
"""Check binary actor lookup and construction/initial-code contracts against x86.

Uses the user's original EXE and archive; no game data is copied into the repo.
The constructor and script entry compare extracted production code to original
instructions with only allocation and script execution intercepted.
"""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe',type=Path)
parser.add_argument('archive',type=Path)
parser.add_argument('--cc',default='clang-21')
parser.add_argument('--asan',action='store_true')
args=parser.parse_args()
source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
pe=args.exe.read_bytes();header=struct.unpack_from('<I',pe,0x3c)[0]
count=struct.unpack_from('<H',pe,header+6)[0];optional=struct.unpack_from('<H',pe,header+20)[0]
def original(start,end):
    for i in range(count):
        at=header+24+optional+i*40
        _,va,size,raw=struct.unpack_from('<IIII',pe,at+8);va+=0x400000
        if va<=start<end<=va+size:return pe[raw+start-va:raw+end-va]
    raise ValueError(hex(start))
def function(name):
    match=re.search(r'(?:static )?(?:int|void|short) '+name+r'\([^)]*\)\s*\{.*?\n\}',source,re.S)
    assert match,name
    return match.group()
# The original pedestal companion must contain these two actor tracks. Keep
# this evidence tied to the user's assets rather than checking fabricated NPCs.
archive=args.archive.read_bytes()
scene_signature=struct.pack('>5H',25,101,175,0xffff,0xffff)
scene=archive.find(scene_signature)
assert scene>=0 and archive[scene-54:scene-50]==b'FANT'
next_resource=archive.find(b'FANT',scene+len(scene_signature))
companion=archive[scene-54:next_resource]
for actor,local_id,position in ((284,907,(8560,3968,-16456)),(293,930,(7276,3600,-18672))):
    assert struct.pack('>5H',26,0xffff,local_id,2,actor) in companion
    assert struct.pack('>3h',*position) in companion
names=args.archive.parent.parent/'Code/ECSTATIC.FAN'
if names.exists():
    raw=names.read_bytes();cursor=34;pools=[]
    for table in range(7):
        entries=[]
        while raw[cursor]:
            end=raw.index(0,cursor);entries.append(raw[cursor:end].decode('ascii'));cursor=end+1
        cursor+=1;pools.append(entries)
    assert pools[1][284]=='gob3' and pools[1][293]=='gob3b'
    assert pools[3][101]=='St_gobsc'
    assert pools[6][1390]=='dav:skipsc' and pools[6][1393]=='dav:stgob'
print('PASS: original St_gobsc camera 175, gob3/gob3b identities, tracks and initial positions')

harness=r"""
#include <stdint.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1,bool;
#define true 1
#define false 0
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4;
typedef uint64_t undefined8,ulonglong;
static uintptr_t DAT_0047a724,DAT_0047a470;
static short DAT_00479e4c;
static uintptr_t _DAT_0063726c;
static int E2R_actor_calc_context,DAT_0047a34a,_DAT_00636588;
static void FUN_0044f310(void) { assert(0); }
#define CONCAT44(a,b) (((uint64_t)(uint)(a)<<32)|(uint)(b))
#define E2R_STREAM_MAGIC 0x45525354u
static int IsBadReadPtr(void *p,uint size) { return p==NULL; }
static int E2R_IsBadWritePtr(void *p,uint size) { return p==NULL; }
static int E2R_actor_resource_name_context = 71;
static uint FUN_00426478(uint a,int b) { return 0x900100; }
static int wander_calls,wander_mask;
static short wander_points[6][3];
__attribute__((regparm(2),used,noinline)) static uint wander_floor(uint coord,uint actor) {
  assert(wander_calls<6);memcpy(wander_points[wander_calls],(void*)coord,6);
  int height=*(short*)(actor+0x86);
  if(wander_mask & (1u<<(wander_calls/2)))height+=257;
  wander_calls++;return height;
}
__attribute__((naked)) static void wander_floor_hook(void) {
  __asm__("push %ecx; push %edx; call wander_floor; pop %edx; pop %ecx; ret");
}
static uint FUN_00448a3c(uint coord,uint actor) { return wander_floor(coord,actor); }
static uint FUN_0045fc10(uint a,uint b) { return 0x1234; }
static int query_calls,block_at;
static short query_points[128][3];
__attribute__((regparm(2))) static uint64_t floor_hook(uint coord,uint height) {
  assert(query_calls<128);memcpy(query_points[query_calls],(void*)coord,6);
  int floor=(int)height+(query_calls++==block_at?-1:1);
  return ((uint64_t)height<<32)|(uint)floor;
}
static uint64_t FUN_00448be0(uint coord,uint height) { return floor_hook(coord,height); }
static volatile uint seen_code __attribute__((used)),seen_actor __attribute__((used)),seen_calls __attribute__((used));
static void FUN_0044f320(uint code,ushort *actor,ushort *node) {
  assert(node==NULL);seen_code=code;seen_actor=(uintptr_t)actor;seen_calls++;
}
__attribute__((naked)) static void allocate_hook(void) { __asm__("mov $0x900100,%eax; ret"); }
__attribute__((naked)) static void code_hook(void) {
  __asm__("mov %eax,seen_code; mov %edx,seen_actor; incl seen_calls; ret");
}
"""
harness+=function('E2R_FindActorArchiveOffset')+'\n'
harness+=function('E2R_PolygonAngle16')+'\n'+function('E2R_NpcPolar16')+'\n'
match=re.search(r'undefined8 __fastcall FUN_0042a098\([^)]*\)\s*\{.*?\n\}',source,re.S)
assert match
harness+=match.group().replace('__fastcall','')+'\n'

for name in ('FUN_00422a48','FUN_00422aa0'):
    match=re.search(r'(?:void|undefined4) __fastcall '+name+r'\([^)]*\)\s*\{.*?\n\}',source,re.S)
    assert match,name
    harness+=match.group().replace('__fastcall','')+'\n'
harness+=function('FUN_00426ca4')+'\n'+function('FUN_0044e238')+'\n'
harness+=r"""
static int DAT_0047a4a0,DAT_00479dd0;
static volatile uint sound_seen[5] __attribute__((used));
static uint64_t FUN_0042fc84(uint a,uint b) { return ((uint64_t)b<<32)|7; }
static void FUN_00451a54(uint a,uint sound) { sound_seen[0]=sound; }
static void FUN_00413ea4(int resource,int close,int volume,int channel) {
  sound_seen[1]=resource;sound_seen[2]=close;sound_seen[3]=volume;sound_seen[4]=channel;
}
__attribute__((naked)) static void sound_load_hook(void) { __asm__("mov %eax,sound_seen; ret"); }
__attribute__((naked)) static void sound_play_hook(void) {
  __asm__("mov %eax,sound_seen+4; mov %edx,sound_seen+8; mov %ebx,sound_seen+12; mov %ecx,sound_seen+16; ret");
}
__attribute__((naked)) static void sound_select_hook(void) { __asm__("mov $7,%eax; ret"); }
"""
match=re.search(r'undefined4 __fastcall FUN_0042fce0\([^)]*\)\s*\{.*?\n\}',source,re.S)
assert match
harness+=match.group().replace('__fastcall','')+'\n'

harness+=function('E2R_TransformVector14')+'\n'
at=source.index('  if (*(short *)(in_EAX + 4) != 7)',source.index('void __fastcall FUN_00423858('))
end=source.index('  /* Cylinder mode retains',at)
harness+='static void root_native(int in_EAX) { int local_54,local_40,iVar10; short *local_58,*psVar9;\n'+source[at:end]+'}\n'

match=re.search(r'undefined4 FUN_0042ce70\([^)]*\)\s*\{.*?\n\}',source,re.S)
assert match
harness+=match.group()+'\n'

at=source.index('      iVar17 = 0;\n      FUN_00422aa0(',source.index('undefined4 __fastcall FUN_00427584'))
end=source.index('\n    }\n    *(byte *)(local_6c + 0xb6)',at)
harness+='static int sight_native(int local_60,int iVar7,short *local_7c,short *out) { short local_84[3]; int iVar17,local_58=0; uint uVar13,extraout_ECX_10=0,extraout_ECX_12=0; short *psVar15,*extraout_EDX_04=NULL; undefined8 uVar27;\n'+source[at:end]+'\nmemcpy(out,local_84,6);return local_58; }\n'

at=source.index('  case 0x8:',source.index('short * __fastcall FUN_0042b880'))
end=source.index('  case 0x9:',at)
harness+='static short *construct_native(short *in_EAX) { uint param_1=0; int iVar9=0; uint uVar12; short *psVar7;\n'+source[at:end].replace('  case 0x8:','')+'}\n'
at=source.index('    if ((-1 < *(short *)(in_EAX + 0x13a))',source.index('void FUN_00420dcc'))
end=source.index('\n  }\n  return;',at)
harness+='static void initial_native(uint in_EAX) {\n'+source[at:end]+'\n}\n'
for name,start,end in [('construct_bytes',0x42ba20,0x42ba4c),('initial_bytes',0x420ea5,0x420ebe),('sight_bytes',0x428080,0x4280c2),('add_bytes',0x422a48,0x422a71),('copy_bytes',0x422aa0,0x422abc),('wander_bytes',0x42a058,0x42a3ae),('sine',0x59b590,0x5bb590),('cosine',0x5de590,0x5fe590),('polar_bytes',0x427160,0x427214),('angle_bytes',0x432c64,0x432de4),('unlink_bytes',0x426ca4,0x426df8),('deactivate_bytes',0x44e238,0x44e354),('scale_bytes',0x42ce70,0x42cf02),('sound_bytes',0x42fce0,0x42fe5e),('root_bytes',0x423858,0x423953),('vector_bytes',0x45de8b,0x45df0e)]:
    harness+='static const byte '+name+'[]={'+','.join(map(str,original(start,end)))+'};\n'
harness+=r"""
static void map(uint addr,uint size) { assert(mmap((void*)addr,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)addr); }
static void jump(uint at,void *fn) { *(byte*)at=0xe9;*(int*)(at+1)=(uintptr_t)fn-at-5; }
static uint construct_original(short *record) {
  uint result;
  __asm__ volatile("call *%%esi":"=a"(result):"S"(0x42ba20),"D"(record):"ecx","edx","memory","cc");
  return result;
}
static void initial_original(uint actor) {
  __asm__ volatile("call *%%esi"::"S"(0x420ea5),"d"(actor):"eax","ecx","memory","cc");
}
static uint64_t wander_original(uint actor,uint retained) {
  uint lo,hi;
  __asm__ volatile("call *%%esi":"=a"(lo),"=d"(hi):"a"(actor),"d"(retained),"S"(0x42a098):"ecx","memory","cc");
  return ((uint64_t)hi<<32)|lo;
}
static void actor_original(uint fn,uint actor) {
  __asm__ volatile("call *%%esi" : "+a"(actor) : "S"(fn) : "ecx","edx","memory","cc");
}
static void polar_original(short *angle,short *distance,int x,int z) {
  __asm__ volatile("call *%%esi" : "+a"(angle),"+d"(distance),"+b"(x),"+c"(z) : "S"(0x427160) : "memory","cc");
}
static void sight_original(uint frame,int steps) {
  __asm__ volatile("push %%ebp; mov %%ecx,%%ebp; call *%%esi; pop %%ebp"
    : "+b"(steps),"+c"(frame) : "S"(0x428080) : "eax","edx","edi","memory","cc");
}
static void sound_original(int sound,int node,int close,int volume,int channel) {
  __asm__ volatile("push %4; call *%%esi" : "+a"(sound),"+d"(node),"+b"(close),"+c"(volume)
    : "m"(channel),"S"(0x42fce0) : "memory","cc");
}
int main(int argc,char **argv) {
  assert(argc==2);FILE *file=fopen(argv[1],"rb");assert(file);fseek(file,0,SEEK_END);long size=ftell(file);rewind(file);
  byte *data=malloc(size);assert(data && fread(data,1,size,file)==(uint)size);fclose(file);
  int stream[7]={0};stream[5]=(uintptr_t)data;stream[2]=(uintptr_t)(data+size);stream[6]=E2R_STREAM_MAGIC;DAT_0047a724=(uintptr_t)stream;
  unsigned headers=0,sampled=0;
  for(long i=0;i+0x36<=size;i++) {
    if(memcmp(data+i,"FANT\0\x37\0\1",8) || data[i+44]!=0 || data[i+45]!=8)continue;
    unsigned id=data[i+48]*256+data[i+49];assert(id<5000);headers++;
    if(headers%53==1 || id==0 || id==71 || id==261 || id==284 || id==293 || id==3551) {
      assert(E2R_FindActorArchiveOffset(id)==i);sampled++;
    }
  }
  assert(headers>1900 && sampled>30);assert(E2R_FindActorArchiveOffset(5000)==-1);
  stream[2]=stream[5]+20;assert(E2R_FindActorArchiveOffset(71)==-1);stream[6]=0;
  assert(E2R_FindActorArchiveOffset(71)==-1);
  map(0x420000,0x50000);map(0x470000,0x10000);map(0x620000,0x20000);map(0x900000,0x1000);
  memcpy((void*)0x423858,root_bytes,sizeof root_bytes);
  *(byte*)0x4238fe=0xe9;*(int*)0x4238ff=0x423947-0x423903;
  memcpy((void*)0x45de8b,vector_bytes,sizeof vector_bytes);
  unsigned seed=0x12345;
  for(int n=0;n<4096;n++) {
    byte *root=(byte*)0x900100,*first=(byte*)0x900400,*second=(byte*)0x900500;
    memset(root,0,0x18c);memset(first,0,0x2a);memset(second,0,0x2a);
    *(short*)(root+4)=n%5==0?7:0;
    *(uint*)(root+0x11e)=n%7==0?0:(uint)first;
    *(uint*)(first+0x26)=n%3==0?0:(uint)second;
    for(int i=0;i<9;i++) { seed=seed*1664525u+1013904223u;*(short*)(root+6+i*2)=seed>>16; }
    for(int i=0;i<3;i++) {
      seed=seed*1664525u+1013904223u;*(short*)(root+0x80+i*2)=seed>>16;
      seed=seed*1664525u+1013904223u;*(short*)(first+4+i*2)=seed>>16;
      seed=seed*1664525u+1013904223u;*(short*)(second+4+i*2)=seed>>16;
    }
    byte saved[0x2a],saved_second[0x2a],expected[0x2a],expected_second[0x2a];
    memcpy(saved,first,sizeof saved);memcpy(saved_second,second,sizeof saved_second);
    actor_original(0x423858,(uint)root);
    memcpy(expected,first,sizeof expected);memcpy(expected_second,second,sizeof expected_second);
    memcpy(first,saved,sizeof saved);memcpy(second,saved_second,sizeof saved_second);root[3]=0;
    root_native((int)root);
    assert(!memcmp(first,expected,sizeof expected) && !memcmp(second,expected_second,sizeof expected_second));
    assert((root[3]&0x80)==(*(short*)(root+4)==7?0:0x80));
  }
  puts("PASS: 4096 original root-reference transforms, including overflow, chains and type-7 exclusion");
  memcpy((void*)0x42ce70,scale_bytes,sizeof scale_bytes);
  for(int n=0;n<512;n++) {
    for(int i=0;i<0x800;i++){seed=seed*1664525u+1013904223u;*(byte*)(0x900000+i)=seed>>24;}
    *(uint*)0x90011e=n%3?0x900300:0;
    *(uint*)0x9003ca=n%2?0x900500:0;*(uint*)0x9005ca=0;
    for(int i=0;i<3;i++) {
      *(short*)(0x9001e6+i*2)=n%7==0?0:(short)(n*317+i*29);
      *(short*)(0x9003e0+i*2)=n%11==0?0:(short)(n*173+i*17);
      *(short*)(0x9005e0+i*2)=n%13==0?0:(short)(n*79+i*37);
    }
    byte initial[0x800],expected[0x800];memcpy(initial,(void*)0x900000,sizeof initial);
    actor_original(0x42ce70,0x900100);memcpy(expected,(void*)0x900000,sizeof expected);
    memcpy((void*)0x900000,initial,sizeof initial);FUN_0042ce70(0x900100);
    assert(!memcmp(expected,(void*)0x900000,sizeof expected));
  }
  puts("PASS: 512 original node-scale root/child field updates");
  memcpy((void*)0x42ba20,construct_bytes,sizeof construct_bytes);*(byte*)0x42ba4c=0xc3;
  jump(0x426478,allocate_hook);
  memcpy((void*)0x420ea5,initial_bytes,sizeof initial_bytes);*(byte*)0x420ebe=0xc3;
  jump(0x44f310,code_hook);
  for(int n=0;n<128;n++) {
    short record[5]={(short)(n*7),8,(short)(n*37%5000),0,0};
    DAT_00479e4c=*(short*)0x479e4c=n*31;
    memset((void*)0x630b60,0,5000*4);memset((void*)0x900100,0,0x17c);
    assert(construct_original(record)==0x900100);
    assert(*(short*)0x900100==record[2] && *(short*)0x900272==DAT_00479e4c);
    assert(*(uint*)(0x630b60+record[2]*4)==0x900100 && *(uint*)0x47a470==0x900100);
    byte expected[0x17c];memcpy(expected,(void*)0x900100,sizeof expected);
    memset((void*)0x630b60,0,5000*4);memset((void*)0x900100,0,0x17c);
    assert((uintptr_t)construct_native(record)==0x900100);
    assert(!memcmp(expected,(void*)0x900100,sizeof expected));
    assert(*(uint*)(0x630b60+record[2]*4)==0x900100 && DAT_0047a470==0x900100);
    *(short*)0x90023a=n;*(uint*)(0x6297c0+n*4)=n%3?0x900600+n*4:0;
    seen_calls=seen_code=seen_actor=0;initial_original(0x900100);
    uint calls=seen_calls,code=seen_code,actor=seen_actor;
    assert(calls==(n%3!=0));seen_calls=seen_code=seen_actor=0;initial_native(0x900100);
    assert(seen_calls==calls && seen_code==code && seen_actor==actor);
  }
  memcpy((void*)0x428080,sight_bytes,sizeof sight_bytes);*(byte*)0x4280c2=0xc3;
  memcpy((void*)0x422a48,add_bytes,sizeof add_bytes);memcpy((void*)0x422aa0,copy_bytes,sizeof copy_bytes);
  jump(0x448be0,floor_hook);
  for(int n=0;n<512;n++) {
    short *origin=(short*)0x900b80,*step=(short*)0x90071a;
    for(int i=0;i<3;i++){ origin[i]=(short)(n*117+i*317);step[i]=(short)(n*7+i*13); }
    int count=n%43-1;block_at=n%3?n%47:-1;
    *(uint*)0x900736=0x900b00;*(uint*)0x90073e=0;
    query_calls=0;sight_original(0x900700,count);
    int calls=query_calls,blocked=*(uint*)0x90073e;
    short expected[3],points[128][3];memcpy(expected,(void*)0x900712,6);memcpy(points,query_points,sizeof points);
    query_calls=0;short actual[3];assert(sight_native(0x900b00,count,step,actual)==blocked);
    assert(query_calls==calls && !memcmp(points,query_points,calls*6) && !memcmp(actual,expected,6));
  }
  map(0x590000,0x70000);memcpy((void*)0x59b590,sine,sizeof sine);memcpy((void*)0x5de590,cosine,sizeof cosine);
  for(int i=0;i<65536;i++) {
    *(short*)(0x59b590+i*2)=(short)lrint(sin(i*6.283185307179586/65536)*16384);
    *(short*)(0x5de590+i*2)=(short)lrint(cos(i*6.283185307179586/65536)*16384);
  }
  for(int i=0;i<256;i++) {
    *(byte*)(0x5fe990+i)=(byte)(atan(i*0.015625)*64.0*2.0*0.3183101550488765+0.5);
    *(byte*)(0x5fe890+i)=(byte)(atan(i*0.25)*64.0*2.0*0.3183101550488765+0.5);
  }
  memcpy((void*)0x427160,polar_bytes,sizeof polar_bytes);memcpy((void*)0x432c64,angle_bytes,sizeof angle_bytes);
  for(int n=0;n<65536;n++) {
    short x=(short)n,z=(short)(n*317),a,d,aa,dd;
    polar_original(&a,&d,x,z);E2R_NpcPolar16(&aa,&dd,x,z);assert(a==aa && d==dd);
  }
  map(0x410000,0x10000);memcpy((void*)0x42fce0,sound_bytes,sizeof sound_bytes);
  jump(0x42fc84,sound_select_hook);jump(0x451a54,sound_load_hook);jump(0x413ea4,sound_play_hook);
  for(int n=0;n<2048;n++) {
    DAT_0047a4a0=*(uint*)0x47a4a0=n%11!=0;
    DAT_00479dd0=*(uint*)0x479dd0=n%13!=0;
    DAT_0047a470=*(uint*)0x47a470=0x900100;
    int sound=n%16,node=n%5==0?0:0x900600,close=n%2,volume=n%3==0?n%128:0,channel=n%4;
    *(uint*)0x900622=n%3==0?0x900100:0x900300;
    for(int i=0;i<3;i++) {
      *(short*)(0x900184+i*2)=(short)(n*173+i*97);
      *(short*)(0x900384+i*2)=(short)(n*317+i*127);
    }
    memset((void*)0x62d960,0,64);
    int resource=n%7==0?0:0x900700;
    *(uint*)(0x62d960+sound*4)=resource;*(uint*)(0x62d960+7*4)=resource;
    *(short*)0x900716=n%131-10;
    for(int i=0;i<5;i++)sound_seen[i]=0xdeadbeef;
    sound_original(sound,node,close,volume,channel);
    uint expected[5];memcpy(expected,(void*)sound_seen,sizeof expected);
    for(int i=0;i<5;i++)sound_seen[i]=0xdeadbeef;
    FUN_0042fce0(sound,node,close,volume,channel);
    if(memcmp(expected,(void*)sound_seen,sizeof expected)) {
      fprintf(stderr,"sound mismatch n=%d actual=%u,%u,%u,%u,%u expected=%u,%u,%u,%u,%u\n",n,
        sound_seen[0],sound_seen[1],sound_seen[2],sound_seen[3],sound_seen[4],expected[0],expected[1],expected[2],expected[3],expected[4]);abort();
    }
  }
  puts("PASS: 2048 original guard sound distance/volume/resource/channel handoffs");
  memcpy((void*)0x42a058,wander_bytes,sizeof wander_bytes);jump(0x448a3c,wander_floor_hook);
  *(byte*)0x45fc10=0xb8;*(uint*)0x45fc11=0x1234;*(byte*)0x45fc15=0xc3;
  for(int n=0;n<4096;n++) {
    *(ushort*)0x900192=n*317;*(short*)0x90019a=n%2001-1000;
    *(short*)0x900184=(short)(n*13);*(short*)0x900186=(short)(n*17);*(short*)0x900188=(short)(n*19);
    short turn=n%3-1;*(short*)0x900198=turn;wander_mask=(n/3)%8;wander_calls=0;
    uint64_t expected=wander_original(0x900100,0x12345678);
    short new_turn=*(short*)0x900198,points[6][3];memcpy(points,wander_points,sizeof points);assert(wander_calls==6);
    *(short*)0x900198=turn;wander_calls=0;
    uint64_t actual=FUN_0042a098(0x900100,0x12345678);if(actual!=expected)fprintf(stderr,"wander mismatch n=%d mask=%d turn=%d expected=%llx actual=%llx\n",n,wander_mask,turn,(unsigned long long)expected,(unsigned long long)actual);assert(actual==expected);
    assert(*(short*)0x900198==new_turn && wander_calls==6 && !memcmp(points,wander_points,sizeof points));
  }
  map(0x640000,0x40000);
  memcpy((void*)0x426ca4,unlink_bytes,sizeof unlink_bytes);memcpy((void*)0x44e238,deactivate_bytes,sizeof deactivate_bytes);
  for(int mode=0;mode<2;mode++)for(int selected=0;selected<4;selected++) {
    byte expected_actors[0x800],expected_static[0x40000];
    memset((void*)0x900000,0,0x1000);memset((void*)0x640000,0,0x40000);
    for(int i=0;i<3;i++) {
      uint actor=0x900100+i*0x200;*(short*)actor=i+1;*(uint*)(actor+0x4c)=i<2?actor+0x200:0;
      *(ushort*)(actor+2)=0x100;*(short*)(actor+0x122)=i+11;*(short*)(actor+0xec)=i+22;*(byte*)(actor+0x184)=i+33;
      for(int j=0;j<3;j++){*(short*)(actor+0x84+j*2)=i*100+j;*(short*)(actor+0x90+j*2)=i*50+j;}
      *(byte*)(0x64a178+(i+1)*2)=2;
    }
    byte original_actors[0x800];memcpy(original_actors,(void*)0x900000,sizeof original_actors);
    uint actor=0x900100+selected*0x200;
    *(uint*)0x63726c=0x900100;*(uint*)0x636588=1000;*(uint*)0x47a34a=0;
    actor_original(mode?0x44e238:0x426ca4,actor);
    uint expected_head=*(uint*)0x63726c;
    memcpy(expected_actors,(void*)0x900000,sizeof expected_actors);memcpy(expected_static,(void*)0x640000,sizeof expected_static);
    memcpy((void*)0x900000,original_actors,sizeof original_actors);memset((void*)0x640000,0,0x40000);
    for(int i=1;i<=3;i++)*(byte*)(0x64a178+i*2)=2;
    _DAT_0063726c=0x900100;_DAT_00636588=1000;DAT_0047a34a=0;E2R_actor_calc_context=actor;
    if(mode)FUN_0044e238(actor);else FUN_00426ca4();
    if(_DAT_0063726c!=expected_head || memcmp(expected_actors,(void*)0x900000,sizeof expected_actors)) {
      fprintf(stderr,"unlink mismatch mode=%d selected=%d head=%x expected=%x\n",mode,selected,(uint)_DAT_0063726c,expected_head);
      for(int i=0;i<sizeof expected_actors;i++)if(expected_actors[i]!=*(byte*)(0x900000+i))fprintf(stderr,"byte %x actual=%x expected=%x\n",i,*(byte*)(0x900000+i),expected_actors[i]);
      abort();
    }
    assert(!memcmp(expected_static,(void*)0x640000,sizeof expected_static));
  }
  free(data);
  printf("PASS: %u binary actor headers, %u real archive lookups; 128 original-x86 actor constructions and 128 initial-code handoffs; 512 line-of-sight vector traces; 4096 wander terrain traces; 65536 NPC polar vectors; 8 actor unlink/deactivation cases\n",headers,sampled);
}
"""
with tempfile.TemporaryDirectory(prefix='e2-population-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie','-Wno-int-conversion','-Wno-return-mismatch','-Wno-pointer-integer-compare','-Wno-pointer-sign',*flags,str(c),'-lm','-o',str(exe)],check=True)
    subprocess.run([str(exe),str(args.archive)],check=True,timeout=30)
