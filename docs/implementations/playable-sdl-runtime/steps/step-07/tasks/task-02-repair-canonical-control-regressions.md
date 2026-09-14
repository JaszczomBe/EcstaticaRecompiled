# Repair Canonical-Control Regression Wrapper

Status: completed
Parent Step: [Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Align the legacy wrapper with the recovered arrow-key input contract and prove both debug and ASan results.

## Scope

1. Replace both `space,num8` wrapper sequences with canonical `space,up`.
2. Retain requester, movement, surface, scene, sanitizer, and diagnostic assertions; explicitly verify VK_UP dispatch.
3. Re-run the wrapper, arrow matrix, and default SDL visibility packet.

## Out Of Scope

1. Changing numpad gameplay behavior to satisfy an obsolete test.
2. Actor/action fixes or full visible-gameplay automation.

## Implementation Notes

Task 01 is complete. Both wrapper sequences use `space,up`, assert `last_key=0x26`, and retain quiet-mode/sanitizer rejection. After Tasks 03–06, the full wrapper passes debug and ASan. All 8 arrow rows and the default SDL scene-175 packet pass. The crash-free manual F5 report and subsequent screenshot/log confirm agreement with the static scene-175 packet, completing the remaining baseline check.

`e2r_wait_for_gameplay_frame` accepts StartGame entry, a mode flag, a scene pointer, and optionally requester clear. It does not prove `Start_sc` completed, geometry rendered, or the actor moved. Keep this wrapper's contract explicitly limited to state/surface regression. Preserve bounded execution; capture a new failure rather than weakening checks or assuming the arrow substitution guarantees success.

## Acceptance Criteria

1. Both debug and ASan execute and pass the corrected wrapper.
2. VK_UP delivery and its movement vector are asserted; sanitizer rejection remains active.
3. All 8 matrix rows pass and the default SDL scene-175 packet preserves its recorded static baseline.
4. Parent implementation and journal record actual results, including any new blocker.

## Verification

From the repository root, after builds are current:

```sh
E2R_SKIP_BUILD=1 E2R_REGRESSION_TMP=/tmp/e2-baseline-regression timeout 300 scripts/run-e2-runtime-regressions.sh
E2R_SKIP_BUILD=1 E2R_CONTROL_MATRIX_TMP=/tmp/e2-baseline-controls timeout 300 scripts/run-e2-control-matrix.sh
SDL_VIDEODRIVER=dummy timeout 140 build/linux-clang32-sdl-debug/e2recomp --auto-scene175-visibility /tmp/e2-baseline-scene175 120 7000
git diff --check
```

Inspect state and presentation dumps, not only exit status. Manual F5 is required if a runtime behavior change becomes necessary; a key-sequence script correction alone does not revalidate manual play.

## Review State

1. Planning state: agreed
2. Implementation state: completed
3. Notes: All automated acceptance checks pass; no assertions were relaxed. Manual SDL F5 survival and final-scene agreement are confirmed.

## Manual Follow-Up — 2026-09-14

The user’s 2026-09-14 screenshot matches the automated scene-175 static capture (red sky, central horned skull, stone platforms and straw); the accompanying input log reports `scene=0x67da4c`, the scene-175 slot address. Together with the earlier crash-free manual F5 report, this resolves the pending final-image comparison and completes the Step 07 baseline check. It does not establish original scene-selection fidelity or visible living actors; those remain Step 08 work. The missing cue panel was traced to the usual SDL launch leaving `E2R_ACTOR_CUES` unset; both SDL launch configurations now enable it after restarting the session.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.

2. Replaced both numpad sequences, asserted VK_UP, retained rejection gates, and ran the wrapper/matrix/SDL checks. Debug passes; ASan natural-completion crash is split into Task 03.

3. Recorded the user’s manual screenshot/scene-pointer evidence, completed the Step 07 static-baseline check, and enabled cues in the usual SDL launch.
