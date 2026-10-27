# Enemy-play crash and dropped potion — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Preceding work: [enemy animation recovery](enemy-model-and-animation-2026-10-27.md).

## Human evidence

The user likes the recovered enemy presentation, then reports a short-play crash
through `FUN_00452a94 → FUN_00414e68 → FUN_0043cac0` and a dropped yellow pickup
that attaches without healing or bottle removal. F5 receipts identify sessions
**20261027_210719_636** and **20261027_211457_194**, both on Debug executable
`a3cdf42315cb73ba9295edbcf0376a821cdaf1e73007fbed246a21022fcf2ac4`.
Both recordings/inspections are incomplete and retention-protected. The latest
session is frozen in `.tmp/enemy-followup/human-211457/`, with its matching pinned
executable; the original session is preserved.

Materialized latest inspection identifies the drop as actor **3820/w_pot1**,
representation **424/w_pot**, rather than workshop actor **537/fakepot2**. It
appears near a dead enemy, plays **1542/potapr → 1557/potglow**, attaches during
Joe's **693/heropkupl_m** at snapshot **1085**, then remains attached. Joe's
health is **65** at pickup and later **60**. This is distinct from the earlier
[workshop bottle repair](consumed-potion-removal-2026-10-24.md).

All new artifacts below live under ignored `.tmp/enemy-followup/`. Agent probes
are bounded, recording-disabled, and use isolated output. Existing staged and
unstaged player/enemy work is preserved; no staging, commit or push.

## Crash: false action-directory entries inside sound data

The captured updating actor requests animation **1256/mummturnl**. Its runtime
index points to archive offset **19120049**, a sound-containing FANT resource
with embedded `SIMD` data. Parsing that as an action eventually reaches bitmap
loading with garbage identity/dimensions; eviction selects a still-unpublished
record, and fatal error formatting faults. The formatter is the final crash
location, not the initial fault.

The loose-archive index scanned every ten bytes for up to 16 KiB after each FANT
signature. It accepted apparent type **0x0b** / action IDs inside unrelated binary
payload, overwriting correct earlier entries. Version-55 action headers actually
begin at resource **+0x22**, after the original 34-byte prefix. Restricting the
existing action branch to that location repairs **seven overwritten real entries**
and removes **two phantom entries**. Action 1256 resolves to **11315890**; action
526 resolves to **10005380**, rather than false sound offset **24711349**.
Every one of the **2000** resulting entries, including all **1333** present actions
and absent slots, matches the installed original `OFFSETS` directory byte values.
No bitmap-capacity guess, eviction skip or invalid-pointer fallback is added.

`resource1256-03` reproduces the same crash using the exact original resource load
from the courtyard. `resource1256-pass-debug-05` and `resource1256-pass-asan-05`
publish the correct action and complete their bounded input/render probe. These
are explicit resource-load fixtures, not ordinary-input gameplay acceptance.

The immutable pinned-binary replay `human-potion-06` reproduces the human crash
at the end of the captured prefix. The **index-only** repaired Debug replay
`human-fixed-debug-07` matches all **256 checkpoints** and exits **75/INCOMPLETE**
on prefix exhaustion at sequence **1923275600**, without that crash. The matching
ASan replay `human-fixed-asan-07` instead diverges in world tick at checkpoint
**180**, last matching **179**, sequence **1248445786**; it is not accepted replay.

Replay qualification is deliberately narrow: the ordinary dummy-driver override
first rejects the absent `env.SDL_VIDEODRIVER` startup field (`replay-original-01`).
The local GDB diagnostic then selects dummy SDL **after** startup identity
validation. Recorded checkpoint validation remains strict; this is not desktop
SDL qualification. The later representation-name repair changes intended game
behavior, so the index-only 256-checkpoint result is not claimed for final source.
The final-source exact-resource and original-directory checks remain valid.

## Dropped bottle: truncated representation-name pool

Pinned replay observes the real pickup callback for actor **3820** at sequence
**1437527386**, dispatching original script **1518/dav:w_pot1**. Its condition
should test representation **424** using token **0x81a8**, but the loaded script
contains **0x8fff**. The actor itself correctly retains requested representation
**424** at `+0x122`. The false condition skips the script's entire drinking,
healing and bottle-removal branch, although the pickup callback already attached
its model to Joe.

The representation interning and lookup wrappers used **1000** bytes despite the
original **4000-byte** allocation. The installed directory has **488** names in
**3872** bytes; `w_pot` starts at byte **3332**. Original `0x446a9c` adds **0xfa0**
(4000), and `0x446ae8` clears a newly interned representation's cache slot at
`0x635980 + id*4`. Both wrappers now use 4000; the interner clears only a newly
published slot, preserving an existing loaded representation on duplicate lookup.
Reconstructed C and `GenerateRecon.js` agree.

