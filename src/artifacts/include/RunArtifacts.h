#pragma once
#ifdef __cplusplus
extern "C" {
#endif
int E2R_ArtifactsStart(const char *data_dir);
const char *E2R_ArtifactsDirectory(void);
void E2R_ArtifactsStopMaintenance(void);
void E2R_ArtifactsShutdown(void);
void E2R_ArtifactsReport(const char *message);
void E2R_ArtifactsSetReporter(void (*reporter)(const char *));
/* Hold root serialization and the source lease while freezing all replay files.
 * Exports outside a session tree require no writable lock files. */
void *E2R_ArtifactsLockSource(const char *replay_directory);
void E2R_ArtifactsUnlockSource(void *token);
#ifdef __cplusplus
}
#endif
