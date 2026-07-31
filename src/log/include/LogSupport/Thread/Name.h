#pragma once
#include <cstdint>
#include <string>

namespace Ecstatica::Recompiled::LogSupport::Thread::Name
{
    bool SetThreadName(const std::string& name);
    void ClearCurrentThreadName();
    // Returns cached thread name if set, otherwise best-effort query from OS for current thread.
    // Returns empty string if unavailable.
    const std::string& GetThreadName();

    // Lookup a recorded name for a thread id as returned by Ecstatica::Recompiled::LogSupport::Thread::ThisThreadId().
    // Returns an empty string when unknown.
    std::string GetThreadNameById(uint64_t thread_id);
}
