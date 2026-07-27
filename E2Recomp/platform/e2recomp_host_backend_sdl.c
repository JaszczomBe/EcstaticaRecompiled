#include "e2recomp_host_backend.h"

#ifndef _WIN32
#include <SDL3/SDL.h>
#include <stdio.h>
#include <string.h>

struct E2R_HostWindow {
    SDL_Window *window;
};

static E2R_HostWindow e2r_sdl_backend;
static int e2r_sdl_initialized;

static UINT e2r_virtual_key_from_sdl(SDL_Keycode key)
{
    if (key >= SDLK_A && key <= SDLK_Z) {
        return (UINT)('A' + (key - SDLK_A));
    }
    if (key >= SDLK_0 && key <= SDLK_9) {
        return (UINT)('0' + (key - SDLK_0));
    }
    if (key >= SDLK_KP_0 && key <= SDLK_KP_9) {
        return 0x60u + (UINT)(key - SDLK_KP_0);
    }
    if (key >= SDLK_F1 && key <= SDLK_F12) {
        return 0x70u + (UINT)(key - SDLK_F1);
    }
    switch (key) {
    case SDLK_ESCAPE: return VK_ESCAPE;
    case SDLK_RETURN:
    case SDLK_KP_ENTER: return VK_RETURN;
    case SDLK_SPACE: return VK_SPACE;
    case SDLK_LCTRL:
    case SDLK_RCTRL: return 0x11;
    case SDLK_LEFT: return 0x64;
    case SDLK_UP: return 0x68;
    case SDLK_RIGHT: return 0x66;
    case SDLK_DOWN: return 0x62;
    default: return 0;
    }
}

static SDL_Keycode e2r_sdl_key_from_virtual_key(UINT vk)
{
    if (vk >= 'A' && vk <= 'Z') {
        return SDLK_A + (SDL_Keycode)(vk - 'A');
    }
    if (vk >= '0' && vk <= '9') {
        return SDLK_0 + (SDL_Keycode)(vk - '0');
    }
    if (vk >= 0x60u && vk <= 0x69u) {
        return SDLK_KP_0 + (SDL_Keycode)(vk - 0x60u);
    }
    if (vk >= 0x70u && vk <= 0x7bu) {
        return SDLK_F1 + (SDL_Keycode)(vk - 0x70u);
    }
    switch (vk) {
    case VK_ESCAPE: return SDLK_ESCAPE;
    case VK_RETURN: return SDLK_RETURN;
    case VK_SPACE: return SDLK_SPACE;
    case 0x11: return SDLK_LCTRL;
    case 0x64: return SDLK_LEFT;
    case 0x68: return SDLK_UP;
    case 0x66: return SDLK_RIGHT;
    case 0x62: return SDLK_DOWN;
    default: return SDLK_UNKNOWN;
    }
}

E2R_HostWindow *E2R_HostCreateWindow(const char *title, int x, int y,
                                     unsigned width, unsigned height)
{
    if (!e2r_sdl_initialized) {
        if (!SDL_InitSubSystem(SDL_INIT_VIDEO)) {
            fprintf(stderr, "warning: SDL video init failed: %s\n", SDL_GetError());
            return NULL;
        }
        e2r_sdl_initialized = 1;
    }
    if (e2r_sdl_backend.window == NULL) {
        e2r_sdl_backend.window =
            SDL_CreateWindow(title ? title : "Ecstatica II",
                             (int)width, (int)height, 0);
    }
    if (e2r_sdl_backend.window == NULL) {
        fprintf(stderr, "warning: SDL window creation failed: %s\n", SDL_GetError());
        return NULL;
    }
    if (x >= 0 && y >= 0) {
        SDL_SetWindowPosition(e2r_sdl_backend.window, x, y);
    }
    return &e2r_sdl_backend;
}

void E2R_HostDestroyWindow(E2R_HostWindow *window)
{
    if (window != &e2r_sdl_backend || window->window == NULL) {
        return;
    }
    SDL_DestroyWindow(window->window);
    window->window = NULL;
}

void E2R_HostShowWindow(E2R_HostWindow *window)
{
    if (window != &e2r_sdl_backend || window->window == NULL) {
        return;
    }
    SDL_ShowWindow(window->window);
}

void E2R_HostPollEvents(E2R_HostWindow *window,
                        E2R_HostKeyDownCallback keydown_callback,
                        void *user)
{
    SDL_Event event;

    if (window != &e2r_sdl_backend || window->window == NULL) {
        return;
    }
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_EVENT_KEY_DOWN && keydown_callback != NULL) {
            UINT vk = e2r_virtual_key_from_sdl(event.key.key);
            if (vk != 0) {
                keydown_callback(vk, user);
            }
        }
    }
}

int E2R_HostPushSyntheticKeyDown(E2R_HostWindow *window, UINT vk)
{
    SDL_Event event;
    SDL_Keycode key;

    if (window != &e2r_sdl_backend || window->window == NULL) {
        return 0;
    }
    key = e2r_sdl_key_from_virtual_key(vk);
    if (key == SDLK_UNKNOWN) {
        return 0;
    }
    memset(&event, 0, sizeof(event));
    event.type = SDL_EVENT_KEY_DOWN;
    event.key.type = SDL_EVENT_KEY_DOWN;
    event.key.down = true;
    event.key.windowID = SDL_GetWindowID(window->window);
    event.key.key = key;
    return SDL_PushEvent(&event);
}
#else
struct E2R_HostWindow {
    int unused;
};

E2R_HostWindow *E2R_HostCreateWindow(const char *title, int x, int y,
                                     unsigned width, unsigned height)
{
    (void)title; (void)x; (void)y; (void)width; (void)height;
    return NULL;
}

void E2R_HostDestroyWindow(E2R_HostWindow *window) { (void)window; }
void E2R_HostShowWindow(E2R_HostWindow *window) { (void)window; }
void E2R_HostPollEvents(E2R_HostWindow *window,
                        E2R_HostKeyDownCallback keydown_callback,
                        void *user)
{
    (void)window; (void)keydown_callback; (void)user;
}
int E2R_HostPushSyntheticKeyDown(E2R_HostWindow *window, UINT vk)
{
    (void)window; (void)vk;
    return 0;
}
#endif
