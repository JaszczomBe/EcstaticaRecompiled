# Create Visible Window

Status: completed
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

## Result

The reconstructed startup reaches the original window path:

```text
FUN_00458714 -> RegisterClassA -> CreateWindowExA
class: Ecstatica2
title: Ecstatica II
size: 640x640
```

`CreateWindowExA` now dynamically loads X11 on Linux, creates and maps a top-level window for the original request, and falls back to the prior headless HWND stub when X11 is unavailable.

Evidence: GDB stopped in `CreateWindowExA` with the `Ecstatica II` title and then `finish` returned the platform HWND; `e2r_x11_window.window` was nonzero (`20971521`) after the X11 map/flush.

Next frontier: after window creation and the first proven resource open, execution now crashes in `FUN_0041af88` while calling through a DirectDraw/surface vtable from the startup logo path.

## Change Log

### 2026-07-13

1. Recovered file descriptor/open-mode bookkeeping needed to advance past the first resource-open close path.
2. Added a minimal dynamically loaded X11 window implementation for top-level `CreateWindowExA` calls.
3. Verified debug and ASan builds compile and recorded the new DirectDraw/surface frontier.
