# Recorded pedestal–courtyard round trip — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Usage: [Gameplay regression suite](../../gameplay-tests.md).

The user reports Regression **04** following a faulty traversal route and records
a correct pedestal → central courtyard → pedestal loop. This continuation changes
test inputs/coverage declarations only. Existing staged/unstaged changes, runtime
C, generator and the preserved animation-name regression remain untouched.

## Source and previous failure

The supplied suite run `.tmp/gameplay-suite/run_20261026_100258_911146/` records
**7 PASS / 1 FAIL**. Debug startup and movement pass; courtyard traversal fails
`Did not cross into camera 166`. ASan passes the short route. The old test tried
Up briefly, then Down, then reversed the chosen key to return. It did not follow
the user's complete route into the central courtyard.

Human session `session_20261026_110852_153` is finalized, native exit **0**, with
complete inspection and a complete recording marker. Executable SHA-256 is
`9818189b760d86c861cf46e4c16706125bca9806246fbd2f5bacd69de5d5aef9`.
The session and matching executable are exported and integrity-verified as
`.tmp/courtyard-route-20261026/human-bundle/`. Original assets remain external.
Inspection evidence establishes:

- Source snapshot **142**, update **1636**: Joe at `(9988,3328,-17408)`, camera
  **175**, healthy and released.
- Outward camera sequence **175 → 166 → 169 → 166 → 176 → 164 → 125**.
  Snapshot **244**, update **2489** reaches `(-6189,4096,-9116)` in the central
  courtyard.
- The separate return path uses **125 → 164 → 176 → 166 → 175**, then climbs
  back to floor **3328**. Final snapshot **400**, update **3411** has Joe at
  `(10154,3328,-17184)`, health **100**, state **4**, action **871**.
- Space is pressed at update **449**, first horseback progress **438/495**.
  This differs from the suite's ordinary delayed skip at **83**.

These are published observations, not an exact-replay verification claim.

## Route and compatible journeys

`scripts/scenarios/courtyard-waypoints.json` materializes **34** samples per leg,
including camera and height transitions, original snapshot/update IDs and
inspection hashes. `Journey.courtyard()` follows each leg continuously through
the existing bounded SDL waypoint controller, observing every reached waypoint.
Its normal **160**-unit guidance tolerance accommodates an actor radius and
live population; coordinates guide input and are never assigned to Joe.

The test preserves the camera-**166** crossing and return camera-**175** /
floor-**3328** assertions. It adds actual central courtyard **125** / floor
**4096** and a final distance below **500** world units from the starting area,
after releasing inputs and advancing another **90** updates. Existing identity,
alive-player, modal, menu exit and completed-inspection gates remain.

Fresh startup state matters. At progress **83**, failed return probes stop near
`(9009,3712,-16331)` while guard **293** occupies `(9365,3584,-16348)`; the human
capture has that guard around `(7734,4096,-18042)`, away from the stairs. A
progress-**438** diagnostic reproduces the latter placement, but later fresh
runs can still place that guard on the stairs. Timing alone does not reproduce
the human population. Movement's turns/modifiers/displacement also alter the
initial situation. A trial split into fresh startup-438 and movement journeys
therefore still fails ASan's return; this is retained rather than counted as
accepted compatibility.

The final route reads live guard **293** after the ground-level return segment.
If it occupies the recorded stair region, a separately declared, bounded set of
SDL guidance points passes around its position and rejoins the human pedestal
endpoint. Otherwise the original return samples are used. The clearance points
are navigation guidance, not published human samples; their journal observations
have `snapshot: null`. No actor, health, clock, RNG, camera or population state is
assigned. Guard position and the chosen branch are retained in shared evidence.
If preceding movement finishes on the steps, the bounded pedestal approach
walks back through that corridor before checking starting camera/floor. This
addresses a route setup difference without assuming state restoration.
The ordinary waypoint attempt/update/host bounds still apply; no failed route
is restarted or silently retried.

