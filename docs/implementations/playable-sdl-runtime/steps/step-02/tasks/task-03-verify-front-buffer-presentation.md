# Verify Front Buffer Presentation

Status: active
Parent Step: [Recover DirectDraw Page And Palette Semantics](../step-02-recover-directdraw-page-and-palette-semantics.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-29

## Goal

Prove SDL is presenting the recovered front buffer with the intended palette behavior.

## Scope

1. Run title/menu and gameplay presentation proofs.
2. Compare presented frame identity with dumped frame artifacts.
3. Record remaining fidelity gaps.

## Subtasks

1. Capture a title/menu frame after palette recovery.
2. Capture a gameplay frame after palette recovery.
3. Compare frame hashes or screenshot artifacts against expected state.
4. Confirm movement/input probes are unchanged.
5. Update the step evidence and next frontier.

## Out Of Scope

1. Scaling/window-size preferences.
2. Animation timing.
3. Audio.

## Implementation Notes

This is a closeout task for presentation fidelity foundations. If the proof exposes unrelated gameplay crashes, open a separate stability task.

Activated after palette recovery. The palette side is now verified (`palette=1`, `updates=11`, `palette_nonzero=254`, `palette_hash=29b6fa49` in title/menu and gameplay probes), but the front-buffer source is still unresolved: title/menu reports `visible=0`, gameplay can report `visible=1`, `DAT_0047a43c=4`, surfaces 0/1/2 are blank, and surface 3 is the only nonblank presentation candidate.

This task remains active, but front-buffer closeout is temporarily gated by startup-sequence parity. The E2WIN95 reference path is Psygnosis logo, Andrew Spencer Studios logo, Ecstatica II loading/logo, then the engine intro beginning with the horseback/credits scene. The rebuilt SDL route now shows a correctly colored Ecstatica II logo, but still skips the first two logos, flashes the loading screen too briefly, and enters a wrong/stalled scene path.

Latest implementation work moved the blocker past the scene-removal crash and through `mar:StartGame`. Narrow `E2R_STARTUP_DIAG=1` logs prove `ken:StartUp` dispatches at guard `822`; the long window was opcode-`0x4d` preload work. `FUN_00447d94` now detects the flat `FANT` layout in `/home/rgrabowski/Games/Ecstatica2/Files/ECSTATIC`, scans `0x19` scene records, and populates `0x650fa0` with `1205` scene offsets instead of interpreting the file as an offset-indexed archive. Startup preloads install matching requested scene records and child-list walks execute. Follow-up hidden-register repairs stabilized scene removal/list cleanup, scene activation, and actor/name lookup. Bounded gdb evidence now reaches `mar:StartGame` stages through `before-return`, then survives until a forced interrupt in the frame loop (`FUN_00426df8 -> FUN_0042a70c -> FUN_0041cf5c -> FUN_004620bb`). The current frontier is not a crash: `mar:StartGame` still logs `_DAT_0073cc3c=0x0`, so the next proof must explain why the expected horseback/credits scene is not installed as the current scene.

## Next Implementation Slice

Prove scene-current ownership after `mar:StartGame` now that startup preloads and scene removal no longer crash, then compare the first post-startup presentation against the E2WIN95 horseback/credits intro.

1. Trace the `mar:StartGame` `PlayScene "horse"` path and confirm the operand remains a real scene token (`0007,461c` was previously observed, with low bits below `0x9c4`).
2. Keep flat-FANT archive recovery scoped to the scene-offset table unless a later load proves another resource table is needed.
3. Determine why `_DAT_0073cc3c` remains `0x0` through `mar:StartGame` `before-return`, or prove the current scene is installed through another recovered pointer.
4. Run a real-display/F5 visual smoke test against the E2WIN95 logo and horseback-intro sequence before returning to page/front-buffer proof.
5. If the route stays in the frame loop with no current scene, record the next named non-crash frontier with stack sample and last scene/action evidence.

## Acceptance Criteria

1. Front-buffer source is identified in logs or code.
2. Palette behavior is verified with the recovered palette path.
3. Default and SDL probes remain green.

## Verification

1. SDL live-frame probe.
2. PGM/screenshot comparison.
3. `scripts/run-e2-runtime-regressions.sh`
4. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: in_progress
3. Notes: Active frontier is startup-sequence parity before final front-buffer/page ownership proof; flat-FANT scene preloads and `mar:StartGame` now execute without crashing, but scene-current installation remains unresolved because `_DAT_0073cc3c` stays `0x0` through `before-return`.

## Change Log

### 2026-07-28

1. Created task.
2. Activated after palette recovery completed.
3. Advanced E2WIN95 startup archive parsing past the `FUN_00426798` actor `+0xd8` crash: GDB watchpoint evidence showed actor initialization leaves `+0xd8` zero, `FUN_00432e08` later writes a small scale residue there, and `FUN_00426798` then treats the same dword as a list head. The reconstruction now discards impossible small/unreadable list residues before linking the first node and stores the original actor pointer into the new node owner field. A 30-second dummy SDL probe reaches the surface-dump exit path; remaining nonzero exit is the dump writer failing to create PGM/PPM artifacts, not a game crash.

### 2026-07-29

1. Recorded the startup-sequence mismatch against E2WIN95: the rebuilt SDL route reaches a correctly colored Ecstatica II logo but still misses the first two logos and does not enter the expected horseback intro.
2. Documented the latest repaired startup boundaries: full scene-name table capacity, mmap-backed compatibility allocations, fixed-slot actor-name copies, opcode-`0x4d` cursor preservation, and host pumping during scene-preload restores.
3. Outlined the next slice: instrument startup action/preload progress until `mar:StartGame` and `PlayScene "horse"` resolution are proven.
4. Documented the flat-FANT `Files/ECSTATIC` scene-offset repair: startup preloads now install requested scene records and child-list walks execute.
5. Moved the task frontier to the `FUN_0043aa98` scene-removal/list unlink crash while loading scene id `1424`, before `mar:StartGame`.
6. Cleared the scene-removal, scene-activation, and actor-name lookup crash chain: bounded SDL/gdb now reaches `mar:StartGame` `before-return` and interrupts later in the frame loop. The next frontier is explaining scene-current ownership and the missing horseback/credits intro.
