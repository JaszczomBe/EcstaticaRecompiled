# Recover DirectDraw Page And Palette Semantics

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-29

## Goal

Replace first-live-frame grayscale heuristics with recovered DirectDraw-facing page, front-buffer, and palette behavior.

## Why This Step Exists

Live SDL presentation currently proves that real recovered frames can reach the backend, but it still depends on selection heuristics and grayscale indexed-8 conversion. A playable runtime needs the compatibility layer to know which page should be visible and which palette should color it.

## Scope

1. Map recovered DirectDraw surface/page ownership.
2. Recover palette update paths and dirty state.
3. Present the intended front buffer through the backend.
4. Keep PGM frame probes useful as regression artifacts.

## Out Of Scope

1. Renderer rewrites.
2. Texture filtering or scaling policy.
3. Audio and timing fixes.

## Usage Budget

Split this step if page ownership and palette recovery turn into separate Ghidra investigations.

## Temporary Sacrifices

1. Sacrifice: Keep heuristic surface 3 presentation until front-buffer ownership is proven.
2. Why accepted now: The current hashes are useful for stability and nonblank-frame proof.
3. Removal trigger: Front-buffer/page ownership is recovered enough to present without scanning for a nonblank candidate.

## Tasks

1. [Map Surface And Page Ownership](tasks/task-01-map-surface-and-page-ownership.md) - completed.
2. [Recover Palette Update Path](tasks/task-02-recover-palette-update-path.md) - completed.
3. [Verify Front Buffer Presentation](tasks/task-03-verify-front-buffer-presentation.md) - active.

## Acceptance Criteria

1. The runtime names the page intended for presentation.
2. Palette state is captured or explicitly proven unchanged for a frame.
3. SDL presentation uses recovered compatibility state instead of only heuristic selection.

## Verification

1. SDL live-frame probe.
2. PGM frame dump comparison.
3. Default debug/ASan regression script.

## Notes

This step should start from existing `E2R_HostPresentIndexed8` and DirectDraw compatibility state, not from direct SDL presentation changes.

Activated after Step 1 proved SDL F5 launch stability: the window presents real frames without crashing, while the visible output remains grayscale/incorrectly colored and page selection still depends on presentation heuristics.

2026-07-28 page mapping result: bounded SDL dummy-driver probes report `DAT_0047a43c=4`, while surfaces 0/1/2 are blank and surface 3 is the only nonblank candidate (`hash=6e39f5ea` for title/menu, `hash=3615add9` for gameplay). Title/menu reports visible page `0`; the later gameplay dump can report visible page `1`. Surface 3 remains the current heuristic presentation page; it is not yet proven as the recovered DirectDraw front buffer.

2026-07-28 palette recovery result: `FUN_0041af88` populates DirectDraw palette entries, and the compatibility shim now captures palette creation, surface palette binding, and palette entry updates. A user screenshot comparison proved the initial six-entry capture was still wrong, so the raw-image and fade palette-source call sites now pass their fixed 0x300-byte buffers into `FUN_0041af88`. SDL presentation receives the active palette through the backend API while keeping grayscale fallback for missing palette state. Title/menu and gameplay probes both report `palette=1`, `updates=11`, `palette_nonzero=254`, and `palette_hash=29b6fa49`; the palette-applied title PPM visually matches the original beige-on-black logo.

2026-07-28 startup-scene recovery result: the F5 data path `build/linux-clang32-sdl-debug/Ecstatica2` is a symlink to `/home/rgrabowski/Games/Ecstatica2`, so the post-logo stall was not a bad data directory. Targeted probes showed actor 0 loaded from archive offset `3997760`, but its live position vector at byte `0x84` stayed zero, causing `FUN_00448744` to select scene id `0` and fall back to scene `7`. The actor archive does not carry a `0x16` live-position record; it carries a `0x14` standing/start vector at byte `0x9c`. `FUN_00451f5c` now invokes the original `FUN_0044146c` initialization helper after successful archive actor parses when the live vector is still zero and the standing vector is nonzero. The bounded SDL probe now reports actor 0 `live=-8448,1536,-15616`, `scene lookup 48744` cell `0x5b96`, and `scene select 4c224` scene id `420`, replacing the previous scene `0`/fallback `7` failure.

