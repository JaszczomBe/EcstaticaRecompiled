# Recover Scene 175 Actors

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-09-15

## Goal

Render and update the living player and scene-backed children after `Start_sc` completes in scene 175.

## Why This Step Exists

Step 03's input investigation exposed independent action-context, geometry, and resource-instantiation failures. The static framebuffer and SDL surfaces agree, so host presentation is already sufficient to observe these repairs. This work now has its own acceptance criteria and follows the automated baseline in [Step 07](../step-07/step-07-restore-reproducible-runtime-baseline.md).

## Scope

1. Recover action 384's actor/action-slot context and advancement.
2. Initialize Joe's rep/model geometry and prove visible movement.
3. Recover scene-backed child instantiation and drawing.

## Out Of Scope

1. Broad combat/inventory, requester polish, or full animated intro fidelity.
2. Timing/audio backend implementation or 64-bit migration.
3. Speculative SDL/page-selection changes to expose absent game pixels.

## Usage Budget

One task per failure family. Recover only the helper signatures/data layouts needed for that task. Split a newly exposed independent crash before broadening the repair.

## Temporary Sacrifices

1. Keep `E2R_ACTION_INDEX_PROBE=1` opt-in while the action path is unstable.
2. Keep the narrow scene-175 handoff guard during actor recovery; validate its removal/replacement through original scene-selection evidence later.
3. Promote action indexing to default only after all tasks and relevant regressions pass; record any reason it remains gated.

## Tasks

1. [Recover Action Context](tasks/task-01-recover-action-context.md) — active; actor/slot repair implemented, gated validation remains open.
2. [Recover Missing-Scene Message Inputs](tasks/task-04-recover-missing-scene-message-inputs.md) — completed; missing-scene string inputs repaired, scene 40 identified.
3. [Recover Post-Intro Scene Selection](tasks/task-05-recover-post-intro-scene-selection.md) — active; corrupt events traced to aliased keyframe allocation; corrected scan gated.
4. [Recover Scene-Activation Pose Inputs](tasks/task-06-recover-scene-activation-pose-inputs.md) — active; actor/state and output destinations implemented, full-route/manual validation incomplete.
5. [Recover Joe Geometry And Rendering](tasks/task-02-recover-joe-geometry-and-rendering.md) — active; node matrix destinations repaired; polygon-input crash is next.
6. [Activate Scene-Backed Children](tasks/task-03-activate-scene-backed-children.md) — planned; validate after the player path is stable.
7. [Project Actor Cues Into The Scene](tasks/task-07-project-actor-cues-into-scene.md) — completed for cue projection; video confirms grid replacement, default Joe remains behind camera.
8. [Recover Packed Event Metadata](tasks/task-08-recover-packed-event-metadata.md) — completed for the table; full action route remains gated.

9. [Recover Post-Intro Action Error Requester](tasks/task-09-recover-post-intro-action-error-requester.md) — implemented and automatically verified; new manual F5 check pending.

Task numbers remain stable. Resume **02 geometry inputs → 05/01 placement and action validation → 03 child activation**, with Task 06 full-route and Task 09 manual checks pending. Pose inputs, trigonometry/projection, two corrupting matrix destinations and packed event metadata are recovered. Gated SDL now crashes in `FUN_00431a7c`; gated headless ASan times out in camera 1073. Action indexing and pool/event-metadata repairs remain opt-in; the default route now exposes the action-384 error after the intro; clicking OK resumes updates at camera 87, whose selection remains unresolved. Camera 175 must not be treated as script scene-resource 175.

## Acceptance Criteria

1. Action 384 loads/advances without losing actor ownership or crashing through hidden registers.
2. Living Joe is drawn into the selected framebuffer, and an arrow input causes source-consistent position and rendered-output changes.
3. Expected scene children instantiate and render according to original resource semantics; any legitimate absence has source evidence.
4. Debug/ASan state regressions pass, SDL presents the changed game frames, and a manual F5 pass confirms the visible scene/control result.

## Verification

The 2026-09-15 revised wrapper and all eight arrow-control rows pass. Generator parity and four Debug builds pass. Task 09 adds SDL Debug/ASan capture, OK dismissal, resumed update and Escape main-menu-entry checks. The supplied video confirms cue replacement; manual verification of the newly visible dialog is pending. Gated SDL/ASan readiness remains unsuccessful. See the [requester evidence](../../../../journal/entries/post-intro-requester-2026-09-15.md).

Use bounded task probes, synchronized visibility packets, the corrected Step 07 wrapper, and the arrow matrix. Static hashes are pre-fix references, not desired post-fix hashes. A changed hash alone is insufficient: inspect actor geometry, state changes, selected pixels, and presentation agreement.

## Notes

See the [audit](../../../../journal/entries/runtime-audit-2026-09-14.md) and [runtime journal](../../../../journal/entries/runtime-crash-fixes.md) for the evidence and reverted latch/root-attachment experiments. After this step, resume [Step 03 Task 03](../step-03/tasks/task-03-verify-camera-and-action-frontiers.md).

## Change Log

### 2026-09-14

1. Split actor/action work out of Step 03 without marking remaining gameplay behavior complete.

2. Activated gated action recovery; split the newly exposed missing-scene message failure into Task 04 and retained incomplete Task 01 acceptance.

3. Completed Task 04 for message inputs/lifetime and added Task 05 for the unresolved position/scene-selection failure.

4. Traced Task 05 to the keyframe pool, kept its repair gated, and added Task 06 for scene-pose inputs. Optional SDL actor cues report live actors and absent-enemy status without satisfying game-rendering criteria.
