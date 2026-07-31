#include "EcstaticaRuntimeBridge.h"

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static int e2r_is_option(const char *value, const char *option)
{
    return value != NULL && strcmp(value, option) == 0;
}

static int e2r_copy_string(char *dest, size_t dest_size, const char *value)
{
    const char *src = value != NULL ? value : "";
    size_t len = strlen(src);
    if (len + 1 > dest_size) {
        return 0;
    }
    memcpy(dest, src, len + 1);
    return 1;
}

static int e2r_set_error(E2R_RuntimeOptions *options, const char *message)
{
    if (options != NULL) {
        snprintf(options->error, sizeof(options->error), "%s", message != NULL ? message : "unknown error");
    }
    return 0;
}

static int e2r_need_value(int argc, int index, const char *option, E2R_RuntimeOptions *out)
{
    if (index + 1 < argc) {
        return 1;
    }

    char message[E2R_RUNTIME_ERROR_MAX];
    snprintf(message, sizeof(message), "%s requires a value", option);
    return e2r_set_error(out, message);
}

static int e2r_is_directory(const char *path)
{
    struct stat st;
    return path != NULL && stat(path, &st) == 0 && S_ISDIR(st.st_mode);
}

static int e2r_resolve_path(const char *path, char *out, size_t out_size)
{
    if (path == NULL || path[0] == '\0') {
        return e2r_copy_string(out, out_size, ".");
    }

    if (path[0] == '/') {
        return e2r_copy_string(out, out_size, path);
    }

    char cwd[PATH_MAX];
    if (getcwd(cwd, sizeof(cwd)) == NULL) {
        return 0;
    }

    int written = snprintf(out, out_size, "%s/%s", cwd, path);
    return written > 0 && (size_t)written < out_size;
}

static int e2r_create_directory_recursive(const char *path)
{
    char buffer[E2R_RUNTIME_PATH_MAX];
    size_t len;

    if (path == NULL || path[0] == '\0') {
        return 0;
    }
    if (e2r_is_directory(path)) {
        return 1;
    }
    if (!e2r_copy_string(buffer, sizeof(buffer), path)) {
        return 0;
    }

    len = strlen(buffer);
    while (len > 1 && buffer[len - 1] == '/') {
        buffer[--len] = '\0';
    }

    for (char *p = buffer + 1; *p != '\0'; ++p) {
        if (*p != '/') {
            continue;
        }
        *p = '\0';
        if (!e2r_is_directory(buffer) && mkdir(buffer, 0755) != 0 && errno != EEXIST) {
            *p = '/';
            return 0;
        }
        *p = '/';
    }

    return e2r_is_directory(buffer) || mkdir(buffer, 0755) == 0 || errno == EEXIST;
}

int E2R_RuntimeResolveOptions(int argc,
                              char **argv,
                              const char *fallback_game_data_dir,
                              const char *fallback_data_dir,
                              E2R_RuntimeOptions *options)
{
    const char *game_data_dir = fallback_game_data_dir != NULL ? fallback_game_data_dir : "";
    const char *data_dir = fallback_data_dir != NULL ? fallback_data_dir : "./data";
    const char *log_level = "";
    const char *log_disabled_modules = "";
    int index = 1;

    if (options == NULL) {
        return 0;
    }
    memset(options, 0, sizeof(*options));
    options->command_index = 1;

    while (index < argc) {
        if (e2r_is_option(argv[index], "--game-data-dir")) {
            if (!e2r_need_value(argc, index, "--game-data-dir", options)) {
                return 0;
            }
            game_data_dir = argv[index + 1];
            options->game_data_dir_explicit = 1;
            index += 2;
            continue;
        }
        if (e2r_is_option(argv[index], "--data-dir")) {
            if (!e2r_need_value(argc, index, "--data-dir", options)) {
                return 0;
            }
            data_dir = argv[index + 1];
            options->data_dir_explicit = 1;
            index += 2;
            continue;
        }
        if (e2r_is_option(argv[index], "--log-level")) {
            if (!e2r_need_value(argc, index, "--log-level", options)) {
                return 0;
            }
            log_level = argv[index + 1];
            options->log_requested = 1;
            index += 2;
            continue;
        }
        if (e2r_is_option(argv[index], "--log-disable-modules")) {
            if (!e2r_need_value(argc, index, "--log-disable-modules", options)) {
                return 0;
            }
            log_disabled_modules = argv[index + 1];
            options->log_requested = 1;
            index += 2;
            continue;
        }

        break;
    }

    options->command_index = index;

    if (game_data_dir[0] == '\0') {
        return e2r_set_error(options, "game data directory is empty");
    }
    if (!e2r_resolve_path(game_data_dir, options->game_data_dir, sizeof(options->game_data_dir))) {
        return e2r_set_error(options, "game data directory path is too long");
    }
    if (!e2r_resolve_path(data_dir, options->data_dir, sizeof(options->data_dir))) {
        return e2r_set_error(options, "runtime data directory path is too long");
    }
    if (!e2r_copy_string(options->log_level, sizeof(options->log_level), log_level)) {
        return e2r_set_error(options, "log level string is too long");
    }
    if (!e2r_copy_string(options->log_disabled_modules, sizeof(options->log_disabled_modules), log_disabled_modules)) {
        return e2r_set_error(options, "log module filter string is too long");
    }

    if (!e2r_is_directory(options->game_data_dir)) {
        return e2r_set_error(options, "game data directory does not exist or is not a directory");
    }
    if ((options->data_dir_explicit || options->log_requested) &&
        !e2r_create_directory_recursive(options->data_dir)) {
        return e2r_set_error(options, "runtime data directory could not be created");
    }

    return 1;
}

void E2R_RuntimePrintOptionHelp(void)
{
    puts("Runtime options, before command:");
    puts("  --game-data-dir <path>         Read-only original Ecstatica II data directory.");
    puts("  --data-dir <path>              Writable runtime output directory; defaults to ./data.");
    puts("  --log-level <level>            Trace, Debug, Info, Warning, Error, Fatal, or Off.");
    puts("  --log-disable-modules <list>   Comma-separated module names to suppress.");
}
