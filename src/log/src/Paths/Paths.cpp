#include "Log/Paths/Paths.h"
#include "LogSupport/IO/FileSystemIO.h"
#include "LogSupport/String/Path.h"
#include <iomanip>
#include <chrono>
#include <ctime>
#include <cstdio>
#include <sstream>
#include <filesystem>

namespace Ecstatica::Recompiled::Log::Paths
{
    static std::string g_root;
    static std::string g_session;

    const std::string& LogsRoot()
    {
        if (g_root.empty())
        {
            g_root = "data/logs";
            Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::CreateDirectory(g_root);
        }
        return g_root;
    }

    std::string BuildSessionDir(std::string_view logsRoot)
    {
        if (logsRoot.empty())
            return {};

        const auto normalizedRoot = Ecstatica::Recompiled::LogSupport::String::Path::EnsureTrailingSlash(std::string(logsRoot));
        if (!Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::CreateDirectory(normalizedRoot))
            return {};

        using namespace std::chrono;
        const auto now = system_clock::now();
        // Create exclusively: simultaneous launches must never share a session.
        for (unsigned attempt = 0; attempt < 1000; ++attempt)
        {
            const auto candidate = now + milliseconds(attempt);
            const auto tt = system_clock::to_time_t(candidate);
            const auto ms = duration_cast<milliseconds>(candidate.time_since_epoch()) % 1000;

            std::tm tm{};
    #if defined(_WIN32)
            localtime_s(&tm, &tt);
    #else
            localtime_r(&tt, &tm);
    #endif

            std::ostringstream sessionName;
            sessionName << "session_" << std::put_time(&tm, "%Y%m%d_%H%M%S")
                        << '_' << std::setw(3) << std::setfill('0') << ms.count();

            const auto sessionDir = Join(normalizedRoot, sessionName.str());
            std::error_code ec;
            if (std::filesystem::create_directory(sessionDir, ec))
                return sessionDir;
            if (ec && ec != std::errc::file_exists)
                return {};
        }
        return {};
    }

    std::string BuildSessionFilePath(std::string_view logsRoot, std::string_view fileName)
    {
        const auto sessionDir = BuildSessionDir(logsRoot);
        if (sessionDir.empty())
            return {};
        return Join(sessionDir, std::string(fileName));
    }

    const std::string& SessionDir()
    {
        if (g_session.empty())
        {
            g_session = BuildSessionDir(LogsRoot());
        }
        return g_session;
    }

    std::string Join(const std::string& a, const std::string& b)
    {
        if (a.empty()) return b;
        if (b.empty()) return a;
        if (a.back() == '/') return a + b;
        return a + "/" + b;
    }
}
