# Menu stages and concurrent regression configurations — 2026-10-25

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Usage: [Gameplay regression suite](../../gameplay-tests.md).
Previous execution work: [Shared checkpoint journeys](shared-gameplay-journeys-2026-10-24.md).

The user authorizes concurrent Debug/ASan execution, superseding the previous
parallelism deferral, and requests menu coverage at horseback intro, pedestal
intro and released gameplay. Unimplemented options and persistence must remain
visible as skipped coverage. Existing staged/unstaged work is preserved; no
runtime C/generator repair, staging, commit or push is made.

## Execution and reporting

`e2_suite_parallel.py` runs two configuration workers by default, sequential
journeys within each worker, and global source/tool checks once before those
workers. All child commands use explicit argv, separate evidence directories
and pinned executables. The parent alone merges incremental HTML/JSON/JUnit
reports. Relative evidence links are prefixed with their configuration directory;
`lanes` records worker start/end times and exits. Worker crashes recover completed
checkpoint assertions from atomic journals and fail overall; the other build
continues. SIGINT signals both workers, retains available reports and stops the
descendant process trees. Coordinator/spawn errors also produce a final failure.

The picker offers `headless`, `visible-debug`, `visible-asan`, `visible-both`.
Showing one configuration keeps the other headless. CLI `visible` aliases both;
`--workers 1` restores sequential configuration execution. Suite **01** bypasses
the picker without changing its name. The user's decorated ordinary-game and
full-suite labels/order remain intact; there is one full-suite entry, first
among regressions, and numbered blocks **01–10**.

The catalogue expands **86 → 182** logical cases. Full selection plans **20**
shared gameplay processes versus **96** isolated. Menu block **03** plans **102**
logical results in **two** processes versus **58** isolated. Selection remains
explicit; walking through a prerequisite never credits its assertions. Existing
startup variants, water routes and fresh potion trials remain distinct. When
menus and other gameplay are selected together, ordinary gameplay owns the
delayed-startup assertion it needs, so an independent intro-menu failure cannot
block movement by withholding startup evidence. Menu-only selection still shares
its delayed-startup prerequisite in the menu process. A contract verifies that
failed menu checks leave independently exercised startup/movement passes intact.

## Menu assertions

`e2_menu_steps.py` implements one bounded SDL-input journey through all three
stages. It observes game memory without assigning actor/camera/options/RNG/time
state. Menus use actual SDL Escape, live item hit rectangles and SDL mouse input;
skips use actual Space. Recording is **off**, with input/checkpoint journals and
isolated inspection. No exact replay acceptance is claimed.

Each stage has ShowHide, Settings, MusicToggle, SoundToggle, Difficulty,
ResolutionToggle, LoadDialog, SaveDialog and StartGame results. ShowHide exercises
Escape cancellation, the Cancel button and Quit → No, checking stage/identity.
Controls require flag changes and corresponding displayed label changes, then
cycle back through input. Gameplay Save is a standalone requester; its cancellation
resumes gameplay, while Load returns to the parent menu. Intro Save must remain
disabled. These assertions do not credit functional save/load or audible output.

StartGame must return to initial horseback camera/action, reset progress and
initial identity/health. Horseback progress advances before its restart check.
The final route orders restarts at their source stages. Pedestal traversal after
a successful restart uses the same observed opening action and delayed Space
at progress **83** or later; released-startup acceptance requires healthy Joe,
state **4**, courtyard camera **175** and floor **3328**. The final native Quit
is required for `Menus.CancelResumeQuit` and for successful journey lifecycle.

MusicPlayback, SoundPlayback, ResolutionRendering, LoadState, SaveState,
Subtitles and FemaleStartGame are explicit optional skips at each stage, with
reasons tied to missing implementation/acceptance. ResolutionToggle observes the
control but skips behavior acceptance. Control/dialog checks and their effects
are separately reported; none of these skips can become an inferred PASS.

Independent UI failures remain FAIL even when cleanup succeeds. Cleanup is real
input returning observed option values, closing dialogs and verifying the live
player/stage. It never retries an assertion. Unexpected native stops/signals
cannot use that recovery. Nested setup failures block their unexercised target;
separate exercised failures retain separate FAIL results. Isolated menu diagnosis
also keeps checkpoint and lifecycle results separate.

## Native acceptance and failures

Evidence root: `.tmp/menu-matrix-development/`; `validation.json` indexes reports,
source identities, worker overlap, binary pins, inspections and exported bundles.
Runs use existing Debug/ASan binaries, not regenerated/rebuilt runtime sources.

