#pragma once

#include <filesystem>
#include <string>

namespace Ecstatica::Recompiled::LogSupport::String::Path
{
    inline std::string EnsureTrailingSlash(std::filesystem::path path)
    {
        auto normalized = path.lexically_normal().string();
        if (!normalized.empty() && normalized.back() != '/')
            normalized += '/';
        return normalized;
    }
}
