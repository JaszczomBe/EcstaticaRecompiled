#include "e2recomp_win32_compat.h"

#include <stdarg.h>
#include <errno.h>
#include <dirent.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <time.h>
#include <unistd.h>
#ifndef _WIN32
#include <dlfcn.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/stat.h>
#ifndef MAP_ANONYMOUS
#define MAP_ANONYMOUS MAP_ANON
#endif

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif
#endif

static E2R_HANDLE__ e2r_module = {0, 0};
static E2R_HANDLE__ e2r_window = {0, 0};
static E2R_HANDLE__ e2r_handle = {0, 0};
static DWORD e2r_last_error;
static void *e2r_tls[64];
static DWORD e2r_next_tls;
static WNDPROC e2r_window_proc;

#define E2R_MESSAGE_QUEUE_CAPACITY 32

static MSG e2r_message_queue[E2R_MESSAGE_QUEUE_CAPACITY];
static unsigned e2r_message_head;
static unsigned e2r_message_tail;

#ifndef _WIN32
static pthread_mutex_t e2r_message_mutex = PTHREAD_MUTEX_INITIALIZER;
#endif

static void e2r_message_lock(void)
{
#ifndef _WIN32
    pthread_mutex_lock(&e2r_message_mutex);
#endif
}

static void e2r_message_unlock(void)
{
#ifndef _WIN32
    pthread_mutex_unlock(&e2r_message_mutex);
#endif
}

static BOOL e2r_message_matches(const MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter)
{
    if (hwnd != NULL && msg->hwnd != hwnd) {
        return FALSE;
    }
    if ((min_filter != 0 || max_filter != 0) &&
        (msg->message < min_filter || msg->message > max_filter)) {
        return FALSE;
    }
    return TRUE;
}

static BOOL e2r_pop_message(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter, BOOL remove)
{
    BOOL found = FALSE;

    e2r_message_lock();
    if (e2r_message_head != e2r_message_tail &&
        e2r_message_matches(&e2r_message_queue[e2r_message_head], hwnd, min_filter, max_filter)) {
        if (msg != NULL) {
            *msg = e2r_message_queue[e2r_message_head];
        }
        if (remove) {
            e2r_message_head = (e2r_message_head + 1u) % E2R_MESSAGE_QUEUE_CAPACITY;
        }
        found = TRUE;
    }
    e2r_message_unlock();
    return found;
}

static BOOL e2r_push_message(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
    unsigned next_tail;
    BOOL queued = FALSE;

    e2r_message_lock();
    next_tail = (e2r_message_tail + 1u) % E2R_MESSAGE_QUEUE_CAPACITY;
    if (next_tail != e2r_message_head) {
        MSG *entry = &e2r_message_queue[e2r_message_tail];
        memset(entry, 0, sizeof(*entry));
        entry->hwnd = hwnd;
        entry->message = msg;
        entry->wParam = wparam;
        entry->lParam = lparam;
        e2r_message_tail = next_tail;
        queued = TRUE;
    }
    e2r_message_unlock();
    return queued;
}

#ifndef _WIN32
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

typedef struct E2R_X11_Window {
    E2R_XDisplay *display;
    E2R_XWindow window;
} E2R_X11_Window;

static E2R_X11_API e2r_x11;
static E2R_X11_Window e2r_x11_window;
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

static void e2r_poll_host_events(void)
{
    if (!e2r_x11_window.display || !e2r_x11_window.window || !e2r_x11.XPending ||
        !e2r_x11.XNextEvent || !e2r_x11.XLookupKeysym) {
        return;
    }

    while (e2r_x11.XPending(e2r_x11_window.display) > 0) {
        E2R_XEvent event;
        e2r_x11.XNextEvent(e2r_x11_window.display, &event);
        if (event.type == E2R_X11_KEY_PRESS) {
            UINT vk = e2r_virtual_key_from_keysym(e2r_x11.XLookupKeysym(&event.xkey, 0));
            if (vk != 0) {
                e2r_push_message(&e2r_window, WM_KEYDOWN, vk, 0);
            }
        }
    }
}