2026-07-29 post-regeneration frontier: after a clean SDL rebuild, the same actor 0 live/start vector `-8448,1536,-15616` is still recovered through `FUN_0044146c`, so actor start-vector initialization is no longer the primary suspect. A bounded diagnostic run shows the initial `FUN_00447638` world table parse remains coherent (`49650` descriptor entries, `1200` segment records, tail starts at offset `2098471`), but `FUN_00448744` now maps that actor coordinate to cell `0x0f49`; descriptor `0x0f49` has scene words `0000,0000`, causing `FUN_0044c224` to select scene `0` and fall back to scene `7`. A diagnostic-only alternate lookup logs that the swapped-axis cell would be `0x0c00` with scene words `0427,0427`, but original disassembly still supports the current `FUN_00448744` coordinate formula. The next repair should prove whether a later table mutation, descriptor-table interpretation, or startup action path changed before applying any x/z swap.

2026-07-29 continuation result: gdb watchpoints proved the startup action preload path (`ken:StartUp` opcode `0x4d`) was overwriting the broad scene-selection grid after the initial `Files/ECSTATIC` parse. The first coherent `FUN_00447638` load reports actor coordinate cell `0x5b96` with descriptor scene words `0038,0038`; later opcode `0x4d` scene preloads clobbered the same cell to `0x0f49`, which caused the scene `0` fallback. `FUN_0045233c` now snapshots/restores the `0x00684d68` grid, descriptor table, and `DAT_0047a77c` around opcode-`0x4d` archive parses. `FUN_0044d4b4`/`FUN_0044d608` were then recovered away from stale `extraout_EDX` child-list walks, and `FUN_00424ed0` now receives actor context through `E2R_actor_calc_context` from `FUN_004249f4`. Verification under escalated gdb and plain escalated dummy-SDL execution now runs past 30 seconds without the scene `0` fallback or the previous post-scene-420 crashes; sandboxed non-escalated execution still exits with signal `31`, so use escalated/gdb or F5 for this runtime check.

2026-07-29 F5 startup-regression repair: a clean rebuild exposed two launch regressions before visual fidelity could be judged. SDL printed only the data directory because hosted `ReadFile` entered libc `FILE*` buffer allocation after SDL/Wayland helper threads were live; `CreateFileA` now makes compatibility file streams unbuffered. The shared X11/SDL path also spent excessive time in repeated Linux `IsBadReadPtr` scans while interning FAN names; `/proc/self/maps` parsing is now cached and refreshed on a cached miss so newly allocated heap ranges are not rejected. A follow-up crash in `FUN_0044c224` was another stale-register loop artifact: the actor flag loops now preserve their own actor index and mask after `FUN_0044d34c`/`FUN_0044d4b4`. With `E2R_STARTUP_LOGO_DELAY_MS=0`, both default and SDL real-display runs reach `E2R open failed: path=rb`, `E2R open failed: path=SCENES`, and `archive 47d94 loaded: cursor=56240 remaining=33019366`; the SDL timeout wrapper still requires manual cleanup, so F5 remains the preferred visual smoke check.

2026-07-29 startup-sequence parity result: comparison against `/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` shows the expected startup sequence is Psygnosis logo, Andrew Spencer Studios logo, Ecstatica II loading/logo, then the engine intro beginning with the horseback/credits scene. The rebuilt SDL route still does not match that: user F5 reports missing first two logos, the Ecstatica II logo appears too briefly, and the runtime enters a wrong/stalled scene path. Investigation showed the source FAN text contains `PlayScene "horse"`, but generated scene-name lookup had been capped to `5000` bytes despite `_DAT_006366bc` being allocated as `20000`; the active generated helpers now use `20000`, preventing that class of `4fff` unresolved scene token. Additional clean-start crash frontiers were repaired: Win32 compatibility allocations now use zeroed mmap-backed blocks instead of libc `calloc`, fixed-slot actor-name table copies no longer depend on stale hidden `in_EAX`, opcode `0x4d` child-list walks no longer overwrite their cursor with `extraout_EDX_11`, and long scene-preload restores call `E2R_PumpHost()` so SDL can process events and present frames during startup work. Verification passed generator syntax/regeneration, debug and SDL builds, `git diff --check`, and a quiet bounded SDL dummy-driver probe that survived to forced timeout after `archive 47d94 loaded`. The probe still did not reach `mar:StartGame` within 60 seconds, so startup/preload progress is now the active blocker before front-buffer presentation can be closed.

