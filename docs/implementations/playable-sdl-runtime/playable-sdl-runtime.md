# Playable SDL Runtime

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-10-22
Parent Plan: [Runtime Milestones](../../plans/runtime-milestones.md)

## Goal

Turn the reconstructed Ecstatica II Linux runtime into a practical SDL developer runtime with visible actors, usable controls, repeatable diagnostics, and recovered game behavior.

## Scope

1. Reproducible generated code and bounded runtime validation.
2. Actor/action initialization and rendering after the intro.
3. Gameplay controls, camera behavior, and requester fidelity.
4. Timing, initial audio compatibility, and developer bootstrap.

## Non-Goals

1. A release-ready port, full original fidelity, or 64-bit core migration.
2. Replacing recovered logic with speculative shortcuts or direct SDL calls.
3. Broad generated-file changes unrelated to a source-backed repair.

## Bare Terminal Baseline

The 2026-09-14 audit rebuilt commit `43ddc8a`; the same-day Step 07 continuations restored generator parity, repaired recursive actor ownership, and reran the corrected wrapper, matrix, and SDL packet. See the [audit evidence and commands](../../journal/entries/runtime-audit-2026-09-14.md). The earlier [Linux reconstruction implementation](../linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) remains a historical milestone record.

| Area | Verified state | Limit |
| --- | --- | --- |
| Builds | X11/SDL Debug and ASan compile | Runtime remains Linux/i386 with fixed-address assumptions |
| Controls | All four arrow rows pass in debug and ASan (8/8) | Checks establish input-state latches, not actor motion or visible gameplay |
| Intro route | First-intro Space enters `Start_sc`; completion reaches action-error requester 0x2e | OK resumes updates at camera 87; original reference instead shows release/HUD in the pedestal courtyard; actor/query inputs remain unresolved |
| Presentation | Action error visible over camera 175; selected surface `c2a56a11`, cue-enabled SDL present/window `fd124785` / `ef9e0785` | Static actor position; hosted dialog typography remains rough |
| Joe | Actor 0 has render rep 67 and a render tree | `model=0xffffffff`, root update list empty, draw vertices zero |
| Scene children | Camera and script-resource namespaces distinguished; Start_sc resource 0 traced | Original video confirms two green creatures; their resource identities/activation remain unresolved; 319/322/318 belonged to an unproven lookup |
| Regression wrapper | Debug/early ASan canonical-Up latches and long-delay ASan error-modal checks pass; arrow matrix 8/8 | State/surface checks do not prove actor motion; separate SDL test covers OK and Escape menu entry |
| Generator | Syntax and all four artifact comparisons pass, including polygon/lighting/copy mirrors | Scoped repairs reproduce; broader helper inputs and behavior remain incomplete |
| Audio/save | Compatibility stubs and requester routing exist | MIDI is silent; quick-save writer is a no-op; functional save/load is unproven |

SDL 3.4.12 is vendored in `dep/SDL`. The host backend presents 640x480 frames centered in the 640x640 window and owns window/input/presentation services. X11 remains the default backend; VS Code offers one `Ecstatica Recompiled` launch following the selected CMake preset; select SDL/i386 Debug for everyday use. The September audit used dummy SDL; subsequent manual evidence is recorded below. F5 now supplies the cylinder/action/proxy flags and differs from this bare terminal baseline. Its current Debug result and ASan limits are recorded in Step 09 and the F5 journal.

The 2026-10-14 [documentation review](../../journal/entries/documentation-review-2026-10-14.md) checked the latest commit `4fb151a` against source and setup. Generator syntax, four-artifact scratch parity, and polygon/lighting original-x86 comparisons pass again, normally and under ASan. Full-runtime checks and manual F5 were not repeated in that initial review. The subsequent Task 11 continuation rebuilds all four Debug configurations and reruns the wrapper, eight arrow rows and both SDL requester checks successfully; manual F5, living actors and gameplay remain unproven.

## Step Roadmap

Step numbers are stable identifiers, not execution order. Step 07 is complete. The user's 2026-10-14 priority is **09 diagnostic gameplay, drawing on required 08 logic repairs and basic 03 movement/camera proofs → remaining 08/03 fidelity and controls → 04 → 05 → 06**. Original meshes, visible animation and all NPCs are no longer prerequisites for the first controllable milestone. Steps 01/02 and Step 03 Tasks 01/02 retain their bounded historical completions.

| Step | Status | Outcome / dependency |
| --- | --- | --- |
| [01 — Interactive SDL stability](steps/step-01/step-01-stabilize-interactive-sdl-f5-runtime.md) | completed | Historical bounded startup/F5 investigation |
| [02 — DirectDraw page and palette semantics](steps/step-02/step-02-recover-directdraw-page-and-palette-semantics.md) | completed | Recovered front source, palette, aspect-fit presentation |
| [07 — Restore reproducible baseline](steps/step-07/step-07-restore-reproducible-runtime-baseline.md) | completed | Automated checks pass; manual screenshot/log confirms scene-175 baseline |
| [09 — Diagnostic gameplay with cylinders](steps/step-09/step-09-enable-diagnostic-gameplay.md) | active | Manual castle locomotion/collision confirmed; population/interaction next; Debug/ASan bounded round trips and 60-second released-input observations pass |
| [08 — Recover scene-175 actors](steps/step-08/step-08-recover-scene-175-actors.md) | active | Logic repairs feed 09; full-render route needs DirectDraw Lock, then geometry/placement/action and children |
| [03 — Gameplay control and camera proofs](steps/step-03/step-03-expand-gameplay-control-and-camera-proofs.md) | partially deferred | Input mapping/matrix complete; basic locomotion/camera proofs join 09, broader controls follow readiness |
| [04 — Timing and frame pacing](steps/step-04/step-04-define-runtime-timing-and-frame-pacing.md) | planned | Recover game timing ownership after visible control proofs |
| [05 — DirectSound compatibility](steps/step-05/step-05-begin-directsound-compatibility.md) | planned | Map sound calls before implementing an audio boundary |
| [06 — Developer runtime packaging](steps/step-06/step-06-package-reproducible-developer-runtime.md) | planned | Consolidate existing setup docs, add unified validation, define release gate |

