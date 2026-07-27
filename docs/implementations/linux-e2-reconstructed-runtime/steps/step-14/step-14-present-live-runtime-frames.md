# Present Live Runtime Frames And SDL F5 Route

Status: completed
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-28

## Goal

Present recovered runtime framebuffer pages through the host backend during the normal reconstructed main loop and make that live SDL backend reachable from the normal VS Code F5 workflow.

## Why This Step Exists

Step 13 proved SDL can create windows, receive input, and present synthetic indexed-8 pixels. The next useful proof is that the actual running game window can receive real recovered framebuffer pixels without moving SDL calls into reconstructed game logic.

The first pass at this milestone was accidentally split into two tiny steps: live runtime-frame presentation and SDL F5 launch wiring. Those are one developer-facing milestone. Live presentation is only useful if the normal debug route can reach it, and the SDL launch route is only meaningful because it selects the backend that can display recovered frames.

## Scope

1. Add a main-thread presentation hook below Win32 compatibility and above the host backend.
2. Reuse the existing bounded framebuffer selection logic for live presentation.
3. Present through `E2R_HostPresentIndexed8` when a backend supports it.
4. Keep worker-thread PGM dump probes unchanged.
5. Add SDL CMake configure/build presets for 64-bit backend probes and 32-bit reconstructed runtime runs.
6. Add a VS Code SDL build task and `Ecstatica Recompiled (SDL)` launch entry.
7. Track the `dep/SDL` submodule gitlink so the vendored SDL source is available in fresh checkouts.
8. Verify the live SDL route without replacing the default debug launch entry.

## Out Of Scope

1. Pixel-perfect DirectDraw page flipping.
2. Palette animation fidelity beyond grayscale indexed-8 display.
3. SDL audio or timing replacement.
4. Removing X11 fallback behavior.
5. Long-play stability beyond bounded launch/runtime probes.

## Usage Budget

Keep each task narrow enough for one context window. If live presentation exposes a new reconstructed-runtime crash, document it as a runtime repair before widening presentation scope.

## Temporary Sacrifices

1. Sacrifice: Present grayscale indexed-8 frames selected by current probe heuristics.
2. Why accepted now: The recovered runtime already proves inspectable frame pages through PGM dumps, and Step 13 only introduced grayscale backend presentation.
3. Removal trigger: DirectDraw page/palette semantics are recovered enough to present the exact front buffer with palette state.

1. Sacrifice: Keep both `Ecstatica Recompiled` and `Ecstatica Recompiled (SDL)` launch entries.
2. Why accepted now: The default route remains the known baseline for runtime repair, while SDL is the live-presentation route under active development.
3. Removal trigger: SDL becomes the default host backend or the X11/no-presentation fallback is intentionally retired.

## Acceptance Criteria

1. The raw F5 route continues to run without the previous allocator abort.
2. SDL backend can present a real recovered runtime frame from the normal message pump.
3. Default debug/ASan runtime regressions still pass.
4. Presentation remains backend-owned and reconstructed code does not call SDL.
5. `linux-clang32-sdl-debug` is available as a CMake preset and builds successfully.
6. VS Code exposes `Ecstatica Recompiled (SDL)` with a matching SDL pre-launch build task.
7. Raw SDL `--run-recon` survives the prior allocator-crash window.

## Tasks

1. [Add Main Thread Presentation Pump](tasks/task-01-add-main-thread-presentation-pump.md) - completed; call backend presentation from compatibility pump points using native framebuffer selection.
2. [Add SDL Developer Launch Route](tasks/task-02-add-sdl-developer-launch-route.md) - completed; add CMake/VS Code wiring and track the SDL gitlink.
3. [Verify Live SDL Runtime Route](tasks/task-03-verify-live-sdl-runtime-route.md) - completed; prove SDL receives real recovered frames and the F5-equivalent route survives the prior crash window.
4. [Close Runtime Presentation Milestone](tasks/task-04-close-runtime-presentation-milestone.md) - completed; rerun default and SDL checks, document evidence, and hand off to the new post-reconstruction implementation.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. `scripts/run-e2-runtime-regressions.sh`
4. SDL-selected build/probe command from the active task.
5. Raw `build/linux-clang32-debug/e2recomp --run-recon` timeout survival.
6. `cmake --preset linux-clang32-sdl-debug`
7. `cmake --build --preset linux-clang32-sdl-debug`
8. Raw `build/linux-clang32-sdl-debug/e2recomp --run-recon` bounded survival.
9. `git diff --check`

## Notes

SDL presentation must happen on the SDL main thread. Existing probe worker threads can still write PGM dumps and post input, but host presentation calls from non-main-thread paths should be harmless no-ops.

The implementation adds `E2R_TryPresentCurrentFrame(HWND)` as a native helper and calls it from `UpdateWindow`, `PeekMessageA`, and `GetMessageA`. The helper validates dimensions, selects a readable recovered framebuffer, throttles attempts to roughly 30 FPS, and routes pixels through `E2R_HostPresentIndexed8`. The SDL backend rejects presentation calls off the SDL main thread.

Opt-in live evidence used:

```text
SDL_VIDEODRIVER=dummy E2R_PRESENT_DIAG=1 build/linux-clang32-sdl-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step14-sdl-live space,num8 6 10000 180 1
```

The probe printed real backend presentations for `surface=3 width=640 height=480` with hashes `6e39f5ea` and `3615add9`, then dumped nonblank surface 3 with hash `3615add9` and `move=[1,0,0,0,0,0,0,0,0]`.

The developer launch route added `linux-clang-sdl-debug` and `linux-clang32-sdl-debug` CMake presets, `CMake: Configure SDL 32-bit` and `CMake: Build SDL 32-bit` VS Code tasks, and an `Ecstatica Recompiled (SDL)` launch entry using `build/linux-clang32-sdl-debug/e2recomp --run-recon` from the SDL build directory. The existing `Ecstatica Recompiled` entry remains unchanged.

`dep/SDL` is tracked as a submodule gitlink at `f87239e71e42da91ca317a12eefb82cfbf3393eb`, matching SDL release 3.4.12.

The raw SDL launch-equivalent probe reached the archive/FAN parse frontier and stayed alive beyond the previously reported `malloc_consolidate()` abort. The terminal timeout wrapper did not collect a clean exit status in the PTY session, so the run was manually interrupted after the survival signal was captured. Visual confirmation remains part of manual VS Code F5 testing.

## Change Log

### 2026-07-28

1. Created Step 14 after Step 13 closed SDL backend parity and the raw F5 route survived.
2. Added the main-thread compatibility presentation pump and SDL main-thread presentation guard.
3. Verified SDL real-frame presentation and closed Step 14.
4. Merged the former Step 15 SDL F5 launch route into this milestone because live presentation and the developer launch path are one implementation unit.
