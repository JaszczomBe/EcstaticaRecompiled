#ifndef E2RECOMP_LOG_H
#define E2RECOMP_LOG_H

#include <stdio.h>
#include <stdarg.h>

int E2R_LogFprintf(FILE *stream, const char *format, ...);
int E2R_LogVfprintf(FILE *stream, const char *format, va_list args);
void E2R_LogFlush(void);

#ifndef E2R_LOG_NO_WRAP
#define fprintf E2R_LogFprintf
#define vfprintf E2R_LogVfprintf
#endif

#endif
