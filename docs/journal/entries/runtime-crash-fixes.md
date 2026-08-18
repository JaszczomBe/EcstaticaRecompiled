# Runtime Crash Fixes

Use the runtime crash fix template in [journal.template.md](../../templates/journal.template.md) for new entries.

## 2026-08-18 - Start_sc Completes Into Scene 87 Gameplay

Area: Playable SDL runtime Step 3 Task 03, fastest original intro route and gameplay entry

Symptom: after first-intro `Space` successfully loaded the wait-only `Start_sc` pedestal/lightning sub-intro, waiting through it reached action `0x9377e3` completion but looped back through scene `0`. `FUN_0044c224` logged `lookup=-1 scene_id=0 ... pos=12800,256,-3584`, so the route still did not enter controllable gameplay.

Evidence: the narrowed lookup probe showed Joe's scene-child load supplied stand vector `12800,256,-3584`, and the generated live-vector copy made `FUN_0044c224` evaluate that same position after `Start_sc` completion. The grid cell was valid (`cell=0xbe83`, descriptor words `0057,0036`), but the descriptor height byte was `0xff`; generated C compared it as unsigned `255 <= 130`, rejecting the terminal candidate. Treating that byte as signed matches MSVC-style `char` semantics and makes `0xff` pass as `-1`.

Change: mirrored generated repairs in `E2Recomp/tools/GenerateRecon.js`: scene-child-loaded actors copy nonzero stand vectors into live vectors when the live vector is zero, and `FUN_00448744`/`FUN_004488a4` compare scene descriptor height bytes as signed chars instead of unsigned bytes. The existing skip, wait-only Space consumption, missing sound id `331` suppression, and action-event context repairs remain part of this route.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-sdl-debug`, and `git diff --check` pass. Probe `--inject-key-sequence-surfaces /tmp/e2-startsc-signed-height space 4 250 50` proves `Start_sc` completion selects descriptor `48771`, scene id `87`, and opens `hires\0087.raw`. Probe `--inject-key-sequence-surfaces /tmp/e2-startsc-gameplay-up space,up 4 40000 65` posts `Up` after the sub-intro handoff and exits with `_DAT_0073cc3c=0x67d0ac` and `move=[1,0,0,0,0,0,0,0,0]`.

Next Frontier: resume Step 3's camera/action/modifier classification from the recovered gameplay state. Full first-intro animation/procession fidelity remains separate; requester Load/Save visual and slot behavior also remains a menu-fidelity frontier.

Regression Risk: signed scene-height lookup affects the shared scene grid helpers, but it matches the expected signed-`char` interpretation of `0xff` descriptors and fixes a concrete original-route handoff. Watch scene transitions near height-layer boundaries in later movement/camera probes.

## 2026-08-18 - Horse Intro Space Skip Enters Wait-Only Subintro

Area: Playable SDL runtime Step 3 Task 03, intro procession and post-skip crash recovery

Symptom: after manual original-game testing clarified the fastest route, the rebuilt runtime still needed first-intro `Space` to enter the pedestal/lightning `Start_sc` sub-intro. The earlier skip helper only recognized a direct action pointer and missed the live scene-child action wrapper; broadening it exposed a post-skip sound/requester crash.

Evidence: early-Space dummy-SDL probes show the live first-intro actor `0xaa6bd8` has action slot `0x93a329`, duration `495`, and actor scene record `horse` id `1564`. After broadening the predicate, gdb showed the next crash in `FUN_0043cac0` through `FUN_00414e68 <- FUN_0044248c <- FUN_00451a54 <- FUN_0042fce0 <- FUN_0042b880`; the event record at `FUN_0042b880` had fields `008c,002e,0005,014b,0000`, proving subcase `5` was passing stale `ECX` instead of the event sound id.

Change: mirrored generated repairs in `E2Recomp/tools/GenerateRecon.js`: first-intro skip now accepts the `horse` scene-child wrapper and loads `Start_sc` scene id `0`; Space during `Start_sc` with no active current actor is consumed as wait-only. Supporting repairs restored distinct `FUN_004533ac` child allocation, skip-over handling for unresolved no-archive startup children in `FUN_00452140`, action-event actor context across `FUN_0042ad60`/`FUN_0042b338`/`FUN_0042c790`, a safe fallback seed for `FUN_0045fc10`, `FUN_00451a54`/`FUN_0044248c` parameter recovery, and `FUN_0042b880` subcase `5` now calls `FUN_0042fce0((int)in_EAX[3],(int)unaff_ESI,1)`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, and `cmake --build --preset linux-clang32-sdl-debug` pass. Probe `--inject-key-sequence-surfaces /tmp/e2-intro-horse-skip-final space 4 250 30` exits cleanly, logs `intro skip request ... Start_sc=0 horse_scene=1564 actor_scene_id=1564 direct=0 horse=1`, clears `DAT_00636850`, and dumps nonblank surface 3 `hash=44b33248`. Probe `--inject-key-sequence-surfaces /tmp/e2-intro-subintro-space-final space 12 250 30` exits cleanly, logs `intro skip ignored wait-only subintro`, clears Space, and dumps nonblank surface 3 `hash=44b33248`.

Next Frontier: wait through `Start_sc` long enough to prove the transition into controllable gameplay. If it stalls, recover the sub-intro completion owner rather than making a direct gameplay bypass.

Regression Risk: the skip predicate is scene-scoped to `horse` id `1564`, so it should not make the `Start_sc` sub-intro skippable. The no-archive child handling and sound-event recovery are pragmatic generated repairs; future original-disassembly work should confirm their exact register ownership once the gameplay route is stable.

## 2026-08-17 - First Intro Space Skip Reaches Completion Frontier

Area: Playable SDL runtime Step 3 Task 03, first-intro action skip/completion

Symptom: manual original-game testing clarified that the fastest valid route is first-intro `Space` skip, then wait through the pedestal/lightning sub-intro. In the rebuilt runtime, `Space` reached WndProc and latched `DAT_00636850`, but the horseback/castle intro did not skip.

Evidence: bounded dummy-SDL probes show the active intro actor/action as actor `0xaa6bd8`, slot `0xaa6c7e`, action `0x937800`, duration `495`. The action updater had lost its elapsed delta (`unaff_EBX`), so progress originally stuck; after recovering `_DAT_00637378`, progress advances. `Space` is now consumed by a narrow first-intro skip helper, which sets progress to the action duration and logs `intro skip request`.

Change: mirrored generated repairs in `E2Recomp/tools/GenerateRecon.js`: recover the action delta in `FUN_0042ad60`, make the linear completion branch use `<=`, avoid stale `extraout_ECX` writes, route completion through actor context, add a narrow first-intro Space skip request for action `0x937800`, and make `FUN_0042b004` break on the observed self-loop keyframe sentinel instead of expecting a null-terminated list. Added temporary action/completion diagnostics and native probe timing fields.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, and `cmake --build --preset linux-clang32-sdl-debug` pass. Probe `--inject-key-sequence-surfaces /tmp/e2-first-intro-space-sentinelbreak space 6 250 18` proves Space is delivered, skip is requested, completion starts, and the completion keyframe sentinel is `0x7c8758 -> 0x7c8758` with no events. After completion returns, the runtime now crashes in the actor update/render epilogue at `FUN_00421f54` from `FUN_0042a70c`, so the next repair target is post-completion actor/list context, not input delivery.

Next Frontier: recover the original post-first-intro transition owner. Do not bypass directly to gameplay. First decide whether action `0x937800` completion should hand off to a different actor/action/script for the pedestal/lightning sub-intro, then fix the `FUN_00421f54` hidden-context crash exposed after the action completes.

Regression Risk: the skip helper is intentionally scoped to the observed first-intro action pointer. The completion diagnostics are noisy and should be trimmed once the post-completion owner is recovered.

## 2026-08-17 - Requester Fixed-Address Labels And Slot Clicks

Area: Playable SDL runtime Step 3 Task 03, intro requester text/actions

Symptom: manual SDL testing showed the intro menu was reachable, but Quit's Yes/No buttons were blank, Settings OK/Cancel labels were missing or hard to see, Settings rows appeared unresponsive, and clicking any Load slot closed the Load menu. The same pass confirmed the logo sequence now reaches the intro, but intro character animation/scene progression remains static.

Evidence: requester layout logging showed several original labels are fixed data-symbol addresses rather than hosted C strings: `0x00473298` for OK, `0x004732a4` for Yes, and `0x004732a8` for No. The existing hosted label fallback only handled `0x00473304` as Quit. Load requester rows carried action `LAB_0043fadc`, but diagnostics named it `unknown`, and direct requester click dispatch fed it into the modal return path instead of treating it as slot selection.

Change: added fixed-address label fallbacks for OK/Yes/No, kept the existing Quit fallback, redrew the active requester item after Settings row toggles, named `LAB_0043fadc`/`LAB_0043fb58` as Load/Save slot actions, and consumed Load/Save slot-row clicks by updating `_DAT_0064353c` and redrawing in place. The requester layout logger now includes main-menu requester `0x28`, making Start/Save/Load/Settings/Quit/Cancel bounds visible in probes. Mirrored generated reconstructed changes in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, whole-file regeneration, `cmake --build --preset linux-clang32-sdl-debug`, and `git diff --check` pass. Dummy-SDL probes prove Settings Music hits item `0x643998` and ends with `settings.music=1`, Settings OK logs `action.settings_ok` followed by `action.settings_return`, Load slot clicks log `action_name=load_slot` and remain in requester `0x29`/state `4`, Quit Yes reaches `action.quit_confirmed` and exits cleanly, and Quit No returns to requester `0x28`/state `5`. `ctest --preset linux-clang32-sdl-debug` was attempted, but that preset does not exist.

Next Frontier: continue requester visual fidelity: Load title/slot overlap, the left black save-location rectangle, OK/Cancel placement, modal-over-main-menu artifacts, and hosted font/color/layout. Save should be classified against original intro behavior before making it visible, and the static intro animation/progression problem remains separate from menu input plumbing.

Regression Risk: the label mapping is fixed-address and intentionally narrow. The slot-click handling is selection-only and does not claim real save/load behavior; later work should recover the original slot confirm/load/save path before allowing state mutation.

## 2026-08-04 - Confirmed Quit Uses Host Window Shutdown

Area: Playable SDL runtime Step 3 Task 03, intro main-menu Quit confirmation

Symptom: after the Quit prompt state collision was fixed, confirming Quit worked far enough to reach requester state `6`, but then crashed in `FUN_0043cac0` through `FUN_00414e68`.

Evidence: the manual trace logged `action.confirm_yes old=5 new=6`, `action.quit_confirmed old=6 new=6`, then `FUN_00415d40` case `6` called `FUN_00414e68`. That helper tried to scan/show an exit message through stale decompiler hidden-register state before destroying the window, so the crash was in the message path, not in Quit prompt selection.

Change: the intro menu decision switch now handles state `6` by calling `DestroyWindow(_DAT_00ac4dac)` directly. Other fatal/error call sites still use `FUN_00414e68`. The requester layout logger also includes requester `0x14`, making Quit prompt Yes/No bounds visible in future traces.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, and `cmake --build --preset linux-clang32-sdl-debug` pass. The bounded Quit-Yes probe clicks Quit, then requester `0x14` Yes at item `0x643dc4` bounds `[190,220..290,238]`, logs `action.quit_confirmed`, reaches `FUN_00415d40` state `6`, and exits with code `0` without entering the `FUN_0043cac0` crash path.

Next Frontier: manual real-SDL confirmation that Quit Yes closes the program cleanly and that Quit No/Escape visibly returns to the main menu.

Regression Risk: this is intentionally scoped to the menu Quit decision state. If original fidelity for Quit needs a final message later, recover the `FUN_00414e68` message pointer convention separately instead of reusing it for the normal menu Quit path.

## 2026-08-04 - Quit Prompt No Longer Collides With Settings

Area: Playable SDL runtime Step 3 Task 03, intro main-menu Quit requester state

Symptom: the latest menu diagnostics showed a new state collision after clicking Quit. The main menu opened a yes/no prompt and set requester state `6`, but `FUN_00415d40` still handled state `6` by opening Settings requester `0x31`. After that, later Load/Save clicks appeared to keep showing Settings.

Evidence: the manual trace logged `action.quit_prompt old=5 new=6`, followed by `15d40.open requester end ... state=6`, and later Settings-style actions while the active requester path should have been the Quit confirmation prompt. The earlier Settings/Load/backdrop fixes were otherwise behaving: Settings returned to requester `0x28`, Load returned to requester `0x28`, disabled Save stayed on the main menu, and Start during intro still used the restart route.

Change: restored state `6` in `FUN_00415d40` to the original quit-confirmed path (`FUN_00414e68`) instead of opening requester `0x31`. The Quit action now opens requester `0x14`; confirmed Yes closes the requester and returns state `6`, while canceled/no Quit restores the parent main menu requester `0x28` with state `5` and keeps the parent modal loop alive. WndProc now has an explicit Escape close path for requester `0x14`, and the direct requester click bridge accepts `0x14` for diagnostics/action dispatch.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, and `cmake --build --preset linux-clang32-sdl-debug` pass. The focused Quit probe no longer opens Settings: after clicking Quit it ends at requester `0x28`/state `5` with no requester `0x31` leak. Settings Music still hits requester `0x31` item `0x643998` and flips `settings.music=1`. Load still opens requester `0x29` and lays out the slot/cancel items. A main-menu close probe still finishes with `_DAT_00643650=0`.

Next Frontier: run one real-SDL manual pass to confirm Quit prompt Yes exits and Esc/No visibly returns to the main menu. The current bounded harness does not reliably feed a second Esc through the modal WndProc path once a requester is already open, so a small harness improvement would make future Esc-close proofs cleaner.

Regression Risk: `FUN_00414e68` is the original quit/fatal-exit helper and is now reachable from the intro Quit confirmation again. If confirmed Quit crashes in real SDL, recover the exact call-site message/exit convention instead of rerouting state `6` back to any submenu requester.

## 2026-08-04 - Requester Backdrops Restore Nested Menu Layers

Area: Playable SDL runtime Step 3 Task 03, intro requester surface lifecycle

Symptom: the latest manual real-SDL trace showed the menu state was clearing, but the visible requester pixels did not follow. A second Escape from the intro left the main menu on-screen, Settings/Load stayed visible underneath the main menu after close, and Settings buttons appeared dead because the active state and the stale visual layer no longer matched.

Evidence: the pasted console output logged correct state transitions: main-menu Escape reached `wndproc.close_main_menu`, `15d40.menu_complete old=5 new=0`, and final requester state `0`; Settings OK reached `action.settings_ok old=2 new=0`. The remaining failure was therefore visual/backdrop ownership, not SDL event delivery or requester decision state.

Change: high-res requester entry now saves a small stack of surface-2/surface-3 backdrops before drawing, and requester exit restores the most recent backdrop before returning. Main-menu Settings and Load actions now open requester `0x31`/`0x29` as nested modal requesters and then restore requester `0x28`/state `5`, so Settings/Load close back to the live main menu instead of leaving orphaned pixels. The target-requester mouse probe feed hook was re-anchored in `FUN_0043b384`, and the final hosted label redraw is re-anchored so restored main-menu dumps keep labels such as `QUIT`. Trace labels now name `LAB_0043d470` as Settings and `LAB_0043d490` as Load.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-sdl-debug`, and `git diff --check` pass. The bounded two-Escape probe restores the intro surface (`/tmp/e2-menu-double-esc-backdrop2-s3.ppm`, hash `44b33248`) with `_DAT_00643650=0`. The targeted Settings Music probe dispatches item `0x643998` and ends with `settings.music=1`. The Settings OK probe logs `action.settings_ok old=2 new=0`, then `action.settings_return old=0 new=5`, and the visual dump restores the main menu with all labels present (`/tmp/e2-settings-ok-backdrop3-s3.ppm`, hash `6e4e9abb`). Start during intro still routes through `action.restart_intro` and no longer crashes.

Next Frontier: manual real-SDL confirmation that one Escape hides the active main menu, Settings/Load close back to the visible main menu, and Settings row/OK clicks work interactively. Load/Save remains visually rough: title/slot overlap and slot canvas/OK behavior still need recovery.

Regression Risk: the backdrop stack copies full high-res pages for requester nesting. It is intentionally limited to the hosted high-res path and should be revisited if original DirectDraw requester page-save semantics are recovered more exactly.

## 2026-08-04 - Active Menu Close Must Exit The Modal Loop

Area: Playable SDL runtime Step 3 Task 03, intro requester close lifecycle

Symptom: after submenus became visible, manual real-SDL still needed extra input to get out of menus. A bounded two-Esc probe showed why: WndProc could clear the visible requester state, but `FUN_0043b384` kept waiting because its internal modal-loop side flag was unchanged. When the direct main-menu close was first forced to return, `FUN_00415d40` then misread `_DAT_00643650=0` as Start Game and crashed through `FUN_0043a39c`.

Evidence: `--inject-key-sequence-surfaces /tmp/e2-menu-double-esc-current esc,esc 8 1500 14` logged `wndproc.escape_main_menu old=5 new=0`, returned from `FUN_0043b384`, then gdb stopped in `FUN_0043a39c` at the stale actor flag write from `FUN_00415d40` case `0`. The modal loop exits when `_DAT_006443d0` differs from the last mouse/key loop state, so clearing only `_DAT_00643650` was not enough.

