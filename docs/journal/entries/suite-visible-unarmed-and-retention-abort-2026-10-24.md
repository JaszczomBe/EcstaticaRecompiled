# Visible suite blocks, unarmed combat and retention abort — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 interaction recovery](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Usage: [Gameplay tests](../../gameplay-tests.md).

The user supplied `.tmp/gameplay-suite/run_20261024_153719_353309/`: **80** cases,
**43 pass / 10 fail / 21 blocked / 6 skipped**, **1,145.18 seconds**. They requested
investigation of its abort, unarmed combat coverage, sequential visible SDL
gameplay and separate prerequisite-aware block launches with a default-headless
display picker. Parallel execution is explicitly deferred.

## Reported abort and repair

`debug.Traversal.Workshop/probe.log` records `SIGABRT` during the final menu phase.
The stopped thread is the session-retention maintenance worker, not the game
thread. The stack shows `std::terminate` after `std::bad_alloc`, constructing
`std::string("Log cleanup failed: ")` at `SessionRetention.cpp:384`. Cleanup's
first exception had already entered its handler; a second allocation failure
escaped that handler and therefore the worker's top-level function. The original
allocation failure's origin is not established by this stopped stack. The GDB
frame's zero-sized allocation argument is insufficient evidence for a cause.

The pinned reported Debug executable is SHA-256
**a8f9eec65d784f84f667d8d417f9155d64d87a28930694cbf255133451ffa693**.
The session was exported with `e2-debug.py bundle` and integrity-verified under
`.tmp/suite-watch-investigation/reported-abort-bundle/`. Adjacent
`reported-abort-extra/` retains the GDB log, phase/input journal, command, probe
report, original binary identity and a hash receipt. Export-time working-tree
context is distinct from the older image's build provenance. Recording was off;
the bundle has no replay and makes no exact reproduction claim.

The repair formats cleanup errors into a bounded stack buffer, attempts the
existing artifact reporter, and catches reporter failure with a direct stderr
fallback. It also handles unknown cleanup/reporter exceptions. Cleanup continues
on the next interval. Reconstructed game code and `GenerateRecon.js` are untouched.
The preserved animation-name mismatch is not overwritten.

`src/artifacts/tests/maintenance.cpp` drives the real retention worker with a
one-second interval, denies allocations on its background thread and supplies a
reporter that throws. `scripts/check-e2-session-maintenance.py` uses the runtime's
actual i386 multilib CMake setup. The old handler reproduces **SIGABRT**. The
repaired Debug and ASan contracts survive at least two failed cleanup cycles,
resume real deletion when allocation becomes available, survive the reporter's
exception and join normally. Logs are `maintenance-before.log`,
`maintenance-after.log` and `maintenance-asan.log` under the investigation root.
`Host.SessionMaintenance` is registered independently in both configurations.
This proves the exception path repair, not absence of memory pressure or other
corruption during gameplay.

## Unarmed coverage

`Combat.UnarmedDirections` depends on movement rather than sword pickup. It
checks unarmed equipment kind, four basic Ctrl/arrow groups, four advanced
Ctrl/Alt/arrow groups, the selected representation slot becoming the live action,
modifier release and actual resumed movement. Original selector instructions
retain the basic **0xb8–0xc3** and advanced **0xcc–0xd3** families and direction
offsets; bounded disassembly is retained as `original-combat-selector.asm`.
The original control reference independently describes both input combinations.

`Combat.UnarmedContact` depends on unarmed controls and workshop traversal. A new
process walks to smith **602** without picking up the sword, strikes through SDL
Ctrl/Up and requires observed enemy health loss while Joe remains unarmed.
The initial Debug qualification observes **100→60**, then resumed movement and
native menu exit. This is contact/damage acceptance; it does not claim every
unarmed move hits, an unarmed kill, original rendered limbs or swimming combat.

## Launches and reporting

The full catalogue now contains **86** cases. Full and ten block launches share
one `pickString` input with **headless** selected by default. A separate
**Ecstatica: Full regression suite — visible SDL** entry directly selects visible
gameplay. Ordinary **Ecstatica Recompiled** F5 configuration is unchanged.

Blocks select targets and then expand their complete prerequisite/observation
closure. They do not supply game state or bypass failed movement. All cases run
one at a time, including Debug and ASan. Visible fresh journeys use the desktop
Wayland/X11 SDL driver, identify case/phase in the title after release, pace host
updates in batches of at most three at a maximum 60 per second, and pause menus
briefly. Host timeouts expand threefold; update/route bounds and assertions stay
the same. Clock/RNG/actor state is not assigned. Fresh timing and encounter
outcomes may differ. Original-code checks have no game window; corpus replays
retain their recorded display environment and strict checks.

