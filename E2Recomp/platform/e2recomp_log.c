#define E2R_LOG_NO_WRAP
#include "e2recomp_log.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#if E2R_ENABLE_RUNTIME_OPTIONS
#include "EcstaticaLogBridge.h"
#endif
#ifndef _WIN32
#include <pthread.h>
#endif

#ifndef _WIN32
static pthread_mutex_t e2r_log_mutex = PTHREAD_MUTEX_INITIALIZER;
#endif
static int e2r_log_line_start = 1;
#if E2R_ENABLE_RUNTIME_OPTIONS
static char e2r_diagnostic_line[4096];
static size_t e2r_diagnostic_length;

/* Called with the stderr mutex held; partial fprintf calls form one record. */
static void e2r_log_mirror(const char *message)
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

static void e2r_log_wall_time(char *out, size_t out_size)
{
    time_t now;
    struct tm tm_value;
    unsigned int millis = 0;

    if (out_size == 0) {
        return;
    }
#ifndef _WIN32
    struct timespec ts;

    if (clock_gettime(CLOCK_REALTIME, &ts) == 0) {
        now = ts.tv_sec;
        millis = (unsigned int)(ts.tv_nsec / 1000000u);
    } else
#endif
    {
        now = time(NULL);
    }
#ifndef _WIN32
    if (localtime_r(&now, &tm_value) != NULL) {
        snprintf(out, out_size, "%04d-%02d-%02d %02d:%02d:%02d.%03u",
                 tm_value.tm_year + 1900, tm_value.tm_mon + 1, tm_value.tm_mday,
                 tm_value.tm_hour, tm_value.tm_min, tm_value.tm_sec, millis);
        return;
    }
#endif
    snprintf(out, out_size, "0000-00-00 00:00:00.000");
}

static void e2r_log_prefix(FILE *stream)
{
    char wall[32];

    e2r_log_wall_time(wall, sizeof(wall));
    fprintf(stream, "[%s] ", wall);
}

int E2R_LogVfprintf(FILE *stream, const char *format, va_list args)
{
    int result;

    if (stream != stderr) {
        result = vfprintf(stream, format, args);
        return result;
    }

#ifndef _WIN32
    pthread_mutex_lock(&e2r_log_mutex);
#endif
    if (e2r_log_line_start) {
        e2r_log_prefix(stream);
    }
#if E2R_ENABLE_RUNTIME_OPTIONS
    va_list mirror_args;
    va_copy(mirror_args, args);
#endif
    result = vfprintf(stream, format, args);
    if (format != NULL && format[0] != '\0') {
        size_t len = strlen(format);
        e2r_log_line_start = len != 0 && format[len - 1] == '\n';
    }
#if E2R_ENABLE_RUNTIME_OPTIONS
    if (result >= 0) {
        char *message = malloc((size_t)result + 1);
        if (message) {
            vsnprintf(message, (size_t)result + 1, format, mirror_args);
            e2r_log_mirror(message);
            if (result > 0)
                e2r_log_line_start = message[result - 1] == '\n';
            free(message);
        }
    }
    va_end(mirror_args);
#endif
#ifndef _WIN32
    pthread_mutex_unlock(&e2r_log_mutex);
#endif
    return result;
}

int E2R_LogFprintf(FILE *stream, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    int result = E2R_LogVfprintf(stream, format, args);
    va_end(args);
    return result;
}
