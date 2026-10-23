#!/usr/bin/env python3
"""Check gameplay actor identities and original water-entry damage eligibility.

Uses the installed archive, production index/gate and actor-flag fragments, and
original x86 flag/damage instructions. This bounds loading/terrain eligibility;
it does not establish swimming animation, steering or live-map traversal.
"""
import argparse
from pathlib import Path
import struct
from e2_original import OriginalImage, function, run_fixture, support

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('exe', type=Path)
p.add_argument('archive', type=Path)
p.add_argument('--asan', action='store_true')
p.add_argument('--keep-harness', type=Path)
a = p.parse_args()
image = OriginalImage(a.exe)
source = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
data = a.archive.read_bytes()
headers = {}
start = 0
while True:
    start = data.find(b'FANT\0\x37\0\1', start)
    if start < 0:
        break
    if data[start+44:start+46] == b'\0\x08':
        actor_id = struct.unpack_from('>H', data, start+48)[0]
        assert actor_id not in headers
        headers[actor_id] = start
    start += 4
assert len(headers) > 1900
joe = headers[0]
assert struct.unpack_from('>5H', data, joe+64) == (0x15, 0, 0x3109, 0xc0, 0xffff)
wrong = headers[4119]
assert struct.unpack_from('>5H', data, wrong+64) == (0x15, 0, 0x29, 0xc0, 0xffff)
names_path = a.archive.parent.parent / 'Code/ECSTATIC.FAN'
raw = names_path.read_bytes()
cursor = 34
pools = []
for _ in range(2):
    names = []
    while raw[cursor]:
        end = raw.index(0, cursor)
        names.append(raw[cursor:end].decode('ascii'))
        cursor = end + 1
    cursor += 1
    pools.append(names)
assert pools[1][0] == 'Joe' and pools[1][4119] == 'fpot6'
print(f'Joe archive offset {joe}; prior local-node alias {wrong} belongs to fpot6 (4119)')

harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;
typedef uint16_t ushort;
typedef uint32_t uint;
static uintptr_t DAT_0047a724,DAT_0047a470;
#define E2R_STREAM_MAGIC 0xe25eed01
static int E2R_actor_archive_load_context,action_index;
static int E2R_ActionIndexProbeEnabled(void) { return action_index; }
static int IsBadReadPtr(const void *p,unsigned size) { return !p || !size; }
'''+support()+function(source, 'E2R_PopulationProbeEnabled')+function(source, 'E2R_FindActorArchiveOffset')
at = source.index('    for (offset = 0; offset < 2500;', source.index('/* 00447d94 */'))
end = source.index('    if (E2R_ActionIndexProbeEnabled()) E2R_IndexFlatArchiveVisibility', at)
harness += '\nstatic unsigned index_native(byte *base,byte *end) {\n'
harness += 'uint offset,id,type,resource_offset,action_count,actor_count,rep_count,scene_count; byte *scan,*rec,*limit;\n'
harness += source[at:end]+'return actor_count;\n}\n'
at = source.index('    param_2[1] = param_2[1] & ~in_EAX[4]')
end = source.index('    if ((in_EAX[4] == -1)', at)
harness += '\nstatic void flags_native(short *param_2,short *in_EAX) {\n'+source[at:end]+'}\n'
harness += function(source, 'E2R_FinishFanActorRecord')
at = source.index('  if (terrain == 7 &&')
end = source.index('\n  }', at)+4
harness += '\nstatic void water_native(uint actor,int terrain) { short state=*(short*)(actor+0x82);\n'+source[at:end]+'}\n'
at = source.index('          if (DAT_0047a470 != (ushort *)0x0) {', source.index('"4f508.op54.reload"'))
end = source.index('          puVar13 = extraout_ECX_34;', at)
harness += '\nstatic void reload_native(void) {\n'+source[at:end].replace('(ushort *)0x0', '0')+'}\n'
for name, begin, finish in [('flags', 0x42bcb0, 0x42bcde), ('water', 0x449533, 0x449574), ('reload', 0x44fd87, 0x44fd9c)]:
    code = image.code(begin, finish)
    harness += f'static const byte {name}_code[]={{'+','.join(map(str,code))+'};\n'
harness += r'''
static void map(uint at,unsigned size) {
 assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);
}
__attribute__((naked)) static void water_original(uint actor,int terrain) {
 __asm__("push %edi; push %esi; sub $0xc0,%esp; mov 0xcc(%esp),%edi; "
         "mov 0xd0(%esp),%eax; mov %eax,0x78(%esp); mov $0x449533,%eax; call *%eax; "
         "add $0xc0,%esp; pop %esi; pop %edi; ret");
}
int main(int argc,char **argv) {
 assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
 fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);byte *data=malloc(size+0x4000);
 assert(data && fread(data,1,size,f)==(unsigned)size);fclose(f);memset(data+size,0,0x4000);
 map(0x420000,0x30000);map(0x470000,0x10000);map(0x630000,0x40000);map(0x900000,0x1000);
 memcpy((void*)0x44fd87,reload_code,sizeof reload_code);*(byte*)0x44fd9c=0xc3;
 memcpy((void*)0x42bcb0,flags_code,sizeof flags_code);*(byte*)0x42bcde=0xc3;
 memcpy((void*)0x449533,water_code,sizeof water_code);*(byte*)0x449574=0xc3;
 int stream[7]={0};stream[5]=(uint)data;stream[2]=(uint)(data+size);stream[6]=E2R_STREAM_MAGIC;
 DAT_0047a724=(uint)stream;unsetenv("E2R_POPULATION_PROBE");
 action_index=0;E2R_actor_archive_load_context=0;assert(!E2R_PopulationProbeEnabled());
 E2R_actor_archive_load_context=1;assert(E2R_PopulationProbeEnabled());
 E2R_actor_archive_load_context=0;action_index=1;assert(E2R_PopulationProbeEnabled());
 unsigned actors=index_native(data,data+size);assert(actors==HEADERS);
 EXPECTED_HEADERS
 short *actor=(short*)0x900000;unsigned cases=0;
 for(int profile=0;profile<2;profile++)for(int terrain=0;terrain<9;terrain++)
 for(int state=0;state<12;state++) {
  short record[]={0,0x15,profile?0x29:0x3109,0xc0,-1};
  memset(actor,0xa5,0x200);actor[0]=0;actor[1]=1;
  byte initial[0x200],expected[0x200];memcpy(initial,actor,sizeof initial);
  struct E2R_Registers regs={.edi=(uint)record,.ebp=(uint)actor};
  e2r_original_call(0x42bcb0,&regs);memcpy(expected,actor,sizeof expected);
  memcpy(actor,initial,sizeof initial);flags_native(actor,record);
  assert(e2r_memory_equal("actor flags",expected,actor,sizeof expected));
  E2R_FinishFanActorRecord(actor,record,55);
  assert((actor[1]&0x100)==(profile?0:0x100));
  *(short*)((byte*)actor+0x82)=state;*(short*)((byte*)actor+0xec)=100;
  memcpy(initial,actor,sizeof initial);water_original((uint)actor,terrain);
  memcpy(expected,actor,sizeof expected);memcpy(actor,initial,sizeof initial);
  water_native((uint)actor,terrain);
  assert(e2r_memory_equal("water eligibility",expected,actor,sizeof expected));
  if(!profile)assert(*(short*)((byte*)actor+0xec)==100);
  if(profile && terrain==7 && state!=8 && state!=5 && state!=11)
   assert(*(short*)((byte*)actor+0xec)==-100);
  cases++;
 }
 for(int n=0;n<256;n++) {
  memset(actor,n,0x200);byte initial[0x200],expected[0x200];memcpy(initial,actor,sizeof initial);
  *(uint*)(0x630b60+n*4)=(uint)actor;
  struct E2R_Registers regs={.edx=n};e2r_original_call(0x44fd87,&regs);
  memcpy(expected,actor,sizeof expected);memcpy(actor,initial,sizeof initial);
  DAT_0047a470=(uint)actor;reload_native();
  assert(*(uint*)0x47a470==DAT_0047a470);
  assert(e2r_memory_equal("reload packed state",expected,actor,sizeof expected));
 }
 puts("PASS: 256 original-x86 actor reload states with adjacent-memory checks");
 printf("PASS: %u original actor headers indexed in gameplay without population-probe; %u original-x86 actor flag/water damage cases\n",actors,cases);
 free(data);return 0;
}
'''
# Finding every resource independently would rescan 33 MB 1,922 times. The
# production index is checked exhaustively; the fallback lookup is sampled.
checks = '\n'.join(f'assert(*(int*)({0x653840 + i*4})=={offset});' for i, offset in headers.items())
checks += f'\nassert(E2R_FindActorArchiveOffset(0)=={joe});'
harness = harness.replace('EXPECTED_HEADERS', checks).replace('HEADERS', str(len(headers)))
# run_fixture has no runtime argv; retain a wrapper entry with the asset path.
assert 'int main(int argc,char **argv)' in harness
harness = harness.replace('int main(int argc,char **argv)', 'static int check(int argc,char **argv)')
escaped = str(a.archive.resolve()).replace('\\','\\\\').replace('"','\\"')
harness += '\nint main(void) { char *argv[]={"check","'+escaped+'"}; return check(2,argv); }\n'
run_fixture(harness, asan=a.asan, keep=a.keep_harness, image=image,
            dependencies=['external installed archive; flag application and terrain eligibility only'])
