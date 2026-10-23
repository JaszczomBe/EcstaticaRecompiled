# Recover Player Motion Vector And Query Ownership

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
<!-- /docs-tree:parent -->

Status: implemented contracts; Up displaces in Debug/ASan, full control acceptance remains open
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-16

## Goal

Carry the real actor, displacement and output destinations from action motion into the recovered world-motion query, then prove press/release displacement and turning. Preserve collision/floor/view behavior; do not implement host movement or substitute player coordinates.

## Evidence

[Player input recovery](../../../../../journal/entries/player-motion-inputs-2026-10-16.md) fixes Joe's packed representation selector and live scan-code reads. Representation 12 is bound after release; idle action 871/previous slot 1000 replaces the false modifier-driven slot 39/action 338. Both Debug and ASan reach movement event `0x13` after Up, then fail in `FUN_004272a8` through `FUN_00448c1c → FUN_00448cb4`. ASan reports a write to a returned stack frame; Debug has an uninitialized output and actor-relative output `0x170`. No displacement or turning acceptance is claimed.

Original `0x448cbf/0x448cc1` retains EAX actor in EDI and EDX vector in ESI. `0x448cc3..0x448ce2` passes stack-local output `+0xa8` in EAX, actor `+0x170` in EDX, and displacement X/Z in EBX/ECX to `0x4272a8`. Recover these together with the upstream transform and recursive vector-splitting contract; assigning `in_EAX` from an already-corrupted parameter is insufficient.

## Implemented Result

The [motion-query journal](../../../../../journal/entries/player-motion-query-2026-10-16.md) records original terminal/interpolated event recovery, contiguous actor-local/world vectors, retained recursion, dual polar outputs, full obstacle/slide/height branches and the actor-relative turn matrix. Comparisons pass 1,920 event cases, 394 polar cases and 92,160 query cases normally and under ASan. Query floor/terrain services are intercepted; they do not prove real-map collision fidelity.

The corrected WndProc probe includes extended arrow releases and asserts held bytes. Debug completes all arrow phases: Up changes position, Left/Right change facing, and release stops those changes. Down displacement is not observed in the short probe. ASan reaches Up displacement, then a hardware watch catches a new height write to -16000 in `FUN_00449680`, before fallback/action teardown and a root-pose child fault. [Task 06](task-06-recover-release-gravity-query-ownership.md) owns that gravity/query frontier. Full experimental ASan runtime does not pass.

## Acceptance And Limits

Task 02 retains the overall motion/control goal. Debug's bounded Up/turn/release evidence does not close Down, real-map blocked/floor/stair behavior, two view crossings or 60 seconds after genuine control readiness. Full NPC activation, models/HUD and full experimental ASan runtime remain separate acceptance. The earlier first-Up `0x4272a8` failure above is historical and superseded by the implemented result.
