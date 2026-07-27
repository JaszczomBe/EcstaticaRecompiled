# Implement SDL Window Input Backend

Status: completed
Parent Step: [Add SDL Host Backend](../step-13-add-sdl-host-backend.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Implement SDL window lifecycle and keyboard polling behind the host backend API.

## Scope

1. Implement SDL create, show, destroy, and poll behavior for `E2R_HostWindow`.
2. Map SDL key events to the same virtual-key values currently produced by the X11 backend.
3. Route key events through `E2R_HostKeyDownCallback`.
4. Preserve compatibility-layer ownership of `WM_KEYDOWN` and message queue behavior.

## Out Of Scope

1. SDL rendering/presentation.
2. SDL audio.
3. New game input semantics.
4. Removing the X11 backend.

## Implementation Notes

Implemented in `E2Recomp/platform/e2recomp_host_backend_sdl.c`. The SDL backend now:

1. Initializes `SDL_INIT_VIDEO`.
2. Creates, shows, and destroys an `SDL_Window`.
3. Polls SDL events.
4. Maps SDL keydown events to the same virtual-key values used by the X11 backend for letters, digits, keypad digits, function keys, Escape, Return, Space, Ctrl, and arrow movement keys.
5. Delivers mapped keys through `E2R_HostKeyDownCallback`, leaving `WM_KEYDOWN` queue ownership in `e2recomp_win32_compat.c`.

Key delivery is proven by `--host-backend-key-probe`, which creates a compatibility window, asks the selected host backend to synthesize a `space` keydown event, polls through `PeekMessageA`, and checks that the compatibility queue receives `WM_KEYDOWN` with `wParam=0x20`.

## Acceptance Criteria

1. SDL backend can create a host window.
2. SDL key events reach the compatibility message queue through the backend callback.
3. Existing X11/default backend behavior is unchanged.

## Verification

1. SDL build from task 01.
2. A bounded SDL input probe chosen by this task.
3. `scripts/run-e2-runtime-regressions.sh` for the default backend.
4. `git diff --check`.

Current verification:

```text
cmake --build build/linux-clang-sdl-debug
build/linux-clang-sdl-debug/e2recomp
SDL_VIDEODRIVER=dummy build/linux-clang-sdl-debug/e2recomp --host-backend-key-probe
cmake --build --preset linux-clang32-debug
cmake --build build/linux-clang32-asan
scripts/run-e2-runtime-regressions.sh
```

The SDL-selected executable prints the normal probe command help. The SDL key probe reports `msg=0x0100 wParam=0x20` and passes. The default runtime regression passes with debug and ASan logs under `/tmp/e2-step11-regression-*.log`. The SDL build uses the vendored `dep/SDL` submodule pinned to SDL 3.4.12, not system SDL.

## Review State

1. Planning state: discussed
2. Implementation state: accepted
3. Notes: SDL window/input behavior is implemented and bounded key delivery is proven; task 03 owns presentation.

## Change Log

### 2026-07-27

1. Created task.
2. Activated after `E2R_HOST_BACKEND=sdl` compiled and linked.
3. Implemented SDL video/window/event polling and virtual-key mapping behind the host backend API.
4. Verified the SDL-selected build and default runtime regression; left key-delivery probe as the remaining review item.
5. Reverified after switching task 01 to vendored SDL source.
6. Added and passed `--host-backend-key-probe`, closing the key-delivery review gap.
