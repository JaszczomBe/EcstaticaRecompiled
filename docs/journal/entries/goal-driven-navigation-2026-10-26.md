# Goal-driven regression navigation — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Bounded regression navigator](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Runtime owner: [Population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Usage: [Gameplay navigation](../../gameplay-tests.md#goal-driven-encounter-navigation).
Baseline: [Regression 05 investigation](goal-driven-navigation-handoff-2026-10-26.md).

The user selects Task 10 for implementation. This continuation replaces the
attacking historical receive-damage schedule with an explicit receive-one-hit
goal and reuses the input/observation controller for workshop, fixed unarmed
contact and sword approach. Recovered runtime C, generator, population policy,
ordinary F5 launch and the user's staged changes remain untouched. No new
controlled encounter, health/position/RNG write or scenario restart is added.

## Observation and original behavior audit

`scripts/e2_navigation.py` has no GDB/game mutation dependencies. Its bridge reads
actor-table identity, the live linked list, positions/heading/height, health,
state, action resource/progress, representation, attachment, flags/radius and
camera. Inputs go through the existing real SDL bridge. The existing archive
fixture identifies guard **284 / gob3**, guard **293 / gob3b**, smith **602 / korc2**,
sword **3717 / nschwrt1**, and their original scene ownership. This manifest is
not a general hostility classifier; terrain actors/props are not selected from
presentation labels or the collision flag.

Bounded disassembly of installed `E2WIN95.EXE` is retained under
`.tmp/goal-navigation-20261026/original-*.asm`, original SHA-256
`737e27ddfb76501ba6caf4f504b0c128854a36733526b17d30f635a1c255025b`:

- **0x428e29–0x428e34** adds **0x6d** to the NPC attack variant in the state-7
  branch. Navigation observes those representation attack slots, rather than
  assuming any loaded actor can attack. The live goblin slots include actions
  **344/550/354**. This eligibility observation alone does not prove a hit.
- **0x42efdc–0x42f34a** reads a melee node's owner at **+0x22**, applies actual
  node-to-target contact/range filters and updates target health. A read-only
  Joe-health watchpoint retains that stack and the owner identity. The native
  evidence below attributes the surviving **100→95** loss to **284**, rather
  than guessing from nearby actors or a changed health value.
- **0x448a3c–0x448be0** shows that the floor query is not universally pure:
  a scripted-block branch at **0x448b3a** writes actor **+0x140**. No planning
  query API or call into that recovered helper is introduced. Existing scene-grid
  fixtures and recorded human floor/camera samples supply the audit boundary.

The controller follows the original connected courtyard samples before pursuing
284. Guard 293 can occupy a different ledge and is never a fallback for this
fixed encounter. **300** units is a local height guidance band, not proof of
floor connectivity or an exact melee-range model. Waypoints verify actual height;
unknown local joins and detours are explicitly unproved until traversed.

## Implementation and failure contract

Each navigator shares **2400 updates / 6 replans / 55 host seconds** across its
route, scene-readiness and approach/receive phases. Batches are **3 updates**;
progress uses a **90-update** window. Readiness has an additional **300-update**
cap. The existing journey host/update bounds remain. Repeated smith bouts reuse
one navigator, fixed identity and pointer; an instance change or disappearance
fails. Scenario-level failures never restart.

Steering tracks live positions. No displacement triggers a bounded local detour;
circling is distinct from steady pursuit of a moving target. Detour progress is
measured against its own waypoint. A nearby actor is evidence of proximity,
not proof of the cause; Joe is excluded from that list. Unknown blockers cannot
be labelled progression-locked or attacked. Automatic door/progression planning
is outside this slice; existing door destruction/collapse/passage predicates
remain unchanged and are not newly accepted here.

The driver releases attack controls for receive-hit setup and finishes as soon
as an attributed surviving hit is observed, including during approach. Setup
failure retains `setup.ReceiveHitEncounter` and blocks the unexercised damage
assertion while failing lifecycle/overall status. Missing damage after an
established encounter remains FAIL. Earlier checkpoint passes survive.

Workshop guidance retains the recorded corridor and its final camera/object
assertions. Earlier attacks can move Joe farther from that corridor: the nearest
height-compatible node may be approached with a separately declared **4000-unit**
local-join bound. Its connectivity is not assumed. Smith **602** and sword
**3717** can initially be active scene-track placeholders with no representation.
The original scene position guides an approach, then bounded released observation
must establish representation before encounter/pickup readiness. A loaded
placeholder never passes as an eligible enemy. Unarmed contact still requires
no sword and real smith damage. Pickup still requires Space, reciprocal attachment,
equipped movement and the sword following Joe.

Atomic `probe-journey.json` retains bounds, goal/phase, target and pointer,
observations, route provenance, path changes, rejected interactions, progress,
health watchpoint events and exhausted budgets. Navigation releases inputs on
failure/interruption; outer probe cleanup stops descendant processes on hard
termination/timeout. Original native crash/retention faults remain separate.

## Native evidence and development attempts

Evidence root: `.tmp/goal-navigation-20261026/`; `validation.json` indexes reports,
pinned executables, source identities, inspections and current limits. Every
attempt is retained. Recording is explicitly **off**; all runs are headless,
with two configuration workers and sequential processes within each lane.
Successful journeys require actual menu Quit, native exit **0** and completed
inspection. No portable exact replay or new visible acceptance is implied.

