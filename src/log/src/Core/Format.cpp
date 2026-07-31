#include "Log/Core/Format.h"

#include "Log/Core/Kotlin/ThrowableFields.h"
#include "Log/Core/Level.h"
#include "Log/Modules/ModuleId.h"
#include "LogSupport/String/Trim.h"
#include "LogSupport/Thread/Name.h"
#include "LogSupport/Time/Timer.h"

#include <cctype>
#include <cerrno>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <filesystem>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

#if defined(__unix__) || defined(__APPLE__)
    #include <cxxabi.h>
    #include <dlfcn.h>
#endif

#if (defined(__linux__) && !defined(ANDROID)) || defined(__APPLE__)
    #define UT_LOG_CAN_SYMBOLIZE_SOURCE 1
#else
    #define UT_LOG_CAN_SYMBOLIZE_SOURCE 0
#endif

namespace Ecstatica::Recompiled::Log
{
    namespace
    {
        inline constexpr bool kAndroidCompactThrowable = true;
        inline constexpr bool kAndroidCompactStack = true;
        inline constexpr bool kAndroidHideRuntimeFrames = true;
        inline constexpr bool kAndroidHideUnresolvedFrames = true;
        inline constexpr bool kHideLoggerInternalFrames = true;
    }

    static void AppendEpochMs(std::string& out, int64_t ms)
    {
        char buf[32];
        int  n = std::snprintf(buf, sizeof(buf), "%lld", static_cast<long long>(ms));
        if(n > 0)
            out.append(buf, static_cast<size_t>(n));
    }

