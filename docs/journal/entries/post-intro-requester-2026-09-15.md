# 2026-09-15 — Post-intro action-error requester

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Area: `FUN_00451880`, `FUN_0043cbf0`, mapped requester records and hosted OK routing.

Symptom: the supplied F5 recording (`Screencast From 2026-09-15 19-22-06.mp4`, 35 seconds) shows Space reaching the pedestal camera, the projected-cue status replacing the old grid, and later arrows/Escape producing no visible response. It confirms bounded default-route survival and cue replacement, not living actors or playable controls.

## Diagnosis and original evidence

The default route completes `Start_sc` at **1102/1102**, then requests action **384, `dav:heropick`**. Its archive offset is -1 because action indexing remains disabled. The apparent freeze is an invisible blocking error requester, ID **0x2e**. `_DAT_00643650 == 0` does not mean no modal is active: this gameplay state and the requester ID are separate fields.

The Escape breakpoint stack is `E2R_WndProc → FUN_0041ba7c → FUN_0043b384 → FUN_0043cbf0 → FUN_0043cbb4 → FUN_00451880 → FUN_00427584 → FUN_0042a70c → FUN_00426df8`. The host pump continues while game updates wait inside the modal. Evidence: `/tmp/e2-escape-before.log`. The initial stale-requester hypothesis was rejected; no WndProc Escape bypass was added.

Original `0x4518a4..0x4518f3` formats the name/id and supplies two strings to `0x43cbb4`, which makes a live `[title, detail, NULL]` list. Original strings at `0x4754c0..0x475510` distinguish load failure from a missing directory name. Original `0x43cc3d..0x43cc4e` copies at most 50 bytes per 51-byte line, then passes requester **0x47a630**, not a line count. The static record at `0x47a630` and line/item initialization in `0x43fc20` establish its layout. Original `0x43c5c6..0x43c5d0` / `0x43c667` accepts the message OK action.

## Change

- Recover bounded action-error formatting with the existing packed-name lookup and a live local message list. Other unrecovered one-argument message-wrapper callers remain unchanged.
- Initialize the mapped message record, 18 static line items and OK item; copy the actual strings, update mapped height and pass the real requester pointer. Generated host globals alone did not populate these records.
- Allow mouse routing for message ID 0x2e even when gameplay state is zero; dispatch its existing OK callback and return from the modal.
- Mirror every reconstruction change in `GenerateRecon.js` and add `scripts/check-e2-postintro-requester.py` for the complete bounded interaction.

## Validation

All four X11/SDL Debug and ASan builds pass; scratch regeneration matches all four artifacts. The isolated arrow matrix passes **8/8**. The revised runtime wrapper retains positive canonical-Up movement-latch checks in Debug and early ASan, plus a long-delay ASan missing-action/modal check. Its former long-delay movement assertion measured an invisible modal and was invalid after restoring that modal. No actor-motion claim follows from these input-state checks.

```sh
cmake --build --preset linux-clang32-debug
cmake --build --preset linux-clang32-debug-asan
cmake --build --preset linux-clang32-sdl-debug
cmake --build --preset linux-clang32-sdl-debug-asan
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_CONTROL_MATRIX_TMP=/tmp/e2-message-matrix scripts/run-e2-control-matrix.sh
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_REGRESSION_TMP=/tmp/e2-message-final-regressions scripts/run-e2-runtime-regressions.sh
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl/e2recomp --output /tmp/e2-message-final-debug
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl-asan/e2recomp --output /tmp/e2-message-final-asan
```

The new SDL Debug/ASan checks capture the real presentation, click the actual OK bounds through WndProc, reach another game update, and feed Escape to verify main-menu entry (ID 0x28, state 5). They do not validate subsequent menu rendering/navigation. GDB needs ptrace permission; the script disables LeakSanitizer only for this ptrace run, leaving AddressSanitizer active. The ordinary regression wrapper uses ASan normally.

The inspected SDL window capture shows the action error over the pedestal. Selected game pixels hash `c2a56a11`; cue-enabled SDL present/window hashes are `fd124785` / `ef9e0785`. The hosted fallback font still substitutes question marks for unsupported punctuation and packs the lines tightly; exact strings are verified in the mapped line buffers. These are presentation limitations, not missing action-name inputs.

## Result and next boundary

**OK resumes game updates at camera 87**, exposing the unresolved rooftop transition. Joe/enemy placement and playable movement remain unproven. The error can recur on another missing-action request; it is not suppressed. Action indexing stays opt-in because its SDL route reaches the existing `FUN_00431a7c` polygon-input crash. Continue [Task 02 geometry inputs](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-02-recover-joe-geometry-and-rendering.md), then Tasks 05/01 placement/actions and Task 03 children.

[Task 09](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-09-recover-post-intro-action-error-requester.md) is implemented and automatically verified; manual dialog/OK behavior was subsequently confirmed on 2026-09-21 (below); manual Escape remains unconfirmed. The earlier video predates this repair.

Regression risk: shared message presentation now executes for recovered callers that previously stalled invisibly. Other message callers, keyboard-only modal interaction, typography and subsequent error/scene behavior remain incompletely recovered. No actor positions or scene selections are forced by this repair.

## Manual follow-up — 2026-09-21

The supplied screenshots show action error 384 over the pedestal (camera 175, one actor behind camera) and over the rooftops (camera 87, one actor offscreen). The user reports that clicking OK causes this transition, with no hero visible. The accompanying Shift/focus log reports scene pointer `0x67d0ac`, consistent with camera 87. This confirms error presentation and progress after OK, not sustained gameplay or manual Escape handling. The same error remains visible after the transition; a new modal invocation versus retained dialog pixels needs runtime tracing before claiming either explanation.

The later [polygon-input repair](polygon-inputs-2026-09-21.md) passes the old reference-pointer crash but reaches another lighting/matrix-input failure. The action gate therefore stays off; these screenshots do not change the remaining actor/scene acceptance criteria.
