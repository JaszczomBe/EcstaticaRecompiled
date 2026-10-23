# Runtime Milestones

<!-- docs-tree:parent -->
[Project README](../../README.md) · [Parent: Planned project work](README.md)
<!-- /docs-tree:parent -->

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-10-14

## Goal

Recover the Ecstatica II engine on Linux using original game data, progressing from bounded execution and input-state proofs to visible, controllable gameplay and then fidelity and portability.

## Completed Reconstruction Horizon

The [Linux reconstruction record](../implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) documents resource loading, configuration/startup repairs, window creation, loop execution, inspectable frames, input latches, the host boundary, and live SDL presentation. Its historical “first gameplay” milestone was a state/surface probe; it did not establish living-character rendering or release readiness.

## Recommended Order

The [active implementation](../implementations/playable-sdl-runtime/playable-sdl-runtime.md) owns changing statuses and commands. Existing step numbers remain stable; execute prerequisites before the remaining control/timing/audio work.

1. Preserve reproducible generated diagnostics and canonical-control regression checks (Step 07, completed).
2. Enable diagnostic gameplay with cylinder actors against original backgrounds (Step 09): narrow visual-render bypass, genuine action/control handoff, real movement and floor queries, then an adjacent-view crossing and return. Reuse required Step 08 logic repairs and bring basic Step 03 movement/camera proofs forward.
3. Expand NPC activation, interaction and broader controls; recover original meshes and visible animation as a separate fidelity track (remaining Steps 08/03). Full original rendering and every NPC are not prerequisites for initial cylinder gameplay.
4. Recover timing and frame-pacing ownership (Step 04).
5. Map DirectSound/music behavior and implement the smallest justified audio boundary (Step 05).
6. Consolidate bootstrap, developer validation, and release criteria (Step 06).

Full animated intro fidelity, requester polish, and functional save/load require focused follow-up tasks before implementation. Their order may change when evidence shows they block a preceding milestone. Diagnostic cylinders must follow actual game state; preserve action events, root motion and queries needed by gameplay even when their visual animation is omitted. Cylinder presentation, mesh/HUD omission and F5 action/script routing are implemented. Palette fades, experimental unsigned ceiling selection and hosted floor-byte decoding are repaired. The F5 prototype explicitly defers background spawning and keeps Joe in the courtyard after release. Motion/control and terminal ASan event ownership still block gameplay/traversal. NPC spawn input contracts have bounded original-x86 coverage; full activation follows the Joe-first milestone. See the [current evidence](../journal/entries/courtyard-floor-decoder-2026-10-14.md).

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
