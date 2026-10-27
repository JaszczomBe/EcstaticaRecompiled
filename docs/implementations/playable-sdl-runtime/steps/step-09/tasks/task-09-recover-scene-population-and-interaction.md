# Recover Scene Population And Interaction

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
<!-- /docs-tree:parent -->

Status: in progress; human sword pickup, four kills and two door destructions verified; animation-cache stall repaired; typed markers and Debug/ASan gameplay menu Quit pass; human random-potion pickup verified; delayed potion effects repaired; human bottle removal/sword use confirmed; diagnostic health/effect panel added; fresh healing 85→100, poison onset and conditional no-op verified; effect expiry/cure open; alternate-target crash repaired with bounded evidence; extended stability open; wider pickups/rendering deferred
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-27

## Goal

Restore original scene objects and NPCs needed for exploration and basic interaction while retaining cylinder presentation and Joe's working movement/camera transitions. Begin with one verified original resource and behavior; original models and full combat remain later work.

## Current work — Door approach reliability regression

The user's full visible-Debug/two-worker run fails door approach and blocks
Debug stability on exactly the same sources and binaries as the earlier green
headless run. Full-suite reliability is **open**; the historical single-run pass
does not establish repeatability. The [reliability journal](../../../../../journal/entries/regression-door-approach-reliability-2026-10-27.md)
owns the counterexample, scene-planned approach repair, required displaced-start
regression and qualification limits. Task 10 owns this test-driver correction;
recovered runtime and generator are unchanged.

A separate diagnostic setup variant also captures a bitmap-disposal fatal path
before door setup; its stopped evidence remains open. Passing navigation runs
do not repair or supersede that runtime counterexample.

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
records accepted `full-final-07/`: all **141 required** checks pass, **144 PASS /
59 optional SKIPPED**, no failures/blocked work, **1795.66 s**, exit **0**. All
**24** Debug/ASan native journeys quit normally and complete inspection. All
**203** catalogue cases occur once, **34** source hashes and pinned/live binaries
match, and JSON/JUnit/checkpoint provenance audits pass. Execution is sequential,
SDL dummy, recording off. Historical failed/interrupted attempts remain retained.

Original-backed runtime repairs recover menu/slot/restart behavior,
[compatibility surfaces and callers](../../step-08/tasks/task-12-recover-directdraw-surface-lock.md),
terminal **0x16/0x17** actor ownership and mapped bitmap-record allocation/return/
disposal ownership. Every reconstructed repair is generator-owned with exact
four-artifact parity. Normal/ASan fixtures compare **3072** terminal events,
**1152** root cases and **14,208** bitmap-record cases per mode. Task 10 owns the
accompanying bounded navigation, input and read-only attribution repairs.
All **66 suite / 46 navigation** contracts pass.

The extended unarmed-prefix door **−100** deactivation has no identified writer;
compatible separate journeys preserve required checks without repairing that
runtime gap. Capturing its original writer is the next bounded diagnostic.
Portable replay, persistence/audio, broader rendering, shore exit, live water
combat damage, final potion expiry/cure, longer stability and new human F5
acceptance remain open. The earlier screenshot freeze is still unconfirmed.

## Current Continuation — Receive-Hit Contact Navigation

The next supplied potion run stops ASan D's receive-hit approach. Task 10 now
positions Joe in front of an observed original opponent, allowing audited guards
**284/293** with same-floor/attack/identity validation and bounded reselection.
Explicit fixed-target checks cannot substitute targets. Surviving real health
loss and original melee attribution remain required. All **99** contracts pass.
The [contact journal](../../../../../journal/entries/receive-hit-contact-navigation-2026-10-26.md)
owns native qualification and retained attempts. No recovered runtime, generator,
population or F5 change accompanies this correction. The earlier screenshot
freeze remains unconfirmed.
Final visible-Debug/headless-ASan potion qualification passes **26 results / 6
optional skips**, all **22 required** checks, ten native menu exits and completed
inspection in **317.58 s**. Receive-hit after movement passes **8/8** in **57.01 s**,
including an actual displaced Debug scene-floor join. Both runs match all **21**
source hashes; the journal records unexercised guard-293/reselection limits.


## Previous Continuation — Regression 08 Freeze Investigation

The user stopped the frozen run; its subsequent `SIGKILL` does not identify the
freeze's cause. New stack capture instead exposes an independent event-7 crash
in `FUN_0042f85c`. Original dispatcher **0x42c602–0x42c604** passes ESI's node;
the recovered function now retains that node and explicit owner/resource/action
inputs rather than uninitialized registers. The generator mirrors the repair,
and **6144** additional original-instruction cases pass normally and with ASan.
The shared rotation helper's new Z case and existing X/Y cases pass **24576**
original comparisons in both configurations. Generated parity is exact and both
SDL builds pass. The [freeze journal](../../../../../journal/entries/regression-08-freeze-and-event-callback-2026-10-26.md)
owns native results and the still-unproven relationship to the screenshot freeze.
Task 10's agent probes now capture bounded stopped stacks before stall cleanup;
all **91** suite/navigation contracts pass.
The full visible-Debug/headless-ASan potion block passes **27 results / 5 optional
skips**, all **22 required** checks, ten native exits and complete inspection in
**343.22 s**. Final diagnostic-output initialization passes native GDB fixtures
and another **4/4** fresh startup/menu selection on the same repaired binaries.

## Previous Continuation — Natural Potion Consumption

The user's random-potion request makes branch summaries optional: required
consumption accepts any observed original outcome, including full-health healing
or an unafflicted no-op, without injecting types or assigning RNG. Actual pickup,
drinking, removal and selected effect assertions remain. The reported lingering
bottle resolves the three preserved animation-name C regressions using the
existing original-x86-compared generator repair. Both normal/ASan fixtures pass
all **1,800** installed names; all four generated artifacts match current source.
Damaged setup shares the bounded navigator's height-compatible workshop join.
The [potion-consumption journal](../../../../../journal/entries/natural-potion-consumption-2026-10-26.md)
owns native qualification and limits. Headless Debug/ASan pass **27 results**
with **5 optional skips**, no failures/blocked checks, ten native menu exits
and complete inspection; all **89** contracts pass. Final visible Debug retains
a startup/input interruption. The farther scene connection is planned and
contract-tested; actual traversal of that fallback remains unaccepted.

