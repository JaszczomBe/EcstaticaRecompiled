# Invalid COURT save retirement and persistence audit — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owners: [Step 12 Task 05](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md)
and [Step 10 Save/Load](../../implementations/playable-sdl-runtime/steps/step-10/step-10-recover-game-save-load.md).
Evidence: `.tmp/save-state-integrity-20261029/`. No commit or push.

## User correction and evidence policy

The user rejects the guessed power150 recovery as an acceptable progression
baseline and requests inspection/repair of Save/Load, removal of the invalid
save and recovery tooling, and explicit documentation/handoff requirements.
This supersedes earlier authorization to preserve/use the COURT recovery.

**Malformed, corrupted or manually patched saves and their descendants MUST NOT
be used to decompile/reconstruct game functionality or accept gameplay
progression.** Inspect invalid state only to diagnose persistence faults. Repair
the implementation and verify from fresh gameplay or an unmodified original
save. A patched file that survives saving/loading still has unknown historical
state; a round trip cannot reconstruct lost power, counters or progression.
Synthetic original-code comparisons remain labelled fixtures, not gameplay proof.

The [COURT experiment](court-recovery-150-and-repeat-spider-2026-10-29.md) stored
life53/100 correctly, but power0 was invalid and historical power/kills/gold were
unavailable. Selecting150 only supplied a guessed divisor. Its later hit/replay
and persistence results are withdrawn as gameplay acceptance. The
[ladder repair](stables-ladder-interaction-recovery-2026-10-29.md) retains its
independent original-x86 signed Space proof and generator mirror; its later
COURT150-derived traversal/landing checks no longer qualify progression or
persistence. Requalify both ladder directions from valid progression.

The source fresh-game ladder recording had already reached life0 while remaining
controllable. Its reproduction is diagnostic history, not valid ladder gameplay
acceptance; the zero-life control issue remains open.

## Save/Load inspection and additional defects

The earlier repair already makes power/kills/gold share original mapped storage
across gameplay and serialization. The current audit adds unconditional live
statistics comparison to the real-menu persistence journey, including health
through its existing active-actor checks. Fresh-game power must start at100;
a zero/negative-power seed cannot qualify these gameplay persistence checks.

Initial Debug/ASan writer, stream, word/matrix and inventory comparisons pass.
Fresh and unmodified-g3 menu round trips also pass their old assertions. However,
read-only decoding exposes a remaining mismatch: fresh gameplay uses Medium
**difficulty1**, while its file stores stale mapped **difficulty0**. Difficulty0
is a valid Easy setting; the defect is disagreement with the actual live setting.
The poison-duration scalar has the same split ownership. Previous checks missed
this because their harnesses aliased exported and mapped values, or did not
compare those live fields. The initial reports remain under the evidence root;
`writer-before.log` records the strengthened fixture's expected pre-repair byte
mismatch and SIGABRT. This was a test assertion, not a game crash or review error.

Original disassembly confirms:

- Writer **0x4542e4/0x4542f0** reads poison duration **0x47ab2c** and difficulty
  **0x47a4a4** into the existing signed-word serialization sequence.
- Loader **0x454dba/0x454dc7** restores the same gameplay fields after `cwde`.

The reconstructed writer now reads the live duration/difficulty exports for
those two entries. The loader restores those exports from the decoded original
slots, as the existing music boundary already does for its live export. The
format, field order, signed-word behavior and damage formula remain unchanged.
There is no save-patching, automatic normalization or zero-divisor guard in the
runtime. Both changes are mirrored in `GenerateRecon.js`; the earlier ladder
repair and unrelated changes remain intact.

## Fresh verification from valid seeds

Final evidence is under `after-repair/`, especially `validation.json` and
`stored-state-validation.json`. Debug SHA-256:
`f1bb7a02c75889a2abe0494b28837853ece24e6839bfeb77e6700fe3fd01ebb3`;
ASan SHA-256:
`6109bb598456b4d196b8cd972c750af1a803c03e25fa62731496a6eb6abad070`.

Each configuration passes:

- **24 complete original-x86 writer byte comparisons**, retaining separate live
  duration/difficulty and deliberately stale mapped storage, plus **81 original
  scalar-loader comparisons**, including signed-word extremes and live-export
  restoration. These use synthetic memory streams only.
