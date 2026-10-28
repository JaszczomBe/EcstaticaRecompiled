# Tower sparkle, storage models and original-behavior boundary — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Human report and preservation requirement

Session **20261028_164651_876** follows the preceding
[tower progression recovery](tower-key-progression-recovery-2026-10-28.md).
The user reports a partly translucent door, flickering box around gold, difficult
key pickup, no sword hit on the key itself, and storage objects still represented
by boxes, including a gold sword. The route reaches cameras **28/19/28/155/299**.
The user subsequently clarifies that the objective is to preserve and recompile
original code, including possible original-game defects. Appearance or pickup
difficulty alone does not justify changing original behavior.

The door appearance remains unresolved. No forced opacity, changed pickup reach,
new key attack action, puzzle shortcut or asset edit was introduced. Original
data places the sword-triggered drop event on adjacent head **265**; key **264**
itself is collectible with Space. The existing bounded head/drop/pickup route is
one verified route, not proof that every original acquisition approach is easy
or that the key itself should be strikeable.

Current acceptance belongs to [Step 12 Task 03](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-03-recover-tower-key-trap-and-door-progression.md)
and [Task 02](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md).

## Protected source session and replay

The finalized source session, pinned executable and all occupied user saves were
copied to `/tmp/e2-tower-followup-20261028/source-session` and `source-saves`.
The **71-file** SHA-256 inventory is `source-sha256.json`; source copies are
read-only. The pinned executable hash is
`07d09576e2e0ba1ae851c5164ec48cde4437864774dbaa5f238bce767e198947`.
Exact pinned replay **MATCHED** sequence **1352872005**, all **1,803 checkpoints**,
with exit zero (`replay.log`). The repaired Debug executable also matches the
complete recording under strict compatible replay with its recorded render
environment (`compatible.log`). This is separate from qualifying the new model
selection; the recorded environment contains the earlier 51-owner selection.

Private runtime copies protect source/user/installed saves. A final audit matches
all 71 copied files and corresponding original session/save files against the
preserved hashes. No source session metadata or original assets were modified.

## Original asset ownership and selective rendering

The coin pile already retains requested/base representation **282** across its
collection lifecycle. The intermittent amber box belongs to a separate spawned
effect **2628/girlsprk**, observed at the actual fallback-marker call during gold
collection (`marker-spy-all.log`). It uses initially zero-size nodes animated by
the original action; a static scene preview alone does not qualify its pixels.
There is no coin-selector/cache repair and no general suppression of unknown
prop boxes.

F5 adds these six exact original owners, for **57 explicit owners** alongside the
unchanged **16 representation families/251 resources**:

| Owner | Original resource and bounded evidence |
| --- | --- |
| **2628/girlsprk** | Original collection sparkle. Natural protected tower journeys observe its animated rounded pixels in Debug/ASan, without a forced scene/event spawn. |
| **3199/nec2** | Necklace, representation **275**, scene **1479**, camera **299**. Original rounded/flat pixels in both modes. |
| **3251/golsord1** | Gold sword, 12 nodes/four stored faces, no standing representation or textures, scene **1479**. Original rounded/flat pixels in both modes. |
| **3782/gchest** | Chest, representation **420**, scene **1939**, camera **153**. Original rounded/flat pixels in both modes. |
| **1028/gastube3** | Gas representation **107**, scene **415**, camera **154**. Original rounded pixels in both modes. |
| **737/gas** | Separate original gas owner. Original rounded pixels in the gas-scene preview in both modes. |

Storage trophy **3190/tro2** was already selected by representation **277**;
blue armour door **3240/bluarmdr** was already selected by **153**. Their presence
does not warrant more generic families or a blanket bypass removal. All six
added resources have no nonnegative texture reference.

`storage-debug/-asan`, `chest-debug/-asan` and `gas-debug/-asan` retain source-scene
preview state, raster pages and logs. The first accepted primitive writes match
between modes: sword **216 rounded / 9 flat**, necklace **26 / 3**, trophy
**432 / 15**, chest **10 / 221**, gas tube **72 rounded**, gas **4 rounded**.
These isolated previews qualify rendering, not natural storage traversal,
collection, weapon use, chest opening or complete gas lifetimes.

## Narrow depth-copy reconstruction repair

Original **0x421bfa–0x421c23** in static-owner promotion explicitly supplies
depth source **1**, destination **0**, rectangle X in EBX and Y in ECX to
**0x41868c**. Decompiled `FUN_00421a14` called the old four-argument wrapper,
whose source/X were lost hidden registers. The repair calls existing
`E2R_CopyDepthRect(1,0,x,y,width,height)` and is mirrored by a narrow anchored
patch in `GenerateRecon.js`. Generated C changes only that call and its comment.

`check-e2-render-copies.py` now executes the complete original/production static
caller with raster leaves intercepted to supply a rectangle. **256 cases per
mode** compare both pages, coordinates, odd widths, depth bytes, actor bounds and
dirty rectangles. Existing **1,536** pixel-copy, **1,152** depth-copy and **256**
dirty-list cases remain passing. This proves the argument repair; it does not
establish that the human door appearance is fixed or caused by that mismatch.

`check-e2-flat-polygon-pixels.py` retains its **3,072** original triangle cases
and adds **384** thin opaque box/paired-triangle comparisons per mode. They use
fixed affine projection and fixed lighting indices. A separate bounded scratch
capture (`diagnostic-door-triangles`, `live-triangles.c` and ASan counterpart)
compares **168 actual door triangles**, including their paired reference planes,
with original **0x431a7c** instructions. All match original pixel/depth behavior;
43 calls draw with the fixture's cleared depth bank. Palette/lighting and
background depth are fixture-controlled, so this does not prove complete
original-game camera/background composition or identify an original-game bug.

Exploratory isolated depth/clip-clearing captures were diagnostic mutations in
private processes only. They do not count as gameplay or repair acceptance.
The door's original-looking composite remained visually unresolved. Do not force
its slabs opaque or alter background/flags without a differing source contract.

## Fresh native verification and limits

`spark-natural-debug` and `spark-natural-asan` pass all five protected tower
processes: locked refusal, head/drop/pickup/keyed passage, three same-process
Save/Load stages and three fresh-process loads, original owner pixels, independent
F3/HUD modes, real menus and clean Quit. The watcher now includes **2628** and
observes its natural animated pixels. Only private probe-owned slot **5** is
written. Debug executable SHA-256:
`33c4ce05ad0722a60e3b748a52b502f06069f7b638c1af44ad862ebab02b6d2e`;
ASan: `46b4c2860be4dc9c3d0fda84bf9b08988e849a8b7e0237f953b43e09f9d9251d`.

All SDL/X11 Debug/ASan builds pass. Normal/ASan flat/rounded raster comparisons
and expanded copy comparisons pass. Independent four-artifact generation parity,
suite runner contracts, documentation-tree update/check and whitespace checks
complete repository verification. Fresh `debug-recording` and `asan-recording`
use the final 57-owner/16-family selection, character meshes, inspection and
**8 KiB** chunks; each passes five independent replay variants. These are bounded
recording regressions, not new recorded natural storage playthroughs.

Human review of the sparkle/storage changes, complete original-game door
composition, difficult pickup alternatives, unarmed head hits, broader tower
death/retry paths and natural acid lifecycle remain unqualified. No original
defect is declared proven or cosmetically corrected. No commit or push occurred;
pre-existing staged/unstaged work is preserved.
