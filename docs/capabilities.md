# Project state and capabilities

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

The active target is Ecstatica II on Linux/i386 with original external game data.
The completed reconstruction milestone is a historical bounded state/surface
proof. Everyday development now uses SDL, original backgrounds and typed
diagnostic markers to recover gameplay.

| Area | Available capability | Acceptance boundary |
| --- | --- | --- |
| Build and editor | Clang 21 i386 Debug/ASan, SDL/X11 builds, selected-target F5 | Debug is the everyday choice; optimized runtime and 64-bit execution remain experimental/incomplete |
| Gameplay | Recovered movement, camera crossings, NPC/object population and bounded workshop activation | Human swimming, sword pickup, four kills and two broken doors verified; animation-cache stall repaired; Debug/ASan door passage and actual menu Quit pass; human random-potion pickup verified and delayed effects repaired with live Debug/ASan poison dispatch; bottle removal and subsequent sword use confirmed in the latest human run; visible health/potion diagnostics added; fresh Debug healing 85→100, poison onset, invisibility dispatch and conditional no-op verified; final effect expiry/cure remains open; latest alternate-target crash repaired with isolated generated Debug/ASan prefix evidence; extended stability is open and takes priority; animation-name parity restored for potion cleanup; natural effect summaries are optional; wider pickups/rendering remain deferred |
| Rendering and audio | Original backgrounds, palette/presentation, typed markers for creatures, corpses, doors, debris, potions, weapons, items and props; modal menus suppress the overlay | Original actor meshes/animation and audio fidelity remain incomplete |
| Persistence | Original data/resource loading and replay | Quick-save is a no-op; functional game save/load is unproven |
| Investigation | Automatic F5 logging, replay, state timeline, rolling frames, pinned binary and debugger evidence | Capture limits, incomplete recordings and strict replay divergence remain explicit |
| Recovery tools | Original-x86 fixtures, crash export, state/report queries, route expectations, dependency-aware Debug/ASan gameplay suite with concurrent configurations, shared checkpoints, three-stage menu coverage, one/two visible windows, unarmed combat and host allocation-fault checks, recovery/diagnostic index | Headless menu labels, three-stage restarts and Load/Save dialog checks pass after original-backed menu/surface repairs; functional persistence/audio and broad rendering remain unqualified; sampled/fixture evidence does not establish complete game behavior; rr is optional and currently absent |

## Current implementation and next work

The [door approach reliability regression](journal/entries/regression-door-approach-reliability-2026-10-27.md)
reopens full-suite acceptance: the user's visible-Debug/two-worker run fails door
approach and blocks stability on matching source/binary hashes. The prior single
headless pass does not prove repeatability. Scene-planned approach now passes a
controlled old-code failing/new-code passing regression, paced Debug/ASan probes
and final headless two-worker integration (**148 PASS / 57 optional SKIPPED**,
all **143 required**, **26** clean native journeys). Actual desktop SDL and an
independent diagnostic setup crash remain open; broad reliability is unqualified.

The [sequential headless sweep](journal/entries/headless-regression-sweep-2026-10-27.md)
records a historical single-run pass: all **141 required** checks pass, **144 PASS / 59
optional SKIPPED**, no failures/blocked checks, **1795.66 s**. All **24** native
Debug/ASan journeys exit zero and complete inspection; **203** case identities,
**34** source hashes and pinned/live binaries are audited. Original-backed
menu/surface, pose and bitmap-record repairs have generator parity. Portable
replay and broader game fidelity remain open. The extended-prefix **−100** door
writer and the earlier screenshot freeze remain unexplained; the journal records
those limits and every retained attempt.

The [runtime implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md)
and [population/interaction task](implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
own the precise current frontier, verification and next bounded recovery action.
The [Regression 08 investigation](journal/entries/regression-08-freeze-and-event-callback-2026-10-26.md)
repairs a captured original event-7 node callback and adds automatic agent-probe
stopped-stack capture. The user's screenshot freeze remains unreproduced; its
later SIGKILL is the user's stop action, not an identified root cause.
The next run's [receive-hit setup failure](journal/entries/receive-hit-contact-navigation-2026-10-26.md)
changes test-input strike alignment and audited guard eligibility; real original
melee damage remains required. No new runtime change accompanies that correction.
Regression 04's recorded round trip passes in Debug/ASan with an explicit
noncombat opening fixture that prevents audited enemy creation. Live combat and
normal gameplay keep population; wider collision/AI and clean visible-input
acceptance remain separate. The task records retained live-route failures.
Follow the [tooling implementation](implementations/debugging-tools/debugging-tools.md)
for debugger integration and tool acceptance.

The [milestone plan](plans/runtime-milestones.md) owns later rendering, control,
timing, sound, persistence and portability direction. The
[journal](journal/journal.md) records recent changes. Check working-tree and commit
state as described in the root README; local repairs can be newer than the last commit.
