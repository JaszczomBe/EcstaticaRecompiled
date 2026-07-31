#include "E2Recomp_recon.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

#undef CreateWindowExA
#undef DialogBoxParamA

uintptr_t E2R_timer_slots[8];
uintptr_t E2R_input_probe_keydown_count;
uintptr_t E2R_input_probe_last_key;
uintptr_t E2R_input_probe_last_char_queue;
uintptr_t E2R_input_probe_last_scan_queue;
uintptr_t E2R_requester_probe_ce58_count;
uintptr_t E2R_requester_probe_last_id;
uintptr_t E2R_requester_probe_last_mode;
uintptr_t E2R_requester_probe_b384_count;
uintptr_t E2R_requester_probe_b384_bad_ptr_count;
uintptr_t E2R_requester_probe_b384_last_ptr;
uintptr_t E2R_requester_probe_b9bc_count;
uintptr_t E2R_requester_probe_b9bc_last_item;
uintptr_t E2R_requester_probe_bd4c_count;
uintptr_t E2R_requester_probe_bd4c_last_key;
uintptr_t E2R_requester_probe_bd4c_seen_key_count;
uintptr_t E2R_requester_probe_bd4c_no_key_count;
uintptr_t E2R_requester_probe_bd4c_last_cursor;
uintptr_t E2R_requester_probe_bd4c_param_item;
uintptr_t E2R_requester_probe_selected_item;
uintptr_t E2R_requester_probe_selected_next;
uintptr_t E2R_requester_probe_selected_action;
uintptr_t E2R_requester_probe_move_count;
uintptr_t E2R_requester_probe_move_key;
uintptr_t E2R_requester_probe_move_from;
uintptr_t E2R_requester_probe_move_to;
uintptr_t E2R_requester_probe_pending_key_count;
uintptr_t E2R_requester_probe_pending_key_read;
uintptr_t E2R_requester_probe_fed_key_count;
uintptr_t E2R_requester_probe_last_fed_key;
uintptr_t E2R_requester_probe_last_fed_char;
uintptr_t E2R_requester_probe_last_fed_scan;
uintptr_t E2R_requester_probe_action_count;
uintptr_t E2R_requester_probe_last_action;
uintptr_t E2R_start_game_probe_count;
uintptr_t E2R_start_game_probe_last_player;
uintptr_t E2R_start_game_probe_last_mode;
uintptr_t E2R_start_code_probe_startup_scans;
uintptr_t E2R_start_code_probe_startup_matches;
uintptr_t E2R_start_code_probe_action_scans;
uintptr_t E2R_start_code_probe_action_matches;
uintptr_t E2R_start_code_probe_dispatches;
uintptr_t E2R_start_code_probe_last_node;
uintptr_t E2R_start_code_probe_last_name_index;
uintptr_t E2R_start_code_probe_last_bytecode_offset;
uintptr_t E2R_action_opcode_count;
uintptr_t E2R_action_last_opcode;
uintptr_t E2R_action_last_cursor;
uintptr_t E2R_action_hit_75_count;
static uintptr_t E2R_requester_probe_pending_keys[16];

static int E2R_game_input_log_initialized;
static int E2R_game_input_log_enabled;
static unsigned E2R_game_input_log_count;

static int E2R_GameInputLogEnabled(void) {
    if (!E2R_game_input_log_initialized) {
        const char *value = getenv("E2R_GAME_STATE_LOG");
#ifndef NDEBUG
        E2R_game_input_log_enabled =
            value == NULL || value[0] == '\0' || value[0] != '0';
#else
        E2R_game_input_log_enabled =
            value != NULL && value[0] != '\0' && value[0] != '0';
#endif
        E2R_game_input_log_initialized = 1;
    }
    return E2R_game_input_log_enabled;
}

static const char *E2R_KeyName(WPARAM key) {
    switch ((unsigned)key) {
    case VK_ESCAPE: return "Escape";
    case VK_SPACE: return "Space";
    case VK_RETURN: return "Return";
    default: return "Other";
    }
}

