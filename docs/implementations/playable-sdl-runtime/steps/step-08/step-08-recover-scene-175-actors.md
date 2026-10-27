# Recover Scene 175 Actors

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-27

## Goal

Render and update the living player and scene-backed children after `Start_sc` completes in scene 175.

## Why This Step Exists

Step 03's input investigation exposed independent action-context, geometry, and resource-instantiation failures. The static framebuffer and SDL surfaces agree, so host presentation is already sufficient to observe these repairs. This work now has its own acceptance criteria and follows the automated baseline in [Step 07](../step-07/step-07-restore-reproducible-runtime-baseline.md).

## Scope

1. Recover action 384's actor/action-slot context and advancement.
2. Initialize Joe's rep/model geometry and prove visible movement.
3. Recover scene-backed child instantiation and drawing.

## Execution Priority — 2026-10-14

The user prioritizes controllable gameplay with cylindrical actors over original meshes and visible animation. [Step 09](../step-09/step-09-enable-diagnostic-gameplay.md) now implements cylinder presentation and a partial polygon bypass. Node removal and required action/script inputs now advance Debug to the wait-ending script; post-intro placement and motion-query recovery are next before real movement and camera traversal. Full geometry and all scene children need not finish first. This step's original-render acceptance remains open. Task 12 is a known full-render blocker; the proxy-render audit must establish whether it also blocks that route.

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
5. [Recover Joe Geometry And Rendering](tasks/task-02-recover-joe-geometry-and-rendering.md) — active; matrix, polygon/lighting and rectangle-copy inputs repaired; compatibility Lock storage blocks the next runtime proof.
6. [Activate Scene-Backed Children](tasks/task-03-activate-scene-backed-children.md) — planned; validate after the player path is stable.
7. [Project Actor Cues Into The Scene](tasks/task-07-project-actor-cues-into-scene.md) — completed for cue projection; video confirms grid replacement, default Joe remains behind camera.
8. [Recover Packed Event Metadata](tasks/task-08-recover-packed-event-metadata.md) — completed for the table; full action route remains gated.

9. [Recover Post-Intro Action Error Requester](tasks/task-09-recover-post-intro-action-error-requester.md) — implemented and automatically verified; manual dialog/OK transition confirmed; Escape and persistent-error behavior remain open.

10. [Recover Polygon Lighting Inputs](tasks/task-10-recover-polygon-lighting-inputs.md) — completed for the flat-polygon path; original-x86 arithmetic comparisons pass.

11. [Recover Dirty-Rectangle Copy Inputs](tasks/task-11-recover-dirty-rectangle-copy-inputs.md) — implemented; original-x86 copy/caller comparisons pass; full-route verification depends on Task 12.

12. [Recover DirectDraw Surface Lock](tasks/task-12-recover-directdraw-surface-lock.md) — provider implemented with bounded headless menu/runtime qualification; distinct storage/pitch and ownership fixtures pass; original-render full-route acceptance remains open.

Task numbers remain stable. The full-render route resumes **12 compatibility Lock / 02 geometry → 05/01 placement and action validation → 03 child activation**, with Task 11 full-route, Task 06 full-route and Task 09 manual Escape checks pending. Pose inputs, trigonometry/projection, two corrupting matrix destinations, packed event metadata, polygon/lighting and copy contracts are recovered. The 2026-10-14 continuation verifies copy arguments and bytes, then identifies generic DirectDraw Lock returning destination base/pitch 0/0 as the current provider failure in `FUN_00418514`. The first proven lighting normal is degenerate, so valid geometry remains unproven. Action indexing and pool/event-metadata repairs remain opt-in; the default route exposes the action-384 error after the intro; clicking OK resumes updates at camera 87. Camera 175 must not be treated as script scene-resource 175.

## Acceptance Criteria

1. Action 384 loads/advances without losing actor ownership or crashing through hidden registers.
2. Living Joe is drawn into the selected framebuffer, and an arrow input causes source-consistent position and rendered-output changes.
3. Expected scene children instantiate and render according to original resource semantics; any legitimate absence has source evidence.
4. Debug/ASan state regressions pass, SDL presents the changed game frames, and a manual F5 pass confirms the visible scene/control result.

## Verification

The 2026-09-15 revised wrapper and all eight arrow-control rows pass. Generator parity and four Debug builds pass. Task 09 adds SDL Debug/ASan capture, OK dismissal, resumed update and Escape main-menu-entry checks. The supplied video confirms cue replacement; the 2026-09-21 screenshots confirm the dialog and camera-87 transition after OK, with the error still visible and Joe absent. Manual Escape remains unconfirmed. Gated SDL/ASan readiness remains unsuccessful. See the [requester evidence](../../../../journal/entries/post-intro-requester-2026-09-15.md).

The [2026-09-21 polygon checks](../../../../journal/entries/polygon-inputs-2026-09-21.md) add 576 original-x86 routing cases and twelve temporary-record cases, passing normally and under ASan. The four builds, parity, default wrapper, eight arrow cases and both requester tests pass again.

The subsequent [lighting checks](../../../../journal/entries/polygon-lighting-2026-09-21.md) pass 10,240 angle cases, 16,384 rotations and 8,192 lighting-index cases, normally and under ASan. Builds, parity and the same default regressions pass again; the gated full route remains unsuccessful.

