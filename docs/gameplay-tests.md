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
Agent probes save `probe-stopped.json` for native signals or thrown
`std::bad_alloc`. After 30 seconds without debugger or inspection progress, they
write `probe-stall.json` and interrupt GDB for bounded stack capture before
process-tree cleanup. The overall probe timeout also captures before cleanup.
Reports distinguish this watchdog interruption from a spontaneous native fault;
completed checkpoints retain their results while interrupted journeys fail.
See the [Regression 08 investigation](journal/entries/regression-08-freeze-and-event-callback-2026-10-26.md).

## Character rendering coverage

Gameplay journeys pass `--player-mesh --npc-mesh`, matching F5's character flags.
Original character ellipsoid bodies and bone animations replace their diagnostic
shapes; objects/equipment retain diagnostic rendering. Per-phase JSON includes local-pose
hashes, node positions and physical-page pixel differences against the background.
The probe requires actual pixels and changing poses when sampled updates differ;
modal snapshots are excluded from that evidence. With NPC meshes enabled, pixel
differences describe all original actors in the physical frame; Joe's local-pose
hash remains player-specific. `probe-enemy-mesh.json` separately records each
selected enemy's node positions, local-pose hashes, health and state. Inspection supplies startup
heartbeat progress even for direct natural-intro player probes. Recording stays off.

The checks block includes `Original.PlayerMesh`, `Original.EllipsoidPixels`,
`Original.InterpolatedNodeEvents` and `Original.RenderCopies` for both Debug and
ASan. These execute bounded original x86 comparisons for pose/camera/shading,
pixels/depth/materials, node event ownership and redraw copies. See the
[player recovery journal](journal/entries/player-model-and-animation-2026-10-27.md)
and [enemy journal](journal/entries/enemy-model-and-animation-2026-10-27.md)
for qualified routes and retained combat failures. A changed pose hash or completed route alone does
not establish visual fidelity or exhaustive player action coverage.
`Original.WaterEntry` also verifies every action offset against the installed
original `OFFSETS` directory, including absent slots. `Original.AnimationNames`
now compares all 488 representation names and cache ownership as well as all
1800 animation names; this covers dropped-potion representation `w_pot` beyond
the former 1000-byte bound. The [human-play follow-up](journal/entries/enemy-play-crash-and-dropped-potion-2026-10-27.md)
records native consumption and the fixture/replay limits.


## Game persistence

```sh
python3 scripts/run-e2-suite.py --build --block persistence --configurations debug asan
```

Regression **11** runs seven source/host fixtures, two round-trip scenarios and a save-open failure
scenario per configuration, plus the two build checks: **22** logical cases and
**ten** native process executions. `Persistence.World` uses live opening actors;
`Persistence.Attachment` uses the established noncombat-opening workshop route to
pick up the sword before saving. `Persistence.SaveFailure` verifies the error
dialog while editing a label, dismissal, resumed movement and clean Quit. Both enable original player/NPC bodies. Each
same-process journey performs two Save/change/Load cycles, then a fresh process
loads that file. Assertions compare serialized actor state at loader return,
then verify movement, animation, original attack action and attached equipment
following Joe. They also compare saved thumbnails with both displayed menu pages,
require the preview rectangle in physical gameplay pages to stay unchanged, switch
between filled/empty/filled previews and cancel without any loader call, and
verify successful Load dismisses both requesters without another Escape. Native pending timers are not present in these opening saves;
`Original.SaveRestoreTimers` compares nonempty timer reconstruction against
original code separately. Menu-only dialog probes retain `state_round_trip=False`.

The probe copies all installed save files into a private runtime directory and
selects only a slot whose installed contents are exactly `CR LF CR LF`. It fails
before running the game if none of slots 0–8 is confirmed empty. A writer guard
stops before any unowned write. Installed saves and unowned private slots are
SHA-256 checked even on failure. Slot 9 is excluded from test writes.
`probe/report.json`, `same.log`, `fresh.log`, `expected-state.json`, input/phase
JSON and the six save-specific extracted fixture/provenance files retain evidence.
`Original.Menus` supplies the original-x86 preview oracle and checks the display-only
2× enlargement on both hosted pages. `Original.MenuLayout` compares original
requester dimensions/title positions and ASCII font pixels. Native probes assert
main/slot panel bounds and every slot hit rectangle and capture the menu pages. Recording
is disabled; native execution has per-process timeouts and a progress watchdog.

