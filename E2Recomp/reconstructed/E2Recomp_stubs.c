#include "E2Recomp_recon.h"
#include <stdarg.h>

#undef CreateWindowExA
#undef DialogBoxParamA

uintptr_t E2R_timer_slots[8];

void *memcpy(void *dst, const void *src, size_t n) {
    unsigned char *d = (unsigned char *)dst;
    const unsigned char *s = (const unsigned char *)src;
    while (n--) *d++ = *s++;
    return dst;
}

static LONG __stdcall E2R_CrashFilter(struct _EXCEPTION_POINTERS *info) {
    char buffer[512];
    DWORD written;
    HANDLE f = CreateFileA("E2Recomp_rebuilt_crash.log", GENERIC_WRITE, FILE_SHARE_READ, NULL,
                           CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f != INVALID_HANDLE_VALUE) {
#if defined(_M_IX86)
        wsprintfA(buffer,
                  "ModuleBase=0x%08lx\r\nExceptionCode=0x%08lx\r\nExceptionAddress=0x%08lx\r\nEIP=0x%08lx\r\nESP=0x%08lx\r\nEAX=0x%08lx EBX=0x%08lx ECX=0x%08lx EDX=0x%08lx\r\nSTACK=0x%08lx 0x%08lx 0x%08lx 0x%08lx 0x%08lx 0x%08lx\r\n",
                  (DWORD)(uintptr_t)GetModuleHandleA(NULL),
                  info->ExceptionRecord->ExceptionCode,
                  (DWORD)(uintptr_t)info->ExceptionRecord->ExceptionAddress,
                  info->ContextRecord->Eip,
                  info->ContextRecord->Esp,
                  info->ContextRecord->Eax, info->ContextRecord->Ebx,
                  info->ContextRecord->Ecx, info->ContextRecord->Edx,
                  ((DWORD *)info->ContextRecord->Esp)[0],
                  ((DWORD *)info->ContextRecord->Esp)[1],
                  ((DWORD *)info->ContextRecord->Esp)[2],
                  ((DWORD *)info->ContextRecord->Esp)[3],
                  ((DWORD *)info->ContextRecord->Esp)[4],
                  ((DWORD *)info->ContextRecord->Esp)[5]);
#else
        wsprintfA(buffer, "ExceptionCode=0x%08lx\r\nExceptionAddress=%p\r\n",
                  info->ExceptionRecord->ExceptionCode,
                  info->ExceptionRecord->ExceptionAddress);
#endif
        WriteFile(f, buffer, lstrlenA(buffer), &written, NULL);
        CloseHandle(f);
    }
    return EXCEPTION_EXECUTE_HANDLER;
}

