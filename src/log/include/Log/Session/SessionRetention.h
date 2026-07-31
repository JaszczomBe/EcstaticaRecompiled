#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace Ecstatica::Recompiled::Log::Session
{
    struct RetentionPolicy
    {
        unsigned int  minSessions = 10;
        std::uint64_t maxTotalSizeBytes = 128ULL * 1024ULL * 1024ULL;
    };

    struct Metadata
    {
        std::string   appId;
        std::string   deviceName;
        std::string   rootLogFileBaseName;
        std::uint64_t rotateBytes = 0;
        unsigned int  retentionMinSessions = 10;
        unsigned int  retentionMaxTotalSizeMb = 128;
    };

    struct CleanupSummary
    {
        std::size_t   scannedSessions = 0;
        std::size_t   keptSessions = 0;
        std::size_t   removedSessions = 0;
        std::size_t   failedRemovals = 0;
        std::uint64_t freedBytes = 0;
        std::uint64_t retainedBytes = 0;
        bool          minSessionFloorPreventedBudgetCompliance = false;
    };

    struct StartupSession
    {
        std::string    sessionDirectory;
        std::string    logFilePath;
        CleanupSummary cleanup;
    };

    StartupSession PrepareStartupSession(std::string_view logsRoot,
                                         std::string_view baseFileName,
                                         const RetentionPolicy& policy,
                                         Metadata metadata);

    void UpdateStartupSessionMetadata(std::string_view sessionDirectory,
                                      Metadata metadata);

    std::string FormatCleanupSummary(const CleanupSummary& summary);
}