For a single bounded diagnostic:

```sh
python3 scripts/probe-e2-game-save-load.py build/Debug/clang21-i386-sdl/e2recomp --game-data /path/to/Ecstatica2 --output /tmp/e2-save-trial --timeout 240
```

Add `--equipment --population-profile noncombat-opening` for the sword route.
`--failure-case empty|save-open|unsupported|truncated|missing` selects one private
file-rejection diagnostic instead of a round trip. Missing/truncated tests stop
at the loader failure helper and kill the isolated process before unqualified
generic fatal cleanup; they do not prove rollback or clean failure exit. The
[journal](journal/entries/game-save-load-recovery-2026-10-27.md) retains failed
attempts, exact original ranges and current gameplay/compatibility limits.

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
numbered **01–11**. The full suite and gameplay blocks use the same
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
| `07` | `swimming` | Unarmed/armed swimming actions and water traversal; optional shore exit remains unfinished |
| `08` | `potions` | Consumption, naturally selected effects and potion-to-sword sequence |
| `09` | `stability` | Mixed gameplay journey and released observation |
| `10` | `replay` | Supplied complete replay corpus, or explicit optional skips |
| `11` | `persistence` | Protected private-slot Save/change/Load cycles and fresh-process restoration |

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
window. Corpus replays receive the selected SDL driver explicitly and retain strict
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

The main workshop journey can execute delayed intro skip → movement/release →
workshop → sword pickup/attachment → four sword attacks → smith kill → door
destruction/passage → mixed input and released observation → menus/exit.
Unarmed attacks/contact and displaced door passage have separate fresh journeys. Only selected checkpoints and the setup they
need run. Workshop traversal, sword pickup and attack setup run once within that
journey. The report retains each checkpoint's phase range, observations and
shared evidence directory. No save/load, snapshots, teleportation or state
restoration supplies subsequent checks. When menus and other gameplay are both
selected, the ordinary gameplay journey owns delayed-startup evidence. A failing
intro menu therefore cannot block independent movement solely by owning its
startup prerequisite; the menu journey validates its own setup without crediting
that startup assertion a second time.

Early skip and natural intro remain separate from delayed skip. Courtyard return,
unarmed swimming and armed swimming use separate routes.
Regression **04** uses the user's recorded pedestal → central courtyard →
pedestal loop from session `20261026_110852_153`. The human opening skip was at
progress **438**, while the suite preserves its progress-**83** startup assertion.
In live diagnostics, population and preceding movement can change who occupies
the stairs; timing alone cannot reproduce the human scene. A bounded input
detour remains available when guard **293** occupies the return staircase. The
default noncombat fixture prevents that guard from being created. This keeps
startup, movement/release and the loop in **one** shared process per configuration:
**eight** logical results in **two** gameplay processes. The full plan remains
**205** logical cases and **26** gameplay processes.

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
Every trial accepts whichever original effect is selected, including a valid
no-op. Branch summaries are informational and never require a particular draw.
Damaged trials require actual fresh damage; missing damage blocks unexercised
potion assertions. Debug and ASan execute separate pinned binaries in independent
processes. Other destructive or incompatible routes receive separate declarations.

## Goal-driven encounter navigation

`scripts/e2_navigation.py` drives bounded observation → SDL input → progress
checks for receive-hit setup, workshop corridors, fixed smith contact and sword
approach. It records decisions under `details.navigation` in `probe-journey.json`.
The navigator is test tooling; normal F5 controls and recovered runtime code are
unchanged. Enemy-contact checks retain live population. Water action/traversal
journeys and suitable pickup checks use `noncombat-opening`.

Navigators default to **2400 updates**, **6 local replans** and **55 host seconds**
(**165** in paced visible mode), with input batches of at most three updates and
a **90-update** ground / **180-update** swimming progress window. Those are
combined across its route/readiness/approach phases, rather than reset on every
waypoint or attack bout. Scene readiness additionally allows **300 updates**.
Scene-planned water approach declares **3200 updates** for its combined
ground/entry/water goal; other navigators retain **2400**. The surrounding
journey's existing update/host limits still apply. There is no
scenario restart on exhaustion. Local guidance uses a **300-unit** height band;
it does not prove connectivity. A recorded corridor establishes the stair
approach, and each reached node must satisfy observed height. Workshop setup can
attempt a separately reported local join within **4000** units after earlier
controls displace Joe. Unknown joins and detours remain unproved until traversed.