static void E2R_LogGameInputFlag(const char *site, WPARAM key) {
    if (!E2R_GameInputLogEnabled() || E2R_game_input_log_count >= 256) {
        return;
    }
    E2R_game_input_log_count++;
    fprintf(stderr,
            "game input: %s key=%s vk=0x%lx esc=%u space=%u mode=%lu requester=%lu scene=0x%lx\n",
            site, E2R_KeyName(key), (unsigned long)key,
            (unsigned)(byte)DAT_00636844, (unsigned)(byte)DAT_00636850,
            (unsigned long)DAT_00479de8, (unsigned long)_DAT_00643650,
            (unsigned long)_DAT_0073cc3c);
}

static void E2R_LogGameInputEvent(const char *site, UINT msg, WPARAM key, LPARAM lParam) {
    if (!E2R_GameInputLogEnabled() || E2R_game_input_log_count >= 256) {
        return;
    }
    E2R_game_input_log_count++;
    fprintf(stderr,
            "game input: %s msg=0x%x key=%s vk=0x%lx lparam=0x%lx esc=%u space=%u mode=%lu requester=%lu scene=0x%lx\n",
            site, (unsigned)msg, E2R_KeyName(key), (unsigned long)key, (unsigned long)lParam,
            (unsigned)(byte)DAT_00636844, (unsigned)(byte)DAT_00636850,
            (unsigned long)DAT_00479de8, (unsigned long)_DAT_00643650,
            (unsigned long)_DAT_0073cc3c);
}

static unsigned char *E2R_legacy_queue(unsigned address) {
    return (unsigned char *)(uintptr_t)address;
}

static unsigned E2R_virtual_key_to_scan(WPARAM key) {
    switch ((unsigned)key) {
    case VK_ESCAPE: return 0x01;
    case 0x08: return 0x0e;
    case VK_RETURN: return 0x1c;
    case VK_SPACE: return 0x39;
    case 0x11: return 0x1d;
    case 0x41: return 0x1e;
    case 0x43: return 0x2e;
    case 0x44: return 0x20;
    case 0x4d: return 0x32;
    case 0x50: return 0x19;
    case VK_Q: return 0x10;
    case 0x57: return 0x11;
    case 0x58: return 0x2d;
    case 0x5a: return 0x2c;
    case 0x61: return 0x4f;
    case 0x62: return 0x50;
    case 0x63: return 0x51;
    case 0x64: return 0x4b;
    case 0x65: return 0x4c;
    case 0x66: return 0x4d;
    case 0x67: return 0x47;
    case 0x68: return 0x48;
    case 0x69: return 0x49;
    case 0x70: return 0x3b;
    case 0x71: return 0x3c;
    case 0x72: return 0x3d;
    case 0x73: return 0x3e;
    case 0x74: return 0x3f;
    case 0x75: return 0x40;
    case 0x76: return 0x41;
    case 0x77: return 0x42;
    case 0x78: return 0x43;
    case 0x79: return 0x44;
    case 0x7a: return 0x57;
    case 0x7b: return 0x58;
    default:
        break;
    }
    return 0;
}

static unsigned E2R_virtual_key_to_char_queue(WPARAM key) {
    unsigned value = (unsigned)key & 0xffu;

    if (value == 0x08 || value == VK_RETURN || value == VK_ESCAPE || value == VK_SPACE) {
        return value;
    }
    if (value >= 0x30 && value <= 0x5a) {
        return value;
    }
    return 0;
}

static void E2R_feed_legacy_keydown(WPARAM key, LPARAM lParam) {
    unsigned scan = ((unsigned)lParam >> 16) & 0x7fu;
    unsigned is_extended = (((unsigned)lParam >> 24) & 1u) != 0;
    unsigned char_key;

    if (scan == 0) {
        scan = E2R_virtual_key_to_scan(key);
    }
    if (scan != 0) {
        if (is_extended) {
            E2R_legacy_queue(0x00507490)[scan] = 1;
            E2R_legacy_queue(0x004c3a90)[scan] = 1;
        }
        else {
            E2R_legacy_queue(0x004c3b90)[scan] = 1;
            E2R_legacy_queue(0x004c3990)[scan] = 1;
        }
        if (key >= 0x61 && key <= 0x69) {
            E2R_legacy_queue(0x00507490)[scan] = 1;
            E2R_legacy_queue(0x004c3a90)[scan] = 1;
        }
        E2R_input_probe_last_scan_queue = scan;
    }

    char_key = E2R_virtual_key_to_char_queue(key);
    if (char_key != 0) {
        E2R_legacy_queue(0x004c3890)[char_key] = 1;
        E2R_input_probe_last_char_queue = char_key;
    }
}

