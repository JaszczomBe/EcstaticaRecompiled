/*
 * Type shim for Ghidra's first-pass C output.
 *
 * This header is intentionally small. It makes the decompiler output easier to
 * inspect with normal C tooling, but it does not mean the dump is finished,
 * idiomatic, or ready to link as original source.
 */
#pragma once

#include <stdint.h>
#include <windows.h>

typedef uint8_t byte;
typedef uint8_t undefined;
typedef uint8_t undefined1;
typedef uint16_t undefined2;
typedef uint32_t undefined4;
typedef uint64_t undefined8;
typedef uint16_t word;
typedef uint32_t dword;
typedef uint64_t qword;
typedef uint32_t uint;
typedef uint16_t ushort;
typedef uint8_t uchar;
typedef uint64_t ulonglong;
typedef int64_t longlong;

#if !defined(_MSC_VER)
#ifndef __fastcall
#define __fastcall
#endif

#ifndef __cdecl
#define __cdecl
#endif

#ifndef __stdcall
#define __stdcall
#endif
#endif

/*
 * Ghidra sometimes emits CONCATxx helpers for register fragments. These are
 * placeholders for source cleanup; use the decompiler's listing to replace the
 * few surviving expressions with proper typed code during reconstruction.
 */
#define CONCAT11(a,b) ((uint16_t)((((uint16_t)(uint8_t)(a)) << 8) | (uint8_t)(b)))
#define CONCAT12(a,b) ((uint32_t)((((uint32_t)(uint8_t)(a)) << 16) | (uint16_t)(b)))
#define CONCAT13(a,b) ((uint32_t)((((uint32_t)(uint8_t)(a)) << 24) | ((uint32_t)(b) & 0x00ffffffu)))
#define CONCAT21(a,b) ((uint32_t)((((uint32_t)(uint16_t)(a)) << 8) | (uint8_t)(b)))
#define CONCAT22(a,b) ((uint32_t)((((uint32_t)(uint16_t)(a)) << 16) | (uint16_t)(b)))
#define CONCAT31(a,b) ((uint32_t)((((uint32_t)(a) & 0x00ffffffu) << 8) | (uint8_t)(b)))
#define CONCAT44(a,b) ((uint64_t)((((uint64_t)(uint32_t)(uintptr_t)(a)) << 32) | (uint32_t)(uintptr_t)(b)))
