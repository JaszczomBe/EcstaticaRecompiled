# Map DirectSound Startup Calls

Status: planned
Parent Step: [Begin DirectSound Compatibility](../step-05-begin-directsound-compatibility.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Identify the DirectSound calls reached during startup, menu, and first gameplay.

## Scope

1. Inspect existing DirectSound stubs.
2. Trace startup music/sound call paths.
3. Record buffer and format assumptions.

## Subtasks

1. Search DirectSound compatibility symbols.
2. Run bounded startup/gameplay probes with opt-in audio diagnostics if needed.
3. Identify the first unsupported buffer operation.
4. Document whether silent success or real buffering is the next safe move.

## Out Of Scope

1. SDL audio implementation.
2. Format conversion.

## Implementation Notes

Use logs sparingly. Audio startup has already been bypassed in earlier runtime work, so this task should clarify what is still hidden.

## Acceptance Criteria

1. DirectSound startup calls are listed.
2. First unsupported operation is named.

## Verification

1. Source inspection.
2. Bounded startup or gameplay probe.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: First audio task.

## Change Log

### 2026-07-28

1. Created task.
