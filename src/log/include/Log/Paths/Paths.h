#pragma once

#include <string>
#include <string_view>

namespace Ecstatica::Recompiled::Log::Paths
{
    const std::string& LogsRoot();
    const std::string& SessionDir();
    std::string BuildSessionDir(std::string_view logsRoot);
    std::string BuildSessionFilePath(std::string_view logsRoot, std::string_view fileName);
    std::string Join(const std::string& a, const std::string& b);
}
