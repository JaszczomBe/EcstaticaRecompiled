#pragma once

#include "Log/Core/Level.h"
#include "Log/Modules/Module.h"

#include <sstream>
#include <string>
#include <string_view>

namespace Ecstatica::Recompiled::Log
{
    inline std::string MakeLifecycleBanner(std::string_view title)
    {
        std::ostringstream stream;
        stream << '\n';
        stream << "================================================================================\n";
        stream << title << '\n';
        stream << "================================================================================\n";
        return stream.str();
    }
}

#define UT_LOG_APP_BANNER(submodule_mask, title) \
    UT_LOGM_MASK(Ecstatica::Recompiled::Log::Level::Info, (submodule_mask), Ecstatica::Recompiled::Log::MakeLifecycleBanner((title)))

#define UT_LOG_APP_SETTINGS(submodule_mask, settings_value) \
    do \
    { \
        std::ostringstream ut_log_settings_stream; \
        ut_log_settings_stream << '\n' << (settings_value); \
        UT_LOGM_MASK(Ecstatica::Recompiled::Log::Level::Info, (submodule_mask), ut_log_settings_stream.str()); \
    } while(0)
