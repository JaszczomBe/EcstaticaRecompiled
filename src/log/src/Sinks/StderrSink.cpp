#include "Log/Sinks/StderrSink.h"

#include "Log/Core/Format.h"
#include "Log/Core/Level.h"
#include "EcstaticaLogBridge.h"

#include <cstdio>
#include <cstdlib>
#include <string>
#if defined(__unix__) || defined(__APPLE__)
#include <unistd.h>
#endif

namespace Ecstatica::Recompiled::Log
{
    StderrSink::StderrSink()
    {
#if defined(__unix__) || defined(__APPLE__)
        if (isatty(fileno(stderr)))
            _fmt.useColor = true;
#endif
    }

    void
    StderrSink::Write(const Record& rec)
    {
        static const bool gameplayVerbose = [] {
            const char* value = std::getenv("E2R_GAMEPLAY_CONSOLE_VERBOSE");
            return value && value[0] && value[0] != '0';
        }();
        if (!gameplayVerbose && rec.module == ModuleID::Runtime &&
            (rec.submoduleMask & E2R_LOG_TAG_ACTOR) && rec.level == Level::Trace)
            return;
        std::string line;
        line.reserve(rec.message.size() + 96);
        Ecstatica::Recompiled::Log::FormatLine(rec, line, _fmt);
        std::fwrite(line.data(), 1, line.size(), stderr);
    }

    void
    StderrSink::Flush()
    {
        std::fflush(stderr);
    }
} // namespace Ecstatica::Recompiled::Log
