# Water goals and scene navigation — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Goal-driven navigation](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Runtime owner: [Population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Previous acceptance: [Recorded swimming approach](swimming-route-navigation-2026-10-26.md).

The user requests actual water traversal and combat coverage, and challenges the
use of an old human session for reaching water. The previous repair used the
shared observation/input navigator, but its corridor still consisted of **47**
human samples. It exercised only entry and a short forward swim. That acceptance
does not establish water combat, a crossing or armed swimming.

## Scene-derived guidance

`e2_scene_navigation.py` reads a bounded snapshot of the live **128×128** scene
grid, **12-byte** descriptor chains, terrain flags and map scale. The shape,
priority, ceiling gate, surface and floor-height decoding follows original
**0x448744–0x448bdd** and matches all **56** saved real floor inputs used by the
original-code scene-grid fixture. The navigator never invokes the recovered
floor helper: its scripted-block path can write actor **+0x140**.

The bounded A* planner uses a **128-unit** lattice, Joe's observed **256-unit**
collision-radius boundary and at most **40,000** expanded nodes. It conservatively
checks the original motion helper's five forward floor probes and forward-drop
exception, plus possible upper layers within an ordinary step. A full circular
floor band was rejected offline because it disconnected the stairs; the original
directional rule supplies the appropriate boundary.
Ordinary height changes remain bounded to **256**; declared water entry can
descend **1024**, with transition bands derived from the planned land/water
floors. These are planning policies, not a second recovered physics engine.
Real SDL input, actual position/height, mode and survival determine acceptance.

The installed version-55 `Code/ECSTATIC.FAN` supplies the script policy. Its
counted bytecode table is parsed after the eleven name pools and prefix records.
Only complete instruction streams consisting of **PlayScene (7)**,
**StartTune (0x25)**, **ClearAmbiant (0x70)** and **AmbiantSound (0x6f)**, with
the proper argument classes, grant traversal permission. Unknown instructions
and malformed argument classes remain rejected. **718** installed streams pass
that audit. In particular, tile code **681 / dav:swimrep** sets music/ambient
sound; it does not teleport Joe. The terrain selection still invokes original
behavior during actual movement. Allowed scene activation does not remove its
props or change population policy.

Water approach goals are selected from camera **543**'s actual water floor,
including clearance when viewed from above the bank. No session waypoint or
recorded input schedule participates in the water plan. Once actual swimming
representation **13** (unarmed) or **10** (sword equipped) at height **5120** is
observed, the navigator replaces the dry guidance with a fresh water-only plan
from that actual position. Input is released during transition observation;
the transition has a separate **180-update** bound within the existing overall
navigation budget. The expanded scene-derived approach has **3200 updates**;
other goals retain **2400**, with the same **6-replan** and **55/165-second** host
bounds. The retained 2400-update failure reaches actual water after five bounded
ground detours but exhausts its remaining allowance during the final stroke;
the explicit approach allowance covers both portions. An early water entry cannot leave the controller following
obsolete dry-bank points.

Each native journey retains map binaries, scale/count/hash and the audited
script policy in separate directories by snapshot hash beside
`probe-journey.json`. Navigation decisions retain each
computed path, expanded-node count, bounds, mode transition and actual actor
observations. The archived `water-waypoints.json` remains historical evidence;
the water driver no longer reads it. Workshop sword pickup still uses its
separately established corridor and actual attachment/equipment assertions.

## Required water checkpoints

The swimming block now selects separate required checks for:

- Unarmed swimming entry and displacement, **Movement.Swimming**.
- Four original in-water attack directions, **Combat.SwimmingDirections**.
- An out-and-back water crossing, **Traversal.Water**.
- Actual sword pickup followed by **Movement.ArmedSwimming**,
  **Combat.ArmedSwimmingDirections** and **Traversal.ArmedWater**.

Both attack checks require Ctrl plus each direction to select the corresponding
original representation slot and the actual mapped action, remain in water,
release controls and resume swimming displacement. Unarmed actions include
**1521/1520/1522**; sword-equipped swimming includes **1479/1482**. Equipment
and reciprocal sword attachment remain required throughout armed checks.
These are directional combat-action assertions; no live-water-enemy damage or
kill is claimed.

