# Gameplay regression suite

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

Run the recovered gameplay journeys in dependency order with the VS Code launch
**Ecstatica: Full regression suite**. Its picker selects **headless** (default)
or **visible** gameplay. It builds the configured SDL Debug and ASan presets,
runs every registered case, and prints GoogleTest-style results in its terminal.
**Ecstatica: Full regression suite — visible SDL** starts the visible full run
directly. The ordinary **Ecstatica Recompiled** gameplay launch is unchanged.
The suite uses the terminal debugger supplied by VS Code; it does not require
the Python debugging extension.

From the repository root:

```sh
python3 scripts/run-e2-suite.py --build --configurations debug asan
python3 scripts/run-e2-suite.py --list
python3 scripts/run-e2-suite.py --configurations debug --filter 'debug.Interaction.DoorPassage'
python3 scripts/run-e2-suite.py --build --block unarmed --display visible
python3 scripts/run-e2-suite.py --block potions --list
```

Filters include prerequisites automatically. Original assets remain external;
`--game-data /path/to/Ecstatica2` overrides the installation from the SDL Debug
CMake cache. Both SDL presets must already be configured for `--build`.
The full suite can take many minutes. Each journey and original-code comparison
has a host timeout; gameplay also has bounded waypoint attempts and update counts.

## Blocks and visible gameplay

Each block below has its own **Ecstatica suite:** launch entry and the same
headless/visible picker. All launches run sequentially, including Debug and ASan.
Selecting a block includes its transitive prerequisites automatically; each
included prerequisite appears in the report. There is no dependency bypass or
reuse of another scenario's live game state. CLI `--filter` narrows targets
within the selected block before prerequisites are added.

| CLI `--block` | Target scenarios |
| --- | --- |
| `full` | All registered cases |
| `checks` | Generation, runner contracts, original-code fixtures and host retention-worker faults |
| `startup` | Early skip, delayed skip and natural intro |
| `movement` | Movement/release and courtyard return |
| `unarmed` | Basic/advanced unarmed attacks, real unarmed enemy contact and natural player damage |
| `workshop` | Workshop traversal, sword pickup, sword attacks, smith kill and door passage |
| `potions` | Consumption trials, branch coverage and potion-to-sword sequence |
| `swimming` | Water traversal/swimming and explicit unfinished armed-water coverage |
| `menus` | Cancel, resume movement and confirmed Quit |
| `stability` | Mixed gameplay journey and released observation |
| `replay` | Supplied complete replay corpus, or explicit optional skips |

Visible journeys open one real SDL window at a time and close it through the
tested menu exit. After startup release, its title identifies the case and phase.
Host pacing limits scripted updates to 60 per second in batches of at most three;
menus pause briefly for observation. Watch mode has a threefold host timeout
allowance and retains the same update bounds and assertions. It changes no game
clock, RNG or actor state, but fresh timing/outcomes can differ from headless runs.
Inputs remain automated; desktop input can interfere with the route.

Visible mode chooses Wayland when `WAYLAND_DISPLAY` is present, otherwise X11
with `DISPLAY`. Use `--video-driver x11` or `wayland` to select explicitly.
Missing desktop configuration is an error rather than a silent headless run.
Headless mode uses SDL's `dummy` driver. Original-code/host checks have no gameplay
window. Corpus replays retain their recorded display environment and strict
service/checkpoint checks; the watch option applies to fresh input journeys.
Report metadata records the block, display driver and worker count (**1**).

## Results and evidence

Console output distinguishes:

| Status | Meaning |
| --- | --- |
| `PASS` | The selected case completed its assertions; gameplay cases also quit normally through the menu and finish inspection |
| `FAIL` | A command, route phase, outcome assertion, sanitizer check or timeout failed |
| `BLOCKED` | A prerequisite failed or was not exercised; the case is not counted as a passing test |
| `SKIPPED` | Explicitly unfinished coverage, absent optional replay corpus, or a required random branch not sampled |

Failures block only declared prerequisites. For example a failed movement check
blocks dependent traversal, while menu startup and original-code comparisons
continue. A courtyard **return** failure does not block the workshop's separate
outward journey. A fresh prerequisite can also fail inside a later journey after its separate
smoke test passed. The action is then `BLOCKED`, with the failed phase retained
as its root cause. Native signals and sanitizer diagnostics remain `FAIL` even
when they interrupt setup. Each journey starts a fresh process and repeats its own traversal;
there is no shared game session or save-state teleport between cases.

Exit **0** means all required selected cases passed. Exit **1** means a failure
or blocked case; **2** means required coverage was skipped; **130** means the
suite was interrupted. Known unfinished optional cases can be skipped without
making an otherwise successful run fail. Skipped cases are always listed.

Default evidence is `.tmp/gameplay-suite/run_<UTC timestamp>/`; `latest.json`
points to the last default run. `--output PATH` requires a new destination and
never replaces an older run. Each completed case refreshes:

- `report.html`: status table, reasons and links to command logs.
- `report.json`: dependencies, root blockers, phases, observations, binary
  identity, timings and overall exit status.
- `report.xml`: JUnit format; blocked cases use `<skipped type="blocked">` and
  retain a separate `status=BLOCKED` property.

