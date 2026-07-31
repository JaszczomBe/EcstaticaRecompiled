# Common Log

Ecstatica Recompiled's adapted logger is an asynchronous, structured, sink-based logging system intended for normal threads and mixed realtime/non-realtime applications.

This file is the canonical documentation for the logger surface, behavior, and maintenance constraints.

The logger's operational target is to avoid blocking the program, especially on realtime-sensitive threads. Current implementation details still fall short of that target in some areas, but new work should preserve and improve that direction rather than move away from it.

## Read First

1. Include [`LogWrite.h`](src/client/core/src/common/include/Log/LogWrite.h) in normal `.cpp` files that only emit logs.
2. Include [`LogSetup.h`](src/client/core/src/common/include/Log/LogSetup.h) only in bootstrap or configuration code that starts, stops, or reconfigures the logger.
3. Use [`Modules/Module.h`](src/client/core/src/common/include/Log/Modules/Module.h) when a translation unit has one primary module.
4. [`Log.h`](src/client/core/src/common/include/Log/Log.h) remains as a compatibility umbrella, but it is no longer the recommended include for new code.
5. Use [`StreamLogToggle.h`](src/client/core/src/common/include/Log/StreamLogToggle.h) only as an adjacent debugging utility, not as the main structured logger API.

## What The Logger Does

The main logger provides:

- asynchronous multi-producer, single-consumer delivery
- separate high-priority handling for `Error` and `Fatal`
- multiple sinks
- level filtering
- module and submodule filtering
- structured `key=value` fields
- optional stack capture
- runtime reconfiguration
- statistics for drops and queue depth

The main logger does not provide nested object logging, JSON output, or arbitrarily deep structured payloads. Structured data is currently flat: each field is one `key=value` pair.

## Operational Requirements

The intended runtime behavior is:

- producer-side submission should avoid blocking normal program execution
- producer-side submission must not block realtime threads
- expensive formatting, filtering decisions, sink I/O, and other heavy work should happen on the consumer thread whenever ownership and lifetime rules allow it
- when the implementation cannot yet meet the ideal producer-path cost, the gap should be documented as technical debt rather than treated as acceptable steady-state behavior

Current note:

- formatted message construction now goes through one internal logger formatting shim, which removes direct backend coupling from the public macros and prepares later producer-path optimizations
- formatted strings are still materialized on the producer path today

## Design Overview

The stable design model is:

- `Logger` is a singleton asynchronous logger
- producers submit from many threads into multi-producer single-consumer queues
- one background consumer thread drains records and fans them out to sinks
- `Error` and `Fatal` records use a separate high-priority queue and are drained before the normal queue
- runtime filtering happens on the consumer thread, not on producer threads
- `Fatal` bypasses all runtime filtering
- `Error` bypasses runtime level filtering and rate limiting, but still respects module and submodule masks

Record model:

- a `Record` carries level, module, submodule mask, message, source location, thread id, sequence number, timestamps, optional fields, and optional callstack
- structured fields are intentionally flat `key=value` metadata
- the logger copies message and field storage during submission so short-lived caller data is acceptable for the duration of the call
- nested object logging and schema-aware structured payloads are out of scope

Public surface shape:

- `LogWrite.h` is the preferred call-site surface for code that only emits logs
- `LogSetup.h` is the preferred setup surface for startup, shutdown, sinks, and runtime reconfiguration
- `Log.h` remains a compatibility umbrella include
- `Logger` keeps a PIMPL boundary so setup headers do not expose queue, worker-thread, or synchronization internals

Formatting and sinks:

- sinks are the formatting and output boundary
- sinks receive already-filtered records from the single consumer thread
- formatting shape is sink-controlled rather than hard-coded in `Logger`
- formatted-message backend selection is compile-time and CMake-driven: prefer `std::format`, fall back to `fmt::format`

## Include And Bootstrap

Normal call sites that only emit logs should start from the write-only include:

```cpp
#include "Log/LogWrite.h"

using namespace Ecstatica::Recompiled::Log;
```

Minimal setup:

