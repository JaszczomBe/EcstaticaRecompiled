#include "Core/LoggerInternal.h"
#include "Log/Core/LogWrite.h"

#include <cstring>
#include <memory>

namespace Ecstatica::Recompiled::Log
{
    void Logger::LoggerInternal::OwnedPayload::Reset()
    {
        messageText.clear();
        sourceFileText.clear();
        sourceFuncText.clear();
        fieldText.clear();
        fieldViews.clear();
        callstackText.reset();
    }

    void Logger::LoggerInternal::OwnedPayload::BindViews(Record& record)
    {
        if(!messageText.empty())
            record.message = messageText;

        record.src.file = sourceFileText.empty() ? nullptr : sourceFileText.c_str();
        record.src.func = sourceFuncText.empty() ? nullptr : sourceFuncText.c_str();

        if(callstackText)
            record.callstack = callstackText;

        if(!fieldViews.empty())
        {
            record.fields     = fieldViews.data();
            record.fieldCount = fieldViews.size();
        }
        else
        {
            record.fields     = nullptr;
            record.fieldCount = 0;
        }
    }

    void Logger::LoggerInternal::OwnedPayload::CaptureFrom(const Record& record, std::string&& ownedMessage)
    {
        Reset();

        if(!ownedMessage.empty())
            messageText = std::move(ownedMessage);
        else if(!record.message.empty())
            messageText.assign(record.message.data(), record.message.size());

        if(record.src.file != nullptr && record.src.file[0] != '\0')
            sourceFileText = record.src.file;
        if(record.src.func != nullptr && record.src.func[0] != '\0')
            sourceFuncText = record.src.func;

        if(record.callstack)
            callstackText = record.callstack;

        if(record.fieldCount == 0 || record.fields == nullptr)
            return;

        fieldText.reserve(record.fieldCount * 2);
        fieldViews.reserve(record.fieldCount);

        for(size_t index = 0; index < record.fieldCount; ++index)
        {
            fieldText.emplace_back(record.fields[index].key.data(), record.fields[index].key.size());
            fieldText.emplace_back(record.fields[index].value.data(), record.fields[index].value.size());

            Record::Field field;
            field.id    = record.fields[index].id;
            field.key   = fieldText[fieldText.size() - 2];
            field.value = fieldText.back();
            fieldViews.emplace_back(field);
        }
    }

    std::unique_ptr<Logger::LoggerInternal::Node> Logger::LoggerInternal::MakeNode(Record&& record,
                                                                                   std::string&& ownedMessage)
    {
        auto node    = std::make_unique<Node>();
        node->storageKind = Node::StorageKind::Heap;
        node->record = std::move(record);
        node->payload.CaptureFrom(node->record, std::move(ownedMessage));
        node->payload.BindViews(node->record);
        return node;
    }

    void Logger::LoggerInternal::InitializeRealtimePool()
    {
        realtimeNodes = std::make_unique<Node[]>(RealtimeNodePoolCapacity);

        for(size_t index = 0; index < RealtimeNodePoolCapacity; ++index)
        {
            realtimeNodes[index].storageKind = Node::StorageKind::RealtimePool;
            realtimeNodes[index].nextFree =
                (index + 1 < RealtimeNodePoolCapacity) ? &realtimeNodes[index + 1] : nullptr;
        }

        realtimeFreeList.store(realtimeNodes.get(), std::memory_order_release);
    }

    Logger::LoggerInternal::Node* Logger::LoggerInternal::AcquireRealtimeNode()
    {
        Node* head = realtimeFreeList.load(std::memory_order_acquire);
        while(head != nullptr)
        {
            Node* next = head->nextFree;
            if(realtimeFreeList.compare_exchange_weak(head, next, std::memory_order_acq_rel))
                return head;
        }

        return nullptr;
    }

    void Logger::LoggerInternal::ReleaseNode(Node* node)
    {
        if(node == nullptr)
            return;

        if(node->storageKind == Node::StorageKind::Heap)
        {
            delete node;
            return;
        }

        node->record                = {};
        node->payload.Reset();
        node->realtimeMessageLength = 0;

        Node* head = realtimeFreeList.load(std::memory_order_acquire);
        do
        {
            node->nextFree = head;
        } while(!realtimeFreeList.compare_exchange_weak(head, node, std::memory_order_acq_rel));
    }

