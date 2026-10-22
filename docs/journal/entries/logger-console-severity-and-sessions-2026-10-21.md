# Logger Console Severity And Sessions — 2026-10-21

The user confirmed the native F5 crash fix, then requested the new logger on the console with severity, colors and sessions under `~/.ecstatica2`. The prior integration still printed through the old C timestamp wrapper and mirrored diagnostics into a file-only C++ sink.

## Implementation

The C wrapper now formats stderr diagnostics and assembles fragmented `fprintf`/`vfprintf` calls into C++ logger records. It does not print a separate console copy. The logger owns stderr and file sinks, both carrying timestamp, module and severity. Severity prefixes retain warning/error/fatal/debug/trace meaning; unprefixed legacy messages remain Info, `failed to ...` is Error, and recoverable file-open failures are Warning. Typed logger calls retain their explicit severity. Console colors default on, including when captured by a debugger; nonempty `NO_COLOR` disables them. File output always excludes ANSI escapes. Level/module filters apply to both sinks. Before bootstrap and in C-only builds, ordinary stdio remains available.

The bridge now reuses `SessionRetention` and `Paths` from `feature/logger`, adding the formerly unused session source to its CMake target. Each launch creates `logs/session_YYYYMMDD_HHMMSS_mmm/` beneath the resolved runtime output root, with `session.meta` JSON and rotating 5 MiB `e2recomp_*.log` files. Session metadata records the PID, local/UTC creation time, build type and retention/rotation settings. Session creation uses exclusive directory creation and retries collisions so simultaneous launches cannot silently share a directory. Failure to create the log directory or metadata fails bootstrap.

The existing startup retention policy preserves at least ten previous sessions and removes older sessions only when their total size exceeds 128 MiB. Existing flat logs remain untouched. The game-data directory and generated reconstruction are unchanged.

## Controlled Exit Regression

The first control/baseline run exposed missing final `input state:` records: probe threads call `_exit`, so their newly asynchronous console records could be discarded before the consumer wrote them. A shared native probe-exit helper now submits any partial diagnostic and stops/drains the logger before `_exit`. All eight controlled probe exits use it. The launch checks now assert the final input state in both console and session output, and assert Error severity for an intentional dump failure. This addresses controlled exits; asynchronous logging does not guarantee delivery after a crash or debugger termination.

## Verification

- All four SDL/X11 Debug/ASan preset builds pass. C-only stub and runtime-options-disabled logging paths compile.
- `check-e2-developer-launch.py`: **22 cases per build**, **44 total**, pass for SDL Debug and SDL ASan. Covers session metadata/isolation, colored console and plain files, `NO_COLOR`, invalid-level Warning, warning-only filtering, Error records, fragmented messages, hard-exit final records, retention using disposable sparse files, debugger exit, overrides and startup failures. Evidence: `/tmp/e2-session-launch-final-{debug,asan}/`.
- Actual `.vscode/launch.json` runs through the installed cppdbg adapter on native Wayland remain running for **30.10 seconds (Debug)** and **30.16 seconds (ASan)** without stop/crash events. These create default sessions under `/home/rgrabowski/.ecstatica2/logs/`. Reports: `/tmp/e2-session-vscode-{debug,asan}.json`, with corresponding `.jsonl` and adapter logs. The adapter probe does not capture inferior console output; console formatting is checked separately by the developer-launch cases.
- Runtime wrapper and all **eight** control matrix rows pass after the controlled-exit repair: `/tmp/e2-session-final-regression-check.log`, `/tmp/e2-session-final-controls-check.log`.
- `git diff --check` passes. The index remains empty and unchanged; all work is unstaged, with no commit made.

Route recording/replay and the existing manual workshop/pickup/full experimental ASan acceptance remain outside this change.
