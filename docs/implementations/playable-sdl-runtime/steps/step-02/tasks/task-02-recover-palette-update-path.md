# Recover Palette Update Path

Status: planned
Parent Step: [Recover DirectDraw Page And Palette Semantics](../step-02-recover-directdraw-page-and-palette-semantics.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Recover enough palette state for SDL presentation to color indexed-8 frames intentionally.

## Scope

1. Find palette creation and update entry points.
2. Map the active palette owner used by presented surfaces.
3. Add a backend-facing palette handoff only after compatibility ownership is clear.

## Subtasks

1. Inspect DirectDraw palette shim functions.
2. Trace palette writes during title/menu startup.
3. Trace palette writes during Start Game transition.
4. Define the minimal palette data passed to the host backend.
5. Verify colorized output against stable hashes or screenshots.

## Out Of Scope

1. Palette animation perfection.
2. Gamma/monitor calibration.
3. Audio.

## Implementation Notes

Do not bake palette behavior into SDL. The compatibility layer should expose the active palette to the backend because other backends need the same information.

## Acceptance Criteria

1. Active palette state is identified.
2. SDL presentation can use recovered palette data.
3. Grayscale fallback remains available for missing palette state.

## Verification

1. SDL presentation probe.
2. Live-frame gameplay probe.
3. Default runtime regression script.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Starts after page ownership is mapped.

## Change Log

### 2026-07-28

1. Created task.
