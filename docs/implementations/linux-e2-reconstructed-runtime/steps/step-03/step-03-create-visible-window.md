# Create Visible Window

Status: planned
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-13

## Goal

Create a visible Linux-hosted window or rendering surface for the reconstructed runtime.

## Scope

1. Identify the original DirectDraw/window initialization path reached by the runtime.
2. Provide the minimum Linux-compatible window/surface shim needed to prove visibility.
3. Preserve VS Code F5 launch behavior.

## Out Of Scope

1. Complete graphics backend accuracy.
2. Audio initialization.
3. Main loop correctness.

## Acceptance Criteria

1. Running the debug build creates a visible window or surface.
2. The window path is documented in the journal.
3. Debug and ASan builds compile.

## Verification

1. Build debug and ASan targets.
2. Launch via VS Code or `./e2recomp --run-recon`.
3. Confirm the visible surface appears without regressing prior resource loading.
