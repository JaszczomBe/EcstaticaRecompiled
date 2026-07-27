# Define Remaining Backend Contracts

Status: planned
Parent Step: [Define Replaceable Host Backend Boundary](../step-12-define-replaceable-host-backend-boundary.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Specify the remaining backend-owned service contracts before adding new host behavior.

## Scope

1. Inventory current timing ownership around `Sleep`, `GetTickCount`, `timeGetTime`, and loop wait behavior.
2. Inventory current presentation ownership around legacy framebuffer pages, probe dumps, and future host display updates.
3. Inventory current audio ownership around DirectSound/MIDI stubs and future host audio calls.
4. Record which contracts should become backend APIs and which should remain compatibility semantics.

## Out Of Scope

1. Implementing the contracts.
2. Adding SDL.
3. Changing probe output formats.
4. Recovering additional DirectDraw or DirectSound fidelity.

## Implementation Notes

Keep this task documentation-first. If code movement looks necessary, split it into a new task before editing source files.

## Acceptance Criteria

1. Step 12 documents backend ownership decisions for timing, presentation, and audio.
2. Each proposed backend API names its current caller and current implementation owner.
3. Any risky or deferred API is explicitly left for Step 13 or a later step.

## Verification

1. Documentation review against `E2Recomp/platform/e2recomp_win32_compat.*`.
2. Documentation review against `E2Recomp/native/e2recomp_native_main.c`.
3. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Designed to fit in one context window as an inventory and contract-writing task.

## Change Log

### 2026-07-27

1. Created task.
