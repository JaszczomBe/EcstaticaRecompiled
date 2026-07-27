# Map Timing Call Sites

Status: planned
Parent Step: [Define Runtime Timing And Frame Pacing](../step-04-define-runtime-timing-and-frame-pacing.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Find the runtime and compatibility call sites that currently influence loop pacing.

## Scope

1. Inspect Win32 time/timer shims.
2. Inspect presentation throttle behavior.
3. Identify reconstructed logic that depends on elapsed time.

## Subtasks

1. Search for timer, tick, sleep, and delay helpers.
2. Map which calls are compatibility semantics and which are backend host services.
3. Run one baseline probe with timing diagnostics only if needed.
4. Record the minimum timing contract needed by the next task.

## Out Of Scope

1. Implementing timing changes.
2. Audio sync.

## Implementation Notes

This is a mapping task. Keep code edits out unless a diagnostic is essential and opt-in.

## Acceptance Criteria

1. Timing call sites are listed with owner layer.
2. The next task has a specific contract to implement or an explicit no-op decision.

## Verification

1. Source inspection.
2. Optional bounded runtime probe.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: First timing task.

## Change Log

### 2026-07-28

1. Created task.