The native images are the same as the retained Regression 05 baseline:

- Debug: `df81e8ca950b25d1f2163f495ee8c410c4ef30cdf8c31e3e6251b0ba1b68ee42`.
- ASan: `e2bde1e384582571221e2ee9d6fbe1fc3a671cf87da70df3e26a38b3ec732b50`.

| Directory | Observation / reason for next changed implementation |
| --- | --- |
| `first-damage/` | Sandbox GDB startup exits 127 before gameplay; subsequent native probes use the authorized external debugger execution |
| `damage-native/` | Both approaches honestly reject guards above Joe; add the recorded connected stairs rather than planar pursuit |
| `stair-encounter/` | ASan has no eligible local opponent at route end; Debug pursues guard 293 toward a different floor; fix target 284 and extend the recorded corridor |
| `guard284-corridor/` | ASan records an attributed 284 hit **100→95**, but the prototype continues approaching and exhausts replans; Debug loses the target. Correct immediate-hit completion and detour progress |
| `progress-hit-stop/` | Debug surviving attributed hit and completed native exit; ASan's movement-before-damage state loses 284, honestly BLOCKED. This focused selection allocates movement to the damage process, unlike block 05 |
| `block05-live/` | Equivalent **14** checks / **4** gameplay processes: both receive-hit objectives PASS, **100→95**, native exit/inspection complete; Debug workshop's old controller fails and blocks contact. **12 PASS / 1 FAIL / 1 BLOCKED**, **104.54 s** |
| `block05-navigation/` | Reused workshop controller passes both traversals and both receive hits; both smith setups reject scene placeholders. **12 PASS / 2 BLOCKED**, **103.99 s**. Add explicit scene-position approach/readiness |
| `unarmed-scene-approach/` | ASan fixed smith contact **100→80**, native exit/inspection complete; Debug's prior attacks displace Joe outside the initial join bound. **10 PASS / 1 FAIL / 1 BLOCKED**, **88.28 s** |
| `pickup-navigation/` | Both controlled workshop and fixed sword pickups, attachment/movement, native Quit/inspection PASS: **10/10**, **51.37 s**, two gameplay processes |
| `block05-final/` | Directory name is provisional: **11 PASS / 1 FAIL / 2 BLOCKED**, **139.51 s**. Smith pursuit treats target motion as circling and exhausts replans; Debug damage passes, ASan approach blocks. Correct moving-target progress and use attack-range guidance, preserving actual damage. A reporting-only Joe/proximity filter changed between journeys, so this development report is not accepted as one frozen source set |

The baseline `.tmp/gameplay-suite/run_20261026_135535_282152/` selects the same
14 logical assertions and four gameplay processes, reporting **12 PASS / 2 FAIL**
in **173.27 s**. `block05-live/` reduces observed wall time **39.7%**, with both
receive-hit assertions now exercised successfully, while retaining its unrelated
workshop failure. This comparison preserves logical assertions/process counts;
it is not a performance benchmark or an overall green claim. Startup/movement
are not repeated per assertion as a workaround.

`qualified-block05/` is the final frozen-source run: **14/14 PASS**, **137.77 s**,
four gameplay processes. Every reported test-source hash matches the final files.
Both builds damage smith **602** unarmed **100→80** (Debug two bouts, ASan one),
receive an attributed guard **284** hit **100→95**, and finish native Quit/inspection.
Debug's receive-hit approach uses all **6** permitted detours and records **2**
steady-pursuit observations; ASan needs no detour. Smith setup uses **1** detour
in each build. The Debug unknown-blocker records retain the observed lack of
progress and chosen paths, without inventing a door or dynamic-collision cause.
No attack/Ctrl input is used by the receive-hit goal.

The same 14 logical assertions/process count now take **20.5%** less observed
wall time than the 173.27-second baseline. The baseline showed Debug and ran
ASan headless; this qualification runs both headless. Display pacing and fresh
population states differ, so this is a measured selection cost, not attribution
of all timing improvement to navigation. Earlier failed attempts remain failures.
The pickup example precedes the last pursuit/reporting changes; its static-target,
no-detour path and assertions are unchanged, and its own source hashes are retained.

## Contracts and remaining limits

**47** runner contracts and **15** navigator contracts pass. Cases cover moving
and circling targets, stuck/unknown/dynamic obstruction observations, height
mismatch, fixed identity/instance, deterministic ties, lost/dead targets,
scene readiness, update/replan/host bounds, interruption/release, early attributed
hits, missing attribution, survival, detour progress and setup/BLOCKED/lifecycle
reporting. `Tools.NavigationContracts` adds one global tools case: **185** logical
cases and the same **20** planned full gameplay processes. The full suite is not
rerun. Python compilation, the **245-document** tree (update then read-only),
and `git diff --check` pass. No runtime/generator edit requires a rebuild or
new original-code repair fixture; the bounded original disassembly audit is
retained alongside the native evidence.

This is a bounded local test navigator with recorded corridor guidance. It does
not solve whole-game routing, prove an arbitrary local join, classify unknown
doors, accept populated traversal generally, or repair live AI/combat/runtime
faults. Live timing and population can still yield honest bounded failures.
The preserved animation-name generator drift, event fault, menu/Load defects,
retention exception/allocation pressure and potion limits remain open. No stage,
commit or push is performed.
