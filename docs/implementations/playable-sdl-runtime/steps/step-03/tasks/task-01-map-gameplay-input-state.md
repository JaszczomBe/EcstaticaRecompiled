# Map Gameplay Input State

Status: planned
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Identify the gameplay input globals and queues worth asserting beyond the existing movement latch.

## Scope

1. Review current Win32 queue and legacy key-state bridges.
2. Identify movement, action, cancel/menu, and camera-related fields.
3. Record candidate proof strings.

## Subtasks

1. Search for existing `move=` probe output and source.
2. Trace keydown handling from SDL/Win32 into gameplay globals.
3. Pick a small key set for the next probe matrix.
4. Document any unknown globals that need Ghidra confirmation.

## Out Of Scope

1. Adding new input behavior.
2. Controller support.

## Implementation Notes

Prefer existing probe logging over new diagnostics until the missing state is proven.

## Acceptance Criteria

1. Candidate globals are listed with source references.
2. The next task has a bounded key matrix.

## Verification

1. Source inspection.
2. One existing movement probe.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: First control-expansion task.

## Change Log

### 2026-07-28

1. Created task.
