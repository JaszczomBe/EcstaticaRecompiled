# Controlled opening population and startup logos — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Usage: [Gameplay tests](../../gameplay-tests.md#controlled-population-and-startup-logos).

The user identifies a test-fixture problem: random enemies and scripted guards
can obstruct or kill Joe before a movement assertion. After a read-only
assessment, they authorize preventing enemy creation for noncombat tests rather
than freezing colliders. This is an explicit controlled environment, not a repair
to original population behavior or evidence that populated traversal is fixed.

## Source boundary and implementation

`E2R_TEST_POPULATION=noncombat-opening` prevents the original scripted guards
**284** / `gob3`, **293** / `gob3b`, and workshop enemy **602** / `korc2` from
loading. Original `Files/ECSTATIC` and `Code/ECSTATIC.FAN` identify the guards as
children of `St_gobsc` (**101**, view **175**) and the smith as a child of
`blaksmit` (**251**, view **347**). The original resource identities, global
namespaces and retained Joe/stock/door/sword identities have an asset fixture.
The collision flag is unsuitable as an enemy classifier: doors and stocks also
carry it. Diagnostic marker names/classification are not used.

The small platform test-policy header is called before generic actor loading in
`FUN_00451f5c`, before each scene-child load in `FUN_00452140`, and at the terrain
creation leaf `FUN_0044dca4`. Suppressed scene children keep their original scene
records; the existing null-actor/completion path proceeds. No fabricated actor,
script completion, player release, health, position, action, clock or RNG state
is assigned. Bypassing creation intentionally changes subsequent RNG/AI timing.
Native startup checks require the healthy-player handoff at the original
camera/floor and prove both guard creation requests were intercepted. This does
not establish original populated-intro fidelity.

The manifest is scoped to the audited opening regression routes. It is not a
general hostility classifier for every game region. Other props, pickups and
structural scene actors retain their original loading/update paths. New routes
must audit additional scripted actors; disabling all non-Joe actors would remove
objects and invalidate meaningful traversal/pickup assertions.

The generator mirrors the three creation gates and header include. Ordinary F5
explicitly clears the fixture variable; unset/empty/live leave creation enabled.
Startup-only, actual unarmed contact/kill/damage, potion and stability journeys
stay live. Noncombat movement/courtyard, action-only attacks, pickup, swimming
and menu journeys select the controlled profile. A journey needing live combat
keeps its live profile even if an external failure later removes some assigned
checkpoints. There is no automatic scenario retry, parallel actor mutation,
invulnerability, save-state shortcut or population restoration.

Console, JSON, HTML and JUnit retain `population_profile` per logical result.
`probe-population-profile.json` records loaded/generated actor IDs and the
intercepted-request mask. A controlled phase fails on a leaked audited enemy or
terrain actor, or missing Joe. The existing failure/blocked/lifecycle rules remain.

## Logo policy and recordings

Normal F5 now sets the default **5000 ms** logo delay rather than zero. Automated
journeys also initialize and present each actual logo, stop at its wait, and
send a separate SDL Space down/up pair. Horseback skip input follows separately.
The first publisher logo is conditional: **two** logos occur in these native
examples; two/three sequences and interrupted waits have runner contracts.
`probe-logos.json` retains each observed logo and input pair. Menu-stage journeys
use the same helper. `--logo-policy natural` observes waits without logo keys.

Read-only inspection of the original `E2WIN95.EXE` and `e2vista.exe` logo blocks
at **0x410a84–0x410b05** finds five-second time loops without a direct key check.
Therefore these taps establish the reconstructed host wait's skip behavior, not
original logo-skip fidelity. No runtime logo-wait repair was introduced.

Replay identity stores `E2R_` environment options, and the replay launcher restores
the recorded environment. Existing captures are not rewritten. Exact replay of
an old capture still requires its matching pinned old executable; this runtime
change creates new binary identities, and compatible replay may diverge in state
or host-service order. Fresh GDB/input examples below use recording **off**,
bounded inputs/updates/timeouts and isolated inspection. No portable exact-replay
acceptance is claimed.

