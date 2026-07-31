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
#include <unistd.h>

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

    static std::string numbered_name(const std::string& path, int index)
    {
        std::string dir, fname; split_path(path, dir, fname);
        std::string stem, ext; split_stem_ext(fname, stem, ext);
        char num[8];
        std::snprintf(num, sizeof(num), "%03d", index);
        std::string out;
        if (!dir.empty()) { out.reserve(dir.size() + stem.size() + 1 + 3 + ext.size() + 1); }
        if (!dir.empty()) { out.append(dir).push_back('/'); }
        out.append(stem).push_back('_');
        out.append(num);
        out.append(ext);
        return out;
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

    FileSink::FileSink(std::string path, bool flush_on_error, int keep, size_t rotate_bytes)
        : _path(std::move(path)),
          _rotate_bytes(rotate_bytes),
          _keep(keep),
          _flush_on_error(flush_on_error),
          _fp(nullptr),
          _current_size(0)
    {
        EnsureParentDirs();
        if (_keep > 0)
        {
            ::unlink(_path.c_str());
            for (int i = 1; i <= _keep; ++i)
                ::unlink(numbered_name(_path, i).c_str());
            _active_index = 1;
            _filled_slots = 1;
            OpenFile(true);
        }
        else
        {
            OpenFile(true);
        }
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
        else if (_keep > 0)
        {
            if (_active_index <= 0 || _active_index > _keep)
                _active_index = 1;
            apath = numbered_name(_path, _active_index);
        }
        else
        {
            if (_rotate_bytes == 0)
            {
                apath = _path;
            }
            else
            {
                do
                {
                    ++_timestampSequence;
                    apath = BuildTimestampedPath();
                } while (::access(apath.c_str(), F_OK) == 0);
            }
        }

        if (truncate)
            ::unlink(apath.c_str());

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

    void FileSink::RotateNow()
    {
        if (_fp)
        {
            std::fclose(_fp);
            _fp = nullptr;
        }

        if (_keep <= 0)
        {
            OpenFile(true);
            return;
        }
        else
        {
            if (_keep > 0)
            {
                if (_filled_slots < _keep)
                {
                    // Grow until the ring is full.
                    _active_index = ++_filled_slots;
                    OpenFile(true);
                    return;
                }

                // Ring full: drop oldest (_001), shift remaining down, write to _keep.
                ::unlink(numbered_name(_path, 1).c_str());
                for (int i = 1; i < _keep; ++i)
                {
                    std::string from = numbered_name(_path, i + 1);
                    std::string to   = numbered_name(_path, i);
                    ::unlink(to.c_str());
                    ::rename(from.c_str(), to.c_str());
                }
                _filled_slots = _keep;
                _active_index = _keep;
                OpenFile(true);
                return;
            }
        }
        OpenFile();
    }

    void FileSink::RotateIfNeeded()
    {
        if (_rotate_bytes == 0)
            return;
        if (_current_size >= _rotate_bytes)
            RotateNow();
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
        if (!_fp) return;
        std::fflush(_fp);
        int fd = fileno(_fp);
        if (fd >= 0) ::fsync(fd);
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
