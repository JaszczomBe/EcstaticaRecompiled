#include "Log/Session/SessionRetention.h"

#include "LogSupport/IO/FileSystemIO.h"
#include "Log/Paths/Paths.h"
#include "LogSupport/String/Path.h"
#include "RunArtifacts.h"
#include <cerrno>

#include <chrono>
#include <cstdio>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <system_error>
#include <vector>

#if defined(_WIN32)
#include <process.h>
#include <windows.h>
#else
#include <unistd.h>
#include <signal.h>
#endif

namespace Ecstatica::Recompiled::Log::Session
{
    namespace
    {
        namespace fs = std::filesystem;

        constexpr char kSessionPrefix[] = "session_";
        constexpr char kSessionMetaFileName[] = "session.meta";
        constexpr int kSessionNameLength = 27; // session_YYYYMMDD_HHMMSS_mmm

        struct ExistingSession
        {
            fs::path     path;
            std::string  sessionId;
            std::uint64_t sizeBytes = 0;
        };

        std::string JsonEscape(std::string_view input)
        {
            std::string output;
            output.reserve(input.size() + 8);

            for (const char ch : input)
            {
                switch (ch)
                {
                    case '\\': output += "\\\\"; break;
                    case '"': output += "\\\""; break;
                    case '\n': output += "\\n"; break;
                    case '\r': output += "\\r"; break;
                    case '\t': output += "\\t"; break;
                    default: output += ch; break;
                }
            }

            return output;
        }

        std::string FormatTimestamp(std::chrono::system_clock::time_point timestamp, bool utc)
        {
            const auto tt = std::chrono::system_clock::to_time_t(timestamp);
            const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(timestamp.time_since_epoch()) % 1000;

            std::tm tm{};
        #if defined(_WIN32)
            if (utc)
                gmtime_s(&tm, &tt);
            else
                localtime_s(&tm, &tt);
        #else
            if (utc)
                gmtime_r(&tt, &tm);
            else
                localtime_r(&tt, &tm);
        #endif

            std::ostringstream stream;
            stream << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S")
                   << '.'
                   << std::setw(3) << std::setfill('0') << ms.count();
            if (utc)
                stream << 'Z';
            return stream.str();
        }

        bool IsDigits(std::string_view token)
        {
            for (const char ch : token)
            {
                if (ch < '0' || ch > '9')
                    return false;
            }
            return !token.empty();
        }

        bool IsSessionDirectoryName(std::string_view name)
        {
            if (name.size() != static_cast<std::size_t>(kSessionNameLength))
                return false;
            if (name.substr(0, sizeof(kSessionPrefix) - 1) != kSessionPrefix)
                return false;
            if (name[16] != '_' || name[23] != '_')
                return false;

            return IsDigits(name.substr(8, 8)) &&
                   IsDigits(name.substr(17, 6)) &&
                   IsDigits(name.substr(24, 3));
        }

        std::uint64_t ComputeDirectorySize(const fs::path& directory)
        {
            std::uint64_t sizeBytes = 0;
            std::error_code ec;

            for (fs::recursive_directory_iterator it(directory, fs::directory_options::skip_permission_denied, ec), end;
                 it != end;
                 it.increment(ec))
            {
                if (ec)
                    continue;

                std::error_code statusEc;
                if (!it->is_symlink(statusEc) && it->is_regular_file(statusEc))
                {
                    const auto fileSize = it->file_size(statusEc);
                    if (!statusEc)
                        sizeBytes += static_cast<std::uint64_t>(fileSize);
                }
            }

            return sizeBytes;
        }

        std::vector<ExistingSession> CollectSessions(const fs::path& logsRoot)
        {
            std::vector<ExistingSession> sessions;
            std::error_code ec;

            if (!fs::exists(logsRoot, ec))
                return sessions;

            for (fs::directory_iterator it(logsRoot, fs::directory_options::skip_permission_denied, ec), end;
                 it != end;
                 it.increment(ec))
            {
                if (ec)
                    continue;

                std::error_code statusEc;
                if (it->is_symlink(statusEc) || !it->is_directory(statusEc))
                    continue;

                const auto sessionId = it->path().filename().string();
                if (!IsSessionDirectoryName(sessionId))
                    continue;

                sessions.push_back(ExistingSession{
                    it->path(),
                    sessionId,
                    ComputeDirectorySize(it->path()),
                });
            }

            std::sort(sessions.begin(),
                      sessions.end(),
                      [](const ExistingSession& lhs, const ExistingSession& rhs)
                      {
                          return lhs.sessionId > rhs.sessionId;
                      });

            return sessions;
        }

        bool RemoveSessionDirectory(const fs::path& directory)
        {
            std::error_code ec;
            fs::remove_all(directory, ec);
            return !ec;
        }