## Native acceptance and retained failures

Evidence root: `.tmp/noncombat-profile-20261026/`. `validation.json` indexes
reports, pinned binaries, source identities and limits. Debug/ASan builds pass.

| Evidence | Result |
| --- | --- |
| `movement-headless/` | **8/8 PASS**, **60.96 s**, two shared gameplay processes; movement/release and both recorded courtyard legs, central 125/floor 4096, return 175/floor 3328/starting area, native Quit and complete inspection |
| `movement-isolated/` | Equivalent selection **8/8 PASS**, **102.21 s**, six isolated gameplay processes; three startups per configuration instead of one |
| `pickup-final/` | **12/12 PASS**, **48.68 s**, two shared processes including the two new original-asset fixtures; workshop traversal, original sword/potion/door identity, real sword pickup/attachment and equipped following, native Quit and complete inspection |
| `menu-stages/` | **8/8 PASS**, **21.58 s**, two processes; show/hide at horseback, pedestal and gameplay, native Quit and complete inspection |
| `natural-logos/` | Debug presents two actual logos with no logo input: waits **5.67 s / 5.69 s**, then separate horseback tap, clean native exit and complete inspection |
| `live-combat/` | **10 PASS / 1 FAIL / 1 BLOCKED**; Debug retains live guards/terrain and smith **100→80** from an unarmed strike; ASan passes startup/movement/eight action checks but misses workshop waypoint 1 at `(9392,3456,-16861)`, correctly blocking contact |
| `movement-final/` | Visible Wayland Debug receives unrelated physical **N/C/R/E/Alt** input before horseback readiness and stops publishing phases. It is explicitly interrupted at **284.61 s**: startup FAIL, movement/return BLOCKED. ASan headless passes its four results. No completed visible Debug acceptance is claimed |
| `visible-x11/` | Changed display/no-activation-hint diagnostic fails immediately: SDL reports **x11 not available**. Evidence is retained; no input/visible acceptance |

The process/startup reduction is **6→2**; observed wall time is **102.21→60.96 s**
(about **40%** lower). These bounded runs are not a performance benchmark:
other investigation processes overlapped, and the isolated startup-only scenario
intentionally retains live population. All selected movement/return assertions
are exercised in both plans. Initial `movement-first/` (**8/8**, **60.93 s**)
validates the creation gates before the final logo/request-mask instrumentation;
`logo-first/` validates separate taps in a live early-skip journey. They are
development evidence, not substitutes for the final headless results.

Controlled census evidence has no audited guard/smith or terrain actor; the
workshop run records request mask **7** and preserves object/pickup checks.
The live ASan route failure remains visible instead of suppressing enemies in
its combat journey or retrying unchanged until green. The visible failure
contains unexpected desktop input, so it cannot establish the cause of the
pre-checkpoint stall or a clean visible-input run. X11 is unavailable in this
environment; default headless acceptance does not accept that driver.

All **46** runner contracts pass, including fixed profile selection after
blocking, leaked-enemy rejection with retained evidence, profile reporting and
separate logo inputs/interruption. Native policy fixtures execute **20,000**
production load-gate cases per configuration against original asset identities.
The original population fixtures pass normally/ASan, including **448** range
and **1060** terrain/placement comparisons and the opt-in no-spawn return.
The NPC fixture now includes the existing population-load wrapper when extracting
the leaf; its stale harness had omitted that already-present production helper.

Scratch generation retains exactly the pre-existing animation-name drift:
missing new-name sentinel initialization and two **0x1117/0x445c** byte-capacity
differences. The four new C hunks match the generator; existing C is never
regenerated over. New original-asset cases bring the catalogue to **184** logical
results, still **20** full shared gameplay processes. The complete suite was
not rerun. Existing event/retention failures, menu label/restart/Load faults,
bottle-removal limits and populated-route variability remain open. No staging,
commit or push is performed by the agent.
