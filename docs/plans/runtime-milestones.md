# Runtime Milestones

Status: planned
Priority: top
Owner: mixed
Last Updated: 2026-07-13

## Goal

Define the next meaningful runtime milestones for running the decompiled Ecstatica II engine on Linux, ordered by expected project gain and unlock value.

## Recommended Order

1. Recover the lost-register and calling-convention cluster around current startup/menu initialization crashes.
2. Load the first real resource file from `/home/rgrabowski/Games/Ecstatica2/`.
3. Create a visible Linux-hosted window or rendering surface.
4. Initialize enough graphics and audio stubs to reach menu or title logic.
5. Reach the main loop without crashing.

## Rationale

The highest-gain next move is not another defensive no-op. The reconstructed C still contains clusters of `extraout_*`, `in_EAX`, and function-pointer artifacts where Ghidra can recover original register and stack intent. Fixing that class should remove several nonsense crashes at once.

Resource loading is the next proof point because it validates the CD data path, filesystem assumptions, and early game data contracts.

A visible window and menu/title logic are later milestones because they need the startup/runtime path to stop corrupting state first.

## Success Criteria

1. Each milestone has a GDB or runtime observation proving it was reached.
2. Each crash frontier change is recorded in the project journal.
3. Each reconstructed C fix that must survive regeneration is mirrored in `GenerateRecon.js`.

## Change Log

### 2026-07-13

1. Created milestone plan.