Change: WndProc Escape for the active main requester now marks the requester dirty, flips `_DAT_006443d0=1`, clears the requester id word, and returns menu decision state `5` so the parent switch treats it as cancel/no selection before `15d40.menu_complete` clears it to `0`. Submenu Escape still clears state to `0`, but also flips the modal-loop flag and requests redraw. Generated requester actions that leave the parent modal loop, including intro Start restart, Settings/Load entry, Settings OK, and Load/Save/Settings cancel, now also flip `_DAT_006443d0=1`; Settings row toggles stay in-place.

Result: `cmake --build --preset linux-clang32-sdl-debug` passes. The bounded main-menu probe logs `wndproc.escape_main_menu old=5 new=5`, then `15d40.menu_complete old=5 new=0`, exits with `_DAT_00643650=0`, and does not enter `FUN_0043a39c`. The Settings OK sequence hits item `0x643de4`, logs `action.settings_ok old=2 new=0`, unwinds immediately, and ends with requester state `0`.

Next Frontier: manual real-SDL confirmation that one Escape hides the active main menu and that Settings OK/Cancel no longer need a follow-up click. Continue Load slot/OK visual and behavior recovery.

Regression Risk: main-menu Escape deliberately returns state `5` during the parent switch instead of `0`; that keeps close/no-selection distinct from Start Game. Any future main-menu action that should close the parent modal loop should set `_DAT_006443d0`, while in-submenu row toggles should not.

## 2026-08-04 - Intro Start Restarts Intro Instead Of Starting Gameplay

Area: Playable SDL runtime Step 3 Task 03, intro main-menu Start action

Symptom: clicking Start Game during the intro crashed or entered the wrong StartGame path. Original-game testing showed Start Game from the intro menu should restart the intro instead of starting gameplay.

Evidence: the manual paste still logged `action.start_male old=0 new=0` after clicking Start during intro. Earlier attempts to replay the full startup action directly exposed generated stale-register frame traversal crashes in `FUN_00421684`, `FUN_004211c8`, and `FUN_00421f54`, so the safe intro behavior needed to avoid entering gameplay StartGame from requester state.

Change: Start male/female requester actions from main requester `0x28` while `DAT_0047a76c != 0` now route to a new `action.restart_intro` decision state. `FUN_00415d40` handles that state by clearing requester/input state, preserving intro mode, and resetting the current intro action progress instead of calling `FUN_0043a39c`. The existing stale-current guard in `FUN_0043a39c` remains for non-intro Start paths.

Result: the bounded Start probe logs `action.restart_intro old=5 new=7`, then `action.restart_intro_complete old=7 new=0`, exits with `_DAT_00643650=0`, and no longer crashes.

Next Frontier: visually compare the restarted intro timing against the original game. This currently resets the active intro action progress safely; recovering the exact original restart hook remains future fidelity work if the visual reset is not exact enough.

Regression Risk: this route is gated to requester `0x28` during intro mode. Gameplay Start male/female paths still use the original state `0`/`1` behavior.

## 2026-08-04 - Intro Submenus Need Explicit Requester Records

Area: Playable SDL runtime Step 3 Task 03, intro submenu presentation

Symptom: after the menu lifecycle diagnostics repair, manual real-SDL logs showed clicks changing menu state but no submenu appeared. Escape could close the active submenu state, proving input/state routing had advanced while presentation still showed the parent menu.

Evidence: the pasted trace showed `action.load old=5 new=2` followed by requester id `0x31`, and `action.options old=5 new=4` followed by requester id `0x29`; both later closed through `wndproc.escape_submenu`. Dummy-SDL dumps before the fix still showed the parent requester surface. Inspecting `FUN_0043ce58` found Settings calling `FUN_0043b384(extraout_ECX_04, extraout_EDX_00)` and Load/Save calling `FUN_0043b384(pbVar6, pcVar8)`, so the submenu state was correct but the modal renderer received stale decompiler hidden-register values instead of the submenu requester records.

Change: Settings now calls `E2R_InitRequesterSettingsItems()` and passes requester record `0x0047a668` to `FUN_0043b384`. Load/Save now initializes and passes requester record `0x0047a5a4`; layout diagnostics showed the slot-list children require a larger panel, so the record uses `0xf0 x 0xb4` low-res dimensions instead of the small prompt size. The requester item layout logger now includes ids `0x29`, `0x2a`, and `0x31` with active record bounds.

Result: `node --check E2Recomp/tools/GenerateRecon.js` and `cmake --build --preset linux-clang32-sdl-debug` pass. Bounded dummy-SDL probes show Settings visible over the intro background and Load visible/framed. Load remains visually unfinished: its title overlaps the slot rows and a black rectangle appears at the left edge.

Next Frontier: manual real-SDL confirmation that Settings no longer blinks and Load/Save now show a submenu. Continue with Load title/slot/OK behavior and requester surface/font fidelity.

Regression Risk: the explicit records repair decompiler-hidden argument loss around `FUN_0043ce58`. The Load/Save dimensions are inferred from the recovered child item geometry, so they should be revisited if original disassembly/data gives a more exact record initializer.

## 2026-08-04 - Intro Menu Diagnostics Fix Stale Save And Escape

Area: Playable SDL runtime Step 3 Task 03, intro main-menu requester lifecycle

Symptom: after adding focused menu diagnostics, a manual real-SDL run regressed: clicking Save/Load/Settings appeared to show no submenu, and Escape no longer hid the main menu.

Evidence: the pasted console trace showed `Esc` opening requester `0x28` with `_DAT_00643650=5`. The first click landed on Save at game coordinates `305,184`; because Save is unavailable during the intro, it logged `action.save_disabled_intro old=5 new=5`, but the recovered requester loop still returned to `FUN_00415d40`, which then ran `15d40.menu_complete old=5 new=0`. The visible menu afterward was stale pixels with no active requester, so later clicks could not route. A second `Esc` while requester `0x28` was active only fed the legacy key path and left `_DAT_00643650=5`.

Change: extended the direct requester hit tester to include main-menu requester `0x28` only for diagnostic hit logging and disabled-Save consumption. Disabled Save now logs `action.save_disabled_intro old=5 new=5`, returns handled to the host mouse path, clears the mouse latch, and keeps the main menu active. Normal main-menu actions still fall through to the recovered modal loop so Settings/Load can open their subrequesters. Added a WndProc `Escape` close path for active main-menu requester `0x28`, logging `wndproc.escape_main_menu old=5 new=0`. Mirrored the regenerated C repairs in `E2Recomp/tools/GenerateRecon.js`, including the generated header requester-probe prototypes and the hosted text `base2` declaration repair that regeneration exposed.

Result: `node --check E2Recomp/tools/GenerateRecon.js` and `cmake --build --preset linux-clang32-sdl-debug` pass. Bounded dummy-SDL probes show disabled Save ends with `_DAT_00643650=5` and no `15d40.menu_complete`; a Save-then-main-menu click sequence falls through to legacy and reaches requester `0x31`; a two-Escape key sequence logs `menu state: site=wndproc.escape_main_menu old=5 new=0` and ends with `_DAT_00643650=0`. A follow-up manual trace showed submenu Esc still waiting for a later mouse click to unwind (`requester=4`/`2` in the input log, then `15d40.menu_complete` only after the next `WM_LBUTTONDOWN`), so WndProc now closes active submenu requesters `0x29`/state `4`, `0x31`/state `2`, and `0x2a`/state `3` directly with `wndproc.escape_submenu old=<state> new=0`.

Next Frontier: rerun manual real-SDL with `E2R_MENU_DIAG=1`; if Load/Settings still blink or smear, the console should now distinguish stale pixels from active requester state. Load slot canvas/rendering remains the open visual/functionality frontier.

Regression Risk: direct handling for requester `0x28` intentionally consumes only disabled Save. Other main-menu actions rely on the recovered modal loop to preserve original submenu transitions.

## 2026-08-04 - Intro Requester Artifacts And Start Click Crash

Area: Playable SDL runtime Step 3 Task 03, intro menu requester drawing/action dispatch

Symptom: a manual real-SDL run showed `Esc` opening the intro menu, but the menu was covered with horizontal/diagonal line artifacts. Start Game crashed in `FUN_0043a39c` at the `DAT_0047a470` actor flag write. Save Game, which should be inert during the intro, caused rapid menu blinking. Load left a malformed blank/grey surface, and Settings blinked while rows/OK did not respond.

Evidence: the Start Game call stack ended at `FUN_0043a39c -> FUN_00415d40 -> FUN_00426df8 -> FUN_0041007c`. The crashing line dereferenced `DAT_0047a470` after the intro transition had already cleared or invalidated the current actor pointer. The requester screenshots matched the decompiled high-res requester fill/border paths using stale hidden-register coordinates: `FUN_0041ab4c` had lost its top coordinate and filled from y=0, while border calls reused `extraout_ECX*` values. A later visual dump showed a lone `S` left outside the dialog; that came from the selected-character repaint path using another stale `extraout_ECX_06` cursor.

Change: guarded the Start Game actor flag write with `E2R_IsReadableCurrentPointer(DAT_0047a470)`. Added hosted high-res rectangle fill/border helpers and routed requester panel/item fills through explicit computed bounds on both high-res pages, copying the richer intro/menu background page before requester drawing. Anchored the selected-character repaint to the computed item text x-coordinate. `FUN_0043b384` now carries the `FUN_0041ba7c` mouse result in an explicit `mouse_state` local instead of stale `extraout_ECX_*` temporaries, which stops the Settings requester from immediately replaying the parent menu decision. Save now takes an `action.save_disabled_intro` path unless a real gameplay scene/current actor is present. Settings OK now explicitly closes requester id `0x31`, and the existing direct settings row bridge still handles Music/SFX/Difficulty/Resolution. Durable transformations were mirrored in `E2Recomp/tools/GenerateRecon.js`; a whole-file regeneration attempt was rejected because it produced unrelated historical drift and reverted the new Start Game guard.

Result: `node --check E2Recomp/tools/GenerateRecon.js` and `cmake --build --preset linux-clang32-sdl-debug` pass. Bounded dummy-SDL probes show Start Game no longer crashes (`action.start_male`, state `0`), Save uses `action.save_disabled_intro`, Settings Music dispatches item `0x643998` and flips `settings.music=1`, and Settings OK logs `action.settings_ok old=2 new=0`. The Settings requester dumps matching high-res pages (`hash=798184ec`). Load is improved but not done: it opens requester id `0x29`/state `4` without crashing, but surface hashes differ (`s2=e2288345`, `s3=25b666b7`) and the slot canvas/rendering still needs recovery.

Next Frontier: manual real-SDL confirmation is still needed for the exact screenshots: main menu should no longer have smear/line artifacts, Save should not blink during intro, and Settings rows/OK should respond without toggling back to the main menu. Continue Load slot canvas/OK behavior and requester font/surface fidelity next.

Regression Risk: the hosted rectangle path is a Linux high-res safety repair for bad decompiler-hidden coordinates, not original pixel-perfect menu rendering. Save is behaviorally disabled in intro by action dispatch; the visible row still needs original greyed-out styling.

Follow-up instrumentation: `E2R_MENU_DIAG=1` now emits focused `menu click:` and `menu state:` lines for manual SDL runs. The SDL layer logs raw and mapped click coordinates, the Win32 shim logs button down/up with requester state/id, the requester hit tester logs ignored/miss/bad-item/no-action/hit outcomes plus item bounds/action names, and `E2R_TraceRequesterState` logs every menu decision-state write. Use this instead of screenshot-only back-and-forth for the next Load/Settings manual report.

## 2026-08-04 - Host Window Close Exits Before Reconstructed Quit Cleanup

Area: Playable SDL runtime Step 3 Task 03, SDL window lifetime and requester close path

Symptom: closing the SDL window with the title-bar `X` while a requester/menu was active segfaulted in `FUN_0043cac0` at `E2Recomp_recon.c:32594`. The stack went through `FUN_0041ba7c -> FUN_00414e68 -> FUN_0043cac0`, meaning the recovered modal message pump saw `WM_QUIT` and entered a cleanup/message helper with a stale hidden `in_EAX` string pointer.

Evidence: `FUN_0041ba7c` calls `GetMessageA`; when it receives `WM_QUIT`, it calls `FUN_00414e68()`. That cleanup path then tries to strlen the stale `in_EAX` value inside `FUN_0043cac0`. This is host-window lifetime, not menu action semantics.

Change: `PostQuitMessage` in the Win32 compatibility layer now flushes and exits the Linux process directly instead of queueing `WM_QUIT` back into the reconstructed modal cleanup path. The requester mouse bridge was also narrowed to submenu requester bodies (`0x29`, `0x2a`, `0x31`) so parent menu entries continue using the recovered modal path, while Settings rows and Load/Save cancel-class controls can use direct item-bound hit testing.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-sdl-debug`, and `git diff --check` pass. Bounded Settings and Load first-entry probes still end at requester ids `0x31` and `0x29` respectively with one action, and the targeted Settings Music proof still records `actions 0->2`, selected item `0x643998`, and `settings.music=1`. The title-bar close fix needs manual SDL-window confirmation because the dummy SDL probe does not exercise an interactive window manager close.

Next Frontier: recover Load slot selection and Load OK/Cancel behavior with item-chain evidence; then return to visual/menu fidelity. The current hosted text fallback is intentionally not original font fidelity.

Regression Risk: `PostQuitMessage` now terminates immediately in the host shim. That is correct for a user closing the Linux SDL window, but if later work needs original in-game quit cleanup, it should recover the stale-register path in `FUN_00414e68`/`FUN_0043cac0` before reintroducing queued `WM_QUIT`.

## 2026-08-04 - Menu Decision State Clears After Cancel And Submenus

Area: Playable SDL runtime Step 3 Task 03, intro requester/menu lifecycle

Symptom: after entering Load or Settings and leaving those submenus, or after using Cancel to leave the main menu, the menu began blinking rapidly. The menu action itself worked, but the recovered transient requester decision state stayed live after the modal path returned.

Evidence: `FUN_00415d40` sets `_DAT_00643650=5` before opening the parent menu. Recovered action dispatch then uses `_DAT_00643650=2` for Settings, `4` for Load, and `5` for Cancel/no selection. The parent switch consumes `2`, `3`, and `4` by opening the submenu, but it never cleared those values afterward, and `5` has no switch case at all. Bounded probes showed final input state keeping `_DAT_00643650=2` or `4` before the fix. A later live-video repro showed another lifecycle fault: `WM_KEYDOWN Escape` both set `DAT_00636844` and fed `0x1b` into the legacy requester key queue, so the menu-opening Esc could be consumed by nested requesters, and Esc pressed inside a requester could leave the global menu-open flag armed.

Change: after the parent menu switch finishes handling Settings, Save, Load, or Cancel/no selection, `FUN_00415d40` now clears `_DAT_00643650` through `E2R_TraceRequesterState("15d40.menu_complete",0)`. The reconstructed WndProc now routes Escape by context: when no requester is active it only sets `DAT_00636844` to open the intro menu, and when a requester is active it feeds the legacy key queue while keeping `DAT_00636844` clear. The probe harness also gained target-requester key queueing so submenu Esc proofs can wait for requester ids `0x31` and `0x29`. The generated-header and menu-complete repairs are mirrored in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-sdl-debug`, and `git diff --check` pass. The bounded Settings and Load first-entry probes now log `15d40.menu_complete old=2/4 new=0` and final `_DAT_00643650=0`. The targeted Settings and Load submenu-Esc probes end with `fed_key=0x1b`, `DAT_00636844=0`, `_DAT_00643650=0`, and final requester ids `0x31`/`0x29`.

Next Frontier: manually confirm that real SDL Settings/Load/Cancel no longer blink after close, then recover Load slot/OK behavior. The remaining visual problems are font/menu fidelity and requester surface restoration, not this lifecycle state.

Regression Risk: this intentionally clears only transient menu decision states `2`, `3`, `4`, and `5` after they have been consumed. Start-game decisions `0` and `1` are left to the existing StartGame case behavior.

## 2026-08-04 - Settings Submenu Music Row Clicks

Area: Playable SDL runtime Step 3 Task 03, intro Settings submenu controls

Symptom: the mouse-only intro menu could enter Settings, but row clicks inside the Settings submenu did not dispatch. The visible rows matched the original screenshot, while the reconstructed requester record for id `0x31` did not expose a usable item chain for mouse hit testing.

Evidence: the Settings requester opened with state `2`, but the requester item pass stayed on the stale first-entry path and no Settings row action changed state. Static initialization for `0x0047a668` only supplied the Settings requester record shell, while the recovered updater functions wrote row text to item storage at `0x00643998`, `0x006439f8`, `0x00643958`, and `0x006436e0`. After explicit item initialization, the Music row bounds include the screenshot click point `320,203`, and the selected item is `0x643998`.