void E2R_RequesterProbeQueueKey(uintptr_t key) {
    if (E2R_requester_probe_pending_key_count - E2R_requester_probe_pending_key_read >= 16) {
        return;
    }
    E2R_requester_probe_pending_keys[E2R_requester_probe_pending_key_count & 15u] = key;
    E2R_requester_probe_pending_key_count++;
}

void E2R_RequesterProbeFeedPendingKey(void) {
    uintptr_t key;
    uintptr_t char_key;
    uintptr_t scan;

    if (E2R_requester_probe_pending_key_read == E2R_requester_probe_pending_key_count) {
        return;
    }
    key = E2R_requester_probe_pending_keys[E2R_requester_probe_pending_key_read & 15u];
    E2R_requester_probe_pending_key_read++;
    E2R_requester_probe_fed_key_count++;
    E2R_requester_probe_last_fed_key = key;
    char_key = E2R_virtual_key_to_char_queue((WPARAM)key);
    scan = E2R_virtual_key_to_scan((WPARAM)key);
    E2R_requester_probe_last_fed_char = char_key;
    E2R_requester_probe_last_fed_scan = scan;
    E2R_feed_legacy_keydown((WPARAM)key, 0);
}

static void E2R_feed_legacy_keyup(WPARAM key, LPARAM lParam) {
    unsigned scan = ((unsigned)lParam >> 16) & 0x7fu;
    unsigned is_extended = (((unsigned)lParam >> 24) & 1u) != 0;

    if (scan == 0) {
        scan = E2R_virtual_key_to_scan(key);
    }
    if (scan == 0) {
        return;
    }
    if (is_extended) {
        E2R_legacy_queue(0x004c3a90)[scan] = 0;
    }
    else {
        E2R_legacy_queue(0x004c3b90)[scan] = 0;
    }
}

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
    if (msg == WM_KEYDOWN) {
        E2R_LogGameInputEvent("wndproc.keydown.enter", msg, wParam, lParam);
        E2R_input_probe_keydown_count++;
        E2R_input_probe_last_key = wParam;
        E2R_feed_legacy_keydown(wParam, lParam);
        E2R_LogGameInputEvent("wndproc.keydown.after_legacy", msg, wParam, lParam);
        switch (wParam) {
        case 0x11:
            if (DAT_00479dfc == 0) {
                DAT_00636852 = 1;
            }
            return 0;
        case VK_ESCAPE:
            DAT_00636844 = 1;
            E2R_LogGameInputFlag("wndproc.set_escape", wParam);
            return 0;
        case VK_SPACE:
            DAT_00636850 = 1;
            E2R_LogGameInputFlag("wndproc.set_space", wParam);
            return 0;
        case 0x41:
            DAT_00636845 = 1;
            return 0;
        case 0x43:
            DAT_0063684f = 1;
            return 0;
        case 0x44:
            DAT_00636849 = 1;
            return 0;
        case 0x4d:
            DAT_0063684b = 1;
            return 0;
        case 0x50:
            DAT_00636847 = 1;
            return 0;
        case VK_Q:
            DAT_00636853 = 1;
            return 0;
        case 0x57:
            DAT_00636851 = 1;
            return 0;
        case 0x58:
            if (DAT_00479dfc != 0) {
                DAT_0063684a = 1;
            }
            return 0;
        case 0x5a:
            if (DAT_00479dfc != 0) {
                DAT_00636852 = 1;
            }
            DAT_00636846 = 1;
            return 0;
        case 0x61:
            DAT_0063685c = 1;
            return 0;
        case 0x62:
            DAT_0063685a = 1;
            return 0;
        case 0x63:
            DAT_00636855 = 1;
            return 0;
        case 0x64:
            DAT_00636854 = 1;
            return 0;
        case 0x65:
        case 0x66:
            DAT_00636856 = 1;
            return 0;
        case 0x67:
        case 0x68:
            DAT_00636859 = 1;
            return 0;
        case 0x69:
            DAT_0063685b = 1;
            return 0;
        case 0x70:
        case 0x71:
        case 0x72:
        case 0x73:
            DAT_0063684d = 1;
            return 0;
        case 0x74:
        case 0x75:
        case 0x76:
        case 0x77:
            DAT_00636848 = 1;
            return 0;
        case 0x78:
        case 0x79:
        case 0x7a:
        case 0x7b:
            DAT_0063684c = 1;
            return 0;
        default:
            break;
        }
    }
    if (msg == WM_CHAR) {
        unsigned char_key = (unsigned)wParam & 0xffu;
        if (char_key != 0) {
            E2R_legacy_queue(0x004c3890)[char_key] = 1;
            E2R_input_probe_last_char_queue = char_key;
        }
        return 0;
    }
    if (msg == WM_KEYUP) {
        E2R_feed_legacy_keyup(wParam, lParam);
        return 0;
    }
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
static void *E2R_palette_obj[16];
static void *E2R_ds_obj[64];
static void *E2R_dsbuf_obj[64];
uint32_t E2R_active_palette[256];
uintptr_t E2R_active_palette_valid;
uintptr_t E2R_active_palette_update_count;

