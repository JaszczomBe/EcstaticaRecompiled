# Add Backend Presentation Hook

Status: planned
Parent Step: [Add SDL Host Backend](../step-13-add-sdl-host-backend.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Define and add the first backend-owned presentation hook for legacy framebuffer pages without replacing developer probe dumps.

## Scope

1. Identify the current framebuffer ownership and page-selection semantics used by probes.
2. Add a backend presentation API only after Step 12 has assigned ownership.
3. Implement the smallest SDL presentation path that can display the current 8-bit framebuffer state.
4. Keep `/tmp` PGM dump probes unchanged.

## Out Of Scope

1. Pixel-perfect DirectDraw page flipping.
2. Palette animation fidelity beyond the minimum display proof.
3. SDL audio.
4. Full renderer replacement.

## Implementation Notes

Presentation is higher risk than window/input. Start with an inspectable host display path and preserve the existing `--dump-surfaces` evidence as the source of truth.

## Acceptance Criteria

1. Presentation ownership is documented before code changes.
2. SDL presentation uses backend APIs, not reconstructed game calls.
3. Existing surface dump probes still work.

## Verification

1. SDL build from task 01.
2. A bounded SDL presentation smoke probe.
3. `scripts/run-e2-runtime-regressions.sh`.
4. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Split further if palette or page-flip fidelity becomes a separate recovery problem.

## Change Log

### 2026-07-27

1. Created task.