## Previous Continuation — Scene-Planned Water Objectives

Water entry/traversal now uses read-only live scene-floor planning through the
shared navigator, replacing the archived human water route. Separate required
unarmed and sword-equipped checkpoints exercise entry, four original swimming
attack directions, released movement and water-camera crossings/returns. The
[water-goal journal](../../../../../journal/entries/water-goals-and-scene-navigation-2026-10-26.md)
owns current native qualification and retained failed attempts. All **84**
contracts pass. Runtime/generator/F5 and the controlled population policy are
unchanged. Shore exit and live-water-enemy damage remain open.
Final headless and visible-Debug block selections pass **22 required checks**
with **2** optional shore-exit skips; focused visible displaced-pedestal
entry/traversal passes **5/5**. All nine final native journeys quit and complete
inspection.

## Previous Continuation — Swimming Route Navigation

The reported visible Debug swimming route starts west of the recorded pedestal
anchor after movement checks and stalls on its direct stair approach. The test
now navigates through the anchor and all recorded route samples, then verifies
actual swimming at camera **543**. A declared terminal height interval covers
the original **4096→5120** water-entry transition; a tighter bank corner avoids
early route cutting. Normal floor checks and representation/displacement
assertions remain. Headless and visible-Debug selections pass all **8 required
checks** in both builds, with **2** unchanged optional skips, native Quit and
complete inspection. The [swimming-route journal](../../../../../journal/entries/swimming-route-navigation-2026-10-26.md)
records current visible qualification and limits. This changes test tooling only;
armed swimming, shore exit and existing runtime faults remain open.

## Current Continuation — Destroyed Workshop Door Passage

The user's latest workshop block passes door **980** destruction but fails the
following fixed forward hold in Debug/ASan. The test driver now aligns with the
known opening and corrects heading from live observations, requiring its gate
crossing and the original released-displacement assertion on the same floor.
Headless workshop acceptance is **16/16**, including actual native Quit and
complete inspection. The [door-passage journal](../../../../../journal/entries/workshop-door-passage-navigation-2026-10-26.md)
records the reported failure, visible qualification and current limits.
Visible Debug remains BLOCKED before gameplay by the existing `FUN_0042f85c`
startup event crash; ASan again passes the door check. Runtime C, generator and F5 controls/population are unchanged. Unknown doors and
progression semantics remain outside this explicit route.

## Current Continuation — Goal-Driven Regression Navigation

[Task 10](task-10-build-goal-driven-regression-navigation.md) now implements a
bounded test-input navigator. Live Debug/ASan guard **284** encounters establish
attributed original melee hits and surviving Joe health **100→95**, followed by
native menu Quit and complete inspection. Fixed smith **602** contact, workshop
corridors and sword **3717** approach reuse observation/progress/steering while
preserving their real damage, no-sword and attachment assertions.

Final headless Regression **05** passes **14/14**, four gameplay processes /
**137.77 s**, with unarmed smith **100→80** in both builds. Controlled pickup
reuse passes **10/10**; **47** runner and **15** navigation contracts pass.

The [navigator journal](../../../../../journal/entries/goal-driven-navigation-2026-10-26.md)
owns current qualification and retained failures. Stuck/circling, moving targets,
height mismatch, scene readiness, instance disappearance and exhausted bounds
remain explicit outcomes. Unknown blockers are never guessed progression-locked.
Runtime C, generator, normal F5 population and controls are unchanged. The
catalogue is **185** cases / **20** planned full gameplay processes; full-suite
and new visible acceptance remain open, alongside the existing runtime faults.

## Current Continuation — Controlled Opening Test Population

The user authorizes preventing enemy creation for noncombat regressions, avoiding
random blockage/death before their assertions. The opt-in
`E2R_TEST_POPULATION=noncombat-opening` fixture bypasses terrain creation and the
original scripted guard **284/293** and smith **602** load paths. It leaves Joe,
props, doors and pickups eligible; no freeze, collision bypass, health/RNG/pose
write or fabricated script completion is introduced. The manifest is audited
for the opening routes, not a general classifier for later regions. Original
archive identities, production load gates and default-off original-x86 population
comparisons cover the boundary; the generator mirrors all reconstructed gates.

Movement/courtyard, action-only attacks, pickup, swimming and menu journeys use
the fixture. Actual enemy contact/kill/damage, startup-only, potion and stability
journeys remain live throughout. Every logical result records its profile;
controlled censuses reject leaked audited enemies/generated actors. Healthy Joe
still must reach the original release camera/floor after both guard creation
requests were intercepted. This accepts controlled assertions, not populated
startup or exploration fidelity.

Normal F5 restores **5000 ms** logo waits. Automated journeys present each actual
logo then inject separate SDL Space press/release pairs; horseback input remains
separate. Conditional first-logo and original skip-fidelity/replay limits are
explicit in the [population/logo journal](../../../../../journal/entries/noncombat-population-and-logos-2026-10-26.md).

Final headless movement passes **8/8**, two processes / **60.96 s**, versus the
same isolated selection **8/8**, six processes / **102.21 s**. Controlled workshop
pickup passes **12/12** and three-stage menu show/hide **8/8**, in Debug/ASan,
with native Quit and complete inspection. A natural-logo Debug example observes
**5.67/5.69 s** waits without logo keys. Live Debug smith damage remains
**100→80**; ASan live traversal fails before contact, correctly BLOCKED. A
visible Wayland run receives unrelated desktop keys and is explicitly interrupted;
X11 is unavailable. These failures are retained, with no completed visible
acceptance or unchanged retry. All **46** contracts pass. The full catalogue is
**184** logical results / **20** shared gameplay processes and is not rerun.
That continuation preserved the animation-name drift, now repaired by the
current potion continuation. The other recorded runtime faults remain open.

## Prior Continuation — Recorded Courtyard Regression Route

The user's Regression **04** run fails Debug's guessed camera-166 crossing while
startup and movement pass. Their finalized session `20261026_110852_153` records
the correct pedestal → central courtyard → pedestal loop. The
[courtyard route journal](../../../../../journal/entries/recorded-courtyard-route-2026-10-26.md)
owns its preserved human bundle, development failures and acceptance limits.

