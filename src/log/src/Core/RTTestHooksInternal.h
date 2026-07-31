#pragma once

#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)

#include <atomic>
#include <cstdint>

namespace Ecstatica::Recompiled::Log::Test
{
    // Internal storage for RT test counters. This state is intentionally kept
    // out of the production public API and exists only in test-enabled builds.
    struct RTTestHooksState
    {
        std::atomic<uint64_t> waiterStopWaitCalls{0};
        std::atomic<uint64_t> realtimeAttempts{0};
        std::atomic<uint64_t> realtimeEnqueued{0};
        std::atomic<uint64_t> realtimeDropped{0};
        std::atomic<uint64_t> realtimeOversizeDrops{0};
    };

    // Shared singleton-like access point used by the logger and Waiter test
    // instrumentation sites.
    RTTestHooksState& AccessRTTestHooksState();
}

#endif