static void e2r_warn_window_unavailable(void)
{
    if (!e2r_x11_warned) {
        fprintf(stderr, "warning: X11 window unavailable; continuing with headless HWND stub\n");
        e2r_x11_warned = 1;
    }
}
#endif

void E2R_MapLegacyAddressSpace(void)
{
#ifndef _WIN32
    static int initialized;
    int flags = MAP_PRIVATE | MAP_ANONYMOUS;
    void *mapped;

    if (initialized) return;
    initialized = 1;

#ifdef MAP_FIXED_NOREPLACE
    flags |= MAP_FIXED_NOREPLACE;
#else
    flags |= MAP_FIXED;
#endif

    mapped = mmap((void *)0x000a0000u, 0x00060000u, PROT_READ | PROT_WRITE, flags, -1, 0);
    if (mapped == MAP_FAILED) {
        fprintf(stderr,
                "warning: could not map legacy Ecstatica VGA range 0x000a0000..0x00100000: %s\n",
                strerror(errno));
    }

    mapped = mmap((void *)0x00400000u, 0x00700000u, PROT_READ | PROT_WRITE, flags, -1, 0);
    if (mapped == MAP_FAILED) {
        fprintf(stderr,
                "warning: could not map legacy Ecstatica address range 0x%08lx..0x%08lx: %s\n",
                (unsigned long)0x00400000u,
                (unsigned long)0x00b00000u,
                strerror(errno));
    }
#endif
}

static HANDLE e2r_alloc_handle(void *ptr)
{
    E2R_HANDLE__ *handle = (E2R_HANDLE__ *)calloc(1, sizeof(*handle));
    if (!handle) return NULL;
    handle->ptr = ptr;
    return handle;
}

static void e2r_normalize_path(char *dst, size_t dst_size, const char *src)
{
    size_t i;
    if (dst_size == 0) return;
    if (!src) src = "";
    for (i = 0; i + 1 < dst_size && src[i]; i++) {
        dst[i] = src[i] == '\\' ? '/' : src[i];
    }
    dst[i] = '\0';
}

static int e2r_append_path_component(char *path, size_t path_size, const char *component)
{
    size_t len = strlen(path);
    size_t comp_len = strlen(component);
    int need_slash = len > 0 && path[len - 1] != '/';
    if (len + (need_slash ? 1 : 0) + comp_len + 1 > path_size) return 0;
    if (need_slash) path[len++] = '/';
    memcpy(path + len, component, comp_len + 1);
    return 1;
}

static int e2r_resolve_case_path(const char *input, char *resolved, size_t resolved_size)
{
    char normalized[PATH_MAX];
    char current[PATH_MAX];
    char *cursor;
    char *component;

    e2r_normalize_path(normalized, sizeof(normalized), input);
    if (normalized[0] == '\0') return 0;

    if (normalized[0] == '/') {
        strcpy(current, "/");
        cursor = normalized + 1;
    } else {
        strcpy(current, ".");
        cursor = normalized;
    }

    component = cursor;
    while (1) {
        char saved;
        char matched[PATH_MAX];
        DIR *dir;
        struct dirent *entry;
        int found = 0;

        while (*component == '/') component++;
        if (*component == '\0') break;

        cursor = component;
        while (*cursor && *cursor != '/') cursor++;
        saved = *cursor;
        *cursor = '\0';

        dir = opendir(current);
        if (!dir) return 0;
        while ((entry = readdir(dir)) != NULL) {
            if (strcasecmp(entry->d_name, component) == 0) {
                e2r_normalize_path(matched, sizeof(matched), entry->d_name);
                found = 1;
                break;
            }
        }
        closedir(dir);
        if (!found || !e2r_append_path_component(current, sizeof(current), matched)) return 0;

        *cursor = saved;
        component = cursor;
        if (saved == '\0') break;
    }

    if (strlen(current) + 1 > resolved_size) return 0;
    strcpy(resolved, current);
    return 1;
}