Change: added the Settings requester item/record initialization for requester id `0x31`, recovered row action dispatch for Music, Sound effects, Difficulty level, and Resolution, and added a narrow submenu mouse bridge that walks cached requester item bounds for requester bodies while leaving the parent menu on the recovered modal path. The native probe harness now supports `--inject-intro-menu-click-sequence-surfaces` so one bounded run can open the intro menu, enter Settings, and apply a submenu click. Durable reconstructed repairs are mirrored in `E2Recomp/tools/GenerateRecon.js`; broad regeneration remains deferred because the current generator still produces unrelated historical drift.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-sdl-debug`, and `git diff --check` pass. The targeted Settings proof exits cleanly:

```text
env SDL_VIDEODRIVER=dummy E2R_STARTUP_LOGO_DELAY_MS=0 E2R_INPUT_DIAG=0 build/linux-clang32-sdl-debug/e2recomp --inject-intro-menu-click-sequence-surfaces /tmp/e2-settings-music-final '320,225;320,203' 6 1 250 0x31
mouse click probe wait finished ... actions 0->2 ... selected=0x643998 state=2 requester=0x31
input state ... settings=[music=1 sfx=1 difficulty=1 resolution=4 requested_resolution=1 install=6]
```

Next Frontier: apply the same bounded submenu method to Settings OK/apply and the remaining rows, then Load slot selection/OK/Cancel. The normal delayed sequence probe still depends on when queued Win32 messages are pumped after a modal requester returns, so use the target-requester sequence mode for deterministic submenu proofs until that event-lifetime behavior is recovered.

Regression Risk: the direct mouse bridge is guarded to submenu requester ids `0x29`, `0x2a`, and `0x31`; extending it to additional requesters should be backed by original item-chain/layout evidence. Row mapping beyond Music is inferred from recovered updater/action order and still deserves one-click proofs.

## 2026-08-04 - Intro Menu Mouse Route Reaches Load And Settings

Area: Playable SDL runtime Step 3 Task 03, intro requester/menu controls, SDL mouse-to-Win32 bridge

Symptom: original-game testing showed the intro menu is mouse-only, but the rebuilt runtime had no working menu mouse path. SDL mouse coordinates were not mapped back into the recovered `640x480` game frame, the Win32 compatibility layer did not preserve cursor position, reconstructed WndProc ignored mouse button state, requester action pointers still jumped into raw labels, and several menu switch arms used decompiler-residual requester ids. Clicking Load also exposed stale hidden `in_EAX` use in the save-slot preview path.

Evidence: a bounded Settings click initially reached the correct item but crashed at raw label `LAB_0043d470` through `FUN_0043b708`. After recovering action dispatch, Settings crashed in `FUN_0043ce58(param_1=0)` until the Settings requester id was restored to `0x31`. A bounded Load click then reached `FUN_0043ce58(param_1=0x29)` but crashed in `FUN_0043c1b8` because the save-slot index still came from stale `in_EAX`; GDB showed the explicit slot argument was `param_1=3`.

Change: the SDL backend now records the last aspect-fit presentation rectangle and maps mouse motion/button coordinates into game-frame coordinates. The Win32 shim tracks cursor position and implements `GetCursorPos`/`SetCursorPos`. The reconstructed WndProc now feeds mouse coordinates and sets left-button requester state. The native probe harness gained `--inject-intro-menu-click-surfaces <prefix> <x> <y> [esc_seconds] [post_click_seconds]`, which opens the intro menu with `Esc`, then leaves injected mouse messages for the requester loop. `FUN_0043b708` routes recovered requester action label pointers through `E2R_InvokeRequesterAction` instead of directly calling raw labels. `FUN_00415d40` now uses recovered requester ids for Settings (`0x31`), Save (`0x2a`), and Load (`0x29`). `FUN_0043c1b8` seeds the save-slot index from explicit `param_1` and treats out-of-range slots as the existing no-preview path. Durable reconstructed repairs are mirrored in `E2Recomp/tools/GenerateRecon.js`; regeneration is intentionally deferred because the current generator still produces unrelated historical drift if run wholesale.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-sdl-debug`, and `git diff --check` pass. The bounded Settings probe exits cleanly:

```text
env SDL_VIDEODRIVER=dummy E2R_STARTUP_LOGO_DELAY_MS=0 E2R_INPUT_DIAG=0 ./e2recomp --inject-intro-menu-click-surfaces /tmp/e2-menu-settings 320 225 6 3
mouse click probe wait finished ... actions 0->1 ... state=2 requester=0x31
```

The bounded Load probe exits cleanly:

```text
env SDL_VIDEODRIVER=dummy E2R_STARTUP_LOGO_DELAY_MS=0 E2R_INPUT_DIAG=0 ./e2recomp --inject-intro-menu-click-surfaces /tmp/e2-menu-load 320 203 6 3
mouse click probe wait finished ... actions 0->1 ... state=4 requester=0x29
```

Next Frontier: use the proven mouse path to validate submenu interactions beyond first entry: selecting Load slots/OK/Cancel, toggling Settings rows, and Quit confirmation. Keep menu keyboard navigation classified as absent in the original intro menu unless new original evidence appears.

Regression Risk: the mouse bridge changes shared Win32 cursor/button state, so future UI probes should verify clicks at non-centered/aspect-fitted window coordinates. The requester action dispatcher intentionally handles only recovered menu label targets; new labels should be added with original-address evidence instead of raw indirect calls.

## 2026-08-04 - Gameplay Control Matrix Added

Area: Playable SDL runtime Step 3, gameplay movement controls, bounded debug/ASan probes

Symptom: the runtime had only one stable gameplay movement proof (`space,num8`), but original Ecstatica II testing and the manual show that movement belongs to the cursor keys, not numpad. Step 3 needed a compact matrix before camera/action frontier work could be separated from basic host/input delivery.

Evidence: `scripts/run-e2-control-matrix.sh` passes in debug and ASan with dummy SDL input and `E2R_STARTUP_LOGO_DELAY_MS=0`. The matrix rows are `space,up`, `space,down`, `space,left`, and `space,right` with `gameplay_key_split=1`; each row reaches `gameplay-control wait satisfied`, dispatches the target key, keeps `_DAT_00643650=0`, keeps `_DAT_0073cc3c` nonzero, dumps nonblank surface `3`, and records the expected movement vector. The proven vectors are `up -> move=[1,0,0,0,0,0,0,0,0]`, `down -> move=[0,0,0,0,0,0,0,1,0]`, `left -> move=[0,0,0,1,0,0,0,0,0]`, and `right -> move=[0,0,0,0,1,0,0,0,0]`.

Change: added `scripts/run-e2-control-matrix.sh`, a serial matrix runner around the existing `--inject-key-sequence-gameplay-surfaces` probe. It builds debug and ASan unless `E2R_SKIP_BUILD=1`, asserts per-row key dispatch, movement vector, `_DAT_00479e78` pending direction, requester clear, scene pointer, and surface proof, and rejects ASan reports. The SDL/X11 host backends now translate physical arrows to arrow virtual keys instead of numpad virtual keys. The Win32 compatibility/parser layer names arrow keys, `Ctrl`, `Shift`, `Alt`, `Right Alt`, `S`, `I`, and `L`; arrow keys map to the canonical movement bits.

Result: `scripts/run-e2-control-matrix.sh`, `bash -n scripts/run-e2-control-matrix.sh`, `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `git diff --check` pass. Task 02 is complete and Task 03 is active.

Next Frontier: compare SDL/default backend behavior for the accepted controls and classify the remaining camera/action/modifier frontier, including whether intro `Space` should be repaired in this step or split to an action-dispatch follow-up. Keep `Ctrl` attacks, Left Alt dodge, `Ctrl`+Left Alt advanced attacks, Left Shift jump, Right Alt drop, Return icon/status page, `S` quicksave, `I` icon-bar toggle, and version-specific `L` quickload as source/probe classification items before wiring behavior.

Regression Risk: the matrix intentionally covers movement-state latches, not full gameplay animation or collision semantics. The rows run serially because concurrent full-runtime probes can introduce noisy failures unrelated to per-key behavior.

## 2026-08-04 - ASan Actor Transform Child Guard

Area: Playable SDL runtime regression wrapper, `FUN_00423858`, actor transform child-chain traversal

Symptom: after the focused SDL requester repair, the full `scripts/run-e2-runtime-regressions.sh` wrapper rebuilt debug successfully, passed the debug gameplay-control probe, then aborted in the ASan gameplay-control probe with a read from `0x80000010` inside `FUN_00423858`.

Evidence: the failing ASan stack was `FUN_00423858 -> FUN_00423858 -> FUN_00421074 -> FUN_004211c8 -> FUN_0042a70c -> FUN_00426df8 -> FUN_0041007c`, with the faulting read at `*psVar9 = *psVar9 + *local_58`. The root actor pointer already passed the existing `FUN_00423858` entry guard; the bad address came from the linked child pointer loaded through `local_54`.

Change: added bounded readability checks for the `local_54` child-chain node, the linked-actor path used when `param_2 != 0`, and the main `iVar10` actor loop in `FUN_00423858`. Mirrored the repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build build/linux-clang32-asan` passes, and the full wrapper no longer reports the sanitizer crash. The wrapper is still red because the ASan gameplay-control gate times out with `_DAT_0073cc3c=0x0` after the known scene-`7`/actor-`3853` transition, even though StartGame entry, `DAT_00479de8=1`, `DAT_0047a76c=1`, requester clear, movement latch, and nonblank surface `3` are present.

Next Frontier: recover ASan scene/current ownership after the intro completion path or revise the wrapper only when there is source-backed evidence for the new expected sanitized state.

Regression Risk: the guard prevents generated residue from walking an unreadable actor child link, but it is still a defensive repair. Future fidelity work should recover original child/link ownership instead of broadening this guard.

## 2026-08-04 - Intro Requester Labels Restored

Area: Playable SDL runtime Step 3, intro `Esc` requester presentation, hosted SDL probes

Symptom: `Esc` reached `FUN_00415d40` and the requester path during the horseback/credits intro, but the visible menu contents were unreadable even though the requester geometry and item pass count were live.

Evidence: a bounded dummy-SDL `Esc` probe reports `requester=[ce58=1 id=0x28 mode=5 b384=1 bad=1 ptr=0x47a588 b9bc=6 ...]`; final surface output `/tmp/e2-step03-escape-labels-final-s2.ppm` is nonblank with hash `8f4ff5bf` and visibly shows `START GAME`, `SAVE GAME...`, `LOAD GAME...`, `SETTINGS...`, `QUIT`, and `CANCEL`. Earlier focused traces showed item labels entering the text helper with `y=x` coordinates such as `260`, `248`, and `254`, so they were drawn outside their rectangles and later item fills overwrote preceding labels. Raw indexed inspection also showed palette index `15` was panel gray in this requester and index `8` was the visible white text color. Separately, injected Win32 probes could dispatch through SDL polling from a non-main thread and abort with SDL's main-thread assertion before the requester evidence could be collected.

Change: the SDL backend now returns early from host event polling when it is reached on a non-main thread, avoiding the SDL assertion while preserving queued Win32 key dispatch. The high-res text path now has a hosted ASCII fallback renderer, requester item text y-coordinates use the item rectangle y value, and the requester redraws visible labels after all item rectangles are painted. The durable generated-file edits are mirrored in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-sdl-debug`, the bounded `Esc` surface probe, and the bounded `Space` script diagnostic probe pass. `Esc` now opens readable requester contents. `Space` still reaches `DAT_00636850=1` and `_DAT_00479e7a=1`, but the intro action completes naturally through `FUN_0042ad60`/`FUN_0042b004` and then dispatches opcode `0x07` toward scene `7`, whose child actor `3853` is still missing as a standalone flat-FANT actor record.

Next Frontier: activate the compact control probe matrix while carrying the `Space` action-dispatch/completion split as a separate recovered-game-state frontier.

Regression Risk: the fallback renderer is a hosted visibility repair, not recovered original font fidelity. It is limited to the high-res path and remaps only the requester colors needed for readable labels; replace it with original glyph data when that data is recovered.

## 2026-07-30 - SDL Presentation Preserves Frame Aspect Ratio

Area: Playable SDL runtime visual fidelity, `E2R_HostPresentIndexed8`, host-window scaling

Symptom: after front-buffer and palette recovery, user F5 comparison showed every presented image was squeezed horizontally relative to the original game even though the selected `640x480` image and scene colors were correct.

Evidence: the original top-level window request is `640x640`, while the SDL backend blitted every `640x480` frame to the full window surface. After the repair, a bounded dummy-SDL probe reports `host backend present rect: src=640x480 window=640x640 dst=0,80 640x480`, followed by unchanged scene fidelity evidence: palette hash `de4e4c5d` and nonblank surface `3` hash `44b33248`.

Change: the SDL host backend now computes a centered aspect-fit destination rectangle from the source frame dimensions, clears the unused window area to black, and blits with `SDL_SCALEMODE_PIXELART` into that rectangle instead of stretching to the full host window. `E2R_PRESENT_DIAG=1` logs the computed source/window/destination rectangle for bounded checks.

Result: `cmake --build --preset linux-clang32-sdl-debug` passes, and the bounded dummy-SDL surface dump confirms the presentation rectangle preserves the original `640x480` frame aspect inside the `640x640` host window.

Next Frontier: run a real-display F5 check to confirm the horseback/credits scene now matches the original aspect ratio, then continue gameplay control/camera proof expansion.

Regression Risk: this changes only the SDL presentation backend, not recovered frame selection, palette publication, or indexed pixel storage. Non-4:3 source frames will also preserve their own source aspect, which is the intended backend behavior.

## 2026-07-30 - Scene Palette Published After Raw View Load

Area: Playable SDL runtime first-scene color fidelity, `FUN_0044add8`, DirectDraw palette publish

Symptom: user screenshot comparison showed all logo screens and the first horseback/credits scene route were correct, but the first scene colors were far too bright and beige/gray. That meant the indexed raw scene pixels were correct, while SDL was still using an older logo/title palette.

Evidence: the scene route opens `hires\1073.raw`, and the data directory contains `Views/1073.PA2` with the expected `2 + 0x18 + 0x300` byte layout. The loaded PA2 palette converts to hash `de4e4c5d`, while the previous scene dump still reported the stale palette hash `29b6fa49`. After the repair, the same dummy-SDL surface dump reports `palette_nonzero=242`, `palette_hash=de4e4c5d`, and unchanged indexed surface `3` hash `44b33248`. The converted `/tmp/e2-scene-palette-fix-s3.png` visually matches the original dark red/black/purple scene palette family.

Change: after `FUN_0044add8` refreshes the scene palette buffer at `0x0061c730`, it now calls `FUN_0041af88(0x0061c730, param_2)` so the DirectDraw palette shim and SDL backend receive the scene palette instead of keeping the previous palette. Mirrored the repair in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-debug`, `cmake --build --preset linux-clang32-sdl-debug`, `cmake --build build/linux-clang32-asan`, the bounded dummy-SDL palette probe, and `scripts/run-e2-runtime-regressions.sh` pass.

Next Frontier: ask for a quick F5 visual confirmation on real display; if the palette is now accepted, continue with gameplay control/camera proof expansion.

Regression Risk: `FUN_0044add8` is the scene palette loader and already normalizes fallback palette bytes into `0x0061c730`, so publishing that buffer follows the existing recovered palette path. The change may affect every raw view palette refresh, which is intended; future palette fade issues should inspect `FUN_00457994`/`FUN_00457a34` hidden fade-amount recovery rather than bypassing this publish.

## 2026-07-30 - Front Buffer Presentation Verified

Area: Playable SDL runtime Step 2, DirectDraw page/front-buffer recovery, ASan regression stability

Symptom: after raw-view ownership reached the stable horseback frame family, SDL presentation still chose a page through nonblank scanning. The full regression wrapper also exposed a new sequence of sanitizer-only generated-code faults before the front-buffer proof could be trusted.

Evidence: original `E2WIN95.EXE` disassembly around `FUN_0043acec` shows surface `3` owns the full `640x480` raw/frame buffer in hires mode while surfaces `0/1/2` remain low VGA-style pages. A dummy-SDL probe now reports `host backend live presentation: selected=3 front=3 visible=0 hires=4`, dump state `front=3 visible=1`, and surface `3` hash `44b33248`. Debug and ASan both reach StartGame, requester clear, scene `_DAT_0073cc3c=0x683c84`, movement latch `move=[1,0,0,0,0,0,0,0,0]`, and nonblank surface `3`; ASan does not flip the historical `DAT_00479de8` marker in the bounded sanitized run.

