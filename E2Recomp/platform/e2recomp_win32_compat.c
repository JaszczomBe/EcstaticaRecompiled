#include "e2recomp_win32_compat.h"

#include <stdarg.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#ifndef _WIN32
#include <sys/mman.h>
#ifndef MAP_ANONYMOUS
#define MAP_ANONYMOUS MAP_ANON
#endif
#endif

static E2R_HANDLE__ e2r_module = {0, 0};
static E2R_HANDLE__ e2r_window = {0, 0};
static E2R_HANDLE__ e2r_handle = {0, 0};
static DWORD e2r_last_error;
static void *e2r_tls[64];
static DWORD e2r_next_tls;

void E2R_MapLegacyAddressSpace(void)
{
#ifndef _WIN32
    static int initialized;
    const uintptr_t base = 0x00400000u;
    const size_t size = 0x00700000u;
    int flags = MAP_PRIVATE | MAP_ANONYMOUS;
    void *mapped;

    if (initialized) return;
    initialized = 1;

#ifdef MAP_FIXED_NOREPLACE
    flags |= MAP_FIXED_NOREPLACE;
#else
    flags |= MAP_FIXED;
#endif

    mapped = mmap((void *)base, size, PROT_READ | PROT_WRITE, flags, -1, 0);
    if (mapped == MAP_FAILED) {
        fprintf(stderr,
                "warning: could not map legacy Ecstatica address range 0x%08lx..0x%08lx: %s\n",
                (unsigned long)base,
                (unsigned long)(base + size),
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

HANDLE CreateFileA(LPCSTR name, DWORD access, DWORD share, LPVOID security,
                   DWORD creation, DWORD flags, HANDLE template_file)
{
    (void)share;
    (void)security;
    (void)creation;
    (void)flags;
    (void)template_file;
    FILE *file = fopen(name ? name : "", (access & GENERIC_WRITE) ? "wb+" : "rb");
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
BOOL IsBadReadPtr(const void *ptr, UINT_PTR size)
{
    (void)size;
    return ptr == NULL || (uintptr_t)ptr < 0x10000u;
}

BOOL IsWindow(HWND hwnd) { return hwnd != NULL; }
BOOL DestroyWindow(HWND hwnd) { (void)hwnd; return TRUE; }
BOOL ShowWindow(HWND hwnd, int cmd_show) { (void)hwnd; (void)cmd_show; return TRUE; }
BOOL UpdateWindow(HWND hwnd) { (void)hwnd; return TRUE; }
HWND SetFocus(HWND hwnd) { return hwnd; }
int ShowCursor(BOOL show) { (void)show; return 0; }
BOOL GetCursorPos(POINT *point) { if (point) point->x = point->y = 0; return TRUE; }
BOOL PeekMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter, UINT remove)
{
    (void)msg; (void)hwnd; (void)min_filter; (void)max_filter; (void)remove;
    return FALSE;
}
BOOL GetMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter)
{
    (void)msg; (void)hwnd; (void)min_filter; (void)max_filter;
    return FALSE;
}
BOOL TranslateMessage(const MSG *msg) { (void)msg; return TRUE; }
LRESULT DispatchMessageA(const MSG *msg) { (void)msg; return 0; }
void WaitMessage(void) {}
void Sleep(DWORD milliseconds) { usleep(milliseconds * 1000u); }
void PostQuitMessage(int exit_code) { (void)exit_code; }
BOOL PostMessageA(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
    (void)hwnd; (void)msg; (void)wparam; (void)lparam;
    return TRUE;
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
    (void)ex_style; (void)class_name; (void)window_name; (void)style;
    (void)x; (void)y; (void)width; (void)height; (void)parent; (void)menu;
    (void)instance; (void)param;
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
ATOM RegisterClassA(const WNDCLASSA *wnd_class) { (void)wnd_class; return 1; }
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
    return (HGLOBAL)e2r_alloc_handle(calloc(1, bytes));
}
LPVOID GlobalLock(HGLOBAL mem) { return mem ? mem->ptr : NULL; }
BOOL GlobalUnlock(HGLOBAL mem) { (void)mem; return TRUE; }
HGLOBAL GlobalHandle(LPCVOID mem) { return (HGLOBAL)mem; }
HGLOBAL GlobalFree(HGLOBAL mem)
{
    if (!mem) return NULL;
    free(mem->ptr);
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
    (void)pattern;
    if (data) memset(data, 0, sizeof(*data));
    return INVALID_HANDLE_VALUE;
}
BOOL FindNextFileA(HANDLE find, LPWIN32_FIND_DATAA data) { (void)find; (void)data; return FALSE; }
BOOL FindClose(HANDLE find) { (void)find; return TRUE; }

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
