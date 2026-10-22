#pragma once
#include <string>
#include <chrono>
#include <map>
#include <memory>
#include <cstdint>
#include <cstdio>

namespace Ecstatica::Recompiled::LogSupport::IO
{
    // Nonblocking, cross-process lease. The OS releases it on normal exit or crash.
    // Keep the lock file on disk: unlinking it can split concurrent lock owners.
    class FileLock
    {
    public:
        static std::unique_ptr<FileLock> TryAcquire(const std::string& path, bool wait = false);
        ~FileLock();
        FileLock(const FileLock&) = delete;
        FileLock& operator=(const FileLock&) = delete;
    private:
        explicit FileLock(std::intptr_t handle) : handle(handle) {}
        std::intptr_t handle;
    };

    using TimePoint     = std::chrono::system_clock::time_point;
    using TimeFileMap   = std::map<TimePoint, std::string>;

    class FileSystemIO
    {
    public:
        static bool         Exists(const std::string &path);
        static bool         CreateDirectory(const std::string &path);
        static long         GetFileSize(const std::string& path);
        static bool         CopyFile(const std::string& from, const std::string& to);
        static bool         Delete(const std::string& target);
        static bool         SyncFile(std::FILE* file);

        static int          SearchFiles(const std::string& directoryPath, const std::string& fileName, TimeFileMap& results);
        static TimePoint    GetModificationTime(const std::string& filePath);        
    };


}