Receive-hit setup follows the recorded courtyard corridor and selects from
original audited `St_gobsc` guards **284/293**. Actor-table identity, active
membership, health, representation, original NPC attack slots and same-height
eligibility are required. A guard on another ledge is rejected. The driver aims
in front of the selected opponent using its observed heading/radius and releases
controls for original melee. Waiting retains the existing 100-unit hysteresis
in front and resumes movement when Joe falls behind. If an opponent becomes
unavailable, reselection consumes the shared replan budget and repeats eligibility
checks; replaced instances fail. Explicit fixed-target goals cannot reselect.

For the encounter corridor, the join prefers the observed height. Displacement
beyond its 1800-unit local boundary invokes the existing live scene-floor planner
before following the corridor, within the same update/replan/host budgets.

A health watchpoint retains the original melee-handler stack and node owner's
identity. Only an attributed hit from the selected eligible opponent with Joe
still alive satisfies damage, including a hit during approach. Nearness alone
cannot pass. A bounded read-only observer retains original melee-node positions.
The [contact-navigation evidence](journal/entries/receive-hit-contact-navigation-2026-10-26.md)
records the failed policies, final correction and native acceptance limits.

Smith **602** remains fixed for unarmed contact; sword **3717** remains fixed for
pickup. A known original scene child can be approached while its scene action
is still pending, but must become represented before encounter/pickup readiness.
That position guidance does not credit an active opponent. Unarmed checks still
require no sword and real smith health loss; pickup still requires Space,
reciprocal attachment, equipped movement and following world position.

Progress distinguishes lack of displacement, circling and steady pursuit of a
moving target. Detours measure progress toward their own waypoint. Nearby actors
are observations rather than proof of obstruction; Joe is excluded. Unknown
blockers cannot be called locked or destructible, and the controller never
attacks them. Known workshop door **980** has a constrained crossing goal after its explicit
sword-damage/collapse assertion succeeds. It aligns before the opening, steers
from live observations and requires an observed plane crossing within a
256-unit half-width test gate. A bypass cannot pass. Released movement must
still finish over 100 units beyond the original door plane on the same floor;
`details.door_passage` records the result. This is specific scenario guidance,
not inferred physical doorway dimensions or automatic door/progression planning.
See the [door-passage evidence](journal/entries/workshop-door-passage-navigation-2026-10-26.md).

A failed encounter setup owns `setup.ReceiveHitEncounter` or
`setup.UnarmedEncounter`, blocks the unexercised combat assertion and fails the
journey lifecycle. Established encounters that fail their actual combat assertion
remain FAIL. Navigation releases held input on return/failure/interruption;
outer probe cleanup stops descendants on timeout or termination. Atomic journals
retain the goal, bounds, targets, positions, actions, camera/height, paths,
rejected interactions, progress and exhausted budget. Source identity includes
the navigator and its contracts. `Tools.NavigationContracts` runs once in the
source/tools selection; the full catalogue is **205** cases with **26** gameplay
processes. See the [implementation evidence and limits](journal/entries/goal-driven-navigation-2026-10-26.md).

Potion-to-sword continuation plans from the actual post-drink floor instead of
requiring every historical prop-corridor point. This approach also avoids
observed actors using original motion flag **0x1000**, state other than **11**
and three-quarter combined radii, with a **64-unit** steering margin and
**60-unit** waypoint tolerance. The plan
records each candidate; it does not infer an actor's role or prove collision
causality. Stalled movement refreshes the observed floor/actor plan within the
same six replans, 2400 updates and 55-second host bound. Final pickup, reciprocal
attachment, attacks and bottle-removal assertions stay required. Bottle approach
uses the same policy to reach the actual bottle position after the workshop join.
Other routes
retain their existing navigation policies. The
[sweep journal](journal/entries/headless-regression-sweep-2026-10-27.md) records
the integration failure, floor-only attempt and qualification boundary.