## Active Frontier

The [post-pedestal callback continuation](../../journal/entries/post-pedestal-deactivation-callback-2026-10-22.md) exactly reproduces the user's new script-deactivation crash and restores its original code/actor/node contract. Debug/ASan natural intros plus 60-second idle checks pass; compatible replay returns from the formerly faulting callbacks before reporting incomplete-prefix exhaustion. An additional populated Debug traversal fails its floor-return check; the ASan round trip passes. Workshop re-entry, sword pickup and full experimental ASan acceptance remain separate under Step 09 / Task 09.

At Step 07 completion, all automated baseline checks passed. Tasks 03–06 repaired recursive actor corruption, default-action context, action-advance inputs, and motion-query ownership. The long-delay ASan probe dispatches Space/Up and captures a nonblank scene-87 surface (`bf4a8e25`) without sanitizer errors. The then-current default SDL skip route captured scene 175 with the recorded static hashes. Task 09 below supersedes that capture after making the blocking dialog visible. The user’s crash-free F5 report and subsequent screenshot/log confirm the static scene-175 final image, completing [Task 02’s manual check](steps/step-07/tasks/task-02-repair-canonical-control-regressions.md) and Step 07. Original scene-selection fidelity and living actors remain Step 08 work.

[Step 08 Task 01](steps/step-08/tasks/task-01-recover-action-context.md) now restores the current actor across action parsing, preserves the action slot across helpers, and supplies Joe to child updates. GDB verifies action 384 at `0xac263c`, Joe `0xaa6bd8`, slot `0xaa6c7e`, and progress 0 → 1638 with context restored. Generator parity, three builds, the default wrapper, all 8 arrow rows, and the default SDL packet pass again.

[Task 04](steps/step-08/tasks/task-04-recover-missing-scene-message-inputs.md) now supplies a live `["Can't find scene", "mtorc4", NULL]` list and eliminates the missing-scene ASan lifetime error. GDB confirms scene 40 has resource pointer 0 and archive offset -1. At Task 04 completion, both gated SDL and ASan checks exited 5 waiting for scene 175; the recovered list reaches requester code, whose visible message rendering/dismissal is not validated.

[Task 05](steps/step-08/tasks/task-05-recover-post-intro-scene-selection.md) traced corrupt coordinate events to aliased keyframe allocation. [Task 06](steps/step-08/tasks/task-06-recover-scene-activation-pose-inputs.md) now supplies the pose actor/state and real output destinations. The projection continuation also repaired two matrix destinations that corrupted a scene child head and a node attachment; [Task 08](steps/step-08/tasks/task-08-recover-packed-event-metadata.md) restored packed dispatch metadata under the action-index gate. Task 02’s 2026-09-21 continuation restores polygon/mode/reference arguments, quad dispatch and temporary record storage, with generator mirrors. The original-x86 comparison passes 576 routing cases plus twelve temporary-record checks, normally and under ASan. Task 10 subsequently recovers the flat-lighting normal, angle and rotation contract plus mapped byte color reads. Its original-x86 comparisons pass 10,240 angles, 16,384 rotations and 8,192 lighting-index cases normally and under ASan. Gated SDL returns from lighting with a degenerate normal, then stops in framebuffer copying at `FUN_00418514`; this does not prove valid geometry. That checkpoint led to [Task 11 rectangle-copy inputs](steps/step-08/tasks/task-11-recover-dirty-rectangle-copy-inputs.md); its later result is recorded below within [Task 02 geometry](steps/step-08/tasks/task-02-recover-joe-geometry-and-rendering.md). Gated SDL ASan instead times out in camera 1073 without reaching geometry. Four builds, parity, default wrapper, eight arrow rows and both SDL requester checks pass; see the [lighting evidence](../../journal/entries/polygon-lighting-2026-09-21.md). The gate remains off by default.

[Task 07](steps/step-08/tasks/task-07-project-actor-cues-into-scene.md) replaces the inset with read-only scene-projected crosses/uprights (`E2R_ACTOR_CUES=1`). Recovered trigonometry, rotations, vector transforms and perspective are checked against original machine code. Default Joe's stored position is behind the pedestal camera (depth -3062), so the settled cue reports **0 VISIBLE / 1 BEHIND**; enemies remain absent. A synthetic drawing fixture verifies the primitives, not actual character placement. The supplied 35-second recording confirms grid replacement and bounded default-route survival, completing the cue check. It does not establish character placement. See the [2026-09-15 journal](../../journal/entries/actor-cues-and-projection-2026-09-15.md) for exact tests and remaining limitations.

