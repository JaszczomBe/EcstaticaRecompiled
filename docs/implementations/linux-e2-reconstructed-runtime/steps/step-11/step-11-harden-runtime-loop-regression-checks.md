# Harden Runtime Loop Regression Checks

Status: completed
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Turn the Step 10 control-ready proof into a repeatable regression check that future runtime, generator, and compatibility changes can run before chasing new behavior.

## Why This Step Exists

Step 10 reached the first controllable scene in both debug and ASan builds, but the path is long and has many recovered calling-convention, stream, input, and surface-copy repairs. Step 11 exists to keep that proof cheap to rerun and hard to accidentally regress while temporary diagnostics are trimmed.

## Scope

1. Add a repository-local command that validates generator syntax, builds debug/ASan targets, and runs the known split gameplay probe.
2. Assert concrete runtime evidence: control-ready gate, requester state clear, delayed movement latch, nonblank surface, and no ASan report.
3. Keep outputs in `/tmp` and document where logs/surface dumps are written.
4. Gate or trim temporary diagnostics only after the regression command protects the Step 10 proof.

## Out Of Scope

1. Full gameplay automation.
2. Pixel-perfect rendering assertions beyond the current nonblank surface proof.
3. Replacing the Linux/X11 host backend.
4. Fully recovering every hidden-register surface-copy call site.

## Current Evidence

The first Step 11 slice added:

```text
scripts/run-e2-runtime-regressions.sh
```

The script runs `node --check`, builds `linux-clang32-debug` and `build/linux-clang32-asan`, then launches the split gameplay probe in both builds:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step11-regression-debug space,num8 6 10000 180 1
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step11-regression-asan space,num8 30 10000 60 1
```

It fails if the logs do not show `gameplay-control wait satisfied`, `_DAT_00643650=0`, `move=[1,0,0,0,0,0,0,0,0]`, and `surface 3 nonblank=1`, or if the ASan log contains an AddressSanitizer report. By default it also rejects opt-in runtime diagnostic trace lines so temporary probes cannot creep back into normal regression output unnoticed.

Initial verification passed:

```text
scripts/run-e2-runtime-regressions.sh

Runtime regressions passed.
Debug log: /tmp/e2-step11-regression-debug.log
ASan log: /tmp/e2-step11-regression-asan.log
```

The successful logs include `_DAT_00643650=0`, `_DAT_0073cc3c=0x681d04`, `move=[1,0,0,0,0,0,0,0,0]`, and `surface 3 nonblank=1 hash=6e39f5ea` in both debug and ASan.

The second Step 11 slice gates the temporary frame, scene-pointer, actor-loop, actor-update, requester-state, start-game, actor-load, and current-actor pointer-shape diagnostics behind `E2R_RUNTIME_DIAG=1`. The regression script still keeps the final probe summaries visible by default, so the proof logs remain short while preserving control, movement, and surface evidence.

While validating that cleanup, a debug probe exposed an older draw helper hazard in `FUN_0041ad54`: `FUN_00418a04` can return a low nonzero base such as `0x16` for a stale surface, and the generated rectangle fill accepted it as writable. The generator now rejects invalid surfaces, low/implausible bases, undersized pitches, oversized dimensions, and bad write spans before writing pixels.

Fresh verification passed after the diagnostic gate, draw guard, and scripted quiet-log assertions:

```text
scripts/run-e2-runtime-regressions.sh

Runtime regressions passed.
Debug log: /tmp/e2-step11-regression-debug.log
ASan log: /tmp/e2-step11-regression-asan.log
```

The default debug/ASan logs contain no `scene pointer write:`, `frame stage:`, `actor loop:`, `actor update:`, `start-game stage:`, requester-state, menu-request, or current-pointer-shape trace lines unless `E2R_RUNTIME_DIAG=1` is set.

## Acceptance Criteria

1. The regression script exits `0` after running both debug and ASan control-ready probes.
2. The script reports log paths for failed and successful runs.
3. Step 10 remains documented as completed, with this step owning regression hardening and diagnostic cleanup.
4. Temporary diagnostics are either gated behind opt-in environment variables or explicitly kept with a removal trigger.

## Verification

1. `scripts/run-e2-runtime-regressions.sh`
2. `git diff --check`

## Notes

Set `E2R_SKIP_BUILD=1` to rerun probes against already-built binaries. Set `E2R_REGRESSION_TMP=/tmp/some-prefix` to change the output prefix. Set `E2R_RUNTIME_DIAG=1` to restore temporary runtime frame, scene, actor, requester, and current-pointer traces, and `E2R_FAN_DIAG=1` to restore the separate FAN parser traces.

The runtime probes must run outside the sandbox in this Codex environment; sandboxed game probes exit with code `159`.

## Change Log

### 2026-07-27

1. Opened Step 11 after Step 10 proved control-ready movement in both debug and ASan.
2. Added `scripts/run-e2-runtime-regressions.sh` to validate generator syntax, build both targets, run split gameplay probes, and assert the key proof strings.
3. Verified the new script once; it passed and wrote debug/ASan logs under `/tmp/e2-step11-regression-*.log`.
4. Gated temporary runtime diagnostics behind `E2R_RUNTIME_DIAG=1`, leaving final probe summaries visible by default.
5. Hardened generated `FUN_0041ad54` against invalid surface bases/spans after the regression harness exposed a debug draw crash with base `0x16`.
6. Reverified `scripts/run-e2-runtime-regressions.sh`; debug and ASan both pass with quiet default logs and nonblank surface 3 hash `6e39f5ea`.
7. Extended the regression script to reject opt-in runtime trace families by default, while allowing them when `E2R_RUNTIME_DIAG=1` is set.
8. Closed Step 11 after all acceptance criteria were covered by the regression script and documentation.
