#pragma once

#include "Log/Core/Level.h"
#include "Log/Core/Record.h"
#include "Log/Modules/ModuleId.h"

#include <cstddef>
#include <functional>
#include <limits>
#include <optional>
#include <string_view>
#include <unordered_map>

namespace Ecstatica::Recompiled::Log
{
    #ifdef NDEBUG
        constexpr Level kDefaultGlobalLogLevel = Level::Info;
    #else
        constexpr Level kDefaultGlobalLogLevel = Level::Trace;
    #endif

    struct Config
    {
        enum class Overflow
        {
            DropNew,
            DropOldest
        };

        Level                                       globalLevel         = kDefaultGlobalLogLevel;
        Overflow                                    overflow            = Overflow::DropNew;
        size_t                                      queueCapacity       = 32 * 1024;
        size_t                                      hiQueueCapacity     = 1024;
        std::function<bool(const Record&)>          rateLimit;
        bool                                        callstackOnError    = true;
        bool                                        callstackOnFatal    = true;
        bool                                        callstackOnWarning  = false;
        bool                                        disableSubmoduleFiltering = false;
        ModuleMask                                  moduleAllowMask     = std::numeric_limits<ModuleMask>::max();
        ModuleMask                                  moduleDenyMask      = 0;
        std::unordered_map<ModuleID, SubmoduleMask> submoduleAllowMasks;
        std::unordered_map<ModuleID, SubmoduleMask> submoduleDenyMasks;
        std::function<std::optional<Level>(ModuleID module, SubmoduleMask submodules)> moduleMinLevelMask;
    };
}
