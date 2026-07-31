#include "Log/LogBootstrap.h"
#include "Log/Constants.h"
#include "Log/Core/Config.h"
#include "Log/Core/Format.h"
#include "Log/Core/Level.h"
#include "Log/Core/Logger.h"
#include "Log/Modules/ModuleId.h"
#if defined(UNDERTONE_ENABLE_E2E_LOG_SINK)
    #include "Log/Sinks/E2EJsonSink.h"
    #include <cstdlib>
#endif
#include "Log/Sinks/FileSink.h"
#include "Log/Sinks/StdoutSink.h"
#include "LogSupport/String/Trim.h"

#include <iostream>
#include <memory>
#include <vector>

namespace Ecstatica::Recompiled::Log
{
    namespace
    {
        Level ParseLevel(std::string_view s) noexcept
        {
            if (auto level = FromString(Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(s)))
                return *level;
            return kDefaultGlobalLogLevel;
        }

        ModuleMask ParseModuleMask(std::string_view modules) noexcept
        {
            if (modules.empty())
                return 0;

            ModuleMask mask = 0;
            while (!modules.empty())
            {
                auto comma = modules.find(',');
                auto name  = (comma == std::string_view::npos) ? modules : modules.substr(0, comma);
                name = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(name);

                if (!name.empty())
                {
                    if (auto id = ModuleFromString(name))
                        mask |= ToMask(*id);
                }

                if (comma == std::string_view::npos)
                    break;
                modules = modules.substr(comma + 1);
            }
            return mask;
        }
    }

    void Bootstrap(std::string_view level,
                   std::string_view modules,
                   bool disableSubmoduleFiltering,
                   void (*configureFormat)(FormatOptions&),
                   std::string_view filePath)
    {
        const auto trimmedLevel = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(level);
        if (!trimmedLevel.empty() && !FromString(trimmedLevel))
        {
            std::cerr << "WARN: unrecognized logLevel '" << trimmedLevel
                      << "', defaulting to build-configured logger level" << std::endl;
        }

        Config cfg;
        if (!trimmedLevel.empty())
            cfg.globalLevel = ParseLevel(trimmedLevel);
        cfg.disableSubmoduleFiltering = disableSubmoduleFiltering;
        // modules is a deny-list: named modules are turned OFF.
        // Default (empty) = nothing denied = all modules enabled.
        cfg.moduleDenyMask            = ParseModuleMask(modules);

        auto& logger = Logger::Instance();
        logger.Start(cfg);

        std::vector<SinkPtr> sinks;

        auto stdoutSink = std::make_shared<StdoutSink>();
        if (configureFormat != nullptr)
        {
            FormatOptions format = stdoutSink->GetFormatOptions();
            configureFormat(format);
            stdoutSink->SetFormatOptions(format);
        }
        sinks.emplace_back(stdoutSink);

        const auto trimmedFilePath = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(filePath);
        if (!trimmedFilePath.empty())
        {
            auto fileSink = std::make_shared<FileSink>(std::string(trimmedFilePath), true, 0, kLogFileRotateBytes);
            auto format = fileSink->GetFormatOptions();
            format.includeTimestamp = true;
            if (configureFormat != nullptr)
                configureFormat(format);
            fileSink->SetFormatOptions(format);
            sinks.emplace_back(fileSink);
        }

#if defined(UNDERTONE_ENABLE_E2E_LOG_SINK)
        if (const char* e2eEventsPath = std::getenv("UNDERTONE_E2E_EVENTS_PATH"))
        {
            const auto trimmedE2EEventsPath = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(e2eEventsPath);
            if (!trimmedE2EEventsPath.empty())
                sinks.emplace_back(std::make_shared<E2EJsonSink>(std::string(trimmedE2EEventsPath)));
        }
#endif

        logger.ReplaceSinks(sinks);
    }

    void BootstrapShutdown()
    {
        Logger::Instance().Stop();
    }
}
