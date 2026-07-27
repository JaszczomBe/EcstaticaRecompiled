# Add Backend Presentation Hook

Status: completed
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

Completed with `E2R_HostPresentIndexed8`, a backend API that accepts indexed-8 pixels selected by native/runtime probe code. The SDL implementation owns conversion to grayscale ARGB and presentation through the SDL3 window-surface path. The X11 backend keeps a no-op return so existing default probes remain unchanged.

The first smoke probe is intentionally synthetic and bounded:

```text
SDL_VIDEODRIVER=dummy build/linux-clang-sdl-debug/e2recomp --host-backend-present-probe
```

It proves a `64x64` indexed-8 frame reaches the SDL presentation path and reports `hash=a92a7045`. Real recovered framebuffer selection remains owned by the existing native dump helpers; `/tmp` PGM dump probes are still the source of truth for current scene evidence.

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
2. Implementation state: accepted
3. Notes: First presentation hook is deliberately grayscale/indexed-8 only; palette fidelity and page-flip semantics remain outside this task.

## Change Log

### 2026-07-27

1. Created task.
2. Added `E2R_HostPresentIndexed8` and implemented SDL3 window-surface presentation.
3. Added and passed `--host-backend-present-probe` while keeping PGM dumps unchanged.
