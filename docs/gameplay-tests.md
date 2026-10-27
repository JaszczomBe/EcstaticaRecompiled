# Gameplay regression suite

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

Run the recovered gameplay checkpoints in shared, dependency-ordered journeys with the VS Code launch
**starred full regression suite**. Its picker selects **headless** (default),
**visible-debug**, **visible-asan** or **visible-both** gameplay. It builds the configured SDL Debug and ASan presets,
covers every registered logical case, and prints GoogleTest-style results in its terminal.
The ordinary **Ecstatica Recompiled** gameplay launch retains live population.
The suite uses the terminal debugger supplied by VS Code; it does not require
the Python debugging extension.

From the repository root:

```sh
python3 scripts/run-e2-suite.py --build --configurations debug asan
python3 scripts/run-e2-suite.py --list
python3 scripts/run-e2-suite.py --configurations debug --filter 'debug.Interaction.DoorPassage'
python3 scripts/run-e2-suite.py --build --block unarmed --display visible
python3 scripts/run-e2-suite.py --block menus --display visible-debug
python3 scripts/run-e2-suite.py --block startup --display visible-both --workers 1
python3 scripts/run-e2-suite.py --block potions --list
python3 scripts/run-e2-suite.py --configurations debug --block workshop --execution isolated
```

Filters include prerequisites automatically. Original assets remain external;
`--game-data /path/to/Ecstatica2` overrides the installation from the SDL Debug
CMake cache. Both SDL presets must already be configured for `--build`.
The full suite can take many minutes. Each journey and original-code comparison
has a host timeout; gameplay also has bounded waypoint attempts and update counts.

## Controlled population and startup logos

Noncombat journeys use the explicit **noncombat-opening** test fixture. It
prevents original scripted guards **284/293** and workshop enemy **602** from
being created and bypasses terrain-generated spawns. It does not freeze existing
actors, disable collision, grant invulnerability or restore player state. Joe,
props, doors and pickups retain their ordinary loading/update paths. The manifest
uses original archive identities: the collision flag also covers doors/stocks,
and diagnostic marker labels are not an enemy classification.

Movement, courtyard return, action-only unarmed/sword checks, pickup, swimming
and menu journeys select this fixture. Startup-only, enemy contact/kill, natural
player damage, potion trials, door combat and stability journeys use **live**
population. A shared journey needing combat stays live throughout, including its
prerequisite traversal. A controlled startup PASS establishes the healthy-player
handoff assertion, not populated-intro fidelity. The fixture is audited for these
opening routes; it is not a general enemy classifier for untested regions.

The console, JSON, HTML and JUnit identify each result's population profile.
`probe-population-profile.json` retains actor-table censuses and intercepted
creation requests; controlled phases fail if an audited enemy or generated actor
is present. The original-asset/load-gate fixtures run in Regression **01**.
For populated diagnosis, use the underlying motion probe with
`--population-profile live --background-spawns` and the same bounded suite
scenario/checkpoints. Isolated suite scenarios remain available and retain the
profile appropriate to their checks.

Normal F5 now uses the runtime's default **5000 ms** logo waits. Automated suite
journeys also present each actual logo, then send a separate SDL Space
press/release before proceeding. Horseback skip input is separate. The first
publisher logo is conditional, so two or three logos are valid. Evidence is in
`probe-logos.json`; `--logo-policy natural` on the motion probe observes the waits
without logo input. `--natural-intro` concerns the horseback sequence separately. A motion probe
without a startup selector now taps the first observed horseback action through
`--run-recon`; the old surface injector is explicit legacy mode
(`--intro-skip-action 0 --startup-logo-delay-ms 0`).
Original x86 has timed five-second logo loops; direct logo key skipping in the
original is not established by those loops. These taps validate the reconstructed
host wait, not original skip fidelity.

Old captures remain tied to their recorded environment and pinned executable.
Changing defaults does not rewrite them. The new executable has a new identity;
exact replay of an old capture requires its matching old executable. Compatible
replay may still diverge. Fresh fixture/GDB journeys record input/inspection with
recording **off** and make no portable exact-replay claim. See the
[population and logo journal](journal/entries/noncombat-population-and-logos-2026-10-26.md)
for current acceptance and retained failures.

## Blocks and visible gameplay

