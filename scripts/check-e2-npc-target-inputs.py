#!/usr/bin/env python3
"""Compare production NPC target inputs/state handoff with original i386 code.

Only angle, line-of-sight floor, copy/vector, RNG and death callbacks are
intercepted. Original control flow, field updates and retained CX execute.
"""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path)
p.add_argument('--cc',default='clang-21')
p.add_argument('--asan',action='store_true')
p.add_argument('--keep-harness',type=Path)
a=p.parse_args()
root=Path(__file__).resolve().parent.parent
source=(root/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
pe=a.exe.read_bytes();header=struct.unpack_from('<I',pe,60)[0]
sections=struct.unpack_from('<H',pe,header+6)[0];optional=struct.unpack_from('<H',pe,header+20)[0]
def original(start,end):
    for i in range(sections):
        at=header+24+optional+i*40
        _,va,size,raw=struct.unpack_from('<IIII',pe,at+8);va+=0x400000
        if va<=start<end<=va+size:return pe[raw+start-va:raw+end-va]
    raise ValueError(hex(start))
start=source.index('undefined4 __fastcall FUN_00427584(')
declarations=source[source.index('{',start)+1:source.index('  in_EAX = (short *)(uintptr_t)param_1;',start)]
start=source.index('  if ((local_70 == (short *)0x0) || ((*(byte *)(local_70 + 1) & 0x80) != 0))',start)
end=source.index('    E2R_TraceActorUpdateExit("27584.check-after-state-switch"',start)
fragment=source[start:end]+'  }\n'
fragment=fragment.replace('E2R_PolygonAngle16(', 'FUN_00432c64(')
# Poison decompiler register temporaries, rather than accidentally getting a
# successful comparison from identical stack contents in both calls.
poison=''
for typ,name in re.findall(r'^\s*(\w+(?:\s*\*)?)\s*(extraout_\w+);',declarations,re.M):
    poison+='  '+name+' = ('+typ+')poison;\n'
angle=re.search(r'static short E2R_PolygonAngle16\([^)]*\)\s*\{.*?\n\}',source,re.S).group()
h=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
#include <math.h>
typedef uint8_t byte,undefined1,bool;
typedef uint16_t ushort,undefined2;
typedef uint32_t uint,undefined4,undefined3,uint3;
typedef int32_t int3;
typedef uint64_t undefined8,ulonglong;
typedef int64_t longlong;
#define true 1
#define false 0
#define CONCAT11(a,b) (((uint)(uint8_t)(a)<<8)|(uint8_t)(b))
#define CONCAT21(a,b) (((uint)(uint16_t)(a)<<8)|(uint8_t)(b))
#define CONCAT22(a,b) (((uint)(uint16_t)(a)<<16)|(uint16_t)(b))
#define CONCAT31(a,b) (((uint)(a)<<8)|(uint8_t)(b))
#define CONCAT44(a,b) (((uint64_t)(uint)(a)<<32)|(uint)(b))
#define E2R_TraceActorUpdateExit(...) ((void)0)
static short *DAT_0047a470;
static int _DAT_00636690=1,DAT_0047a398=1;
static uint seed,random_calls,death_calls,query_calls,angle_calls;
static int block_at;
static short query_points[1024][3],angle_points[8][2];
static volatile uint original_facing __attribute__((used));
'''+angle+r'''
__attribute__((regparm(2),used,noinline)) static uint angle_value(uint x,uint z) {
  assert(angle_calls<8);angle_points[angle_calls][0]=(short)x;angle_points[angle_calls++][1]=(short)z;
  return (ushort)E2R_PolygonAngle16((short)x,(short)z);
}
static uint FUN_00432c64(uint x,short z) { return angle_value(x,(uint)(int)z); }
__attribute__((regparm(2),used,noinline)) static uint floor_value(uint coord,uint height) {
  assert(query_calls<1024);memcpy(query_points[query_calls],(void*)coord,6);
  return (int)height-(query_calls++==(uint)block_at);
}
static undefined8 FUN_00448be0(uint coord,int height) { return CONCAT44(height,floor_value(coord,height)); }
__attribute__((used,noinline)) static uint random_value(void) {
  ++random_calls;seed=seed*0x41c64e6d+0x3039;return(seed>>16)&0x7fff;
}
static undefined8 FUN_0045fc10(uint ignored,uint retained) { return CONCAT44(retained,random_value()); }
static void FUN_004273cc(uint actor) { assert(actor==0x900200);++death_calls; }
static void FUN_00414e68(void) { assert(!"unexpected NPC state"); }
__attribute__((regparm(2),used,noinline)) static void copy_value(uint to,uint from) { memcpy((void*)to,(void*)from,6); }
static void FUN_00422aa0(uint to,void *from) {copy_value(to,(uint)from);}
__attribute__((regparm(2),used,noinline)) static void add_value(uint to,uint from) {
 for(int i=0;i<3;i++)((short*)to)[i]=(short)(((short*)to)[i]+((short*)from)[i]);
}
static void FUN_00422a48(uint to,void *from) {add_value(to,(uint)from);}
__attribute__((naked)) static void angle_hook(void) {__asm__("pushal; call angle_value; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void floor_hook(void) {__asm__("pushal; call floor_value; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void random_hook(void) {__asm__("pushal; call random_value; mov %eax,28(%esp); popal; ret");}
__attribute__((naked)) static void copy_hook(void) {__asm__("pushal; call copy_value; popal; ret");}
__attribute__((naked)) static void add_hook(void) {__asm__("pushal; call add_value; popal; ret");}
__attribute__((naked)) static void death_hook(void) {__asm__("incl death_calls; ret");}
__attribute__((naked)) static void original_run(void) {
 __asm__("pushal; mov $0x900000,%ebp; mov $0x427d6e,%eax; call *%eax; mov %ecx,original_facing; popal; ret");
}
static short native_distance,native_facing;static uint native_target;
static void native_run(uint poison) {
'''+declarations+poison+r'''
 local_6c=(short*)0x900200;local_70=*(short**)0x900026;
 local_54=0x900800;local_60=0x900600;local_64=*(int*)0x900032;
 local_58=0;local_5c=0;uVar19=1000;uVar13=0;
'''+fragment+r'''
 native_distance=sStack_28;native_facing=target_facing;native_target=(uint)local_70;
}
static void map(uint address,uint n) {assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);}
static void hook(uint address,void *function) {*(byte*)address=0xe9;*(int*)(address+1)=(int)function-(int)address-5;}
static void setup(uint test) {
 memset((void*)0x900000,0,0x1000);seed=test+0x2a13f00d;random_calls=death_calls=query_calls=angle_calls=0;
 memset(query_points,0,sizeof query_points);memset(angle_points,0,sizeof angle_points);
 *(uint*)0x90002a=0x900200;*(uint*)0x900026=(test%17==0)?0:0x900400;
 *(uint*)0x900036=0x900600;*(uint*)0x900042=0x900800;
 *(int*)0x900032=test%4;block_at=test%5==0?(int)(test%15):-1;
 *(uint*)0x47a470=(test&8)?0x900200:0;DAT_0047a470=*(short**)0x47a470;
 _DAT_00636690=*(int*)0x636690=(test&16)!=0;DAT_0047a398=*(short*)0x47a398=(test&32)!=0;
 short *actor=(short*)0x900200,*target=(short*)0x900400;
 static const short states[]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,15};
 actor[0x41]=states[(test/16)%15];actor[0x49]=(short)(test*2731);actor[0x91]=test%3;
 actor[1]=(test&64)?0x40:0;actor[0x74]=(test&128)?-1:100;actor[0x75]=(test&256)?0x7fff:0x2000;
 actor[0x76]=(test&512)?-1:100;target[0x76]=(test&1024)?-1:100;
 actor[0xa0]=test%5;actor[0xa8]=test%7;actor[0xac]=(test&2048)?0:5000;actor[0xb7]=test%11;
 *(byte*)((uint)actor+3)=(test&4096)?2:0;*(byte*)((uint)actor+0x16c)=(test&8192)?2:0;
 *(byte*)((uint)target+2)=(test%19==0)?0x80:0;
 short x=(short)((test*619)%18001-9000),z=(short)((test*1031)%18001-9000),y=(short)((test*71)%2401-1200);
 *(short*)0x900680=1000;*(short*)0x900682=512;*(short*)0x900684=-5000;
 *(short*)0x900880=(short)(1000+x);*(short*)0x900882=(short)(512+y);*(short*)0x900884=(short)(-5000+z);
 *(int*)0x900608=(int)(short)(test*13)<<16;*(int*)0x900614=(int)(short)(test*17)<<16;
 actor[0xa9]=(short)(1000-x/2);actor[0xaa]=(short)(512+y/2);actor[0xab]=(short)(-5000-z/2);
 target[0x91]=test%4;target[0xa8]=test%6;
 for(int i=0;i<3;i++)target[0x42+i]=((short*)0x900880)[i];
}
struct result {short actor[0xc8];uint seed,random_calls,death_calls,query_calls,angle_calls,target;short distance,facing;short queries[1024][3],angles[8][2];};
static void save(struct result *r,int native) {
 memset(r,0,sizeof *r);memcpy(r->actor,(void*)0x900200,sizeof r->actor);r->seed=seed;r->random_calls=random_calls;r->death_calls=death_calls;
 r->query_calls=query_calls;r->angle_calls=angle_calls;r->target=native?native_target:*(uint*)0x900026;
 r->distance=native?native_distance:*(short*)0x90006e;r->facing=native?native_facing:(short)original_facing;
 memcpy(r->queries,query_points,sizeof query_points);memcpy(r->angles,angle_points,sizeof angle_points);
}
'''
for name,start,end in [('code',0x427d6e,0x42885f),('table',0x427504,0x427544)]:
 h+='static const unsigned char '+name+'[]={'+','.join(map(str,original(start,end)))+'};\n'
h+=r'''
int main(void) {
 map(0x420000,0x20000);map(0x440000,0x10000);map(0x450000,0x10000);map(0x470000,0x10000);map(0x630000,0x10000);map(0x900000,0x10000);
 memcpy((void*)0x427d6e,code,sizeof code);*(byte*)0x42885f=0xc3;memcpy((void*)0x427504,table,sizeof table);
 hook(0x432c64,angle_hook);hook(0x448be0,floor_hook);hook(0x45fc10,random_hook);
 hook(0x422aa0,copy_hook);hook(0x422a48,add_hook);hook(0x4273cc,death_hook);
 static struct result expected,actual;
 for(uint test=0;test<16384;test++) {
  setup(test);original_run();save(&expected,0);
  setup(test);native_run(test*0x9e3779b9u);save(&actual,1);
  if(memcmp(&expected,&actual,sizeof actual)) {
   fprintf(stderr,"FAIL case=%u state=%d distance=%d/%d facing=%d/%d target=%x/%x rng=%u/%u query=%u/%u angle=%u/%u\n",test,expected.actor[0x41],expected.distance,actual.distance,expected.facing,actual.facing,expected.target,actual.target,expected.random_calls,actual.random_calls,expected.query_calls,actual.query_calls,expected.angle_calls,actual.angle_calls);
   for(uint i=0;i<sizeof actual;i++)if(((byte*)&expected)[i]!=((byte*)&actual)[i]) {fprintf(stderr,"first byte offset=%u expected=%u actual=%u\n",i,((byte*)&expected)[i],((byte*)&actual)[i]);break;}
   return 1;
  }
 }
 puts("PASS: 16384 original NPC target/distance/facing/state/RNG handoffs with poisoned register temporaries");
}
'''
with tempfile.TemporaryDirectory(prefix='e2-npc-target-') as tmp:
    c=Path(tmp)/'target.c';binary=Path(tmp)/'target';c.write_text(h)
    if a.keep_harness:a.keep_harness.write_text(h)
    command=[a.cc,'-m32','-O1','-g','-fno-pie','-no-pie','-fno-omit-frame-pointer','-Wno-int-conversion','-Wno-incompatible-pointer-types','-Wno-pointer-to-int-cast',str(c),'-lm','-o',str(binary)]
    if a.asan:command[1:1]=['-fsanitize=address','-fno-sanitize-recover=all']
    subprocess.run(command,check=True);subprocess.run([str(binary)],check=True)
