# Repeated spider crash and the chosen COURT recovery — 2026-10-29

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
This follows the [first stables spider crash](stables-spider-and-zero-power-save-2026-10-29.md).
The user confirms that **COURT** was the intended checkpoint and explicitly
chooses **power 150** for a separate recovery copy. This is a chosen data-recovery
policy, not proof of the lost historical value or authorization to overwrite an
occupied source save or change original damage behavior.

## New session and exact reproduction

Session `/home/rgrabowski/.ecstatica2/logs/session_20261029_174159_682` pins Debug
SHA-256 `ab3c66eccdfa1eca96c2a2185664dbe22100d37e91165c19b0e5301cf08a07e2`,
source context `38d79da2276c2baef8e0fceec46f0f7557cb8192` / `v0.3.0-dirty`,
and **90 explicit owners / 16 representation families**. Finalization records
SIGFPE, incomplete recording/inspection and retention protection.

Both bounded observation replays match all **1,381 available checkpoints** and
reproduce the fault at sequence **149,142,919**. The actual Load selects runtime
**7/COURT**, **275,083 bytes**, SHA-256
`880abe065c2fd9c5bd255550f93694216cd3e66e66888b4d7fe12aa9e84dca64`.
This remains identical to the preceding two crash inputs. Power, kills and gold
are **0** immediately after Load; no Save call or later power-value change is
observed. The user confirms this intended selection, so no menu-selection
mismatch is established.

The route is courtyard camera **132 → 343** after startup camera 1073. Original
spider **25/w_spids1**, representation **74/spider2**, attacks Joe in camera
**343**, with damage **2**, difficulty **1**, health **53** and power **0**.
The last sampled Joe is **(-20348,4096,-8576)**, representation **9**. This is
another **2 × 100 / 0** at reconstructed line **25738**, matching original
unguarded `idiv ecx` at **0x42f3e3**. Strict checkpoints remain unchanged.

Private evidence root: `.tmp/stables-spider-repeat-20261029/`. Before probes,
**68** session files and all **14** source saves were copied with size/hash
manifests. The crash bundle verifies and keeps both incomplete markers. Raw
first-probe representation value 124 used an incorrect ushort index; the second
audit correctly dereferences the resource pointer at byte **+0x11e** and reports
**74**, agreeing with inspection and original FANT/OFFSETS. Both raw logs remain.

## Original power sources and recovery limits

Original new-game instructions **0x43a656..0x43a662** assign base power **100**.
Original script opcode **0x5b**, at **0x450838..0x450864**, decodes its immediate
and writes mapped **0x47ab28**. The retained original script inventory finds two
candidate assignments: **550/dav:changewizamrep** sets **150** after changing
wizard-amulet/elder representations, and **1410/ken:flagvillage** sets **200**
after setting scene-5 flag bit 8. Extracted instructions and token references are
retained with the private evidence.

COURT's village flags are **0**, and saved representation overrides for actors
**1879/wizamu** and **1795/keldsi2** are both **-2**. These do not establish its
lost power conclusively: actor-reset paths can clear representation overrides.
The user therefore selects **150** explicitly. Gold and kills remain zero;
their lost values are not reconstructed. The original/native arithmetic fixture
already covers power 150 and damage 2 in its passing **2,184 health writes / 16
expected zero-power faults** per Debug/ASan configuration. No new combat code or
automatic zero-power normalization is added.

## Separate recovery copy

`COURT-recovery-150.ECS` has the same **275,083-byte** length, version, thumbnail,
world data and trailer. Only the 26-byte label area and the little-endian power
word at offset **274,823** may differ. The label is **COURT recovery 150**; power
changes **0 → 150**. Original serializer/loader order places this word after the
visibility records, between current music and kills. The bounded footer check
finds one matching layout, with ten status records; native Load must independently
verify that the changed field is power 150. Recovery SHA-256:
`98af361f4dc7404474120098304c6a1f7721f8f6de923669826b1e11f80c40ce`.
`recovery-manifest.json` records every changed byte and the explicit policy.

All user-visible menu slots are occupied across installed/runtime roots. A
separate human gameplay profile is prepared under
`.tmp/play-profiles/court-recovery-150-20261029/runtime/`, with the existing
visible saves copied and only its slot **7** replaced by the recovery copy.
The source `~/.ecstatica2/Saved/0007.ECS` remains unchanged. The existing F5
entry will be switched only after validation; no second human launch is added.
Future saves and recordings in this profile are human persistence and must be
protected, not treated as disposable agent-probe files.

## Verification checkpoint and failures

The first private Debug persistence process loads power 150 and completes one
Save/Load cycle, then exposes a probe assumption: its second-cycle music toggle
assumes enabled music, but COURT saves music disabled. The shared persistence
journey now enables music through actual Settings input before its first cycle
when needed; the existing second-cycle disable/restore assertions remain.
Production audio behavior is unchanged. The failed attempt remains under
`recovery-persistence-debug/` with its driver log.

