# Debugging the reconstructed runtime

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

The debugging tools connect recorded input, engine state, game frames and native
failures. Use `scripts/e2-debug.py --help` for the command inventory. All commands
run locally; original game assets remain in their external installation.

The [gameplay regression suite](gameplay-tests.md) runs bounded fresh-input
journeys and original-code comparisons with dependency-aware reports. Select
the **starred full regression suite** for all configured Debug/ASan cases, or a
separate block launch with automatic prerequisites. Debug/ASan run concurrently;
the display picker defaults to headless and can show either configuration or
both windows. Each configuration runs its journeys sequentially. Use the
ordinary gameplay launch for human F5 investigation.

## Game sound diagnostics

Normal **Ecstatica Recompiled** F5 gameplay now opens SDL audio on the system
playback device. Settings sound off/on retains original request gating; existing
samples finish naturally. Music output remains deferred. Human listening and
broader event/device coverage remain qualified in the
[sound recovery journal](journal/entries/game-sounds-recovery-2026-10-29.md).

For bounded agent probes, `E2R_AUDIO=off` disables device output,
`SDL_AUDIODRIVER=dummy` exercises consumption without speakers, and
`E2R_AUDIO_TRACE=1` reports original sample identity, length, volume and playback
result. `E2R_AUDIO_TAP=/absolute/new-file.s16` captures signed 16-bit little-endian
stereo mixer output at 22,050 Hz, capped at 8 MiB; it never overwrites an existing
file. Audio callbacks own copied PCM and never drive deterministic game state.
Audio mode/tap/trace are host-only replay settings; game checkpoints and sound
request identities remain strict.

## Normal gameplay investigation in VS Code

Use the existing **Ecstatica Recompiled** launch with the SDL/i386 Debug preset.
F5 explicitly enables `E2R_RECORD=auto` and `E2R_INSPECT=1` alongside the established
cylinder/action/population options. A separate capture command is unnecessary
for ordinary human gameplay investigation. F5 clears an inherited `E2R_REPLAY`
value so a normal launch starts fresh gameplay.

The debugger observes one silent startup boundary, pins `/proc/PID/exe` and saves
source/build context under `logs/session_<id>/investigation/`. This pins the image
actually running even if a build replaces the selected executable path. Signal
and breakpoint stops append bounded thread backtraces, registers and replay
progress to `debugger.log`; the debugger remains stopped for normal inspection.
Silent message/fatal-requester entry observations also save call stacks, even if
replay recording has already filled up. Their bounded receipt copies use
`.requester.log` beside the F5 index; these are observations, not proof of a crash.
A signal stop is distinguished from process termination.

When debugging ends, the **Ecstatica: Finalize gameplay investigation** task
generates `investigation/report.html` and final session metadata. A debugger-exit
hook also attempts finalization. The task skips other active sessions, so parallel
launches retain their own leases. If VS Code/GDB is forcibly killed, the raw
session remains useful; rerun the finalization task to process pending closed
sessions. A partial recording/inspection remains explicitly incomplete.

The newest five sessions always survive ordinary cleanup; older sessions have
a separate 2 GiB budget. F5 also creates `investigation.keep` before gameplay and
keeps it after a signal or unsuccessful/unknown exit.
These protected investigations remain until reviewed/exported and their marker
is explicitly removed. Observed clean exits release their marker automatically, with incomplete capture still reported separately.
Signal stacks also have a bounded copy beside their workspace index receipt in
`.tmp/f5-investigations/`. Finalization reports incomplete capture and marks
missing indexed sessions expired instead of returning a stale success path.

Export an important run before releasing its marker:

```sh
python3 scripts/e2-debug.py bundle /absolute/session \
    /absolute/session/investigation/e2recomp /tmp/e2-bug
```