HANDLE CreateFileA(LPCSTR name, DWORD access, DWORD share, LPVOID security,
                   DWORD creation, DWORD flags, HANDLE template_file)
{
    char normalized[PATH_MAX];
    char resolved[PATH_MAX];
    const char *open_name;
    FILE *file;
    (void)share;
    (void)security;
    (void)creation;
    (void)flags;
    (void)template_file;
    e2r_normalize_path(normalized, sizeof(normalized), name);
    open_name = normalized;
    file = fopen(open_name, (access & GENERIC_WRITE) ? "wb+" : "rb");
    if (!file && (access & GENERIC_WRITE) == 0 && e2r_resolve_case_path(normalized, resolved, sizeof(resolved))) {
        open_name = resolved;
        file = fopen(open_name, "rb");
    }
    if (!file) return INVALID_HANDLE_VALUE;
    return e2r_alloc_handle(file);
}

BOOL ReadFile(HANDLE file, LPVOID buffer, DWORD bytes_to_read, DWORD *bytes_read,
              LPOVERLAPPED overlapped)
{
    (void)overlapped;
    if (bytes_read) *bytes_read = 0;
    if (!file || file == INVALID_HANDLE_VALUE || !file->ptr) return FALSE;
    size_t n = fread(buffer, 1, bytes_to_read, (FILE *)file->ptr);
    if (bytes_read) *bytes_read = (DWORD)n;
    return TRUE;
}

BOOL WriteFile(HANDLE file, LPCVOID buffer, DWORD bytes_to_write,
               DWORD *bytes_written, LPVOID overlapped)
{
    (void)overlapped;
    if (bytes_written) *bytes_written = 0;
    if (!file || file == INVALID_HANDLE_VALUE || !file->ptr) return FALSE;
    size_t n = fwrite(buffer, 1, bytes_to_write, (FILE *)file->ptr);
    if (bytes_written) *bytes_written = (DWORD)n;
    return n == bytes_to_write;
}

BOOL CloseHandle(HANDLE file)
{
    if (!file || file == INVALID_HANDLE_VALUE) return FALSE;
    if (file->ptr) fclose((FILE *)file->ptr);
    free(file);
    return TRUE;
}

int wsprintfA(LPSTR buffer, LPCSTR format, ...)
{
    va_list ap;
    va_start(ap, format);
    int result = vsprintf(buffer, format, ap);
    va_end(ap);
    return result;
}

int lstrlenA(LPCSTR value) { return value ? (int)strlen(value) : 0; }
LPSTR lstrcpyA(LPSTR dst, LPCSTR src) { return strcpy(dst, src ? src : ""); }
LPSTR lstrcatA(LPSTR dst, LPCSTR src) { return strcat(dst, src ? src : ""); }

HMODULE GetModuleHandleA(LPCSTR name) { (void)name; return &e2r_module; }
HMODULE LoadLibraryA(LPCSTR name) { (void)name; return &e2r_module; }
void *GetProcAddress(HMODULE module, LPCSTR name) { (void)module; (void)name; return NULL; }

DWORD GetVersion(void) { return 0x00000004u; }
DWORD GetLastError(void) { return e2r_last_error; }
DWORD GetFileType(HANDLE file) { (void)file; return 1; }
DWORD GetCurrentProcessId(void) { return (DWORD)getpid(); }
DWORD GetCurrentThreadId(void) { return 1; }
DWORD GetTickCount(void) { return (DWORD)(time(NULL) * 1000u); }
DWORD timeGetTime(void) { return GetTickCount(); }

LPVOID VirtualAlloc(LPVOID address, size_t size, DWORD allocation_type, DWORD protect)
{
    (void)address;
    (void)allocation_type;
    (void)protect;
    return calloc(1, size);
}

BOOL VirtualProtect(LPVOID address, size_t size, DWORD new_protect, DWORD *old_protect)
{
    (void)address;
    (void)size;
    (void)new_protect;
    if (old_protect) *old_protect = PAGE_READWRITE;
    return TRUE;
}

