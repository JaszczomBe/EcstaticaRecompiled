# Capture SDL F5 Baseline

Status: planned
Parent Step: [Stabilize Interactive SDL F5 Runtime](../step-01-stabilize-interactive-sdl-f5-runtime.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Record the exact behavior of the `Ecstatica Recompiled (SDL)` launch entry under VS Code F5.

## Scope

1. Confirm the selected launch entry is `Ecstatica Recompiled (SDL)`.
2. Capture console output and call stack if it crashes.
3. Note whether a window appears, updates, freezes, or closes.

## Subtasks

1. Ask the user for the latest F5 console/call stack if not already provided.
2. Compare the launch entry against `.vscode/launch.json`.
3. Record the executable, working directory, arguments, and backend build tree.
4. Classify the observed result as crash, hang, visual-only issue, or stable launch.

## Out Of Scope

1. Fixing the crash.
2. Adding new probes.
3. Rendering fidelity.

## Implementation Notes

This task is evidence capture. Do not infer that an old default-backend crash still applies to the SDL route without fresh output.

## Acceptance Criteria

1. The baseline includes exact console output or an explicit "no crash observed" note.
2. The launch configuration has been checked against the recorded run.
3. The next task has a concrete reproduction target.

## Verification

1. Review `.vscode/launch.json`.
2. Review user-provided F5 output.

## Review State

1. Planning state: agreed
2. Implementation state: not_started
3. Notes: First task for the new implementation.

## Change Log

### 2026-07-28

1. Created task.
