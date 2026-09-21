# Recover Joe Geometry And Rendering

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-15

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

Geometry now blocks Task 05/01 full-route validation, so recover its bounded input failure before resuming those checks. Task 06 pose inputs and Task 08 packed metadata are implemented. Historical gate-off baseline packet: Joe actor `0xaa6bd8`, render tree `0x950d3c`, render rep id 67, reported model dword at rep `+0x22` equals `0xffffffff`, slots 17..24 are `-1,-1,384,384,384,384,384,384`. Root `rep_list=0`; sampled local/projected vertices are zero; the current-actor skip flag is clear. Treat sidecar field names as hypotheses to confirm against the original layout.

The earlier Task 01 diagnostic packet advanced action 384 but ended in camera 40. Subsequent pose/matrix/event recovery has moved the current gated SDL stop into geometry: `FUN_00424dd8 → FUN_00424e44 → FUN_00433d30 → FUN_00431a7c`, reading `unaff_EBX + 4` with `unaff_EBX=1`. The argument named `actor` is `0x84b34c`, a draw node, illustrating that parameter names are still hypotheses. Recover original EAX/EBX/EDX ownership at these call boundaries before treating a mode value as a pointer. GDB evidence: `/tmp/e2-cues-final-gated.log`.

Rep version 55 direct records populate fields 18..23. Generic old-version record mirroring, attaching the rep to the root node, and clearing a render-skip latch did not establish a fix; earlier attachment/latch proof edits were reverted. Use typed layouts/signatures for recovered fields where justified, mirrored through the generator.

## 2026-09-15 Matrix Repair

A hardware watchpoint identified `FUN_00423858` rotating node `+0x136` and overwriting its attachment pointer at `+0x13a`. Original `0x423c34..0x423c6b` supplies node `+6` for all three simple-branch rotations. Those destinations are corrected and generator-mirrored; the route now reaches the polygon failure above. Recovering a stubbed node-camera call in `FUN_00424ed0` exposed a separate renderer input and was reverted. It remains incomplete, as do other no-argument vector-transform calls.

Camera-projected host primitives are implemented separately in Task 07. They do not populate or prove game geometry. Default Joe remains behind camera 175; gated Joe changes position before the crash, but correct final placement and motion remain unproven. See the [projection journal](../../../../../journal/entries/actor-cues-and-projection-2026-09-15.md).

## Acceptance Criteria

1. The initialization/update chain populates source-consistent geometry and projected coordinates.
2. Selected game pixels contain living Joe; the SDL present surface matches those pixels.
3. A delayed arrow after sub-intro completion changes actor position/orientation and visible output as appropriate.
4. Bounded debug/ASan checks pass; manual SDL confirms the player is visible.

## Verification

Capture synchronized before/after packets with `--auto-scene175-visibility` and the existing delayed key-sequence probes. Extend a probe only if needed to wait for actual sub-intro completion and sample position/geometry. Use `scripts/e2r_visibility_sheet.py` and visual inspection; a changed hash alone is not acceptance. Preserve generator parity and run baseline regressions.

## Review State

1. Planning state: agreed
2. Implementation state: node matrix destination repaired; polygon-input recovery next
3. Notes: Next source task; keep action indexing gated and split independent later render failures.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.
