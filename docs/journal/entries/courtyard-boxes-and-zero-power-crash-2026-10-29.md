# Courtyard models and the saved zero-power crash — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Save-state acceptance correction — 2026-10-29

The [integrity audit](invalid-court-save-retirement-and-persistence-audit-2026-10-29.md)
identifies old runtime5/123 and6/DFGSDRG as zero-power/zero-counter saves and
quarantines them outside Load. Routes based on those files or descendants cannot
qualify gameplay progression or persistence, including historical tower/castle
and occupied-slot inventory checks. Independent original-code comparisons and
fresh/untouched-original tests retain their stated scope. **Invalid or manually
patched save state MUST NOT be used to decompile game functionality.** Requalify
affected routes from valid progression; the preservation claims below describe
the earlier historical investigation, not current active save availability.


Owner: [Step 12 Task 05](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md).
The second report requests investigation of courtyard object boxes, including
doors, and a crash in `FUN_0042efdc`. Preserve the
[first session's evidence and limits](garden-teleport-and-boots-session-2026-10-29.md).

## Session chain and protected checkpoints

Both newly retained F5 sessions pin Debug executable SHA-256
`ab3c66eccdfa1eca96c2a2185664dbe22100d37e91165c19b0e5301cf08a07e2`,
source context `38d79da2276c2baef8e0fceec46f0f7557cb8192` / `v0.3.0-dirty`,
and the preceding **81-owner** model selection. All investigation outputs are
private under `.tmp/courtyard-session-20261029/`.

| Session | Loaded checkpoint | Result and continuity |
| --- | --- | --- |
| `/home/rgrabowski/.ecstatica2/logs/session_20261029_164439_553` | Installed **2/g3**, **211,193 bytes**, SHA-256 `1c884e338a2d746d3a7a53bc1ccde62e4417e768fd9a34f8d2cbc124674b75fd` | Exact **1,192** checkpoints, complete recording and clean exit 0 at sequence **687,738,401**. Starts with power **200**, kills **574**, gold counter **15,095**. Garden → courtyard → hut → wider route → workshop camera **167**; final Joe **(7575,4096,-10747)**, health **160**, gold sword retained. No Save call occurs. It reloads the same original checkpoint as the first report. |
| `/home/rgrabowski/.ecstatica2/logs/session_20261029_165921_595` | Runtime **7/COURT**, **275,083 bytes**, SHA-256 `880abe065c2fd9c5bd255550f93694216cd3e66e66888b4d7fe12aa9e84dca64` | All **700 available checkpoints** match, then the same **SIGFPE** occurs at sequence **273,138,436**. Recording and inspection remain incomplete. Starts with power, kills and gold **0**, health **53**, regular sword. Courtyard cameras **132 → 162 → 132 → 143**. This loads an older checkpoint rather than the preceding clean session's end state. |

The actual loaded slots and scalars are observed at `FUN_004544a4` entry/return
during exact replay, with no writes to game state. The 700-checkpoint crash
reproduction is not a complete recording or successful playthrough.
The runtime slot-7 file has not changed since the first investigation and its
mtime is **2026-10-28 14:17:23 UTC**, before the later inventory/scalar repair.
Installed slot 7 contains an empty marker and is a different file.

Private copies preserve **59** crash-session files and **56** preceding-session
files, including both pinned binaries, source/build context, recordings,
inspection and debugger evidence. The crash bundle exports and verifies while
retaining incomplete status. All **14** installed/runtime save files are
snapshotted with size/hash. No source protection marker, save or recording tail
is changed. The first session and older crash/audio evidence remain protected.

## Crash cause and original-code comparison

The exact crash has attacker **80/w_dorc2**, target **0/Joe**, camera **143**,
normal difficulty and computed damage **10**. Player power at mapped
**0x47ab28** is already **0** immediately after Load and remains zero at the
fault. The expression attempts **10 × 100 / 0** at reconstructed line **25738**.
There is no evidence of a new scalar write losing power during this route.

Original **0x42f396..0x42f429** branches on player identity and difficulty,
divides by **0x47ab28**, then writes Joe's signed health at **+0xec**. Normal
difficulty uses `idiv ecx` at **0x42f3e3** with no zero guard. The current C has
the same operation. This is the saved-zero condition identified in the
[inventory recovery](enter-inventory-menu-recovery-2026-10-28.md), now reproduced
in an actual human crash rather than only the earlier agent route.

New [combat-power comparison](../../../scripts/check-e2-combat-power.py) extracts
the production health-write branch and executes the original instruction range
with explicit EBX damage and ESI target registers. It passes **1,872** health
write cases in Debug and ASan: player/NPC, signed damage/health, six nonzero
powers, NPC zero power, three difficulty branches and the original fallback
difficulty branch. Eight isolated original/native player-zero cases per
configuration terminate with the expected **SIGFPE**. Core dumps are disabled
for these deliberate fixture faults. Provenance records the original image,
exact code range, harness and intercepted continuation at **0x42f429**.
Collision, damage derivation, sound, scripts and persistence remain outside this
small arithmetic comparison; the actual crash replay supplies native context.

No guard, save normalization, power assignment or save-format change is made.
The old save retains its lost statistics. A healthy existing checkpoint such as
installed **2/g3** supplies power **200**; it is not the end save of the latest
route. Recovering the old checkpoint would require authoritative evidence of
the lost value or a separately chosen data-repair policy. Do not silently guess
**100** or overwrite an occupied slot.

## Courtyard boxes and original owners

Display hotkeys F1/F2/F3 are consumed before replay and input logging, so their
absence from the retained recordings cannot establish the human session's F3
history. The last retained crash frame has no F3 mode banner, consistent with
the default mode at that presentation; it does not establish every earlier
frame. Independently, the nine original owners below are absent from the
81-owner selection and retain diagnostic fallbacks in default mode. Do not
attribute the entire box report to a display-mode choice.

| New owner | Source ownership | Representative Debug/ASan changed pixels |
| --- | --- | --- |
| **256/kdoor** | Representation **28/door**, scene **146**, camera **143**; also original scenes 59/60/62. 33 nodes and 20 flat faces, no textures. The crash checkpoint has a damaged door; do not reset it or remove baked background artwork. | **2 flat / 18 rounded** |
| **1087/kchest7** | Representation **433/chestpot**, scene **442**, camera **162**; 46 nodes and 32 faces. | **118 flat / 4 rounded** |
| **1098/statu9**, **1099/statu8** | Scenes **447/448**, **445/446**, camera **132**; 57 nodes each, original courtyard statue owners. | **37 / 45 rounded** |
| **1027/gastub2** | Representation **107/gas**, scene **414**, camera **144**; 3 nodes. Distinct from selected gas owners 737/1028. | **79 rounded** |
| **1668/amulet** | Representation **172/amulet**, scene **663**, camera **651**; 10 nodes. | **24 rounded** |
| **1843/amusign** | Scene **792**, camera **651**; 6 nodes and 8 faces. Sign/amulet project above the adjacent courtyard. | **18 rounded / 183 flat** |
| **2862/prtpad11** | Scene **1214**, camera **142**, 14 nodes; this courtyard pad differs from selected garden 2927 and castle 2864. | **74 flat** |
| **2925/bootswch** | Scene **1248**, camera **546**, representation **316/twrswch**, 27 nodes. The old checkpoint's brown head differs from the selected gold 2926. | **326 rounded / 3 flat** |

Original OFFSETS/FANT/name-pool inventory is retained in `original-assets.json`.
Explicit original scene installation/activation and read-only raster entry/return
observations qualify these resources in **18** bounded Debug/ASan previews.
They select the original camera and pose; they are not natural traversal,
pickup, completed door opening or full visual composition acceptance. Each
preview also checks HUD/F1/F2 and independent F3 original/mixed/boxes modes.

F5 now selects these **nine** additional owners: **90 explicit owners**, with
the existing **16 representation families** unchanged. Original static/dynamic
page, depth, visibility, material, animation, collision and interaction paths
remain in charge. Other unqualified objects retain fallbacks; F3 still exposes
boxes on demand. No blanket box hiding or global mesh-bypass removal occurs.

A read-only audit also finds **52** original roots using door representation 28,
in seven record-layout groups. Only observed owner **256** is newly selected;
earlier **963/980** remain selected. That audit alone is not a qualification of
every door variant, so representation 28 is not enabled as a whole family.

## Verification and next action

The original combat-power fixture passes normally and under ASan. Four SDL/X11
Debug/ASan builds pass, and independent generation matches all four artifacts.
There is no reconstructed C repair to mirror in `GenerateRecon.js`; the only
runtime-facing change is F5's source-backed model selection.

Final 90-owner commands in `qualify.py` use private outputs and a healthy copied
installed slot 2. Initial requests **did not execute**: automatic approval review
returned timeout/capacity errors, and the permitted retry also timed out. These
were approval-service failures, not failing tests or a safety determination.
The user explicitly approved another retry; it passed without changing models.

Both Debug and ASan pass protected same/fresh-process Save/Load in private
slot 5, original HUD/F1/F2, independent F3 modes, Enter/Escape inventory,
sound/music settings and restore, resumed movement/weapon attachment and Quit.
Recording is off for persistence. Both also pass a fresh live-population,
original-character **27-checkpoint** recording and **six** strict replay variants:
three ordinary repeats, inspection disabled, debugger pause and audio disabled.
Each preserves its capture's original sound-request sequence (**24** requests
in Debug, **20** in ASan) and three-line music resource/play/stop sequence;
enabled devices produce nonzero isolated PCM. These are independent fresh
captures, not a claim of identical Debug/ASan event counts.
Reports are in `persistence-final-{debug,asan}/report.json` and
`replay-final-{debug,asan}/report.json`. These are bounded regression checks,
not fresh item interactions, complete routes, human listening or full visual
acceptance. The preceding 81-owner regression remains historical evidence.

All 14 source saves and all 115 newly retained human-session files preserve
their sizes and SHA-256 hashes. The first report's 58 source-session files are
also unchanged. Documentation checks connect 299 Markdown documents to README;
launch JSON, Python syntax and whitespace checks pass.

Next: link the next human session to its actual loaded checkpoint, continuing
from a validated healthy save such as installed g3. Runtime 7 remains a known zero-power crash
input; it is not repaired by rendering changes. Fresh boots acquisition/hazard
expiry, ladder use, broad model coverage, full visual review, uninterrupted
routes and extended stability retain their prior limits. No commit or push.
