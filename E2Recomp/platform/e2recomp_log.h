#ifndef E2RECOMP_LOG_H
#define E2RECOMP_LOG_H

#include <stdio.h>

int E2R_LogFprintf(FILE *stream, const char *format, ...);

#ifndef E2R_LOG_NO_WRAP
#define fprintf E2R_LogFprintf
#endif

#endif
