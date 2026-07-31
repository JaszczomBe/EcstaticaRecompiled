#pragma once

#if !defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
#error "Log/Test/RTTestHooks.h is available only when UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS is enabled."
#endif

#include <cstdint>

namespace Ecstatica::Recompiled::Log::Test
{
    // Snapshot of test-only counters used to verify RT-path behavior without
    // exposing production internals. This header is compiled only when
    // UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS is enabled in the tests build.
    struct RTTestHooksSnapshot
    {
        // Counts any call to Waiter::StopWait(). RT logging must not increment
        // this because StopWait() goes through a mutex/condition_variable path.
        uint64_t waiterStopWaitCalls   = 0;
        // Counts entry into Logger::LogRealtime(), regardless of outcome.
        uint64_t realtimeAttempts      = 0;
        // Counts RT records accepted onto the queue.
        uint64_t realtimeEnqueued      = 0;
        // Counts RT records rejected on the producer path.
        uint64_t realtimeDropped       = 0;
        // Narrower subset of realtimeDropped for messages that exceed the
        // bounded inline RT message buffer.
        uint64_t realtimeOversizeDrops = 0;
    };

    // Reset counters between test phases so one assertion does not depend on
    // previous logger traffic in the same binary.
    void                ResetRTTestHooks();
    // Read a stable snapshot of the current counters for assertions.
    RTTestHooksSnapshot GetRTTestHooksSnapshot();
}
