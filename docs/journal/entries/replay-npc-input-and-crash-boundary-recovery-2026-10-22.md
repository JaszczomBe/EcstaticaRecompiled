# Replay NPC Inputs And Crash Boundary Recovery — 2026-10-22

The user authorized continuation after the [human pedestal replay test](pedestal-crash-replay-test-2026-10-22.md)
diverged before its reported `FUN_0042db74` crash. Existing staged implementation
is preserved; all changes in this continuation remain unstaged. No commit.

## First Differing Game Path

Read-only GDB capture/replay comparisons isolated NPC decisions before the
palette-clock mismatch. At simulation tick 156, actor 50's first RNG seed and
state match, but subsequent RNG-call placement differs. A later startup trace
also identifies actor 3030 choosing action slot 3 versus 1 from differing facing
values, before sequence 22,164. The service-order report is a later symptom.

Original `E2WIN95.EXE` instruction evidence:

- `0x427dd0` and `0x42812c` preserve target X in ECX across the angle helper;
  generated C instead reads uninitialized `extraout_ECX_08`/`extraout_CX`.
- `0x427f6d` supplies the actor motion reference's X component at `+8`, alongside
  Z at `+0x14`. The C reused an unrelated prior distance temporary as X.
- CX carries target facing through timer/RNG/state selection to `0x428899` and
  the other action branches. The C replaces it with uninitialized volatile
  outputs. The recovered facing is retained explicitly, including target-clear
  and height-rejection branches.
- The legacy `FUN_00432c64` wrapper itself reads uninitialized `in_AX` and uses
  placeholder mapped tables. Only these three recovered NPC calls now use the
  existing original-verified `E2R_PolygonAngle16` leaf. Unrelated legacy callers
  are not promoted globally.
- `0x428bfd`/`0x428c10` reload actor EAX before target-facing turns. Five duplicated
  C call sites passed an angle/volatile temporary as actor. They now retain
  `local_6c`, like the previously repaired player turn callers.

These recover original arguments and register lifetime; no movement/physics or
RNG algorithm is substituted, and replay never forces game state. The generated
C change is 30 added/22 removed lines, with small anchored generator mirrors.
Syntax and regeneration reproduce the hand edit exactly; no other generated
artifact changes.

The focused `check-e2-npc-target-inputs.py` compares **16,384** original x86 target,
distance, facing, field/state and RNG-call handoffs with poisoned register
temporaries. Angle/floor/copy/RNG/death dependencies are intercepted explicitly;
this fixture verifies their inputs and surrounding control flow. The existing
population fixture independently compares the pure angle/polar helper against
original instructions across **65,536** vectors. Both pass under ASan. The
extended turn-caller fixture passes **1,296** existing player cases plus **810**
NPC actor/signed-angle cases, normally and under ASan.

## Publish The Clock That Enters The Fault

After the NPC repairs, fresh replays could follow the recorded NPC path to its
last action, then report `INCOMPLETE: clock prefix exhausted`. The first changed
clock result that released the busy-wait into the faulting update was still
pending in the writer; no later host pump existed to flush it.

`src/replay` now writes and flushes the first result at each changed timestamp
before returning it to the game. Subsequent equal results remain compressed.
This improves process-crash recovery without signal/shutdown handlers or clock
resynchronization. It is not per-call fsync or a power-loss guarantee. Repeated
clock suffixes and other unpublished buffered records remain outside the
recoverable boundary described in [the replay guide](../../replay.md).

A contract captures two million equal clocks, observes the changed clock and
immediately `_Exit`s without a pump, Finish or fclose. A fresh replay consumes
that exact prefix and reaches the same changed result. Debug/ASan parser,
identity, order, checksums, malformed files and truncated-tail contracts pass.

Five million real-clock reads take 0.095–0.097 s without capture versus
0.101–0.104 s with capture (**5–9%** producer overhead), using 9,119–9,379 event
bytes. This is a synthetic clock benchmark, not whole-game overhead. Logs:
`/tmp/e2-replay-publish-clock-bench-{1,2,3}.log`.

