# Pedestal Guard Activation — 2026-10-19

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

## Correction And Result

The user's comparison correctly showed a missing population requirement: camera 175 contains Joe and two green enemies before Joe frees himself. The earlier terrain-population experiment did not establish these instances, and its summary overstated scene restoration. Its opt-in random spawns remain a separate experiment.

The ordinary four-flag F5 route now loads the original two companion tracks and presents their orange cylinders alongside cyan Joe. Restrained and released checkpoints have three live actors and three cylinders inside the viewport. No debugger call activates the companion in this route. Background spawning remains deferred; the population-probe flag is unnecessary for these guards.

This is cylinder presentation and bounded activation, not completed enemy AI/combat, articulated collision, audio playback or general object interaction. Full experimental ASan acceptance remains open.

## Original Resource Evidence

`Files/ECSTATIC` resource `St_gobsc` is at archive offset `0x1274a`. Its normalized scene header is type 25, resource 101, view 175. It contains exactly these two tracks:

| Actor ID | Original name | Local action reference | Initial X,Y,Z |
| --- | --- | --- | --- |
| 284 | `gob3` | 907 | 8560,3968,-16456 |
| 293 | `gob3b` | 930 | 7276,3600,-18672 |

Their actor resources are at `0x21d1bc` and `0x223ee0`. The original global name tables confirm the names and namespaces. Original `dav:skipsc` (code 1390) plays both `Start_sc` and `St_gobsc`; `dav:stgob` (1393) plays the latter. The regular script path already attempted the companion. With no loaded actors it completed empty, leaving scene flags 6 and no active children. Reinvoking `PlayScene` after release consequently did nothing. Fixing the loader at its first activation is necessary.

The hosted actor-name pool is independently malformed: raw 284/293 are labeled `samuel1`/`door`, and raw 261 is actually `stok1`, not the earlier diagnostic label `spide_w3`. Identify these resources through original archive/global-name IDs; the runtime labels in older census files are not verified original names. Global name-pool repair remains separate.

## Recovered Contracts And Prototype Boundary

- `0x452140` now uses the header-aware archive lookup and normalized actor-name constructor field for `St_gobsc`. It retains each original child/action, placement and scene activation. Correct identity remains scoped to this companion (or the existing explicit population experiment); enabling it for all intro actors exposes a separate horseback attachment failure. Joe keeps the working resource route.
- `0x4238a3..0x4238b7` explicitly forwards reference+4, root matrix and reference+0x10 to the existing Q14 vector helper. Root reference chains continue to update.
- `E2R_PROXY_MESH_BYPASS` now omits child-bone transforms/IK after root references (`0x4238fe` onward), plus the alternate box/rounded mesh raster paths `0x425018/0x425538`. Original actor scripts, root transforms, locomotion and scene selection continue. Bone collision/attachments are not validated by cylinder mode; polygon and articulated-model recovery remain future work.
- The first Debug guard sound event crashed in `0x427160` through `0x42fce0`. Sound ID, node, proximity flag, volume override and stack channel are now separate inputs, with original distance/height attenuation and resource-volume scaling. Event, impact and ambient callers preserve their original operands. The sound wrapper retains the resource/volume into the existing backend boundary; this does not establish audible playback.
- ASan then exposed node scale restoration using an uninitialized pointer into a returned event-handler stack. `0x42ce70` now receives its actual node; four terminal/interpolated/restoration callers retain that node through normalization and scale propagation. No null guard substitutes for the lost input.

All reconstructed fixes are mirrored in `GenerateRecon.js`.

## Verification

The population fixture now additionally checks the actual companion header, original actor names and starting positions; 42 archive lookups include both guard resources. It compares 4,096 root-reference transform cases, 2,048 sound handoffs and 512 node-scale updates with original i386 instructions, alongside the previous construction, script, sight, wander, polar and removal cases. Normal and ASan fixture runs pass.

Use the ordinary F5 flags and real SDL keyboard route:

```sh
python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --pedestal-guards --camera-round-trip --observe-seconds 5 \
  --output /tmp/e2-pedestal-guards --timeout 120
```

`--pedestal-guards` waits for both original actors while Joe is restrained, checks update-list membership and projected cylinder rings, then observes release and the existing movement route. It writes guard/action/position records and normal SDL visibility packets. Later culling is recorded rather than requiring offscreen actors to remain active. It never inserts actors or changes their state/position.

Debug evidence `/tmp/e2-guards-debug-sound-route{.json,.log,-guards.json}` passes camera 175→166→175 with original floor 3328 and five seconds of released input. The final restrained capture `/tmp/e2-pedestal-guards-verified.png` visibly shows the two orange stair cylinders and cyan Joe.

Earlier ASan attempts establish the restrained/released guard checkpoints, but do not establish the final route: `/tmp/e2-guards-asan-route-final.log` reaches camera 175 on return at floor 4096 rather than 3328; `/tmp/e2-guards-final-asan-route.log` exposes the subsequently repaired scale-ownership fault. Final checks below supersede the repaired crash while keeping the failed attempts explicit.

Final source verification:

- `/tmp/e2-guards-checked-debug-route{.json,.log,-guards.json}`: restrained/released projection, SDL camera 175→166→175, floor 3328 and five seconds idle pass.
- `/tmp/e2-guards-checked-asan-controls{.json,.log,-guards.json}`: restrained/released projection, Up/Down/Left/Right displacement/rotation and five seconds idle pass.
- `/tmp/e2-guards-scale-asan-route{.json,.log}`: after the scale fix, camera 175→166→175 is observed without a sanitizer report, but Joe returns at floor 4096 and the required floor-3328 checkpoint fails. This route is **not passing**. Do not weaken its assertion or report full experimental ASan success.
- Four SDL/X11 Debug/ASan builds pass. Generator syntax, stable regeneration and independent C/header/globals/names parity pass. Population fixtures pass normally/ASan, including original companion evidence, root references, sound and scale. ASan grid, NPC spawn, deactivation, script-flow and synthetic SDL cylinder fixtures pass.
- `/tmp/e2-guards-checked-baseline-command.log` and `-controls-command.log`: baseline runtime wrapper and all eight arrow rows pass. Both Debug/ASan SDL requester, OK dismissal and Escape checks pass in `-requester-{debug,asan}-command.log`.
- The original git index snapshot matches; all new work remains unstaged. No commits or tags are made in this continuation.

## Remaining Work

Keep terrain population opt-in. Restore one source-confirmed switch, door, trap or pickup interaction separately; do not infer objects from camera IDs. General combat, bone posing/collision and attachments, runtime name pools, the terrain-population attachment event `0x42f9c0`, and sustained full experimental ASan acceptance remain open.
