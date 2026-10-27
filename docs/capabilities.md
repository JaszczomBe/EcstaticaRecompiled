# Project state and capabilities

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

The active target is Ecstatica II on Linux/i386 with original external game data.
The completed reconstruction milestone is a historical bounded state/surface
proof. Everyday development now uses SDL, original backgrounds and typed
diagnostic markers to recover gameplay.

| Area | Available capability | Acceptance boundary |
| --- | --- | --- |
| Build and editor | Clang 21 i386 Debug/ASan, SDL/X11 builds, selected-target F5 | Debug is the everyday choice; optimized runtime and 64-bit execution remain experimental/incomplete |
| Gameplay | Recovered movement, camera crossings, NPC/object population and bounded workshop activation | Human swimming, sword pickup, four kills and two broken doors verified; animation-cache stall repaired; Debug/ASan door passage and actual menu Quit pass; human random-potion pickup verified and delayed effects repaired with live Debug/ASan poison dispatch; bottle removal and subsequent sword use confirmed in the latest human run; visible health/potion diagnostics added; fresh Debug healing 85→100, poison onset, invisibility dispatch and conditional no-op verified; final effect expiry/cure remains open; latest alternate-target crash repaired with isolated generated Debug/ASan prefix evidence; extended stability is open and takes priority; preserved animation-name drift limits current-source acceptance; wider pickups/rendering remain deferred |
| Rendering and audio | Original backgrounds, palette/presentation, typed markers for creatures, corpses, doors, debris, potions, weapons, items and props; modal menus suppress the overlay | Original actor meshes/animation and audio fidelity remain incomplete |
| Persistence | Original data/resource loading and replay | Quick-save is a no-op; functional game save/load is unproven |
| Investigation | Automatic F5 logging, replay, state timeline, rolling frames, pinned binary and debugger evidence | Capture limits, incomplete recordings and strict replay divergence remain explicit |
| Recovery tools | Original-x86 fixtures, crash export, state/report queries, route expectations, dependency-aware Debug/ASan gameplay suite with concurrent configurations, shared checkpoints, three-stage menu coverage, one/two visible windows, unarmed combat and host allocation-fault checks, recovery/diagnostic index | Menu label/restart failures and ASan Load overflow remain visible; sampled/fixture evidence does not establish complete game behavior; rr is optional and currently absent |

## Current implementation and next work

The [runtime implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md)
and [population/interaction task](implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
own the precise current frontier, verification and next bounded recovery action.
Regression 04's recorded round trip passes in Debug/ASan with an explicit
noncombat opening fixture that prevents audited enemy creation. Live combat and
normal gameplay keep population; wider collision/AI and clean visible-input
acceptance remain separate. The task records retained live-route failures.
Follow the [tooling implementation](implementations/debugging-tools/debugging-tools.md)
for debugger integration and tool acceptance.

The [milestone plan](plans/runtime-milestones.md) owns later rendering, control,
timing, sound, persistence and portability direction. The
[journal](journal/journal.md) records recent changes. Check working-tree and commit
state as described in the root README; local repairs can be newer than the last commit.
