# Object Behavior, Rendering and Interaction Handoff — 2026-10-29

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


## User selection

After the `v0.3.0` milestone, the user selected remaining original object behavior
(for example anti-acid boots), rendering and interactions (for example ladder
usage), with additional stability checks and a gameplay playthrough across
several Save/Load sessions. They requested updated handoffs and a short message
for the next context. This turn changes documentation only; it does not establish
that either example is broken, identify their actors or implement a repair.

Start at README → HANDOFF → active runtime implementation →
[Step 12 Task 05](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md).
That task coordinates the continuing playthrough; Tasks 02 and 04 retain their
specific variant/acid and castle evidence. The user authorizes the navigation
change in `docs/HANDOFF.md`: its old sound-task pointer is stale. Current
execution state and new evidence remain in the implementation/task/journal,
rather than becoming another changing state ledger in the durable handoff.

## Baseline

- Repository: `/home/rgrabowski/Work/EcstaticaRecompiled`.
- Branch: `linux-e2-reconstructed-runtime`.
- Observed clean HEAD: `38d79da2276c2baef8e0fceec46f0f7557cb8192`.
- Annotated local tag `v0.3.0` points to that commit. Preserve it; do not move or
  publish tags, commit or push unless separately requested.
- Original external executable/data: `/home/rgrabowski/Games/Ecstatica2/`.
- Normal human investigation: the single **Ecstatica Recompiled** F5 launch,
  SDL/i386 Debug, with automatic recording, inspection and pinned executable.
  See [debugging usage](../../debugging.md) for finalization, protection and bundles.

The [music journal](music-recovery-2026-10-29.md) owns the last implementation:
91 GM sequences compared against the original DLL, 960 loader entries, software
MIDI output, protected persistence and strict replay. The
[sound journal](game-sounds-recovery-2026-10-29.md) owns original sample/buffer
recovery for 404 assets. These are bounded results; preserve their listening,
event, transition and device-loss limitations. Do not restart completed audio
implementation as the next priority unless a new object route exposes a dependency.

## Next work

For the first user-reported session, identify the exact pinned build, loaded save
and route. Preserve the relevant session and save snapshot before investigation;
copying the current file for a slot does not prove it is the version loaded by
an earlier recording. Read-only original mapping for boots/ladders is possible
before a new session report; do not invent an unavailable route or reproduction.

For anti-acid boots, recover actual original acquisition/equipment state,
hazard/resistance/damage eligibility and visible ownership, including persistence.
An inventory icon is not proof that protection works, and the handoff does not
assume the original grants permanent immunity. For ladders, recover the original
interaction conditions, controls, action/animation, movement/collision, camera
handoff and dismount. Establish original Save eligibility around traversal.

Use disassembly/Ghidra and bounded original-code comparisons to distinguish a
reconstruction mismatch from an original restriction or defect. Repair the
smallest proven error, mirror reconstructed C changes in `GenerateRecon.js`,
verify generated parity and qualify fresh Debug/ASan behavior and pixels.
Address demonstrated crashes/blockers before continuing the dependent route.
Do not force flags, grant protection, teleport through a ladder or alter damage,
physics or rendering merely to meet an expectation.

## Save/Load session continuity

Append a dated record for each supplied human session, linked from Task 05 and
the journal index. Keep the following together:

| Record | Required evidence |
| --- | --- |
| Session identity | Absolute session path/ID, pinned executable hash, source/build context, exit/signal and capture completeness |
| Source checkpoint | Loaded slot/label/location, preserved save snapshot and size/SHA-256, preceding session/checkpoint link |
| Route and findings | Cameras/objects/actions when established, items/equipment, expected versus observed behavior and first failure |
| Recovery | Original-code proof, scoped generator-mirrored changes, failed attempts and fresh verification bounds |
| Continuation | Last safe save/checkpoint, state expected after Load, unresolved blockers and next bounded action |

At this handoff, no new post-milestone session is identified and no boots/ladder
fault is established. The first route row is intentionally pending. The next
context should incorporate the user's actual session and Save/Load observations,
then keep this chain current rather than assuming a new game or uninterrupted
process for each turn. Record human playthrough separately from controlled or
isolated diagnostic acceptance.

The newest five sessions survive ordinary retention, but older clean-exit
sessions can later be removed. Preserve relied-on sessions with a private copy
or investigation bundle before cleanup, including pinned executable, recordings,
inspection and matching save snapshot. Retain crash protection markers and
incomplete tails; do not manufacture complete recordings or weaken strict replay.

## Protected saves and prior evidence

Read-only inventory for this documentation turn is in
`.tmp/object-behavior-handoff-20261029/saves-before.json` (14 installed/runtime
save files, with size and SHA-256). It is a baseline, not permission to overwrite
anything or a substitute for re-scanning occupancy after human play.

- Runtime `~/.ecstatica2/Saved/`: occupied **0005 (123), 0006, 0007, 0009**.
- Installed `Ecstatica2/Saved/`: occupied **0–4, 8, 9**; **5/6/7** currently
  contain the four-byte empty marker. Installed and runtime slots with the same
  number are different files; normal runtime reads take precedence.
- Agent persistence/reproduction uses private game/runtime copies and only
  freshly confirmed empty private slots. Never overwrite an occupied user save,
  reuse a historical probe's free-slot assumption or overwrite quick-save 9.
- Preserve `~/.ecstatica2/logs/session_20261028_173846_961/`, its pinned crash
  evidence and incomplete replay, `.tmp/inner-castle-20261028/preserved`,
  `.tmp/enter-menu-20261028`, `.tmp/game-sounds-20261029` and
  `.tmp/music-20261029`. The music journal records 8,486 unchanged protected
  files at that milestone; future sessions require updated inventories.

Keep all prior visual/gameplay/persistence/audio limits: equipped armour and full
gate/effect composition, unresolved door translucency, natural acid-room
lifecycle, wider item/interaction coverage and the incomplete castle recording.
The [castle recovery](inner-castle-crash-and-presentation-recovery-2026-10-28.md)
and [inventory recovery](enter-inventory-menu-recovery-2026-10-28.md) retain their
specific evidence. Historical crashes already repaired are not new failures;
previous failed live-combat persistence remains a failure, distinct from passing
isolated noncombat checks.

## Verification for subsequent repairs

Use bounded ordinary-input Debug/ASan probes with private outputs and recording
off unless explicitly testing recording/replay. Test interaction outcomes and
rendered ownership, affected same/fresh-process Save/Load and resumed controls.
Retain HUD/F1/F2, F3, inventory, menus/Quit, original sound/music and strict replay.
Run relevant original-code checks, affected SDL/X11 builds, generator parity and
documentation checks, with new acceptance recorded per repaired path.

This documentation handoff adds no runtime/build/gameplay acceptance. Only the
documentation tree, whitespace and unchanged save inventory are checked here.

## Handoff verification

`python3 scripts/check-docs-tree.py --update` followed by the check without
`--update` passes: **297** Markdown documents connect to README. `git diff --check`
passes. All **14** inventoried installed/runtime save files retain their sizes
and SHA-256 hashes (`.tmp/object-behavior-handoff-20261029/saves-check.json`).
Only documentation changes; no runtime probes/builds, commits, pushes or tag
changes are performed for this handoff.
