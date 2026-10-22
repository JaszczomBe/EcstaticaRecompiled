# Logger Cleanup And Bounded Session Maintenance — 2026-10-21

The user approved a narrowed cleanup after clarifying the required capabilities: retain real-time pools/deferred formatting, macros and module/submodule masks, native callstacks, filesystem wrappers and capped periodic retention. Error/Fatal must bypass severity thresholds and take priority over ordinary records; chronological reconstruction uses producer timestamps and sequence numbers.

## Removed And Preserved

Removed Kotlin throwable IDs/extraction/rendering; Android, stdout and Undertone E2E sink source/headers; unused app lifecycle/stream helpers; obsolete cached `data/logs` path helpers; unused polymorphic task/count scaffolding; live sink add/remove/format-mutation APIs; and the unused module-level resolver callback. Normal structured fields remain supported and owned by queued records. The logger guide now describes the actual runtime rather than the imported application.

Retained C and C++ entry points, formatted/field/stack macros, module registration and masking, per-module thresholds, rate limiting, asynchronous priority queues, RT pools and deferred argument capture, native POSIX source symbolization and filesystem wrappers. RT test hooks use the project-specific `E2R_LOG_ENABLE_RT_TEST_HOOKS` name; parity helper names no longer refer to Kotlin. The simplified named worker still runs the existing consumer callback. C++20 formatting and i386 multilib checks remain intact.

The logger inventory decreased from **73 files / 7,457 lines** to **64 files / 6,122 lines**, including documentation and the new C++ contract checks. Ten unused files were removed and one contract source was added. Reconstructed game code and the generator are unchanged.

## Critical Records And Callstacks

The existing runtime Error/Fatal bypass is preserved. Compile-time macro guards now honor it even when `UT_LOG_MIN_LEVEL=Off`. Error still respects module/submodule masks; Fatal bypasses them. The consumer also checks the priority queue between normal records: an error arriving during a normal batch no longer waits for the entire batch to finish. A record already being written is not interrupted.

Producer wall/monotonic timestamps and sequence numbers remain intact when priority reorders output. Native stacks are still captured at the originating logging call and resolved/rendered by the consumer. The focused fixture verifies a real function name and its `contract.cpp` source location in the formatted log.

## Retention

Defaults are **100 sessions**, **128 MiB**, and **60-second cleanup intervals**, with startup cleanup too. Positive integer overrides are `E2R_LOG_MAX_SESSIONS`, `E2R_LOG_MAX_TOTAL_MB` and `E2R_LOG_CLEANUP_INTERVAL_SECONDS`. Both count and byte budgets apply; the former minimum-session floor no longer overrides the caps. File rotation remains append-only at 5 MiB, with the unused destructive numbered ring mode removed.

The filesystem wrapper now supplies cross-process file leases and file synchronization using POSIX/Windows branches. Each active session holds `session.active.lock`; the OS releases it on clean exit, crash or debugger kill. A root `.retention.lock` serializes creation and cleanup. Older sessions without leases remain protected while their recorded PID is alive. Closed sessions cannot be reactivated. Cleanup ignores symlinked session directories, unrelated directory names and legacy flat files.

A maintenance worker scans off the producer path and stops before logger shutdown. It removes oldest completed sessions until both budgets are met. Active sessions remain protected even when active data alone exceeds the budget; that condition is logged and retried periodically. Metadata schema 2 records the current limits without the obsolete device/minimum/update fields. Windows branches are implemented but were not executed in this Linux verification.

## Verification

- All four SDL/X11 Debug/ASan preset builds pass without compiler warnings.
- **60 developer launch cases** pass: 30 for SDL Debug and 30 for SDL ASan, including existing compact input transitions, colors, session files, precedence and controlled-exit records, plus invalid retention settings and Error output while severity is Off. Evidence: `/tmp/e2-cleanup-final-launch-{debug,asan}/` and corresponding `-check.log` files.
- Optional `E2R_LOG_BUILD_TESTS` builds `e2r-log-contract` in isolated Debug/ASan directories. Both pass critical filtering across all seven thresholds, compile-time formatted macro bypass, Error/Fatal mask policy, priority ordering, queued field ownership, native function/source stacks, RT deferred argument ownership, no RT producer allocations or waiter wakeups, pool exhaustion/reuse, append-only rotation, active leases, hard budgets below ten sessions and symlink exclusion. Evidence: `/tmp/e2-cleanup-final-contracts-{debug,asan}-check.log`.
- The allocation-counting test initially needed matching sized-delete overloads for ASan. Its fixture was corrected; the final ASan run passes with no checks disabled.
- `check-e2-log-retention.py` passes for both SDL executables using real concurrent processes: periodic deletion of a completed session, active/legacy PID protection, and cleanup after an intentionally killed process releases its lease. Evidence: `/tmp/e2-cleanup-final-retention-{debug,asan}-check.log`.
- Runtime baseline wrapper and all **eight** control rows pass: `/tmp/e2-cleanup-final-regressions-check.log`, `/tmp/e2-cleanup-final-controls-check.log`.
- Actual native `.vscode/launch.json` startup is checked through the installed cppdbg adapter for Debug and ASan. Reports: `/tmp/e2-cleanup-final-vscode-{debug,asan}.json`, with corresponding event/adapter logs. These establish bounded startup, not manual gameplay acceptance.
- The earlier staged work remains byte-for-byte unchanged: staged patch SHA-256 `39afd42a01c9692264ce1678e99824ee4a3ae00780e4aa53e9d5812b024c54e7`. This cleanup remains unstaged; no commit is made.

Recorder/replayer implementation and manual workshop re-entry, sword pickup and full experimental ASan acceptance remain separate work.