```cpp
#include "Log/LogSetup.h"

void InitLogging()
{
    Config cfg;
    cfg.globalLevel = Level::Info;
    cfg.queueCapacity = 8192;
    cfg.hiQueueCapacity = 1024;

    auto& logger = Logger::Instance();
    logger.Start(cfg);
    logger.AddSink(std::make_shared<StdoutSink>());
}
```

Shutdown:

```cpp
Logger::Instance().Stop();
```

When no explicit runtime level is supplied, the logger keeps the build default global level:

- debug builds default to `Trace`
- release builds default to `Info`

Application bootstrap may override that default by passing a resolved `Config::LoggingConfig` slice into the logger bootstrap path.

Formatted message backend selection is compile-time and CMake-driven:

- prefer `std::format` when the active toolchain supports it correctly
- fall back to `fmt::format` when `std::format` support is insufficient
- logger call sites use one internal formatting shim rather than including backend-specific formatting headers directly

## Severity Roles

Severity assignment matters. The logger's filtering behavior is designed around the assumption that levels are used consistently.

- `Trace`: very high-volume execution detail for bring-up, callbacks, and step-by-step flow analysis
- `Debug`: developer-oriented diagnostics that are useful during investigation but not expected in normal operations
- `Info`: significant normal lifecycle events such as startup, configuration, resource selection, and state transitions
- `Warning`: abnormal but tolerated conditions where the system continues with degraded quality, fallback behavior, or possible future trouble
- `Error`: correctness or functionality failure where a requested operation did not succeed or an important capability is unavailable
- `Fatal`: unrecoverable condition after which the process cannot continue correctly and termination or immediate abort is expected

Severity policy in the current logger:

- `Trace` through `Warning` use the normal queue and follow the full runtime filter chain
- `Error` uses the high-priority queue, respects module and submodule masks, but bypasses runtime level filtering and rate limiting
- `Fatal` uses the high-priority queue and bypasses all runtime filtering so it is always emitted

Practical rule:

- do not use `Error` for routine retries, expected misses, or noisy transient states
- do not use `Fatal` unless continuing execution is no longer a valid option

## Quick Start

If one file belongs to one module, declare it once near the top of the `.cpp`:

```cpp
#include "Log/LogWrite.h"

using namespace Ecstatica::Recompiled::Log;

UT_MODULE(ModuleID::Runtime_Player);

void StartPlayback(const std::string& trackName, int sampleRate)
{
    UT_LOGM(Level::Info, "Playback starting");
    UT_LOGM_FMT(Level::Info, "Opened track {} at {} Hz", trackName, sampleRate);
}
```

Typical final output in `StdoutSink`:

```text
[2026-04-03 12:44:51.128][Runtime.Player][INFO] Playback starting
[2026-04-03 12:44:51.129][Runtime.Player][INFO] Opened track intro.wav at 48000 Hz
```

If you do not use `UT_MODULE`, log with an explicit module:

```cpp
Logger::Instance().Log(Level::Info,
                       ModuleID::Assets_Manager,
                       UT_SRC_LOC,
                       "Asset database ready");
```

Example output:

```text
[2026-04-03 12:44:51.140][Assets.Manager][INFO] Asset database ready
```

## Why `UT_MODULE` Matters

`UT_MODULE(moduleId)` is not technically required, but it is strongly recommended when one translation unit primarily belongs to one module.

It gives you:

- shorter call sites via `UT_LOGM*`
- consistent module assignment across the file
- less copy-paste risk than repeating `ModuleID::...` everywhere
- a natural place to define submodule-tagged logs

Placement guidance:

- place it once in the `.cpp`, near includes or near the start of the file
- do not put it in headers unless the header intentionally owns logging for a single compiled context
- do not use it in mixed-responsibility files where logs clearly belong to different modules

## Macro Matrix

The current macro names are compact but easy to confuse. Use them this way:

- `UT_LOG`: plain message, explicit module
- `UT_LOG_FMT`: formatted message, explicit module
- `UT_LOGF`: plain message plus structured fields, explicit module
- `UT_LOGF_FMT`: formatted message plus structured fields, explicit module
- `UT_LOG_STACK`: plain message plus explicit stack capture request
- `UT_LOG_STACK_FMT`: formatted message plus explicit stack capture request
- `UT_LOG_MASK`: plain message with explicit submodule mask
- `UT_LOG_MASK_FMT`: formatted message with explicit submodule mask

