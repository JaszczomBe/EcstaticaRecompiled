# Workshop door passage navigation — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Goal-driven regression navigation](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Runtime owner: [Population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Previous evidence: [Original door hit callback and passage](workshop-door-hit-callback-2026-10-24.md).
Usage: [Goal-driven gameplay tests](../../gameplay-tests.md#goal-driven-encounter-navigation).

The user supplies workshop block
`.tmp/gameplay-suite/run_20261026_154335_902300/` and requests the next failure be
fixed. The run selects **16** logical checks and two live gameplay processes:
Debug visible on Wayland, ASan headless, two configuration workers, recording off.
Both builds pass pickup, four sword directions, smith death and door destruction.
Both fail the subsequent passage assertion: **14 PASS / 2 FAIL**, **93.17 s**.

## Evidence and repair boundary

Original actor **980 / kdorr**, owned by `cyd_dor8`, remains at
**(-2368,4096,-10944)**. Both native journals prove its health **100→60→20→−20**,
state **11** and representation **0** before passage. Destruction is exercised;
there is no demonstrated new contact-script crash or failed collapse in this run.

At passage start, Debug Joe is approximately **(-2572,4096,-10520)** and ASan Joe
**(-2565,4096,-10539)**, yaw **28160** in both. The fixed **60-update** forward
hold then **30-update** release observation ends at **(-1335,4096,-9299)**,
yaw **4608**, in Debug, and **(-1551,4096,-9961)**, yaw **6656**, in ASan.
Recovered movement changes heading during the hold; the controller never corrects
it and Joe leaves the opening's approach region. These observations do not
establish the particular collision/steering cause. Failure inspections are
incomplete after the assertion, not successful menu exits.

The [2026-10-24 door investigation](workshop-door-hit-callback-2026-10-24.md)
and original scene placement establish the known opening and the accepted
negative-Z passage from camera **347→164**. The new controller uses that explicit
scenario guidance only for verified door **980**. It does not infer the traversable
normal of arbitrary doors, call recovered floor queries, or classify unknown
blockers as locked/destructible.

`Navigator.cross_opening()` first aligns with a near point, then guides Joe
through the door center and a far point using live heading/position observations
and ordinary SDL input. It uses the existing navigator's three-update batches,
update/replan/host bounds, local progress checks and failure/interruption cleanup.
A **256-unit** half-width is a conservative test gate around the declared center,
not an extracted physical doorway width. Interpolated consecutive observations
must cross that plane within the gate and height band. A detour outside the
required gate fails rather than crediting passage through another route.

`Journey.strike()` still requires actual door health loss, nonpositive final
health, state **11** and removed representation before starting the crossing.
After crossing, it releases input, advances **30** updates, retains the original
**distance beyond door >100** assertion and also requires the door's floor.
`details.door_passage` retains approach/final positions, plane/gate, crossing,
released displacement and camera; `details.navigation` retains every steering
and crossing observation. Earlier checkpoint passes survive a failure, and an
established door/passage failure remains FAIL.

This changes test navigation only. Runtime C, generator, actor placement,
collision, population, health, RNG and ordinary F5 controls are untouched. All
pre-existing staged/unstaged work remains; no stage, commit or push is performed.

## Native validation

Evidence root: `.tmp/door-passage-navigation-20261026/`. `baseline.json` retains
reported failure observations and identities; `validation.json` indexes the
new reports, exact source hashes, pinned executable identities and inspections.
Native examples use live population, recording **off**, explicit bounds and real
SDL input. All successful journeys require actual menu Quit, native exit **0**
and complete inspection. No exact replay acceptance is claimed.

`headless/` passes **16/16** in **92.26 s**, with two gameplay processes and two
configuration workers. Both verify the original destruction and all earlier
workshop assertions. Debug crosses with **45** navigator updates, ASan **81**,
without local replans. After release, Joe is **967.91** units beyond the original
door assertion plane in Debug and **779.80** in ASan, at floor **4096**, camera **164**.
Recorded final positions are **(-2417,4096,-12007)** and
**(-2317,4096,-11774)** respectively. Native exits and inspections complete.

`visible-debug/` repeats the user's display/selection with unchanged sources.
ASan headless passes all eight of its logical checks, including destruction,
gate crossing, **1207.62** units of released projected displacement and camera
**164**, native exit **0** and complete inspection. Visible Debug stops before
courtyard readiness with **SIGSEGV** in the previously documented
`FUN_0042f85c ← FUN_0042b880 ← FUN_0042b338 ← FUN_0042ae80 ← FUN_00427584`
event family. The fault is reconstructed line **26639**, reading through the
unrecovered `in_EAX`, arguments **11282398 / 8854972**. The retained `probe.log`
contains the stopped stack; the executable is pinned and inspection is incomplete.
No navigation or door phase has executed in that process. This run is
**9 PASS / 1 FAIL / 6 BLOCKED**, **85.83 s**. Earlier independent ASan results
remain PASS; visible Debug's door assertion stays BLOCKED. This is separate from
the repaired door-passage failure, and the unchanged startup fault is not retried
until green. Completed visible Debug acceptance remains open.

Pinned native images retain the reported failure's identities:

- Debug: `df81e8ca950b25d1f2163f495ee8c410c4ef30cdf8c31e3e6251b0ba1b68ee42`.
- ASan: `e2bde1e384582571221e2ee9d6fbe1fc3a671cf87da70df3e26a38b3ec732b50`.

## Contracts and limits

**48** suite contracts and **19** navigator contracts pass. New cases require
heading correction and a real gate crossing, reject bypasses, wrong floors,
substituted identities and initially unobserved crossings, and retain bounded
stuck/interruption failure plus input release. An integration contract proves
an intact/still-represented door cannot reach the passage controller and that
a controller's reported success cannot replace the original released-displacement
or same-floor assertions.

Builds complete for both existing SDL configurations. The catalogue remains
**185** logical cases / **20** planned full gameplay processes. The full suite,
general door/progression planning, other doors and whole-game navigation are not
accepted by this change. The **246-document** tree passes update and read-only
checks; Python compilation and `git diff --check` pass. Existing generator drift,
runtime event/menu/Load faults,
retention/allocation pressure and broader live-population variability remain.
