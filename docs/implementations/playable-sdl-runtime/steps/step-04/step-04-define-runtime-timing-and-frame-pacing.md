# Define Runtime Timing And Frame Pacing

Status: planned
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Identify runtime timing ownership and add frame-pacing behavior only where compatibility or backend contracts require it.

## Why This Step Exists

Live presentation currently throttles presentation attempts, but that is not the same as recovering the game's timing model. A playable runtime needs predictable loop pacing without hiding original timing semantics.

## Scope

1. Map timing-related Win32 calls and reconstructed delay/state paths.
2. Define backend timing APIs only when a caller needs them.
3. Verify that frame pacing does not change input or gameplay proofs.

## Out Of Scope

1. Audio synchronization.
2. Full original timing accuracy.
3. Removing temporary presentation throttling before replacement behavior is proven.

## Usage Budget

Keep timing work to one ownership decision and one bounded verification path per task.

## Temporary Sacrifices

1. Sacrifice: Keep presentation throttle separate from game timing.
2. Why accepted now: It protects the backend from excessive pump calls without pretending to emulate original timing.
3. Removal trigger: Recovered timing/frame pacing makes the throttle unnecessary or moves it to a better owner.

## Tasks

1. [Map Timing Call Sites](tasks/task-01-map-timing-call-sites.md) - planned.
2. [Add Backend Timing Contract](tasks/task-02-add-backend-timing-contract.md) - planned.
3. [Verify Frame Cadence](tasks/task-03-verify-frame-cadence.md) - planned.

## Acceptance Criteria

1. Timing ownership is documented by layer.
2. Any new timing API is backed by a real caller.
3. Gameplay/input/presentation probes remain stable.

## Verification

1. Runtime regression script.
2. SDL live-frame probe.
3. Manual F5 smoke check if pacing changes.

## Notes

Do not use SDL delay calls from reconstructed code. Timing belongs in compatibility or backend layers.

## Change Log

### 2026-07-28

1. Created step.
