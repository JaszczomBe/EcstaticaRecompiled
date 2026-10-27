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
| Rendering and audio | Original animated player and enemy ellipsoid bodies, original backgrounds, palette/depth/page presentation; diagnostic shapes for objects and equipment | The user accepted the corrected player; enemy bodies have bounded live guard/attack evidence, with broader combat and human visual qualification still open; equipment polygons, original HUD and audio remain incomplete |
| Persistence | Original data/resource loading and replay | Quick-save is a no-op; functional game save/load is unproven |
| Investigation | Automatic F5 logging, replay, state timeline, rolling frames, pinned binary and debugger evidence | Capture limits, incomplete recordings and strict replay divergence remain explicit |
| Recovery tools | Original-x86 fixtures, crash export, state/report queries, route expectations, dependency-aware Debug/ASan gameplay suite with concurrent configurations, shared checkpoints, three-stage menu coverage, one/two visible windows, unarmed combat and host allocation-fault checks, recovery/diagnostic index | Headless menu labels, three-stage restarts and Load/Save dialog checks pass after original-backed menu/surface repairs; functional persistence/audio and broad rendering remain unqualified; sampled/fixture evidence does not establish complete game behavior; rr is optional and currently absent |

## Current implementation and next work

The user accepted the corrected player model/animation on 2026-10-27 and moved
**enemy animations ahead of functional game save/load**, then game sounds and
music. Investigation session saving, replay and the gameplay regression suite
remain closed milestones with recorded minor limits deferred.

The [runtime implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md)
and [enemy task](implementations/playable-sdl-runtime/steps/step-08/tasks/task-03-activate-scene-backed-children.md)
own current work. F5 enables `E2R_PLAYER_MESH=1` and `E2R_NPC_MESH=1`: original
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
