# Verify Front Buffer Presentation

Status: completed
Parent Step: [Recover DirectDraw Page And Palette Semantics](../step-02-recover-directdraw-page-and-palette-semantics.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-30

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

Earlier work temporarily gated front-buffer closeout on startup-sequence parity. The E2WIN95 reference path is Psygnosis logo, Andrew Spencer Studios logo, Ecstatica II loading/logo, then the engine intro beginning with the horseback/credits scene. The front-buffer source is now verified independently; the remaining skipped/shortened startup-logo timing belongs to the next visual/control parity pass.

Latest implementation work moved the blocker past the scene-removal crash and through `mar:StartGame`. Narrow `E2R_STARTUP_DIAG=1` logs prove `ken:StartUp` dispatches at guard `822`; the long window was opcode-`0x4d` preload work. `FUN_00447d94` now detects the flat `FANT` layout in `/home/rgrabowski/Games/Ecstatica2/Files/ECSTATIC`, scans `0x19` scene records, and populates `0x650fa0` with `1205` scene offsets instead of interpreting the file as an offset-indexed archive. Startup preloads install matching requested scene records and child-list walks execute. Follow-up hidden-register repairs stabilized scene removal/list cleanup, scene activation, and actor/name lookup. Bounded gdb evidence now reaches `mar:StartGame` stages through `before-return`, then survives until a forced interrupt in the frame loop (`FUN_00426df8 -> FUN_0042a70c -> FUN_0041cf5c -> FUN_004620bb`).

The latest Ghidra-backed repair narrowed the `mar:StartGame` scene opcode itself. Original `E2WIN95.EXE` disassembly around `0044f6cc`/`0044f6f3` and `0044f770`/`0044f78f` shows opcodes `0x07` and `0x0c` pass the loaded scene record to `FUN_004523f8`, not the current-scene global. The generated reconstruction now does the same and adds gated `E2R_SCRIPT_DIAG=1` scene-opcode traces. A bounded dummy-SDL probe proves `mar:StartGame` token `0x061c` resolves to `horse`, flat-FANT offset `607214`, scene slot `0xac2594`, and flags change to `0x02` after activation. This means `PlayScene "horse"` is no longer the unknown.

The actor/current ownership gap is now narrowed. `FUN_00447d94` also scans flat-FANT type `0x08` actor records into `0x653840`; generated-code probes report `archive 47d94 flat FANT: actors=81 scenes=1205 bytes=33075606`. The normal `mar:StartGame` route loads actor `0` from offset `12773490`, activates `horse` at slot `0xac2594`, sets the active scene record to `0x67c728`, and reaches the frame loop with `current=0xaa6bd8 actors=0xaa6bd8 links=0xaa6bd8`. The first frame still clears `_DAT_0073cc3c`, but actor `0` keeps `p132=0xac2594`, tying it back to the active `horse` scene.

The raw view/camera crash is now cleared. Original disassembly shows both the `FUN_004211c8 -> FUN_0044be20` render epilogue path and the `FUN_004523f8` current-actor child pass pass `scene_record[0] >> 16` into `FUN_0044be20`; the generated code now makes that hidden `AX` value explicit. The adjacent `FUN_0044add8` palette path builder now uses a full local path buffer, writes the four scene digits from `_DAT_0073ccba`, appends it to the data directory buffer, and the shared `FUN_0045fd2c`/`FUN_0045fd4b` helpers initialize their hidden `EAX` destination from `param_1`. A regenerated 30-frame dummy-SDL probe exits successfully after `view raw open: scene=1073 camera=1073 hires=1 path=hires\1073.raw`, stable actor-loop updates, and a nonblank surface-3 dump (`hash=44b33248`).

Front-buffer presentation is now verified. Original `FUN_0043acec` disassembly proves surface `3` is the full `640x480` raw/frame buffer in hires mode, while surfaces `0/1/2` are low-page buffers. The native selector recovers `front=3` when `DAT_0047a43c != 0`, tries that surface first, and keeps the previous nonblank heuristic as a fallback. Probe evidence shows `host backend live presentation: selected=3 front=3 visible=0 hires=4`, dump state `front=3 visible=1`, scene palette hash `de4e4c5d`, and surface `3` hash `44b33248`.

The default regression wrapper passes in both builds. Debug still trips the historical control-ready marker. ASan reaches StartGame, clears requester state, installs scene `_DAT_0073cc3c=0x683c84`, accepts `num8` movement, dumps nonblank surface `3`, and exits without sanitizer reports; the ASan harness gate now accepts that scene/control/surface evidence because `DAT_00479de8` remains unset in the bounded sanitized run.

## Next Implementation Slice

Closed. Carry remaining visual-startup timing work into the next gameplay/control slice.

1. Expand movement and camera proofs beyond `num8`.
2. Keep the recovered `front=3` evidence in future SDL probes.
3. Reconcile Psygnosis, Andrew Spencer, and loading-logo timing during the next real-display pass.

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
2. Implementation state: complete
3. Notes: Front-buffer/page ownership is verified. Hires/full-frame mode presents recovered surface `3`; palette-applied probes dump nonblank surface `3` with hash `44b33248`, scene palette hash `de4e4c5d`, and debug/ASan runtime regressions pass.

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
8. Recovered flat-FANT actor offsets and hidden actor context in the `FUN_004523f8` child pass. Generated probes now load actor `0` from offset `12773490` and enter the frame loop with `current=0xaa6bd8 actors=0xaa6bd8 links=0xaa6bd8`; the new crash frontier is bogus raw view/camera ids in `FUN_00449b4c -> FUN_0043cbb4 -> FUN_0043cbf0 -> FUN_0043b384 -> FUN_0041ab4c`.
9. Recovered the hidden scene-id argument to `FUN_0044be20`, repaired `FUN_0044add8` palette path construction, and initialized `FUN_0045fd2c`/`FUN_0045fd4b` destination pointers from their explicit arguments. Regenerated 30-frame SDL probes now survive through repeated actor updates and dump nonblank surface 3 after loading raw view `1073`.

### 2026-07-30

1. Recovered the DirectDraw front source for hires/full-frame presentation from original surface setup: surface `3` is the intended `640x480` front buffer.
2. Updated native presentation and dump diagnostics to report `front`, and made the selector use recovered front surface `3` before falling back to nonblank scanning.
3. Updated the regression wrapper so ASan validates scene/control/surface state instead of the debug-only `DAT_00479de8` marker; `scripts/run-e2-runtime-regressions.sh` now passes.
4. Fixed screenshot-reported first-scene colors by publishing `FUN_0044add8`'s loaded `Views/1073.PA2` palette buffer (`0x0061c730`) via `FUN_0041af88`; the color dump now matches the original red/black scene palette family.
