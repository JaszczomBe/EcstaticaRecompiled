#include "Log/Session/SessionRetention.h"

#include "LogSupport/IO/FileSystemIO.h"
#include "Log/Paths/Paths.h"
#include "LogSupport/String/Path.h"

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
#else
#include <unistd.h>
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
                if (it->is_regular_file(statusEc))
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
                if (!it->is_directory(statusEc))
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

        std::string ReadJsonStringField(const fs::path& path, std::string_view fieldName)
        {
            std::ifstream input(path, std::ios::in);
            if (!input.good())
                return {};

            std::ostringstream buffer;
            buffer << input.rdbuf();
            const auto content = buffer.str();
            const std::string pattern = "\"" + std::string(fieldName) + "\": \"";
            const auto start = content.find(pattern);
            if (start == std::string::npos)
                return {};

            const auto valueStart = start + pattern.size();
            std::string value;
            bool escaped = false;
            for (std::size_t index = valueStart; index < content.size(); ++index)
            {
                const char ch = content[index];
                if (escaped)
                {
                    value += ch;
                    escaped = false;
                    continue;
                }
                if (ch == '\\')
                {
                    escaped = true;
                    continue;
                }
                if (ch == '"')
                    return value;
                value += ch;
            }

            return {};
        }

        void WriteSessionMetadata(const fs::path& sessionDirectory,
                                  const std::string& sessionId,
                                  const Metadata& metadata,
                                  bool preserveCreationTimestamp)
        {
            const auto now = std::chrono::system_clock::now();
            const auto metaPath = sessionDirectory / kSessionMetaFileName;
            const auto tempPath = sessionDirectory / "session.meta.tmp";

            const auto nowLocal = FormatTimestamp(now, false);
            const auto nowUtc = FormatTimestamp(now, true);
            std::string createdAtLocal = preserveCreationTimestamp
                ? ReadJsonStringField(metaPath, "createdAtLocal")
                : std::string{};
            std::string createdAtUtc = preserveCreationTimestamp
                ? ReadJsonStringField(metaPath, "createdAtUtc")
                : std::string{};
            if (createdAtLocal.empty())
                createdAtLocal = nowLocal;
            if (createdAtUtc.empty())
                createdAtUtc = nowUtc;

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
                return;

            output << "{\n"
                   << "  \"schemaVersion\": 1,\n"
                   << "  \"appId\": \"" << JsonEscape(metadata.appId) << "\",\n"
                   << "  \"sessionId\": \"" << JsonEscape(sessionId) << "\",\n"
                   << "  \"createdAtLocal\": \"" << JsonEscape(createdAtLocal) << "\",\n"
                   << "  \"createdAtUtc\": \"" << JsonEscape(createdAtUtc) << "\",\n"
                   << (preserveCreationTimestamp
                        ? "  \"metadataUpdatedAtLocal\": \"" + JsonEscape(nowLocal) + "\",\n"
                        : "")
                   << (preserveCreationTimestamp
                        ? "  \"metadataUpdatedAtUtc\": \"" + JsonEscape(nowUtc) + "\",\n"
                        : "")
                   << "  \"pid\": " << pid << ",\n"
                   << "  \"deviceName\": \"" << JsonEscape(metadata.deviceName) << "\",\n"
                   << "  \"buildType\": \"" << buildType << "\",\n"
                   << "  \"rootLogFileBaseName\": \"" << JsonEscape(metadata.rootLogFileBaseName) << "\",\n"
                   << "  \"rotateBytes\": " << metadata.rotateBytes << ",\n"
                   << "  \"retentionMinSessions\": " << metadata.retentionMinSessions << ",\n"
                   << "  \"retentionMaxTotalSizeMb\": " << metadata.retentionMaxTotalSizeMb << "\n"
                   << "}\n";
            output.close();

            if (!output.good())
            {
                std::error_code removeEc;
                fs::remove(tempPath, removeEc);
                return;
            }

            std::error_code ec;
            fs::rename(tempPath, metaPath, ec);
            if (!ec)
                return;

            std::error_code removeEc;
            fs::remove(metaPath, removeEc);
            fs::rename(tempPath, metaPath, ec);
            if (ec)
                fs::remove(tempPath, removeEc);
        }
    }

    StartupSession PrepareStartupSession(std::string_view logsRoot,
                                         std::string_view baseFileName,
                                         const RetentionPolicy& policy,
                                         Metadata metadata)
    {
        StartupSession startupSession;
        if (logsRoot.empty() || baseFileName.empty())
            return startupSession;

        const auto normalizedLogsRoot = Ecstatica::Recompiled::LogSupport::String::Path::EnsureTrailingSlash(std::string(logsRoot));
        Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::CreateDirectory(normalizedLogsRoot);

        auto sessions = CollectSessions(normalizedLogsRoot);
        startupSession.cleanup.scannedSessions = sessions.size();
        startupSession.cleanup.keptSessions = sessions.size();

        for (const auto& session : sessions)
            startupSession.cleanup.retainedBytes += session.sizeBytes;

        const auto minSessions = std::max(1U, policy.minSessions);
        for (std::size_t index = sessions.size(); index > minSessions && startupSession.cleanup.retainedBytes > policy.maxTotalSizeBytes; --index)
        {
            const auto& session = sessions[index - 1];
            if (RemoveSessionDirectory(session.path))
            {
                startupSession.cleanup.removedSessions += 1;
                startupSession.cleanup.keptSessions -= 1;
                startupSession.cleanup.freedBytes += session.sizeBytes;
                startupSession.cleanup.retainedBytes -= session.sizeBytes;
            }
            else
            {
                startupSession.cleanup.failedRemovals += 1;
            }
        }

        startupSession.cleanup.minSessionFloorPreventedBudgetCompliance =
            startupSession.cleanup.retainedBytes > policy.maxTotalSizeBytes &&
            startupSession.cleanup.keptSessions <= minSessions;

        startupSession.sessionDirectory = Paths::BuildSessionDir(normalizedLogsRoot);
        if (startupSession.sessionDirectory.empty())
            return startupSession;

        startupSession.logFilePath = Paths::Join(startupSession.sessionDirectory, std::string(baseFileName));

        const fs::path sessionPath(startupSession.sessionDirectory);
        WriteSessionMetadata(sessionPath, sessionPath.filename().string(), metadata, false);
        return startupSession;
    }

    void UpdateStartupSessionMetadata(std::string_view sessionDirectory,
                                      Metadata metadata)
    {
        if (sessionDirectory.empty())
            return;

        const fs::path sessionPath{std::string(sessionDirectory)};
        WriteSessionMetadata(sessionPath, sessionPath.filename().string(), metadata, true);
    }

    std::string FormatCleanupSummary(const CleanupSummary& summary)
    {
        std::ostringstream stream;
        stream << "Log cleanup: scanned=" << summary.scannedSessions
               << " kept=" << summary.keptSessions
               << " removed=" << summary.removedSessions;

        if (summary.failedRemovals > 0)
            stream << " failedRemovals=" << summary.failedRemovals;

        stream << " freed=" << FormatMiB(summary.freedBytes)
               << " retained=" << FormatMiB(summary.retainedBytes);

        if (summary.minSessionFloorPreventedBudgetCompliance)
            stream << " (above size limit; min-session floor preserved)";

        return stream.str();
    }
}
