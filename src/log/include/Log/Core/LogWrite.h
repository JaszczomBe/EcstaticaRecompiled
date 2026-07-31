#pragma once

#include "Log/Core/Level.h"
#include "Log/Core/Record.h"
#include "Log/Core/SourceLoc.h"
#include "Log/Core/TextFormat.h"
#include "Log/Modules/ModuleId.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>

namespace Ecstatica::Recompiled::Log
{
    namespace detail
    {
        struct RealtimeTextArgCapture
        {
            enum class Kind : std::uint8_t
            {
                StringView,
                Char
            };

            Kind             kind = Kind::StringView;
            std::string_view text{};
            char             character = '\0';
        };

        inline RealtimeTextArgCapture MakeRealtimeTextArgCapture(std::string_view value)
        {
            return {RealtimeTextArgCapture::Kind::StringView, value, '\0'};
        }

        inline RealtimeTextArgCapture MakeRealtimeTextArgCapture(const std::string& value)
        {
            return MakeRealtimeTextArgCapture(std::string_view(value));
        }

        inline RealtimeTextArgCapture MakeRealtimeTextArgCapture(const char* value)
        {
            return MakeRealtimeTextArgCapture(value ? std::string_view(value) : std::string_view{});
        }

        inline RealtimeTextArgCapture MakeRealtimeTextArgCapture(char* value)
        {
            return MakeRealtimeTextArgCapture(static_cast<const char*>(value));
        }

        template <size_t N>
        inline RealtimeTextArgCapture MakeRealtimeTextArgCapture(const char (&value)[N])
        {
            return MakeRealtimeTextArgCapture(std::string_view(value, N - 1));
        }

        inline RealtimeTextArgCapture MakeRealtimeTextArgCapture(char value)
        {
            return {RealtimeTextArgCapture::Kind::Char, {}, value};
        }

        template <typename T>
        inline constexpr bool IsRealtimeTextArgV =
            requires(T&& value) { MakeRealtimeTextArgCapture(std::forward<T>(value)); };

        struct RealtimeFormatAnalysis
        {
            size_t placeholderCount = 0;
            bool   valid            = true;
        };

        template <size_t N>
        constexpr RealtimeFormatAnalysis AnalyzeRealtimeFormat(const char (&fmt)[N])
        {
            RealtimeFormatAnalysis analysis{};
            for(size_t i = 0; i + 1 < N; ++i)
            {
                if(fmt[i] == '{')
                {
                    if(fmt[i + 1] == '{')
                    {
                        ++i;
                        continue;
                    }

                    if(fmt[i + 1] == '}')
                    {
                        ++analysis.placeholderCount;
                        ++i;
                        continue;
                    }

                    analysis.valid = false;
                    break;
                }

                if(fmt[i] == '}')
                {
                    if(fmt[i + 1] == '}')
                    {
                        ++i;
                        continue;
                    }

                    analysis.valid = false;
                    break;
                }
            }

            return analysis;
        }
    }

    bool WriteLog(Level                lvl,
                  ModuleID             module,
                  SourceLoc            src,
                  std::string_view     msg,
                  const Record::Field* fields             = nullptr,
                  size_t               fieldCount         = 0,
                  bool                 withStack          = false,
                  ModuleMask           moduleMaskOverride = 0,
                  SubmoduleMask        submoduleMask      = 0);
    bool WriteLogOwned(Level                lvl,
                       ModuleID             module,
                       SourceLoc            src,
                       std::string&&        msg,
                       const Record::Field* fields             = nullptr,
                       size_t               fieldCount         = 0,
                       bool                 withStack          = false,
                       ModuleMask           moduleMaskOverride = 0,
                       SubmoduleMask        submoduleMask      = 0);
    bool WriteRealtimeLog(Level            lvl,
                          ModuleID         module,
                          SourceLoc        src,
                          std::string_view msg,
                          ModuleMask       moduleMaskOverride = 0,
                          SubmoduleMask    submoduleMask      = 0);
    bool WriteRealtimeLogfCaptured(Level                              lvl,
                                   ModuleID                           module,
                                   SourceLoc                          src,
                                   std::string_view                   fmt,
                                   const detail::RealtimeTextArgCapture* args,
                                   size_t                             argCount,
                                   ModuleMask                         moduleMaskOverride = 0,
                                   SubmoduleMask                      submoduleMask      = 0);

    template <typename... Args>
    bool WriteLogfDetailed(Level                                 lvl,
                           ModuleID                              module,
                           SourceLoc                             src,
                           const Record::Field*                  fields,
                           size_t                                fieldCount,
                           bool                                  withStack,
                           ModuleMask                            moduleMaskOverride,
                           SubmoduleMask                         submoduleMask,
                           detail::TextFormatDescriptor<Args...> fmt,
                           Args&&... args);

    template <typename... Args>
    bool WriteLogf(
        Level lvl, ModuleID module, SourceLoc src, detail::TextFormatDescriptor<Args...> fmt, Args&&... args);

    template <typename... Args>
    bool WriteLogf(Level                                 lvl,
                   ModuleID                              module,
                   SourceLoc                             src,
                   const Record::Field*                  fields,
                   size_t                                fieldCount,
                   bool                                  withStack,
                   detail::TextFormatDescriptor<Args...> fmt,
                   Args&&... args);

    template <size_t N, typename... Args>
    bool WriteRealtimeLogf(Level            lvl,
                           ModuleID         module,
                           SourceLoc        src,
                           ModuleMask       moduleMaskOverride,
                           SubmoduleMask    submoduleMask,
                           const char (&fmt)[N],
                           Args&&... args);

}

#include "Log/Core/LogWrite.inl"