The regression now follows published waypoints through central camera **125** /
floor **4096**, then back to pedestal **175** / floor **3328**, within **500**
world units of its starting area. The old camera-166 crossing, identity/alive,
released movement, native Quit and completed-inspection gates remain. Continuous
SDL input follows the two recorded legs; a separately declared bounded clearance
path is selected only when live guard **293** occupies the return stairs. No
actor, camera, clock, RNG, health or population state is written.

Human skip progress **438** is recorded as provenance. Fresh probes show timing
alone does not reproduce guard placement, so the final suite preserves its
ordinary progress-**83** startup and all movement assertions in the same process
as traversal. Regression **04** passes **8/8** in **69.68 seconds**, with Debug
visible and ASan headless, using one shared process per build. The full plan
remains **182** cases / **20** gameplay processes. Earlier failed route attempts
are retained; this does not close wider movement/AI or full-suite acceptance.
Separate native examples validate the alternate return input path in ASan with
a guard in the stair region and, in Debug, the bounded pedestal approach after
movement finishes on floor **3712**. Both finish the full loop, confirmed Quit,
native exit **0** and complete inspection. All **42** runner contracts, the
**241-document** README tree and whitespace checks pass. Recording is off for
these fresh probes; no exact-replay acceptance is claimed.

## Prior Continuation — Menu Stages And Concurrent Configurations

The user requests broader menu coverage and now authorizes concurrent Debug/ASan
execution, superseding the previous parallelism deferral. The
[menu/parallel journal](../../../../../journal/entries/menu-stages-and-parallel-suite-2026-10-25.md)
records bounded acceptance and newly exposed failures. The catalogue has **182**
logical cases and plans **20** gameplay processes shared versus **96** isolated.
Block **03** selects **102** logical results in **two** processes, one per build.

The display picker offers headless, visible Debug, visible ASan or both windows.
Configurations run concurrently by default; each retains sequential journeys,
isolated artifacts and a pinned executable. CLI `--workers 1` restores sequential
execution. Source/tool checks run once, prerequisite handling is preserved and
merged HTML/JSON/JUnit reports retain checkpoint provenance. Worker interruption
and crashes preserve completed assertions and fail the overall suite.
Suite **01** still bypasses the display picker; the user's game/full-suite names
and ordering are preserved.

`Journey.MenuStages` checks horseback intro, pedestal intro and released gameplay
in one process: Escape/Cancel/Quit-No, Settings, option controls and labels,
Load/Save availability/dialog cancellation, and Start Game returning to the
initial horseback camera/action/player state. No state restoration is used.
Resolution behavior, audible music/effects, actual saved-state serialization and
loading, subtitles and female restart remain explicit per-stage optional skips.
A flag change or dialog opening cannot count as functional audio or persistence.
Independent UI failures can continue only after verified cleanup through input;
failed assertions remain FAIL, and native stops/crashes cannot use this cleanup.

The user's former visible menu selection passed **6/6** in **53.04 seconds**.
The equivalent concurrent selection passes **6/6** in **26.19 seconds**, showing
Debug while ASan runs headless. The expanded both-visible run retains **17 PASS /
14 FAIL / 25 BLOCKED / 46 SKIPPED** in **54.28 seconds**. Debug completes dialog
and show/hide assertions at all three stages, but all nine option-label checks
fail and gameplay Start Game segfaults in `FUN_0043a39c`. ASan preserves earlier
passes/options failures before an intro Load stack-buffer overflow in
`FUN_0043ce58`. Both failures have exported, integrity-verified bundles and remain
open. The route subsequently orders restarts at each source stage; isolated
checks pass horseback restart and fail pedestal → initial intro in both builds,
retaining clean native exit and completed inspection. No runtime fix is made.
The final focused route passes **12** logical checks and records **6** optional
resolution skips in **24.98 seconds**, using two headless processes with delayed
skip progress **83**, native exit **0** and completed inspection. All **40** runner
contracts, the **240-document** README tree and whitespace checks pass. The new
journal distinguishes final route acceptance from development-route failure
evidence. The full native suite has not been rerun.

## Prior Continuation — Shared Checkpoint Journeys

The [shared-journey continuation](../../../../../journal/entries/shared-gameplay-journeys-2026-10-24.md)
changes suite execution without editing reconstructed C or the generator. The
**86** logical cases remain; the full default plan selects **18** gameplay
processes across Debug/ASan instead of **42** isolated scenarios. Compatible
checks execute their real assertions once in a shared process, with explicit
coverage declarations. Early/delayed/natural startup, swimming, fresh RNG trials
and the two configurations retain distinct journeys. `--execution isolated`
keeps the prior diagnostic paths available. Full/block and visible launches
retain automatic prerequisites, sequential windows and the headless picker.
The 2026-10-25 launch cleanup numbers the regression blocks **01–10** from
basic to advanced checks and removes the game name from their labels. One
**★ FULL REGRESSION SUITE (Debug + ASan)** entry appears first with
a prominent label and the display picker.

The user's 2026-10-25 Suite 01 report retains **24 PASS / 4 FAIL**. No window
is expected for its **28 source/tool/host checks**, even with visible selected;
the console explains that, and **01** now bypasses the display picker while
retaining its ordinary label. Its runner-contract failure came
from exact full-suite/gameplay labels and absolute launch position assumptions.
Contracts now identify those entries by their commands and verify the full suite
comes first among regression entries, preserving the user's decorated names
and ordinary-game ordering. All **28 contracts** and a desktop-free visible
CLI selection of `Tools.SuiteContracts` pass. The supplied generation diff has
exactly the documented animation-slot clearing and two **0x1117 / 0x445c**
capacity hunks; Debug/ASan animation fixtures fail that same slot ownership
assertion. Those three real source failures remain preserved; no runtime C,
generator or assertions are changed to make them pass.

The user's visible Suite 02 run
`.tmp/gameplay-suite/run_20261025_133932_503306/` passes **8/8** logical results in
**236.28 seconds**: two builds plus six distinct startup journeys. Inspection of
its commands confirms early skip (progress **1**), delayed skip (progress **83**)
and natural completion, each in Debug and ASan. Every native exit is zero and
all six inspections are complete. Repeated released-player/menu phases validate
each distinct process; these startup variants and configurations cannot share
one execution. Console startup lines now identify the mode/configuration and
covered checks, the delayed route is named `Journey.DelayedSkip`, and lifecycle
metadata records both. The supplied gameplay run is retained without rerunning;
all **28** runner contracts pass after these reporting/launch-only changes.

