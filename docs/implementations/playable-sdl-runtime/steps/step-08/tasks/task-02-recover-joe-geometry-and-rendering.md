# Recover Joe Geometry And Rendering

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
<!-- /docs-tree:parent -->

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-14

## Goal

Initialize Joe’s geometry through the recovered update path and draw the living actor into scene 175.

## Scope

1. Trace actor `+0x11e` rep 67 through model/action setup and render-tree update ownership.
2. Recover vertex update/projection inputs from original code.
3. Compare settled no-input and delayed-arrow frames and position state.

## Out Of Scope

1. Replacing original geometry/rendering as this task's final result. The user-authorized diagnostic cylinders in [Step 09](../../step-09/step-09-enable-diagnostic-gameplay.md) have separate acceptance and may precede this task's completion.
2. Full camera/combat behavior or assuming rep slots are model pointers without source confirmation.

## Implementation Notes

The user's 2026-10-14 priority is Step 09 diagnostic gameplay. This task remains the original-rendering owner; its full mesh recovery need not block real action/movement proofs if a narrowly audited visual bypass supports them. Preserve any root-motion/logical-pose inputs required by gameplay.

On the full original-render route, geometry blocks Task 05/01 validation, so recover its bounded input failure before resuming those checks. Step 09 may reach those logic checks earlier through its audited visual bypass. Task 06 pose inputs and Task 08 packed metadata are implemented. Historical gate-off baseline packet: Joe actor `0xaa6bd8`, render tree `0x950d3c`, render rep id 67, reported model dword at rep `+0x22` equals `0xffffffff`, slots 17..24 are `-1,-1,384,384,384,384,384,384`. Root `rep_list=0`; sampled local/projected vertices are zero; the current-actor skip flag is clear. Treat sidecar field names as hypotheses to confirm against the original layout.

The earlier Task 01 diagnostic packet advanced action 384 but ended in camera 40. At the 2026-09-15 checkpoint, pose/matrix/event recovery moved the gated SDL stop into geometry: `FUN_00424dd8 → FUN_00424e44 → FUN_00433d30 → FUN_00431a7c`, reading `unaff_EBX + 4` with `unaff_EBX=1`. The argument named `actor` is `0x84b34c`, a draw node, illustrating that parameter names are still hypotheses. The 2026-09-21 repair below recovers those EAX/EDX/EBX inputs. GDB evidence: `/tmp/e2-cues-final-gated.log`.

Rep version 55 direct records populate fields 18..23. Generic old-version record mirroring, attaching the rep to the root node, and clearing a render-skip latch did not establish a fix; earlier attachment/latch proof edits were reverted. Use typed layouts/signatures for recovered fields where justified, mirrored through the generator.

## 2026-09-15 Matrix Repair

A hardware watchpoint identified `FUN_00423858` rotating node `+0x136` and overwriting its attachment pointer at `+0x13a`. Original `0x423c34..0x423c6b` supplies node `+6` for all three simple-branch rotations. Those destinations are corrected and generator-mirrored; the route now reaches the polygon failure above. Recovering a stubbed node-camera call in `FUN_00424ed0` exposed a separate renderer input and was reverted. It remains incomplete, as do other no-argument vector-transform calls.

Camera-projected host primitives are implemented separately in Task 07. They do not populate or prove game geometry. Default Joe remains behind camera 175; gated Joe changes position before the crash, but correct final placement and motion remain unproven. See the [projection journal](../../../../../journal/entries/actor-cues-and-projection-2026-09-15.md).

## 2026-09-21 Polygon Input Repair

The selector now supplies the optional reference polygon from the owner’s polygon table, and flat/textured dispatch preserves explicit polygon, mode and reference arguments across triangle and quad paths. The temporary direct caller uses contiguous vertex/polygon records and passes their real addresses. Reconstruction and prototypes are generator-mirrored.

Original-machine-code routing comparison passes 576 cases; a twelve-face temporary-record fixture passes normally and under ASan. Four builds, generator parity, default wrapper, eight arrow rows and SDL Debug/ASan requester checks pass. Vertex transforms in the temporary caller and full rasterization remain incomplete.

