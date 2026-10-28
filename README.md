# Ecstatica Recompiled

Ecstatica II is being reconstructed from original x86 behavior into a Linux/i386
runtime using original game data. The developer game renders original animated
characters, selected item/weapon/door/blood/pool assets, rats, the stable horse,
courtyard projectiles, animated pools/flames, coloured doors and collectible
families against SDL backgrounds.
Other objects retain diagnostic fallbacks. **F3** cycles
original models with unrecovered fallbacks, models plus boxes, and boxes only.
Original HUD artwork is the default; **F1** selects it and **F2** selects the debug overlay.
Original-format menu save/load has bounded Debug/ASan round-trip verification. Audio,
remaining models, broad gameplay fidelity and the 64-bit runtime remain incomplete.

## Start here

The inner-castle crash is reproduced and its original node argument recovered;
negative rectangle clipping is also repaired. F5 includes the original teleport,
head switches, armour, wizardess details, prison key, mace/sparkles and stairwell
strike/explosion owners. Start with [Step 12 Task 04](docs/implementations/playable-sdl-runtime/steps/step-12/tasks/task-04-recover-inner-castle-progression-crash-and-models.md)
and the [recovery evidence](docs/journal/entries/inner-castle-crash-and-presentation-recovery-2026-10-28.md).
All 3,190 recovered-prefix checkpoints match; the recording remains incomplete.
Extended route, equipped-armour and full gate/effect visual acceptance remain open.

The tower key/spike-trap/door route now passes bounded Debug/ASan progression
and protected Save/Load checks. F5 includes its original key, head, spike and door
models. Strike the head, collect the fallen key with **Space**, then approach the
keyed door. [Step 12 Task 03](docs/implementations/playable-sdl-runtime/steps/step-12/tasks/task-03-recover-tower-key-trap-and-door-progression.md)
and the [recovery evidence](docs/journal/entries/tower-key-progression-recovery-2026-10-28.md)
retain human visual-review and wider gameplay limits. Remaining object/acid work
precedes audio.

The [latest tower/storage follow-up](docs/journal/entries/tower-storage-render-followup-2026-10-28.md)
adds original collection sparkle and storage models, including the gold sword.
The reported translucent door remains unresolved; preserve original behavior
unless comparison proves a reconstruction error.

1. Read [project state and capabilities](docs/capabilities.md).
2. Follow the [handoff and working rules](docs/HANDOFF.md).
3. Open the [active runtime implementation](docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md)
   and its [next object-model/animation step](docs/implementations/playable-sdl-runtime/steps/step-12/step-12-recover-object-models-and-animations.md).
4. Use [build and VS Code setup](docs/building.md), then press F5 with
   **Ecstatica Recompiled** and the **Debug · Clang 21 · i386 · SDL** preset.

F5 is the normal gameplay investigation workflow. It enables logging, automatic
replay recording, state inspection and rolling game frames. The debugger pins the
running executable and saves stopped-thread evidence. Ending debugging generates
an inspection report in that session. See [debugging tools and usage](docs/debugging.md)
for the artifacts, replay, comparisons and export commands.

For automated regression checks, select the **starred full regression suite**.
Its picker offers headless, one visible configuration or both windows. Debug and
ASan run concurrently, each in dependency order, producing individual
PASS/FAIL/BLOCKED/SKIPPED reports. Separate block
launches include their prerequisites and are numbered from basic to advanced
checks. The full-suite entry appears first. See [gameplay tests](docs/gameplay-tests.md).

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
