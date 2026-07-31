#pragma once

#include "LogSupport/Algorithm/Singleton.h"
#include "Log/Core/Config.h"
#include "Log/Modules/ModuleId.h"
#include "Log/Sinks/Sink.h"

#include <cstdint>
#include <functional>
#include <memory>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace Ecstatica::Recompiled::Log
{
    namespace detail
    {
        struct RealtimeTextArgCapture;
    }

    class Logger
    {
    public:
        static Logger& Instance();

        void           Start(const Config& cfg);
        void           Stop();

        void           AddSink(const SinkPtr& sink);
        void           ClearSinks();

        bool           Submit(Record&& rec);

        bool           Log(Level                lvl,
                           ModuleID             module,
                           SourceLoc            src,
                           std::string_view     msg,
                           const Record::Field* fields             = nullptr,
                           size_t               fieldCount         = 0,
                           bool                 withStack          = false,
                           ModuleMask           moduleMaskOverride = 0,
                           SubmoduleMask        submoduleMask      = 0);
        bool           LogOwned(Level                lvl,
                                ModuleID             module,
                                SourceLoc            src,
                                std::string&&        msg,
                                const Record::Field* fields             = nullptr,
                                size_t               fieldCount         = 0,
                                bool                 withStack          = false,
                                ModuleMask           moduleMaskOverride = 0,
                                SubmoduleMask        submoduleMask      = 0);
        bool           LogRealtime(Level            lvl,
                                   ModuleID         module,
                                   SourceLoc        src,
                                   std::string_view msg,
                                   ModuleMask       moduleMaskOverride = 0,
                                   SubmoduleMask    submoduleMask      = 0);
        bool           LogRealtimeFormatted(Level                              lvl,
                                            ModuleID                           module,
                                            SourceLoc                          src,
                                            std::string_view                   fmt,
                                            const detail::RealtimeTextArgCapture* args,
                                            size_t                             argCount,
                                            ModuleMask                         moduleMaskOverride = 0,
                                            SubmoduleMask                      submoduleMask      = 0);

        void           SetGlobalLevel(Level lvl);
        Level          GlobalLevel() const;
        bool           IsEnabled_KTParity(Level lvl,
                                          ModuleID module,
                                          ModuleMask moduleMaskOverride = 0,
                                          SubmoduleMask submoduleMask = 0);
        bool           ShouldCaptureCallstack_KTParity(Level lvl);

        uint64_t       NextSeq();
        void           MarkRealtimeThread(bool isRealtime);
        void           SetLevelForModule(ModuleID module, Level lvl);
        void           ClearLevelForModule(ModuleID module);
        void           ClearAllModuleOverrides();

        struct Stats
        {
            uint64_t enqueuedTotal     = 0;
            uint64_t droppedTotal      = 0;
            // Subset of droppedTotal from LogRealtime(): RT pool exhausted or
            // queue full. Distinct from normal-path drops so callers can tell
            // whether they need to widen the RT pool or the main queue.
            uint64_t droppedRealtime   = 0;
            uint64_t drainedTotal      = 0;
            uint64_t enqueuedHigh      = 0;
            uint64_t enqueuedNormal    = 0;
            uint64_t droppedByLevel[8] = {0};
            size_t   queueDepth        = 0;
            size_t   highQueueDepth    = 0;
        };
        Stats GetStats() const;

        void UpdateConfig(const std::function<void(Config&)>& updater);
        void SetModuleMinLevelResolver(std::function<std::optional<Level>(ModuleID module, SubmoduleMask submodules)> resolver);
        void SetRateLimiter(std::function<bool(const Record&)> limiter);
        void ReplaceSinks(const std::vector<SinkPtr>& sinks);
        bool RemoveSink(const SinkPtr& sink);
        void UpdateSinkFormatOptions(const std::function<void(FormatOptions&)>& updater);
        void RegisterModuleSubmoduleNames(ModuleID module, void (*registrar)(FormatOptions&));
        void SetModuleMask(ModuleMask allow_mask, ModuleMask deny_mask);
        void SetSubmoduleMask(ModuleID module, SubmoduleMask allow_mask, SubmoduleMask deny_mask);
        void ClearSubmoduleMask(ModuleID module);

    private:
        friend class Ecstatica::Recompiled::LogSupport::Algorithm::Singleton<Logger>;
        Logger() = default;

        bool SubmitPrepared(Record&& record, std::string&& ownedMessage);

        struct LoggerInternal;
        std::unique_ptr<LoggerInternal> logImpl;
    };

    inline bool AutoRegisterModuleLogging(ModuleID module,
                                          void (*registrar)(FormatOptions&),
                                          SubmoduleMask defaultDeniedSubmodules)
    {
        auto& logger = Logger::Instance();
        logger.RegisterModuleSubmoduleNames(module, registrar);
        logger.SetSubmoduleMask(module, std::numeric_limits<SubmoduleMask>::max(), defaultDeniedSubmodules);
        return true;
    }
}
