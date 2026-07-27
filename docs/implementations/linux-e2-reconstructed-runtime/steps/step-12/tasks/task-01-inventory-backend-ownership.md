# Inventory Backend Ownership

Status: completed
Parent Step: [Define Replaceable Host Backend Boundary](../step-12-define-replaceable-host-backend-boundary.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Record the current ownership split between reconstructed game logic, Win32/DirectX compatibility semantics, host backend services, and developer-only probes.

## Scope

1. Inspect `E2Recomp/platform/e2recomp_win32_compat.*`.
2. Inspect `E2Recomp/native/e2recomp_native_main.c`.
3. Document which current functions belong to compatibility, backend, or probe layers.

## Out Of Scope

1. Moving code.
2. Introducing SDL.
3. Changing runtime behavior.

## Implementation Notes

The task result is captured in the Step 12 `Current ownership shape` notes. The first practical boundary candidate is host window/input polling below the compatibility message queue.

## Acceptance Criteria

1. Step 12 names the current compatibility, backend, and probe ownership.
2. The first backend boundary candidate is identified.

## Verification

1. Review Step 12 `Notes`.
2. Confirm the parent implementation still points at Step 12 as active.

## Review State

1. Planning state: agreed
2. Implementation state: accepted
3. Notes: Completed as documentation before extracting the first backend API.

## Change Log

### 2026-07-27

1. Created task and marked it completed from the Step 12 ownership inventory.
