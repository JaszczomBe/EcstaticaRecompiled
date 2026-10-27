# Recover Functional Game Save And Load

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: functional persistence accepted; menu refinements verified within recorded bounds
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-28

## Goal

Save actual gameplay through the original menu and restore it in both the same
process and a fresh process, using recovered original serialization and resource
reconstruction. Session logs, input recordings and save-slot previews are separate
capabilities.

## Current recovery

[Writer recovery](tasks/task-02-recover-original-save-writer.md) and
[restore/menu dispatch](tasks/task-03-recover-original-restore-and-menu-dispatch.md)
are implemented. The [dated journal](../../../../journal/entries/game-save-load-recovery-2026-10-27.md)
owns the original ABI/format map, Debug/ASan fixtures, real repeated menu
Save/change/Load, fresh-process loading, resumed animation/input/attack and sword
attachment evidence. Native opening saves have no active timers; nonempty timer
restoration is verified against original loader code. Missing/truncated failures
are observed at their source-backed boundaries; generic fatal cleanup and full
original progression compatibility remain unqualified. The source observations
below retain their **historical v0.2.0** baseline meaning.

The user requires preserving occupied saves. Installed slots **0–4, 8, 9** are
occupied; **5–7** are empty. Agent trials use private copies and originally free
slots only; quick-save slot **9** must not be used by tests. All writes route
through writable runtime storage under `--data-dir/Saved`.

## Menu refinement follow-up

The user accepted functional save/load and requested saved images, automatic
menu dismissal after Load, and removal of a flickering preview-sized gameplay
patch after cancelling. [Task 04](tasks/task-04-refine-save-load-menu-presentation.md)
and its [journal](../../../../journal/entries/save-load-menu-refinements-2026-10-27.md)
own the original-backed presentation repair and fresh Debug/ASan evidence.
Previews now use both hosted menu pages without changing physical game pages;
successful Load resumes play automatically. Cancellation keeps its parent-menu
route. The focused probe compares pixels and observes automatic dismissal as
well as its existing state/attachment/input checks.

## Original menu layout follow-up

The supplied original/recompiled screenshots exposed a wrong slot-panel size,
misplaced title and provisional uppercase font. [Task 05](tasks/task-05-recover-menu-layout-and-font.md)
and its [journal](../../../../journal/entries/menu-layout-and-font-2026-10-28.md)
own the original geometry/font recovery and the requested 160×120 preview display.
The saved image format remains 80×60. The final focused suite passes 28/28
Debug/ASan checks, including original geometry/font/edit-state comparisons,
same/fresh-process restoration, enlarged previews and preserved installed saves.
The three-stage menu sweep has no failures, with its existing skips explicit.
Retain broader gameplay/rendering limits; sounds remain next in the selected order.

## Next Context Handoff

The user accepted Joe's corrected appearance and animation, then the recovered
enemies. Subsequent play exposed the dropped-potion/resource-index failures and
the tower actor-eviction failure; their repairs are committed. The selected next
work is **functional game save/load → game sounds → music**. Investigation
session saving, replay and the gameplay regression-suite implementation are
closed milestones with recorded minor gaps deferred. Do not restart those
projects as prerequisites to persistence.

Baseline branch: `linux-e2-reconstructed-runtime`, commit
`ae54e6f8e4dcb3570625c4780cfaf74ca252ecd1`, annotated tag **v0.2.0**. Both
**v0.1.0** (commit `1f81f76c3c5e4698c382cf0628a2be4f64f633c9`) and **v0.2.0**
were pushed to `origin` and verified. The worktree was clean before this handoff;
these documentation changes are subsequent work. Check actual status before
editing and preserve unrelated changes. This handoff does not authorize another
commit, push or tag change.

Start with [Task 01: map the original persistence contracts](tasks/task-01-map-original-save-load-contracts.md).
It owns the first bounded action and evidence. Continue with separate writer,
restore and native round-trip tasks as those contracts become concrete; this
step owns completion of the whole persistence milestone.

## Historical v0.2.0 Persistence Boundary

The following are source observations at v0.2.0, not new gameplay tests:

| Entry or implementation | Known state and next inspection |
| --- | --- |
| `FUN_00453920`, original `0x453920..0x4544a4` | Save writer is replaced by a return-zero no-op; the original body remains in `E2Recomp/src/E2Recomp_decompiled.c` and the external executable |
| `GenerateRecon.js`, patches near lines 762 and 4369 | **Two** replacements emit that no-op; restoring only one lets the other discard the repair during regeneration |
| `FUN_004544a4`, original `0x4544a4..0x454fe4` | Large load routine remains decompiler-shaped, with unresolved register inputs; the function has no direct C caller in the current reconstruction |
| `FUN_00415d40` | Quick-save key flag `DAT_004c39af` calls the writer; menu states 3/4 open Save/Load requesters, without established serialization/restore dispatch |
| `E2R_RequesterHandleMouseClick` | Slot callbacks `LAB_0043fadc` / `LAB_0043fb58` currently select `_DAT_0064353c`, redraw and return; reconstruct their original confirm/name/overwrite/dispatch semantics before connecting them |
| `FUN_0043fea4`, `FUN_0043c1b8` | Ten-slot labels and 80×60 thumbnail reads have original-code evidence; they are not gameplay persistence |
| `FUN_00417308`, `FUN_004173c8`, `FUN_00454fe4`, `FUN_00455034` | Starting points for word I/O and matrix serialization/restore; audit actual register, stream and byte-order contracts |
| `FUN_0045eb05`, `FUN_0045ec6c`, compatibility `CreateFileA` | Audit binary open/read/write/close, error and path ownership with their actual callers |

