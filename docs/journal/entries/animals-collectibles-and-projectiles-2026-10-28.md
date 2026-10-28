# Animals, collectibles and courtyard projectiles — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 12 Task 02](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md).
Baseline `a2a6043`, branch `linux-e2-reconstructed-runtime`. Preserve the staged
handoff and preceding uncommitted recovery. No commit, push or tag change.

## Human evidence and original mapping

The next human playthrough reports a boxed mouse, green boxes near killed
enemies, invisible automatic collectibles and stable horse, and boxed courtyard
bombs. Read-only inspection of sessions **20261028_141403_633** and
**20261028_143811_094** identifies the owners below. Earlier fifteen-ID evidence
never covered these resources. Source inventory and bounded artifacts are under
`.tmp/object-render/more-variants/`.

| Report | Original owners and geometry/actions |
| --- | --- |
| Mouse at the blacksmith | **601/krat**, **608/krat2**, representation **89/ratty**, scene **255**, camera **350**. Fourteen rounded nodes, no stored polygons or textures. **466/walkrat**, **467/468** turns, **469–471** stops. |
| Stable horse | **663/khorse**, representation **96/horse1**, scene **271**, camera **177**, original position `(-2496,4096,-5568)`. Fifty-one nodes and four flat faces, no textures. Original walk **490** and standing actions **500/501** are observed; the resource also names turns, trot and rearing, which are not exhaustively qualified. |
| Courtyard bombs | Original stone-ball/statue trap assets: **1100/1101**, **1122–1125**, **1127–1131**, **1190–1193**. Scene pairs **445–460 / 513–517**, cameras **132/419/420/127/128/124**. Rounded stone-ball geometry has 10–14 nodes; statue owners have 57. Representation **130/statball** names **645/explode**. No textures. These are not an invented bomb mesh or sprite. |
| Green props around combat | Additional blood owner **1153/blodsqt1**, 22 rounded nodes; armour-hit owner **1188/armrhit**, 37 rounded nodes. Original action **340/Gobhitfron** contains spawn words `(46,88,8,1153,694,12,0,12288)` at archive **0x937bdc**. **568/statgethit2** contains `(46,1,8,1188,754,12,0,16640)` at **0x9a1852**. Correct actions are **694/blodsqt1** and **754/armrhit**, rather than reusing blood-1085's action 661. |

The final human frame also labels separate green **PROP 1128/1129** and hit
effect **1188** near the workshop. Actual dead-enemy samples retain flag
**0x1000**: actors **284/293** have **0x1c40**, and **602** has **0x1c49**.
They still classify as creatures/corpses after representation removal. Blood
**1153** has **0x2c68** and classifies as a separate prop. The fixture retains
these samples. This supports recovering omitted effects/traps, not changing
corpse classification or hiding all green props. Complete corpse/combat visual
acceptance still needs a natural combat journey. Separate **1189/sparks** retains
its fallback because its source action path was not qualified.

## Collectible families and selective bypass

`e2_object_assets.py --representations` inventories every original actor whose
authored record **55** names a selected representation, including scene links,
standing actions, primitive records and nonnegative texture IDs. The source audit
finds **65** resources in these five families, with **no texture references**:

| Representation | Original resources | Representative standing action |
| --- | ---: | --- |
| **271/gem** | 6 | **2671**, **1449/rgem** |
| **277/trophy** | 10 | **2703**, **1181/trophyturn** |
| **279/crown** | 4 | **2708**, **1187/crownturn** |
| **282/coins** | 28 | **2709**, **1197/coinsparkle** |
| **349/blugem** | 17 | **2718**, **1350/blugemglo** |

Placed human-route samples include coins **3734–3736/3739/3742**, trophy **3738**,
and ruby **3920** with coin **3918**. Coin scene **1918**, camera **1090**, and
ruby scene **2020**, camera **345**, provide separate placed-asset previews.
The gems include flat faces and rounded glow nodes; the crown includes flat
geometry. Qualification therefore observes both primitive kinds rather than
stopping after a rounded glow writes a pixel.

F5 now selects **35 explicit owner IDs**, listed in the [build guide](../../building.md),
plus `E2R_OBJECT_MESH_REPS=271,277,279,282,349`. The native read-only selector
requires a registered original root, then matches its requested **+0x122** or
saved standing **+0x124** representation. Original **0x426227..0x426231** copies
the former to the latter. This retains the qualified render path across action
changes without treating bone IDs, animation IDs or pointers as actor IDs.
Family-only configuration also enables physical-page presentation. Original
collection, inventory, disappearance and collision logic are unchanged.

