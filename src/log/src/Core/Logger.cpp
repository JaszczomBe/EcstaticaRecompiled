#include "Log/Core/Logger.h"

#include "Core/LoggerInternal.h"
#include "Core/RTTestHooksInternal.h"
#include "Log/Debug/StackTrace.h"
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
    #include "Log/Test/RTTestHooks.h"
#endif
#include "LogSupport/Thread/Id.h"
#include "LogSupport/Thread/RealtimeContext.h"

#include <algorithm>
#include <chrono>
#include <iostream>
#include <limits>
#include <memory>
#include <utility>

namespace Ecstatica::Recompiled::Log
{
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
    namespace Test
    {
        RTTestHooksState& AccessRTTestHooksState()
        {
            static RTTestHooksState state;

            return state;
        }

        void ResetRTTestHooks()
        {
            auto& state = AccessRTTestHooksState();
            state.waiterStopWaitCalls.store(0, std::memory_order_relaxed);
            state.realtimeAttempts.store(0, std::memory_order_relaxed);
            state.realtimeEnqueued.store(0, std::memory_order_relaxed);
            state.realtimeDropped.store(0, std::memory_order_relaxed);
            state.realtimeOversizeDrops.store(0, std::memory_order_relaxed);
        }

        RTTestHooksSnapshot GetRTTestHooksSnapshot()
        {
            auto&               state    = AccessRTTestHooksState();
            RTTestHooksSnapshot snapshot;
            snapshot.waiterStopWaitCalls = state.waiterStopWaitCalls.load(std::memory_order_relaxed);
            snapshot.realtimeAttempts    = state.realtimeAttempts.load(std::memory_order_relaxed);
            snapshot.realtimeEnqueued    = state.realtimeEnqueued.load(std::memory_order_relaxed);
            snapshot.realtimeDropped     = state.realtimeDropped.load(std::memory_order_relaxed);
            snapshot.realtimeOversizeDrops = state.realtimeOversizeDrops.load(std::memory_order_relaxed);

            return snapshot;
        }
    }
#endif

    Logger& Logger::Instance()
    {
        return Ecstatica::Recompiled::LogSupport::Algorithm::Singleton<Logger>::Instance();
    }

    void Logger::Start(const Config& cfg)
    {
        if(!logImpl)
            logImpl = std::make_unique<LoggerInternal>();
        else
            Stop();

        logImpl->config = cfg;

        logImpl->stopping.store(false, std::memory_order_release);
        logImpl->InitializeQueues(cfg.queueCapacity);

        logImpl->runner.Start(
            [this]() -> bool
            {
                logImpl->DrainOnce();

                if(logImpl->stopping.load(std::memory_order_acquire))
                {
                    logImpl->DrainOnce();
                    return false;
                }

                logImpl->waiter.AwaitFor(LoggerInternal::RealtimeIdlePollInterval);
                return true;
            });
    }

    void Logger::Stop()
    {
        if(!logImpl)
            return;

        if(logImpl->stopping.exchange(true, std::memory_order_acq_rel))
            return;

        logImpl->waiter.StopWait();
        logImpl->runner.Stop();

        logImpl->DrainOnce();
        {
            std::lock_guard<std::mutex> lock(logImpl->sinksMutex);
            for(auto& sink : logImpl->sinks)
                sink->Flush();
        }
    }

