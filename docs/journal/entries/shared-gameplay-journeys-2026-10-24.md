# Shared gameplay checkpoint journeys — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Usage: [Gameplay regression suite](../../gameplay-tests.md).

The user authorized replacing repeated fresh-process prerequisite scenarios with
shared journeys: journeys execute, checkpoints report. Initial inspection finds
a clean worktree at **39b0f41**, following **3a1aab1**; the prior runtime/generator,
suite and retention repairs are committed. This continuation changes orchestration,
launches and documentation. Reconstructed C, including the preserved animation-name
regression, and `GenerateRecon.js` remain untouched.

## Execution and coverage

`SHARED_ROUTES` in `scripts/e2_suite.py` declares compatible sequences. Selection
still expands prerequisites/observations, then assigns each selected logical
check exactly once. Workshop prerequisites are assigned before fresh potion
trials to avoid a projected dependency cycle. The remaining explicit routes
prefer the most uncovered checks, with shorter declarations breaking ties.
Unselected checks are omitted. Local input setup runs once per journey and never
supplies assertion credit to an unexercised logical check.

The main declaration orders delayed startup, movement, eight unarmed attacks,
workshop, unarmed contact, sword attachment, sword attacks, smith death, door
passage, stability and menus. Narrow selections omit unnecessary checkpoints.
Courtyard return, water, early skip and natural intro remain distinct routes.
Four potion processes retain waits **0, 37, 83, 221**, real damage where required
and fresh RNG; Trial A can continue into potion-to-sword assertions. Debug and
ASan remain separate. The complete **86-case** plan has **18** gameplay processes,
compared with **42** isolated scenarios. These are planned counts, not a claim
that every journey completes on current runtime source.

The CLI defaults to `--execution shared`, shows coverage/process counts with
`--list`, and retains `--execution isolated` for diagnosis. Full, ten block and
dedicated visible-full launches select shared execution. The headless/visible
picker, phase titles, bounded watch pacing, menu pauses and sequential windows
remain. No parallel execution, save/load, state restoration or teleport is added.

## Reporting and lifecycle

Checkpoint contexts save status, phase range, duration and copied observations
atomically in `probe-journey.json`. Logical results link the journey, checkpoint
and shared evidence. Potion branch evaluators retain the actual trial's evidence;
full-health healing still cannot satisfy damaged-healing coverage.

A later failure preserves earlier passes, fails the active checkpoint and blocks
unexercised checks. Nested fresh setup failure retains a failing `setup.*` row
and blocks its unexercised target without overwriting an independent earlier pass.
External prerequisite failures suppress only affected checkpoints, allowing an
otherwise eligible potion trial to run after a sword failure.

Journey lifecycle is independent of checkpoint credit: timeout, native fault,
incomplete report/inspection or shutdown failure fails overall even when all
assertions previously passed. JSON schema `e2suite.result.2` retains lifecycle
rows; HTML/JUnit add explicit failed-journey entries. JUnit carries separate
journey/checkpoint/evidence properties. Interruption reads partial journals,
retains completed passes and exits **130**. GDB timeout/interruption cleanup now
uses the existing descendant-aware process stopper before the debugger vanishes.

## Native evidence

Evidence root: `.tmp/shared-journeys/`. Every fresh probe uses recording **off**,
SDL input only, isolated inspection and bounded update/waypoint/host limits.
Executables are pinned per run/configuration with SHA-256 metadata.

| Run | Logical results | Native gameplay processes | Duration |
| --- | --- | --- | --- |
| `unarmed-shared-permitted` | **5/5 PASS**, delayed startup, movement/release, eight unarmed groups, menus | **1** | **50.82 s** |
| `unarmed-isolated-final` | Equivalent **5/5 PASS** isolated Debug selection | **4** | **114.79 s** |
| `workshop-shared` | **8/8 PASS**, startup, movement, workshop, sword/following, attacks, smith kill, door passage | **1** | **74.08 s** |
| `workshop-isolated-final` | Equivalent **8/8 PASS** isolated Debug selection | **7** | **274.17 s** |
| `workshop-asan-shared` | Same **8/8 PASS** under ASan | **1** | **74.38 s** |
| `menus-visible-shared` | **3/3 PASS**, real visible Wayland startup/menu window, cancel/resumed displacement/confirmed Quit | **1** | **25.55 s** |
| `native-interruption` | Expected **2 PASS / 1 FAIL / 2 BLOCKED**, driver PASS, suite exit **130** | **1** | **18.99 s** |
| `core-shared-final` | **4 PASS / 1 FAIL / 7 BLOCKED**, timeout during workshop after startup/movement/unarmed passes | **1** | **290.13 s** |

