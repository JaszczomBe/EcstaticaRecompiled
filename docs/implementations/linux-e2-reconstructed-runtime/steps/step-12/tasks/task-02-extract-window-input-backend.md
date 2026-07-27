# Extract Window Input Backend

Status: completed
Parent Step: [Define Replaceable Host Backend Boundary](../step-12-define-replaceable-host-backend-boundary.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Move host window lifecycle and host key polling below a backend API while preserving the game-facing Win32 message queue and `WM_KEYDOWN` semantics.

## Scope

1. Add a narrow `E2R_HostWindow` API for create, show, destroy, and poll.
2. Move X11 dynamic loading, X11 window state, keysym mapping, and X11 event polling into the backend implementation.
3. Keep HWND stubs and message filtering in `e2recomp_win32_compat.c`.
4. Build and run the Step 11 runtime regression script.

## Out Of Scope

1. SDL implementation.
2. Presentation frame upload.
3. Audio backend behavior.
4. Reconstructed runtime logic changes.

## Implementation Notes

The current files are:

```text
E2Recomp/platform/e2recomp_host_backend.h
E2Recomp/platform/e2recomp_host_backend.c
E2Recomp/platform/e2recomp_win32_compat.c
```

The backend returns an opaque `E2R_HostWindow *`. The compatibility layer stores it in the existing HWND stub payload and translates backend key callbacks into queued `WM_KEYDOWN` messages.

## Acceptance Criteria

1. `e2recomp_win32_compat.c` no longer owns X11 dynamic-loading or X11 event-loop internals.
2. `CreateWindowExA`, `ShowWindow`, `DestroyWindow`, `PeekMessageA`, and `GetMessageA` route through the backend API where host behavior is needed.
3. Existing debug and ASan runtime probes still pass.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. `scripts/run-e2-runtime-regressions.sh`
4. `git diff --check`

## Review State

1. Planning state: agreed
2. Implementation state: ready_for_review
3. Notes: Implemented as the first Step 12 code slice.

## Change Log

### 2026-07-27

1. Created task after extracting the X11 host window/input backend seam.
