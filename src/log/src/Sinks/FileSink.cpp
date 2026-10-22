#include "Log/Sinks/FileSink.h"
#include "Log/Core/Format.h"
#include "Log/Core/Level.h"
#include "LogSupport/IO/FileSystemIO.h"
#include <chrono>
#include <cerrno>
#include <cstring>
#include <ctime>
#include <iomanip>
#include <sstream>

namespace Ecstatica::Recompiled::Log
{
    static void split_path(const std::string& path, std::string& dir, std::string& fname)
    {
        auto pos = path.find_last_of('/');
        if (pos == std::string::npos)
        {
            dir.clear();
            fname = path;
        }
        else
        {
            dir = path.substr(0, pos);
            fname = path.substr(pos + 1);
        }
    }

    static void split_stem_ext(const std::string& fname, std::string& stem, std::string& ext)
    {
        auto dot = fname.find_last_of('.');
        if (dot == std::string::npos || dot == 0)
        {
            stem = fname;
            ext.clear();
        }
        else
        {
            stem = fname.substr(0, dot);
            ext = fname.substr(dot); // includes dot
        }
    }

    static std::string timestamped_name(const std::string& path, unsigned long long sequence)
    {
        std::string dir, fname; split_path(path, dir, fname);
        std::string stem, ext; split_stem_ext(fname, stem, ext);

        using namespace std::chrono;
        const auto now = system_clock::now();
        const auto tt = system_clock::to_time_t(now);
        const auto ms = duration_cast<milliseconds>(now.time_since_epoch()) % 1000;

        std::tm tm{};
    #if defined(_WIN32)
        localtime_s(&tm, &tt);
    #else
        localtime_r(&tt, &tm);
    #endif

        std::ostringstream out;
        if (!dir.empty())
            out << dir << '/';
        out << stem << '_' << std::put_time(&tm, "%Y%m%d_%H%M%S")
            << '_' << std::setw(3) << std::setfill('0') << ms.count()
            << '_' << std::setw(4) << std::setfill('0') << sequence
            << ext;
        return out.str();
    }

    static size_t file_size(std::FILE* fp)
    {
        if (!fp) return 0;
        long cur = std::ftell(fp);
        if (cur < 0) return 0;
        if (std::fseek(fp, 0, SEEK_END) != 0) return static_cast<size_t>(cur);
        long end = std::ftell(fp);
        std::fseek(fp, cur, SEEK_SET);
        if (end < 0) return static_cast<size_t>(cur);
        return static_cast<size_t>(end);
    }

    FileSink::FileSink(std::string path, bool flush_on_error, size_t rotate_bytes)
        : _path(std::move(path)),
          _rotate_bytes(rotate_bytes),
          _flush_on_error(flush_on_error),
          _fp(nullptr),
          _current_size(0)
    {
        EnsureParentDirs();
        OpenFile(true);
    }

    FileSink::~FileSink()
    {
        if (_fp)
            std::fclose(_fp);
    }

    void FileSink::OpenFile(bool truncate)
    {
        if (_fp)
        {
            std::fclose(_fp);
            _fp = nullptr;
        }
        std::string apath;
        if (!truncate && !_activePath.empty())
        {
            apath = _activePath;
        }
        else if (_rotate_bytes == 0)
        {
            apath = _path;
        }
        else
        {
            do
            {
                ++_timestampSequence;
                apath = BuildTimestampedPath();
            } while (Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::Exists(apath));
        }

        const char* mode = truncate ? "wb" : "ab";
        _fp = std::fopen(apath.c_str(), mode);
        if (_fp)
        {
            _activePath = apath;
            _current_size = truncate ? 0 : file_size(_fp);
        }
        else
        {
            if (truncate)
                _activePath.clear();
            _current_size = 0;
        }
    }

    void FileSink::RotateIfNeeded()
    {
        if (_rotate_bytes == 0)
            return;
        if (_current_size >= _rotate_bytes)
            OpenFile(true);
    }

    std::string FileSink::BuildTimestampedPath() const
    {
        return timestamped_name(_path, _timestampSequence);
    }

    // Use shared formatter from Log/Format.h

    void FileSink::Write(const Record& rec)
    {
        if (!_fp)
            OpenFile();
        if (!_fp)
            return;

        std::string line;
        line.reserve(rec.message.size() + 64);
        Ecstatica::Recompiled::Log::FormatLine(rec, line, _fmt);

        if (WriteLine(line))
            FlushBufferedLine();

        if (_flush_on_error && (rec.level == Level::Error || rec.level == Level::Fatal))
            Flush();

        RotateIfNeeded();
    }

    bool FileSink::WriteLine(std::string_view line)
    {
        if (!_fp) return false;

        size_t offset = 0;
        bool recovered = false;
        while (offset < line.size())
        {
            const size_t written = std::fwrite(line.data() + offset, 1, line.size() - offset, _fp);
            if (written > 0)
            {
                offset += written;
                _current_size += written;
                continue;
            }

            if (recovered || !RecoverAfterWriteFailure())
                return false;

            recovered = true;
        }

        return true;
    }

    bool FileSink::RecoverAfterWriteFailure()
    {
        if (_fp)
        {
            std::clearerr(_fp);
            std::fclose(_fp);
            _fp = nullptr;
        }

        OpenFile(false);
        return _fp != nullptr;
    }

    void FileSink::FlushBufferedLine()
    {
        if (!_fp) return;
        if (std::fflush(_fp) == 0)
            return;

        RecoverAfterWriteFailure();
    }

    void FileSink::Flush()
    {
        if (_fp)
            Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::SyncFile(_fp);
    }

    void FileSink::EnsureParentDirs()
    {
        auto pos = _path.find_last_of('/');
        if (pos == std::string::npos) return;
        std::string dir = _path.substr(0, pos);
        if (dir.empty()) return;
        Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::CreateDirectory(dir);
    }
}