[Task 09](steps/step-08/tasks/task-09-recover-post-intro-action-error-requester.md) diagnoses the video’s apparent freeze: `Start_sc` completes at 1102/1102, then missing action 384 (`dav:heropick`) opens an invisible modal. The repair restores its live message list, mapped record/text/items and OK routing. SDL Debug and ASan capture the visible error, dismiss it, resume a game update at camera 87, and verify Escape enters the main menu. The revised wrapper retains early ASan input-latch coverage and explicitly checks the later modal. The 2026-09-21 manual result confirms dialog presentation and advancement to camera 87 after OK, with the error still visible and Joe absent. Manual Escape confirmation remains pending; see the [requester journal](../../journal/entries/post-intro-requester-2026-09-15.md).

[Task 11](steps/step-08/tasks/task-11-recover-dirty-rectangle-copy-inputs.md) now supplies surface/X/Y/width/height across four callers, preserves opposite-page selection and recovers mapped lock-descriptor/unlock ownership. Original-x86 comparisons pass 2,048 copy/ownership cases and 256 dirty-list dispatch cases normally and under ASan. Four builds, generator parity, the default wrapper, eight arrow rows and both requester checks pass. Gated Debug still stops in `FUN_00418514`, now because compatibility DirectDraw Lock returns destination base/pitch **0/0**; its vtable slot is a generic no-op. [Task 12](steps/step-08/tasks/task-12-recover-directdraw-surface-lock.md) owns this provider failure. Gated SDL ASan exits 5 in camera 1073 without reaching the copy. Full-route and living-actor acceptance remain open; see the [rectangle evidence](../../journal/entries/rectangle-copy-2026-10-14.md).

Keep action indexing/expanded scripts opt-in during recovery; the single F5 configuration now opts in together with cylinders and mesh/HUD omission. Bare baseline actions remain unavailable, so dismissing its error cannot prove gameplay. [Step 09](steps/step-09/step-09-enable-diagnostic-gameplay.md) and [Task 01](steps/step-09/tasks/task-01-recover-action-event-node-removal.md) recover node removal plus required action/script inputs. Continuous Debug execution shows Joe on the pedestal without the action-384 modal and reaches opcode `0x75`, wait 0/modal 0. The [floor-decoder continuation](../../journal/entries/courtyard-floor-decoder-2026-10-14.md) restores high-address hosted byte reads with bounded original-x86 comparisons, removing the forest fallback. It also recovers NPC spawn query/range/placement inputs; full activation/loading remains open. F5 adds `E2R_DEFER_BACKGROUND_SPAWNS=1`, with on-screen status, to keep the first prototype focused on Joe. Existing actors/scripts and player queries remain active. Continuous Debug keeps Joe `9988,3328,-17408` visible in camera 175 after wait zero, but Up produces no displacement. The [2026-10-16 root-pose repair](../../journal/entries/terminal-root-pose-2026-10-16.md) fixes the watched terminal event-link writer. Debug/ASan execute matching 30-event chains and retain representation 67 at `+0x11e`, but Up/Left press/release still leaves Joe immobile. Full experimental ASan runtime acceptance remains open. [Task 02](steps/step-09/tasks/task-02-recover-post-intro-placement-and-motion-queries.md) owns motion/control and required event recovery; [Task 04](steps/step-09/tasks/task-04-recover-npc-spawn-query-inputs.md) records implemented spawn contracts and deferred full activation. Decoder/spawn fixtures, four builds, generator parity and default wrapper/SDL modal regressions pass; runtime playability remains open. Original DirectDraw Lock remains Step 08 Task 12; other rendering/copies remain active. No gameplay/traversal acceptance is claimed.

The [player-input continuation](../../journal/entries/player-motion-inputs-2026-10-16.md) supersedes the retained-representation frontier: Joe receives representation 12, and live keyboard reads remove a false modifier action. Debug/ASan now reach movement event `0x13` after Up, then fail in `0x4272a8` through the world-motion query. [Step 09 Task 05](steps/step-09/tasks/task-05-recover-player-motion-vector-ownership.md) owns explicit actor/vector/output inputs. New original-code comparisons and final baseline checks pass; movement/traversal and full experimental ASan remain open.

The [motion-query continuation](../../journal/entries/player-motion-query-2026-10-16.md) supersedes that first-query failure. Task 05 recovers event/vector/output ownership with original-code comparisons. A corrected Debug probe demonstrates Up displacement, Left/Right turning and release stopping; Down displacement remains unproven. ASan reaches Up, then a watched gravity write changes height to -16000 after release. [Step 09 Task 06](steps/step-09/tasks/task-06-recover-release-gravity-query-ownership.md) owns that first producer before subsequent fallback/action teardown. Full experimental ASan, real-map collision/traversal and 60-second acceptance remain open; baseline regressions and four-artifact parity pass.

The [2026-10-19 idle-action continuation](../../journal/entries/player-idle-action-2026-10-19.md) resolves that observed height failure at its upstream caller. The queued action ID comes from actor +0x162; passing the representation pointer instead loaded an unrelated FAN and replaced Joe's floor cell. Both Debug/ASan arrow probes and four combined turn/Up probes now retain height 3328/camera 175. Up release has further queued-action displacement, so stopping acceptance must be re-established. Task 02 retains settled stopping, Down, collision, traversal and sustained-time proof; full experimental ASan acceptance remains open. The new original-code caller fixture, four builds, generator parity and baseline checks pass.