The label/preview evidence establishes a 26-byte name, a two-byte version and
an 80×60 column-major thumbnail prefix in installed saves. Recover the remaining
format and version branches from the original writer/reader; do not infer the
save format version from FAN version 55. Existing `Saved/*.ECS` files include
named and CR-prefixed empty slots and must remain read-only reference fixtures.

The current host entry changes the working directory to `--game-data-dir`.
Compatibility `CreateFileA` ignores its creation argument and opens generic
writes as `wb+`. These are audit starting points, not established save-specific
requirements. Before enabling the writer, route writable save storage through
the existing runtime-data boundary (`--data-dir`, normally `~/.ecstatica2`) and
establish consistent label/preview/read/write lookup. Keep platform paths and
host file semantics in compatibility/runtime layers. Agent trials use isolated
scratch data and private save copies, never overwrite installed game saves.

## Implementation Sequence

1. Trace original callbacks, writer, reader and stream helpers. Record register
   ownership, slot/name handling, version/order/terminators, serialized fields,
   resource identities and reconstruction steps. Produce bounded original-code
   comparisons and an observed first native failure.
2. Recover writer and required binary file services. Verify actual bytes, close
   and failure results, slot metadata and preview. Mirror every reconstructed C
   repair in the generator, including removal/replacement of both no-op patches.
3. Recover loader and callback dispatch. Rebuild original resource references,
   actor/attachment relationships, scripts/timers and scene state according to
   the format. Distinguish serialized fields from state the original recreates.
4. Validate a real menu save → continue and change state → load round trip, then
   loading that save from a fresh process. Add focused Debug/ASan regressions to
   the existing suite and record remaining compatibility limits.

## Acceptance Criteria

1. Actual gameplay Save writes an original-format file in writable runtime
   storage; slot/name/overwrite/cancel behavior follows original evidence.
2. Load restores the saved player location, health, equipment and relevant world
   progression as supported by the recovered format. Tests record which fields
   are serialized and which are reconstructed, including attachments and timers.
3. Same-process and fresh-process loading both resume input, animation, collision,
   camera traversal and subsequent interaction. Repeated save/load cycles work.
4. Empty slots, missing/truncated/unsupported saves and file failures have observed,
   source-backed behavior. Record destructive-load boundaries and unresolved
   recovery limits instead of inventing success or state rollback.
5. Original-code fixtures, relevant existing regressions and bounded native
   Debug/ASan checks pass; rebuilt source has exact four-artifact generation
   parity. Menu opening, a new filename or matching thumbnail alone cannot pass.

## Verification And Working Rules

Use the single **Ecstatica Recompiled** F5 launch for human investigation. It
already enables original player/enemy bodies. Agent probes have explicit input,
timeout, isolated output and recording-off policies; observe gameplay state
rather than assigning health, coordinates or completion flags to manufacture a
round trip. A low-level explicit serializer/resource call is a labelled fixture,
not a real menu-route result. Recover only the blocking failure family at a time.

Use `scripts/e2_original.py` and the external executable
`/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` for bounded original comparisons.
Original assets stay external. Relevant existing checks include
`check-e2-menu-contracts.py`, `check-e2-ddraw-surfaces.py`, actor/attachment/timer
fixtures and the suite's menu/startup/movement/interaction cases. The current
`scripts/e2_menu_steps.py` LoadDialog/SaveDialog checks explicitly report
`state_round_trip=False`; retain their distinction when adding persistence tests.

Build SDL Debug/ASan first, then the affected X11 configurations. Verify generator
parity using `scripts/check-e2-generation-parity.py --output <new-directory>`.
Update this step, its task and the journal with new results; run the documentation
tree update/check. See the dated journal for fresh acceptance and explicit limits.

## Evidence To Carry Forward

- [Player recovery and user acceptance](../../../../journal/entries/player-model-and-animation-2026-10-27.md)
  and [enemy recovery](../../../../journal/entries/enemy-model-and-animation-2026-10-27.md): accepted character direction; equipment polygons, original HUD and exhaustive animation coverage remain separate.
- [Resource index and dropped potion](../../../../journal/entries/enemy-play-crash-and-dropped-potion-2026-10-27.md): all 2000 action offsets and 488 representation names compared with original data; bounded consumption evidence and failed routes retained.
- [Tower eviction](../../../../journal/entries/tower-actor-eviction-crash-2026-10-27.md): 163 original-code cases per normal/ASan mode; final Debug matches 1088 checkpoints then diverges from the recorded fatal requester. ASan diverges earlier at checkpoint 887; further human tower play remains unqualified.
- [Earlier menu/preview recovery](../../../../journal/entries/headless-regression-sweep-2026-10-27.md#slot-previews-and-actual-directdraw-storage): binary slot reads and physical surface ownership; functional loading was explicitly excluded.

All four builds and generation parity passed for v0.2.0. The full gameplay suite
has not been rerun with every latest character/crash repair. Historical full-suite
success is not current acceptance. The prior broad suite-contract run retained
a descendant-cleanup timing failure; the tower pass verified its three affected
catalogue contracts and both new eviction suite cases. Keep these limits visible
without reopening the closed tooling milestone.

## Usage Budget

No explicit token/time budget. Keep work bounded by the active failure family;
do not expand into audio, music, renderer polish, packaging or 64-bit execution.

## Change Log

### 2026-10-27

1. Created the save/load continuation handoff after tagging v0.2.0.
2. Recovered original writer/loader/menu dispatch and protected runtime save storage; added original-code and real menu Debug/ASan checks. Fresh evidence and failure limits are linked above.
