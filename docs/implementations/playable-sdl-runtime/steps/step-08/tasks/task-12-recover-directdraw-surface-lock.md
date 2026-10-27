# Recover DirectDraw Surface Lock

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
<!-- /docs-tree:parent -->

Status: provider implemented and bounded menu/runtime callers verified; original-render acceptance remains open
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-27

## Goal

Supply real surface storage and pitch through the compatibility DirectDraw Lock/Unlock contract so the recovered rectangle-copy path can execute in the runtime.

## Current continuation — Headless menu sweep

The [2026-10-27 sweep](../../../../../journal/entries/headless-regression-sweep-2026-10-27.md)
reaches this provider through Load previews. The original installed saves expose
real thumbnail reads; ASan returns base/pitch **0/0** from the generic Lock.
The compatibility provider now supplies distinct physical surface objects and
owned pixels, aligned pitch, exact 108-byte descriptor fields, validated
Lock/Unlock ownership, Restore lifetime, references, attached buffers and Flip.
Auxiliary buffers 2/3 and presentation snapshots retain separate ownership.

Original creation/mode disassembly restores contiguous descriptors, real mode
width/height and complete COM arguments. The high/low wrappers recover their
original mode flags, dimensions, scene clear and palette pointer. Original
`0x417cd7/0x417ce8` restores two copy-unlock selectors previously discarded by
Ghidra. All reconstructed repairs are generator-owned; the compatibility provider
is handwritten in `E2Recomp_stubs.c`.

Both normal/ASan provider fixtures pass **100** ownership/storage lifecycles,
including recovered high/low/high mode callers, invalid unlocks, attachment/flip,
release and auxiliary isolation. Existing original-x86 comparisons again pass
**2048** rectangle copies and **256** dispatches per mode. The complete headless
Debug/ASan menu block passes **54 required checks / 48 optional skips**, two native
exits and complete inspection in **54.06 s**, with all **26** source hashes
matching. The journal owns retained attempts and exact limits. This does not
establish the original actor renderer, visible presentation, arbitrary mode
switching or the older full-render gated route. Broader Task 12 acceptance and
the complete regression sweep remain open.

## Evidence

[Task 11](task-11-recover-dirty-rectangle-copy-inputs.md) recovers all five copy inputs, opposite-page selection, descriptor storage and unlock ownership. Its original-x86 comparisons pass 2,048 copy/ownership cases and 256 dirty-list dispatch cases, normally and under ASan. Gated SDL now reaches a coherent one-pixel rectangle but `FUN_00418a04` returns **base 0 / pitch 0**. The copy still faults; this is not a successful scene capture.

`DirectDrawCreate` in `E2Recomp/reconstructed/E2Recomp_stubs.c` initializes the shared `E2R_surf_obj` vtable to `E2R_DD_Generic`, then replaces only SetPalette. Lock (slot 25), Restore (27) and Unlock (32) remain generic no-ops; CreateSurface returns the same shared object. A success code without a populated descriptor cannot satisfy the original copy contract.

Original `0x418a04..0x418aff` selects the physical object using the selector and front-page flag, clears the mapped 108-byte descriptor at `0x636864`, calls Lock with flags 1, and reads pitch at descriptor `+0x10` and base at `+0x24`. Original `0x418b00..0x418b97` unlocks the same object's returned base and handles surface-lost restoration. Source pitch `DAT_00477060` is initialized to 640 in `E2Recomp_data_init.c`, matching the original executable; do not substitute it for the destination's returned pitch.

## Scope

1. Audit original surface creation/attachment/flip callers and their required object/storage identity before replacing the shared generic object. Keep physical surfaces distinct from auxiliary game buffers 2/3 and from host presentation snapshots.
2. Implement the smallest justified compatibility surface storage and Lock/Unlock/Restore behavior, with correct descriptor offsets and lifetime. Keep host-specific services below the compatibility boundary; do not add SDL calls or fabricated surface addresses to reconstructed game logic.
3. Verify the compatibility contract directly, then recheck Task 11's source-copy/ownership comparisons and actual gated execution. Split independent blit/flip/actor/rasterization failures rather than broadening this task to all DirectDraw semantics.
4. Preserve source-backed reconstructed changes through the generator if additional caller repairs are needed; handwritten compatibility stub changes must also remain reviewable.

## Acceptance And Verification

Lock returns valid storage and its actual pitch for the selected object; Unlock uses matching ownership/base. Check two distinct objects, write/read lifetime, repeated locks, descriptor contents and relevant restore/error cases. Then build X11/SDL Debug and ASan, run default wrapper/arrow/requester regressions and rectangle comparisons, and use the minimally interrupted gated repro from the [rectangle journal](../../../../../journal/entries/rectangle-copy-2026-10-14.md).

Record whether the runtime really copies the requested rectangle and reaches a later boundary. A passing mock-surface comparison or a GDB shell exit zero is insufficient. Gated ASan must actually enter the affected path before it counts as runtime coverage; a camera-1073 readiness timeout remains a failed readiness result. Use stage/action checkpoints for skips and the pedestal wait; video logo/horseback timings were shortened by user skip taps.

## Review State

The independent compatibility failure now has a real provider and bounded menu
qualification. Task 11's comparisons remain separate from original full-render
and visible presentation acceptance, which are still open.
