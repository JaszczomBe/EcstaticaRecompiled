#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum E2R_LogLevel
{
    E2R_LOG_LEVEL_TRACE = 0,
    E2R_LOG_LEVEL_DEBUG = 1,
    E2R_LOG_LEVEL_INFO = 2,
    E2R_LOG_LEVEL_WARNING = 3,
    E2R_LOG_LEVEL_ERROR = 4,
    E2R_LOG_LEVEL_FATAL = 5,
    E2R_LOG_LEVEL_OFF = 6
};

enum E2R_LogModule
{
    E2R_LOG_MODULE_RUNTIME = 1ull << 0,
    E2R_LOG_MODULE_WIN32_COMPAT = 1ull << 1,
    E2R_LOG_MODULE_HOST_BACKEND = 1ull << 2,
    E2R_LOG_MODULE_DIRECTDRAW_COMPAT = 1ull << 3,
    E2R_LOG_MODULE_DIRECTSOUND_COMPAT = 1ull << 4,
    E2R_LOG_MODULE_PROBE = 1ull << 5,
    E2R_LOG_MODULE_RECONSTRUCTION = 1ull << 6,
    E2R_LOG_MODULE_SCRIPT = 1ull << 7,
    E2R_LOG_MODULE_ACTOR = 1ull << 8,
    E2R_LOG_MODULE_REQUESTER = 1ull << 9,
    E2R_LOG_MODULE_FILE_IO = 1ull << 10,
    E2R_LOG_MODULE_PRESENTATION = 1ull << 11,
    E2R_LOG_MODULE_TIMING = 1ull << 12,
    E2R_LOG_MODULE_AUDIO = 1ull << 13
};

enum E2R_LogTag
{
    E2R_LOG_TAG_STARTUP = 1ull << 0,
    E2R_LOG_TAG_INPUT = 1ull << 1,
    E2R_LOG_TAG_FILE_IO = 1ull << 2,
    E2R_LOG_TAG_PRESENTATION = 1ull << 3,
    E2R_LOG_TAG_SCRIPT = 1ull << 4,
    E2R_LOG_TAG_ACTOR = 1ull << 5,
    E2R_LOG_TAG_REQUESTER = 1ull << 6,
    E2R_LOG_TAG_TIMING = 1ull << 7,
    E2R_LOG_TAG_AUDIO = 1ull << 8,
    E2R_LOG_TAG_PROBE = 1ull << 9
};

void E2R_LogBootstrap(const char *level, const char *disabled_modules, const char *data_dir);
void E2R_LogShutdown(void);

void E2R_LogWrite(int level,
                  uint64_t module,
                  uint64_t tag,
                  const char *file,
                  const char *func,
                  int line,
                  const char *message);
void E2R_LogWritef(int level,
                   uint64_t module,
                   uint64_t tag,
                   const char *file,
                   const char *func,
                   int line,
                   const char *format,
                   ...);

#define E2R_LOG_WRITE(level, module, tag, message) \
    E2R_LogWrite((level), (module), (tag), __FILE__, __func__, __LINE__, (message))

#define E2R_LOG_INFO(module, tag, message) \
    E2R_LOG_WRITE(E2R_LOG_LEVEL_INFO, (module), (tag), (message))

#define E2R_LOG_WARNING(module, tag, message) \
    E2R_LOG_WRITE(E2R_LOG_LEVEL_WARNING, (module), (tag), (message))

#define E2R_LOG_ERROR(module, tag, message) \
    E2R_LOG_WRITE(E2R_LOG_LEVEL_ERROR, (module), (tag), (message))

#define E2R_LOG_INFOF(module, tag, format, ...) \
    E2R_LogWritef(E2R_LOG_LEVEL_INFO, (module), (tag), __FILE__, __func__, __LINE__, (format), __VA_ARGS__)

#define E2R_LOG_WARNINGF(module, tag, format, ...) \
    E2R_LogWritef(E2R_LOG_LEVEL_WARNING, (module), (tag), __FILE__, __func__, __LINE__, (format), __VA_ARGS__)

#define E2R_LOG_ERRORF(module, tag, format, ...) \
    E2R_LogWritef(E2R_LOG_LEVEL_ERROR, (module), (tag), __FILE__, __func__, __LINE__, (format), __VA_ARGS__)

#ifdef __cplusplus
}
#endif
