# Expand Gameplay Control And Camera Proofs

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-08-18

## Goal

Grow the current single movement-latch proof into a compact gameplay-control matrix covering movement, action, cancel/menu, and camera-adjacent state.

## Why This Step Exists

The reconstructed runtime originally proved movement with a `num8` probe, but Ecstatica II's manual and original-game testing show that cursor keys are the canonical movement controls. A playable runtime needs confidence that the arrow keys and their modifier actions survive the Win32 queue, legacy key state, and gameplay-state transitions.

The immediate blocker is earlier than the planned broad matrix: during the horseback/credits intro, SDL input reaches the reconstructed window procedure and key globals, but `Esc` and `Space` do not produce the expected visible behavior. This step remains the owner because the fault is now inside reconstructed control/state consumption rather than the SDL host event bridge.

## Scope

1. Map current gameplay input globals and key queues.
2. Add bounded probes for several control paths.
3. Record camera/control state that changes in response to input.
4. First classify the intro `Esc`/`Space` response path before expanding the matrix.

## Out Of Scope

1. Full key rebinding.
2. Controller support.
3. Combat or inventory systems.

## Usage Budget

Keep this to a small input matrix. Split when a single key uncovers a new parser or actor crash family.

## Temporary Sacrifices

1. Sacrifice: Use scripted probes before broad manual play.
2. Why accepted now: Scripted keys give repeatable proof while runtime stability is still moving.
3. Removal trigger: Interactive play is stable enough for longer manual sessions.

## Tasks

1. [Map Gameplay Input State](tasks/task-01-map-gameplay-input-state.md) - completed; intro `Esc`/`Space` state is mapped, `Esc` requester presentation is readable, and `Space` is split to the action-dispatch frontier.
2. [Add Control Probe Matrix](tasks/task-02-add-control-probe-matrix.md) - completed; debug and ASan now assert canonical arrow movement: `up`, `down`, `left`, and `right`.
3. [Verify Camera And Action Frontiers](tasks/task-03-verify-camera-and-action-frontiers.md) - active.

## Current Findings

