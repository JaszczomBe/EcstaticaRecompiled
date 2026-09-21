# Recover Dirty-Rectangle Copy Inputs

Status: planned
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-21

## Goal

Recover the framebuffer-copy arguments exposed after the flat-polygon lighting path returns.

## Evidence

Gated SDL reaches `FUN_004211c8 → FUN_00424bd8 → FUN_00418484 → FUN_00418514` and crashes at `*puVar5 = *puVar3`. The current three-argument reconstruction loses the original surface/rectangle contract; `FUN_00418514` still derives row addresses from uninitialized `unaff_EBX`.

Original `0x418484` forwards a stack argument into the high-resolution helper `0x418514`, alongside register inputs. Recover the full caller/helper contract, including surface, coordinates, dimensions, source/destination pitch and unlock ownership; do not interpret current parameter names as established facts. See the [lighting journal](../../../../../journal/entries/polygon-lighting-2026-09-21.md), `/tmp/e2-lighting-mapped.log` and the minimally interrupted `/tmp/e2-lighting-once.log`.

## Scope

1. Audit original rectangle dispatch and all direct callers of the affected copy helpers.
2. Supply the recovered inputs and preserve original copy/clipping semantics without adding a broad invalid-pointer skip.
3. Mirror source changes and verify bounded rectangle copies, then rerun relevant Debug/ASan and gated probes.
4. Record the next independent failure; keep geometry, action and scene-selection acceptance separate.

## Limits And Acceptance

The corrected path must copy the original source rectangle to the intended surface with valid ownership and pitches, and pass generator parity and relevant regressions. This does not by itself establish valid actor geometry or visible Joe. The first proven lighting normal is degenerate (0,0,0); heavily instrumented runs can instead expose `FUN_0042c790` action-channel failures. Action indexing remains opt-in.

## Review State

Next bounded source task within Task 02 geometry recovery. No rectangle-copy implementation is included in Task 10.