At the polygon-input checkpoint, gated SDL advanced to `FUN_00431a7c → FUN_004226bc → FUN_004228b8 → FUN_0045dd04`. [Task 10](task-10-recover-polygon-lighting-inputs.md) owns that separate lighting/matrix-input failure; its subsequent repair is recorded below. Gated SDL ASan times out in camera 1073 without reaching geometry. None of this establishes living Joe or visible movement. See the [polygon journal](../../../../../journal/entries/polygon-inputs-2026-09-21.md) for original addresses, commands and limitations.

## 2026-09-21 Flat-Lighting Repair

Task 10 recovers the normal/angle/local-rotation contract and mapped byte color reads in the flat leaf. Original-x86 angle, rotation and lighting-index comparisons pass normally and with ASan; builds, parity and default regressions pass again. A minimally interrupted gated run returns lighting indices 64/64 for normal 0/0/0, then fails in framebuffer copying at `FUN_00418514`. The degenerate normal does not prove valid geometry. Heavily instrumented runs can instead fail in `FUN_0042c790` action-channel handling; gated SDL ASan still times out before geometry.

At this checkpoint [Task 11](task-11-recover-dirty-rectangle-copy-inputs.md) owned the copy-input failure. Its 2026-10-14 repair now passes original-x86 copy/caller comparisons; real DirectDraw Lock still provides base/pitch 0/0. [Task 12](task-12-recover-directdraw-surface-lock.md) owns the next compatibility failure before actual runtime copying/geometry can be verified. See the [lighting journal](../../../../../journal/entries/polygon-lighting-2026-09-21.md). Visible Joe, movement, vertex generation and complete rasterization remain open.

## Acceptance Criteria

1. The initialization/update chain populates source-consistent geometry and projected coordinates.
2. Selected game pixels contain living Joe; the SDL present surface matches those pixels.
3. A delayed arrow after sub-intro completion changes actor position/orientation and visible output as appropriate.
4. Bounded debug/ASan checks pass; manual SDL confirms the player is visible.

## Original-Game Visual Target — 2026-10-14

The [reference log/contact sheet](../../../../../journal/entries/original-game-reference-2026-10-14.md) identifies Joe in the **rear stocks**, then opening restraint, release/jump/landing, standing free and movement toward the left stairs. Compare changing actor silhouettes, pose and overlap with the stock boards/platform at those separate events. The blue foreground body-like form remains fixed while Joe moves independently; it cannot satisfy living-player rendering acceptance. Two green creatures also remain visible/moving through the sequence. The source of the user-described lightning effect and the exact action assigned to each phase still need tracing.

The recorded initial HUD/gameplay view remains the pedestal courtyard. Do not use the reconstructed rooftop/error outcome as the desired reference or substitute a projected host cue for rendered Joe. Task 11's implemented copy contract and Task 12's required surface provider precede this full geometry/animation verification.

## Verification

Capture synchronized before/after packets with `--auto-scene175-visibility` and the existing delayed key-sequence probes. Extend a probe only if needed to wait for actual sub-intro completion and sample position/geometry. Use `scripts/e2r_visibility_sheet.py` and visual inspection; a changed hash alone is not acceptance. Preserve generator parity and run baseline regressions.

## Review State

1. Planning state: agreed
2. Implementation state: matrix destinations, polygon/lighting and copy inputs repaired; Task 12 DirectDraw Lock storage next
3. Notes: Next source task; keep action indexing gated and split independent later render failures.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.

## F5 Continuation — 2026-10-14

[Step 09's continuous-runtime continuation](../../../../../journal/entries/f5-diagnostic-route-2026-10-14.md) supersedes the old event-0x3f diagnostic crash. F5 now selects cylinders/action indexing/mesh and HUD omission; node-removal, retained action/actor and script-input comparisons pass. Debug reaches the wait-ending script, then selects an invalid height and leaves Joe behind camera 83 without motion. Step 09 Task 02 owns that placement/query/control work. Original-render acceptance and compatibility Lock remain open; gated ASan faults in a motion query.