Use bounded task probes, synchronized visibility packets, the corrected Step 07 wrapper, and the arrow matrix. Static hashes are pre-fix references, not desired post-fix hashes. A changed hash alone is insufficient: inspect actor geometry, state changes, selected pixels, and presentation agreement.

The [2026-10-14 rectangle-copy continuation](../../../../journal/entries/rectangle-copy-2026-10-14.md) adds 2,048 original-x86 copy/ownership cases and 256 dirty-list caller cases, passing normally and with ASan. Real gated execution remains unsuccessful because compatibility Lock provides no storage/pitch. Task 12 is the next full-render failure family; the fixture's mock COM surfaces do not prove the host provider.

## Original-Game Reference Capture

The 2026-10-14 original-game clip is analyzed in the [timestamped reference log and contact sheet](../../../../journal/entries/original-game-reference-2026-10-14.md). It establishes a restrained Joe in the rear stocks, two moving green creatures, restraint opening/release, then the HUD and initial movement in the same pedestal courtyard. The current action-error/rooftop result does not match that initial handoff. Prior cue/requester screenshots and recordings cited above remain reconstruction evidence.

Use separate visual checkpoints for restrained actors, credits cleared, restraint opening/release, Joe standing free before HUD, and HUD plus movement. The blue foreground body-like form stays fixed while Joe moves independently and must not be counted as living Joe. Lightning/power-surge narrative comes from the user; its distinct effect frame/event is not confidently isolated. The clip has two game instances/foreground switches, no key overlay and no audio track, so it does not establish universal timing, natural/skip equivalence, exact controls, audio or later camera behavior.

The user confirms that skip taps accelerate **all three logos** and also shorten the **horseback first intro**. Probes must distinguish those stages: separate taps/releases for logos and first-intro skip, then wait for pedestal/action/HUD state. Do not infer natural durations from the recording, hold a skip across transitions, or treat a logo-delay override as validation of key-driven skipping.

Further original-game video would help with those remaining questions. Screenshots support placement, silhouettes, occlusion, palette and requester layout; motion and transition order need video.

Prefer the original Windows version corresponding to the analyzed `E2WIN95.EXE`. Record the executable/version, host or emulator, graphics settings, whether the intro was skipped, and input times. Preserve the full game image at native resolution and keep an unedited timeline.

Remaining useful reference coverage is:

1. A fresh Start Game recording through natural intro completion, the pedestal/lightning sequence and the first 20–30 seconds of control, including a brief idle interval. This establishes the transition and expected actors without relying on the scene-175 guard.
2. A second run pressing Space during the horseback intro, then waiting through the pedestal sequence. This tests whether the skip and natural routes reach the same location and actor state.
3. From the first controllable scene, isolated Up/Down/Left/Right inputs with a pause between them, followed by one short movement across a camera boundary. Show or annotate key presses and durations.
4. Unscaled stills at the pedestal sequence, first controllable frame, before/after movement and camera change, plus the Escape menu. Include timestamps linking them to the video.

Also retain a clear lightning/effect moment and an audio track if those behaviors are being compared. The existing clip already covers the visible release/HUD sequence and first courtyard movement; it is not a missing prerequisite for compatibility Lock recovery.

These captures support Tasks 02/05/03 and the later control proofs. They are useful alongside executable/resource evidence; Task 12 can proceed without them. Do not infer script resource IDs or internal coordinates from pixels alone.

## Notes

See the [audit](../../../../journal/entries/runtime-audit-2026-09-14.md) and [runtime journal](../../../../journal/entries/runtime-crash-fixes.md) for the evidence and reverted latch/root-attachment experiments. Basic [Step 03 Task 03](../step-03/tasks/task-03-verify-camera-and-action-frontiers.md) movement/camera proofs now join Step 09; broader controls follow genuine player readiness.

## Change Log

### 2026-10-14

1. Confirmed the documented frontier against `4fb151a`; expanded Task 11's implementation/verification plan and recorded original-game capture requirements. Bounded comparisons and generator parity pass again; full runtime and manual checks were not repeated.
2. Added the supplied original-game reference and event-based actor/release/HUD comparison targets. These do not complete reconstructed-runtime acceptance.
3. Recorded the user's logo/horseback skip clarification, implemented Task 11's copy contract and split generic DirectDraw Lock storage into Task 12. Full gated scene readiness and actor rendering remain unresolved.
4. Linked Step 09's cylinder-first priority; full meshes/children no longer block initial diagnostic locomotion and traversal. Original-render acceptance remains unchanged.

### 2026-09-14

1. Split actor/action work out of Step 03 without marking remaining gameplay behavior complete.

2. Activated gated action recovery; split the newly exposed missing-scene message failure into Task 04 and retained incomplete Task 01 acceptance.

3. Completed Task 04 for message inputs/lifetime and added Task 05 for the unresolved position/scene-selection failure.

4. Traced Task 05 to the keyframe pool, kept its repair gated, and added Task 06 for scene-pose inputs. Optional SDL actor cues report live actors and absent-enemy status without satisfying game-rendering criteria.
