# Player model and animation recovery — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Scope and priority

The user closes investigation session saving, session replay and the gameplay
regression suite as milestones with minor follow-ups, and orders the next work:
original player model/animation → functional game save/load → other enemy
animation → sounds → music. [Step 08 Task 02](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-02-recover-joe-geometry-and-rendering.md)
owns player acceptance. The handoff stays a durable navigation/rules document;
changing implementation evidence belongs here and in the owning task.

The player reuses original model and action resources. `E2R_PLAYER_MESH=1`
selects Joe's original body while `E2R_PROXY_MESH_BYPASS=1` retains the accepted
NPC/equipment diagnostic path and omitted original HUD. F5 and gameplay suite
journeys now enable the player flag; Joe's cylinder/label is hidden, while the
health/potion panel remains. `E2R_PLAYER_MESH=0` permits the earlier comparison.

## Visual rejection and projection correction

The user's follow-up accepts the input/animation response but rejects the model's
ellipsoid placement, size and shape. The supplied camera-672 screenshot shows a
grossly disfigured Joe. The original footage/contact sheet in the
[reference record](original-game-reference-2026-10-14.md) shows a coherent red-shirted
human body. The preceding implementation was incomplete; its claimed general
projected-basis/camera qualification is withdrawn for the reason below. Player
visual fidelity remains the active milestone, before game save/load.

A read-only live capture (`.tmp/player-fidelity/baseline-03-*`) retains all **70**
nodes, local/world/camera matrices, dimensions and mapped source tables. Matrix
norms and local radii are plausible; nearly round parts become extremely thin
projected shapes. Replaying the actual pelvis through original `0x432ecc` yields
**53/57/−1** (X extent / Y extent / slope), while the old reconstruction yields
**56/3/54** for the same **52/60/43** local radii and camera matrix.

Original register/vector tracing in `trace2.log` identifies the first divergence:
`0x433202..0x433215` calls the angle helper with **Y then X**, where the
reconstruction supplied X then Y. The subsequent frame angle and basis sums at
`0x43323b..0x43331e` also selected the wrong components. Five explicit X/Y
corrections in `FUN_00432ecc`, mirrored in `GenerateRecon.js`, restore the original
frame and projected extents. No dimensions, bone offsets, animation timing or
player coordinates are tuned to match a screenshot.

The earlier random projection tests allocated their Euler angle arrays on the
high host stack. `E2R_ApplyEulerMatrix` rejects pointers above `0x70000000`, so
those matrices stayed **zero** and both original and reconstructed functions
agreed on degenerate input. The pose/other tests have their separately recorded
scope; the old **8192 projected-basis / 4096 camera-draw** counts do not establish
nonzero projection coverage. `nonzero-oracle-fail.log` retains the corrected
fixture failing on the previous code at its first nonzero case.

The fixture now stores angles in mapped game memory, asserts nonzero matrix rows
and includes the captured pelvis as a fixed original-x86 counterexample. The
corrected **8192** projected-basis and **4096** camera/draw cases pass normally and
under ASan, plus the captured **53/57/−1** result. `nonzero-asan-06.log` retains
current ASan output. Four-artifact scratch parity passes in `parity-09/`.

`corrected-debug-05-*` retains ten actual pose/pixel samples through four arrow
press/release phases and released observation. Visual inspection against the
original contact sheet now shows connected head/torso/limbs, normal proportions
and a coherent silhouette. The prior equivalent `player-model-debug-17` is the
malformed control; it is not visual acceptance. New captures remain headless
SDL with recording off. Exact camera-672/human replay and whole-game fidelity
are not claimed from the bounded courtyard comparison. The original free-standing
reference frame (contact sheet 09) was inspected beside the corrected courtyard
capture; silhouette, clothing and limb proportions are coherent again, without
claiming identical action phase or pixel colors. `before-after.png` retains the
matched old/corrected crop and `corrected-workshop.png` the new close-up attack.

