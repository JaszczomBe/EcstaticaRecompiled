# Ecstatica Recompiled

Ecstatica II is being reconstructed from original x86 behavior into a Linux/i386
runtime using original game data. The developer game renders original animated
characters, selected item/weapon/door/blood/pool assets, rats, the stable horse,
courtyard projectiles, animated pools/flames, coloured doors and collectible
families against SDL backgrounds.
Other objects retain diagnostic fallbacks. **F3** cycles
original models with unrecovered fallbacks, models plus boxes, and boxes only.
Original HUD artwork is the default; **F1** selects it and **F2** selects the debug overlay.
Original-format menu save/load has bounded Debug/ASan round-trip verification. Original game sounds and original-sequence General MIDI music now play through SDL;
remaining models, broad gameplay fidelity and the 64-bit runtime remain incomplete.

## Start here

**Next priority: remaining object behavior, rendering and interactions.**
After `v0.3.0`, the user selected anti-acid boots, ladder usage and other
remaining object paths, with stability checks and a playthrough across several
Save/Load sessions. Start with
[Step 12 Task 05](docs/implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md)
and its [continuation handoff](docs/journal/entries/object-behavior-and-interactions-handoff-2026-10-29.md).
Preserve each session's pinned build, matching save/checkpoint and findings;
recover original contracts before changing behavior. The [save-state integrity correction](docs/journal/entries/invalid-court-save-retirement-and-persistence-audit-2026-10-29.md)
withdraws the fabricated COURT150 progression baseline. Invalid saves and patched
descendants **MUST NOT be used to decompile game functionality**. The old COURT,
power150 copies and derived checkpoints are removed; recovery tooling/profile
selection is retired. F5 uses normal runtime storage. Resume from a fresh game
or a verified, unmodified original save. Current Save/Load also repairs live
difficulty and poison-duration ownership, with Debug/ASan checks from valid seeds.
The [ladder repair](docs/journal/entries/stables-ladder-interaction-recovery-2026-10-29.md)
retains its original-x86 Space-predicate proof; traversal and landing persistence
must be requalified from valid progression. Other ladders, visual review and
the recorded zero-life controllable state remain open.
The
The
[first session investigation](docs/journal/entries/garden-teleport-and-boots-session-2026-10-29.md)
matches all 1,386 checkpoints and adds original garden pad/glow, courtyard gold
head, hut chest and boots models to F5. Its installed checkpoint already has spent
boots. Final Debug/ASan persistence, HUD/F3/inventory, audio/music replay and
original-pixel checks pass. Fresh boots interaction, full effect review and wider
playthrough remain open.

The [COURT investigation](docs/journal/entries/court-recovery-150-and-repeat-spider-2026-10-29.md)
records the historical zero-power crash and abandoned power150 experiment.
Its patched-save hit/replay results do not qualify gameplay or recovered
progression. Health53 was stored correctly, but other lost statistics cannot
be reconstructed by choosing a power value or saving the file again.

Earlier tower/castle and occupied-slot inventory routes based on the other
quarantined zero-power saves5/123 and6/DFGSDRG also require valid-state
requalification. Independent original-code repairs remain; historical acceptance
summaries below must be read with this restriction.

The [preceding courtyard investigation](docs/journal/entries/courtyard-boxes-and-zero-power-crash-2026-10-29.md)
reproduces the reported SIGFPE from old runtime **7/COURT**, whose saved power is
already zero. The original damage instructions have the same unguarded division;
the occupied save and arithmetic remain unchanged. The preceding clean run loads
healthy installed **2/g3** instead. Nine additional original courtyard owners,
including the door, chest and statues, are selected in F5 (90 total). Final
Debug/ASan protected persistence, HUD/F3/inventory and strict audio/music replay
checks pass. Fresh interactions, full visual review and extended play remain open.

**Original music now plays through software General MIDI.** See its retained
[Step 05 Task 05](docs/implementations/playable-sdl-runtime/steps/step-05/tasks/task-05-recover-original-music.md)
and the [music recovery evidence](docs/journal/entries/music-recovery-2026-10-29.md).
The sequencer matches the original DLL across all 91 GM tracks; bounded native
output, independent Music/Sound settings, protected persistence and strict replay
are verified. An external SoundFont supplies instruments; see the task for bank
selection. Human listening, broader transitions and hardware-specific timbre remain open.

**Original game sounds now play through SDL.** See the retained
[Step 05 Task 04](docs/implementations/playable-sdl-runtime/steps/step-05/tasks/task-04-recover-original-game-sounds.md)
and the [sound recovery evidence](docs/journal/entries/game-sounds-recovery-2026-10-29.md).
All 404 indexed assets match original sample conversion; bounded real PulseAudio
Debug and dummy-device ASan routes cover playback, Settings, HUD/F3/inventory,
protected persistence and strict recording/replay. Human F5 listening, broader
natural event coverage and device-loss behavior remain open. Music continues in Task 05 above;
prior gameplay and visual acceptance limits remain.

The original **Enter inventory/status menu** is recovered:
Enter opens inventory, progress, gold and kill statistics; Escape returns to
gameplay. Read [Step 11 Task 02](docs/implementations/playable-sdl-runtime/steps/step-11/tasks/task-02-recover-enter-inventory-and-progress-menu.md)
and its [screenshot and continuation handoff](docs/journal/entries/enter-inventory-menu-handoff-2026-10-28.md).
Original-backed inventory/statistics, repeated Enter/Escape, protected Debug/ASan
persistence and fresh recording/replay pass within the
[recovery evidence](docs/journal/entries/enter-inventory-menu-recovery-2026-10-28.md).
Human visual review and low-mode/hourglass gameplay remain open.

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
continues under the selected object/interaction recovery above.

The [latest tower/storage follow-up](docs/journal/entries/tower-storage-render-followup-2026-10-28.md)
adds original collection sparkle and storage models, including the gold sword.
The reported translucent door remains unresolved; preserve original behavior
unless comparison proves a reconstruction error.

1. Read [project state and capabilities](docs/capabilities.md).
2. Follow the [handoff and working rules](docs/HANDOFF.md).
3. Open the [active runtime implementation](docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md)
   and its [selected object/interaction task](docs/implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md).
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