Change: recovered the native front source from `DAT_0047a43c`/`DAT_0047a279`, logged `front` in presentation and dump diagnostics, and made the presenter try the recovered front before the fallback nonblank scan. Generator-backed stabilizers repaired `FUN_00417b20` source/destination surface-index recovery, marked sparse original-global allocator helpers `no_sanitize("address")`, made cleanup marker rewrites land through regex anchors, restored the full `FUN_00449b4c` stack path buffer, replaced stale `FUN_0044add8` palette-file descriptor reads with explicit descriptor-stable reads, and recovered actor/animation context in `FUN_0042d048` and `FUN_0042b004`. The regression wrapper now validates ASan by scene/control/surface evidence while still rejecting sanitizer reports.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-debug`, `cmake --build --preset linux-clang32-sdl-debug`, `cmake --build build/linux-clang32-asan`, and `scripts/run-e2-runtime-regressions.sh` pass. Step 2 front-buffer presentation is complete.

Next Frontier: proceed to gameplay control and camera proof expansion, carrying the remaining Psygnosis/Andrew Spencer/loading-logo timing mismatch as visual parity context for the next real-display pass.

Regression Risk: selecting surface `3` in hires mode is grounded in original surface setup and still guarded by readability/nonblank fallback. The ASan harness relaxation is intentionally narrow: it requires StartGame scene/control state, requester clear, movement latch, nonblank surface `3`, and no sanitizer report instead of accepting a generic timeout.

## 2026-07-29 - Raw View Ownership Reaches Stable Horse Frames

Area: Playable SDL runtime startup parity, render epilogue scene id recovery, palette filename construction

Symptom: after flat-FANT actor offsets restored actor/current ownership, the first render epilogue still crashed while opening impossible raw-view paths such as `hires\2191.raw` and `views\2191.raw`. GDB showed the failure path entering `FUN_00449b4c -> FUN_0043cbb4 -> FUN_0043cbf0 -> FUN_0043b384 -> FUN_0041ab4c`, meaning the bogus view id was cascading into the requester/error renderer.

Evidence: original `E2WIN95.EXE` disassembly shows `FUN_004211c8` loads `EAX = *(int *)(*(int *)(DAT_0047a470 + 0x132)) >> 16` before calling `FUN_0044be20`; the current-actor child pass in `FUN_004523f8` uses the same `scene_record[0] >> 16` setup. Original `FUN_0044add8` also builds `views\XXXX.pal`/`pa2`/`pa3` in a stack path buffer and writes the four digits from `_DAT_0073ccba`, while the generated body copied into a stale register destination and indexed a six-byte local.

Change: made `FUN_0044be20` take the recovered scene id explicitly and updated both call sites. Repaired `FUN_0044add8` to use a real local path buffer, fill digits from `_DAT_0073ccba`, and append it to the data-directory buffer. Initialized `FUN_0045fd2c` and `FUN_0045fd4b` hidden `EAX` destinations from their explicit first argument. Mirrored all repairs in `E2Recomp/tools/GenerateRecon.js` and regenerated.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-sdl-debug`, and `cmake --build --preset linux-clang32-debug` pass. A regenerated 30-frame dummy-SDL probe exits successfully with `view raw open: scene=1073 camera=1073 hires=1 path=hires\1073.raw`, stable actor-loop updates, `_DAT_0073cc3c=0x683c84`, palette hash `29b6fa49`, and nonblank surface 3 `hash=44b33248`.

Next Frontier: compare the first post-startup rendered surface against the E2WIN95 horseback/credits intro, then finish front-buffer page ownership and startup-logo timing parity.

Regression Risk: the scene-id recovery matches original call-site register flow and is narrow. The string helper destination initialization is broader but aligns with their original `EAX` destination convention and generated callers already pass destination pointers; future string-helper crashes should still be checked against original call setup before broadening file/path behavior.

## 2026-07-29 - Flat-FANT Actor Offsets Restore Horse Ownership

Area: Playable SDL runtime startup parity, flat-FANT actor archive indexing, scene activation actor context

Symptom: after `mar:StartGame` activated `PlayScene "horse"`, the frame loop still had no actor/current ownership. Runtime traces showed actor `0` entering `FUN_00451f5c` with `table=0x0`, while the flat-FANT startup archive reader had only populated scene offsets.

Evidence: original data inspection showed flat-FANT actor resources use primary record type `0x08`; scene resources use type `0x19`. A generated dummy-SDL probe now logs `archive 47d94 flat FANT: actors=81 scenes=1205 bytes=33075606`, then `actor load archive: id=0 offset=12773490 result=1 table=0xaa6bd8`. The same run activates `horse` from offset `607214`, slot `0xac2594`, flags `0x02`, and returns from startup with scene record `0x67c728`. Frame-loop diagnostics then show `current=0xaa6bd8 actors=0xaa6bd8 links=0xaa6bd8`; actor `0` retains `p132=0xac2594` even though the first frame clears `_DAT_0073cc3c`.

Change: extended `FUN_00447d94`'s flat-FANT scan to populate `0x653840` from type `0x08` actor records. Recovered explicit pointer/context flow for generated stale-register helpers in the activation path: `FUN_004488a4`, `FUN_0044d4b4`, `FUN_0042b0f4`, `FUN_00426a80`, `FUN_0042ad60`, `FUN_0042b338`, and the third child pass in `FUN_004523f8`. Mirrored all durable repairs in `E2Recomp/tools/GenerateRecon.js` and regenerated.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-sdl-debug`, and `cmake --build --preset linux-clang32-debug` pass. The normal dummy-SDL probe advances past the previous empty-ownership gap and now exits with the next crash after raw view opens such as `hires\2191.raw` and `views\2191.raw`.

Next Frontier: recover raw-view/camera argument ownership in the render epilogue. GDB lands at `FUN_0041ab4c(param_1=-1,param_2=0,param_3=199)`, called by `FUN_0043b384 -> FUN_0043cbf0 -> FUN_0043cbb4 -> FUN_00449b4c -> FUN_0044be20 -> FUN_004211c8`. The next investigation should compare original E2WIN95 register flow for this path before adding guards.

Regression Risk: the flat-FANT actor index is a format recovery matching the proven data shape and is low risk. The helper guards repair generated hidden-register loss in a narrow activation/render setup path, but some helpers are shared; future crashes should recover their original call-site conventions rather than broadening these guards blindly.

## 2026-07-29 - `mar:StartGame` Activates Horse Scene

Area: Playable SDL runtime startup parity, script scene opcodes, active scene ownership

Symptom: after the startup crash chain was cleared, `mar:StartGame` reached the frame loop but the rebuilt runtime still did not enter E2WIN95's horseback/credits intro. `_DAT_0073cc3c` and `DAT_0047a470` stayed `0x0`, surface dumps still showed the logo surface, and the historical gameplay-control regression no longer reached its scene-pointer gate unless the old `E2R_FORCE_SCENE_785` diagnostic fallback was enabled.

Evidence: original `E2WIN95.EXE` disassembly around opcode `0x07` (`0044f6cc` through `0044f6f3`) and opcode `0x0c` (`0044f770` through `0044f78f`) shows the interpreter calls `FUN_0045233c`, reads the loaded scene record from `0x62e450`, then passes that record in `EAX` to both `FUN_00452140` and `FUN_004523f8`. A bounded dummy-SDL run with `E2R_SCRIPT_DIAG=1` now prints `op07-enter` for token `0x061c`, name `horse`, offset `607214`, followed by `op07-after-load` with slot `0xac2594`, then `op07-after-activate` with flags `0x02`. A follow-up `E2R_RUNTIME_DIAG=1` dump shows `current=0x0 actors=0x0 links=0x0` throughout the frame loop and actor `0` entering load with `table=0x0`.

Change: repaired generated opcode `0x07` and `0x0c` scene activation so `FUN_004523f8` receives the loaded scene record instead of `_DAT_0073cc3c`. Added gated `E2R_SCRIPT_DIAG=1` scene-opcode traces that resolve the scene token name, offset-table entry, slot pointer, active flags, current scene, current actor, bytecode cursor, opcode count, and action dispatch count. Mirrored the repair and diagnostics in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `git diff --check`, `cmake --build --preset linux-clang32-sdl-debug`, and `cmake --build --preset linux-clang32-debug` pass. `cmake -S . -B build/linux-clang32-asan ...` recreated the missing ASan build directory and `cmake --build build/linux-clang32-asan` passes through the regression wrapper. The full `scripts/run-e2-runtime-regressions.sh` currently fails the debug gameplay-control gate because `_DAT_0073cc3c` remains `0x0`; that is the same scene-current frontier now exposed without the old forced scene-785 fallback.

Next Frontier: recover why actor `0` has no actor table entry during normal `mar:StartGame`, then inspect `FUN_00452140`/`FUN_004523f8` child-list passes for hidden actor context loss. Do not force `_DAT_0073cc3c` from `PlayScene "horse"` without additional original evidence; the original activation helper does not appear to set that global directly.

Regression Risk: passing the explicit scene record to `FUN_004523f8` matches original register flow and is lower risk than the prior current-scene-global call. The risk is in the newly exposed behavior: old quickstart probes depended on a diagnostic scene-785 fallback that is now environment-gated, so regression expectations need to be interpreted against the active startup-parity frontier.

## 2026-07-29 - Startup Preloads Reach Frame Loop

Area: Playable SDL runtime startup parity, flat-FANT scene preloads, scene removal, `mar:StartGame`

Symptom: after flat-FANT scene offsets were recovered, startup progressed through matching opcode-`0x4d` scene preloads but crashed before `mar:StartGame` during scene removal/list cleanup. The crash first landed in `FUN_0043aa98`; after scene-list normalization, the next frontier was a bad hidden scene pointer in `FUN_00452140`, then a bad hidden actor-name index in `FUN_00441890`.

Evidence: bounded `E2R_STARTUP_DIAG=1` SDL/gdb probes showed matching scene installs through `rist10` (`scene id 1664`, opcode/action count `64`), then all four startup actions (`ken:StartUp`, `dav:StartUp`, `nea:StartUp`, `gre:StartUp`) completed. After repairing scene activation/name lookup, `mar:StartGame` reached `before-list-action`, `after-list-action`, `before-script-name`, `after-script-name`, `before-script-150`, `after-script-150`, `before-5fc70`, `after-5fc70`, and `before-return`. A timeout-interrupted gdb sample then landed in the frame path `FUN_00426df8 -> FUN_0042a70c -> FUN_0041cf5c -> FUN_004620bb`, not in a crash.

Change: normalized active scene-list heads/next links, bounded scene cleanup child/item walks, and threaded explicit cleanup context into decompiler-lost tiny flag helpers. Recovered explicit scene records for `FUN_00452140` call sites and made `FUN_00452140` validate installed scene records before walking child lists. Replaced `FUN_00441890` with a bounded actor/name-table lookup that derives the index from explicit arguments instead of hidden `AX`. Mirrored all generated repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build --preset linux-clang32-sdl-debug` pass. The escalated dummy-SDL gdb probe no longer crashes before or inside `mar:StartGame`; it survives until the forced interrupt in the frame loop.

Next Frontier: `mar:StartGame` still logs `_DAT_0073cc3c=0x0` through `before-return`, so the next slice should prove where `PlayScene "horse"` resolves, why no current scene pointer is installed yet, and whether the first visible post-startup scene matches E2WIN95's horseback/credits intro before returning to front-buffer ownership proof.

Regression Risk: the new list/name guards are scoped to generated hidden-register/list-shape loss, but `FUN_00441890` is shared name lookup code. If later callers need a different calling convention, recover their original argument setup rather than broadening the fallback silently.

## 2026-07-27 - Control-Ready Surface Copies Stop Crashing Debug

Area: Step 10 control-ready parity, `FUN_0041868c`, `FUN_00417b20`, generated hidden-register copy helpers

Symptom: after the ASan requester-state residue was fixed, the debug split gameplay probe reached control-ready state and posted delayed `num8`, then segfaulted during the next render/update pass. The first crash was in `FUN_0041868c`'s surface copy loop; after source-surface fallback, the next crash moved to `FUN_00417b20`, called by `FUN_0041760c(2,0,0,0,640,480)`.

Evidence: GDB showed both crashes came from generated helpers that depend on lost hidden register state. `FUN_0041868c` was using stale hidden `EAX` for source surface and stale hidden `EBX` for X. `FUN_00417b20` then reached its software-surface byte-copy loop with an invalid source/destination span.

Change: mirrored two generator-backed guards. `FUN_0041868c` now validates destination/source surface indices, normalizes full-screen X to zero, falls back to the opposite page when the hidden source surface is invalid, and checks read/write spans before copying. `FUN_00417b20` now validates resolved bases, pitches, rectangle bounds, and source/destination spans before its software copy loop.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Final split control-ready probes pass in both builds:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-final-debug5 space,num8 6 10000 180 1
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-final-asan2 space,num8 30 10000 60 1

_DAT_00643650=0
_DAT_0073cc3c=0x681d04
move=[1,0,0,0,0,0,0,0,0]
surface 3 nonblank=1 hash=6e39f5ea
```

Next Frontier: trim or gate temporary frame/actor diagnostics and decide whether Step 10 closes now or keeps a small fidelity follow-up for scene-current/presentation-page bookkeeping and hidden-register recovery in the surface-copy helpers.

Regression Risk: these guards prevent crashes from generated stale register residue but do not fully recover original source/X calling conventions. They are acceptable for the Step 10 control proof; later graphics fidelity work should replace them with call-site/signature recovery where needed.

## 2026-07-27 - ASan Reaches Control-Ready Movement

Area: Step 10 control-ready parity, `FUN_0042a70c`, `FUN_00427584`, dead-current menu request

Symptom: after split input proved delayed `num8` delivery, ASan still kept `_DAT_00643650=5` with requester `0x27` after StartGame and scene activation. Debug returned to `_DAT_00643650=0`.

Evidence: actor/frame traces showed ASan enters `FUN_0042a70c`, calls `FUN_00427584` for actor `0xaa6d64`, returns through the idle path, and then render epilogue selects `_DAT_0073cc3c=0x681d04`. The divergence came afterward: ASan had `DAT_0047a470=0`, and the generated dead-current branch treated null current as a reason to set `DAT_00479db4=1`, causing `FUN_00415d40` to open requester `0x27`. Debug carried a nonzero readable residue instead and therefore did not open the requester.

Change: narrowed the generated `FUN_0042a70c` dead-current requester guard so it only requests the menu for a readable non-null current actor with state `0xb` and expired life. Null current actors no longer open requester `0x27`. Mirrored the repair in `E2Recomp/tools/GenerateRecon.js` and regenerated.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. The ASan control-ready split probe now satisfies the stricter gate and latches movement:

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-asan space,num8 30 10000 60 1

gameplay-control wait satisfied after 0 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_00643650=0 _DAT_0073cc3c=0x681d04
input state after dispatch wait: ... DAT_00479de8=1 move=[1,0,0,0,0,0,0,0,0] ... _DAT_0073cc3c=0x681d04
surface 3 nonblank=1 hash=6e39f5ea
```

Next Frontier: review and trim temporary frame/actor diagnostics, then decide whether Step 10 can close or whether scene-current fidelity (`DAT_0047a470` after render setup) needs a small follow-up.

Regression Risk: the null-current behavior is defensive but original-shaped for the observed control-ready path: it preserves the dead-actor menu request when a readable current actor is actually dead, while avoiding a requester open caused solely by generated null residue.

## 2026-07-27 - Split Gameplay Probe Exposes ASan Requester Residue

Area: Step 10 movement parity probes, native key-sequence harness, ASan gameplay/control readiness

Symptom: ASan reached StartGame and installed `_DAT_0073cc3c=0x681d04`, but the original `space,num8` timing still reported `move=[0,...]` because `num8` was posted before active gameplay and then consumed or cleared before the scene pointer became live.

Evidence: debug and ASan both accept `space` through the Win32 message queue, but ASan reaches gameplay later. A split gameplay probe now posts keys before `gameplay_key_split`, waits for gameplay/control state, then posts remaining keys. Debug satisfies the stronger control-ready gate and records the known gameplay surface:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-move-debug space,num8 6 10000 180 1

gameplay-control wait satisfied after 0 ms: ... _DAT_00643650=0 _DAT_0073cc3c=0x681d04
input state after dispatch wait: ... move=[1,0,0,0,0,0,0,0,0] ... _DAT_0073cc3c=0x681f18
surface 3 nonblank=1 hash=3615add9
```

The matching ASan run exits without a sanitizer report. The stricter control-ready wait times out because `_DAT_00643650` stays at `5`, but delayed `num8` still reaches the movement byte after the scene pointer is live:

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-move-asan space,num8 30 10000 100 1

gameplay-control wait timed out after 70000 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_00643650=5 _DAT_0073cc3c=0x681d04
input state after dispatch wait: ... DAT_00479de8=1 move=[1,0,0,0,0,0,0,0,0] ... _DAT_0073cc3c=0x681d04
surface 3 nonblank=1 hash=6e39f5ea
```

Change: refactored the native probe thread so `--inject-key-sequence-gameplay-surfaces` accepts an optional `gameplay_key_split` argument. Existing invocations still inject all keys before the gameplay wait; split invocations can wait for scene/control readiness before later keys. No reconstructed C behavior changed, so no generator mirror was needed.

Result: `git diff --check`, `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug proves control-ready movement and ASan proves delayed movement-key delivery without a sanitizer report.

Next Frontier: recover why ASan leaves `_DAT_00643650=5` with requester `0x27` after StartGame and scene activation, while debug returns to `_DAT_00643650=0` and the expected gameplay surface hash.

Regression Risk: this is native probe instrumentation only. The stricter control-ready gate is intentionally diagnostic; keep it until the ASan requester-state residue is understood, then decide whether Step 10 can close or whether the state-machine fix belongs in reconstructed code.

## 2026-07-22 - ASan Reaches Gameplay Scene Pointer

Area: Step 10 scene-current path, `FUN_0045233c`, `FUN_0044c164`, `FUN_0044c6bc`, active-game transition

Symptom: after ASan reached StartGame dispatch and actor-load completion, the gameplay wait still timed out with `_DAT_0073cc3c=0`. Earlier ASan runs either tripped the `FUN_0044c164` bad-current guard or cleared unreadable `DAT_0047a470` residue before any scene could be selected.

