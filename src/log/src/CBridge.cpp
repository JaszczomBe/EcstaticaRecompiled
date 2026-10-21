#include "EcstaticaLogBridge.h"

#include "Log/Core/Format.h"
#include "Log/Core/Logger.h"
#include "Log/LogBootstrap.h"

#include <cstdarg>
#include <atomic>
#include <cstdio>
#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace
{
    std::atomic<bool> diagnosticMirrorEnabled{false};
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
            {E2R_LOG_TAG_DIAGNOSTIC, "Diagnostic"},
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
        std::filesystem::path root = dataDir;
        std::filesystem::path logs = root / "logs";
        std::error_code ec;
        std::filesystem::create_directories(logs, ec);
        if (ec)
            return {};
        return (logs / "e2recomp.log").string();
    }
}

extern "C" int E2R_LogBootstrap(const char* level, const char* disabled_modules, const char* data_dir)
{
    try
    {
        if (data_dir == nullptr || data_dir[0] == '\0')
            return 0;
        const std::string logPath = BuildLogPath(data_dir);
        if (logPath.empty() || !Ecstatica::Recompiled::Log::Bootstrap(
            level != nullptr ? level : "",
            disabled_modules != nullptr ? disabled_modules : "",
            false,
            RegisterCommonTags,
            logPath, false))
            return 0;
        diagnosticMirrorEnabled.store(true, std::memory_order_release);
        return 1;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "logger bootstrap failed: %s\n", error.what());
        return 0;
    }
}

extern "C" void E2R_LogShutdown(void)
{
    diagnosticMirrorEnabled.store(false, std::memory_order_release);
    Ecstatica::Recompiled::Log::BootstrapShutdown();
}

extern "C" void E2R_LogDiagnostic(const char* message)
{
    if (diagnosticMirrorEnabled.load(std::memory_order_acquire))
        E2R_LogWrite(E2R_LOG_LEVEL_INFO, E2R_LOG_MODULE_RUNTIME,
                     E2R_LOG_TAG_DIAGNOSTIC, nullptr, nullptr, 0, message);
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
