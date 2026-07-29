# Recover DirectDraw Page And Palette Semantics

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Replace first-live-frame grayscale heuristics with recovered DirectDraw-facing page, front-buffer, and palette behavior.

## Why This Step Exists

Live SDL presentation currently proves that real recovered frames can reach the backend, but it still depends on selection heuristics and grayscale indexed-8 conversion. A playable runtime needs the compatibility layer to know which page should be visible and which palette should color it.

## Scope

1. Map recovered DirectDraw surface/page ownership.
2. Recover palette update paths and dirty state.
3. Present the intended front buffer through the backend.
4. Keep PGM frame probes useful as regression artifacts.

## Out Of Scope

1. Renderer rewrites.
2. Texture filtering or scaling policy.
3. Audio and timing fixes.

## Usage Budget

Split this step if page ownership and palette recovery turn into separate Ghidra investigations.

## Temporary Sacrifices

1. Sacrifice: Keep grayscale presentation until palette ownership is proven.
2. Why accepted now: The current hashes are useful for stability and nonblank-frame proof.
3. Removal trigger: Palette writes and front-buffer ownership are recovered enough to compare colored output.

## Tasks

1. [Map Surface And Page Ownership](tasks/task-01-map-surface-and-page-ownership.md) - active.
2. [Recover Palette Update Path](tasks/task-02-recover-palette-update-path.md) - planned.
3. [Verify Front Buffer Presentation](tasks/task-03-verify-front-buffer-presentation.md) - planned.

## Acceptance Criteria

1. The runtime names the page intended for presentation.
2. Palette state is captured or explicitly proven unchanged for a frame.
3. SDL presentation uses recovered compatibility state instead of only heuristic selection.

## Verification

1. SDL live-frame probe.
2. PGM frame dump comparison.
3. Default debug/ASan regression script.

## Notes

This step should start from existing `E2R_HostPresentIndexed8` and DirectDraw compatibility state, not from direct SDL presentation changes.

Activated after Step 1 proved SDL F5 launch stability: the window presents real frames without crashing, while the visible output remains grayscale/incorrectly colored and page selection still depends on presentation heuristics.

## Change Log

### 2026-07-28

1. Created step.
2. Activated after SDL F5 stabilization classified the first frontier as DirectDraw page/palette/front-buffer fidelity.
