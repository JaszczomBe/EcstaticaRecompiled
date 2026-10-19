# Recover Post-Intro Placement And Motion Queries

Status: active; terminal root-pose corruption repaired, player movement/turning next
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-16

## Goal

Keep Joe at the recovered courtyard placement after the pedestal action, make the required world queries receive real coordinate/actor inputs, and verify movement and turning from press/release input. Do not repair visibility or readiness by forcing coordinates, camera or wait state.

## Current Evidence

The [floor-decoder continuation](../../../../../journal/entries/courtyard-floor-decoder-2026-10-14.md) restores courtyard release. The [terminal root-pose repair](../../../../../journal/entries/terminal-root-pose-2026-10-16.md) now makes Debug and ASan execute the same 30 terminal events, clear the script wait and retain Joe `9988,3328,-17408` in camera 175. A hardware watch identified the invalid next link's writer: a rotation in `FUN_0042b0f4` used the event as its matrix. Actor-matrix and saved-position destinations now match original instructions, with 1,152 original-code fixture cases normally and under ASan. Child conversion through `0x42d860` remains outside that repair.

The repaired post-release route binds **representation 67 at actor `+0x11e`** and retains it. The earlier zero-reference observation is superseded on this route; the packet's separate zero attachment is `+0xf2`. Up/Left synthetic press/release still produces no displacement or facing change. Up selects slot 39 before the final representation-slot gate (previous 1000, state 4). The retained action is `0xac263c`, duration 40; its `FUN_0042ae80` progress is normalized Q16, so 63882/65520 is not evidence of duration overrun. Follow selected-slot metadata/events and actual root-motion/query inputs next.

NPC query/range/placement inputs have original-x86 comparisons. Full activation/loading remains open in [Task 04](task-04-recover-npc-spawn-query-inputs.md); F5 defers only automatic background spawning. Existing actors, scripts and player queries still run. The bounded ASan release probe now completes without the prior fault; full experimental runtime, 60 seconds after genuine control readiness and traversal remain unproven.

The earlier wrong-height/rooftop and forest results are historical in the [F5 journal](../../../../../journal/entries/f5-diagnostic-route-2026-10-14.md) and [palette continuation](../../../../../journal/entries/palette-and-release-handoff-2026-10-14.md). The final position event executes with actual action data, and the scene owner has no end callback. The corrected grid contains courtyard descriptors and selects 175; an additional teleport/camera lock is not needed.

## Next Bounded Action

1. Preserve the recovered terminal root-pose destinations and matching Debug/ASan event chain. If a required child conversion reaches `0x42d860`, split its explicit node/matrix/vector inputs rather than broadening the root fixture claim.
2. Trace keyboard state through selected slot 39, representation 67's action metadata and event/motion evaluation. Explain why the selected action advances without displacement despite a bound `+0x11e`. Recover necessary motion inputs without requiring a full model renderer or adding host-driven movement.
3. Audit `0x448c1c/0x448cb4` actor/vector/mode inputs, retaining actual contiguous vectors. Compare required query branches with original instructions, including floor/stair/blocked-boundary cases.
4. Original `0x42ad87` completes only when progress is greater than duration and retains the EAX-selected slot; current `0x42ad60` uses greater-or-equal and substitutes the actor slot. These remain candidates requiring bounded proof; they were not changed by the floor repair.
5. Once movement is coherent, test arrow press/release displacement and turning, then cross a real view boundary and return. Wait zero alone does not prove player readiness.

## Boundaries And Verification

Preserve scripts, action events, root motion, collision/falling and camera/resource selection. Keep the corrected script/floor route opt-in. Report the explicit background-spawn and visual omissions; do not call them full NPC/HUD fidelity. Original meshes, DirectDraw Lock and NPC activation follow basic Joe control unless required by its logic.

Use all four launch flags from [building](../../../../../building.md), separate logo/horseback/pedestal phases and release injected keys. Zero logo delay is only a crash-probe shortcut. Capture actual state and normal SDL presentation before input, during held input and after release. Require visible coordinate/orientation changes, an adjacent-view crossing/return, and 60 seconds after genuine control readiness. Debug and ASan must reach each claimed boundary; a fixture, timeout or input latch cannot substitute.

Retain default wrapper, arrow and SDL modal checks. Unset `DISPLAY` for headless X11 probes. Mirror narrow source-backed repairs and verify all four generated artifacts.