Successful runs require native exit zero and completed inspection. The Debug and
ASan workshop chains each execute one startup and one workshop traversal, followed
by the full sword/enemy/door assertions. The unarmed selection executes movement
and all eight action/modifier combinations, rather than inferring them from
travel. Reports and journals retain their individual outcomes.

The paired Debug workshop selections have exactly the same eight logical cases
and both pass. Shared execution reduces measured wall time **274.17 → 74.08 s**
(**73.0%**) and native processes **7 → 1**. Phase journals show startup checks
**7 → 1**, workshop traversal **5 → 1**, sword pickup **4 → 1** and attack-direction
phases **12 → 4**. The meaningful movement assertion still executes once in each
selection; traversal does not stand in for it. Smith death and door passage each
execute their own health/state/deactivation and displacement assertions. The
paired unarmed/menu selection likewise passes the same five logical cases:
**4 → 1** processes and **114.79 → 50.82 s** (**55.7%** reduction), retaining all
eight unarmed action groups and the meaningful movement/release checks.

The larger combined Debug route stops progressing at **2,703** updates during
`traversal.workshop`, after all unarmed checks. Its **290-second** probe bound
fails the journey; startup, movement and unarmed logical passes remain, workshop
is FAIL and the seven later checkpoints are BLOCKED. Native output contains four
`Log cleanup failed: std::bad_alloc` messages, without the formerly escaping
worker exception/SIGABRT. The reason for memory pressure and the stalled update
is unresolved. There is no stopped-stack diagnosis or evidence connecting this
to the separate existing `FUN_0042f85c` signal. The failed path is not retried.
Unarmed contact before sword pickup and the subsequent 60-second observation
are therefore declared but unaccepted in this larger sequence.

The inactive session is exported and integrity-verified in
`core-timeout-bundle/`, with matching Debug SHA-256
**8701a474790eba560b6bf811a78befb251c7a2e0b439c36c95f9f02cfd1f47dd**.
It retains incomplete inspection and has no replay. Probe/input/phase output,
commands and matching executable remain in `core-shared-final/`;
`core-timeout-extra/` retains the phase/input/GDB/command files and hash receipt; export-time
working-tree context does not establish build provenance. No deterministic
reproduction or portable exact replay is claimed. Process inspection after the
bound confirms only the next sequential probe remains, with no timed-out inferior.

The deliberate native interruption sends SIGINT to the suite after the startup
checkpoint passes while movement is active. The final implementation retains
startup PASS, movement FAIL, unarmed/menu BLOCKED and suite exit **130**, writes
HTML/JSON/JUnit, and stops its native process tree. The bounded driver reports
PASS for those expected red-suite outcomes; it does not credit movement or
combat acceptance. Its source and receipt are retained beside the report.

## Contracts and limits

All **28** runner contracts pass, including the CLI/report execution. The
**239-document** README tree and whitespace checks pass. The contracts exercise shared coverage, all single-case/block plans,
prerequisite selection without cycles, distinct intro/RNG/water/configuration
routes, one-time workshop/sword/attack dispatch, partial failure propagation,
interruption, real subprocess timeouts, missing assertions, external dependency
filtering, lifecycle failures after all passes, coverage provenance, isolated
reporting compatibility and visible launch forwarding. Historical runner
contracts continue to exercise sanitizer detection and child-tree cleanup.

Development artifacts are retained separately: the first CLI attempt lacked the
new probe scenario choice; the sandbox-only attempt cannot ptrace; two initial
isolated comparisons exposed a report renderer treating legacy journey details
as a string. That renderer is corrected with a compatibility contract before the
final isolated comparisons. These are tooling/environment failures, not accepted
gameplay or unchanged runtime retries.

The aggregate evidence/comparison index is `validation.json` at the evidence
root; `source-snapshot/` records the final scripts and launch configuration.
Each native run retains its own preflight source digests, which can predate later
report/contract refinements during development. These runs are fresh samples,
not a timing guarantee.

The complete 86-case native suite is not rerun. Preserved animation-name and
generator drift, bottle-removal failures, courtyard-return and variable damage
routing remain open. The separate `FUN_0042f85c` fault and unexplained allocation
pressure remain visible. No stage, commit or push is performed.

## Launch picker follow-up — 2026-10-25

The user requests shorter regression launch names, one full-suite entry with the
headless/visible picker, and basic-to-complex ordering. Regression labels now use
**Regression 01–11**: source/tool checks, startup, menus, movement, unarmed combat,
workshop, swimming, potions, stability, replay and the full suite. The dedicated
visible-full duplicate is removed; every regression launch retains the shared
display picker. The ordinary **Ecstatica Recompiled** launch is unchanged.