The `M` variants are the same API but use `UT_CURRENT_MODULE_ID` from `UT_MODULE`:

- `UT_LOGM`
- `UT_LOGM_FMT`
- `UT_LOGM_F`
- `UT_LOGM_F_FMT`
- `UT_LOGM_STACK`
- `UT_LOGM_STACK_FMT`
- `UT_LOGM_MASK`
- `UT_LOGM_MASK_FMT`

Realtime-safe variants:

- `UT_RT_LOG`: fixed-size preallocated RT path, explicit module, plain message
- `UT_RT_LOG_FMT`: fixed-size preallocated RT path, explicit module, bounded text formatting
- `UT_RT_LOG_MASK`: RT path with explicit submodule mask
- `UT_RT_LOG_MASK_FMT`: RT path with explicit submodule mask and bounded text formatting
- `UT_RT_LOGM`: RT path using `UT_MODULE`
- `UT_RT_LOGM_FMT`: RT path using `UT_MODULE` with bounded text formatting
- `UT_RT_LOGM_MASK`: RT path using `UT_MODULE` and submodule mask
- `UT_RT_LOGM_MASK_FMT`: RT path using `UT_MODULE`, submodule mask, and bounded text formatting

Rule of thumb:

- choose `*_FMT` when the message is assembled from values
- choose `*F*` when you want flat `key=value` fields attached
- choose `*_STACK*` when the stack itself is part of the diagnostic value
- choose `*_MASK*` when the log should be filterable by submodule
- choose `UT_RT_*` only on realtime-sensitive threads when you need the explicit no-allocation / no-blocking path and can stay within the RT formatting limits

## Compile-Time And Runtime Filtering

Two different filters exist.

### 1. Compile-time macro gate

The macros check `UT_LOG_MIN_LEVEL`.

- Debug builds default to `Trace`
- Release builds default to `Info`

That means a `Trace` log compiled out by `UT_LOG_MIN_LEVEL` will never reach the runtime logger, even if runtime config is set to `Trace`.

### 2. Runtime logger policy

At runtime the consumer thread applies:

1. module allow/deny mask
2. submodule allow/deny mask
3. global level, per-module override, or resolver result
4. rate limiter

Severity-specific exceptions:

- `Error` still passes through module and submodule filtering, then bypasses runtime level filtering and rate limiting
- `Fatal` bypasses all runtime filtering and is always emitted

This is why compile-time and runtime level confusion can happen. If a log does not appear, check both.

## Integration Guidance For `src/*`

Use the closest `Ecstatica::Recompiled::Log::ModuleID` value for runtime integrations.

Safe with the normal logger:

- high-level runtime bootstrapping
- host-backend diagnostics outside callbacks that must stay layout-sensitive
- file-open and asset-path diagnostics

Use the RT-safe path only after per-call-path review:

- timing or helper code reachable from frame-critical paths
- audio callbacks or future mixer plumbing
- synchronization or queue-adjacent plumbing

Do not integrate the main logger into:

- `src/log` internals, sinks, formatting, bootstrap, and control-plane code
- scheduler, queue, and lock-free plumbing that would couple logger behavior back into itself
- thread-priority setup and RT context plumbing where normal logger calls would violate the call-path contract
- `ScopeTimer` or similar timing helpers used from RT-sensitive code

Guardrails:

- decide by call path, not by directory name
- do not replace existing RT-adjacent `sLOG` or stdio with normal `UT_LOG*` unless the path is proven non-RT
- do not add logger self-logging inside logger internals
- treat RT logging as bounded but still non-free; use it for state transitions and rare diagnostics, not hot-path chatter

## Structured Fields

Structured fields are flat metadata appended to the message as `key=value`.

Example:

```cpp
Record::Field fields[] = {
    {"asset", "intro.wav"},
    {"phase", "decode"},
    {"retry", "2"},
};

UT_LOGM_F(Level::Error, "Failed to decode resource", fields, 3);
```