        std::string FormatMiB(std::uint64_t bytes)
        {
            std::ostringstream stream;
            stream << std::fixed << std::setprecision(1)
                   << (static_cast<double>(bytes) / (1024.0 * 1024.0))
                   << " MiB";
            return stream.str();
        }

        bool WriteSessionMetadata(const fs::path& sessionDirectory,
                                  const std::string& sessionId,
                                  const Metadata& metadata,
                                  const RetentionPolicy& policy)
        {
            const auto now = std::chrono::system_clock::now();
            const auto metaPath = sessionDirectory / kSessionMetaFileName;
            const auto tempPath = sessionDirectory / "session.meta.tmp";

            const auto nowLocal = FormatTimestamp(now, false);
            const auto nowUtc = FormatTimestamp(now, true);
        #if defined(_WIN32)
            const auto pid = static_cast<unsigned long long>(_getpid());
        #else
            const auto pid = static_cast<unsigned long long>(getpid());
        #endif

        #if defined(NDEBUG)
            const char* buildType = "Release";
        #else
            const char* buildType = "Debug";
        #endif

            std::ofstream output(tempPath, std::ios::out | std::ios::trunc);
            if (!output.good())
                return false;

            output << "{\n"
                   << "  \"schemaVersion\": 2,\n"
                   << "  \"appId\": \"" << JsonEscape(metadata.appId) << "\",\n"
                   << "  \"sessionId\": \"" << JsonEscape(sessionId) << "\",\n"
                   << "  \"createdAtLocal\": \"" << JsonEscape(nowLocal) << "\",\n"
                   << "  \"createdAtUtc\": \"" << JsonEscape(nowUtc) << "\",\n"
                   << "  \"pid\": " << pid << ",\n"
                   << "  \"buildType\": \"" << buildType << "\",\n"
                   << "  \"rootLogFileBaseName\": \"" << JsonEscape(metadata.rootLogFileBaseName) << "\",\n"
                   << "  \"rotateBytes\": " << metadata.rotateBytes << ",\n"
                   << "  \"retentionMaxSessions\": " << policy.maxSessions << ",\n"
                   << "  \"retentionMinimumSessions\": " << RetentionPolicy::minimumSessions << ",\n"
                   << "  \"retentionBudgetScope\": \"older-than-newest-five\",\n"
                   << "  \"retentionMaxTotalSizeMb\": " << (policy.maxTotalSizeBytes / (1024 * 1024)) << "\n"
                   << "}\n";
            output.close();

            if (!output.good())
            {
                std::error_code removeEc;
                fs::remove(tempPath, removeEc);
                return false;
            }

            std::error_code ec;
            fs::rename(tempPath, metaPath, ec);
            if (ec)
                fs::remove(tempPath);
            return !ec;
        }

        bool LegacySessionIsActive(const fs::path& metadata)
        {
            std::ifstream input(metadata);
            std::string line;
            while (std::getline(input, line))
            {
                const auto field = line.find("\"pid\":");
                if (field == std::string::npos)
                    continue;
                std::istringstream value(line.substr(field + 6));
                unsigned long pid = 0;
                if (!(value >> pid) || pid == 0)
                    return false;
#if defined(_WIN32)
                HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
                if (!process)
                    return GetLastError() == ERROR_ACCESS_DENIED;
                DWORD code = 0;
                const bool active = GetExitCodeProcess(process, &code) && code == STILL_ACTIVE;
                CloseHandle(process);
                return active;
#else
                return kill(static_cast<pid_t>(pid), 0) == 0 || errno == EPERM;
#endif
            }
            return false;
        }

