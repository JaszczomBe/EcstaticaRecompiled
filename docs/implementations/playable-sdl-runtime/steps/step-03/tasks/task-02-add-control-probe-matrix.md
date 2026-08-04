# Add Control Probe Matrix

Status: completed
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-08-04

## Goal

Add a compact bounded probe matrix for gameplay controls.

## Scope

1. Extend existing key-sequence probe support if needed.
2. Run a small set of directional/action/cancel keys.
3. Assert stable proof strings for each accepted path.

## Subtasks

1. Define the smallest useful key matrix.
2. Reuse the split intro/gameplay key injection path.
3. Add assertions for state changes that are already understood.
4. Keep unsupported keys recorded without making the run fail prematurely.
5. Update regression coverage only after the signals are stable.

## Out Of Scope

1. Full gameplay automation.
2. Menu localization/text fidelity.

## Implementation Notes

Avoid turning exploratory unknowns into hard regression failures. First record, then harden.

The intro blocker is now split: `Esc` visibly opens readable requester contents, while `Space` latches in game state but does not skip the intro action. Additional probes should avoid broad automation and focus on a small deterministic matrix that preserves this evidence while mapping the first stable gameplay controls.

Implemented matrix:

1. `up` - `last_key=0x26`, `_DAT_00479e78=0`, `move=[1,0,0,0,0,0,0,0,0]`.
2. `down` - `last_key=0x28`, `_DAT_00479e78=7`, `move=[0,0,0,0,0,0,0,1,0]`.
3. `left` - `last_key=0x25`, `_DAT_00479e78=3`, `move=[0,0,0,1,0,0,0,0,0]`.
4. `right` - `last_key=0x27`, `_DAT_00479e78=4`, `move=[0,0,0,0,1,0,0,0,0]`.

`scripts/run-e2-control-matrix.sh` runs each row through `--inject-key-sequence-gameplay-surfaces` with dummy SDL input and `E2R_STARTUP_LOGO_DELAY_MS=0`, first posting `space`, waiting for the gameplay-control gate, then posting the row key. Each row asserts key dispatch, movement vector, pending direction, requester clear, nonzero scene pointer, and nonblank surface `3`. ASan rows also reject sanitizer reports.

## Acceptance Criteria

1. At least three gameplay controls have bounded evidence.
2. The probe remains deterministic in debug and ASan or documents the difference.

## Verification

1. Debug control matrix probe.
2. ASan control matrix probe.
3. `scripts/run-e2-control-matrix.sh`
4. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: Four canonical arrow movement controls are now asserted in debug and ASan. Numpad is no longer treated as original Ecstatica II movement. The older long-delay regression wrapper still owns the separate ASan scene-current caveat after intro natural completion.

## Change Log

### 2026-07-28

1. Created task.

### 2026-07-31

1. Marked the task as blocked behind the intro control-state frontier to avoid broad probe work before the current blocker is understood.

### 2026-08-04

1. Activated the task after Task 01 restored readable intro `Esc` requester labels and split the remaining `Space` behavior to the action-dispatch/completion frontier.
2. Added `scripts/run-e2-control-matrix.sh`, then corrected it to the original Ecstatica II control layout after manual/original-game evidence showed numpad is not used for movement.
3. `up`, `down`, `left`, and `right` now pass with the expected movement vectors and `_DAT_00479e78` directions in debug and ASan. Added named probe aliases for `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; Task 03 keeps modifier/status/save/load behavior open until source-backed.
