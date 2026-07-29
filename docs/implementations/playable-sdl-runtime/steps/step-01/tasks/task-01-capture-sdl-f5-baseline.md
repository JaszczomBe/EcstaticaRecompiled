# Capture SDL F5 Baseline

Status: completed
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

## Baseline Evidence

Manual VS Code F5 baseline, reported 2026-07-28:

1. Launch entry: `Ecstatica Recompiled (SDL)`.
2. Program: `${workspaceFolder}/build/linux-clang32-sdl-debug/e2recomp`.
3. Arguments: `--run-recon`.
4. Working directory: `${workspaceFolder}/build/linux-clang32-sdl-debug`.
5. Pre-launch task: `CMake: Build SDL 32-bit`.
6. Window behavior: SDL window appears and updates.
7. Visual behavior: the window shows the Ecstatica II logo, then a partial city/gameplay-like frame.
8. Crash behavior: no crash observed and no call stack captured.
9. Console behavior: default console prints repeated `FAN header mismatch` and `archive resource parse` lines around archive offsets `56256` through `56368`.

Representative console lines:

```text
FAN header mismatch: value=08420000 offset=56260
archive resource parse: input=56256 mapped=56256 result=0 final=56260 remaining=33019346
FAN header mismatch: value=000c0000 offset=56264
archive resource parse: input=56260 mapped=56260 result=0 final=56264 remaining=33019342
archive resource parse: input=56364 mapped=56364 result=0 final=56368 remaining=33019238
```

Classification: stable SDL F5 launch baseline with visual fidelity issues. The first observed technical frontier is not a crash; it is likely DirectDraw page/palette/front-buffer ownership, with separate low-priority log hygiene for archive parser diagnostics leaking into default console output.

## Acceptance Criteria

1. The baseline includes exact console output or an explicit "no crash observed" note.
2. The launch configuration has been checked against the recorded run.
3. The next task has a concrete reproduction target.

## Verification

1. Review `.vscode/launch.json`.
2. Review user-provided F5 output.

## Review State

1. Planning state: agreed
2. Implementation state: completed
3. Notes: User-provided SDL F5 baseline captured. Continue with command-line bounded reproduction before classifying the frontier.

## Change Log

### 2026-07-28

1. Created task.
2. Captured manual SDL F5 baseline: window appears, logo and partial city frame present, no crash or call stack, archive parser diagnostics print in the console by default.
