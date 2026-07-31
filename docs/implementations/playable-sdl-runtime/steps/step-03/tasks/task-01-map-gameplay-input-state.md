# Map Gameplay Input State

Status: active
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-31

## Goal

Identify the gameplay input globals and queues worth asserting beyond the existing movement latch, starting with the intro `Esc`/`Space` paths that receive input but do not produce the expected behavior.

## Scope

1. Review current Win32 queue and legacy key-state bridges.
2. Identify movement, action, cancel/menu, and camera-related fields.
3. Record candidate proof strings.
4. Separate host input delivery from reconstructed game-state consumption.

## Subtasks

1. Search for existing `move=` probe output and source.
2. Trace keydown handling from SDL/Win32 into gameplay globals.
3. Record the proven intro `Esc`/`Space` globals and state transitions.
4. Identify the action-dispatch path that should consume `Space` during the intro.
5. Identify the requester/presentation path that should make `Esc` visible during the intro.
6. Pick a small key set for the later probe matrix.
7. Document any unknown globals that need Ghidra confirmation.

## Out Of Scope

1. Adding new input behavior.
2. Controller support.

## Implementation Notes

Prefer existing probe logging over new diagnostics until the missing state is proven. If more diagnostics are needed, keep them targeted to action completion, script dispatch, requester state, and front-surface selection; do not add broad per-frame logs.

Current mapped state:

1. SDL and host-window events are proven to reach the reconstructed window procedure.
2. `Space` during the horseback/credits intro sets `DAT_00636850=1` and `_DAT_00479e7a=1`.
3. `Esc` during the horseback/credits intro enters `FUN_00415d40`'s menu/requester branch and advances requester state.
4. The horseback/credits intro actor is actor `0`, with active action `0x937800`, sequence `0x7c8758`, and observed duration `495`.
5. The intro actor follows `FUN_0042a70c`'s dependency-action path rather than the normal `FUN_00427584` player-control path, so the known original `DAT_00636850` branch in the normal action-selection code is not sufficient to explain intro skipping.
6. On natural completion, action dispatch reaches script opcode `0x07`, activates scene `7`, and attempts to load missing child actor `3853`.

## Acceptance Criteria

1. Candidate globals are listed with source references.
2. The intro `Esc` and `Space` consumption paths are classified.
3. The next task has a bounded key matrix.

## Verification

1. Source inspection.
2. One existing movement probe.

## Review State

1. Planning state: discussed
2. Implementation state: in_progress
3. Notes: Active blocker is not SDL event delivery; it is intro `Esc`/`Space` consumption and presentation.

## Change Log

### 2026-07-28

1. Created task.

### 2026-07-31

1. Activated task for the intro input-state blocker.
2. Recorded that `Space` and `Esc` reach reconstructed game state, but expected skip/menu behavior is still absent.
3. Recorded that the next proof should focus on intro action dispatch and requester presentation, not more host input plumbing.
