# Verify Camera And Action Frontiers

Status: active
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-08-04

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

Current pre-closeout frontier: `Space` during the intro latches in game state but natural-completes into scene `7` and missing actor `3853`; `Esc` enters requester/menu state and presents readable requester contents. Original-game testing showed the intro menu does not respond to keyboard navigation, so this task now carries the mouse path as the menu-control proof. `--inject-intro-menu-click-surfaces /tmp/e2-menu-settings 320 225 6 3` reaches requester id `0x31` with state `2`, and `--inject-intro-menu-click-surfaces /tmp/e2-menu-load 320 203 6 3` reaches requester id `0x29` with state `4`; both record one requester action and exit cleanly. Task 02 added a deterministic movement matrix for canonical Ecstatica II arrow controls: `up`, `down`, `left`, and `right` in debug and ASan. Original-game modifier/utility reports are parser-visible as `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; source/manual mapping says arrows move, `Ctrl`+arrows attack, Left Alt+arrows dodge, `Ctrl`+Left Alt+arrows advanced attack, Left Shift jumps, Right Alt drops carried items, `Space` interacts, `Return` opens the icon/status page, `Esc` opens menu or closes status/menu, `S` quick-saves, and `I` toggles the icon bar. Do not close this step until the camera/action/modifier owner layer is recorded and the intro `Space` split is either repaired or deliberately carried as a source-backed follow-up.

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
3. Notes: Final task for Step 3; start from the completed arrow movement matrix and compare SDL/default backend behavior before deciding whether to split the remaining intro `Space` action frontier. Classify `Ctrl`/`Shift`/`Left Alt`/`Right Alt`, `Return`, `S`, `I`, and any version-specific `L` quickload report before wiring unproven gameplay behavior.

## Change Log

### 2026-07-28

1. Created task.

### 2026-07-31

1. Added the current intro action/requester frontier as the required pre-closeout evidence.

### 2026-08-04

1. Activated after Task 02 landed `scripts/run-e2-control-matrix.sh` and proved four canonical arrow movement controls in debug and ASan.
2. Added the menu-control sub-slice after original screenshots/testing showed the intro menu is mouse-only. Bounded SDL probes now prove Settings and Load submenu entry through mouse events, while the visual surface dump remains a diagnostic artifact rather than a faithful screenshot proof.