If observed actors disconnect an otherwise connected floor route, the driver
proves floor-only connectivity, releases input for **30 updates**, then refreshes
actor clearance within the same six-replan/update/host budget. It never walks
the floor-only diagnostic path. Static disconnection, node-budget errors and
persistent obstruction still fail.

Receive-hit corridor guidance hands over at the first eligible opponent within
**1800 units** on Joe's actual floor. It avoids walking past that opponent to a
historical endpoint. Pursuit moves around the opponent's original collision
disc before closing on the front contact point at three-quarter combined radii plus **64** (**448 units**
for the observed 256-unit radii). Its approach band is **64**, with **32** waiting
hysteresis, preventing a loose off-axis stop or a goal inside the collision disc.
Original state-2 retreat with signed readiness **+0xea ≤ 0x3000** is ineligible;
a ready guard of either audited
identity remains eligible. Actual surviving damage attributed to original enemy
melee is still required. The sweep journal records native handoff, outside-disc
steering and released-clearance-wait evidence, plus the guard-293 damage limit.

Sword approach uses the original pickup query's forward selection region:
one Joe radius ahead, then one radius around that point. With Joe's observed
256-unit radius, approach stops within **2R−64 = 448 units**, faces the actual
sword and sends Space. Actual reciprocal attachment, equipment and subsequent
movement/combat assertions remain required.

Unarmed directions/contact use their own fresh native journey. The armed
workshop, smith, door and stability route preserves a fresh active door and all
real prerequisites. An extended combined unarmed-contact → pickup prefix once
left the door at **−100** before the dedicated door check; its writer remains
unidentified. Separate compatible lifecycles preserve both assertions without
resetting game state. Door/stability journeys enable a bounded read-only door
health watch, retaining at most **64** original writer stacks. A repeated
unexpected deactivation still fails the required door check.

Smith-kill guidance follows and faces the same live actor between bounded
strike bouts. The smith can retreat after a hit; holding one stale heading is
insufficient. One fixed-target navigator retains the six-replan/update/host
bounds, with at most **20×60** attack updates and **150** settling updates.
Actual health loss, death, state **11** and representation removal stay required.
When required directional attacks have already killed the smith, the later
checkpoint needs a positive pre-attack baseline and a read-only observed fatal
write from original melee owned by Joe **0**, against the same actor pointer.
Other writers, other attackers and truncated traces cannot supply that evidence.
Final death and representation removal still have to pass; an unexplained
already dead target remains a failure.
The same fatal-hit evidence can stop a fixed kill pursuit if a queued original
strike finishes during a navigation update. Only that explicit fixed goal has
this completion observation; absent/replaced actors still fail. Input releases
before the driver waits for the required final death/removal state.

Water paths now use `Navigator.navigate()` and the read-only live scene-floor
planner in `e2_scene_navigation.py`. The archived human water route is no longer
read by the driver. Goals come from actual water cells in cameras **543/545**;
the bounded planner checks floor shapes, height layers, Joe's **256-unit**
clearance and audited audio/scene-load bytecode. It never calls the side-effecting
recovered floor helper. Actual swimming entry triggers a fresh water-only plan
from Joe's observed position. Forward/backward swim steering avoids orbiting a
nearby target behind Joe and completes each stroke before minor heading
corrections. Region goals retain **512-unit** camera clearance; return goals
use an interior cell in the starting water region. Captured maps/script policy and `details.navigation`
retain source hashes, planned paths, bounds and decisions. A route movement over
**1024 units** between observations still stops as an unproved discontinuity.

The swimming block requires entry/displacement, four original combat directions
and a camera-crossing return journey, both unarmed and after real sword pickup.
The mode must remain representation **13** or **10**, respectively, throughout
water traversal; armed checks retain reciprocal sword attachment. Each combat
direction verifies its actual original mapped action, release and resumed swim
movement. These checks exercise combat actions, not live-water-enemy damage.
The controlled **noncombat-opening** population remains explicit. Shore exit is
a separate optional unfinished check, rather than a reason to skip armed water
actions. See the [water-goal evidence](journal/entries/water-goals-and-scene-navigation-2026-10-26.md)
for current qualification and the [previous route repair](journal/entries/swimming-route-navigation-2026-10-26.md)
for historical acceptance.