`movement-08/` passes **8/8** existing Debug/ASan startup, input/release and
courtyard-return results in **60.32 s**. Both native journeys Cancel/resume/Quit,
exit **0**, and complete inspection. `corrected-sword-asan-07` also reaches the
workshop through real input, picks up the sword, performs all four attacks and
moves after release; ten distinct 70-node pose/pixel samples, actual menu exit
**0**, no sanitizer report. `nonzero-final-10.log` retains the final normal
original-code comparisons. SDL Debug/ASan builds pass; current fix is five
component selections plus corrected regression inputs, preserving the previously
staged implementation. No commit or push is made.

## Earlier implementation and evidence

The sections below describe the preceding implementation and its historical
results. The projection qualification above supersedes their zero-matrix scope;
route completion and changed pixels did not prove Joe's proportions.

## Recovered contracts

All reconstructed repairs are mirrored in `E2Recomp/tools/GenerateRecon.js`.

| Original boundary | Recovered behavior |
| --- | --- |
| `0x423858..0x424162`, `0x423674`, `0x424164` | Explicit parent/sibling ownership, complete forward skeletal transforms, reference targets, endpoint/IK solutions and derived scale; preserve the earlier proxy root-only path for other actors |
| `0x426491`, `0x42649f` | Initialize each allocated node's two matrices, rather than overwriting the camera identity through lost destinations |
| `0x42c790`, `0x42b490`, `0x42b5fc` → `0x442954/0x4429e0` | Scope interpolated/reset metadata to the actual target node and retain interpolation factors; restore prior calculation context |
| `0x424ed0..0x424f9b` | World-to-camera node origins and near-depth handling |
| `0x425538..0x4257df`, `0x432ecc..0x433689` | Perspective, per-axis camera matrix composition with original fixed-point rounding, projected ellipsoid basis and explicit draw/surface ownership |
| `0x4307d0`, `0x430fd8..0x431775`, `0x45d10e/0x45d2cc/0x45d482/0x45d5f8` | High-resolution ellipsoid pixel columns, clipping, materials/transparency, original shade-map/depth reads, depth tests and dirty bounds; replace self-modified/register-only inputs with explicit C |
| `0x415167..0x41535b`, `0x414f00` | Original sixteen-profile actor palette/shade table, replacing synthetic diagnostic colors |
| `0x417c38..0x417ceb`, `0x41868c` | Explicit background pixel copy and rounded depth spans with independent hosted buffers, real pitch and matching Unlock selectors |
| `0x4215bd`, `0x421684`, `0x424b48..0x424bd7`, camera/background callers | Pass the actual dirty actor; restore background/depth pages and copy depth page 1 to drawing page 0 for each dirty rectangle |

A hardware watchpoint captured Joe's `+0xe4` rectangle pointer becoming a small
extent value inside node metadata updates. The old calculation context pointed
to the actor root rather than the selected node. Recovering that context and the
retained interpolation factor removes the corrupting writer; it does not merely
skip the bad rectangle.

The DirectDraw provider already owned real storage. A read-only
`E2R_GetDirectDrawPixels` accessor now exposes an unlocked physical surface's
pixels, dimensions and pitch to native presentation/visibility capture. In player
mode the front source follows the actual physical Flip page. Auxiliary background
buffers remain separate; no SDL operation is added to reconstructed game logic.

## Original executable comparisons

Original data remains external at `/home/rgrabowski/Games/Ecstatica2`.
New fixtures read executable bytes from `E2WIN95.EXE`; the raster fixture also
reads the installation's original `SHADEMAP.DAT`. No original assets are added
to the repository. Each comparison passes normally and under ASan:

