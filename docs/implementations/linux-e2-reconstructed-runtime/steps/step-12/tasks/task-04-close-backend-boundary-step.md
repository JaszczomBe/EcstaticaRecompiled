# Close Backend Boundary Step

Status: planned
Parent Step: [Define Replaceable Host Backend Boundary](../step-12-define-replaceable-host-backend-boundary.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Close Step 12 only after the backend boundary is documented, the first seam is verified, and Step 13 has a clean SDL handoff.

## Scope

1. Confirm all Step 12 task acceptance criteria.
2. Run the full debug/ASan regression script.
3. Update the parent implementation to mark Step 12 complete and Step 13 active when ready.
4. Add any final notes needed to start SDL work without re-reading the whole Step 12 history.

## Out Of Scope

1. SDL implementation.
2. New backend API expansion not already documented in task 03.
3. Runtime crash recovery unrelated to the backend boundary.

## Implementation Notes

This task should be a closure and handoff pass. If new code is needed, create a separate task first.

## Acceptance Criteria

1. Step 12 is marked completed.
2. Step 13 is linked and ready to start.
3. `scripts/run-e2-runtime-regressions.sh` passes after the final docs/code state.

## Verification

1. `scripts/run-e2-runtime-regressions.sh`
2. `git diff --check`

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Use this to prevent Step 12 from turning into the SDL implementation step.

## Change Log

### 2026-07-27

1. Created task.