    static void AppendHumanTime(std::string& out, std::chrono::system_clock::time_point tp, FormatOptions::TimeZone tz)
    {
        using namespace std::chrono;
        auto        ms_total = duration_cast<milliseconds>(tp.time_since_epoch());
        auto        secs     = duration_cast<seconds>(ms_total);
        auto        millis   = ms_total - secs;
        std::time_t tt       = secs.count();
        std::tm     tm;
        if(tz == FormatOptions::TimeZone::Utc)
        {
#if defined(_WIN32)
            gmtime_s(&tm, &tt);
#else
            gmtime_r(&tt, &tm);
#endif
        }
        else
        {
#if defined(_WIN32)
            localtime_s(&tm, &tt);
#else
            localtime_r(&tt, &tm);
#endif
        }
        char   buf[64];
        size_t n = std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tm);
        if(n > 0)
        {
            out.append(buf, n);
            char msbuf[8];
            int  m = std::snprintf(msbuf, sizeof(msbuf), ".%03d", static_cast<int>(millis.count()));
            if(m > 0)
                out.append(msbuf, static_cast<size_t>(m));
        }
    }

    static const std::filesystem::path& SourceRoot()
    {
        static const std::filesystem::path root = []
        {
            std::filesystem::path file_path(__FILE__);
            file_path                    = file_path.lexically_normal();
            std::string       normalized = file_path.generic_string();
            const std::string needle     = "/src/";
            auto              pos        = normalized.find(needle);
            if(pos == std::string::npos || pos == 0)
                return std::filesystem::path{};
            return std::filesystem::path(normalized.substr(0, pos));
        }();
        return root;
    }

    static const std::string& SourceRootGeneric()
    {
        static const std::string value = []
        {
            const auto& root = SourceRoot();
            return root.empty() ? std::string{} : root.generic_string();
        }();
        return value;
    }

    static std::string RelativizePath(std::string_view file)
    {
        if(file.empty())
            return {};

        std::filesystem::path full(file);
        full                 = full.lexically_normal();
        std::string full_str = full.generic_string();

        const auto& root     = SourceRootGeneric();
        if(!root.empty() && full_str.size() > root.size() && full_str.compare(0, root.size(), root) == 0 &&
           full_str[root.size()] == '/')
        {
            return full_str.substr(root.size() + 1);
        }

        return full_str;
    }

    static std::string_view LevelColor(Level lvl)
    {
        using namespace std::string_view_literals;
        switch(lvl)
        {
        case Level::Trace:
            return "\x1b[90m"sv; // bright black
        case Level::Debug:
            return "\x1b[36m"sv; // cyan
        case Level::Info:
            return "\x1b[32m"sv; // green
        case Level::Warning:
            return "\x1b[33m"sv; // yellow
        case Level::Error:
            return "\x1b[31m"sv; // red
        case Level::Fatal:
            return "\x1b[95m"sv; // bright magenta
        default:
            return "\x1b[0m"sv;
        }
    }

    static constexpr std::string_view kColorReset = "\x1b[0m";

    static void AppendColoredLine(std::string& out, std::string_view color, bool use_color, std::string_view content)
    {
        if(use_color)
            out.append(color);
        out.append(content.data(), content.size());
        if(use_color)
            out.append(kColorReset);
        out.push_back('\n');
    }

    static void AppendMultilineSection(std::string& out,
                                       std::string_view color,
                                       bool useColor,
                                       std::string_view label,
                                       std::string_view text)
    {
        if(text.empty())
            return;

        std::string line;
        line.reserve(label.size() + text.size() + 4);
        line.append("  ");
        line.append(label.data(), label.size());
        line.append(": ");

        size_t start = 0;
        bool firstLine = true;
        while(start <= text.size())
        {
            const size_t end = text.find('\n', start);
            const bool hasNewline = end != std::string_view::npos;
            const size_t lineEnd = hasNewline ? end : text.size();
            if(!firstLine)
            {
                line.assign("    ");
            }
            line.append(text.data() + start, lineEnd - start);
            AppendColoredLine(out, color, useColor, line);
            line.clear();

            if(!hasNewline)
                break;

            start = lineEnd + 1;
            firstLine = false;
        }
    }

    static void AppendCompactSection(std::string& out, std::string_view label, std::string_view text, std::string_view indent)
    {
        if(text.empty())
            return;

        out.append("\n");
        out.append(indent.data(), indent.size());
        out.append(label.data(), label.size());
        out.append(": ");

        for(size_t i = 0; i < text.size(); ++i)
        {
            const char ch = text[i];
            if(ch == '\r')
                continue;
            if(ch == '\n')
            {
                out.append("\n");
                out.append(indent.data(), indent.size());
                out.append("  ");
                continue;
            }
            out.push_back(ch);
        }
    }

    std::string RenderModuleName(ModuleID id)
    {
        return std::string(ModuleToString(id));
    }

    std::string RenderModuleMaskName(ModuleMask mask)
    {
        if(mask == 0)
            return RenderModuleName(ModuleID::None);

        if(auto single = SingleModuleFromMask(mask))
            return RenderModuleName(*single);

        auto names = ModuleMaskToStrings(mask);
        if(names.empty())
            return RenderModuleName(ModuleID::None);

        std::string combined;
        for(size_t i = 0; i < names.size(); ++i)
        {
            if(i)
                combined.push_back('|');
            combined.append(names[i]);
        }
        return combined;
    }

    std::string RenderRecordTag(const Record& rec, const FormatOptions& opt)
    {
        ModuleMask mask = rec.moduleMask;
        if(mask == 0 && rec.module != ModuleID::None)
            mask = ToMask(rec.module);

        std::string tag = RenderModuleMaskName(mask);
        if(rec.submoduleMask != 0)
        {
            bool rendered = false;
            ModuleID module = rec.module;
            if(module == ModuleID::None)
            {
                if(const auto single = SingleModuleFromMask(mask))
                    module = *single;
            }
            auto it = opt.submoduleNames.find(module);
            if(it != opt.submoduleNames.end())
            {
                const auto&   entries   = it->second;
                bool          any       = false;
                SubmoduleMask remaining = rec.submoduleMask;
                for(const auto& e : entries)
                {
                    const SubmoduleMask bitmask = e.first;
                    if(bitmask != 0 && (rec.submoduleMask & bitmask))
                    {
                        if(!any)
                        {
                            tag.push_back(kCanonicalModuleSubmoduleDelimiter);
                            any = true;
                        }
                        else
                        {
                            tag.push_back('|');
                        }
                        tag.append(e.second);
                        remaining &= ~bitmask;
                    }
                }
                // Only accept mapping when all bits are accounted for
                rendered = any && (remaining == 0);
                if(!rendered && any)
                {
                    auto pos = tag.rfind(kCanonicalModuleSubmoduleDelimiter);
                    if(pos != std::string::npos)
                        tag.erase(pos);
                }
            }

            if(!rendered)
            {
                char buf[40];
                int  n = std::snprintf(
                    buf,
                    sizeof(buf),
                    "%c0x%016llx",
                    kCanonicalModuleSubmoduleDelimiter,
                    static_cast<unsigned long long>(rec.submoduleMask));
                if(n > 0)
                    tag.append(buf, static_cast<size_t>(n));
            }
        }

        return tag;
    }

    static void AppendModuleAndSubmodule(std::string& line, const Record& rec, const FormatOptions& opt)
    {
        line.push_back('[');
        line.append(RenderRecordTag(rec, opt));
        line.push_back(']');
    }

    static void AppendRealtimeFormattedMessage(std::string& line, const Record& rec)
    {
        const auto fmt = rec.realtimeFormat;
        size_t     argIndex = 0;

        for(size_t i = 0; i < fmt.size(); ++i)
        {
            const char ch = fmt[i];
            if(ch == '{' && i + 1 < fmt.size())
            {
                if(fmt[i + 1] == '{')
                {
                    line.push_back('{');
                    ++i;
                    continue;
                }

                if(fmt[i + 1] == '}')
                {
                    if(argIndex < rec.realtimeFormatArgCount)
                    {
                        const auto& arg = rec.realtimeFormatArgs[argIndex++];
                        line.append(arg.data(), arg.size());
                    }
                    else
                    {
                        line.append("{}");
                    }

                    ++i;
                    continue;
                }
            }

            if(ch == '}' && i + 1 < fmt.size() && fmt[i + 1] == '}')
            {
                line.push_back('}');
                ++i;
                continue;
            }

            line.push_back(ch);
        }
    }

    static std::string ToHex(uintptr_t value)
    {
        char buf[32];
        std::snprintf(buf, sizeof(buf), "0x%llx", static_cast<unsigned long long>(value));
        return std::string(buf);
    }

