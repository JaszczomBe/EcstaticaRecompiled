# Stabilize Interactive SDL F5 Runtime

Status: active
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Make the `Ecstatica Recompiled (SDL)` F5 route produce a clear, reproducible stability frontier instead of relying on manual observation alone.

## Why This Step Exists

The reconstructed runtime can now reach gameplay and present live SDL frames, but the user-facing F5 route is the path that will expose real interactive crashes and visual problems. This step turns that route into bounded evidence.

## Scope

1. Capture the user's current F5 result and console output.
2. Reproduce the same route from the command line where possible.
3. Separate debugger/display issues from runtime crashes.
4. Add the smallest bounded probe needed to preserve the new frontier.

## Out Of Scope

1. Rendering fidelity.
2. Audio behavior.
3. Long-play testing beyond the first stable interactive frontier.

## Usage Budget

Keep this step to one crash/frontier family. If a second unrelated crash appears, document it and split.

## Temporary Sacrifices

1. Sacrifice: Manual F5 visual confirmation remains part of the evidence.
2. Why accepted now: Automated display capture is not yet part of the runtime harness.
3. Removal trigger: A later developer-runtime package can run an SDL screenshot/surface proof in CI-like form.

## Tasks

1. [Capture SDL F5 Baseline](tasks/task-01-capture-sdl-f5-baseline.md) - planned.
2. [Add Bounded Interactive Repro](tasks/task-02-add-bounded-interactive-repro.md) - planned.
3. [Classify First Interactive Frontier](tasks/task-03-classify-first-interactive-frontier.md) - planned.

## Acceptance Criteria

1. F5 behavior is recorded with exact launch entry, command, and console output.
2. The first failure or stable boundary has a bounded reproduction.
3. Existing debug/ASan regressions remain green after any repair.

## Verification

1. `cmake --build --preset linux-clang32-sdl-debug`
2. Raw SDL `--run-recon` reproduction command.
3. `scripts/run-e2-runtime-regressions.sh`
4. Manual `Ecstatica Recompiled (SDL)` F5 check.

## Notes

The first implementation action should start from the newest user-provided F5 console and call stack, not from older default-backend crash logs.

## Change Log

### 2026-07-28

1. Created step.
