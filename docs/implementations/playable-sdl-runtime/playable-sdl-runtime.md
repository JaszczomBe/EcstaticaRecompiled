# Playable SDL Runtime

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-08-17
Parent Plan: [Runtime Milestones](../../plans/runtime-milestones.md)

## Goal

Turn the reconstructed Ecstatica II Linux runtime from a proven first-gameplay/live-frame milestone into a practical SDL-backed developer runtime that can be launched, observed, controlled, debugged, and improved through repeatable bounded checks.

## Scope

1. Interactive SDL F5 stability and crash-frontier triage.
2. DirectDraw page, palette, and front-buffer fidelity.
3. Gameplay input, camera, and control-state proof expansion.
4. Runtime timing and frame pacing ownership.
5. Initial DirectSound/audio compatibility boundary.
6. Repeatable developer bootstrap, launch, and validation workflow.

## Non-Goals

1. Shipping a polished multi-platform release.
2. Replacing original-shaped reconstructed game logic with host-library shortcuts.
3. Pixel-perfect rendering or full audio fidelity in the first pass.
4. Removing 32-bit/fixed-address assumptions before they are mapped.
5. Broad generated-file churn outside focused, Ghidra-backed repairs.

## Current Baseline

The completed [Run Reconstructed E2 On Linux](../linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) implementation proves the first runtime horizon:

1. Original Ecstatica II data loads from `/home/rgrabowski/Games/Ecstatica2/`.
2. The reconstructed main loop survives under debug and ASan probes.
3. Menu input reaches requester navigation and Start Game.
4. Gameplay control-ready probes reach `_DAT_00643650=0`, `_DAT_0073cc3c=0x681d04`, nonblank surface 3 `hash=6e39f5ea`, and `move=[1,0,0,0,0,0,0,0,0]`.
5. Host window/input/presentation behavior is isolated behind a backend boundary.
6. SDL 3.4.12 is vendored under `dep/SDL`.
7. The SDL backend receives real recovered `640x480` runtime frames from recovered front surface `3` in hires/full-frame mode.
8. The SDL backend aspect-fits those frames into the host window instead of stretching them; a `640x640` host surface now presents the game at centered `640x480`.
9. VS Code exposes `Ecstatica Recompiled (SDL)` for the live-presentation backend.

## Step Roadmap

Each step should be small enough for a single context window. If a step starts collecting unrelated fixes, split it before implementation continues.

1. [Stabilize Interactive SDL F5 Runtime](steps/step-01/step-01-stabilize-interactive-sdl-f5-runtime.md) - completed; captured the user's F5 behavior, reproduced the stable SDL boundary, and classified the first frontier as DirectDraw page/palette/front-buffer fidelity.
2. [Recover DirectDraw Page And Palette Semantics](steps/step-02/step-02-recover-directdraw-page-and-palette-semantics.md) - completed; recovered palette ownership and the hires/full-frame front-buffer source.
3. [Expand Gameplay Control And Camera Proofs](steps/step-03/step-03-expand-gameplay-control-and-camera-proofs.md) - active; intro `Esc` now reaches readable requester contents, the mouse-only intro menu can route clicks to Load and Settings, a bounded Settings submenu proof toggles Music through the reconstructed row/action chain, requester backdrop stacking restores main-menu/intro layers in bounded probes, four movement controls are covered by a debug/ASan matrix, and the next task is camera/action frontier verification while carrying the `Space` action-dispatch/completion split.
4. [Define Runtime Timing And Frame Pacing](steps/step-04/step-04-define-runtime-timing-and-frame-pacing.md) - planned; identify timing ownership and add a backend timing contract only where needed.
5. [Begin DirectSound Compatibility](steps/step-05/step-05-begin-directsound-compatibility.md) - planned; map startup sound behavior and define the first replaceable audio boundary.
6. [Package Reproducible Developer Runtime](steps/step-06/step-06-package-reproducible-developer-runtime.md) - planned; make clone/submodule/build/launch validation boring and repeatable.

## Active Frontier

The current user-facing target is E2WIN95 startup-sequence parity, not only palette or front-buffer selection. The expected reference path is:

