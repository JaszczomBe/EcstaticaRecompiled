#pragma once
#include <string>
#include <chrono>
#include <map>

namespace Ecstatica::Recompiled::LogSupport::IO
{

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

        static int          SearchFiles(const std::string& directoryPath, const std::string& fileName, TimeFileMap& results);
        static TimePoint    GetModificationTime(const std::string& filePath);        
    };


}
