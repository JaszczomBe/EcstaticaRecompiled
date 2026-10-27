# Enemy bodies and animation recovery — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Request and ownership

The user accepted the corrected player (“perfection, works as a charm”) and
requested enemy animation next, ahead of game save/load. Session saving, replay
and the regression-suite implementation remain closed milestones with their
recorded minor limits deferred. [Step 08 Task 03](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-03-activate-scene-backed-children.md)
owns this pass; the [player record](player-model-and-animation-2026-10-27.md)
retains the prerequisite projection correction and acceptance.

## Implementation and original evidence

`E2R_NPC_MESH=1` enables original character ellipsoid bodies and full skeletal
poses through the renderer recovered for Joe. F5 enables both character flags;
gameplay suite commands now pass `--player-mesh --npc-mesh`. Original resources,
scheduler, actions, movement, AI and damage remain in control. No artwork,
replacement animation timing, health writes or actor-coordinate assignments were
introduced.

The existing bypass now distinguishes rounded primitives from NPC polygon/box
leaves. Full pose `FUN_00423858`, redraw `FUN_004211c8` and ellipsoid
`FUN_00425538` select character owners using node `+0x22`; polygon
`FUN_00424e44` and box `FUN_00425018` retain the NPC bypass. The selector uses the
existing host presentation classification from original actor/representation
names, flags and generated-actor metadata, retaining prior character identity
when dead actors lose their representation. This is a render-selection heuristic,
not a complete original resource taxonomy or a change to AI. It rejects Joe,
items, doors and weapons in the character-specific host selector. Reconstructed
changes are mirrored in `GenerateRecon.js`.

Physical-page presentation/export accepts either character flag. SDL omits
character diagnostic shapes while retaining objects/equipment and health/potion
status. `--npc-mesh` evidence records each selected active enemy's identity,
health/state, node positions and local-pose hashes. Guard observations require
nonempty, changing poses for both original actors. Pixel differences against the
static background now describe all original actors in the physical frame; Joe's
local-pose hash remains player-specific.

Original executable/data evidence remains bounded and reproducible:

- Original `St_gobsc` resource **101**, camera **175**, contains actor tracks
  **284/gob3** and **293/gob3b**. The real archive fixture checks names, positions
  and tracks; historical 319/322/318 child identities remain unassociated.
- `FUN_00423858` (`0x423858..0x424162`) drives full bone poses; original camera
  origin/composition, projected ellipsoid basis and rounded dispatch are checked
  by `check-e2-player-mesh.py`. The captured-pelvis projection regression stays.
- Original ellipsoid rasterization uses its shade map, material/depth tests and
  physical surfaces. `check-e2-ellipsoid-pixels.py` compares actual pixel/depth/
  dirty-rectangle results, rather than only draw-call or hash changes.

The [original reference](original-game-reference-2026-10-14.md) shows two green
articulated creatures around the pedestal during restraint/release. New captures
visibly contain those green bodies, heads and limbs, replacing cylinders; the
attack frame shows one striking Joe on the stairs. This is an agent visual
comparison, not synchronized animation-timing or fresh human enemy acceptance.

## Passing native evidence

Artifacts live under ignored `.tmp/enemy-animation/`; they are local evidence,
not committed game assets. All probes have explicit time/update bounds, recording
off and SDL dummy. Guard/intro observations end at their bound under GDB; they
are distinct from routes that complete the real Quit lifecycle.

| Prefix | Configuration and population | Result |
| --- | --- | --- |
| `guards-debug-04` | Debug, live scripted/terrain actors, 8 input frames per direction and 5 s observation | Original green bodies visible in restrained/released and later changing poses; bounded probe completes |
| `guards-asan-05` | ASan, same live policy | Guards **52/53 nodes**, **12 distinct poses each** across 22 enemy checkpoints; bounded probe completes without sanitizer report |
| `damage-asan-06` | ASan, live population, real receive-hit navigation | Guard **284** inflicts actual health loss **100 → 95**; changing original bodies; Cancel/resume/Quit exits **0** |
| `workshop-debug-11` | Debug, scripted enemies retained, terrain spawns deferred | Workshop traversal, sword pickup, equipped movement and Cancel/resume/Quit pass; smith **56 nodes, 6 distinct poses**, native exit **0** |
| `workshop-asan-11` | ASan, same scripted-enemy policy | Same route and smith node/pose counts pass; native exit **0**, no sanitizer report |
| `natural-asan-11` | ASan, live population, uninterrupted horseback intro, restrained/released guards, 2-frame input phases and 3 s observation | Bounded probe completes; **11 distinct poses per guard**, no sanitizer report |

