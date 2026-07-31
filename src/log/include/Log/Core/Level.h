#pragma once

#include <cctype>
#include <cstdint>
#include <optional>
#include <string_view>

namespace Ecstatica::Recompiled::Log
{
    enum class Level : uint8_t
    {
        Trace = 0,
        Debug,
        Info,
        Warning,
        Error,
        Fatal,
        Off
    };

    inline const char* ToString(Level lvl)
    {
        switch (lvl)
        {
            case Level::Trace:   return "TRACE";
            case Level::Debug:   return "DEBUG";
            case Level::Info:    return "INFO";
            case Level::Warning: return "WARN";
            case Level::Error:   return "ERROR";
            case Level::Fatal:   return "FATAL";
            default:             return "OFF";
        }
    }

    inline std::optional<Level> FromString(std::string_view level) noexcept
    {
        const auto equalsIgnoreCase = [](std::string_view lhs, std::string_view rhs) noexcept
        {
            if (lhs.size() != rhs.size())
                return false;

            for (std::size_t i = 0; i < lhs.size(); ++i)
            {
                const auto l = static_cast<unsigned char>(lhs[i]);
                const auto r = static_cast<unsigned char>(rhs[i]);
                if (std::tolower(l) != std::tolower(r))
                    return false;
            }

            return true;
        };

        if (level.empty())
            return Level::Info;
        if (equalsIgnoreCase(level, "trace"))
            return Level::Trace;
        if (equalsIgnoreCase(level, "debug"))
            return Level::Debug;
        if (equalsIgnoreCase(level, "info"))
            return Level::Info;
        if (equalsIgnoreCase(level, "warn") || equalsIgnoreCase(level, "warning"))
            return Level::Warning;
        if (equalsIgnoreCase(level, "error"))
            return Level::Error;
        if (equalsIgnoreCase(level, "fatal"))
            return Level::Fatal;
        if (equalsIgnoreCase(level, "off"))
            return Level::Off;

        return std::nullopt;
    }
}
