# Verify Silent And First Buffer Paths

Status: planned
Parent Step: [Begin DirectSound Compatibility](../step-05-begin-directsound-compatibility.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Prove the DirectSound compatibility path is stable whether it remains silent or submits the first recovered buffer.

## Scope

1. Run startup/menu/gameplay probes after audio compatibility changes.
2. Confirm no audio path reintroduces crashes or noisy logs.
3. Record the next audio fidelity frontier.

## Subtasks

1. Run default debug/ASan regressions.
2. Run SDL runtime route.
3. Check audio diagnostics or proof strings.
4. Document whether real playback is active, silent, or deferred.

## Out Of Scope

1. Full music playback.
2. Audio/video sync.

## Implementation Notes

Passing silently is acceptable if the compatibility behavior is explicit and stable.

## Acceptance Criteria

1. Audio path does not regress startup or gameplay.
2. Silent or first-buffer behavior is documented.
3. Next audio work has a concrete target.

## Verification

1. Runtime regression script.
2. SDL F5 smoke route.
3. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Final task for Step 5.

## Change Log

### 2026-07-28

1. Created task.