#if defined(__unix__) || defined(__APPLE__)
    static std::string Demangle(const char* name)
    {
        if(!name || !*name)
            return {};
        int         status = 0;
        size_t      len    = 0;
        char*       dem    = abi::__cxa_demangle(name, nullptr, &len, &status);
        std::string result;
        if(status == 0 && dem)
            result.assign(dem);
        else
            result.assign(name);
        std::free(dem);
        return result;
    }

    struct FrameSymbol
    {
        std::string function;
        std::string file;
        int         line = -1;
        std::string address;
    };

    #if UT_LOG_CAN_SYMBOLIZE_SOURCE
    static std::string QuoteArg(const char* path)
    {
        std::string quoted("'");
        for(const char* p = path; p && *p; ++p)
        {
            if(*p == '\'')
                quoted.append("'\\''");
            else
                quoted.push_back(*p);
        }
        quoted.push_back('\'');
        return quoted;
    }

    // Resolves source info for all addresses in one subprocess call per binary.
    // symbols[i].function and symbols[i].file/line are updated in-place.
    static void BatchResolveSource(const std::vector<uintptr_t>& addrs, std::vector<FrameSymbol>& symbols)
    {
        struct Group
        {
            std::string         fname;
            uintptr_t           base = 0;
            std::vector<size_t> indices;
        };
        std::vector<Group> groups;
        groups.reserve(4);

        for(size_t i = 0; i < addrs.size(); ++i)
        {
            if(addrs[i] == 0)
                continue;
            Dl_info info{};
            if(dladdr(reinterpret_cast<void*>(addrs[i]), &info) == 0 || !info.dli_fname)
                continue;
            uintptr_t base  = reinterpret_cast<uintptr_t>(info.dli_fbase);
            bool      found = false;
            for(auto& g : groups)
            {
                if(g.fname == info.dli_fname)
                {
                    g.indices.push_back(i);
                    found = true;
                    break;
                }
            }
            if(!found)
                groups.push_back({std::string(info.dli_fname), base, {i}});
        }

        for(const auto& group : groups)
        {
        #if defined(__APPLE__)
            // atos has ~600ms startup cost even when it finds no debug info.
            // Without a .dSYM bundle, atos returns only "(in <binary>)" — no source lines.
            // Check for a dSYM first; if absent, dladdr+Demangle is already the best we can do.
            {
                std::error_code ec;
                namespace fs = std::filesystem;
                fs::path bin(group.fname);
                fs::path dsym1 = bin.parent_path() / (bin.filename().string() + ".dSYM");
                fs::path dsym2 = bin.parent_path().parent_path() / (bin.filename().string() + ".dSYM");
                if(!fs::exists(dsym1, ec) && !fs::exists(dsym2, ec))
                    continue; // no dSYM → atos would give no source info, skip the slow call
            }
        #endif
            std::ostringstream cmd;
        #if defined(__APPLE__)
            // atos returns one demangled line per address: "func (in binary) (file:line)"
            cmd << "atos -o " << QuoteArg(group.fname.c_str()) << " -l 0x" << std::hex << group.base;
            for(size_t idx : group.indices)
                cmd << " 0x" << std::hex << addrs[idx];
        #else
            // addr2line without -f: one line per address ("file:line"), no function name.
            // Function names come from dladdr+Demangle in SymbolizeFrame — already demangled.
            cmd << "addr2line -e " << QuoteArg(group.fname.c_str());
            for(size_t idx : group.indices)
                cmd << " 0x" << std::hex << (addrs[idx] - group.base);
        #endif
            FILE* pipe = popen(cmd.str().c_str(), "r");
            if(!pipe)
                continue;
            std::string output;
            char        buffer[512];
            while(fgets(buffer, sizeof(buffer), pipe))
                output.append(buffer);
            pclose(pipe);

            std::istringstream iss(output);
            for(size_t idx : group.indices)
            {
        #if defined(__APPLE__)
                // atos: parse demangled function name AND file:line from single line
                std::string line;
                if(!std::getline(iss, line))
                    break;
                while(!line.empty() && (line.back() == '\n' || line.back() == '\r'))
                    line.pop_back();
                line = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespaceCopy(line);
                auto func_end = line.find(" (in ");
                if(func_end != std::string::npos)
                    symbols[idx].function = line.substr(0, func_end);
                auto file_begin = line.find('(', func_end != std::string::npos ? func_end : 0);
                auto file_end   = line.find(')', file_begin != std::string::npos ? file_begin : 0);
                if(file_begin != std::string::npos && file_end != std::string::npos && file_end > file_begin + 1)
                {
                    std::string file_loc = line.substr(file_begin + 1, file_end - file_begin - 1);
                    auto        colon    = file_loc.find_last_of(':');
                    if(colon != std::string::npos)
                    {
                        symbols[idx].file = file_loc.substr(0, colon);
                        symbols[idx].line = std::atoi(file_loc.c_str() + colon + 1);
                    }
                    else
                    {
                        symbols[idx].file = file_loc;
                    }
                }
        #else
                // addr2line without -f: single "file:line" line per address.
                // Do not touch symbols[idx].function — dladdr+Demangle already gave a demangled name.
                std::string file_line;
                if(!std::getline(iss, file_line))
                    break;
                while(!file_line.empty() && (file_line.back() == '\n' || file_line.back() == '\r'))
                    file_line.pop_back();
                file_line = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespaceCopy(file_line);
                if(!file_line.empty() && file_line != "??:0")
                {
                    auto colon = file_line.find_last_of(':');
                    if(colon != std::string::npos)
                    {
                        symbols[idx].file = file_line.substr(0, colon);
                        symbols[idx].line = std::atoi(file_line.c_str() + colon + 1);
                    }
                    else
                    {
                        symbols[idx].file = file_line;
                    }
                }
        #endif
            }
        }
    }
    #endif // UT_LOG_CAN_SYMBOLIZE_SOURCE

    static FrameSymbol SymbolizeFrame(uintptr_t addr)
    {
        FrameSymbol sym;
        sym.address = ToHex(addr);

        Dl_info info{};
        if(dladdr(reinterpret_cast<void*>(addr), &info) != 0)
        {
            if(info.dli_sname)
                sym.function = Demangle(info.dli_sname);
            if(sym.function.empty() && info.dli_sname)
                sym.function = info.dli_sname;
        }

        if(sym.function.empty())
            sym.function = sym.address;

        return sym;
    }
