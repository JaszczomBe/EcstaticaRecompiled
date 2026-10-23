# Recover Courtyard Camera Transitions

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
<!-- /docs-tree:parent -->

Status: completed for bounded 175 → 166 → 175 traversal in SDL Debug and ASan
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-19

## Goal And Result

Allow Joe to leave the pedestal view for the castle courtyard and return using actual movement input, preserving the current actor and the original camera/background and terrain-script paths.

The [camera-traversal journal](../../../../../journal/entries/courtyard-camera-traversal-2026-10-19.md) identifies the first blocker: an added helper treated camera 166 as a FAN script-resource ID, opening a missing-scene requester before background loading. Ordinary view changes now follow original `0x44c2e5..0x44c302` without that call. The cached-camera word read uses the same dword as the original write/test. A subsequently reached terrain trigger now passes its code-table record and current actor through the existing recovered script wrapper.

## Verification

Extended scene-grid comparisons pass normally/ASan: 16,384 grid cases, 16,384 cached-camera cases, 1,199 camera/background dispatch cases, 16,384 terrain-script cases and four no-view fallbacks. Existing script-wrapper/nested-ownership comparisons pass. Generated C matches the generator; all four builds, baseline wrapper, eight arrow rows and both SDL requester checks pass.

`scripts/probe-e2-player-motion.py --camera-round-trip` uses real SDL keys after the observed release checkpoint and captures both boundary crossings and normal presentation. Debug walks Up into camera 166, then Down returns to camera 175/height 3328. ASan's Up attempt follows a different path; Down crosses into 166, then Up returns to 175/height 3328. Both retain Joe, wait/modal zero and clear held keys after release. No actor/camera/coordinate values are forced. The normal Debug courtyard and return backgrounds were visually inspected. Evidence prefixes and commands are in the journal.

## Remaining Boundaries

This completion covers view selection, the required caller repairs and bounded crossing/return. It does not establish identical Debug/ASan steering, exact retracing, every scene/resource transition, complete collisions/falling, NPC activation or 60 seconds after readiness. [Task 07](task-07-recover-motion-query-steering.md) retains motion-query fidelity; [Task 02](task-02-recover-post-intro-placement-and-motion-queries.md) retains overall gameplay and full experimental ASan acceptance. Preserve the explicit background-spawn and original-model/HUD omissions.