Corrected validation is prepared for Debug and ASan: protected same/fresh
persistence/HUD/F3/inventory, Settings controls, natural walking to a spider hit,
normal difficulty selected through Settings, post-hit control/Quit and fresh
strict audio-on/off replay. Initial automatic approval review and its retry
timed out without executing the corrected command. The user approved another
retry, which failed at reviewer model capacity before execution. A subsequent
Debug-only request was approved and ran. These service failures are not safety
denials; their unsuccessful attempts did not execute the proposed commands.

Corrected Debug validation in `recovery-persistence-r2-debug/report.json` passes
two same-process Save/Load cycles and fresh-process restoration. Both processes
exit **0**, all six inventory observations retain power **150**, HUD/F1/F2/F3,
music enable/disable/restore, resumed controls and protected private slot-5
persistence pass. The initial failed probe remains separate.

The Debug natural walking/hit probe then stops on debugger breakpoint **-22**
at `FUN_0042faf8:26112` and raises **Unexpected native stop during menu route**.
Its `HitReturned` finish-breakpoint integration needs investigation; this is not
a new SIGFPE or a completed natural-hit result. `recovery-hit-debug/hit.result.json`
is absent. The runner exits **1**, and no probe remains running. ASan, the fresh
route recordings' strict replays and a completed recovered stables route remain
unaccepted. F5 has not been switched.

## Next-context handoff — user requested stop

The user requests stopping capacity retries and a message for the next context.
Do not start more validation or change F5 in this turn. Resume only in the next
authorized context, keeping prior runtime/rendering/audio/playthrough limits.

1. Start at README → HANDOFF → active implementation → Task 05 → this entry.
   Preserve the dirty staged/unstaged work; no commit or push.
2. The user deliberately wants COURT and explicitly chooses power **150** for
   a separate recovery copy. No further confirmation of that choice is needed.
   Original source save SHA-256 remains `880abe…dca64`; recovery is `98af36…c40ce`.
   Source saves, recordings, protection and original combat arithmetic stay intact.
3. Evidence and scripts are under `.tmp/stables-spider-repeat-20261029/`:
   `recovery-manifest.json`, `session-ledger.json`, `recovery-validation.json`,
   `recovery-hit.gdb.py`, `validate-recovery.py`, both exact replay logs and the
   preserved crash bundle. Inspect `recovery-hit-debug/hit.log` for the unexpected
   finish breakpoint and `recovery-persistence-r2-debug/report.json` for the pass.
4. Fix the private probe's return-breakpoint interaction with `TowerJourney.step`.
   The prepared runner currently reruns persistence into existing directories;
   add resume support or choose new output names before rerunning. Never delete
   or overwrite failed/passing evidence. Run the remaining Debug hit/replay and
   ASan persistence/hit/replay when the approval service works. Stop if capacity
   errors recur, as requested; do not keep retrying or weaken approvals.
5. After successful validation, point the **existing** F5 launch's `--data-dir`
   at `${workspaceFolder}/.tmp/play-profiles/court-recovery-150-20261029/runtime`
   and select **COURT recovery 150**. The profile is prepared with all visible
   save copies; none of the source menu slots is free. Protect subsequent human
   saves/recordings there and track that new root explicitly. Do not switch early.

Independent generation matches all four artifacts; no reconstructed C repair or
generator mirror is needed. The only shared test change is initially-muted
music setup in `scripts/e2_save_load_steps.py`. Documentation/syntax/whitespace
checks pass. Original 14 saves and all 68 new source-session files retain hashes.
No commit or push.

## Authorized continuation — life assessment and completed validation

This continuation supersedes the stopped checkpoint above. The user first asks
whether the save actually stores life correctly, since the crash happens on a
hit. Read-only decoding follows the original-format resource records, active
actor section and cached actor table. In both the preserved original COURT and
the power150 copy, Joe's active life word at file offset **143,928** is **53**,
maximum life is **100**, and cached life at **148,991** is also **53**. The earlier
Debug round-trip save independently contains life53 at **114,758** and cached
life53 at **119,821**. Native same/fresh restoration agrees. The private decoder
and result are `continuation-r3/assess-save-life.py` and
`continuation-r3/save-life-assessment.json`.

The complete current save writer matches executable original x86 in **24**
synthetic worlds, including active/cached life, both thumbnail branches, timers,
attachments and trailer. Its retained harness/provenance are under
`continuation-r3/save-writer-native.c*`. The sandboxed attempt is blocked by
SIGSYS; the authorized native boundary passes. This memory-stream fixture does
not itself establish menu behavior; real-menu persistence below does. There is
no evidence of a life-serialization defect in this checkpoint or current writer.
The available evidence cannot prove the live value before the historical save
was created. The old file predates the previously documented scalar-ownership
repair; **power0** is separate from life53. Original combat divides by power
before writing reduced life. Neither life nor combat arithmetic is changed.

### Private probe repairs and retained failures

