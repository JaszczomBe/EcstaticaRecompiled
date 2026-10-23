# Gameplay recording and replay

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

For correlated state/frame inspection, native crash bundles, reverse-debugging
launchers and recorded-route assertions, see [Debugging the reconstructed
runtime](debugging.md). `E2R_INSPECT=1` adds a separate observational capture;
`scripts/replay-e2.py run ... --inspect` enables it during replay. Inspection
settings do not enter replay identity or change the CSV replay schema.

Normal SDL `--run-recon` and human F5 launches record automatically in
`<data-dir>/logs/session_<id>/replay/`. `--data-dir` overrides `E2R_DATA_DIR`;
the default remains `~/.ecstatica2`. Logging filters do not control recording.
Logger-off builds retain sessions, leases, retention and recording. Builds with
runtime options disabled retain the original C-only scaffold, without replay.

```sh
./e2recomp --record auto --run-recon
./e2recomp --record off --run-recon
./e2recomp --replay /absolute/session/replay --run-recon
```

Options precede the command. Environment equivalents are `E2R_RECORD=auto|off`
and `E2R_REPLAY=/absolute/session/replay`. Explicit CLI values win. Replay never
records another replay, although it creates ordinary diagnostic logs. Probe
commands default off; agent launch helpers explicitly use `E2R_RECORD=off`.
The human `.vscode/launch.json` retains the automatic policy. No GDB detection
is used to classify a launch.

Use the runner to restore the recorded environment and game-data location in a
fresh process. Direct CLI replay instead requires matching startup environment.

```sh
python3 scripts/replay-e2.py run build/Debug/clang21-i386-sdl/e2recomp \
    /absolute/session/replay --timeout 120 --data-dir /tmp/e2-investigation
python3 scripts/replay-e2.py run build/Debug/clang21-i386-sdl/e2recomp \
    /absolute/session/replay --stop-before 100000
python3 scripts/replay-e2.py inspect /absolute/session/replay
python3 scripts/replay-e2.py export /absolute/session/replay /absolute/bug-bundle
```

Native stop controls are `--replay-stop-before SEQUENCE` and
`--replay-stop-checkpoint ID`. `E2R_REPLAY_PAUSE=1` raises SIGSTOP at that
boundary for debugger attachment; continuing then exits with status 76. Inspect
`E2R_replay_sequence` and `E2R_replay_last_checkpoint`, or break on replay API
functions. The sequence expands individual clock calls inside compressed runs.
F11 or closing the physical window aborts replay. F12 remains a visibility tool;
neither F12 transition is gameplay input. Physical gameplay messages are drained
and suppressed during replay, including while expanding long clock runs.

## Status and current acceptance

The [water-entry capture](journal/entries/water-entry-and-player-resource-2026-10-23.md)
reproduces the user's post-death menu exactly with its pinned executable. The
repair restores Joe's resource, so compatible replay now stops at sequence
21,659 / last matching checkpoint 11. Fresh input-driven Debug/ASan routes prove
water survival and forward swimming separately; they do not claim an old-capture
checkpoint match.

- **0 / MATCHED:** all recorded ordered calls and sampled checkpoints matched;
  a clean completion marker was reached. This verifies the sampled route, not
  every byte of game memory or causality of a crash.
- **73 / REJECTED:** malformed/unsupported input or incompatible startup state.
- **74 / DIVERGED:** first service/order/field mismatch; output gives the sequence,
  expected/actual field or service, and last matching checkpoint.
- **75 / INCOMPLETE:** the recoverable prefix ended or completion was unpublished.
- **76:** stopped before the requested boundary. **77:** physical abort.
- Native crashes/signals remain native crashes. The bounded runner also reports
  timeout separately; neither establishes successful replay.

The **Debug and ASan intro/menu** routes each pass three fresh-process replays
and a replay with a two-second debugger pause, retaining overlapping arrow
presses, repeated keydown and releases. These are menu inputs; they do **not**
establish matching player traversal.

