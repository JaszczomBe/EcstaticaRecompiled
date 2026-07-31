#pragma once
#include "Log/Sinks/Sink.h"

namespace Ecstatica::Recompiled::Log
{
    class AndroidSink : public Sink
    {
    public:
        void Write(const Record& rec) override;
        void Flush() override {}
        void SetFormatOptions(const FormatOptions& opt) override { _fmt = opt; }
        FormatOptions GetFormatOptions() const override { return _fmt; }
    private:
        // Keep Logcat compact, but preserve default error/fatal stack rendering parity
        // with the shared logger behavior.
        FormatOptions _fmt
        {
            /* humanTime          */ false,
            /* timeZone           */ FormatOptions::TimeZone::Local,
            /* includeTimestamp   */ false,
            /* includeSource      */ false,
            /* includeThread      */ false,
            /* includeThreadName  */ true,
            /* includeSeq         */ false,
            /* includeStack       */ true,
            /* useColor           */ false,
            /* stackIndentSpaces  */ 2,
            /* stackShowSource    */ false,
            /* stackRelativePaths */ true,
            /* submoduleNames     */ {}
        };
    };
}
