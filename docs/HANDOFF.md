# EcstaticaRecompiled Handoff

This is the durable root road sign for future context windows. It explains where project truth lives and how to resume work; it is intentionally not a timeline or a copy of the current crash frontier.

## Project Objective

Run the decompiled Ecstatica II reconstructed runtime on Linux using original game data, while preserving recovered game behavior and isolating host services behind compatibility boundaries suitable for later replacement.

The first reconstruction implementation is complete: original data loads, the main loop survives bounded debug/ASan probes, Start Game reaches first gameplay, movement input latches, real recovered frames present through SDL, SDL 3.4.12 is vendored under `dep/SDL`, and VS Code has an `Ecstatica Recompiled (SDL)` launch route.

Development is evidence-driven: use repeatable CMake builds, bounded runtime probes, ASan/GDB observations, original disassembly or Ghidra evidence, and concise journal entries.

## Resume Here

Read these sources in order:

1. [Run Reconstructed E2 On Linux](implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) - completed reconstruction result, proof history, roadmap, and verification commands.
2. [Playable SDL Runtime](implementations/playable-sdl-runtime/playable-sdl-runtime.md) - active post-reconstruction implementation for SDL F5 stability, presentation fidelity, controls, timing, audio, and developer workflow.
3. The active step linked from the active implementation - current scope, acceptance criteria, evidence, and next frontier.
4. [Runtime crash fixes](journal/entries/runtime-crash-fixes.md) and any journal linked by the active step - historical reasoning and regression risks.
5. [Runtime Milestones](plans/runtime-milestones.md) - durable milestone order and architecture direction.
6. `git status --short` and `git log -1 --oneline` - worktree and latest-commit state.

Do not infer the current step from this file. The active implementation document owns changing execution state so this root anchor cannot drift out of sync. As of 2026-07-28, the completed reconstruction record is [Run Reconstructed E2 On Linux](implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md), and the active next horizon is [Playable SDL Runtime](implementations/playable-sdl-runtime/playable-sdl-runtime.md).

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
4. Keep reconstructed game logic original-shaped. Linux/X11, Win32, DirectDraw, DirectSound, CRT, and future SDL behavior belongs in compatibility or host-backend layers.
5. Build and run after each runtime fix when feasible; use bounded probes for unstable paths.
6. Journal fixes that advance the runtime frontier, including evidence, result, next frontier, and regression risk.
7. Preserve user changes in a dirty worktree. Do not revert unrelated work.
8. Do not commit or push unless explicitly asked.
9. Respect the active implementation usage budget recorded in its documentation.

## Stable Development Coordinates

- Repository branch used for this effort: `linux-e2-reconstructed-runtime`
- Original game data: `/home/rgrabowski/Games/Ecstatica2/`
- Build-tree data link name: `Ecstatica2`
- Debug build: `cmake --build --preset linux-clang32-debug`
- ASan build: `cmake --build build/linux-clang32-asan`
- Reconstructed runtime entry: `./e2recomp --run-recon` from a build directory
- Generator syntax check: `node --check E2Recomp/tools/GenerateRecon.js`

## Documentation Map

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