Crossing goals are chosen in camera **545** (or **543** when starting in 545), at least
**1200 units** from the current position. Actual displacement over **600**,
the destination camera and return to the starting water camera are mandatory.
Combat may leave Joe in another water camera. Return goals use an interior
water cell in that original region, rather than a possibly ambiguous boundary
coordinate. Region targets require **512-unit** camera clearance. Every
navigation observation must retain the required swimming representation; a
dry-land shortcut fails. Both journeys use the explicit **noncombat-opening**
fixture. This is controlled traversal/attack coverage, not populated water combat.

The coupled optional **Movement.ArmedSwimmingAndShoreExit** placeholder is
replaced by the real armed checks and a separate optional **Movement.ShoreExit**.
The inspected water component exposes no conservative ordinary-step route onto
dry land; the climb/exit interaction remains unrecovered. This limitation cannot
skip swimming actions that have executable tests. The catalogue now has **195**
logical cases, **106** isolated gameplay scenarios and **22** full shared
gameplay processes. A swimming block selects **24** logical cases and **4**
gameplay processes, retaining only two optional shore-exit skips.

## Retained development attempts

Evidence root: `.tmp/water-goals-20261026/`. No unchanged failed scenario is
restarted until green; each attempt follows a changed planner, mode/height policy
or checkpoint set. Recording is explicitly off; inputs and inspection are bounded.

| Attempt | Selection | Outcome and next correction |
| --- | --- | --- |
| `scene-plan/` | Debug entry | **3 PASS / 1 BLOCKED**, **29.97 s**; conservative script rejection stops before traversal; audit actual audio/scene-load bytecode |
| `water-actions/` | Debug/ASan unarmed block | **7 PASS / 1 FAIL / 4 BLOCKED / 2 SKIPPED**, **55.04 s**; Debug reaches water but crossing target is too close; ASan is still falling at a water node |
| `water-crossing/` | Debug/ASan unarmed block | **9 PASS / 3 BLOCKED / 2 SKIPPED**, **113.54 s**; ASan performs all attacks, resumed movement, crossing and return, native Quit and inspection; Debug hits the upper-bank height boundary |
| `armed-and-unarmed/` | Expanded block, four processes | **10 PASS / 12 BLOCKED / 2 SKIPPED**, **147.96 s**; sword pickup succeeds in both builds; narrow clearance and continuing dry guidance after early swimming exhaust/mismatch setup |
| `observed-transition/` | Expanded block, four processes | **14 PASS / 2 FAIL / 6 BLOCKED / 2 SKIPPED**, **273.87 s**; ASan performs armed and unarmed water attacks; close water-waypoint circling exhausts host/update bounds |
| `swim-steering/` | Expanded block, four processes | **16 PASS / 6 BLOCKED / 2 SKIPPED**, **251.19 s**; Debug completes both armed/unarmed actions and crossings, native Quit and inspection; ASan still exhausts local-replan bounds around short water points |
| `clear-water-segments/` | Expanded block, four processes | **14 PASS / 2 FAIL / 6 BLOCKED / 2 SKIPPED**, **172.17 s**; native attacks still work; full-cycle backward swimming and traversal origins need explicit mode handling |
| `complete-swim-strokes/` | Expanded block, four processes | **18 PASS / 1 FAIL / 3 BLOCKED / 2 SKIPPED**, **184.22 s**; water crossing takes seconds; ASan return lands across a camera boundary, Debug approach reaches water after five detours but exhausts 2400 updates |

Water turning actions also translate Joe. Turning through 180 degrees around a
nearby point repeatedly places that point behind him. The controller now uses
the original backward swim (**1480 / herobkswim**) for a target behind Joe, with
a water-specific turn band and ordinary **180-unit** water arrival radius.
Ground steering remains unchanged. The full-radius boundary, exact final scene
goal and replanning from actual swimming remain in force. The next changed
qualification also smooths water-only guidance into the farthest clear segment,
checking every **64 units** against actual water floors. It never smooths a dry
shortcut into an accepted water path.

