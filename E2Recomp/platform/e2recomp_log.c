#define E2R_LOG_NO_WRAP
#include "e2recomp_log.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#ifndef _WIN32
#include <pthread.h>
#endif

#ifndef _WIN32
static pthread_mutex_t e2r_log_mutex = PTHREAD_MUTEX_INITIALIZER;
#endif
static int e2r_log_line_start = 1;

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

int E2R_LogFprintf(FILE *stream, const char *format, ...)
{
    va_list args;
    int result;

    if (stream != stderr) {
        va_start(args, format);
        result = vfprintf(stream, format, args);
        va_end(args);
        return result;
    }

#ifndef _WIN32
    pthread_mutex_lock(&e2r_log_mutex);
#endif
    if (e2r_log_line_start) {
        e2r_log_prefix(stream);
    }
    va_start(args, format);
    result = vfprintf(stream, format, args);
    va_end(args);
    if (format != NULL && format[0] != '\0') {
        size_t len = strlen(format);
        e2r_log_line_start = len != 0 && format[len - 1] == '\n';
    }
#ifndef _WIN32
    pthread_mutex_unlock(&e2r_log_mutex);
#endif
    return result;
}
