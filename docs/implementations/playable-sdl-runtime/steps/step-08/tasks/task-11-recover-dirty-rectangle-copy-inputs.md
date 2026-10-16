# Recover Dirty-Rectangle Copy Inputs

Status: implemented; full-route validation blocked by Task 12
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-14

## Goal

Recover the framebuffer-copy arguments exposed after the flat-polygon lighting path returns.

## Evidence

Gated SDL reaches `FUN_004211c8 → FUN_00424bd8 → FUN_00418484 → FUN_00418514` and crashes at `*puVar5 = *puVar3`. The current three-argument reconstruction loses the original surface/rectangle contract; `FUN_00418514` still derives row addresses from uninitialized `unaff_EBX`.

Original `0x418484` forwards a stack argument into the high-resolution helper `0x418514`, alongside register inputs. Recover the full caller/helper contract, including surface, coordinates, dimensions, source/destination pitch and unlock ownership; do not interpret current parameter names as established facts. See the [lighting journal](../../../../../journal/entries/polygon-lighting-2026-09-21.md), `/tmp/e2-lighting-mapped.log` and the minimally interrupted `/tmp/e2-lighting-once.log`.

The 2026-10-14 source review confirms these unrecovered inputs remain in `4fb151a`. Original `0x418514..0x418588` establishes this entry contract:

| Original input | Role / evidence |
| --- | --- |
| EAX | Destination surface selector; saved for the unlock and passed to `0x418a04` |
| EDX | Horizontal byte offset; added to both source and destination bases |
| ECX | Bytes copied per row; saved and reloaded for `rep movsb` |
| EBX | Starting row; multiplied by each surface's pitch |
| Stack argument | Row count; read at stack `+0x20` after the helper prologue |

The source is `_DAT_00636158` with pitch `DAT_00477060`; `0x418a04` supplies the destination base and pitch. Original `0x418575..0x41857d` unlocks with the saved surface selector and the returned base. Current C instead uses width as the lock selector and loop-derived state as the unlock input, while the row remains `unaff_EBX`. The adjacent `FUN_00418b00` also retains an uninitialized `in_EAX`; recover that input at this boundary rather than assuming the existing unlock implementation is complete.

## Scope

1. Audit original rectangle dispatch and all direct callers of the affected copy helpers.
2. Supply the recovered inputs and preserve original copy/clipping semantics without adding a broad invalid-pointer skip.
3. Mirror source changes and verify bounded rectangle copies, then rerun relevant Debug/ASan and gated probes.
4. Record the next independent failure; keep geometry, action and scene-selection acceptance separate.

## Limits And Acceptance

The corrected path must copy the original source rectangle to the intended surface with valid ownership and pitches, and pass generator parity and relevant regressions. This does not by itself establish valid actor geometry or visible Joe. The first proven lighting normal is degenerate (0,0,0); heavily instrumented runs can instead expose `FUN_0042c790` action-channel failures. Action indexing remains opt-in.

## Next Implementation And Verification

1. Trace the four direct original calls to `0x418484` at `0x421bf5`, `0x421e11`, `0x424c95` and `0x455340`. Recover all five inputs in their C callers, including packed dirty-rectangle coordinates and inclusive endpoint arithmetic. Inspect the low-resolution branch and lock/unlock helpers before selecting explicit C signatures.
2. Implement the smallest explicit caller/dispatch/high-resolution contract and required unlock ownership. Preserve the original branch-specific copy direction, alignment and pitch behavior. Recover clipping from callers where present; do not invent a general clipping rule or bypass invalid state. Split unrelated `0x41868c` copy failures if exposed.
3. Mirror each changed body/prototype in `GenerateRecon.js`. Check syntax and scratch parity for all four outputs before broad runtime probes.
4. Add a bounded comparison against original i386 instructions, intercepting surface lock/unlock only as needed. Use asymmetric source/destination pitches, nonzero X/Y, odd and even widths, multiple rows, valid edge rectangles and sentinel padding. Check copied bytes, untouched regions and matching lock/unlock selector/base; run normally and with ASan. This fixture proves the copy contract, not geometry.
5. Build X11/SDL Debug and ASan with the current presets. Rerun the default wrapper, eight arrow rows, and SDL Debug/ASan requester checks. Repeat the lighting journal's minimally interrupted gated SDL repro with fresh capture prefixes; inspect the inferior stop reason, not GDB's shell status. Repeat gated SDL ASan and record whether it actually reaches the copy path or still times out in camera 1073.

Success for this task is a source-consistent copy and execution past the prior copy boundary, with any new independent failure recorded. A static frame/hash, an ASan run that never enters this path, or a degenerate normal is insufficient to close Task 02. Resume placement/action validation and child activation only after this bounded repair.

## Review State

The copy-input repair is implemented and mirrored in `GenerateRecon.js`. Both copy helpers now receive surface/X/Y/width/height; all four callers supply the original opposite-page selector and row input. The low-resolution branch preserves four-pixel group rounding and its explicit planar mask. The high-resolution branch retains separate source/destination pitches, forward-copy order and original lock/unlock behavior even when row count is zero.

The lock helper preserves its selector across a real 108-byte clear at mapped `0x636864`, passes that descriptor to COM, and reads the mapped pitch/base. Unlock now receives its selector explicitly and supplies the original two COM arguments. Existing cached-surface guards are retained; other unrecovered callers and DirectDraw operations are not declared complete.

`scripts/check-e2-rectangle-copy.py` passes **2,048 original-x86 copy/ownership cases** plus **256 original-x86 dirty-list dispatch cases**, normally and under ASan. It exercises the original Lock/Unlock instructions against mock COM methods, both page flags, selectors 0–3, zero/negative row counts, odd/aligned spans, asymmetric pitches, both overlap directions, padding and surface-lost retries. The caller comparison caught and corrected a mistaken current-page selection before final verification.

The actual gated run still faults at the copy because the compatibility Lock slot is a generic success/no-output stub: destination base/pitch are now explicitly **0/0**. [Task 12](task-12-recover-directdraw-surface-lock.md) owns that separate provider failure. The bounded argument/copy contract is verified; execution past the copy and full-route/actor acceptance remain open. See the [2026-10-14 journal](../../../../../journal/entries/rectangle-copy-2026-10-14.md) for final builds, regressions, repro and limits. Task 10 did not include this repair.