    Logger::LoggerInternal::Node* Logger::LoggerInternal::MakeRealtimeNode(Record&& record,
                                                                           const detail::RealtimeTextArgCapture* formatArgs,
                                                                           size_t formatArgCount)
    {
        Node* node = AcquireRealtimeNode();
        if(node == nullptr)
            return nullptr;

        node->record                = std::move(record);
        node->payload.Reset();
        node->realtimeMessageLength = node->record.message.size();
        node->realtimeFormatStringStorageUsed = 0;

        if(node->realtimeMessageLength > RealtimeMessageCapacity)
        {
            ReleaseNode(node);
            return nullptr;
        }

        if(node->realtimeMessageLength > 0)
        {
            std::memcpy(node->realtimeMessage, node->record.message.data(), node->realtimeMessageLength);
            node->record.message = std::string_view(node->realtimeMessage, node->realtimeMessageLength);
        }
        else
        {
            node->record.message = {};
        }

        if(formatArgCount > RealtimeFormatMaxArgs)
        {
            ReleaseNode(node);
            return nullptr;
        }

        if(!node->record.realtimeFormat.empty())
        {
            for(size_t index = 0; index < formatArgCount; ++index)
            {
                std::string_view value;
                if(formatArgs[index].kind == detail::RealtimeTextArgCapture::Kind::Char)
                {
                    if(node->realtimeFormatStringStorageUsed + 1 > RealtimeFormatStringStorageCapacity)
                    {
                        ReleaseNode(node);
                        return nullptr;
                    }

                    node->realtimeFormatStringStorage[node->realtimeFormatStringStorageUsed] = formatArgs[index].character;
                    value = std::string_view(
                        &node->realtimeFormatStringStorage[node->realtimeFormatStringStorageUsed], 1);
                    node->realtimeFormatStringStorageUsed += 1;
                }
                else
                {
                    value = formatArgs[index].text;
                    if(node->realtimeFormatStringStorageUsed + value.size() > RealtimeFormatStringStorageCapacity)
                    {
                        ReleaseNode(node);
                        return nullptr;
                    }

                    if(!value.empty())
                    {
                        std::memcpy(
                            node->realtimeFormatStringStorage + node->realtimeFormatStringStorageUsed,
                            value.data(),
                            value.size());
                    }

                    value = std::string_view(
                        node->realtimeFormatStringStorage + node->realtimeFormatStringStorageUsed, value.size());
                    node->realtimeFormatStringStorageUsed += value.size();
                }

                node->realtimeFormatArgsViews[index] = value;
            }

            node->record.realtimeFormatArgs     = node->realtimeFormatArgsViews.data();
            node->record.realtimeFormatArgCount = formatArgCount;
        }
        else
        {
            node->record.realtimeFormatArgs     = nullptr;
            node->record.realtimeFormatArgCount = 0;
        }

        node->record.fields     = nullptr;
        node->record.fieldCount = 0;
        node->record.callstack.reset();
        return node;
    }

    void Logger::LoggerInternal::InitializeQueues(size_t capacity)
    {
        normalQueue.Initialize(static_cast<unsigned int>(capacity));
        const auto highCapacity = config.hiQueueCapacity < 2 ? 2u : static_cast<unsigned int>(config.hiQueueCapacity);
        highPriorityQueue.Initialize(highCapacity);
        InitializeRealtimePool();
    }

    bool Logger::LoggerInternal::EnqueueNormal(std::unique_ptr<Node>& node)
    {
        if(!node)
            return false;

        if(!normalQueue.TryEnqueueRaw(node.get()))
            return false;

        node.release();
        waiter.StopWait();
        return true;
    }

    bool Logger::LoggerInternal::EnqueueHighPriority(std::unique_ptr<Node>& node)
    {
        if(!node)
            return false;

        if(!highPriorityQueue.TryEnqueueRaw(node.get()))
            return false;

        node.release();
        waiter.StopWait();
        return true;
    }

    void Logger::LoggerInternal::ApplyPendingControls()
    {
        if(!controlPending.load(std::memory_order_acquire))
            return;

        std::vector<std::function<void(LoggerInternal&)>> ops;
        {
            std::lock_guard<std::mutex> lock(controlMutex);
            ops.swap(controlOps);
            controlPending.store(false, std::memory_order_release);
        }

        for(auto& op : ops)
            op(*this);
    }

    void Logger::LoggerInternal::RecordEnqueued(bool highPriority)
    {
        statsEnqueuedTotal.fetch_add(1, std::memory_order_relaxed);
        if(highPriority)
            statsEnqueuedHigh.fetch_add(1, std::memory_order_relaxed);
        else
            statsEnqueuedNormal.fetch_add(1, std::memory_order_relaxed);
    }

    void Logger::LoggerInternal::RecordDropped(Level level, bool isRealtime)
    {
        statsDroppedTotal.fetch_add(1, std::memory_order_relaxed);
        statsDroppedByLevel[static_cast<int>(level)].fetch_add(1, std::memory_order_relaxed);
        if(isRealtime)
            statsDroppedRealtime.fetch_add(1, std::memory_order_relaxed);
    }

