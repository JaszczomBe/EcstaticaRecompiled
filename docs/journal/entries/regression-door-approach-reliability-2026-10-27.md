# Door approach regression and acceptance reliability — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Playable SDL runtime](../../implementations/playable-sdl-runtime/playable-sdl-runtime.md).
Navigation: [Task 10](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Prior evidence: [Sequential headless sweep](headless-regression-sweep-2026-10-27.md).

## Superseding acceptance status

The user supplied a full `--build --configurations debug asan --execution shared
--display visible-debug` run with the default two workers. Retained report:
`.tmp/gameplay-suite/run_20261027_160429_746159/report.json`:
**142 PASS / 1 FAIL / 1 BLOCKED / 59 optional SKIPPED**, **987.46 s**, exit **1**.
`debug.Interaction.DoorPassage` fails before striking the door;
`debug.Stability.MixedJourney` is blocked by that failed prerequisite. ASan's
workshop, door and stability pass. All **34** test-source hashes and both pinned
executable hashes match `full-final-07/` exactly. The original asset hash matches.
This is a directly comparable failure, not a source/build mismatch.

The earlier single headless pass remains factual evidence for that execution;
it does not establish reliable regression acceptance across live AI outcomes,
display pacing or concurrent configurations. Current full-suite reliability is
**open**. A green retry cannot erase this counterexample. Visible SDL and worker
count both differ, so the evidence does not isolate SDL as the cause.

## Captured cause and correction

The user's smith fight ends with Joe at **[4790, 4096, −11985]**, smith **602** at
**[5161, 4096, −12065]**, with three original Joe melee writes **100→60→20→−20**
and final state **11**, representation **0**. The subsequent door approach
tries its first fixed waypoint **(−1800, −9800)** directly. After **512** updates
it fails at **[244, 4096, −11253]**, before any door health sample or strike.
The passing headless executions finish the fight near the local door corridor.

Door **980** now joins the existing local strike route through the bounded
navigator's live scene-floor and observed-actor planning. The local strike
positions, health/death/removal assertions, required opening gate, released
beyond-door displacement and same-floor assertion stay mandatory. There is no
recovered-runtime, generator, RNG or actor-state edit.

A new required `Interaction.DoorPassageDisplaced` case has a fresh intact-door
lifecycle in each configuration. It performs real workshop/sword/combat setup,
then walks to the captured distant Joe position using SDL input. The observed
start must be within **240** units on floor **4096** before the same door
interaction is attempted. It cannot wait for a favourable smith outcome or
credit a door destroyed by a previous case. Full catalogue: **205** logical
checks, **143 required**, **26** shared native journeys (**108** isolated).

## Qualification plan

All new attempt, source-variant and audit artifacts are under
`.tmp/regression-door-reliability/`.

Preserve every attempt and freeze test sources during qualification. First run
a negative control with only the new scene join removed in a scratch copy: the
controlled distant start must expose the old approach failure. Then run the
affected Debug/ASan door and stability selection with one headless worker, a
headless two-worker workshop selection, and paced-dummy native probes with the
same bounded update batching used by visible probes. Inspect actual start,
door damage/collapse/gate crossing, native exit, completed inspection and hashes.
These are finite declared selections, not retry-until-green acceptance. Native
agent probes remain invisible with recording off. Actual desktop SDL qualification
and a fresh complete final-source suite remain separate from this focused proof.

## Retained attempts

`negative-control-debug/` stops during `combat.attack-up` before distant-start
setup. It captures **SIGSEGV** in `FUN_0043cac0` reached through the original
fatal path `FUN_00414e68` from bitmap disposal `FUN_00452a94`; `probe-stopped.json`
retains the stack/locals/registers. This is **not** a successful negative control
and is not claimed repaired. The fresh case was missing the movement portion of
its declared prerequisite prefix; it now repeats that real input setup locally
before workshop/combat, in both shared and isolated modes. This is a test-setup
correction, not evidence explaining or repairing the native crash. Any later
qualification retains this unresolved runtime counterexample.

`negative-control-prefix-debug/` completes real movement, workshop, pickup,
attacks and smith kill, then fails at the new fixture's navigator construction:
an empty eligible-ID set is rejected before any displacement. This test-driver
error is corrected to declare door **980**; no native gameplay result is credited.

`negative-control-eligible-debug/` provides the intended **red control**. On the
unchanged Debug executable, real input reaches **[4853, 4096, −12016]** (about
**70.2** units from the declared distant start), after successful complete
prerequisites and smith death. The old approach then fails its first waypoint
at **[567, 4096, −11248]** after **498** updates. There is no door strike. The
scratch variant removes only the new scene connection and its diagnostic field;
`negative-control.json` retains its source identities. This reproduction does
not need visible SDL or a random far-retreating smith.

`focused-serial-01/` passes the ordinary Debug door and stability journey
(**195.88 s**). Its separate distant-start fixture reaches **[4817, 4096,
−11932]**, within **59.5** units, but then advances an unnecessary **eight**
released updates before checking the start. Joe continues to **[5111, 4096,
−11844]**, outside the unchanged **240** bound, so the case correctly fails.
The fixture will hand over at the actual reached waypoint, without that
post-arrival movement. It does not require a stationary start; all observations,
real input, floor checks and later door assertions remain required. The run is
retained as failed, and its exact nine relevant source snapshots are retained.

The serial attempt completes **19 PASS / 1 FAIL / 0 BLOCKED**, exit **1**,
**589.56 s**. Both ordinary door/stability journeys pass; ASan's distant-start
case also passes with actual start **[4854, 4096, −11936]**, real door damage and
passage, clean menu exit and complete inspection. Debug's fixture failure is not
relabelled. Final fixture code removes the eight-update gap, and a contract
rejects any added update between arrival and start measurement. After this
correction the final-source matrix is: one matching red control, paced-dummy
Debug/ASan distant-start probes, then one complete headless two-worker integration
run. This covers the changed handoff, visible-style batching/pacing and concurrent
configuration execution without opening agent windows. It does not claim actual
desktop SDL qualification or erase the independent earlier native crash.

`negative-control-handoff-debug/` repeats the **red control on final fixture
code**, removing only the scene join and its diagnostic field. Required start
**[4847, 4096, −11985]** is **57** units from the goal. The old route again fails
waypoint **0**, now at **[243, 4096, −11252]** after **508** updates—within about
**1.4** units of the user's failed position **[244, 4096, −11253]**. All real
prerequisites and distant-start assertions pass before this intended failure;
there is no strike or native signal. This isolates the approach defect without
requiring desktop SDL, parallel workers or a particular random smith retreat.

The first pacing launcher (`paced-debug/`) is rejected by the official probe's
`--watch requires a desktop video driver` argument guard, before native startup
(exit **2**). To isolate pacing invisibly, a retained scratch probe removes only
that CLI restriction. Native watch batching/delays, input and assertions are
unchanged; all gameplay modules are symlinks to the official frozen sources.
`pacing-probe-identity.json` records exact original/diagnostic hashes. This is a
pacing diagnostic, not desktop-driver qualification; the official CLI is unchanged.

## Final-source focused proof

Both paced-dummy probes pass, with all actual setup and door assertions intact.
**Debug: 142.77 s; ASan: 147.39 s**, native exit **0**, completed inspection,
no stopped/stall diagnostic. `door-audit.json` verifies the intended old-code
failure and both current-code outcomes, including the measured initial condition,
positive starting door health, terminal death/removal, actual required gate
crossing and released same-floor displacement beyond the door.

| Mode | Observed distant start | Start error | Door health | Gate lateral | Released distance beyond |
| --- | --- | ---: | --- | ---: | ---: |
| Debug paced dummy | `[4743, 4096, -11984]` | 47.01 | **100→−20** | 57.62 | 926.46 |
| ASan paced dummy | `[4732, 4096, -11995]` | 58.86 | **100→−20** | 43.06 | 656.99 |

All **67 suite / 46 navigation = 113** contracts pass. Sources are frozen for
final integration. Runtime/generator and both executable identities remain those
of the user's report; only test input/setup, catalogue/profile and contracts
change. Final changed test-source identities:

| Source | SHA-256 |
| --- | --- |
| `e2_gameplay_steps.py` | `fdb468577d24a7d24420529a7afc54a40ca13438c09fbd56e1b835de473e3f2e` |
| `e2_suite.py` | `7d716196f52542daae103a8d70bd6903ed208a4530c0365e429318a9dd7ce31a` |
| `e2_population_profile.py` | `cbb4f1eff458eb09c75310c72ec9496b128692e1a79738190b0c627b33c03b13` |
| `check-e2-suite.py` | `53d27949fecd37d0d9ef9e49dca9f834161ea248bb570255e83582e0bd588c23` |

The full concurrent run is under `full-concurrent-01/`. Its initial “No gameplay
executions selected” line is from the shared source-check lane; configuration
lanes still run the planned native journeys. It is not a claim that the whole
selection omits gameplay.

The delta inspection stream strengthens the obstruction evidence:
`stationary-approach.json` records that Joe's XYZ never changes for the last
**62** snapshot intervals of the user's attempt (**669→731**) and **49** of the
final red control (**862→911**), while action/progress/heading fields continue
changing. This is not just the last step of an otherwise progressing long walk.
The scene-planned connection addresses the blocked straight path; no waypoint
budget or door assertion is relaxed.

## Remaining acceptance limits

The controlled-start red/green evidence addresses this specific driver defect.
It does not make the runtime's RNG, clocks or AI trajectories identical, prove
all possible starting states, or qualify the desktop Wayland/X11 backends.
Native bounded failures remain failures; no retry result overwrites them.

The independent early diagnostic's bitmap-disposal fatal path remains open,
as does the older extended-unarmed-prefix **−100** door writer. A bounded
runtime continuation should capture the bitmap record/name/stream inputs at the
first fatal gate and compare the owning parser/disposal path with original x86;
changing the fatal requester would not explain the invalid resource state.
Portable replay and the existing optional persistence/audio/rendering, water,
potion-lifetime and longer human-play limits remain unchanged.

## Full integration result and scoped acceptance

The final-source concurrent headless integration completes **148 PASS / 57
optional SKIPPED / 0 FAIL / 0 BLOCKED**, all **143 required** checks, **205**
logical cases, **26** native journeys, **123** execution units, **1112.78 s**
(**18 min 32.78 s**), exit **0**:

```sh
python3 scripts/run-e2-suite.py --build --configurations debug asan --workers 2 --execution shared --display headless --output .tmp/regression-door-reliability/full-concurrent-01
```

All **26** native journeys quit with exit **0** and complete inspection; none
retains a stopped/stall diagnostic. All **34** recorded source hashes and both
pinned/live binaries match. Executable hashes remain **Debug
`4c6d47a8c9e306228ba41af4fc0e8c59103a6fb167f99e1cb4e873040189e94b`** and
**ASan `b91f57280b2acbcd9362bc947cf0bd3b42708133c8eca6654376e31e07ad043c`**.
`comparison.json` separately verifies exact source/binary equality between the
user's original failed report and the earlier headless green report.

`validation.json` audits final lifecycles, required outcomes and identities.
`door-audit.json` verifies **six** final-source successful door interactions,
including **four** controlled distant starts across paced and concurrent modes,
and the intended old-code failure. Distant-start errors are **47.01–58.86**,
within the unchanged **240** bound; every door starts at health **100**, finishes
at **−20** with state **11** / representation **0**, crosses the **256**-unit
half-width gate and finishes beyond **100** on the same floor. The required
full-run distant-start cases pass in **81.28 s Debug / 85.10 s ASan**; native
journeys including startup/menu exit take **106.72 / 111.37 s**.

This accepts the reported door-approach correction under the exercised conditions.
It does **not** close broad full-suite reliability: actual desktop SDL remains
unqualified on these final sources, and the independent earlier setup crash
remains unresolved. The single green integration supplements the controlled
regression proof; it does not replace the retained failures or prove identical
AI/clock/RNG trajectories. No files are staged, committed or pushed by this work.

Final integration audit passes: each of the **205** catalogue identities occurs
once with the correct required/optional classification; **143 required** pass;
all **26** planned journey identities and **123** units match. JSON/JUnit agree,
and every passed checkpoint/optional branch has its actual successful native
provenance. The scratch auditor initially uses the sequential journey-name path;
it is adapted to the merged parallel report's `artifacts` path. No native result,
assertion or report is changed by that auditor correction.

Final verification: all **113** contracts and registered original/host fixtures
pass in integration; exact four-artifact generator parity and Node syntax pass.
The frozen source baseline still matches after qualification. Documentation-tree
update and read-only check pass for **254** Markdown documents; `git diff --check`
passes. Existing staged/unstaged/untracked work is preserved.
