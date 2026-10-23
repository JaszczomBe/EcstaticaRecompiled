# Recover Post-Intro Placement And Motion Queries

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
<!-- /docs-tree:parent -->

Status: basic control/traversal/collision manually confirmed; broader automated physics and full runtime acceptance remain open
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-19

## Goal

Keep Joe at the recovered courtyard placement after the pedestal action, make the required world queries receive real coordinate/actor inputs, and verify movement and turning from press/release input. Do not repair visibility or readiness by forcing coordinates, camera or wait state.

## Current Evidence

The [floor-decoder continuation](../../../../../journal/entries/courtyard-floor-decoder-2026-10-14.md) restores courtyard release. The [terminal root-pose repair](../../../../../journal/entries/terminal-root-pose-2026-10-16.md) now makes Debug and ASan execute the same 30 terminal events, clear the script wait and retain Joe `9988,3328,-17408` in camera 175. A hardware watch identified the invalid next link's writer: a rotation in `FUN_0042b0f4` used the event as its matrix. Actor-matrix and saved-position destinations now match original instructions, with 1,152 original-code fixture cases normally and under ASan. Child conversion through `0x42d860` remains outside that repair.

The [player-input continuation](../../../../../journal/entries/player-motion-inputs-2026-10-16.md) recovers `0x4575c4`'s packed actor fields and retained owner, then replaces stale generated keyboard labels with live scan-code reads. Joe now binds representation **12**, rests in slot 1000/idle action 871, and Up reaches movement event `0x13`. The former slot 39/action 338 selection was driven by a stale nonzero modifier, not proof of walking. Selector and keyboard-load comparisons pass 10,368/256 original-code cases normally and under ASan.

The [motion-query continuation](../../../../../journal/entries/player-motion-query-2026-10-16.md) implements [Task 05](task-05-recover-player-motion-vector-ownership.md): actor/vector transforms, recursive splitting, dual polar outputs, obstacle/slide/height arguments and turn matrices. Debug now completes a corrected press/release probe with Up displacement and Left/Right turning; release stops those changes. Down selects its action but shows no displacement in 60 update entries. ASan reaches Up displacement, then fails after release. A watch identifies `FUN_00449680` writing floor result -16000 to Joe's height before fallback/action teardown; [Task 06](task-06-recover-release-gravity-query-ownership.md) owns the next bounded family. Full experimental ASan, real-map collision/traversal and 60 seconds after control readiness remain unproven.

The [queued idle-action repair](../../../../../journal/entries/player-idle-action-2026-10-19.md) closes Task 06's observed bad-height producer: the idle caller passed a representation pointer as an action ID and loaded a FAN that replaced the floor grid. Original +0x162 queue ownership is restored in C and the generator. Both Debug/ASan arrow probes complete at height 3328/camera 175. Up release has additional displacement during its queued action; the earlier immediate-stop result is superseded. Settled stopping, Down displacement, collision and traversal remain open.

The [manual-input continuation](../../../../../journal/entries/player-release-and-spin-2026-10-19.md) reproduces actual SDL Left release leaving its held byte set, then repairs release symmetry in the compatibility bridge. It restores the original clock wait after observing 173 zero-time facing changes and recovers `0x42ed6c` actor/time/range and angle ownership from the reported crash. New comparisons and actual SDL Debug/ASan replays pass. Turn release settles facing at rest; longer Down input displaces. Up/Down still change facing with both turn bytes clear, so [Task 07](task-07-recover-motion-query-steering.md) owns the next bounded investigation. Straight controls, collisions, camera traversal and sustained full-runtime ASan acceptance remain open.

NPC query/range/placement inputs have original-x86 comparisons. Full activation/loading remains open in [Task 04](task-04-recover-npc-spawn-query-inputs.md); F5 defers only automatic background spawning. Existing actors, scripts and player queries still run.

The earlier wrong-height/rooftop and forest results are historical in the [F5 journal](../../../../../journal/entries/f5-diagnostic-route-2026-10-14.md) and [palette continuation](../../../../../journal/entries/palette-and-release-handoff-2026-10-14.md). The final position event executes with actual action data, and the scene owner has no end callback. The corrected grid contains courtyard descriptors and selects 175; an additional teleport/camera lock is not needed.

