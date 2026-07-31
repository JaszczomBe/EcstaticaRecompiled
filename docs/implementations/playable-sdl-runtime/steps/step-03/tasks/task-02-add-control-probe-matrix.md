# Add Control Probe Matrix

Status: planned
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-31

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

Do not expand the matrix before the intro `Esc`/`Space` blocker is classified. Current evidence already proves the host event path, so additional probes should target only action-dispatch/requester-presentation state until `Esc` visibly opens the menu and `Space` skips or the failure is split into a narrower runtime repair.

## Acceptance Criteria

1. At least three gameplay controls have bounded evidence.
2. The probe remains deterministic in debug and ASan or documents the difference.

## Verification

1. Debug control matrix probe.
2. ASan control matrix probe.
3. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Blocked behind intro `Esc`/`Space` classification.

## Change Log

### 2026-07-28

1. Created task.

### 2026-07-31

1. Marked the task as blocked behind the intro control-state frontier to avoid broad probe work before the current blocker is understood.
