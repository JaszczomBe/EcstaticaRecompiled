# Recover Joe Geometry And Rendering

Status: planned
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Initialize Joe’s geometry through the recovered update path and draw the living actor into scene 175.

## Scope

1. Trace actor `+0x11e` rep 67 through model/action setup and render-tree update ownership.
2. Recover vertex update/projection inputs from original code.
3. Compare settled no-input and delayed-arrow frames and position state.

## Out Of Scope

1. Synthesizing player pixels or replacing the renderer.
2. Full camera/combat behavior or assuming rep slots are model pointers without source confirmation.

## Implementation Notes

Depends on completed Task 01 validation, including Task 06 scene-pose inputs and Task 05 scene-selection validation (Task 04 message inputs are complete). Baseline packet: Joe actor `0xaa6bd8`, render tree `0x950d3c`, render rep id 67, reported model dword at rep `+0x22` equals `0xffffffff`, slots 17..24 are `-1,-1,384,384,384,384,384,384`. Root `rep_list=0`; sampled local/projected vertices are zero; the current-actor skip flag is clear. Treat sidecar field names as hypotheses to confirm against the original layout.

The gated Task 01 diagnostic packet now advances action 384 but ends in scene slot 40 with changed live coordinates and zero sampled vertices. Establish position/scene ownership before interpreting its image as scene 175; split independent motion/selection repairs if needed. The negative `rep_id` actor-update trace word overlaps the runtime rep pointer and is not the pointed-to rep id.

Rep version 55 direct records populate fields 18..23. Generic old-version record mirroring, attaching the rep to the root node, and clearing a render-skip latch did not establish a fix; earlier attachment/latch proof edits were reverted. Use typed layouts/signatures for recovered fields where justified, mirrored through the generator.

## Acceptance Criteria

1. The initialization/update chain populates source-consistent geometry and projected coordinates.
2. Selected game pixels contain living Joe; the SDL present surface matches those pixels.
3. A delayed arrow after sub-intro completion changes actor position/orientation and visible output as appropriate.
4. Bounded debug/ASan checks pass; manual SDL confirms the player is visible.

## Verification

Capture synchronized before/after packets with `--auto-scene175-visibility` and the existing delayed key-sequence probes. Extend a probe only if needed to wait for actual sub-intro completion and sample position/geometry. Use `scripts/e2r_visibility_sheet.py` and visual inspection; a changed hash alone is not acceptance. Preserve generator parity and run baseline regressions.

## Review State

1. Planning state: agreed
2. Implementation state: not_started
3. Notes: Start after the dependency described above is satisfied.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.
