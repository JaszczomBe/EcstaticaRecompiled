# Verify Frame Cadence

Status: planned
Parent Step: [Define Runtime Timing And Frame Pacing](../step-04-define-runtime-timing-and-frame-pacing.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Prove timing changes keep the runtime responsive and do not break gameplay or presentation proofs.

## Scope

1. Measure bounded presentation cadence.
2. Check input delivery after timing changes.
3. Record any remaining pacing drift or instability.

## Subtasks

1. Run SDL live-frame probe with cadence diagnostics if available.
2. Run the gameplay movement/control proof.
3. Run manual F5 long enough to observe obvious pacing problems.
4. Update the step with accepted timing behavior and remaining gaps.

## Out Of Scope

1. Pixel-perfect animation timing.
2. Audio sync.

## Implementation Notes

Frame cadence evidence can be approximate at this stage. It should catch hangs, runaway loops, and obvious input starvation.

## Acceptance Criteria

1. Presentation remains live.
2. Input remains responsive in probes.
3. Any timing caveat is documented.

## Verification

1. SDL live-frame probe.
2. Runtime regression script.
3. Manual SDL F5 check.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Final task for Step 4.

## Change Log

### 2026-07-28

1. Created task.
