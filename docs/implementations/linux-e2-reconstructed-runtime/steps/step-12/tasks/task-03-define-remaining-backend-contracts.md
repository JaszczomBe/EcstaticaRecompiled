# Define Remaining Backend Contracts

Status: completed
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

Completed as a documentation-first task. No code movement was needed because the current contracts are still ownership decisions rather than stable implementation seams.

Contract summary:

1. Timing: Win32 names and return semantics remain in compatibility; backend sleep/monotonic-time helpers are deferred until SDL/event-loop timing needs them.
2. Presentation: legacy framebuffer page state and DirectDraw-like semantics remain compatibility/reconstructed state; backend presentation should consume established framebuffer/palette state later without replacing probe dumps.
3. Audio: MIDI/MMIO/DirectSound API shapes remain compatibility; actual device/mixer behavior is deferred until runtime paths prove the needed semantics.

Deferred backend API candidates:

```text
E2R_HostSleepMilliseconds
E2R_HostMonotonicMilliseconds
E2R_HostPresentIndexedFrame
E2R_HostAudioInit
E2R_HostAudioSubmit
E2R_HostAudioShutdown
```

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
2. Implementation state: accepted
3. Notes: Completed in one context window as an inventory and contract-writing task.

## Change Log

### 2026-07-27

1. Created task.
2. Documented timing, presentation, and audio backend ownership decisions in Step 12 and marked the task completed.
