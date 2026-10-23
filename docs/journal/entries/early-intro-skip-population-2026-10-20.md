# Early Intro Skip And Population — 2026-10-20

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

## Report And Cause

The user sees extra actors in the visible diagnostic runs, but only the two pedestal enemies after launching **Ecstatica Recompiled** with F5. The user confirms skipping the horseback intro with Space.

The launch file already sets `E2R_DEFER_BACKGROUND_SPAWNS=0`. VS Code's saved configuration selects `linux-clang32-sdl-debug` and `e2recomp`, the same current build used by the probes. No launch-flag change is needed.

The difference is the timing of the Space skip. An early skip reproduces the report: after release and another 180/300 updates, only Joe and actors 284/293 are loaded/active. The original script gate `DAT_0047a450` remains **1**. The scheduler clock continues advancing, but this separate gate suppresses terrain population. The later third-action skip used in most visible tests leaves the gate **0** and produces additional actors. Natural completion also enables population, including in an uninstrumented launch with the four F5 flags.

## Source Evidence And Repair

The loaded original code record 1390, `dav:skipsc`, starts `Start_sc` and `St_gobsc`, performs its cleanup/preload operations and includes opcode **0x6a**. Original interpreter `0x450928..0x45093a` clears `0x47a450` and advances the script cursor for that opcode. The existing `E2R_RequestIntroSkip` shortcut only called the scene-start helper for `Start_sc`; it omitted the skip script's remaining effects. Later intro paths happened to have enabled population already.

The recovered-action route now dispatches the original `skipsc` record through `FUN_0044f2fc`, which retains nested script ownership. The existing scene-start fallback remains for the bare baseline/resource-missing route. Population is enabled by the original script, with its terrain selection, placement, rejection and population limit; no debugger or host option writes the gate to satisfy the probe.

The eight-line generated C change is mirrored by anchored replacements in `GenerateRecon.js`. Syntax, in-place regeneration and independent C/header/globals/names generation parity pass with no unrelated generated drift.

The motion probe now supports `--startup-logo-delay-ms 5000` to match F5's default per-logo waits. Its snapshots/census record the script gate, scheduler tick and RNG state; actor census rows include original table flags. `--require-background-population` requires both an open script gate and an active actor with the original terrain-generation flag `0x08`. This distinguishes terrain spawns from the scripted pedestal pair and secondary effects without an enemy whitelist. F12 state packets also record the script gate and scheduler clock.

## Verification And Limits

| Route | Evidence prefix | Result |
| --- | --- | --- |
| Before repair, early Space, default logo waits, 300 population updates | `/tmp/e2-f5-population-skip1` | Only Joe and both guards |
| Before repair, early Space, 180 updates, gate/tick trace | `/tmp/e2-f5-population-gate-skip1` | Gate 1; three active actors |
| Before repair, third-action Space, same waits/trace | `/tmp/e2-f5-population-gate-skip3` | Gate 0; seven active actors |
| Before repair, natural intro, same waits, 300 updates | `/tmp/e2-f5-population-natural` | Eight active actors, including four terrain actors |
| Before repair, uninstrumented natural launch | `/tmp/e2-f5-population-raw` | Automatic packet records seven active actors; process later segfaults, so sustained runtime is not passing |
| Repaired early Space, Debug | `/tmp/e2-f5-population-script-skip1` | At release: gate 0, seven active actors and five projected cylinders; later NPC pose-event crash |
| Repaired early Space, bounded Debug release plus 30 updates | `/tmp/e2-f5-population-bounded-skip1-debug` | Completes the required open-gate/live-terrain-actor assertions; longer failure remains as recorded above |
| Repaired early Space, ASan, 180 updates | `/tmp/e2-f5-population-script-skip1-asan` | Both guards retained; gate 0 and live terrain actors 77/78/79; completes |
| Repaired third-action Space, ASan, 180 updates | `/tmp/e2-f5-population-late-skip3-asan` | Both guards retained; open gate and live terrain actors 77/78/79; completes |
| Repaired early Space, native Wayland Debug | `/tmp/e2-f5-population-native-skip1` | Extra actors present at release; later reaches the same NPC pose-event crash |

The Debug release packet shows Joe, the two original guards, three terrain actors and secondary splash actor 3803. Five cylinders are on screen; two resources are outside the viewport. Screenshot: `/tmp/e2-f5-population-restored.png`. Loaded/active counts are not all visible enemies.

Example:

```sh
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl-asan/e2recomp \
  --intro-skip-action 1 --startup-logo-delay-ms 5000 \
  --background-spawns --pedestal-guards --population-only \
  --population-frames 180 --require-background-population --burst-frames \
  --timeout 150 --output /tmp/e2-early-skip-population
```

All four SDL/X11 Debug/ASan builds pass. Original population and script-flow fixtures pass normally/ASan; the original spawn-action/root-FK fixture passes under ASan. The baseline runtime wrapper, all eight arrow rows, both SDL requester/OK/Escape checks and generation parity pass. Final baseline logs use `/tmp/e2-f5-population-final-*`.

## Open Pose-Event Frontier

Restoring early-skip population also makes the existing pose frontier reachable on that route. Debug, including native Wayland, fails after the first two 30-update population samples in `FUN_0042f9c0 → FUN_00424318 → FUN_00423674`. The source event requests actor 1159/action 702 from node `0x985ce4`; the root pose enters its IK branch and calls the leaf without retaining the node from `local_30`. The leaf dereferences uninitialized `in_EAX` at +3. Original `0x42457c..0x424580` supplies that node in EAX. Subsequent IK transforms/angles still contain unrecovered inputs; the passing root/FK fixture explicitly excludes this branch.

The preceding native Debug `0x42faf8 → 0x424318` failure also remains open. Do not call the restored early-skip Debug exploration route stable, or declare full experimental ASan passing, on the basis of the bounded population checkpoint or the passing ASan run. Next recovery is the original node/root/IK contract required by these NPC action events, with corresponding original-code coverage.

The prior direction/modifier changes remain unstaged alongside this continuation. The starting index is unchanged; no commits are made.