The reconstructed bypass already consults this native helper for both root and
node **+0x22** owners. No additional reconstructed C change was needed here;
preceding repairs remain mirrored in `GenerateRecon.js`. Unknown objects and
unqualified textured/planar paths keep fallbacks. All recovered models retain
their diagnostic geometry in F3 mixed/boxes modes; F1/F2 remains independent.

## Fresh bounded evidence

All gameplay probes below use SDL dummy, recording off and private runtime
storage. Scene previews explicitly select/load an original camera and hold it
for normal original updates; event previews invoke original **0x42f9c0** at an
existing guard-284 bone with the source resource/action IDs. Neither fixture
assigns actor coordinates, health, dimensions or animation progress. These are
asset previews, not natural traversal, drops or collection acceptance.

- `rats-debug` / `rats-asan`: original **601/608** rounded calls change
  **79/71** pixels in both builds. Four distinct sampled node poses per rat and
  original walking/turning/stopping actions are observed.
- `horse-debug` / `horse-asan`: original **663** rounded call changes **792**
  pixels in both; four sampled poses with actions **490/500/501**. The later
  `horse-flat-debug` capture separately records a **17**-pixel flat-face write
  as well as the rounded body. Physical/indexed/final SDL captures show the horse.
- `coins-debug` observes placed **3734/3735/3736** rounded writes of **1/3/9**
  pixels. `ruby-debug` observes rounded writes for **3920/3918** of **98/8**.
  These are individual successful draw calls, not total model sizes.
- `bomb-debug` / `bomb-asan`: rounded writes **1127=86**, **1128=96**,
  **1129=33** in both builds. Crown **3913** also writes **15** flat pixels;
  the later per-kind watcher records its rounded glow separately.
- `events-debug` / `events-asan`: all five collectible representatives write
  original pixels through family selection, without their actor IDs in the
  explicit list. Red gem rounded/flat writes are **46/17** and **46/12**;
  trophy **59/3** and **53/2**; crown flat/rounded **35/17** and **33/16**;
  coins rounded **8** and **6**; blue gem rounded/flat **64/18** and **51/1**.
  Glow/turn actions progress normally; coin sparkle progress changes even though
  sampled local bone poses remain constant. Blood **1153** writes **1/10**
  filtered pixels and armour-hit **1188** writes **2/2**. Both event journeys
  complete menu Cancel/resume/Quit with native exit **0**, without an ASan report.
- Real SDL **0/1/2/0** F3 cycling at eight checkpoints in each event journey,
  plus animal/projectile scene checks, preserves every sampled actor/bone record,
  all four game pages and all three depth banks byte-for-byte. Repeat/focus
  events and F1/F2 independence pass; original presentation restores identically.
- `marker-final-debug` / `marker-final-asan` pass read-only projection,
  exact/family selection, requested/base representation transitions, negative
  selection, family fallback suppression, F3, menu/page guards and captured
  corpse-flag classification. These use synthetic actors, not gameplay placement.
- `save-debug` / `save-asan` pass repeated real-menu Save/Load plus a fresh
  process restore, HUD and menu geometry switching using the final selection.
  Private slot **5** only; all **ten installed saves** and **nine unowned private
  slots** hash identically before/after. Each save is **232725 bytes**.
- Original-x86 shade, forward-pose, camera-origin, ellipsoid basis and projection/
  draw-selector fixtures pass normally and under ASan. SDL/X11 Debug/ASan builds
  pass. Independent scratch generation matches **C/header/globals/names** with
  zero mismatches. Native replay parser/integrity and chunk rotation/corruption/
  interrupted-tail/export contracts pass in both builds; no new large-volume
  recording acceptance is inferred from these bounded checks.

## Remaining acceptance

This fixes the identified owner/family omissions within the recorded bounds.
It does not establish every world instance or animation, naturally reached
automatic pickup/removal, complete blood/hit lifetimes, every trap trajectory or
new human visual acceptance. Earlier live combat failures remain failures.
Natural acid-room traversal, pool lifecycle/hazard checks, other unknown assets
and unsupported texture/planar paths remain in Task 02. Original object recovery
still precedes sounds and music.
