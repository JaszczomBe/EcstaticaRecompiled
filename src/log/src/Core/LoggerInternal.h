#pragma once

#include "Log/Core/Logger.h"
#include "LogSupport/Algorithm/MPSCQueue.h"
#include "LogSupport/Thread/BackgroundRunner.h"
#include "LogSupport/Thread/Waiter.h"

#include <array>
#include <atomic>
#include <chrono>
#include <functional>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace Ecstatica::Recompiled::Log
{
    struct Logger::LoggerInternal
    {
        static constexpr size_t RealtimeNodePoolCapacity = 256;
        static constexpr size_t RealtimeMessageCapacity  = 256;
        static constexpr size_t RealtimeFormatMaxArgs    = 4;
        static constexpr size_t RealtimeFormatStringStorageCapacity = 192;
        static constexpr auto   RealtimeIdlePollInterval = std::chrono::milliseconds(1);

        struct OwnedPayload
        {
            std::string                    messageText;
            std::string                    sourceFileText;
            std::string                    sourceFuncText;
            std::vector<std::string>       fieldText;
            std::vector<Record::Field>     fieldViews;
            std::shared_ptr<std::string>   callstackText;

            void Reset();
            void BindViews(Record& record);
            void CaptureFrom(const Record& record, std::string&& ownedMessage = {});
        };

        struct Node
        {
            enum class StorageKind
            {
                Heap,
                RealtimePool
            };

            Node*        nextFree         = nullptr;
            StorageKind  storageKind      = StorageKind::Heap;
            Record       record;
            OwnedPayload payload;
            char         realtimeMessage[RealtimeMessageCapacity] = {};
            size_t       realtimeMessageLength                    = 0;
            std::array<std::string_view, RealtimeFormatMaxArgs> realtimeFormatArgsViews{};
            char         realtimeFormatStringStorage[RealtimeFormatStringStorageCapacity] = {};
            size_t       realtimeFormatStringStorageUsed = 0;
        };

        std::unique_ptr<Node> MakeNode(Record&& record, std::string&& ownedMessage = {});
        void        InitializeRealtimePool();
        Node*       AcquireRealtimeNode();
        void        ReleaseNode(Node* node);
        Node*       MakeRealtimeNode(Record&& record,
                                     const detail::RealtimeTextArgCapture* formatArgs = nullptr,
                                     size_t formatArgCount = 0);
        void        InitializeQueues(size_t capacity);
        bool        EnqueueNormal(std::unique_ptr<Node>& node);
        bool        EnqueueHighPriority(std::unique_ptr<Node>& node);
        void        ApplyPendingControls();
        void        RecordEnqueued(bool highPriority);
        void        RecordDropped(Level level, bool isRealtime = false);
        void        UpdateQueueDepths();
        void        ApplyDropOldestRequests(Ecstatica::Recompiled::LogSupport::Algorithm::MPSCQueue<Node>& queue, std::atomic<size_t>& pendingCount);
        bool        PassesModuleFilters(const Record& record) const;
        void        DrainQueue(Ecstatica::Recompiled::LogSupport::Algorithm::MPSCQueue<Node>& queue, bool highPriority);
        void        DrainOnce();

        Config                                              config;
        Ecstatica::Recompiled::LogSupport::Algorithm::MPSCQueue<Node> normalQueue;
        Ecstatica::Recompiled::LogSupport::Algorithm::MPSCQueue<Node> highPriorityQueue;

        std::atomic<uint64_t>                               sequence{0};
        std::vector<SinkPtr>                                sinks;
        std::mutex                                          sinksMutex;

        std::atomic<bool>                                   stopping{false};
        Ecstatica::Recompiled::LogSupport::Thread::BackgroundRunner   runner{"Logger"};
        Ecstatica::Recompiled::LogSupport::Thread::Waiter             waiter;

        std::atomic<size_t>                                 pendingDropOldestNormal{0};
        std::atomic<size_t>                                 pendingDropOldestHigh{0};
        std::unique_ptr<Node[]>                             realtimeNodes;
        std::atomic<Node*>                                  realtimeFreeList{nullptr};

        std::mutex                                          controlMutex;
        std::vector<std::function<void(LoggerInternal&)>>   controlOps;
        std::atomic<bool>                                   controlPending{false};

        std::unordered_map<ModuleID, Level>                 moduleLevels;
        std::unordered_map<ModuleID, void (*)(FormatOptions&)> moduleFormatRegistrars;

        std::atomic<uint64_t>                               statsEnqueuedTotal{0};
        std::atomic<uint64_t>                               statsDroppedTotal{0};
        std::atomic<uint64_t>                               statsDroppedRealtime{0};
        std::atomic<uint64_t>                               statsDrainedTotal{0};
        std::atomic<uint64_t>                               statsEnqueuedHigh{0};
        std::atomic<uint64_t>                               statsEnqueuedNormal{0};
        std::atomic<size_t>                                 statsQueueDepth{0};
        std::atomic<size_t>                                 statsHighQueueDepth{0};
        std::array<std::atomic<uint64_t>, 8>                statsDroppedByLevel{};
    };
}
