#pragma once

#include <atomic>
#include <functional>
#include "Log/Core/Record.h"

namespace Ecstatica::Recompiled::Log
{
    inline std::function<bool(const Record&)> KeepOneInN(unsigned n)
    {
        if (n < 2)
            return [](const Record&) { return true; };

        auto counter = std::make_shared<std::atomic<uint32_t>>(0);
        return [counter, n](const Record&) -> bool
        {
            return (counter->fetch_add(1, std::memory_order_relaxed) % n) == 0;
        };
    }
}
