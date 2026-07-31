#include "EcstaticaLogBridge.h"

#include "Log/Core/Format.h"
#include "Log/Core/Logger.h"
#include "Log/LogBootstrap.h"

#include <cstdarg>
#include <cstdio>
#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace
{
    using namespace Ecstatica::Recompiled::Log;

    Level ToLevel(int level)
    {
        if (level < static_cast<int>(Level::Trace))
            return Level::Trace;
        if (level > static_cast<int>(Level::Off))
            return Level::Off;
        return static_cast<Level>(level);
    }

    ModuleID ToModule(uint64_t module)
    {
        return static_cast<ModuleID>(module);
    }

    void RegisterCommonTags(FormatOptions& format)
    {
        const std::vector<std::pair<SubmoduleMask, std::string>> tags = {
            {E2R_LOG_TAG_STARTUP, "Startup"},
            {E2R_LOG_TAG_INPUT, "Input"},
            {E2R_LOG_TAG_FILE_IO, "FileIO"},
            {E2R_LOG_TAG_PRESENTATION, "Presentation"},
            {E2R_LOG_TAG_SCRIPT, "Script"},
            {E2R_LOG_TAG_ACTOR, "Actor"},
            {E2R_LOG_TAG_REQUESTER, "Requester"},
            {E2R_LOG_TAG_TIMING, "Timing"},
            {E2R_LOG_TAG_AUDIO, "Audio"},
            {E2R_LOG_TAG_PROBE, "Probe"},
        };

        for (auto module : {ModuleID::Runtime,
                            ModuleID::Win32Compat,
                            ModuleID::HostBackend,
                            ModuleID::DirectDrawCompat,
                            ModuleID::DirectSoundCompat,
                            ModuleID::Probe,
                            ModuleID::Reconstruction,
                            ModuleID::Script,
                            ModuleID::Actor,
                            ModuleID::Requester,
                            ModuleID::FileIO,
                            ModuleID::Presentation,
                            ModuleID::Timing,
                            ModuleID::Audio})
        {
            format.submoduleNames[module] = tags;
        }
    }

    std::string BuildLogPath(const char* dataDir)
    {
        std::filesystem::path root = dataDir != nullptr && dataDir[0] != '\0' ? dataDir : "./data";
        std::filesystem::path logs = root / "logs";
        std::error_code ec;
        std::filesystem::create_directories(logs, ec);
        return (logs / "e2recomp.log").string();
    }
}

extern "C" void E2R_LogBootstrap(const char* level, const char* disabled_modules, const char* data_dir)
{
    const std::string logPath = BuildLogPath(data_dir);
    Ecstatica::Recompiled::Log::Bootstrap(
        level != nullptr ? level : "",
        disabled_modules != nullptr ? disabled_modules : "",
        false,
        RegisterCommonTags,
        logPath);
}

extern "C" void E2R_LogShutdown(void)
{
    Ecstatica::Recompiled::Log::BootstrapShutdown();
}

extern "C" void E2R_LogWrite(int level,
                              uint64_t module,
                              uint64_t tag,
                              const char* file,
                              const char* func,
                              int line,
                              const char* message)
{
    Ecstatica::Recompiled::Log::Logger::Instance().Log(
        ToLevel(level),
        ToModule(module),
        Ecstatica::Recompiled::Log::SourceLoc{file, func, line},
        message != nullptr ? message : "",
        nullptr,
        0,
        false,
        module,
        tag);
}

extern "C" void E2R_LogWritef(int level,
                               uint64_t module,
                               uint64_t tag,
                               const char* file,
                               const char* func,
                               int line,
                               const char* format,
                               ...)
{
    char buffer[1024];
    va_list ap;
    va_start(ap, format);
    std::vsnprintf(buffer, sizeof(buffer), format != nullptr ? format : "", ap);
    va_end(ap);
    E2R_LogWrite(level, module, tag, file, func, line, buffer);
}
