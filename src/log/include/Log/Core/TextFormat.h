#pragma once

#include <string>
#include <utility>

#if defined(UT_LOG_USE_STD_FORMAT)
    #include <format>
#elif defined(UT_LOG_USE_FMT_FORMAT)
    #include <fmt/format.h>
#else
    #error "No log text formatting backend configured"
#endif

namespace Ecstatica::Recompiled::Log::detail
{
#if defined(UT_LOG_USE_STD_FORMAT)
    template <typename... Args>
    using TextFormatDescriptor = std::format_string<Args...>;

    template <typename... Args>
    inline std::string TextFormat(TextFormatDescriptor<Args...> fmt, Args&&... args)
    {
        return std::format(fmt, std::forward<Args>(args)...);
    }
#elif defined(UT_LOG_USE_FMT_FORMAT)
    template <typename... Args>
    using TextFormatDescriptor = fmt::format_string<Args...>;

    template <typename... Args>
    inline std::string TextFormat(TextFormatDescriptor<Args...> fmt, Args&&... args)
    {
        return fmt::format(fmt, std::forward<Args>(args)...);
    }
#endif
}