Checkpoint passes survive later failures. A failing checkpoint is FAIL and
unexercised dependents are BLOCKED; fresh setup failures retain their own root
checkpoint. Journey lifecycle failure makes the run fail even after all logical
assertions passed. JSON, HTML and JUnit preserve shared evidence and independent
logical results. The guide documents the schema and lifecycle rows.

Bounded native Debug and ASan workshop chains each pass **8/8** logical cases in
one process, including movement/release, sword attachment/following, four attacks,
smith death and door passage, at **74.08 / 74.38 seconds**. A Debug startup,
movement, eight-unarmed-attack and menu selection passes **5/5** in one process
(**50.82 seconds**); a visible Debug menu selection passes **3/3** in one SDL
window (**25.55 seconds**). Recording is off; inspection and phase/input journals
are retained. These results do not establish exact replay. The equivalent
isolated Debug workshop selection also passes **8/8**, using **7** processes
and **274.17 seconds**: sharing removes six startups and four workshop traversals
and reduces measured duration by **73.0%**, retaining all logical assertions.
The unarmed/menu equivalent is **4 → 1** processes and **114.79 → 50.82 seconds**
(**55.7%** reduction), with all five logical cases passing in both modes.
A deliberate native interruption verifies partial PASS/FAIL/BLOCKED reports,
exit **130** and process cleanup. All **28** runner contracts and the
**239-document** README tree pass. Full-suite native acceptance is not claimed.

The larger combined Debug route is explicitly **red**: after startup, movement
and unarmed checkpoint passes, workshop traversal stops progressing at **2,703**
probe updates and hits its **290-second** probe bound. Results retain **4 PASS /
1 FAIL / 7 BLOCKED**, including build identity. Four `Log cleanup failed:
std::bad_alloc` messages occur without the former worker abort. This does not
explain the allocation failure, establish its connection to the stalled update,
or reproduce the separate `FUN_0042f85c` signal. The inactive session and matching
binary are exported and integrity-verified in `core-timeout-bundle/` under the
journal's evidence root. No unchanged gameplay retry or runtime repair is made.
Later unarmed-contact/sword/stability checkpoints are not credited. Broader
combined-route and full-suite acceptance remain open.

## Prior Continuation — Automated Gameplay Regression Suite

The [visible-block and abort continuation](../../../../../journal/entries/suite-visible-unarmed-and-retention-abort-2026-10-24.md)
repairs session maintenance's allocating error handler after the user's new
suite SIGABRT. A controlled i386 allocation/reporter fault reproduces the old
termination and passes after repair normally/ASan; the original allocation
failure's cause remains unproven. The catalogue now has **86** cases, including
eight unarmed attack directions/modifier combinations and real unarmed enemy
contact independently of sword pickup. Full and block launches offer a
default-headless display picker, automatic prerequisites and sequential visible
SDL windows; a direct visible full-suite entry is also available. Parallelism
is deferred. The normal human F5 launch remains unchanged.

Focused final checks pass **14/14** in Debug/ASan: eight unarmed input/action
combinations in each, actual smith damage **100→80** without sword pickup, their
movement/workshop/menu prerequisites and both host fault contracts. Separate
workshop probes pass **65-second** released observations and clean menu exit in
both configurations, beyond the default retention interval. Earlier prototype
contact failures remain recorded. These fresh probes do not establish an exact
replay of the reported allocation failure or close broader stability.

The user now prioritizes a maintained end-to-end regression suite. The
[suite guide](../../../../../gameplay-tests.md) describes its separate full-suite
VS Code launch, dependency order, input-only journeys and
PASS/FAIL/BLOCKED/SKIPPED HTML/JSON/JUnit reports. Original-code checks run
independently of failed traversal prerequisites. Every successful journey also
checks menu cancellation, resumed movement and confirmed Quit/native exit zero.

The catalogue covers startup variants, movement, courtyard/workshop traversal,
sword pickup and attacks, smith death, player damage, door passage, potion
consumption and branch coverage, swimming and bounded mixed stability. Remaining
potion lifetime/cure and shore exit are explicit skips; armed-water checks now
run in the current water block. Four bounded fresh potion trials cannot
guarantee every random branch; the current potion continuation makes those
summaries optional. The initial animation-name gate failure is now repaired
through the original-code comparison and existing generator mirror. See the
[suite journal](../../../../../journal/entries/gameplay-regression-suite-2026-10-24.md)
for current runs, route limitations and evidence.

The first 80-case integration run finishes with **43 pass / 10 fail / 21 blocked /
6 skipped**. Focused final checks recover correct menu/waypoint qualification;
Debug/ASan core sword, smith kill, door and swimming journeys pass. Damage is
observed **100→95** in a focused Debug run, but fresh trials can remain unexercised.
A later ASan mixed-journey process exposes a new `FUN_0042f85c ← FUN_0042b880`
SIGSEGV during workshop traversal. Its binary/input/state/stack evidence is
preserved in the suite journal; source-backed recovery and longer stability
remain open.

The newer visible ASan block catches that same `FUN_0042f85c` leaf before the
movement scenario's courtyard readiness, correctly blocking dependent unarmed
combat. Its separate pinned bundle and limits are in the visible-block journal.
It remains an open event-contract fault, distinct from retention's repaired
exception handler. Source-backed recovery of this captured failure takes
priority when gameplay stability work resumes.

## Prior Continuation — Extended-Gameplay Alternate Target Crash

The [crash investigation](../../../../../journal/entries/alternate-target-crash-2026-10-24.md)
supersedes the earlier stability deferral. Pinned human session
**20261024_161320_208** reproduces `FUN_0042e684` SIGSEGV at sequence
**2,260,310,849**, checkpoint **204**. Original caller/leaf instructions recover
the updating actor in EAX and independent X/Z angle inputs with retained Z.
The scoped repair is mirrored in the generator; **65,536** alternate-target
and **65,536** sibling attack-height comparisons pass normally/ASan.

