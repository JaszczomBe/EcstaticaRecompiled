# Define Audio Backend Contract

Status: planned
Parent Step: [Begin DirectSound Compatibility](../step-05-begin-directsound-compatibility.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Define the smallest backend audio API needed by recovered DirectSound compatibility behavior.

## Scope

1. Decide buffer creation, lock/unlock, play, stop, and volume responsibilities.
2. Add backend API declarations only for required behavior.
3. Implement safe default and SDL placeholders or first-buffer support.

## Subtasks

1. Convert mapped DirectSound behavior into backend requirements.
2. Add a minimal host-backend audio contract.
3. Keep no-backend/default behavior deterministic.
4. Add SDL implementation only for the proven contract.
5. Build default and SDL targets.

## Out Of Scope

1. Music sequencing.
2. 3D/spatial audio.
3. Latency tuning.

## Implementation Notes

The contract should be DirectSound-shaped at the compatibility boundary and host-shaped only below the backend boundary.

## Acceptance Criteria

1. Audio API has concrete compatibility callers.
2. No direct SDL calls enter reconstructed code.
3. Builds remain green.

## Verification

1. Default build.
2. SDL build.
3. Runtime smoke probe.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Activated after DirectSound calls are mapped.

## Change Log

### 2026-07-28

1. Created task.