Current headless and visible-Debug full-block selections both pass **22 required
checks**, retaining **2** optional shore-exit skips. A separate focused visible
entry/traversal selection passes **5/5** after movement leaves Joe west of the
pedestal. Successful journeys require native menu Quit and complete inspection.

Door **980** approach now plans from Joe's actual post-combat position to the
existing local strike corridor through scene floors and observed actor clearance.
`Interaction.DoorPassageDisplaced` is a separate required case: after real
workshop/sword/smith setup, SDL input must reach the captured distant start
**[4790, 4096, −11985]**, within **240** units on its actual floor. Only then may
the same damage/collapse/opening-crossing assertions run against a fresh door.
This controlled precondition exercises the user's failure condition without
relying on a particular random smith retreat or assigning game state.
The [reliability journal](journal/entries/regression-door-approach-reliability-2026-10-27.md)
records the negative control, qualification matrix and remaining display limits.

## Menu stages and unfinished effects

The catalogue has **205** logical cases across Debug/ASan. The full shared plan
uses **26** gameplay processes, compared with **108** isolated diagnostic scenarios.
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

The first expanded visible run found stale
music/sound/difficulty labels, Debug gameplay Start Game SIGSEGV, and an ASan
stack-buffer overflow opening Load during the intro. Isolated restart checks
pass horseback restart but fail pedestal → initial intro in both builds.
Earlier passes survive; unexercised checks are blocked. See the
[menu/parallel journal](journal/entries/menu-stages-and-parallel-suite-2026-10-25.md)
for that historical evidence. The
[2026-10-27 headless sweep](journal/entries/headless-regression-sweep-2026-10-27.md)
repairs original option-item storage, restart dispatch/identity, binary slot
labels/previews and the actual compatibility surface provider/callers. Its full
menu block passes **54 required results / 48 optional skips**, with native menu
exits and completed inspection in both configurations (**54.06 s**). Functional
audio, persistence and full renderer acceptance remain outside those passes.

The same sweep repairs a terminal action-event actor handoff exposed by the
ASan stability journey. Events **0x16/0x17** retain the original actor before
root-pose calculation; **3072** original-x86 event comparisons and **1152**
root-pose cases pass per normal/ASan fixture mode. The repaired stability block
passes **16/16**, including mixed input, **60-second** released observation,
native Quit and completed inspection. This remains a bounded stability result.

A later watchdog captures a bitmap-record stall while loading an unarmed action.
Original-backed repairs restore the allocated record return, mapped **20×20-byte**
pool and selected disposal owner. `Original.BitmapRecords` compares **14,208**
allocation, publication, eviction, compaction and reuse cases per normal/ASan
fixture mode. The journal distinguishes these fixtures from native parser and
gameplay qualification and retains the stopped attempt.

## Results and evidence

The user's later full visible-Debug/two-worker run returns **142 PASS / 1 FAIL /
1 BLOCKED / 59 optional SKIPPED** on matching sources and executables. The
[door approach reliability continuation](journal/entries/regression-door-approach-reliability-2026-10-27.md)
supersedes full-suite acceptance. A single headless green run does not prove
reliability across live AI outcomes, display pacing and concurrent configurations.
The failing approach never reaches the door's damage assertion, so that run
cannot prove either door passage or subsequent Debug stability.

The correction passes an old-code failing control, paced Debug/ASan distant-start
probes and a complete final-source two-worker headless run: **148 PASS / 57
optional SKIPPED**, all **143 required**, zero failures/blocked checks,
**1112.78 s**, **26** clean native exits with complete inspection. All **34**
source hashes and pinned/live binaries match; **113** contracts pass. Six actual
door interactions, including four controlled distant starts, retain original
outcome assertions. Actual desktop SDL qualification and an independent earlier
diagnostic setup crash remain open. This scoped proof does not make AI, clocks
or RNG identical, and a single integrated pass does not establish broad reliability.

The [2026-10-27 sweep](journal/entries/headless-regression-sweep-2026-10-27.md)
records the earlier `full-final-07/` execution: **144 PASS / 59 optional SKIPPED**, all
**141 required** checks, no failures/blocked work, **1795.66 s**, exit **0**. All
**24** native journeys quit normally and complete inspection. Audits verify all
**203** case identities exactly once, **34** source hashes, pinned/live binaries,
checkpoint/branch provenance and JSON/JUnit agreement. All **112** contracts and
registered native fixtures pass. This does not qualify optional omitted features,
whole-game fidelity or new human gameplay.

