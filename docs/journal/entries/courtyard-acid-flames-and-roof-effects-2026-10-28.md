# Courtyard acid, flames and roof effects — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 12 Task 02](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md).
Baseline **a2a6043**, branch **linux-e2-reconstructed-runtime**. Preserve staged
handoff documents and preceding uncommitted recovery. No commit, push or tag change.

## Human recording and replay boundary

Session **20261028_151455_581** reports an invisible pedestal lightning effect,
smith potion boxes, missing animated torches/fireplace, two boxed courtyard acid
paths, roof pickup boxes, and red/blue doors. Original resource inventory,
observations and bounded probes are in `.tmp/object-render/courtyard-acid/`.

`replay-native` runs the session's **pinned executable**, hash
`d22733b03f3a0b83dcaef40b27750ed3805db66009024d230b4e867c869733b5`,
with its recorded startup environment and private output. It completes with
native exit **0**, sequence **3204241550**, last matching checkpoint **2492**.
The user naturally reaches cameras **124/125/91/163/161/132** after the workshop.
This is complete replay evidence for that pinned configuration, not a replay
qualification of a changed renderer.

The retained human gameplay frame **331** explicitly says **F3: MODELS + BOXES**.
Recovered potions and coins intentionally retain diagnostic geometry in that
mode. Their boxes alone do not establish missing models. Other boxes identify
genuinely omitted owners, including a separate shelf, additional pool styles and
roof effects. Original F3 mode suppresses the qualified owners; mixed and boxes
modes preserve them as requested. Unknown objects still have fallbacks.

Replay preserves strict environment and event checking. Initial attempts to
override SDL to dummy, including compatible mode, correctly reject the extra
startup environment. The successful pinned replay uses the recorded environment.
Two explicitly labelled private render-policy variants keep original event/state
streams but change only copied metadata for the new selection (one also changes
the driver). Both diverge at checkpoint **17**, expected `cursor_get`, actual
`clock`, sequence **13239093**, after the intro handoff. Neither is accepted.
`render-variant-audit.json` retains changes/hashes and verifies every original
recording file remains identical. Do not relax replay checks to absorb a changed
render-call/pump sequence. New captures with the actual final selection have
separate passing replay evidence below.

## Original owners and methods

| Report / owner | Source-backed representation and contract |
| --- | --- |
| Pedestal sky effect **3551/joespl** | Scene **0**, camera **175**, 40 authored rounded nodes initially sized zero. Original scene records around archive **0x28ce** place it at `(8960,1276,-17408)` and begin node growth at scene frame **533**: node **108** gets dimensions `(4,4,112)` plus authored transforms, followed by other segments. It is thin rounded geometry controlled by the scene, not a texture/sprite or a fabricated lightning graphic. It has no standing action. |
| First courtyard acid path | **944/slim4e**, **946/slim1b**, **3248/slim4**, scene **352**, authored camera **137**, seen naturally from **124**. Representations **126/slime3**, **102/slime**, actions **627/slimglo3**, **532/slimeglo**. Six flattened rounded nodes per resource. |
| Second courtyard acid path | **1089/slm4g**, **1090/slm4h**, **1091/slm4i**, **1095/slm4k**, **1096/slm4l**, **1097/slm4m**, scenes **443/444**, authored camera **162**, seen from **132**. Representations **135/slm6**, **133/slim4**, **134/slm5**, **103/slime2**; actions **664/662/663/531**. Four to seven rounded nodes. |
| Small torch/flame **413/flame1** | Representation **66/flame1**, action **381/flame**, scene **158**, camera **149**. Seven rounded nodes. |
| Large flame / fireplace style | Representation **86/bigfire**, action **435/bigfire**, seven authored resources including **564–567/570/571** on the recorded route. Five rounded nodes per resource, including zero-Z planes such as `(52,115,0)`. Original animated ellipsoid geometry supplies the flames; no replacement fire image or invented timing. |
| Smith shelf **536/kshelf3** | Separate from potion **537**: scene **225**, camera **352**, 14 rounded/box nodes, static source geometry. Potion **537** already has original glow **384**; selection now also covers its whole **67/potion** family. |
| Well-side bottle **3986/welbotl** | Scene **2059**, camera **125**, 14 nodes and 30 flat faces, no standing representation. A distinct resource from 537 and dropped bottles **3820–3822**. |
| Red and blue doors | Both use **153/reddoor**, despite the name. **42** authored variants, 37/41 nodes with 8/20 flat faces. Observed **2072/redor** and **2127/redor14**, plus blue **2713/bludor1**, provide samples. Source hit slots name **945/Reddorshuuder**. This restores their appearance while retaining original progression, locking, collision and damage; later bashing/destruction is not newly accepted here. |
| Roof collectibles / other items | Coin **282** was already selected; **3734–3736** retain original **1197/coinsparkle**. Additional **3737/klstab2** is a static eight-node wand, not a coin; chalice family **287/chal1** uses **1204/chalturn1**, sampled at **3919/stabchal**. |
| Separate boxed roof effects | **3994–4001/fuzbom25–32**, scenes **2064/2065**, cameras **491/492**. Twenty rounded nodes each, original actions **1628–1635**, initial root dimensions such as `(94,81,98)`. These account for separate boxes in the roof view; no automatic collection/inventory contract is inferred from their gold-like appearance. |

