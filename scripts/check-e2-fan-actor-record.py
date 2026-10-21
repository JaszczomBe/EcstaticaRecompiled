#!/usr/bin/env python3
"""Compare FAN actor dispatch/field ownership with original i386 instructions.

Exercises suspended action events, null-actor construction entries and nested
FAN dispatch, plus every version boundary in the type-0x15 actor finalizer.
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
args=parser.parse_args()
pe=args.exe.read_bytes();header=struct.unpack_from('<I',pe,0x3c)[0]
count=struct.unpack_from('<H',pe,header+6)[0];optional=struct.unpack_from('<H',pe,header+20)[0]
def original(start,end):
    for i in range(count):
        at=header+24+optional+i*40
        _,va,size,raw=struct.unpack_from('<IIII',pe,at+8);va+=0x400000
        if va<=start<end<=va+size:return pe[raw+start-va:raw+end-va]
    raise ValueError(hex(start))
source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
def function(name):
    match=re.search(r'^static (?:void|int|short \*)'+r' ?'+name+r'\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
    assert match,name
    return match.group()+'\n'
harness=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef unsigned char byte;
typedef unsigned short ushort;
typedef unsigned int uint;
static uintptr_t DAT_0047a470,_DAT_0073cc3c;
static int E2R_action_event_context;
static short *E2R_fan_parse_record;
static volatile uint32_t observed[4] __attribute__((used));
static unsigned calls,nested;
static short *E2R_DispatchFanActorRecord(short*,short*);
static int IsBadReadPtr(void *p,unsigned n) { return p==NULL; }
static short *FUN_0042b880(int param_1,short *param_2) {
  short *in_EAX;
'''
# Retain the actual production shared-handler entry selector in the fixture.
at=source.index('  if (E2R_action_event_context != 0)',source.index('short * __fastcall FUN_0042b880('))
end=source.index('  unaff_ESI = param_2;',at)
harness+=source[at:end]
harness+=r'''
  observed[0]=(uintptr_t)in_EAX;observed[1]=(uintptr_t)param_2;observed[2]=observed[3]=0;calls++;
  if (nested) {
    nested=0;
    uint32_t parent[4];memcpy(parent,(void*)observed,sizeof parent);
    short *entry_record=E2R_fan_parse_record;
    assert(E2R_action_event_context==0);
    E2R_DispatchFanActorRecord((short*)0x900180,NULL);
    assert(E2R_fan_parse_record==entry_record && E2R_action_event_context==0);
    memcpy((void*)observed,parent,sizeof parent);
  }
  return param_2;
}
__attribute__((naked)) static void record_hook(void) {
  __asm__("mov %eax,observed; mov %edx,observed+4; mov %ecx,observed+8; mov %ebx,observed+12; ret");
}
static void map(uintptr_t addr,unsigned size) {
  assert(mmap((void*)addr,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)addr);
}
static void dispatch_original(short *record) {
  __asm__ volatile("call *%%edi" :: "D"(0x44453b),"S"(record) : "eax","ebx","ecx","edx","memory","cc");
}
static void finish_original(short *record) {
  __asm__ volatile("call *%%edi" :: "D"(0x444556),"S"(record) : "eax","ebx","ecx","edx","memory","cc");
}
'''
harness+=function('E2R_DispatchFanActorRecord')+function('E2R_FinishFanActorRecord')
harness+=function('E2R_NormalizeSceneRecordPointer')
at=source.index('  uVar5 = DAT_0047a470;',source.index('void __fastcall FUN_00452140('))
end=source.index('  if (in_EAX != 0)',at)
harness+='static int scene_entry_native(uint param_1) { int in_EAX; uint uVar5;\n'+source[at:end]+'  return in_EAX;\n}\n'
for name,start,end in [('dispatch_bytes',0x44453b,0x44454c),('finish_bytes',0x444556,0x444631),('scene_entry_bytes',0x452140,0x45215a),('scene_exit_bytes',0x452329,0x45233c)]:
    harness+='static const byte '+name+'[]={'+','.join(map(str,original(start,end)))+'};\n'
harness+=r'''
int main(void) {
  map(0x420000,0x30000);map(0x470000,0x10000);map(0x670000,0x10000);map(0x900000,0x2000);
  memcpy((void*)0x44453b,dispatch_bytes,sizeof dispatch_bytes);*(byte*)0x44454c=0xc3;
  *(byte*)0x42b880=0xe9;*(int*)0x42b881=(uintptr_t)record_hook-0x42b885;
  memcpy((void*)0x444556,finish_bytes,sizeof finish_bytes);*(byte*)0x444631=0xc3;
  map(0x450000,0x10000);map(0x620000,0x10000);
  memcpy((void*)0x452140,scene_entry_bytes,sizeof scene_entry_bytes);
  *(byte*)0x45215a=0xe9;*(int*)0x45215b=0x452329-0x45215f;
  memcpy((void*)0x452329,scene_exit_bytes,sizeof scene_exit_bytes);
  for(int n=0;n<256;n++) {
    int scene=n%3?0x900100+(n%2)*0x40:0;
    for(int i=0;i<2;i++) {
      int pointer=0x900100+i*0x40;*(short*)pointer=i+10;
      *(uint*)(pointer+4)=0x900200+i*0x40;*(uint*)(0x62e450+(i+10)*4)=pointer;
    }
    _DAT_0073cc3c=0x900140;DAT_0047a470=*(uint*)0x47a470=0x900400;
    int expected=scene;
    __asm__ volatile("call *%%esi" : "+a"(expected) : "S"(0x452140) : "ecx","edx","memory","cc");
    assert(scene_entry_native(scene)==expected);
  }
  for (int n=0;n<128;n++) {
    short *record=(short*)0x900100,*actor=n%2?(short*)0x900400:NULL;
    record[1]=n%2?0x15:8;*(uintptr_t*)0x47a470=(uintptr_t)actor;
    dispatch_original(record);
    uint32_t expected[4];memcpy(expected,(void*)observed,sizeof expected);
    memset((void*)observed,0,sizeof expected);
    E2R_action_event_context=n%3?0x900080:0;
    E2R_fan_parse_record=(short*)0x9000c0;
    int entry_event=E2R_action_event_context;
    if(entry_event) {
      calls=0;FUN_0042b880(0,actor);
      assert(!calls || observed[0]!=(uintptr_t)record);
    }
    calls=0;nested=n%2;
    assert(E2R_DispatchFanActorRecord(record,actor)==actor);
    assert(calls==(n%2?2:1) && !memcmp(expected,(void*)observed,sizeof expected));
    assert(E2R_action_event_context==entry_event && E2R_fan_parse_record==(short*)0x9000c0);
  }
  unsigned seed=0x12345;
  for(int version=0;version<=55;version++)for(int n=0;n<128;n++) {
    byte *actor=(byte*)0x900400;short *record=(short*)0x900100;
    for(int i=0;i<0x400;i++){seed=seed*1664525u+1013904223u;actor[i]=seed>>24;}
    record[4]=(short)(n*317+version);*(uintptr_t*)0x47a470=(uintptr_t)actor;
    *(short*)0x67bc92=version;
    byte initial[0x400],expected[0x400];memcpy(initial,actor,sizeof initial);
    finish_original(record);memcpy(expected,actor,sizeof expected);
    memcpy(actor,initial,sizeof initial);E2R_FinishFanActorRecord((short*)actor,record,version);
    assert(!memcmp(expected,actor,sizeof expected));
  }
  puts("PASS: 256 original scene-input cases; 128 original FAN record/actor handoffs, suspended-event/nested restoration; 7168 original actor-finalizer cases with adjacent-memory checks");
}
'''
with tempfile.TemporaryDirectory(prefix='e2-fan-actor-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie','-Wno-int-conversion',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=30)
