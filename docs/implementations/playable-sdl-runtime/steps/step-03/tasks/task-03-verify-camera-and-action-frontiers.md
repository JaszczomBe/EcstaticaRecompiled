# Verify Camera And Action Frontiers

Status: deferred
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Classify action, modifier, status, and camera behavior after the player and scene actors are visible.

## Scope

1. Compare default and SDL behavior using bounded probes.
2. Map accepted inputs to their game-state owners and visible consequences.
3. Record missing behavior or new crashes as separate tasks.

## Dependencies

Complete [Step 07](../../step-07/step-07-restore-reproducible-runtime-baseline.md), then [Step 08](../../step-08/step-08-recover-scene-175-actors.md). Action 384/context recovery, Joe geometry, and scene-backed child activation now have separate owners in Step 08. Do not close this task just because those prerequisites complete.

## Out Of Scope

1. Fixing every action-system crash or implementing full combat/inventory.
2. Full first-intro animation, requester visual polish, and functional save/load; create dedicated tasks for those changes.

## Implementation Notes

The 2026-09-14 audit verifies first-intro skipping and `Start_sc` completion into preserved scene 175. It also confirms the static-room-only packet and the gated action-384 crash. Earlier claims that Space cannot skip, Joe is visible, or input-state readiness establishes gameplay are superseded. See the [audit](../../../../../journal/entries/runtime-audit-2026-09-14.md) and [runtime journal](../../../../../journal/entries/runtime-crash-fixes.md).

The existing four-arrow matrix passes debug and ASan. Its gate checks StartGame entry, a mode flag, a scene pointer, and requester clear; it can pass while the sub-intro action is still running. Future behavior probes must wait for actual completion and observe the actor/action/camera layer.

Historical grouped-key evidence uses comma-separated taps and plus-separated held keys, e.g. `space,ctrl+up`. Left Ctrl/Alt/Shift reach flags; Right Alt reaches the key queue without the left-Alt gameplay flag. Return, S, I, L, and gameplay Space had no conclusive owner-state change in short probes. These observations were not all rerun during the audit.

| Input | Original/reference intent | Remaining proof |
| --- | --- | --- |
| Arrows | Move/turn | Position/orientation and rendered response after sub-intro completion |
| Ctrl + arrows | Basic attacks | Action selection and execution |
| Left Alt + arrows | Dodge | Action and motion owner |
| Ctrl + Left Alt + arrows | Advanced attacks | Modifier combination and action owner |
| Left Shift | Jump | Actor action/trajectory |
| Right Alt | Drop | Distinct right-modifier and carried-item owner |
| Space | Interact | Context-dependent action, separate from intro skip |
| Return / Esc | Status/menu open/close | Status and requester ownership |
| S / I | Quick-save / icon bar | Save writer is currently a no-op; HUD owner unclassified |
| L | Reported quickload | Verify version-specific original behavior before implementing |
| F12 | Reference healing control | Compatibility currently also requests a visibility packet; classify coexistence before claiming gameplay support |

Historical intro-menu proofs use mouse clicks: Settings (`320,225`) opens requester `0x31`, Load (`320,203`) opens `0x29`; Settings Music selects item `0x643998` and toggles `settings.music`. Settings OK and Quit Yes/No routes have bounded evidence. Load/Save slot clicks are consumed as selection, not proof that persistence works. Refer to the dated journal for commands and remaining layout artifacts.

## Acceptance Criteria

1. Each accepted control names its owner, state delta, and visible result where applicable.
2. Player/camera behavior is measured after completed sub-intro and visible-actor readiness.
3. Default/SDL comparisons and manual visual results are recorded.
4. Unknown controls or independent failures have explicit follow-up scope; key delivery alone is not marked as implemented gameplay.

## Verification

1. Existing control matrix and corrected runtime wrapper.
2. Bounded held-key/action probes with actor position, action, camera, and requester state.
3. Synchronized framebuffer/presentation packets and manual SDL F5.

## Review State

1. Planning state: agreed
2. Implementation state: in_progress
3. Notes: Deferred with historical input/menu evidence retained. Resume after Step 08; actor recovery itself is owned there.

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
5. Advanced first-intro `Space` from input latch to action-completion frontier: skip request now consumes Space and sets action `0x937800` to duration `495`; completion reaches the self-loop sentinel once, then exposes the next crash in `FUN_00421f54` after `FUN_0042a70c`.

### 2026-08-18

1. Recovered first-intro `Space` skipping for the real scene-child action wrapper rather than only the earlier direct action pointer. The final early-Space probe `--inject-key-sequence-surfaces /tmp/e2-intro-horse-skip-final space 4 250 30` exits cleanly, logs `horse_scene=1564`/`actor_scene_id=1564`, loads `Start_sc=0`, clears `DAT_00636850`, and dumps nonblank surface 3 `hash=44b33248`.
2. Confirmed `Start_sc` remains wait-only: `--inject-key-sequence-surfaces /tmp/e2-intro-subintro-space-final space 12 250 30` logs `intro skip ignored wait-only subintro`, clears Space, exits cleanly, and dumps nonblank surface 3 `hash=44b33248`.
3. Repaired the post-skip crash chain exposed by the direct transition: scene-child allocator reuse, unresolved no-archive child activation, action-event hidden context, CRT RNG seed fallback, and the `FUN_0042b880` sound subcase stale-ECX call into `FUN_0042fce0`.
4. Recovered the first version of the fastest gameplay path: `--inject-key-sequence-surfaces /tmp/e2-startsc-gameplay-up space,up 4 40000 65` skipped the first intro, waited through `Start_sc`, posted `Up` after the initial scene-87 handoff, and exited with `move=[1,0,0,0,0,0,0,0,0]`. The 2026-08-20 continuation supersedes the scene target by preserving scene `175`.
5. Added held-key group support to the native probe parser: comma still separates sequential taps and plus now holds keys in one group, so probes such as `space,ctrl+up`, `space,alt+up`, and `space,ctrl+alt+up` can classify modifier ownership.
6. Recorded modifier/utility frontier evidence. Left `Ctrl`, Left `Alt`, `Ctrl+Alt`, and Left `Shift` latch their reconstructed flags; `ralt` reaches the key queue but does not set the gameplay alt flag; `return`, `s`, `i`, `l`, and gameplay `space` reach the queues without a visible short-probe state delta yet.
7. Repaired the ASan control-matrix crash chain exposed by Task 03: explicit actor/node/vector context for render/list helpers, explicit actor context for `FUN_00433d30`/`FUN_00431a7c`, and absolute byte-table reads for `FUN_0042c790`.
8. Verified `scripts/run-e2-control-matrix.sh` passes all debug and ASan rows for `up`, `down`, `left`, and `right` after the repairs.

