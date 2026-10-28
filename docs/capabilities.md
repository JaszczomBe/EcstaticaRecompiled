# Project state and capabilities

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

The active target is Ecstatica II on Linux/i386 with original external game data.
The completed reconstruction milestone is a historical bounded state/surface
proof. Everyday development now uses SDL, original backgrounds and typed
diagnostic object markers alongside recovered animated character bodies.

| Area | Available capability | Acceptance boundary |
| --- | --- | --- |
| Build and editor | Clang 21 i386 Debug/ASan, SDL/X11 builds, selected-target F5 | Debug is the everyday choice; optimized runtime and 64-bit execution remain experimental/incomplete |
| Gameplay | Recovered movement, camera crossings, NPC/object population and bounded workshop activation | Human swimming, sword pickup, four kills and two broken doors verified; animation-cache stall repaired; Debug/ASan door passage and actual menu Quit pass; human random-potion pickup verified and delayed effects repaired with live Debug/ASan poison dispatch; bottle removal and subsequent sword use confirmed in the latest human run; visible health/potion diagnostics added; fresh Debug healing 85→100, poison onset, invisibility dispatch and conditional no-op verified; final effect expiry/cure remains open; latest alternate-target crash repaired with isolated generated Debug/ASan prefix evidence; extended stability remains a follow-up; animation-name parity restored for potion cleanup; natural effect summaries are optional; wider pickups/rendering remain deferred |
| Rendering and audio | Original animated player and enemy ellipsoid bodies, original backgrounds, palette/depth/page presentation; diagnostic shapes for objects and equipment | The user accepted the corrected player and enemy recovery direction; bounded live guard/attack evidence does not establish exhaustive species/actions or broader combat; equipment polygons and audio remain incomplete; original HUD artwork/default and F1/F2 selection have bounded original-code/native evidence |
| Persistence | Original-format gameplay Save/Load, writable runtime slots and original read fallback | Debug/ASan repeated same-process and fresh-process loads restore active actors and sword ownership, then resume input/animation/attacks; saved previews display at 160×120 without dirtying game pages, original menu geometry/font and title alignment are restored, successful Load dismisses the menu; installed saves remain intact; arbitrary original progressions and malformed-file recovery remain unqualified |
| Investigation | Automatic F5 logging, replay, state timeline, rolling frames, pinned binary and debugger evidence | Capture limits, incomplete recordings and strict replay divergence remain explicit |
| Recovery tools | Original-x86 fixtures, crash export, state/report queries, route expectations, dependency-aware Debug/ASan gameplay suite with concurrent configurations, shared checkpoints, three-stage menu coverage, one/two visible windows, unarmed combat and host allocation-fault checks, recovery/diagnostic index | Headless menu labels, three-stage restarts and Load/Save dialog checks pass after original-backed menu/surface repairs; broader persistence, audio and exhaustive rendering remain unqualified; sampled/fixture evidence does not establish complete game behavior; rr is optional and currently absent |

## Current implementation and next work

The user selected **original HUD → game sounds → music** on 2026-10-28 after
functional save/load and menu/layout refinement. [Step 11](implementations/playable-sdl-runtime/steps/step-11/step-11-recover-original-hud.md)
and its [first task](implementations/playable-sdl-runtime/steps/step-11/tasks/task-01-recover-hud-and-display-mode-ownership.md)
own recovered life/armour/hand/capacity/magic graphics and original-default/F1/F2
presentation. Original visual state is composed onto an indexed presentation copy;
game pages, diagnostic observations and original saves remain independent.
Fresh evidence and remaining native indicator branches are recorded in the
[HUD recovery journal](journal/entries/original-hud-recovery-2026-10-28.md).
Investigation session saving, replay and the
gameplay regression suite remain closed milestones with minor limits deferred.

The [runtime implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md)
owns current acceptance. Baseline is `22c36a3f70bef9467e62299376905cbb5552dd71`
on `linux-e2-reconstructed-runtime`; functional persistence is committed in
`35be1cc` and menu/layout refinements in `22c36a3`. The historical v0.2.0 tag
remains at `ae54e6f8e4dc`; no newer release/push is inferred.

The [persistence step](implementations/playable-sdl-runtime/steps/step-10/step-10-recover-game-save-load.md)
and [save/load journal](journal/entries/game-save-load-recovery-2026-10-27.md)
retain version-4 serialization, actual repeated menu round trips, fresh-process
restoration and file-rejection limits. Saves write to `--data-dir/Saved`
(normally `~/.ecstatica2/Saved`); installed saves are read-only fallbacks. Tests
use private copies and confirmed originally empty slots only. The
[menu layout/font follow-up](implementations/playable-sdl-runtime/steps/step-10/tasks/task-05-recover-menu-layout-and-font.md)
passes 28 focused Debug/ASan checks and preserves the original saved-image format;
its three-stage menu sweep retains explicit unsupported checks. HUD recovery must
preserve these paths and verify affected behavior afresh.

F5 enables `E2R_PLAYER_MESH=1` and `E2R_NPC_MESH=1`: original
character bodies use recovered bones, camera composition, ellipsoid shading and
depth/page restoration. Their diagnostic shapes are hidden. Objects/equipment
retain diagnostic rendering; their polygon and box leaves remain bypassed.
The [enemy recovery journal](journal/entries/enemy-model-and-animation-2026-10-27.md)
records live guard poses, actual enemy-inflicted damage, retained combat failures
and current acceptance limits. The [player journal](journal/entries/player-model-and-animation-2026-10-27.md)
retains the original projection correction and user acceptance.

The subsequent [human-play follow-up](journal/entries/enemy-play-crash-and-dropped-potion-2026-10-27.md)
repairs false animation-directory entries that led into bitmap eviction and
restores the full original representation-name pool for dropped-potion script
conditions. Fresh original-code and bounded native evidence remain distinct from
full-suite, complete replay and long-play acceptance.

The [tower eviction repair](journal/entries/tower-actor-eviction-crash-2026-10-27.md)
is also included in v0.2.0: actor removal and root reuse pass original-code
comparisons, while Debug and ASan replay limits and further tower acceptance
remain recorded. These follow-ups do not replace the selected HUD recovery.

The prior [door approach correction](journal/entries/regression-door-approach-reliability-2026-10-27.md)
and [headless sweep](journal/entries/headless-regression-sweep-2026-10-27.md) retain
historical suite results and counterexamples. They do not establish full-suite
acceptance for the newly enabled player renderer. Follow the
[tooling implementation](implementations/debugging-tools/debugging-tools.md) for
debugger and replay limits.

The [milestone plan](plans/runtime-milestones.md) owns later rendering, control,
timing, sound, persistence and portability direction. The
[journal](journal/journal.md) records recent changes. Check working-tree and commit
state as described in the root README; local repairs can be newer than the last commit.
