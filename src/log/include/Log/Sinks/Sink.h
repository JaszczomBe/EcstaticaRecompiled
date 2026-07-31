#pragma once

#include "Log/Core/Format.h"
#include "Log/Core/Record.h"

#include <memory>

namespace Ecstatica::Recompiled::Log
{
    struct Sink
    {
        virtual         ~Sink() = default;
        virtual void    Write(const Record& rec) = 0;
        virtual void    Flush() {}
        virtual void    SetFormatOptions(const FormatOptions&) {}
        virtual FormatOptions GetFormatOptions() const { return {}; }
    };

    using SinkPtr = std::shared_ptr<Sink>;
}