Both pool groups use the already recovered flattened-ellipsoid/rounded-bubble
path. Source root samples include `(195,16,182)`, `(122,10,114)` and `(42,10,54)`
with flags **0x2042**. They have **no stored polygon faces or texture references**.
All retain original callback **236/ken:slimhit**. They are not water polygons,
sprites or assumed meshes. The earlier camera-116 five-pool preview did not
cover these owners; the user did not reach camera 116 in this recording.

The smith's **1189/sparks** is also mapped more precisely: scene **251** contains
original events at frames **31/107** spawning **1188/action 754** from node **140**.
It is not an unproven new standing animation. Its own pixels were not qualified,
so **1189 keeps its fallback**; already qualified 1188 remains selected.

## Selection and observation changes

F5 selects **47 explicit IDs**, listed in the [build guide](../../building.md), plus
representations **66,67,86,102,103,126,133,134,135,153,271,277,279,282,287,349**.
The read-only inventory finds **251 authored resources** across these 16 families:

- Potion **67**: 79; small flame **66**: 1; large flame **86**: 7.
- Stationary pools **102/103/126/133/134/135**: **11/9/8/1/6/1**, total **36**.
- Red/blue doors **153**: 42; chalices **287**: 21.
- Earlier gem/trophy/crown/coin/blue-gem families: 65.

Including explicit IDs and overlaps, **292 distinct selected resources** have
no nonnegative texture reference. `inventory-final.json` retains source hashes,
node/material/texture/face records, actions, callbacks and scene locations.
Unverified decor and textured/planar paths keep fallbacks. Low-resolution mode
retains its previous fallback. F3 boxes remain independent of the selection.

No new reconstructed-C repair was required. Existing native root/representation
selection and owner **+0x22** bypass resolution already admit these original
paths. Preceding C repairs remain mirrored in `GenerateRecon.js`; scratch parity
still matches C, header, globals and names without unrelated churn.

Raster observation now starts before the intro, not just after Joe's release.
Authored zero-size dormant nodes no longer consume the bounded pixel-observation
budget. The original draw still executes; this only changes what GDB samples.
The observer retains early attempt inputs, simulation time/camera, requested/base
representation IDs and separate per-kind before/after images. An initial
128-attempt zero-size sample did not prove missing lightning; subsequent captures
observe actual grown segments. No game progress, coordinates, dimensions, health,
visibility or completion fields are assigned by the observer.

## Fresh bounded evidence

Asset probes use SDL dummy, recording off and isolated runtime storage. Remote
scene previews explicitly load/select an authored camera and run original updates
and render leaves, with a bounded camera hold; these are distinct from natural
traversal. Counts below are single successful draw calls, not complete model sizes.

- `lightning-debug-02` / `lightning-asan`: original node **108** writes **28/29**
  pixels near the top of camera 175. Source-driven dimensions are `(4,4,121)` /
  `(4,4,130)` at capture; the first successful samples follow the authored growth.