1. Psygnosis logo.
2. Andrew Spencer Studios logo.
3. Ecstatica II loading/logo screen.
4. First engine intro scene: two people ride on horseback toward the castle; at the castle gate one is captured and the other is knocked down by flying beings. This scene lasts roughly 30-40 seconds.
5. The first intro scene can be skipped with `Space`, or it can run to natural completion.
6. Second brief intro/sub-intro scene: the main character is bound to a pedestal, lightning strikes, and the character breaks free. This scene lasts roughly 10 seconds and should be waited out rather than skipped.
7. Proper gameplay begins with normal controls after the sub-intro finishes.
8. `Esc` can enter the menu during the intro; `Space` should advance toward the gameplay path.

Current rebuilt SDL behavior has advanced past several crash boundaries, but it still does not match that sequence. Startup diagnostics now prove the route finds and dispatches `ken:StartUp`, and `FUN_00447d94` now recognizes the flat `FANT` layout in `Files/ECSTATIC` instead of treating it as an offset-indexed archive. The flat-FANT scan populates the scene offset table at `0x650fa0`, so opcode-`0x4d` preloads install matching scene records and child-list passes execute instead of walking empty table slots. Follow-up generated repairs stabilized scene removal/list cleanup, scene activation, and actor/name lookup; bounded SDL/gdb now reaches all startup actions, reaches `mar:StartGame`, logs through `before-return`, and then survives until the frame loop. The pragmatic next priority is to recover the fastest valid gameplay route: skip the first long intro with `Space`, then let the second pedestal/lightning sub-intro finish naturally and enter proper gameplay. Full animated first-intro fidelity can follow once that route is understood.

The Step 2 DirectDraw-facing presentation frontier is closed. Original `E2WIN95.EXE` disassembly around `FUN_0043acec` maps surfaces `0/1/2` to the low VGA-style pages and surface `3` to the full `640x480` raw frame buffer. The host presenter now recovers surface `3` as the front source whenever `DAT_0047a43c != 0`, logs both `front` and `visible`, and only falls back to the old nonblank scan if the recovered front is unreadable or blank. A dummy-SDL probe reports `selected=3 front=3 visible=0 hires=4`, dump state `front=3 visible=1`, scene palette hash `de4e4c5d`, and nonblank surface `3` hash `44b33248`, matching the stable horseback/credits intro frame family.

The SDL backend now preserves the source frame aspect ratio during the final host-window blit. This keeps the recovered `640x480` frame centered inside the original-shaped `640x640` top-level window instead of stretching it to the full surface. With `E2R_PRESENT_DIAG=1`, a dummy-SDL check reports `host backend present rect: src=640x480 window=640x640 dst=0,80 640x480`.

The current active blocker is no longer SDL event delivery. Window events, keydown/keyup events, mouse motion/button events, and Win32-style message dispatch reach the reconstructed window procedure. During the horseback/credits intro, `Space` reaches the game input state (`DAT_00636850=1`, `_DAT_00479e7a=1`) but does not skip the intro action; the action instead completes naturally, then dispatches script opcode `0x07` into scene `7`, whose child actor `3853` is not present as a standalone flat-FANT actor record in `Files/ECSTATIC`. A manual real-SDL pass on 2026-08-17 confirmed startup now shows the Psygnosis logo, Andrew Spencer Studios logo, and Ecstatica II title/loading screen, then reaches a static intro scene without animated characters or scene progression. `Esc` reaches the menu/requester branch in `FUN_00415d40` and now presents readable requester contents: `START GAME`, `SAVE GAME...`, `LOAD GAME...`, `SETTINGS...`, `QUIT`, and `CANCEL`. Original testing showed the intro menu is mouse-only, so the current proof follows that route: bounded SDL probes inject an intro `Esc`, then Win32 mouse clicks. Settings reaches requester id `0x31` with state `2`, Load reaches requester id `0x29` with state `4` without crashing, a targeted two-click Settings proof selects item `0x643998` and toggles `settings.music` from `0` to `1`, Settings OK returns to the main menu, and Quit Yes/No now draw fallback labels and route to confirm/cancel. The latest repair also redraws Settings row toggles in place, consumes Load/Save slot-row clicks as `load_slot`/`save_slot` selection instead of closing the requester, consumes disabled Save without closing active requester `0x28`, keeps Settings/Load as nested modal requesters over the active main menu, restores high-res requester backdrops when submenus or the main menu close, returns active main-menu Escape as cancel state `5` before `15d40.menu_complete` clears it, routes Start during intro through `action.restart_intro`, and passes explicit requester records to `FUN_0043b384` for Settings and Load/Save so submenus actually draw. The widened Load/Save slot-list record now frames its children instead of spilling across the screen, but title/slot overlap, the left black save-location rectangle, modal-over-main-menu artifacts, and hosted font/color/layout fidelity remain visual frontiers. The Ecstatica II manual mapping uses cursor keys for movement, not numpad; `scripts/run-e2-control-matrix.sh` now proves the four canonical arrow movement controls in debug and ASan: `up`, `down`, `left`, and `right`. Treat later control work as camera/action/modifier frontier verification while carrying the `Space` action-dispatch/completion split, not host input plumbing.

