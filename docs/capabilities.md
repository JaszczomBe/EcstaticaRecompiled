# Project state and capabilities

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

The active target is Ecstatica II on Linux/i386 with original external game data.
The completed reconstruction milestone is a historical bounded state/surface
proof. Everyday development now uses SDL, original backgrounds and diagnostic
actor cylinders to recover gameplay.

| Area | Available capability | Acceptance boundary |
| --- | --- | --- |
| Build and editor | Clang 21 i386 Debug/ASan, SDL/X11 builds, selected-target F5 | Debug is the everyday choice; optimized runtime and 64-bit execution remain experimental/incomplete |
| Gameplay | Recovered movement, camera crossings, NPC/object population and bounded workshop activation | Manual workshop re-entry, sword pickup, broader interactions/combat and full experimental ASan acceptance remain open |
| Rendering and audio | Original backgrounds, palette/presentation, projected diagnostic cylinders | Original actor meshes/animation and audio fidelity remain incomplete |
| Persistence | Original data/resource loading and replay | Quick-save is a no-op; functional game save/load is unproven |
| Investigation | Automatic F5 logging, replay, state timeline, rolling frames, pinned binary and debugger evidence | Capture limits, incomplete recordings and strict replay divergence remain explicit |
| Recovery tools | Original-x86 fixtures, crash export, state/report queries, route expectations, recovery/diagnostic index | Sampled/fixture evidence does not establish complete game behavior; rr is optional and currently absent |

## Current implementation and next work

The [runtime implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md)
and [population/interaction task](implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
own the precise current frontier, verification and next bounded recovery action.
The broader populated Debug floor-return assertion remains an open route issue.
Follow the [tooling implementation](implementations/debugging-tools/debugging-tools.md)
for debugger integration and tool acceptance.

The [milestone plan](plans/runtime-milestones.md) owns later rendering, control,
timing, sound, persistence and portability direction. The
[journal](journal/journal.md) records recent changes. Check working-tree and commit
state as described in the root README; local repairs can be newer than the last commit.
