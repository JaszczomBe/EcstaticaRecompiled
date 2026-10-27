# Sequential invisible regression sweep handoff — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Implementation owner: [Playable SDL runtime](../../implementations/playable-sdl-runtime/playable-sdl-runtime.md).
Runtime repairs: [Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Test navigation: [Task 10](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Commands and coverage: [Gameplay regression suite](../../gameplay-tests.md).

## User authorization and next action

The user requests a handoff for the next context to test all regressions one by
one, fix failures accordingly, and use invisible SDL throughout. Continue that
work without another general confirmation. Run numbered **Regression 01–10** in
order, one block at a time. Inspect every selected logical result within each
block; use exact case filters to isolate and repair failures. Run Debug then ASan
sequentially with **`--workers 1`**. Do not launch concurrent blocks or visible
windows. Shared journeys retain their real prerequisite checkpoints.

This handoff-writing turn changes documentation only. The block inventories
below were checked using `--list`; no new regression execution or repair is
claimed here. The next action is Regression **01**, not another potion-only run.

Start at [README](../../../README.md), then read [capabilities](../../capabilities.md),
[working rules](../../HANDOFF.md), the owning implementation/tasks and the latest
[receive-hit evidence](receive-hit-contact-navigation-2026-10-26.md). Inspect
`git status --short` before editing. The worktree contains substantial staged,
unstaged and untracked implementation work, including the navigator modules and
current journals. Preserve all of it. Do not stage, commit, push or reset files
as part of this sweep unless the user requests that separately.

## Invisible SDL and execution commands

Use **`--display headless`**. `e2_suite.display_driver()` maps this to SDL's
**`dummy`** video driver; this is the requested null/invisible mode. The game
still runs recovered gameplay, input, presentation and inspection. There is no
`--display null` option, and the suite's `--video-driver` argument only selects
desktop drivers for visible runs. No desktop display or F5 window is needed.
Keep the ordinary human F5 configuration unchanged.

From `/home/rgrabowski/Work/EcstaticaRecompiled`:

```sh
python3 scripts/run-e2-suite.py --build --configurations debug asan --workers 1 --execution shared --block checks --display headless --list
python3 scripts/run-e2-suite.py --build --configurations debug asan --workers 1 --execution shared --block checks --display headless --output .tmp/headless-regression-sweep/01-checks-initial
```

For each next block, substitute its name and use a **new** output directory for
every attempt. Review the completed result before starting the next command.
Do not use a blind loop that continues past failures or overwrites evidence.
Original assets normally resolve from the configured CMake cache; if needed add
`--game-data /home/rgrabowski/Games/Ecstatica2`.

For a failing logical case, use its exact catalogue name, for example:

```sh
python3 scripts/run-e2-suite.py --build --configurations asan --workers 1 --execution shared --block potions --filter asan.Potion.TrialD --display headless --output .tmp/headless-regression-sweep/08-trial-d-investigation-01
```

Prerequisites are intentionally included. `--execution isolated` is available
for a fresh-process diagnosis; retain shared execution for block and final
qualification so lifecycle/checkpoint problems stay visible. Agent probes keep
recording **off**, with bounded real SDL input and inspection in their own output
directories. Do not route them into normal human session retention.

## Order and coverage inventory

Counts include automatically selected prerequisites, both configurations and
optional entries. They are inventory, not passing evidence. The source catalogue
and `--list` are authoritative if repairs add cases.

| Regression | `--block` | Logical cases | Gameplay processes | Focus |
| --- | --- | ---: | ---: | --- |
| 01 | `checks` | 31 | 0 | Source/generator, tools, original-code fixtures and host checks |
| 02 | `startup` | 8 | 6 | Early/delayed skip and natural intro |
| 03 | `menus` | 102 | 2 | Horseback, pedestal and gameplay menu matrix |
| 04 | `movement` | 8 | 2 | Controls, release and courtyard round trip |
| 05 | `unarmed` | 14 | 4 | Unarmed actions, actual smith contact and receive damage |
| 06 | `workshop` | 16 | 2 | Traversal, sword, combat, kill and door passage |
| 07 | `swimming` | 24 | 4 | Unarmed/armed water entry, combat and traversal |
| 08 | `potions` | 32 | 10 | Natural consumption/effects and potion-to-sword |
| 09 | `stability` | 16 | 2 | Mixed gameplay and released observation |
| 10 | `replay` | 2 | 0 without corpus | Complete recordings, when available |

The current complete catalogue is **195 logical cases / 22 shared gameplay
processes**. Block counts overlap through prerequisites. List each block before
running it. For Regression 10, inspect existing complete recording manifests;
pass a suitable manifest with `--replay-corpus` when available. Never invent a
complete recording, rewrite its binary identity or treat incomplete capture as
accepted exact replay. If none is available, retain the explicit optional skips
and record that replay coverage remains unqualified.

## Repair and qualification workflow

1. Run the current block headlessly and read its exit status, `report.json`,
   journey lifecycle results and failed phases. Record the actual root failure;
   zero logical FAIL results can still conceal a failed journey and BLOCKED checks.
2. Inspect the failing execution's `console.log`, `probe.log`,
   `probe-journey.json`, navigation/input streams, pinned executable and inspection.
   Use `probe-stopped.json`/`probe-stall.json` for signals, allocation exceptions
   or watchdog interruptions. The watchdog interrupts after **30 seconds** without
   debugger/inspection progress and allows **five seconds** for capture before
   process-tree cleanup. Distinguish this intentional SIGINT from a native fault.
3. Diagnose the narrow boundary: original runtime behavior, test navigation,
   observer/assertion error, or missing setup. Use original disassembly/Ghidra and
   bounded original-code comparisons for runtime repairs. Mirror reconstructed C
   changes in `E2Recomp/tools/GenerateRecon.js`, regenerate, verify exact scoped
   parity and run the affected normal/ASan fixtures and SDL builds.
4. For driver repairs, reuse `e2_navigation.py`, live scene-floor planning in
   `e2_scene_navigation.py` and the shared gameplay steps. Preserve assertions and
   real input. Never assign player/actor position, health, RNG, action, attachment,
   camera or clocks to manufacture success. Do not fix a navigation failure by
   weakening the required combat, pickup, water or passage assertion.
5. Run meaningful targeted contracts/probes for the repair, then requalify the
   affected block in both configurations with invisible SDL. Keep failed attempts.
   Do not repeat unchanged scenarios until lucky. Freeze relevant sources while
   a qualification run is active and verify recorded source/binary hashes afterward.
6. Recheck earlier blocks when a shared helper or runtime change affects their
   accepted paths. Move to the next numbered block after addressing current
   failures. If missing external input genuinely prevents a check, record that
   boundary and continue independent blocks; never relabel required BLOCKED work
   as a harmless optional skip.

Retain a progress table in the owning implementation/journal with each block's
latest report path, Debug/ASan status, failure cause, repair, validation and limits.
Do not infer new acceptance from historical rows. Add a meaningful fixture or
contract where it protects the repaired behavior; avoid tests that merely mirror
the implementation or broad repeated testing without a reason.

After all numbered blocks, run the integrated full suite on final sources:

```sh
python3 scripts/run-e2-suite.py --build --configurations debug asan --workers 1 --execution shared --block full --display headless --output .tmp/headless-regression-sweep/full-final
```

Include `--replay-corpus` here too if a corpus was qualified. If this final sweep
exposes an integration failure, repair and validate it before claiming completion.
Require native menu exit zero and completed inspection for accepted gameplay
journeys, alongside checkpoint assertions. Report any remaining optional coverage
gaps explicitly. Update the owning task/implementation and journal; run
`python3 scripts/check-docs-tree.py --update`, then the read-only check and
`git diff --check`.

## Starting evidence and constraints

The latest [receive-hit continuation](receive-hit-contact-navigation-2026-10-26.md)
owns exact hashes and all retained attempts under
`.tmp/regression08-contact-20261026/`:

- `final-potions/report.html`: **26 PASS / 6 optional SKIPPED**, all **22 required**
  checks, **317.58 s**, visible Debug plus headless ASan.
- `final-damage/report.html`: **8/8 PASS**, **57.01 s**, the same display split;
  Debug actually traverses a live scene-planned join after displaced movement.
- `validation.json`: twelve native menu exits, completed inspections, original
  melee attribution, pinned binary identity and all **21** recorded test-source
  hashes matched. Contracts: **61 suite + 38 navigation = 99 PASS**.

This is partial baseline evidence. **The complete suite and the latest full
headless Debug potion block have not been qualified by those selections.** Start
the requested new sweep at 01 and test 08 again in headless mode.

Preserve these recovered/tested behaviors:

- Receive-hit aligns in front of an opponent using observed heading/radius and
  requires surviving health loss attributed to original melee. Audited guards
  **284/293** are eligible only with valid identity, active state, attack slots and
  compatible height. Unavailable targets can be reselected within the shared
  replan budget; replaced instances fail. Fixed smith/sword/door goals cannot
  silently switch targets. Native final evidence currently hits **284** only;
  293 selection/reselection has contract/asset evidence, not a native 293 hit claim.
- Courtyard encounter joining prefers observed height and uses the live scene
  planner beyond the **1800-unit** local bound. Workshop joining has its separate
  **4000-unit** fallback. Use the established helpers rather than extending old
  recorded input schedules. Navigation has finite update/replan/host limits.
- Swimming now plans from live scene floors. Exercise **both combat and traversal**,
  unarmed and sword-equipped. Do not restore the archived human water route or
  drop assertions to entry alone. See the [water evidence](water-goals-and-scene-navigation-2026-10-26.md).
- Potion type is naturally randomized. Required checks accept the observed
  consumption and actual effect, including full-health healing and valid no-op;
  drinking, attachment/removal and selected branch assertions remain required.
  Branch summaries are optional. Do not require a healing draw or inject a type.
- Noncombat journeys use the audited noncombat-opening fixture; actual combat,
  damage and potion trials retain live population. Do not suppress their opponent,
  grant invulnerability or alter normal human gameplay to make a test pass.

Known open areas are the menu label/restart behaviors and ASan Load overflow,
shore exit and water-enemy damage, final potion death/expiry/cure, broader route/AI
variability and extended stability. Investigate current failures rather than
assuming those historical boundaries still fail in precisely the same way.
Optional entries must stay distinguishable from unperformed required work.

The [earlier freeze investigation](regression-08-freeze-and-event-callback-2026-10-26.md)
repairs a separately captured original event-7 node callback (`FUN_0042f85c`) and
verifies generated parity. The original screenshot freeze is still unconfirmed;
the user explicitly stopped that frozen run, so its later SIGKILL is not evidence
of an OOM kill or proof of that callback as the freeze's cause. Preserve this limit.

Primary code is `scripts/e2_suite.py` (catalogue/dependencies/reporting),
`run-e2-suite.py`/`e2_suite_parallel.py` (execution), `e2_gameplay_steps.py`
(objectives), `e2_navigation.py`/`e2_scene_navigation.py` (input guidance),
`probe-e2-player-motion.py`/`e2_probe_diagnostics.py` (native probes), and the
existing `check-e2-*.py` original-code/contract fixtures. Do not edit the durable
`docs/HANDOFF.md` anchor just to record this changing sweep status.
