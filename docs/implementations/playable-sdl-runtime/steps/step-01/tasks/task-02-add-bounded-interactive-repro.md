# Add Bounded Interactive Repro

Status: planned
Parent Step: [Stabilize Interactive SDL F5 Runtime](../step-01-stabilize-interactive-sdl-f5-runtime.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Turn the observed SDL F5 behavior into a bounded command or probe that can be rerun without manual debugger setup.

## Scope

1. Reproduce the launch path from `build/linux-clang32-sdl-debug`.
2. Add a focused runtime flag or script only if existing probes cannot express the observed failure.
3. Keep any new diagnostics opt-in and quiet by default.

## Subtasks

1. Run the existing raw SDL `--run-recon` route.
2. Add timeout or frame-count bounds around the observed scenario.
3. If input is needed, reuse the existing key-sequence probe machinery.
4. If presentation evidence is needed, reuse `E2R_PRESENT_DIAG=1`.
5. Record the exact success/failure strings to assert in later regressions.

## Out Of Scope

1. Broad regression harness redesign.
2. Long-play automation.
3. Direct rendering or audio changes.

## Implementation Notes

Prefer extending existing runtime probe paths over adding a new standalone harness. If the failure only reproduces under VS Code/gdb, document that constraint clearly.

## Acceptance Criteria

1. The observed F5 behavior has a repeatable bounded command when feasible.
2. The command distinguishes runtime failure from sandbox/display failure.
3. The command leaves useful logs or proof strings.

## Verification

1. Bounded SDL reproduction command.
2. `git diff --check` if files change.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Activated after baseline capture.

## Change Log

### 2026-07-28

1. Created task.
