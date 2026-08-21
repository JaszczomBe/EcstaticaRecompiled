# Verify Camera And Action Frontiers

Status: active
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-08-21

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

Current pre-closeout frontier: `Space` during the first intro is no longer an input-delivery, action-completion, or gameplay-entry blocker. The hook recognizes the horseback scene-child wrapper by actor scene `horse` id `1564`, logs `intro skip request`, and loads `Start_sc` scene id `0`. `Space` during the following `Start_sc` pedestal/lightning sub-intro is wait-only and is consumed with `intro skip ignored wait-only subintro`. `Start_sc` reaches action `0x9377e3` completion, signed scene-height lookup selects descriptor `48771`, and the one-shot handoff repair now preserves scene `175` when the selector proposes scene `87`. The latest visibility packets correct the earlier false "Joe visible" classification: selected surface 3, SDL present, and SDL window all match, but the selected game framebuffer itself lacks the living player/enemy actors shown in the original-game reference screenshots. The next blocker is actor/rep activation for scene 175, not SDL presentation, page selection, or arrow-key delivery. Original-game testing showed the intro menu does not respond to keyboard navigation, so this task still carries the mouse path as the menu-control proof. `--inject-intro-menu-click-surfaces /tmp/e2-menu-settings 320 225 6 3` reaches requester id `0x31` and then clears the consumed menu decision state back to `0`; `--inject-intro-menu-click-surfaces /tmp/e2-menu-load 320 203 6 3` does the same after reaching requester id `0x29`. The Settings requester row/action chain is reconstructed enough for a targeted two-click proof: `--inject-intro-menu-click-sequence-surfaces /tmp/e2-settings-music-final '320,225;320,203' 6 1 250 0x31` records `actions 0->2`, selects item `0x643998`, ends with `settings.music=1`, and clears `_DAT_00643650=0`.

Original-game intro progression, recorded from manual reference: after the three logos, the first engine scene shows two people riding on horseback toward the castle. At the castle gate one person is captured and the other is knocked down by flying beings. This first intro scene lasts roughly 30-40 seconds and can either be skipped with `Space` or allowed to finish. The next brief sub-intro shows the main character bound to a pedestal; lightning strikes, and the character breaks free. This sub-intro lasts roughly 10 seconds and should be waited out. Proper controllable gameplay begins after that sub-intro finishes. The rebuilt runtime currently shows only a static first intro image, does not animate/process through both scenes, and `Space` does not skip the first intro. For playable-runtime purposes, prefer recovering the fastest original gameplay route before investing in full first-intro animation fidelity: make `Space` advance from the first intro into the pedestal/lightning sub-intro, then let that sub-intro complete naturally into gameplay.

