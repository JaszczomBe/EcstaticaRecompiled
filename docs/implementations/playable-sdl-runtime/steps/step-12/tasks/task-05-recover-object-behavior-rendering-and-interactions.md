# Recover Object Behavior, Rendering and Interactions Across Playthrough Sessions

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Item, Weapon, Door and Acid-Pool Models and Animations](../step-12-recover-object-models-and-animations.md)
<!-- /docs-tree:parent -->

Status: active; invalid COURT recovery retired; Save/Load scalar repair verified; ladder progression needs valid-seed requalification
Parent Step: [Object models and animations](../step-12-recover-object-models-and-animations.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-29

## Goal and priority

After the `v0.3.0` sound/music milestone, the user selected remaining original
object behavior, rendering and interactions, with additional stability checks
and a gameplay playthrough spread across several Save/Load sessions. Initial
examples are **anti-acid boots** and **ladder usage**. These identify investigation
targets, not proven failures or permission to invent missing mechanics.

This task coordinates the next continuation. [Task 02](task-02-qualify-object-variants-and-natural-acid-lifecycle.md)
retains detailed variant/acid evidence; [Task 04](task-04-recover-inner-castle-progression-crash-and-models.md)
retains castle repairs and unfinished route/equipment acceptance. The
[handoff journal](../../../../../journal/entries/object-behavior-and-interactions-handoff-2026-10-29.md)
records baseline, protection, first actions and session continuity. No new object
repair, crash reproduction or gameplay acceptance is claimed by this handoff.

## Scope

1. Follow the user's actual route across successive saved sessions. Identify each
   reported object, interaction, rendering gap or stability failure using its
   source save, pinned executable, session recording and original resource owner.
   Address a demonstrated crash/blocker before dependent progression.
2. Recover item/equipment behavior together with its loose, collected, equipped
   and persistent representation. For anti-acid boots, trace the actual original
   item/flags, acquisition/equipment conditions, hazard eligibility, damage or
   resistance rules and any authored lifetime. Do not infer protection from an
   inventory icon or assume permanent immunity, automatic equipping or a timer.
3. Recover environmental interactions such as ladders: original approach/facing,
   input and eligibility conditions; script/action and animation ownership;
   collision, movement, camera handoff, dismount and subsequent control. Establish
   which states the original allows saving; verify those through real Save/Load.
4. Recover remaining original object/equipment/effect pixels, attachments, action
   lifetimes, material/depth/page ownership and removal. Keep diagnostic fallbacks
   until each class has source-backed and fresh native evidence. Preserve F3's
   independent original/mixed/boxes modes and original HUD/F1/F2 ownership.
5. Extend stability and persistence checks around each recovered path, then
   resume playthrough from the documented checkpoint. Preserve original code
   and possible original defects; require a proven reconstruction mismatch
   before changing behavior, appearance, physics, damage or timing.

## Session continuity

Use the existing single **Ecstatica Recompiled** F5 launch for normal human play.
The user will Save/Load over several sessions; there is no assumption of one
continuous process or a fresh game on each report. Record an explicit link from
one session's end checkpoint to the next session's loaded save.

For every investigated session, append evidence to the owning dated journal
and update this task's current checkpoint/next action. Retain:

- Session path/ID, exact pinned executable hash and source/build context; normal
  exit, signal or incomplete-capture status. Do not identify a run only by newest
  timestamp: automated probes can also create sessions.
- Actual loaded slot, label and source location, plus save size/SHA-256 before
  investigation. A slot number alone does not identify its contents after later
  human saves; preserve the relevant snapshot before it is replaced or rotated.
- Route/cameras and object/actor/representation/action identities when established;
  held/equipped items and relevant progression state before and after Load.
- The user's expected/observed result, evidence that proves a mismatch or leaves
  it unresolved, exact changes, failed attempts and Debug/ASan verification bounds.
- The last safe checkpoint, remaining blockers and concrete next action. Link the
  next session explicitly; do not promote a recovered prefix to a full playthrough.

Important clean-exit recordings can be removed by retention later. Preserve a
private copy or investigation bundle of relied-on sessions, pinned binaries and
save snapshots before cleanup; retain existing protection markers. Do not alter
source recordings, complete an incomplete tail or weaken strict checkpoints.

## Current session checkpoint

The [save-state integrity correction](../../../../../journal/entries/invalid-court-save-retirement-and-persistence-audit-2026-10-29.md)
supersedes the COURT recovery and its descendant progression. **Malformed,
corrupted or manually patched saves and their descendants MUST NOT be used
to decompile/reconstruct game functionality or accept gameplay progression.**
Inspect them only for persistence diagnosis; repair the implementation and
verify it from a fresh game or unmodified original save. A patched-save
round trip proves persistence of supplied bytes, not recovery of lost state.

COURT, power150 copies and derived progression checkpoints are removed. Private
recovery runners are removed and F5 returns to normal runtime storage. The
other old zero-power slots123/DFGSDRG are quarantined with non-loadable
extensions; source recordings, diagnostic reports and unrelated saves remain.
No automatic state restoration, power assignment or combat guard is introduced.

Current Save/Load additionally repairs live difficulty and poison-duration
ownership. Debug/ASan valid-seed tests cover two menu Save/Load cycles and
fresh-process restoration, live/stored health and power/kills/gold/difficulty,
Settings difficulty changes, inventory/music, resumed movement/attacks and
normal Quit. Complete writer/scalar restoration comparisons match original x86.
These results do not establish arbitrary progression or malformed-file recovery.

The [ladder report](../../../../../journal/entries/stables-ladder-interaction-recovery-2026-10-29.md)
retains fresh-game session182427_259, 568 exact diagnostic checkpoints and
the original-backed stale Space mismatch. Its signed-byte repair and generator
mirror remain supported by 4,768 original condition comparisons. The later
92-checkpoint ladder traversal and landing persistence used COURT150 descendants
and are withdrawn as gameplay acceptance. Requalify down/up from valid state.

Next: start a fresh human F5 game or verify an untouched original checkpoint,
link its actual loaded save/build/session, then repeat the ladder route and
eligible landing Save/Load. Do not resume the retired recovery profile or
use private endpoint saves. The zero-life controllable state, other ladders,
fresh boots/acid lifecycle, visuals and extended play remain open.

### Historical invalid COURT experiment

The [repeat crash/recovery journal](../../../../../journal/entries/court-recovery-150-and-repeat-spider-2026-10-29.md)
retains the 1,381-checkpoint zero-power crash diagnosis, life53/100 assessment
and abandoned guessed-power experiment. Historical power/kills/gold cannot
be established. Its patched-save hit, replay and round-trip results are
diagnostic records only and cannot qualify recovered progression.

The [preceding stables spider investigation](../../../../../journal/entries/stables-spider-and-zero-power-save-2026-10-29.md)
preserves **20261029_173150_691** with its pinned 90-owner Debug executable,
matching source-save snapshot and incomplete crash bundle. All **915** available
checkpoints match before the same SIGFPE at sequence **719,566,321**. It again
loads unchanged runtime **7/COURT**, power/kills/gold **0**; no Save call occurs.
Spider **26/w_spids4** hits Joe for damage **2** in camera **346**, attempting
**2 × 100 / 0**. Original code has the same unguarded division. Expanded Debug/ASan
comparisons pass **2,184** health writes and **16** expected original/native
zero-power faults per configuration. No production behavior or save changes.
Continue human play from validated installed **2/g3** or a fresh game;
reloading COURT remains a known combat-crash input.

The [preceding courtyard investigation](../../../../../journal/entries/courtyard-boxes-and-zero-power-crash-2026-10-29.md)
preserves crash **20261029_165921_595** and intervening clean session
**20261029_164439_553**, with matching pinned executables and save snapshots.
The crash strictly matches all **700** available checkpoints before the same
SIGFPE: it loads old runtime **7/COURT** with power **0**. Original combat
arithmetic has the same division; the original/native fixture passes, and no
save or damage normalization is made. The preceding clean run matches **1,192**
checkpoints from installed **2/g3**, power **200**, and makes no Save call.
This is an explicit checkpoint change, not continued progress from its end.

F5 selects **90** explicit owners after nine further courtyard models pass
Debug/ASan pixels and HUD/F3 checks. Final protected same/fresh persistence,
HUD/F3/inventory and six strict audio/music replay variants per configuration
pass, each matching 27 fresh checkpoints. Initial approval-service failures
are retained in the journal; an explicitly approved retry completed the checks.
Keep unqualified boxes and the old-save
fault visible as limits. The [first report](../../../../../journal/entries/garden-teleport-and-boots-session-2026-10-29.md)
retains its **1,386**-checkpoint exact replay, garden teleport qualification and
spent-boots finding. Fresh boots/hazard/expiry, ladder use and full visual or
extended gameplay acceptance remain open. Next reports must identify their
actual loaded save; runtime 7 is still a known crash input.

## First bounded action

1. Re-read the selected task and handoff; check HEAD/worktree and retained limits.
   Identify the user's first post-milestone session/route and actual loaded save
   from supplied observations and session evidence. If no such report exists,
   begin read-only original asset/script mapping for the boots and ladders;
   session-dependent reproduction waits for an identified checkpoint.
2. Inventory/hash current installed/runtime saves and relevant session/crash
   evidence. Pin the actual session executable and create private reproduction
   inputs before running probes. Discover current occupancy again; the baseline
   slot list is not a future allocation policy.
3. Trace the first reported behavior or rendering path through original
   `E2WIN95.EXE`, disassembly/Ghidra and original game resources. Identify input,
   owner/state and save contracts before editing code. The example objects have
   no established actor IDs or proven defect in this handoff.
4. Reproduce with bounded ordinary input from a protected copy. Record the first
   divergence/fault, compare the corresponding original instructions, and repair
   the smallest demonstrated reconstruction error. Mirror C repairs in
   `E2Recomp/tools/GenerateRecon.js` and verify independent generated parity.
5. Verify the affected path and Save/Load boundary, then return a clear checkpoint
   for the user's next human session. Keep isolated or forced-state diagnostics
   distinct from naturally reached gameplay acceptance.

## Verification and acceptance

- Use bounded Debug/ASan probes with explicit input/timeouts and private runtime
  storage. Recording defaults off except explicit fresh record/replay tests.
  Compare original instructions and meaningful rendering/state evidence for each
  repaired contract; do not replace source recovery with speculative guards.
- Verify actual interaction outcomes, ownership, damage/resistance when applicable,
  original animation/pixels and control after completion. Static previews and
  survival alone do not establish working boots, ladders or complete progression.
- Use only confirmed empty **private** save slots. Test affected item, equipment,
  world and progression state through same-process and fresh-process Load, plus
  resumed input and camera transitions. Do not force saving in an originally
  ineligible state or change the original save format to pass a probe.
- Retain characters, HUD/F1/F2, F3, Enter/Escape inventory, menus/Quit, original
  sound/music and strict recording/replay. Run relevant existing regressions and
  affected SDL/X11 Debug/ASan builds; add checks for newly proven contracts.
- Record fresh evidence, failed attempts and limits in this task and dated
  journals. Full route, human visual/behavioral review and long-session stability
  require their own evidence; earlier successful probes do not qualify new paths.

## Preservation and boundaries

Protect all occupied runtime/installed saves and quick-save 9. At this handoff,
runtime **5 (123), 6, 7, 9** are occupied. Installed slots 5/6/7 have empty markers,
but they are different from occupied runtime saves of the same number. Re-scan
before every probe; the user will continue saving during the playthrough.

Keep the protected 2026-10-28 crash session, incomplete source replay, prior
castle/inventory evidence and the full sound/music evidence. Preserve existing
changes and all earlier acceptance limits, including unresolved translucency,
equipped-armour/full gate effects, natural acid lifecycle, HUD/inventory branches,
audio device/focus transitions and optimized-build/portability work.

Unrelated cleanup, broad physics/AI/damage changes, replacement art, blanket
fallback/bypass removal, save-format changes and portability remain outside this
continuation. A source-backed dependency repair belongs here only when needed
for the reported original object path. Do not commit, push or change tags unless
separately requested.

## Review state

1. Planning: user selected the priority and multi-session workflow.
2. Implementation: 90 original owners selected; no reconstructed C or damage
   change. Actual runtime-7 crash and original arithmetic are compared; nine
   additional courtyard owners pass native pixel/HUD/F3 checks.
3. Current checkpoint: invalid COURT recovery and descendants are retired. Save/Load
   difficulty/poison-duration repairs pass valid-seed Debug/ASan checks. The
   original-backed Space predicate remains; ladder traversal and persistence
   require requalification from valid progression. F5 uses normal storage.

## Change log

### 2026-10-29

1. Retired invalid COURT/recovery state and tooling by user instruction, forbade
   invalid save ancestry as reconstruction evidence, withdrew dependent gameplay
   acceptance and repaired the remaining duration/difficulty Save/Load ownership.
   Fresh-game and original-g3 Debug/ASan same/fresh checks pass; requalify ladders
   from valid progression before continuing deeper gameplay acceptance.

The earlier entries below record historical work; the retirement above supersedes
recovery-profile continuation and patched-save acceptance.

1. Reproduced the stables ladder report through all 568 checkpoints, repaired the
   original Space predicate, qualified both directions and eligible landing
   persistence in Debug/ASan with 92-checkpoint strict replay, and corrected F5's
   profile-option order. Other ladder and zero-life control limits remain.

1. Reproduced the next intended COURT spider crash through 1,381 checkpoints,
   audited original power sources, and prepared the explicitly chosen power-150
   recovery copy/profile. Corrected Debug persistence passes; route/ASan/replay
   remain pending when the user stops further work after review-service failures.

1. Reproduced the latest stables spider hit after all 915 available checkpoints,
   confirmed another Load of unchanged zero-power COURT, expanded original/native
   arithmetic comparisons to damage 2 and preserved all session/save evidence.

1. Investigated the latest courtyard crash and preceding clean session, proved
   the saved-zero condition against original code, and selected nine more
   source-backed model owners while preserving saves and fallback coverage.
1. Investigated the first supplied garden/courtyard/hut session, selected five
   original owners, verified protected intermediate regressions and natural
   teleport/glow, and retained spent boots, old-save crash, failed probes and
   full effect/fresh boots/ladder acceptance limits.
2. Selected object behavior, rendering and interactions as the next priority
   after audio; added session continuity, protected persistence and stability
   criteria without claiming new runtime acceptance.
