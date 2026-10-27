# Swimming route navigation — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Goal-driven regression navigation](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Runtime owner: [Population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Human route: [Water replay and sword pickup](water-replay-and-sword-pickup-2026-10-24.md).
Usage: [Goal-driven gameplay tests](../../gameplay-tests.md#goal-driven-encounter-navigation).

The user supplies swimming block
`.tmp/gameplay-suite/run_20261026_160531_737113/`: Debug visible on Wayland fails
the first water-route waypoint while Joe remains near the pedestal, ASan headless
completes actual swimming. The run reports **7 PASS / 1 FAIL / 2 SKIPPED**,
**52.39 s**, two gameplay processes with concurrent configuration workers.
Armed swimming/shore exit are explicit optional skips and remain outside this fix.

## Observed failure and navigation changes

After the visible Debug movement checks, Joe is at **(8011,3328,-18581)**.
`swimming()` omitted the human route's starting anchor **(9988,3328,-17408)**
and headed directly for its stair point **(9743,3456,-16847)**. The legacy
`walk()` checks heading/distance but has no stuck-progress replanning. Joe reaches
about **(8485,3328,-17943)**, retains forward action **193**, and makes no further
displacement before the **630-update** attempt fails. The particular blocker is
not established by stationarity alone. Debug inspection remains incomplete after
the assertion; the ASan run has a native clean exit and completed inspection.

The shared swimming journey now joins the recorded starting anchor before
following all **47** original samples through the existing bounded navigator.
Their snapshot IDs, camera provenance and coordinates remain unchanged. The join
is explicitly bounded to **4000** units and its observed starting position/distance
is retained. No coordinates, height, camera, health, clock, RNG or actor state
are assigned. Source-backed stair heights remain guidance checked against actual
observations, with stuck/circling detection and bounded local detours. The normal
noncombat population fixture is unchanged and does not freeze colliders.

A failed approach owns `setup.WaterApproach`, blocks the unexercised swimming
assertion and fails the journey. The actual swim still requires camera **543**,
representation **13**, displacement through real Up input, surviving Joe and
released keys. Reaching a waypoint cannot substitute for those assertions.

## Transient water-entry height

The first changed headless run, `headless/`, reaches the water in both builds.
ASan completes swimming; Debug reaches terminal snapshot **338**'s X/Z at
**(-721,4132,-2790)**, camera **543**, but its generic height check rejects the
recorded **4460** sample by **328** units. Debug has traversed the full route,
including six bounded local detours around an unknown stables-region obstruction;
this is a separate terminal-height setup failure, not the original pedestal stall.
The attempt is retained: **7 PASS / 1 BLOCKED / 2 SKIPPED**, **67.22 s**.

The same human session establishes approach height **4096**, entry sample **4460**
and later sustained swimming at **5120** across cameras **543→545**. Thus 4460 is
a moment during the transition, not a stable floor. Only the final route sample
now declares the source-backed interval **[4096,5120]**, with its provenance in
`water-waypoints.json`. `Navigator.follow_route()` validates and records explicit
per-node height intervals; all ordinary nodes retain the normal height band.
Unrelated floors, invalid intervals and an interval on another node cannot bypass
those checks. Actual swimming representation/displacement remain mandatory.
The suite now hashes the water route asset alongside the navigator/probe sources;
the original report had omitted that asset's hash.

Visible navigation uses the suite's existing threefold host-time allowance:
**165 seconds** versus **55** headless, while retaining the same **2400-update**
and **6-replan** bounds. The probe supplies its actual watch-mode boolean to the
journey context; this changes only the host allowance, not game time or pacing.
This avoids treating the visible observer's deliberate pacing as a game failure.

## Native verification

Evidence root: `.tmp/swimming-navigation-20261026/`. `baseline.json` retains the
reported observations and source/binary context; `validation.json` indexes every
attempt, pinned executables, final source hashes, swimming states and inspections.
Inputs are real SDL, recording is explicitly **off**, and all runs use two
configuration workers with sequential gameplay within each lane. Successful
journeys require actual menu Quit, native exit **0** and completed inspection.
No exact replay acceptance is implied.

`transition-height/` passes **8 required checks**, retaining the **2 optional
skips**, in **59.33 s**, two headless gameplay processes. Both follow the anchor
and all route nodes, reach camera **543**, then swim at **5120**, health **100**,
state **4**, representation **13**, with all keys released and complete native
exit/inspection. Debug moves **(-766,4272,-2768)→(-934,5120,-2166)** during the
swimming phase; ASan moves **(-792,4444,-2744)→(-896,5120,-2304)**. Neither needs
a local replan in this fresh run; the previous changed attempt retains its actual
obstacle/stuck evidence rather than being rewritten as a success.

The first `visible-debug/` qualification passes visible Debug, including actual
swimming and clean native exit/inspection. Its ASan headless lane stops during
setup: **7 PASS / 1 BLOCKED / 2 SKIPPED**, **66.92 s**. Three local replans
clear a stables-region obstruction. Later, the ordinary **180-unit** node radius
accepts the dry-bank point **(-551,4096,-3414)** at **(-605,4096,-3585)**.
While steering toward the final water point, Joe moves from
**(-629,4096,-3404)** to **(6404,3200,-3824)** within three updates. Continued
steering ends in fall impact at height **5120**, health **88**, state **8**. The
existing liveness check labels that state “Joe died”; the retained health does
not establish death. No runtime cause for the abrupt displacement is established.

The dry-bank node now declares a tighter **80-unit** tolerance, with single-update
observations within twice that radius, before turning toward water. This is
test-driver guidance around the same recorded point, not a replacement coordinate
or recovered-physics repair. Other nodes retain their ordinary radius and
three-update batches. Routes also stop immediately on observed horizontal
movement over **1024 units** between samples; a discontinuity cannot silently
continue as a connected route. The failed attempt remains retained.

The final frozen-source `bank-corner/` headless qualification passes **8 required
checks / 2 optional skips**, **76.95 s**. Debug uses **2238 updates / 6 replans**,
retaining the unknown stables obstruction and bounded clearance decisions; ASan
uses **1246 updates / 0 replans**. Both reach the tighter bank node, camera **543**
and actual swimming, with native menu Quit, exit **0** and complete inspection.

The matching `bank-corner-visible/` command passes **8 required checks / 0 FAIL /
0 BLOCKED / 2 optional skips**, **68.36 s**, with Debug visible on Wayland and
ASan headless. Visible Debug begins the water approach at
**(7911,3328,-18622)**, reproducing the displaced-pedestal starting condition,
then reaches the anchor and all **47** route nodes. Both builds retain health
**100**, state **4**, swimming representation **13**, released keys, native menu
Quit, native exit **0** and complete inspection:

| Final selection | Build | Navigation updates / replans | Water approach → swimming |
| --- | --- | --- | --- |
| Headless | Debug | 2238 / 6 | (-751,4360,-2752) → (-919,5120,-2307) |
| Headless | ASan | 1246 / 0 | (-763,4236,-2648) → (-1035,5120,-1793) |
| Visible Debug | Debug | 1114 / 0 | (-723,4392,-2710) → (-851,5120,-2225) |
| Visible Debug | ASan | 1231 / 0 | (-785,4400,-2664) → (-933,5120,-2141) |

`validation.json` verifies final source hashes against both final reports, all
original route samples against HEAD, all four pinned native images and complete
inspection/menu exits. It retains the original failure and every changed attempt
with their earlier source identities. An observed PASS with the tighter corner
does not establish a runtime cause or repair for the earlier discontinuity.

Native images retain the reported failure's SHA-256 identities:

- Debug: `df81e8ca950b25d1f2163f495ee8c410c4ef30cdf8c31e3e6251b0ba1b68ee42`.
- ASan: `e2bde1e384582571221e2ee9d6fbe1fc3a671cf87da70df3e26a38b3ec732b50`.

## Contracts and limits

**50** suite contracts and **22** navigator contracts pass. New coverage verifies
the displaced pedestal start still visits the original anchor and all heights,
explicit terminal transition intervals without relaxing earlier nodes, wrong
camera, wrong representation, lack of displacement, blocked/out-of-bounds joins,
setup/BLOCKED versus exercised FAIL reporting, released input and watch-mode
host allowance without expanded update/replan bounds, reaching a narrow corner
before changing nodes with bounded input samples, and immediate released failure
on route discontinuity. Python compilation and whitespace checks pass. The
documentation-tree update and subsequent read-only check both pass with **247**
Markdown documents.

Runtime C, generator, normal F5 behavior and population policy are untouched.
The catalogue remains **185** logical cases / **20** planned full gameplay
processes; the full suite is not rerun. Armed swimming, shore exit, general
navigation, the separate `FUN_0042f85c` event fault, menu/Load/retention problems
and preserved animation-name generator drift remain open. No stage, commit or
push is performed.
