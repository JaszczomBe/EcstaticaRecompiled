# Recover NPC Spawn Query Inputs

Status: bounded query/range/placement inputs implemented; full activation/loading deferred behind Joe control
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-14

## Goal

Make the existing NPC population/spawn update receive valid world-query vectors and actor-range inputs so Debug and ASan can inspect courtyard control reliably. Preserve population, actor lifetime and terrain behavior.

## Evidence

The [floor-decoder continuation](../../../../../journal/entries/courtyard-floor-decoder-2026-10-14.md) repairs the forest handoff but reveals an independent stability dependency. ASan faults in `FUN_00448744` through `FUN_00448a48 → FUN_00448a3c → FUN_0044dca4 → FUN_0044e354`; one Debug probe instead crashes in `FUN_0044db80`. The successful continuous Debug capture remains camera 175 after release, without proving repeatable stability or motion.

Original `0x44dd24/0x44dd32/0x44dd3f` pass one contiguous local XYZ vector to the floor, visibility and descriptor lookups. Original `0x44db87` retains the first actor ID in ESI and range length in EDX across RNG. The C loses the query pointers and first ID. Later activation/position/deactivation helpers also retain missing inputs; audit only dependencies exercised by the supported spawn path.

## Implemented Slice

`FUN_0044dca4` now retains a contiguous world vector, the original terrain-to-actor ranges, nine floor samples and actor identity across overlap/height rejection and activation. `FUN_0044db80` retains first ID/count and selected load identity. Original-x86 comparisons pass 448 range cases and 1,060 terrain/placement/query cases normally and under ASan, with external services intercepted. The explicit deferral option makes no actor/query mutations when enabled. Narrow generator mirrors reproduce the two cleaned functions.

Full spawn-on loading/activation is not accepted: an intermediate live run reaches an invalid requester rather than a proven NPC instance. `E2R_DEFER_BACKGROUND_SPAWNS=1` now explicitly defers this automatic population leaf for the Joe-first F5 prototype and reports it on screen. Existing script actors and player queries still update. Resume full spawn-on verification after [Task 02 control](task-02-recover-post-intro-placement-and-motion-queries.md).

## Remaining Action And Verification

1. Recover the three query calls with a real contiguous vector, retaining updated Y. Compare against original instruction blocks with intercepted query services, including no-floor/no-spawn branches.
2. Recover `0x44db80`'s actor range, selection and activation identity; prove active-slot skipping and table/flag changes against original instructions. Audit `0x451f5c` and placement/cleanup inputs only when reached.
3. Preserve the full population update when deferral is off: this is live actor logic. The explicit Joe-first option defers only `0x44dca4`; it does not bypass all of `0x44e354`, existing actors, scripts or player queries. Do not manufacture the reference creatures or suppress collision/falling.
4. Mirror narrow repairs, regenerate with four-artifact parity, rebuild and rerun bounded Debug/ASan at the relevant phase plus baseline regressions. Then resume [Task 02 movement](task-02-recover-post-intro-placement-and-motion-queries.md), with press/release displacement and an adjacent-view crossing as separate acceptance.