The latest manual real-SDL menu issue covered visual artifacts plus intro action routing: main-menu requester rectangles smeared across the frame, Start Game crashed in `FUN_0043a39c` when `DAT_0047a470` was stale, Save blinked despite being unavailable in intro, Load left a malformed surface, and Settings rows/OK did not respond. The current narrow fix set guards the Start Game actor flag write, routes high-res requester panel/item fill and borders through explicit hosted rectangle bounds on both high-res pages, anchors the selected-character repaint to the computed text x-coordinate, makes Save use `action.save_disabled_intro` without changing gameplay Save, carries requester mouse state through a real `mouse_state` local, and gives Settings OK an explicit close action. Follow-up menu diagnostics showed disabled Save must stay in the active main menu, not close it: requester `0x28` now consumes only disabled Save directly, leaves `_DAT_00643650=5`, and lets normal main-menu actions fall through to the recovered modal loop. Submenu entry now passes explicit requester records into `FUN_0043b384`: Settings uses `0x0047a668`, while Load/Save initializes and passes `0x0047a5a4` with the larger `0xf0 x 0xb4` slot-list dimensions. The newest visual lifecycle repair adds a high-res requester backdrop stack and opens Settings/Load as nested modal requesters over active requester `0x28`, so submenu close restores the main-menu backdrop and main-menu close restores the intro frame. Bounded proofs now show Start during intro routes through `action.restart_intro` and `action.restart_intro_complete` without crashing, two-Esc main-menu open/close restores the intro surface (`hash=44b33248`) with `_DAT_00643650=0`, Settings Music dispatches item `0x643998` and flips `settings.music=1`, and Settings OK logs `action.settings_ok old=2 new=0` followed by `action.settings_return old=0 new=5` with a restored main-menu dump (`hash=6e4e9abb`). The 2026-08-17 manual pass confirmed three logos display in order and the menu is basically reachable, but also confirmed the intro sequence remains static, Quit/Settings/Load have missing/wrong labels or rough placement, Save shows nothing during intro, and Load slot clicks closed the menu. The latest repair maps fixed-address requester labels `0x00473298`/`0x004732a4`/`0x004732a8` to `OK`/`Yes`/`No`, redraws Settings rows after toggles, names Load/Save slot actions, consumes Load/Save slot clicks without closing requester `0x29`/`0x2a`, and logs requester `0x28` bounds. Load still has title/slot overlap and a left black rectangle, and the hosted font/color/layout is still approximate. A whole-file generator run is now part of the verification flow; keep generated C/H changes mirrored by `E2Recomp/tools/GenerateRecon.js`.

The next implementation continuation should treat manual SDL as a visual/fidelity check rather than an input-delivery check. For intro progression, the fastest original route is now understood and proven through the visible pedestal scene: first-intro `Space` skip, wait through the pedestal/lightning sub-intro, preserve scene `175` on the scene-87 proposal, then continue control-readiness work there. Do not shortcut `Space` directly to final gameplay; the recovered route already follows the original procession. Continue with camera/action/modifier classification from the gameplay state, or with Load title/slot/OK behavior and requester surface/font/color/layout fidelity if menu usability is the user-facing priority. Save should be classified against original intro behavior before making it visible. Full first-intro animation/progression fidelity should be split from gameplay-entry work.

The latest intro-progression slice proves the pragmatic skip route end to end: early `Space` during the first intro logs `intro skip request scene=0x683c84 actor=0xaa6bd8 action=0x93a329 ... Start_sc=0 horse_scene=1564 actor_scene_id=1564 direct=0 horse=1`, activates `Start_sc`, ignores missing sound id `331`, completes action `0x9377e3`, and preserves scene `175` when descriptor `48771` proposes scene id `87`. The repair chain includes distinct scene-child pool allocation in `FUN_004533ac`, skip-over handling for no-archive startup children in `FUN_00452140`, scene-child live-vector initialization for Joe at `12800,256,-3584`, action-event context recovery through `FUN_0042ad60`/`FUN_0042b338`/`FUN_0042c790`, a safe RNG seed fallback in `FUN_0045fc10`, `FUN_0042b880` subcase-`5` passing event field `in_EAX[3]` as the sound id into `FUN_0042fce0`, signed-byte scene-height comparison in `FUN_00448744`/`FUN_004488a4`, and the one-shot `Start_sc` completion handoff guard in `FUN_0044c224`.

