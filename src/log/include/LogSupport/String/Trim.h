#pragma once

#include <cctype>
#include <string>
#include <string_view>

namespace Ecstatica::Recompiled::LogSupport::String
{
    inline std::string_view TrimLeftAsciiWhitespace(std::string_view s) noexcept
    {
        while(!s.empty() && std::isspace(static_cast<unsigned char>(s.front())))
            s.remove_prefix(1);
        return s;
    }

    inline std::string_view TrimRightAsciiWhitespace(std::string_view s) noexcept
    {
        while(!s.empty() && std::isspace(static_cast<unsigned char>(s.back())))
            s.remove_suffix(1);
        return s;
    }

    inline std::string_view TrimAsciiWhitespace(std::string_view s) noexcept
    {
        return TrimRightAsciiWhitespace(TrimLeftAsciiWhitespace(s));
    }

    inline std::string TrimAsciiWhitespaceCopy(std::string_view s)
    {
        s = TrimAsciiWhitespace(s);
        return std::string(s);
    }
}
