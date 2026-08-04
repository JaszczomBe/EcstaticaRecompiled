# Expand Gameplay Control And Camera Proofs

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-08-04

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
2. `Space` reaches game state during the horseback/credits intro (`DAT_00636850=1`, `_DAT_00479e7a=1`) but does not skip the intro action. The intro actor action continues to natural completion.
3. Natural completion currently enters `FUN_0042a70c`'s dependency-action completion path, then dispatches an action table through `FUN_0044f2fc`/`FUN_0044f508`. The observed script opcode is `0x07`, and the runtime activates scene `7`.
4. Scene `7` then tries to load child actor `3853`; archive scans did not find actor `3853` as a standalone type-`0x08` flat-FANT actor record in `Files/ECSTATIC`. Treat this as a wrong transition or wrong dispatch context until original evidence says otherwise.
5. `Esc` reaches `FUN_00415d40`'s menu/requester branch, changes requester state, and now presents readable high-res requester contents. The verified intro menu shows `START GAME`, `SAVE GAME...`, `LOAD GAME...`, `SETTINGS...`, `QUIT`, and `CANCEL`.
6. A hand proof attempt in reconstructed C explored lost callback/action context around `FUN_0042b004`, `FUN_0042b338`, and `FUN_0042b880`. It may still be relevant for later action callbacks, but it did not explain the current first-intro `Space` failure because the observed intro path reaches completion without callback attachment evidence.
7. `scripts/run-e2-control-matrix.sh` proves four canonical gameplay movement controls in debug and ASan with zero startup-logo delay: `up`, `down`, `left`, and `right` each dispatch through the Win32 queue, reach gameplay-control state, set the expected movement vector and `_DAT_00479e78` direction, keep requester state clear, keep a nonzero scene pointer, and dump nonblank surface `3`.
8. Original-game modifier and utility-key reports are now represented in the probe parser: `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l` can be injected by name. Source/manual mapping says `Ctrl`+arrows attack, Left Alt+arrows dodge, `Ctrl`+Left Alt+arrows advanced attack, Left Shift jumps, Right Alt drops carried items, `S` quick-saves, `I` toggles the icon bar, `Return` opens the icon/status page, `Esc` opens menu or closes status/menu, and `Space` interacts. Task 03 should prove the reconstructed owner flags before wiring any unproven behavior.
9. Original-game menu testing showed the intro menu is mouse-only. The SDL backend now maps host mouse coordinates through the aspect-fit presentation rectangle, the Win32 shim preserves cursor position, and the reconstructed WndProc feeds requester mouse state. Bounded intro-menu click probes now route Settings to requester id `0x31`/state `2` and Load to requester id `0x29`/state `4` without crashing. A targeted Settings sequence probe selects item `0x643998` and toggles `settings.music=1`, proving at least one submenu row action beyond first-entry routing. Target-requester Esc probes for Settings and Load now close requester ids `0x31`/`0x29` with final `DAT_00636844=0` and `_DAT_00643650=0`. The raw surface dumps from these probes are nonblank but not yet useful as visual submenu screenshots, so treat the log state as the current proof.

## Acceptance Criteria

1. `Esc` during the horseback/credits intro either opens the expected menu contents or has a documented, source-backed requester content/presentation frontier. Completed 2026-08-04: `Esc` opens readable requester contents in the bounded SDL dump.
2. `Space` during the horseback/credits intro either skips to the expected next sequence/gameplay state or has a documented, source-backed action-dispatch frontier.
3. After the intro-specific blocker is resolved or split, multiple movement/action keys reach gameplay state. Completed 2026-08-04 for four canonical arrow movement controls.
4. Probes record the relevant state deltas. Completed 2026-08-04 for the movement matrix.
5. New crashes are classified as separate runtime frontiers.

## Verification

1. Intro `Esc`/`Space` key-sequence probes.
2. Gameplay key-sequence probes.
3. Default runtime regression script.
4. SDL F5 smoke check when controls affect presentation.

## Notes

Task 02 completed the compact arrow movement matrix and corrected the host translation that had made physical arrows look like numpad keys. Carry `Space` as a narrower action-dispatch/completion frontier: it is delivered and latched, but the intro action still completes naturally and dispatches opcode `0x07` into scene `7`. Task 03 should compare SDL/default backend behavior and decide whether the next owned frontier is camera/action/modifier-state proof or the intro-completion scene-current split.

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