void *SetUnhandledExceptionFilter(void *filter) { return filter; }
static BOOL e2r_is_bad_memory_range(const void *ptr, UINT_PTR size, char permission)
{
    uintptr_t start = (uintptr_t)ptr;
    uintptr_t end;
    uintptr_t cursor;
#ifndef _WIN32
    FILE *maps;
    char line[256];
#endif

    if (size == 0) return FALSE;
    if (ptr == NULL || start < 0x10000u) return TRUE;
    end = start + (uintptr_t)size;
    if (end <= start) return TRUE;

#ifndef _WIN32
    maps = fopen("/proc/self/maps", "r");
    if (!maps) return TRUE;

    cursor = start;
    while (fgets(line, sizeof(line), maps)) {
        unsigned long lo;
        unsigned long hi;
        char perms[5];

        if (sscanf(line, "%lx-%lx %4s", &lo, &hi, perms) != 3) continue;
        if ((uintptr_t)hi <= cursor) continue;
        if ((uintptr_t)lo > cursor) break;

        if ((permission == 'r' && perms[0] != 'r') ||
            (permission == 'w' && perms[1] != 'w')) {
            fclose(maps);
            return TRUE;
        }

        cursor = (uintptr_t)hi;
        if (cursor >= end) {
            fclose(maps);
            return FALSE;
        }
    }

    fclose(maps);
    return TRUE;
#endif

    return FALSE;
}

BOOL IsBadReadPtr(const void *ptr, UINT_PTR size)
{
    return e2r_is_bad_memory_range(ptr, size, 'r');
}

BOOL E2R_IsBadWritePtr(const void *ptr, UINT_PTR size)
{
    return e2r_is_bad_memory_range(ptr, size, 'w');
}