| Selection / directory | Logical results | Processes | Wall time |
| --- | --- | --- | --- |
| User's former visible menus, `.tmp/gameplay-suite/run_20261025_134757_704135/` | 6 PASS | 2 sequential | 53.04 s |
| `parallel-visible-debug/`, same six logical checks | 6 PASS | 2 concurrent | 26.19 s |
| `show-hide-three-stages/`, first Debug stage probe | 4 PASS | 1 | 20.16 s |
| `matrix-visible-both/`, expanded menus | 17 PASS / 14 FAIL / 25 BLOCKED / 46 SKIPPED | 2 concurrent visible | 54.28 s |
| `intro-restarts/`, both intro restart paths in each build | 4 PASS / 2 FAIL | 2 concurrent | 5.22 s |
| `three-stages-final/`, delayed startup, three-stage show/hide, explicit resolution skips and gameplay cancel/resume/Quit | 12 PASS / 6 SKIPPED | 2 concurrent headless | 24.98 s |

The six-case timing comparison removes **50.6%** of observed wall time with
unchanged logical assertions. The new run shows Debug while ASan is headless;
the user's baseline showed both sequentially. This is a measured selection,
not an assertion that every full run halves its duration. Each still executes
one independent process per build. Both-window mode is exercised by the expanded
run, and worker timestamps prove overlap. Final three-stage runs observe delayed
skip progress **83**, native exit **0** and complete inspection in both builds.

The first `settings-dialogs/` probe retained Intro.Settings PASS, music-label
FAIL and blocked subsequent checks. A changed route subsequently adds independent
cleanup/continuation; it retains all observed label failures, without retrying
until green. `matrix-visible-both/` records:

- Debug ShowHide, Settings, Load and Save-dialog checks pass at all three stages;
  the delayed startup also passes. Music/sound/difficulty flags change, but their
  displayed item labels do not; all **nine** checks remain FAIL. Reconstruction
  inspection shows helpers updating named globals while item text is held in
  fixed requester records. This is evidence for investigation, not a runtime fix.
- Debug gameplay Start Game receives **SIGSEGV** in `FUN_0043a39c`, reconstructed
  line **31219**, indexed write through Joe's identity into `0x0064a178`.
  Pinned executable SHA-256:
  `9818189b760d86c861cf46e4c16706125bca9806246fbd2f5bacd69de5d5aef9`.
- ASan opening Load during horseback intro reports **stack-buffer-overflow** in
  `FUN_0043ce58`, line **33786**, writing past local `acStack_50` (declared at
  **33699**), called from `E2R_InvokeRequesterAction` line **1844**. Earlier
  ShowHide/Settings passes and three option-label failures remain; later checks
  are blocked. Pinned SHA-256:
  `16fdb6ed823b2f68da57a0bf8ea9d65b689cc716e669a6ad661a80424ea1a5be`.

Both inactive sessions and pinned binaries are exported and integrity-verified
as `gameplay-start-bundle/` and `asan-load-bundle/`; matching `*-extra/` directories
retain probe logs, checkpoint journals, commands and reports. Recording is off;
these exports preserve evidence and do not establish deterministic replay.

The development expanded route deferred restart checks until after ordinary
stage controls. Gameplay Start Game then prevented both earlier intro restart
assertions. The final route places each restart at its source stage; isolated
`intro-restarts/` supplies new coverage rather than repeating those crashes.
Horseback restart passes in both builds. Pedestal restart fails to return to
initial horseback in both, matching the current helper resetting only the active
intro action. Those failures remain FAIL despite clean Quit/native exit **0**
and complete inspection. The final focused stage run omits known destructive
faults and validates the finished route's skip/report/exit machinery. A complete
final-order menu block is not claimed accepted; the failing runtime paths are
not rerun unchanged until green.

## Validation and limits

**40** runner contracts pass, including real child-process overlap, one-time
source selection, configuration-local prerequisites, full child catalogue
selection, partial checkpoint recovery after worker death, interruption cleanup,
spawn failure, merged links and HTML/JSON/JUnit, display mapping, three-stage
declarations, explicit unfinished effects, independent failure/skip propagation,
isolated lifecycle handling and stopped-thread/ASan leaf identification.

The **240-document** README tree passes both update and read-only checks;
`git diff --check` also passes.
The complete **182-case** suite is not rerun. Original animation-name drift and
its source/generator/fixture failures remain untouched. Earlier allocation
pressure, courtyard-return/bottle issues, natural damage variability and the
separate `FUN_0042f85c` event fault remain open. Audio, rendered resolution and
functional persistence still have no acceptance. New runtime repairs require
original-code evidence and generator mirrors in a separate continuation.
