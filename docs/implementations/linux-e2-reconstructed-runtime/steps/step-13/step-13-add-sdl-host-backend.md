# Add SDL Host Backend

Status: planned
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Add an SDL-backed host implementation that can replace or supplement the current X11 backend while preserving reconstructed game logic and Win32/DirectX compatibility semantics.

## Why This Step Exists

The current Linux runtime proof uses an X11 scaffold behind the host backend boundary. SDL is the intended portable host layer for future window, input, timing, presentation, and audio work, but it should be introduced only after Step 12 defines the contracts SDL must implement.

## Scope

1. Add a selectable SDL backend build path without removing the X11 backend.
2. Implement SDL window lifecycle and input polling behind `e2recomp_host_backend.*`.
3. Add the first backend-owned presentation path only after framebuffer ownership is specified.
4. Preserve the Step 11 debug/ASan runtime regression proof.

## Out Of Scope

1. Calling SDL directly from reconstructed game logic.
2. Removing the X11 backend before SDL parity is proven.
3. Full DirectDraw or DirectSound fidelity.
4. Packaging a user-facing release.

## Usage Budget

Split implementation into the task files below. If a task exposes a runtime crash or a missing recovered game semantic, stop and create a focused runtime task instead of expanding SDL scope.

## Temporary Sacrifices

1. Sacrifice: Keep X11 available as a known-good backend while SDL is introduced.
2. Why accepted now: The regression proof is established against the current host behavior.
3. Removal trigger: SDL passes the same debug/ASan runtime probes and any added presentation/input checks.

## Acceptance Criteria

1. SDL can be selected at build/configuration time without changing reconstructed game code.
2. SDL window and input behavior reaches the same compatibility message queue semantics as X11.
3. Any SDL presentation work is backend-owned and leaves probe dumps intact.
4. `scripts/run-e2-runtime-regressions.sh` passes for the default backend, and any SDL-specific probe command is documented.

## Tasks

1. [Add SDL Build Selection](tasks/task-01-add-sdl-build-selection.md) - planned; make SDL opt-in without disturbing existing X11 builds.
2. [Implement SDL Window Input Backend](tasks/task-02-implement-sdl-window-input-backend.md) - planned; map SDL events to backend key callbacks.
3. [Add Backend Presentation Hook](tasks/task-03-add-backend-presentation-hook.md) - planned; define the first host presentation path without replacing probe dumps.
4. [Verify SDL Backend Parity](tasks/task-04-verify-sdl-backend-parity.md) - planned; prove SDL does not regress the stabilized runtime loop.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. `scripts/run-e2-runtime-regressions.sh`
4. SDL-specific build/probe command documented by task 01 or task 04.
5. `git diff --check`

## Notes

Step 13 should not begin until Step 12 closes or explicitly records the backend contracts SDL must satisfy. The smallest successful SDL slice is a build-selectable backend that creates a window and maps keyboard input through the existing backend callback into the compatibility message queue.

## Change Log

### 2026-07-27

1. Created Step 13 from the parent roadmap and split it into context-sized tasks.
