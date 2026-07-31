#include "EcstaticaLogBridge.h"

#include <stdarg.h>

void E2R_LogBootstrap(const char *level, const char *disabled_modules, const char *data_dir)
{
    (void)level;
    (void)disabled_modules;
    (void)data_dir;
}

void E2R_LogShutdown(void)
{
}

void E2R_LogWrite(int level,
                  uint64_t module,
                  uint64_t tag,
                  const char *file,
                  const char *func,
                  int line,
                  const char *message)
{
    (void)level;
    (void)module;
    (void)tag;
    (void)file;
    (void)func;
    (void)line;
    (void)message;
}

void E2R_LogWritef(int level,
                   uint64_t module,
                   uint64_t tag,
                   const char *file,
                   const char *func,
                   int line,
                   const char *format,
                   ...)
{
    va_list ap;
    va_start(ap, format);
    va_end(ap);
    (void)level;
    (void)module;
    (void)tag;
    (void)file;
    (void)func;
    (void)line;
    (void)format;
}
