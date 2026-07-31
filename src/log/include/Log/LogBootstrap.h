#pragma once

#include <cstddef>
#include <string_view>

namespace Ecstatica::Recompiled::Log
{
    struct FormatOptions;

    // Start the logger with a stdout sink, applying resolved app-level logging
    // inputs such as level and module filters.
    //
    // level:   "Trace"|"Debug"|"Info"|"Warning"|"Error"|"Fatal"|"Off"
    //          empty string keeps the build default: Trace in debug, Info in release
    // modules: comma-separated module names to DISABLE (deny-list).
    //          empty string = all modules enabled (default)
    //          e.g. "Core_Audio,Core_Scripts" suppresses those two modules
    // disableSubmoduleFiltering:
    //          when true, submodule allow/deny masks are ignored entirely
    // configureFormat:
    //          optional callback used to register submodule display names on sinks
    //
    // Intended to be called once per process, after the app has resolved its
    // logging config from CLI, settings files, platform input, or other sources.
    void Bootstrap(std::string_view level,
                   std::string_view modules,
                   bool disableSubmoduleFiltering = false,
                   void (*configureFormat)(FormatOptions&) = nullptr,
                   std::string_view filePath = {});

    // Stop the logger and flush all pending records. Call before process exit.
    void BootstrapShutdown();
}
