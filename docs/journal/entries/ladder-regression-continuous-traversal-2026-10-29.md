# Continuous ladder regression traversal — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 12 Task 05](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md).
Evidence: `.tmp/ladder-visible-traversal-20261029/`. No commit or push.
This follows the [required ladder regression](ladder-regression-and-headless-audio-policy-2026-10-29.md).

## Report and diagnosis

The user's visible Debug/headless ASan run reports 7/8 PASS in
`.tmp/gameplay-suite/run_20261029_184651_130250/`. Both Debug ladder directions
actually pass: scenes761→762 and763→764, life95, correct landings and restored
turning. Debug then fails in `setup.MenuExit`: Quit leaves requester0x28 active
instead of opening confirmation0x14. It is a probe lifecycle failure after the
interaction, not a failed descent/ascent. The full case correctly remains failed.

The separate `LadderJourney.walk` releases all input and advances four updates
at every point. The floor-planned route visits120 points, producing the reported
stop/start movement. Debug sends448 keyboard transitions, including110 forward
releases across the full journey. Reaching both landings does not excuse this
navigation behavior. The user requests the existing traversal helper and the
recorded route as loose position guidance.

## Continuous shared traversal and safe approach

`e2_ladder_steps.py` now calls the existing `Journey.walk` once for one connected
route. The duplicate walker and per-node floor planning are removed. The shared
helper retains its existing steering, bounded attempts and update limits. It
holds movement between intermediate points and releases at route completion.
There are no changes to the shared walker or reconstructed game code.

`scripts/scenarios/stables-ladder-waypoints.json` retains55 selected positions,
source snapshot identities and inspection hashes from session182427_259.
Combat pauses and loops are omitted. The regression observes current position
and yaw to steer ordinary SDL arrows; it does not reproduce input timing, RNG,
health, progression or saved state. Each reached waypoint still records the
population census. No scene, coordinate, life or power assignment is used.

The recorded endpoint is close to the kitchen drop. Initial continuous-route
attempts coast beyond the upper floor during braking/alignment. `headless-r1`
and `headless-r2` retain the failure; the second observes camera723, life78,
state8 and action644 after falling rather than running the ladder scenes.
`visible-r3` retains another facing failure, although headless ASan completes
both directions. These attempts are not accepted. Facing now rejects death
states as well as nonpositive health and preserves the observed failure state.

The final approach preserves two additional recorded corner positions and aims
inside the original upper ladder tile, at(-18176,4096,-13568), leaving room to
brake before turning. The fixture explicitly distinguishes this guidance target
from source snapshot1743's actual position. The original tile/script, facing
predicate, Space interaction, animations and destinations remain unchanged.

## Complete SDL menu gesture

`MenuJourney.click` previously injected only button-down and assumed an80-pixel
top letterbox. It now converts logical item coordinates through the current SDL
presentation rectangle and queues motion, left-button down and left-button up.
It records the actual mapping in the input report. Normal host processing and
the existing requester assertions still judge the result; there is no direct
menu-state change or retry that hides a failure. This repairs the shared probe
gesture and handles resized presentation rectangles. The earlier failure's
exact timing is not reconstructed from its log, which lacks this mapping detail.

## Final acceptance

Both final shared ladder selections pass8/8, with no failures, blocks or skips:

| Evidence | Display | Time | Debug arrival/climb life | ASan arrival/climb life |
| --- | --- | --- | --- | --- |
| `visible-r4/report.json` | Visible Debug, headless ASan | 59.17s | 85→85→85 | 100→100→100 |
| `visible-asan-final/report.json` | Headless Debug, visible ASan | 58.84s | 100→100→100 | 100→100→100 |

The complementary run uses `--build`; both retain the previously pinned native
binaries. Every process observes both required scene pairs, camera723/y6656 and
camera725/y4096, positive unchanged climb health, resumed turning, zero host
audio frames and native exit0. Save/Load guards remain installed, private save
directories stay empty and installed save hashes remain unchanged. Authored
projectiles remain active; arrival health may vary and is never repaired.

Visible Debug now sends274 keyboard transitions and26 forward releases across
the full journey, compared with448 and110 in the user's run. All55 waypoint
observations retain forward held. Turns can still require braking, and route
completion deliberately releases input; there are no forced stops at intermediate
waypoints. This is bounded navigation evidence, not full visual acceptance.

`menu-checks/report.json` separately passes6/6 selected Debug/ASan cases,
including gameplay Show/Hide, Quit cancellation, Settings and clean lifecycle.
All71 suite contracts pass. New contracts verify continuous held movement across
collinear points, bounded stalled traversal, and complete mouse gestures mapped
through three presentation sizes/letterboxes. Python syntax, whitespace and the
305-document README tree pass.

The evidence root retains all failed attempts, final reports, harness sources,
input metrics and the initial staged/worktree patches. The staged patch remains
byte-for-byte unchanged. Existing saves, recordings, invalid-save retirement,
ordinary F5 selection and audio policy are preserved. No game-code or generator
change is made in this continuation.

Landing Save/Load, other ladders, broader visual fidelity, zero-life control and
wider play remain open. Invalid or manually patched saves and descendants
**MUST NOT** be used to reconstruct game functionality or accept progression;
the positional session guide does not reinstate any withdrawn save-based result.
