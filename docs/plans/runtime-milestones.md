# Runtime Milestones

<!-- docs-tree:parent -->
[Project README](../../README.md) · [Parent: Planned project work](README.md)
<!-- /docs-tree:parent -->

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-10-29

## Goal

Recover the Ecstatica II engine on Linux using original game data, progressing from bounded execution and input-state proofs to visible, controllable gameplay and then fidelity and portability.

## Completed Reconstruction Horizon

The [Linux reconstruction record](../implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) documents resource loading, configuration/startup repairs, window creation, loop execution, inspectable frames, input latches, the host boundary, and live SDL presentation. Its historical “first gameplay” milestone was a state/surface probe; it did not establish living-character rendering or release readiness.

## Recommended Order

After the `v0.3.0` milestone, the user's latest selection on **2026-10-29** is
**remaining object behavior, rendering and interactions**, with added stability
checks and a gameplay playthrough across several Save/Load sessions.
[Step 12 Task 05](../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md)
coordinates anti-acid boots, ladder usage and other remaining object paths. The
[handoff](../journal/entries/object-behavior-and-interactions-handoff-2026-10-29.md) records baseline, session/save/checkpoint
continuity and protection. This priority selection adds no runtime acceptance.

The preceding sound/music recovery is implemented with bounded original-code,
output, persistence and replay evidence in Step 05 Tasks 04/05. Keep their human
listening, event/transition and device-loss limits open while treating audio as
regression coverage for the selected playthrough work.

Earlier object-model and inner-castle priorities retain their recorded bounded
acceptance. Tower key/drop/door passage and protected persistence pass within
[Task 03](../implementations/playable-sdl-runtime/steps/step-12/tasks/task-03-recover-tower-key-trap-and-door-progression.md).
The partly translucent door remains unresolved. [Task 04](../implementations/playable-sdl-runtime/steps/step-12/tasks/task-04-recover-inner-castle-progression-crash-and-models.md)
has original-backed crash/rendering repairs and 3,190 matching recovered-prefix
checkpoints, while its source recording is incomplete and extended route,
equipped-armour human review and full gate/effect composition remain open.
Remaining object/acid work stays tracked without blocking the selected object/interaction
continuation. Preserve possible original defects until a reconstruction mismatch
is proven.

Session saving, replay and the gameplay regression suite remain closed milestones
with recorded limits. Session saving means investigation recording, not game-state
persistence. Existing step/task numbers stay stable. The
[active implementation](../implementations/playable-sdl-runtime/playable-sdl-runtime.md)
owns current acceptance. The retained recovery sequence and current object/interaction focus are:

1. Original player model/animation (Step 08, Task 02): accepted by the user after
   the projection correction on 2026-10-27; retain recorded equipment/video limits.
2. Original enemies' bodies and animations (Step 08, Task 03): accepted direction
   by the user; retain exhaustive species/action, equipment and broader gameplay
   limits. The subsequent gameplay repairs are included in v0.2.0.
3. Implement [functional game save/load](../implementations/playable-sdl-runtime/steps/step-10/step-10-recover-game-save-load.md),
   now implemented with bounded Debug/ASan menu save/change/load and fresh-process
   verification. The owning step records protected original saves, timer-fixture
   evidence and malformed-file/full-progression limits.
4. Recover the [original game HUD](../implementations/playable-sdl-runtime/steps/step-11/step-11-recover-original-hud.md),
   including the player life bar and related indicators. Default to original HUD;
   F1 selects original HUD and F2 selects the existing debug overlay. Implemented
   with bounded original-code and Debug/ASan native verification; Step 11 retains
   indicator-branch and visual-review limits.
5. Recover [item, weapon, door and acid-pool models and animations](../implementations/playable-sdl-runtime/steps/step-12/step-12-recover-object-models-and-animations.md)
   (Step 12), with selected rendering/F3 slices and bounded tower progression
   implemented in Task 03. Establish original asset/owner/primitive/material
   and action contracts for remaining classes; retain fallbacks until
   each recovered class has original-code and fresh native visual evidence.
6. **Implemented with bounded acceptance:** recover [game sounds](../implementations/playable-sdl-runtime/steps/step-05/tasks/task-04-recover-original-game-sounds.md) and original event, resource/PCM, buffer, volume and channel ownership.
7. **Implemented with bounded acceptance:** [recover music](../implementations/playable-sdl-runtime/steps/step-05/tasks/task-05-recover-original-music.md) and its original track selection, looping and transitions. Bounded General MIDI output is implemented; the task owns acceptance limits.
8. **Selected next:** [object behavior, rendering and interactions](../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md),
   with stability checks and session-to-session Save/Load playthrough continuity.

