# Recover Polygon Lighting Inputs

Status: completed (bounded flat-polygon lighting inputs)
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-21

## Goal

Recover the normal-vector and rotation inputs that block the next gated geometry update after polygon argument recovery.

## Evidence

The 2026-09-21 polygon repair passes the former invalid EBX reference read. At that checkpoint, gated SDL stopped in `FUN_00431a7c → FUN_004226bc → FUN_004228b8 → FUN_0045dd04`, whose matrix pointers are unrecovered. Original `0x4226c4..0x4226dc` preserves the vector, supplies a signed angle, builds a local matrix and transforms into an explicit output before copying back. The reconstructed no-argument rotation call and flattened normal storage do not preserve that contract.

See the [polygon journal](../../../../../journal/entries/polygon-inputs-2026-09-21.md) and `/tmp/e2-polygon-after.log`. Gated SDL ASan instead times out in camera 1073; no gated geometry acceptance follows from its lack of a sanitizer report.

## Scope

1. Recover the flat-polygon normal's contiguous storage, angle-helper inputs and the two rotation calls from original code.
2. Recover required rotation/matrix destinations, auditing other callers before changing shared signatures. Use the already recovered Q14 vector arithmetic where the original contract matches.
3. Mirror the bounded repair and compare arithmetic/call behavior against original code; rerun relevant runtime regressions.
4. Record and split any newly exposed independent rasterization failure.

## Out Of Scope

Forcing actor placement, enabling action indexing by default, substituting synthetic pixels, broad rasterizer recovery, or declaring Task 02 complete after merely passing a crash.

## Acceptance

1. The reached lighting path uses source-backed vectors, angles and output buffers without stale pseudo-registers.
2. Bounded gated probes pass this failure and identify the next observed boundary honestly.
3. Generator parity, builds and relevant Debug/ASan tests pass; visible-player acceptance remains with Task 02.

## Review State

Implemented and generator-mirrored: contiguous normal storage, recovered atan tables, explicit local X/Y rotations and original lighting-index numerators/divisor. The flat leaf also uses byte reads from the two mapped color tables. Shared legacy wrappers, textured lighting and full color fidelity remain incomplete.

Original-x86 comparisons pass 10,240 angle cases, 16,384 rotations and 8,192 lighting-index cases, both normally and with ASan. Four builds, generator parity, default regressions, eight arrow rows and both SDL requester checks pass. A minimal gated probe returns indices 64/64 from a degenerate normal 0/0/0, then crashes in `FUN_00418514` framebuffer copying. This is execution past lighting, not valid geometry or a visible player. Gated SDL ASan still times out before geometry.

See the [lighting journal](../../../../../journal/entries/polygon-lighting-2026-09-21.md). Resume [Task 11 copy inputs](task-11-recover-dirty-rectangle-copy-inputs.md) within active Task 02; action indexing remains opt-in.
