# Implement SDL Window Input Backend

Status: planned
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

Use the X11 backend's virtual-key behavior as the compatibility baseline. If SDL key mapping exposes ambiguity, document the mapping and keep the task bounded to the keys used by existing probes first.

## Acceptance Criteria

1. SDL backend can create a host window.
2. SDL key events reach the compatibility message queue through the backend callback.
3. Existing X11/default backend behavior is unchanged.

## Verification

1. SDL build from task 01.
2. A bounded SDL input probe chosen by this task.
3. `scripts/run-e2-runtime-regressions.sh` for the default backend.
4. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Designed to fit one context window after SDL build selection exists.

## Change Log

### 2026-07-27

1. Created task.
