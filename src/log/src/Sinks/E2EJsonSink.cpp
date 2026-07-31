#if defined(UNDERTONE_ENABLE_E2E_LOG_SINK)
#include "Log/Sinks/E2EJsonSink.h"

#include "LogSupport/IO/FileSystemIO.h"
#include "Log/Core/Level.h"
#include "Log/Modules/ModuleId.h"

#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <string_view>
#include <unistd.h>

namespace Ecstatica::Recompiled::Log
{
    namespace
    {
        void AppendJsonString(std::string& out, std::string_view value)
        {
            out.push_back('"');
            for(const unsigned char ch : value)
            {
                switch(ch)
                {
                    case '"':  out += "\\\""; break;
                    case '\\': out += "\\\\"; break;
                    case '\b': out += "\\b"; break;
                    case '\f': out += "\\f"; break;
                    case '\n': out += "\\n"; break;
                    case '\r': out += "\\r"; break;
                    case '\t': out += "\\t"; break;
                    default:
                        if(ch < 0x20)
                        {
                            char escaped[7];
                            std::snprintf(escaped, sizeof(escaped), "\\u%04x", ch);
                            out += escaped;
                        }
                        else
                        {
                            out.push_back(static_cast<char>(ch));
                        }
                        break;
                }
            }
            out.push_back('"');
        }

        std::string FormatWallTime(std::chrono::system_clock::time_point timePoint)
        {
            using namespace std::chrono;
            const auto tt = system_clock::to_time_t(timePoint);
            const auto ms = duration_cast<milliseconds>(timePoint.time_since_epoch()) % 1000;

            std::tm tm{};
#if defined(_WIN32)
            gmtime_s(&tm, &tt);
#else
            gmtime_r(&tt, &tm);
#endif

            std::ostringstream out;
            out << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S")
                << '.' << std::setw(3) << std::setfill('0') << ms.count()
                << 'Z';
            return out.str();
        }
    }

    E2EJsonSink::E2EJsonSink(std::string path)
        : _path(std::move(path))
    {
        EnsureParentDirs();
        ::unlink(_path.c_str());
        _fp = std::fopen(_path.c_str(), "wb");
    }

    E2EJsonSink::~E2EJsonSink()
    {
        if(_fp)
            std::fclose(_fp);
    }

    void E2EJsonSink::Write(const Record& rec)
    {
        if(!_fp)
            return;

        std::string line;
        line.reserve(rec.message.size() + 256);

        line += "{\"ts\":";
        AppendJsonString(line, FormatWallTime(rec.timePointWall));
        line += ",\"seq\":";
        line += std::to_string(rec.seq);
        line += ",\"level\":";
        AppendJsonString(line, ToString(rec.level));
        line += ",\"module\":";
        AppendJsonString(line, ModuleToString(rec.module));
        line += ",\"moduleMask\":";
        line += std::to_string(rec.moduleMask);
        line += ",\"submoduleMask\":";
        line += std::to_string(rec.submoduleMask);
        line += ",\"threadId\":";
        line += std::to_string(rec.threadId);
        line += ",\"message\":";
        AppendJsonString(line, rec.message);
        line += ",\"source\":{\"file\":";
        AppendJsonString(line, rec.src.file ? rec.src.file : "");
        line += ",\"function\":";
        AppendJsonString(line, rec.src.func ? rec.src.func : "");
        line += ",\"line\":";
        line += std::to_string(rec.src.line);
        line += "}";

        for(size_t index = 0; index < rec.fieldCount; ++index)
        {
            if(rec.fields[index].key == "event")
            {
                line += ",\"event\":";
                AppendJsonString(line, rec.fields[index].value);
                break;
            }
        }

        line += ",\"fields\":{";
        for(size_t index = 0; index < rec.fieldCount; ++index)
        {
            if(index > 0)
                line.push_back(',');
            AppendJsonString(line, rec.fields[index].key);
            line.push_back(':');
            AppendJsonString(line, rec.fields[index].value);
        }
        line += "}}\n";

        std::fwrite(line.data(), 1, line.size(), _fp);
        std::fflush(_fp);
    }

    void E2EJsonSink::Flush()
    {
        if(_fp)
            std::fflush(_fp);
    }

    void E2EJsonSink::EnsureParentDirs()
    {
        const auto pos = _path.find_last_of('/');
        if(pos == std::string::npos)
            return;

        const auto dir = _path.substr(0, pos);
        if(!dir.empty())
            Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::CreateDirectory(dir);
    }
}
#endif