BOOL IsWindow(HWND hwnd) { return hwnd != NULL; }
BOOL DestroyWindow(HWND hwnd)
{
#ifndef _WIN32
    if (hwnd == &e2r_window && e2r_x11_window.display && e2r_x11_window.window) {
        e2r_x11.XDestroyWindow(e2r_x11_window.display, e2r_x11_window.window);
        e2r_x11.XFlush(e2r_x11_window.display);
        e2r_x11_window.window = 0;
        hwnd->ptr = NULL;
    }
#endif
    (void)hwnd;
    return TRUE;
}
BOOL ShowWindow(HWND hwnd, int cmd_show)
{
#ifndef _WIN32
    if (hwnd == &e2r_window && e2r_x11_window.display && e2r_x11_window.window && cmd_show != 0) {
        e2r_x11.XMapWindow(e2r_x11_window.display, e2r_x11_window.window);
        e2r_x11.XFlush(e2r_x11_window.display);
    }
#endif
    (void)hwnd; (void)cmd_show;
    return TRUE;
}
BOOL UpdateWindow(HWND hwnd) { (void)hwnd; return TRUE; }
HWND SetFocus(HWND hwnd) { return hwnd; }
int ShowCursor(BOOL show) { (void)show; return 0; }
BOOL GetCursorPos(POINT *point) { if (point) point->x = point->y = 0; return TRUE; }
BOOL PeekMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter, UINT remove)
{
#ifndef _WIN32
    e2r_poll_host_events();
#endif
    return e2r_pop_message(msg, hwnd, min_filter, max_filter, (remove & PM_REMOVE) != 0);
}
BOOL GetMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter)
{
#ifndef _WIN32
    e2r_poll_host_events();
#endif
    if (!e2r_pop_message(msg, hwnd, min_filter, max_filter, TRUE)) {
        return FALSE;
    }
    return msg == NULL || msg->message != WM_QUIT;
}
BOOL TranslateMessage(const MSG *msg) { (void)msg; return TRUE; }
LRESULT DispatchMessageA(const MSG *msg)
{
    if (msg == NULL) {
        return 0;
    }
    if (e2r_window_proc != NULL && msg->message != WM_QUIT) {
        return e2r_window_proc(msg->hwnd, msg->message, msg->wParam, msg->lParam);
    }
    return DefWindowProcA(msg->hwnd, msg->message, msg->wParam, msg->lParam);
}
void WaitMessage(void) {}
void Sleep(DWORD milliseconds) { usleep(milliseconds * 1000u); }
void PostQuitMessage(int exit_code)
{
    e2r_push_message(NULL, WM_QUIT, (WPARAM)exit_code, 0);
}
BOOL PostMessageA(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
    return e2r_push_message(hwnd, msg, wparam, lparam);
}
LRESULT SendMessageA(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
    (void)hwnd; (void)msg; (void)wparam; (void)lparam;
    return 0;
}
LRESULT DefWindowProcA(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
    (void)hwnd; (void)msg; (void)wparam; (void)lparam;
    return 0;
}
HWND CreateWindowExA(DWORD ex_style, LPCSTR class_name, LPCSTR window_name,
                     DWORD style, int x, int y, int width, int height,
                     HWND parent, HMENU menu, HINSTANCE instance, LPVOID param)
{
    (void)ex_style; (void)class_name; (void)style; (void)menu; (void)instance; (void)param;
#ifndef _WIN32
    if (!parent) {
        int screen;
        unsigned int w = width > 0 ? (unsigned int)width : 640u;
        unsigned int h = height > 0 ? (unsigned int)height : 480u;

        if (!e2r_load_x11()) {
            e2r_warn_window_unavailable();
            return &e2r_window;
        }

        if (!e2r_x11_window.display) {
            e2r_x11_window.display = e2r_x11.XOpenDisplay(NULL);
            if (!e2r_x11_window.display) {
                e2r_warn_window_unavailable();
                return &e2r_window;
            }
        }

        screen = e2r_x11.XDefaultScreen(e2r_x11_window.display);
        if (e2r_x11_window.window == 0) {
            E2R_XWindow root = e2r_x11.XRootWindow(e2r_x11_window.display, screen);
            unsigned long black = e2r_x11.XBlackPixel(e2r_x11_window.display, screen);
            unsigned long white = e2r_x11.XWhitePixel(e2r_x11_window.display, screen);
            e2r_x11_window.window =
                e2r_x11.XCreateSimpleWindow(e2r_x11_window.display, root, x, y, w, h, 1, black, white);
        }
        if (e2r_x11_window.window != 0) {
            e2r_x11.XSelectInput(e2r_x11_window.display, e2r_x11_window.window, E2R_X11_KEY_PRESS_MASK);
            e2r_x11.XStoreName(e2r_x11_window.display, e2r_x11_window.window,
                               window_name ? window_name : "Ecstatica II");
            e2r_x11.XMapWindow(e2r_x11_window.display, e2r_x11_window.window);
            e2r_x11.XFlush(e2r_x11_window.display);
            e2r_window.ptr = &e2r_x11_window;
        }
    }
#else
    (void)window_name; (void)x; (void)y; (void)width; (void)height; (void)parent;
#endif
    return &e2r_window;
}
INT_PTR DialogBoxParamA(HINSTANCE inst, LPCSTR tmpl, HWND parent, DLGPROC proc,
                        LPARAM param)
{
    (void)inst; (void)tmpl; (void)parent; (void)proc; (void)param;
    return 0;
}
BOOL EndDialog(HWND dialog, INT_PTR result) { (void)dialog; (void)result; return TRUE; }
HWND GetDlgItem(HWND dialog, int id) { (void)dialog; (void)id; return &e2r_window; }
int MessageBoxA(HWND hwnd, LPCSTR text, LPCSTR caption, UINT type)
{
    (void)hwnd; (void)type;
    fprintf(stderr, "%s: %s\n", caption ? caption : "MessageBox", text ? text : "");
    return 0;
}
HICON LoadIconA(HINSTANCE instance, LPCSTR icon_name) { (void)instance; (void)icon_name; return (HICON)&e2r_handle; }
HCURSOR LoadCursorA(HINSTANCE instance, LPCSTR cursor_name) { (void)instance; (void)cursor_name; return (HCURSOR)&e2r_handle; }
HGDIOBJ GetStockObject(int object) { (void)object; return (HGDIOBJ)&e2r_handle; }
ATOM RegisterClassA(const WNDCLASSA *wnd_class)
{
    e2r_window_proc = wnd_class != NULL ? wnd_class->lpfnWndProc : NULL;
    return 1;
}
BOOL UnregisterClassA(LPCSTR class_name, HINSTANCE instance) { (void)class_name; (void)instance; return TRUE; }
int GetSystemMetrics(int index) { (void)index; return 640; }
HMENU GetMenu(HWND hwnd) { (void)hwnd; return (HMENU)&e2r_handle; }
DWORD CheckMenuItem(HMENU menu, UINT item, UINT check) { (void)menu; (void)item; return check; }
HDC GetDC(HWND hwnd) { (void)hwnd; return (HDC)&e2r_handle; }
int ReleaseDC(HWND hwnd, HDC dc) { (void)hwnd; (void)dc; return 1; }
BOOL GetTextExtentPoint32A(HDC dc, LPCSTR text, int count, SIZE *size)
{
    (void)dc;
    if (size) {
        size->cx = (LONG)((count >= 0 ? count : lstrlenA(text)) * 8);
        size->cy = 16;
    }
    return TRUE;
}
BOOL SetWindowTextA(HWND hwnd, LPCSTR text) { (void)hwnd; (void)text; return TRUE; }

