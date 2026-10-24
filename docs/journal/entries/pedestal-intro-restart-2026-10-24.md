# Pedestal intro restart after early skip — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The user's ordinary F5 run skips the horseback intro, enters the pedestal scene,
then unexpectedly resumes the horseback sequence and eventually kills Joe. Exact
replay reproduces the whole recording. Two original actor-name contracts restore
the skip script's cleanup: its byte pool must span 40,000 bytes, and its initial
names must retain their complete suffixes. Fresh early-skip Debug/ASan routes now
finish the pedestal scene, retain control and pass populated courtyard returns.

## Original capture and reproduction

Session `session_20261024_111934_221` has complete replay and inspection. Its pinned
Debug executable SHA-256 is
`1136dedd1b9d0ebfe0ef669ada3a551b4a96ed4f69073b8fa3877e005653d698`.
The verified immutable bundle is preserved outside session retention at
`.tmp/replay-bugs/pedestal-restart-20261024` and `/tmp/e2-pedestal-restart-20261024`.

Fresh exact replay completes through sequence **1,485,105,582**, matching all
**1,810 checkpoints**. Evidence: `/tmp/e2-pedestal-exact-native`.

The recorded Space tap occurs at progress **83/495** of the first horseback
action, in camera 1073. It starts `Start_sc` and camera 175 correctly. While Joe
is still restrained, original scene 1564 (`horse`) completes from an actor left
on its old track. `FUN_0042a70c` dispatches its completion code **1257**,
`dav:horse2`, activating scene **1563** and camera **1072**. Later horseback scenes
continue; Joe ultimately has health **-100**, state **5**, and requester **0x27**.
The intermediate **0x28** requesters are manual Escape menus. A process exit zero
does not establish successful gameplay.

Bounded GDB replay captures the first unwanted activation:

`FUN_00452140 ← FUN_0044f508 ← FUN_0044f2fc ← FUN_0042a70c`.

The old horse record remains the completion owner even though the current view
is the pedestal. Its original duration explains why the restart occurs partway
through that scene. Evidence: `/tmp/e2-pedestal-trace{,2}.log`.

## Actor-name recovery

The original `dav:skipsc` code **1390** starts `Start_sc` and `St_gobsc`, deactivates
nine named intro actors, and enables population. Its reconstructed nine opcode
**0x5d** actor operands all became **0x2fff**. That means actor lookup failed;
starting the next scene alone cannot retire the old intro actors.

Two defects contribute:

1. Original `0x44673c` adds **0x9c40**, or **40,000 bytes**, to the actor-name pool
   base. The existing allocator already reserves that much. The reconstructed
   interner and lookup instead stop at **10,000 bytes**, returning -1 for later
   names. The installed directory contains **4,120 names / 31,986 bytes**; **2,787**
   entries begin beyond byte 10,000. Original `0x446788` also clears the new
   actor's table slot; duplicate lookup preserves an existing actor.
2. Startup name mirroring copies only the first exported dword of **108** actor
   literals. For example, `w_gob1` becomes `w_go`. Importing the full original
   names then appends duplicates and shifts later identities. Fixing capacity
   alone changes the cleanup tokens but leaves the route broken. Restoring the
   complete original literals in `0x470740..0x470bff` restores the intended IDs.

The repaired live pool matches the installed directory byte for byte. The nine
cleanup IDs are now **3331, 3330, 3329, 3409, 3402, 3401, 3437, 3438, 3407**.
No camera override, forced release/death suppression, hardcoded actor removal or
skip-script replacement is added. Original `skipsc` executes its own cleanup.
The literal mirror restores original constants before the existing startup seed
construction. Diagnostic actor-name reads use the same 40,000-byte boundary.

All reconstructed changes have generator mirrors. Syntax, in-place regeneration
and independent scratch C/header/globals/names parity pass without unrelated
changes.

## Verification