The [manual spinning/input continuation](../../journal/entries/player-release-and-spin-2026-10-19.md) repairs actual SDL key-up table selection, restores the original frame-clock wait and recovers the target-facing crash's actor/time/range/angle inputs. Original-code/bridge fixtures and actual SDL Debug/ASan replays pass; releasing turn keys settles facing at rest and longer Down presses displace. Motion queries still steer during Up/Down with turn keys clear, so straight controls and the circling report remain open alongside collision/traversal and full experimental ASan acceptance. Final four builds, generator parity and baseline checks pass.


The [courtyard-camera continuation](../../journal/entries/courtyard-camera-traversal-2026-10-19.md) removes an unsupported camera-slot-to-script-resource activation, recovers the cached camera hint and supplies the terrain trigger's code/actor inputs. [Step 09 Task 08](steps/step-09/tasks/task-08-recover-courtyard-camera-transitions.md) completes bounded actual-SDL **175 → 166 → 175** traversal in Debug and ASan, with Joe retained, wait/modal zero and all keys released. Debug also reaches 167. ASan follows a different route, so identical steering, exact retracing, complete collision behavior and sustained/full experimental ASan acceptance remain open. Original-code fixtures, all four builds, generator parity and baseline regressions pass; the user now confirms practical input and prioritizes further exploration.

The [live steering audit](../../journal/entries/courtyard-steering-audit-2026-10-19.md) verifies 128 captured steering outcomes and 896 real floor responses against original code normally/ASan. Different time/vector inputs precede different Debug/ASan paths; no steering change is warranted for that first-turn family. Both builds pass a camera round trip followed by 60 seconds with released keys and stable Joe state. Reusable capture/replay and saved cases now support further investigation. Task 02 retains physical collision assertions, wider active exploration and full experimental ASan acceptance; this is not sustained continuous-walking proof.

The [manual castle exploration report](../../journal/entries/manual-castle-exploration-2026-10-19.md) confirms practical stairs, angled ledges, collisions and extended free movement. The next priority is [Step 09 Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md): restore original scene population and basic interaction using cylinders. F5 still defers automatic background spawning; missing scripted objects require separate activation/presentation evidence. Full models, exhaustive physics and full experimental ASan remain later acceptance.

[Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md) now identifies the actual pedestal enemies: original `St_gobsc` tracks 284/`gob3` and 293/`gob3b`. Ordinary F5 shows both orange cylinders alongside Joe before and after release. Cylinder mode retains root/motion updates while omitting articulated bones/IK and mesh drawing; bone collision/combat remains unaccepted. The earlier terrain-population probe stays opt-in and did not establish this fixed pair. See the [guard recovery and verification limits](../../journal/entries/pedestal-guard-activation-2026-10-19.md).

The [intro-skip parser continuation](../../journal/entries/intro-skip-fan-ownership-2026-10-19.md) repairs FAN record selection during action callbacks, scene argument ownership and actor finalizer write widths. Space skips at distinct horseback action checkpoints retain both guards and reach release in Debug/ASan. The exact user-reported launch crash has not reproduced in local runtime comparisons; the ownership failure and corrected writes have original-code fixture coverage.

The [general-population continuation](../../journal/entries/general-population-and-direction-audit-2026-10-19.md) supersedes the retained F5 deferral and spawn-event failure: F5 now sets `E2R_DEFER_BACKGROUND_SPAWNS=0`. Original scheduler/event loads scope global archive identity without enabling the old population probe at startup. Generic NPCs and a secondary splash resource activate; populated Debug/ASan camera round trips and released-input observations pass. The user confirms pedestal guard wandering but reports a new immediate post-release direction/arrow regression. Local combined-input replays do not reproduce it; that report remains open alongside general object interaction, combat, articulated collision and full experimental ASan acceptance.

The [2026-10-20 direction continuation](../../journal/entries/direction-modifier-release-2026-10-20.md) reproduces a matching Up+Left/YROT freeze after released Shift/Alt flags remain set in the compatibility bridge. Modifier release now clears those flags; deterministic Debug/ASan and native Wayland ASan replays turn, and the user reports no freezes anymore. A longer native Debug run later fails in the NPC pose-event path `0x42faf8 → 0x424318`. That event handoff, broader interactions and full experimental ASan remain open. F12 packets now retain yaw, matrices and held-arrow bytes for physical reports.

The [early-Space population continuation](../../journal/entries/early-intro-skip-population-2026-10-20.md) reproduces why F5 can still show only the pedestal pair: an early skip omitted `dav:skipsc`'s population-enable opcode. The recovered skip now dispatches that original script, restoring extra actors at release with the existing launch flags. Bounded ASan population passes; Debug later fails in the IK node-pose path `0x42f9c0 → 0x424318 → 0x423674`. Stable early-skip populated Debug exploration and full experimental ASan remain open.

The [NPC pose continuation](../../journal/entries/npc-pose-chain-recovery-2026-10-20.md) closes the early-Space endpoint/IK failure and recovers event-node/pose-owner handoffs. Original-code pose/table fixtures, four builds, independent generator parity and baselines pass. Populated Debug/ASan round trips plus 60-second observations pass, with continuing NPC activity. Native scripted camera steering retains a route limit. [Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md) next owns one original object interaction; full experimental ASan and broader combat/model fidelity remain unaccepted.

