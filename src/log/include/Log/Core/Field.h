#pragma once
#include <string_view>

namespace Ecstatica::Recompiled::Log
{
    // Owned by the queued payload before the producer returns.
    struct Field
    {
        std::string_view key;
        std::string_view value;
    };
}
