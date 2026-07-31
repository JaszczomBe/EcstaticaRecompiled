#pragma once

#include "Log/Core/LogWrite.h"
#include "Log/Modules/ModuleId.h"

#ifndef UT_LOG_MIN_LEVEL
    #ifdef NDEBUG
        #define UT_LOG_MIN_LEVEL Ecstatica::Recompiled::Log::Level::Info
    #else
        #define UT_LOG_MIN_LEVEL Ecstatica::Recompiled::Log::Level::Trace
    #endif
#endif

#define UT_SRC_LOC Ecstatica::Recompiled::Log::SourceLoc{__FILE__, __func__, __LINE__}

#define UT_LOG(lvl, module_id, msg) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLog((lvl), (module_id), UT_SRC_LOC, (msg)); \
    } while(0)

#define UT_LOG_FMT(lvl, module_id, fmt, ...) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLogf((lvl), (module_id), UT_SRC_LOC, (fmt) __VA_OPT__(, __VA_ARGS__)); \
    } while(0)

#define UT_LOGF(lvl, module_id, msg, fields_ptr, fields_count) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLog((lvl), (module_id), UT_SRC_LOC, (msg), (fields_ptr), (fields_count)); \
    } while(0)

#define UT_LOGF_FMT(lvl, module_id, fields_ptr, fields_count, fmt, ...) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLogfDetailed((lvl), (module_id), UT_SRC_LOC, (fields_ptr), (fields_count), false, 0, 0, (fmt) __VA_OPT__(, __VA_ARGS__)); \
    } while(0)

#define UT_LOG_STACK(lvl, module_id, msg) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLog((lvl), (module_id), UT_SRC_LOC, (msg), nullptr, 0, true); \
    } while(0)

#define UT_LOG_STACK_FMT(lvl, module_id, fmt, ...) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLogfDetailed((lvl), (module_id), UT_SRC_LOC, nullptr, 0, true, 0, 0, (fmt) __VA_OPT__(, __VA_ARGS__)); \
    } while(0)

#define UT_LOG_MASK(lvl, module_id, submodule_mask, msg) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLog((lvl), (module_id), UT_SRC_LOC, (msg), nullptr, 0, false, Ecstatica::Recompiled::Log::ToMask(module_id), (submodule_mask)); \
    } while(0)

#define UT_RT_LOG(lvl, module_id, msg) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteRealtimeLog((lvl), (module_id), UT_SRC_LOC, (msg)); \
    } while(0)

#define UT_RT_LOG_FMT(lvl, module_id, fmt, ...) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteRealtimeLogf((lvl), (module_id), UT_SRC_LOC, 0, 0, (fmt) __VA_OPT__(, __VA_ARGS__)); \
    } while(0)

#define UT_RT_LOG_MASK(lvl, module_id, submodule_mask, msg) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteRealtimeLog((lvl), (module_id), UT_SRC_LOC, (msg), Ecstatica::Recompiled::Log::ToMask(module_id), (submodule_mask)); \
    } while(0)

#define UT_RT_LOG_MASK_FMT(lvl, module_id, submodule_mask, fmt, ...) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteRealtimeLogf((lvl), (module_id), UT_SRC_LOC, Ecstatica::Recompiled::Log::ToMask(module_id), (submodule_mask), (fmt) __VA_OPT__(, __VA_ARGS__)); \
    } while(0)

#define UT_LOG_MASK_FMT(lvl, module_id, submodule_mask, fmt, ...) \
    do \
    { \
        if ((int)(lvl) >= (int)UT_LOG_MIN_LEVEL) \
            Ecstatica::Recompiled::Log::WriteLogfDetailed((lvl), (module_id), UT_SRC_LOC, nullptr, 0, false, Ecstatica::Recompiled::Log::ToMask(module_id), (submodule_mask), (fmt) __VA_OPT__(, __VA_ARGS__)); \
    } while(0)