    void Logger::AddSink(const SinkPtr& sink)
    {
        if(!logImpl || !sink)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back(
                [sink](LoggerInternal& state)
                {
                    auto format = sink->GetFormatOptions();
                    for(const auto& [module, registrar] : state.moduleFormatRegistrars)
                    {
                        (void)module;
                        if(registrar)
                            registrar(format);
                    }
                    sink->SetFormatOptions(format);

                    std::lock_guard<std::mutex> stateLock(state.sinksMutex);
                    state.sinks.push_back(sink);
                });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    void Logger::ClearSinks()
    {
        if(!logImpl)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back(
                [](LoggerInternal& state)
                {
                    std::lock_guard<std::mutex> stateLock(state.sinksMutex);
                    state.sinks.clear();
                });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    bool Logger::SubmitPrepared(Record&& record, std::string&& ownedMessage)
    {
        if(!logImpl)
            return false;

        if(logImpl->stopping.load(std::memory_order_acquire))
            return false;

        record.seq             = logImpl->sequence.fetch_add(1, std::memory_order_relaxed) + 1;
        record.threadId        = Ecstatica::Recompiled::LogSupport::Thread::ThisThreadId();
        record.timePointSteady = std::chrono::steady_clock::now();
        record.timePointWall   = std::chrono::system_clock::now();

        auto node              = logImpl->MakeNode(std::move(record), std::move(ownedMessage));

        const bool  highPriority = node->record.level == Level::Error || node->record.level == Level::Fatal;
        const Level nodeLevel    = node->record.level;

        auto        tryEnqueue   = [&]() -> bool
        { return highPriority ? logImpl->EnqueueHighPriority(node) : logImpl->EnqueueNormal(node); };

        bool enqueued = tryEnqueue();

        if(!enqueued && !logImpl->stopping.load(std::memory_order_acquire))
        {
            const Config::Overflow overflowPolicy = logImpl->config.overflow;

            if(overflowPolicy == Config::Overflow::DropOldest)
            {
                // Signal the consumer to evict one old entry, then retry once.
                // The retry is not guaranteed to succeed: if the consumer hasn't
                // run yet the queue is still full and the new record will be
                // dropped. DropOldest is best-effort, not strictly "always accepts
                // latest." See ApplyDropOldestRequests for the full concurrency notes.
                logImpl->waiter.StopWait();
                auto& pendingCount = highPriority ? logImpl->pendingDropOldestHigh : logImpl->pendingDropOldestNormal;
                pendingCount.fetch_add(1, std::memory_order_release);
                enqueued = tryEnqueue();
            }
        }

        if(!enqueued)
        {
            logImpl->RecordDropped(nodeLevel);
            return false;
        }
        logImpl->RecordEnqueued(highPriority);

        return true;
    }

    bool Logger::Submit(Record&& record)
    {
        return SubmitPrepared(std::move(record), {});
    }

    bool Logger::Log(Level                lvl,
                     ModuleID             module,
                     SourceLoc            src,
                     std::string_view     msg,
                     const Record::Field* fields,
                     size_t               fieldCount,
                     bool                 withStack,
                     ModuleMask           moduleMaskOverride,
                     SubmoduleMask        submoduleMask)
    {
        Record record;
        record.level          = lvl;
        record.module         = module;

        ModuleMask moduleMask = moduleMaskOverride;
        if(moduleMask == 0 && module != ModuleID::None)
            moduleMask = ToMask(module);

        record.moduleMask    = moduleMask;
        record.submoduleMask = submoduleMask;
        record.message       = msg;
        record.src           = src;
        record.fields        = fields;
        record.fieldCount    = fieldCount;

        const bool wantStack = withStack || (logImpl && lvl == Level::Fatal && logImpl->config.callstackOnFatal) ||
                               (logImpl && lvl == Level::Error && logImpl->config.callstackOnError) ||
                               (logImpl && lvl == Level::Warning && logImpl->config.callstackOnWarning);

        // Callstack capture is gated strictly on the thread-local IsRealtimeThread()
        // flag, set via MarkRealtimeThread() / RealtimeContext::Scope.  It is NOT
        // tied to which logging macro was used.  Any thread that hasn't registered
        // itself as RT will call backtrace() here on Error/Fatal — audio-adjacent
        // threads must register appropriately.  Note: backtrace() only captures raw
        // addresses; addr2line / atos symbolization happens offline in the sink.
        if(wantStack && logImpl && !Ecstatica::Recompiled::LogSupport::Thread::RealtimeContext::IsRealtimeThread())
            record.callstack = CaptureCallstack(true, 64);

        return SubmitPrepared(std::move(record), {});
    }

    bool Logger::LogOwned(Level                lvl,
                          ModuleID             module,
                          SourceLoc            src,
                          std::string&&        msg,
                          const Record::Field* fields,
                          size_t               fieldCount,
                          bool                 withStack,
                          ModuleMask           moduleMaskOverride,
                          SubmoduleMask        submoduleMask)
    {
        Record record;
        record.level          = lvl;
        record.module         = module;

        ModuleMask moduleMask = moduleMaskOverride;
        if(moduleMask == 0 && module != ModuleID::None)
            moduleMask = ToMask(module);

        record.moduleMask    = moduleMask;
        record.submoduleMask = submoduleMask;
        record.message       = msg;
        record.src           = src;
        record.fields        = fields;
        record.fieldCount    = fieldCount;

        const bool wantStack = withStack || (logImpl && lvl == Level::Fatal && logImpl->config.callstackOnFatal) ||
                               (logImpl && lvl == Level::Error && logImpl->config.callstackOnError) ||
                               (logImpl && lvl == Level::Warning && logImpl->config.callstackOnWarning);

        // Same guard as Log() — see comment there.
        if(wantStack && logImpl && !Ecstatica::Recompiled::LogSupport::Thread::RealtimeContext::IsRealtimeThread())
            record.callstack = CaptureCallstack(true, 64);

        return SubmitPrepared(std::move(record), std::move(msg));
    }

    bool Logger::LogRealtime(Level            lvl,
                             ModuleID         module,
                             SourceLoc        src,
                             std::string_view msg,
                             ModuleMask       moduleMaskOverride,
                             SubmoduleMask    submoduleMask)
    {
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
        auto& testHooks = Test::AccessRTTestHooksState();
        testHooks.realtimeAttempts.fetch_add(1, std::memory_order_relaxed);
#endif

        if(!logImpl)
            return false;

        if(logImpl->stopping.load(std::memory_order_acquire))
            return false;

        Record record;
        record.level          = lvl;
        record.module         = module;
        record.moduleMask     = moduleMaskOverride == 0 && module != ModuleID::None ? ToMask(module) : moduleMaskOverride;
        record.submoduleMask  = submoduleMask;
        record.message        = msg;
        record.src            = src;
        record.seq            = logImpl->sequence.fetch_add(1, std::memory_order_relaxed) + 1;
        record.threadId       = Ecstatica::Recompiled::LogSupport::Thread::ThisThreadId();
        record.timePointSteady = std::chrono::steady_clock::now();
        record.timePointWall   = std::chrono::system_clock::now();

#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
        const bool oversizeMessage = msg.size() > LoggerInternal::RealtimeMessageCapacity;
#endif
        LoggerInternal::Node* node = logImpl->MakeRealtimeNode(std::move(record));
        if(node == nullptr)
        {
            // RT pool exhausted or message too large for the 256-byte buffer —
            // tracked separately from normal-path drops via droppedRealtime.
            logImpl->RecordDropped(lvl, /*isRealtime=*/true);
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
            testHooks.realtimeDropped.fetch_add(1, std::memory_order_relaxed);
            if(oversizeMessage)
                testHooks.realtimeOversizeDrops.fetch_add(1, std::memory_order_relaxed);
#endif
            return false;
        }

        const bool highPriority = node->record.level == Level::Error || node->record.level == Level::Fatal;
        const bool enqueued =
            highPriority ? logImpl->highPriorityQueue.TryEnqueueRaw(node) : logImpl->normalQueue.TryEnqueueRaw(node);

        if(!enqueued)
        {
            logImpl->ReleaseNode(node);
            logImpl->RecordDropped(lvl, /*isRealtime=*/true);
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
            testHooks.realtimeDropped.fetch_add(1, std::memory_order_relaxed);
#endif
            return false;
        }
        logImpl->RecordEnqueued(highPriority);
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
        testHooks.realtimeEnqueued.fetch_add(1, std::memory_order_relaxed);
#endif

        return true;
    }

    bool Logger::LogRealtimeFormatted(Level                              lvl,
                                      ModuleID                           module,
                                      SourceLoc                          src,
                                      std::string_view                   fmt,
                                      const detail::RealtimeTextArgCapture* args,
                                      size_t                             argCount,
                                      ModuleMask                         moduleMaskOverride,
                                      SubmoduleMask                      submoduleMask)
    {
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
        auto& testHooks = Test::AccessRTTestHooksState();
        testHooks.realtimeAttempts.fetch_add(1, std::memory_order_relaxed);
#endif

        if(!logImpl)
            return false;

        if(logImpl->stopping.load(std::memory_order_acquire))
            return false;

        Record record;
        record.level               = lvl;
        record.module              = module;
        record.moduleMask          = moduleMaskOverride == 0 && module != ModuleID::None ? ToMask(module) : moduleMaskOverride;
        record.submoduleMask       = submoduleMask;
        record.src                 = src;
        record.seq                 = logImpl->sequence.fetch_add(1, std::memory_order_relaxed) + 1;
        record.threadId            = Ecstatica::Recompiled::LogSupport::Thread::ThisThreadId();
        record.timePointSteady     = std::chrono::steady_clock::now();
        record.timePointWall       = std::chrono::system_clock::now();
        record.realtimeFormat      = fmt;
        record.realtimeFormatArgs  = nullptr;
        record.realtimeFormatArgCount = 0;

        LoggerInternal::Node* node = logImpl->MakeRealtimeNode(std::move(record), args, argCount);
        if(node == nullptr)
        {
            logImpl->RecordDropped(lvl, /*isRealtime=*/true);
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
            testHooks.realtimeDropped.fetch_add(1, std::memory_order_relaxed);
#endif
            return false;
        }

        const bool highPriority = node->record.level == Level::Error || node->record.level == Level::Fatal;
        const bool enqueued =
            highPriority ? logImpl->highPriorityQueue.TryEnqueueRaw(node) : logImpl->normalQueue.TryEnqueueRaw(node);

        if(!enqueued)
        {
            logImpl->ReleaseNode(node);
            logImpl->RecordDropped(lvl, /*isRealtime=*/true);
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
            testHooks.realtimeDropped.fetch_add(1, std::memory_order_relaxed);
#endif
            return false;
        }

        logImpl->RecordEnqueued(highPriority);
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
        testHooks.realtimeEnqueued.fetch_add(1, std::memory_order_relaxed);
#endif

        return true;
    }

    void Logger::SetGlobalLevel(Level lvl)
    {
        if(!logImpl)
            return;

        UpdateConfig([lvl](Config& config) { config.globalLevel = lvl; });
    }

    Level Logger::GlobalLevel() const
    {
        if(!logImpl)
            return Level::Info;

        return logImpl->config.globalLevel;
    }

    bool Logger::IsEnabled_KTParity(Level lvl, ModuleID module, ModuleMask moduleMaskOverride, SubmoduleMask submoduleMask)
    {
        if(!logImpl)
            return false;

        logImpl->ApplyPendingControls();

        Record record;
        record.level         = lvl;
        record.module        = module;
        record.moduleMask    = moduleMaskOverride == 0 && module != ModuleID::None ? ToMask(module) : moduleMaskOverride;
        record.submoduleMask = submoduleMask;

        const bool highPriority = lvl == Level::Error || lvl == Level::Fatal;
        if(highPriority)
        {
            if(lvl == Level::Error)
                return logImpl->PassesModuleFilters(record);

            return true;
        }

        if(!logImpl->PassesModuleFilters(record))
            return false;

        Level    minimumLevel    = logImpl->config.globalLevel;
        bool     levelOverridden = false;
        ModuleID resolvedModule  = record.module;
        if(resolvedModule == ModuleID::None)
        {
            if(auto moduleId = SingleModuleFromMask(record.moduleMask))
                resolvedModule = *moduleId;
        }

        if(resolvedModule != ModuleID::None)
        {
            const auto moduleLevelIt = logImpl->moduleLevels.find(resolvedModule);
            if(moduleLevelIt != logImpl->moduleLevels.end())
            {
                minimumLevel    = moduleLevelIt->second;
                levelOverridden = true;
            }

            if(!levelOverridden && logImpl->config.moduleMinLevelMask)
            {
                if(auto custom = logImpl->config.moduleMinLevelMask(resolvedModule, record.submoduleMask))
                    minimumLevel = *custom;
            }
        }

        return static_cast<int>(record.level) >= static_cast<int>(minimumLevel);
    }

    bool Logger::ShouldCaptureCallstack_KTParity(Level lvl)
    {
        if(!logImpl)
            return false;

        logImpl->ApplyPendingControls();

        switch(lvl)
        {
            case Level::Warning:
                return logImpl->config.callstackOnWarning;
            case Level::Error:
                return logImpl->config.callstackOnError;
            case Level::Fatal:
                return logImpl->config.callstackOnFatal;
            default:
                return false;
        }
    }

    uint64_t Logger::NextSeq()
    {
        if(!logImpl)
            return 0;

        return logImpl->sequence.load(std::memory_order_relaxed) + 1;
    }

    void Logger::MarkRealtimeThread(bool isRealtime)
    {
        Ecstatica::Recompiled::LogSupport::Thread::RealtimeContext::SetRealtimeThread(isRealtime);
    }

    void Logger::UpdateConfig(const std::function<void(Config&)>& updater)
    {
        if(!logImpl || !updater)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back([updater](LoggerInternal& state) { updater(state.config); });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    void Logger::SetModuleMinLevelResolver(
        std::function<std::optional<Level>(ModuleID module, SubmoduleMask submodules)> resolver)
    {
        if(!logImpl)
            return;

        UpdateConfig([resolver = std::move(resolver)](Config& config) { config.moduleMinLevelMask = resolver; });
    }

    void Logger::SetRateLimiter(std::function<bool(const Record&)> limiter)
    {
        if(!logImpl)
            return;

        UpdateConfig([limiter = std::move(limiter)](Config& config) { config.rateLimit = limiter; });
    }

    void Logger::ReplaceSinks(const std::vector<SinkPtr>& sinks)
    {
        if(!logImpl)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back(
                [sinks](LoggerInternal& state)
                {
                    std::vector<SinkPtr> configuredSinks;
                    configuredSinks.reserve(sinks.size());
                    for(const auto& sink : sinks)
                    {
                        if(!sink)
                        {
                            configuredSinks.push_back(sink);
                            continue;
                        }

                        auto format = sink->GetFormatOptions();
                        for(const auto& [module, registrar] : state.moduleFormatRegistrars)
                        {
                            (void)module;
                            if(registrar)
                                registrar(format);
                        }
                        sink->SetFormatOptions(format);
                        configuredSinks.push_back(sink);
                    }

                    std::lock_guard<std::mutex> stateLock(state.sinksMutex);
                    state.sinks = std::move(configuredSinks);
                });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    bool Logger::RemoveSink(const SinkPtr& sink)
    {
        if(!logImpl || !sink)
            return false;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back(
                [sink](LoggerInternal& state)
                {
                    std::lock_guard<std::mutex> stateLock(state.sinksMutex);
                    state.sinks.erase(std::remove(state.sinks.begin(), state.sinks.end(), sink), state.sinks.end());
                });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
        return true;
    }

    void Logger::UpdateSinkFormatOptions(const std::function<void(FormatOptions&)>& updater)
    {
        if(!logImpl || !updater)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back(
                [updater](LoggerInternal& state)
                {
                    std::lock_guard<std::mutex> stateLock(state.sinksMutex);
                    for(auto& sink : state.sinks)
                    {
                        if(!sink)
                            continue;

                        auto format = sink->GetFormatOptions();
                        updater(format);
                        sink->SetFormatOptions(format);
                    }
                });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    void Logger::RegisterModuleSubmoduleNames(ModuleID module, void (*registrar)(FormatOptions&))
    {
        if(module == ModuleID::None || registrar == nullptr)
            return;

        if(!logImpl)
            logImpl = std::make_unique<LoggerInternal>();

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back(
                [module, registrar](LoggerInternal& state)
                {
                    const auto existing = state.moduleFormatRegistrars.find(module);
                    if(existing != state.moduleFormatRegistrars.end())
                    {
                        if(existing->second != registrar)
                        {
                            std::cerr << "WARN: submodule names for module '" << ModuleToString(module)
                                      << "' were registered more than once with a different registrar"
                                      << std::endl;
                        }
                        return;
                    }

                    state.moduleFormatRegistrars.emplace(module, registrar);

                    std::lock_guard<std::mutex> stateLock(state.sinksMutex);
                    for(auto& sink : state.sinks)
                    {
                        if(!sink)
                            continue;

                        auto format = sink->GetFormatOptions();
                        registrar(format);
                        sink->SetFormatOptions(format);
                    }
                });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    void Logger::SetModuleMask(ModuleMask allow_mask, ModuleMask deny_mask)
    {
        if(!logImpl)
            return;

        UpdateConfig(
            [allow_mask, deny_mask](Config& config)
            {
                config.moduleAllowMask = allow_mask;
                config.moduleDenyMask  = deny_mask;
            });
    }

    void Logger::SetSubmoduleMask(ModuleID module, SubmoduleMask allow_mask, SubmoduleMask deny_mask)
    {
        if(module == ModuleID::None)
            return;

        if(!logImpl)
            logImpl = std::make_unique<LoggerInternal>();

        UpdateConfig(
            [module, allow_mask, deny_mask](Config& config)
            {
                if(allow_mask == std::numeric_limits<SubmoduleMask>::max())
                    config.submoduleAllowMasks.erase(module);
                else
                    config.submoduleAllowMasks[module] = allow_mask;

                if(deny_mask == 0)
                    config.submoduleDenyMasks.erase(module);
                else
                    config.submoduleDenyMasks[module] = deny_mask;
            });
    }

    void Logger::ClearSubmoduleMask(ModuleID module)
    {
        if(!logImpl)
            return;

        UpdateConfig(
            [module](Config& config)
            {
                config.submoduleAllowMasks.erase(module);
                config.submoduleDenyMasks.erase(module);
            });
    }

    void Logger::SetLevelForModule(ModuleID module, Level lvl)
    {
        if(!logImpl)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back([module, lvl](LoggerInternal& state)
                                             { state.moduleLevels[module] = lvl; });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    void Logger::ClearLevelForModule(ModuleID module)
    {
        if(!logImpl)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back([module](LoggerInternal& state) { state.moduleLevels.erase(module); });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    void Logger::ClearAllModuleOverrides()
    {
        if(!logImpl)
            return;

        {
            std::lock_guard<std::mutex> lock(logImpl->controlMutex);
            logImpl->controlOps.emplace_back([](LoggerInternal& state) { state.moduleLevels.clear(); });
            logImpl->controlPending.store(true, std::memory_order_release);
        }

        logImpl->waiter.StopWait();
    }

    Logger::Stats Logger::GetStats() const
    {
        Stats snapshot;
        if(!logImpl)
            return snapshot;

        snapshot.enqueuedTotal   = logImpl->statsEnqueuedTotal.load(std::memory_order_relaxed);
        snapshot.droppedTotal    = logImpl->statsDroppedTotal.load(std::memory_order_relaxed);
        snapshot.droppedRealtime = logImpl->statsDroppedRealtime.load(std::memory_order_relaxed);
        snapshot.drainedTotal    = logImpl->statsDrainedTotal.load(std::memory_order_relaxed);
        snapshot.enqueuedHigh    = logImpl->statsEnqueuedHigh.load(std::memory_order_relaxed);
        snapshot.enqueuedNormal  = logImpl->statsEnqueuedNormal.load(std::memory_order_relaxed);
        snapshot.queueDepth      = logImpl->statsQueueDepth.load(std::memory_order_relaxed);
        snapshot.highQueueDepth  = logImpl->statsHighQueueDepth.load(std::memory_order_relaxed);

        for(size_t i = 0; i < std::size(snapshot.droppedByLevel); ++i)
            snapshot.droppedByLevel[i] = logImpl->statsDroppedByLevel[i].load(std::memory_order_relaxed);

        return snapshot;
    }
}