The default regression wrapper is not currently green. Debug still satisfies the gameplay-control gate. ASan no longer crashes in the latest `FUN_00423858` actor-transform child-chain frontier and still reaches StartGame entry, `DAT_00479de8=1`, `DAT_0047a76c=1`, requester state clear, movement latch `move=[1,0,0,0,0,0,0,0,0]`, and nonblank surface `3`, but the bounded wrapper rejects the run because `_DAT_0073cc3c` stays `0x0` after the scene-`7`/actor-`3853` transition. Keep that as a regression-wrapper caveat for Task 03 instead of treating the full wrapper as green.

## Invariants

1. Keep SDL below the host backend; reconstructed C must not call SDL directly.
2. Keep the default debug route available until SDL is intentionally promoted to default.
3. Treat visual/audio fidelity fixes as compatibility semantics unless original logic evidence says otherwise.
4. Mirror durable reconstructed fixes in `E2Recomp/tools/GenerateRecon.js`.
5. Record every new crash frontier with command, call stack, last useful proof line, and regression impact.
6. Prefer bounded probes that terminate automatically; manual F5 findings should become reproducible commands when feasible.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. `cmake --build --preset linux-clang32-sdl-debug`
4. `scripts/run-e2-runtime-regressions.sh`
5. SDL backend probes relevant to the active step.
6. Manual VS Code F5 check when a step changes interactive behavior.
7. `git diff --check`

## Change Log

### 2026-07-28

1. Created implementation after the reconstructed-runtime plan reached first gameplay, live SDL presentation, and an SDL F5 launch route.
2. Completed Step 1 with a stable SDL F5/no-crash boundary and activated DirectDraw page/palette/front-buffer recovery.
3. Step 2 advanced post-logo startup scene selection by initializing archive-loaded actor live positions through the original `FUN_0044146c` helper.

### 2026-07-29

1. Reframed the active frontier around E2WIN95 startup-sequence parity after palette recovery proved the logo colors but F5 still skipped the Psygnosis/Andrew Spencer screens and entered the wrong scene/stall path.
2. Recorded the latest bounded result: SDL startup survives to timeout after archive load with crash fixes applied, but does not reach `mar:StartGame` or the expected horseback intro yet.
3. Recovered flat-FANT startup preloads by scanning `Files/ECSTATIC` scene records into `0x650fa0`; opcode-`0x4d` now installs requested scene ids, and the active crash frontier moved to `FUN_0043aa98` scene-removal/list unlinking while loading scene id `1424` before `mar:StartGame`.
4. Cleared the pre-`mar:StartGame` crash chain: bounded SDL/gdb reaches `mar:StartGame` `before-return` and later interrupts in the frame loop. The active frontier is now scene-current ownership and the missing horseback/credits intro route.
5. Repaired generated opcode `0x07`/`0x0c` scene activation to match original `E2WIN95.EXE` register flow by passing the loaded scene record into `FUN_004523f8`. The `horse` scene now activates, exposing the next non-crash frontier: empty actor/current ownership after activation.
6. Recovered flat-FANT actor offsets and hidden actor context through the `FUN_004523f8` activation pass. The normal route now loads actor `0` and reaches the frame loop with nonzero actor/current ownership; the next crash frontier is bogus raw-view/camera selection in the render epilogue.
7. Recovered raw-view scene id and palette filename construction for the render epilogue. Regenerated SDL debug probes now survive 30 frames after `mar:StartGame`, load `hires\1073.raw`, and dump nonblank surface 3; the active frontier moves back to visual/front-buffer parity.

### 2026-07-30

