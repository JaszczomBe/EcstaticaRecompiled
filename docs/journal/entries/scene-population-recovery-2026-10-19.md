# Scene Population Recovery — 2026-10-19

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

## Result And Limits

**Correction:** this terrain-population experiment did not restore the two fixed pedestal enemies in the user's reference. See the later [pedestal guard recovery](pedestal-guard-activation-2026-10-19.md), which establishes their separate `St_gobsc` resource and live cylinders. Names in the older hosted census are diagnostic labels from an incorrectly seeded name pool, not verified original names; use original archive IDs.

Original terrain-selected actor resources now load and enter the update list in a bounded post-release experiment. ASan records wandering state and displacement with Joe still active; a longer SDL input probe reaches camera 166 with additional cylinders. Everyday F5 remains the four-flag Joe route with automatic population deferred. Doors, switches, traps, pickups and general interaction are not restored by this slice.

Full population acceptance remains open. An extended Debug run crashes in the next attachment/spawn action helper, `FUN_0042f9c0`. The population-enabled ASan run crosses into camera 166 but fails the reverse-route checkpoint. Neither that route nor full experimental ASan is reported as passing.

## Census And First Failed Contracts

Before the companion-loader repair, after observed courtyard release, actor table `0x630b60` and update list `0x63726c` contain only Joe; the active script-scene list is empty. The population scheduler is called and its timing/gating state advances. No NPC output from the existing overlay was therefore a loading/activation problem, rather than a cylinder filtering problem. Script-owned objects remain a separate empty path.

The floor helper returned real heights, including 3,072, 3,328, 3,968 and 4,096. Its wrapper `FUN_00448a3c` discarded the result; all 25 sampled wrapper results were garbage `1457343648`. Original `0x448a3c..0x448a45` returns EAX unchanged. Returning the helper result allows spawning to reach actor loading.

`Files/ECSTATIC` is the flat resource archive, not `Code/ECSTATIC.FAN`. The old scan indexed actor sections by raw word 1 and searched through payload bytes. Raw word 1 is a local node ID; raw word 2 is the actor name. The first real actor section is at FANT +`0x2c`. There are 1,922 real actor headers, compared with 81 entries from the old scan. Actor 71 exists at archive offset `0x1666b0`; actor 77 is at `0x17035e`. Original constructor `0x42ba2c` reads normalized record +4 (name), not +0 (node).

Changing all actor identities at startup also changes the resource loaded as Joe: the legacy route uses resource `0xc2e872` (actual actor 4,119) under local actor 0, whereas actual actor 0 is at `0xf86f6`. Applying the corrected global index immediately exposes missing skeletal/IK inputs in `FUN_00423674` and `FUN_00423858`. It is not safe to silently replace the working F5 route with that experiment.

## Recovery Boundary

`E2R_POPULATION_PROBE` is opt-in. The production motion probe starts with it disabled, waits for the observed release checkpoint, then enables it and disables background deferral through `setenv`. The original scheduler chooses terrain, resource IDs, placement and lifetime. No actor, position, facing or camera is injected.

Missing actors use a header-aware archive lookup. Correct constructor identity is scoped to requested archive parsing, rather than every action-event record. The existing all-actor placement fallback in the loader is excluded from the population experiment: invoking it for a newly loaded actor reset Joe to his stand position. Real spawn placement remains owned by the scheduler.

Source-backed dependencies recovered along that path:

- `0x420ea5..0x420eb9`: initial script code and actor inputs.
- `0x428080..0x4280ab`: a contiguous line-of-sight vector retained through copy/add/floor calls; `0x4282a1` copies target position into actor +`0x152`.
- `0x42a098..0x42a3ad`: three wander vectors, six floor queries, obstacle bits, turn memory and action selection; both callers retain the actor.
- `0x427160` and `0x44e4a5..0x44e4de`: separate angle/distance outputs and short X/Z inputs for targeting/culling.
- `0x44e4fb..0x44e562` and `0x44e238`: persistent position/rotation destinations and selected actor ownership through deactivation and recursive attachments.
- `0x426cc3/0x426cd2`: next actor is at byte +`0x4c`. Two reads used byte +`0x26` because the global head has integer type. Rejection/removal could consequently drop Joe or fail to remove a non-head actor.