The user now reports input works and prioritizes missing scene changes. The [camera-traversal continuation](../../../../../journal/entries/courtyard-camera-traversal-2026-10-19.md) completes [Task 08](task-08-recover-courtyard-camera-transitions.md): actual SDL Debug/ASan camera **175 → 166 → 175** round trips retain Joe, wait/modal zero and released keys. It removes the wrong camera-slot-to-script-resource activation, fixes cached-camera storage and supplies terrain-script code/actor inputs. ASan follows a different movement route and returns elsewhere within camera 175. Broader steering/collision and sustained/full experimental ASan acceptance remain open; bounded traversal is now demonstrated.

The [steering audit](../../../../../journal/entries/courtyard-steering-audit-2026-10-19.md) closes Task 07's first-turn family: 128 complete query replays and 896 real floor responses match original code, including the observed opposite/zero-vector turns. Different time/vector inputs precede differing paths; no gameplay patch is justified by the captured samples. Debug/ASan both complete the round trip plus another 60 seconds with released input and stable Joe state. This proves bounded post-traversal idle stability, not continuous active play or every collision path. Next priority is explicit stair/wall/blocked-boundary behavior and wider exploration.

## Next Bounded Action

The [manual castle report](../../../../../journal/entries/manual-castle-exploration-2026-10-19.md) confirms stairs, angled ledges, collisions and extended free exploration. Basic control is now practically validated. Prioritize [Task 09 population/interaction](task-09-recover-scene-population-and-interaction.md) next; retain the investigations below for a newly observed movement failure or later broader acceptance rather than blocking object recovery on additional locomotion work. Exact manual duration/build and exhaustive collision/falling behavior remain unspecified.

1. Preserve the recovered terminal root-pose destinations and matching Debug/ASan event chain. If a required child conversion reaches `0x42d860`, split its explicit node/matrix/vector inputs rather than broadening the root fixture claim.
2. Preserve [Task 06](task-06-recover-release-gravity-query-ownership.md)'s queued action-ID repair and floor-map ownership evidence. Retain the release/clock repairs and Task 07's verified original obstacle steering; use captured inputs to investigate any new deviation rather than suppressing query-driven turns.
3. Preserve Task 05's original-code vector/query fixtures and corrected extended-key probe. Actual SDL releases survive in both builds and Down displaces in longer runs; establish direction/steering fidelity and real-map floor/stair/blocked-boundary behavior. The [turn-caller repair](../../../../../journal/entries/player-turn-callers-2026-10-16.md) restores both simultaneous-input actor arguments with original-code and Debug/ASan call-boundary proof; the repaired idle caller now removes the observed ASan bad-height failure.
4. Original `0x42ad87` completes only when progress is greater than duration and retains the EAX-selected slot; current `0x42ad60` uses greater-or-equal and substitutes the actor slot. These remain candidates requiring bounded proof; they were not changed by the floor repair.
5. Preserve Task 08's demonstrated camera crossings/return and repeatable `--camera-round-trip` probe. Broaden exploration only from real input, trace Debug/ASan steering differences and establish complete collisions plus sustained control readiness. Wait zero alone does not prove player readiness.

## Boundaries And Verification

Preserve scripts, action events, root motion, collision/falling and camera/resource selection. Keep the corrected script/floor route opt-in. Report the explicit background-spawn and visual omissions; do not call them full NPC/HUD fidelity. Original meshes, DirectDraw Lock and NPC activation follow basic Joe control unless required by its logic.

Use all four launch flags from [building](../../../../../building.md), separate logo/horseback/pedestal phases and release injected keys. Zero logo delay is only a crash-probe shortcut. Capture actual state and normal SDL presentation before input, during held input and after release. Require visible coordinate/orientation changes, an adjacent-view crossing/return, and 60 seconds after genuine control readiness. Debug and ASan must reach each claimed boundary; a fixture, timeout or input latch cannot substitute.

Retain default wrapper, arrow and SDL modal checks. Unset `DISPLAY` for headless X11 probes. Mirror narrow source-backed repairs and verify all four generated artifacts.