Timing, remaining gameplay defects and portability remain tracked follow-ups.
Take one up sooner when it blocks the active milestone. Preserve the completed
regression suite as verification throughout this sequence.

## Architecture Direction

Reconstructed game logic calls Win32/DirectX-shaped compatibility services, which call the replaceable host backend. SDL already owns window/input/presentation below that boundary. Timing and audio APIs should be added only when recovered callers establish their required semantics.

Linux/i386 is the proving ground. Packed 32-bit pointers, legacy calling conventions, and fixed-address memory remain core constraints. Cross-platform and 64-bit work follows recovery of those assumptions.

## Success Criteria

1. A state latch, nonblank frame, visible actor, actual motion, and faithful gameplay are distinct claims with distinct evidence.
2. Each active blocker has a bounded command, owner layer, and next task; historical notes do not override current status.
3. Generated repairs and retained diagnostics reproduce from `GenerateRecon.js` without unexplained drift.
4. Debug/ASan checks and SDL captures accompany runtime repairs, with manual visual checks for user-facing changes.
5. Temporary guards/no-ops have an explicit limitation and a source-backed replacement/removal condition.
6. Original behavior is recovered through disassembly/Ghidra evidence; host-specific behavior stays below compatibility boundaries.
7. Diagnostic playability and original visual fidelity have separate acceptance. A useful first playable result is genuine input-driven cylinder movement, floor/stair checks and camera traversal with continuous actor state.

## Change Log

### 2026-10-29

1. Subsequently selected Step 12 Task 05 after `v0.3.0`: remaining object
   behavior/rendering/interactions, stability and multi-session playthrough.
   Earlier entries below retain their original selection context.
1. Selected original game sounds after inventory/status recovery, followed by
   music. Activated Step 05 Task 04 with an audible-playback objective.
2. Preserved object/acid, inventory visual/low-mode/hourglass and inner-castle
   acceptance limits; no new audio implementation is claimed.

### 2026-10-28

1. Recorded the committed save/load and menu/layout baseline and the user's new
   priority: original HUD before sounds, then music.
2. Added Step 11 and its first original-code recovery task, with default/F1/F2
   display requirements and preserved diagnostic/gameplay boundaries.

### 2026-10-27

1. Recorded user acceptance of player/enemy recovery and selected functional game persistence as the next milestone after v0.2.0.
2. Added Step 10's context handoff and first original-contract mapping task; game sounds and music follow persistence.

### 2026-10-14

1. Prioritized the user's cylinder-based gameplay milestone over full mesh/animation recovery; added Step 09 and brought basic movement/camera proofs forward.
2. Kept source-backed simulation and original-render fidelity requirements distinct; the proxy path still needs implementation and validation.

### 2026-07-13

1. Created milestone plan.
2. Marked the first five milestones complete after reaching `FUN_00410a48 -> thunk_FUN_004620db`.
3. Added the next runtime milestone sequence from the post-main-loop-entry `"e_config"` crash through first controllable gameplay.

### 2026-07-14

1. Clarified that Linux is the current proving ground, while long-term portability should come from a backend-neutral host layer.
2. Reframed visible-frame and input milestones so they target compatibility-layer behavior rather than Linux/X11-specific implementation.
3. Added explicit future milestones for a replaceable host boundary and SDL-backed host implementation.

### 2026-07-28

1. Marked the reconstruction milestone chain complete through first gameplay, live SDL frame presentation, and SDL F5 launch wiring.
2. Added the playable-runtime horizon: interactive SDL stability, DirectDraw page/palette fidelity, control/camera probes, timing, audio, and reproducible developer workflow.
3. Linked the new Playable SDL Runtime implementation as the owner of post-reconstruction work.

### 2026-07-31

1. Updated milestone 17 to reflect the active frontier: SDL input delivery is proven, while intro `Esc`/`Space` game-state consumption and requester presentation remain unresolved.

### 2026-09-14

1. Reconciled historical reconstruction milestones with the audit's limits on playability.
2. Prioritized baseline and actor recovery before remaining control, timing, audio, and packaging steps.
3. Removed obsolete startup-crash and intro-input descriptions from current guidance.