| Fixture | Cases per mode |
| --- | --- |
| `check-e2-player-mesh.py` | 262144 shade entries; 6144 forward skeletal poses; 6144 camera origins; 8192 projected bases; 4096 camera composition/projection/draw selectors |
| `check-e2-ellipsoid-pixels.py` | 3072 pixel/depth/material/dirty-bound/Lock cases; 1902 draw actual pixels |
| `check-e2-interpolated-node-events.py` | 8192 interpolated node events and 4096 reset/interpolation/context/actor-rectangle cases |
| `check-e2-render-copies.py` | 1536 pixel/pitch/overlap/selector cases; 1152 depth/odd-width/alias cases; 256 dirty-depth page/list cases |
| Existing `check-e2-ddraw-surfaces.py` | 100 ownership/lifetime cycles including locked accessor rejection and physical Flip contents |

The skeletal fixture executes the original bone solver and its math dependencies.
The raster fixture executes original self-modifying column drawers; only surface
Lock/Unlock are intercepted. Copy comparisons intercept hidden-cursor leaves;
physical-to-physical COM blits are outside that fixture. Camera/draw dispatch
comparison intercepts the final drawer, independently covered by the raster
fixture. Existing pickup, population and polygon-input extraction fixtures were
adapted to the recovered function bodies, retaining their original comparisons.

Reproduce the registered original/host/tool checks:

```sh
python3 scripts/run-e2-suite.py --configurations debug asan --block checks \
  --output .tmp/player-render/contracts-fresh
```

Current result: `.tmp/player-render/contracts-25/`, **47 PASS**, no failures,
blocked checks or skips, **32.68 s**, exit **0**. This includes independent
four-artifact scratch generator parity and **67 suite / 46 navigation** contracts.
Existing rectangle-copy, population and polygon-input original-x86 fixtures also
pass under ASan after recovery. The four SDL/X11 Debug/ASan builds pass. Build logs are retained under
`.tmp/player-render/build-*-17.log`, `build-*-23.log` and `build-x11-*-28.log`.

## Actual player rendering and gameplay

All agent journeys use SDL dummy, bounded inputs/updates and `E2R_RECORD=off`.
No actor position, facing, animation slot or camera is assigned to manufacture
player acceptance. Per-phase mesh evidence reads the original flat node chain,
local bone pose hashes and actual physical-page pixels against the static
background. SDL cylinder pixels cannot satisfy this test. Modal snapshots are
excluded. Visibility packets retain game pages and SDL present/window captures.

| Current evidence | Result |
| --- | --- |
| `player-model-debug-17` | Ten samples, 70 nodes, ten distinct local poses, every sample has rendered pixels; four direction press/release phases plus released observation |
| `player-courtyard-asan-20` | Camera 175 → central courtyard 125 → 175, 70 nodes, changing poses and pixels at each sampled view |
| `player-sword-debug-19` | Actual route to workshop 347, Space pickup, representation 12 → 9, four sword attacks and equipped movement; nine distinct poses, real player pixels in all samples |
| `player-sword-asan-29` | Workshop pickup, representation 12 → 9, four sword attack directions and equipped movement; ten changing poses/pixel samples, Cancel/resume/Quit and native exit 0 |
| `player-natural-asan-22` | Natural horseback/pedestal intro completes without horseback Space; released movement follows, nine samples/distinct poses with 70 nodes |
| `movement-24/` | **8/8 PASS**, Debug/ASan movement/release and recorded courtyard return, **61.32 s** |
| `unarmed-26/` | **8/8 PASS**, Debug/ASan basic and advanced attacks in all four directions, release and subsequent movement, **51.89 s** |
| `swimming-27/` | **10/10 PASS**, Debug/ASan swimming representation/actions and four water attacks, release and subsequent movement, **80.26 s** |

The three suite subsets contain six native journeys. Each cancels/resumes through
the real menu, confirms Quit, exits **0**, and completes inspection. These are
**26 logical passing results**, including repeated build/startup prerequisites;
they are not 26 distinct gameplay routes. Retained HTML/JSON/JUnit reports own
per-case outcomes and pinned executable/source identities. Both movement journey
reports retain 70-node samples with eight distinct local poses across nine samples.

