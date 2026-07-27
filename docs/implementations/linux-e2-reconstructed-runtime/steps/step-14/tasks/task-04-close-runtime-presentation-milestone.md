# Close Runtime Presentation Milestone

Status: completed
Parent Step: [Present Live Runtime Frames And SDL F5 Route](../step-14-present-live-runtime-frames.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-28

## Goal

Close the reconstructed-runtime presentation milestone with default and SDL verification evidence, then hand future work to a new post-reconstruction implementation.

## Scope

1. Rerun default debug/ASan runtime regressions.
2. Rerun SDL probes needed by Step 14.
3. Confirm raw F5-equivalent routes still survive the known crash window.
4. Update Step 14 and parent implementation state.
5. Point the next horizon at a separate implementation instead of extending this reconstruction rollout indefinitely.

## Subtasks

1. Build the default debug target.
2. Build the ASan target.
3. Build the SDL 32-bit target.
4. Run `scripts/run-e2-runtime-regressions.sh` and check that default logs stay quiet.
5. Run SDL synthetic presentation probes for the backend-owned presentation baseline.
6. Run the SDL live-frame gameplay probe with `E2R_PRESENT_DIAG=1`.
7. Run the raw F5-equivalent default debug route long enough to catch allocator regressions.
8. Run the raw SDL launch-equivalent route long enough to catch allocator regressions.
9. Update Step 14 and parent implementation evidence with exact commands, hashes, and remaining sacrifices.
10. Remove the standalone Step 15 docs by merging their content into Step 14.
11. Run `git diff --check`.

## Out Of Scope

1. New rendering features after the first live-frame proof.
2. Audio implementation.
3. Packaging work.
4. Long-play or input-fidelity repair.

## Implementation Notes

This task intentionally gathers evidence across both backend paths because Step 14 touches shared pump behavior. The default X11/no-presentation route remains the baseline for runtime repair, while SDL proves live pixels can leave the recovered framebuffers. A failure in either path means the presentation pump changed runtime semantics and should be fixed before broadening rendering fidelity work.

The reconstructed-runtime implementation has reached its original goal: original data loads, the main loop survives, input reaches gameplay, recovered frames can be inspected and presented, SDL is vendored and selectable, and an SDL F5 route exists. Work after this point should move into a new implementation focused on making the runtime pleasant, accurate, and repeatable rather than merely reconstructed enough to run.

## Acceptance Criteria

1. All Step 14 verification commands pass.
2. Remaining rendering gaps are documented as follow-up scope.
3. `git diff --check` passes.
4. The parent implementation records the merged Step 14 as completed.
5. The next rendering frontier is described in terms of DirectDraw/page/palette fidelity, not vague "make graphics better" work.
6. The next major horizon is represented by a new implementation document.

## Verification

1. `scripts/run-e2-runtime-regressions.sh`
2. SDL Step 14 probe commands.
3. `jq empty .vscode/launch.json .vscode/tasks.json CMakePresets.json`
4. `git diff --check`

## Review State

1. Planning state: agreed
2. Implementation state: accepted
3. Notes: Default regressions, SDL probes, SDL live-frame proof, raw F5-equivalent survival, and new-horizon documentation are recorded.

## Evidence

1. Debug, ASan, SDL 64-bit, and SDL 32-bit builds passed.
2. `scripts/run-e2-runtime-regressions.sh` passed.
3. SDL synthetic presentation probes passed on 64-bit and 32-bit builds with hash `a92a7045`.
4. SDL live-frame proof passed with real recovered surface hashes `6e39f5ea` and `3615add9`.
5. Raw F5-equivalent `build/linux-clang32-debug/e2recomp --run-recon` survived a 25-second timeout without allocator abort.
6. Raw SDL launch-equivalent `build/linux-clang32-sdl-debug/e2recomp --run-recon` survived beyond the prior allocator-crash window.
7. `git diff --check` passed.

## Change Log

### 2026-07-28

1. Created task by merging the former Step 14 closeout and Step 15 documentation closeout.