Representative reproducible commands:

```sh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --player-mesh --npc-mesh --pedestal-guards --background-spawns --frames 8 \
  --sdl-events --observe-seconds 5 --timeout 120 \
  --output .tmp/enemy-animation/guards-asan-fresh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --player-mesh --npc-mesh --suite-scenario damage --background-spawns \
  --gameplay-menu-exit --burst-frames --timeout 240 \
  --output .tmp/enemy-animation/damage-asan-fresh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl/e2recomp \
  --player-mesh --npc-mesh --suite-scenario sword --intro-skip-action 1 \
  --intro-skip-progress 83 --gameplay-menu-exit --burst-frames --timeout 180 \
  --output .tmp/enemy-animation/workshop-debug-fresh
```

`final-identity.json` retains source hashes and final executable identities:

- SDL Debug: `a3cdf42315cb73ba9295edbcf0376a821cdaf1e73007fbed246a21022fcf2ac4`
- SDL ASan: `feb7a512edb815ca07f13e06701a43f418735f146ed98628a9e56a4ce3328ddb`

## Retained failures and acceptance limits

| Prefix | Observed failure and consequence |
| --- | --- |
| `guards-debug-02` | Initial broad activation entered unfinished flat-polygon raster `FUN_00424e44 → FUN_00433d30 → FUN_00431a7c → FUN_00418b00`, with invalid surface selector **−973722242**, then fatal error handling. NPC polygon/box rendering stays bypassed; no guessed surface guard was added. |
| `combat-debug-05` | Live workshop navigation exhausts its replan budget before combat. No kill acceptance. |
| `combat-debug-07` | Terrain-deferred workshop/pickup and first three attacks pass; requested down attack never starts. No complete combat acceptance. |
| `combat-asan-07` | Terrain-deferred workshop/pickup and two attacks pass; right attack reaches bitmap pool `FUN_004451a8 → FUN_00452a58 → FUN_00414e68`, then error formatter faults. This unrepaired path is separate from the initial polygon failure; no claim that NPC rendering repairs it. |
| `combat-debug-10` | Explicit delayed skip/live population reaches workshop, pickup and first attack; Joe dies during the next attack. No passing journey. |
| `combat-asan-10` | Four attack phases pass. Smith health **100 → 60 → 44 → 4 → −12**, state **11**, with a retained **56-node** corpse pose. Joe lands two original melee hits; actor **25** lands the final blow. The fixed-Joe kill assertion correctly remains unsatisfied and encounter setup fails because the smith is already dead. |

The last ASan captures establish changing smith poses, damage and a rendered
final corpse, **not a passing Joe-kills-smith regression or complete death-clip
sampling**. Completed guard/workshop routes do not erase these failures. The full
suite has not been rerun with NPC bodies; human enemy visual review, all species,
actions, continuous timing/occlusion and longer stability remain unqualified.
Equipment and object polygons/boxes, original HUD and arbitrary video modes
remain separate work. Functional game save/load follows this enemy milestone,
then game sounds and music.

## Verification

All four SDL/X11 Debug/ASan builds pass. Independent scratch generation matches
all four generated artifacts (`parity-09`), with no unrelated generated drift.
Normal and ASan player-render original-x86 comparisons pass: **6144** skeletal
poses, **6144** camera origins, **8192** projected bases, **4096** composition/draw
cases and **262144** shade entries per mode. ASan additionally passes **3072**
ellipsoid pixel/depth/rectangle/lock cases, **12288** pickup query/caller cases,
**4096** model-origin cases, **576** polygon-routing cases and twelve temporary
polygon records. Normal/ASan population fixtures pass original guard identities,
construction, action, deactivation and transform contracts. Normal/ASan SDL marker
fixtures verify character selection excludes doors/items/Joe, preserves a corpse
without its representation, and does not mutate game memory. All **67** suite
contracts pass. Documentation tree/update and whitespace checks accompany this
record; historical full-suite results remain historical.

## Subsequent human play and repairs

The user likes the recovered enemy rendering and supplies a short-play bitmap
crash plus a dropped potion that stays attached without healing. The
[follow-up](enemy-play-crash-and-dropped-potion-2026-10-27.md) identifies false
action-directory entries inside sound payload and a truncated representation-name
pool. It records the repairs and fresh qualification; the failed attempts above
retain their original outcomes.
