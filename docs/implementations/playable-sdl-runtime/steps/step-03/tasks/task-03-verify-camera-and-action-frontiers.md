# Verify Camera And Action Frontiers

Status: active
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-08-17

## Goal

Classify what camera/action behavior is reachable after the control matrix lands.

## Scope

1. Run the control matrix against SDL and default builds.
2. Identify action/camera state changes or the next blocking crash.
3. Record a concise next frontier.

## Subtasks

1. Compare debug and ASan probe output.
2. Compare SDL and default backend behavior when presentation is active.
3. Capture call stacks for any new crash.
4. Update the step with accepted controls and remaining unknowns.
5. Prove the original mouse-only intro menu route before treating keyboard menu behavior as missing.

## Out Of Scope

1. Fixing every action-system crash.
2. Combat or inventory fidelity.

## Implementation Notes

This closeout should keep the next action crisp: either continue control fidelity or split to a specific runtime crash repair.

Current pre-closeout frontier: `Space` during the intro latches in game state but natural-completes into scene `7` and missing actor `3853`; `Esc` enters requester/menu state and presents readable requester contents. Original-game testing showed the intro menu does not respond to keyboard navigation, so this task now carries the mouse path as the menu-control proof. `--inject-intro-menu-click-surfaces /tmp/e2-menu-settings 320 225 6 3` reaches requester id `0x31` and then clears the consumed menu decision state back to `0`; `--inject-intro-menu-click-surfaces /tmp/e2-menu-load 320 203 6 3` does the same after reaching requester id `0x29`. The Settings requester row/action chain is now reconstructed enough for a targeted two-click proof: `--inject-intro-menu-click-sequence-surfaces /tmp/e2-settings-music-final '320,225;320,203' 6 1 250 0x31` records `actions 0->2`, selects item `0x643998`, ends with `settings.music=1`, and clears `_DAT_00643650=0`.

Original-game intro progression, recorded from manual reference: after the three logos, the first engine scene shows two people riding on horseback toward the castle. At the castle gate one person is captured and the other is knocked down by flying beings. This first intro scene lasts roughly 30-40 seconds and can either be skipped with `Space` or allowed to finish. The next brief sub-intro shows the main character bound to a pedestal; lightning strikes, and the character breaks free. This sub-intro lasts roughly 10 seconds and should be waited out. Proper controllable gameplay begins after that sub-intro finishes. The rebuilt runtime currently shows only a static first intro image, does not animate/process through both scenes, and `Space` does not skip the first intro. For playable-runtime purposes, prefer recovering the fastest original gameplay route before investing in full first-intro animation fidelity: make `Space` advance from the first intro into the pedestal/lightning sub-intro, then let that sub-intro complete naturally into gameplay.

The latest manual real-SDL menu issue covered visual artifacts plus intro action routing: main-menu requester rectangles smeared across the frame, Start Game crashed in `FUN_0043a39c` when `DAT_0047a470` was stale, Save blinked despite being unavailable in intro, Load left a malformed surface, and Settings rows/OK did not respond. The current narrow fix set guards the Start Game actor flag write, routes high-res requester panel/item fill and borders through explicit hosted rectangle bounds on both high-res pages, anchors the selected-character repaint to the computed text x-coordinate, makes Save use `action.save_disabled_intro` without changing gameplay Save, carries requester mouse state through a real `mouse_state` local, and gives Settings OK an explicit close action. Follow-up menu diagnostics showed disabled Save must stay in the active main menu, not close it: requester `0x28` now consumes only disabled Save directly, leaves `_DAT_00643650=5`, and lets normal main-menu actions fall through to the recovered modal loop. Submenu entry now passes explicit requester records into `FUN_0043b384`: Settings uses `0x0047a668`, while Load/Save initializes and passes `0x0047a5a4` with the larger `0xf0 x 0xb4` slot-list dimensions. The newest visual lifecycle repair adds a high-res requester backdrop stack and opens Settings/Load as nested modal requesters over active requester `0x28`, so submenu close restores the main-menu backdrop and main-menu close restores the intro frame. Bounded proofs now show Start during intro routes through `action.restart_intro` and `action.restart_intro_complete` without crashing, two-Esc main-menu open/close restores the intro surface (`hash=44b33248`) with `_DAT_00643650=0`, Settings Music dispatches item `0x643998` and flips `settings.music=1`, and Settings OK logs `action.settings_ok old=2 new=0` followed by `action.settings_return old=0 new=5` with a restored main-menu dump (`hash=6e4e9abb`). The 2026-08-17 manual pass confirmed three logos display in order and the menu is basically reachable, but also confirmed the intro sequence remains static, Quit/Settings/Load have missing/wrong labels or rough placement, Save shows nothing during intro, and Load slot clicks closed the menu. The latest repair maps fixed-address requester labels `0x00473298`/`0x004732a4`/`0x004732a8` to `OK`/`Yes`/`No`, redraws Settings rows after toggles, names Load/Save slot actions, consumes Load/Save slot clicks without closing requester `0x29`/`0x2a`, and logs requester `0x28` bounds. Load still has title/slot overlap and a left black rectangle, and the hosted font/color/layout is still approximate. A whole-file generator run is now part of the verification flow; keep generated C/H changes mirrored by `E2Recomp/tools/GenerateRecon.js`.