Each block below has a numbered **Regression** launch entry. Gameplay blocks
share the display picker; source/tool checks in **01** launch directly. Debug and
ASan run concurrently by default, with sequential journeys within each configuration.
Source/tool checks without a configuration run once before those workers.
Use `--workers 1` for sequential configuration execution.
Selecting a block includes its transitive prerequisites automatically; each
included prerequisite appears in the report. Compatible checkpoints share the
same live game process; separate journeys start fresh. CLI `--filter` narrows targets
within the selected block before prerequisites are added. Full and block launches
use `--execution shared`; use `--execution isolated` for separate diagnostic
scenarios with repeated setup. `--list` shows logical coverage and the planned
number of gameplay processes for either execution mode.

The single **starred full regression suite** appears first among regression entries,
with a distinct full-suite label. Block entries follow in basic-to-complex order,
numbered **01–10**. The full suite and gameplay blocks use the same
headless/visible picker; **01** has no display prompt.

| Launch | CLI `--block` | Target scenarios |
| --- | --- | --- |
| `★ Full` | `full` | All registered cases |
| `01` | `checks` | Generation, runner contracts, original-code fixtures and host retention-worker faults; no game window |
| `02` | `startup` | Early skip, delayed skip and natural intro |
| `03` | `menus` | Horseback/pedestal/gameplay menus, settings, load/save dialogs, Start Game and explicit unfinished effect coverage |
| `04` | `movement` | Movement/release and courtyard return |
| `05` | `unarmed` | Basic/advanced unarmed attacks, real unarmed enemy contact and natural player damage |
| `06` | `workshop` | Workshop traversal, sword pickup, sword attacks, smith kill and door passage |
| `07` | `swimming` | Water traversal/swimming and explicit unfinished armed-water coverage |
| `08` | `potions` | Consumption trials, branch coverage and potion-to-sword sequence |
| `09` | `stability` | Mixed gameplay journey and released observation |
| `10` | `replay` | Supplied complete replay corpus, or explicit optional skips |

**Regression 01** runs source/tool/host checks only, so it opens no game process
or SDL window. Its ordinary launch name is retained and it bypasses the display
picker; a desktop display is unnecessary. The CLI still explains why no window
is opened when a display option is supplied manually.
**Regression 02: Startup** is the first numbered block with gameplay windows.
The display picker controls gameplay journeys, not source comparisons.

**Regression 02** intentionally executes **six** gameplay processes: early Space skip,
delayed Space skip and natural intro completion, each once in **Debug** and once
in **ASan**. These paths require different startup inputs, and each configuration
runs a separate executable. The eight logical results include two builds.
Common released-player and menu-exit phases repeat in each window to verify its
own successful startup and clean shutdown. Console startup lines identify the
mode and configuration; `Journey.DelayedSkip` names the delayed variant directly.

`visible-debug` and `visible-asan` show that configuration while the other runs
headless. `visible-both` shows up to two SDL windows concurrently, one per
configuration. CLI `visible` remains an alias for both. With `--workers 1`,
visible windows run one at a time. Successful journeys close through the tested
menu exit. Window titles identify their configuration, journey and current phase.
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
Report metadata records the block, per-configuration display mode, driver and
worker count. Concurrent output names each logical case's configuration; phase
lines also identify their worker. Showing one window still runs both builds.

## Journeys execute; checkpoints report

`scripts/e2_suite.py` declares compatible checkpoint sequences explicitly in
`SHARED_ROUTES`. Selection expands logical prerequisites first, assigns the
workshop prerequisites before dependent potion trials, then covers the remaining
checks with the smallest practical compatible routes. Ties prefer shorter route
declarations. Unselected checks are omitted. A dependency never establishes
coverage: the movement checkpoint actually executes its turn, displacement,
modifier and settled-release assertions, even when workshop traversal follows.

The main journey can execute delayed intro skip → movement/release → all eight
unarmed attacks → workshop → unarmed smith damage → sword pickup/attachment →
four sword attacks → smith kill → door destruction/passage → mixed input and
released observation → menus/exit. Only selected checkpoints and the setup they
need run. Workshop traversal, sword pickup and attack setup run once within that
journey. The report retains each checkpoint's phase range, observations and
shared evidence directory. No save/load, snapshots, teleportation or state
restoration supplies subsequent checks. When menus and other gameplay are both
selected, the ordinary gameplay journey owns delayed-startup evidence. A failing
intro menu therefore cannot block independent movement solely by owning its
startup prerequisite; the menu journey validates its own setup without crediting
that startup assertion a second time.