Typical output:

```text
[2026-04-03 12:45:07.201][Runtime.Player][ERROR] Failed to decode resource asset=intro.wav phase=decode retry=2 [src/client/core/src/player/src/Player.cpp:88]
```

Capabilities today:

- flat list of fields
- arbitrary field count per record
- caller can provide stack or no stack independently from fields
- fields are copied by the logger during submission, so temporary caller storage is acceptable for the duration of the call

Limitations today:

- fields are one-dimensional only
- there is no nested structure, arrays, maps, or typed storage
- values are stored as strings or string views, not as strongly typed schema values
- output formatting is `key=value`, not JSON

If you need multi-dimensional information, flatten it explicitly:

- `voice.id=12`
- `voice.state=paused`
- `stream.buffer.fill=73`

That keeps filtering and grep-friendly diagnostics simple.

## `FMT` Versus Fields

`FMT` and structured fields solve different problems.

- `FMT` shapes the human-readable message
- structured fields attach stable machine-readable context

Best practice:

- put the main story in the formatted message
- put dimensions you may want to grep or compare in fields

Example:

```cpp
Record::Field fields[] = {
    {"track", trackName},
    {"sample_rate", "48000"},
    {"device", deviceName},
};

UT_LOGM_F_FMT(Level::Info,
              fields,
              3,
              "Opened track {} on device {}",
              trackName,
              deviceName);
```

Typical output:

```text
[2026-04-03 12:45:16.040][Audio.Startup][INFO] Opened track intro.wav on device EcstaticaDevice track=intro.wav sample_rate=48000 device=EcstaticaDevice
```

## Rate Limiting

Rate limiting exists because some logs are valuable individually but disastrous in volume.

Typical cases:

- per-frame logs
- per-audio-callback logs
- rapidly repeating error storms
- state logs inside a hot polling loop

Without rate limiting, these logs:

- drown out the useful events
- increase queue pressure
- increase dropped-log risk for other logs
- make file logs noisy and expensive

The supplied helper is `KeepOneInN(n)`.

Example:

```cpp
auto limiter = KeepOneInN(10);

Config cfg;
cfg.rateLimit = [limiter](const Record& rec)
{
    if (rec.module == ModuleID::Runtime_Player)
        return limiter(rec);
    return true;
};
```

Meaning:

- keep every 10th matching record
- drop the rest

Practical guidance:

- start with rate limiting only on known hot-path spam
- prefer submodule-based targeting instead of globally throttling everything
- do not rate limit rare correctness-critical logs such as startup failures, configuration errors, or asset validation failures

Current severity interaction:

- rate limiting applies to records that reach the normal runtime filter chain
- `Error` bypasses rate limiting after passing module and submodule masks
- `Fatal` bypasses rate limiting entirely

## Queue Sizes

The logger has two queues:

- `queueCapacity`: normal queue for `Trace`, `Debug`, `Info`, `Warning`
- `hiQueueCapacity`: high-priority queue for `Error`, `Fatal`

Good starting values:

- desktop debug build: `queueCapacity = 8192`, `hiQueueCapacity = 512` or `1024`
- desktop release build: `queueCapacity = 4096` to `8192`, `hiQueueCapacity = 256` to `512`
- constrained/mobile build: start smaller, for example `2048` and `256`, then measure drops

Increase queue sizes when:

- stats show frequent drops during short bursts
- startup or asset loading legitimately emits large temporary log bursts
- file or console sinks are intentionally verbose and you want to absorb bursts

Decrease queue sizes when:

- memory footprint matters more than log retention
- logs are already well filtered and the queue never fills
- you want misconfigured log storms to fail fast rather than consume more memory

Operational rule:

- if `droppedTotal` rises during normal expected behavior, the queue is probably too small or the logging policy is too noisy
- `droppedRealtime` is a subset of `droppedTotal` counting only drops from the RT-safe path; if it rises, the RT node pool (fixed at 256 nodes with 256-byte message buffers) is exhausted or the main queue was full when the RT path tried to enqueue — widen whichever limit applies
- if queue depth stays near zero and memory is tight, the queue may be larger than needed

