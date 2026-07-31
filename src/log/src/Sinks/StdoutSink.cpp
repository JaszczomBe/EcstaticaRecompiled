#include "Log/Sinks/StdoutSink.h"

#include "Log/Core/Format.h"
#include "Log/Core/Level.h"

#include <cstdio>
#include <cstring>
#include <string>
#if defined(__unix__) || defined(__APPLE__)
#include <unistd.h>
#endif

namespace Ecstatica::Recompiled::Log
{
    StdoutSink::StdoutSink()
    {
#if defined(__unix__) || defined(__APPLE__)
        if (isatty(fileno(stdout)))
            _fmt.useColor = true;
#endif
    }

    void
    StdoutSink::Write(const Record& rec)
    {
        std::string line;
        line.reserve(rec.message.size() + 96);
        Ecstatica::Recompiled::Log::FormatLine(rec, line, _fmt);
        std::fwrite(line.data(), 1, line.size(), stdout);
    }

    void
    StdoutSink::Flush()
    {
        std::fflush(stdout);
    }
} // namespace Ecstatica::Recompiled::Log
