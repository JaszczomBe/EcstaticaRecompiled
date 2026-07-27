# Add SDL Build Selection

Status: planned
Parent Step: [Add SDL Host Backend](../step-13-add-sdl-host-backend.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Make SDL selectable as an optional host backend build path while preserving the existing default backend.

## Scope

1. Decide the CMake option name and default.
2. Add build discovery or clearly documented dependency expectations.
3. Compile a stub SDL backend path only when selected.
4. Leave the current X11 backend as the default until SDL parity is proven.

## Out Of Scope

1. SDL input mapping.
2. SDL presentation.
3. Removing X11 code.
4. Runtime behavior changes.

## Implementation Notes

Prefer a narrow CMake option such as `E2R_HOST_BACKEND=...` or an equivalent cache setting. Avoid network dependency installation in this task.

## Acceptance Criteria

1. Default builds keep their current backend behavior.
2. SDL selection either configures and builds or fails with an actionable dependency message.
3. The selected backend is visible in CMake output or documentation.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. SDL configuration/build command chosen by this task.
4. `git diff --check`

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Keep this task build-system focused.

## Change Log

### 2026-07-27

1. Created task.