This preserves the original progress-83 startup/movement/courtyard shared journey:
**eight** logical results and **two** gameplay processes for Regression **04**,
one per configuration. Each logical assertion runs once. Full selection remains
**182** cases and **20** gameplay processes. The human skip timing is provenance,
not startup credit or a state-restoration mechanism. The route asset is included
in source hashes, and isolated diagnostic execution uses the same route policy.

## Development evidence and limits

Evidence root: `.tmp/courtyard-route-20261026/`. Fresh probes use recording
**off**, bounded input/update/host limits and isolated inspection. Retained
development failures are not retried unchanged until green:

| Directory | Observation |
| --- | --- |
| `route-first/` | The first sampled route reaches central camera 125 in both builds, but stopping at every waypoint and using startup 83 stalls on the return stairs; 6 PASS / 2 FAIL |
| `continuous-route/` | Continuous input with overly tight 60-unit guidance fails ASan's initial anchor and Debug's occupied stair waypoint; 6 PASS / 2 FAIL |
| `recorded-startup/` | At skip 438, guard 293 remains away from the stairs, but 60-unit guidance asks Joe to enter another actor's occupied radius near `(108,-13452)`; diagnostic failure retained |
| `recorded-compatible-debug/`, `recorded-compatible-asan/` | Continuous route at recorded startup with normal guidance completes both legs, menu Quit, native exit 0 and complete inspection in each build |
| `movement-final/` | Combining movement with startup 438 changes the route's initial state; 6 PASS / 2 FAIL |
| `movement-accepted/` | Despite the provisional directory name, the split-startup trial is **red**, 7 PASS / 1 FAIL; fresh ASan still encounters guard 293 on the stairs |
| `stair-clearance-asan/` | Progress-83 diagnostic completes the loop and clean exit with the original stair branch; guard placement is observed outside the clearance region |

The final default block, `movement-clearance/`, passes **8/8** in **69.68 seconds**:
one shared process per configuration, Debug visible and ASan headless. Both use
the ordinary progress-**83** startup. All native exits are **0**, and inspections
are complete. Both runs select the original stair branch, so that result alone
does not accept the alternative path.

`clearance-path-asan/` explicitly selects the alternate **input path**, with
`courtyard_stair_clearance: true`. Live guard 293 is at `(8945,3840,-16680)` in
the stair region, and the diagnostic observes `occupied: true`, `diagnostic:
true`, `used: true`. Movement, both legs, return camera/floor/area, actual menu
Quit, native exit **0** and completed inspection pass. The diagnostic changes
input policy, not actor or population state. Its synthetic clearance guidance
retains null source snapshot IDs. The first Debug alternate-path attempt instead
fails the initial floor check after movement; the subsequent input-only pedestal
approach is validated separately. These failed/changed attempts remain explicit.
`clearance-and-approach-debug/` validates that approach from
`(9012,3712,-16385)`, then the full loop with the alternate return input path.
Both selected checkpoints pass, native exit is **0**, and inspection is complete.
Guard occupancy is false at its return gate, while the explicit diagnostic
selector still exercises the alternate physical route. Together these examples
cover the original path, observed occupied stairs, the diagnostic selector and
the post-movement approach without state assignments.

The test suite's contracts verify camera/floor/return-area failures rather than
accepting waypoint guidance alone, including the guard-clearance branch. Shared selection and executor contracts
verify the original progress-83 startup/movement assertions remain in one process. All **42** runner contracts pass, including displaced-start setup, clear/occupied
stair selection, the explicit diagnostic selector and rejection of incorrect
central camera, return floor or return area. The owning task records final
acceptance; the **241-document** README tree and whitespace checks pass.

No full-suite native rerun or general NPC-obstacle avoidance acceptance is claimed.
The earlier menu faults, allocation-pressure stall, separate `FUN_0042f85c` event
fault, bottle-removal/damage-routing limits and source/generator drift remain open.
