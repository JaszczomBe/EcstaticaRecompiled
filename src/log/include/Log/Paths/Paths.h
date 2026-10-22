#pragma once

#include <string>
#include <string_view>

namespace Ecstatica::Recompiled::Log::Paths
{
    std::string BuildSessionDir(std::string_view logsRoot);
    std::string Join(const std::string& a, const std::string& b);
}
