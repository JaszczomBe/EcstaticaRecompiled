# Recover Item, Weapon, Door and Acid-Pool Models and Animations

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: active; selected objects/effects, representation families and F3 implemented within recorded bounds
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-28

## Goal

Recover the original visible representations and animations of items, weapons,
doors and acid pools. The user selected this work after HUD recovery and the
recording repair. The next order is **object models/animations → game sounds →
music**. The first bounded slice now has original-code and Debug/ASan evidence;
remaining variants and natural acid-room gameplay are still open.

## Why This Step Exists

Player/enemy bodies and poses are recovered within their recorded bounds, and
original HUD presentation is implemented. Original actor IDs **537,710,711,908,
909,912,980,3717** now use recovered rounded, flat-polygon and box paths in F5;
other objects/equipment retain diagnostic fallbacks. The identified pools in
scene **350**, camera **116**, use flattened ellipsoids and animated rounded
bubble nodes, with actions **531/532/627**, rather than polygon water or sprites.
The [recovery journal](../../../../journal/entries/object-rendering-recovery-2026-10-28.md)
records actual resources, source contracts, original/native checks and limits.

The [human-play follow-up](../../../../journal/entries/object-variants-and-f3-2026-10-28.md)
extends selection with **5,603,963,1085,3820,3821,3822**. F3 retains all diagnostic
representations and cycles original models with unrecovered fallbacks, mixed
models/boxes, and boxes only, independently of F1/F2. The first eight-asset record
above remains historical evidence; Task 02 owns current variant acceptance.

The [animal/collectible/projectile continuation](../../../../journal/entries/animals-collectibles-and-projectiles-2026-10-28.md)
records **35 explicit owners** and **five audited collectible families/65 actor
resources**, original rat/horse actions, courtyard trap projectiles and additional
blood/hit effects. Native Debug/ASan previews qualify representative pixels and
poses; natural contact collection, combat lifetimes and acid traversal remain
separate acceptance work. F3 diagnostic representations remain available.

The [courtyard/intro/decorative record](../../../../journal/entries/courtyard-acid-flames-and-roof-effects-2026-10-28.md)
extends selection to **47 explicit owners** and **16 audited families/251 original
resources**, with complete replay of the preceding human recording and fresh
Debug/ASan pool/flame/door/lightning/roof-effect pixels. F3 mixed mode still
includes all recovered boxes. Natural hazard checks, later door destruction,
unknown decor and other unqualified paths remain open.

## Baseline and retained acceptance

Repository: `/home/rgrabowski/Work/EcstaticaRecompiled`.
Branch: `linux-e2-reconstructed-runtime`.
Observed HEAD: `a2a6043ed2def4ca6babf9cc8a6ef45587e0431b`.
HUD recovery is committed in `44ebf8f`; chunked recording/streaming replay is in
`a2a6043`. Persistence and menu/layout remain in `35be1cc` and `22c36a3`.
The worktree was clean before this documentation handoff. Recheck status and
preserve all subsequent changes. Do not commit, push or change tags unless asked.

Keep the accepted character renderers, original-default/F1/F2 HUD ownership,
menu layout, original-format Save/Load, independent diagnostics and recording
behavior. Current evidence belongs to the [HUD journal](../../../../journal/entries/original-hud-recovery-2026-10-28.md),
[recording journal](../../../../journal/entries/chunked-recording-and-streaming-replay-2026-10-28.md)
and their owning steps. Historical suite/replay success is not acceptance of
newly enabled object rendering.

## Scope

1. Identify original item, weapon, door and acid-pool resources, live owners,
   scene locations, model/material records and action/event sequences. Recover
   the actual representation for each class, including static objects where no
   animation exists. Do not invent motion or assume every class is a mesh.
2. Recover needed polygon/box/rounded/sprite or other original draw contracts,
   attachment/world transforms, projection, lighting/material/palette ownership,
   clipping, depth, dirty rectangles and page restoration from disassembly/Ghidra.
3. Verify loose and held weapons, pickup/consumption/removal, door movement or
   destruction/debris when supported, and acid-pool appearance/animation through
   the original scripts/actions. Preserve existing collision, damage and timing.
