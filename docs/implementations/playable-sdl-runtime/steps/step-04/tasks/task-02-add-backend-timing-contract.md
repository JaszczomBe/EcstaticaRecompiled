# Add Backend Timing Contract

Status: planned
Parent Step: [Define Runtime Timing And Frame Pacing](../step-04-define-runtime-timing-and-frame-pacing.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Add the smallest host-backend timing API needed by mapped compatibility callers.

## Scope

1. Define timing API shape in the host backend boundary.
2. Implement X11/default and SDL behavior.
3. Keep reconstructed C callers unchanged.

## Subtasks

1. Add only the timing function proven by Step 4 task 1.
2. Implement no-op or host-backed behavior per backend.
3. Preserve current presentation throttle unless replaced deliberately.
4. Build default and SDL targets.
5. Document layer ownership.

## Out Of Scope

1. Frame interpolation.
2. Audio synchronization.
3. Multi-platform release policy.

## Implementation Notes

Backend timing should be easy to swap. Avoid leaking SDL types into compatibility headers.

## Acceptance Criteria

1. Timing API has a concrete caller.
2. Default and SDL builds compile.
3. Existing gameplay probes still pass.

## Verification

1. Default build.
2. SDL build.
3. Runtime regression script.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Activated only after timing call sites are mapped.

## Change Log

### 2026-07-28

1. Created task.
