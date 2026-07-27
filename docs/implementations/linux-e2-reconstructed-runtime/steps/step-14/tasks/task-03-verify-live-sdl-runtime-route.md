# Verify Live SDL Runtime Route

Status: completed
Parent Step: [Present Live Runtime Frames And SDL F5 Route](../step-14-present-live-runtime-frames.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-28

## Goal

Prove the SDL backend receives real recovered runtime frames and that the F5-equivalent SDL route survives the previous allocator-crash window.

## Scope

1. Build the SDL-selected backend.
2. Run a bounded SDL runtime route that reaches a known nonblank frame.
3. Record evidence that backend presentation accepted real `640x480` pixels.
4. Run the SDL executable with `--run-recon` from its build directory.
5. Confirm no allocator abort or SDL main-thread assertion appears during the bounded run.

## Subtasks

1. Configure `linux-clang32-sdl-debug` after adding the preset.
2. Build `linux-clang32-sdl-debug` through the same path VS Code uses.
3. Re-run the synthetic SDL presentation probe to preserve the known backend baseline.
4. Enable only `E2R_PRESENT_DIAG=1` for live-frame evidence.
5. Drive the existing split gameplay probe so presentation happens after real scene data loads.
6. Compare live presentation hashes with known nonblank gameplay-surface dump hashes.
7. Confirm movement input still latches after live presentation is active.
8. Run raw SDL `--run-recon` from `build/linux-clang32-sdl-debug` against the real display when permitted.
9. Compare the first runtime console lines with the prior F5 crash report.
10. Confirm the run passes the previous `malloc_consolidate()` abort point.
11. Record sandbox-related reruns separately from runtime failures.

## Out Of Scope

1. Automating visual inspection of the real display.
2. Pixel-perfect palette validation.
3. Long interactive play sessions.
4. Fixing newly discovered game logic crashes.
5. Replacing PGM probe artifacts.

## Implementation Notes

The useful proof is not just "a window updated." The probe must show that a recovered runtime framebuffer reached `E2R_HostPresentIndexed8`, because Step 13 already proved synthetic pixels. The accepted signal is an opt-in diagnostic line with a real runtime surface id, `640x480` dimensions, and a hash that matches known nonblank gameplay-frame evidence.

Use the dummy SDL video driver for automated presentation evidence so the check is reproducible in a headless or sandbox-limited context. Real display inspection stays manual unless a later task adds screenshot automation.

The command-line `--run-recon` run is a proxy for the VS Code launch configuration because both routes use the same executable, arguments, and working directory. It cannot fully replace a user-facing F5 visual check because VS Code owns the debugger/display environment and the user can observe the live window directly.

The prior reported failure was `malloc_consolidate(): unaligned fastbin chunk detected` from the default F5 route. For this task, the important signal is whether the SDL launch-equivalent route survives past the same startup/archive parse window without allocator abort or SDL main-thread failure. Later crashes should be scoped to the next runtime repair step.

## Acceptance Criteria

1. SDL backend reports or otherwise proves at least one real runtime frame presentation.
2. Existing synthetic presentation probe still passes.
3. No SDL main-thread assertion is triggered.
4. The gameplay probe still reaches the control-ready movement proof.
5. Live-presentation diagnostics remain opt-in.
6. SDL raw route survives the prior allocator-crash window.
7. Any sandbox `Bad system call` result is rerun outside sandbox before being treated as a runtime failure.
8. Remaining manual F5 visual confirmation is documented explicitly.

## Verification

1. `cmake --preset linux-clang32-sdl-debug`
2. `cmake --build --preset linux-clang32-sdl-debug`
3. `SDL_VIDEODRIVER=dummy build/linux-clang32-sdl-debug/e2recomp --host-backend-present-probe`
4. `SDL_VIDEODRIVER=dummy E2R_PRESENT_DIAG=1 build/linux-clang32-sdl-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step14-sdl-live space,num8 6 10000 180 1`
5. `timeout 25s ./e2recomp --run-recon` from `build/linux-clang32-sdl-debug`
6. `git diff --check`

## Review State

1. Planning state: agreed
2. Implementation state: accepted
3. Notes: SDL build and runtime probes pass; real-display raw launch survives beyond the prior allocator crash window.

## Evidence

1. SDL live-frame proof printed real backend presentations for `surface=3 width=640 height=480` with hashes `6e39f5ea` and `3615add9`.
2. The same live-frame probe dumped nonblank surface 3 with hash `3615add9` and `move=[1,0,0,0,0,0,0,0,0]`.
3. `SDL_VIDEODRIVER=dummy build/linux-clang32-sdl-debug/e2recomp --host-backend-present-probe` passed with `hash=a92a7045`.
4. `cmake --preset linux-clang32-sdl-debug` completed successfully.
5. `cmake --build --preset linux-clang32-sdl-debug` completed successfully with no rebuild needed.
6. Real-display `timeout 25s ./e2recomp --run-recon` from `build/linux-clang32-sdl-debug` reached the archive/FAN parse frontier and stayed alive beyond the previously reported `malloc_consolidate()` abort. The PTY timeout wrapper did not collect a terminal status, so the process was manually interrupted after the survival signal was captured.

## Change Log

### 2026-07-28

1. Created task by merging SDL live-frame and F5-route verification into one runtime-route proof.