void E2R_InstallCrashHandler(void) {
    SetUnhandledExceptionFilter(E2R_CrashFilter);
    VirtualAlloc((LPVOID)0x00400000, 0x00100000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    VirtualAlloc((LPVOID)0x00600000, 0x00100000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    VirtualAlloc((LPVOID)0x00700000, 0x00200000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    VirtualAlloc((LPVOID)0x00900000, 0x00100000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    VirtualAlloc((LPVOID)0x00a00000, 0x00100000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
}

void E2R_WinMainThunk(void) {
    MSG msg;
    _DAT_00ac4d90 = (uintptr_t)GetModuleHandleA(NULL);
    if (FUN_00458714() != 0) {
        FUN_0041ba68(0, 0);
        FUN_0041007c(0);
    }
    while (IsWindow((HWND)_DAT_00ac4dac)) {
        while (PeekMessageA(&msg, NULL, 0, 0, PM_REMOVE)) {
            if (msg.message != WM_QUIT) {
                TranslateMessage(&msg);
                DispatchMessageA(&msg);
            }
        }
        Sleep(16);
    }
}

LRESULT CALLBACK E2R_WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (msg == WM_DESTROY) {
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcA(hWnd, msg, wParam, lParam);
}

int in(unsigned short port) { (void)port; return 0; }
void out(unsigned short port, unsigned int value) { (void)port; (void)value; }

double fpatan(double a, double b) { (void)b; return a; }
double fptan(double a) { return a; }
int ROUND(double value) { return (int)value; }
void halt_baddata(void) {}

unsigned __int64 ZEXT48(unsigned int value) { return value; }
unsigned __int64 CONCAT24(unsigned short hi, unsigned int lo) { return (((unsigned __int64)hi) << 32) | lo; }
unsigned __int64 CONCAT28(unsigned short hi, unsigned __int64 lo) { return (((unsigned __int64)hi) << 48) | (lo & 0x0000ffffffffffffULL); }
unsigned int SUB84(unsigned __int64 value, unsigned int offset) { return (unsigned int)(value >> (offset * 8)); }
unsigned int SUB104(unkuint10 value, unsigned int offset) { return (unsigned int)(value >> (offset * 8)); }
int CARRY1(unsigned char a, unsigned char b) { return (unsigned int)a + (unsigned int)b > 0xffu; }
int CARRY4(unsigned int a, unsigned int b) { return (unsigned __int64)a + (unsigned __int64)b > 0xffffffffULL; }
int ABS(int value) { return value < 0 ? -value : value; }
void LOCK(void) {}
void UNLOCK(void) {}
void swi(unsigned int interrupt_id) { (void)interrupt_id; }

double NAN = 0.0;
uintptr_t LocalDescriptorTableRegister = 0;
int _except1 = 0;

void func_0x0045cf39(void) {}
void func_0x0045d839(void) {}
void func_0x0045d7c4(void) {}
void func_0x0045d10e(void) {}
void func_0x0045d5f8(void) {}
void func_0x0045d482(void) {}
void func_0x0045d92a(void) {}
void func_0x0045dab9(void) {}
void func_0x0045db21(void) {}
void func_0x0045dbba(void) {}
void func_0x0000023b(void) {}
void func_0x012eb116(void) {}

HWND E2R_CreateWindowExA(DWORD exStyle, ...) {
    va_list ap;
    LPCSTR className;
    LPCSTR windowName;
    DWORD style;
    int x, y, width, height;
    HWND parent;
    HMENU menu;
    HINSTANCE instance;
    LPVOID param;

    va_start(ap, exStyle);
    className = va_arg(ap, LPCSTR);
    windowName = va_arg(ap, LPCSTR);
    style = va_arg(ap, DWORD);
    x = va_arg(ap, int);
    y = va_arg(ap, int);
    width = va_arg(ap, int);
    height = va_arg(ap, int);
    parent = va_arg(ap, HWND);
    menu = va_arg(ap, HMENU);
    instance = va_arg(ap, HINSTANCE);
    param = va_arg(ap, LPVOID);
    va_end(ap);

    return CreateWindowExA(exStyle, className, windowName, style, x, y, width, height, parent, menu, instance, param);
}

INT_PTR E2R_DialogBoxParamA(HINSTANCE inst, LPCSTR tmpl, HWND parent, DLGPROC proc, LPARAM param) {
    return DialogBoxParamA(inst, tmpl, parent, proc, param);
}

static void *E2R_dd_obj[64];
static void *E2R_surf_obj[64];
static void *E2R_ds_obj[64];
static void *E2R_dsbuf_obj[64];

static int E2R_DD_Generic(void) { return 0; }
static int E2R_DD_CreateSurface(void *self, void *desc, void **out, void *outer) {
    (void)self; (void)desc; (void)outer;
    if (out) *out = E2R_surf_obj;
    return 0;
}
static int E2R_DS_CreateSoundBuffer(void) {
    _DAT_00ac4eb8 = (uintptr_t)E2R_dsbuf_obj;
    return 0;
}

HRESULT DirectDrawCreate(void *guid, void **ddraw, void *outer) {
    int i;
    (void)guid;
    (void)outer;
    for (i = 0; i < 64; i++) {
        E2R_dd_obj[i] = (void *)E2R_DD_Generic;
        E2R_surf_obj[i] = (void *)E2R_DD_Generic;
    }
    E2R_dd_obj[0] = E2R_dd_obj;
    E2R_surf_obj[0] = E2R_surf_obj;
    E2R_dd_obj[6] = (void *)E2R_DD_CreateSurface;
    if (ddraw) *ddraw = E2R_dd_obj;
    return 0;
}

HRESULT DirectSoundCreate(void) {
    int i;
    for (i = 0; i < 64; i++) {
        E2R_ds_obj[i] = (void *)E2R_DD_Generic;
        E2R_dsbuf_obj[i] = (void *)E2R_DD_Generic;
    }
    E2R_ds_obj[0] = E2R_ds_obj;
    E2R_dsbuf_obj[0] = E2R_dsbuf_obj;
    E2R_ds_obj[3] = (void *)E2R_DS_CreateSoundBuffer;
    DAT_0047d1f0 = (uintptr_t)E2R_ds_obj;
    return 0;
}

int acmMetrics(void) {
    return 0;
}

short SIMD_InitDriver(unsigned int flags, GUID *guid, short device) {
    (void)flags; (void)guid; (void)device;
    return 0;
}

short SIMD_PlayTune(char *path, short mode) {
    (void)path; (void)mode;
    return 0;
}

short SIMD_StopTune(void) {
    return 0;
}

short SIMD_RemoveDriver(void) {
    return 0;
}
