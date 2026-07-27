# Package Reproducible Developer Runtime

Status: planned
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Make the SDL developer runtime easy to recreate, validate, and hand off from a fresh checkout.

## Why This Step Exists

The runtime now depends on a vendored SDL submodule, multiple build presets, runtime data links, and a growing set of probes. A clear bootstrap and validation workflow prevents future sessions from rediscovering setup details.

## Scope

1. Document clone/submodule/bootstrap requirements.
2. Add or refine a developer validation script.
3. Record expected launch entries, probes, and known caveats.

## Out Of Scope

1. End-user installer packaging.
2. Cross-platform binary releases.
3. CI service integration unless already available locally.

## Usage Budget

Keep packaging work to local developer reproducibility. Split if real release packaging starts.

## Temporary Sacrifices

1. Sacrifice: Developer runtime still expects local original game data.
2. Why accepted now: Redistribution and installer design are outside the reconstruction/debugging scope.
3. Removal trigger: A later release-packaging implementation defines legal data discovery and user setup.

## Tasks

1. [Document Bootstrap Requirements](tasks/task-01-document-bootstrap-requirements.md) - planned.
2. [Add Developer Validation Script](tasks/task-02-add-developer-validation-script.md) - planned.
3. [Record Release Readiness Gate](tasks/task-03-record-release-readiness-gate.md) - planned.

## Acceptance Criteria

1. Fresh-checkout setup is documented.
2. One command validates the expected developer runtime surface.
3. Known manual checks and caveats are explicit.

## Verification

1. Bootstrap documentation review.
2. Developer validation script.
3. Existing runtime regression script.

## Notes

This step should make the workflow boring, not hide unstable runtime behavior.

## Change Log

### 2026-07-28

1. Created step.