The formerly unexplained animation-name hunk is now committed in **e2c4acd**:
its reduced bounds and removed slot clearing remain preserved. Current-source
Debug/ASan compatible replay diverges at checkpoint **155**; the existing
animation-name fixture also fails. Isolated generated builds retain the original
animation-name repair and match all **204** checkpoints in Debug/ASan, returning
a valid target at the exact former fault before exit **75/INCOMPLETE**. This is
failure-boundary evidence, not complete replay or extended gameplay acceptance.
The journal distinguishes those isolated executables from normal build outputs.
Four ordinary builds, baseline/control/requester checks and fresh Debug/ASan
sword routes pass. Longer fresh input trials survive 300 additional updates and
15 seconds in isolated generated Debug/ASan, but do not select a nonempty target;
they retain their distinct paths and health observations in the journal.

## Prior Continuation — Random Potion Outcomes

The [outcome review](../../../../../journal/entries/random-potion-outcomes-2026-10-24.md)
replays human session **20261024_153511_995** through all **135** exact checkpoints.
Its `ken:potmagic` selection is a conditional cure/no-op: Joe has neither relevant
timer, so health remains **85** while drinking and bottle removal succeed.
The original selector has healing, poison, invisibility and this conditional
branch. Repeating exact replay cannot vary recorded RNG; bounded fresh input
routes sample different branches without assigning health or RNG. Poison onset
and invisibility dispatch/cleanup have fresh evidence. A route derived from human
keyboard holds now reproduces natural damage before adaptive workshop navigation;
two fresh healing selections restore Joe **85→100** through `gethealth`, remove
the bottle and retain control. All four branches are observed across **17**
successful fresh pickups. Final poison death, invisibility expiry/cure and human
healing repetition remain open. Wider work stays deferred.

## Prior Continuation — Visible Health And Potion Status

The [health/status review](../../../../../journal/entries/diagnostic-health-and-potion-status-2026-10-24.md)
confirms the user's latest bottle removal and later sword attachment/attacks.
Recorded health falls **100→70** before drinking; original HUD graphics are
omitted in diagnostic gameplay. A new read-only bottom panel exposes actual
health plus poison/invisibility action/timer status. It hides during modal
menus and stays visible with Joe offscreen. Normal/ASan marker fixtures, four
builds and live Debug/ASan potion routes pass. Human health recovery and potion
lifetime/cure checks are next. Wider pickups, extended stability and rendering
are deferred at the user's explicit request.

## Prior Continuation — Consumed Bottle Removal

The [bottle-removal review](../../../../../journal/entries/consumed-potion-removal-2026-10-24.md)
confirms both left-hand bottle and right-hand sword attachments in the user's
new run; all **549** exact replay checkpoints match. Animation-name interning
and lookup incorrectly used **4,375** of the original **17,500** bytes. This
turned the bottle's `glofade`/`potvan` chain into missing actions. Restoring the
original bounds and new-animation slot ownership lets `ken:RemoveActor` clear
the bottle's representation and reciprocal attachment.

All **1,800** installed animation names match original x86 in normal/ASan
fixtures. Fresh input-only Debug/ASan routes verify drinking and bottle removal,
then sword collection, all four attack directions and movement with the bottle
still gone. Separate final routes retain poison dispatch. Four builds, generator
parity, actor/script-name fixtures and runtime baselines pass. Human F5 repetition,
healing from damage, other effects/items and broader fidelity remain open.

## Prior Continuation — Workshop Random Potion And Delayed Effects

The [potion review](../../../../../journal/entries/workshop-random-potion-and-timers-2026-10-24.md)
confirms human session **20261024_142028_732** through all **742** exact
checkpoints and clean menu exit. Bottle **537**/`fakepot2` is a random-effect
potion: the original script **189** selects **183**/`ken:purpotion` on pickup.
It attaches to Joe and starts `joedrink`. This corrects its earlier prop label.

Delayed effects lost their actor/action/delay arguments, allocated outside the
original timer pool and never passed an unsigned deadline test. Those contracts
are restored with generator parity and **12,288** original-code cases each in
normal/ASan. Fresh input-only Debug/ASan routes now queue poison/death, execute
poison action **409** and remove its timer, retaining future death, Joe health
**100**, state **4**, and no sanitizer report. Four builds, marker and scheduled
completion fixtures pass. Healing from below maximum health, final bottle
cleanup, poison death/cure/fade and broader items remain open. Current sampled
bottle attachment persists; no speculative disappearance is introduced.

## Prior Continuation — Door Marker Placement And Creature Direction

