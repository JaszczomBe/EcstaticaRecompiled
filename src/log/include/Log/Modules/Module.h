#pragma once

#include "Log/Macros/Macros.h"
#include "Log/Modules/ModuleId.h"

#define UT_MODULE(module_id) \
    [[maybe_unused]] static constexpr Ecstatica::Recompiled::Log::ModuleID UT_CURRENT_MODULE_ID = (module_id); \
    [[maybe_unused]] static constexpr Ecstatica::Recompiled::Log::ModuleMask UT_CURRENT_MODULE_MASK = Ecstatica::Recompiled::Log::ToMask(module_id)

#define UT_LOGM(lvl, msg) \
    UT_LOG(lvl, UT_CURRENT_MODULE_ID, msg)

#define UT_LOGM_FMT(lvl, fmt, ...) \
    UT_LOG_FMT(lvl, UT_CURRENT_MODULE_ID, fmt __VA_OPT__(,) __VA_ARGS__)

#define UT_LOGM_F(lvl, msg, fields_ptr, fields_count) \
    UT_LOGF(lvl, UT_CURRENT_MODULE_ID, msg, fields_ptr, fields_count)

#define UT_LOGM_F_FMT(lvl, fields_ptr, fields_count, fmt, ...) \
    UT_LOGF_FMT(lvl, UT_CURRENT_MODULE_ID, fields_ptr, fields_count, fmt __VA_OPT__(,) __VA_ARGS__)

#define UT_LOGM_STACK(lvl, msg) \
    UT_LOG_STACK(lvl, UT_CURRENT_MODULE_ID, msg)

#define UT_LOGM_STACK_FMT(lvl, fmt, ...) \
    UT_LOG_STACK_FMT(lvl, UT_CURRENT_MODULE_ID, fmt __VA_OPT__(,) __VA_ARGS__)

#define UT_LOGM_MASK(lvl, submodule_mask, msg) \
    UT_LOG_MASK(lvl, UT_CURRENT_MODULE_ID, submodule_mask, msg)

#define UT_RT_LOGM(lvl, msg) \
    UT_RT_LOG(lvl, UT_CURRENT_MODULE_ID, msg)

#define UT_RT_LOGM_FMT(lvl, fmt, ...) \
    UT_RT_LOG_FMT(lvl, UT_CURRENT_MODULE_ID, fmt __VA_OPT__(,) __VA_ARGS__)

#define UT_RT_LOGM_MASK(lvl, submodule_mask, msg) \
    UT_RT_LOG_MASK(lvl, UT_CURRENT_MODULE_ID, submodule_mask, msg)

#define UT_RT_LOGM_MASK_FMT(lvl, submodule_mask, fmt, ...) \
    UT_RT_LOG_MASK_FMT(lvl, UT_CURRENT_MODULE_ID, submodule_mask, fmt __VA_OPT__(,) __VA_ARGS__)

#define UT_LOGM_MASK_FMT(lvl, submodule_mask, fmt, ...) \
    UT_LOG_MASK_FMT(lvl, UT_CURRENT_MODULE_ID, submodule_mask, fmt __VA_OPT__(,) __VA_ARGS__)
