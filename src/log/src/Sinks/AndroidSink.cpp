#include "Log/Sinks/AndroidSink.h"
#include "Log/Core/Format.h"
#include "Log/Core/Level.h"

#if defined(ANDROID)
    #include <android/log.h>
#endif

namespace Ecstatica::Recompiled::Log
{
    void AndroidSink::Write(const Record& rec)
    {
    #if defined(ANDROID)
        int prio = ANDROID_LOG_VERBOSE;
        switch (rec.level)
        {
            case Level::Trace:   prio = ANDROID_LOG_VERBOSE; break;
            case Level::Debug:   prio = ANDROID_LOG_DEBUG;   break;
            case Level::Info:    prio = ANDROID_LOG_INFO;    break;
            case Level::Warning: prio = ANDROID_LOG_WARN;    break;
            case Level::Error:   prio = ANDROID_LOG_ERROR;   break;
            case Level::Fatal:   prio = ANDROID_LOG_FATAL;   break;
            default:             prio = ANDROID_LOG_SILENT;  break;
        }

        const std::string tag = RenderRecordTag(rec, _fmt);

        // Use common formatter; allow options via set_format_options
        std::string line;
        line.reserve(rec.message.size() + 64);
        Ecstatica::Recompiled::Log::FormatAndroidLine(rec, line, _fmt);

        __android_log_write(prio, tag.c_str(), line.c_str());
    #else
        (void)rec;
    #endif
    }
}