The next implementation continuation should treat manual SDL as a visual/fidelity check rather than an input-delivery check. For intro progression, focus first on the fastest original route: identify the state/scene/action entered by first-intro `Space` skip, verify or recover the pedestal/lightning sub-intro, then wait for that sub-intro to complete into controllable gameplay. Do not shortcut `Space` directly to final gameplay unless a temporary diagnostic bypass is explicitly marked as such. Continue Load title/slot/OK behavior and then requester surface/font/color/layout fidelity only if menu usability is blocking this probe. Save should be classified against original intro behavior before making it visible. Full first-intro animation/progression fidelity should be split from the gameplay-entry repair once the skip-to-sub-intro and sub-intro-to-gameplay destinations are understood.

Task 02 added a deterministic movement matrix for canonical Ecstatica II arrow controls: `up`, `down`, `left`, and `right` in debug and ASan. Original-game modifier/utility reports are parser-visible as `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; source/manual mapping says arrows move, `Ctrl`+arrows attack, Left Alt+arrows dodge, `Ctrl`+Left Alt+arrows advanced attack, Left Shift jumps, Right Alt drops carried items, `Space` interacts, `Return` opens the icon/status page, `Esc` opens menu or closes status/menu, `S` quick-saves, and `I` toggles the icon bar. Do not close this step until the camera/action/modifier owner layer is recorded and the intro `Space` split is either repaired or deliberately carried as a source-backed follow-up.

## Acceptance Criteria

1. Accepted controls are listed.
2. Remaining frontier has a command and owner layer.
3. Mouse-only menu controls have bounded probe evidence for at least the first submenu layer.

## Verification

1. Control matrix probes.
2. Runtime regression script.
3. Manual SDL F5 smoke check if the route is stable.

## Review State

1. Planning state: discussed
2. Implementation state: active
3. Notes: Final task for Step 3; the freshest sub-slice is now intro gameplay-entry recovery, with requester visual/slot behavior still pending but lower priority unless it blocks probes. Use the corrected fastest original sequence as the target: first-intro `Space` skip, wait through the pedestal/lightning sub-intro, then controllable gameplay. Once that route is recovered, resume the original camera/action/modifier classification from the completed arrow movement matrix and decide whether to split full first-intro animation fidelity. Classify `Ctrl`/`Shift`/`Left Alt`/`Right Alt`, `Return`, `S`, `I`, and any version-specific `L` quickload report before wiring unproven gameplay behavior.

## Change Log

### 2026-07-28

1. Created task.

### 2026-07-31

1. Added the current intro action/requester frontier as the required pre-closeout evidence.

### 2026-08-04

1. Activated after Task 02 landed `scripts/run-e2-control-matrix.sh` and proved four canonical arrow movement controls in debug and ASan.
2. Added the menu-control sub-slice after original screenshots/testing showed the intro menu is mouse-only. Bounded SDL probes now prove Settings and Load submenu entry through mouse events, while the visual surface dump remains a diagnostic artifact rather than a faithful screenshot proof.
3. Extended the menu-control proof into the Settings submenu: the targeted sequence probe opens Settings and toggles Music through row item `0x643998`.
4. Cleared consumed menu decision states after Settings/Load/Cancel paths so requester state returns to `0` instead of repeatedly redrawing/blinking.
5. Split Escape routing by requester context and added target-requester Esc probes; Settings and Load submenu close paths now finish with `DAT_00636844=0` and `_DAT_00643650=0`.
6. Repaired the manual intro requester repro: guarded the stale-current Start Game crash, replaced high-res requester fill/border hidden-register usage with explicit hosted rectangles, fixed selected-character repaint placement, made Save inert in intro, and proved Settings row/OK dispatch with bounded dummy-SDL probes. Follow-up menu diagnostics now prove disabled Save is consumed without closing requester `0x28`, normal main-menu clicks still fall through to the recovered modal loop, and a second Escape closes active requester `0x28`.
7. Fixed the no-submenu regression by replacing stale hidden-register `FUN_0043b384` calls with explicit requester records for Settings and Load/Save. Load/Save now uses slot-list dimensions and is visible/framed in bounded dumps, with title/slot overlap and the left black rectangle still owning the slot canvas/OK frontier.
8. Fixed the remaining modal-close regression: close actions now flip `_DAT_006443d0` so `FUN_0043b384` unwinds immediately, main-menu Escape returns cancel state `5` before `15d40.menu_complete` clears it, Settings OK closes without a follow-up click, and Start during intro routes to `action.restart_intro` instead of gameplay StartGame.
9. Fixed stale visible requester layers by saving/restoring high-res requester backdrops and keeping Settings/Load nested over the active main menu. Two-Esc now restores the intro surface, Settings row clicks work in the nested requester, and Settings OK restores the main menu instead of leaving the Settings panel underneath.

### 2026-08-17

1. Recorded the user's real-SDL baseline: the logo sequence is correct, intro animation/progression is still static, main menu Esc/Cancel basically work, Quit/Settings/Load are visually/control rough, Save is inert, and some labels/layout/colors are wrong.
2. Fixed fixed-address requester labels for `OK`, `Yes`, and `No`; Settings rows now redraw after in-place toggles; Load/Save slot actions are named and consumed without closing the active requester.
3. Verified `linux-clang32-sdl-debug` dummy-SDL probes for Settings Music, Settings OK, Load slot selection, Quit Yes, and Quit No. `ctest --preset linux-clang32-sdl-debug` was attempted but no such test preset exists.
4. Corrected the original intro progression target: the first horseback/castle intro lasts roughly 30-40 seconds and can be skipped with `Space`; the following pedestal/lightning sub-intro lasts roughly 10 seconds and should be waited out; proper gameplay begins after that sub-intro finishes.