The 2026-08-19/2026-08-21 player-visibility continuation keeps the best next move on the post-intro scene/rep path. `FUN_0044c224` activates selected scene records for normal positive scene switches, and the flat-FANT scanner restores actor/scene counts while adding targeted rep offsets (`actors=81 reps=389 scenes=1205`). The direct archive parser now allocates rep `67` from `0x35`/`0x36` records, and the manual-stack crash chain after `Start_sc` is cleared by explicit actor motion/side-link guards, packed-byte extraction for `DAT_004c3ad5`, and action-id parameter recovery in `FUN_00451880`/`FUN_0045190c`/`FUN_00441b24`. The F12 visibility packet disproved the earlier visual read: the game selected page, SDL converted present surface, and SDL window surface all contain the same static scene without the living player or two enemies. The actor census shows only actor `0` on `_DAT_0063726c`; the corrected sidecar now distinguishes `attached_rep=0` from the live `render_rep=0xf4430008`/`render_rep_id=67`, but Joe still does not draw into the selected framebuffer. The activated scene-175 record has children `319/sword2cv`, `322/burkrt`, and `318/sword2` with no actor-table entries and no actor archive offsets; they are scene/rep-backed in the flat archive (`319 scene=0x216ae rep=0x890d46`, `322 scene=0x218dc rep=0x891052`, `318 scene=0x215ec rep=0x890bc0`). The one-shot handoff now forces preserved-scene activation once, which exposes the scene-175 child state without changing the framebuffer hash. Continue by recovering scene-backed child activation and Joe's render-rep/model path; do not spend more time on SDL presentation or WASD.

Task 02 added a deterministic movement matrix for canonical Ecstatica II arrow controls: `up`, `down`, `left`, and `right` in debug and ASan. Original-game modifier/utility reports are parser-visible as `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; source/manual mapping says arrows move, `Ctrl`+arrows attack, Left Alt+arrows dodge, `Ctrl`+Left Alt+arrows advanced attack, Left Shift jumps, Right Alt drops carried items, `Space` interacts, `Return` opens the icon/status page, `Esc` opens menu or closes status/menu, `S` quick-saves, and `I` toggles the icon bar. Do not close this step until the camera/action/modifier owner layer is recorded and the intro `Space` split is either repaired or deliberately carried as a source-backed follow-up.

Task 03 now has grouped held-key probe notation: comma separates sequential taps, while plus holds keys in the same dispatch group, for example `space,ctrl+up`. Debug probes prove the host/WndProc layer preserves left-modifier flags for held groups: `ctrl+up` dispatches both keys and ends with `ctrl=1`, `alt+up` ends with `alt=1`, and `ctrl+alt+up` ends with both modifier flags set while `Up` still latches movement. `shift` alone latches the shift flag without movement. `ralt` reaches WndProc as `VK_RMENU`/scan `0x38` but does not set the gameplay alt flag, so Right Alt/drop ownership is still unmapped. `return`, `s`, `i`, and `l` reach the Win32/legacy key queues but have no visible gameplay state delta in the short post-handoff probes. `Space` after the recovered intro route reaches the input path but has no interaction delta in these scene/context probes. The next control frontier is therefore no longer grouped input delivery; it is action/status/save/load/drop owner-state discovery in the reconstructed gameplay layer.

The latest ASan control-matrix blocker is fixed. The grouped-probe work exposed hidden-register/render-helper crashes in the actor render epilogue (`FUN_00421a14`/`FUN_00421f54` through `FUN_00424cbc`/`FUN_00424d14`/`FUN_00424d58`/`FUN_00424d98`/`FUN_00424dd8`/`FUN_00424e44`, then `FUN_00433d30`/`FUN_00431a7c`) and an ASan-only packed global table read in `FUN_0042c790`. The durable fix makes those helpers take explicit actor/node/vector context, removes stale `extraout_*` cursor propagation, and rewrites the `DAT_0063679e` action-event flag table reads to absolute byte-address reads. `scripts/run-e2-control-matrix.sh` now passes all debug and ASan rows for `up`, `down`, `left`, and `right`.

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
3. Notes: Final task for Step 3; intro gameplay-entry recovery is now proven, and the arrow movement matrix is green again in debug and ASan after the render/action helper repairs. Resume owner-layer classification from grouped modifier probes. Classify `Ctrl`/`Shift`/`Left Alt`/`Right Alt`, `Return`, `S`, `I`, `Space`, and any version-specific `L` quickload report before wiring unproven gameplay behavior. Requester visual/slot behavior and full first-intro animation fidelity remain separate follow-ups unless they block the probes.

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
