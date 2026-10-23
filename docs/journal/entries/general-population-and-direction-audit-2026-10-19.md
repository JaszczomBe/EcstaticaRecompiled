# General Population And Direction Audit — 2026-10-19

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

## User Evidence And Current Result

The user confirms that the two original pedestal guards wander after intro 2, but sees no other enemies while exploring. F5 still set `E2R_DEFER_BACKGROUND_SPAWNS=1`, explicitly suppressing the original terrain scheduler. This continuation repairs its next live failures and changes F5 to `E2R_DEFER_BACKGROUND_SPAWNS=0`.

Population uses the original terrain families, random selection, placement, rejection, lifetime/culling and actor/action resources. Cylinder presentation already walks validated live actors, so there is no enemy-name whitelist or fabricated spawn position. Examples observed in the original archive include `w_gob3` (11), `w_spids2/3/6` (28/29/30), `w_sprit2/3` (72/73), `w_dorc2/3` (80/81) and `w_fish2` (117). Existing hosted name-pool labels are unreliable; these names come from `Code/ECSTATIC.FAN` and global archive IDs.

The user also reports that Joe no longer follows the diagnostic arrow and that simultaneous Up+Left freezes the arrow, **immediately after release**. That report remains open. Local frame-stepped and normal-speed SDL replays turn and displace Joe; both Debug and ASan update yaw and orientation matrices during combined input. A prior-source comparison gives the same combined-input result. Do not claim the direction regression fixed or dismiss the user's physical F5 observation based on these bounded replays.

## Recovered Contracts

Original `0x42f9c0` retains five independent inputs: node in EAX, actor ID in EDX, action ID in EBX, owner flag in ECX and orientation flag on the stack. The C lost the node and action, then dereferenced an uninitialized node on the first live secondary spawn. Both action-event callers and interpreter opcode 100 now retain those operands. Reverse node links, source ownership, destination position/angles, activation and queued action follow the original instructions.

The shared reverse-chain pose helper now retains its actor and the root/FK transform input, output and matrix addresses. Matrix-to-Euler conversion retains its destination and original Y/X premultiplication. Attached-root and IK branches remain outside the recovered pose fixture; cylinder rendering still omits articulated posing/collision. This is not full skeletal recovery.

Actor reset retains its selected ID and actor context, and accepts the archive's upper-half actor IDs. Queued-action installation retains actor/action/immediate flag. Consuming a queued action no longer uses a lost post-reset EDX as its actor. Scheduled action loading retains the scheduled node, and reclamation receives that node before list advancement.

`E2R_LoadPopulationActor` scopes corrected archive lookup/actor-name construction to original scheduler and spawn-event loads, restoring nested load/actor context afterward. Initial Joe/intro resources retain their existing initialization boundary. F5 does **not** require `E2R_POPULATION_PROBE`; that flag remains available for historical diagnostic comparisons.

The secondary resource that first exposed the spawn helper is actor 3803, `splash_s`. It is a splash effect, not combat-projectile acceptance. Guard wandering, generic population and secondary effects are distinct from accepted combat behavior.

All reconstructed repairs are mirrored in `GenerateRecon.js`; the existing staged index is preserved.

## Verification

`scripts/check-e2-spawn-action.py EXE [--asan]` executes original x86 and compares:

- 5,120 queued-action flag/list/reclamation cases, including scheduled nodes.
- 2,048 root/FK poses with rotations, absolute-matrix flags and adjacent memory.
- 4,096 matrix-to-Euler conversions with actual nonzero rotations.
- 768 spawn ownership/flag/memory/call cases, including absent resources, attached ownership and actor ID 3803. Loading, pose evaluation, activation and angle extraction are intercepted in this last contract comparison and tested separately where stated above.

Passing bounded runtime evidence:

| Route | Prefix |
| --- | --- |
| Debug, original generic spawning from startup, Space at horseback action 3, both guards, 900 population frames | `/tmp/e2-general-debug` |
| Debug, population from startup, 300 population frames, SDL camera 175→166→175, return floor 3328, five seconds released | `/tmp/e2-general-route-debug` |
| ASan, population from startup, 600 population frames, simultaneous Up+Left, release and five seconds idle | `/tmp/e2-general-asan` |
| Final ASan, 300 population frames, populated camera round trip, return floor 3328 and five seconds released | `/tmp/e2-general-final-route-asan` |
| Immediate combined-input traces with guards, Debug/ASan | `/tmp/e2-direction-guards`, `/tmp/e2-direction-guards-asan` |
| Combined input without per-frame Python/turn breakpoints | `/tmp/e2-direction-burst-fixed` |
| Natural intro, generic spawning, simultaneous Up+Left and released observation | `/tmp/e2-general-natural-debug` |
| Simultaneous input on the first released frame (`--release-delay 0`), with no attachment | `/tmp/e2-general-immediate-debug` |
| Prior-source combined-input comparison | `/tmp/e2-direction-old` |

The Debug 900-frame census ends with 27 loaded resources and eight active actors. The ASan 600-frame census ends with 22 loaded resources and eight active actors. Resource tables include inactive/cullable instances; loaded counts are not visible enemy counts.

The motion probe adds `--background-spawns` for the production scoped loader, `--simultaneous-turn` and `--burst-frames`, `--release-delay 0` for first-frame input, plus root/motion matrices, attachment pointers and per-frame heading captures. `--population-frames` with `--background-spawns` only records the census; it does not enable the old lookup flag. Actor state is read, never repositioned to satisfy a route.

Example:

```sh
python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --intro-skip-action 3 --pedestal-guards --background-spawns \
  --population-frames 300 --camera-round-trip --burst-frames \
  --observe-seconds 5 --timeout 180 --output /tmp/e2-general-route
```

All four SDL/X11 Debug/ASan builds pass. Generator syntax, stable regeneration and independent C/header/globals/names parity pass. Original population, FAN parser, motion-query, action-motion and forward/turn fixtures pass with ASan. The baseline runtime wrapper, all eight headless arrow rows and default SDL requester/OK/Escape checks in Debug/ASan pass. Logs use `/tmp/e2-general-*`; the final queued-action fixture is `/tmp/e2-general-queued-fixture.log`.

## Remaining Acceptance

Physical F5 direction/arrow behavior still requires reproduction and correction if it persists. Do not mark Joe's new report resolved. Broader enemy-family/action coverage, interactions with switches/doors/traps/pickups, combat, articulated collision, original models and sustained populated exploration remain open. Full experimental ASan runtime is **not** declared passing. The bounded populated checks replace the earlier F9c0-crash and failed-return frontier, not those broader acceptance requirements.
