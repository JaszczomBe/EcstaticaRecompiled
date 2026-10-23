#include "EcstaticaLogBridge.h"
#include "RunArtifacts.h"

#include "Log/Core/Format.h"
#include "Log/Core/Logger.h"
#include "Log/LogBootstrap.h"
#include "Log/Constants.h"
#include "Log/Session/SessionRetention.h"

#include <cstdarg>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
#include <limits>
#include <stdexcept>
#include <charconv>

namespace
{
    std::atomic<bool> loggingActive{false};
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
            {E2R_LOG_TAG_MISSING_SOUND, "MissingSound"},
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

    int DiagnosticLevel(std::string_view message)
    {
        if (message.starts_with("replay: RECORDING INCOMPLETE:"))
            return E2R_LOG_LEVEL_WARNING;
        if (message.starts_with("fatal:") || message.starts_with("FATAL:"))
            return E2R_LOG_LEVEL_FATAL;
        if (message.starts_with("error:") || message.starts_with("ERROR:") || message.starts_with("failed to "))
            return E2R_LOG_LEVEL_ERROR;
        if (message.starts_with("warning:") || message.starts_with("WARN:") || message.starts_with("WARNING:") ||
            message.starts_with("E2R open failed:"))
            return E2R_LOG_LEVEL_WARNING;
        if (message.starts_with("debug:") || message.starts_with("DEBUG:"))
            return E2R_LOG_LEVEL_DEBUG;
        if (message.starts_with("trace:") || message.starts_with("TRACE:"))
            return E2R_LOG_LEVEL_TRACE;
        return E2R_LOG_LEVEL_INFO;
    }

    bool IsVerboseInputDiagnostic(std::string_view message)
    {
        if (message.starts_with("game state: ") && message.find(" input esc=") != std::string_view::npos)
            return true;
        for (const auto prefix : {"host input ", "host keyboard state:", "host message dispatch:",
                                  "host pump:", "host class register:", "host window proc bind:",
                                  "game input:", "game state: 15d40.clear input "})
            if (message.starts_with(prefix))
                return true;
        return false;
    }

    bool VerboseInputEnabled()
    {
        static const bool enabled = [] {
            const char* value = std::getenv("E2R_INPUT_DIAG_VERBOSE");
            return value != nullptr && value[0] != '\0' && value[0] != '0';
        }();
        return enabled;
    }


}

extern "C" int E2R_LogBootstrap(const char* level, const char* disabled_modules, const char* data_dir)
{
    try
    {
        if (data_dir == nullptr || data_dir[0] == '\0')
            return 0;
        using namespace Ecstatica::Recompiled::Log;
        if (!E2R_ArtifactsStart(data_dir)) return 0;
        const std::string logFile = std::string(E2R_ArtifactsDirectory()) + "/e2recomp.log";
        if (!Bootstrap(
            level != nullptr ? level : "",
            disabled_modules != nullptr ? disabled_modules : "",
            false,
            RegisterCommonTags,
            logFile, true))
            return 0;
        loggingActive.store(true, std::memory_order_release);
        E2R_ArtifactsSetReporter(E2R_LogDiagnostic);
        E2R_LogWrite(E2R_LOG_LEVEL_INFO, E2R_LOG_MODULE_RUNTIME, E2R_LOG_TAG_STARTUP,
                     nullptr, nullptr, 0, (std::string("Log session: ") + E2R_ArtifactsDirectory()).c_str());
        return 1;
    }
    catch (const std::exception& error)
    {
        if (loggingActive.load(std::memory_order_acquire))
            E2R_LogShutdown();
        std::fprintf(stderr, "logger bootstrap failed: %s\n", error.what());
        return 0;
    }
}

extern "C" void E2R_LogShutdown(void)
{
    E2R_ArtifactsStopMaintenance();
    E2R_ArtifactsSetReporter(nullptr);
    loggingActive.store(false, std::memory_order_release);
    Ecstatica::Recompiled::Log::BootstrapShutdown();
    E2R_ArtifactsShutdown();
}

extern "C" int E2R_LogIsActive(void)
{
    return loggingActive.load(std::memory_order_acquire);
}

extern "C" void E2R_LogDiagnostic(const char* message)
{
    if (!E2R_LogIsActive() || message == nullptr)
        return;
    const std::string_view text = message;
    int level = DiagnosticLevel(text);
    uint64_t tag = E2R_LOG_TAG_DIAGNOSTIC;
    if (text.starts_with("game state: sound archive missing ignored "))
    {
        level = E2R_LOG_LEVEL_TRACE;
        tag = E2R_LOG_TAG_MISSING_SOUND;
    }
    else if (IsVerboseInputDiagnostic(text))
    {
        if (!VerboseInputEnabled())
            return;
        level = E2R_LOG_LEVEL_DEBUG;
        tag = E2R_LOG_TAG_INPUT;
    }
    else if (text.starts_with("input:") || text.starts_with("input state") ||
             text.starts_with("posted key ") || text.starts_with("dispatched "))
    {
        level = E2R_LOG_LEVEL_DEBUG;
        tag = E2R_LOG_TAG_INPUT;
    }
    else if (text.starts_with("game state: 42b004.") || text.starts_with("game state: 42ad60."))
    {
        level = E2R_LOG_LEVEL_TRACE;
        tag = E2R_LOG_TAG_ACTOR;
    }
    E2R_LogWrite(level, E2R_LOG_MODULE_RUNTIME, tag, nullptr, nullptr, 0, message);
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