Console output distinguishes:

| Status | Meaning |
| --- | --- |
| `PASS` | The logical checkpoint completed its own assertions; journey lifecycle separately requires clean menu exit and completed inspection |
| `FAIL` | A command, route phase, outcome assertion, sanitizer check or timeout failed |
| `BLOCKED` | A prerequisite failed or was not exercised; the case is not counted as a passing test |
| `SKIPPED` | Explicitly unfinished coverage, absent optional replay corpus, or an optional random outcome not sampled |

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
| Player damage | Bounded live guard-284 encounter, attributed original melee hit and surviving Joe health loss |
| Door | Actual repeated damage, collapse/deactivation of door 980 and movement through its opening |
| Potion trials | Actual branch, drinking, removal and original action/timer/health effects |
| Potion then sword | Bottle remains removed after sword attachment and all four attacks |
| Swimming | Live scene-floor routes to water cameras 543/545, swimming representation/displacement, directional actions and outward/return traversal |
| Menus | Escape, cancel, actual resumed movement, reopened Quit and Yes, native exit zero |
| Mixed stability | Workshop, sword, attacks, door passage, repeated movement and bounded released observation before menu exit |

Every successful journey includes the menu exit check. The selected menu case
is credited only where that checkpoint actually passes; other journeys retain
their exit evidence as lifecycle validation. The registry also runs scratch
generation parity and focused actor/animation/script-name, key release, attack,
pickup, attachment, timer, cache, script-flow and water-identity comparisons.
Failures in those isolated comparisons remain independently visible.

Waypoint coordinates have journal provenance in `scripts/scenarios/`. They
guide bounded SDL input; they are never written to game state. The historical
`potion-damage-inputs.json` remains evidence and is no longer the receive-hit setup. Fresh Debug/ASan timing and RNG can produce different
paths or encounter outcomes. A route failure is retained, rather than retried
until green.

## Random outcomes and unfinished work

Four fresh potion trials use bounded waits **0, 37, 83, 221** updates. Two first
require real damage. Trials validate whichever original branch is observed;
pickup, drinking and reciprocal attachment must be observed, followed by bottle
removal and the selected effect's health/action/timer checks. Healing while
already healthy and an unafflicted conditional no-op are valid consumption.
There are no injected potions, forced types or RNG writes. Four optional branch
summaries record naturally observed healing from damage, poison onset,
invisibility onset and no-op. An absent outcome is optional **SKIPPED**, so luck
cannot make a successful consumption block incomplete. A failed trial still
fails the block and cannot supply branch acceptance.

Damaged potion setup shares the navigator's height-aware workshop corridor join
instead of walking back toward the pedestal. Guard chases beyond its existing
local join boundary require a connection planned from the live scene floors;
the planner's update, node and script-policy bounds remain enforced. The
[potion-consumption journal](journal/entries/natural-potion-consumption-2026-10-26.md)
records the reported failures, animation-name repair and current acceptance.

Poison death, invisibility expiry/cure and shore exit remain
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

The suite forwards its selected SDL driver through the scenario and replay
launchers. Direct `replay-e2.py run` or `e2-debug.py scenario` calls preserve the
recorded driver unless `--video-driver dummy|x11|wayland` is supplied. An explicit
override is recorded in scenario results and remains subject to the native
startup compatibility checks. Historical human captures that omit an SDL driver
are rejected as having an extra environment field when dummy is enforced; they
cannot qualify invisible replay. The [current sweep](journal/entries/headless-regression-sweep-2026-10-27.md)
retains both failed supplied-corpus diagnostics and explicit optional corpus
skips. No recording or strict verification rule is rewritten to obtain a pass.

## Maintaining the suite

Add a `Case` with a stable name, real prerequisites, bound and observable
assertions. `observes` schedules coverage evidence without requiring every trial
to pass before the evaluator can report its actual coverage. Avoid requiring an
unrelated return journey for a test that only needs an outward route.

```sh
python3 scripts/check-e2-suite.py
python3 scripts/check-e2-navigation.py
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
