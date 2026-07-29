# Classify First Interactive Frontier

Status: completed
Parent Step: [Stabilize Interactive SDL F5 Runtime](../step-01-stabilize-interactive-sdl-f5-runtime.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Decide whether the first SDL F5 issue belongs to runtime reconstruction, Win32/DirectDraw compatibility, SDL backend behavior, debugger/display setup, or documentation.

## Scope

1. Use the bounded repro and call stack to identify the owning layer.
2. Make one focused repair when the owner is clear.
3. Record the next frontier when the owner is not yet clear.

## Subtasks

1. Map the top frames of any crash to reconstructed, compatibility, or backend source.
2. Check whether the default debug route reproduces the same issue.
3. Check whether SDL dummy-driver probes reproduce the same issue.
4. If a generated-code repair is needed, mirror it in `GenerateRecon.js`.
5. If a backend repair is needed, keep the API boundary stable unless the task proves a missing contract.
6. Update this step with the fixed or remaining frontier.

## Out Of Scope

1. Multiple unrelated runtime fixes.
2. DirectDraw fidelity work after the first stability frontier.
3. Audio.

## Implementation Notes

This is the gate between launch stabilization and the later fidelity steps. A clear crash fix can land here; ambiguous visual accuracy work should move to Step 2.

## Classification

Owner: DirectDraw compatibility semantics, specifically page selection, palette ownership, and front-buffer presentation.

Evidence:

1. Manual `Ecstatica Recompiled (SDL)` F5 opens a window, presents the logo and then a partial city/gameplay-like frame, and does not crash.
2. Real-display command-line `./e2recomp --run-recon` from `build/linux-clang32-sdl-debug` reproduces the same console/log frontier and stays alive.
3. Automated SDL dummy-driver gameplay probe exits `0`, reaches control-ready gameplay, latches movement, and dumps nonblank surface 3 `hash=3615add9`.
4. The visible output is grayscale/incorrectly colored and still depends on the first-live-frame page heuristic documented in the previous SDL presentation milestone.

Result: Step 1 has a stable launch boundary, not a runtime crash frontier. No generated-code or SDL-backend stability repair is needed in this step. The next implementation step should recover DirectDraw page/palette/front-buffer semantics. Archive parser console diagnostics remain a secondary log-hygiene issue unless they interfere with future bounded assertions.

## Acceptance Criteria

1. The first frontier has an owner and evidence.
2. Any fix is covered by default and SDL checks.
3. The next step can start from a stable or clearly documented launch state.

## Verification

1. Bounded repro after repair or classification.
2. `scripts/run-e2-runtime-regressions.sh`
3. SDL probe relevant to the touched layer.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: First SDL interactive frontier classified as DirectDraw page/palette/front-buffer fidelity. Continue with Step 2 Task 1.

## Change Log

### 2026-07-28

1. Created task.
2. Activated after bounded SDL reproduction passed and the manual F5 route showed no crash.
3. Completed classification: stable SDL launch, no crash repair needed, next owner is DirectDraw compatibility fidelity.
