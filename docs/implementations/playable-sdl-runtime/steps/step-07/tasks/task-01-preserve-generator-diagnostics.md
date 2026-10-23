# Preserve Generator Diagnostics

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
<!-- /docs-tree:parent -->

Status: completed
Parent Step: [Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Regenerate the committed actor/action/rep diagnostics without changing game behavior.

## Scope

1. Compare scratch-generated C against committed C.
2. Mirror missing diagnostics through narrow anchored generator replacements.
3. Regenerate and verify all emitted artifacts.

## Out Of Scope

1. Action 384 or model initialization repairs.
2. Broad Ghidra re-export or generated-file cleanup.

## Implementation Notes

The audit generated from the committed decompilation plus `functions.tsv`/`symbols.tsv`. Header, globals, and rename map matched. C lost 155 lines and gained 12, principally `E2R_TraceActorUpdateExit`, `E2R_TraceActionLookup`, model fields in actor logging, rep-parser stop logging, and their call sites. The action-index gate itself survives regeneration.

Use the scratch recipe in the [audit](../../../../../journal/entries/runtime-audit-2026-09-14.md); `/tmp/e2-audit-generator.diff` was the original ephemeral evidence. Verify replacement anchors match exactly before applying changes. Preserve the committed C as the reference; do not accept deleting diagnostics merely to eliminate drift.

## Result — 2026-09-14

`GenerateRecon.js` now has 23 checked, ordered anchors preserving the committed actor model/exit diagnostics, action lookup diagnostics, rep-parser stop log, counters, and call sites. Missing or duplicate anchors throw before reconstructed output is written. The former intermediate C write/read was removed; final normalization and parameter repairs still occur in memory before diagnostic patches.

Scratch generation at `/tmp/e2-generator-audit-n4jzg9fh` matches C, header, globals, and names. In-place generation produces zero differences in those four files against `HEAD`. Generator syntax, all three builds, and `git diff --check` pass. Runtime results after Task 02's wrapper correction are recorded in that task; generator parity does not imply the long-delay runtime is crash-free.

## Acceptance Criteria

1. `node --check` passes.
2. Scratch output matches committed C/header/globals/names after the intended generator repair.
3. In-place regeneration produces no unexplained reconstructed-file differences.
4. The retained diagnostics compile in debug, ASan, and SDL debug.

## Verification

1. `node --check E2Recomp/tools/GenerateRecon.js`.
2. Run the audit's scratch generation/comparison recipe.
3. Once scratch output matches, `node E2Recomp/tools/GenerateRecon.js .`; inspect `git diff --stat` and `git diff -- E2Recomp/reconstructed`.
4. Build `linux-clang32-debug`, `build/linux-clang32-asan`, and `linux-clang32-sdl-debug`.
5. `git diff --check`.

Record the result; run runtime baseline checks once in Task 02 after its script change.

## Review State

1. Planning state: agreed
2. Implementation state: accepted
3. Notes: Generator repair accepted. Scratch and in-place output match all four committed artifacts byte-for-byte; debug, ASan, and SDL debug builds pass.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.

2. Completed diagnostic mirrors, exact regeneration comparison, and debug/ASan/SDL debug build verification.