Block, display mode/driver and worker count **1** are recorded in report metadata.
Fifteen runner contracts pass, including block closure without sword pickup for
unarmed tests, desktop selection/failure, command propagation, launch entries,
default picker, native timeout, root blockers and reporting semantics.

The sequential visible Wayland menu block qualifies **3/3** cases in **48.29
seconds** under `visible-menus/`, with both gameplay processes exiting zero and
complete inspection. No parallel scheduler is added. Native gameplay validation
continues below; historical full-suite failures are retained unchanged.


## Native follow-up evidence

The repaired workshop probes traverse the normal route, observe released input
for **65.14 seconds (Debug)** and **65.28 seconds (ASan)**, then verify menu
cancellation, resumed movement and confirmed Quit. Both exit zero, complete
inspection and report no ASan or cleanup error. The process lifetime crosses the
default **60-second** maintenance interval. Artifacts are
`retention-workshop-{debug,asan}.*` under the investigation root. These are fresh,
recording-off bounded probes, not an exact replay or proof that memory pressure
cannot recur.

The first integrated unarmed qualification, `unarmed-acceptance/`, retains
**12 pass / 1 fail / 1 blocked** in **361.07 seconds**. Both configurations pass
all eight direction/modifier combinations, host fault injection, startup,
movement and workshop traversal. Debug's contact setup exhausts a fixed-point
approach; ASan's single held heading does not damage the moving smith. The
prototype records both outcomes rather than treating them as passing contact.

The final encounter follows observed live target positions and reorients between
at most **12** bounded attack bouts. It never assigns actor state or health.
Per-bout player/target positions, heading and target health are retained. The
waypoint helper also checks whether its last allowed update actually reached the
radius before declaring exhaustion; it adds no input or tolerance. A new Debug
qualification observes smith health **100→80** in two bouts and exits normally.
The final combined evidence is recorded below.

`unarmed-final/` completes **14/14 PASS** in **352.34 seconds**, including both
host fault contracts and both complete build/startup/movement/workshop/unarmed
dependency chains. All eight requested unarmed action groups pass in each
configuration. Actual smith damage is **100→80** in Debug (two bouts) and ASan
(one bout); both retain unarmed equipment, finish the gameplay menu assertions,
exit zero and complete inspection. The earlier prototype results remain separate.


The first visible ASan combat block, `visible-unarmed-final/`, retains **3 pass /
1 fail** in **110.90 seconds**. Startup, movement and menu exit pass; the unarmed
readiness assertion waits for only IDs 11/12 while Joe remains in original idle
variant **871**. Original instructions **0x429c22–0x429c9c** select six categories
and read the signed high word at `rep+0x24+category*2`, equivalent to a short at
`rep+0x26+category*2`. Readiness now uses those six live slots and records them.
`original-idle-selector.asm` preserves the bounded original comparison. Attack
slot/action, health, release and damage assertions are unchanged. This is a test
precondition correction, not a runtime repair or a retry of unchanged assertions.

With that correction, `unarmed-idle-table-debug.*` passes all eight attack groups
and clean menu exit from idle **871**, using the six live slots. The next visible
ASan block, `visible-unarmed-idle-table/`, retains **2 pass / 1 fail / 1 blocked**
in **47.79 seconds**. Its startup smoke passes, but the new movement process
hits the previously recorded event fault before courtyard readiness:

`FUN_0042f85c ← FUN_0042b880 ← FUN_0042b338 ← FUN_0042ae80 ← FUN_00427584`.

The leaf is reconstructed line **26638**, arguments **11282596 / 8874952**.
The pinned ASan executable has SHA-256
**12cfcb667ca6c34e6d01fa176468e18f30f35fc4c06f07e518567d2a5f7f39be**.
Combat is correctly **BLOCKED** by the native movement-scenario failure. This
does not establish an ASan allocator report or a connection to retention's
separate `SIGABRT`. Its session is exported and verified in `visible-event-bundle/`;
`visible-event-extra/` preserves GDB output, command, pinned identity and hashes.
Recording is off, so no deterministic replay is claimed. The event contract
still needs original-code recovery; the failed run is not retried until green.

The separate final visible Debug block, `visible-debug-idle-table/`, passes
**4/4** cases in **114.40 seconds** with the corrected original idle table:
pinned build, startup, movement/release and all eight unarmed attack groups.
Its three gameplay windows run sequentially on Wayland, use phase titles and
menu observation pauses, then exit zero with completed inspection. The ASan
failure above remains unchanged; this is independent configuration acceptance.

Both SDL builds, fifteen runner contracts, Python syntax, generator syntax,
whitespace and the **238-document** README tree pass. Native results/source
identities and bundle verification pointers are collected in
`.tmp/suite-watch-investigation/validation.json`. The full 86-case suite is not
rerun in this continuation. Existing source/generator, animation/potion and
courtyard/damage-route failures remain open, alongside the captured event fault
and unexplained allocation pressure. No stage, commit or push is performed.