The export includes the F5 investigation artifacts and debugger output. Source
context is a startup snapshot, while the executable hash identifies the binary;
context alone is not proof that every file produced that image. Terminal launches
keep inspection opt-in. F5 now retains the default five-second startup logo
waits. Regression probes present each logo and use separate SDL Space taps;
[gameplay tests](gameplay-tests.md#controlled-population-and-startup-logos) explain
the natural-wait option and the original-code/replay limits.

## Health and potion observation

Normal F5 starts with the recovered original HUD. **F1** selects original HUD;
**F2** selects the diagnostic overlay, including a bottom **HEALTH** panel with
**POISON / INVISIBILITY** status. Health is Joe's actual signed value; **HEALING**
appears during his health-effect action. Potion indicators observe current
actions and their scheduled expiry/death records, using **NONE, PENDING, ACTIVE,
FADING**. They do not predict random potion contents or establish original mesh
effects. In F2 mode the panel hides during modal menus and remains visible when Joe is
offscreen. Visibility packets include the corresponding `player_status` row;
status codes are 0/1/2/3 in the order above. See the
[health/status evidence](journal/entries/diagnostic-health-and-potion-status-2026-10-24.md).

Exact replay includes recorded RNG outcomes, so repeating a recording selects
the same potion branch. To exercise different random outcomes, repeat a fresh
input route and record the actual selected branch. A full-health pickup does
not prove healing; the
[random-potion review](journal/entries/random-potion-outcomes-2026-10-24.md)
separates those checks.

## Capture an investigation from the terminal

```sh
python3 scripts/e2-debug.py capture build/Debug/clang21-i386-sdl/e2recomp \
    /tmp/e2-investigation --gdb --timeout 90
python3 scripts/e2-debug.py verify /tmp/e2-investigation
```

The destination must be new. This starts the diagnostic cylinder route with
normal intro timing, population enabled, replay recording and inspection. Play
normally, close the game, or let the timeout end the observation. `--dummy` uses
dummy SDL video/audio for unattended investigation. `--game-data PATH` overrides
the executable's configured original installation. Native i386 and GDB execution
need the same host/ptrace permissions as existing runtime probes.

The bundle contains the pinned executable (including its embedded debug
information), session logs, replay, inspection, debugger output, source context
and available CMake build configuration. With `--gdb`, a native stop includes all
thread backtraces and registers. A timeout is recorded separately from a signal.
Source context identifies the working tree at export time; it does not establish
that every context file produced the binary. The executable hash pins that binary.

Files and directories are published read-only with a recursive `SHA256SUMS` and
manifest. Verification detects missing, changed and extra files. If export fails,
the raw capture is retained in the reported `.e2-capture-*` directory beside the
destination. Bundles sit outside automatic session retention. Non-replay evidence
is bounded to 256 MiB per file and 768 MiB total. Replay exports include all
manifest-listed chunks and recoverable tails without that aggregate cap;
original game assets remain external.

Export an existing **inactive** session with its matching executable:

```sh
python3 scripts/e2-debug.py bundle /absolute/session /absolute/matching-e2recomp /tmp/e2-bug
python3 /tmp/e2-bug/tools/replay-e2.py run /tmp/e2-bug/executable/e2recomp \
    /tmp/e2-bug/session/replay --timeout 120
```

An executable/hash mismatch or an active session lease rejects the export. An
incomplete replay remains incomplete in the bundle; export never changes its
acceptance status. Preserve separately split debug files yourself if using a
build that does not embed its debug information.

## Inspect state and frames

Actor observations include `health`, `water_capable` and `archive_offset`.
World observations include `terrain_type`, `map_height_shift` and
`swimming_scene_flags`. These are inspection-only fields, so adding them leaves
replay checkpoint sampling unchanged. The [water-entry investigation](journal/entries/water-entry-and-player-resource-2026-10-23.md)
shows why health and original resource identity matter even when the process
exits cleanly. Agent motion probes write sessions beneath `<output>-runtime`.

Enable inspection on an ordinary launch or while replaying:

```sh
E2R_INSPECT=1 ./build/Debug/clang21-i386-sdl/e2recomp --run-recon
python3 scripts/replay-e2.py run build/Debug/clang21-i386-sdl/e2recomp \
    /absolute/session/replay --inspect --data-dir /tmp/e2-replay-investigation
```

Inspection writes `inspection/` within the ordinary log session. F5 enables it;
terminal launches can opt in with the environment variable above. It
works with the logger disabled, and is disabled with runtime options disabled.
Use a session directory, its `inspection/` directory, or a bundle's `session/`
directory as the inspection source:

```sh
python3 scripts/e2-debug.py timeline /absolute/session --limit 20
python3 scripts/e2-debug.py timeline /absolute/session --kind input_before --after 10
python3 scripts/e2-debug.py state /absolute/session --actor 0
python3 scripts/e2-debug.py state /absolute/session --snapshot 3 --scope script
python3 scripts/e2-debug.py diff /absolute/session 2 3
python3 scripts/e2-debug.py diff /absolute/session 2 3 --other /absolute/other-session
python3 scripts/e2-debug.py report /absolute/session /tmp/e2-inspection.html
```

CLI results are JSON. The self-contained HTML report provides an event slider,
searchable state table and the nearest preceding retained game frame. It needs
no web server. Its destination must be new. Cross-run differences compare chosen
snapshots; the investigator must establish that those snapshots represent the
same gameplay event. `script.last_cursor_address` is a diagnostic process address
and is unsuitable as a portable identity.

Observations include actor positions/orientations, actions and progress,
representation/scene IDs, active update order, input bytes, camera, RNG state,
script wait/modal state, requester ID, last script opcode/cursor and attachment ownership.
Message requesters publish a `requester` event before entering their blocking loop
and request the next presented frame; actor updates are not required to observe them.
They sample script state; they do not trace every interpreter instruction or
serialize all script state. Terrain-query internals remain available through
`scripts/probe-e2-player-motion.py --trace-queries` and its original-code fixtures.

`timeline.csv` distinguishes event ID, expanded replay sequence, last matching
replay checkpoint, actor-update ID, presentation ID and inspection snapshot ID.
Actor-update boundaries surround the existing `FUN_0042a70c` call. They do not
assert a fixed simulation frequency or equate updates with presentation frames.
`state.csv` stores the initial state and subsequent changed/deleted fields;
deletion removes absent actors and released input entries from reconstructed
inspection state. State rows flush before their timeline reference. Reading an
active capture shows only complete published observations.

SDL captures at sampled camera/action changes, the first presentation, periodically,
and after F12 bookmarks when the next presentation occurs. Captures retain the
converted game image including diagnostic cylinders, without the resizable
desktop/window margins. Old frame files are evicted; earlier timeline/state
observations remain searchable. Capture never forces a presentation or pumps
additional input, so a fast replay may produce fewer images than a normal run.
The existing F12 multi-surface packet remains available independently.

| Setting | Default | Bound |
| --- | --- | --- |
| `E2R_INSPECT=1` | off | Normal `--run-recon` only |
| `E2R_INSPECT_INTERVAL` | 30 | Sample first/every N actor updates, before and after the update |
| `E2R_INSPECT_FRAME_INTERVAL` | 30 | Capture every N successful presentations, plus event triggers |
| `E2R_INSPECT_MAX_FRAMES` | 20 | Retain last N frames; maximum 100, each at most 640 by 480 |

Input transitions and F12 bookmarks also sample state. Timeline/state output is
bounded to 32 MiB combined. Reaching the limit or an I/O failure stops inspection
and leaves `inspection.incomplete`; gameplay continues. A crash also leaves that
marker. The reader recovers newline-published prefixes and rejects malformed
complete rows. Inspection flushes do not claim power-loss durability.

Inspection settings are excluded from replay startup identity. Existing replay
schema/checkpoint checksums are unchanged. A completed inspection means the
observational writer closed; replay completion and gameplay acceptance remain
separate checks. The observer reads state without invoking reconstructed
projection helpers, writing game state or calling game-visible clocks.

## Compare original functions

`scripts/e2_original.py` supplies a bounded PE32/i386 loader, production-function
extraction and fixture compilation. `scripts/e2_original_fixture.h` supplies a
register-input/output trampoline and first-byte memory difference reports. The
trampoline supports register-only calls; stack arguments require an explicit
fixture adapter. Original x86 code and recovered C run in the same isolated
fixture process with dependency interceptions stated by that fixture.

The detach/caller and motion-query fixtures now use the shared framework:

```sh
python3 scripts/check-e2-attachment-detach.py /path/to/E2WIN95.EXE --keep-harness /tmp/detach.c
python3 scripts/check-e2-motion-query.py /path/to/E2WIN95.EXE --keep-harness /tmp/motion.c
```

Repeat with `--asan`. Retained harnesses receive a `.fixture.json` sidecar with
the original executable hash, original code ranges, harness hash, compiler,
sanitizer setting and intercepted dependencies. These comparisons prove the
tested function contracts under those dependencies; real-map traversal has its
own acceptance gate. Other existing fixtures remain independent and can adopt
the framework incrementally.

For a dormant scripted object, the motion probe's explicit asset fixture can
install and start its authored scene with `--inspect-object-scene ID
--inspect-load-scene --inspect-start-scene`. It calls original scene installation
and activation, then bounds the selected-camera preview. This can run scripted
children and authored poses; it is separate from ordinary-input traversal and
natural event acceptance. Omit `--inspect-start-scene` for a visibility-only
preview of an already active/static scene.

## Debug backward

```sh
python3 scripts/e2-debug.py capabilities
python3 scripts/e2-debug.py reverse /tmp/e2-bug /tmp/e2-reverse \
    --backend gdb --function FUN_0042db74 --ignore 0
python3 /tmp/e2-reverse/launch.py
```

The prepared launcher restores the replay environment and stops at the selected
function before enabling GDB `record full`. Continue or step within that window;
then use `reverse-next`, `reverse-stepi` or a watchpoint with `reverse-continue`.
Record only the suspected window: instruction support, recorded-history limits
and external device effects constrain GDB process recording. See the
[GDB process recording manual](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Process-Record-and-Replay.html).

An optional `rr` pilot records the pinned bundle replay in a fresh process:

```sh
python3 scripts/e2-debug.py reverse /tmp/e2-bug /tmp/e2-rr --backend rr --timeout 120
```

`rr` must already be installed. The command retains its log, trace directory and
process result outside session retention. Check the log for recorder failures;
replaying the resulting trace establishes host compatibility. Native CPU/kernel
and ptrace requirements still apply. This environment currently lacks `rr`;
the GDB recording-window path has a verified i386 reverse-write pilot. See
[rr usage](https://github.com/rr-debugger/rr/wiki/Usage).

## Gate recorded gameplay routes

```sh
python3 scripts/e2-debug.py scenario /absolute/matching-e2recomp \
    /absolute/session/replay scripts/scenarios/intro-menu.json /tmp/e2-scenario
```

Each scenario combines recorded input with explicit state/event expectations.
The checked-in example expects camera 175, Joe loaded, and delivered Up press
and release. It applies to the intro/menu route produced by
`scripts/check-e2-replay.py`; it does not establish player traversal.

Scenario JSON schema `e2debug.scenario.1` accepts `assertions` and `events`.
Assertions identify `scope`, `entity_id`, `field`, optional `name`, and `when`:
`eventually`, `always`, `final`, or `changes`. Comparisons support `eq`, `ne`,
`ge`, `le`, with `value`; `changes` requires distinct observed values. An optional
`from_snapshot` narrows the observation interval. Missing fields fail comparisons,
including `always`/`final`. Events select `kind` and optionally `a`/`b`.

Success requires all expectations, native replay exit zero and a completed
inspection. Crashes, timeouts, rejected/divergent replay and incomplete prefixes
fail even if earlier observations met expectations. `--compatible` explicitly
attempts a changed executable while retaining strict replay checks. Outcome
assertions cover sampled observations, not continuous state between samples.
Fresh-route traversal remains available through existing motion probes; accepting
new movement/pickup recordings requires their own route evidence.

## Find recovery evidence and diagnostics

```sh
python3 scripts/e2-debug.py recovery --function FUN_0042db74
python3 scripts/e2-debug.py recovery --limit 10
python3 scripts/e2-debug.py diagnostics build/Debug/clang21-i386-sdl \
    --function FUN_00415d40 --limit 20
```

Recovery queries connect original addresses, current C signatures/lines,
referenced fixtures, journals, generator mentions and unresolved register
placeholders. The ranked inventory uses placeholder counts as investigation
hints. Textual references do not prove coverage or correctness. It also identifies
missing local links in the active implementation and replay documentation.

Diagnostics uses the selected build's `compile_commands.json`, enabling targeted
Clang warnings in a syntax-only pass. It leaves normal build flags and generated
source unchanged. Use the warnings to investigate original calling conventions;
initializing decompiler placeholders arbitrarily would conceal the missing
contract. New data layouts and arithmetic should follow original-code evidence.

## Console gameplay detail

Frequent `42b004` action events and `42ad60` action completions are
`Runtime.Actor` Trace records. Session files retain them at Trace level, while
the console hides them by default. Set `E2R_GAMEPLAY_CONSOLE_VERBOSE=1` and keep
the Trace threshold to show them in the console. Input summaries and critical
messages keep their existing behavior. Recording-failure notices are warnings.

## Large recordings and missing message text

Replay events and checkpoints now rotate into 16 MiB CSV files with an ordered,
checksummed manifest. Recording continues beyond the former 256 MiB ceiling.
The reader validates into anonymous temporary disk files and plays sequentially,
keeping memory independent of the recording's total length. Older single-file
recordings remain readable. Export/inspection tools include all chunks; disk
failures still retain incomplete status and continue gameplay. See the
[storage/recovery contract](replay.md#physical-storage) and
[fresh Debug/ASan evidence](journal/entries/chunked-recording-and-streaming-replay-2026-10-28.md).

An empty/unreadable game message now shows "Internal game error. See the session
log." and emits an Error with native call-site evidence. This is a hosted
presentation fallback; it preserves the caller's existing modal/exit behavior.
It is not acceptance of the unrecovered caller or proof that its exit was repaired.

## Verify the tools

```sh
python3 scripts/check-e2-inspection.py
python3 scripts/check-e2-inspection.py --asan
python3 scripts/check-e2-debug-tools.py --native
python3 scripts/check-e2-f5-investigation.py --native
python3 scripts/check-e2-empty-requester.py
python3 scripts/check-e2-directional-reaction.py /path/to/E2WIN95.EXE
python3 scripts/check-docs-tree-contracts.py
python3 scripts/check-docs-tree.py
python3 scripts/check-e2-replay.py build/Debug/clang21-i386-sdl/e2recomp --inspect
```

Repeat the final command with the ASan executable. The inspector regression
records a real SDL menu route, checks independent replays with inspection on/off,
and repeats after a debugger pause. Add `--inventory --character-meshes` to include
a released-player Enter/Escape status-page transition; `--chunk-bytes 65536`
also exercises chunk rotation on that bounded route. Existing replay parser/lifecycle tests and
runtime/control regressions remain separate gates.

<!-- docs-tree:children -->
## Related documents

- [Ecstatica Runtime Logger](../src/log/include/Log/README.md)
<!-- /docs-tree:children -->