The first new attempt, `continuation-r3/hit-debug/`, replaces the function-finish
observer with a post-health-write line observer, but `TowerJourney.step` again
rejects that observation stop. `continuation-r4/` adds a private journey that
explicitly consumes only its two owned breakpoints in `FUN_0042efdc`, checking
pending target identity and exact health arithmetic. Signals, unrelated stops,
exits and bounded-loop exhaustion still fail. Its natural Debug hit and normal
Quit pass, but strict replay diverges at sequence **21,973**, checkpoint **11**:
shared input helpers injected an extra host pump, rather than letting native
execution reach it. The logs and complete capture remain unchanged.

The final `continuation-r5/recovery-hit.gdb.py` queues SDL keys, motion and button
events for the normal native pump; it never injects host-pump, cursor-service or
presentation calls. Display/inventory checks remain in the separate persistence
journey. Its recording executes in an isolated Python namespace and uses the
explicit observation-stop handling. No production file is repaired.
`continuation-r5/validate-recovery.py` reuses the completed Debug persistence
report only after checking completion, native exits and binary SHA-256. Completed
hit/replay stages can resume; exclusive log creation and fresh copy destinations
prevent overwriting earlier attempts. Failed stages require a new output root.
Use this final runner, not the earlier root-level runner, for continuation.

### Final bounded acceptance

Final report: `continuation-r5/validation.json`. Debug pins SHA-256
`ab3c66eccdfa1eca96c2a2185664dbe22100d37e91165c19b0e5301cf08a07e2`;
ASan pins `ce12e56dcebe60f9ed765870b1be7ede7715cb41f9581d9fad2f20e2d6ffea50`.

- Debug reuses the already passing protected same/fresh persistence report at
  `recovery-persistence-r2-debug/report.json`. Fresh ASan
  `continuation-r5/persistence-asan/report.json` passes both same-process cycles
  and fresh-process restoration, HUD/F1/F2/F3, Enter/Escape inventory, music
  enable/disable/restore, resumed input/attachments and normal Quit. Both ASan
  processes exit **0**; all six inventory observations retain power **150**.
  Actor-field comparisons include Joe's life **53** and maximum **100**.
- Both configurations naturally load recovery slot7, walk toward spider
  **25/w_spids1**, and observe computed damage **2**, normal difficulty **1**,
  power **150**. The observed Debug write is life **52 → 51**; ASan is
  **53 → 52**, matching integer **2 × 100 / 150 = 1**. These are independent
  captures, not identical timing or complete damage-event coverage. Living Joe,
  menu cancellation, resumed movement and confirmed normal Quit pass.
- Fresh strict replay with audio **on** and **off** completes **60 checkpoints**
  per configuration, four successful replays total. Debug ends at sequence
  **208,784,212**; ASan at **70,472,624**. Strict checkpoints are unchanged.
  There is no SIGFPE or AddressSanitizer diagnostic in these final runs.

Only after those checks, the existing F5 launch gains `--data-dir` pointing to
`${workspaceFolder}/.tmp/play-profiles/court-recovery-150-20261029/runtime`.
Choose **Load → COURT recovery 150**; no second human launch or automatic-load
behavior is added. Its slot7 still hashes to `98af36…c40ce` and begins at the
recovery checkpoint, life53/power150, rather than the end of an agent route.
`human-persistence.json` beside the runtime marks the new root as human gameplay
persistence: protect future saves/recordings and never treat them as disposable
agent outputs. The original source slot7 remains `880abe…dca64`.

The two existing launch contracts now allow the optional `--data-dir` argument
while keeping host probes on their private roots; no human profile argument is
forwarded into agent probes. All **67** suite contracts and **31** bounded
developer-launch/logging cases per Debug/ASan configuration pass. Runner resume,
Python/generator syntax, whitespace and the **301-document** README tree pass.

Independent generation again matches all four artifacts. The final continuation
records source/profile preservation and checks in `continuation-r5/`; all
**14** source saves, **68** original-session files and **10** prepared-profile
save files retain their sizes/hashes. Staged changes remain byte-identical.
No production C, generator, original save or combat change, commit or push occurs.

These results qualify the bounded recovery route and current persistence, not
historical lost power/kills/gold, complete stables traversal, fresh boots pickup,
acid protection/expiry, ladder interaction, human listening, full visual review
or extended playthrough. Continue human play through the existing F5 launch and
link the next actual Load/session to this explicit recovery profile.

## Later F5 argument-order correction

The [subsequent ladder investigation](stables-ladder-interaction-recovery-2026-10-29.md)
finds that the profile argument added here followed `--run-recon`, where the
runtime stops parsing global options. Private validation above used the correct
order and remains valid; the human F5 override did not yet take effect. The
ladder continuation corrects the existing launch to put `--data-dir PATH` first,
updates its two launch contracts, and verifies both builds without changing any
occupied save. Use that later entry for the actual post-recovery session/root
and ladder acceptance.