1. Host input delivery is not the current blocker. SDL window controls, keydown/keyup events, and Win32-style `WM_KEYDOWN`/`WM_KEYUP` dispatch reach the reconstructed window procedure.
2. `Space` reaches game state during the horseback/credits intro (`DAT_00636850=1`, `_DAT_00479e7a=1`) and now skips the first intro when the current actor belongs to the `horse` scene record. The bounded proof logs `horse_scene=1564`, `actor_scene_id=1564`, and loads `Start_sc` scene id `0`.
3. `Space` during the following `Start_sc` pedestal/lightning sub-intro is intentionally wait-only: the skip hook consumes the latched key with or without an active current actor and logs `intro skip ignored wait-only subintro`.
4. `Start_sc` now runs to completion and hands off into controllable gameplay. The repaired scene lookup selects descriptor `48771`, scene id `87`, opens `hires\0087.raw`, and a delayed `Up` key in scene pointer `0x67d0ac` ends with `move=[1,0,0,0,0,0,0,0,0]`. Full horseback animation/procession fidelity remains separate from this fastest-route proof.
5. `Esc` reaches `FUN_00415d40`'s menu/requester branch, changes requester state, and now presents readable high-res requester contents. The verified intro menu shows `START GAME`, `SAVE GAME...`, `LOAD GAME...`, `SETTINGS...`, `QUIT`, and `CANCEL`.
6. A hand proof attempt in reconstructed C explored lost callback/action context around `FUN_0042b004`, `FUN_0042b338`, and `FUN_0042b880`. It may still be relevant for later action callbacks, but it did not explain the current first-intro `Space` failure because the observed intro path reaches completion without callback attachment evidence.
7. `scripts/run-e2-control-matrix.sh` proves four canonical gameplay movement controls in debug and ASan with zero startup-logo delay: `up`, `down`, `left`, and `right` each dispatch through the Win32 queue, reach gameplay-control state, set the expected movement vector and `_DAT_00479e78` direction, keep requester state clear, keep a nonzero scene pointer, and dump nonblank surface `3`.
8. Original-game modifier and utility-key reports are now represented in the probe parser: `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l` can be injected by name. Source/manual mapping says `Ctrl`+arrows attack, Left Alt+arrows dodge, `Ctrl`+Left Alt+arrows advanced attack, Left Shift jumps, Right Alt drops carried items, `S` quick-saves, `I` toggles the icon bar, `Return` opens the icon/status page, `Esc` opens menu or closes status/menu, and `Space` interacts. Task 03 should prove the reconstructed owner flags before wiring any unproven behavior.
9. Original-game menu testing showed the intro menu is mouse-only. The SDL backend now maps host mouse coordinates through the aspect-fit presentation rectangle, the Win32 shim preserves cursor position, and the reconstructed WndProc feeds requester mouse state. Bounded intro-menu click probes now route Settings to requester id `0x31`/state `2` and Load to requester id `0x29`/state `4` without crashing. A targeted Settings sequence probe selects item `0x643998` and toggles `settings.music=1`, proving at least one submenu row action beyond first-entry routing. Target-requester Esc probes for Settings and Load now close requester ids `0x31`/`0x29` with final `DAT_00636844=0` and `_DAT_00643650=0`. The manual artifact/crash repro is now covered by a narrow fix set: Start Game guards stale `DAT_0047a470`, high-res requester rectangles use explicit hosted bounds on both high-res pages, disabled Save is consumed without closing requester `0x28`, normal main-menu actions fall through to the recovered modal loop, main-menu Escape now returns cancel state `5` and unwinds through `15d40.menu_complete`, and Settings Music/OK dispatch in bounded probes. Settings and Load/Save submenu entry now pass explicit requester records into `FUN_0043b384`; Load/Save uses a widened slot-list record (`0xf0 x 0xb4`) so the submenu is visible and framed. A high-res requester backdrop stack now restores the intro frame after main-menu close and restores the main menu after Settings/Load close; Settings/Load open as nested modal requesters over requester `0x28`. The 2026-08-17 manual pass confirmed the remaining user-facing issues: intro playback is static after the logo sequence, Quit prompt and Settings/Load surfaces are rough, Save is inert, several labels/layouts are wrong, and Load clicks closed the requester. The latest generated repair resolves the blank fixed-address labels for `OK`/`Yes`/`No`, redraws Settings row changes immediately, consumes Load/Save slot-row clicks as selection instead of close, and logs main-menu requester bounds. Start during intro now routes to `action.restart_intro` instead of gameplay StartGame. The corrected fastest original route is: skip the first 30-40 second horseback/castle intro with `Space`, then wait roughly 10 seconds for the pedestal/lightning sub-intro to finish, then enter controllable gameplay. Load title/slot overlap, the left black rectangle, modal-over-main-menu artifacts, and hosted font/color fidelity remain the next menu visual frontier.

## Acceptance Criteria

1. `Esc` during the horseback/credits intro either opens the expected menu contents or has a documented, source-backed requester content/presentation frontier. Completed 2026-08-04: `Esc` opens readable requester contents in the bounded SDL dump.
2. `Space` during the horseback/credits intro either skips to the expected next sequence/gameplay state or has a documented, source-backed action-dispatch frontier. Completed 2026-08-18: first-intro `Space` enters `Start_sc`, `Start_sc` completes into scene `87`, and delayed `Up` movement latches afterward.
3. After the intro-specific blocker is resolved or split, multiple movement/action keys reach gameplay state. Completed 2026-08-04 for four canonical arrow movement controls.
4. Probes record the relevant state deltas. Completed 2026-08-04 for the movement matrix.
5. New crashes are classified as separate runtime frontiers.

## Verification

1. Intro `Esc`/`Space` key-sequence probes.
2. Gameplay key-sequence probes.
3. Default runtime regression script.
4. SDL F5 smoke check when controls affect presentation.

## Notes

Task 02 completed the compact arrow movement matrix and corrected the host translation that had made physical arrows look like numpad keys. The fastest original gameplay route is now proven: first-intro `Space` skips into `Start_sc`, Space during the pedestal/lightning sub-intro is consumed and ignored, the sub-intro completes into scene `87`, and delayed `Up` movement latches. Task 03's freshest direction can return to camera/action/modifier classification and requester visual polish; full first-intro animation fidelity remains a separate follow-up.

## Change Log

### 2026-07-28

1. Created step.

### 2026-07-31

