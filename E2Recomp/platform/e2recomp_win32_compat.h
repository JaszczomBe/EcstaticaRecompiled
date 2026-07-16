#pragma once

#include <stddef.h>
#include <stdint.h>

#ifndef WINAPI
#define WINAPI
#endif

#ifndef CALLBACK
#define CALLBACK
#endif

#ifndef __stdcall
#define __stdcall
#endif

typedef struct E2R_HANDLE__ {
    int unused;
    void *ptr;
} E2R_HANDLE__;
typedef E2R_HANDLE__ *HANDLE;
typedef E2R_HANDLE__ *HWND;
typedef E2R_HANDLE__ *HINSTANCE;
typedef E2R_HANDLE__ *HMENU;
typedef E2R_HANDLE__ *HDC;
typedef E2R_HANDLE__ *HGDIOBJ;
typedef E2R_HANDLE__ *HICON;
typedef E2R_HANDLE__ *HCURSOR;
typedef E2R_HANDLE__ *HBRUSH;
typedef E2R_HANDLE__ *HMODULE;
typedef E2R_HANDLE__ *HGLOBAL;
typedef E2R_HANDLE__ *HLOCAL;
typedef E2R_HANDLE__ *HMMIO;
typedef const char *LPCSTR;
typedef char *LPSTR;
typedef char *HPSTR;
typedef const void *LPCVOID;
typedef void *LPVOID;
typedef uint8_t BYTE;
typedef char CHAR;
typedef uint16_t WCHAR;
typedef uint16_t WORD;
typedef uint32_t DWORD;
typedef uint32_t UINT;
typedef uintptr_t WPARAM;
typedef uintptr_t UINT_PTR;
typedef intptr_t LPARAM;
typedef intptr_t LRESULT;
typedef intptr_t INT_PTR;
typedef int32_t HRESULT;
typedef int32_t LONG;
typedef uint32_t MMRESULT;
typedef size_t SIZE_T;
typedef int BOOL;
typedef WORD *LPWORD;
typedef DWORD *LPDWORD;
typedef LONG *PLONG;
typedef void *LPSECURITY_ATTRIBUTES;
typedef void *LPOVERLAPPED;
typedef WORD ATOM;

void E2R_MapLegacyAddressSpace(void);
BOOL IsBadReadPtr(const void *ptr, UINT_PTR size);
BOOL E2R_IsBadWritePtr(const void *ptr, UINT_PTR size);

typedef struct _GUID {
    uint32_t Data1;
    uint16_t Data2;
    uint16_t Data3;
    uint8_t Data4[8];
} GUID;

typedef struct tagPOINT {
    LONG x;
    LONG y;
} POINT;

typedef struct tagSIZE {
    LONG cx;
    LONG cy;
} SIZE;

typedef struct tagMSG {
    HWND hwnd;
    UINT message;
    WPARAM wParam;
    LPARAM lParam;
    DWORD time;
    POINT pt;
} MSG;

typedef LRESULT (CALLBACK *WNDPROC)(HWND, UINT, WPARAM, LPARAM);
typedef void (CALLBACK *TIMERPROC)(HWND, UINT, UINT_PTR, DWORD);
typedef UINT_PTR (CALLBACK *LPOFNHOOKPROC)(HWND, UINT, WPARAM, LPARAM);

typedef struct tagWNDCLASSA {
    UINT style;
    WNDPROC lpfnWndProc;
    int cbClsExtra;
    int cbWndExtra;
    HINSTANCE hInstance;
    HICON hIcon;
    HCURSOR hCursor;
    HBRUSH hbrBackground;
    LPCSTR lpszMenuName;
    LPCSTR lpszClassName;
} WNDCLASSA;

typedef struct tagMIDIOUTCAPSA {
    WORD wMid;
    WORD wPid;
    uint32_t vDriverVersion;
    char szPname[32];
    WORD wTechnology;
    WORD wVoices;
    WORD wNotes;
    WORD wChannelMask;
    DWORD dwSupport;
} MIDIOUTCAPSA;
typedef MIDIOUTCAPSA *LPMIDIOUTCAPSA;

