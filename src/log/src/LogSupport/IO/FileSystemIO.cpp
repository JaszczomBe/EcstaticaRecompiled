#include "LogSupport/IO/FileSystemIO.h"

#include <filesystem>

namespace Ecstatica::Recompiled::LogSupport::IO
{
    bool FileSystemIO::Exists(const std::string& path)
    {
        return std::filesystem::exists(path);
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
