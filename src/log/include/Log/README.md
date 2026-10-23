# Ecstatica Runtime Logger

<!-- docs-tree:parent -->
[Project README](../../../../README.md) · [Parent: Debugging the reconstructed runtime](../../../../docs/debugging.md)
<!-- /docs-tree:parent -->

The runtime uses the C API in `EcstaticaLogBridge.h`. C++ instrumentation can use
`Log/Log.h`, formatted macros and module/submodule masks. The logger owns message,
field and deferred argument storage before submission returns.

## Outputs and sessions

Bootstrap installs stderr and file sinks. Both include severity, module/tag and
producer timestamps. Stderr uses severity colors unless `NO_COLOR` is nonempty;
files contain plain text. The C runtime resolves the output root before entering
the original game-data directory, defaulting to `~/.ecstatica2`.

Each run creates `logs/session_YYYYMMDD_HHMMSS_mmm/` with `session.meta`, an active
lease file and rotating `e2recomp_*.log` files. Rotation creates a fresh file at
5 MiB and does not overwrite older chunks. Metadata schema 2 records PID,
creation times, build type, rotation size and retention limits.

Retention runs at startup and periodically on its own maintenance thread:

| Environment setting | Default |
| --- | --- |
| `E2R_LOG_MAX_SESSIONS` | 100 |
| `E2R_LOG_MAX_TOTAL_MB` | 128 |
| `E2R_LOG_CLEANUP_INTERVAL_SECONDS` | 60 |

Values must be positive integers. Oldest completed sessions are removed until
both caps are met; there is no minimum-session floor overriding the budget.
Active sessions are protected by OS-managed leases, automatically released even
after a crash or debugger kill. The filesystem wrapper implements leases on
POSIX and Windows. Older sessions without leases are protected while their saved
PID is alive. Concurrent session creation and cleanup share a root lock.

The budget includes active sessions, but active sessions are never deleted.
If active data alone exceeds the caps, cleanup reports the overrun and retries
at the next interval. Legacy flat files, unrelated directory names and symlinked
session directories are excluded. Each launch always creates a fresh directory;
a completed session is never reactivated.

## Severity, masks and priority

Levels are Trace, Debug, Info, Warning, Error, Fatal and Off. The build default
threshold is Trace for Debug builds and Info for Release builds. Runtime CLI/env
options select the threshold and module deny-list.

- **Error and Fatal bypass every severity threshold**, including compile-time
  `UT_LOG_MIN_LEVEL=Off`, per-module levels, runtime Off and rate limiting.
- Error respects module and submodule masks; Fatal bypasses those masks too.
- Error/Fatal use the priority queue. The consumer checks it between ordinary
  records, so critical events can overtake older ordinary messages.
- Record wall/monotonic timestamps and sequence numbers are assigned on the
  producer. Use them to reconstruct chronology; file order reflects priority.
- Queue depth and dropped-record counters remain available through `GetStats`.
  An asynchronous queue is bounded and does not guarantee delivery on a crash.

Module and submodule masks, per-module thresholds, module tag registration,
rate limiting and formatted field records remain available through `Logger`.
Startup installs sinks with `ReplaceSinks`; live sink add/remove and generic
format mutation APIs are intentionally absent.

## C++ instrumentation

```cpp
#include "Log/Log.h"
using namespace Ecstatica::Recompiled::Log;

UT_MODULE(ModuleID::Actor);
UT_LOGM_FMT(Level::Debug, "Actor {} changed state to {}", actorId, state);
UT_LOGM_MASK_FMT(Level::Debug, MakeSubmoduleMask(0), "Position {} {}", x, z);
UT_LOGM_STACK(Level::Error, "Actor initialization failed");
```

`UT_LOG`/`UT_LOG_FMT` accept an explicit module. `UT_LOG_MASK` and
`UT_LOG_MASK_FMT` also accept a submodule mask. `UT_LOGF`/`UT_LOGF_FMT` attach
key/value fields, copied during submission. `UT_LOG_STACK` requests a stack
explicitly. `UT_LOGM_*` variants use the module declared by `UT_MODULE`.
Formatted normal-path macros use the configured C++20 `std::format` backend.

Input summaries use `Runtime.Input` at Debug, with one pressed record, one held
record on the first repeat, and one released record per delivered virtual key.
Additional repeats do not suppress game input. Protocol details require
`E2R_INPUT_DIAG_VERBOSE=1`. Missing sound archives use `Runtime.MissingSound` at
Trace. See `docs/building.md` for runtime options and input diagnostics.

## Native callstacks

Normal-path Error/Fatal records automatically capture the originating thread's
native stack. `Config` also supports warning stacks and explicit stack requests.
Capture happens on the producer; function/source resolution and rendering happen
on the consumer. POSIX source resolution uses `addr2line` on Linux and `atos` on
macOS. Source locations and raw addresses remain available when resolution fails.
Debug symbols are required for source lines.

## Real-time producers

`LogRealtime`, `UT_RT_LOG*`, and `UT_RT_LOGM*` retain the bounded pool and deferred
formatting path. Mark callback threads with `LogSupport::Thread::RealtimeContext::Scope`.
The producer avoids heap allocation, callstack capture and mutex/condition-variable
wakeups. The consumer polls for this traffic.

The pool has 256 nodes; each holds a message up to 256 bytes. Deferred formatting
accepts up to four string-like/char arguments in 192 bytes of copied argument
storage. Supported placeholders are `{}` and escaped braces. Use static format
string literals. Argument text is copied before returning; non-string formatting
remains on the normal path. Pool/queue exhaustion rejects the record and
increments drop counters.

## Shutdown and checks

The runtime flushes partial C diagnostic lines and stops session maintenance
before draining/stopping the logger. Controlled probe exits do this before
`_exit`; debugger kills rely on OS lease release, not graceful logger delivery.
The C-only stub remains available when `E2R_ENABLE_LOGGER=OFF`.

Build focused checks in an isolated directory:

```sh
cmake --preset linux-clang32-sdl-debug -B /tmp/e2-log-check -DE2R_LOG_BUILD_TESTS=ON
cmake --build /tmp/e2-log-check --target e2r-log-contract
/tmp/e2-log-check/src/log/e2r-log-contract /tmp/e2-log-check-artifacts
```

Use fresh artifact directories. `E2R_LOG_BUILD_TESTS` enables the RT test hooks
only in that build. Checks cover critical filtering/macros, masks, queued field
ownership, native source stacks, priority, RT allocations/wakeups/pool reuse,
deferred argument lifetime, append-only rotation and retention leases/budgets.
`scripts/check-e2-log-retention.py EXE` checks real-process periodic cleanup,
concurrent sessions, legacy active PIDs and lease release after a killed process.