### 2026-08-20

1. Repaired the user-reported post-subintro wrong location by preserving scene slot `175` for the one `Start_sc` action-completion handoff where `FUN_0044c224` proposed scene `87`.
2. Verified `--inject-key-sequence-surfaces /tmp/e2-startsc-handoff-fix space,up 4 40000 105` exits cleanly with scene pointer `0x67da4c` and nonblank surface 3 hash `321e33d6`; later visibility packets corrected the earlier claim that this proved Joe visible.
3. Repaired stale post-subintro SDL presentation by pumping host presentation on every compatibility `Sleep` slice. Verified `--inject-key-sequence-surfaces /tmp/e2-present-loop-clean-space-only space 4 40000 20` exits with `front=2 selected=3 selected_valid=1`, surface 3 hash `321e33d6`, and scene pointer `0x67da4c`.

### 2026-08-21

1. Added a visibility packet probe for the current manual no-player report: F12 in the SDL window requests a synchronized packet, and `E2R_VISIBILITY_DUMP_PREFIX` can auto-write one packet with optional `E2R_VISIBILITY_DUMP_AFTER_MS` and `E2R_VISIBILITY_DUMP_SCENE_SLOT`.
2. The packet writes all four indexed game pages, all four palette-applied game pages, SDL's converted present surface, SDL's final window surface, and a state sidecar with scene slot, actor/action state, selected/front pages, movement flags, and palette hash.
3. Verified the post-handoff dummy-SDL packet after `start-sc handoff preserve scene current=175 selected=87`: scene slot `175`, action pointer `0`, selected surface `3` hash `321e33d6`, SDL present hash `914159a1`, and SDL window hash `5cf799a1`. Added `scripts/e2r_visibility_sheet.py` to create a contact sheet and selected-vs-present diff.
4. Extended the visibility state sidecar with actor-list and scene-child census data. Current F12/user-equivalent packets classify the no-character report as pre-SDL: selected framebuffer, SDL present, and SDL window match, but dynamic actors do not render into the game framebuffer. Actor `0` is live and marked visible, with `attached_rep=0` and `render_rep=0xf4430008`/`render_rep_id=67`; scene-175 children `319`/`322`/`318` have no actor resources/table entries but do have scene/rep archive offsets.
5. Added a one-shot activation after the preserved `Start_sc` handoff so the packet can inspect scene 175's dynamic record even when the compact descriptor is already current. This does not yet change the visible hash; it exposes the next blocker in actor/rep loading.
6. Added timestamped stderr logging with local-time `[YYYY-MM-DD HH:MM:SS.mmm]` prefixes so future manual SDL logs can line up F12, handoff, and input events without guessing from raw order alone.
7. Recorded the user's manual F12 packet from `/tmp/e2-visibility-000`: scene `175` is selected and presented, but selected/present/window images match the static-room baseline, actor `0` has `render_rep_id=67` with `model=0xffffffff`, and scene-175 children still have no actor instances. Extended the native sidecar with render-tree roots, render-rep slots `17..24`, and the current-actor render skip flag for the next packet.
8. Added `--auto-scene175-visibility <prefix> [timeout_seconds] [packet_wait_ms]` so scene-175 visibility packets no longer require manual timing or F12. The first automated packet at `/tmp/e2-auto-scene175` confirms Joe is not skipped and has a render tree, but rep `67` still lacks the model pointer in slots `17/18`.
9. Changed the auto scene-175 packet to wait its packet-delay argument before capture, then verified a settled packet still lacks living actors. Render-node sidecar evidence now points to Joe's actor-level rep `67` without a root render-tree rep/update list, and latch/owner proof edits were reverted after they did not change the framebuffer.
10. Gated the experimental flat-FANT action index behind `E2R_ACTION_INDEX_PROBE=1` after the user's fresh manual run crashed in the action/motion path. Default no-click automation now exits cleanly with `actions=0`, scene `175`, surface 3 hash `321e33d6`, SDL present hash `914159a1`, and SDL window hash `5cf799a1`. The opt-in gdb repro resolves Joe fallback action `384` at offset `9790200`, installs action pointer `0xac263c`, clears `DAT_0047a470` during parse, and crashes in `FUN_0042ae80` on stale hidden-register `in_EAX=0x5b59`. Continue there for action/model initialization; do not treat this as SDL presentation, selected framebuffer, WASD, or "Joe visible."

### 2026-09-14

1. Split action context, player geometry, and scene-child activation into Step 08.
2. Consolidated current guidance, retained historical change-log evidence, and defined prerequisites and behavioral acceptance limits.
