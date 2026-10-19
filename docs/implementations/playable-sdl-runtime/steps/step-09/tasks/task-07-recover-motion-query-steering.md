# Recover Motion-Query Steering With Turn Keys Released

Status: active; remaining Up/Down heading changes originate in FUN_00448cb4
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-19

## Goal

Establish source-consistent forward/backward movement after a turn key is released. Preserve real obstacle sliding, floor/stair queries and view changes; do not suppress all query-driven rotation or clamp Joe into camera 175.

## Evidence

The [SDL release/clock/target-facing continuation](../../../../../journal/entries/player-release-and-spin-2026-10-19.md) repairs three contracts from the user's manual spinning/crash report. Actual SDL key-up now clears its held byte, and a released turn preserves facing through a 150-update no-input phase in both runtimes. The original clock wait prevents poll-count exits from repeatedly turning at zero elapsed time. The target-facing helper/caller have original-code actor/time/range comparisons.

Up/Down still change facing while their turn-key bytes remain zero. The final ASan SDL replay `/tmp/e2-spin-sdl-steering-asan` records **39 calls**, all from **FUN_00448cb4**: 36 angles -512 and three +512. Both turn bytes are clear in the movement packet, and release settles facing. This identifies a different producer from stale keyboard input or the two combined-input player callers.

The query's `found` branch projects motion onto a blocker tangent and calls `0x42b074` with a limit of elapsed ticks × 512 for slots 1/7/180/183. Existing 92,160 original-code query comparisons include synthetic obstacles and intercepted floor services, but do not prove the actual courtyard obstacle/floor inputs or expected physical steering. The current evidence does not establish that these real-map rotations are erroneous, nor that the user's circling report is fully resolved.

The user subsequently confirms input works and prioritizes exploration. [Task 08](task-08-recover-courtyard-camera-transitions.md) now demonstrates actual SDL **175 → 166 → 175** camera round trips in both runtimes. The same initial Up input produces different Debug/ASan routes: Debug reaches the courtyard directly; ASan initially circles within 175 and reaches 166 after reversing to Down. Both return to 175 with released keys, but at different positions. The [camera journal](../../../../../journal/entries/courtyard-camera-traversal-2026-10-19.md) records those limits; this task retains steering fidelity rather than blocking the now recovered camera transitions.

## Next Bounded Action

1. At the first unexpected query turn, capture Joe's radius +0x9a, motion vector/angle, flags, prior slot, candidate actors and attachment exclusions. Record all five perimeter sample coordinates, floor results and descriptor chains, selected blockers, tangent and projected motion.
2. Compare that recorded query with original instructions and the same floor responses. If arithmetic matches, trace the first incorrect radius, descriptor, actor placement or floor response rather than changing the turn limit.
3. Recover only the proven owner/contract, mirror it in GenerateRecon.js and add a focused comparison for the newly exposed boundary. Keep keypad/arrow release, real-tick waiting and target-facing tests intact.
4. Repeat actual SDL turn → release → Up/Down with state/caller traces, then establish direction, floor/stair/blocked-boundary behavior and genuine view crossing/return. Keep Task 02's overall gameplay acceptance open until sustained sessions pass in Debug and ASan.

## Verification And Limits

Use the four F5 flags and `scripts/probe-e2-player-motion.py --sdl-events --turn-forward left --release-turn-first --frames 150`. The probe now captures each turn helper's caller, angle, elapsed time and motion distance. Its zero exit establishes completed phases only. No-input release, backward displacement and collision fidelity are distinct claims. Preserve original-code fixtures, baseline regressions, generator parity and staged/unstaged separation. Full NPC activation and original models/HUD remain separate work.
