# Recover DirectDraw Page And Palette Semantics

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

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

## Change Log

### 2026-07-28

1. Created step.
2. Activated after SDL F5 stabilization classified the first frontier as DirectDraw page/palette/front-buffer fidelity.
3. Completed surface/page mapping and activated palette update-path recovery.
4. Completed palette update-path recovery and activated front-buffer presentation verification.
5. Recovered first post-logo actor live-position initialization enough for startup scene selection to advance from fallback scene `7` to scene `420`.
6. Preserved the world scene-selection grid across opcode-`0x4d` scene preloads, repaired post-scene-420 actor visibility child walks, and recovered `FUN_00424ed0` actor context enough for the dummy SDL runtime to stay alive past 30 seconds outside the sandbox.
7. Repaired the clean-build F5 startup regression by avoiding SDL-era stdio buffer allocation, caching Linux memory-map pointer checks with refresh-on-miss, and preserving actor-loop indices around the scene-change visibility passes.
