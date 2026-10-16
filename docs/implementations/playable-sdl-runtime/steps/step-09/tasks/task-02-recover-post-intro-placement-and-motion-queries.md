# Recover Post-Intro Placement And Motion Queries

Status: active; courtyard release restored, player movement/terminal event ownership next
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-14

## Goal

Keep Joe at the recovered courtyard placement after the pedestal action, make the required world queries receive real coordinate/actor inputs, and verify movement and turning from press/release input. Do not repair visibility or readiness by forcing coordinates, camera or wait state.

## Current Evidence

The [floor-decoder continuation](../../../../../journal/entries/courtyard-floor-decoder-2026-10-14.md) fixes shifted floor descriptors caused by rejecting valid high-address hosted streams. With the four F5 flags, including explicit background-spawn deferral, continuous Debug completes release and stays at camera 175 with Joe `9988,3328,-17408`, depth 4739, wait 0/modal 0. Up latches without position changes. Actor state is 4, facing -13056, action field `0xac263c`, duration 40, progress 63882; motion-reference field `+0x11e` is zero. Home `12800,256,-3584` and previous `2048,16384,14336` are trace evidence, not replacement coordinates.

NPC query/range/placement inputs now have original-x86 comparisons. Full activation/loading remains open in [Task 04](task-04-recover-npc-spawn-query-inputs.md); F5 defers only automatic background spawning. Existing actors, scripts and player queries still run.

Experimental ASan with spawning deferred reaches terminal `FUN_0042b004`, then faults on an invalid event link. It logs event `0x776434` as type `0x17`, then incorrectly follows `0x77643a` rather than the Debug `0x776442` next record. Watch the link write and root/previous-pose helper effects before adding pointer guards. ASan has not passed the handoff.

The earlier wrong-height/rooftop and forest results are historical in the [F5 journal](../../../../../journal/entries/f5-diagnostic-route-2026-10-14.md) and [palette continuation](../../../../../journal/entries/palette-and-release-handoff-2026-10-14.md). The final position event executes with actual action data, and the scene owner has no end callback. The corrected grid contains courtyard descriptors and selects 175; an additional teleport/camera lock is not needed.

## Next Bounded Action

1. Trace terminal event links through `0x42b880`/`0x42b0f4`; recover matrix/root/previous-state destinations from original registers. Reuse the recovered Euler-matrix helper where its contract matches. Verify Debug and ASan finish the same event chain before claiming readiness.
2. Trace keyboard state into the real actor's selected action and motion-reference table. Explain why `+0x11e` is zero and why the selected action progresses without displacement. Recover necessary representation/motion metadata without requiring a full model renderer or adding host-driven movement.
3. Audit `0x448c1c/0x448cb4` actor/vector/mode inputs, retaining actual contiguous vectors. Compare required query branches with original instructions, including floor/stair/blocked-boundary cases.
4. Original `0x42ad87` completes only when progress is greater than duration and retains the EAX-selected slot; current `0x42ad60` uses greater-or-equal and substitutes the actor slot. These remain candidates requiring bounded proof; they were not changed by the floor repair.
5. Once movement is coherent, test arrow press/release displacement and turning, then cross a real view boundary and return. Wait zero alone does not prove player readiness.

## Boundaries And Verification

Preserve scripts, action events, root motion, collision/falling and camera/resource selection. Keep the corrected script/floor route opt-in. Report the explicit background-spawn and visual omissions; do not call them full NPC/HUD fidelity. Original meshes, DirectDraw Lock and NPC activation follow basic Joe control unless required by its logic.

Use all four launch flags from [building](../../../../../building.md), separate logo/horseback/pedestal phases and release injected keys. Zero logo delay is only a crash-probe shortcut. Capture actual state and normal SDL presentation before input, during held input and after release. Require visible coordinate/orientation changes, an adjacent-view crossing/return, and 60 seconds after genuine control readiness. Debug and ASan must reach each claimed boundary; a fixture, timeout or input latch cannot substitute.

Retain default wrapper, arrow and SDL modal checks. Unset `DISPLAY` for headless X11 probes. Mirror narrow source-backed repairs and verify all four generated artifacts.