The [marker follow-up](../../../../../journal/entries/long-play-cache-reclamation-and-markers-2026-10-24.md#follow-up-door-marker-placement-and-creature-direction)
corrects intact doors to follow the first model node's offset, half-extents and
rotation. Workshop door **980** is broad along local Z and offset from its actor;
the previous centred X-wide slab misrepresented its placement. Living creature
markers again draw their projected local +Z line. Corpse markers remain low.
The host computes these cues privately, without changing actor/collision state.
Debug/ASan marker fixtures verify both hinge-side headings, visible creature
direction pixels, corpse suppression and unchanged game memory. Four builds
pass; fresh Debug/ASan input routes confirm sword pickup, collapse and passage
with health **100** and no sanitizer report. Evidence and limits are recorded
in the linked journal.

## Prior Continuation — Longer Playthrough, Cache Reclamation And Markers

The [2026-10-24 review](../../../../../journal/entries/long-play-cache-reclamation-and-markers-2026-10-24.md)
verifies deaths of actors **602, 293, 284, 74**, destruction of doors **980, 963**
and attached sword **3717**. Potion pickup is not confirmed: the two workshop
Space attempts leave **537**/`fakepot2` unchanged; its original handler is
`ken:fakepot`.

Exact replay reaches checkpoint **469**, then exhausts the temporary record pool
while loading enemy animation **1439**. Escape is never delivered. Cache eviction
now retains the selected action and releases its keyframes/event records, with
original-code comparisons and generator mirrors. Final Debug replay passes the
load and all **469** checkpoints, ending at the incomplete recording boundary.

Host-only shapes distinguish creatures, corpses, doors, debris, bottles, blades,
items and props, with original-name labels. Modal menus suppress the overlay.
Fresh Debug/ASan input routes acquire the sword, destroy/pass the door, cancel
Escape, reopen Quit, confirm Yes and exit normally. Four builds, parity,
original comparisons, marker fixtures and runtime regressions pass. The long ASan replay is incomplete at 180 seconds/checkpoint **308** with Joe alive and no sanitizer report; the late cache boundary is established by Debug replay and original-code/ASan fixtures. Genuine
potion effects, other items/points, wider combat and full rendering remain open;
prior ASan courtyard steering/floor-return limits remain separate.

## Prior Continuation — Workshop Door Hit Callback

The [2026-10-24 door journal](../../../../../journal/entries/workshop-door-hit-callback-2026-10-24.md)
confirms the human smith kill (actor **602**, health **−20**, state **11**) and
exactly reproduces the door crash at checkpoint **125**, sequence
**1,768,693,458**. Target **980**/`kdorr` still has health **60**: this is a hit
callback failure before collapse. The selected attack and target-hit script
records were lost entering the interpreter. Both original handoffs are restored
with scoped code/owner/target/child/node contexts and generator parity.

The expanded original-code fixture passes **32,768** cases normally/ASan,
including **37,188** scripted callback handoffs. Fresh SDL Debug/ASan routes
reduce the left door **100 → 60 → 20 → −20**, execute hit action **370** and
collapse action **377**, then observe state **11** with no representation.
Released forward movement passes through the opening into camera **164** with
Joe health **100**, state **4** and no modal or sanitizer report. Four builds,
baseline/control and requester checks pass. Next is human F5 door collapse and
passage repetition; other objects, area attacks, wider combat and full rendering
remain separate acceptance. Prior ASan courtyard steering/floor-return limits
remain open.

## Prior Continuation — Sword Attacks And Attached Position

The [2026-10-24 attack journal](../../../../../journal/entries/sword-attacks-and-attached-position-2026-10-24.md)
confirms human pickup and exactly reproduces the subsequent Ctrl/arrow crash in
`FUN_0042e7dc` at checkpoint **91**, sequence **1,338,228,752**. Original actor/XZ
and direction-preservation contracts are restored. The sword's persistent
workbench cylinder reflects stale actor coordinates: attached rendering lost
owner/actor arguments and cylinder mode omitted the moving hand pose. Those
contracts and the original bounded pose work-list are restored, with generator
parity and normal/ASan original-code comparisons.

Fresh SDL Debug/ASan input routes acquire the sword, start all four requested
Ctrl/arrow attack directions, release and move with health **100**, state **4**,
representation **9**, no modal and reciprocal attachment links. The sword's
world coordinates change with its hand attachment. Builds, baseline/control and
requester checks pass. Debug's populated courtyard return passes; ASan steering
attempts miss the outward camera or return floor while retaining health 100 and
no sanitizer report. Human swing/marker repetition and actual weapon contact/damage remain open.

## Prior Continuation — Water Replay And Sword Pickup

The [2026-10-24 pickup journal](../../../../../journal/entries/water-replay-and-sword-pickup-2026-10-24.md)
confirms human session `20261024_115621_101`: all **565** exact checkpoints match,
including swimming across cameras 543→545 with health **100**, state **4** and
representation **13**. Session `20261024_115718_697` confirms walking through
350/348 into workshop camera **347**, then exactly reproduces the Space pickup
crash at checkpoint **62**. Both pinned recordings are preserved independently
of session retention.

Original player/polar arguments, the first model-node origin needed for pickup
height, the attachment event's node/owner/script handoff, and hosted Space release
are restored. Fresh SDL Debug/ASan input routes acquire actor **3717**, verify
reciprocal attachment links to Joe, equipped kind **3** and representation **9**,
then move while retaining health **100**, state **4** and no modal. Original-code
comparisons, generation parity, populated courtyard returns and baseline checks
pass. The crashed recording ends at its fault; fresh input supplies pickup
completion evidence. The newer human report above confirms pickup; the attack
and attached-position continuation owns the next acceptance.

## Prior Continuation — Early-Skip Startup Regression

The [2026-10-24 startup repair](../../../../../journal/entries/pedestal-intro-restart-2026-10-24.md)
reproduces the user's pedestal-to-horseback restart, rooftop displacement and
later death/menu in a complete exact replay (1,810 matching checkpoints). The
original skip script's nine actor cleanup references were unresolved because
actor names were truncated at 10,000 rather than 40,000 bytes and 108 startup
literal suffixes were absent. Both contracts and new actor-slot ownership are
restored, with generator parity and original-code comparisons.

Fresh Debug/ASan early skips finish the pedestal scene, retain movement and pass
60-second released-input checks. Skipping at the recorded first-action progress
83/495 also passes populated crossing/return with health 100 in both builds.
Natural-intro water/swimming checks pass again. The complete 83/495 skip-to-water
route passes in Debug; ASan times out before water with health 100 and remains
incomplete. The newer human sessions confirm traversal, swimming and workshop
re-entry after the startup repair; pickup repetition and the separate broader
Debug floor-return issue remain open. Old recordings
correctly diverge after changed cleanup; no checkpoint acceptance is weakened.

## Prior Continuation — Water Entry And Object Interaction

The [water-entry repair](../../../../../journal/entries/water-entry-and-player-resource-2026-10-23.md)
restores original actor identity for ordinary gameplay loading: local node zero
formerly aliased potion actor 4119/`fpot6` as Joe, losing his swimming capability.
Live swimming-scene reads and opcode-0x54's packed state write are also recovered.
All 1,922 actor headers and bounded original-x86 water/selector/reload contracts
pass. Natural-startup Debug/ASan input routes reach camera 543 and swim forward
with health 100, state 4, representation 13 and no modal. The newer human replay
confirms water entry/swimming; shore exit and held-item swimming remain open.

## Prior Continuations — NPC Poses And Object Interaction

The [camera-722 continuation](../../../../../journal/entries/blank-requester-and-large-replay-2026-10-23.md)
restores the full original directional-reaction table and passes 524,288 x86
comparisons normally/ASan. The user repeated the location without the blank OK
prompt; the new recording completes and passes three exact replays with all 120
checkpoints matching. The old recording's post-repair divergence
keeps its original terminating caller unproven. Requester text/evidence and
console/reader improvements are documented with the tool acceptance.

The [post-pedestal callback repair](../../../../../replay.md#status-and-current-acceptance) reproduces the user's new `FUN_0043cac0 ← FUN_00414e68 ← FUN_0044f508 ← FUN_0044f310 ← FUN_00426ca4` stack by exact replay at sequence 890,925,953/checkpoint 47. Original instructions recover selected code/actor arguments, cleared script node and retained actor lifetime. Compatible replay returns from four callbacks before incomplete-prefix exhaustion; natural Debug/ASan intros and 60-second released idle observations pass. Original callback comparisons and baselines pass. An additional populated Debug traversal remains failing its floor-return assertion; ASan's bounded round trip passes. Workshop re-entry, pickup and full experimental ASan acceptance remain open.

The [natural-intro detach repair](../../../../../journal/entries/natural-intro-attachment-detach-2026-10-22.md) recovers the reported `FUN_0042db74` event node and attached-actor inputs. Its original checkpoint completes both intros in Debug without input or recording, followed by a verified 15-second idle observation. Original detach/caller comparisons pass normally and under ASan. The separate actor-deactivation script failure exposed then is addressed by the callback continuation above; workshop re-entry, sword pickup and broader interaction acceptance remain open.

The user confirms the two pedestal guards wander after intro 2. [General population and direction audit](../../../../../journal/entries/general-population-and-direction-audit-2026-10-19.md) now recovers the first `0x42f9c0` spawn event and queued-action failure, including root/FK pose and angle conversion inputs. Correct archive identity is scoped to original scheduler/event loads. F5 sets `E2R_DEFER_BACKGROUND_SPAWNS=0`, with no population-probe flag or per-enemy whitelist. Populated Debug/ASan 175→166→175 routes and released-input observations pass. Earlier deferral, opt-in-only and failed-return statements below describe the prior slice.

The [2026-10-20 modifier-release continuation](../../../../../journal/entries/direction-modifier-release-2026-10-20.md) reproduces a matching immediate Up+Left freeze after released desktop modifiers remain logically held. YROT also freezes. The compatibility key-up repair clears those flags; deterministic Debug/ASan and native Wayland ASan replays turn again, and the user reports no freezes anymore. The longer native Debug route later fails in an NPC pose event (`0x42faf8 → 0x424318`), whose node/pose handoff is recovered by the NPC pose continuation below. General object interactions, broader enemy actions/combat, complete directional fidelity and full experimental ASan remain unaccepted.

The [NPC pose continuation](../../../../../journal/entries/npc-pose-chain-recovery-2026-10-20.md) recovers endpoint/root/IK inputs and the node-chain event's pose owner from original instructions. Original x87 table initialization, endpoint/IK/attachment memory comparisons and event handoffs pass normally/ASan. The prior early-Space Debug spawn frontier is crossed; populated Debug/ASan round trips and 60-second observations pass. Native scripted camera steering retains a route limit; wider combat/interaction and full experimental ASan remain open.

The [stables crash continuation](../../../../../journal/entries/stables-node-hit-query-2026-10-20.md) follows the user's camera-177 report at `0x427160 ← 0x42efdc ← 0x42faf8`. The hit-query caller now retains X/Z and separate polar outputs; the adjacent owner-to-target facing vector also has both coordinates. Normal/ASan original-code comparisons cover 16,384 filter/contact cases. Exact manual stable re-entry, horse presence and broader scripted/weapon contacts remain separate acceptance.

The [blacksmith sword activation](../../../../../journal/entries/blacksmith-sword-activation-2026-10-20.md) restores placement caching, the original loose-archive visibility index and retained actor/action inputs. Scene 1909's sword actor 3717 activates at its original workbench position and projects as an orange cylinder in Debug/ASan. The integration probe selects camera 347 through the normal visibility sweep, then restores the prior view without moving Joe; it does not establish walking into the workshop or pickup. Populated courtyard round trips pass afterward. F12 now includes preloaded script scenes for the current camera, including resource IDs above 1199.

The [workshop initialization/visibility continuation](../../../../../journal/entries/workshop-initialization-and-actor-visibility-2026-10-20.md) follows the user's failed approach at camera 350. An isolated prior-source build reproduces `0x456924` during object initialization; the helper and opcodes `0x66`/`0x68` now retain their actor/value/action inputs. The actor visibility updater also retains the original world-position argument. Neutral object markers, separate generated counts and visibility filtering address the misleading enemy density; the scheduler still matches the original four-generated-actor cap and 50-tick cadence. Debug/ASan view sweeps 356→350→347 activate the sword and pass populated courtyard returns, with the real durability call observed under ASan. Exact F5 walking re-entry and pickup remain open.

## Evidence And Dependencies

The [early-Space continuation](../../../../../journal/entries/early-intro-skip-population-2026-10-20.md) reproduces the user's remaining F5 population difference: an early skip leaves the original script population gate set even with the correct launch flags. Space now dispatches the original `dav:skipsc` script, including its population-enable opcode. Additional actors appear at release and the bounded ASan census passes. Debug then reached `0x42f9c0 → 0x424318 → 0x423674` in an unrecovered IK branch. The NPC pose continuation above supersedes that failed exploration result and recovers this node/root/IK family plus the preceding node-chain event pose handoff. Broader interactions remain the next bounded work.

The [manual castle report](../../../../../journal/entries/manual-castle-exploration-2026-10-19.md) confirms practical stairs, angled ledges, collisions and extended free movement, but no switches, doors, traps, enemies or pickups. The existing F5 launch explicitly defers automatic background population. [Task 04](task-04-recover-npc-spawn-query-inputs.md) recovers its bounded inputs; full loading/activation remains unresolved. [Step 08 Task 03](../../step-08/tasks/task-03-activate-scene-backed-children.md) owns original scene-child identities and activation.

Automatic NPC population and scripted objects are separate paths. An empty cylinder overlay alone does not prove no interaction state exists. Establish resource identity, live instance/scene membership and presentation eligibility before classifying each missing category. Do not infer script resources from camera slots or manufacture the reference creatures/objects.

## Next Bounded Action

Extended gameplay stability takes priority after the latest human crash report.
Repeat the longer route through the normal **Ecstatica Recompiled** F5 launch,
preserve its pinned executable/recording, and investigate the first new failure
from original code. The current crash recording ends at its fault, so further
route acceptance requires fresh bounded input or a new human recording.

The current potion repair resolves the animation-name mismatch through original
instructions, passing normal/ASan fixtures and complete generated parity.
The linked crash journal retains the original mismatch and earlier replay
limits; replay acceptance must still be established with the current binary.

Potion lifetime/cure, broader items/points and original mesh work remain later
work. Retain existing courtyard steering and full-render limits.

## Acceptance And Limits

The first slice requires a source-confirmed resource to instantiate/activate, appear as a suitable diagnostic cue when applicable, and perform one expected behavior or player interaction. Joe must remain controllable, and the courtyard crossing/return must still work. Record loading, actor/script state and normal SDL presentation together. Full category coverage, enemy AI/combat, original models and full experimental ASan remain separate acceptance; do not remove population deferral globally based only on intercepted fixture success.

## Pedestal Pair Correction — 2026-10-19

The original terrain experiment below did **not** establish the two pedestal enemies. The user's screenshot comparison is the acceptance target: Joe plus two enemies while still restrained. Original `St_gobsc` resource 101/view 175 owns actor 284 (`gob3`) and 293 (`gob3b`), independently of terrain spawning.

Scoped scene-child archive loading now preserves their original identities/tracks. Ordinary four-flag F5 presents three cylinders before and after Joe's release; no population flag or debugger activation is required. Root-reference, sound-event and node-scale inputs have original-code coverage. Cylinder mesh bypass now omits child-bone/IK posing as well as alternate mesh raster paths; articulated collision/combat and attachments remain unverified. General object interaction and complete Task 09 acceptance remain open.

Run `scripts/probe-e2-player-motion.py EXE --pedestal-guards --camera-round-trip --observe-seconds 5 --timeout 120` for restrained/released guard presence, projection and the SDL route. Follow the [guard journal](../../../../../journal/entries/pedestal-guard-activation-2026-10-19.md) for final verification and remaining limits. Older census names come from a malformed hosted name pool; verify original resource names by archive ID.

A subsequent user Space-skip crash report led to [FAN/action parser ownership and finalizer repairs](../../../../../journal/entries/intro-skip-fan-ownership-2026-10-19.md). `--intro-skip-action N` now tests the real SDL Space handoff at observed horseback actions; `--natural-intro` tests completion without a skip. Keep the runtime reproduction limit and broader acceptance limits explicit.

## Implemented Population Slice — 2026-10-19

Before the companion-loader fix, the release census found only Joe in the loaded/active actor tables and no active script-scene children. The original population scheduler is reached; it was not an input or scheduling gate. Its floor wrapper discarded the valid height return. After that repair, actor loading exposes an archive identity error: the binary header's local node field was used as the global actor name, and payload bytes were accepted as headers. A header-aware lookup finds 1,922 actual actor resources, including the previously missing terrain-selected resources.

`E2R_POPULATION_PROBE` isolates corrected archive actor identity. The repeatable probe enables it **after observed release**, then disables spawn deferral through configuration only. Actor construction uses the normalized name field only while parsing the requested archive actor. The existing intro/action resources keep their earlier behavior. This boundary is necessary: applying all corrected actor identities at startup exposes unrecovered skeletal transform inputs. Do not add the flag to the everyday F5 environment yet.

The slice also restores the initial script's code/actor inputs, contiguous line-of-sight vectors, NPC wandering terrain samples, distance outputs, persistent pose destinations and deactivation ownership. Two byte-offset mistakes in actor-list removal could discard Joe when a new spawn was rejected or culled; both now compare with original instructions. Cylinder mode also omits the actor pixel-rectangle overlap pass, extending its existing graphics bypass while actor updates, physics, scene selection and scripts continue.

The new `scripts/check-e2-population.py` compares original actor construction and script handoffs, 512 line-of-sight traces, 4,096 wander traces, 65,536 distance vectors and actor removal/deactivation. It checks 40 real archive lookups among 1,922 headers. The scene-grid fixture now compares the floor wrapper return as well as its helper.

```sh
python3 scripts/check-e2-population.py \
  /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE \
  /home/rgrabowski/Games/Ecstatica2/Files/ECSTATIC --asan
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl-asan/e2recomp \
  --population-frames 300 --population-only --output /tmp/e2-population-census
```

The live census records resource names, loaded instances, active membership, positions, actions and states alongside SDL visibility packets. ASan survives 300 population frames with Joe active and original resources entering state 3 (wander) and changing position. A longer ASan input probe reaches camera 166 with additional projected cylinders in the normal SDL window. This establishes a bounded population/behavior/presentation recovery, not general interaction or full experimental sanitizer acceptance.

## Prior Slice Failure And Acceptance Still Open

- Debug's extended population probe reaches an attachment/spawn action through `0x427584 → 0x42ae80 → 0x42b338 → 0x42b880 → 0x42f9c0`; that helper still loses its node/actor/action inputs. Recover this event family before enabling population in F5.
- The population-enabled ASan camera probe crosses to 166 but its reverse-input route does not return to pedestal camera/floor within the probe limit. Existing Joe-only Debug/ASan crossing/return remains verified. Do not treat either the longer probe or the full task as passing.
- Script-owned scene activation remains independent: the original empty release census predates the fixed guard companion. Switches, doors, traps and pickups still require a source-confirmed resource and one verified interaction. Camera slots are not script IDs.

See the [population recovery journal](../../../../../journal/entries/scene-population-recovery-2026-10-19.md) for evidence and commands. Keep the original Task 09 acceptance criteria and F5 spawn deferral in place.

## Callback contract

The post-pedestal repair supplies the selected script code and actor to
`FUN_0044f310`, clears the script node/child arguments, and preserves actor ownership
across the callback. The durable repair is mirrored in `GenerateRecon.js` and
covered by the script-flow and population fixtures. The replay guide records the
historical exact-crash and compatible-prefix results; native completion and wider
traversal remain separate acceptance gates.

The originally referenced continuation journal and its local bug bundle are not
present in this checkout. This task and the replay status are the available
implementation record; they do not replace the missing raw historical artifacts.
