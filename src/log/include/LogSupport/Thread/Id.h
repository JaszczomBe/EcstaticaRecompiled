#pragma once

#include <cstdint>

namespace Ecstatica::Recompiled::LogSupport::Thread
{
    // Stable logger-facing thread identifier based on hashing std::thread::id.
    uint64_t ThisThreadId();
}
