# Game sounds continuation handoff — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 05 Task 04](../../implementations/playable-sdl-runtime/steps/step-05/tasks/task-04-recover-original-game-sounds.md).

## User selection

After the original Enter inventory/status recovery, the user selects restoration
of **game sounds** as the next focus and requests documentation for a fresh
context. The next order is **game sounds → music**. Remaining object, route and
visual qualifications stay open; they are not prerequisites that override this
selection. This turn updates documentation only. The continuing context should
proceed with original-backed investigation and implementation of the selected
task; actual audible sound, not silent stub success, is the objective.

Step 05 remains the audio entry point. Its original tasks cover startup mapping,
backend ownership and first-buffer verification. New Task 04 owns the end-to-end
sound objective and supersedes the earlier first-buffer-only stopping rule.
The handoff anchor changes only to point a blank context to this new owner;
current facts and evidence stay in the implementation, task and journals.

## Committed baseline and preserved acceptance

At inspection, the index/worktree are clean on `linux-e2-reconstructed-runtime`,
HEAD **`a1898a8745e8d42cec9741d25ca37433db2a3a57`**, the inventory/status recovery
commit. Recheck actual status next time, preserve later changes and do not commit
or push without a new instruction.

The [inventory recovery journal](enter-inventory-menu-recovery-2026-10-28.md)
records original Enter/Escape, artwork/HUD/icons, mapped gold/kill/power ownership,
99% completion cap and five-digit numeric truncation. Historical acceptance:
four SDL/X11 builds, four-artifact generation parity, 22 focused checks, 67 runner
contracts, twelve clean native processes and ten strict replay variants. All
199 protected files retained their hashes. These results do not establish audio
behavior and must be refreshed where sound changes affect them. Human screenshot
review, low-mode/planar play and natural hourglass lifetime remain open.

The [inner-castle recovery](inner-castle-crash-and-presentation-recovery-2026-10-28.md)
retains source-backed node/pose/clipping repairs and 76 selected original owners.
Its source recording is incomplete despite all 3,190 matching prefix checkpoints.
Uninterrupted extended route, equipped-armour human review and complete gate/
effect composition remain open. Preserve unresolved tower-door appearance and
other object/acid acceptance limits; sound work does not close them.

## Current source leads and first action

Read-only inspection confirms `DirectSoundCreate` and `E2R_DS_CreateSoundBuffer`
in `E2Recomp/reconstructed/E2Recomp_stubs.c` install generic/no-op behavior with
a shared dummy buffer. `SIMD_*` music functions are also stubs. These are source
observations, not original-contract proof or an explanation of every silence.

The task records precise leads: startup `FUN_004594a0`, node/event wrapper
`FUN_0042fce0`, scheduling wrapper `FUN_00413ea4`, archive/resource loading
`FUN_00451a54`, buffer playback `FUN_00458c24`, `mmio*` compatibility, and the
host audio boundary to define. The existing generator already repairs several
sound-related arguments; preserve those repairs while recovering downstream
contracts. The installed `Files/ECSTATIC` archive and actual original file-opening
paths need inspection. Missing-sound diagnostics are Trace-level; silence in an
Info/Debug log is not evidence that requests were absent.

First refresh protection hashes and trace one naturally reached game sound from
original event/ID through resource lookup, decoding and buffer submission in a
bounded Debug probe. Recover original arguments/format/ownership and prove a
reconstruction mismatch before changing behavior. Mirror reconstructed repairs
in `GenerateRecon.js`; preserve DirectSound-shaped game calls and keep host/SDL
services below compatibility boundaries. Do not infer each sample's format from
the primary device format or blanket-enable missing archive paths.

Task acceptance includes original-x86/resource and lifecycle comparisons,
measurable PCM/output evidence, bounded Debug/ASan gameplay and stop/overlap/toggle
checks, separate human audible F5 review, protected persistence, HUD/F3/inventory,
headless operation and strict recording/replay. Backend callbacks must not drive
game state, RNG, clocks or deterministic checkpoints. Music is later work;
shared initialization dependencies can be investigated without claiming music
playback acceptance.

## Protection and workflow

Preserve occupied runtime **slots 5/123, 6, 7 and 9**, installed saves and crash
session `~/.ecstatica2/logs/session_20261028_173846_961/`, including its pinned
binary/source/recording. Keep `.tmp/inner-castle-20261028/preserved/` and
`.tmp/enter-menu-20261028/`, particularly its `final-summary.json` and protection
inventories. Refresh actual occupancy before any write. Use private copies and a
verified empty private slot; never overwrite source saves or normalize old values.

Normal human investigation uses the single **Ecstatica Recompiled** F5 launch.
Agent probes use explicit time/input bounds, private outputs and recording off
except an explicit bounded recording/replay check. Preserve original behavior,
including possible defects; require a proven reconstruction mismatch before a
repair. No explicit usage/token budget is requested.

## Handoff verification

Only documentation changed. `python3 scripts/check-docs-tree.py --update` and
its subsequent check without `--update` pass: **292** Markdown documents connect
to README.md with valid parent/local links. `git diff --check` also passes.
No new audio implementation, native probe, build or audible acceptance is claimed.
No commit or push was made.
