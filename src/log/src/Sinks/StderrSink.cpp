#include "Log/Sinks/StderrSink.h"

#include "Log/Core/Format.h"
#include "Log/Core/Level.h"

#include <cstdio>
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
