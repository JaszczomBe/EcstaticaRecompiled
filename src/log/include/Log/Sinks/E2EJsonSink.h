#pragma once
#if defined(UNDERTONE_ENABLE_E2E_LOG_SINK)

#include "Log/Sinks/Sink.h"

#include <cstdio>
#include <string>

namespace Ecstatica::Recompiled::Log
{
    class E2EJsonSink : public Sink
    {
    public:
        explicit E2EJsonSink(std::string path);
        ~E2EJsonSink() override;

        void Write(const Record& rec) override;
        void Flush() override;

    private:
        void EnsureParentDirs();

        std::string _path;
        std::FILE*  _fp = nullptr;
    };
}
#endif
