# Object variants and F3 geometry modes — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 12 Task 02](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md).
Baseline: `a2a6043`, branch `linux-e2-reconstructed-runtime`. Preserve the staged
handoff and all preceding uncommitted work. No commit, push or tag change.

## Human report and actual owners

The user reports missing dropped bottles, closed doors and smith equipment,
boxed blood, and requests F3 original/mixed/boxes modes. The read-only inspection
in `~/.ecstatica2/logs/session_20261028_134534_737` identifies the live resources
below. This corrects the first slice's coverage boundary; successful checks of
placed potion 537 and loose sword 3717 never qualified these different owners.

| Owner | Original resource and path |
| --- | --- |
| **3820/w_pot1**, **3821/w_pot2**, **3822/w_pot3** | Representation **424/w_pot**; original **1542/potapr → 1557/potglow**. Eleven authored nodes, 32 flat faces, no texture references. Pickup scripts are **1518–1520**. Actor 424 is unrelated; selection uses the actual registered actor IDs. |
| **603/korax2** | Smith **602**'s separately attached axe, rather than Joe's loose sword 3717. Seven rounded/box nodes, no stored faces or textures, scene **251/blaksmit**, camera **347**. Attachment/poses remain original. |
| **963/kdora** | Additional observed door, scene **358/cyd_dor**, camera **356**, position `(5568,4096,-7948)`, representation **28/door**, 33 box/rounded nodes and 20 flat faces. No textures. Earlier selection only covered workshop **980/kdorr**. |
| **5/BloodSpu** | Ten rounded nodes, action **1/BloodSpu**, no stored faces or textures. Original dimensions, visibility and lifetime come from the action. |
| **1085/bloodsqt** | Twenty-two rounded nodes, action **661/bloodsqt**, material/flag-controlled colour filtering through original shadow tables. The emitter's root is hidden; it is not a red replacement box or sprite. |

`scripts/e2_object_assets.py` retains the source inventory in
`.tmp/object-render/f3-variants/assets.json`. Original dispatch **0x424cbc..0x424dd8**
and rounded/box/flat leaves remain the recovered paths. Static actor flag
**+3 & 4** selects page **2**; original **0x421a14** caches its rectangle, while
**0x421f54** draws dynamic actors. The original clean camera background already
contains closed-door artwork. Do not remove that artwork, force a door into its
hit/open action, or interpret the later dynamic model as a newly invented spawn.
The pre-change closed-980 preview and per-face observations are retained. The
second actual door ID required explicit selection, not a global bypass removal.

F5 now selects exactly
`5,537,603,710,711,908,909,912,963,980,1085,3717,3820,3821,3822`.
Unselected classes and unqualified texture/planar paths retain their fallbacks.
The original acid-pool ellipsoid mapping and its natural-traversal limits remain
in the [first recovery record](object-rendering-recovery-2026-10-28.md).

## F3 presentation ownership

F3 cycles **original models with unrecovered boxes → models plus all boxes →
boxes only → original models with unrecovered boxes**. The default is the first
mode. Recovered characters retain their diagnostic geometry too. Mixed/boxes
modes enable diagnostic shapes even without a cue environment override.

The host consumes both key edges, ignores SDL repeated F3 downs, and releases
its latch on focus loss. F1/F2 still selects HUD independently. State is local to
the process and stays outside original saves, input dispatch and replay events.
The geometry choice never gates original poses, collisions, actions, mesh
rasterization or dirty/depth bookkeeping. Boxes-only presents clean camera page
**3** beneath the same HUD/diagnostic overlay. Original background artwork stays
in all modes. Modal menus retain their own pixels; physical-page exports remain
original render evidence. F3 markers keep their existing diagnostic dimensions
and lack wall occlusion.

## Fresh bounded evidence

Artifacts are isolated under `.tmp/object-render/f3-variants/`; gameplay probes
record off and use SDL dummy. The fixture is distinct from natural enemy drops.
`--object-event-preview` calls recovered original **0x42f9c0** at an existing
original guard-284 bone with the authored resource/action and independent-owner
flag. It does not assign coordinates, health, dimensions, animation progress or
completion state. Normal updates execute afterward. `--object-raster-probe`
observes entry/return pixel differences, bounded to 128 attempts per selected
owner; it never intercepts or replaces the draw operation.

