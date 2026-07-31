#pragma once

namespace Ecstatica::Recompiled::Log
{
    template <typename... Args>
    bool WriteLogf(Level lvl, ModuleID module, SourceLoc src, detail::TextFormatDescriptor<Args...> fmt, Args&&... args)
    {
        return WriteLogfDetailed(lvl, module, src, nullptr, 0, false, 0, 0, fmt, std::forward<Args>(args)...);
    }

    template <typename... Args>
    bool WriteLogf(Level                                 lvl,
                   ModuleID                              module,
                   SourceLoc                             src,
                   const Record::Field*                  fields,
                   size_t                                fieldCount,
                   bool                                  withStack,
                   detail::TextFormatDescriptor<Args...> fmt,
                   Args&&... args)
    {
        return WriteLogfDetailed(
            lvl, module, src, fields, fieldCount, withStack, 0, 0, fmt, std::forward<Args>(args)...);
    }

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
                           Args&&... args)
    {
        auto message = detail::TextFormat(fmt, std::forward<Args>(args)...);
        return WriteLogOwned(
            lvl, module, src, std::move(message), fields, fieldCount, withStack, moduleMaskOverride, submoduleMask);
    }

    template <size_t N, typename... Args>
    bool WriteRealtimeLogf(Level         lvl,
                           ModuleID      module,
                           SourceLoc     src,
                           ModuleMask    moduleMaskOverride,
                           SubmoduleMask submoduleMask,
                           const char (&fmt)[N],
                           Args&&... args)
    {
        static_assert((detail::IsRealtimeTextArgV<Args> && ...),
                      "UT_RT_*_FMT supports only string-like arguments and char values.");

        const auto analysis = detail::AnalyzeRealtimeFormat(fmt);
        if(!analysis.valid || analysis.placeholderCount != sizeof...(Args))
            return false;

        std::array<detail::RealtimeTextArgCapture, sizeof...(Args)> captures{
            detail::MakeRealtimeTextArgCapture(std::forward<Args>(args))...};

        return WriteRealtimeLogfCaptured(
            lvl,
            module,
            src,
            std::string_view(fmt, N - 1),
            captures.data(),
            captures.size(),
            moduleMaskOverride,
            submoduleMask);
    }
}
