#pragma once

#include "e2recomp_win32_compat.h"

typedef struct E2R_HostWindow E2R_HostWindow;
typedef void (*E2R_HostMessageCallback)(UINT msg, WPARAM wparam, LPARAM lparam,
                                        void *user);

E2R_HostWindow *E2R_HostCreateWindow(const char *title, int x, int y,
                                     unsigned width, unsigned height);
void E2R_HostDestroyWindow(E2R_HostWindow *window);
void E2R_HostShowWindow(E2R_HostWindow *window);
void E2R_HostPollEvents(E2R_HostWindow *window,
                        E2R_HostMessageCallback message_callback,
                        void *user);
int E2R_HostPushSyntheticKeyDown(E2R_HostWindow *window, UINT vk);
int E2R_HostPresentIndexed8(E2R_HostWindow *window, const unsigned char *pixels,
                            unsigned width, unsigned height, unsigned pitch,
                            const uint32_t *palette_rgb);
int E2R_HostDumpPresentation(E2R_HostWindow *window, const char *prefix);

/* Read-only runtime snapshot for optional host-side actor diagnostics. */
#define E2R_ACTOR_CUE_CAPACITY 64
typedef struct E2R_ActorCue {
    int id, x, y, z, is_joe;
} E2R_ActorCue;
typedef struct E2R_ActorCueSnapshot {
    int scene_slot, origin_x, origin_z;
    unsigned count;
    E2R_ActorCue actors[E2R_ACTOR_CUE_CAPACITY];
} E2R_ActorCueSnapshot;
void E2R_GetActorCues(E2R_ActorCueSnapshot *snapshot);
