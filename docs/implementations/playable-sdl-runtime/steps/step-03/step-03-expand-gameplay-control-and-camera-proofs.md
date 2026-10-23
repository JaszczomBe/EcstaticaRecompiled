# Expand Gameplay Control And Camera Proofs

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: partially deferred; basic movement/camera proofs planned with Step 09
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-14

## Goal

Classify gameplay controls and camera behavior using both recovered state and visible actor response.

## Why This Step Exists

The canonical arrow-key mapping and bounded input latches are proven. The investigation also exposed action/context, geometry, and child-instantiation failures, which now belong to [Step 08](../step-08/step-08-recover-scene-175-actors.md). The [Step 07 baseline repairs](../step-07/step-07-restore-reproducible-runtime-baseline.md) are complete. At the user's 2026-10-14 request, basic movement/camera proofs join [Step 09's cylinder gameplay route](../step-09/step-09-enable-diagnostic-gameplay.md); they do not wait for full meshes or all NPCs. Broader control classification still needs genuine player readiness.

## Scope

1. Preserve the completed input-state map and four-arrow matrix.
2. Classify modifier/action/status/interaction owners after genuine control readiness, using diagnostic cylinders where needed.
3. Record source-backed movement/camera changes and relevant backend comparisons.

## Out Of Scope

1. Action 384 calling conventions, Joe geometry, and scene-child activation (Step 08).
2. Full combat/inventory implementation, rebinding, or controller support.
3. Full intro animation, save/load implementation, and requester visual polish; split these before implementation.

## Usage Budget

Keep each control proof bounded. Split any new parser, renderer, or actor crash family into a separate task.

## Temporary Sacrifices

1. Existing probes prove state delivery while visible gameplay is incomplete.
2. Resume behavioral assertions after the necessary action/placement/motion prerequisites pass. Diagnostic proxies can supply visible response; original mesh recovery remains separate.

## Tasks

1. [Map Gameplay Input State](tasks/task-01-map-gameplay-input-state.md) — completed historical mapping.
2. [Add Control Probe Matrix](tasks/task-02-add-control-probe-matrix.md) — completed; 8/8 debug/ASan arrow rows reverified 2026-09-14.
3. [Verify Camera And Action Frontiers](tasks/task-03-verify-camera-and-action-frontiers.md) — basic movement/camera proofs planned with Step 09; broader controls deferred until readiness, task not complete.

## Current Findings

1. First-intro Space enters `Start_sc`; Space during the sub-intro is wait-only. Completion preserves scene 175 through a one-shot guard. The selected framebuffer has the pedestal background but lacks living actors.
2. SDL input delivery and frame presentation are sufficient for the next engine investigation. The current action-index crash and actor render state are tracked in Step 08.
3. The arrow matrix verifies Win32 delivery, movement vector, direction, requester clear, nonzero scene pointer, and a nonblank surface. Its readiness gate does not require completed sub-intro, geometry, or actual motion.
4. Historical grouped probes establish left Ctrl/Alt/Shift flags. Right Alt/drop, Return/status, S/I/L utilities, gameplay Space, and camera/action state remain unclassified at the owning game-logic layer.
5. Historical mouse-menu probes reach Settings/Load, toggle Music, close Settings, and route Quit confirmation. Intro Save is intentionally disabled; quick-save is a no-op. Slot behavior and visual fidelity remain separate follow-ups.

## Acceptance Criteria

1. Preserve the completed input mapping and arrow-state evidence.
2. Record the owner and observable result of each accepted action/modifier/status control, or link a narrowly scoped unresolved task.
3. Demonstrate input-driven player/camera changes after actual control readiness, measuring real actor state and visible response. Label diagnostic-cylinder results separately from original mesh fidelity.
4. Record default/SDL differences and a manual visual check before closing remaining Task 03.

## Verification

1. Existing arrow matrix and corrected Step 07 wrapper.
2. Grouped key probes with completed-sub-intro and actor-state evidence.
3. Synchronized game/SDL captures and manual F5 when behavior changes.
4. `git diff --check`.

## Notes

See the [2026-09-14 audit](../../../../journal/entries/runtime-audit-2026-09-14.md) for reverified evidence. The dated entries below describe investigation history; their earlier blocker descriptions do not override the current task/dependency map.

## Change Log

### 2026-10-14

1. Brought basic locomotion and camera proofs forward with Step 09's diagnostic cylinders. Necessary game logic still needs recovery; original meshes and all NPCs are no longer blanket prerequisites.

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
4. Recovered the post-`Start_sc` handoff by copying scene-child actor live vectors, restoring signed-byte scene-height lookup semantics, and adding the later one-shot scene-175 preserve guard for the descriptor-48771 scene-87 proposal.
5. Added grouped held-key probes for modifiers and repaired the ASan render/action helper frontiers exposed by the movement matrix. The full control matrix is green again for debug and ASan `up/down/left/right`.

### 2026-08-20

1. Reclassified the user's wrong-location report: the post-`Start_sc` scene lookup still proposed scene `87`, but the expected visible frame is current scene slot `175`.
2. Added a one-shot `Start_sc` action-completion handoff guard in generated reconstruction code. The long dummy-SDL route now exits with scene pointer `0x67da4c`, `hires\0175.raw`, and surface 3 hash `321e33d6`; later visibility packets reclassified this as correct pedestal background preservation without living-character rendering.
3. Repaired stale SDL presentation after the second intro by pumping host presentation during every compatibility `Sleep` slice. Surface dumps now report the selected framebuffer page; the clean proof ends with `front=2 selected=3 selected_valid=1`, surface 3 hash `321e33d6`, and scene pointer `0x67da4c`.

### 2026-09-14

1. Deferred remaining controls behind Steps 07/08 and split actor recovery into dedicated tasks.
2. Replaced stale intro-skip/current-gameplay claims with bounded input and presentation evidence.