#else // !(__unix__ || __APPLE__)
    struct FrameSymbol
    {
        std::string function;
        std::string file;
        int         line = -1;
        std::string address;
    };

    static FrameSymbol SymbolizeFrame(uintptr_t addr)
    {
        FrameSymbol sym;
        sym.address  = ToHex(addr);
        sym.function = sym.address;
        return sym;
    }
#endif

    static bool ParseAddressLine(std::string_view line, uintptr_t& addr)
    {
        line = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(line);
        if(line.empty())
            return false;

        if(line.front() == '+')
            line.remove_prefix(1);
        if(line.size() > 2 && line[0] == '0' && (line[1] == 'x' || line[1] == 'X'))
            line.remove_prefix(2);

        size_t len = 0;
        while(len < line.size() && std::isxdigit(static_cast<unsigned char>(line[len])))
            ++len;
        if(len == 0)
            return false;

        std::string hex(line.substr(0, len));
        errno                    = 0;
        unsigned long long value = std::strtoull(hex.c_str(), nullptr, 16);
        if(errno != 0)
            return false;
        addr = static_cast<uintptr_t>(value);
        return true;
    }

    static bool ShouldIncludeFrame(
        std::string_view function,
        std::string_view address,
        bool             hideRuntimeFrames,
        bool             hideUnresolvedFrames)
    {
        if(function.empty())
            return false;
        if(hideUnresolvedFrames && (function == address || function.rfind("0x", 0) == 0))
            return false;
        if(hideRuntimeFrames)
        {
            if(function.rfind("art::", 0) == 0)
                return false;
            if(function.find("art::interpreter::DoCall") != std::string_view::npos)
                return false;
            if(function.find("art::ArtMethod::Invoke") != std::string_view::npos)
                return false;
        }
        if(kHideLoggerInternalFrames)
        {
            if(function == "Ecstatica::Recompiled::Log::CaptureCallstack(bool, int)")
                return false;
            if(function.find("Ecstatica::Recompiled::Log::Logger::Log(") != std::string_view::npos)
                return false;
            if(function.find("Ecstatica::Recompiled::Log::Logger::LogOwned(") != std::string_view::npos)
                return false;
            if(function.find("Ecstatica::Recompiled::Log::WriteLog(") != std::string_view::npos)
                return false;
            if(function.find("Ecstatica::Recompiled::Log::WriteLogf(") != std::string_view::npos)
                return false;
            if(function.find("Ecstatica::Recompiled::Log::WriteLogfDetailed(") != std::string_view::npos)
                return false;
            if(function.find("Ecstatica::Recompiled::Log::WriteLogOwned(") != std::string_view::npos)
                return false;
        }
        return true;
    }

    static std::string BuildStacktraceSummary(
        const std::string& raw,
        const FormatOptions& opt,
        bool hideRuntimeFrames,
        bool hideUnresolvedFrames)
    {
        // Parse all addresses up-front so we can batch the external resolver call.
        std::vector<uintptr_t> addrs;
        {
            size_t pos = 0;
            while(pos < raw.size())
            {
                size_t           end = raw.find('\n', pos);
                std::string_view entry(raw.data() + pos, (end == std::string::npos ? raw.size() : end) - pos);
                pos = (end == std::string::npos) ? raw.size() : end + 1;
                if(!entry.empty() && entry.back() == '\r')
                    entry.remove_suffix(1);
                entry = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(entry);
                if(entry.empty())
                    continue;
                uintptr_t addr = 0;
                if(ParseAddressLine(entry, addr))
                    addrs.push_back(addr);
            }
        }

        Ecstatica::Recompiled::LogSupport::Time::Timer timer;
        timer.Start();

        std::vector<FrameSymbol> symbols;
        symbols.reserve(addrs.size());
        for(uintptr_t addr : addrs)
            symbols.push_back(SymbolizeFrame(addr));

        std::vector<uintptr_t> filteredAddrs;
        std::vector<FrameSymbol> filteredSymbols;
        filteredAddrs.reserve(addrs.size());
        filteredSymbols.reserve(symbols.size());
        for(size_t i = 0; i < addrs.size(); ++i)
        {
            if(!ShouldIncludeFrame(symbols[i].function, symbols[i].address, hideRuntimeFrames, hideUnresolvedFrames))
                continue;
            filteredAddrs.push_back(addrs[i]);
            filteredSymbols.push_back(std::move(symbols[i]));
        }

#if UT_LOG_CAN_SYMBOLIZE_SOURCE
        if(opt.stackShowSource && !filteredAddrs.empty())
            BatchResolveSource(filteredAddrs, filteredSymbols);
#endif

        timer.Stop();

        std::string joined;
        for(size_t i = 0; i < filteredSymbols.size(); ++i)
        {
            const auto& sym = filteredSymbols[i];

            std::string frame = sym.function;
            if(opt.stackShowSource && !sym.file.empty())
            {
                std::string path = opt.stackRelativePaths ? RelativizePath(sym.file) : sym.file;
                frame.append(" (");
                frame.append(path);
                if(sym.line >= 0)
                {
                    frame.push_back(':');
                    frame.append(std::to_string(sym.line));
                }
                frame.push_back(')');
            }
            else if(!hideUnresolvedFrames)
            {
                frame.append(" [");
                frame.append(sym.address);
                frame.push_back(']');
            }

            if(!joined.empty())
                joined.push_back('\n');
            joined.append("   ");
            joined.append(frame);
        }

        if(joined.empty())
            return {};

        std::string summary;
        summary.reserve(joined.size() + 48);
        summary.append("\n");
        summary.append(joined);
        summary.append("\n");
        summary.append("  resolved in ");
        summary.append(timer.ToString());
        return summary;
    }

    static void AppendStacktraceLines(const std::string&   raw,
                                      const FormatOptions& opt,
                                      std::string&         out,
                                      std::string_view     color)
    {
        std::string indent;
        if(opt.stackIndentSpaces > 0)
            indent.assign(static_cast<size_t>(opt.stackIndentSpaces), ' ');

        std::vector<uintptr_t> addrs;
        {
            size_t pos = 0;
            while(pos < raw.size())
            {
                size_t           end = raw.find('\n', pos);
                std::string_view entry(raw.data() + pos, (end == std::string::npos ? raw.size() : end) - pos);
                pos = (end == std::string::npos) ? raw.size() : end + 1;
                if(!entry.empty() && entry.back() == '\r')
                    entry.remove_suffix(1);
                entry = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(entry);
                if(entry.empty())
                    continue;
                uintptr_t addr = 0;
                if(ParseAddressLine(entry, addr))
                    addrs.push_back(addr);
            }
        }

        Ecstatica::Recompiled::LogSupport::Time::Timer timer;
        timer.Start();

        std::vector<FrameSymbol> symbols;
        symbols.reserve(addrs.size());
        for(uintptr_t addr : addrs)
            symbols.push_back(SymbolizeFrame(addr));

        std::vector<uintptr_t> filteredAddrs;
        std::vector<FrameSymbol> filteredSymbols;
        filteredAddrs.reserve(addrs.size());
        filteredSymbols.reserve(symbols.size());
        for(size_t i = 0; i < addrs.size(); ++i)
        {
            if(!ShouldIncludeFrame(symbols[i].function, symbols[i].address, false, false))
                continue;
            filteredAddrs.push_back(addrs[i]);
            filteredSymbols.push_back(std::move(symbols[i]));
        }

#if UT_LOG_CAN_SYMBOLIZE_SOURCE
        if(opt.stackShowSource && !filteredAddrs.empty())
            BatchResolveSource(filteredAddrs, filteredSymbols);
#endif

        timer.Stop();

        for(size_t i = 0; i < filteredSymbols.size(); ++i)
        {
            const auto& sym = filteredSymbols[i];
            std::string line = indent;
            line.append("at ");
            line.append(sym.function);

            if(opt.stackShowSource && !sym.file.empty())
            {
                std::string path = opt.stackRelativePaths ? RelativizePath(sym.file) : sym.file;
                line.append(" (");
                line.append(path);
                if(sym.line >= 0)
                {
                    line.push_back(':');
                    line.append(std::to_string(sym.line));
                }
                line.push_back(')');
            }
            else
            {
                line.append(" [");
                line.append(sym.address);
                line.push_back(']');
            }

            AppendColoredLine(out, color, opt.useColor, line);
        }

        std::string info(indent);
        info.append("stack resolved in ");
        info.append(timer.ToString());
        AppendColoredLine(out, color, opt.useColor, info);
    }

    static std::string BuildRecordSummary(const Record& rec, const FormatOptions& opt)
    {
        std::string line;
        line.reserve(rec.message.size() + 128);

        if(opt.includeTimestamp)
        {
            line.push_back('[');
            if(opt.humanTime)
                AppendHumanTime(line, rec.timePointWall, opt.timeZone);
            else
            {
                auto ms =
                    std::chrono::duration_cast<std::chrono::milliseconds>(rec.timePointWall.time_since_epoch()).count();
                AppendEpochMs(line, ms);
            }
            line.push_back(']');
        }

        if(opt.includeThreadName)
        {
            auto name = Ecstatica::Recompiled::LogSupport::Thread::Name::GetThreadNameById(rec.threadId);
            if(!name.empty())
            {
                line.push_back('[');
                line.append(name);
                line.push_back(']');
            }
        }

        if(opt.includeThread)
        {
            line.push_back('[');
            char b[24];
            int  n = std::snprintf(b, sizeof(b), "%llu", static_cast<unsigned long long>(rec.threadId));
            if(n > 0)
                line.append(b, static_cast<size_t>(n));
            line.push_back(']');
        }

        AppendModuleAndSubmodule(line, rec, opt);

        line.push_back('[');
        line.append(ToString(rec.level));
        line.push_back(']');

        if(opt.includeSeq)
        {
            char b[24];
            int  n = std::snprintf(b, sizeof(b), "[#%llu]", static_cast<unsigned long long>(rec.seq));
            if(n > 0)
                line.append(b, static_cast<size_t>(n));
        }

        line.push_back(' ');
        if(!rec.realtimeFormat.empty() && rec.realtimeFormatArgs != nullptr)
            AppendRealtimeFormattedMessage(line, rec);
        else
            line.append(rec.message.data(), rec.message.size());

        for(size_t i = 0; i < rec.fieldCount; ++i)
        {
            const auto& kv = rec.fields[i];
            if(IsKotlinThrowableField(kv))
                continue;

            line.push_back(' ');
            line.append(kv.key.data(), kv.key.size());
            line.push_back('=');
            line.append(kv.value.data(), kv.value.size());
        }

        const bool force_source = (rec.level == Level::Error || rec.level == Level::Fatal);
        if((opt.includeSource || force_source) && rec.src.file)
        {
            line.append(" [");
            line.append(RelativizePath(rec.src.file));
            char lb[16];
            int  n = std::snprintf(lb, sizeof(lb), ":%d", rec.src.line);
            if(n > 0)
                line.append(lb, static_cast<size_t>(n));
            line.push_back(']');
        }

        return line;
    }

    void FormatLine(const Record& rec, std::string& out, const FormatOptions& opt)
    {
        auto        color = LevelColor(rec.level);
        std::string line  = BuildRecordSummary(rec, opt);
        const auto  kotlinThrowable = ExtractKotlinThrowableFields(rec);

        if(kotlinThrowable.present)
        {
            std::string summary;
            if(!kotlinThrowable.type.empty())
                summary.append(kotlinThrowable.type.data(), kotlinThrowable.type.size());
            if(!kotlinThrowable.message.empty())
            {
                if(!summary.empty())
                    summary.append(": ");
                summary.append(kotlinThrowable.message.data(), kotlinThrowable.message.size());
            }
            if(summary.empty())
                summary = "present";

            std::string summaryLine = "  Kotlin throwable: ";
            summaryLine.append(summary);
            AppendColoredLine(out, color, opt.useColor, summaryLine);

            AppendMultilineSection(out, color, opt.useColor, "Kotlin stack", kotlinThrowable.stack);

            std::string causeSummary;
            if(!kotlinThrowable.causeType.empty())
                causeSummary.append(kotlinThrowable.causeType.data(), kotlinThrowable.causeType.size());
            if(!kotlinThrowable.causeMessage.empty())
            {
                if(!causeSummary.empty())
                    causeSummary.append(": ");
                causeSummary.append(kotlinThrowable.causeMessage.data(), kotlinThrowable.causeMessage.size());
            }
            if(!causeSummary.empty())
            {
                std::string causeSummaryLine = "  Kotlin cause: ";
                causeSummaryLine.append(causeSummary);
                AppendColoredLine(out, color, opt.useColor, causeSummaryLine);
            }

            AppendMultilineSection(out, color, opt.useColor, "Kotlin cause stack", kotlinThrowable.causeStack);
        }

        if(opt.includeStack && rec.callstack && !rec.callstack->empty())
            AppendStacktraceLines(*rec.callstack, opt, out, color);

        AppendColoredLine(out, color, opt.useColor, line);
    }

    void FormatAndroidLine(const Record& rec, std::string& out, const FormatOptions& opt)
    {
        auto        color = LevelColor(rec.level);
        std::string line  = BuildRecordSummary(rec, opt);
        const auto  kotlinThrowable = ExtractKotlinThrowableFields(rec);

        if(kotlinThrowable.present)
        {
            std::string summary;
            if(!kotlinThrowable.type.empty())
                summary.append(kotlinThrowable.type.data(), kotlinThrowable.type.size());
            if(!kotlinThrowable.message.empty())
            {
                if(!summary.empty())
                    summary.append(": ");
                summary.append(kotlinThrowable.message.data(), kotlinThrowable.message.size());
            }
            if(summary.empty())
                summary = "present";

            if(kAndroidCompactThrowable)
            {
                AppendCompactSection(line, "Kotlin throwable", summary, "");
                AppendCompactSection(line, "Kotlin stack", kotlinThrowable.stack, "");
            }

            std::string causeSummary;
            if(!kotlinThrowable.causeType.empty())
                causeSummary.append(kotlinThrowable.causeType.data(), kotlinThrowable.causeType.size());
            if(!kotlinThrowable.causeMessage.empty())
            {
                if(!causeSummary.empty())
                    causeSummary.append(": ");
                causeSummary.append(kotlinThrowable.causeMessage.data(), kotlinThrowable.causeMessage.size());
            }
            if(!causeSummary.empty())
                AppendCompactSection(line, "Kotlin cause", causeSummary, "");

            AppendCompactSection(line, "Kotlin cause stack", kotlinThrowable.causeStack, "");
        }

        if(opt.includeStack && rec.callstack && !rec.callstack->empty() && kAndroidCompactStack)
        {
            const std::string stackSummary =
                BuildStacktraceSummary(*rec.callstack, opt, kAndroidHideRuntimeFrames, kAndroidHideUnresolvedFrames);
            if(!stackSummary.empty())
                line.append(stackSummary);
        }

        AppendColoredLine(out, color, opt.useColor, line);
    }
} // namespace Ecstatica::Recompiled::Log