Original `0x421414..0x4215d3` only manages actor pixel-redraw rectangles and graphic-slot overlap. Under the existing `E2R_PROXY_MESH_BYPASS`, that pass is omitted along with polygon drawing. This avoids dereferencing absent mesh rectangles when populated actors enter view. Transforms, actor simulation, scene/terrain scripts and collision continue; no rectangle or actor flag is invented.

All reconstructed repairs are mirrored in `GenerateRecon.js`.

## Verification

New `scripts/check-e2-population.py`, normal and ASan:

- 1,922 real binary actor headers and 40 archive lookups.
- 128 original-x86 actor construction cases and 128 initial-script handoffs.
- 512 line-of-sight vector/query traces.
- 4,096 wander terrain traces with original initialized trig tables.
- 65,536 NPC polar vectors.
- Eight actor unlink/deactivation cases covering head, middle, tail and absent actors; no action callbacks in these lifetime cases.

The scene-grid fixture now verifies the original floor wrapper as well as the helper: 56 saved real floor cases, alongside the existing grid/camera/trigger suite. Existing NPC spawn/range, motion-query, actor-deactivation, script-flow and synthetic SDL cylinder fixtures pass, including ASan. Wrapper/matrix checks pass, as do Debug/ASan requester dismissal. Four build targets compile. Generator syntax, stable in-place regeneration and independent four-artifact parity pass. The initial git index snapshot still matches exactly; new changes remain unstaged.

Temporary evidence (not committed game assets):

| Probe | Evidence | Result |
| --- | --- | --- |
| Debug bounded loading | `/tmp/e2-population-debug-census{.json,-population.json,.log}` | 150 frames complete; real resources loaded/rejected/culled; Joe remains active |
| ASan bounded behavior | `/tmp/e2-population-asan-census{.json,-population.json,.log}` | 300 frames complete; active `w_stond2` (78) and `w_ba` (38) change positions |
| Debug extended population | `/tmp/e2-population-pixels-debug-route{.log,-population.json}` | Resource `w_fi` (117) reaches wander/moves, then attachment-event fault before the 300-frame input route |
| ASan populated traversal | `/tmp/e2-population-pixels-asan-route{.json,-population.json,.log}` and `-courtyard-held-{state.txt,sdl-window.ppm}` | Camera 166 reached; five live actor cues, three projected cylinders visible; reverse-input route misses return checkpoint |
| Everyday F5 Debug/ASan | `/tmp/e2-population-final-{debug,asan}-route{.json,.log}` | Camera 175→166→175 and five seconds released-input observation pass with population deferred |
| Baselines | `/tmp/e2-population-final-regressions.log`, `/tmp/e2-population-control-matrix.log`, `/tmp/e2-population-requester-{debug,asan}-command.log` | Runtime wrapper, eight arrow rows and requester probes pass |

Repeat the bounded behavior probe:

```sh
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl-asan/e2recomp \
  --population-frames 300 --population-only --output /tmp/e2-population-census
```

Add `--camera-round-trip` instead of `--population-only` to inspect the still-unaccepted traversal. The probe uses skipped logos/shortened intro timing; readiness and subsequent scene/action checkpoints, not recording timestamps, establish each phase.

## Next Frontier

Debug fault: `FUN_0042f9c0(0,3803,1)` dereferences uninitialized `in_EAX` at actor/node +`0x22`, through `FUN_0042b880 → FUN_0042b338 → FUN_0042ae80 → FUN_00427584`. Original `0x42f9c3..0x42f9c9` retains node EAX, actor ID EDX, action ID EBX and flag ECX. The C signature loses node/action, and both the event caller and helper's subordinate calls need an ownership audit. Do not add a null guard or disable that action to claim activation success.

After that bounded event family, revalidate population movement/crossing/return before promoting the flag into F5. Independently trace `0x452140/0x4523f8/0x4533ac` for one real script-owned object and interaction. The current absence of active script-scene children does not justify camera-to-script ID mapping or fabricated instances.