- `event-debug-03` observes bottle rounded writes of **58/53/63** changed pixels
  for **3820/3821/3822**, plus **8** blood-5 pixels. Full physical/indexed/final SDL
  captures and action/pose samples retain appearance/glow and blood progression.
- `event-asan-03` observes **57/53/43** bottle pixels, **5** blood-squirt pixels and
  **10** blood-5 pixels. Both event journeys complete menu Cancel/resume/Quit
  with native exit **0** and no ASan report. Counts are individual observed draw
  calls, not total model sizes or a claim that every frame is visible.
- A progress-zero capture can consume the brief squirt's whole lifetime under
  GDB. The initial Debug event sample has **46** squirt calls with no changed
  pixels and remains insufficient pixel evidence. `blood-squirt-debug-01`
  advances normal updates before its first slow capture and observes a real
  filtered pixel. This is deliberately narrow evidence of the original path;
  complete naturally triggered blood lifetimes remain unqualified.
- `sword-debug-01` and `sword-asan-01` walk to the live smith, pick up Joe's sword,
  verify held movement, exercise F3 and complete menu Quit with native exit **0**.
  The attached smith axe remains actor **603**, with its original owner/poses.
- `door963-debug` and `door963-asan` capture the intact original door before any
  hit through explicit scene/camera asset previews. The separate closed-980
  preview and first-slice destruction/passage evidence remain distinct.
  `door980-debug` observes original flat-face writes before a hit.
  `sword-raster-asan` observes **400** changed pixels from the separately attached
  smith axe and **17** from a closed-door flat face, then exits **0**.
- Real SDL F3 checks at original, held-sword and asset checkpoints include repeat
  and focus events. All four presentations (**0/1/2/0**) preserve actor records,
  bone records, all four game pages and all three depth banks byte-for-byte.
  Returning to mode 0 restores the identical SDL frame. F1/F2 selection stays
  unchanged. The SDL fixture separately verifies restored recovered-object boxes,
  three-mode cycling and read-only/trail-free presentation in Debug and ASan.
- Protected `save-debug/` and `save-asan/`, then final
  `save-debug-menu/` and `save-asan-menu/`, each pass repeated actual-menu Save/Load
  and fresh-process equipment restoration, including HUD/F1/F2 checks. All four
  native processes exit **0**. Only private, confirmed empty slot **5** is written;
  all ten installed hashes and unowned private slots, including **9**, match.
  Final menu checks cycle real SDL F3 through all modes with pixel-identical
  requesters. The focused fixture additionally covers an active requester ID
  while its action-state word is zero; boxes-only must not select page 3 there.

The live `enemy-debug-01` attempt fails because Joe dies before the qualifying
smith kill; it remains a failed combat journey. Original spawn-event previews do
not substitute for natural drops, live combat acceptance or extended gameplay.

## Contracts and regressions

The flat pixel fixture now includes nonzero reference polygons with independent
world coordinates, as used by box faces. Debug/ASan each pass **3,072** original-x86
pixel/depth/rectangle/Lock comparisons, **2,007** drawing pixels. Existing character
pose, camera composition, shade and captured-pelvis regressions pass in both
modes. Original machine instructions execute only in bounded comparison fixtures.

All four SDL/X11 Debug/ASan builds pass. Independent scratch generation matches
all four generated artifacts. No new reconstructed C repair was needed for the
additional ID selections or host-only F3 policy; preceding C repairs remain
mirrored in `GenerateRecon.js`. Chunked recording/streaming replay fixtures pass
in both configurations, including exact chunk replay, legacy reading, malformed
chunk rejection and export integrity. This pass does not rerun the >256 MiB
variant, complete human recording or full gameplay suite.

Final `mode-debug-final` and `mode-asan-final` checks use the finished binaries
and structured probe metadata; both pass F3 cycling, unchanged game/pose/depth
bytes and identical original-frame restoration. `final-identity.json` retains
source/executable hashes, parity and protected persistence summaries.

Remaining work stays in Task 02: other items/weapons/doors, natural drop/blood
lifecycles, extended visual review and naturally reached acid-room hazards/camera
transitions. Sounds/music remain deferred. F3 comparison preserves each recovered
actor's diagnostic representation for that review.
