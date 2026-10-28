# Original object rendering recovery — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 12 Task 01](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-01-recover-object-rendering-and-animation-contracts.md).
Baseline: `a2a6043` on `linux-e2-reconstructed-runtime`. The staged handoff documents
and Git index are preserved. This is the first bounded rendering slice, not
completion of every item, weapon, door and hazard variant. Audio remains deferred.

## Original asset and owner map

`scripts/e2_object_assets.py` reads the installed version-55 `OFFSETS`,
`Files/ECSTATIC` and eleven `Code/ECSTATIC.FAN` name pools. It records hashes,
actor/node/material/texture records, representation slots, callback references
and scene tracks. Assets stay external; local evidence is in ignored
`.tmp/object-render/`, including `assets-final.json`.

| Class | Original identity and location | Representation and drawing ownership |
| --- | --- | --- |
| Item | **537/fakepot2**, scene **225/cyd_shlf**, camera **352**, `(428,4096,-11856)` | **67/potion**, standing action **384/poglow**; 12 nodes, 24 vertices and 32 polygon faces, plus rounded components; pickup follows `ken:fakepot` rather than assuming a healing effect |
| Weapon | **3717/nschwrt1**, scene **1909**, camera **347**, `(-972,3884,-10208)` | Static loose model: 5 nodes, 7 vertices, 10 faces, no standing representation; `dav:sword1` pickup, then original node `+0x13a`/actor `+0xf2` attachment to Joe; pickup action **692**, held motion follows Joe's actions |
| Door | **980/kdorr**, scene **373/cyd_dor8**, camera **347**, `(-2368,4096,-10944)` | **28/door**; 33 box/rounded nodes, no stored polygon faces; hit **370/doorshudder** and observed lethal transition **377/Rdooropen**; representation removal leaves original final geometry, not invented rubble |
| Acid/slime pools | **710/slime**, **711/slime2**, **908/slime3**, **909/slime4**, **912/slim2b**; scene **350/mt_slim1**, camera **116**, floor **2432** | Representations **102/slime**, **103/slime2**, **126/slime3**, actions **532/slimeglo**, **531/slimglo2**, **627/slimglo3**; flattened ellipsoid nodes and animated rounded bubble nodes; no polygon faces or graphic/sprite registration |

The five pool placements are respectively `(-10200,2432,-1848)`,
`(-9824,2432,-1800)`, `(-10024,2432,-1648)`, `(-10488,2432,-1424)` and
`(-9912,2432,-2024)`. Original callback references identify **236/ken:slimhit**.
That identifies the hazard's script owner; this pass does not qualify damage,
resistance or collision behavior through a natural visit. **55/w_slim** is a
separate moving slime: representation **129/slimmove**, actions **641–643** and
**655/slimdie**, callback **1011/ken:slimmove**. It is inventoried but remains on
its previous fallback.

The acid-pool method is established from actual resource records and dispatch,
not its name: the first node has half dimensions **122,10,114**, flags **0x2042**,
and the rounded/box selector's box bit is clear. Original `0x424cbc..0x424dd8`
selects the rounded passes; `0x425538` composes the camera basis,
`0x432ecc` projects the quadric, and the high-resolution ellipsoid raster writes
indexed pixels and depth. Original actions animate node dimensions, positions,
materials and flags. Camera 116's clean background has no green puddles; the
initial original physical frame differs from it at **2,498 pixels**, identically
in Debug and ASan. Later frames contain changing bubbles/pool pixels. This is
neither a textured polygon water surface nor a fabricated 2D pool.

## Recovered contracts

- `E2R_UseProxyMesh` admits only the selected registered original actor IDs and
  their bone owners at **+0x22**. Child recursion must resolve that owner too;
  admitting just the root left descendants unposed. Other object/NPC polygon
  bypasses and legacy HUD/graphic skips remain.
- `FUN_00431a7c`: original **0x4322b5..0x432bcc** locks the preserved surface
  selector, retains pixels/pitch, splits at the middle X vertex and passes
  pixel/depth destinations and Z step to **0x45d92a**. The recovered scalar
  column loop preserves Q4 edge setup, 32-bit wrap, signed 16-bit depth comparison,
  clipping, shade byte, dirty rectangles and paired Unlock. It uses the actual
  generated depth-bank variables, not empty mapped aliases. The pre-existing
  lighting recovery remains; its arithmetic has separate original-code checks.
- `FUN_00425018`: original **0x425199..0x425204** supplies local vertex, node
  matrix, world destination and origin explicitly. Eight transformed vertices
  feed twelve temporary faces and retained reference triangles. The immutable
  three 12-entry tables at **0x47a2b8..0x47a347** are contiguous arrays; walking
  between separately allocated Ghidra scalar globals was both incorrect and an
  ASan overflow. Texture-loader ID inputs are retained, but textured raster
  qualification remains open.

Reconstructed repairs are mirrored in `GenerateRecon.js`. Only reconstructed C
changes among the four generated artifacts. No original machine code is executed
by the runtime; extracted x86 runs only in bounded comparison harnesses.

## Activation and capture policy

F5 retains the single **Ecstatica Recompiled** launch and adds
`E2R_OBJECT_MESH_IDS=537,710,711,908,909,912,980,3717`. Only those eight assets lose
their SDL diagnostic shapes in high-resolution mode. Low-resolution mode keeps
their previous fallback because its planar raster is unqualified. Unknown items, weapons, doors and other pool variants
retain theirs. Setting the list empty restores their bypass/fallback. Selection
is independent of F1/F2, original saves, scripts and population. Physical-page
selection also recognizes an object-only configuration. Replay metadata already
records this environment variable through its existing `E2R_` capture rule.

