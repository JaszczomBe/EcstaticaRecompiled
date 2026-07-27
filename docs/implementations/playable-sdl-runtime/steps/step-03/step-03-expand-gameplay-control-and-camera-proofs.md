# Expand Gameplay Control And Camera Proofs

Status: planned
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Grow the current single movement-latch proof into a compact gameplay-control matrix covering movement, action, cancel/menu, and camera-adjacent state.

## Why This Step Exists

The reconstructed runtime proves that `num8` can latch movement after Start Game. A playable runtime needs confidence that multiple controls survive the Win32 queue, legacy key state, and gameplay-state transitions.

## Scope

1. Map current gameplay input globals and key queues.
2. Add bounded probes for several control paths.
3. Record camera/control state that changes in response to input.

## Out Of Scope

1. Full key rebinding.
2. Controller support.
3. Combat or inventory systems.

## Usage Budget

Keep this to a small input matrix. Split when a single key uncovers a new parser or actor crash family.

## Temporary Sacrifices

1. Sacrifice: Use scripted probes before broad manual play.
2. Why accepted now: Scripted keys give repeatable proof while runtime stability is still moving.
3. Removal trigger: Interactive play is stable enough for longer manual sessions.

## Tasks

1. [Map Gameplay Input State](tasks/task-01-map-gameplay-input-state.md) - planned.
2. [Add Control Probe Matrix](tasks/task-02-add-control-probe-matrix.md) - planned.
3. [Verify Camera And Action Frontiers](tasks/task-03-verify-camera-and-action-frontiers.md) - planned.

## Acceptance Criteria

1. Multiple movement/action keys reach gameplay state.
2. Probes record the relevant state deltas.
3. New crashes are classified as separate runtime frontiers.

## Verification

1. Gameplay key-sequence probes.
2. Default runtime regression script.
3. SDL F5 smoke check when controls affect presentation.

## Notes

Start from the known `move=[1,0,0,0,0,0,0,0,0]` proof and extend cautiously.

## Change Log

### 2026-07-28

1. Created step.
