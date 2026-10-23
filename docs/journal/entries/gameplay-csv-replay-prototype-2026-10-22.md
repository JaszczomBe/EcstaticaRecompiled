# Gameplay CSV Recorder And Replay Prototype — 2026-10-22

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Branch entry: `feature/logger`, HEAD `f714d24`, clean staged/unstaged worktree.
The user approved implementation after investigation and selected readable CSV
instead of the earlier suggested JSON Lines. Capture failure must leave gameplay
running with an incomplete notice. Original assets are fixed; save/load is not
reconstructed yet. This change remains unstaged and uncommitted. Undertone was
consulted read-only; no files there were modified.

## Result And Ownership

Implemented the initial recorder/replayer, with **full gameplay fidelity still
unaccepted**. [Usage and schema](../../replay.md) describes the precise contract.

- `src/replay` exposes a C interface for CSV capture/parsing, ordered service and
  input replay, clock run-length expansion, checksums and first-divergence reports.
- `src/artifacts` owns the shared session/lease/maintenance context. Existing
  filesystem wrappers, session naming and retention are reused independently
  of logger thresholds, masks and logger-enabled builds.
- Compatibility wrappers capture direct SDL delivery, queued dispatch, empty and
  nested pumps, cursor services, Sleep slices, GetTickCount/timeGetTime and
  GetLocalTime. Replayed host delivery updates the normal cursor and window
  procedure path. Physical gameplay input is suppressed; F11 aborts and F12 is
  tooling only. A real host poll also keeps long clock expansions responsive.
- A pure native adapter observes Joe through actor table ID zero, counters,
  camera, input tables, actor order/state, scene children/modal flags and RNG.
  It calls no reconstructed projection functions and never forces game state.
- Automatic SDL human/F5 capture, explicit agent opt-out, environment equivalents,
  compatible-rebuild attempts, stop-before controls, a fresh-process runner and
  read-only bug-bundle export are connected. Replay freezes its inputs before
  startup retention can remove the source, and never nests a recording.

The only generated C difference is removing `static` from fallback RNG storage so
the native adapter can read it. Seed `0x2a13f00d`, LCG arithmetic, all reconstructed
functions, physics and movement are unchanged. This visibility-only change has a
small generator mirror. Syntax/regeneration pass; the generated C diff is one
line and generated headers/globals/names have no drift.

The synchronous buffered writer has no dropping queue. Runs are bounded at
65,536 clock calls and split by ordered events. Per-pump flush and periodic sync
retain useful prefixes. `recording.incomplete` persists through crashes or
write/flush/sync/close failure; only successfully finalized files remove it.
Event/state files cap at 128 MiB each, preserving a replayable incomplete prefix
when reached. Larger full captures and stronger power-loss publication are
future work. Mutable settings are fingerprinted and rejected if changed;
automatic restoration and future save startup are not implemented.

## Verification

- All four SDL/X11 Debug/ASan builds pass without warnings. Logger-off SDL and
  C-only runtime-options-off scaffold builds pass too.
- Debug and ASan replay contracts pass two million ordered clock calls, runs
  beyond 65,536 polls, repeated keys, cursor/time/Sleep services, first-field
  divergence, malformed input, schema/identity rejection, event/state checksums,
  truncated tails and unpublished completion. SHA-256 is cross-checked with
  Python hashlib. Final logs: `/tmp/e2-replay-contract-{debug,asan}-check.log`.
- Lifecycle checks pass with the logger on and off: abrupt SIGKILL, partial final
  CSV row, an old source actually removed by startup retention after freezing,
  no nested/probe recording and forced disk-write failure while gameplay stays
  alive. Logs: `/tmp/e2-replay-lifecycle-{debug,no-log}.log`.
- The final **Debug intro/menu** route passes three fresh-process replays and a
  fourth through GDB with a two-second pause: **11 inputs, 20 checkpoints,
  590,652 clock calls in 26 clock rows, 1,518,280 total recording bytes**. Fresh
  runs take about 0.82–0.84 s; the paused run takes 2.97 s. This is overlapping
  arrow/repeat/release delivery within a modal menu, not player displacement.
  Evidence: `/tmp/e2-replay-delivery-final/report.json` and its capture/play/pause
  logs. The exported `/tmp/e2-replay-bundle-final` also replays successfully;
  SHA256SUMS, read-only file modes, stop sequence and stop checkpoint pass.
- A synthetic five-million-real-clock-read benchmark takes 0.090–0.091 s without
  recording versus 0.096–0.097 s with recording: about **6–7% producer overhead**,
  4,589–4,680 event bytes. This excludes whole-game/checkpoint overhead. Source
  `/tmp/e2-replay-clock-bench.cpp`, logs `/tmp/e2-replay-clock-bench-{1,2,3}.log`.
  An earlier over-frequent checkpoint prototype grew about 5 MiB in four seconds;
  periodic checkpoints now use 1,024 pump intervals, plus input transitions.
  Repeats/mouse motion stay lossless without full snapshots per repeat/pixel.
- Existing logger contracts pass normally/ASan, including RT pools, native stacks,
  priority/masks, leases and retention. Developer launch checks pass **30 + 30**
  cases; real retention checks pass Debug/ASan. Evidence uses
  `/tmp/e2-replay-launch-*-check.log`, `/tmp/e2-replay-retention-*.log`.
- Runtime baseline and all eight control rows pass:
  `/tmp/e2-replay-regressions.log`, `/tmp/e2-replay-controls.log`.
  Original-i386 frame-clock comparisons pass all **560** cases through 100,000
  unchanged polls, normally/ASan: `/tmp/e2-replay-frame-clock{,-asan}.log`.
- Actual native `.vscode/launch.json` Debug and ASan launches pass eight-second
  observations both with agent recording disabled and with `--record auto`
  explicitly testing human F5 capture. Both automatic launches produce replay
  files. Reports: `/tmp/e2-replay-vscode-auto-{debug,asan}.json` and associated
  adapter/console logs. These are startup/capture observations, not gameplay
  acceptance. The human launch configuration remains unchanged.

## Fidelity Frontier — Do Not Hide It

Broader movement replay is **not accepted**. One early populated attempt first
mismatched actor 77's X by one unit; later attempts diverged in service ordering
or RNG state after matching checkpoint 15. A read-only GDB RNG audit confirms
that RNG call placement differs before the differing seed; it does not establish
which unrecovered game input causes it. Evidence:
`/tmp/e2-replay-rng-audit/{record,play}-rng.json` and logs,
`/tmp/e2-replay-route-debug7/play-0.log`. A longer route also reaches the existing
reconstructed `FUN_0042db74` actor-target crash. No gameplay repair is included.

The ASan intro/menu attempt reports an expected-clock/actual-cursor-get mismatch
after matching checkpoint 12 (`/tmp/e2-replay-menu-asan/play-0.log`). ASan library,
recovery, logging and native-launch checks do not supersede this replay failure.
`scripts/check-e2-replay.py --released-player --background-spawns` retains the
broader failing gate; it is not silently relaxed into a successful replay.

The current tool distinguishes a matching sampled prefix from divergence,
interruption, rejection and native crashes. It does not yet prove that a human's
full movement route or memory-corruption crash repeats. The next bounded replay
investigation is the first differing game path/RNG-call placement after the last
matching checkpoint, using read-only debugger observations and the retained
recordings. Full script interpreter serialization, save/load, workshop walking
re-entry, sword pickup and full experimental ASan remain separate work.
