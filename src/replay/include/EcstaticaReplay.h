#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Stable debugger-visible progress, including individual expanded clock calls.
 */
extern volatile uint64_t E2R_replay_sequence;
extern volatile uint64_t E2R_replay_last_checkpoint;
typedef void (*E2R_ReplaySampler)(void);
typedef void (*E2R_ReplayDelivery)(unsigned message, uintptr_t key,
                                   intptr_t lparam);
/* Freeze and validate source BEFORE logger/artifact startup can run retention.
 */
int E2R_ReplayPrepare(const char *path);
int E2R_ReplayStart(const char *record, int gameplay, const char *session,
                    const char *game_data, int argc, char **argv,
                    int compatible, uint64_t stop_sequence,
                    uint64_t stop_checkpoint, E2R_ReplaySampler sampler);
void E2R_ReplayFinish(void);
void E2R_ReplaySetHostControl(void (*poll)(void), void (*flush)(void));
int E2R_ReplayPlaying(void);
int E2R_ReplayCaptureIncomplete(void);
void E2R_ReplayAbort(void);
uint32_t E2R_ReplayClock(uint32_t host_result);
void E2R_ReplayLocalTime(uint16_t fields[8]);
void E2R_ReplayPumpBegin(void);
void E2R_ReplayPumpInputs(E2R_ReplayDelivery deliver);
void E2R_ReplayPumpEnd(void);
void E2R_ReplayInput(unsigned message, uintptr_t key, intptr_t lparam, int x,
                     int y);
void E2R_ReplayQueued(unsigned message, uintptr_t key, intptr_t lparam);
void E2R_ReplayService(const char *kind, int64_t a, int64_t b);
/* Called only by the pure native sampler. Field names/IDs never contain
 * addresses. */
void E2R_ReplayField(const char *scope, int id, const char *field,
                     int64_t value);
#ifdef __cplusplus
}
#endif