- Existing original word/matrix, hosted-stream and inventory comparisons.
- Input-only real-menu persistence from **fresh gameplay** and untouched installed
  **2/g3**, SHA-256 `1c884e338a2d746d3a7a53bc1ccde62e4417e768fd9a34f8d2cbc124674b75fd`.
  Both routes save twice into private originally empty slot5, change difficulty
  through Settings **Medium1 → Hard2 → Easy0**, restore in the same process and
  a separate fresh process, compare active actors/attachments and all five
  statistics, check inventory/music and resume movement/attacks. All **eight
  native processes exit0**, with no ASan diagnostic.
- Read-only decoding of the final files agrees with the live Save snapshots:
  fresh life90/max100, power100/kills0/gold0; g3 life171/max300,
  power200/kills574/gold-counter15095. Both configurations finish with the
  deliberately selected difficulty0 and poison-duration0. Active/cached life
  agree. These observations describe the private tests, not a replacement human
  checkpoint.

All four SDL/X11 Debug/ASan builds and four-artifact scratch generation parity
pass. All **67 suite contracts**, **31 developer-launch/logging cases per
configuration**, Python/generator syntax, whitespace and the **303-document**
README tree pass; logs are retained beside the results. No full gameplay suite or valid-seed
ladder traversal is claimed by this audit.

## Removal, quarantine and preservation

`save-audit.json` records the read-only layout/field inspection. The explicit
hash-checked `retirement-plan.json` and `retirement-completed.json` record each
removed or renamed path. No source recording or investigation-context file is a
target. The retirement removes **159 save copies**:90 copies of invalid COURT,
26 copies of the guessed recovery and43 known descendants. This includes active
`~/.ecstatica2/Saved/0007.ECS`, the standalone `COURT-recovery-150.ECS`, profile
slot7, historical invalid snapshots and private recovery/ladder endpoint saves.
The old save hashes remain diagnostic metadata, not reusable game state.

**18 private runners** tied to the retired recovery are removed. There was no
production save-patching workaround to remove. The single F5 launch returns to
`--run-recon`, and its two contracts again require that ordinary argument list.
The old profile's metadata and evidence roots explicitly mark it retired; human
logs and recordings inside it remain preserved.

The audit also identifies runtime **5/123** and **6/DFGSDRG** with the old
zero-power/zero-counter state. Their **176 copies** are renamed to
`.ECS.invalid`, including the two active default-runtime slots, so they cannot
appear in Load. Their original bytes remain available for persistence diagnosis;
they and their descendants cannot qualify gameplay. This also invalidates
historical progression/persistence acceptance from those seeds in the
[tower](tower-key-progression-recovery-2026-10-28.md),
[castle](inner-castle-crash-and-presentation-recovery-2026-10-28.md) and occupied-slot
[inventory](enter-inventory-menu-recovery-2026-10-28.md) routes; their journals and
owning tower/castle tasks carry explicit requalification notices. Independent
original-code proof and genuinely fresh/untouched-original checks remain scoped
evidence. No value is invented to repair the old saves. The unrelated valid runtime quick-save retains its original hash,
as do installed reference saves used by the probes.

Some historical snapshot directories were owner-read-only. The first retirement
attempt stops on that permission boundary after117 authorized deletions. The
resume verifies every remaining hash, temporarily grants owner write permission
only to the affected parent directories, performs the listed operations and
restores their original modes. `retirement-completed.json` verifies all targets
are absent or quarantined. This was a filesystem permission issue; no approval
capacity error occurred.

The staged patch remains byte-identical to `initial-staged.patch`; unrelated
worktree changes are retained. Documentation current-state summaries and prior
handoffs explicitly revoke the old recovery instructions and acceptance. Earlier
journals remain historical records with the superseding policy clearly marked.

## Next continuation and limits

Use the single normal F5 launch. Start a fresh game or verify an untouched
original checkpoint and record its loaded slot/hash/build/session chain. Repeat
the stables/kitchen ladder down/up and eligible landing persistence from that
valid progression before claiming acceptance or advancing dependent tests.
Do not select a retired profile or re-create a patched COURT checkpoint.

Current evidence does not prove arbitrary original progressions, active-poison
native Save/Load, malformed-file recovery, fresh boots/acid lifetime, other
ladders, full animation/composition, zero-life control or long-session fidelity.
Nonzero duration and signed restoration have bounded original-code fixture
coverage; a natural active-poison route remains separate. No historical missing
statistic or progression is recovered by this audit.
