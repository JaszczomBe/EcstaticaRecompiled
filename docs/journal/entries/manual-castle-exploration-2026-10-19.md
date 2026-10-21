# Manual Castle Exploration And Population Frontier — 2026-10-19

The user reports manually traversing several stairs and angled ledges, finding collisions work well, and moving freely around the castle for an extended session without problems. This adds practical manual evidence for basic locomotion, physical boundaries and wider exploration beyond the automated courtyard round trip. The report does not specify an exact duration, build or sanitizer configuration; it does not establish every collision/falling path or full experimental ASan acceptance.

The remaining visible gap is scene population and interaction: no switches, doors, traps, enemies or pickups such as points/weapons are present. Prioritize that frontier over more locomotion work unless a new concrete movement failure appears. Original models remain secondary; use cylinders for recovered instances where applicable.

## Known Deferral And Separate Resource Paths

The current F5 launch explicitly sets `E2R_DEFER_BACKGROUND_SPAWNS=1`. `FUN_0044dca4` returns at that option before its terrain-driven population work. [Task 04](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-04-recover-npc-spawn-query-inputs.md) already recovers bounded spawn query/range/placement inputs, but its fixtures intercept actor loading and activation. Its last full activation attempt reached a requester, so removing the launch flag alone is not an established repair.

The flag defers only automatic population. It does not establish why every interactive object is absent. Scripted scene children have separate loading/activation paths through `FUN_00452140`, `FUN_004523f8` and `FUN_004533ac`. Objects may also depend on dynamic geometry or script-owned state; determine the role from original resources and callers. Camera IDs must not be reused as scene-resource IDs: that assumption caused the recently repaired camera-transition failure.

## Next Bounded Slice

[Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md) coordinates population and interaction recovery with Task 04 and Step 08's scene-child task. First distinguish missing instances from instances omitted by the diagnostic presentation, trace a real resource's loading/activation, and recover one object or NPC end to end. Establish one source-consistent behavior/interaction before expanding to all missing categories. Keep the current usable F5 route while spawn-on diagnostics identify the first failing contract.

This continuation records the user's evidence, inspects the existing deferral and activation code, and updates priorities. It makes no runtime/launch changes or new runtime-test claims. The earlier steering-audit changes were staged by the user; their index contents remain unchanged. New documentation edits are unstaged, and no commits/tags were made.