The [stables crash continuation](../../journal/entries/stables-node-hit-query-2026-10-20.md) repairs missing X/Z and distinct output pointers in `0x42efdc → 0x427160`, plus its adjacent facing vector. Original-code contact/filter fixtures pass normally/ASan; the recorded courtyard checks do not replace manual camera-177 re-entry. Horse presence, scripted/weapon contacts and full experimental ASan remain open.

The [blacksmith sword continuation](../../journal/entries/blacksmith-sword-activation-2026-10-20.md) restores scene-1909/actor-3717 activation and cylinder presentation using original placement and visibility data. Debug/ASan resource integration and populated courtyard round trips pass. The diagnostic probe selects the workshop camera without moving Joe; ordinary F5 workshop re-entry and sword pickup remain unaccepted under Task 09.

The [workshop initialization/visibility continuation](../../journal/entries/workshop-initialization-and-actor-visibility-2026-10-20.md) reproduces the user's camera-350 crash in the prior source and repairs object durability helper/script arguments. Original actor visibility coordinates and separate object/generated cue labels are restored; the original four-generated-actor cap remains unchanged. Debug/ASan view activation 356→350→347, populated courtyard returns and baselines pass. Manual walking re-entry and sword pickup remain Task 09's next acceptance.

## Original-Game Reference — 2026-10-14

The supplied original-game recording now has a [timestamped observation log, contact sheet and code correlations](../../journal/entries/original-game-reference-2026-10-14.md). Joe is restrained in the rear wooden stocks, the restraint opens around 31.4 seconds, Joe leaves/lands/stands, and the HUD appears around 33.4–33.5 seconds. Two green creatures animate before and after that handoff. The first visible gameplay stays in the pedestal courtyard; the reconstructed action-error/rooftop route does not match this reference. The persistent blue foreground form is not evidence of a rendered living Joe. The user's lightning/power-surge explanation is retained separately from directly isolated visual events.

Use restrained, release, free-before-HUD and HUD-with-movement checkpoints during Tasks 02/05/01/03 and Step 09. This reference supplies visual targets, not new reconstructed-runtime acceptance or exact internal scene/resource IDs. Step 09's node repair is complete; post-intro placement/motion queries are next. Task 12 remains the known full-render provider blocker. The user confirms skip taps advance all three logos and shorten the horseback intro; probes must separate those stages and wait for pedestal/action/HUD state. Duplicate instances/foreground switches still limit timing comparisons, and the recording has no audio stream or explicit key timings.

## Deferred Fidelity Work

Earlier reference reports describe three logos, a 30–40 second horseback/castle intro (Space-skippable), then a pedestal/lightning sub-intro (wait-only) and gameplay. The 2026-10-14 clip shows about 16 seconds from the pedestal fade-in to the full HUD, so the older roughly 10-second sub-intro estimate is not an acceptance deadline. Full animation/procession, effects and source-consistent handoff remain incomplete; route/timer progression alone is insufficient.

Historical menu probes show readable Esc contents, mouse-only intro-menu routing to Settings/Load, Music toggling, Settings OK, and Quit confirmation. Load title/slot overlap, a black slot-area rectangle, modal artifacts, and font/color/layout remain unresolved. Task 09 repairs the shared message-copy/requester-pointer defects and verifies the default action-error dialog. Other message callers, keyboard-only modal interaction and typography remain incomplete; the historical gated missing-scene route has not been revalidated through dismissal. These are follow-ups after actor recovery unless they block a specific proof. Full save/load implementation needs a separate task before it is attempted.

## Invariants

1. Keep SDL below the host backend and preserve default X11 builds.
2. Recover calling conventions and data ownership from original disassembly/Ghidra; mirror durable fixes and diagnostics in `GenerateRecon.js`.
3. Distinguish a state latch, a visible actor, actual movement, and faithful gameplay in acceptance claims.
4. Record bounded commands, failures, last useful evidence, and regression impact in the journal.
5. Split new crash families into narrow tasks instead of expanding the control matrix indefinitely.

## Verification

