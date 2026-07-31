#pragma once

#include "Log/Core/Record.h"

#include <string>
#include <unordered_map>
#include <vector>

namespace Ecstatica::Recompiled::Log
{
    inline constexpr char kCanonicalModuleSubmoduleDelimiter = '.';

    struct FormatOptions
    {
        enum class TimeZone
        {
            Local,
            Utc
        };

        bool        humanTime          = false;
        TimeZone    timeZone           = TimeZone::Local;
        bool        includeTimestamp   = false;
        bool        includeSource      = false;
        bool        includeThread      = true;
        bool        includeThreadName  = true;
        bool        includeSeq         = false;
        bool        includeStack       = false;
        bool        useColor           = false;
        int         stackIndentSpaces  = 2;
        bool        stackShowSource    = true;
        bool        stackRelativePaths = true;

        std::unordered_map<ModuleID, std::vector<std::pair<SubmoduleMask, std::string>>> submoduleNames;
    };

    std::string RenderModuleName(ModuleID id);
    std::string RenderModuleMaskName(ModuleMask mask);
    std::string RenderRecordTag(const Record& rec, const FormatOptions& opt = {});
    void FormatLine(const Record& rec, std::string& out, const FormatOptions& opt = {});
    void FormatAndroidLine(const Record& rec, std::string& out, const FormatOptions& opt = {});
}