UINT_PTR SetTimer(HWND hwnd, UINT_PTR id_event, UINT elapse, TIMERPROC timer_func)
{
    (void)hwnd; (void)elapse; (void)timer_func;
    return id_event ? id_event : 1;
}
BOOL KillTimer(HWND hwnd, UINT_PTR id_event) { (void)hwnd; (void)id_event; return TRUE; }

HGLOBAL GlobalAlloc(UINT flags, size_t bytes)
{
    (void)flags;
    return (HGLOBAL)calloc(1, bytes);
}
LPVOID GlobalLock(HGLOBAL mem) { return mem; }
BOOL GlobalUnlock(HGLOBAL mem) { (void)mem; return TRUE; }
HGLOBAL GlobalHandle(LPCVOID mem) { return (HGLOBAL)mem; }
HGLOBAL GlobalFree(HGLOBAL mem)
{
    if (!mem) return NULL;
    free(mem);
    return NULL;
}
HLOCAL LocalAlloc(UINT flags, size_t bytes) { return (HLOCAL)GlobalAlloc(flags, bytes); }
HLOCAL LocalFree(HLOCAL mem) { return (HLOCAL)GlobalFree((HGLOBAL)mem); }

BOOL GetOpenFileNameA(LPOPENFILENAMEA open_file_name) { (void)open_file_name; return FALSE; }
BOOL WriteProfileStringA(LPCSTR app, LPCSTR key, LPCSTR value)
{
    (void)app; (void)key; (void)value;
    return TRUE;
}

