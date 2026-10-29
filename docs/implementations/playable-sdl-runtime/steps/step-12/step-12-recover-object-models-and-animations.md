# Recover Item, Weapon, Door and Acid-Pool Models and Animations

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: active continuation in Task 05; object behavior/rendering/interactions across Save/Load playthrough sessions
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-29

## Goal

Recover remaining original object behavior, visible representations, animations
and interactions. After the `v0.3.0` sound/music milestone, the user selected
[Task 05](tasks/task-05-recover-object-behavior-rendering-and-interactions.md) as the next priority: anti-acid boots, ladder usage and
other remaining object paths, with stability checks and a playthrough over several
Save/Load sessions. The earlier sequence was object models → sounds → music;
those bounded recoveries retain their recorded acceptance. No new boots/ladder
fault, behavior repair or complete playthrough is established by this handoff.

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

Current continuation baseline: `v0.3.0` at `38d79da2276c2baef8e0fceec46f0f7557cb8192`.
The worktree was clean before the new documentation handoff. Task 05 and its
[handoff journal](../../../../journal/entries/object-behavior-and-interactions-handoff-2026-10-29.md)
own current session/save continuity. The first-slice coordinates below are
historical; re-check HEAD/status and current save occupancy before investigation.
The [first supplied session](../../../../journal/entries/garden-teleport-and-boots-session-2026-10-29.md)
now adds five original F5 owners (81 total), qualifies natural Debug/ASan garden
teleport/glow and preserves the spent boots checkpoint and old-save zero-power
fault. Final 81-owner Debug/ASan protected persistence and strict audio/music
replay pass; fresh boots, ladders and wider playthrough remain open.

The [save-state integrity correction](../../../../journal/entries/invalid-court-save-retirement-and-persistence-audit-2026-10-29.md)
retires the invalid COURT/power150 recovery, descendant checkpoints, private
runners and F5 profile override. Malformed or patched saves **MUST NOT** support
game-function reconstruction or progression acceptance. Save/Load now also
preserves live difficulty/poison duration, with Debug/ASan real-menu checks
from fresh gameplay and untouched g3. The original-backed ladder Space repair
remains; its COURT150-derived traversal/persistence claims are withdrawn.
Requalify both ladder directions from valid progression; see Task05.

The [preceding stables spider session](../../../../journal/entries/stables-spider-and-zero-power-save-2026-10-29.md)
exactly reproduces all 915 available checkpoints, then the same original
zero-power division after another Load of unchanged runtime **7/COURT**.
Debug/ASan original/native arithmetic comparisons include damage 2 and pass;
the save and behavior remain unchanged. Continue from validated g3 or fresh play.

The [preceding courtyard investigation](../../../../journal/entries/courtyard-boxes-and-zero-power-crash-2026-10-29.md)
adds nine further original owners (90 total), records the exact runtime-7
zero-power crash and a passing original arithmetic comparison, and retains the
intervening healthy g3 session. Final 90-owner Debug/ASan protected persistence,
HUD/F3/inventory and six strict audio/music replay variants per configuration
pass. No save normalization or damage guard is added; fresh interactions,
full visual review and extended play remain open.

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
6. Recover original item/equipment behavior and environmental interactions,
   including hazard protection and ladder traversal where supported; verify
   original state/eligibility and Save/Load contracts through natural play.
7. Maintain session/save/checkpoint continuity and additional Debug/ASan stability
   checks around each recovered path; Task 05 owns the ongoing playthrough.

## Current tasks

[Task 05: Object Behavior, Rendering and Interactions](tasks/task-05-recover-object-behavior-rendering-and-interactions.md) now
coordinates the next work across human Save/Load sessions, with anti-acid boots
and ladder usage as initial examples. Preserve matching source saves, pinned
session builds and explicit route/checkpoint links. Source-backed stability fixes
and same/fresh-process persistence checks accompany each newly recovered path.
The [selection handoff](../../../../journal/entries/object-behavior-and-interactions-handoff-2026-10-29.md)
records this documentation-only priority change after sound/music recovery.

[Task 04](tasks/task-04-recover-inner-castle-progression-crash-and-models.md) retains
bounded acceptance after original-backed event/node and signed-clipping repairs. The
[recovery evidence](../../../../journal/entries/inner-castle-crash-and-presentation-recovery-2026-10-28.md)
records pinned crash reproduction, all **3,190** recovered-prefix checkpoints,
original x86 comparisons and **76** selected owners covering the reported paths.
Fresh Debug/ASan mace pickup/persistence and stairwell survival pass; bounded
post-event control/combat and persistence also pass. Uninterrupted human-route
reproduction, equipped-armour human review and complete gate/effect composition
remain open. The source recording remains incomplete. Protect occupied slots
**5/123, 6, 7 and 9**; persistence uses a separately isolated private game tree.

[Task 03](tasks/task-03-recover-tower-key-trap-and-door-progression.md) now has
bounded Debug/ASan acceptance for the loaded tower puzzle. The [recovery journal](../../../../journal/entries/tower-key-progression-recovery-2026-10-28.md)
records original head-hit/key-drop, Space pickup, locked-door refusal, keyed-door
passage, blocker tracks and same/fresh-process persistence at three stages.
The missing model selection obscured the existing mechanism. F5 now includes
owners **259/264/265/266**. The [tower/storage follow-up](../../../../journal/entries/tower-storage-render-followup-2026-10-28.md)
adds collection sparkle, storage necklace/gold sword and nearby gas/chest models,
for **57 explicit owners** plus the existing 16 representation families. Original
pixels, F3, HUD/menu/save preservation and recording checks pass. The reported
partly translucent door remains unresolved; preserve original behavior, including
possible original defects, unless a reconstruction mismatch is proven. Full
original-game composition and broader tower coverage remain unqualified.

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

Source-backed repairs required by Task 03's progression and Task 04's demonstrated
inner-castle crash are in scope. Earlier exclusions of arbitrary tower work refer
to unrelated stability/physics changes, not these explicitly requested paths.

## Out Of Scope

Unrelated audio/music expansion, fabricated replacement art or animations, global
bypass removal, speculative physics/AI/damage changes, save-format changes,
arbitrary stability fixes and broad portability. Fix a shared dependency narrowly when it
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

### 2026-10-29

1. Selected Task 05 after `v0.3.0`: remaining object behavior, rendering and
   interactions with stability checks and multi-session Save/Load playthrough.
2. Added continuation and protection rules; no new runtime acceptance claimed.

### 2026-10-28

1. Implemented and verified the first eight-asset slice; acid rendering is now
   mapped to original animated ellipsoids. Remaining variants/natural gameplay
   continue in Task 02; sounds/music stay deferred.
2. Parked the user-selected next recovery step ahead of sounds and music.
2. Added its first task and current committed baseline; no runtime changes made.
