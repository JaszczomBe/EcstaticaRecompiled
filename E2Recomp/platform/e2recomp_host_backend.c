#include "e2recomp_host_backend.h"

#ifndef _WIN32
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

typedef struct E2R_XDisplay E2R_XDisplay;
typedef unsigned long E2R_XWindow;

typedef struct E2R_XKeyEvent {
    int type;
    unsigned long serial;
    int send_event;
    E2R_XDisplay *display;
    E2R_XWindow window;
    E2R_XWindow root;
    E2R_XWindow subwindow;
    unsigned long time;
    int x;
    int y;
    int x_root;
    int y_root;
    unsigned int state;
    unsigned int keycode;
    int same_screen;
} E2R_XKeyEvent;

typedef union E2R_XEvent {
    int type;
    E2R_XKeyEvent xkey;
    long pad[24];
} E2R_XEvent;

typedef struct E2R_X11_API {
    void *lib;
    E2R_XDisplay *(*XOpenDisplay)(const char *);
    int (*XDefaultScreen)(E2R_XDisplay *);
    E2R_XWindow (*XRootWindow)(E2R_XDisplay *, int);
    unsigned long (*XBlackPixel)(E2R_XDisplay *, int);
    unsigned long (*XWhitePixel)(E2R_XDisplay *, int);
    E2R_XWindow (*XCreateSimpleWindow)(E2R_XDisplay *, E2R_XWindow, int, int, unsigned int, unsigned int, unsigned int, unsigned long, unsigned long);
    int (*XStoreName)(E2R_XDisplay *, E2R_XWindow, const char *);
    int (*XMapWindow)(E2R_XDisplay *, E2R_XWindow);
    int (*XDestroyWindow)(E2R_XDisplay *, E2R_XWindow);
    int (*XFlush)(E2R_XDisplay *);
    int (*XCloseDisplay)(E2R_XDisplay *);
    int (*XSelectInput)(E2R_XDisplay *, E2R_XWindow, long);
    int (*XPending)(E2R_XDisplay *);
    int (*XNextEvent)(E2R_XDisplay *, E2R_XEvent *);
    unsigned long (*XLookupKeysym)(E2R_XKeyEvent *, int);
} E2R_X11_API;

struct E2R_HostWindow {
    E2R_XDisplay *display;
    E2R_XWindow window;
};

static E2R_X11_API e2r_x11;
static E2R_HostWindow e2r_x11_window;
static int e2r_x11_load_attempted;
static int e2r_x11_warned;

#define E2R_X11_KEY_PRESS 2
#define E2R_X11_KEY_PRESS_MASK (1L << 0)

static void *e2r_x11_symbol(const char *name)
{
    return e2r_x11.lib ? dlsym(e2r_x11.lib, name) : NULL;
}

static int e2r_load_x11(void)
{
    if (e2r_x11_load_attempted) return e2r_x11.lib != NULL;
    e2r_x11_load_attempted = 1;

    e2r_x11.lib = dlopen("libX11.so.6", RTLD_LAZY);
    if (!e2r_x11.lib) return 0;

    e2r_x11.XOpenDisplay = (E2R_XDisplay *(*)(const char *))e2r_x11_symbol("XOpenDisplay");
    e2r_x11.XDefaultScreen = (int (*)(E2R_XDisplay *))e2r_x11_symbol("XDefaultScreen");
    e2r_x11.XRootWindow = (E2R_XWindow (*)(E2R_XDisplay *, int))e2r_x11_symbol("XRootWindow");
    e2r_x11.XBlackPixel = (unsigned long (*)(E2R_XDisplay *, int))e2r_x11_symbol("XBlackPixel");
    e2r_x11.XWhitePixel = (unsigned long (*)(E2R_XDisplay *, int))e2r_x11_symbol("XWhitePixel");
    e2r_x11.XCreateSimpleWindow = (E2R_XWindow (*)(E2R_XDisplay *, E2R_XWindow, int, int, unsigned int, unsigned int, unsigned int, unsigned long, unsigned long))e2r_x11_symbol("XCreateSimpleWindow");
    e2r_x11.XStoreName = (int (*)(E2R_XDisplay *, E2R_XWindow, const char *))e2r_x11_symbol("XStoreName");
    e2r_x11.XMapWindow = (int (*)(E2R_XDisplay *, E2R_XWindow))e2r_x11_symbol("XMapWindow");
    e2r_x11.XDestroyWindow = (int (*)(E2R_XDisplay *, E2R_XWindow))e2r_x11_symbol("XDestroyWindow");
    e2r_x11.XFlush = (int (*)(E2R_XDisplay *))e2r_x11_symbol("XFlush");
    e2r_x11.XCloseDisplay = (int (*)(E2R_XDisplay *))e2r_x11_symbol("XCloseDisplay");
    e2r_x11.XSelectInput = (int (*)(E2R_XDisplay *, E2R_XWindow, long))e2r_x11_symbol("XSelectInput");
    e2r_x11.XPending = (int (*)(E2R_XDisplay *))e2r_x11_symbol("XPending");
    e2r_x11.XNextEvent = (int (*)(E2R_XDisplay *, E2R_XEvent *))e2r_x11_symbol("XNextEvent");
    e2r_x11.XLookupKeysym = (unsigned long (*)(E2R_XKeyEvent *, int))e2r_x11_symbol("XLookupKeysym");

    if (!e2r_x11.XOpenDisplay || !e2r_x11.XDefaultScreen || !e2r_x11.XRootWindow ||
        !e2r_x11.XBlackPixel || !e2r_x11.XWhitePixel || !e2r_x11.XCreateSimpleWindow ||
        !e2r_x11.XStoreName || !e2r_x11.XMapWindow || !e2r_x11.XDestroyWindow ||
        !e2r_x11.XFlush || !e2r_x11.XCloseDisplay || !e2r_x11.XSelectInput ||
        !e2r_x11.XPending || !e2r_x11.XNextEvent || !e2r_x11.XLookupKeysym) {
        dlclose(e2r_x11.lib);
        memset(&e2r_x11, 0, sizeof(e2r_x11));
        return 0;
    }

    return 1;
}

