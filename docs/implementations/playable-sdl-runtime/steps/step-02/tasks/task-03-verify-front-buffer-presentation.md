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

Latest implementation work moved the blocker past the scene-removal crash and through `mar:StartGame`. Narrow `E2R_STARTUP_DIAG=1` logs prove `ken:StartUp` dispatches at guard `822`; the long window was opcode-`0x4d` preload work. `FUN_00447d94` now detects the flat `FANT` layout in `/home/rgrabowski/Games/Ecstatica2/Files/ECSTATIC`, scans `0x19` scene records, and populates `0x650fa0` with `1205` scene offsets instead of interpreting the file as an offset-indexed archive. Startup preloads install matching requested scene records and child-list walks execute. Follow-up hidden-register repairs stabilized scene removal/list cleanup, scene activation, and actor/name lookup. Bounded gdb evidence now reaches `mar:StartGame` stages through `before-return`, then survives until a forced interrupt in the frame loop (`FUN_00426df8 -> FUN_0042a70c -> FUN_0041cf5c -> FUN_004620bb`).

The latest Ghidra-backed repair narrowed the `mar:StartGame` scene opcode itself. Original `E2WIN95.EXE` disassembly around `0044f6cc`/`0044f6f3` and `0044f770`/`0044f78f` shows opcodes `0x07` and `0x0c` pass the loaded scene record to `FUN_004523f8`, not the current-scene global. The generated reconstruction now does the same and adds gated `E2R_SCRIPT_DIAG=1` scene-opcode traces. A bounded dummy-SDL probe proves `mar:StartGame` token `0x061c` resolves to `horse`, flat-FANT offset `607214`, scene slot `0xac2594`, and flags change to `0x02` after activation. This means `PlayScene "horse"` is no longer the unknown.

The current frontier is still a non-crash scene ownership gap after activation. `_DAT_0073cc3c` remains `0x0`, `DAT_0047a470` remains `0x0`, and `E2R_RUNTIME_DIAG=1` frame-loop traces show `current=0x0 actors=0x0 links=0x0` even after `DAT_00479de8` becomes `1`. The same run reports actor `0` load entering with `table=0x0`, and a 20-second dump remains on surface 3 hash `6e39f5ea` with an all-zero palette (`palette_nonzero=0`, `palette_hash=f59c39c5`). The next proof should therefore shift from `PlayScene "horse"` resolution to why actor/scene tables are empty when the active `horse` scene enters the frame loop.

## Next Implementation Slice

Prove scene-current ownership after `mar:StartGame` now that startup preloads and scene removal no longer crash, then compare the first post-startup presentation against the E2WIN95 horseback/credits intro.

1. Trace `FUN_00451f5c` actor `0` loading under the normal `mar:StartGame` route; the latest proof shows `table=0x0`, so the actor archive/table handoff may be missing.
2. Inspect `FUN_00452140`/`FUN_004523f8` child-list passes for hidden actor context loss. The `horse` scene is active, but no actor/current-scene ownership reaches the frame loop.
3. Determine whether `_DAT_0073cc3c` should remain separate from active scene records during the intro, or whether a later recovered scene-select path is failing to run.
4. Run a real-display/F5 visual smoke test against the E2WIN95 logo and horseback-intro sequence before returning to page/front-buffer proof.
5. If the route stays in the frame loop with no actors/current scene, record the next named non-crash frontier with stack sample and last scene/action evidence.

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
3. Notes: Active frontier is startup-sequence parity before final front-buffer/page ownership proof; flat-FANT scene preloads and `mar:StartGame` now execute without crashing, and `PlayScene "horse"` now loads/activates the correct scene record, but no current actor/current scene reaches the frame loop.

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
7. Repaired generated opcode `0x07`/`0x0c` scene activation to pass the loaded scene record into `FUN_004523f8`, matching original disassembly. `E2R_SCRIPT_DIAG=1` proves `mar:StartGame` activates `horse` (`token=0x061c`, slot `0xac2594`, offset `607214`, flags `0x02`), but runtime traces still show no current actor/current scene in the frame loop.