Early skip and natural intro remain separate from delayed skip. Courtyard return
and swimming use separate routes; armed-water checks remain unfinished.
Regression **04** uses the user's recorded pedestal → central courtyard →
pedestal loop from session `20261026_110852_153`. The human opening skip was at
progress **438**, while the suite preserves its progress-**83** startup assertion.
In live diagnostics, population and preceding movement can change who occupies
the stairs; timing alone cannot reproduce the human scene. A bounded input
detour remains available when guard **293** occupies the return staircase. The
default noncombat fixture prevents that guard from being created. This keeps
startup, movement/release and the loop in **one** shared process per configuration:
**eight** logical results in **two** gameplay processes. The full plan remains
**184** logical cases and **20** gameplay processes.

`scripts/scenarios/courtyard-waypoints.json` retains published snapshot IDs,
positions, cameras and inspection hashes for both legs. These points guide
continuous SDL input with the existing actor-radius tolerance. The clearance
coordinates are separately declared navigation guidance, not human samples, and
rejoin the recorded pedestal endpoint. Neither route assigns game state or treats
guidance coordinates as exact-position assertions. The route must cross camera
**166**, reach central courtyard **125** at floor **4096**, and return to pedestal
**175**, floor **3328**, within **500** world units of its starting area. Live
observations are retained at each waypoint, followed by released-input and clean
menu-exit checks. See the
[courtyard route journal](journal/entries/recorded-courtyard-route-2026-10-26.md)
for acceptance and the earlier incompatible/overprecise probe failures.

If preceding movement finishes on the nearby steps, bounded ordinary input
first approaches the pedestal through the clearance corridor; the same starting
camera/floor assertions still apply. Diagnostic motion probes can explicitly
exercise the alternate input path with suite option
`"courtyard_stair_clearance": true`; this selects inputs and changes no game state.

Four potion trials remain four fresh processes with their original bounded waits
and live RNG. Trial A can continue directly into potion-to-sword assertions.
Damaged trials require actual fresh damage; missing damage blocks unexercised
potion assertions. Debug and ASan execute separate pinned binaries in independent
processes. Other destructive or incompatible routes receive separate declarations.

## Menu stages and unfinished effects

The catalogue has **184** logical cases across Debug/ASan. The full shared plan
uses **20** gameplay processes, compared with **96** isolated diagnostic scenarios.
Menu block **03** selects **102** logical results and **two** gameplay processes,
one per configuration, instead of **58** isolated scenarios.

`Journey.MenuStages` follows horseback intro → pedestal intro → released gameplay.
At each stage it tests Escape open/close, the Cancel button, Quit → No, Settings
open/OK, music and sound controls, all difficulty values, Load dialog/cancel and
Save availability/dialog/cancel. Input targets the live item hit rectangles.
Control checks require both the actual flag and its displayed label to change,
then return to the initial value through input. Save is expected to remain
disabled during both intros. Dialog checks do not credit serialization or loading.

Start Game is selected at each stage. Each checkpoint must return to the initial
horseback camera/action and initial player identity/health, with reset action
progress. Intro progress advances before testing restart, so simply resuming
cannot pass. A successful restart advances naturally or through the accepted
delayed Space skip to the next required stage. There is no snapshot or game-state
restoration. The delayed-startup result requires actual opening-action progress
of at least **83**, SDL Space and healthy released Joe at the expected courtyard
camera/floor. Unselected restart checks do not run during focused diagnostics.

Every stage explicitly lists optional `MusicPlayback`, `SoundPlayback`,
`ResolutionRendering`, `LoadState`, `SaveState`, `Subtitles` and `FemaleStartGame`
as **SKIPPED** with specific missing implementation/acceptance reasons.
`ResolutionToggle` observes the current control but is also **SKIPPED** until
resource reload and rendered dimensions have accepted assertions. A changed
music/sound flag alone cannot prove audible output; an opened dialog cannot prove
the loaded scene/state or the saved game's correctness.

An independent UI assertion may fail while its requester remains live. The
journey records that **FAIL**, restores any changed option to its observed
baseline through real input, closes the menu and verifies the live player/stage
before continuing independent checks. This is cleanup, not an assertion retry.
Unexpected signals/stops cannot use that recovery path. A failed Start Game may
continue only if the same live stage is observed; its transition remains **FAIL**.

Current acceptance is red: the first expanded visible run finds stale
music/sound/difficulty labels, Debug gameplay Start Game SIGSEGV, and an ASan
stack-buffer overflow opening Load during the intro. Isolated restart checks
pass horseback restart but fail pedestal → initial intro in both builds.
Earlier passes survive; unexercised checks are blocked. See the
[menu/parallel journal](journal/entries/menu-stages-and-parallel-suite-2026-10-25.md)
for evidence, timings and limits. No runtime repair is part of this suite change.

