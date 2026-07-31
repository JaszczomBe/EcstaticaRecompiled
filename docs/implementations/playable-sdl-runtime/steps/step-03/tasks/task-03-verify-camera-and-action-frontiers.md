# Verify Camera And Action Frontiers

Status: planned
Parent Step: [Expand Gameplay Control And Camera Proofs](../step-03-expand-gameplay-control-and-camera-proofs.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-31

## Goal

Classify what camera/action behavior is reachable after the control matrix lands.

## Scope

1. Run the control matrix against SDL and default builds.
2. Identify action/camera state changes or the next blocking crash.
3. Record a concise next frontier.

## Subtasks

1. Compare debug and ASan probe output.
2. Compare SDL and default backend behavior when presentation is active.
3. Capture call stacks for any new crash.
4. Update the step with accepted controls and remaining unknowns.

## Out Of Scope

1. Fixing every action-system crash.
2. Combat or inventory fidelity.

## Implementation Notes

This closeout should keep the next action crisp: either continue control fidelity or split to a specific runtime crash repair.

Current pre-closeout frontier: `Space` during the intro latches in game state but natural-completes into scene `7` and missing actor `3853`; `Esc` enters requester/menu state and presents a menu with broken contents. Do not close this step until those two paths are either repaired or deliberately split into source-backed follow-up steps.

## Acceptance Criteria

1. Accepted controls are listed.
2. Remaining frontier has a command and owner layer.

## Verification

1. Control matrix probes.
2. Runtime regression script.
3. Manual SDL F5 smoke check if the route is stable.

## Review State

1. Planning state: discussed
2. Implementation state: not_started
3. Notes: Final task for Step 3; not ready until intro `Esc`/`Space` behavior is classified.

## Change Log

### 2026-07-28

1. Created task.

### 2026-07-31

1. Added the current intro action/requester frontier as the required pre-closeout evidence.