DWORD SetFilePointer(HANDLE file, LONG distance, PLONG high_distance, DWORD method)
{
    (void)high_distance;
    if (!file || !file->ptr) return (DWORD)-1;
    int whence = method == 1 ? SEEK_CUR : method == 2 ? SEEK_END : SEEK_SET;
    if (fseek((FILE *)file->ptr, distance, whence) != 0) return (DWORD)-1;
    return (DWORD)ftell((FILE *)file->ptr);
}
BOOL DeleteFileA(LPCSTR path) { return remove(path) == 0; }
BOOL RemoveDirectoryA(LPCSTR path) { return rmdir(path) == 0; }
BOOL CreateDirectoryA(LPCSTR path, LPSECURITY_ATTRIBUTES attrs)
{
    (void)attrs;
    return mkdir(path, 0777) == 0;
}
BOOL SetCurrentDirectoryA(LPCSTR path) { return chdir(path) == 0; }
DWORD GetCurrentDirectoryA(DWORD size, LPSTR buffer)
{
    if (!buffer || !getcwd(buffer, size)) return 0;
    return (DWORD)strlen(buffer);
}
DWORD GetFullPathNameA(LPCSTR path, DWORD size, LPSTR buffer, LPSTR *file_part)
{
    if (!buffer || !path) return 0;
    char *resolved = realpath(path, NULL);
    const char *value = resolved ? resolved : path;
    snprintf(buffer, size, "%s", value);
    if (file_part) *file_part = strrchr(buffer, '/');
    free(resolved);
    return (DWORD)strlen(buffer);
}
UINT GetWindowsDirectoryA(LPSTR buffer, UINT size)
{
    snprintf(buffer, size, "%s", "/tmp");
    return lstrlenA(buffer);
}
BOOL GetDiskFreeSpaceA(LPCSTR root, LPDWORD sectors, LPDWORD bytes, LPDWORD free_clusters,
                       LPDWORD clusters)
{
    (void)root;
    if (sectors) *sectors = 1;
    if (bytes) *bytes = 4096;
    if (free_clusters) *free_clusters = 1024 * 1024;
    if (clusters) *clusters = 1024 * 1024;
    return TRUE;
}
HANDLE FindFirstFileA(LPCSTR pattern, LPWIN32_FIND_DATAA data)
{
    char normalized[PATH_MAX];
    char resolved[PATH_MAX];
    const char *path;
    const char *leaf;
    struct stat st;

    e2r_normalize_path(normalized, sizeof(normalized), pattern);
    path = normalized;
    if (stat(path, &st) != 0) {
        if (!e2r_resolve_case_path(normalized, resolved, sizeof(resolved)) || stat(resolved, &st) != 0) {
            return INVALID_HANDLE_VALUE;
        }
        path = resolved;
    }
    if (data) {
        memset(data, 0, sizeof(*data));
        data->dwFileAttributes = S_ISDIR(st.st_mode) ? 0x10u : FILE_ATTRIBUTE_NORMAL;
        data->nFileSizeLow = (DWORD)st.st_size;
        leaf = strrchr(path, '/');
        leaf = leaf ? leaf + 1 : path;
        strncpy(data->cFileName, leaf, sizeof(data->cFileName) - 1);
    }
    return e2r_alloc_handle(NULL);
}
BOOL FindNextFileA(HANDLE find, LPWIN32_FIND_DATAA data) { (void)find; (void)data; return FALSE; }
BOOL FindClose(HANDLE find) { if (!find || find == INVALID_HANDLE_VALUE) return FALSE; free(find); return TRUE; }

BOOL GetConsoleMode(HANDLE console, DWORD *mode) { (void)console; if (mode) *mode = 0; return TRUE; }
BOOL SetConsoleMode(HANDLE console, DWORD mode) { (void)console; (void)mode; return TRUE; }
HANDLE GetStdHandle(DWORD id) { (void)id; return &e2r_handle; }
BOOL ReadConsoleInputA(HANDLE input, INPUT_RECORD *records, DWORD length, DWORD *read)
{
    (void)input; (void)records; (void)length;
    if (read) *read = 0;
    return FALSE;
}
BOOL WriteConsoleA(HANDLE console, LPCVOID buffer, DWORD chars, DWORD *written, LPVOID reserved)
{
    (void)console; (void)reserved;
    if (written) *written = chars;
    fwrite(buffer, 1, chars, stdout);
    return TRUE;
}

LPSTR GetCommandLineA(void) { return ""; }
LPSTR GetEnvironmentStrings(void) { return ""; }
DWORD GetModuleFileNameA(HMODULE module, LPSTR filename, DWORD size)
{
    (void)module;
    snprintf(filename, size, "%s", "e2recomp");
    return lstrlenA(filename);
}
void ExitProcess(UINT exit_code) { exit((int)exit_code); }
void ExitThread(DWORD exit_code) { exit((int)exit_code); }