2026-07-29 flat-FANT startup-preload result: narrow `E2R_STARTUP_DIAG=1` logs proved startup does find and dispatch `ken:StartUp` at guard `822`, so the previous 60-second no-progress window was inside long opcode-`0x4d` preload work rather than before `FUN_0043a39c`. The root cause was `FUN_00447d94` treating `/home/rgrabowski/Games/Ecstatica2/Files/ECSTATIC` as if it had an offset-index preamble; the file actually starts with flat `FANT` resources. `FUN_00447d94` now detects that layout, clears archive offset tables to `-1`, scans `0x19` scene records, and builds `0x650fa0` scene offsets by record id while leaving the old indexed path intact for non-flat archives. Probe logs now report `archive 47d94 flat FANT: scenes=1205 bytes=33075606`, and opcode-`0x4d` preloads install matching scene records such as `requested=2086/scepboms record=2086/scepboms`, `requested=2095/hbowl record=2095/hbowl`, and `requested=1560/necchest record=1560/necchest`; child-list walks now run instead of seeing zeroed slots. Follow-up generated repairs stabilized active scene-list normalization, scene cleanup context, scene activation, and actor/name lookup. Bounded gdb now reaches every startup action, reaches `mar:StartGame`, logs through `before-return`, and then survives until a forced interrupt in the frame path (`FUN_00426df8 -> FUN_0042a70c -> FUN_0041cf5c -> FUN_004620bb`). The current frontier is no longer a crash before `mar:StartGame`; it is that `mar:StartGame` still reports `_DAT_0073cc3c=0x0`, so the expected horseback/credits intro scene is not yet proven current.

## Next Implementation Step

Prove scene-current ownership after `mar:StartGame`, then compare the first post-startup visible route against E2WIN95's horseback/credits intro.

Scope for the next slice:

1. Trace the `mar:StartGame` `PlayScene "horse"` execution and confirm the repaired scene token path is still below `0x9c4`.
2. Keep the flat-FANT archive scan scoped to the scene-offset table; add other resource tables only when a real load proves they are needed.
3. Explain why `_DAT_0073cc3c` remains `0x0` through `mar:StartGame` `before-return`, or identify the recovered pointer that owns the active scene instead.
4. Compare the next visible scene against E2WIN95's horseback/credits intro before returning to page/front-buffer proof.
5. If no current scene is installed, preserve the frame-loop sample and name the next non-crash frontier with stack and action evidence.

Acceptance for the next slice:

1. Matching opcode-`0x4d` scene preloads remain intact and `mar:StartGame` still returns without crashing.
2. The `PlayScene "horse"` operand is resolved or the remaining remap failure is named with table index and lookup evidence.
3. The current scene pointer after `mar:StartGame` is installed, or the missing install path is named with stack and last successful action evidence.
4. F5/real-display startup no longer triggers the system "not responding" watchdog during the preload pass.
5. Any generated C repair is mirrored in `E2Recomp/tools/GenerateRecon.js` and regenerated.

## Change Log

### 2026-07-28

1. Created step.
2. Activated after SDL F5 stabilization classified the first frontier as DirectDraw page/palette/front-buffer fidelity.
3. Completed surface/page mapping and activated palette update-path recovery.
4. Completed palette update-path recovery and activated front-buffer presentation verification.
5. Recovered first post-logo actor live-position initialization enough for startup scene selection to advance from fallback scene `7` to scene `420`.
6. Preserved the world scene-selection grid across opcode-`0x4d` scene preloads, repaired post-scene-420 actor visibility child walks, and recovered `FUN_00424ed0` actor context enough for the dummy SDL runtime to stay alive past 30 seconds outside the sandbox.
7. Repaired the clean-build F5 startup regression by avoiding SDL-era stdio buffer allocation, caching Linux memory-map pointer checks with refresh-on-miss, and preserving actor-loop indices around the scene-change visibility passes.

### 2026-07-29

1. Repaired additional startup crash classes with mmap-backed compatibility allocation, fixed-slot actor-name copies, opcode-`0x4d` cursor preservation, and host event pumping during scene-preload restores.
2. Recovered the likely `PlayScene "horse"` remap failure class by using the full `20000` byte `_DAT_006366bc` scene-name table capacity.
3. Recorded the next active frontier: the SDL route survives to timeout but does not reach `mar:StartGame` within 60 seconds, so startup action/preload progress must be mapped next.
4. Added narrow startup/action/preload diagnostics and proved `ken:StartUp` dispatches; the stall was inside opcode-`0x4d` preload work rather than before startup action execution.
5. Recovered flat-FANT scene-offset population for `Files/ECSTATIC`, verified matching requested/installed scene records through startup preloads, repaired scene-remove hidden context, and moved the active frontier to `FUN_0043aa98` list unlinking while loading scene id `1424`.
6. Stabilized scene removal/list cleanup, scene activation, and actor/name lookup enough for bounded SDL/gdb to reach `mar:StartGame` `before-return` and later interrupt in the frame loop; the remaining startup-parity frontier is scene-current ownership and the missing horseback/credits intro.
