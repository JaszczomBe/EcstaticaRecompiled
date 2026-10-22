#include "EcstaticaLogBridge.h"
#include "RunArtifacts.h"

#include <stdarg.h>

int E2R_LogBootstrap(const char *level, const char *disabled_modules, const char *data_dir)
{
    (void)level;
    (void)disabled_modules;
    (void)data_dir;
    return E2R_ArtifactsStart(data_dir);
}

int E2R_LogIsActive(void)
{
    return 0;
}

void E2R_LogDiagnostic(const char *message)
{
    (void)message;
}

void E2R_LogShutdown(void)
{
    E2R_ArtifactsShutdown();
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
