# Stables spider hit and the retained zero-power save — 2026-10-29

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
The user reports another crash in `FUN_0042efdc`, this time when a spider hits
Joe at the stables. This follows the
[courtyard investigation](courtyard-boxes-and-zero-power-crash-2026-10-29.md);
the stack alone was not treated as proof of the same cause.

## Pinned session and checkpoint continuity

Session `/home/rgrabowski/.ecstatica2/logs/session_20261029_173150_691` pins Debug
SHA-256 `ab3c66eccdfa1eca96c2a2185664dbe22100d37e91165c19b0e5301cf08a07e2`,
source context `38d79da2276c2baef8e0fceec46f0f7557cb8192` / `v0.3.0-dirty`,
and the **90-owner / 16-family** F5 selection. Finalization records **SIGFPE**,
incomplete replay/inspection and retained crash protection. These statuses remain
unchanged. Evidence is private under `.tmp/stables-spider-session-20261029/`.

Bounded exact replay observes Load slot **7** and resolves it to runtime
`/home/rgrabowski/.ecstatica2/Saved/0007.ECS`, label **COURT**, **275,083 bytes**,
SHA-256 `880abe065c2fd9c5bd255550f93694216cd3e66e66888b4d7fe12aa9e84dca64`.
Power, kills and gold are already **0** when Load returns. This is the identical
file used by the preceding courtyard crash, not a newly saved continuation or
the validated installed **2/g3** checkpoint. No Save call occurs in this session.

All **915 available checkpoints** match before the same signal at replay sequence
**719,566,321**. This is an exact crash reproduction from an incomplete recording,
not clean completion. The gameplay camera route is **132 → 161 → 546 → 161 →
163 → 161 → 130 → 345 → 346**; camera 1073 belongs to startup before Load.
The last sampled Joe is **(-21517,4096,-13664)**, health **53**, representation
**9**, with the ordinary sword state retained.

The actual attacker is original **26/w_spids4**, representation **74/spider2**,
archive offset **1,134,210**, in stables camera **346**. Last sampled spider
action is **1272**. Its identity and representation agree with original OFFSETS,
FANT/name pools and the retained inspection state.

## Fault operands and original behavior

At the reproduced fault: attacker **26**, target **0/Joe**, normal difficulty
**1**, damage **2**, mapped player power **0**, Joe health **53**. Reconstructed
line **25738** attempts **2 × 100 / 0**. The Load observation establishes the
zero before traversing to the stables; there is no evidence here of a new
spider-induced power loss.

The original **0x42f396..0x42f429** bytes match the preceding retained extraction.
They load power from **0x47ab28** and execute unguarded `idiv ecx` at
**0x42f3e3** for normal difficulty, before writing signed health at **+0xec**.
Current C has the same operation. Original image SHA-256 is
`737e27ddfb76501ba6caf4f504b0c128854a36733526b17d30f635a1c255025b`;
the 147-byte range has SHA-256
`8309009522620451aee60f0b6a4f0e4fad536ab5b54a838e0127b9f399477004`.

The [combat-power fixture](../../../scripts/check-e2-combat-power.py) now includes
damage **2** among the compared health writes and tests both observed damage
values **2/10** in isolated original/native zero-power cases. Debug and ASan
each pass **2,184** health-write comparisons and **16** expected SIGFPE cases.
The fixture uses extracted production C and executable original instructions;
only the continuation after the health write is intercepted. Deliberate faults
have core dumps disabled. Collision, damage derivation, scripts, audio and
persistence remain outside that arithmetic fixture; exact session replay supplies
the real spider-hit context.

An initial fixture launch did not execute because automatic approval review was
at capacity. One bounded retry succeeded without a model change. This is an
execution-service failure followed by passing checks, not a failed fixture or
a safety denial. The first replay observer read a 16-bit fragment of the resource
pointer at byte **+0x11e** instead of dereferencing that 32-bit pointer for its
resource ID; its raw negative value is invalid evidence. Use inspection's representation **74** and original resource
mapping, as recorded in `route-and-attacker.json`. Raw logs are preserved.

## Preservation, verification and next action

Before replay, **63** session files and all **14** installed/runtime saves were
copied with size/SHA-256 manifests. The exported crash bundle verifies and retains
the incomplete replay/inspection markers. Replay uses copied runtime saves,
the pinned executable and recorded environment, with recording and audio-device
output off. It does not force game state or weaken strict checkpoints.

There is no production C, generator or F5 selection change in this follow-up.
Independent generation still matches all four artifacts. Python syntax,
whitespace and README-rooted documentation checks pass. No runtime rebuild,
new HUD/F3/inventory/persistence/audio acceptance or healthy stables playthrough
is claimed from the expanded arithmetic fixture. The preceding final 90-owner
Debug/ASan regression evidence and its limits remain intact.

All 14 source saves, the 63 new source-session files and the preceding three
sessions' **173** source files retain their sizes/hashes after investigation.
Existing occupied saves, crash protection and recordings remain preserved.

Next human play should load a validated healthy checkpoint such as installed
**2/g3** (power **200**, label **g3**) or start a fresh game. Loading **COURT**
again restores the same lost scalar values; rebuilding does not repair that
file. A recovery of its original statistics needs authoritative values or a
separately selected data-repair policy. No guard, guessed replacement power,
save rewrite, commit or push is introduced. Continue recording each actual
Load and preserve fresh boots/hazard/expiry, ladder, full visual review and
extended stability limits.
