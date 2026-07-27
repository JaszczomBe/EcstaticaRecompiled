# Add Main Thread Presentation Pump

Status: completed
Parent Step: [Present Live Runtime Frames](../step-14-present-live-runtime-frames.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-28

## Goal

Call backend presentation from normal main-thread compatibility pump points using real recovered framebuffer data.

## Scope

1. Export a native helper that selects and validates the current runtime framebuffer.
2. Call the helper from `PeekMessageA`, `GetMessageA`, and `UpdateWindow`.
3. Route pixels through `E2R_HostPresentIndexed8`.
4. Keep worker-thread probe dumps unchanged.

## Subtasks

1. Identify the safest main-thread pump points already reached by the reconstructed runtime.
2. Add a compatibility-facing helper declaration without exposing SDL or host-backend types to reconstructed C.
3. Reuse `e2r_select_framebuffer` so live presentation and worker dump probes agree on candidate surfaces.
4. Validate width, height, pitch, and pointer readability before presenting a page.
5. Add a monotonic-clock throttle so pump-heavy loops cannot flood the backend.
6. Keep diagnostics opt-in through `E2R_PRESENT_DIAG=1`.
7. Make the SDL backend reject off-main-thread presentation calls.
8. Rebuild default and SDL targets after the hook lands.

## Out Of Scope

1. Full page-flip recovery.
2. Palette-correct color presentation.
3. Direct SDL calls from reconstructed C.

## Implementation Notes

Ownership is deliberately split across three layers. `E2R_TryPresentCurrentFrame(HWND)` lives in native runtime support because it knows how to inspect recovered framebuffers and owns the existing probe selection heuristic. `e2recomp_win32_compat.c` only calls that helper from Win32-style pump points; it does not learn SDL details or pick surfaces itself. `e2recomp_host_backend_sdl.c` remains the only SDL-aware presentation implementation.

The hook points were chosen because the original runtime already calls them while yielding to the host. That keeps presentation naturally paced by the game loop and avoids adding host rendering calls inside generated reconstruction logic.

Failure handling must remain quiet by default. A missing or unreadable framebuffer is not fatal, and backend presentation failure should only become noisy when an explicit diagnostic switch is enabled.

## Acceptance Criteria

1. Default backend builds and regressions still pass.
2. SDL builds still compile.
3. Raw F5-equivalent debug route survives a bounded run.
4. Reconstructed generated C remains free of direct backend or SDL calls.
5. Worker-thread gameplay probes continue to dump PGM frames without needing an SDL main-thread context.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. `scripts/run-e2-runtime-regressions.sh`
4. Raw `--run-recon` timeout check.

## Review State

1. Planning state: agreed
2. Implementation state: accepted
3. Notes: Added `E2R_TryPresentCurrentFrame`, wired it from compatibility pump points, and kept worker-thread presentation harmless through SDL main-thread checks.

## Evidence

1. `E2R_TryPresentCurrentFrame(HWND)` was added to the native runtime and declared through `e2recomp_win32_compat.h`.
2. `UpdateWindow`, `PeekMessageA`, and `GetMessageA` now attempt live presentation after polling/yield work.
3. SDL presentation returns a harmless failure when called away from the SDL main thread.
4. `git diff --check` passed after the implementation.

## Change Log

### 2026-07-28

1. Created task.
2. Added native framebuffer selection/presentation from `UpdateWindow`, `PeekMessageA`, and `GetMessageA`.
