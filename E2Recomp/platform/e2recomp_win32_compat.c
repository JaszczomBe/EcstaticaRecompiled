#include "e2recomp_win32_compat.h"
#include "e2recomp_host_backend.h"

#include <stdarg.h>
#include <ctype.h>
#include <errno.h>
#include <dirent.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <time.h>
#include <unistd.h>
#include "e2recomp_log.h"
#ifndef _WIN32
#include <fcntl.h>
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
static POINT e2r_cursor_pos;

#define E2R_MESSAGE_QUEUE_CAPACITY 32
#define E2R_HOST_ALLOC_MAGIC 0xe2a110c0u
#define E2R_REGISTERED_CLASS_CAPACITY 16

static MSG e2r_message_queue[E2R_MESSAGE_QUEUE_CAPACITY];
static unsigned e2r_message_head;
static unsigned e2r_message_tail;

static DWORD e2r_monotonic_milliseconds(void)
{
#ifndef _WIN32
    struct timespec ts;

    if (clock_gettime(CLOCK_MONOTONIC, &ts) == 0) {
        return (DWORD)((uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u);
    }
#endif
    return (DWORD)(time(NULL) * 1000u);
}

typedef struct E2R_REGISTERED_CLASS {
    LPCSTR name;
    WNDPROC proc;
} E2R_REGISTERED_CLASS;

static E2R_REGISTERED_CLASS e2r_registered_classes[E2R_REGISTERED_CLASS_CAPACITY];
static unsigned e2r_registered_class_count;

typedef struct E2R_HOST_ALLOC_HEADER {
    size_t mapping_size;
    unsigned magic;
} E2R_HOST_ALLOC_HEADER;

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

static void e2r_update_cursor_from_lparam(LPARAM lparam)
{
    e2r_cursor_pos.x = (int16_t)(lparam & 0xffffu);
    e2r_cursor_pos.y = (int16_t)((lparam >> 16) & 0xffffu);
}

static BOOL e2r_class_name_matches(LPCSTR a, LPCSTR b)
{
    if (a == b) {
        return TRUE;
    }
    if (a == NULL || b == NULL) {
        return FALSE;
    }
    return strcmp(a, b) == 0;
}

static WNDPROC e2r_find_registered_class_proc(LPCSTR class_name)
{
    unsigned i;

    for (i = 0; i < e2r_registered_class_count; i++) {
        if (e2r_class_name_matches(e2r_registered_classes[i].name, class_name)) {
            return e2r_registered_classes[i].proc;
        }
    }
    return NULL;
}

static void e2r_register_class_proc(LPCSTR class_name, WNDPROC proc)
{
    unsigned i;

    for (i = 0; i < e2r_registered_class_count; i++) {
        if (e2r_class_name_matches(e2r_registered_classes[i].name, class_name)) {
            e2r_registered_classes[i].proc = proc;
            return;
        }
    }
    if (e2r_registered_class_count < E2R_REGISTERED_CLASS_CAPACITY) {
        e2r_registered_classes[e2r_registered_class_count].name = class_name;
        e2r_registered_classes[e2r_registered_class_count].proc = proc;
        e2r_registered_class_count++;
    }
}

static int e2r_input_diag_enabled(void)
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
        initialized = 1;
    }
    return enabled;
}

static int e2r_should_log_host_message(UINT msg)
{
    switch (msg) {
    case WM_CLOSE:
    case WM_DESTROY:
    case WM_SIZE:
    case WM_KEYDOWN:
    case WM_KEYUP:
    case WM_LBUTTONDOWN:
    case WM_LBUTTONUP:
    case WM_RBUTTONDOWN:
    case WM_RBUTTONUP:
    case WM_MBUTTONDOWN:
    case WM_MBUTTONUP:
        return 1;
    default:
        return 0;
    }
}

