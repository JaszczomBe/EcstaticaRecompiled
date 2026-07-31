#pragma once

namespace Ecstatica::Recompiled::Log
{
    struct SourceLoc
    {
        const char* file;
        const char* func;
        int         line;
    };
}