## Results and evidence

Console output distinguishes:

| Status | Meaning |
| --- | --- |
| `PASS` | The logical checkpoint completed its own assertions; journey lifecycle separately requires clean menu exit and completed inspection |
| `FAIL` | A command, route phase, outcome assertion, sanitizer check or timeout failed |
| `BLOCKED` | A prerequisite failed or was not exercised; the case is not counted as a passing test |
| `SKIPPED` | Explicitly unfinished coverage, absent optional replay corpus, or a required random branch not sampled |

Completed checkpoint passes survive later assertion failures, crashes and
interruptions. The failing checkpoint is `FAIL`; checkpoints the stopped journey
has not exercised are `BLOCKED`. A fresh setup failure retains its own failing
`setup.*` checkpoint and blocks the unexercised target, without rewriting an
earlier independent prerequisite pass. External prerequisite failures block only
the affected checks; another eligible checkpoint in the same planned journey
can still execute. Multiple independently exercised failures remain separate
FAIL results, even when subsequent cleanup and native Quit succeed. A checkpoint
explicitly skipped by the live journey remains SKIPPED, with observed evidence
and its reason.

Each journey also has a lifecycle result. A crash, timeout, incomplete probe,
nonzero native exit or incomplete inspection fails the journey and the suite,
even if every earlier logical checkpoint passed. JSON retains those lifecycle
results in `journeys`; HTML and JUnit add a separate failing journey row so an
all-pass checkpoint list cannot conceal a shutdown failure. JUnit may therefore
contain additional lifecycle failures beyond the logical-case count.

Exit **0** means all required selected cases passed. Exit **1** means a failure
or blocked case; **2** means required coverage was skipped; **130** means the
suite was interrupted. Known unfinished optional cases can be skipped without
making an otherwise successful run fail. Skipped cases are always listed.

Default evidence is `.tmp/gameplay-suite/run_<UTC timestamp>/`; `latest.json`
points to the last default run. `--output PATH` requires a new destination and
never replaces an older run. After each execution unit, results refresh:

- `report.html`: status table, reasons and links to command logs.
- `report.json`: dependencies, root blockers, checkpoint phase ranges and observations,
  journey lifecycle, planned process counts, binary identity, timings and overall
  exit status (`e2suite.result.2`).
- `report.xml`: JUnit format; blocked cases use `<skipped type="blocked">` and
  retain a separate `status=BLOCKED` property, plus journey/checkpoint/evidence
  properties for shared results.

With two workers, the root reports merge `debug/`, `asan/` and the one-time
`shared/` worker reports. Relative evidence links include that worker directory;
each worker retains its runner log and exact command. JSON `lanes` records
start/end times and exit codes, so overlap can be verified. Only the coordinator
writes merged reports. A worker crash preserves completed checkpoint passes
from its atomic journal, fails its lifecycle and blocks unexercised checks;
the other configuration continues. Interrupting the coordinator signals both
workers, finalizes available partial results and stops their process trees.

Each configuration pins its executable and SHA-256 before gameplay and executes
that copy, verifying its identity before each journey/replay. Commands,
console/GDB output, input transitions and ordered journey phases are retained
per execution unit. The shared checkpoint/phase/input journal updates atomically
as work progresses and is read on timeout or interruption, even if the final
probe report does not exist. Native inspection stores state and the last eight game frames in an
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
| Courtyard | Recorded route via camera 166 to central courtyard 125/floor 4096, then pedestal 175/floor 3328 and starting area |
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

Every successful journey includes the menu exit check. The selected menu case
is credited only where that checkpoint actually passes; other journeys retain
their exit evidence as lifecycle validation. The registry also runs scratch
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

The runner contracts cover dependency and block selection, explicit shared
coverage, distinct startup/RNG/water/configuration paths, one-time traversal and
weapon setup, partial passes, setup failures, external blockers, missing
assertions, crashes after successful checkpoints, interrupted journals, native
subprocess timeouts, coverage provenance, all report formats, isolated-mode
compatibility and visible launch/picker forwarding. The native
`Host.SessionMaintenance` cases inject repeated allocation failure and a throwing
reporter into the real cleanup worker, then verify recovery and clean shutdown.
Current runtime results belong to the [active gameplay task](implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
and its linked journal, rather than a permanently green claim in this guide.
