# Tower key progression handoff — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## User request and next priority

The user requests a handoff for the next context after loading a saved game at
the top of the tower. A key should be available on the spike trap, but cannot
be taken. The key, spike trap and associated keyed door have no recovered models.
The user identifies this as a vital progression blocker, not optional decoration.

[Step 12 Task 03](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-03-recover-tower-key-trap-and-door-progression.md)
now owns recovery of the original acquisition/trap/door mechanism and models.
It precedes remaining decorative/acid coverage, game sounds and music. This
handoff does not implement or accept a runtime fix. No commit, push or tag change.

## Baseline and evidence read

Current branch **linux-e2-reconstructed-runtime**, HEAD
**990bdd9ea080ccdf434f626d4d20bf440f12a422**, containing the preceding object/F3
recovery. The worktree was clean when this documentation handoff began.
Earlier journal baseline **a2a6043** is historical, not the current resume point.

The latest finalized human session is
`/home/rgrabowski/.ecstatica2/logs/session_20261028_161516_514/`.
Its manifest pins Debug executable
`investigation/e2recomp`, SHA-256
`d4af20e324efe494a22c8efb69fce69faf5b95efb0d183cf4dd7206e5e5c8a00`,
and revision **990bdd9**. Recording and inspection are published complete, with
native exit **0**. The final inspection event has checkpoint **964**, update
**1053**, sequence **432662538**. These describe the capture, not a successful
replay or resolved progression. No native process/replay was run for this handoff.

The runtime log records `action.load_complete` at **16:15:25** local time.
Inspection changes from intro camera **1073** to tower camera **28** at snapshot
**33**, then stays there. Original-data names identify live **259/pike**,
**264/key3**, **265/keyhed3**, **266/door3**, **443/blocker1** and nearby
**3113/coins7**. Source scenes/scripts and bounded observed state are recorded
in Task 03. Nearby coins already belong to selected representation 282; do not
mistake their successful/removal state for acquisition of key 264.

Key **264** retains position `(-18432,-3776,-620)`, flags **0x0c28**, state **0**
and no action/representation in the post-load observations. Joe is initially
`(-18881,-3328,-1032)`, health **69**, and ends at `(-18304,-3328,-2160)`,
health **74**, scene **65/hdeth1**. Trap **259** ends in that same scene.
This supports preserving the reported key/trap interaction failure as an active
blocker; it does not identify its root cause or prove that every correct original
input/timing condition was attempted. Source-authored key height must not be
changed merely to make a generic pickup query succeed.

Original resource inventory identifies key **264** with six nodes, trap **259**
with two nodes/eight flat faces, key-head **265** with 19 nodes, and door **266**
with 20 nodes, all without texture references. Trap/head representations are
**53/pikerep** and **52/keyhd3**. They are outside the current explicit F5
selection. These are render/owner leads, not verified original pixels.

The previous finalized session **20261028_160713_387** loads into courtyard
camera **132** and continues through town; it is not the primary tower repro.
The [older tower eviction journal](tower-actor-eviction-crash-2026-10-27.md)
mentions loading **264/key3** but only qualifies its source-backed allocator/
eviction repair. It does not qualify the current puzzle or its models.

## Save protection and reproducibility

Runtime saves were read only. Currently `~/.ecstatica2/Saved/` contains these
occupied files; do not overwrite any of them, including quick-save slot 9:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| **0006.ECS** (`DFGSDRG`) | 246301 | `5da846d89e4fae206e87ac9016d0f006e6790c9d6547c285e4e73d2f79442e8a` |
| **0007.ECS** (`COURT`) | 275083 | `880abe065c2fd9c5bd255550f93694216cd3e66e66888b4d7fe12aa9e84dca64` |
| **0009.ECS** (quick save) | 171052 | `a314c1287b937cf9f95f360fe3539b01c6ebd412d9629f55fa5333c41c3167c0` |

The actual selected load slot is not established here. Freeze the finalized
session/pinned binary and these runtime saves into private storage, preserving
their bytes and directory layout, then identify the loaded file from the recorded
menu/input and restored state. Keep installed saves read-only too. A replay that
only sees installed-save fallbacks may restore different progress and cannot
qualify this reported attempt. Never alter recording metadata or loosen replay
checks to hide a mismatch; record any missing dependency/divergence explicitly.

## Concrete first action for the next context

Read README → capabilities → HANDOFF → active implementation → Step 12 Task 03
and this journal. Freeze the matching evidence/save inputs and reproduce the
Load-to-trap attempt with bounded observation. Trace scenes **83/key3**,
**84/key3_st**, **65/hdeth1**, **2004/hdeth2**, **68/h_doropn** and
**86/h_doors1**, plus original FAN names **Key3**, **key3_st**, **h_doropn**,
**dav:key3_st** and **dav:h_doropn**. Recover original eligibility, scene phase,
interaction controls, state ownership and door/blocker transition before fixing
the smallest proven fault. Compare the loaded-state path with ordinary activation
where needed; do not assume either a save defect or a rendering-only defect.

Task 03 requires natural key acquisition and actual door passage, original
models/animation, protected before/after persistence, generator mirroring,
four-artifact parity and bounded Debug/ASan evidence. Retain characters, HUD/F1/F2,
F3 fallbacks, menus and recording. No further task-selection confirmation is
needed; do not substitute a spawned key, forced inventory flag or removed blocker.

## Documentation changes and limits

The user explicitly requested the next-context handoff. The structural reason
for changing HANDOFF's resume links is that they still point at completed first-
slice Task 01; the next context must open the newly prioritized blocking Task 03.
Changing evidence remains owned by the task/implementation and this journal,
not copied into the durable HANDOFF anchor. README, capabilities, Step 12,
Task 02 and milestones point to the new priority without erasing prior evidence.

Verification for this turn is documentation-tree update/check and whitespace
validation. The session/resource/save reads above are observational only; no
runtime source, launch selection, original asset, recording or save is changed.
