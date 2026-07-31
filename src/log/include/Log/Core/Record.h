#pragma once

#include "Log/Core/Field.h"
#include "Log/Core/Level.h"
#include "Log/Core/SourceLoc.h"
#include "Log/Modules/ModuleId.h"

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string_view>

namespace Ecstatica::Recompiled::Log
{
    struct Record
    {
        using Field = Ecstatica::Recompiled::Log::Field;

        Level                                 level;
        ModuleID                              module        = ModuleID::None;
        ModuleMask                            moduleMask    = 0;
        SubmoduleMask                         submoduleMask = 0;
        std::string_view                      message;
        SourceLoc                             src;
        uint64_t                              threadId;
        uint64_t                              seq;
        std::chrono::steady_clock::time_point timePointSteady;
        std::chrono::system_clock::time_point timePointWall;
        const Field*                          fields     = nullptr;
        size_t                                fieldCount = 0;
        std::shared_ptr<std::string>          callstack;
        // Optional deferred RT format payload. When present, the consumer
        // formats `realtimeFormat` with the bounded inline string arguments
        // referenced by `realtimeFormatArgs`.
        std::string_view                      realtimeFormat;
        const std::string_view*               realtimeFormatArgs = nullptr;
        size_t                                realtimeFormatArgCount = 0;
    };
}