Run from the repository root:

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build --preset linux-clang32-debug-asan`
4. `cmake --build --preset linux-clang32-sdl-debug` and `cmake --build --preset linux-clang32-sdl-debug-asan`
5. `env -u DISPLAY scripts/run-e2-control-matrix.sh`
6. `env -u DISPLAY scripts/run-e2-runtime-regressions.sh` — isolated debug and ASan pass in the 2026-10-14 verification.
7. `SDL_VIDEODRIVER=dummy timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-scene175 120 7000`
8. `python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl/e2recomp` — repeat with the SDL ASan executable; requires GDB/ptrace.
9. `python3 scripts/check-e2-polygon-inputs.py /path/to/E2WIN95.EXE` — repeat with `--asan`; routing/storage checks, not rasterization.
10. `python3 scripts/check-e2-polygon-lighting.py /path/to/E2WIN95.EXE` — repeat with `--asan`; original-x86 angle/rotation/lighting indices, not rendered actors.
11. `python3 scripts/check-e2-rectangle-copy.py /path/to/E2WIN95.EXE` — repeat with `--asan`; copy/ownership and dirty-list dispatch checks with mock COM surfaces.
12. `git diff --check`

Configure each fresh build with its matching preset and game-data path; see [build setup](../../building.md). Use the [audit](../../journal/entries/runtime-audit-2026-09-14.md) for safe scratch regeneration and the gated GDB repro. Manual F5 remains a separate visual check when runtime behavior changes.

## Manual Follow-Up — 2026-09-14

The user’s 2026-09-14 screenshot matches the automated scene-175 static capture (red sky, central horned skull, stone platforms and straw); the accompanying input log reports `scene=0x67da4c`, the scene-175 slot address. Together with the earlier crash-free manual F5 report, this resolves the pending final-image comparison and completes the Step 07 baseline check. It does not establish original scene-selection fidelity or visible living actors; those remain Step 08 work. The missing cue panel was traced to the usual SDL launch leaving `E2R_ACTOR_CUES` unset; the launch at that time enabled cues with an SDL preset after restarting the session. The 2026-10-14 F5 correction below now selects the diagnostic cylinder/action route.

## Change Log

### 2026-10-19

Recovered actual SDL release handling, the original clock wait and target-facing inputs after the user's spinning/crash report. Both runtimes pass SDL release/movement replays and all final baseline checks; motion-query steering remains the next gameplay boundary. See [Step 09](steps/step-09/step-09-enable-diagnostic-gameplay.md) and the [journal](../../journal/entries/player-release-and-spin-2026-10-19.md).

Recovered the queued idle-action ID and traced its wrong FAN load as the source of the ASan release-height failure. Bounded Debug/ASan arrow and combined-input probes now survive with valid height; full controls/traversal acceptance stays open. See [Step 09](steps/step-09/step-09-enable-diagnostic-gameplay.md) and the [journal](../../journal/entries/player-idle-action-2026-10-19.md).

### 2026-10-16 — Player Motion Inputs

Recovered packed player representation selection and live scan-code reads, with original-i386 comparisons and a release-checkpoint press/release probe. Up now reaches an unrecovered world-motion query rather than a false modifier action; Task 05 owns its actor/vector/output contract. Final builds, parity and baseline regressions pass. See the [input journal](../../journal/entries/player-motion-inputs-2026-10-16.md).

### 2026-10-16 — Terminal Root-Pose Ownership

Recovered actor-matrix and saved-position destinations that corrupted the terminal ASan event chain. Original-code fixtures, matching bounded Debug/ASan courtyard release, four builds, generator parity and baseline checks pass. Motion/traversal remain open; representation 67 is bound after release. See the [root-pose journal](../../journal/entries/terminal-root-pose-2026-10-16.md).

### 2026-10-14 — F5 Diagnostic Route Correction

Corrected the cue-only editor launch after the user's screenshots exposed the mismatch with a stopped opt-in capture. Recovered bounded node-removal, action/actor and script-input contracts. Continuous Debug shows Joe during the pedestal action and executes the wait-ending script without the old action error; invalid height/placement and motion-query inputs now block visibility/control. Expanded script names remain gated, baseline checks pass with the noted isolated arrow-row rerun, and gated ASan has a separate query failure. See [historical F5 evidence](../../journal/entries/f5-diagnostic-route-2026-10-14.md); the [floor-decoder continuation](../../journal/entries/courtyard-floor-decoder-2026-10-14.md) supersedes the placement/ASan frontier.


### 2026-10-14 — Cylinder Implementation

Implemented opt-in cylinder presentation, raw state labels/sidecars and a source-audited polygon gate. Drawing/state-preservation fixtures, polygon comparisons, four builds, generator parity, wrapper, eight arrow rows and SDL requester checks pass. A real paused capture shows Joe during the pedestal action; event-0x3f node removal blocked that initial diagnostic route. The later F5 continuation below supersedes that frontier. Full gameplay and original rendering remain open.

### 2026-10-14 — Diagnostic Gameplay Priority

Added Step 09 at the user's request: prioritize controllable cylinder actors, recovered locomotion and view traversal over original meshes/visible animation. Basic Step 03 movement/camera proofs move forward with the necessary Step 08 logic repairs. The rendering bypass and its minimum surface dependencies require audit; this planning update implements no runtime mode and closes no gameplay acceptance.

### 2026-10-14 — Documentation Review

Checked `4fb151a`, corrected build/cue guidance and stale summaries, reverified generator parity and bounded polygon/lighting comparisons, and expanded Task 11's source-backed plan. Original-game capture requirements are recorded in [Step 08](steps/step-08/step-08-recover-scene-175-actors.md#original-game-reference-capture). No runtime implementation or full-route acceptance changed.

Analyzed the subsequently supplied original-game clip and recorded the screen/actor timeline, release/HUD checkpoints, two visible creatures, initial courtyard continuity and code connections. Linked those targets into the actor/action/placement tasks; the reference analysis itself did not change runtime behavior. The subsequent authorized Task 11 repair restores copy/lock inputs and passes original-x86 comparisons and regressions; real surface Lock storage is split into Task 12. Logo/horseback skip taps are recorded explicitly for future probes.

### 2026-07-28

1. Created implementation after the reconstructed-runtime plan reached first gameplay, live SDL presentation, and an SDL F5 launch route.
2. Completed Step 1 with a stable SDL F5/no-crash boundary and activated DirectDraw page/palette/front-buffer recovery.
3. Step 2 advanced post-logo startup scene selection by initializing archive-loaded actor live positions through the original `FUN_0044146c` helper.

### 2026-07-29

1. Reframed the active frontier around E2WIN95 startup-sequence parity after palette recovery proved the logo colors but F5 still skipped the Psygnosis/Andrew Spencer screens and entered the wrong scene/stall path.
2. Recorded the latest bounded result: SDL startup survives to timeout after archive load with crash fixes applied, but does not reach `mar:StartGame` or the expected horseback intro yet.
3. Recovered flat-FANT startup preloads by scanning `Files/ECSTATIC` scene records into `0x650fa0`; opcode-`0x4d` now installs requested scene ids, and the active crash frontier moved to `FUN_0043aa98` scene-removal/list unlinking while loading scene id `1424` before `mar:StartGame`.
4. Cleared the pre-`mar:StartGame` crash chain: bounded SDL/gdb reaches `mar:StartGame` `before-return` and later interrupts in the frame loop. The active frontier is now scene-current ownership and the missing horseback/credits intro route.
5. Repaired generated opcode `0x07`/`0x0c` scene activation to match original `E2WIN95.EXE` register flow by passing the loaded scene record into `FUN_004523f8`. The `horse` scene now activates, exposing the next non-crash frontier: empty actor/current ownership after activation.
6. Recovered flat-FANT actor offsets and hidden actor context through the `FUN_004523f8` activation pass. The normal route now loads actor `0` and reaches the frame loop with nonzero actor/current ownership; the next crash frontier is bogus raw-view/camera selection in the render epilogue.
7. Recovered raw-view scene id and palette filename construction for the render epilogue. Regenerated SDL debug probes now survive 30 frames after `mar:StartGame`, load `hires\1073.raw`, and dump nonblank surface 3; the active frontier moves back to visual/front-buffer parity.

### 2026-07-30

1. Completed DirectDraw front-buffer recovery: hires/full-frame presentation uses recovered surface `3`, with diagnostics reporting `front=3` and palette-applied surface hash `44b33248`.
2. Kept the default runtime regression green by adding generated ASan-safe repairs for surface blits, sparse original globals, raw-view path buffers, palette reads, cleanup marker helpers, and actor animation context.
3. Activated the next implementation step around gameplay control/camera proof expansion and remaining startup-logo timing parity.
4. Fixed the first-scene color mismatch reported by screenshot comparison by publishing `FUN_0044add8`'s freshly loaded `Views/1073.PA2` palette through `FUN_0041af88`; the scene dump now reports palette hash `de4e4c5d`.
5. Fixed the user-reported horizontal squeeze by making SDL presentation aspect-fit source frames instead of stretching `640x480` content to the full `640x640` host window.

### 2026-07-31

1. Reclassified the active input problem: SDL/window event delivery is proven, but intro `Esc`/`Space` game behavior is still wrong.
2. Recorded that `Space` latches in game state during the horseback/credits intro yet is not consumed as a skip; natural completion dispatches opcode `0x07` to scene `7`, which then tries to load missing actor `3853`.
3. Recorded that `Esc` enters the reconstructed menu/requester state path and shows a menu with broken contents, making requester drawing/content presentation the likely next proof area.
4. Paused broader runtime edits and generator work until the action-dispatch/requester-presentation cause is isolated with smaller evidence.

### 2026-08-04

1. Restored hosted high-res requester label visibility for the intro `Esc` path, including a conservative ASCII fallback renderer, requester-item text y-coordinate correction, and a final label redraw after item rectangles are painted.
2. Hardened SDL event polling against injected Win32 probe dispatch from a non-main thread; bounded probes now avoid the SDL main-thread assertion while still delivering queued keys.
3. Added a narrow `FUN_00423858` child/linked actor readability guard after the full wrapper exposed an ASan-only actor-transform crash; the wrapper now fails at the known ASan scene-control gate instead of a sanitizer report.
4. Completed Step 3 Task 01 and activated Task 02 for the compact control probe matrix, carrying the `Space` action-dispatch/completion frontier as the remaining intro-control split.
5. Added and passed `scripts/run-e2-control-matrix.sh`, then corrected it to the Ecstatica II manual mapping: arrow keys are canonical movement and numpad keys are not original controls.
6. Fixed SDL/X11 host key translation so physical arrows reach WndProc as `VK_UP`, `VK_DOWN`, `VK_LEFT`, and `VK_RIGHT` instead of masquerading as numpad keys. Added parser/scan coverage for `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; Task 03 owns modifier, status/icon, save/load behavior classification.
7. Added bounded intro-menu mouse-click probes and fixed the requester mouse path. `--inject-intro-menu-click-surfaces` now proves Settings (`320,225`) routes to requester id `0x31`/state `2`, and Load (`320,203`) routes to requester id `0x29`/state `4` without crashing. The sequence probe `--inject-intro-menu-click-sequence-surfaces` now proves the Settings Music row dispatches through item `0x643998` and flips `settings.music=1`, and its target-requester Esc mode proves Settings/Load submenu close paths finish with `DAT_00636844=0` and `_DAT_00643650=0`.
8. Repaired the manual intro-menu artifact/crash repro: Start Game now guards the stale-current actor write in `FUN_0043a39c` and routes to `action.restart_intro` during the intro, high-res requester panel/item rectangles draw from explicit hosted bounds instead of hidden-register coordinates, disabled Save is consumed without closing requester `0x28`, active main-menu Escape unwinds as cancel/no-selection, and Settings row/OK clicks dispatch in bounded probes. Submenu opening now passes explicit requester records for Settings and Load/Save; Load/Save uses the wider slot-list record so it is visible and framed, with title/slot overlap and the left black rectangle still pending. Keep manual real-SDL confirmation as the next acceptance check before moving on to Load slot/OK fidelity.