4. Replace a class's diagnostic fallback only after its actual original pixels
   are verified. Keep unrecovered classes visible; do not globally clear mesh
   bypasses or use F1/F2 to control geometry or simulation.
5. Mirror reconstructed C repairs in `E2Recomp/tools/GenerateRecon.js` and verify
   independent four-artifact parity. Keep host presentation below its boundary.

## Current tasks

[Task 01](tasks/task-01-recover-object-rendering-and-animation-contracts.md) completes
the original asset/owner map and first bounded rendering slice: explicit child
owner selection, flat columns/Lock/depth and original box vertices/face tables.
Native evidence covers potion removal and sword use, controlled door destruction
and passage, and successive original acid-pool action frames in an explicit asset
preview. Both protected Save/Load configurations pass same/fresh-process equipment
restoration with HUD/F1/F2 checks. Four builds and independent generation parity
pass. This does not qualify all variants or a naturally reached acid-room lifecycle.
[Task 02](tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md) owns
remaining object coverage and natural pool activation/hazard/camera transitions. The [selection journal](../../../../journal/entries/object-models-and-animations-handoff-2026-10-28.md)
records the priority change without claiming runtime work.

## Out Of Scope

Audio/music implementation, fabricated replacement art or animations, global
bypass removal, changed physics/AI/damage, save-format changes, arbitrary tower
stability fixes and broad portability. Fix a shared dependency narrowly when it
blocks a demonstrated original object path; retain unrelated limits.

## Usage Budget and Workflow

No explicit token or time budget is set. Use the single **Ecstatica Recompiled**
F5 launch for human investigation. Agent probes require bounded input/timeouts,
recording disabled unless testing replay explicitly, and isolated output. Use
`scripts/e2_original.py` for bounded comparisons with
`/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` and original data in the same
installation; keep assets external to the repository.

Protect installed saves. Persistence regression checks use private game/save
copies and slots freshly confirmed free; never overwrite occupied slots or
quick-save slot 9. Preserve preview cancellation and successful-Load dismissal.

## Temporary Sacrifices

Diagnostic shapes and selective bypasses remain for classes whose original draw
path is not yet qualified. Remove each fallback only with original-code and
fresh native pixel/animation evidence for that class. Do not hide missing assets
to make captures look complete.

## Acceptance Criteria

1. Each selected class has an original resource/scene/owner map and its actual
   rendering/animation contract. Static representations are identified honestly.
2. Original pixels render with correct world/attachment placement, materials,
   depth/occlusion and repainting. Success includes transitions, removal and
   camera changes without stale markers, trails, ghosting or missing equipment.
3. Native evidence covers item pickup/removal, loose/held weapon poses and use,
   applicable door states/debris, and an identified acid pool over successive
   frames. Unreached variants and unsupported branches remain explicit.
4. Characters, HUD/F1/F2, menus, Save/Load and input retain their existing behavior.
   Save/Load of affected objects restores ownership and visible state using only
   protected private copies.
5. Relevant original-code fixtures, Debug/ASan native checks, affected SDL/X11
   builds, generation parity and documentation checks pass with fresh evidence.
   Human visual review and extended gameplay remain separate acceptance claims.

## Verification

Compare recovered contracts and pixels against original instructions with
explicit register/memory/dependency ownership. Retain bounded native captures of
physical pages, composed indexed presentation and final SDL output, alongside
object identities, actions, attachments and input. Reuse relevant polygon,
pose/attachment, surface, pickup, door and persistence fixtures; extend them only
for the new contracts. Record failures as failures and split newly exposed crash
families instead of weakening replay/checkpoint or gameplay checks.

## Change Log

### 2026-10-28

1. Implemented and verified the first eight-asset slice; acid rendering is now
   mapped to original animated ellipsoids. Remaining variants/natural gameplay
   continue in Task 02; sounds/music stay deferred.
2. Parked the user-selected next recovery step ahead of sounds and music.
2. Added its first task and current committed baseline; no runtime changes made.
