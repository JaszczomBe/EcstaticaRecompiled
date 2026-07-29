#pragma once

#include "e2recomp_win32_compat.h"

typedef struct E2R_HostWindow E2R_HostWindow;
typedef void (*E2R_HostKeyDownCallback)(UINT vk, void *user);

E2R_HostWindow *E2R_HostCreateWindow(const char *title, int x, int y,
                                     unsigned width, unsigned height);
void E2R_HostDestroyWindow(E2R_HostWindow *window);
void E2R_HostShowWindow(E2R_HostWindow *window);
void E2R_HostPollEvents(E2R_HostWindow *window,
                        E2R_HostKeyDownCallback keydown_callback,
                        void *user);
int E2R_HostPushSyntheticKeyDown(E2R_HostWindow *window, UINT vk);
int E2R_HostPresentIndexed8(E2R_HostWindow *window, const unsigned char *pixels,
                            unsigned width, unsigned height, unsigned pitch,
                            const uint32_t *palette_rgb);
