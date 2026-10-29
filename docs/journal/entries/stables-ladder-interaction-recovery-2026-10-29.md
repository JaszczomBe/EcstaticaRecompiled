# Stables ladder interaction recovery — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Superseding save-state policy — 2026-10-29

The [integrity correction](invalid-court-save-retirement-and-persistence-audit-2026-10-29.md)
supersedes recovery-profile continuation and acceptance based on invalid
COURT/power150 state or descendants. **Malformed/corrupted or manually
patched saves MUST NOT be used to decompile game functionality or accept
progression.** COURT and its recovery/derived saves and runners are removed;
F5 uses normal storage. Historical commands below are not resume instructions.
Diagnostic logs and original-code proof remain; patched-save traversal,
persistence and replay do not qualify gameplay. Requalify from fresh
gameplay or an unmodified original save after the Save/Load repairs.


Owner: [Step 12 Task 05](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md).
The user reports that the latest recorded session reaches a ladder which does
not work. This follows the [COURT recovery](court-recovery-150-and-repeat-spider-2026-10-29.md).
Evidence root: `.tmp/ladder-session-20261029/`. No commit or push is requested.

## Session, preservation and actual checkpoint

The reported session is `/home/rgrabowski/.ecstatica2/logs/session_20261029_182427_259`.
Its pinned Debug executable is SHA-256
`ab3c66eccdfa1eca96c2a2185664dbe22100d37e91165c19b0e5301cf08a07e2`,
revision `38d79da2276c2baef8e0fceec46f0f7557cb8192` / `v0.3.0-dirty`,
with the existing **90 owners / 16 representation families**. Recording and
inspection are complete; the process exits **0**. Both exact observation replays
match all **568 checkpoints**, ending at sequence **2,308,265,829**. This proves
reproduction of the reported route, not a successful ladder traversal.

The recording starts a fresh game at camera **175**, rather than loading the
recovery save. It proceeds through **166/169/176/164/125/91/163/161/130/346/724**
to stables camera **725**. Inspection already records Joe's life as **0** before
the ladder attempts; he nevertheless remains controllable. That separate state
is retained as a limit, not repaired or used to dismiss the ladder report.
The last sampled Joe is **(-18559,4096,-14091)**, representation **12/heropunh**.

Before probes, **24** installed/default-runtime/recovery-profile saves and
**127** files from this session and the preceding **182359_497** SIGFPE session
are copied with size/SHA-256 manifests. The preceding signal is preserved without
claiming a new operand investigation. Original protection markers, recording
completion status, source saves and staged changes remain intact.

The session arguments reveal a correction to the preceding F5 profile change:
`--run-recon --data-dir ...` puts the global option after the command, where
`RuntimeArgs.c` stops parsing options. The actual log/save root therefore remains
`~/.ecstatica2`. The existing F5 entry is corrected to
`--data-dir ${workspaceFolder}/.tmp/play-profiles/court-recovery-150-20261029/runtime --run-recon`.
The two launch contracts now require the override before the command. No parser
behavior, second human launch or occupied profile save is changed.

## Original contract and demonstrated mismatch

The original stables ladder is a scripted floor interaction. Script
**459/ken:hladdown** contains:

`if Space (0x59), if facing (0x0e), start scene 761, end, end`.

Scene **761/hladdown** starts the descent from camera **725**, and
**762/kitchlad** completes it in kitchen camera **723**. Script
**461/ken:kitchenup** uses Space and facing condition **0x10** for the reverse
**763/kitchup → 764/upfrmkct** route. Original OFFSETS/FANT resources and global
script tokens are retained in `ladder-names.json`, `ladder-scenes.json` and the
scene binary extracts. No ladder mesh, activation range, facing rule, destination
or animation is invented.

At the first reported qualifying attempt, sequence **1,926,779,547**, checkpoint
**187**, Joe is **(-18392,4096,-13772)**, yaw **32353**. The live Space export is
**1**, but `_DAT_0063684d >> 24` is **0**. The executing script record equals the
mapped **459** record, and the original facing expression is nonzero. The same
mismatch appears at checkpoint **194**, yaw **18070**. Native evidence is retained
in `exact-replay-r3/observations.json`; the broader `r4` observation also counts
condition **0x59** dispatches. Its initial grid/flag dumps used incorrect bases
and are not navigation evidence; subsequent route dumps use **0x684d68** and
**0x636624**.

Original **0x44ebf2..0x44ebfb** loads the overlapping dword at **0x63684d** and
arithmetically shifts it by 24, reading the signed Space byte at **0x636850**.
The reconstruction's separate exported globals do not alias, so the condition
reads stale storage. The repair reads `(signed char)DAT_00636850`, preserving
original sign extension, negation and cursor advancement. It is mirrored in the
existing `FUN_0044e810` generator patch. This is the only production behavior
change; combat arithmetic, health, saves and all other script predicates remain.

