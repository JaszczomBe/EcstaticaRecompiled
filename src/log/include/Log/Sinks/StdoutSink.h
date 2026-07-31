#pragma once
#include "Log/Sinks/Sink.h"

namespace Ecstatica::Recompiled::Log
{
    class StdoutSink : public Sink
    {
    public:
        StdoutSink();
        void Write(const Record& rec) override;
        void Flush() override;
        void SetFormatOptions(const FormatOptions& opt) override { _fmt = opt; }
        FormatOptions GetFormatOptions() const override { return _fmt; }

    private:
        FormatOptions _fmt
        {
            /* humanTime          */ true,
            /* timeZone           */ FormatOptions::TimeZone::Local,
            /* includeTimestamp   */ false,
            /* includeSource      */ false,
            /* includeThread      */ false,
            /* includeThreadName  */ true,
            /* includeSeq         */ false,
            /* includeStack       */ true,
            /* useColor           */ true,
            /* stackIndentSpaces  */ 2,
            /* stackShowSource    */ true,
            /* stackRelativePaths */ true,
            /* submoduleNames     */ {}
        };
    };
}