`--object-mesh-ids` exposes the same selection to motion/persistence probes.
`scripts/e2_object_render.py` retains original identities, attachment/root owners,
node dimensions/world/camera positions, pose hashes and face inputs. Selected
object checkpoints capture physical pages, indexed/HUD presentation and final
SDL output. No replacement art or animation timing is introduced.

Remote acid inspection is explicitly an **asset preview**, not gameplay traversal.
`--inspect-object-scene 350 --inspect-load-scene` invokes the original loader,
selects the original view, updates selected objects once, then runs the original
pose/static/dynamic draw and Flip tail with its background copy. During **36**
bounded normal updates, a temporary GDB return intercept holds only automatic
Joe-camera selection (`FUN_0044c224`). Joe's coordinates are never assigned.
Actions, poses, materials and rasterization execute the normal recovered paths;
the original view is restored afterward. This proves source-backed animated
pixels, not a naturally reached acid-room lifecycle or synchronized game timing.

## Fresh native evidence

All agent processes use SDL dummy, explicit time/update bounds, isolated output
and recording off. Successful gameplay routes finish actual menu Quit with
native exit **0**. Asset previews stop under GDB at their observation bound.

| Prefix under `.tmp/object-render/` | Fresh result and limits |
| --- | --- |
| `sword-debug-04` | Live scripted smith, terrain spawns deferred: workshop traversal, loose sword pickup, attached movement, Cancel/resume/Quit pass; original door boxes also enabled |
| `potion-debug-08`, `potion-asan-10` | Live potion path, pickup/drinking/removal, subsequent sword pickup, four attack directions, bottle remains removed, HUD captures and Cancel/resume/Quit pass; randomized effect outcome is observed, not forced |
| `door-debug-controlled-09`, `door-asan-controlled-09` | Explicit audited `noncombat-opening` population fixture: original door health **100→60→20→−20**, shudder/open action, state **11**, representation removal and passage pass; final beyond-door distances about **871/1,470** world units; no live-smith encounter acceptance |
| `slime-debug-08`, `slime-asan-10` | Five real pool actors, original actions **531/532/627**, changing pose/material/pixels over three later samples; source background/camera recovered; explicit asset preview policy above |
| `slime-debug-final`, `slime-asan-final` | Final exact F5 asset selection and SDL marker suppression; physical/indexed/final SDL captures at original action checkpoints |
| `save-debug-final/`, `save-asan-final/` | Final object selection, real-menu repeated same-process Save/Load and fresh-process equipment restoration; original/default/F1/F2 HUD and menu ownership checked; all four native processes exit **0** |

Persistence uses **private copies of confirmed empty slot 5**. All ten installed
save hashes and all unowned private slots remain unchanged, including slot 9.
No installed save is written. Standard human recording remains automatic/chunked.

Representative commands:

```sh
python3 scripts/e2_object_assets.py /home/rgrabowski/Games/Ecstatica2 \
  --output .tmp/object-render/assets-fresh.json
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --game-data /home/rgrabowski/Games/Ecstatica2 --player-mesh --npc-mesh --hud \
  --object-mesh-ids 537 3717 980 --suite-scenario potion-sword \
  --intro-skip-progress 83 --gameplay-menu-exit --burst-frames --timeout 240 \
  --output .tmp/object-render/potion-asan-fresh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl/e2recomp \
  --game-data /home/rgrabowski/Games/Ecstatica2 --player-mesh --npc-mesh \
  --object-mesh-ids 710 711 908 909 912 --inspect-object-scene 350 \
  --inspect-load-scene --frames 1 --sdl-events --timeout 100 \
  --output .tmp/object-render/slime-debug-fresh
```

## Verification and retained failures

Both modes pass **3,072** flat-polygon pixel/depth/rectangle/Lock comparisons
(**2,070** cases draw pixels) and **1,024** box cases/**12,288** face-input
comparisons. Flat lighting is fixed at 64/64 in the pixel fixture; separate
lighting tests pass **10,240** angles, **24,576** rotations and **8,192** indices.
Camera projection/rasterization is intercepted in the box-face fixture. Shared
character tests pass **6,144** poses, **6,144** camera origins, **8,192** projected
bases, the captured Joe-pelvis regression, **4,096** composition/selector cases and
**262,144** shade entries per mode. Both ellipsoid pixel fixtures pass **3,072**
cases; polygon routing passes **576** plus twelve stack records; attachment,
pickup and read-only SDL marker/HUD selection fixtures pass. The marker fixture
also verifies selected-object fallback removal without game-memory writes.

SDL/X11 Debug/ASan builds and independent four-artifact scratch parity pass.
The native recording fixtures pass exact chunk replay across **69 event/526
state chunks**, legacy single-file reading, corrupted/missing/order/symlink
rejection, incomplete tails and export/bundle integrity in both configurations.
The large >256 MiB variant and full gameplay suite are not rerun in this pass.

Failures remain evidence: `sword-debug-02` reproduces the lost surface selector;
`sword-debug-03` exposes the mapped/generated depth-pointer distinction;
`door-asan-05` exposes scalar-global face-table indexing. Those source contracts
are repaired and their focused checks pass. `door-asan-07` reaches all four sword
directions but Joe dies during the strike approach; it remains a failed live
journey. Initial remote-view captures only selected a camera and retained the
old physical background; those captures are not pixel acceptance. The capture
now executes the full original drawing tail and background copy. Two initial
polygon-routing fixture compiles had an outdated intercepted texture-loader
parameter type; corrected comparisons pass, with old logs retained.

Human visual review, natural acid-room entry/hazard behavior, exhaustive object
variants, low-resolution planar polygons and textured raster paths remain open.
No broad mesh-bypass removal, physics/AI/damage tuning, save-format change,
commit, push or tag action is performed. Continue with
[Task 02](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md)
before sounds and music.