The existing tower-condition fixture now keeps the Space and overlapping exports
separate, rather than mapping both onto the same original memory. It fails before
the repair and passes **4,768** original/native comparisons in Debug and ASan,
including **2,048** live-Space/stale-overlap cases over all 256 byte values,
negation, existing scene/facing conditions and held-key checks. Harnesses,
original ranges/hashes and logs are retained as `conditions-before*` and
`conditions-after*`. Original image SHA-256 remains `737e27…255025b`.

## Natural traversal and persistence

The repaired Debug route first completes natural descent from a private copy of
**COURT recovery 150**, preserving life **53** (`ladder-debug-r4/`). The ASan
`ladder-asan-r7/` route subsequently reaches the same ladder from COURT through
ordinary input, completes both directions, and saves/loads both landings with
life53/power150. Its final Quit helper fails on a premature menu assertion;
that recording remains incomplete and is not accepted as a clean capture.

The naturally saved upper landing, `ladder-asan-r7/ladder-returned.ECS`, supplies
a separate private installation facade for repeatable final checks. This is an
explicit original-format Load, not a forced position or progression edit.
The baseline and final commands use fresh private roots and the same checkpoint:

- **Unchanged pinned baseline**, `ladder-baseline-r9/`: Space leaves Joe at camera
  **725**, life **53**. Resumed movement and normal Quit pass.
- **Repaired Debug and ASan**, `ladder-{debug,asan}-r9/`: Space runs original
  **761 → 762**, reaching **(-18104,6656,-14136)** in camera **723**; the reverse
  runs **763 → 764**, returning to **(-18240,4096,-13712)** in camera **725**.
  Both preserve life **53** and power **150**, restore control, save/load each
  eligible landing in owned private slot **5**, resume movement and exit **0**.
  Saves are made after scene ownership ends, never forced during a climb.
- Independent fresh processes load both endpoint saves and compare the serialized
  actor fields, attachments, inventory and music state. Each configuration passes
  original HUD/F1/F2, independent F3 modes, Enter/Escape inventory, Sound/Music
  toggles and restoration, resumed movement and normal Quit. Reports are
  `ladder-{debug,asan}-r9/fresh-validation-r2.json` and `fresh-*-r2/fresh.result.json`.
- Strict audio-on/off replay matches all **92 checkpoints** per configuration,
  four successful replays total. Debug ends at sequence **281,087,296**, ASan at
  **82,001,898**. Replays begin from copied initial saves, not the capture's
  already-written slot5. No checkpoint is relaxed or source recording changed.

Final Debug SHA-256 is
`0ec8c56d01e558d135c121725f8c3b6b36668cb84af443ac595fd6d7d29cbe54`;
ASan is `b8c1d7a062fea8c88b9423d8b05c1c04d04133ee8634f1d03125c50aaa18c529`.
Each final route directory pins its executable.

## Probe failures, regression checks and remaining limits

All failed attempts remain separate. The first two historical replay attempts
are rejected for added SDL driver environment variables; exact-environment runs
then pass all 568 checkpoints. Initial straight walking hits a courtyard wall;
conservative floor planning cannot cover the scripted stables entrance. Later
probes use mapped courtyard paths and the observed human approach, with NPC
interference retained as failures. A mistaken combat modifier stops movement in
`r5`; it is removed. Incomplete mouse events are corrected to press/release.
The queued-event driver must wait for the actual main requester, rather than the
shared helper's fixed pump count. These private fixes do not change runtime logic.
The first fresh HUD attempts reuse a recording driver's no-op presentation helper
and fail; recording-off fresh checks use the shared synchronous input/presentation
helpers and pass. The user interrupts during probes and explicitly resumes; all
partially completed outputs are retained.

All four SDL/X11 Debug/ASan builds pass. Independent generation matches all four
artifacts, with only the intended reconstructed condition diff. All **67** suite
contracts and **31** developer-launch/logging cases per configuration pass.
Python/generator syntax, whitespace and README-tree checks pass. Final preservation
and result indexes are retained under the evidence root.

The existing F5 launch now actually uses the prepared human recovery profile.
Load **COURT recovery 150**; its saved starting life53/power150 and all occupied
slots remain unchanged. Private ladder endpoint saves are evidence, not automatic
replacements for human slots. Continue linking the next human session to its
actual loaded save and root.

This qualifies the stables/kitchen ladder in both directions and its eligible
landing persistence. Other ladder variants, uninterrupted human-route acceptance,
full animation/composition review, mid-climb saving, the reported zero-life
controllable state, fresh boots/acid lifecycle, broader sound transitions and
extended playthrough remain open. No original save, source recording, combat
behavior, commit or push is changed.
