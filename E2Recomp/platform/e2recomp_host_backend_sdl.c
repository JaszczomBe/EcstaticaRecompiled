#include "e2recomp_host_backend.h"

#ifndef _WIN32
#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct E2R_HostWindow {
    SDL_Window *window;
    SDL_Surface *present_surface;
    unsigned present_width;
    unsigned present_height;
    SDL_Rect presentation_rect;
    int has_presentation_rect;
};

static E2R_HostWindow e2r_sdl_backend;
static int e2r_sdl_initialized;

static int e2r_sdl_present_diag_enabled(void)
{
    static int initialized;
    static int enabled;

    if (!initialized) {
        const char *diag = getenv("E2R_PRESENT_DIAG");
        enabled = diag != NULL && diag[0] != '\0' && diag[0] != '0';
        initialized = 1;
    }
    return enabled;
}

static int e2r_sdl_input_diag_enabled(void)
{
    static int initialized;
    static int enabled;

    if (!initialized) {
        const char *diag = getenv("E2R_INPUT_DIAG");
#ifndef NDEBUG
        enabled = diag == NULL || diag[0] == '\0' || diag[0] != '0';
#else
        enabled = diag != NULL && diag[0] != '\0' && diag[0] != '0';
#endif
        fprintf(stderr, "host input diag: enabled=%d env=%s\n",
                enabled, diag != NULL ? diag : "<unset>");
        initialized = 1;
    }
    return enabled;
}

static int e2r_sdl_menu_diag_enabled(void)
{
    static int initialized;
    static int enabled;

    if (!initialized) {
        const char *diag = getenv("E2R_MENU_DIAG");
        enabled = diag != NULL && diag[0] != '\0' && diag[0] != '0';
        initialized = 1;
    }
    return enabled;
}

static SDL_Rect e2r_sdl_aspect_fit_rect(int dst_width, int dst_height,
                                        unsigned src_width, unsigned src_height)
{
    SDL_Rect rect;

    rect.x = 0;
    rect.y = 0;
    rect.w = dst_width > 0 ? dst_width : 0;
    rect.h = dst_height > 0 ? dst_height : 0;
    if (dst_width <= 0 || dst_height <= 0 || src_width == 0 || src_height == 0) {
        return rect;
    }

    if ((int64_t)dst_width * (int64_t)src_height >
        (int64_t)dst_height * (int64_t)src_width) {
        rect.h = dst_height;
        rect.w = (int)((int64_t)dst_height * (int64_t)src_width /
                       (int64_t)src_height);
        if (rect.w < 1) {
            rect.w = 1;
        }
        rect.x = (dst_width - rect.w) / 2;
    }
    else {
        rect.w = dst_width;
        rect.h = (int)((int64_t)dst_width * (int64_t)src_height /
                       (int64_t)src_width);
        if (rect.h < 1) {
            rect.h = 1;
        }
        rect.y = (dst_height - rect.h) / 2;
    }
    return rect;
}

static LPARAM e2r_pack_point(float x, float y)
{
    int xi = (int)x;
    int yi = (int)y;
    return (LPARAM)(((unsigned int)xi & 0xffffu) |
                    (((unsigned int)yi & 0xffffu) << 16));
}

static LPARAM e2r_pack_mapped_window_point(E2R_HostWindow *window, float x, float y)
{
    SDL_Rect rect;
    int mapped_x;
    int mapped_y;

    if (window == NULL || !window->has_presentation_rect ||
        window->present_width == 0 || window->present_height == 0) {
        return e2r_pack_point(x, y);
    }

    rect = window->presentation_rect;
    if (rect.w <= 0 || rect.h <= 0) {
        return e2r_pack_point(x, y);
    }

    mapped_x = (int)(((x - (float)rect.x) * (float)window->present_width) /
                     (float)rect.w);
    mapped_y = (int)(((y - (float)rect.y) * (float)window->present_height) /
                     (float)rect.h);
    if (mapped_x < 0) {
        mapped_x = 0;
    }
    if (mapped_y < 0) {
        mapped_y = 0;
    }
    if (mapped_x >= (int)window->present_width) {
        mapped_x = (int)window->present_width - 1;
    }
    if (mapped_y >= (int)window->present_height) {
        mapped_y = (int)window->present_height - 1;
    }
    return e2r_pack_point((float)mapped_x, (float)mapped_y);
}

