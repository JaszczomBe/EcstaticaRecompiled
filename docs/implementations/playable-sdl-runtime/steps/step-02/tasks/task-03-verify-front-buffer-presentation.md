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

Latest implementation work moved the blocker from a vague 60-second startup stall to a named scene-removal crash. Narrow `E2R_STARTUP_DIAG=1` logs prove `ken:StartUp` dispatches at guard `822`; the long window was opcode-`0x4d` preload work. `FUN_00447d94` now detects the flat `FANT` layout in `/home/rgrabowski/Games/Ecstatica2/Files/ECSTATIC`, scans `0x19` scene records, and populates `0x650fa0` with `1205` scene offsets instead of interpreting the file as an offset-indexed archive. Startup preloads now install matching requested scene records and child-list walks execute. Follow-up hidden-register repairs made `FUN_00452738` name removals by scene id and let `FUN_0043aa98` receive an explicit scene-remove context. The current bounded/gdb frontier is a segfault in `FUN_0043aa98` at `E2Recomp_recon.c:30109` while loading scene id `1424`, after the last successful `rist10` scene record install and before `mar:StartGame`.

## Next Implementation Slice

Stabilize `FUN_0043aa98` scene-removal/list unlinking after the flat-FANT preload repair, then continue startup execution until the bounded SDL route reaches `mar:StartGame` and resolves `PlayScene "horse"` to a real scene id.

1. Inspect and repair `FUN_0043aa98` list cursor preservation/validity during removals invoked from `FUN_00452738`/`FUN_00452ebc`.
2. Keep flat-FANT archive recovery scoped to the scene-offset table unless a later load proves another resource table is needed.
3. Re-run bounded `E2R_STARTUP_DIAG=1 E2R_SCRIPT_DIAG=1` dummy-SDL/gdb probes until execution passes opcode/action count `64` and reaches either `mar:StartGame` or a later named frontier.
4. Verify the `PlayScene "horse"` token remap after the `_DAT_006366bc` capacity repair; the bad signature was `0007,4fff`, and a repaired scene token should be `0007,4xxx` with low bits below `0x9c4`.
5. Once `PlayScene "horse"` executes, run a real-display/F5 visual smoke test against the E2WIN95 logo and horseback-intro sequence before returning to page/front-buffer proof.

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
3. Notes: Active frontier is startup-sequence parity before final front-buffer/page ownership proof; flat-FANT scene preloads now resolve correctly, and the runtime must clear the `FUN_0043aa98` scene-removal crash before reaching the scripted `mar:StartGame`/`PlayScene "horse"` path.

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
