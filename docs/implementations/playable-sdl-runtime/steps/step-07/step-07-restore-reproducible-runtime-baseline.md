# Restore Reproducible Runtime Baseline

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: completed
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Make generation and regression commands preserve and verify the runtime currently under investigation.

## Why This Step Exists

The audit found that regeneration discards committed diagnostics and the old wrapper injects numpad movement after the runtime switched to canonical arrows. These failures obscure the next actor/action repair. See the [audit](../../../../journal/entries/runtime-audit-2026-09-14.md).

## Scope

1. Preserve actor/action/rep diagnostics in `GenerateRecon.js`.
2. Repair the wrapper's input contract and verify debug/ASan outcomes.
3. Recover the narrow natural-intro action-candidate failure exposed by the corrected ASan probe.
4. Update current verification results after the code repairs.

## Out Of Scope

1. Broad actor rendering/action semantics changes (Step 08); Task 03 is limited to the natural-intro candidate handoff blocking this baseline.
2. Relaxing evidence checks to turn a failed probe green.
3. Full developer bootstrap/packaging (Step 06).

## Usage Budget

One focused source repair per task. Split any runtime failure uncovered by corrected probes from this harness repair.

## Temporary Sacrifices

1. The full canonical-Up wrapper now passes debug and ASan after Tasks 03–06. Task 02’s manual SDL F5 survival and final-image comparison are confirmed.
2. The long-delay natural route ends in scene 87; the separate skip route preserves the static scene-175 packet. Neither route establishes visible actor motion.
3. Neither check establishes visible gameplay; retain that limit after the wrapper is green.

## Tasks

1. [Preserve Generator Diagnostics](tasks/task-01-preserve-generator-diagnostics.md) — completed; all four generated artifacts match.
2. [Repair Canonical-Control Regression Wrapper](tasks/task-02-repair-canonical-control-regressions.md) — completed; automated checks pass and the manual screenshot/log matches scene 175.
3. [Recover Natural Intro Action Handoff](tasks/task-03-recover-natural-intro-action-handoff.md) — completed; recursive actor repair and long-delay acceptance pass.
4. [Recover Default-Action Actor Context](tasks/task-04-recover-default-action-actor-context.md) — completed; scoped actor context supplied and restored at three caller sites.
5. [Recover Natural Action-Advance Inputs](tasks/task-05-recover-natural-action-advance-inputs.md) — completed; explicit inputs restore the original empty-action return.
6. [Recover Natural Motion Query](tasks/task-06-recover-natural-motion-query.md) — completed; source-backed ownership/table repair makes the full wrapper pass.

This baseline step is complete. Continue Step 08 scene-pose and actor recovery.

## Acceptance Criteria

1. Scratch regeneration matches all four generator outputs with no unexplained drift.
2. The corrected wrapper passes debug and ASan with canonical controls and still rejects missing evidence/sanitizer reports.
3. The existing 8-row matrix and scene-175 packet remain stable; actual results are recorded with their limits.

## Verification

Follow each task's commands and record the result in the journal. Step 08 starts after this baseline is established. If a corrected wrapper reveals a new runtime crash, record and split it; do not mark this step complete while its acceptance checks fail.

## Notes

The 2026-09-14 continuation passes generator parity, all three builds, the full debug/ASan wrapper, all 8 arrow rows, and the static scene-175 packet. Task 06 repaired actor/query ownership, the optional output pointer, contiguous candidate storage, and fixed-address byte-table access. Manual SDL F5 survives the pedestal intro; the supplied screenshot and scene-pointer log now confirm agreement with the static scene-175 capture. Step 07 is complete within its baseline scope.

## Manual Follow-Up — 2026-09-14

The user’s 2026-09-14 screenshot matches the automated scene-175 static capture (red sky, central horned skull, stone platforms and straw); the accompanying input log reports `scene=0x67da4c`, the scene-175 slot address. Together with the earlier crash-free manual F5 report, this resolves the pending final-image comparison and completes the Step 07 baseline check. It does not establish original scene-selection fidelity or visible living actors; those remain Step 08 work. The missing cue panel was traced to the usual SDL launch leaving `E2R_ACTOR_CUES` unset; both SDL launch configurations now enable it after restarting the session.

## Change Log

### 2026-09-14

1. Created as the prerequisite to scene-175 actor recovery, retaining existing step numbers and links.

2. Completed Task 01; implemented Task 02 script correction and split its newly exposed ASan failure into Task 03. Step 07 remains open.

3. Recorded the user’s manual screenshot/scene-pointer evidence, completed the Step 07 static-baseline check, and enabled cues in the usual SDL launch.