static const char *e2r_sdl_event_name(Uint32 type)
{
    switch (type) {
    case SDL_EVENT_QUIT: return "quit";
    case SDL_EVENT_WINDOW_SHOWN: return "window shown";
    case SDL_EVENT_WINDOW_HIDDEN: return "window hidden";
    case SDL_EVENT_WINDOW_EXPOSED: return "window exposed";
    case SDL_EVENT_WINDOW_MOVED: return "window moved";
    case SDL_EVENT_WINDOW_RESIZED: return "window resized";
    case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED: return "window pixel size changed";
    case SDL_EVENT_WINDOW_MINIMIZED: return "window minimized";
    case SDL_EVENT_WINDOW_MAXIMIZED: return "window maximized";
    case SDL_EVENT_WINDOW_RESTORED: return "window restored";
    case SDL_EVENT_WINDOW_MOUSE_ENTER: return "window mouse enter";
    case SDL_EVENT_WINDOW_MOUSE_LEAVE: return "window mouse leave";
    case SDL_EVENT_WINDOW_FOCUS_GAINED: return "window focus gained";
    case SDL_EVENT_WINDOW_FOCUS_LOST: return "window focus lost";
    case SDL_EVENT_WINDOW_CLOSE_REQUESTED: return "window close requested";
    case SDL_EVENT_KEY_DOWN: return "key down";
    case SDL_EVENT_KEY_UP: return "key up";
    case SDL_EVENT_TEXT_INPUT: return "text input";
    case SDL_EVENT_MOUSE_MOTION: return "mouse motion";
    case SDL_EVENT_MOUSE_BUTTON_DOWN: return "mouse button down";
    case SDL_EVENT_MOUSE_BUTTON_UP: return "mouse button up";
    case SDL_EVENT_MOUSE_WHEEL: return "mouse wheel";
    default: return "other";
    }
}

static int e2r_sdl_should_log_event(Uint32 type)
{
    switch (type) {
    case SDL_EVENT_QUIT:
    case SDL_EVENT_KEY_DOWN:
    case SDL_EVENT_KEY_UP:
    case SDL_EVENT_TEXT_INPUT:
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
    case SDL_EVENT_MOUSE_BUTTON_UP:
    case SDL_EVENT_WINDOW_RESIZED:
    case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
    case SDL_EVENT_WINDOW_MINIMIZED:
    case SDL_EVENT_WINDOW_MAXIMIZED:
    case SDL_EVENT_WINDOW_RESTORED:
    case SDL_EVENT_WINDOW_FOCUS_GAINED:
    case SDL_EVENT_WINDOW_FOCUS_LOST:
    case SDL_EVENT_WINDOW_CLOSE_REQUESTED:
        return 1;
    default:
        return 0;
    }
}

static int e2r_sdl_should_log_window_message(Uint32 type)
{
    switch (type) {
    case SDL_EVENT_WINDOW_RESIZED:
    case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
    case SDL_EVENT_WINDOW_MINIMIZED:
    case SDL_EVENT_WINDOW_MAXIMIZED:
    case SDL_EVENT_WINDOW_RESTORED:
    case SDL_EVENT_WINDOW_FOCUS_GAINED:
    case SDL_EVENT_WINDOW_FOCUS_LOST:
    case SDL_EVENT_WINDOW_CLOSE_REQUESTED:
        return 1;
    default:
        return 0;
    }
}

static const char *e2r_sdl_scancode_name(SDL_Scancode scancode)
{
    switch (scancode) {
    case SDL_SCANCODE_ESCAPE: return "Escape";
    case SDL_SCANCODE_RETURN: return "Return";
    case SDL_SCANCODE_SPACE: return "Space";
    case SDL_SCANCODE_LCTRL: return "LeftCtrl";
    case SDL_SCANCODE_RCTRL: return "RightCtrl";
    case SDL_SCANCODE_LALT: return "LeftAlt";
    case SDL_SCANCODE_RALT: return "RightAlt";
    case SDL_SCANCODE_LSHIFT: return "LeftShift";
    case SDL_SCANCODE_RSHIFT: return "RightShift";
    case SDL_SCANCODE_LEFT: return "Left";
    case SDL_SCANCODE_RIGHT: return "Right";
    case SDL_SCANCODE_UP: return "Up";
    case SDL_SCANCODE_DOWN: return "Down";
    case SDL_SCANCODE_F1: return "F1";
    case SDL_SCANCODE_F2: return "F2";
    case SDL_SCANCODE_F3: return "F3";
    case SDL_SCANCODE_F4: return "F4";
    case SDL_SCANCODE_F5: return "F5";
    case SDL_SCANCODE_F6: return "F6";
    case SDL_SCANCODE_F7: return "F7";
    case SDL_SCANCODE_F8: return "F8";
    case SDL_SCANCODE_F9: return "F9";
    case SDL_SCANCODE_F10: return "F10";
    case SDL_SCANCODE_F11: return "F11";
    case SDL_SCANCODE_F12: return "F12";
    default:
        if (scancode >= SDL_SCANCODE_A && scancode <= SDL_SCANCODE_Z) {
            static char names[26][2];
            int index = (int)scancode - (int)SDL_SCANCODE_A;
            names[index][0] = (char)('A' + index);
            names[index][1] = '\0';
            return names[index];
        }
        return "Other";
    }
}

