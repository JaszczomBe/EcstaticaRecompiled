#pragma once
#include <cstdio>
#include <string>
#include <cstddef>
#include "Log/Constants.h"
#include "Log/Sinks/Sink.h"

namespace Ecstatica::Recompiled::Log
{
    class FileSink : public Sink
    {
    public:
        // keep > 0 => numbered circular rotation, keep <= 0 => append-only timestamped files.
        explicit FileSink(std::string path,
                          bool flush_on_error = true,
                          int keep = 0,
                          size_t rotate_bytes = kLogFileRotateBytes);
        ~FileSink() override;

        void Write(const Record& rec) override;
        void Flush() override;
        void SetFormatOptions(const FormatOptions& opt) override { _fmt = opt; }
        FormatOptions GetFormatOptions() const override { return _fmt; }

    private:
        void OpenFile(bool truncate = false);
        void RotateIfNeeded();
        void RotateNow();
        bool WriteLine(std::string_view line);
        bool RecoverAfterWriteFailure();
        void FlushBufferedLine();
        void EnsureParentDirs();
        std::string BuildTimestampedPath() const;

    private:
        std::string     _path;
        std::string     _activePath;
        size_t          _rotate_bytes;
        int             _keep;
        bool            _flush_on_error;
        std::FILE*      _fp;
        size_t          _current_size;
        int             _active_index = 0;  // for circular mode
        int             _filled_slots = 0;  // number of allocated slots in circular mode
        unsigned long long _timestampSequence = 0;
        FormatOptions   _fmt
        {
            /* humanTime          */ true,
            /* timeZone           */ FormatOptions::TimeZone::Local,
            /* includeTimestamp   */ false,
            /* includeSource      */ true,
            /* includeThread      */ false,
            /* includeThreadName  */ true,
            /* includeSeq         */ false,
            /* includeStack       */ true,
            /* useColor           */ false,
            /* stackIndentSpaces  */ 2,
            /* stackShowSource    */ true,
            /* stackRelativePaths */ true,
            /* submoduleNames     */ {}
        };
    };
}