Navigation now appends every decision to `probe-navigation.jsonl` and every
actual input transition to `probe-inputs.jsonl`. Large progress snapshots publish
at most **30 updates** apart, plus every outcome, plan or detour. Full final and
caught-failure reports retain the existing navigation/input arrays. The stream
keeps the latest evidence available if the debugger is killed between progress
publications; it avoids rewriting a growing multi-megabyte snapshot for every
steering observation and key transition. Input release still writes immediately.
The changed qualification is `clear-water-segments/`; earlier passes are not
substituted for the current sources. Native samples of action **1480** show
positive forward displacement in the first progress quarter and the main
backward push in the second. `stroke-observation.json` retains a stricter sample:
Down held alone, action 1480 at both observations and unchanged heading. Its
first-quarter mean forward displacement is **+3.15**, versus **−36.83** in the
second quarter. The controller now retains a selected swimming
stroke through its observed action-progress wrap, with a **180-update** cap,
and uses a **180-update** swimming progress window versus **90** on land.
It does not restart a stroke for each minor heading correction. The latest
qualification is `interior-water-goals/` with the camera-interior goals,
directional floor probes and explicit approach allowance above.

## Final native qualification

The final sources pass the full expanded block headless and with Debug visible
on Wayland / ASan headless. Both selections use four gameplay processes with
two configuration workers and sequential journeys in each lane:

| Final selection | Result | Time |
| --- | --- | --- |
| `interior-water-goals/` — headless Debug/ASan | **22 PASS / 0 FAIL / 0 BLOCKED / 2 optional shore-exit SKIPPED** | **174.87 s** |
| `interior-water-visible/` — visible Debug / headless ASan | **22 PASS / 0 FAIL / 0 BLOCKED / 2 optional shore-exit SKIPPED** | **206.28 s** |
| `displaced-visible/` — focused visible Debug entry/traversal | **5 PASS / 0 FAIL / 0 BLOCKED / 0 SKIPPED** | **86.15 s** |

The focused selection keeps startup, movement, swimming and water traversal in
one process. Movement leaves Joe west of the pedestal at
**(8669,3328,-18107)**. The scene planner chooses actual water goal
**(256,5120,-2304)**, reaches camera **543** at **(176,5120,-2453)** and completes
the crossing and return. It uses no old session route or restored state. This
qualifies the reported displaced-pedestal condition independently of the full
block's separate armed setup.

All **nine** final native journeys exit through menu Quit with native status
**0** and completed inspection. Their water-state samples retain health **100**,
state **4**, the required representation **10/13**, released movement/modifier
keys and actual displacement. Both full selections exercise all four unarmed
actions **1521/1521/1520/1522** and all four sword-equipped actions
**1479/1479/1479/1482**, then cross and return in the required water regions.

`validation.json` indexes all **11** retained attempts and their source identities,
verifies both final full reports and the focused report against current source
hashes, checks every final raw map hash/script policy, and compares complete
decision/input streams with the final journey arrays. No failed attempt is
discarded or relabeled. Pinned binaries remain:

- Debug SHA-256: `df81e8ca950b25d1f2163f495ee8c410c4ef30cdf8c31e3e6251b0ba1b68ee42`.
- ASan SHA-256: `e2bde1e384582571221e2ee9d6fbe1fc3a671cf87da70df3e26a38b3ec732b50`.

Bounded original disassembly of floor selection, motion probes and swimming
representation selection is retained beside the receipt. Recording remains
explicitly off; no portable exact-replay acceptance is implied.

## Verification and remaining limits

Current contracts: **53** suite and **31** navigation tests. They cover original
floor samples, unknown bytecode rejection, planning bounds, real mode transition
and its timeout, in-water mode invariants, actual directional action requirements,
post-attack movement/release, armed/unarmed selection and separate journeys,
backward swimming to a target behind Joe without a circling turn, clear-water
smoothing with a dry-tile counterexample, and streamed actual inputs/decisions
before batched progress publication, a stroke that initially recedes, and
directional floor-drop versus wall rejection.

Runtime C, generator, F5 controls, health, actor coordinates, clock/RNG and
population policy are unchanged. General navigation, shore exit, water-enemy
damage, the full suite and pre-existing runtime faults retain their boundaries.
Source/binary identities, native menu exits and completed inspections belong to
the validation receipt. Python compilation and all **84** contracts pass. The
documentation-tree update and subsequent read-only check pass with **248**
Markdown documents; whitespace checks pass. No stage, commit or push is performed.