static void e2r_sdl_log_keyboard_snapshot(E2R_HostWindow *window)
{
    static uint64_t last_mask;
    static unsigned snapshot_diag_count;
    static const SDL_Scancode watched[] = {
        SDL_SCANCODE_ESCAPE, SDL_SCANCODE_RETURN, SDL_SCANCODE_SPACE,
        SDL_SCANCODE_LEFT, SDL_SCANCODE_RIGHT, SDL_SCANCODE_UP, SDL_SCANCODE_DOWN,
        SDL_SCANCODE_LCTRL, SDL_SCANCODE_RCTRL, SDL_SCANCODE_LALT, SDL_SCANCODE_RALT,
        SDL_SCANCODE_LSHIFT, SDL_SCANCODE_RSHIFT,
        SDL_SCANCODE_A, SDL_SCANCODE_C, SDL_SCANCODE_D, SDL_SCANCODE_M,
        SDL_SCANCODE_P, SDL_SCANCODE_Q, SDL_SCANCODE_S, SDL_SCANCODE_W, SDL_SCANCODE_X,
        SDL_SCANCODE_Z, SDL_SCANCODE_F1, SDL_SCANCODE_F2, SDL_SCANCODE_F3,
        SDL_SCANCODE_F4, SDL_SCANCODE_F5, SDL_SCANCODE_F6, SDL_SCANCODE_F7,
        SDL_SCANCODE_F8, SDL_SCANCODE_F9, SDL_SCANCODE_F10, SDL_SCANCODE_F11,
        SDL_SCANCODE_F12
    };
    int key_count = 0;
    const bool *keys = SDL_GetKeyboardState(&key_count);
    uint64_t mask = 0;
    size_t i;

    if (keys == NULL) {
        return;
    }
    for (i = 0; i < sizeof(watched) / sizeof(watched[0]); i++) {
        int scancode = (int)watched[i];
        if (scancode < key_count && keys[scancode]) {
            mask |= (uint64_t)1u << i;
        }
    }
    if (mask == last_mask || snapshot_diag_count >= 256u) {
        return;
    }
    fprintf(stderr, "host keyboard state: focus=%d keys=",
            SDL_GetKeyboardFocus() == window->window);
    if (mask == 0) {
        fprintf(stderr, "<none>");
    }
    else {
        int first = 1;
        for (i = 0; i < sizeof(watched) / sizeof(watched[0]); i++) {
            if ((mask & ((uint64_t)1u << i)) != 0) {
                fprintf(stderr, "%s%s", first ? "" : ",",
                        e2r_sdl_scancode_name(watched[i]));
                first = 0;
            }
        }
    }
    fprintf(stderr, "\n");
    last_mask = mask;
    snapshot_diag_count++;
}

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
    case SDLK_RCTRL: return VK_CONTROL;
    case SDLK_LALT: return VK_MENU;
    case SDLK_RALT: return VK_RMENU;
    case SDLK_LSHIFT:
    case SDLK_RSHIFT: return VK_SHIFT;
    case SDLK_LEFT: return VK_LEFT;
    case SDLK_UP: return VK_UP;
    case SDLK_RIGHT: return VK_RIGHT;
    case SDLK_DOWN: return VK_DOWN;
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
    case VK_CONTROL: return SDLK_LCTRL;
    case VK_MENU: return SDLK_LALT;
    case VK_RMENU: return SDLK_RALT;
    case VK_SHIFT: return SDLK_LSHIFT;
    case VK_LEFT: return SDLK_LEFT;
    case VK_UP: return SDLK_UP;
    case VK_RIGHT: return SDLK_RIGHT;
    case VK_DOWN: return SDLK_DOWN;
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
                             (int)width, (int)height, SDL_WINDOW_RESIZABLE);
    }
    if (e2r_sdl_backend.window == NULL) {
        fprintf(stderr, "warning: SDL window creation failed: %s\n", SDL_GetError());
        return NULL;
    }
    if (x >= 0 && y >= 0) {
        SDL_SetWindowPosition(e2r_sdl_backend.window, x, y);
    }
    SDL_SetWindowFocusable(e2r_sdl_backend.window, true);
    SDL_RaiseWindow(e2r_sdl_backend.window);
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
    SDL_RaiseWindow(window->window);
}

