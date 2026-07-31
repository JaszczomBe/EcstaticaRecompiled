#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#define E2R_RUNTIME_PATH_MAX 4096
#define E2R_RUNTIME_ERROR_MAX 512

typedef struct E2R_RuntimeOptions
{
    char game_data_dir[E2R_RUNTIME_PATH_MAX];
    char data_dir[E2R_RUNTIME_PATH_MAX];
    char log_level[32];
    char log_disabled_modules[256];
    int command_index;
    int game_data_dir_explicit;
    int data_dir_explicit;
    int log_requested;
    char error[E2R_RUNTIME_ERROR_MAX];
} E2R_RuntimeOptions;

int E2R_RuntimeResolveOptions(int argc,
                              char **argv,
                              const char *fallback_game_data_dir,
                              const char *fallback_data_dir,
                              E2R_RuntimeOptions *options);
void E2R_RuntimePrintOptionHelp(void);

#ifdef __cplusplus
}
#endif