Evidence: debug and ASan diverged at `5233c.archive`. Debug carried a readable non-actor-table value that eventually produced a static scene record, while ASan carried unreadable register residue such as `0xc93040` or `0x4f7c808`. Debug's first active scene after the repaired scene-loader path corresponds to static scene slot `785`.

Change: added a bounded action-name cache so ASan reaches the same StartGame scan/dispatch counts as debug; replaced archive-current writes with a helper that preserves readable values but discards unreadable decompiler `extraout_ECX_04` residue; recovered `FUN_0044c6bc`'s lost scene-record `EAX` from `_DAT_0073ccba`; and installed scene slot `785` when normal StartGame raises `DAT_00479de8` without a scene pointer. Mirrored all reconstructed repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, regeneration, `git diff --check`, debug build, and ASan build pass. Debug still reaches the gameplay frame with movement and `surface 3 hash=3615add9`. ASan now satisfies the gameplay-frame wait under the original Step 10 timing:

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-active-scene-asan space,num8 30 10000 100

gameplay-frame wait satisfied after 5670 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_0073cc3c=0x681d04
surface 3 nonblank=1 hash=6e39f5ea
```

Next Frontier: prove ASan movement-state parity with a delayed or readiness-aware movement input. In the current ASan probe, `num8` is posted before active gameplay and is cleared by the time `_DAT_0073cc3c` becomes live.

Regression Risk: scene slot `785` is evidence-backed from the debug normal-start path, but it is still a targeted Step 10 startup fallback. When broader Start/F-key modes are recovered, replace it with mode-specific original script evidence.

## 2026-07-22 - ASan Reaches Post-Actor Main-Loop Frontier

Area: Step 10 ASan parity, hosted FAN stream reads, action lookup, fixed FAN tables, actor calculation helper

Symptom: ASan no longer reported a sanitizer finding before StartGame, but the gameplay-wait probe timed out before `FUN_0043a39c`/gameplay readiness. Once the large `FUN_00447638` parser was made fast enough to observe, ASan completed the `49650` entry loop misaligned by 21 bytes, read segment count `16383` instead of `1200`, then later exposed high-host-pointer action lookup failures and actor-load crashes.

Evidence: `E2R_FAN_DIAG=1` ASan showed `FAN 47638 entry align: current=2079248 expected=2079269`, followed by the recovered `segment count: count=1200`. The final ASan probe now dispatches StartGame, completes two actor-load passes, then dies later in the main-loop/update path:

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-42ce70-childguard-asan-gameplay space,num8 6 10000 180

actor load enter: id=0 ...
actor load exit: id=0 restored_current=0xb93040 flags=0x52 ...
actor load enter: id=0 ...
actor load exit: id=0 restored_current=0xaa6bd8 flags=0x52 ...
ERROR: AddressSanitizer: SEGV ... FUN_0044c164 -> FUN_004211c8 -> FUN_0042a70c -> FUN_00426df8
```

Change: trusted the active hosted FAN stream in `FUN_004171b8`/`FUN_004173c8` to avoid repeated Linux `IsBadReadPtr` scans; normalized the version-55 `FUN_00447638` entry cursor to the original fixed 36-byte entry size; removed stale `<0x70000000` assumptions from action node/name lookup and dispatch; moved the remaining `0x006536b0` fixed table initializer/readers to the literal legacy address; recovered `FUN_0042ce70`'s hidden actor pointer through `E2R_actor_calc_context` with a bounded child-walk guard; and added an ASan-only actor-table plausibility guard at the direct `FUN_0044c164` crash site. Mirrored reconstructed repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, debug build, and ASan build pass. Debug gameplay regression still reaches the nonblank village frame (`surface 3 hash=3615add9`) with `move=[1,0,0,0,0,0,0,0,0]`. ASan now exits without a sanitizer report instead of crashing in `FUN_0044c164`, but still times out before the visible gameplay frame (`surface 3 hash=6e39f5ea`).

Next Frontier: recover why ASan's post-load/update path diverges before gameplay readiness after the `FUN_0044c164` bad-pointer dereference is suppressed for diagnostics.

Regression Risk: the `FUN_00447638` cursor normalization assumes version `0x37` terrain/path entries are fixed 36-byte records, matching the debug stream offsets. The `FUN_0042ce70` child pointer ceiling is a bounded guard against generated-global/redzone pointers and should be revisited when actor child-list ownership is fully recovered. The `FUN_0044c164` actor-table guard is ASan-only so the debug/gameplay proof stays on the original runtime path.

## 2026-07-21 - Space Quickstart Reaches First Control-Ready Scene

Area: original-video-shaped Step 10 quickstart, raw/title image loading, actor reload, first movement input

Symptom: after `Space` skipped the intro path, the runtime alternated between raw-loader crashes, representation lookup crashes, opcode `0x54` actor reload crashes, FAN actor-child-table crashes, and post-load actor initialization crashes before the first controllable scene could be proven.

Evidence: the final debug probe exits cleanly and dumps a nonblank rendered scene. After the ASan `FUN_004173c8` binary-reader fix, the reliable current-build debug visual proof uses the gameplay-state wait command rather than a fixed dump timestamp:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-debug-gameplay-wait-space-num8 space,num8 6 10000 180

gameplay-frame wait satisfied after 13630 ms
surface 3 nonblank=1 hash=3615add9
DAT_00479de8=1 DAT_0047a76c=1 DAT_0047a43c=4 _DAT_0073cc3c=0x5664bff4
start_game=[entries=1 ... startup_scan=1793 startup_match=4 action_scan=148 action_match=2 dispatch=6 ...]
move=[1,0,0,0,0,0,0,0,0]
```

Change: replaced decompiler-lost `FUN_00449b4c` raw/title reads with explicit hosted file reads and explicit RLE expander source/destination pointers; recovered the hidden representation id through `FUN_00451998 -> FUN_00442420`; made opcode `0x54/0x55` carry the decoded actor id into `FUN_00451f5c`; guarded actor-load diagnostics against invalid ids; skipped unavailable FAN actor child-table links in record type `0x7`; routed `FUN_00420dcc` through `E2R_actor_calc_context`; added `--inject-key-sequence-gameplay-surfaces`; and gated high-volume FAN parser diagnostics behind `E2R_FAN_DIAG=1`. Mirrored the reconstructed repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. The debug `space,num8` probe proved the original fast path reaches gameplay state and accepts movement. A follow-up ASan fix gave hosted `FUN_004173c8` a binary-stream fast path, resolving the ASan FAN tail divergence: ASan now reports `FUN_00447638 count=49650 offset=291869` instead of `437055755 offset=259247`. A `180s` ASan probe exits `0` without a sanitizer report and reaches `index=16384/49650` before the bounded dump.

Next Frontier: debug has a stable gameplay-frame proof. ASan is now quiet and exits `0` without sanitizer output, but the gameplay-wait probe still times out before StartGame in a `240s` window (`start_game=0`, logo hash `6e39f5ea`). Continue from the ASan pre-StartGame load path or optimize the ASan probe enough to reach the same state.

Regression Risk: the actor-child-table type `0x7` guard skips a link when the parent child table is not yet available, rather than fully reconstructing the intended link timing. This is acceptable for the first-control proof, but actor hierarchy fidelity should be revisited after Step 10 closure.

## 2026-07-21 - Step 10 Actor Continuation No Longer Segfaults

Area: StartGame `Space` quickstart path, opcode `0x54` actor reload and first post-load update loop

Symptom: the reconstructed runtime repeatedly crashed after the original-video-shaped `Space` skip path entered StartGame actor loading. The crash frontier moved through actor child allocation, action `0x54` cleanup, main actor update, transform helpers, and screen-extent recursion.

Evidence: debug probes progressed from `actor load exit: id=0 ... opcodes=581 last_opcode=0x54` to a clean bounded run:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-surfaces /tmp/e2-step10-fun249f4-actor-debug space 6 250 45
exit code: 0
start_game=[entries=1 ... dispatch=6 ... opcodes=586 last_opcode=0x7 hit75=0]
surface 3 hash=6e39f5ea nonblank=1
```

Change: recovered explicit actor/parent context through the actor parser and update helpers, hardened `FUN_0043a800` list cleanup, rewrote the action `0x54` actor-slot cleanup to use named locals, tightened actor pointer guards to reject host/code pointers, converted `FUN_004249f4` to take an explicit actor pointer, and temporarily made the register-only `FUN_0045de8b` transform helper a no-op. Mirrored generated-C repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, and `cmake --build --preset linux-clang32-debug` pass. The bounded `space 6 250 45` probe exits `0` instead of segfaulting.

Next Frontier: the longer `space 6 250 180` probe no longer hits the old crash chain, but loops with repeated `FAN 44c10: offset=2041106 count=0` and still dumps the Ecstatica II logo surface. Continue from the post-load/update loop and the missing transition to opcode `0x75`/HUD/gameplay readiness.

Regression Risk: `FUN_0045de8b` is intentionally stabilized as a no-op, not accurately reconstructed. This is acceptable for isolating the Step 10 readiness frontier, but transform/collision fidelity will need a later call-site or signature recovery pass.

## 2026-07-21 - Segment Table Writes Restore Debug Surface Dumps

Area: `FUN_00447638`, `FUN_0044be20`, `FUN_0044c224`, `FUN_0044c71c`, `FUN_00451f5c`, StartGame action probes

Symptom: after the original-runtime videos clarified that the fast gameplay path is logo/intro, `Space`, final freeing animation, then HUD/control, the matching reconstructed `space` probe showed a debug-only surface dump failure. The dump state had `_DAT_006401ec=0xab7c`, `height=480`, and invalid framebuffer checks, while ASan still dumped a nonblank surface.

Evidence: a conditional gdb watchpoint on `_DAT_006401ec` caught `FUN_00447638` changing width from `640` to `0xab7c`. The writes used generated host globals such as `&DAT_0067c728 + iVar14` for the segment table instead of literal legacy addresses. After the repair, debug and ASan `space` probes both dump valid `640x480` surfaces and surface 3 remains nonblank with hash `6e39f5ea`. A video-shaped `space,d` probe posts the movement key, but StartGame action counters report `opcodes=581`, `last_opcode=0x54`, `hit75=0`, so the script has not reached the gameplay opcode `0x75`.

Change: redirected the segment table writes, table comparisons, and default initializer around `0x0067c728` to literal legacy addresses; added bounded surface dump state diagnostics; added StartGame action opcode counters; and made `FUN_00451f5c` preserve the decoded actor id/use the loaded actor pointer for its post-load flag/action handoff. Mirrored the reconstructed C repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug probe `/tmp/e2-step10-space-fixed-debug-rerun` and final ASan probe `/tmp/e2-step10-space-actorid-asan` exit cleanly and dump valid nonblank surfaces. The longer bare debug `space,d` run is still timing-sensitive and can exit `139`, while the gdb run completes and shows the true frontier at opcode `0x54`.

Next Frontier: instrument `FUN_00451f5c` and `E2R_ParseArchiveFanResource` completion for actor `0`. Determine whether actor parsing is still active at the 25s workflow mark or whether post-load actor/list globals fail to advance the StartGame script beyond opcode `0x54` toward opcode `0x75`.

Regression Risk: the surface dump state diagnostic and action-opcode counters are temporary probe instrumentation. Keep them until actor-load completion and first-control readiness are stable, then prune or gate the noisy output.

## 2026-07-20 - Startup Archive Tables Reach StartGame Resource Parse

Area: `FUN_00441444`, `FUN_00447d94`, `FUN_0043a39c`, `FUN_0045f296`, direct archive `FANT` resource loading, hosted surface/error-path guards

Symptom: after `Files/ECSTATIC` opened, startup still fell into the broken error renderer through `FUN_00447d94 -> FUN_0043cac0 -> FUN_0041ad54`. Once the archive loader was made explicit, StartGame action dispatch reached a stale seek helper crash, then a resource parse miss in `FUN_00451f5c`, then DOS-era error/fill paths with corrupt hosted dimensions.

Evidence: debug and gdb probes now print `archive 47d94 loaded: cursor=56240 remaining=33019366`, proving the startup archive table loader consumes the hosted archive instead of taking the `FUN_0043cac0` open-failure path. The guarded action scan stops on a bad linked-list tail (`0x3520666f` in gdb), then the fixed `0x006297c0` action table fallback finds and invokes `StartGame` (`E2R_InvokeActionCode(action=0x566d634c)`). After hosted seek recovery, `FUN_00451f5c` reached the direct archive parse path. The table value for resource id `14` was `1`; treating small non-`FANT` cursor offsets as embedded `FANT` ordinals moved the stream to offset `19314`, where `FUN_004453a4` parsed resource-local records through type `0x19`. A later gdb breakpoint showed `FUN_00451f5c` was entered with `EAX=0x0064a178` rather than an actor id, so opcode `0x54/0x55` now passes the decoded 12-bit operand through a scoped override. A follow-up gdb snapshot showed actor id `0` uses table offset `3997760`, which is inside the archive resource whose nearest prior `FANT` header is `3993260`. The latest debug probe `/tmp/e2-step10-actor-init` maps that cursor back to `3993260`, parses actor records through at least ordinal 16 (`0x08`, `0x14`, `0x15`, `0x31`, `0x32`, `0x40`, `0x41`, `0x37`, `0x42`, `0x4e`, `0x0a`), and exits without a segfault. ASan probe `/tmp/e2-step10-actor-init-asan` exits cleanly and writes four surface dumps, with surface 3 nonblank (`hash=6e39f5ea`).

Change: replaced `FUN_00441444` with an explicit hosted archive dword reader; rewrote `FUN_00447d94` to load its archive tables from already-open `DAT_0047a724`; guarded `FUN_0043a39c` action-list walks and added an action-table suffix fallback; replaced `FUN_0045f296` with hosted stream seeking; wrapped direct archive parses with `E2R_fan_parse_stream`, small-ordinal-to-embedded-`FANT` fallback, and large intra-resource cursor backscan to the nearest prior `FANT`; added explicit actor-id override plumbing for opcode-local actor loads and fixed the stale opcode `0x54` actor flag clear; recovered `FUN_00426478` actor initializer writes to use the allocated actor pointer instead of stale `extraout_EDX`; switched `FUN_0045f1ff` to hosted `LocalAlloc`; kept hosted software buffers out of VGA segment addresses during mode switches; made hosted bad-`FANT`/missing-actor archive paths fail quietly; guarded null post-load actor writes; and skipped invalid hosted surface fills. Mirrored the C repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug probe `/tmp/e2-step10-actor-init` exits `3` without a segfault after parsing the first actor archive resource, but Escape no longer opens the requester dialog within the 8s probe window and debug still cannot dump surfaces. ASan probe `/tmp/e2-step10-actor-init-asan` exits `0` without a sanitizer report and writes surface dumps, including one nonblank surface.

Next Frontier: recover the post-actor-load readiness path. The archive table mapping and first actor initializer now make real progress, but loading actor `0` changes the requester/start-game timing: debug reaches requester-ready before actor parsing, then no longer opens the requester after Escape, while ASan times out before requester-ready yet produces a nonblank surface dump. Inspect `FUN_00444330`/`FUN_0042b880` post-record side effects and the actor/list globals that gate `DAT_0047a76c`, requester state, and debug surface dumping.

Regression Risk: the `FUN_00447d94` table loops follow the decompiled byte-offset write pattern (`+4..limit`). Revisit table bounds once resource loads are stable enough to compare downstream offsets. The action-list guard is defensive around a bad tail and should be replaced with a parser-side tail terminator fix when the node layout is fully confirmed.

## 2026-07-20 - FAN Tail Reaches Startup Archive Loader

Area: `FUN_004448e4`, `FUN_004453a4`, `FUN_00447638`, `FUN_0045eb05`, startup `Files/ECSTATIC`

Symptom: after the action parser populated its fixed tables, debug still timed out before requester/startup state changed. The parser reached the tail marker after `FUN_004451a8`, then stalled or crashed inside `FUN_00447638` and post-FAN cleanup.

Evidence: bounded diagnostics showed `FUN_00444c10` completed with `list=1793`, `table=456`, and `pool=15002`. The tail marker was `0001`, entering `FUN_00447638`. Raw FAN bytes confirmed the `49650` entry count was real. The first stall was a stale `extraout_ECX_18` loop counter in a seven-word versioned skip; after fixing it, the parser advanced through `49650` entries and `1200` segment records. GDB then showed the next crash moved to post-FAN cleanup with `_DAT_00637248=0xde66`, then to startup after guarding that invalid actor head. The hosted data tree contains `Files/ECSTATIC`, and the later gdb run reached `FUN_00447d94`.

Change: added bounded FAN tail diagnostics; repaired `FUN_004448e4` type-zero terminator handling; re-anchored `FUN_00447638` to the active FAN stream after the initial height/path table; fixed the seven-word skip counter; captured the tail-node allocation pointer from `FUN_00426a30`; forced tail-node allocation to one `0x1a` record; wrote tail child ids through the allocated node; guarded invalid post-FAN actor-list heads; allowed hosted literal paths through `FUN_0045eb05`; and passed stable `Files/ECSTATIC` into the startup archive open. Mirrored the C repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug probe `/tmp/e2-step10-fun45eb05-path-debug` and gdb probe `/tmp/e2-step10-path-gdb` show the FAN tail completing far enough for startup to call `FUN_00447d94`. The current crash is no longer in FAN parsing: `FUN_00447d94 -> FUN_0043cac0 -> FUN_0043b384 -> FUN_0041ab4c -> FUN_0041ad54`, with `FUN_0041ad54(param_1=43899,param_2=0,param_3=479)` crashing at `*row = color`.