- `acid-a-debug` / `acid-a-asan`: **944=391**, **946=526**, **3248=480** rounded
  pixels in both. Four distinct sampled source poses per pool, actions **627/532**.
- `acid-b-debug` / `acid-b-asan`: **1089=774**, **1090=429**, **1091=1055**,
  **1095=63**, **1096=58**, **1097=742** rounded pixels in both. Three/four sampled
  poses each, with original **664/662/663/531** progression/restarts.
- `torch-debug` / `torch-asan`: **413=24** pixels in both, four flame poses.
  `fire-debug` sees **564=4** pixels and four source poses; ASan pool/roof previews
  independently observe large-flame **571/564** writes. Other captures also show
  **565/566/567** through the same qualified large-flame family.
- `shelf-debug` / `shelf-asan`: **536** flat/rounded writes **62/277**, potion
  **537** rounded/flat **78/1** in both. Source captures show the shelf/bottles.
  `well-bottle-debug` observes **3986** rounded/flat **35/1**, while ASan shelf
  sampling also sees its rounded path.
- `acid-b-debug` / `acid-b-asan`: red **2072** flat/rounded **7/2**.
  `blue-door-asan` and `roof-effects-debug`: blue **2713** flat/rounded **2/2**,
  red **2127** flat/rounded **14/2**. Original coloured geometry is visible.
- `chalice-debug` / `chalice-asan`: **3919=19** rounded pixels and original
  **1204** progression, three/four poses. `roof-debug` / `roof-asan`: static wand
  **3737=45** pixels and trophy **3738** rounded/flat **40/4** in both.
- `roof-effects-debug`: **3998/3999/4000/4001=71/102/121/124** rounded pixels;
  `roof-effects-asan`: **3994/3995/3996/3997=296/106/298/79**. Each has four sampled
  source poses and its own **1628–1635** action, rather than a substituted coin.
- Native F3 **0/1/2/0**, repeat/focus and F1/F2 independence checks pass at asset
  checkpoints: actors, nodes, four game pages and three depth banks are unchanged
  byte-for-byte. Original presentation restores identically. Debug/ASan marker
  fixtures also pass read-only selection, projection and menu/page guards.
- Final `save-roofs-debug` / `save-roofs-asan`: repeated real-menu Save/Load,
  fresh-process restore, HUD/F1/F2 and menu F3 pass using the final selection.
  Private confirmed-empty slot **5** only; all **ten installed saves** and **nine
  unowned private slots** remain identical. The earlier Debug equipped round trip
  passes; the separate ASan equipped attempt fails its following-movement check
  and is not promoted by the passing unarmed persistence checks.
- `recording-roofs-debug` / `recording-roofs-asan`: new bounded captures with
  final models, active population, released-player input, inspection and **64 KiB**
  test chunk rotation pass five independent replays each: three ordinary runs,
  inspection disabled, and a debugger pause. Native exits are all **0**. Normal
  F5 automatic recording still uses its existing **16 MiB** chunks. The replay
  test now accepts explicit model selections so this evidence is reproducible.
- Debug/ASan native replay integrity, chunk rotation/corruption/interrupted-tail/
  export contracts pass. Four SDL/X11 builds, independent four-artifact generation
  parity and documentation-tree checks pass. No new large-volume claim is made.

## Retained failures and remaining work

Direct smith scene-251 previews do not activate a source child from the remote
pedestal position. Legacy live sword approaches miss waypoint 1 while Joe is
alive; newer explicitly noncombat routes stop on movement-discontinuity checks.
The ASan equipped persistence approach reaches pickup but fails movement after
Space release. These are preserved failures, without a speculative gameplay or
navigation change. Successful pixel previews, unarmed Save/Load or a new replay
do not turn those routes into accepted smith/combat journeys.

The two visited courtyard pool groups now have original geometry/action evidence.
Natural hazard/contact damage, complete pool/effect lifetimes and camera-116
traversal remain open, as do future coloured-door destruction, unknown decorative
owners, unsupported rendering and new human visual acceptance. Keep source-owned
gameplay, characters, original HUD/F1/F2, menus, protected saves and F3 fallbacks.
Object recovery still precedes sounds and music.
