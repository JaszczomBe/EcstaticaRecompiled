# Begin DirectSound Compatibility

Status: planned
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Map the reconstructed runtime's DirectSound startup behavior and define the first replaceable audio compatibility/backend boundary.

## Why This Step Exists

Audio was intentionally stubbed while startup, gameplay, input, and presentation were unstable. With live SDL runtime work underway, sound can be introduced as a bounded compatibility surface instead of a source of opaque crashes.

## Scope

1. Map DirectSound creation, buffer, and playback calls reached during startup/gameplay.
2. Decide which behavior belongs to DirectSound compatibility and which belongs to the host backend.
3. Implement a silent or first-buffer-safe path before real playback.

## Out Of Scope

1. Complete audio fidelity.
2. Music streaming accuracy.
3. Mixer latency tuning.

## Usage Budget

Stop after first-buffer-safe behavior if real playback needs a larger asset or format investigation.

## Temporary Sacrifices

1. Sacrifice: Silent success is acceptable before real playback.
2. Why accepted now: Startup and gameplay stability matter more than noisy partial audio.
3. Removal trigger: Buffer format and ownership are recovered enough to submit PCM to a backend.

## Tasks

1. [Map DirectSound Startup Calls](tasks/task-01-map-directsound-startup-calls.md) - planned.
2. [Define Audio Backend Contract](tasks/task-02-define-audio-backend-contract.md) - planned.
3. [Verify Silent And First Buffer Paths](tasks/task-03-verify-silent-and-first-buffer-paths.md) - planned.

## Acceptance Criteria

1. DirectSound call ownership is documented.
2. Startup/gameplay audio calls no longer rely on unexplained stubs.
3. Existing runtime probes remain stable.

## Verification

1. Startup/F5 route.
2. Runtime regression script.
3. SDL backend build.

## Notes

This step should not start by wiring SDL audio directly. Recover the DirectSound-facing contract first.

## Change Log

### 2026-07-28

1. Created step.