static UINT e2r_virtual_key_from_keysym(unsigned long keysym)
{
    if (keysym >= 'a' && keysym <= 'z') {
        keysym -= 'a' - 'A';
    }
    if (keysym >= 0xffb0u && keysym <= 0xffb9u) {
        return 0x60u + (UINT)(keysym - 0xffb0u);
    }
    if (keysym >= 0xffbeu && keysym <= 0xffc9u) {
        return 0x70u + (UINT)(keysym - 0xffbeu);
    }
    switch (keysym) {
    case 0xff1b: return VK_ESCAPE;
    case 0xff0d: return VK_RETURN;
    case 0x20: return VK_SPACE;
    case 0xffe3:
    case 0xffe4: return 0x11;
    case 0xff51: return 0x64;
    case 0xff52: return 0x68;
    case 0xff53: return 0x66;
    case 0xff54: return 0x62;
    default:
        if (keysym >= 'A' && keysym <= 'Z') {
            return (UINT)keysym;
        }
        return 0;
    }
}

static void e2r_warn_window_unavailable(void)
{
    if (!e2r_x11_warned) {
        fprintf(stderr, "warning: X11 window unavailable; continuing with headless HWND stub\n");
        e2r_x11_warned = 1;
    }
}

E2R_HostWindow *E2R_HostCreateWindow(const char *title, int x, int y,
                                     unsigned width, unsigned height)
{
    int screen;

    if (!e2r_load_x11()) {
        e2r_warn_window_unavailable();
        return NULL;
    }

    if (!e2r_x11_window.display) {
        e2r_x11_window.display = e2r_x11.XOpenDisplay(NULL);
        if (!e2r_x11_window.display) {
            e2r_warn_window_unavailable();
            return NULL;
        }
    }

    screen = e2r_x11.XDefaultScreen(e2r_x11_window.display);
    if (e2r_x11_window.window == 0) {
        E2R_XWindow root = e2r_x11.XRootWindow(e2r_x11_window.display, screen);
        unsigned long black = e2r_x11.XBlackPixel(e2r_x11_window.display, screen);
        unsigned long white = e2r_x11.XWhitePixel(e2r_x11_window.display, screen);
        e2r_x11_window.window =
            e2r_x11.XCreateSimpleWindow(e2r_x11_window.display, root, x, y,
                                        width, height, 1, black, white);
    }
    if (e2r_x11_window.window == 0) {
        return NULL;
    }

    e2r_x11.XSelectInput(e2r_x11_window.display, e2r_x11_window.window,
                         E2R_X11_KEY_PRESS_MASK);
    e2r_x11.XStoreName(e2r_x11_window.display, e2r_x11_window.window,
                       title ? title : "Ecstatica II");
    e2r_x11.XMapWindow(e2r_x11_window.display, e2r_x11_window.window);
    e2r_x11.XFlush(e2r_x11_window.display);
    return &e2r_x11_window;
}

void E2R_HostDestroyWindow(E2R_HostWindow *window)
{
    if (window != &e2r_x11_window || !window->display || !window->window) {
        return;
    }
    e2r_x11.XDestroyWindow(window->display, window->window);
    e2r_x11.XFlush(window->display);
    window->window = 0;
}

void E2R_HostShowWindow(E2R_HostWindow *window)
{
    if (window != &e2r_x11_window || !window->display || !window->window) {
        return;
    }
    e2r_x11.XMapWindow(window->display, window->window);
    e2r_x11.XFlush(window->display);
}

void E2R_HostPollEvents(E2R_HostWindow *window,
                        E2R_HostMessageCallback message_callback,
                        void *user)
{
    if (window != &e2r_x11_window || !window->display || !window->window ||
        !e2r_x11.XPending || !e2r_x11.XNextEvent || !e2r_x11.XLookupKeysym) {
        return;
    }

    while (e2r_x11.XPending(window->display) > 0) {
        E2R_XEvent event;
        e2r_x11.XNextEvent(window->display, &event);
        if (event.type == E2R_X11_KEY_PRESS && message_callback != NULL) {
            UINT vk = e2r_virtual_key_from_keysym(e2r_x11.XLookupKeysym(&event.xkey, 0));
            if (vk != 0) {
                message_callback(WM_KEYDOWN, vk, 0, user);
            }
        }
    }
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