void E2R_HostPollEvents(E2R_HostWindow *window,
                        E2R_HostMessageCallback message_callback,
                        void *user)
{
    static unsigned input_diag_count;
    static unsigned key_diag_count;
    static unsigned mouse_diag_count;
    static unsigned input_poll_diag_count;
    static unsigned input_thread_diag_count;
    static unsigned window_diag_count;
    SDL_Event event;
    SDL_WindowID window_id;
    int is_main_thread;

    if (window != &e2r_sdl_backend || window->window == NULL) {
        return;
    }
    is_main_thread = SDL_IsMainThread();
    window_id = SDL_GetWindowID(window->window);
    if (e2r_sdl_input_diag_enabled() && input_poll_diag_count < 1u) {
        SDL_Window *keyboard_focus = SDL_GetKeyboardFocus();
        SDL_Window *mouse_focus = SDL_GetMouseFocus();
        SDL_WindowFlags flags = SDL_GetWindowFlags(window->window);
        fprintf(stderr,
                "host input poll: window_id=%u main=%d flags=0x%llx key_focus=%d mouse_focus=%d\n",
                (unsigned)window_id, is_main_thread,
                (unsigned long long)flags, keyboard_focus == window->window,
                mouse_focus == window->window);
        input_poll_diag_count++;
    }
    if (e2r_sdl_input_diag_enabled()) {
        e2r_sdl_log_keyboard_snapshot(window);
    }
    if (!is_main_thread && e2r_sdl_input_diag_enabled() &&
        input_thread_diag_count < 8u) {
        fprintf(stderr, "host input poll: SDL reports non-main thread\n");
        input_thread_diag_count++;
    }
    if (!is_main_thread) {
        return;
    }
    while (SDL_PollEvent(&event)) {
        if (e2r_sdl_input_diag_enabled() && e2r_sdl_should_log_event(event.type) &&
            input_diag_count < 256u) {
            fprintf(stderr, "host input event: type=0x%x name=\"%s\"",
                    (unsigned)event.type, e2r_sdl_event_name(event.type));
            if (event.type == SDL_EVENT_KEY_DOWN || event.type == SDL_EVENT_KEY_UP) {
                fprintf(stderr, " key=0x%x scancode=0x%x down=%u repeat=%u window=%u",
                        (unsigned)event.key.key, (unsigned)event.key.scancode,
                        (unsigned)event.key.down, (unsigned)event.key.repeat,
                        (unsigned)event.key.windowID);
            }
            else if (event.type == SDL_EVENT_MOUSE_MOTION) {
                fprintf(stderr, " x=%.1f y=%.1f xrel=%.1f yrel=%.1f state=0x%x window=%u",
                        event.motion.x, event.motion.y, event.motion.xrel,
                        event.motion.yrel, (unsigned)event.motion.state,
                        (unsigned)event.motion.windowID);
            }
            else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN ||
                     event.type == SDL_EVENT_MOUSE_BUTTON_UP) {
                fprintf(stderr, " button=%u down=%u clicks=%u x=%.1f y=%.1f window=%u",
                        (unsigned)event.button.button, (unsigned)event.button.down,
                        (unsigned)event.button.clicks, event.button.x, event.button.y,
                        (unsigned)event.button.windowID);
            }
            else if (event.type >= SDL_EVENT_WINDOW_FIRST &&
                     event.type <= SDL_EVENT_WINDOW_LAST) {
                fprintf(stderr, " window=%u data1=%d data2=%d",
                        (unsigned)event.window.windowID,
                        (int)event.window.data1, (int)event.window.data2);
            }
            fprintf(stderr, " main=%d\n", is_main_thread);
            input_diag_count++;
        }
        if (event.type == SDL_EVENT_QUIT && message_callback != NULL) {
            message_callback(WM_CLOSE, 0, 0, user);
        }
        else if (event.type == SDL_EVENT_KEY_DOWN && message_callback != NULL) {
            UINT vk = e2r_virtual_key_from_sdl(event.key.key);
            if (e2r_sdl_input_diag_enabled() && key_diag_count < 512u) {
                fprintf(stderr, "host input keydown: sdl=0x%x vk=0x%x window=%u\n",
                        (unsigned)event.key.key, (unsigned)vk,
                        (unsigned)event.key.windowID);
                key_diag_count++;
            }
            if (vk != 0) {
                message_callback(WM_KEYDOWN, vk, 0, user);
            }
        }
        else if (event.type == SDL_EVENT_KEY_UP && message_callback != NULL) {
            UINT vk = e2r_virtual_key_from_sdl(event.key.key);
            if (e2r_sdl_input_diag_enabled() && key_diag_count < 512u) {
                fprintf(stderr, "host input keyup: sdl=0x%x vk=0x%x window=%u\n",
                        (unsigned)event.key.key, (unsigned)vk);
                key_diag_count++;
            }
            if (vk != 0) {
                message_callback(WM_KEYUP, vk, 0, user);
            }
        }
        else if (event.type == SDL_EVENT_TEXT_INPUT) {
            if (e2r_sdl_input_diag_enabled() && key_diag_count < 512u) {
                fprintf(stderr, "host input text: window=%u text=\"%s\"\n",
                        (unsigned)event.text.windowID,
                        event.text.text != NULL ? event.text.text : "");
                key_diag_count++;
            }
        }
        else if (event.type == SDL_EVENT_MOUSE_MOTION && message_callback != NULL &&
                 event.motion.windowID == window_id) {
            message_callback(WM_MOUSEMOVE, (WPARAM)event.motion.state,
                             e2r_pack_mapped_window_point(window, event.motion.x,
                                                          event.motion.y),
                             user);
        }
        else if ((event.type == SDL_EVENT_MOUSE_BUTTON_DOWN ||
                  event.type == SDL_EVENT_MOUSE_BUTTON_UP) &&
                 message_callback != NULL && event.button.windowID == window_id) {
            UINT msg = 0;
            if (event.button.button == 1) {
                msg = event.type == SDL_EVENT_MOUSE_BUTTON_DOWN ?
                    WM_LBUTTONDOWN : WM_LBUTTONUP;
            }
            else if (event.button.button == 2) {
                msg = event.type == SDL_EVENT_MOUSE_BUTTON_DOWN ?
                    WM_MBUTTONDOWN : WM_MBUTTONUP;
            }
            else if (event.button.button == 3) {
                msg = event.type == SDL_EVENT_MOUSE_BUTTON_DOWN ?
                    WM_RBUTTONDOWN : WM_RBUTTONUP;
            }
            if (msg != 0) {
                LPARAM mapped_point =
                    e2r_pack_mapped_window_point(window, event.button.x, event.button.y);
                if (e2r_sdl_input_diag_enabled() && mouse_diag_count < 128u) {
                    fprintf(stderr,
                            "host input mousebutton: msg=0x%x button=%u down=%u x=%.1f y=%.1f\n",
                            (unsigned)msg, (unsigned)event.button.button,
                            (unsigned)event.button.down, event.button.x, event.button.y);
                    mouse_diag_count++;
                }
                if (e2r_sdl_menu_diag_enabled()) {
                    int mapped_x = (int)(int16_t)(mapped_point & 0xffffu);
                    int mapped_y = (int)(int16_t)((mapped_point >> 16) & 0xffffu);
                    fprintf(stderr,
                            "menu click: phase=sdl msg=0x%x button=%u down=%u "
                            "raw=%.1f,%.1f mapped=%d,%d present_rect=%d,%d %dx%d\n",
                            (unsigned)msg, (unsigned)event.button.button,
                            (unsigned)event.button.down, event.button.x, event.button.y,
                            mapped_x, mapped_y, window->presentation_rect.x,
                            window->presentation_rect.y, window->presentation_rect.w,
                            window->presentation_rect.h);
                }
                message_callback(msg, 0, mapped_point, user);
            }
        }
        else if (event.type >= SDL_EVENT_WINDOW_FIRST &&
                 event.type <= SDL_EVENT_WINDOW_LAST &&
                 message_callback != NULL && event.window.windowID == window_id) {
            if (e2r_sdl_input_diag_enabled() &&
                e2r_sdl_should_log_window_message(event.type) &&
                window_diag_count < 128u) {
                fprintf(stderr, "host input windowmsg: type=0x%x name=\"%s\" data=%d,%d\n",
                        (unsigned)event.type, e2r_sdl_event_name(event.type),
                        (int)event.window.data1, (int)event.window.data2);
                window_diag_count++;
            }
            if (event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED) {
                message_callback(WM_CLOSE, 0, 0, user);
            }
            else if (event.type == SDL_EVENT_WINDOW_RESIZED ||
                     event.type == SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED) {
                message_callback(WM_SIZE, 0,
                                 (LPARAM)(((unsigned int)event.window.data1 & 0xffffu) |
                                          (((unsigned int)event.window.data2 & 0xffffu)
                                           << 16)),
                                 user);
            }
            else if (event.type == SDL_EVENT_WINDOW_MOVED) {
                message_callback(WM_MOVE, 0,
                                 (LPARAM)(((unsigned int)event.window.data1 & 0xffffu) |
                                          (((unsigned int)event.window.data2 & 0xffffu)
                                           << 16)),
                                 user);
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
                            unsigned width, unsigned height, unsigned pitch,
                            const uint32_t *palette_rgb)
{
    static unsigned rect_diag_count;
    SDL_Surface *window_surface;
    SDL_Rect dst_rect;
    Uint32 colors[256];
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
        if (palette_rgb != NULL) {
            uint32_t color = palette_rgb[i];
            colors[i] = SDL_MapSurfaceRGBA(window->present_surface,
                                           (Uint8)((color >> 16) & 0xffu),
                                           (Uint8)((color >> 8) & 0xffu),
                                           (Uint8)(color & 0xffu), 255);
        }
        else {
            colors[i] = SDL_MapSurfaceRGBA(window->present_surface,
                                           (Uint8)i, (Uint8)i, (Uint8)i, 255);
        }
    }
    for (y = 0; y < height; y++) {
        const unsigned char *src = pixels + ((size_t)y * pitch);
        Uint32 *dst = (Uint32 *)((unsigned char *)window->present_surface->pixels +
                                 ((size_t)y * (size_t)window->present_surface->pitch));
        unsigned x;
        for (x = 0; x < width; x++) {
            dst[x] = colors[src[x]];
        }
    }
    SDL_UnlockSurface(window->present_surface);

    window_surface = SDL_GetWindowSurface(window->window);
    if (window_surface == NULL) {
        fprintf(stderr, "warning: SDL window surface unavailable: %s\n", SDL_GetError());
        return 0;
    }
    dst_rect = e2r_sdl_aspect_fit_rect(window_surface->w, window_surface->h,
                                       width, height);
    window->presentation_rect = dst_rect;
    window->has_presentation_rect = 1;
    if (!SDL_FillSurfaceRect(window_surface, NULL,
                             SDL_MapSurfaceRGBA(window_surface, 0, 0, 0, 255))) {
        fprintf(stderr, "warning: SDL presentation clear failed: %s\n", SDL_GetError());
        return 0;
    }
    if (e2r_sdl_present_diag_enabled() && rect_diag_count < 8u) {
        fprintf(stderr,
                "host backend present rect: src=%ux%u window=%dx%d dst=%d,%d %dx%d\n",
                width, height, window_surface->w, window_surface->h,
                dst_rect.x, dst_rect.y, dst_rect.w, dst_rect.h);
        rect_diag_count++;
    }
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
                        E2R_HostMessageCallback message_callback,
                        void *user)
{
    (void)window; (void)message_callback; (void)user;
}
int E2R_HostPushSyntheticKeyDown(E2R_HostWindow *window, UINT vk)
{
    (void)window; (void)vk;
    return 0;
}
int E2R_HostPresentIndexed8(E2R_HostWindow *window, const unsigned char *pixels,
                            unsigned width, unsigned height, unsigned pitch,
                            const uint32_t *palette_rgb)
{
    (void)window; (void)pixels; (void)width; (void)height; (void)pitch;
    (void)palette_rgb;
    return 0;
}
#endif