### 2026-08-17

1. Folded the latest manual real-SDL report into Task 03: startup logo order is now correct, the intro still lacks character animation/scene progression, main menu Esc/Cancel works basically, Quit/Settings/Load remain rough, and Save is inert in the intro menu.
2. Repaired requester label fallbacks for fixed-address `OK`, `Yes`, and `No` text, redraws Settings row toggles in place, names Load/Save slot actions in diagnostics, consumes slot-row clicks without closing the active Load/Save requester, and logs requester `0x28` item bounds for future probes.
3. Verified with `linux-clang32-sdl-debug` dummy-SDL probes: Settings Music toggles to `settings.music=1`, Settings OK returns to the main menu, Load slot clicks report `action_name=load_slot` while staying in requester `0x29`, Quit Yes exits cleanly, and Quit No returns to requester `0x28`.
4. Moved first-intro `Space` from input-delivery proof to action-completion proof: the skip helper now consumes Space and sets action `0x937800` to duration `495`, `FUN_0042b004` breaks on the observed self-loop sentinel, and the active frontier is the post-completion `FUN_00421f54` actor/list-context crash before the pedestal/lightning sub-intro is reached.

### 2026-08-18

1. Recovered the pragmatic first-intro skip route: `Space` during the `horse` scene-child action wrapper now logs `intro skip request` and loads `Start_sc`; `Space` during `Start_sc` is consumed as wait-only.
2. Repaired supporting generated frontiers exposed by the skip path: fixed scene-child allocation, skipped unresolved no-archive startup children, preserved action-event actor context, added a CRT RNG fallback, and recovered the sound id for `FUN_0042b880` subcase `5`.
3. Recovered `Start_sc` completion into gameplay: scene-child actor live-vector initialization now preserves Joe at `12800,256,-3584`, signed scene-height lookup treats descriptor byte `0xff` as passable, and the later handoff repair preserves scene `175` when `FUN_0044c224` tries to switch to scene `87`.
4. Added grouped held-key probe notation and repaired the ASan render/action helper crash chain exposed while re-running the movement matrix. `scripts/run-e2-control-matrix.sh` now passes all debug and ASan rows for `up/down/left/right` after the explicit-context and packed-table fixes.

