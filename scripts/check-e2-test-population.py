#!/usr/bin/env python3
"""Check opening/ladder test fixtures against original actor/scene identities.

The fixture intentionally changes population, not recovered game behavior.
Execute its production load gate and verify all other IDs remain eligible.
"""
import argparse
from pathlib import Path
import struct

from e2_original import run_fixture
from e2_population_profile import NONCOMBAT_ACTORS

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive', type=Path)
parser.add_argument('--asan', action='store_true')
args = parser.parse_args()
data = args.archive.read_bytes()
raw = (args.archive.parent.parent / 'Code/ECSTATIC.FAN').read_bytes()
cursor = 34
pools = []
for _ in range(7):
    names = []
    while raw[cursor]:
        end = raw.index(0, cursor)
        names.append(raw[cursor:end].decode('ascii'))
        cursor = end + 1
    cursor += 1
    pools.append(names)
assert tuple(pools[1][identity] for identity in NONCOMBAT_ACTORS) == ('gob3', 'gob3b', 'korc2')
for scene, camera, identities in ((101, 175, (284, 293)), (251, 347, (602,))):
    assert pools[3][scene] == ('St_gobsc' if scene == 101 else 'blaksmit')
    at = data.index(struct.pack('>5H', 25, scene, camera, 0xffff, 0xffff))
    end = data.index(b'FANT', at)
    resource = data[at:end]
    children=[struct.unpack_from('>5H',resource,offset) for offset in range(len(resource)-9)
              if resource[offset:offset+4]==struct.pack('>2H',26,0xffff)]
    assert set(identities) <= {row[4] for row in children if row[3]==2}
    if scene==101:assert {row[4] for row in children}==set(identities)
for identity, name in ((0, 'Joe'), (261, 'stok1'), (980, 'kdorr'), (3717, 'nschwrt1')):
    assert pools[1][identity] == name, (identity, pools[1][identity])
source = (ROOT / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
start = source.index('  if (E2R_actor_load_id_override != -1)', source.index('void FUN_00451f5c(void)'))
end = source.index('  parse_result = 0;', start)
gate = source[start:end]
# Execute the actual early gate, before unrelated diagnostics/loader internals.
gate = gate[:gate.index('  if ((actor_id < 0)')]
assert 'if (E2R_TestSuppressActor(actor_id)) return;' in gate
scene_start = source.index('void __fastcall FUN_00452140(')
scene_gate = source.index('      if (E2R_TestSuppressActor(*psVar3)) continue;', scene_start)
assert scene_gate < source.index('E2R_TraceSceneChildActivate("52140.child"', scene_start)
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef uint32_t undefined4;
static int E2R_actor_load_id_override = -1;
static undefined4 DAT_0047a470;
static int allocations;
'''
harness += '#include "' + str(ROOT / 'E2Recomp/platform/e2recomp_test_population.h') + '"\n'
harness += 'static void load(void) { undefined4 in_EAX=0,uVar3; int actor_id;\n' + gate + '\nallocations++;}\n'
harness += r'''
int main(void) {
  const char *profiles[]={NULL,"","live","noncombat-opening","noncombat-ladder"};
  for(unsigned p=0;p<5;p++) {
    if(profiles[p])setenv("E2R_TEST_POPULATION",profiles[p],1);else unsetenv("E2R_TEST_POPULATION");
    E2R_test_suppressed_mask=0;
    for(int id=0;id<5000;id++) {
      int blocked=p>=3 && (id==284 || id==293 || id==602);
      E2R_actor_load_id_override=id;DAT_0047a470=0x12345678;allocations=0;
      load();
      assert(allocations==!blocked && DAT_0047a470==0x12345678 && E2R_actor_load_id_override==-1);
    }
    assert(E2R_test_suppressed_mask==(p>=3?7u:0u));
  }
  puts("PASS: original guard/smith identities; 25,000 production load-gate cases; opening/ladder fixtures retain Joe/props/items");
}
'''
run_fixture(harness, asan=args.asan)