A fresh **Debug intro/NPC crash** capture now reaches SIGSEGV in three fresh
replays. A paused GDB replay verifies the same `FUN_0042db74` stack, sequence
475,145,280 and last matching checkpoint 16 as its capture. This is an incomplete
crash recording, not a clean `MATCHED` completion. The original human recording
remains preserved and divergent when attempted with the repaired executable;
compatible mode does not conceal that difference. See the
[recovery evidence and local bug bundle](journal/entries/replay-npc-input-and-crash-boundary-recovery-2026-10-22.md).
That bundle pins the pre-fix executable. The native detach crash was
[subsequently repaired and tested through natural intros without replay](journal/entries/natural-intro-attachment-detach-2026-10-22.md).

A separate [post-pedestal callback recording](implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md#callback-contract), pinned to `2e6c7e1`'s executable hash, reproduces the reported `FUN_0043cac0 ← FUN_00414e68 ← FUN_0044f508 ← FUN_0044f310 ← FUN_00426ca4` stack by exact replay at sequence 890,925,953/checkpoint 47. The repaired executable's explicit compatible attempt returns from all four callbacks, then exits **75/INCOMPLETE** at the recorded prefix end with no divergence. This establishes passage through that failure boundary, not a clean replay completion. The export and matching executable are preserved separately in `.tmp/replay-bugs/post-pedestal-20261022*`.

The recovery fixes lost NPC coordinate/facing/actor inputs against original
instructions, separately from recorder scheduling. Replay never writes physics,
random values, script state or positions. RNG seed/LCG arithmetic are unchanged.
Full movement routes, future save/load and full experimental ASan remain open;
the broader populated movement probe currently reaches the native crash while
recording and therefore does not pass its clean-route gate.

X11 still builds and passes existing input regressions, but automatic capture is
SDL-only: the existing X11 backend has no equivalent release fidelity. Initial
exact replay requires the same executable hash, backend, assets and startup
configuration. `--replay-compatible` permits executable/build/revision differences,
while keeping startup environment and checkpoint comparisons strict. This is an
attempt, including for rebuilt/ASan binaries, rather than a compatibility promise.

Original 1996 assets remain an external fixed installation: identify the original
executable by SHA-256 and archive filenames/sizes, without copying or rehashing
all archives every launch. Any root `e_config`/`E_CONFIG` present is fingerprinted;
changed settings are rejected and must currently be restored manually. Save/load
reconstruction and automatic restoration of mutable settings are separate work;
metadata explicitly identifies fresh-process startup, never a savestate.

## CSV schema 1

Files use UTF-8-compatible text, LF record endings, decimal integers and ordinary
CSV quoting (double embedded quotes, quote commas and newlines). No JSON payloads,
process pointers, native window handles or wall-clock scheduling are used. There
is one logical game window, `1:main`, declared in metadata.

`metadata.csv` has `key,value` rows: schema `e2replay.csv.1`, recording/session ID,
UTC correlation time, executable SHA-256, build-time revision/dirty marker,
backend/build/ASan flags, game command arguments, relevant environment, original
asset identity and startup settings identity. The executable hash identifies the
actual dirty build; `revision` alone is descriptive.

`events.csv` columns:

```text
seq,repeat,kind,pump,message_or_result,wparam,lparam,cursor_x,cursor_y,value_5,value_6,value_7,detail
```

The eight numeric columns following `pump` are named for input; service rows use
them in the documented order below. Unused numeric fields are zero. `repeat` is
one except clock runs. A run covers `[seq, seq+repeat)`, at most 65,536 calls;
the next row starts at that exclusive end. Repeated keydowns remain distinct
input rows. Ordering is global, including nested and empty host pumps.

| kind | Numeric values / detail |
| --- | --- |
| `clock` | First value: exact unsigned 32-bit game-visible millisecond result. `timeGetTime` delegates once to the same recording boundary. |
| `localtime` | Eight SYSTEMTIME words: year, month, weekday, day, hour, minute, second, millisecond. |
| `pump_begin`, `pump_end` | Unique increasing pump ID, with checked nesting; no input is required. |
| `input` | Delivered message, exact wParam (virtual key/button where applicable), lParam, game-space X/Y. Host cursor side effects precede the window procedure. |
| `queued` | Message/wParam/lParam at queued dispatch; verified against the game's normal queue, rather than injected twice. |
| `cursor_set`, `cursor_get` | First two values: game-space X/Y. |
| `sleep` | First value: requested milliseconds; replay keeps the same pump slices without requiring wall-time sleep. |
| `checkpoint` | First value: checkpoint ID; second: field count. Detail: SHA-256 of its canonical CSV state rows. |
| `end` | First value: final recorded checkpoint ID. Sequence is the final event sequence. Detail: SHA-256 of all preceding canonical event rows, including the header. |

`checkpoints.csv` columns are
`checkpoint_id,scope,entity_id,field,value`. Snapshots contain simulation counters,
Joe by actor ID zero, camera data, nonzero held/queued input bytes, active update
order, loaded actor poses/actions/flags, script-scene children/modal state and
active RNG state. Resource references become IDs. Hashes cover named fields and
canonical IDs, excluding addresses and padding. Hash mismatch and per-field
comparison are both enforced. This is a useful world signature, not a complete
serialization of all script interpreter state.

The observation point is the outer host-pump entry before input, periodically
at pump 1 and every 1,024 pumps, and before input transitions. Pure repeated
keydown and mouse-motion events remain lossless without full snapshots per
repeat/pixel. Input checkpoints also occur immediately before those deliveries
inside a pump. Both capture and replay follow that exact boundary; it is not
asserted to be a completed simulation update or a presentation boundary. The
adapter reads fields directly and calls no reconstructed projection functions.

## Recovery, retention and limits

The writer is synchronous and buffered; there is no dropping producer queue.
Clock runs are bounded and end before intervening ordered records. Snapshot rows
are flushed before their event reference. Event/state buffers flush at pump exit.
The first clock result and the first result at each changed millisecond value
also flush before returning to the game: a changed result can release a busy-wait
directly into a faulting update. Equal-result suffixes remain run-length encoded
and can still be lost before publication. Filesystem synchronization runs at
pump exits roughly once per real second and at completion. Other buffered tails
can be lost, especially without a following pump. Only completed newline-terminated rows are recoverable; an
unfinished final row is excluded. Malformed complete rows, gaps, missing referenced
state and invalid checksums are rejected, not skipped. Event/state files are currently bounded
to 256 MiB each (metadata 1 MiB at preparation); reaching the capture limit marks
recording incomplete and retains the usable prefix. Parsing freezes the input
in memory. Larger complete captures require a future streaming-reader change.

`recording.incomplete` remains present while active, interrupted or failed.
Successful event/state sync and close plus a clean `end` precede its removal.
Write/flush/sync/close failure leaves this marker and gameplay continues. SDL
shows **RECORDING INCOMPLETE** in the window title and cylinder overlay. Absence of
`end`, or presence of this marker, never produces a matching completion. These
are process-crash recovery guarantees; power-loss durability additionally depends
on directory publication and filesystem behavior. No whole-file compression is
used, so valid prefixes remain inspectable.

Recording and logs share one session lease and the 60-second maintenance
policy. The newest five sessions are always kept. Older sessions have a separate
2 GiB byte budget; all their regular artifact bytes count. Active sessions and
F5 `investigation.keep` markers remain protected even above the budget. See
[current retention settings](building.md#runtime-logging). Before any startup
cleanup, replay takes retention serialization and the inactive source lease,
freezes all inputs, then releases those locks. Cleanup may subsequently remove
the original session; playback owns the frozen copy. Active captures are rejected
as replay sources. Export creates a fresh read-only bundle with SHA256SUMS outside
automatic session cleanup; it excludes the original game assets.

Tests:

```sh
cmake --preset linux-clang32-sdl-debug -DE2R_REPLAY_BUILD_TESTS=ON
cmake --build --preset linux-clang32-sdl-debug --target e2recomp e2r-replay-contract
python3 scripts/check-e2-replay-contracts.py build/Debug/clang21-i386-sdl/src/replay/e2r-replay-contract
python3 scripts/check-e2-replay-lifecycle.py build/Debug/clang21-i386-sdl/e2recomp
python3 scripts/check-e2-replay.py build/Debug/clang21-i386-sdl/e2recomp
# Broader, currently unaccepted movement/population gates:
python3 scripts/check-e2-replay.py build/Debug/clang21-i386-sdl/e2recomp --released-player --background-spawns
```

Use native i386/ptrace permission for these checks. Repeat contracts/builds with
ASan and logger disabled. Workshop walking re-entry, sword pickup, save/load and
full experimental ASan acceptance remain independent.