void GetLocalTime(SYSTEMTIME *time_out)
{
    time_t now = time(NULL);
    struct tm tm_now;
    localtime_r(&now, &tm_now);
    if (!time_out) return;
    time_out->wYear = (WORD)(tm_now.tm_year + 1900);
    time_out->wMonth = (WORD)(tm_now.tm_mon + 1);
    time_out->wDay = (WORD)tm_now.tm_mday;
    time_out->wDayOfWeek = (WORD)tm_now.tm_wday;
    time_out->wHour = (WORD)tm_now.tm_hour;
    time_out->wMinute = (WORD)tm_now.tm_min;
    time_out->wSecond = (WORD)tm_now.tm_sec;
    time_out->wMilliseconds = 0;
}
DWORD GetTimeZoneInformation(LPTIME_ZONE_INFORMATION info)
{
    if (info) memset(info, 0, sizeof(*info));
    return 0;
}
BOOL FileTimeToLocalFileTime(const FILETIME *file_time, FILETIME *local_file_time)
{
    if (local_file_time && file_time) *local_file_time = *file_time;
    return TRUE;
}
BOOL FileTimeToDosDateTime(const FILETIME *file_time, LPWORD date, LPWORD time_out)
{
    (void)file_time;
    if (date) *date = 0;
    if (time_out) *time_out = 0;
    return TRUE;
}

HANDLE CreateMutexA(LPSECURITY_ATTRIBUTES attrs, BOOL initial_owner, LPCSTR name)
{
    (void)attrs; (void)initial_owner; (void)name;
    return &e2r_handle;
}
DWORD WaitForSingleObject(HANDLE handle, DWORD milliseconds)
{
    (void)handle; (void)milliseconds;
    return 0;
}
BOOL ReleaseMutex(HANDLE handle) { (void)handle; return TRUE; }
BOOL SetEvent(HANDLE handle) { (void)handle; return TRUE; }
DWORD TlsAlloc(void) { return e2r_next_tls < 64 ? e2r_next_tls++ : (DWORD)-1; }
BOOL TlsSetValue(DWORD index, LPVOID value)
{
    if (index >= 64) return FALSE;
    e2r_tls[index] = value;
    return TRUE;
}
LPVOID TlsGetValue(DWORD index) { return index < 64 ? e2r_tls[index] : NULL; }

UINT midiOutGetNumDevs(void) { return 0; }
MMRESULT midiOutGetDevCapsA(UINT_PTR device_id, LPMIDIOUTCAPSA caps, UINT size)
{
    (void)device_id;
    if (caps) memset(caps, 0, size);
    return 0;
}

HMMIO mmioOpenA(LPSTR filename, LPMMIOINFO info, DWORD flags)
{
    (void)info; (void)flags;
    FILE *file = fopen(filename ? filename : "", "rb");
    return file ? (HMMIO)e2r_alloc_handle(file) : NULL;
}
MMRESULT mmioClose(HMMIO mmio, UINT flags) { (void)flags; return CloseHandle((HANDLE)mmio) ? 0 : 1; }
LONG mmioRead(HMMIO mmio, HPSTR buffer, LONG count)
{
    if (!mmio || !mmio->ptr) return -1;
    return (LONG)fread(buffer, 1, count, (FILE *)mmio->ptr);
}
LONG mmioSeek(HMMIO mmio, LONG offset, int origin)
{
    if (!mmio || !mmio->ptr) return -1;
    return fseek((FILE *)mmio->ptr, offset, origin) == 0 ? (LONG)ftell((FILE *)mmio->ptr) : -1;
}
MMRESULT mmioDescend(HMMIO mmio, LPMMCKINFO ck, const MMCKINFO *parent, UINT flags)
{
    (void)mmio; (void)ck; (void)parent; (void)flags;
    return 1;
}
MMRESULT mmioAscend(HMMIO mmio, LPMMCKINFO ck, UINT flags)
{
    (void)mmio; (void)ck; (void)flags;
    return 0;
}
MMRESULT mmioGetInfo(HMMIO mmio, LPMMIOINFO info, UINT flags)
{
    (void)mmio; (void)flags;
    if (info) memset(info, 0, sizeof(*info));
    return 0;
}
MMRESULT mmioAdvance(HMMIO mmio, LPMMIOINFO info, UINT flags)
{
    (void)mmio; (void)info; (void)flags;
    return 0;
}
MMRESULT mmioSetInfo(HMMIO mmio, const MMIOINFO *info, UINT flags)
{
    (void)mmio; (void)info; (void)flags;
    return 0;
}
