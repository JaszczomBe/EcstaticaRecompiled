#pragma once
#include <stdint.h>
#if E2R_ENABLE_RUNTIME_OPTIONS
#ifdef __cplusplus
extern "C" {
#endif
typedef void (*E2R_InspectSampler)(void);
void E2R_InspectStart(const char *session, E2R_InspectSampler sampler);
void E2R_InspectFinish(void);
void E2R_InspectObserve(const char *kind, int64_t a, int64_t b);
void E2R_InspectUpdate(int completed);
void E2R_InspectField(const char *scope, int id, const char *name, int64_t value);
/* Returns a fresh prefix only when a bounded frame capture is due. */
const char *E2R_InspectPresent(void);
void E2R_InspectFrameResult(int success);
#ifdef __cplusplus
}
#endif
#else
#define E2R_InspectStart(...) ((void)0)
#define E2R_InspectFinish(...) ((void)0)
#define E2R_InspectObserve(...) ((void)0)
#define E2R_InspectUpdate(...) ((void)0)
#define E2R_InspectField(...) ((void)0)
#define E2R_InspectPresent() ((const char *)0)
#define E2R_InspectFrameResult(...) ((void)0)
#endif
