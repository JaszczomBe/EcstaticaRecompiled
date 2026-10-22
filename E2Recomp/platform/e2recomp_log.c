#define E2R_LOG_NO_WRAP
#include "e2recomp_log.h"

#include <stdarg.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#if E2R_ENABLE_RUNTIME_OPTIONS
#include "EcstaticaLogBridge.h"
#endif
#ifndef _WIN32
#include <pthread.h>
#endif

#ifndef _WIN32
static pthread_mutex_t e2r_log_mutex = PTHREAD_MUTEX_INITIALIZER;
#endif
#if E2R_ENABLE_RUNTIME_OPTIONS
static char e2r_diagnostic_line[4096];
static size_t e2r_diagnostic_length;

/* Called with the stderr mutex held; partial fprintf calls form one record. */
static void e2r_log_submit(const char *message)
{
    while (*message) {
        char value = *message++;
        if (value != '\n')
            e2r_diagnostic_line[e2r_diagnostic_length++] = value;
        if (value == '\n' || e2r_diagnostic_length == sizeof(e2r_diagnostic_line) - 1) {
            e2r_diagnostic_line[e2r_diagnostic_length] = '\0';
            E2R_LogDiagnostic(e2r_diagnostic_line);
            e2r_diagnostic_length = 0;
        }
    }
}
#endif

void E2R_LogFlush(void)
{
#ifndef _WIN32
    pthread_mutex_lock(&e2r_log_mutex);
#endif
#if E2R_ENABLE_RUNTIME_OPTIONS
    if (e2r_diagnostic_length) {
        e2r_diagnostic_line[e2r_diagnostic_length] = '\0';
        E2R_LogDiagnostic(e2r_diagnostic_line);
        e2r_diagnostic_length = 0;
    }
#endif
#ifndef _WIN32
    pthread_mutex_unlock(&e2r_log_mutex);
#endif
}

int E2R_LogVfprintf(FILE *stream, const char *format, va_list args)
{
#if E2R_ENABLE_RUNTIME_OPTIONS
    if (stream == stderr && E2R_LogIsActive()) {
        char buffer[4096];
        char *message = buffer;
        va_list copy;
        va_copy(copy, args);
        int result = vsnprintf(buffer, sizeof(buffer), format, copy);
        va_end(copy);
        if (result < 0)
            return result;
        if ((size_t)result >= sizeof(buffer)) {
            message = malloc((size_t)result + 1);
            if (!message) {
                errno = ENOMEM;
                return -1;
            }
            vsnprintf(message, (size_t)result + 1, format, args);
        }
#ifndef _WIN32
        pthread_mutex_lock(&e2r_log_mutex);
#endif
        e2r_log_submit(message);
#ifndef _WIN32
        pthread_mutex_unlock(&e2r_log_mutex);
#endif
        if (message != buffer)
            free(message);
        return result;
    }
#endif
    /* Before bootstrap and in C-only builds, preserve ordinary stdio behavior.
       Arbitrary FILE* writes (including binary/surface dumps) never reach logging. */
    return vfprintf(stream, format, args);
}

int E2R_LogFprintf(FILE *stream, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    int result = E2R_LogVfprintf(stream, format, args);
    va_end(args);
    return result;
}