Representative commands:

```sh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl/e2recomp \
  --player-mesh --frames 30 --sdl-events --observe-seconds 3 --timeout 120 \
  --output .tmp/player-render/player-model-fresh
python3 scripts/run-e2-suite.py --configurations debug asan --block movement
python3 scripts/run-e2-suite.py --configurations debug asan --block unarmed \
  --filter '*.Combat.UnarmedDirections'
python3 scripts/run-e2-suite.py --configurations debug asan --block swimming \
  --filter '*.Movement.Swimming' '*.Combat.SwimmingDirections'
```

Visual inspection of the captures identifies the live model at the **rear
stocks**, then changing body/limb positions and workshop combat poses. The blue
foreground body-like object remains part of the static background and is not
used as player evidence. Full-resolution captures and local enlarged crops are
under `.tmp/player-render/`; diagnostic NPC/weapon shapes remain visibly distinct.

## Retained failed attempts and corrections

- Initial native/original-code execution inside the sandbox could not run i386
  probes/GDB. The same bounded read-only/native checks run with reviewed execution
  escalation. No automatic approval rejection occurred.
- Earlier rendering attempts exposed missing calculation contexts, matrix
  destinations and camera/copy inputs before useful physical model pixels existed.
  Prefixes `01..14` retain exploratory artifacts; they are not acceptance runs.
- `player-model-debug-15` completes the input route but contains only sparse,
  disappearing player fragments. Dirty-depth restoration still called a legacy
  helper with lost source/X arguments. Original `0x424b48` proves **1 → 0** depth
  restoration. Repair plus the 256-case original comparison produces sustained
  player silhouettes in `17` and the later native journeys.
- `contracts-16/` has **46 PASS / 1 FAIL**: adding eight Debug/ASan fixture cases
  changed catalogue size from 205 to 213. The suite-contract expectation was
  updated; `contracts-25/` passes all 47 selected checks.
- `player-camera-asan-18` crosses views without a sanitizer report, then fails the
  older direct reverse-input return assertion. It is not a passing round trip.
  The accepted recorded-courtyard navigator in `20` and `movement-24/` passes.
- `player-natural-asan-21` lacks inspection startup heartbeat and is interrupted
  by the 30-second no-progress watchdog during uninterrupted natural intro.
  Its SIGINT is the probe's interruption, not a spontaneous native fault. Player
  probes now enable bounded inspection with rolling-frame cap 8; `22` completes.

## Acceptance and next work

The original high-resolution player ellipsoid body and bone animation are
implemented and automatically qualified over the recorded routes. This is not
exhaustive animation or whole-game visual acceptance. Fresh human F5 review is
still pending, especially stocks/platform occlusion, continuous silhouettes and
movement timing. Original equipped-object polygon geometry, NPC models, original
HUD, low-resolution/arbitrary video modes and longer gameplay remain separate.
The full regression suite has not been rerun with the player mesh enabled.

Functional **game save/load** is the next feature milestone. Recover original
serialization and restoration ownership, including actor/action/world state and
pointers/resources, then prove menu save → continued changed gameplay → load in
Debug/ASan. Existing slot previews and investigation session recording do not
satisfy that milestone. Preserve the earlier suite/replay minor gaps without
reopening those completed implementation tracks.

## Subsequent user acceptance and priority change

The user reviewed the projection-corrected F5 build and confirmed “perfection,
works as a charm.” The current player model/animation milestone is accepted.
The next request explicitly moves enemy animation ahead of game save/load;
[enemy recovery](enemy-model-and-animation-2026-10-27.md) records that work.
Earlier pending-review/next-save-load statements above describe the state before
this acceptance and priority change. Equipment polygons, original HUD, broad
video modes/actions and longer gameplay remain recorded follow-ups.
