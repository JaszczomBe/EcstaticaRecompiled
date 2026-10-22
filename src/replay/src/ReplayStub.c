#include "EcstaticaReplay.h"
volatile uint64_t E2R_replay_sequence, E2R_replay_last_checkpoint;
int E2R_ReplayPrepare(const char *p) { return !p || !*p; }
int E2R_ReplayStart(const char *r, int g, const char *s, const char *d, int n,
                    char **a, int c, uint64_t x, uint64_t y,
                    E2R_ReplaySampler f) {
  return 1;
}
void E2R_ReplayFinish(void) {}
int E2R_ReplayPlaying(void) { return 0; }
int E2R_ReplayCaptureIncomplete(void) { return 0; }
void E2R_ReplayAbort(void) {}
uint32_t E2R_ReplayClock(uint32_t v) { return v; }
void E2R_ReplayLocalTime(uint16_t f[8]) {}
void E2R_ReplayPumpBegin(void) {}
void E2R_ReplayPumpInputs(E2R_ReplayDelivery f) {}
void E2R_ReplayPumpEnd(void) {}
void E2R_ReplayInput(unsigned m, uintptr_t k, intptr_t l, int x, int y) {}
void E2R_ReplayQueued(unsigned m, uintptr_t k, intptr_t l) {}
void E2R_ReplayService(const char *k, int64_t a, int64_t b) {}
void E2R_ReplayField(const char *s, int i, const char *n, int64_t v) {}

void E2R_ReplaySetHostControl(void (*p)(void), void (*f)(void)) {}