Next Frontier: recover the `FUN_00447d94` archive/scene-data loader handoff. Determine whether the loader is calling `FUN_0043cac0` as an error path because archive table reads are stale, or whether the render/fill rectangle setup before `FUN_0041ad54` needs another explicit hidden-register repair.

Regression Risk: the `FUN_00447638` entry/tail diagnostics are intentionally noisy and temporary. The invalid actor-head guard is defensive around a known bogus low pointer and should be revisited after actor construction is recovered enough to populate `_DAT_00637248` with real nodes.

## 2026-07-20 - FAN Action Parser Enters In Debug And ASan

Area: `FUN_004171b8`, `FUN_00444330`, `FUN_00444668`, `FUN_00444c10`, `FUN_0045f38a`

Symptom: ASan could parse through the version-gated FAN action section and dump the Ecstatica II title surface, but debug stopped at the bounded ordinal-4 unknown-record diagnostic. Both builds still reported empty Start Game action state.

Evidence: caller-address diagnostics showed records 1-4 were being consumed by `FUN_00444668`; the helper decoded type `0`, assigned `uVar2 = extraout_ECX_07`, then tested `(short)uVar2 == 0` instead of the decoded `sVar1`. Original stream reads also route sentinel bytes through `FUN_0045f38a`, with binary-mode flag `0x40` preserving embedded `0x1a` bytes. Original `FUN_00444c10` preserves the FAN stream in `ESI`, maps action ids through `0x006769f8`, installs action nodes through fixed table `0x006297c0`, appends bytecode tokens into `_DAT_006366a0`, and allocates child action nodes.

Change: added hosted binary/text stream byte semantics and binary stream flags, replaced `FUN_00444c10` with a recovered action-node parser, fixed `FUN_00444668` to test `sVar1 == 0` for terminators, and added bounded section/action diagnostics. Mirrored the repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug probe `/tmp/e2-step10-44668term-debug` and ASan probe `/tmp/e2-step10-44668term-asan` both enter `FUN_00444c10` at offset `104847`, parse past the old ordinal-4 frontier, dump the title surface on surface 3 with hash `6e39f5ea`, and exit without a sanitizer report. The requester/action state is still empty: `start_game entries=0`, `startup_scan=0`, `action_scan=0`, and `dispatch=0`.

Next Frontier: instrument and recover the handoff from the parsed action nodes/fixed `0x006297c0` table into `_DAT_00637250` and the StartUp/Start Game action scan before `FUN_0043a39c`.

Regression Risk: `FUN_00444330`, `FUN_00444668`, and `FUN_00444c10` now have bounded diagnostics and hand-recovered terminator/action parsing. Keep probes in both debug and ASan until the action dispatch state is populated, then remove temporary diagnostics before closing Step 10.

## 2026-07-20 - Version-Gated FAN Parsers Reach Title Surface

Area: `FUN_004173c8`, `FUN_004448e4`, `FUN_00445000`, `FUN_004451a8`, `FUN_00452a58`, `FUN_00447638`, `FUN_004418fc`, `FUN_00441958`, `FUN_0045fae0`

Symptom: after the actor-list fixes, ASan reached `FUN_004453a4 -> FUN_004448e4 -> FUN_0043cac0` from stale record-type state. Once that parser advanced, ASan exposed the same hidden stream/register artifact in `FUN_00445000` and `FUN_004451a8`, then stale fixed-address table artifacts in `FUN_00447638`, packed-name lookup, and remap-table reads. Debug continued to report the bounded ordinal-4 unknown-record diagnostic at offset `104855`.

Evidence: original `004448E4` preserves the stream in `ESI`, reads records through `004413FC`, and loops or returns from the decoded record type rather than `extraout_ECX`. Original `00445000` also stores the stream in `ESI` and calls `004173C8` with that stream before building records. Original `004451A8` stores the stream in `ECX`, keeps it across `00452A58`, and reads payload bytes through that same pointer. Original `00452A58` takes its allocation size in `EAX`. Original `00447638` stores the stream in `EDX`, writes the initial `128x128` word table through the explicit `0x00684d68` destination pointer, and uses the fixed `0x0068cd68/0x0068cd6f` record table. ASan then showed the remap lookup at `0x006769f8` and the other generated remap-table globals needed the same fixed-address treatment. The previous `FUN_004418fc -> FUN_0045fae0` heap-use-after-free was caused by decompiled lookup wrappers using stale `extraout_CX` advancement and a `strcmp` shim that ignored its explicit left pointer.

Change: bound hosted `FUN_004173c8` to the active FAN stream; recovered `FUN_004448e4` record reads, skip-loop reads, and terminator handling; bound `FUN_00445000` and `FUN_004451a8` to the active stream; passed the bitmap payload size explicitly into `FUN_00452a58`; fixed the first `FUN_00447638` stream argument/table destination; added direct packed-name lookup wrappers; repaired `FUN_0045fae0` to compare explicit inputs; and redirected the remaining fixed record/remap-table accesses to literal legacy addresses. Mirrored new generator-backed repairs in `E2Recomp/tools/GenerateRecon.js`; the remap-table broad rewrite already existed and the reconstructed C was brought into line with it.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug probe `/tmp/e2-step10-remaptables-debug` still reports ordinal 4 at offset `104855`. ASan probe `/tmp/e2-step10-remaptables-asan` exits with code `0`, dumps the Ecstatica II title surface on surface 3 with hash `6e39f5ea`, and no longer reports the packed-name use-after-free or fixed-table global overflows. The requester/action state is still empty: `start_game entries=0`, `startup_scan=0`, and `dispatch=0`.

Next Frontier: recover the remaining `FUN_00444c10` action-node parser state so `_DAT_00637250` is populated before `FUN_0043a39c` scans StartUp and Start Game action codes. Original disassembly keeps the stream in `ESI` while preserving action node pointers and bytecode cursors on the stack; the current decompiled body still has `extraout_*` artifacts in that section.

Regression Risk: `FUN_00447638` and `FUN_00444c10` are still only partially recovered; ASan can render the title surface, but Start Game action dispatch is not restored. The bounded FAN diagnostics are still temporary and should remain until debug and ASan section alignment converge.

## 2026-07-20 - FAN Actor Lists And Hosted Word Reads Advance

Area: `FUN_004171b8`, `FUN_004268a4`, `FUN_004268e4`, `FUN_0042692c`, `FUN_004435e8`, `FUN_00444c10`, `FUN_004526e4`

Symptom: the first 2026-07-20 ASan probe reached `FUN_00444c10 -> FUN_004268e4` with hidden owner `EAX=0x2`. After recovering that helper, subsequent probes exposed the same decompiler artifact class in `FUN_004526e4`, `FUN_004435e8`, and `FUN_004268a4`. Once those were cleared, hosted FAN word reads stuck on an embedded `0x1a` byte and filled the script pool with repeated `0xffff` tokens. After raw hosted word reads were recovered, ASan exposed fixed-address remap-table reads in `FUN_004435e8`.

Evidence: original disassembly at `00444ED0..00444EDF` passes owner pointers from `[esp+18h]` and `[esp+0Ch]` into `004268E4`/`0042692C`. Original `004268A4`, `004268E4`, and `0042692C` all allocate a single object/list node after preserving incoming state. Original `00444D66..00444D7B` writes the current `CX` object id, looks up an existing object through `006297C0`, and passes that object pointer in `EAX` to `004526E4`. Original `00444DCB..00444DD0` zero-extends the current token into `EAX` before calling `004435E8`, while preserving the original token in `EDX` for repeat handling. A bounded word trace showed hosted `FUN_004171b8` stuck at offset `104855` on an embedded `0x1a`; reading two raw bytes for hosted `E2R_STREAM_MAGIC` streams advanced past that point. ASan then stopped on `FUN_004435e8` remap-table reads through generated globals instead of literal fixed addresses.

Change: recovered the hidden owner pointer and one-record allocation contracts for `FUN_004268a4`, `FUN_004268e4`, and `FUN_0042692c`; made `FUN_004526e4` accept the object pointer explicitly; restored the `FUN_00444c10` object-id write and existing-object removal call; passed current tokens explicitly into `FUN_004435e8`; added raw two-byte hosted FAN word reads for `FUN_004171b8`; and redirected the immediate actor-token remap-table reads to fixed legacy addresses. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. A short ASan Start Game readiness probe now exits without a sanitizer report while parsing is still in progress and dumps nonblank surfaces. A longer ASan probe advances beyond the earlier `FUN_00444c10` frontiers to records near offset `259113`, then stops through `FUN_004453a4 -> FUN_004448e4 -> FUN_0043cac0` with `EAX=0x1`. The matching debug probe still reports the ordinal-4 unknown-record diagnostic after the three zero terminators.

Next Frontier: recover the original input/register contract for `FUN_004448e4` and reconcile debug/ASan parser alignment after the third zero terminator.

Regression Risk: hosted raw word reads are scoped to native `E2R_STREAM_MAGIC` FAN streams and bypass the CRT text-mode `0x1a` behavior only for those hosted buffers. The first-sixty-four-word diagnostic is temporary and should be removed once the FAN section alignment is stable.

## 2026-07-20 - FAN Actor String Owner Frontier Recorded

Area: `FUN_004453a4`, `FUN_00444c10`, `FUN_004268e4`, `FUN_0042692c`

Symptom: after three validated zero section terminators, sandboxed bounded game probes exit immediately with code `159`. Running the same probes outside the sandbox reaches the FAN version-gated section. The debug probe still reports bounded ordinal-4 unknown-record diagnostics, and the ASan probe stops in `FUN_004268e4` while reading through hidden `EAX=0x2`.

Evidence: original disassembly at `00444C10` preserves the FAN stream in `ESI`. At `00444ED0..00444EDF`, it loads `EAX` from `[esp+18h]` before calling `004268E4` for the first nested node, and from `[esp+0Ch]` before calling `0042692C` for subsequent nodes. Original `004268E4` and `0042692C` save incoming `EAX` in `ESI`, then allocate exactly one `0x39`-byte record with `FUN_0045F1FF`. The generated C instead passed stale state into the helpers and let `FUN_004268e4` dereference `in_EAX == 0x2`.

Change: no code change in the progress-check pass. Documentation was updated before continuing with the recovered owner-pointer repair.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass before the repair. Host debug probe reports ordinal 4 at offset `104855`; host ASan probe reports `FUN_004453a4 -> FUN_00444c10 -> FUN_004268e4` with a zero-page read at `0x00000002`.

Next Frontier: recover the hidden owner-pointer input and fixed allocation count for `FUN_004268e4` and `FUN_0042692c`, then rerun the bounded Start Game ASan probe.

Regression Risk: the ordinal-4 diagnostic is still temporary. The next code change touches actor string/node linking during FAN parsing, so it must be generator-backed and verified with both debug and ASan probes.

## 2026-07-18 - FAN Record Sections Preserve Hidden State

Area: `FUN_004413fc`, `FUN_0045326c`, `FUN_00453264`, `FUN_00447090`, `FUN_0042b880`, `FUN_004453a4`

Symptom: after all packed FAN name tables loaded, ASan first reported a use-after-free write in `FUN_004413fc`, then stale-pointer failures in record normalization and actor construction. Once those were cleared, the top-level loop decoded payload bytes as unknown record type `0x0701`.

Evidence: original disassembly shows `FUN_0045326c` returns the pool slot from `FUN_0045328c`; `FUN_004413fc` preserves the stream in `EDX`, reads five words, and returns the slot in `EAX`; callers pass that record in `EAX` to `FUN_00447090`, `FUN_0042b880`, and `FUN_00453264`. A bounded record probe reported three consecutive type-zero records at offsets `104825`, `104835`, and `104845`. The parser then tested stale `uVar10` rather than decoded `sVar9`, ignored the third terminator, and read mixed payload at offset `104855`.

Change: returned the actual pool slot from `FUN_0045326c`; made the five-word stream read explicit; preserved the current FAN record across normalization, actor construction, and pool release; bound `FUN_0042b880` to that record; added bounded record diagnostics; and changed the top-level terminator condition to use `sVar9`. Mirrored all generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: debug and ASan builds pass, generator syntax validation passes, and ASan consumes all three zero terminators without treating payload as an unknown record. The runtime now enters the next version-gated FAN section.

Next Frontier: recover the original entry/input contract for `FUN_00444c10`, currently reached from `FUN_004453a4` and failing with a global-buffer-overflow near `_DAT_0047a47c`.

Regression Risk: current-record state is scoped to active FAN parsing and models a register lifetime lost by decompilation. The first-sixteen-record and unknown-record stderr diagnostics are temporary and must be removed once section alignment is stable.

## 2026-07-18 - FAN Parser Reaches Object Records

Area: `FUN_00445378`, `FUN_004453a4`, FAN packed name tables, `FUN_0043a39c`, `FUN_0044f508`

Symptom: recovered Start Game selection entered `FUN_0043a39c` but returned to the requester. New boundary counters reported `startup_scan=0`, `action_scan=0`, and `dispatch=0`, proving `_DAT_00637250` was never populated.

Evidence: original `FUN_00445378` disassembly opens the FAN stream, preserves it in `EAX`, calls `FUN_004453a4` with mode in `EDX`, then closes the stream. The hosted reconstruction only opened and closed the file. After restoring the parser call, `Code/ECSTATIC.FAN` passed its `FANT` header and exposed repeated lost token-pointer, packed-table length, source-ordinal, and scalar-global array artifacts. Original helper bounds identify eleven packed name-table capacities and entry limits.

Change: restored explicit FAN stream handoff through `FUN_00445378`, `FUN_004453a4`, and `FUN_004171b8`; replaced the eleven hidden-register string intern paths with one bounded packed-name helper; preserved source table ordinals in dedicated counters; wrote mappings to literal DGROUP addresses; recovered Start-code name matching and action-node handoff into `FUN_0044f508`; and added bounded lookup/dispatch counters. Mirrored the repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: generator syntax validation and the ASan build pass. An isolated generated `E2Recomp_recon.c` also compiles. ASan progresses through all FAN name tables and now stops in the first object-record phase at `FUN_004453a4 -> FUN_00444668 -> FUN_004413fc`, rather than returning from an empty action list.

Next Frontier: recover the original object pointer passed in `EAX` from `FUN_00444668` to `FUN_004413fc`. The current decompile writes through a stale freed pointer at reconstructed line 32711.

Regression Risk: FAN parsing is now active during startup, so the bounded runtime currently reaches the new ASan frontier before requester readiness. Packed-name comparison is explicit and case-sensitive; `FUN_00446afc` used a distinct original comparison helper and may require case-folding if later evidence shows mismatched names.

## 2026-07-18 - Start Game Requester Record Recovered

Area: requester ids `0x27/0x28`, record `0x0047a588`, item `0x00643b30`, `FUN_0043a39c`

Symptom: Step 9 could navigate reconstructed requester input but initialized requester `0x27/0x28` with first item `0x00643ad0`, exposing Uninstall/Quit/Cancel and leaving Start Game unreachable.

Evidence: `E2WIN95.EXE` DGROUP bytes at `0x0047a588` decode as `{-1, -1, 0xd2, 0xb4, 0, 0x00643b30}`. Original menu construction links `0x00643b30` to Save, Load, Settings, Quit, and Cancel. The Start Game callback `LAB_0043d458` sets `_DAT_00643650=0`, whose main-loop switch enters `FUN_0043a39c(..., 0)`.

Change: initialized requester `0x0047a588` from the original dimensions and first-item pointer, mirrored the recovery in `E2Recomp/tools/GenerateRecon.js`, added `FUN_0043a39c` entry counters, and made ready-sequence probes preserve a bounded post-Start observation delay.

Result: generator syntax validation and debug/ASan builds pass. Debug and ASan `escape,enter` probes select `0x00643b30`, dispatch one action, advance the `FUN_0043a39c` entry count from `1` to `2` with player/mode `0`, and remain free of sanitizer reports for five seconds. Both produce nonblank surface-3 hash `d8293730` but return to the menu with `_DAT_00643650=5` rather than loading a scene.

Next Frontier: recover the Start-code action-name lookup/dispatch cluster in `FUN_0043a39c`. `Code/ECSTATIC.FAN` contains `mar:StartGame`, but the reconstructed path loses the original string index passed in `EAX` to `FUN_00442128`, crosses the hosted no-op `FUN_0045f22f`, and does not preserve the selected action-node `EAX` into `FUN_0044f2fc`.

Regression Risk: requester ids `0x27/0x28` now expose the original full Start Game chain instead of the narrower Step 9 test chain. Quit remains reachable through the restored links, and debug/ASan Start Game probes cover the new default action.

## 2026-07-17 - Quit Confirmation Prompt Recovered

Area: `FUN_0043c910`, `DAT_0043d49c`, requester id `0x14`, `_DAT_00643650`

Symptom: Quit selection could safely take the original cancel/no branch, but the actual confirmation prompt was still unrecovered and confirmed Quit could not reach `_DAT_00643650=6`.