Overflow behavior:

- `DropNew`: reject the new record immediately when the target queue is full
- `DropOldest`: request consumer-side eviction of the oldest queued record; this is best-effort and the current record may still be dropped

Realtime rule:

- producer submission is non-blocking for realtime and non-realtime threads in the current implementation
- if a queue is full, the record is either accepted immediately or dropped according to the non-blocking overflow path

## Module And Submodule Filtering

Modules are coarse ownership buckets. Submodules are finer-grained tags inside a module.

### Static Module Registration

`ModuleID` is static by design. If a new ownership domain needs logging, add a new enum value and a matching canonical entry in `MODULE_NAMES`.

Example setup:

```cpp
namespace PlayerLog
{
    static constexpr SubmoduleMask AudioCallback = MakeSubmoduleMask(0);
    static constexpr SubmoduleMask Streaming     = MakeSubmoduleMask(1);
    static constexpr SubmoduleMask SceneLoad     = MakeSubmoduleMask(2);

    inline void RegisterSubmoduleNames(FormatOptions& fo)
    {
        fo.submoduleNames[ModuleID::Runtime_Player] = {
            {AudioCallback, "AudioCallback"},
            {Streaming, "Streaming"},
            {SceneLoad, "SceneLoad"},
        };
    }
}
```

Logging with submodules:

```cpp
UT_MODULE(ModuleID::Runtime_Player);

UT_LOGM_MASK(Level::Trace, PlayerLog::AudioCallback, "audio tick");
UT_LOGM_MASK(Level::Info, PlayerLog::Streaming, "network refill complete");
UT_LOGM_MASK(Level::Warning, PlayerLog::SceneLoad, "missing optional ambient stem");
```

Typical output:

```text
[2026-04-03 12:46:02.111][Runtime.Player::AudioCallback][TRACE] audio tick
[2026-04-03 12:46:02.250][Runtime.Player::Streaming][INFO] network refill complete
[2026-04-03 12:46:02.401][Runtime.Player::SceneLoad][WARN] missing optional ambient stem
```

Runtime filtering example:

```cpp
Logger::Instance().SetModuleMask(ToMask(ModuleID::Runtime_Player) |
                                     ToMask(ModuleID::Assets_Manager),
                                 0);

Logger::Instance().SetSubmoduleMask(ModuleID::Runtime_Player,
                                    PlayerLog::Streaming | PlayerLog::SceneLoad,
                                    PlayerLog::AudioCallback);
```

Meaning:

- only `Runtime_Player` and `Assets_Manager` are allowed globally
- for `Runtime_Player`, allow `Streaming` and `SceneLoad`
- for `Runtime_Player`, deny `AudioCallback`
- `Error` logs still obey these module and submodule decisions
- `Fatal` logs bypass them and are always emitted

### `Config::LoggingConfig` Ownership

Logger control is now documented around `Config::LoggingConfig`, not `Cmd::Settings`.

Ownership model:

- `Config` owns neutral logging inputs such as `logLevel`, `disableLogModules`, and `disableSubmoduleFiltering`
- `Cmd` may parse CLI flags into `Config::LoggingConfig`, but it should not be the logger's runtime ownership boundary
- the application composition root resolves config, then bootstraps the logger from the app aggregate's `logging` slice

Current bootstrap surface:

```cpp
void Bootstrap(std::string_view level,
               std::string_view modules,
               bool disableSubmoduleFiltering,
               void (*configureFormat)(FormatOptions&));
```

Typical app-level wiring:

```cpp
void ApplyLoggingConfig(const RuntimeLoggingConfig& logging)
{
    Bootstrap(logging.logLevel,
              logging.disableLogModules,
              logging.disableSubmoduleFiltering,
              nullptr);
}
```

That keeps command parsing, settings files, platform input, and app-specific bootstrap concerns outside the logger core while still giving one app-level place to turn noisy channels on and off.

## Stack Capture And Realtime Context

Stack capture can be requested explicitly through `UT_LOG_STACK*` or enabled automatically for `Warning`, `Error`, and `Fatal` in `Config`.

