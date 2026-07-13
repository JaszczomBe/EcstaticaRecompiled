# Reach Menu Or Title Logic

Status: planned
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
