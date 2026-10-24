# Ecstatica Recompiled

Ecstatica II is being reconstructed from original x86 behavior into a Linux/i386
runtime using original game data. The current developer game uses SDL backgrounds
and diagnostic actor cylinders for gameplay recovery. Original meshes, audio,
save/load, broad gameplay fidelity and the 64-bit runtime remain incomplete.

## Start here

1. Read [project state and capabilities](docs/capabilities.md).
2. Follow the [handoff and working rules](docs/HANDOFF.md).
3. Open the [active runtime implementation](docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md)
   and its [current population and interaction task](docs/implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
4. Use [build and VS Code setup](docs/building.md), then press F5 with
   **Ecstatica Recompiled** and the **Debug · Clang 21 · i386 · SDL** preset.

F5 is the normal gameplay investigation workflow. It enables logging, automatic
replay recording, state inspection and rolling game frames. The debugger pins the
running executable and saves stopped-thread evidence. Ending debugging generates
an inspection report in that session. See [debugging tools and usage](docs/debugging.md)
for the artifacts, replay, comparisons and export commands.

For automated regression checks, select **Ecstatica: Full regression suite**.
It offers a headless/visible picker and runs Debug/ASan cases sequentially in
dependency order, producing PASS/FAIL/BLOCKED/SKIPPED reports. Separate block
launches include their prerequisites; a direct visible SDL full-suite entry is
also available. See [gameplay tests](docs/gameplay-tests.md).

## Documentation tree

| Branch | Contents |
| --- | --- |
| [Project documentation](docs/README.md) | Current state, handoff, setup, tools, plans, implementations, tasks, journal, templates and style |
| [Reconstruction source workflow](E2Recomp/README.md) | Ghidra exports, generated C, original executable facts and reconstructed builds |
| [Dependencies](dep/README.md) | SDL/Ghidra setup and the linked upstream documentation branch |
| [Contributing](CONTRIBUTING.md) | Evidence, verification, generated-code changes and documentation upkeep |
| [Agent instructions](AGENTS.md) | Entry protocol and rules for future AI contexts |
| [Code of conduct](CODE_OF_CONDUCT.md) | Collaboration expectations |

Every Markdown document has a place in this tree. Project documents link back to
their parent; vendored documents are linked through the dependency index without
editing upstream content. [Documentation maintenance](docs/documentation.md)
explains ownership and provides the automated tree/link check.

## Current work and history

The [runtime implementation](docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md)
owns gameplay acceptance and the next recovery task. The
[debugging implementation](docs/implementations/debugging-tools/debugging-tools.md)
owns tooling status. [Milestones](docs/plans/runtime-milestones.md) describe planned
work; the [journal](docs/journal/journal.md) records dated changes and evidence.
Use `git status --short` and `git log -5 --oneline` to distinguish the current
working tree from committed history.

## First build

With Clang 21 multilib, CMake 3.25+, Ninja, SDL and original game data installed:

```sh
git submodule update --init --recursive dep/SDL
cmake --preset linux-clang32-sdl-debug -DECSTATICA2_DATA_DIR=/path/to/Ecstatica2
cmake --build --preset linux-clang32-sdl-debug
```

Then select that CMake preset and target in VS Code and use F5. Debug is the
validated everyday configuration; ASan has its own preset. Terminal entry,
experimental optimized presets and regression commands are in the build guide.

## Original project credit

Original project presentation: Spacefarer Retro Remasters. Existing support links:
[Buy Me a Coffee](https://buymeacoffee.com/jakeysbakery), PayPal
`jake@spacefarergames.com`. See [LICENSE](LICENSE).
