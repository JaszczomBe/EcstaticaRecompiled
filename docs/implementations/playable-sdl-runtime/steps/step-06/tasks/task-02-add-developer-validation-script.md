# Add Developer Validation Script

Status: planned
Parent Step: [Package Reproducible Developer Runtime](../step-06-package-reproducible-developer-runtime.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Provide one local command that validates the expected developer runtime surface.

## Scope

1. Build default and SDL targets needed by developers.
2. Run existing debug/ASan runtime regressions.
3. Run SDL backend probes relevant to launch readiness.

## Subtasks

1. Decide whether to extend `scripts/run-e2-runtime-regressions.sh` or add a separate developer script.
2. Include submodule/preset checks.
3. Include SDL presentation probe.
4. Keep real-display F5 as a manual follow-up.
5. Document expected output.

## Out Of Scope

1. CI provider configuration.
2. Long-play automation.

## Implementation Notes

The script should fail for missing setup and runtime regressions, but it should not require a visible display unless explicitly requested.

## Acceptance Criteria

1. One command validates build and probe readiness.
2. Headless SDL checks use the dummy driver.
3. Manual F5 remains separately documented.

## Verification

1. New or updated validation script.
2. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Activated after bootstrap docs.

## Change Log

### 2026-07-28

1. Created task.
