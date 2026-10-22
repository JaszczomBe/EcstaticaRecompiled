#include "LogSupport/IO/FileSystemIO.h"

#include <filesystem>
#if defined(_WIN32)
#include <windows.h>
#include <io.h>
#else
#include <fcntl.h>
#include <sys/file.h>
#include <unistd.h>
#endif

namespace Ecstatica::Recompiled::LogSupport::IO
{
    std::unique_ptr<FileLock> FileLock::TryAcquire(const std::string& path, bool wait)
    {
#if defined(_WIN32)
        HANDLE handle = CreateFileA(path.c_str(), GENERIC_READ | GENERIC_WRITE,
                                   FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                   nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (handle == INVALID_HANDLE_VALUE)
            return {};
        OVERLAPPED position{};
        if (!LockFileEx(handle, LOCKFILE_EXCLUSIVE_LOCK | (wait ? 0 : LOCKFILE_FAIL_IMMEDIATELY),
                        0, 1, 0, &position))
        {
            CloseHandle(handle);
            return {};
        }
        return std::unique_ptr<FileLock>(new FileLock(reinterpret_cast<std::intptr_t>(handle)));
#else
        const int handle = open(path.c_str(), O_RDWR | O_CREAT | O_CLOEXEC | O_NOFOLLOW, 0600);
        if (handle < 0)
            return {};
        if (flock(handle, LOCK_EX | (wait ? 0 : LOCK_NB)) != 0)
        {
            close(handle);
            return {};
        }
        return std::unique_ptr<FileLock>(new FileLock(handle));
#endif
    }

    FileLock::~FileLock()
    {
#if defined(_WIN32)
        CloseHandle(reinterpret_cast<HANDLE>(handle));
#else
        close(static_cast<int>(handle));
#endif
    }

    bool FileSystemIO::SyncFile(std::FILE* file)
    {
        if (!file || std::fflush(file) != 0)
            return false;
#if defined(_WIN32)
        return _commit(_fileno(file)) == 0;
#else
        return fsync(fileno(file)) == 0;
#endif
    }

    bool FileSystemIO::Exists(const std::string& path)
    {
        std::error_code ec;
        return std::filesystem::exists(path, ec);
    }

    bool FileSystemIO::CreateDirectory(const std::string& path)
    {
        if (path.empty())
            return false;

        std::error_code ec;
        if (std::filesystem::exists(path, ec))
            return std::filesystem::is_directory(path, ec);

        return std::filesystem::create_directories(path, ec) || std::filesystem::is_directory(path, ec);
    }

    long FileSystemIO::GetFileSize(const std::string& path)
    {
        std::error_code ec;
        const auto size = std::filesystem::file_size(path, ec);
        if (ec)
            return -1;
        return static_cast<long>(size);
    }

    bool FileSystemIO::CopyFile(const std::string& from, const std::string& to)
    {
        std::error_code ec;
        std::filesystem::copy_file(from, to, std::filesystem::copy_options::overwrite_existing, ec);
        return !ec;
    }

    bool FileSystemIO::Delete(const std::string& target)
    {
        std::error_code ec;
        return std::filesystem::remove(target, ec);
    }

    int FileSystemIO::SearchFiles(const std::string& directoryPath, const std::string& fileName, TimeFileMap& results)
    {
        std::error_code ec;
        if (!std::filesystem::is_directory(directoryPath, ec))
            return -1;

        for (const auto& entry : std::filesystem::recursive_directory_iterator(directoryPath, ec))
        {
            if (ec)
                break;
            if (!entry.is_regular_file(ec) || ec)
                continue;
            if (entry.path().filename() != fileName)
                continue;
            results[GetModificationTime(entry.path().string())] = entry.path().string();
        }

        return static_cast<int>(results.size());
    }

    TimePoint FileSystemIO::GetModificationTime(const std::string& filePath)
    {
        std::error_code ec;
        const auto fileTime = std::filesystem::last_write_time(filePath, ec);
        if (ec)
            return TimePoint();

        const auto nowFile = std::filesystem::file_time_type::clock::now();
        const auto nowSystem = std::chrono::system_clock::now();
        const auto systemTime = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
            fileTime - nowFile + nowSystem);
        return systemTime;
    }
}