static void e2r_queue_host_message(UINT msg, WPARAM wparam, LPARAM lparam, void *user)
{
    static unsigned message_diag_count;

    (void)user;
    switch (msg) {
    case WM_MOUSEMOVE:
    case WM_LBUTTONDOWN:
    case WM_LBUTTONUP:
    case WM_RBUTTONDOWN:
    case WM_RBUTTONUP:
    case WM_MBUTTONDOWN:
    case WM_MBUTTONUP:
        e2r_update_cursor_from_lparam(lparam);
        break;
    default:
        break;
    }
    if (e2r_input_diag_enabled() && e2r_should_log_host_message(msg) &&
        message_diag_count < 256u) {
        fprintf(stderr,
                "host message dispatch: msg=0x%x wparam=0x%lx lparam=0x%lx direct=%d wndproc=%p\n",
                (unsigned)msg, (unsigned long)wparam, (unsigned long)lparam,
                e2r_window_proc != NULL, (void *)e2r_window_proc);
        message_diag_count++;
    }
    if (msg == WM_KEYDOWN && wparam == VK_F12) {
        E2R_RequestVisibilityDump();
        return;
    }
    if (e2r_window_proc != NULL && msg != WM_QUIT) {
        e2r_window_proc(&e2r_window, msg, wparam, lparam);
        return;
    }
    if (msg == WM_CLOSE) {
        DefWindowProcA(&e2r_window, msg, wparam, lparam);
        return;
    }
    e2r_push_message(&e2r_window, msg, wparam, lparam);
}

static void e2r_poll_host_events(const char *site)
{
    static unsigned poll_diag_count;

    if (e2r_window.ptr == NULL) {
        return;
    }
    if (e2r_input_diag_enabled() && poll_diag_count < 1u) {
        fprintf(stderr, "host pump: site=%s hwnd_ptr=%p wndproc=%p\n",
                site, e2r_window.ptr, (void *)e2r_window_proc);
        poll_diag_count++;
    }
    E2R_HostPollEvents((E2R_HostWindow *)e2r_window.ptr,
                       e2r_queue_host_message, NULL);
}

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