static int E2R_DD_Generic(void) { return 0; }

static void E2R_DD_CopyPaletteEntries(const void *entries, unsigned start, unsigned count) {
    const unsigned char *src = (const unsigned char *)entries;
    unsigned i;

    if (entries == NULL || start >= 256u) {
        return;
    }
    if (count > 256u - start) {
        count = 256u - start;
    }
    if (count == 0 || IsBadReadPtr(entries, (UINT_PTR)count * 4u)) {
        return;
    }
    for (i = 0; i < count; i++) {
        E2R_active_palette[start + i] =
            ((uint32_t)src[i * 4u] << 16) |
            ((uint32_t)src[i * 4u + 1u] << 8) |
            (uint32_t)src[i * 4u + 2u];
    }
    E2R_active_palette_valid = 1;
    E2R_active_palette_update_count++;
}

static int E2R_DD_CreatePalette(void *self, unsigned int flags, void *entries, void **out, void *outer) {
    (void)self; (void)flags; (void)outer;
    E2R_DD_CopyPaletteEntries(entries, 0, 256);
    if (out) *out = E2R_palette_obj;
    return 0;
}
static int E2R_DD_CreateSurface(void *self, void *desc, void **out, void *outer) {
    (void)self; (void)desc; (void)outer;
    if (out) *out = E2R_surf_obj;
    return 0;
}
static int E2R_DDS_SetPalette(void *self, void *palette) {
    (void)self;
    if (palette == E2R_palette_obj && E2R_active_palette_update_count != 0) {
        E2R_active_palette_valid = 1;
    }
    return 0;
}
static int E2R_DDP_SetEntries(void *self, unsigned int flags, unsigned int start,
                              unsigned int count, void *entries) {
    (void)self; (void)flags;
    E2R_DD_CopyPaletteEntries(entries, start, count);
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
    for (i = 0; i < 16; i++) {
        E2R_palette_obj[i] = (void *)E2R_DD_Generic;
    }
    E2R_dd_obj[0] = E2R_dd_obj;
    E2R_surf_obj[0] = E2R_surf_obj;
    E2R_palette_obj[0] = E2R_palette_obj;
    E2R_dd_obj[5] = (void *)E2R_DD_CreatePalette;
    E2R_dd_obj[6] = (void *)E2R_DD_CreateSurface;
    E2R_surf_obj[31] = (void *)E2R_DDS_SetPalette;
    E2R_palette_obj[6] = (void *)E2R_DDP_SetEntries;
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