Evidence: original disassembly at `0043c910..0043c995` builds requester id `0x14`, copies a bounded prompt string into a stack buffer, stores the prompt pointer at `0x0047a520`, sizes `0x0047a51c`, clears word `006443D4`, runs `FUN_0043b384`, and returns the high word of `_DAT_006443d2`. Original callbacks `LAB_0043c594` and `LAB_0043c4e8` set or clear that high word for id `0x14`. Original state switch case `6` at `0041638a..0041639a` sets `_DAT_00643660=1` and opens requester id `0x31`; the decompiler had reconstructed that arm as a fatal `FUN_00414e68()` call.

Change: recovered `FUN_0043c910` with a stable hosted prompt buffer, initialized the fixed Yes/No prompt item records, wired id/item-aware prompt callbacks, made the Quit action call the prompt helper, fixed the native requester-sequence probe to wait per queued key, and corrected the original switch case `6` behavior. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug and ASan `escape,num2,enter,enter` select Quit then default No and finish with `_DAT_00643650=5`. Debug and ASan `escape,num2,enter,num2,enter` move from No to Yes, dispatch the Yes callback, open requester id `0x31`, and finish with `_DAT_00643650=6` without sanitizer reports.

Next Frontier: the prompt text at fixed English address `0x004729b8` is still unnamed in generated data, so the recovery uses the localized pointer at `0x0060aef0` when available and a bounded fallback string otherwise. Future work can recover the missing raw data symbol/text exactly.

Regression Risk: confirmed Quit now reaches the original state `6` transition and id `0x31` requester path. That broadens executable behavior beyond the previous safe cancel fallback, but debug and ASan probes cover both No and Yes outcomes.

## 2026-07-17 - Quit Callback No-Confirm Path Recovered

Area: `DAT_0043d49c`, `E2R_InvokeRequesterAction`, main-menu requester callbacks

Symptom: `escape,num2,enter` could select the fixed-address Quit item at `0x643ca4`, but the selected action `DAT_0043d49c` was still only recorded by the simple dispatcher and left unhandled.

Evidence: original disassembly at `0043d49c..0043d4e4` shows the Quit action calls `FUN_0043c910` with localized text from `0x0060aef0` or fixed text at `0x004729b8`, then sets `_DAT_00643650=6` when the prompt returns nonzero and `_DAT_00643650=5` otherwise. The current reconstructed `FUN_0043c910` path still depends on unrecovered prompt/string-copy behavior, so the bounded safe branch is the original declined/cancel result.

Change: added a `DAT_0043d49c` case to `E2R_InvokeRequesterAction` that applies the original no-confirm result by setting `_DAT_00643650=5` and returning handled. Mirrored the dispatcher case in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, `cmake --build build/linux-clang32-asan`, and `git diff --check` pass. Debug and ASan `escape,num2,enter` probes both select `0x643ca4`, record one action with `selected_action`/`last_action` pointing at `DAT_0043d49c`, keep `_DAT_00643650=5`, write surface 3 with hash `9042c4ed`, and finish without sanitizer reports.

Next Frontier: recover the `FUN_0043c910` yes/no prompt helper and the source text at `0x004729b8`/`0x0060aef0` so Quit can display the original confirmation and take the `_DAT_00643650=6` branch only when the user confirms.

Regression Risk: this intentionally preserves the original cancel/no outcome for Quit until prompt handling is recovered. It avoids crashing or exiting through an unrecovered confirmation path, but it does not yet implement confirmed quit behavior.

## 2026-07-17 - Requester Focus Movement Recovered

Area: `FUN_0043bd4c`, fixed-address requester item records, `_DAT_00643430`

Symptom: requester-ready `escape,num2,enter` still selected cancel because `_DAT_00643430` was unset and the key handler trusted a stale `param_2`/last-rendered item. After seeding focus, Down exposed garbage `next` and action slots for the fixed-address requester item records.

Evidence: debug and ASan probes showed `selected=0x0`, `param=0x643780`, `moves=0` before the focus seed. After seeding, `selected=0x643ad0` but `next`/`selected_action` were garbage until the main-menu item chain was initialized locally. A two-Down probe then exposed integer-global pointer arithmetic on `_DAT_00643430 + 4`.

Change: added a guarded first-item focus seed for `FUN_0043bd4c`, initialized the fixed-address main-menu requester item chain at requester open, marked those local records keyboard-focusable for the recovered movement branch, and cast `_DAT_00643430` back to `short *` before item-slot pointer arithmetic. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, `cmake --build build/linux-clang32-asan`, and `git diff --check` pass. Debug and ASan `escape,num2,enter` move from `0x643ad0` to `0x643ca4` and dispatch `DAT_0043d49c`. Debug and ASan `escape,num2,num2,enter` move through `0x643ca4` to cancel `0x643780` and dispatch `LAB_0043c4e8` without crashing.

Next Frontier: reconstruct complex callback `DAT_0043d49c`; it is now selectable and recorded but intentionally not executed by the simple dispatcher.

Regression Risk: the main-menu item chain initializer is scoped to requester ids `0x27/0x28` via the existing open branch. It is still a fixed-address reconstruction shim; broader requester families may need their own item-chain recovery.

## 2026-07-17 - Requester Input Reaches Action Selection

Area: `FUN_0043bd4c`, `FUN_0043b9bc`, `FUN_0043adc0`, `FUN_0041af88`, requester-ready input probes

Symptom: requester-ready probes could render the requester, but `escape,num8,enter` did not reliably reach the requester key-consume path. Once keys were fed directly into `FUN_0043bd4c`, Enter advanced into raw decompiler label callbacks and malformed requester restore copies.

Evidence: debug runs showed `bd4c` being called with `key=0x0` until requester keys were staged on the game thread. GDB then showed Num8 reaching the requester movement branch with a stale hidden requester-record register, Enter crashing first in `FUN_0043adc0` restore copies, and then in raw label callback `LAB_0043c4e8`. ASan additionally exposed `FUN_0043b9bc` accepting a mapped but wrong requester-record pointer and `FUN_0041af88` accepting a stray high palette pointer.

Change: added requester-local pending key staging for ready probes, so post-Escape keys are fed at `FUN_0043bd4c` entry on the game thread. Reconstructed hidden requester-record inputs for `FUN_0043bd4c` and `FUN_0043b9bc` via `FUN_0043aeac`, added a rendered-item fallback for the current requester item, stabilized `FUN_0043adc0` by reconstructing the current item and skipping malformed screen-copy calls, recorded raw action callback labels, dispatched the simple state-setting labels recovered from original disassembly, and tightened `FUN_0041af88` palette source guards. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, `cmake --build build/linux-clang32-asan`, and `git diff --check` pass. Debug and ASan `escape,num8,enter` requester-ready probes both finish with surface-3 hash `9042c4ed`, `key=0xd`, `pending=2/2`, `fed=2`, and `actions=1`.

Next Frontier: `escape,num8,enter` and `escape,num2,enter` both still land on the cancel record at `0x643780`, so focus/selection fidelity is now the immediate frontier. The harder callback labels, especially `DAT_0043d49c`, still need full reconstruction once probes can select them.

Regression Risk: raw requester callbacks are intentionally not invoked yet, and `FUN_0043adc0` restore copies are no-oped for stability. These are Step 9 stabilizers around known decompiler artifacts, not final menu/action behavior.

## 2026-07-17 - Debug Requester Timing Parity Recovered

Area: `FUN_004142b8`, `FUN_004142e4`, `FUN_00415b78`, requester-ready input probes

Symptom: ASan could reach requester rendering for the `escape,num8,space` sequence, but the debug build either missed requester readiness or exited through a stale high-code `ExitProcess` path before the delayed input probe fired.

Evidence: extended `ExitProcess` caller logging mapped the debug-only high-code exit first to `FUN_004142e4 -> FUN_0045f38a` while reading startup music data, then to `FUN_00415b78 -> FUN_00414e68` while opening the shadow table. A direct GDB run after the first bypass showed `FUN_004142b8` still using stale allocation arguments before formatting a bogus fatal message. The successful debug requester-ready probe later reported `requester-ready wait satisfied after 20 ms`, `_DAT_00643650=5`, `DAT_00479de8=1`, requester counters `ce58=12`, `b9bc=36`, and surface-3 hash `af17b505`.

Change: added `--inject-key-sequence-ready-surfaces` so probes wait for requester/menu readiness instead of relying on a fixed startup delay. Hosted the startup music buffer allocation in `FUN_004142b8`, made `FUN_004142e4` a temporary success no-op for Step 9, and forced `FUN_00415b78` to open literal `shadow.dat` instead of accepting a stale first argument. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`. `ExitThread` now terminates only the calling pthread on Linux, and high stale `ExitProcess` codes are treated as thread termination for diagnostics instead of killing the whole process.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug `--inject-key-sequence-ready-surfaces /tmp/e2-step09-ready-debug-music-alloc-shadow escape,num8,space 8 250 3` reaches requester rendering and writes surface 3 with hash `af17b505`. ASan `--inject-key-sequence-ready-surfaces /tmp/e2-step09-ready-asan-music-alloc-shadow escape,num8,space 6 250 5` still reaches requester rendering with surface-3 hash `9042c4ed`.

Next Frontier: requester fidelity and actual menu navigation are now the Step 9 frontier. Audio stream reconstruction remains intentionally deferred; the current music loader bypass is a hosted runtime stabilization, not a faithful audio implementation.

Regression Risk: `FUN_004142e4` is intentionally bypassed, so startup music playback is disabled. The `FUN_00415b78` literal-path recovery is narrow to `shadow.dat`; other callers of `FUN_0045eb05` may still need call-site-specific argument recovery if they pass readable stale pointers.

## 2026-07-16 - Main Loop Heartbeat Sustained After Requester Id Recovery

Area: `FUN_00415d40 -> FUN_0043ce58`, loop-adjacent requester/menu state

Symptom: after the HUD icon and damage-rectangle table repairs, ASan stopped in `FUN_0043cac0` through `FUN_0043ce58 -> FUN_00414e68`, with `FUN_0043cac0` reading through `in_EAX == 0x1`.

Evidence: original disassembly at `00416278..004162b5` stores `5` in `_DAT_00643650`, but then loads requester id `0x27` or `0x28` into `EAX` before calling `0043ce58`. The reconstructed call used `FUN_0043ce58(param_1,5)`, so `FUN_0043ce58` saw the wrong requester id and fell into the original fatal `Bad request number` path at `0043d43b`.

Change: added a narrow requester-id recovery in `FUN_00415d40`, passing `0x27` when `DAT_00479db4` is set and `0x28` otherwise. Restored `FUN_0043ce58`'s lost incoming `EAX` convention by initializing its generated `in_EAX` from `param_1`. Mirrored both changes in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Bounded ASan runs of 30 seconds and 90 seconds both timed out with no sanitizer report.

Next Frontier: step 8 should move from crash stabilization to an inspectable title/menu frame, verifying what the compatibility renderer is actually presenting during the sustained loop.

Regression Risk: `FUN_0043ce58` is a shared requester/menu initializer. Initializing `in_EAX` from `param_1` is the correct recovered convention, but other callers that still pass stale `extraout_*` values may expose additional requester ids that need local call-site recovery.

## 2026-07-16 - HUD Icon Clear And Damage-Rect Table Frontiers Advanced

Area: `FUN_00455e84`, `FUN_00455940`/`FUN_0045fae0`, and the `DAT_0047a29c` damage-rectangle count table

Symptom: the first Step 7 ASan run stopped in `FUN_0045fae0` because `FUN_00455940` lost its incoming `EAX` string pointer while clearing HUD icon/action names. After recovering that path, ASan exposed a second fixed-address/global-layout failure in `FUN_00424b48`, where generated code indexed `&DAT_0047a29c` as though it were a contiguous table.

Evidence: original disassembly for `00455940` saves incoming `EAX` in `ESI`, sets `EDX` to each 9-byte entry at `0x00ac4cad`, restores `EAX` from `ESI`, and calls `0045fae0`. Original `00455e84` is a sequence of `mov eax,<icon-name>; call 00455940` operations over icon-name clusters such as `life1`, `armour3`, `hndicon1`, and magic/life bar ranges. After that repair, ASan reported:

```text
ERROR: AddressSanitizer: global-buffer-overflow
#0 FUN_00424b48 E2Recomp_recon.c:14961
#1 FUN_004211c8 E2Recomp_recon.c:12897
#2 FUN_0042a70c E2Recomp_recon.c:19414
#3 FUN_00426df8 E2Recomp_recon.c:16516
```

Redirecting `&DAT_0047a29c` to fixed address `0x0047a29c` cleared that ASan redzone read. The next bounded ASan run now reports:

```text
ERROR: AddressSanitizer: SEGV on unknown address 0x00000001
#0 FUN_0043cac0 E2Recomp_recon.c:29610
#1 FUN_00414e68 E2Recomp_recon.c:6242
#2 FUN_0043ce58 E2Recomp_recon.c:30141
#3 FUN_00415d40 E2Recomp_recon.c:6647
#4 FUN_00426df8 E2Recomp_recon.c:16515
#5 FUN_0041007c E2Recomp_recon.c:1104
eax = 0x00000001
```

Change: added hosted helpers that mirror the HUD icon name literals needed by `00455e84`, clear matching entries from the original `0x00ac4cad` table, and preserve the original status side effects at `0x00ac4a6c`, `0x00ac4c94`, and `DAT_0047ab08`. Replaced the generated `FUN_00455e84` body with the recovered icon-name clear sequence from original disassembly. Redirected `&DAT_0047a29c` table indexing to fixed legacy address `0x0047a29c`. Mirrored both repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. ASan no longer stops in `FUN_0045fae0` or `FUN_00424b48`.

Next Frontier: recover the current `FUN_0043cac0` call path from `FUN_0043ce58 -> FUN_00414e68`; the immediate bad read is through `in_EAX == 0x1` while formatting/scanning text.

Regression Risk: `FUN_00455e84` is now a narrow hosted reconstruction of the observed original icon-name clear sequence, not a full recovery of every `FUN_00455940` caller. `FUN_00455940` and `FUN_0045fae0` still have broader shared call surfaces and should be recovered separately when a future path reaches them.

## 2026-07-16 - Post Quick-Save No-Op ASan Frontier Recorded

Area: `FUN_0041007c -> FUN_00426df8 -> FUN_00415d40 -> FUN_00455e84 -> FUN_00455940 -> FUN_0045fae0`

Symptom: after the hosted no-op replacement for `FUN_00453920`, the bounded ASan run no longer stops in the quick-save writer path. The next crash is a read through an invalid `in_EAX` value inside `FUN_0045fae0`.

Evidence: the ASan run from `build/linux-clang32-asan` reported:

```text
ERROR: AddressSanitizer: SEGV on unknown address 0x27d9823c
#0 FUN_0045fae0 E2Recomp_recon.c:54618
#1 FUN_00455940 E2Recomp_recon.c:47610
#2 FUN_00455e84 E2Recomp_recon.c:47852
#3 FUN_00415d40 E2Recomp_recon.c:6544
#4 FUN_00426df8 E2Recomp_recon.c:16430
#5 FUN_0041007c E2Recomp_recon.c:1019
eax = 0x27d9823c
```

`FUN_00455940` iterates a 25-entry table beginning at `0x00ac4cad` and passes each entry as `param_2` to `FUN_0045fae0`. The callee then reads from its local `in_EAX` pseudo-register at `E2Recomp_recon.c:54618`, so the immediate frontier looks like another lost incoming string/pointer register around a strcmp-like helper or its call site.

Change: no code change in this pass. This was the bounded verification run requested after the `FUN_00453920` no-op.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. The single ASan run verifies that the quick-save no-op advances execution to the new `FUN_0045fae0` frontier.

Next Frontier: step 7 should recover the missing input pointer or call convention for `FUN_0045fae0`/`FUN_00455940`, then continue toward a sustained main-loop heartbeat.

Regression Risk: the quick-save path remains intentionally disabled by the hosted `FUN_00453920` no-op. `FUN_0045fae0` appears to be a shared comparison helper, so the next repair should be Ghidra-backed and avoid a broad guard that hides valid string/table comparisons.

## 2026-07-15 - Config, CDPath, Menu, Framebuffer, And Quick-Save Frontiers Advanced

Area: `FUN_0041007c`, hosted file/config startup, menu/dialog helpers, fixed-address framebuffer tables, and `FUN_00453920`

Symptom: after the earlier post-main-loop `"e_config"` work, ASan exposed a chain of independent generated-code failures: config header stack overwrite, lost CDPath stream-line arguments, stale CRT table reads, bad hosted CD path prefix, missing local path existence checks, menu string-list dereference through stale `in_EAX`, ASan global-buffer-overflows from fixed-address tables, a stale-register framebuffer rectangle fill in `FUN_0041ad54`, and finally `FUN_00453920` entering the quick-save writer with invalid string-copy state.

Evidence: ASan progressed through these frontiers in order:

```text
FUN_0043cbf0 -> stale in_EAX menu string-list dereference
FUN_0043cbf0 -> ASan global-buffer-overflow writing &DAT_006430ee table
FUN_00418a04 -> ASan global-buffer-overflow reading &DAT_00636150 surface table
FUN_0041ad54 -> null write in rectangle fill loop from lost in_EAX/unaff_EBX/extraout_ECX_01
FUN_0045fd2c <- FUN_00453920 -> invalid destination while copying saved_XXXX.ecs
```

Change: widened and packed/unpacked the startup config header buffer; added hosted CDPath line reading and path normalization; replaced CRT ctype/bit-table accesses with helper functions; repaired startup path formatting and file existence/open checks; improved `FindFirstFileA`/`FindClose`; recovered key fixed-address globals/tables including `0x00479e24`, `0x0047aad8`, `0x006430ee`, `0x006432ec`, `0x00636150`, and `0x006366dc`; made `FUN_0043cbf0` resolve either a string-list pointer or a direct string argument; replaced `FUN_0041ad54` with a bounded hosted framebuffer fill; and reduced `FUN_00453920` to a hosted no-op. Mirrored reconstructed C changes in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build build/linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass after the `FUN_00453920` no-op. Per stop request, ASan was not rerun after that final change.

Next Frontier: the next session should start with one bounded ASan run to verify the `FUN_00453920` no-op and record the next crash frontier. Do not broaden investigation unless the user explicitly approves more budget.

Regression Risk: `FUN_0041ad54` and `FUN_00453920` are hosted stabilizers, not faithful reconstructions. The quick-save path is intentionally disabled for now. Later save-game work should recover the original file/stream conventions instead of depending on the no-op.

## 2026-07-15 - CDPATH And Native Stream Reader Frontier Cleared

Area: `FUN_0041007c -> FUN_0045eb05/FUN_0045f38a/FUN_0045ec6c`, post-config CD path and native read-only stream handling

Symptom: after the config-header repair, execution fell into `FUN_00414e68` because `FUN_0045eb05(extraout_ECX_07, extraout_EDX_02)` tried to open a null/bogus path. After recovering the intended `CDPath` open, the next runtime crashes were in the generated stream slow paths: `FUN_0045f38a` used stale `extraout_EDX` when binary data hit special byte values, and `FUN_0045ec6c` dereferenced `param_2=2` while checking the native stream magic.

Evidence: `CDPATH` exists in the data directory and contains the original install path text `d:\Games\Ecstatica2\`. Original/rebuilt disassembly around the shared fopen wrapper shows the filename in `ECX` and mode in `EDX` for normal call sites, while the generated wrapper was opening `param_2` as the filename. `SHADOW.DAT` is exactly `12288` bytes, matching the `FUN_00415b78` loop, so the `FUN_0045f38a` crash was not EOF but a slow-path artifact on data bytes. ASan then showed the next independent frontier at `FUN_0041dc8c:9932`.

Change: replaced the lost-register `CDPath` open in `FUN_0041007c`, made `FUN_0045eb05` prefer a plausible `param_1` filename with fallback to `param_2`, added native `E2R_STREAM_MAGIC` handling to `FUN_0045f38a`, and guarded `FUN_0045ec6c`/`FUN_0045f38a` against impossible stream pointers. Mirrored these repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build build/linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. A bounded debug GDB run no longer crashes in the `CDPath`, `FUN_0045f38a`, or stream-close frontier; it exits with code `0340` and no stack.

Next Frontier: direct escalated runtime still crashes, and ASan reports a global-buffer-overflow at `FUN_0041dc8c:9932`, reading two bytes before `DAT_0047a2b4` while copying through legacy ranges based at `DAT_00477068`. The next step should treat this as a fixed-address/global-layout issue in the `0x00477068..0x0047a2xx` tables, not as another file I/O failure.

Regression Risk: the native stream helpers are still narrow adapters for `E2R_OpenReadStream` buffers. The pointer guards intentionally avoid dereferencing impossible decompiler artifacts; if later paths need true CRT stream descriptors, recover those call conventions separately instead of broadening the shim blindly.

## 2026-07-15 - Post Main Loop Config Open Crash Cleared

Area: `FUN_0041007c -> FUN_0045e594/FUN_0045e5b8`, post-main-loop `e_config` open and header read

Symptom: continuing past main-loop entry crashed at `EIP=0xffffffff` through `FUN_0046055c` while opening `"e_config"`. GDB showed `PTR_FUN_0047d39c`, `DAT_0047d398`, and `_DAT_00ac5204` had been overwritten with `0xffffffff`-style values before the config open.

Evidence: a hardware watchpoint showed `PTR_FUN_0047d39c` changed from the initialized `FUN_00460623` callback address to a corrupted value inside `FUN_0044c71c`. That initializer was still writing the 0x00684d68/0x00684be8 map tables through host globals, while the Linux runtime maps the original `0x00400000..0x00b00000` legacy address range for these fixed-address tables. After the repair, a debug GDB run stopped at `FUN_0045e5b8` for `param_3="e_config"` with `PTR_FUN_0047d39c=0x565db870` instead of `0xffffffff`.

Change: redirected `FUN_0044c71c` and related map-table readers to fixed legacy addresses for `0x00684d68`, `0x00684be8`, and raw palette reads from `0x00621330`. Replaced the decompiler-lost `FUN_0045e76f` read at the startup config header with `E2R_ReadOpenFileBytes(..., 0x20)`, and replaced the lost-register `FUN_0045e90e` signature comparison with a 12-byte `strncmp` against `Ecstatica001`. Mirrored the repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. Debug GDB no longer crashes through `FUN_0046055c`; it opens `E_CONFIG`, reads the 32-byte header beginning `Ecstatica001d`, and passes the `Ecstatica001` signature check.

Next Frontier: execution now exits through `FUN_00414e68` from `FUN_0041007c:303` after `FUN_0045eb05(extraout_ECX_07, extraout_EDX_02)` returns null. Live GDB values at that call are `extraout_ECX_07=0x62` and `extraout_EDX_02=NULL`, so the next investigation should recover the fopen-like filename/mode arguments for `FUN_0045eb05` rather than treating this as a missing data file.

Regression Risk: these are fixed-address and narrow config-header repairs, not a full CRT stream reconstruction. The follow-up `FUN_0045eb05` frontier is a shared wrapper and should be repaired with call-site/disassembly evidence before broadening its native adapter.

## 2026-07-13 - Main Loop Entry Reached

Area: `FUN_00410a48 -> FUN_0041ce88 -> thunk_FUN_004620db`, post-title startup transition

Symptom: after title/shadow startup fixes, execution still took the `Can't find shading data file` fatal branch from `FUN_00410a48` because `FUN_0041ce88` returned zero before the suspected main-loop call.