1. Activated the step around the user-reported intro control blocker.
2. Reclassified the failure from SDL input delivery to reconstructed game-state consumption and presentation: `Space` latches but does not skip; `Esc` reaches requester state and shows broken menu contents.
3. Recorded the current wrong-transition evidence: horseback intro actor `0` completes action `0x937800`, dispatches opcode `0x07`, activates scene `7`, and then fails to load missing child actor `3853`.

### 2026-08-04

1. Completed Task 01's input-state mapping slice: `Esc` requester presentation is fixed and proven by `/tmp/e2-step03-escape-labels-final-s2.ppm` (`hash=8f4ff5bf`), while `Space` remains a documented action-dispatch frontier.
2. Activated Task 02 for the compact gameplay control probe matrix, with the full debug/ASan regression wrapper caveat carried in the parent implementation document.
3. Completed Task 02 by adding `scripts/run-e2-control-matrix.sh`; all debug and ASan rows for `up`, `down`, `left`, and `right` pass against the expected movement vectors and surface proof.
4. Activated Task 03 to verify camera/action frontiers and compare SDL/default backend behavior.
5. Corrected the matrix and host input translation after original-game/manual evidence showed Ecstatica II does not use numpad movement. Probe aliases now exist for `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; Task 03 still owns modifier/status/save/load classification.
6. Advanced Task 03's menu-control slice: added a bounded intro-menu mouse-click probe, restored requester mouse-action dispatch through recovered action ids, and proved Settings and Load submenu entry by requester state/id instead of keyboard navigation.
7. Added the Settings requester row/action chain and a targeted sequence probe; the Music row proof dispatches through item `0x643998` and changes `settings.music` to `1`.
8. Added target-requester Esc close proofs for Settings and Load, while carrying manual real-SDL blink confirmation and requester visual fidelity as the next menu frontiers.
9. Repaired the reported intro requester artifact/crash path: hosted rectangle fills/borders no longer use stale hidden coordinates, Start Game no longer dereferences a stale current actor pointer, disabled Save is consumed without closing the active main menu, a second Escape closes requester `0x28`, and Settings rows/OK dispatch in bounded probes.
10. Fixed the submenu regression by passing explicit requester records into `FUN_0043b384` for Settings and Load/Save. The Load/Save record now uses the slot-list dimensions required by its child rows; bounded dumps show the submenu visible and framed, with title/slot overlap and a left black rectangle still pending.
11. Fixed the remaining menu-close/Start regression: close actions flip the requester modal-loop flag, main-menu Escape returns cancel state `5` before `15d40.menu_complete` clears it, Settings OK closes without waiting for another event, and Start during intro resets the intro action path instead of entering gameplay StartGame.
12. Fixed the stale requester visual stack: high-res requester entry saves/restores surface backdrops, Settings/Load open as nested requesters over the active main menu, target-requester probes feed submenu clicks again, and restored main-menu dumps redraw final hosted labels.

### 2026-08-17

1. Recorded the manual real-SDL baseline: three startup logos show in the expected order, the intro is still static, main menu Esc/Cancel basically work, Quit/Settings/Load have label/layout/control issues, and Save is inert during intro.
2. Repaired fixed-address requester labels for `OK`, `Yes`, and `No`; Settings rows now redraw after toggles; Load/Save slot actions are diagnosed as `load_slot`/`save_slot` and consumed without closing the active requester.
3. Added requester `0x28` layout logging and verified focused dummy-SDL probes for Settings Music, Settings OK, Load slot selection, Quit Yes, and Quit No.
4. Corrected the original playable-intro target: the fastest route is first-intro `Space` skip, then waiting for the roughly 10 second pedestal/lightning sub-intro to finish before gameplay. Full first-intro animation/procession remains fidelity work.

### 2026-08-18

1. Repaired first-intro `Space` skip for the scene-child action wrapper: the hook recognizes actor scene `horse` id `1564` and loads `Start_sc` id `0`.
2. Repaired the post-skip crash chain by fixing scene-child allocation, preserving action-event/actor context, adding an RNG seed fallback, and recovering the `FUN_0042b880` subcase-`5` sound id from the event record.
3. Added wait-only sub-intro consumption so Space during `Start_sc` clears `DAT_00636850` without requesting another transition.
4. Recovered the post-`Start_sc` handoff by copying scene-child actor live vectors and restoring signed-byte scene-height lookup semantics; the delayed `Up` proof reaches scene `0x67d0ac` and movement vector `[1,0,0,0,0,0,0,0,0]`.