1. Completed DirectDraw front-buffer recovery: hires/full-frame presentation uses recovered surface `3`, with diagnostics reporting `front=3` and palette-applied surface hash `44b33248`.
2. Kept the default runtime regression green by adding generated ASan-safe repairs for surface blits, sparse original globals, raw-view path buffers, palette reads, cleanup marker helpers, and actor animation context.
3. Activated the next implementation step around gameplay control/camera proof expansion and remaining startup-logo timing parity.
4. Fixed the first-scene color mismatch reported by screenshot comparison by publishing `FUN_0044add8`'s freshly loaded `Views/1073.PA2` palette through `FUN_0041af88`; the scene dump now reports palette hash `de4e4c5d`.
5. Fixed the user-reported horizontal squeeze by making SDL presentation aspect-fit source frames instead of stretching `640x480` content to the full `640x640` host window.

### 2026-07-31

1. Reclassified the active input problem: SDL/window event delivery is proven, but intro `Esc`/`Space` game behavior is still wrong.
2. Recorded that `Space` latches in game state during the horseback/credits intro yet is not consumed as a skip; natural completion dispatches opcode `0x07` to scene `7`, which then tries to load missing actor `3853`.
3. Recorded that `Esc` enters the reconstructed menu/requester state path and shows a menu with broken contents, making requester drawing/content presentation the likely next proof area.
4. Paused broader runtime edits and generator work until the action-dispatch/requester-presentation cause is isolated with smaller evidence.

### 2026-08-04

1. Restored hosted high-res requester label visibility for the intro `Esc` path, including a conservative ASCII fallback renderer, requester-item text y-coordinate correction, and a final label redraw after item rectangles are painted.
2. Hardened SDL event polling against injected Win32 probe dispatch from a non-main thread; bounded probes now avoid the SDL main-thread assertion while still delivering queued keys.
3. Added a narrow `FUN_00423858` child/linked actor readability guard after the full wrapper exposed an ASan-only actor-transform crash; the wrapper now fails at the known ASan scene-control gate instead of a sanitizer report.
4. Completed Step 3 Task 01 and activated Task 02 for the compact control probe matrix, carrying the `Space` action-dispatch/completion frontier as the remaining intro-control split.
5. Added and passed `scripts/run-e2-control-matrix.sh`, then corrected it to the Ecstatica II manual mapping: arrow keys are canonical movement and numpad keys are not original controls.
6. Fixed SDL/X11 host key translation so physical arrows reach WndProc as `VK_UP`, `VK_DOWN`, `VK_LEFT`, and `VK_RIGHT` instead of masquerading as numpad keys. Added parser/scan coverage for `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; Task 03 owns modifier, status/icon, save/load behavior classification.
7. Added bounded intro-menu mouse-click probes and fixed the requester mouse path. `--inject-intro-menu-click-surfaces` now proves Settings (`320,225`) routes to requester id `0x31`/state `2`, and Load (`320,203`) routes to requester id `0x29`/state `4` without crashing. The sequence probe `--inject-intro-menu-click-sequence-surfaces` now proves the Settings Music row dispatches through item `0x643998` and flips `settings.music=1`, and its target-requester Esc mode proves Settings/Load submenu close paths finish with `DAT_00636844=0` and `_DAT_00643650=0`.
8. Repaired the manual intro-menu artifact/crash repro: Start Game now guards the stale-current actor write in `FUN_0043a39c` and routes to `action.restart_intro` during the intro, high-res requester panel/item rectangles draw from explicit hosted bounds instead of hidden-register coordinates, disabled Save is consumed without closing requester `0x28`, active main-menu Escape unwinds as cancel/no-selection, and Settings row/OK clicks dispatch in bounded probes. Submenu opening now passes explicit requester records for Settings and Load/Save; Load/Save uses the wider slot-list record so it is visible and framed, with title/slot overlap and the left black rectangle still pending. Keep manual real-SDL confirmation as the next acceptance check before moving on to Load slot/OK fidelity.

### 2026-08-17

1. Folded the latest manual real-SDL report into Task 03: startup logo order is now correct, the intro still lacks character animation/scene progression, main menu Esc/Cancel works basically, Quit/Settings/Load remain rough, and Save is inert in the intro menu.
2. Repaired requester label fallbacks for fixed-address `OK`, `Yes`, and `No` text, redraws Settings row toggles in place, names Load/Save slot actions in diagnostics, consumes slot-row clicks without closing the active Load/Save requester, and logs requester `0x28` item bounds for future probes.
3. Verified with `linux-clang32-sdl-debug` dummy-SDL probes: Settings Music toggles to `settings.music=1`, Settings OK returns to the main menu, Load slot clicks report `action_name=load_slot` while staying in requester `0x29`, Quit Yes exits cleanly, and Quit No returns to requester `0x28`.
