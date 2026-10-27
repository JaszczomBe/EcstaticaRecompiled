# Map Original Save And Load Contracts

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
<!-- /docs-tree:parent -->

Status: complete; original contract map and subsequent implementation evidence linked
Parent Step: [Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-27

## Goal

Establish the original menu-to-file-to-world contract and the first bounded
counterexample before restoring the disabled save writer and unrecovered loader.

## Initial Bounded Action (v0.2.0)

Read the [parent handoff](../step-10-recover-game-save-load.md), then compare
original `0x43fadc` / `0x43fb58` slot callbacks and their surrounding requester
code with `E2R_RequesterHandleMouseClick` and `FUN_00415d40`. Trace calls into writer
`0x453920..0x4544a4` and reader `0x4544a4..0x454fe4`, including actual slot,
label, stream and return arguments. Start from `E2Recomp/src/E2Recomp_decompiled.c`
and original executable bytes; generated save code is a deliberate no-op.

Record a compact original-address/ABI/format map and a bounded original-code
fixture for the first useful leaf or dispatch contract. If observing native
Save first, use private save copies and an isolated writable destination. Capture
the actual missing dispatch/no-op boundary without treating a selected slot as
a completed save. Use the result to create the next narrow writer/restore tasks
under Step 10 and continue the selected persistence milestone when authorized.

## Scope

1. Recover slot selection, name editing, overwrite/confirmation and cancellation
   dispatch, including intro restrictions and quick-save behavior.
2. Map save header/version, thumbnail and subsequent record ordering, widths,
   sentinel values and helper ABIs. Distinguish stored IDs from live pointers.
3. Identify actor/world/script/timer state that is serialized versus recreated
   during loading, and the boundary where the old world is discarded.
4. Audit binary host file services and consistent writable runtime save lookup
   before a real writer can touch files.

## Initial Implementation Notes (v0.2.0)

Both generator no-op replacements for `FUN_00453920` must be accounted for in
later implementation. `FUN_004544a4` still contains many unresolved register
aliases. Do not enable the entire raw writer/reader and guess initial register
values to suppress the resulting crashes. Mirror proven C repairs narrowly.

Installed `Saved/*.ECS` are read-only evidence. The host currently starts in the
original data directory, so merely unstubbing Save risks targeting those files.
Reuse the runtime-data boundary and isolated probe storage. Audit CRT wrappers
as well as `CreateFileA`; do not assume both have identical buffering/error rules.

## Out Of Scope

1. Implementing a new save format, host memory dump or replay-based substitute.
2. Audio/music, equipment/HUD rendering, unrelated stability and tooling redesign.
3. Claiming full game persistence from labels, previews or menu cancellation.

## Acceptance Criteria

1. Original callback/ABI and byte-layout evidence is linked from a dated journal.
2. The first failure has a bounded fixture/native procedure and a clear owning
   layer, with original installed saves preserved.
3. A concrete writer/restore implementation sequence follows the observed format
   and calls; original compatibility assumptions and unknowns are explicit.
4. No change in functional-persistence acceptance is claimed from mapping alone.

## Verification

Use original-byte comparisons with intercepted host dependencies where necessary;
record those limits. Reuse menu/slot fixtures for any touched dispatch or preview
contract. Run builds, scoped regressions and generator parity if runtime changes;
for documentation alone run tree update/check and `git diff --check`.

## Review State

1. Planning state: agreed milestone; source starting points inspected for this handoff.
2. Implementation state: original ABI/format map and writer fixtures recorded in the
   [save/load journal](../../../../../journal/entries/game-save-load-recovery-2026-10-27.md).
   Continue with [writer recovery](task-02-recover-original-save-writer.md) and
   [restore/menu dispatch](task-03-recover-original-restore-and-menu-dispatch.md).
3. Notes: subsequent writer/restore tasks record bounded functional acceptance; all installed saves remain intact and tests use only private originally empty slots.

## Change Log

### 2026-10-27

1. Created the first save/load task from the inspected v0.2.0 source boundaries.