## Repeated Native Crash Evidence

Fresh Debug recording: `session_20261022_205543_607`.
Executable SHA-256:
`b76f1329b2459c372acd22ca00144932a7f701fb8968f33a22f2c5b8493f2260`.
It retains **475,117,178** game-clock calls in **26,901** rows, **16** checkpoints
and about **2.81 MB** of recording files, through sequence **475,145,280**.
It remains incomplete and has no clean end marker.

Three fresh bounded native replays exit **139/SIGSEGV**, with no prior divergence,
at the same logged action-event boundary. A fourth run through GDB pauses for
two seconds, then verifies the capture's exact function, sequence and checkpoint:

`FUN_0042db74`, sequence `475145280`, last matching checkpoint `16`.

The exported bundle's `--stop-before 475145280` also exits 76 at sequence
475,145,279 with checkpoint 16 still matching, providing a bounded inspection
point before the final recorded clock call. No replay creates a nested capture.

The GDB capture and paused replay have the same call chain through
`FUN_0042b880 → FUN_0042b338 → FUN_0042ae80 → FUN_00427584 → FUN_0042a70c`, including
the same action-slot/actor arguments. The lost `in_EAX` inside `FUN_0042db74`
remains the native crash to repair separately. This establishes a repeatable
bounded crash route; it does not prove every game byte or all corruption causes.

The exported read-only recording, pinned executable, hashes, capture/three replay
logs, paused GDB trace and reproduction notes are preserved outside retention in
`.tmp/replay-bugs/pedestal-recovered-20261022/`. `README.txt` contains the runner
command. Original human evidence remains untouched in
`.tmp/replay-bugs/pedestal-20261022-202026/`.

The repaired executable correctly rejects that **old** human capture in exact
mode (73, executable identity). Its explicit compatible attempt diverges at
sequence 22,156 after matching checkpoint 13. No claim is made that old faulty
decisions can be recovered with the repaired code, or that its missing final
clock result can be reconstructed. New human recordings use the fixes.

## Other Verification And Acceptance Limits

- Debug **and ASan** clean intro/menu captures each pass three fresh replays plus
  a two-second GDB pause: 11 inputs/20 checkpoints each. Debug retains 338,218
  clock calls; ASan retains 194,207. This supersedes the earlier ASan menu-order
  failure, not full ASan gameplay acceptance. Reports:
  `/tmp/e2-replay-npc-menu{,-asan}-final/report.json`.
- All four SDL/X11 Debug/ASan builds and logger-off SDL build pass. Original
  frame-clock checks retain all **560** cases normally/ASan, including 100,000
  unchanged polls. Population/line-of-sight/wander/lifetime ASan fixtures pass.
- Crash/truncated-tail recovery, pre-cleanup freezing of an older replay source,
  no nested/probe capture and forced disk-write failure with continued gameplay
  pass with logger enabled and disabled. Evidence:
  `/tmp/e2-replay-publish-lifecycle{,-no-log}.log`.
- Actual native `.vscode/launch.json` Debug/ASan launches survive eight seconds
  each with `--record auto`, producing automatic recordings. Reports:
  `/tmp/e2-replay-npc-vscode-{debug,asan}.json`.
- Existing runtime regressions and all eight Debug/ASan control rows pass.
  Full populated movement capture still reaches `FUN_0042db74` before completing
  its route; that clean-route gate remains failing, with no assertions relaxed.

The next crash investigation can use the preserved new recording and stop before
sequence 475,145,280, then recover the original node/actor contract in
`FUN_0042db74`. Workshop walking re-entry, sword pickup and full experimental ASan
remain separate. Staged patch SHA-256 remains
`b7b181717ceaec035bf79ae70fc8911e50a51c89057fc06efb12343f4422cca7`.