The existing launch contracts now verify one full-suite entry, numbered order,
labels without the game name, all ten blocks and picker forwarding. All **28**
runner contracts, the **239-document** README tree and whitespace checks pass.
No gameplay probe is needed for label/order changes; existing runtime acceptance
and failures above remain unchanged. Previously staged work is preserved, and
this follow-up is left unstaged.

The user's subsequent ordering correction puts the full suite first in the
launch list as **★ FULL REGRESSION SUITE (Debug + ASan)**, with a star and
uppercase label. The ten numbered blocks retain basic-to-complex order below
the ordinary gameplay entry. The full suite still uses the same display picker;
launch contracts verify the first position and distinct label.

## Suite 01 human report — 2026-10-25

The user runs **Regression 01** with `--block checks --display visible` and
reports no window, **24 PASS / 4 FAIL** in **23.35 seconds**. The original report
is `.tmp/gameplay-suite/run_20261025_133025_086883/` and remains unchanged.
This block selects 28 source/tool/host checks and zero gameplay journeys, so no
SDL window is expected. Its launch label now says **(no game window)**, and the
CLI explains this before execution. Selections without gameplay no longer
require a Wayland/X11 desktop just because visible was chosen; report metadata
retains the requested display mode and `gameplay_selected=false`.

`Tools.SuiteContracts/console.log` contains two failing assertions inside the
single failing suite case: exact full-suite label matching and exact ordinary
game name matching. The user had decorated/renamed both and placed ordinary
gameplay before the regression entries. These label/absolute-position assertions
were too brittle. The checks now identify the ordinary launch by its debugger
program and the full suite by its runner command, retain the real arguments and
picker requirements, and verify full-suite position among regression entries.
The user's labels and ordinary-game ordering are preserved.

All **28 runner contracts** pass after that repair. A bounded CLI run with
`DISPLAY` and `WAYLAND_DISPLAY` unset, `--block checks --display visible --filter
Tools.SuiteContracts`, passes and prints the no-window notice. Its HTML/JSON/JUnit
reports are `.tmp/shared-journeys/suite01-contracts-fixed/`; terminal logs are
`/tmp/e2-suite01-contracts.log` and `/tmp/e2-suite01-cli-fixed.log`. This executes
runner checks only, with no native gameplay/input or recording.

The user's generation patch contains exactly the three previously preserved
animation-name hunks: omitted new-animation slot clearing at **0x62ba20** and
lookup/intern capacities **0x1117** rather than **0x445c**. Both configuration
fixtures fail the corresponding new-slot assertion. These are the documented
source/generator and animation-name failures, not a display failure. The runtime
C and generator are untouched, and the same failing fixtures are not rerun until
green. No full checks block or gameplay suite rerun is claimed.

Documentation tree and whitespace checks pass. Prior staged and unstaged work
is preserved; no stage, commit or push is performed.

## Suite 01 picker and Suite 02 startup variants — 2026-10-25

The user requests removing the Suite 01 label suffix and disabling its display
picker instead. Its original numbered name is restored, and its launch no
longer references `e2SuiteDisplay`; it uses the default CLI display and opens no
game window. The full suite and all gameplay blocks retain their picker. Launch
contracts now verify that exception, including the block argument at the end
of the source-check command.

The user supplies visible startup run
`.tmp/gameplay-suite/run_20261025_133932_503306/`: **8 PASS / 0 FAIL**, **236.28 s**.
Read-only verification confirms six unique native combinations: Debug/ASan each
use early skip at progress **1**, delayed skip at **83**, and natural completion
without a skip. All six native exits are zero and all inspections complete.
The other two logical results are the builds. Released-player and menu phases
repeat because each startup process must independently establish healthy release
and clean shutdown. These distinct intro paths/configurations are retained,
with no assertion or coverage removed.

Reporting now prints a startup description, build configuration and covered
checks before each gameplay execution. The generic `Journey.Startup` route is
renamed `Journey.DelayedSkip`; lifecycle metadata includes `configuration` and
`startup`. Inputs, pacing, assertions, timeout bounds and process counts remain
unchanged. The supplied acceptance is preserved; no native gameplay rerun is
needed for these label/console/metadata changes.

All **28** runner contracts, Python syntax, the **239-document** README tree and
whitespace checks pass. Known runtime and source/generator failures remain open.
Prior staged/unstaged work and the user's customized ordinary/full launch labels
are preserved. Nothing is staged, committed or pushed in this continuation.
