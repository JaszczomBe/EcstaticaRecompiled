#!/usr/bin/env python3
"""Compare actor visibility flags and query coordinates with original i386 code.

The world visibility query is intercepted; all caller branches and its actual
position/actor arguments are compared, including scripted and airborne actors.
"""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('exe', type=Path)
p.add_argument('--asan', action='store_true')
p.add_argument('--cc', default='clang-21')
a = p.parse_args()
source = (Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
function = re.search(r'undefined4 __fastcall FUN_0044d2b4\([^\n]*\)\s*\{.*?\n\}', source, re.S).group()
pe = a.exe.read_bytes()
header = struct.unpack_from('<I', pe, 60)[0]
count = struct.unpack_from('<H', pe, header+6)[0]
optional = struct.unpack_from('<H', pe, header+20)[0]
for i in range(count):
    _, va, size, raw = struct.unpack_from('<IIII', pe, header+24+optional+i*40+8)
    va += 0x400000
    if va <= 0x44d2b4 < 0x44d349 <= va+size:
        code = pe[raw+0x44d2b4-va:raw+0x44d349-va]
        break
else:
    raise ValueError('Original visibility function missing')
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint32_t uint,undefined4;
typedef int64_t longlong;typedef uint64_t ulonglong;
#define __fastcall
#define DAT_0047a470 (*(uint*)0x47a470)
#define DAT_0047a34a (*(short*)0x47a34a)
static uint query_position,query_actor,query_calls,query_result;
__attribute__((naked)) static void query_hook(void) {
 __asm__("mov %eax,query_position;mov %edx,query_actor;incl query_calls;mov query_result,%eax;ret");
}
static ulonglong FUN_0044d28c(uint position,uint actor) {
 query_position=position;query_actor=actor;query_calls++;
 return ((ulonglong)actor<<32)|query_result;
}
'''+function+r'''
static void map(uint at,uint size) {
 assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
int main(void) {
 map(0x440000,0x10000);map(0x470000,0x10000);map(0x900000,0x10000);
'''
harness += 'unsigned char code[]={'+','.join(map(str, code))+'};\n'
harness += r'''
 memcpy((void*)0x44d2b4,code,sizeof code);
 *(byte*)0x44d28c=0xe9;*(int*)0x44d28d=(int)query_hook-0x44d291;
 uint cases=0;int actor=0x900000;short velocities[]={-123,0,234};
 for(int flags=0;flags<256;flags++)for(int current=0;current<2;current++)
 for(int scene=0;scene<2;scene++)for(int action=0;action<3;action++)
 for(int v=0;v<3;v++)for(int visible=0;visible<2;visible++) {
  memset((void*)actor,0xa5,0x1000);*(byte*)(actor+2)=flags;
  *(int*)(actor+0xa6)=action?0x901000:0;*(byte*)0x90100c=action==2?2:0;
  *(short*)(actor+0x5a)=velocities[v];DAT_0047a34a=scene;
  DAT_0047a470=current?actor:0x902000;query_result=visible?0x4000:0;
  byte before[0x1000],expected[0x1000];memcpy(before,(void*)actor,sizeof before);
  query_calls=query_position=query_actor=0;
  __asm__ volatile("call *%%edi" : "+a"(actor) : "D"(0x44d2b4) : "memory","cc");
  // The original returns an unspecified EAX; restore the retained caller actor.
  actor=0x900000;memcpy(expected,(void*)actor,sizeof expected);
  uint calls=query_calls,position=query_position,queried_actor=query_actor;
  memcpy((void*)actor,before,sizeof before);query_calls=query_position=query_actor=0;
  FUN_0044d2b4(actor);
  assert(!memcmp(expected,(void*)actor,sizeof expected));
  assert(query_calls==calls && query_position==position && query_actor==queried_actor);
  if(calls)assert(position==actor+0x84 && queried_actor==actor);
  cases++;
 }
 printf("PASS: %u original actor visibility flag/query-coordinate cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-actor-visibility-') as tmp:
    c = Path(tmp)/'check.c'
    exe = Path(tmp)/'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if a.asan else []
    subprocess.run([a.cc, '-m32', '-O1', '-fno-pie', '-no-pie', '-Wno-return-type',
                    *flags, str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=30)
