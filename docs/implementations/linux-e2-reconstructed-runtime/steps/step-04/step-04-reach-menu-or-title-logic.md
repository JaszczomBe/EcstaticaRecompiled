# Reach Menu Or Title Logic

Status: completed
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-13

## Goal

Initialize enough graphics and audio stubs to reach menu or title-screen logic.

## Scope

1. Continue from the visible-window milestone.
2. Stub or recover only the graphics/audio calls needed to reach title/menu code.
3. Document the first title/menu function or asset reached.

## Out Of Scope

1. Full DirectDraw implementation.
2. Full DirectSound implementation.
3. Gameplay main loop correctness.

## Acceptance Criteria

1. GDB/runtime evidence shows title or menu logic reached.
2. Any stubs added are documented as temporary sacrifices.
3. Debug and ASan builds compile.

## Verification

1. Build debug and ASan targets.
2. Run under GDB.
3. Record the reached title/menu call path in the journal.

## Result

The runtime now advances past the visible-window milestone, startup logo loading, DirectDraw palette setup, and fullscreen logo blit far enough to reach title logic:

```text
FUN_00410a48 -> FUN_00414a94
FUN_00410a48 -> FUN_00414b24
```

Evidence: GDB breakpoints hit `FUN_00414a94` at `E2Recomp_recon.c:5316` and then `FUN_00414b24` at `E2Recomp_recon.c:5378`; the process then exited with code `0340` rather than crashing in the prior DirectDraw/surface frontier.

Temporary sacrifices: the DirectDraw shim now provides minimal success-return palette/surface methods and a palette object sufficient for startup-title progress. It does not implement accurate rendering, surface memory, clipping, or palette behavior yet.

Next frontier: step 5 should continue from reached title logic toward the reconstructed main loop.

## Change Log

### 2026-07-13

1. Added a minimal DirectDraw palette object and `CreatePalette` stub.
2. Repaired the `_DAT_006366c0` palette-handle overlap, `FUN_00418a04` buffer index, and `FUN_00417b20` startup blit coordinate artifacts.
3. Mapped the legacy VGA-style `0xa0000..0x100000` range for startup blits.
4. Verified debug and ASan builds compile and recorded title logic reached in GDB.