typedef struct tagOPENFILENAMEA {
    DWORD lStructSize;
    HWND hwndOwner;
    HINSTANCE hInstance;
    LPCSTR lpstrFilter;
    LPSTR lpstrCustomFilter;
    DWORD nMaxCustFilter;
    DWORD nFilterIndex;
    LPSTR lpstrFile;
    DWORD nMaxFile;
    LPSTR lpstrFileTitle;
    DWORD nMaxFileTitle;
    LPCSTR lpstrInitialDir;
    LPCSTR lpstrTitle;
    DWORD Flags;
    WORD nFileOffset;
    WORD nFileExtension;
    LPCSTR lpstrDefExt;
    LPARAM lCustData;
    LPOFNHOOKPROC lpfnHook;
    LPCSTR lpTemplateName;
} OPENFILENAMEA;
typedef OPENFILENAMEA *LPOPENFILENAMEA;

typedef struct _MMCKINFO {
    DWORD ckid;
    DWORD cksize;
    DWORD fccType;
    DWORD dwDataOffset;
    DWORD dwFlags;
} MMCKINFO;
typedef MMCKINFO *LPMMCKINFO;

typedef struct _MMIOINFO {
    DWORD dwFlags;
    DWORD fccIOProc;
    LPVOID pIOProc;
    UINT wErrorRet;
    void *htask;
    LONG cchBuffer;
    char *pchBuffer;
    char *pchNext;
    char *pchEndRead;
    char *pchEndWrite;
    LONG lBufOffset;
    LONG lDiskOffset;
    DWORD adwInfo[3];
    DWORD dwReserved1;
    DWORD dwReserved2;
    void *hmmio;
} MMIOINFO;
typedef MMIOINFO *LPMMIOINFO;

typedef struct _WIN32_FIND_DATAA {
    DWORD dwFileAttributes;
    uint64_t ftCreationTime;
    uint64_t ftLastAccessTime;
    uint64_t ftLastWriteTime;
    DWORD nFileSizeHigh;
    DWORD nFileSizeLow;
    DWORD dwReserved0;
    DWORD dwReserved1;
    char cFileName[260];
    char cAlternateFileName[14];
} WIN32_FIND_DATAA;
typedef WIN32_FIND_DATAA *LPWIN32_FIND_DATAA;

typedef struct _INPUT_RECORD {
    WORD EventType;
    union {
        struct {
            BOOL bKeyDown;
            WORD wRepeatCount;
            WORD wVirtualKeyCode;
            WORD wVirtualScanCode;
            union {
                char AsciiChar;
                WCHAR UnicodeChar;
            } uChar;
            DWORD dwControlKeyState;
        } KeyEvent;
        struct {
            DWORD dwMousePosition;
            DWORD dwButtonState;
            DWORD dwControlKeyState;
            DWORD dwEventFlags;
        } MouseEvent;
        BYTE Raw[32];
    } Event;
} INPUT_RECORD;

typedef struct _SYSTEMTIME {
    WORD wYear;
    WORD wMonth;
    WORD wDayOfWeek;
    WORD wDay;
    WORD wHour;
    WORD wMinute;
    WORD wSecond;
    WORD wMilliseconds;
} SYSTEMTIME;

typedef struct _TIME_ZONE_INFORMATION {
    LONG Bias;
    WCHAR StandardName[32];
    SYSTEMTIME StandardDate;
    LONG StandardBias;
    WCHAR DaylightName[32];
    SYSTEMTIME DaylightDate;
    LONG DaylightBias;
} TIME_ZONE_INFORMATION;
typedef TIME_ZONE_INFORMATION *LPTIME_ZONE_INFORMATION;

typedef struct _FILETIME {
    DWORD dwLowDateTime;
    DWORD dwHighDateTime;
} FILETIME;

typedef struct _EXCEPTION_RECORD {
    DWORD ExceptionCode;
    void *ExceptionAddress;
} EXCEPTION_RECORD;

typedef struct _CONTEXT {
    uintptr_t Eip;
    uintptr_t Esp;
    uintptr_t Eax;
    uintptr_t Ebx;
    uintptr_t Ecx;
    uintptr_t Edx;
} CONTEXT;

