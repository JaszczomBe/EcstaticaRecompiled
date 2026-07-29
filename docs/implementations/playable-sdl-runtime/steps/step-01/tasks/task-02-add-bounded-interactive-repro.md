# Add Bounded Interactive Repro

Status: completed
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

## Reproduction Evidence

Manual real-display command-line route, run from `build/linux-clang32-sdl-debug` on 2026-07-28:

```text
timeout 20s ./e2recomp --run-recon
```

Result: the SDL runtime opened and reproduced the same default console archive parser diagnostics observed under F5. No crash or call stack appeared. The process stayed alive after the timeout wrapper did not terminate the SDL route cleanly and was manually killed. This matches the prior Step 14 timeout-wrapper caveat, so the real-display route remains a manual stability confirmation rather than the automated bound.

Automated bounded SDL route, run outside the sandbox after the sandboxed dummy-driver run exited `159` with no output:

```text
env SDL_VIDEODRIVER=dummy ./e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step01-sdl-bounded space,num8 6 10000 180 1
```

Result: exit `0`. The probe posted `space`, reached control-ready gameplay, posted `num8`, latched `move=[1,0,0,0,0,0,0,0,0]`, dumped surface 3 as nonblank, and recorded `hash=3615add9`.

Key proof lines:

```text
gameplay-control wait satisfied after 1260 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_00643650=0 _DAT_0073cc3c=0x67d8c4
input state after dispatch wait: ... DAT_00479de8=1 move=[1,0,0,0,0,0,0,0,0] ... _DAT_0073cc3c=0x67d8c4
surface 3 nonblank=1 hash=3615add9
```

The bounded automated frontier is stable gameplay/presentation proof under the SDL backend. The remaining real-display issue from F5 is visual fidelity, not launch stability.

## Acceptance Criteria

1. The observed F5 behavior has a repeatable bounded command when feasible.
2. The command distinguishes runtime failure from sandbox/display failure.
3. The command leaves useful logs or proof strings.

## Verification

1. Bounded SDL reproduction command.
2. `git diff --check` if files change.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: Real-display route reproduced the no-crash/log frontier but did not terminate cleanly through `timeout`; the existing SDL dummy-driver gameplay probe provides the automated bounded proof.

## Change Log

### 2026-07-28

1. Created task.
2. Activated after the user-provided SDL F5 baseline showed a stable window with logo and partial city frames, no crash, and default archive parser console diagnostics.
3. Completed with an SDL dummy-driver gameplay probe that exits `0`, reaches control-ready gameplay, latches movement, and dumps nonblank surface 3 `hash=3615add9`.