### 2026-08-20

1. Repaired the post-`Start_sc` wrong-location handoff reported from manual SDL: the exact action `0x9377e3` completion now sets a one-shot guard, and `FUN_0044c224` preserves current scene slot `175` when descriptor `48771` proposes scene `87`.
2. Verified `node --check`, regeneration, `git diff --check`, `cmake --build --preset linux-clang32-sdl-debug`, and the long dummy-SDL route. The route exits with `_DAT_0073cc3c=0x67da4c`, `hires\0175.raw`, surface 3 hash `321e33d6`. The initial Joe-visible interpretation was disproved by the 2026-08-21 packets.

### 2026-08-21

1. Added a post-handoff visibility packet probe with F12 and env triggers. It captures game framebuffer pages, SDL converted presentation, SDL final window surface, and a state sidecar so the current manual no-player report can be classified by layer.
2. Verified the post-handoff dummy-SDL packet: scene slot `175`, action pointer cleared, selected surface `3` hash `321e33d6`, SDL present hash `914159a1`, SDL window hash `5cf799a1`, and contact/diff artifacts generated by `scripts/e2r_visibility_sheet.py`.

### 2026-09-14

1. Reconciled current claims against the audit, retracted living-Joe visibility, and separated input proof from playability.
2. Added Steps 07/08 and deferred remaining Step 03 controls behind baseline and actor recovery.
3. Recorded generator drift and the current debug numpad-wrapper failure; source repairs remain pending.

4. Completed generator diagnostic mirrors and canonical wrapper correction; split the ASan natural-intro action-candidate crash into Step 07 Task 03. All 8 arrow rows and the SDL static packet remain passing; Step 07 is not complete.

### 2026-09-14 — SDL Cue Launch Follow-Up

The usual SDL F5 launch now enables actor cues. The supplied screenshot/log resolves the manual static-scene comparison and closes Step 07; Step 08 remains active.

### 2026-09-14 — Build And Editor Workflow

Consolidated F5 around the selected CMake target, shared preset settings, added X11/SDL ASan presets, and moved personal data paths to environment/cache/local overrides. See [build and editor setup](../../building.md). Step 08 source recovery is unchanged; Step 06 still owns unified validation and broader bootstrap acceptance.

### 2026-09-14 — Build Types And Compiler Visibility

Added SDL Debug/Release/RelWithDebInfo/MinSizeRel choices, explicit Debug + ASan names, and configuration-first output directories. Shared presets use `clang-21` with a major-version check; local presets can select another installed Clang in an isolated directory. Regression scripts and current Step 08 commands follow the new paths. All nine configurations build; the Debug wrapper/matrix and SDL probes pass. Release, RelWithDebInfo and MinSizeRel currently crash during startup, so their runtime recovery remains separate from the active Debug scene-pose work. See [build setup](../../building.md).