typedef struct _EXCEPTION_POINTERS {
    EXCEPTION_RECORD *ExceptionRecord;
    CONTEXT *ContextRecord;
} EXCEPTION_POINTERS;

typedef INT_PTR (CALLBACK *DLGPROC)(HWND, UINT, WPARAM, LPARAM);
typedef INT_PTR (WINAPI *FARPROC)();

#define TRUE 1
#define FALSE 0
#define NULL 0
#define INVALID_HANDLE_VALUE ((HANDLE)(intptr_t)-1)
#define E_FAIL ((HRESULT)0x80004005u)
#define WM_QUIT 0x0012
#define WM_DESTROY 0x0002
#define WM_KEYDOWN 0x0100
#define WM_KEYUP 0x0101
#define WM_CHAR 0x0102
#define PM_REMOVE 0x0001
#define VK_RETURN 0x0d
#define VK_ESCAPE 0x1b
#define VK_SPACE 0x20
#define VK_Q 0x51
#define GENERIC_WRITE 0x40000000u
#define FILE_SHARE_READ 0x00000001u
#define CREATE_ALWAYS 2u
#define FILE_ATTRIBUTE_NORMAL 0x00000080u
#define MEM_COMMIT 0x00001000u
#define MEM_RESERVE 0x00002000u
#define PAGE_READWRITE 0x04u
#define PAGE_EXECUTE_READWRITE 0x40u
#define EXCEPTION_EXECUTE_HANDLER 1

HANDLE CreateFileA(LPCSTR name, DWORD access, DWORD share, LPVOID security,
                   DWORD creation, DWORD flags, HANDLE template_file);
BOOL WriteFile(HANDLE file, LPCVOID buffer, DWORD bytes_to_write,
               DWORD *bytes_written, LPVOID overlapped);
BOOL CloseHandle(HANDLE file);
int wsprintfA(LPSTR buffer, LPCSTR format, ...);
int lstrlenA(LPCSTR value);
HMODULE GetModuleHandleA(LPCSTR name);
LPVOID VirtualAlloc(LPVOID address, size_t size, DWORD allocation_type, DWORD protect);
BOOL VirtualProtect(LPVOID address, size_t size, DWORD new_protect, DWORD *old_protect);
void *SetUnhandledExceptionFilter(void *filter);
BOOL IsWindow(HWND hwnd);
BOOL PeekMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter, UINT remove);
BOOL GetMessageA(MSG *msg, HWND hwnd, UINT min_filter, UINT max_filter);
BOOL TranslateMessage(const MSG *msg);
LRESULT DispatchMessageA(const MSG *msg);
void Sleep(DWORD milliseconds);
void PostQuitMessage(int exit_code);
BOOL PostMessageA(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam);
LRESULT DefWindowProcA(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam);
HWND CreateWindowExA(DWORD ex_style, LPCSTR class_name, LPCSTR window_name,
                     DWORD style, int x, int y, int width, int height,
                     HWND parent, HMENU menu, HINSTANCE instance, LPVOID param);
INT_PTR DialogBoxParamA(HINSTANCE inst, LPCSTR tmpl, HWND parent, DLGPROC proc,
                        LPARAM param);
HMODULE LoadLibraryA(LPCSTR name);
void *GetProcAddress(HMODULE module, LPCSTR name);
HICON LoadIconA(HINSTANCE instance, LPCSTR icon_name);
HCURSOR LoadCursorA(HINSTANCE instance, LPCSTR cursor_name);
HGDIOBJ GetStockObject(int object);
ATOM RegisterClassA(const WNDCLASSA *wnd_class);
UINT_PTR SetTimer(HWND hwnd, UINT_PTR id_event, UINT elapse, TIMERPROC timer_func);
BOOL KillTimer(HWND hwnd, UINT_PTR id_event);
BOOL GetOpenFileNameA(LPOPENFILENAMEA open_file_name);
int MessageBoxA(HWND hwnd, LPCSTR text, LPCSTR caption, UINT type);
HGLOBAL GlobalFree(HGLOBAL mem);
MMRESULT mmioClose(HMMIO mmio, UINT flags);