Current implementation detail:

- stack capture is skipped if `RealtimeContext::IsRealtimeThread()` returns true — this is a thread-local flag set by `MarkRealtimeThread()` or `RealtimeContext::Scope`, not inferred from which logging macro was used
- threads that are audio-adjacent but not registered as RT will still call `backtrace()` on `Error` and `Fatal`; only raw addresses are captured on the producer thread — symbolization via addr2line or atos happens in the sink on the consumer thread
- the logger now consults [`RealtimeContext.h`](src/client/core/src/common/include/LogSupport/Thread/RealtimeContext.h)

Recommended usage:

```cpp
Ecstatica::Recompiled::LogSupport::Thread::RealtimeContext::Scope realtimeScope;
```

`Logger::MarkRealtimeThread()` remains available as a compatibility wrapper, but the shared `RealtimeContext` scope is now the authoritative marker.

## Realtime-Safe Logging

The logger now exposes a dedicated realtime-safe write path through `UT_RT_*` macros.

Current contract:

- fixed-size preallocated node pool
- fixed-size message copy buffer
- no structured fields
- no stack capture
- bounded `FMT` support only for static text plus bare `{}` placeholders
- RT format arguments are limited to string-like values and `char`
- if the pool is exhausted, the queue is full, the message is too long, or the RT format shape is unsupported, the record is dropped immediately

This path is intentionally narrower than the normal logging API. Those limits are what make the no-allocation and no-blocking guarantee credible.

## Output Formatting And Sinks

Available sinks:

- `StdoutSink`
- `StderrSink`
- `FileSink`
- `AndroidSink`

Formatting supports:

- human or epoch time
- local or UTC timezone
- module and optional submodule naming
- optional thread id
- optional thread name
- optional sequence number
- source file and line
- color
- optional rendered stack

`Error` and `Fatal` always force source location into formatted output.

`FileSink` behavior:

- writes to one file when `keep <= 0`
- rotates numbered files when `keep > 0`
- can flush immediately on `Error` and `Fatal`

Example:

```cpp
FormatOptions fmt;
fmt.humanTime = true;
fmt.includeThreadName = true;
fmt.includeStack = true;
fmt.includeSource = false;
PlayerLog::RegisterSubmoduleNames(fmt);

auto sink = std::make_shared<StdoutSink>();
sink->SetFormatOptions(fmt);
Logger::Instance().AddSink(sink);
```

Typical output:

```text
[2026-04-03 12:46:40.553][audio][Runtime.Player::Streaming][INFO] network refill complete
```

## `StreamLogToggle.h`

[`StreamLogToggle.h`](src/client/core/src/common/include/Log/StreamLogToggle.h) is a small file-local debugging utility for temporarily suppressing raw `std::cout`, `std::cerr`, and `std::clog` usage.

It gives you:

- `UT_COUT`, `UT_CERR`, `UT_CLOG`
- `UT2_COUT`, `UT2_CERR`, `UT2_CLOG`

Usage:

```cpp
#define UT_DISABLE_STREAM_LOG
#include "Log/StreamLogToggle.h"

UT_COUT << "disabled in this file\n";
UT2_CERR << "still enabled unless UT_DISABLE_STREAM_LOG_2 is also defined\n";
```

Why this is useful:

- quickly silence ad-hoc stream spam in one `.cpp`
- keep debug stream statements in place without deleting them
- isolate one noisy stream channel while leaving another enabled

This utility is valuable during bring-up, debugging, and temporary instrumentation, but it is not a replacement for the structured logger.

## Current Assumptions And Verified Limitations

- `Logger` must be started before normal use.
- `Submit()` now follows a non-blocking producer path
- when queues are full, `Submit()` follows the configured overflow policy and returns `false` if the record is ultimately dropped
- `Error` and `Fatal` use the high-priority queue
- `Error` bypasses runtime level filtering and rate limiting, but still respects module and submodule masks
- `Fatal` bypasses all runtime filtering
- config changes are applied asynchronously on the consumer thread
- `DropOldest` is best-effort consumer-side eviction, not a guarantee that the current record will be preserved
- structured fields are flat only
