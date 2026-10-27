# Regression 08 freeze and event callback — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Runtime owner: [Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Probe owner: [Task 10](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
This continues the [natural potion checks](natural-potion-consumption-2026-10-26.md).

## Reported freeze

The screenshot matches Debug Potion A in
`.tmp/gameplay-suite/run_20261026_201316_367843/`: camera **176**, Joe
**(1922,4096,-12336)**, health **100**, during `traversal.potion`.
The last retained inspection is update **1612**, presentation **562**. The native
log records `Log cleanup failed: std::bad_alloc` and subsequently `SIGKILL`;
the probe later reports that there is no process to debug. The user confirms
stopping the suite **after** the game froze. Consequently that signal does not
establish an OOM kill, and no stopped stack survives to identify the freeze.
No unrelated desktop key sequence is observed in this failed journey.

The parent report remains `running` after interruption. Child reports retain
Debug **5 PASS / 1 FAIL / 2 BLOCKED / 8 SKIPPED**, ASan **7 PASS / 1 FAIL /
8 SKIPPED**; later interrupted B trials are distinct from the screenshot.
Neither the earlier input-interrupted startup nor historical headless success
explains this in-game freeze.

## New diagnostic evidence and original-code repair

All investigation artifacts are under `.tmp/regression08-freeze-20261026/`.
An allocation-catch Debug A selection passes **5/5** in **99.39 s**. A subsequent
concurrent visible-Debug/headless-ASan block with stack and memory capture
retains **22 PASS / 0 FAIL / 6 BLOCKED / 4 SKIPPED**, **272.42 s**, exit **1**
because Debug C crashes before its startup checkpoint. Both A/B trials and the
ASan block pass. Neither attempt reproduces the reported freeze or allocation
failure. Sampled Debug memory stays near **538 MiB virtual / 189 MiB resident**;
these samples do not diagnose the original allocation failure.

`stop-1207212.json` captures a separate `SIGSEGV` in **FUN_0042f85c**.
Its reconstructed `in_EAX` is uninitialized (**0x148**), while the dispatcher's
actual event node is **0x987580**. Original **0x42c602–0x42c604** explicitly
moves ESI into EAX before the call. Original **0x42f85c–0x42f9c0** retains that
node across owner/attachment posing, three RNG draws and X/Y/Z rotations, actor
**5** and action **1** loads, position/orientation copies, activation and immediate
action attachment. The reconstructed function and dispatcher now carry those
inputs explicitly and preserve the hosted actor context. The shared rotation
helper gains its original Z case, preserving existing X/Y behavior.

The generator mirrors the function, signature and dispatcher repair. Actual
regeneration and scratch generation match all four artifacts without unrelated
reconstruction changes. The original executable SHA-256 is
`737e27ddfb76501ba6caf4f504b0c128854a36733526b17d30f635a1c255025b`.

`check-e2-spawn-action.py` adds **6144** original-instruction comparisons across
attached/unattached nodes, resource absence, matrices and deterministic fixture
RNG streams. It compares three RNG draws, call order, IDs, pose/activation
ownership, action attachment, restored context and the complete fixture memory.
Both normal and ASan runs pass, together with the existing pose/spawn/queued
action cases. The polygon-lighting fixture is extended to exercise Z directly;
both normal and ASan runs pass **24576 X/Y/Z rotations**, **10240 angles** and
**8192** lighting comparisons against original instructions. Debug and ASan SDL
builds pass.
This repairs the captured callback crash; equivalence to the user's freeze is
**unproven**.

## Automatic probe capture

Agent GDB probes now save `probe-stopped.json` on native signals and thrown
`std::bad_alloc`, including bounded all-thread stacks, stopped-frame locals,
registers and process status/maps/limits. A watchdog observes GDB progress and
inspection frames. After **30 seconds** without either, or the overall probe
timeout, it writes `probe-stall.json`, interrupts its own debugger once, allows
**five seconds** for stack capture, then uses existing process-tree cleanup.
GDB progress prevents the inspection observation cap from creating a false stall.
There is no automatic retry, actor write, health/RNG assignment or recording.
Normal human F5 launch behavior is unchanged.

Reports retain stopped/stall artifacts and recognize `Program terminated with
signal SIGKILL` as well as received signals. Watchdog SIGINT is marked as an
agent interruption, rather than presented as a spontaneous crash. Existing
checkpoint/lifecycle rules continue to preserve completed checks and fail the
interrupted journey. The new diagnostics module is included in source hashes.

All **60** suite contracts and **31** navigation contracts pass. Three bounded
synthetic native GDB fixtures prove actual stack capture for `SIGSEGV`, thrown
`std::bad_alloc`, and watchdog `SIGINT`, including process maps/status. These
fixtures do not modify the game or inject potion types.

## Native qualification

The full potion block in `repaired-native/` passes **27 results / 5 optional
skips / 0 FAIL / 0 BLOCKED**, **343.22 seconds**, exit **0**, with visible Debug
and headless ASan. All **22 required** results pass, including all eight fresh
consumption trials, both sword continuations and real receive-damage checks.
All ten native game processes exit zero through the menu and complete inspection.
No signal, allocation exception, watchdog interruption or sanitizer error occurs.

Debug naturally selects poison in A/B/C and healing **95→100** in D. ASan
selects no-op at **100** in A, invisibility in B/D and poison after damage in C.
All bottles are removed. Three unobserved optional branch summaries and two
unfinished death/expiry/cure checks account for the skips. No potion type or RNG
is injected, and the original screenshot freeze is **not reproduced**.

After this full run, diagnostic initialization additionally removes stale
heartbeat/stop/stall files when a direct probe reuses its output prefix. Native
synthetic GDB signal/allocation/stall fixtures pass again with deliberately stale
files present. Fresh visible-Debug/headless-ASan startup/menu qualification in
`final-diagnostics-startup/` passes **4/4** in **27.20 seconds**, with two more
clean native exits and complete inspection. This changes diagnostic-file
initialization only; the reconstructed runtime and gameplay driver are unchanged.

`validation.json` verifies all twelve native exits and inspections, both pinned
binaries against the live builds, required-result status and source provenance.
All **21** source hashes in the final startup selection match current files.
The full block retains its executed hashes: **20** still match; the diagnostics
module differs solely by the subsequent stale-file cleanup just qualified.

Pinned SDL executable SHA-256:

- Debug: `18d276951a842ac75a8e59dde47783e7ce3e59a7bf8b3bf71c895146221b7fd0`.
- ASan: `7212786677358c0e0ac614a88dbd9a7e24abd38a81192f3c3a75a04eadbbf487`.

Source SHA-256:

- Reconstructed C: `04b41b3fec5f293e215dce2ab188cf8dc029ba2bf8cc2f59f576c7d8c5c1bcab`.
- Generator: `248d310bb6dccec17169d95e08c98057430e91fd68b9d1d6cf146311bffc16ea`.
- Final diagnostics: `b9dd0a499e72d7d4ca3e53fc3c9f3f90c09fd1fd8eb3d7eaad0ab464cbdbc4b6`.

The screenshot freeze remains unconfirmed, rather than attributed to the
separately repaired callback crash or desktop input. These runs do not establish
extended stability, final potion death/expiry/cure, human F5 acceptance or the full
regression suite. No commit or push is made.
