# Document Bootstrap Requirements

Status: planned
Parent Step: [Package Reproducible Developer Runtime](../step-06-package-reproducible-developer-runtime.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Document the local setup required to build and launch the SDL developer runtime from a fresh checkout.

## Scope

1. Submodule initialization.
2. 32-bit toolchain expectations.
3. Original data directory and build-tree data link.
4. VS Code launch entries.

## Subtasks

1. Record `dep/SDL` submodule expectations.
2. Record required CMake presets.
3. Record data path assumptions.
4. Record the preferred F5 entry for live presentation.
5. Link the runtime regression script.

## Out Of Scope

1. Installer creation.
2. Game data redistribution.

## Implementation Notes

Keep setup docs aligned with actual presets and `.vscode` files.

## Acceptance Criteria

1. A fresh context can find the SDL runtime setup.
2. Bootstrap steps are linked from the implementation.

## Verification

1. Documentation review.
2. `cmake --list-presets`.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: First packaging task.

## Change Log

### 2026-07-28

1. Created task.
