#pragma once

#include "LogSupport/IO/FileSystemIO.h"
#include <chrono>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <string>
#include <string_view>
#include <thread>

namespace Ecstatica::Recompiled::Log::Session
{
    struct RetentionPolicy
    {
        unsigned maxSessions = 100;
        std::uint64_t maxTotalSizeBytes = 128ULL * 1024ULL * 1024ULL;
        std::chrono::seconds cleanupInterval{60};
    };

    struct Metadata
    {
        std::string appId;
        std::string rootLogFileBaseName;
        std::uint64_t rotateBytes = 0;
    };

    struct CleanupSummary
    {
        std::size_t scannedSessions = 0, keptSessions = 0, removedSessions = 0;
        std::size_t failedRemovals = 0, protectedSessions = 0;
        std::uint64_t freedBytes = 0, retainedBytes = 0;
        bool overBudget = false;
    };

    struct StartupSession
    {
        std::string sessionDirectory;
        std::string logFilePath;
        CleanupSummary cleanup;
        std::unique_ptr<LogSupport::IO::FileLock> lease;
    };

    StartupSession PrepareStartupSession(std::string_view logsRoot,
                                         std::string_view baseFileName,
                                         const RetentionPolicy& policy,
                                         const Metadata& metadata);
    CleanupSummary CleanupSessions(std::string_view logsRoot, const RetentionPolicy& policy);
    std::string FormatCleanupSummary(const CleanupSummary& summary);

    // Owns the active lease until logging has stopped; cleanup never runs on a producer.
    class Maintenance
    {
    public:
        Maintenance(std::string logsRoot, RetentionPolicy policy, StartupSession session);
        ~Maintenance();
        void Stop();
    private:
        StartupSession session;
        std::mutex mutex;
        std::condition_variable wake;
        bool stopped = false;
        std::thread worker;
    };
}
