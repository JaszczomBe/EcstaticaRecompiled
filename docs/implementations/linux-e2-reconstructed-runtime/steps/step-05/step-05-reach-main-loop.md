# Reach Main Loop

Status: planned
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-13

## Goal

Advance the reconstructed runtime to the main loop without crashing.

## Scope

1. Continue from title/menu logic.
2. Fix only blockers needed to enter the main loop.
3. Record the first verified main-loop call path.

## Out Of Scope

1. Full gameplay correctness.
2. Rendering/audio accuracy beyond what is needed to enter the loop.
3. Performance tuning.

## Acceptance Criteria

1. GDB/runtime evidence shows the main loop reached.
2. The main-loop entry point is documented.
3. Debug and ASan builds compile.

## Verification

1. Build debug and ASan targets.
2. Run `./e2recomp --run-recon`.
3. Capture a GDB backtrace or log proving main-loop entry.