        CleanupSummary CleanupUnlocked(const fs::path& logsRoot, const RetentionPolicy& policy)
        {
            CleanupSummary summary;
            const auto sessions = CollectSessions(logsRoot);
            summary.scannedSessions = summary.keptSessions = sessions.size();
            for (const auto& session : sessions)
                summary.retainedBytes += session.sizeBytes;
            const auto olderCount = sessions.size() > RetentionPolicy::minimumSessions
                ? sessions.size() - RetentionPolicy::minimumSessions : 0;
            for (std::size_t i = RetentionPolicy::minimumSessions; i < sessions.size(); ++i)
                summary.olderBytes += sessions[i].sizeBytes;
            const auto countLimit = std::max(policy.maxSessions, RetentionPolicy::minimumSessions);
            std::size_t visited = 0;
            for (auto it = sessions.rbegin(); it != sessions.rend(); ++it)
            {
                if (visited++ >= olderCount)
                    break;
                if (summary.keptSessions <= countLimit && summary.olderBytes <= policy.maxTotalSizeBytes)
                    break;
                // F5 marks pending/failed investigations while its active lease
                // is held. Keep their evidence until explicitly released.
                if (fs::exists(it->path / "investigation.keep"))
                {
                    ++summary.protectedSessions;
                    continue;
                }
                const auto leasePath = it->path / "session.active.lock";
                // Pre-lease sessions can belong to an older, still-running build.
                if (!fs::exists(leasePath) && LegacySessionIsActive(it->path / kSessionMetaFileName))
                {
                    ++summary.protectedSessions;
                    continue;
                }
                auto lease = LogSupport::IO::FileLock::TryAcquire(leasePath.string());
                if (!lease)
                {
                    ++summary.protectedSessions;
                    continue;
                }
                // All session creation/cleanup holds the root lease, and sessions
                // are never reactivated. Close this handle before removal so
                // Windows can remove the directory containing the lease file.
                lease.reset();
                if (RemoveSessionDirectory(it->path))
                {
                    ++summary.removedSessions;
                    --summary.keptSessions;
                    summary.freedBytes += it->sizeBytes;
                    summary.retainedBytes -= it->sizeBytes;
                    summary.olderBytes -= it->sizeBytes;
                }
                else
                    ++summary.failedRemovals;
            }
            summary.overBudget = summary.keptSessions > countLimit || summary.olderBytes > policy.maxTotalSizeBytes;
            return summary;
        }
    }

    StartupSession PrepareStartupSession(std::string_view logsRoot,
                                         std::string_view baseFileName,
                                         const RetentionPolicy& policy,
                                         const Metadata& metadata)
    {
        StartupSession session;
        if (logsRoot.empty() || baseFileName.empty() || !LogSupport::IO::FileSystemIO::CreateDirectory(std::string(logsRoot)))
            return session;
        auto rootLease = LogSupport::IO::FileLock::TryAcquire(Paths::Join(std::string(logsRoot), ".retention.lock"), true);
        if (!rootLease)
            return session;
        session.sessionDirectory = Paths::BuildSessionDir(logsRoot);
        if (session.sessionDirectory.empty())
            return session;
        session.lease = LogSupport::IO::FileLock::TryAcquire(Paths::Join(session.sessionDirectory, "session.active.lock"));
        if (!session.lease || !WriteSessionMetadata(session.sessionDirectory,
                fs::path(session.sessionDirectory).filename().string(), metadata, policy))
            return {};
        session.logFilePath = Paths::Join(session.sessionDirectory, std::string(baseFileName));
        session.cleanup = CleanupUnlocked(std::string(logsRoot), policy);
        return session;
    }

    CleanupSummary CleanupSessions(std::string_view logsRoot, const RetentionPolicy& policy)
    {
        auto rootLease = LogSupport::IO::FileLock::TryAcquire(Paths::Join(std::string(logsRoot), ".retention.lock"));
        return rootLease ? CleanupUnlocked(std::string(logsRoot), policy) : CleanupSummary{};
    }

    Maintenance::Maintenance(std::string logsRoot, RetentionPolicy policy, StartupSession startup)
        : session(std::move(startup)), worker([this, logsRoot = std::move(logsRoot), policy] {
            std::unique_lock lock(mutex);
            while (!wake.wait_for(lock, policy.cleanupInterval, [this] { return stopped; }))
            {
                lock.unlock();
                try
                {
                    const auto summary = CleanupSessions(logsRoot, policy);
                    if (summary.removedSessions || summary.failedRemovals || summary.overBudget)
                        E2R_ArtifactsReport(FormatCleanupSummary(summary).c_str());
                }
                catch (const std::exception& error)
                {
                    E2R_ArtifactsReport((std::string("Log cleanup failed: ") + error.what()).c_str());
                }
                lock.lock();
            }
        })
    {
    }

    Maintenance::~Maintenance() { Stop(); }

    void Maintenance::Stop()
    {
        { std::lock_guard lock(mutex); stopped = true; }
        wake.notify_all();
        if (worker.joinable())
            worker.join();
    }

    std::string FormatCleanupSummary(const CleanupSummary& summary)
    {
        std::ostringstream stream;
        stream << "Log cleanup: scanned=" << summary.scannedSessions
               << " kept=" << summary.keptSessions
               << " removed=" << summary.removedSessions;

        stream << " protected=" << summary.protectedSessions;

        if (summary.failedRemovals > 0)
            stream << " failedRemovals=" << summary.failedRemovals;

        stream << " freed=" << FormatMiB(summary.freedBytes)
               << " retained=" << FormatMiB(summary.retainedBytes);
        stream << " older=" << FormatMiB(summary.olderBytes);

        if (summary.overBudget)
            stream << " (budget exceeded; active/retained investigations or removal failures protected)";

        return stream.str();
    }
}