`check-e2-actor-names.py E2WIN95.EXE Code/ECSTATIC.FAN [--asan]` passes normally and
under ASan. It compares all **4,120** append/lookup/reuse cases with original x86,
including complete pool memory, actor-slot ownership and all **108** restored
literals with unchanged neighboring memory. Original strcmp's register bridge is
intercepted; full scene execution belongs to the integration routes.

Original population/constructor/deactivation/callback comparisons, script-name
comparisons and script-flow comparisons pass normally and under ASan. All four
SDL/X11 Debug/ASan builds, the runtime regression wrapper, eight arrow rows and
both SDL requester/OK/resumed-update/Escape checks pass.

| Fresh route | Result | Evidence prefix |
| --- | --- | --- |
| Early first-action Space, Debug and ASan | Pedestal release, all arrows and another 60 seconds of released-input stability pass | `/tmp/e2-pedestal-fixed2-skip1-{debug,asan}` |
| Space at the recorded **83/495** point, Debug and ASan | Both guards, open population gate, generated actors, courtyard crossing/return at floor 3328, health 100 and five seconds idle pass | `/tmp/e2-pedestal-progress83-{debug,asan}` |
| Third horseback-action Space, Debug | Pedestal release and all arrows pass | `/tmp/e2-pedestal-skip3-debug` |
| Natural intro to water, Debug and ASan | Camera 543, original transition, forward swimming at height 5120, health 100/state 4, swimming flag 8 and no modal | `/tmp/e2-pedestal-water-{debug,asan}` |
| Skip at 83/495 through water, Debug | Pedestal release, input-only traversal and forward swimming pass; health 100/state 4, flag 8 and no modal | `/tmp/e2-pedestal-progress83-water-debug` |
| Skip at 83/495 through water, ASan | 240-second probe timeout at waypoint 12 before water; last sample health 100/state 4, no reported sanitizer error; incomplete | `/tmp/e2-pedestal-progress83-water-asan` |

The Debug camera-175 SDL image after release was visually checked. These are real
SDL input routes with observational GDB checkpoints, not coordinate/angle/camera
writes. `probe-e2-player-motion.py` now accepts `--intro-skip-progress 83`, records
health and rejects death during traversal observations. Its population census
reads the complete actor-name allocation.

The unchanged old water helper's first early-skip attempt stops on its own
hardware release watchpoint and fails its readiness assertion before movement:
`/tmp/e2-pedestal-skip-water-debug.log`. This is a probe failure, not a native
crash. The combined continuation uses the current probe's readiness handling;
its local helper is retained in `.tmp/pedestal-startup-20261024/auto-water.py`.

The successful combined Debug run swims from `(-1352,5120,-2697)` to
`(-1459,5120,-2323)` in camera 543, with health 100. The combined ASan timeout's
last sample is `(2598,4096,-12798)`, still before water. It does not pass combined
skip-to-water acceptance; the natural-startup ASan water route and separate
83/495 startup/courtyard route remain the passing bounded ASan checks.

Final executable SHA-256 values are
`a66c1240697042ec42a9274892bd5af44705c8feaccedc4eb9e25acc516ecda5` (SDL Debug)
and `9b7dafe05528a60b347f191bfde13a1bcedf5ebbf7007808618ad7565b27de55`
(SDL ASan). Contract logs use `/tmp/e2-pedestal-{actor-fixture,population-fixture,script-flow}*`;
build/baseline/arrow/requester logs use the same `/tmp/e2-pedestal-` prefix.

The original recording with the repaired executable correctly returns
**74 / DIVERGED**, sequence **40,350,480**, last matching checkpoint **17**.
Changing the cleanup changes native service/state history. Compatibility mode
keeps that strict rejection; the fresh input routes supply post-repair evidence.

## Remaining acceptance

Ordinary human F5 repetition of the exact skip/pedestal/water route remains the
manual confirmation. Shore exit, held-item swimming, broader combat/interactions,
workshop re-entry and sword pickup remain open. The new passing populated routes
do not retroactively close the separately recorded broader Debug floor-return
failure or establish full experimental ASan gameplay acceptance.

The startup regression takes priority over the next object interaction. After
manual confirmation, resume water acceptance and the existing workshop target.
