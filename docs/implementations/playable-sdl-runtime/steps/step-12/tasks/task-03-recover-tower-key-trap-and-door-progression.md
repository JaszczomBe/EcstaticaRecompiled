# Recover Tower Key, Spike Trap and Door Progression

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Item, Weapon, Door and Acid-Pool Models and Animations](../step-12-recover-object-models-and-animations.md)
<!-- /docs-tree:parent -->

Status: bounded progression/persistence accepted; human door appearance report remains unresolved
Parent Step: [Object models and animations](../step-12-recover-object-models-and-animations.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-28

## Goal and priority

The next-context priority is now [Task 04](task-04-recover-inner-castle-progression-crash-and-models.md),
covering the later inner-castle crash and missing presentation. This task retains
the earlier bounded progression/persistence evidence and unresolved door limits.

Restore the original tower-top key/trap/door interaction so the player can obtain
the key and continue through its door. The user loaded a saved tower state and
reports that the key cannot be taken and the key, spike trap and keyed door lack
models. This blocks progression. Investigate interaction and rendering together;
enabling a model alone does not resolve an uncollectable key.

This task was prioritized over additional decorative coverage, the remaining
[Task 02](task-02-qualify-object-variants-and-natural-acid-lifecycle.md) acid work,
sounds and music. The following investigation is now complete within the bounds
below. Preserve existing work and do not commit, push or change tags unless
separately instructed.

## Human follow-up and preservation boundary

Session **20261028_164651_876** reaches the keyed doorway and storage, but the
user reports a partly translucent door, intermittent gold box, difficult key
pickup and additional storage boxes. The [follow-up journal](../../../../../journal/entries/tower-storage-render-followup-2026-10-28.md)
records its exact **1,803-checkpoint** replay, source comparisons and fresh checks.
The user explicitly clarified that preserving original code behavior includes
possible original-game defects. Do not force opacity, change pickup reach or
make the key itself a sword target without proving a reconstruction mismatch.

The intermittent gold box belongs to spawned **2628/girlsprk**, not the coin
pile. F5 now includes that original effect and original storage/nearby owners
**737,1028,3199,3251,3782**: **57 explicit owners** with the existing 16 families.
Debug/ASan tower journeys observe natural sparkle pixels; storage previews
qualify the gold sword and necklace alongside the already selected trophy.
Preview evidence does not establish their natural collection/combat lifecycle.

The sole C repair restores original **0x421bfa–0x421c23** depth-copy source,
destination and X/Y arguments in static-owner promotion; its generator mirror
and **256** original-x86 caller cases pass in both modes. It does **not** resolve
or establish the cause of the door appearance. **384** integrated opaque-box
cases and **168** captured door-triangle comparisons match original x86 per
mode. Full original-game composition remains unverified; retain the observed
appearance until a differing reconstructed contract is demonstrated. The key
is collectible; the adjacent head owns the original sword-triggered drop scene.

## Accepted recovery — 2026-10-28

The [recovery journal](../../../../../journal/entries/tower-key-progression-recovery-2026-10-28.md)
records the original mechanism and fresh evidence. The pinned attempt replays
exactly through all **964 checkpoints** with private runtime saves. Its selected
slot is **6/DFGSDRG**. On a fresh Load, ordinary Ctrl/Up attack against head
**265** runs action **334** and script **135/dav:keyhd3**, starting scene **83**.
That scene lowers key **264** to `(-18292,-3328,-1088)`. Space acquires it in
Joe's node **7**. Approaching door **266** while holding the key starts scene
**68**, transfers the key to door node **8**, moves blocker **443** from
Y **-3328** to **-4032**, and permits actual passage past X **-19550**.
An unsuccessful approach while holding the sword leaves the door locked.

No gameplay or Save/Load fault was proven. The implementation adds original
render selection for owners **259/264/265/266** to F5; reconstructed C and
`GenerateRecon.js` remain unchanged. Both SDL Debug/ASan qualify all four owners'
original pixel writes, head/drop/pickup/door stages, three same-process and three
independent fresh-process persistence stages, control, F3, HUD/F1/F2, menus and
clean Quit. Private slot **5** alone is written; source/user/installed saves and
all unowned private slots are hash-verified unchanged. The original key height,
trap timing, damage, conditions and blocker track remain authored behavior.

`scripts/check-e2-tower-conditions.py` compares **2,720** original-x86 condition
cases per mode and is registered as `Original.TowerConditions` in the suite.
`scripts/probe-e2-tower-progression.py` reproduces the native journey from an
explicit supplied save set; usage is in [gameplay tests](../../../../../gameplay-tests.md#tower-key-progression).
Four builds, independent four-artifact parity, relevant original fixtures and
separate chunked recording/replay checks pass. Human F5 visual review, other
loaded tower saves, unarmed head hits and wider tower/death/retry journeys remain
unqualified. The original reported attempt reaches the death scene; it is not a
successful pickup route. Remaining variants/acid work stays in Task 02.

## Start from this evidence

Read the [tower handoff journal](../../../../../journal/entries/tower-key-progression-handoff-2026-10-28.md),
then session **20261028_161516_514** under `~/.ecstatica2/logs/`. It loads into
camera **28**; the runtime log records `action.load_complete`. Its pinned Debug
executable hash is
`d4af20e324efe494a22c8efb69fce69faf5b95efb0d183cf4dd7206e5e5c8a00`.
Manifest revision and current HEAD are **990bdd9ea080ccdf434f626d4d20bf440f12a422**
on `linux-e2-reconstructed-runtime`. The worktree was clean before this handoff.
The manifest marks recording/inspection complete and OS exit 0; no replay or
functional acceptance has been performed for this tower attempt.

Observed and original-resource identities:

| Owner | Original resource / scene clues |
| --- | --- |
| **264/key3** | Six rounded/box nodes, no stored faces, textures or standing representation. Scenes **83/key3**, **84/key3_st**, **68/h_doropn**, camera **28**. Live position `(-18432,-3776,-620)`, flags **0x0c28**, state **0**, no action/representation; remains unchanged across the post-load observations. |
| **259/pike** | Two nodes, eight flat faces, no textures; representation **53/pikerep**, action **336/pike_srk**. Scenes **65/hdeth1**, **83**, **84**, **2004/hdeth2**, camera **28**. This is the spike/trap owner to trace, not an assumed new trap mesh. |
| **265/keyhed3** | Nineteen nodes, no stored faces/textures; representation **52/keyhd3**, action **334/keyhd3** in hit slots. Scenes **83/84**, camera **28**. Recover its role in the key mechanism instead of assuming actor 264 alone owns the interaction. |
| **266/door3** | Twenty nodes, no stored faces/textures or standing representation. Scenes **68/h_doropn**, **86/h_doors1**, camera **28**; live `(-19456,-3392,-1556)`. |
| **443/blocker1** | One node; linked with door 266 in scenes **68/86**; live `(-19456,-3328,-1792)`. Recover original blocker removal/retention with door progression. Do not disable it to permit passage. |

Original FAN names identify scripts **10/Key3**, **64/key3_st**,
**65/h_doropn**, **136/dav:key3_st**, **138/dav:h_doropn**. They are starting
points, not recovered interaction contracts. Actor callback records alone are
empty for these resources; inspect scene/global script ownership too.

At snapshot **33** after Load, Joe is `(-18881,-3328,-1032)`, health **69**;
at the final snapshot **160**, Joe is `(-18304,-3328,-2160)`, health **74**,
scene **65**, while the key remains unchanged. Trace trap/death-scene transitions
without assuming that positive health proves control or interaction completion.
The key's height is authored in the original resource; do not lower it speculatively.

## Required investigation and repair

1. Freeze the finalized session/pinned binary and required saves into private
   test storage. The session starts by loading existing progress: copy runtime
   saves as read-only source fixtures before replaying. Identify the selected slot
   from evidence; it is not established by this handoff. Do not replay against
   writable user storage or rely only on installed-save fallbacks.
2. Reproduce the reported attempt from that Load with bounded ordinary input.
   Inspect original script/scene activation, trap phase, key/head ownership,
   visibility/eligibility flags, range/height/facing, action selection and control
   release. Recover the original pickup mechanism and controls rather than
   assuming automatic contact or Space. Separate a post-Load restoration defect
   from a general interaction defect and a render-only omission.
3. Trace the original key-acquisition state and its propagation into inventory,
   key/head removal or transformation, door scene **68** and blocker **443**.
   Compare relevant instructions/Ghidra and bounded original-x86 cases. Existing
   `FUN_0042dc9c`, `FUN_00427584`, pose/owner and scene/script helpers are leads;
   do not assume the generic sword/potion path implements this puzzle.
4. Recover original geometry/animation for the actual key, trap and door owners.
   Current F5 selects neither these IDs nor representations **52/53**. Qualify
   actual pixel/pose/action paths before selective bypass changes; preserve
   fallback boxes and all F3 modes. Do not infer rendering from names alone.
5. Apply only source-backed repairs. Do not spawn a replacement key, force an
   inventory/progression flag, teleport Joe/key, skip trap timing, force the door
   open, remove its blocker, change collision/damage or reset the loaded progress
   to make a test pass. Mirror reconstructed C repairs in `GenerateRecon.js`.

## Acceptance and preservation

- From a protected copy of the user's loaded tower state, ordinary input obtains
  the original key with its correct trap timing/interaction. Record before/after
  key, head, player, script and inventory state. An isolated eligibility fixture
  or visible model is insufficient progression acceptance.
- Use the acquired key through the original door path and demonstrate actual
  passage with correct blocker/geometry state. Verify relevant unsuccessful
  attempts/locked behavior rather than bypassing their original conditions.
- Debug/ASan evidence includes original key/trap/door pixels, animation/static
  behavior, acquisition/removal, door transition and repainting. Record remaining
  natural traversal and human-review limits honestly.
- Save/Load before and after acquisition/door progression preserves key ownership,
  scripts, trap/door/blocker state and control in the same and a fresh process.
  Use private copies and freshly confirmed empty private test slots only; never
  overwrite occupied/installed saves or quick-save slot **9**.
- Preserve characters, HUD/F1/F2, F3, menus, protected saves and chunked recording.
  Agent probes are bounded, isolated and recording-off except explicit recording
  tests. Human review uses the single **Ecstatica Recompiled** F5 launch.
- Run relevant original-code fixtures, affected SDL/X11 Debug/ASan checks,
  independent four-artifact parity and documentation-tree checks. Retain failed
  probes and replay divergences; do not weaken checkpoints to manufacture success.

The [earlier tower eviction repair](../../../../../journal/entries/tower-actor-eviction-crash-2026-10-27.md)
also loaded **264/key3**. Its allocator/eviction fix does not establish key pickup,
trap behavior, models or door progression. Preserve it and investigate a shared
dependency only when current source evidence points there.