Each configuration pins its executable and SHA-256 before gameplay and executes
that copy, verifying its identity before each journey/replay. Commands,
console/GDB output, input transitions and ordered journey phases are retained
per case. Native inspection stores state and the last eight game frames in an
isolated runtime directory. Failure phases retain stacks/registers when GDB is
stopped. Timeout/interruption stops the child process tree and preserves partial
results. No session output uses the normal human log-retention directory.

Recording is explicitly **off** for these input-driven probes. The existing
probe pumps SDL input under GDB; its call scheduling is not claimed to be a
portable exact replay. Instead, the suite retains its input/phase journal and
inspection, and supports independent complete-recording scenarios below.

## Registered gameplay

The catalogue in `scripts/e2_suite.py` owns ordering and dependencies;
`scripts/e2_gameplay_steps.py` owns shared input-only journey steps. New tests
reuse those steps without assigning actor positions, actions, health, RNG,
attachments, camera or clocks.

| Journey | Assertions |
| --- | --- |
| Early skip, delayed skip, natural intro | Healthy Joe released at courtyard camera/floor; no restart or actor substitution |
| Movement and release | Both turn directions, modifier release, forward/backward displacement and settled released input |
| Courtyard | Outward crossing, return camera and expected floor |
| Workshop | Traverse the human-recorded route and identify sword 3717, potion 537 and door 980 |
| Sword | Real Space pickup, reciprocal attachment, equipped movement and following world position |
| Four attacks | Each Ctrl/arrow direction starts its original slot group and releases |
| Unarmed attacks | Without a sword, all four basic Ctrl/arrow and advanced Ctrl/Alt/arrow groups become live actions; modifiers release and movement resumes |
| Unarmed contact | Traverse to smith 602 without sword pickup and observe actual enemy health loss from unarmed strikes |
| Smith kill | Actual target health loss, death and representation removal for actor 602 |
| Player damage | Human-derived SDL input route causes real health loss without changing health directly |
| Door | Actual repeated damage, collapse/deactivation of door 980 and movement through its opening |
| Potion trials | Actual branch, drinking, removal and original action/timer/health effects |
| Potion then sword | Bottle remains removed after sword attachment and all four attacks |
| Swimming | Traverse sampled human route to camera 543; swimming representation plus displacement |
| Menus | Escape, cancel, actual resumed movement, reopened Quit and Yes, native exit zero |
| Mixed stability | Workshop, sword, attacks, door passage, repeated movement and bounded released observation before menu exit |

Every successful journey includes the menu exit check. This does not make one
case's state a prerequisite for the next. The registry also runs scratch
generation parity and focused actor/animation/script-name, key release, attack,
pickup, attachment, timer, cache, script-flow and water-identity comparisons.
Failures in those isolated comparisons remain independently visible.

Waypoint coordinates and the natural-damage keyboard schedule have journal
provenance in `scripts/scenarios/`. They guide bounded SDL input; they are never
written to game state. Fresh Debug/ASan timing and RNG can produce different
paths or encounter outcomes. A route failure is retained, rather than retried
until green.

## Random outcomes and unfinished work

Four fresh potion trials use bounded waits **0, 37, 83, 221** updates. Two first
require real damage. Trials validate whichever original branch is observed;
coverage cases separately require healing from below maximum health, poison
onset, invisibility onset and an unafflicted conditional no-op. Missing branches
are reported as required **SKIPPED** coverage, not invented or forced by RNG
writes. A failed consumption trial blocks branch acceptance. Full-health healing
dispatch alone does not satisfy the healing coverage case.

Poison death, invisibility expiry/cure, armed swimming and shore exit remain
explicit optional skips until their original behavior and routes are accepted.
The mixed journey is a bounded stress check, not proof that the entire game is
stable or that every resource-cache eviction has been reached.

## Complete replay corpus

Complete captures can supplement fresh journeys. Supply `--replay-corpus PATH`
with a local JSON manifest:

```json
{
  "schema": "e2suite.recordings.1",
  "recordings": [
    {
      "source": "/absolute/exported-bundle/session/replay",
      "specification": "/absolute/ordered-route-expectations.json"
    }
  ]
}
```

Relative paths resolve beside the manifest. Specifications use the existing
`e2debug.scenario.1` format from the [replay guide](replay.md). Explicit compatible
mode permits changed executable identity while retaining strict service and
checkpoint checks. A replay passes only with native exit zero, completed
inspection and all scenario assertions. Divergence, timeout, crashes and incomplete
prefix exhaustion fail. Historical crash prefixes cannot masquerade as completed
end-to-end scenarios. Keep recordings immutable and review baseline changes.

## Maintaining the suite

Add a `Case` with a stable name, real prerequisites, bound and observable
assertions. `observes` schedules coverage evidence without requiring every trial
to pass before the evaluator can report its actual coverage. Avoid requiring an
unrelated return journey for a test that only needs an outward route.

```sh
python3 scripts/check-e2-suite.py
python3 scripts/check-docs-tree.py
```

The fifteen runner contracts cover topological ordering, transitive filters, independent
failures, root blockers, missing random coverage, interrupted reports, timeout
cleanup, sanitizer failures, JUnit output, block prerequisite inclusion, desktop
selection, visible command forwarding and launch/picker configuration. The native
`Host.SessionMaintenance` cases inject repeated allocation failure and a throwing
reporter into the real cleanup worker, then verify recovery and clean shutdown.
Current runtime results belong to the [active gameplay task](implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
and its linked journal, rather than a permanently green claim in this guide.