static void *e2r_host_alloc_zero(size_t bytes)
{
    size_t payload_size = bytes == 0 ? 1 : bytes;
#ifndef _WIN32
    size_t mapping_size;
    E2R_HOST_ALLOC_HEADER *header;

    if (payload_size > ((size_t)-1) - sizeof(*header)) return NULL;
    mapping_size = sizeof(*header) + payload_size;
    header = (E2R_HOST_ALLOC_HEADER *)mmap(NULL, mapping_size, PROT_READ | PROT_WRITE,
                                           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (header == MAP_FAILED) return NULL;
    header->mapping_size = mapping_size;
    header->magic = E2R_HOST_ALLOC_MAGIC;
    return (void *)(header + 1);
#else
    return calloc(1, payload_size);
#endif
}

static void e2r_host_free(void *mem)
{
#ifndef _WIN32
    E2R_HOST_ALLOC_HEADER *header;

    if (mem == NULL) return;
    header = ((E2R_HOST_ALLOC_HEADER *)mem) - 1;
    if (header->magic == E2R_HOST_ALLOC_MAGIC) {
        size_t mapping_size = header->mapping_size;
        header->magic = 0;
        munmap(header, mapping_size);
        return;
    }
#endif
    free(mem);
}

static HANDLE e2r_alloc_handle(void *ptr)
{
    E2R_HANDLE__ *handle = (E2R_HANDLE__ *)e2r_host_alloc_zero(sizeof(*handle));
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

static int e2r_resolve_known_data_path(const char *input, char *resolved, size_t resolved_size)
{
    static const struct {
        const char *lower;
        const char *actual;
    } dirs[] = {
        {"code", "Code"},
        {"files", "Files"},
        {"graphics", "Graphics"},
        {"hires", "Hires"},
        {"lowgraph", "Lowgraph"},
        {"music", "Music"},
        {"saved", "Saved"},
        {"views", "Views"},
    };
    const char *slash;
    const char *rest;
    size_t dir_len;
    size_t i;
    size_t out;

    if (!input || input[0] == '/' || resolved_size == 0) return 0;
    slash = strchr(input, '/');
    if (!slash) {
        struct stat st;
        for (out = 0; input[out] != '\0' && out + 1 < resolved_size; out++) {
            resolved[out] = (char)toupper((unsigned char)input[out]);
        }
        if (input[out] != '\0') return 0;
        resolved[out] = '\0';
        return stat(resolved, &st) == 0;
    }
    dir_len = (size_t)(slash - input);
    rest = slash + 1;
    for (i = 0; i < sizeof(dirs) / sizeof(dirs[0]); i++) {
        if (strlen(dirs[i].lower) == dir_len && strncasecmp(input, dirs[i].lower, dir_len) == 0) {
            break;
        }
    }
    if (i == sizeof(dirs) / sizeof(dirs[0])) return 0;
    if (snprintf(resolved, resolved_size, "%s/%s", dirs[i].actual, rest) >= (int)resolved_size) {
        return 0;
    }
    for (out = strlen(dirs[i].actual) + 1; resolved[out] != '\0'; out++) {
        resolved[out] = (char)toupper((unsigned char)resolved[out]);
    }
    return 1;
}

HANDLE CreateFileA(LPCSTR name, DWORD access, DWORD share, LPVOID security,
                   DWORD creation, DWORD flags, HANDLE template_file)
{
    char normalized[PATH_MAX];
    char resolved[PATH_MAX];
    char cwd[PATH_MAX];
    const char *open_name;
    FILE *file;
    int resolved_case = 0;
    (void)share;
    (void)security;
    (void)creation;
    (void)flags;
    (void)template_file;
    e2r_normalize_path(normalized, sizeof(normalized), name);
    open_name = normalized;
    file = fopen(open_name, (access & GENERIC_WRITE) ? "wb+" : "rb");
    if (!file && (access & GENERIC_WRITE) == 0 && e2r_resolve_known_data_path(normalized, resolved, sizeof(resolved))) {
        open_name = resolved;
        resolved_case = 2;
        file = fopen(open_name, "rb");
    }
    if (!file && (access & GENERIC_WRITE) == 0 && strchr(normalized, '/') != NULL &&
        e2r_resolve_case_path(normalized, resolved, sizeof(resolved))) {
        open_name = resolved;
        resolved_case = 1;
        file = fopen(open_name, "rb");
    }
    if (!file) {
        const char *diag = getenv("E2R_FILE_DIAG");
        if (diag && diag[0] && diag[0] != '0') {
            if (!getcwd(cwd, sizeof(cwd))) {
                snprintf(cwd, sizeof(cwd), "(getcwd failed)");
            }
            fprintf(stderr,
                    "CreateFileA failed: name=%s normalized=%s resolved_case=%d open_name=%s cwd=%s errno=%d\n",
                    name ? name : "(null)", normalized, resolved_case, open_name, cwd, errno);
        }
        return INVALID_HANDLE_VALUE;
    }
    setvbuf(file, NULL, _IONBF, 0);
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
    e2r_host_free(file);
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
DWORD GetTickCount(void) { return e2r_monotonic_milliseconds(); }
DWORD timeGetTime(void) { return GetTickCount(); }

LPVOID VirtualAlloc(LPVOID address, size_t size, DWORD allocation_type, DWORD protect)
{
    (void)address;
    (void)allocation_type;
    (void)protect;
    return e2r_host_alloc_zero(size);
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

#ifndef _WIN32
static int e2r_maps_hex_digit(char ch)
{
    if ('0' <= ch && ch <= '9') return ch - '0';
    if ('a' <= ch && ch <= 'f') return ch - 'a' + 10;
    if ('A' <= ch && ch <= 'F') return ch - 'A' + 10;
    return -1;
}

static const char *e2r_parse_maps_hex(const char *cursor, const char *end, uintptr_t *value)
{
    int digit;
    uintptr_t parsed = 0;
    int saw_digit = 0;

    while (cursor < end && (digit = e2r_maps_hex_digit(*cursor)) >= 0) {
        parsed = (parsed << 4) | (uintptr_t)digit;
        cursor++;
        saw_digit = 1;
    }
    if (!saw_digit) return NULL;
    *value = parsed;
    return cursor;
}

static int e2r_parse_maps_line(const char *line, size_t length, uintptr_t *lo, uintptr_t *hi, char perms[4])
{
    const char *cursor = line;
    const char *end = line + length;

    cursor = e2r_parse_maps_hex(cursor, end, lo);
    if (cursor == NULL || cursor >= end || *cursor != '-') return 0;
    cursor++;
    cursor = e2r_parse_maps_hex(cursor, end, hi);
    if (cursor == NULL || cursor >= end || *cursor != ' ') return 0;
    while (cursor < end && *cursor == ' ') cursor++;
    if ((size_t)(end - cursor) < 4) return 0;

    perms[0] = cursor[0];
    perms[1] = cursor[1];
    perms[2] = cursor[2];
    perms[3] = cursor[3];
    return 1;
}

typedef struct E2R_MemoryMapRange {
    uintptr_t lo;
    uintptr_t hi;
    char perms[4];
} E2R_MemoryMapRange;

#define E2R_MEMORY_MAP_CACHE_CAPACITY 1024

static E2R_MemoryMapRange e2r_memory_map_cache[E2R_MEMORY_MAP_CACHE_CAPACITY];
static size_t e2r_memory_map_cache_count;
static int e2r_memory_map_cache_valid;
static pthread_mutex_t e2r_memory_map_cache_mutex = PTHREAD_MUTEX_INITIALIZER;

static int e2r_refresh_memory_map_cache(void)
{
    int maps_fd;
    char buffer[4096];
    char line[512];
    size_t line_length = 0;
    size_t count = 0;
    ssize_t bytes_read;

    maps_fd = open("/proc/self/maps", O_RDONLY
#ifdef O_CLOEXEC
                   | O_CLOEXEC
#endif
    );
    if (maps_fd < 0) return 0;

    while ((bytes_read = read(maps_fd, buffer, sizeof(buffer))) > 0) {
        ssize_t i;

        for (i = 0; i < bytes_read; i++) {
            char ch = buffer[i];
            if (ch != '\n') {
                if (line_length < sizeof(line)) {
                    line[line_length++] = ch;
                }
                continue;
            }

            if (count < E2R_MEMORY_MAP_CACHE_CAPACITY) {
                E2R_MemoryMapRange *range = &e2r_memory_map_cache[count];
                if (e2r_parse_maps_line(line, line_length, &range->lo, &range->hi,
                                        range->perms)) {
                    count++;
                }
            }
            line_length = 0;
        }
    }

    if (bytes_read == 0 && line_length != 0 && count < E2R_MEMORY_MAP_CACHE_CAPACITY) {
        E2R_MemoryMapRange *range = &e2r_memory_map_cache[count];
        if (e2r_parse_maps_line(line, line_length, &range->lo, &range->hi,
                                range->perms)) {
            count++;
        }
    }

    close(maps_fd);
    if (bytes_read < 0) return 0;
    e2r_memory_map_cache_count = count;
    e2r_memory_map_cache_valid = 1;
    return 1;
}

static BOOL e2r_is_bad_memory_range_cached(uintptr_t start, uintptr_t end, char permission)
{
    uintptr_t cursor = start;
    size_t i;

    for (i = 0; i < e2r_memory_map_cache_count; i++) {
        const E2R_MemoryMapRange *range = &e2r_memory_map_cache[i];

        if (range->hi <= cursor) continue;
        if (range->lo > cursor) return TRUE;
        if ((permission == 'r' && range->perms[0] != 'r') ||
            (permission == 'w' && range->perms[1] != 'w')) {
            return TRUE;
        }

        cursor = range->hi;
        if (cursor >= end) return FALSE;
    }

    return TRUE;
}
#endif

static BOOL e2r_is_bad_memory_range(const void *ptr, UINT_PTR size, char permission)
{
    uintptr_t start = (uintptr_t)ptr;
    uintptr_t end;

    if (size == 0) return FALSE;
    if (ptr == NULL || start < 0x10000u) return TRUE;
    end = start + (uintptr_t)size;
    if (end <= start) return TRUE;

#ifndef _WIN32
    {
        BOOL bad;

        pthread_mutex_lock(&e2r_memory_map_cache_mutex);
        if (!e2r_memory_map_cache_valid && !e2r_refresh_memory_map_cache()) {
            pthread_mutex_unlock(&e2r_memory_map_cache_mutex);
            return TRUE;
        }
        bad = e2r_is_bad_memory_range_cached(start, end, permission);
        if (bad && e2r_refresh_memory_map_cache()) {
            bad = e2r_is_bad_memory_range_cached(start, end, permission);
        }
        pthread_mutex_unlock(&e2r_memory_map_cache_mutex);
        return bad;
    }
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

BOOL IsWindow(HWND hwnd)
{
    if (hwnd == &e2r_window) {
        return hwnd->ptr != NULL;
    }
    return hwnd != NULL;
}
BOOL DestroyWindow(HWND hwnd)
{
    if (hwnd == &e2r_window && hwnd->ptr != NULL) {
        E2R_HostDestroyWindow((E2R_HostWindow *)hwnd->ptr);
        hwnd->ptr = NULL;
        if (e2r_window_proc != NULL) {
            e2r_window_proc(hwnd, WM_DESTROY, 0, 0);
        }
    }
    (void)hwnd;
    return TRUE;
}
BOOL ShowWindow(HWND hwnd, int cmd_show)
{
    if (hwnd == &e2r_window && hwnd->ptr != NULL && cmd_show != 0) {
        E2R_HostShowWindow((E2R_HostWindow *)hwnd->ptr);
    }
    (void)hwnd; (void)cmd_show;
    return TRUE;
}
BOOL UpdateWindow(HWND hwnd)
{
    if (hwnd == &e2r_window && e2r_window.ptr != NULL) {
        E2R_PumpHostEvents();
    }
    E2R_TryPresentCurrentFrame(hwnd);
    (void)hwnd;
    return TRUE;
}
HWND SetFocus(HWND hwnd) { return hwnd; }
int ShowCursor(BOOL show) { (void)show; return 0; }
BOOL GetCursorPos(POINT *point)
{
    if (point != NULL) {
        *point = e2r_cursor_pos;
    }
    return TRUE;
}
BOOL SetCursorPos(int x, int y)
{
    e2r_cursor_pos.x = x;
    e2r_cursor_pos.y = y;
    return TRUE;
}
void E2R_PumpHost(void)
{
    if (e2r_window.ptr != NULL) {
        E2R_PumpHostEvents();
        E2R_TryPresentCurrentFrame(&e2r_window);
    }
}
void E2R_PumpHostEvents(void)
{
    e2r_poll_host_events("E2R_PumpHostEvents");
}
BOOL PeekMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter, UINT remove)
{
    E2R_PumpHost();
    return e2r_pop_message(msg, hwnd, min_filter, max_filter, (remove & PM_REMOVE) != 0);
}
BOOL GetMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter)
{
    E2R_PumpHost();
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
void Sleep(DWORD milliseconds)
{
#ifndef _WIN32
    DWORD remaining = milliseconds;

    do {
        DWORD slice = remaining > 16u ? 16u : remaining;
        E2R_PumpHost();
        usleep((slice == 0u ? 1u : slice) * 1000u);
        if (remaining <= slice) {
            break;
        }
        remaining -= slice;
    } while (remaining != 0u);
#else
    (void)milliseconds;
#endif
}
void PostQuitMessage(int exit_code)
{
    fflush(NULL);
    exit(exit_code);
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
    if (msg == WM_CLOSE) {
        DestroyWindow(hwnd);
        return 0;
    }
    (void)hwnd; (void)wparam; (void)lparam;
    return 0;
}
HWND CreateWindowExA(DWORD ex_style, LPCSTR class_name, LPCSTR window_name,
                     DWORD style, int x, int y, int width, int height,
                     HWND parent, HMENU menu, HINSTANCE instance, LPVOID param)
{
    (void)ex_style; (void)style; (void)menu; (void)instance; (void)param;
    if (!parent) {
        E2R_HostWindow *host_window;
        WNDPROC class_proc;
        unsigned int w = width > 0 ? (unsigned int)width : 640u;
        unsigned int h = height > 0 ? (unsigned int)height : 480u;

        host_window = E2R_HostCreateWindow(window_name ? window_name : "Ecstatica II",
                                           x, y, w, h);
        if (host_window != NULL) {
            e2r_window.ptr = host_window;
            class_proc = e2r_find_registered_class_proc(class_name);
            if (class_proc != NULL) {
                e2r_window_proc = class_proc;
                if (e2r_input_diag_enabled()) {
                    fprintf(stderr,
                            "host window proc bind: class=%s wndproc=%p title=%s\n",
                            class_name != NULL ? class_name : "<null>",
                            (void *)e2r_window_proc,
                            window_name != NULL ? window_name : "<null>");
                }
            }
        }
    }
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
    if (wnd_class != NULL) {
        e2r_register_class_proc(wnd_class->lpszClassName, wnd_class->lpfnWndProc);
        if (e2r_window_proc == NULL) {
            e2r_window_proc = wnd_class->lpfnWndProc;
        }
        if (e2r_input_diag_enabled()) {
            fprintf(stderr, "host class register: class=%s wndproc=%p active=%p\n",
                    wnd_class->lpszClassName != NULL ? wnd_class->lpszClassName : "<null>",
                    (void *)wnd_class->lpfnWndProc, (void *)e2r_window_proc);
        }
    }
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
    return (HGLOBAL)e2r_host_alloc_zero(bytes);
}
LPVOID GlobalLock(HGLOBAL mem) { return mem; }
BOOL GlobalUnlock(HGLOBAL mem) { (void)mem; return TRUE; }
HGLOBAL GlobalHandle(LPCVOID mem) { return (HGLOBAL)mem; }
HGLOBAL GlobalFree(HGLOBAL mem)
{
    if (!mem) return NULL;
    e2r_host_free(mem);
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
void ExitProcess(UINT exit_code)
{
    fprintf(stderr, "E2R ExitProcess(%u) caller=%p caller1=%p caller2=%p caller3=%p\n",
            exit_code, __builtin_return_address(0), __builtin_return_address(1),
            __builtin_return_address(2), __builtin_return_address(3));
    fflush(stderr);
#ifndef _WIN32
    if (exit_code > 0xffu) {
        fprintf(stderr, "E2R treating high ExitProcess code as stale-register thread termination\n");
        fflush(stderr);
        pthread_exit((void *)(uintptr_t)(exit_code & 0xffu));
    }
#endif
    exit((int)exit_code);
}

void ExitThread(DWORD exit_code)
{
    fprintf(stderr, "E2R ExitThread(%u)\n", exit_code);
    fflush(stderr);
#ifndef _WIN32
    pthread_exit((void *)(uintptr_t)exit_code);
#else
    exit((int)exit_code);
#endif
}

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
