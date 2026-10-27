# Build Goal-Driven Gameplay Regression Navigation

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
<!-- /docs-tree:parent -->

Status: bounded encounter and scene-floor navigation implemented; armed/unarmed water objectives verified in Debug/ASan
Parent Step: [Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Runtime Owner: [Task 09 — Population and interaction](task-09-recover-scene-population-and-interaction.md)
Last Updated: 2026-10-27

## Current work — Door approach reliability regression

The user's full visible-Debug/two-worker run fails door approach and blocks
Debug stability on exactly the same sources and binaries as the earlier green
headless run. Full-suite reliability is **open**; the historical single-run pass
does not establish repeatability. The [reliability journal](../../../../../journal/entries/regression-door-approach-reliability-2026-10-27.md)
owns the counterexample, scene-planned approach repair, required displaced-start
regression and qualification limits. Task 10 owns this test-driver correction;
recovered runtime and generator are unchanged.

The correction now has an old-code failing control, passing paced Debug/ASan
probes and a concurrent headless integration: **148 PASS / 57 optional SKIPPED**,
all **143 required**, zero failures/blocked checks, **1112.78 s**, exit **0**.
All **26** native journeys quit and complete inspection; **34** hashes and both
executables match. The new required distant-start case reaches its measured
precondition through real input before testing a fresh door. **113** contracts
pass. This is scoped door-driver acceptance; actual desktop SDL and broader
runtime reliability remain open. The journal retains every failed attempt.

## Previous evidence — Single invisible regression sweep

The [execution journal](../../../../../journal/entries/headless-regression-sweep-2026-10-27.md)
owns accepted `full-final-07/`: all **141 required** checks pass, **144 PASS / 59
optional SKIPPED**, zero failures/blocked checks, **1795.66 s**, exit **0**. All
**24** native journeys quit normally and complete inspection; **203** catalogue
cases occur once, **34** source hashes/executable identities match, and checkpoint,
branch provenance and JSON/JUnit audits pass. All **66 suite / 46 navigation**
contracts pass. Task 09 owns runtime repairs; Task 10 owns input and observers.

Potion guidance uses live floors and observed actor clearance. Actor-disconnected
routes may wait **30 released updates**, within the same six-replan/update/host
budget, only after proving floor connectivity. The floor-only diagnostic route
is never walked. Pickup uses original forward-selection geometry and retains
actual attachment/drinking/removal assertions. Smith strikes track the same
actor; only observed fatal original Joe melee can credit a kill completed during
prerequisite attacks or pursuit. Final death/removal remains mandatory.

Receive-hit leaves its corridor at the first eligible nearby opponent on Joe's
actual floor. It moves around original collision clearance toward a front point
at three-quarter combined radii plus **64** (**448** with observed radii **256**).
Its **64** approach band and **32** waiting hysteresis prevent loose off-axis
settling inside the collision disc. Original unready retreat is ineligible;
either audited guard identity may remain eligible when ready. Actual attributed
surviving damage stays required. The journal records native handoff, outside-disc
steering and released-clearance waits; actual guard-293 damage remains open.

Unarmed contact has its own compatible lifecycle; door/stability retains every
fresh prerequisite without state resets. The extended-prefix **−100** door
writer remains unknown and is not claimed repaired by route separation. Replay
forwarding preserves immutable captures and strict verification; historical
recordings reject dummy SDL, retaining two optional portable-corpus skips.
Whole-game planning, broader route/AI variability and new human acceptance remain
outside this bounded qualification.

## Current continuation — Receive-hit strike alignment

The user's next potion block stops ASan D while pursuing guard **284**. A
radius-only contact experiment still misses original melee contact. The driver
now approaches a point in front of the opponent using live heading/radius and
releases for the original attack. The eligible-opponent goal allows audited
guards **284/293**, with same-floor, attack-slot and instance validation; losing
an opponent permits reselection only within the existing replan budget. Explicit
fixed-target goals cannot switch targets. Real attributed surviving health loss
and all bounds remain mandatory. Original melee-node observations retain contact
evidence. All **61** suite / **38** navigation contracts pass. The
[contact-navigation journal](../../../../../journal/entries/receive-hit-contact-navigation-2026-10-26.md)
owns native qualification, identities and retained failed/interrupted attempts.
Runtime/generator, population, RNG and normal F5 behavior are unchanged.
Final visible-Debug/headless-ASan potion qualification passes **26 results / 6
optional skips**, all **22 required** checks, ten native menu exits and completed
inspection in **317.58 s**. Receive-hit after movement passes **8/8** in **57.01 s**,
including an actual displaced Debug scene-floor join. Both runs match all **21**
source hashes; the journal records unexercised guard-293/reselection limits.


## Previous continuation — Regression 08 stopped-stack capture

The screenshot's Debug potion traversal freeze ends with the user's stop action;
its `SIGKILL` cannot establish the freeze's cause. Agent probes now retain bounded
thread stacks, stopped-frame locals, registers and process maps/status for native
signals and thrown allocation failures. A **30-second** absence of both GDB and
inspection progress, or overall timeout, triggers one debugger interrupt and a
**five-second** capture allowance before process-tree cleanup. The new module is
included in test-source hashes. Reports retain watchdog provenance and terminated
signals, preserving completed checkpoints and failing interrupted journeys.
All **60** suite / **31** navigation contracts pass; native synthetic GDB fixtures
verify signal, allocation-exception and stall capture. The
[freeze journal](../../../../../journal/entries/regression-08-freeze-and-event-callback-2026-10-26.md)
owns native qualification and limits. Task 09 repairs a separately captured
original event-7 callback crash; the screenshot freeze remains unreproduced.
The full visible-Debug/headless-ASan potion block passes **27 results / 5 optional
skips**, all **22 required** checks, ten clean native exits and complete inspection.
Final cleanup of stale diagnostics on prefix reuse passes native GDB fixtures
and fresh startup/menu checks in both builds; the journal records the exact
source delta and executed hashes.

## Previous continuation — Potion approach after damage

Potion setup now shares the bounded workshop corridor join, selecting the nearest
height-compatible node from Joe's actual position after a hit. Connections beyond
the existing local join boundary use read-only scene-floor planning. It no longer
returns to the pedestal's first waypoint from floor **4096**. Potion branch
summaries are optional; required consumption observes whichever original effect
occurs, including a valid no-op. Task 09 owns the accompanying restoration of
the original animation-name repair for bottle removal. The
[potion-consumption journal](../../../../../journal/entries/natural-potion-consumption-2026-10-26.md)
records native qualification and remaining limits. Headless Debug/ASan pass
**27 results / 5 optional skips**, all **22 required** checks, ten native menu
exits and complete inspection. All **89** contracts pass. Final visible Debug
retains a startup/input interruption; the farther scene connection has real-grid
planning and contract evidence, without final native traversal acceptance.

## Previous continuation — Scene-planned water objectives

The water driver now plans from a read-only snapshot of actual scene floors and
audited bytecode, using the shared navigator without reading the archived human
water route. Actual water entry triggers a fresh water-only plan. Required
checks now cover entry, four swimming combat directions, released movement and
camera-crossing returns, both unarmed and after real sword pickup. Shore exit is
separately unfinished. **53** suite / **31** navigation contracts pass; native
qualification and every retained attempt belong to the
[water-goal journal](../../../../../journal/entries/water-goals-and-scene-navigation-2026-10-26.md).
The catalogue is **195** logical cases / **22** full shared gameplay processes.
Runtime/generator/F5 behavior and population policy are unchanged. Water-enemy
damage, shore exit and whole-game planning are not claimed.
Headless and visible-Debug full-block selections pass **22 required checks**
with **2** optional shore-exit skips. A separate visible displaced-pedestal
entry/traversal selection passes **5/5**; all nine final processes quit natively
and complete inspection. Water approach has an explicit **3200-update** bound;
other goals retain **2400**, with unchanged replan/host caps.

## Previous continuation — Recorded water-route approach

Swimming now joins the original recorded pedestal anchor through the navigator
before following all **47** route samples. Only the final transient water-entry
sample declares its source-backed **4096–5120** height interval. The last dry-bank
corner requires **80-unit** proximity with shorter observations nearby; unexpected
route discontinuities stop immediately. Camera **543**,
actual swimming representation **13** and displacement remain mandatory. A
failed setup blocks the unexercised assertion and fails the journey. Headless
and visible-Debug selections pass all **8 required checks** in both builds,
retaining **2** optional armed/shore skips.
The [swimming-route journal](../../../../../journal/entries/swimming-route-navigation-2026-10-26.md)
owns qualification, retained failed attempts and limits. All **50** suite / **22** navigator
contracts pass; visible mode expands host allowance only, with unchanged update
and replan bounds. Runtime/generator/F5 behavior is unchanged.

## Continuation — Verified door crossing

Door **980** passage now reuses bounded observation/steering after its actual
sword damage and collapse assertion. The user's reported fixed-hold failure is
retained; the controller requires a gate crossing and released displacement
beyond the door on its floor. Headless Debug/ASan workshop checks pass **16/16**;
**48** suite and **19** navigation contracts pass. The
[door-passage journal](../../../../../journal/entries/workshop-door-passage-navigation-2026-10-26.md)
records current visible qualification and the known-opening guidance boundary.
Visible Debug remains BLOCKED before gameplay by the existing `FUN_0042f85c`
startup crash; the ASan counterpart passes. Automatic door classification,
progression planning and other doors remain open.
No recovered runtime repair accompanies this continuation.

## Current implementation — 2026-10-26

The reusable `scripts/e2_navigation.py` controller now drives receive-one-hit
setup, recorded workshop routes, fixed smith contact and sword approach. It
retains explicit update/replan/host bounds, scene readiness, height checks,
stuck/circling versus moving-target progress, local detours, fixed-instance
validation and released input. Unknown blockers never acquire guessed progression
or destruction semantics. `details.navigation` and `details.enemy_hits` retain
observations, decisions and attributed original melee events.

Original guard **284**, its NPC attack slots and the node-owner contract in
`FUN_0042efdc` establish the receive-hit eligibility/evidence boundary. Final
frozen-source Regression **05** passes **14/14** in **137.77 seconds**,
with four gameplay processes. Both live Debug and ASan complete surviving
**100→95** hits and unarmed smith **100→80**, native menu Quit and complete
inspection. Pickup reuse separately passes **10/10** in **51.37 seconds**.
All **47** runner and **15** navigator contracts pass. Fixed smith **602** contact
and sword **3717** approach use
the same navigation layer; actual damage/equipment/attachment assertions remain.
No targeted population fixture, runtime C repair or generator change is added.

Read the [implementation journal](../../../../../journal/entries/goal-driven-navigation-2026-10-26.md)
for every retained attempt, current native qualification, exact source/binary
identities and remaining live-navigation limits. Usage and the contract are in
[gameplay tests](../../../../../gameplay-tests.md#goal-driven-encounter-navigation).
The catalogue adds `Tools.NavigationContracts`: **185** logical cases, still
**20** full shared gameplay processes. The full suite and visible acceptance are
not established. The original handoff below is preserved as scope and baseline.

## Original handoff — resume instruction and authorization

Continue in `/home/rgrabowski/Work/EcstaticaRecompiled`. The user requests this
handoff to task the next context with a goal-driven regression navigator after
investigation of Regression **05**. Proceed with the bounded implementation
below without another general confirmation. This handoff-writing turn changes
documentation only; no navigator, runtime repair or new native run is completed.

Read `AGENTS.md` and the [root README](../../../../../../README.md), then follow
[capabilities](../../../../../capabilities.md), [HANDOFF](../../../../../HANDOFF.md),
the [active implementation](../../../playable-sdl-runtime.md), this step and
Task 09 before edits. Read [gameplay tests](../../../../../gameplay-tests.md), the
[Regression 05 investigation](../../../../../journal/entries/goal-driven-navigation-handoff-2026-10-26.md),
and these relevant journals:

- [Controlled population and logos](../../../../../journal/entries/noncombat-population-and-logos-2026-10-26.md).
- [Recorded courtyard route](../../../../../journal/entries/recorded-courtyard-route-2026-10-26.md).
- [Shared journeys](../../../../../journal/entries/shared-gameplay-journeys-2026-10-24.md).
- [Menu stages and parallel configurations](../../../../../journal/entries/menu-stages-and-parallel-suite-2026-10-25.md).
- [Unarmed combat and retention abort](../../../../../journal/entries/suite-visible-unarmed-and-retention-abort-2026-10-24.md).
- [Alternate-target crash](../../../../../journal/entries/alternate-target-crash-2026-10-24.md).

## Problem and latest evidence

The user observes that live enemies can block or kill Joe before traversal or
combat assertions, move away from attack positions, and invalidate recorded
input schedules. They propose goals such as attacking the closest enemy,
traversing with obstacle avoidance, recognizing stuck movement and distinguishing
destructible doors from blockers requiring progression.

The latest inspected block **05** is
`.tmp/gameplay-suite/run_20261026_135535_282152/`. Its `report.json`, `report.html`,
configuration runner logs and `*/<configuration>.Journey.*/probe-*` artifacts
are the baseline. It ran shared journeys, Debug visible through Wayland and
ASan headless, with recording **off** and two configuration workers.

| Check | Debug | ASan |
| --- | --- | --- |
| Startup, movement/release, eight unarmed attack combinations | PASS | PASS |
| Workshop traversal and unarmed smith contact | PASS; smith 602 **100→80** | PASS; smith 602 **100→80** |
| Receive natural enemy damage | FAIL; Joe stays **100** | FAIL; Joe stays **100** |

Overall **12 PASS / 2 FAIL**, **173.27 seconds**. Both unarmed-contact processes
exit natively **0** with completed inspection. The damage processes stop on the
assertion and have incomplete inspection, not successful menu exits. There is
no demonstrated native crash or proof of a damage-runtime defect in this run.

Block **05 intentionally excludes sword pickup** to keep contact unarmed.
Pickup belongs to block **06**. Do not add a sword to make an unarmed test pass.
The inspected source hashes match the report for `e2_gameplay_steps.py`,
`e2_suite.py`, `e2_population_profile.py` and `probe-e2-player-motion.py`.
Pinned binaries are retained in each configuration's Build directory:

- Debug SHA-256: `df81e8ca950b25d1f2163f495ee8c410c4ef30cdf8c31e3e6251b0ba1b68ee42`.
- ASan SHA-256: `e2bde1e384582571221e2ee9d6fbe1fc3a671cf87da70df3e26a38b3ec732b50`.

`Journey.damage()` currently executes **98** historical input transitions over
**2506** updates from `scripts/scenarios/potion-damage-inputs.json`, including
**815** updates holding Ctrl. It then pursues guards **284/293** by X/Z distance
and heading, with no height/reachability or obstacle-aware planning. Recorded
health changes show guard 293 **100→60** in Debug and guard 284 **100→40** in
ASan, while Joe remains **100**. The sequence is not a reliable receive-hit
setup. These observations alone do not establish which actor caused every hit.
ASan finishes with Joe at `(8825,4096,-16951)` while guard 293 is at
`(10237,3328,-17208)`: horizontal pursuit does not establish a reachable encounter.

## Goal and scope

Build a reusable, bounded, state-aware **test driver**. Scenarios declare an
objective; the navigator observes current game state, selects ordinary input,
checks progress and replans locally within explicit limits. Joe must still move,
attack, pick up objects and change scenes through recovered game behavior and
real SDL input. The navigator must not implement a second gameplay simulation.

Start with a reliable **receive one enemy hit while surviving** objective and
the navigation needed to establish that encounter. Then reuse the layer for
unarmed contact and selected pickup/door approaches. Do not expand the first
slice into a general autonomous whole-game solver or a per-frame language-model
controller. A small explicit state machine and route/obstacle policy is suitable.

Suggested objectives, with names left to the implementation:

1. **Reach location or actor:** use connected route segments/waypoints, observed
   height/camera transitions, live obstacles, heading and distance. Detect lack
   of displacement/progress, circling, inaccessible height and stale targets.
   Bounded local avoidance/replanning must retain the reason and attempted path.
2. **Damage an eligible enemy:** select an alive, reachable target permitted by
   the test; maintain facing/range as it moves; exercise the intended weapon and
   attack; observe actual target damage. Prefer reachable route cost over raw
   nearest X/Z distance. A smith-specific assertion must still target smith 602.
3. **Receive one hit:** choose an eligible opponent capable of the required
   attack, reach its encounter region, release attack controls, observe the
   opponent's behavior and Joe's health loss, and stop before uncontrolled death.
   Do not reuse an attacking historical sequence as the primary setup.
4. **Interact with a blocker:** only perform interactions allowed by the scenario.
   A verified destructible door may require acquiring a weapon, bashing and
   verifying collapse before passage. A no-combat traversal must not silently
   destroy a door or leave its required route to obtain a PASS.

There is no existing general navigation graph/pathfinder. `walk()` is a waypoint
heading controller, `face()` turns toward a live actor, `unarmed_contact()` follows
the moving smith in short bouts, and `strike()` mostly fixes the initial approach
before holding attack. Build on their useful observation/input boundaries;
another larger fixed input schedule will not solve the reported problem.

## Observation and semantic limits

- Keep actor identity, position, orientation, health, actions, attachment,
  camera/floor, actual displacement and relevant original collision properties
  available to decisions and the journal. Validate table identity/liveness before
  reusing a target. A loaded resource is not necessarily an active opponent.
- Use original-code/asset-backed enemy and interaction eligibility. Presentation
  marker labels are heuristics; the collision flag also covers props/doors/stocks.
  Do not treat every non-Joe actor as hostile or every nearby actor as reachable.
- Human route samples can seed connected corridors, not teleportation or exact
  state restoration. Audit available floor/grid data before adding a planning
  query API; do not assume calling recovered query functions is side-effect free.
- A stationary player proves lack of progress, not the cause. Distinguish observed
  dynamic obstruction, height mismatch and an unknown blocker. Calling a door
  progression-locked requires original script/state evidence. Lack of damage
  alone does not prove progression locking or indestructibility.
- The target/route success predicate remains owned by the logical checkpoint.
  Adaptive steering may change setup inputs, never replace an unexercised
  assertion, silently switch a required target or bypass a required doorway.

## Population and original behavior

Keep the implemented `noncombat-opening` profile for suitable tests. It suppresses
scripted **284/293/602** and terrain generation before creation, not by freezing
colliders. Actual combat currently uses fully live population, so its prerequisite
traversal remains exposed to unrelated enemies.

A controlled **targeted encounter** is a possible complementary fixture: retain
the intended original enemy and its ordinary AI while suppressing unrelated
creation. Audit scripts/intro dependencies and declare/report the exact profile
if implementing this. Do not count a controlled encounter as populated-world
coverage. Keep separate live-population navigation/combat checks. Any failure in
live AI/damage remains visible; navigator uncertainty must not become a PASS.

Normal F5 gameplay must keep original population and controls. Do not change
spawning, collision, health, RNG, actor placement, script release or AI globally
to accommodate the navigator. No teleportation, invulnerability, save/load,
snapshots or assumed state restoration. Runtime C repairs require original
disassembly/Ghidra evidence and matching `GenerateRecon.js` changes.

## Reporting and execution contract

Preserve journeys as execution units and logical checkpoints as reporting units.
Full/block selection must continue choosing a small compatible journey set,
without separately rerunning every standalone prerequisite. Retain isolated
diagnostic scenarios, dependency handling, GoogleTest-style console output and
HTML/JSON/JUnit reports. The current catalogue is **184** cases, with **20**
planned full shared gameplay processes; the complete suite is not rerun/accepted.

Navigation setup should have explicit checkpoints/outcomes. A failed approach
must retain its setup failure and leave combat assertions that never executed
BLOCKED. If an established eligible encounter exercises the damage behavior and
its assertion fails, report FAIL for that assertion. Root setup/lifecycle failure
must still fail the overall journey, including when all target checks are BLOCKED.
Do not turn required unperformed actions into harmless optional SKIPs. Completed
passes survive a later failure; interrupted/crashed journeys fail overall.

Record goal, phase, target identity, eligibility/reachability evidence, positions
and height, blocker observations, chosen/rejected actions, path changes, progress
measurements and exhausted budgets. Use deterministic decision/tie-break rules
for identical observations, with separate game-update, replan and host-time bounds.
Input release and evidence retention must work on failure/interruption too.
Bounded replanning inside one goal is distinct from silently restarting an entire
failed scenario until it passes; the latter remains prohibited.

Preserve the headless/default display picker, one full-suite entry, numbered
blocks and current user labels/order. Debug/ASan concurrency is authorized now:
two independent configuration workers, sequential windows within each lane;
`--workers 1` remains available. Keep configurable one/both visible windows.

## Implementation locations

- `scripts/e2_gameplay_steps.py`: current objectives, `walk`, `face`, contact,
  `strike`, `damage`, shared checkpoint dispatch.
- A focused reusable Python navigator module if useful; keep it out of recovered
  game logic and include it in suite source-identity metadata.
- `scripts/probe-e2-player-motion.py`: GDB/SDL observation and bounded input bridge.
- `scripts/e2_suite.py`, `scripts/run-e2-suite.py`, `scripts/e2_suite_parallel.py`:
  explicit coverage/profile declarations, execution, source identity and reports.
- `scripts/check-e2-suite.py`: meaningful navigator/report/failure contracts;
  separate focused contracts if that avoids overloading this file.
- `scripts/e2_population_profile.py` and
  `E2Recomp/platform/e2recomp_test_population.h` only if an audited targeted
  encounter profile is needed; mirror reconstructed gates in the generator.
- `scripts/scenarios/courtyard-waypoints.json`: retained human route provenance.
  Preserve `potion-damage-inputs.json` as historical evidence/explicit diagnosis
  when replacing its use as the primary receive-hit setup.
- `docs/gameplay-tests.md`, this task, Task 09 and a dated journal: usage,
  acceptance, measured execution cost and remaining limits.

## Acceptance and validation

1. Add contracts with meaningful moving-target, height mismatch, blocked route,
   stuck/circling, target disappearance/death, bounded-replan and interruption
   cases. Verify fixed-target checks cannot switch targets and unknown blockers
   cannot be guessed progression-locked. Verify failure propagation/evidence.
2. Demonstrate native Debug and ASan receive-hit objectives through actual enemy
   behavior and Joe health loss, without assigning health or state. Retain enough
   attack/hit evidence to distinguish the intended enemy from other damage sources.
   If a controlled encounter is used, declare and separately qualify it.
3. Verify unarmed contact still requires no sword and actual target damage. For
   the first reuse slice, demonstrate obstacle/stuck handling with its recorded
   decisions and unchanged goal assertions; do not claim whole-game navigation.
4. A path needing a permitted interaction must verify that interaction; a blocked
   or unimplemented prerequisite must produce an honest bounded failure/BLOCKED
   result. Use source-backed cases where available, otherwise state the limit.
5. Run focused native examples with isolated artifacts, pinned executable/source
   identities, explicit recording **off**, update/host bounds, real SDL inputs,
   native menu Quit and complete inspection for successful journeys. No portable
   exact-replay acceptance is implied. Start headless; visible acceptance is
   separate because desktop input previously interfered with automated runs.
6. Reuse the retained latest **05** failure as the baseline; do not repeatedly run
   unchanged failures. Exercise materially different fresh encounter states with
   declared validation inputs/conditions, retaining every failed attempt. Compare
   logical assertion coverage, process counts and elapsed time for the chosen
   equivalent selection. Do not add repeated startup/traversal as a workaround.
7. Run appropriate contracts and affected original-code checks/builds if runtime
   code changes. At the previous implementation boundary **46** runner contracts
   passed; the documentation tree had **242** documents before this handoff.
   Run documentation maintenance and whitespace checks at completion:

   ```sh
   python3 scripts/check-docs-tree.py --update
   python3 scripts/check-docs-tree.py
   git diff --check
   ```

## Worktree and open failures to preserve

At handoff, HEAD is `39b0f41`; the preceding commit is `3a1aab1`. All existing
suite/profile/runtime-gate/documentation changes are **staged**, with no unstaged
diff before this handoff. The agent made no commit. Reinspect status, staged and
unstaged diffs and recent commits: the user may commit or stage more meanwhile.
Preserve all unrelated work; do not stage, commit or push unless requested.

The reconstructed-C animation-name regression is deliberately preserved: missing
new-name sentinel initialization and two **0x1117/0x445c** byte-capacity differences
against the generator. Do not regenerate over it. Use scratch generation and
compare only the intended delta if changing runtime/generator code.

Keep open: unexplained retention cleanup exception despite repaired error-handler
allocation failure; separate `FUN_0042f85c ← FUN_0042b880 ← FUN_0042b338 ←
FUN_0042ae80 ← FUN_00427584` event fault; menu option-label/restart failures and
ASan Load overflow; bottle removal/potion limits; live traversal/AI variability.
The separate event bundle has ASan SHA-256
`12cfcb667ca6c34e6d01fa176468e18f30f35fc4c06f07e518567d2a5f7f39be`
under `.tmp/suite-watch-investigation/visible-event-bundle/`. Its recording was
off; do not claim deterministic replay acceptance. Noncombat and route evidence
also lives under `.tmp/noncombat-profile-20261026/validation.json` and
`.tmp/courtyard-route-20261026/validation.json`.

Normal logos now use **5000 ms** waits, automated probes tap each actual logo
separately, and horseback input is distinct. The first logo is conditional.
Original direct logo-key-skip fidelity remains unestablished; do not reintroduce
zero-wait defaults. Old recordings retain their environment and pinned binaries;
new executable/control changes may diverge even under compatible replay.

## First concrete action

Inspect the latest **05** journals and implementation, then define the smallest
observation/progress/outcome interface for `receive_one_hit`. Establish valid
opponent/reachability evidence and a bounded route before adding attack/damage
assertions. Implement that slice and its failure contracts first; expand through
the reusable interface only after native evidence supports it.