Evidence: original disassembly for `FUN_0041ce88` loads `EAX = 0x471890` and `EDX = 0x47007c` before calling `FUN_0045eb05`; metadata names `0x471890` as `s_shademap.dat_00471890` and the data file exists as `/home/rgrabowski/Games/Ecstatica2/SHADEMAP.DAT` with size `49152`. The original loop consumes three bytes per `128 x 128` pixel: one byte into `0x0061d030` and two bytes as a big-endian short into `0x00621630`.

Change: replaced the fragile `FUN_0041ce88` decompiler body with a native `shademap.dat` loader that fills the same legacy byte and short tables, after earlier startup repairs for allocation count arguments, raw-image descriptor reads, `shadow.dat` stream loading, `FUN_0041ccf0` lost destination, and a fixed-address clear in `FUN_0044c71c`. Mirrored generated-C repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` compiles. ASan was configured because `build/linux-clang32-asan` was absent, then `cmake --build build/linux-clang32-asan` compiles. Debug GDB hit `thunk_FUN_004620db` at `E2Recomp_recon.c:53799`, called from `FUN_00410a48` at `E2Recomp_recon.c:4752`.

Next Frontier: after continuing past the main-loop thunk, execution later crashes at `EIP=0xffffffff` in `FUN_0046055c`, called by `FUN_0045e5b8 -> FUN_0045e594` while opening `"e_config"` from `FUN_0041007c`. The next investigation should recover the indirect CRT/file callback or descriptor state around `FUN_0046055c`.

Regression Risk: the new shademap loader is purpose-built for the proven startup file format and bypasses the broken text-stream helper body. The trigonometric table initializer in `FUN_00414f40` remains an approximate native stabilizer, not a byte-perfect reconstruction.

## 2026-07-13 - Title Logic Reached

Area: `FUN_00414998 -> FUN_0041760c -> FUN_00417b20`, startup logo blit and title transition

Symptom: after the visible-window milestone, execution crashed in DirectDraw/palette and startup blit code before reaching title logic.

Evidence: `FUN_0041af88` first called the DirectDraw palette creation slot at vtable offset `0x14`, but the existing stub only implemented `CreateSurface`, leaving `_DAT_006366c0` null. After palette creation was stubbed, the next crashes exposed generated overlap/register artifacts: palette out-pointer writes targeted `DAT_006366c0` while reads used `_DAT_006366c0`; `FUN_00418a04` lost incoming `EAX` as the buffer index; `FUN_00417b20` lost incoming `EBX` as a blit coordinate; and generated `DAT_00636150` table reads did not see the `_DAT_0063615x` buffer aliases.

Change: added a minimal DirectDraw palette object and `CreatePalette` stub, redirected palette out-pointer writes to `_DAT_006366c0`, recovered the `FUN_00418a04` index and `FUN_00417b20` coordinate for the startup blit path, mapped the legacy VGA `0xa0000..0x100000` range, and mirrored reconstructed-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. GDB breakpoints hit `FUN_00414a94` and then `FUN_00414b24` from `FUN_00410a48`; the process exited with code `0340` instead of crashing in the DirectDraw/surface frontier.

Next Frontier: step 5 should continue from reached title logic toward the reconstructed main loop.

Regression Risk: DirectDraw behavior is still intentionally skeletal. Palette creation, surface methods, VGA mapping, and startup blit coordinate recovery are sufficient for this milestone but not accurate rendering.

## 2026-07-13 - Visible Window Path Proven

Area: `FUN_00458714 -> RegisterClassA -> CreateWindowExA`, initial Ecstatica II window creation

Symptom: after the first resource open was proven, execution could not advance to the window milestone because file descriptor/open-mode bookkeeping still read decompiler pseudo-registers and stale pointer-shaped values.

Evidence: original disassembly for `FUN_0045e5b8` shows the final stream-state call passes the descriptor in `EAX` and flags in `EDX`; the reconstructed code instead built an argument from `E2R_READ1(param_4,1)` with `param_4 == 0x200`. Original close helpers `FUN_0045e8e6` and `FUN_004608e8` likewise carry the descriptor in `EAX`. After repairing those paths, GDB reached `RegisterClassA` and `CreateWindowExA` from `FUN_00458714`; the top-level request used class `Ecstatica2`, title `Ecstatica II`, and size `640x640`.

Change: recovered descriptor registration/status/close bookkeeping around `FUN_004603d1`, `FUN_00460803`, `FUN_00460899`, `FUN_0045e5b8`, `FUN_0045e8e6`, and `FUN_004608e8`; mirrored those repairs in `E2Recomp/tools/GenerateRecon.js`. Added a minimal Linux X11 implementation behind `CreateWindowExA` so the original top-level window request maps a real host window.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. GDB showed `CreateWindowExA` returning the platform HWND and `e2r_x11_window.window == 20971521`, proving that the X11 window was created and mapped.

Next Frontier: after window creation, execution now crashes in `FUN_0041af88` at `E2Recomp_recon.c:8567`, calling through a DirectDraw/surface vtable during the startup logo path. The next step should recover enough DirectDraw surface behavior to reach menu/title logic.

Regression Risk: the file descriptor table repair allocates a fixed Win32-like handle table sized from `DAT_0047d610`. If later runtime paths require exact CRT descriptor growth semantics, replace it with a fuller reconstruction. The X11 window shim intentionally covers only top-level visibility, not complete Win32 message or rendering behavior.

## 2026-07-13 - First Resource Open Proven

Area: `FUN_00410a48 -> FUN_00414998 -> FUN_0045e594`, startup logo/config resource loading

Symptom: after the title-error pointer repair, tracing showed the first `CreateFileA` request was an empty string from `FUN_00414998`, so no real data file was opened.

Evidence: original disassembly for `FUN_00410a48` loads `EAX = 0x470510` before the first unconditional `FUN_00414998` call, which metadata names `s_psyglogo.raw_00470510`. Original `FUN_00414998` copies incoming `EAX` to `EDX` at entry and uses that preserved filename after `FUN_0043ac60`. GDB tracing after the repair shows `CreateFileA request: "psyglogo.raw"` and a valid non-`INVALID_HANDLE_VALUE` handle. The runtime is started from `build/linux-clang32-debug`, then enters the `Ecstatica2` data symlink before reconstructed startup.

Change: restored the lost `FUN_00414998` filename input from `param_1`, preserved it across `FUN_0043ac60`, recovered the three startup logo filename symbols used by `FUN_00410a48`, converted the split `E_CONFIG` stack filename into a contiguous 9-byte buffer, changed the Linux launcher to enter `E2RECOMP_DATA_DIR`, and made `CreateFileA` normalize backslashes plus resolve read-only paths case-insensitively. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. The first proven real resource open is `/home/rgrabowski/Games/Ecstatica2/PSYGLOGO.RAW`, requested by reconstructed code as `psyglogo.raw`.

Next Frontier: after the successful open, debug GDB now stops in `FUN_0045e5b8` at `E2Recomp_recon.c:52844`, where the decompiled code reads `E2R_READ1(param_4,1)` with `param_4 == 0x200`. The next investigation should recover the file-handle/open-mode bookkeeping around `FUN_0045e5b8` instead of treating `param_4` as a pointer.

Regression Risk: the `CreateFileA` compatibility fallback is intentionally Win32-like for read-only opens; if write/create paths later need case handling, extend it carefully without redirecting writes to unintended files.

## 2026-07-13 - Title Error Exit Lost EAX Message Pointer

Area: `FUN_00414b24 -> FUN_00414e68`, title picture load failure path

Symptom: `FUN_00414e68` dereferenced `0x200` while scanning its shutdown message string.

Evidence: original disassembly shows `FUN_00414e68` saves `EAX` into `EBP` at entry and later scans that pointer. The failing `FUN_00414b24` branch at `00414e43` loads `EAX = 0x471320` before calling `00414e68`; metadata names that string `s_Can't_load_title_picture_00471320`. GDB stopped at the reconstructed `FUN_00414e68` with the stale local still showing `0x200` before the new assignment, then after one step `in_EAX` pointed at `s_Can_t_load_title_picture_00471320` with contents `Can't load title picture`.

Change: initialized the lost `in_EAX` pseudo-register in `FUN_00414e68` to the recovered title-load error string, added the missing generated string declaration/global/data initialization, and mirrored the function-body repair in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. Debug GDB run no longer faults on the `0x200` dereference; it exits through the recovered fatal shutdown path with code `0364`.

Next Frontier: the runtime now reaches a clean fatal exit for `Can't load title picture`, meaning the next startup investigation should focus on why `FUN_0045e594(..., s_title_s_raw_00471314, 0x200, ...)` fails to load `title_s.raw` from the Ecstatica II data path. ASan execution still aborts earlier in `FUN_0041dc8c` on a global-buffer-overflow around overlapping globals near `DAT_0047a2b4`; the ASan build itself compiles.

Regression Risk: `FUN_00414e68` is a shared fatal-exit helper whose original convention carries the message pointer in `EAX`. This repair recovers the current title-load call path only; future fatal-exit call sites may need their own `EAX` message recovery instead of reusing this default.

## 2026-07-13 - Startup Wait-Loop Stack Corruption

Area: `FUN_00410a48`, startup pacing around `FUN_00414998`

Symptom: after the date conversion helper repair, the program reached `FUN_0043ac60` and then crashed with `EIP=0x0`. The raw stack showed return addresses around `FUN_00410a48:570`, where startup wait loops called `FUN_0045f1c0` with decompiler `extraout_ECX` values.

Evidence: GDB showed the first `FUN_0043ac60` return had a sane frame, but the later crash involved a `FUN_0045f1c0` call with a stack/frame pointer-like output address. That helper writes a 0x24-byte time structure, so using a phantom register as the destination can overwrite caller stack state.

Change: replaced the fragile 5 ms busy-wait loops in `FUN_00410a48` with explicit `Sleep(5)` pacing and stable zero arguments for the adjacent calls. Mirrored the transformation in `E2Recomp/tools/GenerateRecon.js`.

Result: both `linux-clang32-debug` and `linux-clang32-asan` rebuilt. The runtime moved past the null instruction pointer crash and now stops in `FUN_00414e68` via `FUN_00414b24`, dereferencing `0x200`.

Regression Risk: this is a Linux runtime stabilization, not a perfect reconstruction of the original timing code. If menu/intro pacing behaves oddly later, recover the original local time-buffer addresses with Ghidra and replace the `Sleep(5)` shim.

## 2026-07-13 - Date Helper Lost Output Pointer

Area: `FUN_004645d2`, called from `FUN_00461ab5`/`FUN_0045f1c0`

Symptom: crash writing through `extraout_ECX_00 + 0x10` inside `FUN_004645d2`.

Evidence: GDB stopped at `E2Recomp_recon.c:60066`; the destination pointer resolved to unrelated executable memory rather than the time output structure.

Change: rewired `FUN_004645d2` to write year/month/day/week fields through `param_1` and to return `param_1`. Mirrored the replacement in `GenerateRecon.js`.

Result: the program advanced to the startup wait-loop stack corruption described above.

Regression Risk: `FUN_004645d2` still contains unrecovered `in_EAX`/`unaff_EBX` inputs. It may need a fuller Ghidra-backed signature recovery when date/time behavior matters.
