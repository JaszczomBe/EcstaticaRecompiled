#include "e2recomp_host_backend.h"

#ifndef _WIN32
#include <SDL3/SDL.h>
#include <stdio.h>
#include <string.h>

struct E2R_HostWindow {
    SDL_Window *window;
    SDL_Surface *present_surface;
    unsigned present_width;
    unsigned present_height;
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
    if (window->present_surface != NULL) {
        SDL_DestroySurface(window->present_surface);
        window->present_surface = NULL;
        window->present_width = 0;
        window->present_height = 0;
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
    if (!SDL_IsMainThread()) {
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

static int e2r_sdl_ensure_present_surface(E2R_HostWindow *window,
                                          unsigned width, unsigned height)
{
    if (window->present_surface != NULL &&
        window->present_width == width && window->present_height == height) {
        return 1;
    }
    if (window->present_surface != NULL) {
        SDL_DestroySurface(window->present_surface);
        window->present_surface = NULL;
    }
    window->present_surface =
        SDL_CreateSurface((int)width, (int)height, SDL_PIXELFORMAT_ARGB8888);
    if (window->present_surface == NULL) {
        fprintf(stderr, "warning: SDL presentation surface creation failed: %s\n",
                SDL_GetError());
        window->present_width = 0;
        window->present_height = 0;
        return 0;
    }
    window->present_width = width;
    window->present_height = height;
    return 1;
}

int E2R_HostPresentIndexed8(E2R_HostWindow *window, const unsigned char *pixels,
                            unsigned width, unsigned height, unsigned pitch)
{
    SDL_Surface *window_surface;
    SDL_Rect dst_rect;
    Uint32 grayscale[256];
    unsigned i;
    unsigned y;

    if (window != &e2r_sdl_backend || window->window == NULL ||
        pixels == NULL || width == 0 || height == 0) {
        return 0;
    }
    if (!SDL_IsMainThread()) {
        return 0;
    }
    if (pitch == 0) {
        pitch = width;
    }
    if (pitch < width || width > 4096u || height > 4096u) {
        return 0;
    }
    if (!e2r_sdl_ensure_present_surface(window, width, height)) {
        return 0;
    }
    if (!SDL_LockSurface(window->present_surface)) {
        fprintf(stderr, "warning: SDL presentation surface lock failed: %s\n",
                SDL_GetError());
        return 0;
    }
    for (i = 0; i < 256u; i++) {
        grayscale[i] = SDL_MapSurfaceRGBA(window->present_surface,
                                          (Uint8)i, (Uint8)i, (Uint8)i, 255);
    }
    for (y = 0; y < height; y++) {
        const unsigned char *src = pixels + ((size_t)y * pitch);
        Uint32 *dst = (Uint32 *)((unsigned char *)window->present_surface->pixels +
                                 ((size_t)y * (size_t)window->present_surface->pitch));
        unsigned x;
        for (x = 0; x < width; x++) {
            dst[x] = grayscale[src[x]];
        }
    }
    SDL_UnlockSurface(window->present_surface);

    window_surface = SDL_GetWindowSurface(window->window);
    if (window_surface == NULL) {
        fprintf(stderr, "warning: SDL window surface unavailable: %s\n", SDL_GetError());
        return 0;
    }
    dst_rect.x = 0;
    dst_rect.y = 0;
    dst_rect.w = window_surface->w;
    dst_rect.h = window_surface->h;
    if (!SDL_BlitSurfaceScaled(window->present_surface, NULL, window_surface,
                               &dst_rect, SDL_SCALEMODE_PIXELART)) {
        fprintf(stderr, "warning: SDL presentation blit failed: %s\n", SDL_GetError());
        return 0;
    }
    if (!SDL_UpdateWindowSurface(window->window)) {
        fprintf(stderr, "warning: SDL presentation update failed: %s\n", SDL_GetError());
        return 0;
    }
    return 1;
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
int E2R_HostPresentIndexed8(E2R_HostWindow *window, const unsigned char *pixels,
                            unsigned width, unsigned height, unsigned pitch)
{
    (void)window; (void)pixels; (void)width; (void)height; (void)pitch;
    return 0;
}
#endif