The original drop script then requests Joe's drinking animation, queues the
potion-specific continuation, fades the bottle, and schedules original healing
code **1515/dav:heltpot1**. Health/removal follow those original scripts and events;
there is no direct health increment or forced deletion in the repair.

`potion-fields-08` retains the old live operands and unchanged post-script queues.
The expanded original-name fixture initially fails the old representation-slot
ownership assertion (`representation-old-control.log`). Final normal/ASan
fixtures compare all **488** installed representation names against original x86,
including **355** names beyond byte 1000 and `w_pot == 424`, plus fresh-slot clearing,
duplicate preservation, lookup and pool memory. The existing **1800** animation
name cases continue to pass.

## Native consumption checks and remaining limits

The bounded local drop fixture first obtains **real guard-inflicted damage**,
then invokes original spawn event `FUN_0042f9c0` for **3820/w_pot1**, action
**1542/potapr**, at an existing bone. It uses actual keyboard Space pickup and
observes subsequent original scripts/updates. It never assigns Joe's health,
actor coordinates, script operands, attachment completion or bottle lifetime.
This explicitly tests original dropped-resource consumption; it does **not**
prove a fresh enemy-kill/drop sequence or repeat the human's armed journey.

- `dropped-potion-asan-10`: original scripts **1518** and **1515** execute; health
  **95 → 100**, bottle attachment and representation both become **0**; actual
  Cancel/resume/Quit exits **0**, no sanitizer report.
- Final-source `dropped-potion-asan-14`: bounded approach/Space retries also pass
  original pickup/healing/removal and native menu exit **0**. Health reaches
  **100** and later falls to **80** under continuing real enemy attacks; requiring
  the final sample to stay at 100 would misattribute later damage.
- `dropped-potion-debug-10`: guard attacks interrupt the single pickup tap; bottle
  never attaches and health falls **95 → 70**. This is a failed fixture route.
- `dropped-potion-debug-12`: clearance walking misses its second waypoint.
- `dropped-potion-debug-14`: approach to the moving/stairside drop misses its
  waypoint. Neither failed navigation attempt proves Debug consumption.

Debug native consumption remains a qualification limit. Debug exact-resource
loading and normal original-code comparisons pass; ASan demonstrates real Space
consumption with healing/removal twice. Do not turn the failed Debug routes into
passes or describe the spawn fixture as a full combat regression. The full suite,
longer gameplay and a new human retest have not been completed on these repairs.

## Verification and reproduction

All four SDL/X11 Debug/ASan builds pass. Scratch generation matches all four
artifacts (`parity-final-13`); whitespace and connected documentation checks pass.
Normal/ASan name comparisons pass **1800 animation + 488 representation** cases,
and normal/ASan water-entry fixtures verify all **2000** original action offsets,
**1922** actor headers, **256** reload cases and **216** flag/water cases. ASan
additionally passes **16384** pickup-attachment cases, **256** pickup event handoffs
and **14208** original bitmap allocation/publication/eviction cases. The bitmap
allocator itself remains unchanged. Final identities are in `final-identities.json`.

The broad suite-contract command has **66 PASS / 1 FAIL** on both
`suite-contracts-final.log` and `suite-contracts-serial-15.log`: the unchanged
`test_timeout_kills_descendant_and_retains_output` observes a descendant before
it disappears/becomes a zombie. That same check passes alone in
`suite-timeout-isolated-15.log`. This is a retained cleanup/timing qualification
failure, not a passing complete contract run; the closed suite milestone is not
reopened or its assertion weakened in this gameplay repair.

```sh
python3 scripts/check-e2-water-entry.py /path/to/E2WIN95.EXE /path/to/Files/ECSTATIC --asan
python3 scripts/check-e2-animation-names.py /path/to/E2WIN95.EXE /path/to/Code/ECSTATIC.FAN --asan
python3 scripts/check-e2-pickup-attachment.py /path/to/E2WIN95.EXE --asan
python3 scripts/check-e2-bitmap-records.py /path/to/E2WIN95.EXE --asan
```

The local `resource-fixed-probe.py`, `replay-observe.py` and
`dropped-potion-approach-probe.py` retain the exact bounded diagnostic procedures
used above. Ordinary human investigation still uses the single F5 launch, with
original player/enemy bodies, logging, recording and inspection enabled.
