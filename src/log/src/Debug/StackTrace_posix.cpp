#include "Log/Debug/StackTrace.h"
#include <memory>
#include <string>
#include <cstdio>

#if defined(__APPLE__) || defined(__linux__) || defined(ANDROID)
    #define UT_HAS_EXECINFO 1
    #include <execinfo.h>
#else
    #define UT_HAS_EXECINFO 0
#endif

namespace Ecstatica::Recompiled::Log
{
    namespace
    {
        // Default logger-internal frames to skip from captured native callstacks:
        // CaptureCallstack itself plus the immediate logger wrappers above it.
        inline constexpr int kInternalLoggerFramesToSkip = 3;
    }

    std::shared_ptr<std::string> CaptureCallstack(bool symbolize, int max_frames)
    {
#if UT_HAS_EXECINFO
        (void)symbolize;
        if (max_frames < 1) max_frames = 1;
        if (max_frames > 256) max_frames = 256;
        void* buf[256];
        int n = ::backtrace(buf, max_frames);
        if (n <= 0) return nullptr;

        const int skip = kInternalLoggerFramesToSkip;
        auto out = std::make_shared<std::string>();
        if (n <= skip)
            return out;
        out->reserve(static_cast<size_t>(n - skip) * 24);
        for (int i = skip; i < n; ++i)
        {
            char tmp[32];
            std::snprintf(tmp, sizeof(tmp), "%p", buf[i]);
            out->append(tmp);
            out->push_back('\n');
        }
        return out;
#else
        (void)symbolize; (void)max_frames;
        return nullptr;
#endif
    }
}
