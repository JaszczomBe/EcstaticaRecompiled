# Automated gameplay regression suite — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Usage: [Gameplay regression suite](../../gameplay-tests.md).

The user requests end-to-end regression protection for recovered movement,
traversal, weapons, enemies, damage, potions, doors and menus, including their
dependencies and a VS Code launch that runs all current cases. This continuation
adds test tooling and assertions; reconstructed runtime/generator repairs from
the prior crash investigation remain staged and untouched.

## Implementation

- `scripts/run-e2-suite.py` supplies the CLI and configuration/data discovery.
- `scripts/e2_suite.py` owns the catalogue, dependency graph, root blockers,
  independent checks, time bounds, child cleanup and incremental reports.
- `scripts/e2_gameplay_steps.py` supplies shared input-only journeys through the
  existing motion probe; no actor state, RNG or camera assignment is used.
- `scripts/check-e2-generation-parity.py` compares four scratch-generated
  artifacts without overwriting current C, retaining differences on failure.
- `scripts/check-e2-suite.py` verifies eleven runner/lifecycle/report contracts.
- `.vscode/launch.json` adds **Ecstatica: Full regression suite**, using the
  installed `node-terminal` launch capability to run both configured SDL builds.
  The original ordinary gameplay launch stays first and unchanged.

The full catalogue has **80** cases across source/tooling and Debug/ASan.
Every live scenario starts a new process and traverses its own route. Passing
another case never supplies a shared saved state. Prerequisites govern scheduling
and explain blocked actions; independent original-code comparisons continue.
The courtyard return gate is deliberately separate from the outward workshop
route, so its known floor-return limit does not suppress unrelated interaction
coverage.

All successful journeys finish via Escape, cancellation, actual movement after
resuming, reopened Quit and Yes, followed by native exit zero and completed
inspection. The observer retains ordered phases, SDL input changes, game state
and eight rolling frames in a per-case data directory. Recording is off because
the existing debugger-driven probe's additional input pumps are not claimed to
be portable replay scheduling. Independent complete replay corpora use the
existing strict scenario evaluator; absent corpora are explicit optional skips.

Four bounded potion trials sample live RNG without assigning it. Two require
natural damage. Separate coverage gates distinguish healing from below maximum,
poison onset, invisibility onset and conditional no-op. Missing random branches
are required skips; failed trials block branch acceptance. Final effect
expiry/cure and armed swimming/shore exit remain optional skips.

The input schedule and swimming waypoints are now repository resources, with
provenance from the potion journal and materialized human water-session
inspection. No `.tmp` or `/tmp` recording is required to run the catalogue.
The original game data stays external.

## Verification and limits

Eleven runner contracts pass without game data: dependency order/cycles, transitive
filters, independent failure continuation, root blockers, required/optional skip
semantics, interrupted report preservation, process-tree timeout cleanup,
sanitizer diagnostics, random coverage qualification, JUnit and launch entries.
The installed VS Code debugger schema confirms the launch's command/cwd fields.
Documentation tree, Python syntax and whitespace checks pass.

The initial native full run is
`.tmp/gameplay-suite/acceptance-20261024/`, with detailed console output in
`/tmp/e2-suite-acceptance.log`. Focused runner development checks are under
`.tmp/e2-suite-development/`. The suite was refined while this first integration
run progressed; focused subsequent checks verify the final changed assertions.
Per-case results and logs preserve what actually ran.

Debug has already verified normal/early/delayed startup, input and release,
workshop traversal, sword pickup/following, all four attack directions, an actual
smith kill, door collapse/passage and water entry/swimming. These are automated
journey outcomes, not a blanket acceptance of the full game.

The preserved animation-name regression is detected independently by generation
parity, original animation-slot comparison and actual potion bottle cleanup.
Its C hunk is not overwritten. The known courtyard return/floor limit is also
reported rather than relaxed. The first historical damage-input attempt did not
produce damage; it is retained as failed route qualification, with dependent
healing trials blocked. A bounded read-only live-guard approach supplements that
historical input path in the final damage journey.

An initial menu resumption assertion attempted only Down while Joe stood at the
pedestal; geometry could legitimately block it. The final assertion tries both
travel directions before declaring lost control. This corrects test routing,
without changing game behavior or accepting a mere input latch as movement.

## Native results and new failure boundary

The initial full **80-case** integration run completes in **1,074.60 seconds**:
**43 PASS / 10 FAIL / 21 BLOCKED / 6 SKIPPED**, exit **1**. This is an honest red
baseline, including the preserved source/name regression and prototype route
assertions subsequently refined. Its immutable per-case results are not rewritten
to reflect later tests.

Focused final checks are separate:

| Run under `.tmp/e2-suite-development/` | Observed result |
| --- | --- |
| `damage-and-menu-final` | **5/5 pass**: pinned build identity, startup, movement, real enemy damage **100→95**, menus/resumed movement and clean exit |
| `pinned-startup-final` | **4/4 pass** across Debug/ASan, executing the pinned copies, checking native exit zero and completed inspection |
| `asan-interactions-final` | **8 pass / 1 fail**: startup, movement, workshop, sword, four attacks, actual smith death and door collapse/passage pass; a new native failure interrupts the separate mixed journey |
| `damaged-potions-final` | Prerequisite damage case passes, but both independent fresh trials fail to receive a hit; the final classifier treats such repeated setup failures as **BLOCKED action / failed prerequisite phase**, not potion-effect regressions |
| `tool-contracts-cli` | Runner/tool contracts pass through the CLI without installed game data |

The successful Debug mixed journey includes its active input phase and the
**60-second** released observation, then menu exit. Swimming passes in Debug and
ASan. Natural-damage routing is not deterministic across fresh processes: even
when its independent smoke test passes, another trial may not receive a hit.
The final runner retains that phase failure and blocks the unexercised target
instead of silently retrying until a branch passes. Eleven contracts verify
these distinctions, including that a native crash is always a failure rather
than being downgraded to a blocked action.

The final ASan mixed-journey attempt exposes **SIGSEGV** in:

`FUN_0042f85c ← FUN_0042b880 ← FUN_0042b338 ← FUN_0042ae80 ← FUN_00427584 ← FUN_0042a70c`.

The stopped leaf is reconstructed C line **26638**, arguments **11282640** and
**8881612**. This happens during the new process's `traversal.workshop` phase,
after **104** completed probe updates, before its stress phase. It is not the
previous alternate-target crash and is not established as an ASan memory-error
report. The actual SIGSEGV, thread stacks, registers, partial inputs, state and
rolling frames are retained under
`.tmp/e2-suite-development/asan-interactions-final/asan.Stability.MixedJourney/`.
Its matching executable is `asan-interactions-final/asan.Build/e2recomp`, SHA-256
**12963beaee167b1cfabbdd1a35db98137cbfee1f566512685a3c759a9079ea6c**.
Recording is off; no complete replay or deterministic fresh reproduction is
claimed. Source-backed recovery of this new event contract is separate work.

The guide and owning task record the remaining original-code and coverage limits.
Aggregate validation pointers are `.tmp/e2-suite-development/validation.json`.
No runtime/generator hunk is overwritten; no stage, commit or push is performed.
