#include "Log/Core/LogWrite.h"

#include "Log/Core/Logger.h"

namespace Ecstatica::Recompiled::Log
{
    bool WriteLog(Level                lvl,
                  ModuleID             module,
                  SourceLoc            src,
                  std::string_view     msg,
                  const Record::Field* fields,
                  size_t               fieldCount,
                  bool                 withStack,
                  ModuleMask           moduleMaskOverride,
                  SubmoduleMask        submoduleMask)
    {
        return Logger::Instance().Log(
            lvl, module, src, msg, fields, fieldCount, withStack, moduleMaskOverride, submoduleMask);
    }

    bool WriteLogOwned(Level                lvl,
                       ModuleID             module,
                       SourceLoc            src,
                       std::string&&        msg,
                       const Record::Field* fields,
                       size_t               fieldCount,
                       bool                 withStack,
                       ModuleMask           moduleMaskOverride,
                       SubmoduleMask        submoduleMask)
    {
        return Logger::Instance().LogOwned(
            lvl, module, src, std::move(msg), fields, fieldCount, withStack, moduleMaskOverride, submoduleMask);
    }

    bool WriteRealtimeLog(Level            lvl,
                          ModuleID         module,
                          SourceLoc        src,
                          std::string_view msg,
                          ModuleMask       moduleMaskOverride,
                          SubmoduleMask    submoduleMask)
    {
        return Logger::Instance().LogRealtime(lvl, module, src, msg, moduleMaskOverride, submoduleMask);
    }

    bool WriteRealtimeLogfCaptured(Level                              lvl,
                                   ModuleID                           module,
                                   SourceLoc                          src,
                                   std::string_view                   fmt,
                                   const detail::RealtimeTextArgCapture* args,
                                   size_t                             argCount,
                                   ModuleMask                         moduleMaskOverride,
                                   SubmoduleMask                      submoduleMask)
    {
        return Logger::Instance().LogRealtimeFormatted(
            lvl, module, src, fmt, args, argCount, moduleMaskOverride, submoduleMask);
    }
}
