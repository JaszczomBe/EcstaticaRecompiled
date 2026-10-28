# EcstaticaRecompiled Handoff

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

Start at the central [project README](../README.md). This handoff is its durable
working-rules branch: it explains where project truth lives and how to resume
work, without copying the changing crash frontier. The README-rooted
[documentation tree](README.md) connects capabilities, plans, implementation
state, tasks, journal, tools and collaboration/style guidance.

## Project Objective

Run the decompiled Ecstatica II reconstructed runtime on Linux using original game data, while preserving recovered game behavior and isolating host services behind compatibility boundaries suitable for later replacement.

The first reconstruction implementation is a completed historical proof of resource loading, bounded loop execution, input-state latching, and recovered-frame presentation through SDL. Those probes do not establish visible, controllable gameplay. The active implementation owns current playability, regression results, and remaining recovery work; completed milestones must be read with their recorded acceptance limits.

Development is evidence-driven: use repeatable CMake builds, bounded runtime probes, ASan/GDB observations, original disassembly or Ghidra evidence, and concise journal entries.

## Resume Here

For a fresh AI context, read the root README, [capabilities](capabilities.md),
this handoff, the active implementation and current task, then relevant dated
evidence. Normal human investigation uses the single **Ecstatica Recompiled**
F5 launch with recording, inspection, executable pinning and debugger evidence.
See [build setup](building.md) and [debugging usage](debugging.md).

For the selected next continuation, open the
[original-HUD step](implementations/playable-sdl-runtime/steps/step-11/step-11-recover-original-hud.md)
and its [Enter inventory/status menu task](implementations/playable-sdl-runtime/steps/step-11/tasks/task-02-recover-enter-inventory-and-progress-menu.md).
The user explicitly requested this next-context handoff after inner-castle
recovery, supplying an original-game inventory/progress screenshot. This
navigation change makes the selected menu task discoverable from a blank context;
the task and its [handoff journal](journal/entries/enter-inventory-menu-handoff-2026-10-28.md)
own the changing source leads, reference and acceptance. Prior object/progression
limits remain open; audio/music remain deferred.

Read these sources in order:

1. [Playable SDL Runtime](implementations/playable-sdl-runtime/playable-sdl-runtime.md) - current execution state, acceptance limits and active gameplay work.
2. The active step/task linked from that implementation - scope, criteria, evidence and next bounded action.
3. Relevant journal entries and [runtime crash fixes](journal/entries/runtime-crash-fixes.md) - dated reasoning and regression risks.
4. [Debugging tools](debugging.md) and their implementation record when the work concerns investigation capabilities.
5. [Runtime Milestones](plans/runtime-milestones.md) - planned work and architecture direction.
6. [Run Reconstructed E2 On Linux](implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) when historical reconstruction proof is needed.
7. `git status --short` and `git log -1 --oneline` - worktree and latest-commit state.

Do not infer the current step from this file. The active implementation document owns changing execution state so this durable guide cannot drift out of sync. The completed reconstruction record is [Run Reconstructed E2 On Linux](implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md), and the active next horizon is [Playable SDL Runtime](implementations/playable-sdl-runtime/playable-sdl-runtime.md).

## Blank Context Protocol

When a fresh context is given only an instruction to read this file:

1. Follow the resume order above before proposing code changes.
2. Report the active step and concrete frontier from the implementation and step documents.
3. Summarize scope and acceptance criteria in no more than three bullets each.
4. State the next bounded action and its verification.
5. Wait for confirmation before substantial implementation unless the user already said to proceed.

If the user already selected a step or said to proceed, restate the bounded scope briefly and continue without asking them to choose again.

## Generated Reconstruction Workflow

This repository has generated reconstruction files, especially `E2Recomp/reconstructed/E2Recomp_recon.c`. Large generated diffs are expensive to review and are usually a workflow failure unless the user explicitly asked for regeneration-wide churn.

When touching generated reconstruction behavior:

1. Inspect `git status --short`, `git diff --stat`, and `git diff --cached --stat` before editing, because staged hand fixes may already exist.
2. Treat `E2Recomp/reconstructed/*` as proof/output and `E2Recomp/tools/GenerateRecon.js` as the durable source of repeatable fixes.
3. For a new runtime fix, make the smallest hand edit needed to prove the behavior, then mirror that exact repair in `GenerateRecon.js` before broad verification.
4. Prefer small, anchored generator patches or ordered replacement tables. Do not use giant generated-file patches when a generator mirror can express the change.
5. If regeneration creates a large unrelated diff, stop immediately. Do not build on top of it. Narrow the generator anchors, regenerate again, and continue only when the reconstructed diff is zero or deliberately explained.
6. Before reporting success, run `node --check E2Recomp/tools/GenerateRecon.js`, regenerate with `node E2Recomp/tools/GenerateRecon.js .` when the generator changed, then confirm generated-file drift with `git diff --stat` and targeted `git diff -- E2Recomp/reconstructed`.

## Repository Invariants

1. Read the active implementation and relevant journal before changing reconstructed code.
2. Prefer original disassembly or Ghidra-backed recovery over speculative defensive behavior.
3. Mirror reconstructed C hand fixes in `E2Recomp/tools/GenerateRecon.js` so regeneration preserves them.
4. Keep reconstructed game logic original-shaped. Linux/X11, Win32, DirectDraw, DirectSound, CRT, and SDL behavior belongs in compatibility or host-backend layers.
5. Build and run after each runtime fix when feasible; use bounded probes for unstable paths.
6. Journal fixes that advance the runtime frontier, including evidence, result, next frontier, and regression risk.
7. Preserve user changes in a dirty worktree. Do not revert unrelated work.
8. Do not commit or push unless explicitly asked.
9. Respect the active implementation usage budget recorded in its documentation.

## Stable Development Coordinates

- Repository branch used for this effort: `linux-e2-reconstructed-runtime`
- Original game data: `/home/rgrabowski/Games/Ecstatica2/`
- Build-tree data link name: `Ecstatica2`
- Everyday SDL Debug build: `cmake --build --preset linux-clang32-sdl-debug`
- SDL Debug ASan build: `cmake --build --preset linux-clang32-sdl-debug-asan`
- X11 regression builds: `cmake --build --preset linux-clang32-debug` and `cmake --build --preset linux-clang32-debug-asan`
- Current build directories and first-time configuration: [Build and editor setup](building.md). Presets use `build/Debug/clang21-i386-{sdl,x11}[-asan]`; old `build/linux-clang*` paths are historical.
- Reconstructed runtime entry: `./e2recomp --run-recon` from a build directory
- Generator syntax check: `node --check E2Recomp/tools/GenerateRecon.js`

## Documentation Map

- [Build and editor setup](building.md)
- [Implementation workflow](templates/implementation-workflow.template.md)
- [Playable SDL Runtime](implementations/playable-sdl-runtime/playable-sdl-runtime.md)
- [Run Reconstructed E2 On Linux](implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md)
- [Journal index](journal/journal.md)
- [Runtime crash fixes](journal/entries/runtime-crash-fixes.md)
- [Generated code repairs](journal/entries/generated-code-repairs.md)
- [Linux portability](journal/entries/linux-portability.md)
- [Reverse engineering workflow](journal/entries/reverse-engineering-workflow.md)
- [Runtime milestones](plans/runtime-milestones.md)
- [Commit message template](templates/commit-message.template.md)

## Anchor Policy

This file changes only when its navigation, durable project objective, resume protocol, or invariants become incorrect. Runtime milestones, active steps, crash addresses, probe results, and recent fixes belong in implementation, step, and journal documents. Any edit to this anchor requires explicit user permission and a stated structural reason.