    void Logger::LoggerInternal::UpdateQueueDepths()
    {
        statsQueueDepth.store(normalQueue.Count(), std::memory_order_relaxed);
        statsHighQueueDepth.store(highPriorityQueue.Count(), std::memory_order_relaxed);
    }

    void Logger::LoggerInternal::ApplyDropOldestRequests(Ecstatica::Recompiled::LogSupport::Algorithm::MPSCQueue<Node>& queue,
                                                         std::atomic<size_t>&                                 pendingCount)
    {
        // Multiple producers may call fetch_add concurrently. Each producer signals
        // the consumer, increments this counter, then retries its own enqueue once.
        // Because the retry happens immediately (before the consumer has had a chance
        // to drain), the retry may still see a full queue, and the newest record can
        // be dropped. This is by design: DropOldest is best-effort under sustained
        // overload, not a strict "always-accepts-latest" policy.
        size_t requested = pendingCount.exchange(0, std::memory_order_acq_rel);
        while(requested > 0)
        {
            Node* dropped = queue.TryDequeueRaw();
            if(!dropped)
                break;

            RecordDropped(dropped->record.level);
            ReleaseNode(dropped);
            --requested;
        }

        if(requested > 0)
            pendingCount.fetch_add(requested, std::memory_order_release);
    }

    bool Logger::LoggerInternal::PassesModuleFilters(const Record& record) const
    {
        if(record.moduleMask != 0)
        {
            if((config.moduleDenyMask & record.moduleMask) != 0)
                return false;

            if((config.moduleAllowMask & record.moduleMask) == 0)
                return false;

            if(!config.disableSubmoduleFiltering && record.submoduleMask != 0)
            {
                if(auto moduleId = SingleModuleFromMask(record.moduleMask))
                {
                    const auto denyIt = config.submoduleDenyMasks.find(*moduleId);
                    if(denyIt != config.submoduleDenyMasks.end() && (denyIt->second & record.submoduleMask) != 0)
                        return false;

                    const auto allowIt = config.submoduleAllowMasks.find(*moduleId);
                    if(allowIt != config.submoduleAllowMasks.end() && (allowIt->second & record.submoduleMask) == 0)
                        return false;
                }
            }

            return true;
        }

        return config.moduleAllowMask != 0;
    }

    void Logger::LoggerInternal::DrainQueue(Ecstatica::Recompiled::LogSupport::Algorithm::MPSCQueue<Node>& queue, bool highPriority)
    {
        for(;;)
        {
            Node* node = queue.TryDequeueRaw();
            if(!node)
                break;

            const Record& record = node->record;

            if(highPriority)
            {
                if(record.level == Level::Error && !PassesModuleFilters(record))
                {
                    ReleaseNode(node);
                    continue;
                }
            }
            else
            {
                if(!PassesModuleFilters(record))
                {
                    ReleaseNode(node);
                    continue;
                }

                Level    minimumLevel    = config.globalLevel;
                bool     levelOverridden = false;

                ModuleID resolvedModule  = record.module;
                if(resolvedModule == ModuleID::None)
                {
                    if(auto moduleId = SingleModuleFromMask(record.moduleMask))
                        resolvedModule = *moduleId;
                }

                if(resolvedModule != ModuleID::None)
                {
                    const auto moduleLevelIt = moduleLevels.find(resolvedModule);
                    if(moduleLevelIt != moduleLevels.end())
                    {
                        minimumLevel    = moduleLevelIt->second;
                        levelOverridden = true;
                    }

                    if(!levelOverridden && config.moduleMinLevelMask)
                    {
                        if(auto custom = config.moduleMinLevelMask(resolvedModule, record.submoduleMask))
                        {
                            minimumLevel    = *custom;
                            levelOverridden = true;
                        }
                    }
                }

                if(static_cast<int>(record.level) < static_cast<int>(minimumLevel))
                {
                    ReleaseNode(node);
                    continue;
                }

                if(config.rateLimit && !config.rateLimit(record))
                {
                    ReleaseNode(node);
                    continue;
                }
            }

            {
                std::lock_guard<std::mutex> lock(sinksMutex);
                for(auto& sink : sinks)
                    sink->Write(record);

                if(record.level == Level::Fatal)
                {
                    for(auto& sink : sinks)
                        sink->Flush();
                }
            }

            statsDrainedTotal.fetch_add(1, std::memory_order_relaxed);

            ReleaseNode(node);
        }
    }

    void Logger::LoggerInternal::DrainOnce()
    {
        ApplyPendingControls();
        ApplyDropOldestRequests(highPriorityQueue, pendingDropOldestHigh);
        DrainQueue(highPriorityQueue, true);

        ApplyDropOldestRequests(normalQueue, pendingDropOldestNormal);
        DrainQueue(normalQueue, false);
        UpdateQueueDepths();
    }
}
