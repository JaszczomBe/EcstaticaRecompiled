# Verify SDL Backend Parity

Status: planned
Parent Step: [Add SDL Host Backend](../step-13-add-sdl-host-backend.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Prove the SDL backend preserves the stabilized runtime loop and document what remains different from the default backend.

## Scope

1. Run the default Step 11 regression script as a baseline.
2. Run the SDL-selected build/probe commands from earlier Step 13 tasks.
3. Compare control-ready, movement, surface, and diagnostic evidence.
4. Document any remaining SDL gaps and decide whether Step 13 can close.

## Out Of Scope

1. Fixing large runtime divergences discovered during parity checks.
2. Full rendering fidelity.
3. Packaging or installer work.

## Implementation Notes

If SDL exposes a reconstructed-runtime crash, record the crash as a runtime task instead of burying it in backend parity work.

## Acceptance Criteria

1. Default backend regression script still passes.
2. SDL backend reaches the documented parity target for the implemented SDL scope.
3. Remaining gaps are documented as follow-up tasks or later steps.

## Verification

1. `scripts/run-e2-runtime-regressions.sh`
2. SDL-specific regression command from Step 13.
3. `git diff --check`

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: This is the closing task for Step 13, not the place to add new SDL features.

## Change Log

### 2026-07-27

1. Created task.
