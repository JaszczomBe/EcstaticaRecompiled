const fs = require("fs");
const path = require("path");

const workspaceRoot = process.argv[2] || "C:\\ecstatica2";
const repoLayoutRoot = path.join(workspaceRoot, "E2Recomp");
const root = fs.existsSync(path.join(repoLayoutRoot, "src", "E2Recomp_decompiled.c"))
  ? repoLayoutRoot
  : path.join(workspaceRoot, "reverse", "E2Recomp");
const srcPath = path.join(root, "src", "E2Recomp_decompiled.c");
const funcPath = path.join(root, "metadata", "functions.tsv");
const symPath = path.join(root, "metadata", "symbols.tsv");
const outDir = path.join(root, "reconstructed");
const outSrc = path.join(outDir, "E2Recomp_recon.c");
const outHdr = path.join(outDir, "E2Recomp_recon.h");
const outGlobals = path.join(outDir, "E2Recomp_globals.c");
const outRenames = path.join(outDir, "E2Recomp_names.tsv");

fs.mkdirSync(outDir, { recursive: true });

function readTsv(file) {
  const [head, ...rows] = fs.readFileSync(file, "utf8").trimEnd().split(/\r?\n/);
  const cols = head.split("\t");
  return rows.map((row) => {
    const values = row.split("\t");
    const out = {};
    cols.forEach((c, i) => (out[c] = values[i] || ""));
    return out;
  });
}

function escRe(s) {
  return s.replace(/[\\^$.*+?()[\]{}|]/g, "\\$&");
}

let source = fs.readFileSync(srcPath, "utf8");
const functions = readTsv(funcPath);
const symbols = readTsv(symPath);

const externalNames = new Set();
for (const s of symbols) {
  if (s.address.startsWith("EXTERNAL:") && s.type === "Function") {
    const leaf = s.name.split("::").pop();
    if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(leaf)) externalNames.add(leaf);
  }
}

for (const f of [...functions].sort((a, b) => parseInt(b.address, 16) - parseInt(a.address, 16))) {
  if (!externalNames.has(f.name)) continue;
  const pattern = new RegExp(`/\\*\\s*${f.address.toLowerCase()}\\s*\\*/\\s*(?:/\\*.*?\\*/\\s*)*.*?\\b${escRe(f.name)}\\s*\\([^;{}]*\\)\\s*\\{.*?^\\}`, "gms");
  source = source.replace(pattern, `/* ${f.address.toLowerCase()} import thunk ${f.name} removed; linked from system import library. */`);
}

source = source.replace(/\bstack0x([0-9a-fA-F]+)\b/g, "stack_$1");
source = source.replace(/\b([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\._0_([1248])_/g, "$1");
source = source.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\._([0-9]+)_([1248])_/g, "E2R_READ$3($1,$2)");

const valueUsed = new Set();
for (const m of source.matchAll(/(?:=\s*|\([A-Za-z_][A-Za-z0-9_\s*]*\)\s*|return\s+|if\s*\(\s*)(FUN_[0-9a-fA-F]+|thunk_FUN_[0-9a-fA-F]+)\s*\(/g)) {
  valueUsed.add(m[1]);
}
for (const name of valueUsed) {
  source = source.replace(new RegExp(`\\bvoid(\\s+(?:__fastcall|__cdecl|__stdcall)\\s+${escRe(name)}\\s*\\()`, "g"), "undefined4$1");
  source = source.replace(new RegExp(`\\bvoid(\\s+${escRe(name)}\\s*\\()`, "g"), "undefined4$1");
}

source = source.replace('#include "e2recomp_types.h"', '#include "E2Recomp_recon.h"');
source = source.replace(
  '#include "E2Recomp_recon.h"',
  '#include "E2Recomp_recon.h"\n#include <math.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#ifdef NAN\n#undef NAN\n#endif\n#define NAN(x) isnan((double)(x))\n\nstatic uint E2R_file_flags[256];\n#define E2R_STREAM_MAGIC 0xe25eed01u\n\nstatic int E2R_round_to_int(double value)\n{\n  return (int)(value < 0.0 ? value - 0.5 : value + 0.5);\n}\n\nstatic byte E2R_clamp_byte(int value)\n{\n  if (value < 0) {\n    return 0;\n  }\n  if (255 < value) {\n    return 255;\n  }\n  return (byte)value;\n}\n\nstatic short E2R_clamp_short(int value)\n{\n  if (value < -32768) {\n    return -32768;\n  }\n  if (32767 < value) {\n    return 32767;\n  }\n  return (short)value;\n}\n\nstatic undefined4 E2R_OpenReadStream(LPCSTR path)\n{\n  HANDLE file;\n  DWORD size;\n  DWORD bytes_read = 0;\n  char *buffer;\n  undefined4 *stream;\n\n  file = CreateFileA(path,0x80000000,3,(LPSECURITY_ATTRIBUTES)0x0,3,0x80,(HANDLE)0x0);\n  if (file == INVALID_HANDLE_VALUE) {\n    return 0;\n  }\n  size = SetFilePointer(file,0,(PLONG)0x0,2);\n  if (size == 0xffffffff) {\n    CloseHandle(file);\n    return 0;\n  }\n  SetFilePointer(file,0,(PLONG)0x0,0);\n  buffer = (char *)LocalAlloc(0x40,size == 0 ? 1 : size);\n  stream = (undefined4 *)LocalAlloc(0x40,0x1c);\n  if (buffer == (char *)0x0 || stream == (undefined4 *)0x0) {\n    if (buffer != (char *)0x0) {\n      LocalFree(buffer);\n    }\n    if (stream != (undefined4 *)0x0) {\n      LocalFree(stream);\n    }\n    CloseHandle(file);\n    return 0;\n  }\n  if (size != 0 && ReadFile(file,buffer,size,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    LocalFree(buffer);\n    LocalFree(stream);\n    CloseHandle(file);\n    return 0;\n  }\n  CloseHandle(file);\n  stream[0] = (undefined4)(uintptr_t)buffer;\n  stream[1] = (undefined4)bytes_read;\n  stream[2] = (undefined4)(uintptr_t)(buffer + bytes_read);\n  stream[3] = 0;\n  stream[4] = 0xffffffff;\n  stream[5] = (undefined4)(uintptr_t)buffer;\n  stream[6] = E2R_STREAM_MAGIC;\n  return (undefined4)(uintptr_t)stream;\n}\n\nstatic uint E2R_ReadOpenFileBytes(int descriptor,char *buffer,DWORD bytes_to_read)\n{\n  DWORD bytes_read = 0;\n  HANDLE file;\n  uint slot = (uint)descriptor;\n\n  if (_DAT_00ac51fc == 0 || _DAT_00ac51f8 <= slot) {\n    return 0xffffffff;\n  }\n  file = *(HANDLE *)(_DAT_00ac51fc + slot * 4);\n  if (file == (HANDLE)0x0 || file == INVALID_HANDLE_VALUE) {\n    return 0xffffffff;\n  }\n  if (ReadFile(file,buffer,bytes_to_read,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    return 0xffffffff;\n  }\n  return bytes_read;\n}\n'
);
source = source.replace(
  "#define NAN(x) isnan((double)(x))\n\nstatic uint E2R_file_flags",
  "#define NAN(x) isnan((double)(x))\n#ifndef __has_feature\n#define __has_feature(x) 0\n#endif\n\nstatic uint E2R_file_flags"
);
source = source.replace(
  "static uint E2R_file_flags[256];\n#define E2R_STREAM_MAGIC",
  "static uint E2R_file_flags[256];\nstatic uint E2R_open_diag_count;\nstatic uint E2R_archive_read_diag_count;\nstatic uint E2R_archive_resource_diag_count;\nstatic uint E2R_archive_parse_summary_count;\nstatic uint E2R_actor_load_diag_count;\nstatic int E2R_actor_load_id_override = -1;\nstatic int *E2R_fan_parse_stream;\nstatic short *E2R_fan_parse_record;\nstatic uint E2R_fan_parse_record_count;\nstatic uint E2R_fan_word_read_diag_count;\nstatic uint E2R_fan_action_read_diag_count;\nstatic uint E2R_fan_dispatch_diag_count;\nstatic uint E2R_fan_actor_diag_count;\nstatic uint E2R_fan_action_summary_diag_count;\nstatic uint E2R_fan_phase_diag_count;\nstatic uint E2R_actor_current_diag_count;\nstatic uint E2R_current_actor_trace_diag_count;\nstatic const char *E2R_current_actor_last_site;\nstatic uintptr_t E2R_current_actor_last_value;\nstatic int E2R_actor_calc_context;\n\nstatic void E2R_InitDiagnostics(void) __attribute__((constructor));\nstatic void E2R_InitDiagnostics(void)\n{\n  char *fan_diag = getenv(\"E2R_FAN_DIAG\");\n\n  if (fan_diag != (char *)0x0 && fan_diag[0] != '\\0' && fan_diag[0] != '0') {\n    return;\n  }\n\n  E2R_fan_word_read_diag_count = 0x7fffffff;\n  E2R_fan_action_read_diag_count = 0x7fffffff;\n  E2R_fan_dispatch_diag_count = 0x7fffffff;\n  E2R_fan_actor_diag_count = 0x7fffffff;\n  E2R_fan_action_summary_diag_count = 0x7fffffff;\n  E2R_fan_phase_diag_count = 0x7fffffff;\n}\n\nstatic uint E2R_FanStreamOffset(void)\n{\n  if (E2R_fan_parse_stream == (int *)0x0 || IsBadReadPtr(E2R_fan_parse_stream,0x1c)) {\n    return 0;\n  }\n  return (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                (byte *)(uintptr_t)E2R_fan_parse_stream[5]);\n}\n#define E2R_STREAM_MAGIC"
);
source = source.replace(
  "#define E2R_STREAM_MAGIC 0xe25eed01u\n\nstatic int E2R_round_to_int",
  "#define E2R_STREAM_MAGIC 0xe25eed01u\n\nstatic int E2R_IsKnownActorPointer(int actor)\n{\n  short actor_id;\n\n  if (actor == 0) {\n    return 1;\n  }\n  if ((uint)actor < 0x10000u || 0x70000000u <= (uint)actor ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x136)) {\n    return 0;\n  }\n  actor_id = *(short *)(uintptr_t)actor;\n  if (actor_id < 0 || 5000 <= actor_id) {\n    return 0;\n  }\n  return *(int *)((undefined1 *)0x00630b60 + actor_id * 4) == actor;\n}\n\nstatic int E2R_CurrentSceneTableSlot(uintptr_t value)\n{\n  uintptr_t offset;\n\n  if (value < (uintptr_t)0x0067c728 ||\n      (uintptr_t)(0x0067c728 + 0x4b0 * 0x1c) <= value) {\n    return -1;\n  }\n  offset = value - (uintptr_t)0x0067c728;\n  if (offset % 0x1c != 0) {\n    return -1;\n  }\n  return (int)(offset / 0x1c);\n}\n\nstatic int E2R_IsReadableCurrentPointer(uintptr_t value)\n{\n  return value != 0 && 0x10000u <= (uint)value && (uint)value < 0x70000000u &&\n         !IsBadReadPtr((void *)value,0xaa);\n}\n\nstatic void E2R_PrintCurrentPointerShape(const char *site, uintptr_t value)\n{\n  int readable;\n  short word0 = 0;\n  short word82 = 0;\n  int dword84 = 0;\n  int dworda6 = 0;\n\n  readable = E2R_IsReadableCurrentPointer(value);\n  if (readable) {\n    word0 = *(short *)value;\n    word82 = *(short *)(value + 0x82);\n    dword84 = *(int *)(value + 0x84);\n    dworda6 = *(int *)(value + 0xa6);\n  }\n  fprintf(stderr,\n          \"current pointer shape: site=%s value=0x%lx readable=%d \"\n          \"known_actor=%d scene=0x%lx eq_scene=%d scene_slot=%d \"\n          \"w0=%d w82=0x%x d84=0x%lx da6=0x%lx table0=0x%lx\\n\",\n          site,(unsigned long)value,readable,E2R_IsKnownActorPointer((int)value),\n          (unsigned long)_DAT_0073cc3c,value == (uintptr_t)_DAT_0073cc3c,\n          E2R_CurrentSceneTableSlot(value),(int)word0,(unsigned int)(ushort)word82,\n          (unsigned long)(uint)dword84,(unsigned long)(uint)dworda6,\n          (unsigned long)*(int *)0x00630b60);\n}\n\nstatic uintptr_t E2R_TraceCurrentActorWrite(const char *site, uintptr_t value)\n{\n  E2R_current_actor_last_site = site;\n  E2R_current_actor_last_value = value;\n  if (value != 0 && E2R_current_actor_trace_diag_count < 32 &&\n      (strcmp(site,\"5233c.archive\") == 0 || strcmp(site,\"525f0.archive\") == 0)) {\n    E2R_current_actor_trace_diag_count = E2R_current_actor_trace_diag_count + 1;\n    E2R_PrintCurrentPointerShape(site,value);\n  }\n  return value;\n}\n\nstatic uintptr_t E2R_TraceArchiveCurrentActorWrite(const char *site, uintptr_t value)\n{\n  if (value != 0 && !E2R_IsReadableCurrentPointer(value)) {\n    E2R_current_actor_last_site = site;\n    E2R_current_actor_last_value = 0;\n    if (E2R_current_actor_trace_diag_count < 32) {\n      E2R_current_actor_trace_diag_count = E2R_current_actor_trace_diag_count + 1;\n      E2R_PrintCurrentPointerShape(site,value);\n    }\n    return 0;\n  }\n  return E2R_TraceCurrentActorWrite(site,value);\n}\n\nstatic void E2R_SelectSceneRecord(short scene_id)\n{\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return;\n  }\n  _DAT_0073ccba = (ushort)scene_id;\n  FUN_0044c6bc();\n}\n\nstatic int E2R_round_to_int"
);
source = source.replace(
  "static undefined4 E2R_OpenReadStream(LPCSTR path)",
  "static int E2R_ReadHostedStreamByte(undefined4 *stream)\n{\n  byte *cursor;\n  int value;\n\n  if (stream == (undefined4 *)0x0 || IsBadReadPtr(stream,0x1c)) {\n    return -1;\n  }\n  if ((int)stream[1] < 1) {\n    *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x10;\n    return -1;\n  }\n  cursor = (byte *)(uintptr_t)stream[0];\n  value = (int)*cursor;\n  stream[0] = (undefined4)(uintptr_t)(cursor + 1);\n  stream[1] = stream[1] + -1;\n  if ((*(byte *)(stream + 3) & 0x40) == 0) {\n    if (value == '\\r') {\n      if ((int)stream[1] < 1) {\n        *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x10;\n        return -1;\n      }\n      cursor = (byte *)(uintptr_t)stream[0];\n      value = (int)*cursor;\n      stream[0] = (undefined4)(uintptr_t)(cursor + 1);\n      stream[1] = stream[1] + -1;\n    }\n    if (value == '\\x1a') {\n      *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x10;\n      return -1;\n    }\n  }\n  return value;\n}\n\nstatic int E2R_ReadFanWordByte(int *stream)\n{\n  byte *cursor;\n\n  if (stream == E2R_fan_parse_stream && stream != (int *)0x0 &&\n      (uint)stream[6] == E2R_STREAM_MAGIC) {\n    if (0 < stream[1] && ((*(byte *)(stream + 3) & 4) == 0)) {\n      cursor = (byte *)(uintptr_t)stream[0];\n      if (*cursor != '\\r' && *cursor != '\\x1a') {\n        stream[0] = (int)(uintptr_t)(cursor + 1);\n        stream[1] = stream[1] + -1;\n        return (int)*cursor;\n      }\n    }\n    return E2R_ReadHostedStreamByte((undefined4 *)stream);\n  }\n  if (stream == (int *)0x0 || IsBadReadPtr(stream,0x1c)) {\n    return -1;\n  }\n  if (0 < stream[1] && ((*(byte *)(stream + 3) & 4) == 0)) {\n    cursor = (byte *)(uintptr_t)stream[0];\n    if (!IsBadReadPtr(cursor,1) && *cursor != '\\r' && *cursor != '\\x1a') {\n      stream[0] = (int)(uintptr_t)(cursor + 1);\n      stream[1] = stream[1] + -1;\n      return (int)*cursor;\n    }\n  }\n  return E2R_ReadHostedStreamByte((undefined4 *)stream);\n}\n\nstatic undefined4 E2R_OpenReadStream(LPCSTR path)"
);
source = source.replace(
  "  file = CreateFileA(path,0x80000000,3,(LPSECURITY_ATTRIBUTES)0x0,3,0x80,(HANDLE)0x0);\n  if (file == INVALID_HANDLE_VALUE) {\n    return 0;\n  }",
  "  file = CreateFileA(path,0x80000000,3,(LPSECURITY_ATTRIBUTES)0x0,3,0x80,(HANDLE)0x0);\n  if (file == INVALID_HANDLE_VALUE) {\n    if (E2R_open_diag_count < 12) {\n      E2R_open_diag_count = E2R_open_diag_count + 1;\n      fprintf(stderr,\"E2R open failed: path=%s\\n\",path);\n    }\n    return 0;\n  }"
);
source = source.replace(
  "  size = SetFilePointer(file,0,(PLONG)0x0,2);\n  if (size == 0xffffffff) {\n    CloseHandle(file);\n    return 0;\n  }",
  "  size = SetFilePointer(file,0,(PLONG)0x0,2);\n  if (size == 0xffffffff) {\n    if (E2R_open_diag_count < 12) {\n      E2R_open_diag_count = E2R_open_diag_count + 1;\n      fprintf(stderr,\"E2R size failed: path=%s\\n\",path);\n    }\n    CloseHandle(file);\n    return 0;\n  }"
);
source = source.replace(
  "  if (buffer == (char *)0x0 || stream == (undefined4 *)0x0) {\n    if (buffer != (char *)0x0) {",
  "  if (buffer == (char *)0x0 || stream == (undefined4 *)0x0) {\n    if (E2R_open_diag_count < 12) {\n      E2R_open_diag_count = E2R_open_diag_count + 1;\n      fprintf(stderr,\"E2R alloc failed: path=%s size=%u buffer=%p stream=%p\\n\",\n              path,size,(void *)buffer,(void *)stream);\n    }\n    if (buffer != (char *)0x0) {"
);
source = source.replace(
  "  if (size != 0 && ReadFile(file,buffer,size,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    LocalFree(buffer);",
  "  if (size != 0 && ReadFile(file,buffer,size,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    if (E2R_open_diag_count < 12) {\n      E2R_open_diag_count = E2R_open_diag_count + 1;\n      fprintf(stderr,\"E2R read failed: path=%s size=%u read=%u\\n\",path,size,bytes_read);\n    }\n    LocalFree(buffer);"
);
source = source.replace("  stream[3] = 0;\n  stream[4] = 0xffffffff;", "  stream[3] = 0x41;\n  stream[4] = 0xffffffff;");

const protoMatches = source.matchAll(/^\s*((?:[A-Za-z_][A-Za-z0-9_]*\s+|[*]\s*)+[A-Za-z_][A-Za-z0-9_]*\s*\([^;{}]*?\))\s*\r?\n\s*\{/gms);
const prototypes = [];
const seenProto = new Set();
for (const m of protoMatches) {
  const proto = m[1].replace(/\s+/g, " ").trim();
  if (!/\b(FUN_[0-9a-fA-F]+|thunk_FUN_[0-9a-fA-F]+|entry|__[A-Za-z0-9_]+)\s*\(/.test(proto)) continue;
  if (/\b(DirectDrawCreate|DirectSoundCreate|CreateFileA|ExitProcess|timeGetTime)\s*\(/.test(proto)) continue;
  if (!seenProto.has(proto)) {
    seenProto.add(proto);
    prototypes.push(`${proto};`);
  }
}

const idPattern = /\b_?(?:DAT|PTR|s|u|UNK|FLOAT|DOUBLE|LAB)_[A-Za-z0-9_%]+_[0-9a-fA-F]{8}\b|\b_?DAT_[0-9a-fA-F]{8}\b|\bLAB_[0-9a-fA-F]{8}\b|\bPTR_[A-Za-z0-9_]+_[0-9a-fA-F]{8}\b|\b[A-Za-z]*Ram[0-9a-fA-F]{8}\b/g;
const ids = new Set();
for (const m of source.matchAll(idPattern)) {
  if (!m[0].startsWith("FUN_")) ids.add(m[0]);
}
const stackIds = new Set([...source.matchAll(/\bstack_[0-9a-fA-F]+\b/g)].map((m) => m[0]));

const nonStringId = /(?:_?(?:DAT|PTR|u|UNK|FLOAT|DOUBLE|LAB)_[A-Za-z0-9_%]+_[0-9a-fA-F]{8}|_?DAT_[0-9a-fA-F]{8}|LAB_[0-9a-fA-F]{8}|PTR_[A-Za-z0-9_]+_[0-9a-fA-F]{8}|[A-Za-z]*Ram[0-9a-fA-F]{8})/;
source = source.replace(new RegExp(`\\b(${nonStringId.source})\\s*\\[`, "g"), "((undefined4 *)(uintptr_t)$1)[");
source = source.replace(new RegExp(`(\\([A-Za-z_][A-Za-z0-9_\\s*]*\\))\\*\\s*(${nonStringId.source})\\b`, "g"), "$1*(undefined4 *)(uintptr_t)$2");
source = source.replace(new RegExp(`(^|[^A-Za-z0-9_\\]])\\*\\s*(${nonStringId.source})\\b`, "gm"), "$1*(undefined4 *)(uintptr_t)$2");
source = source.replace(/([A-Za-z0-9_\]])\s*\*\(undefined4 \*\)\(uintptr_t\)([A-Za-z_][A-Za-z0-9_]*)/g, "$1 * $2");
source = source.replace(/\*\(undefined4 \*\)\(uintptr_t\)_DAT_006401ec/g, "* _DAT_006401ec");
source = source.replace(/\*\(undefined4 \*\)\(uintptr_t\)DAT_0047a408/g, "* DAT_0047a408");
source = source.replace(/\bpcStack_28 \+ -1\b/g, "(code *)((uintptr_t)pcStack_28 - 1)");
source = source.replace(
  /(float10 __fastcall FUN_00465588\(uint param_1,undefined4 \*param_2\)[\s\S]*?)\n  undefined4 local_40;/,
  "$1\n  undefined4 *local_40;"
);
source = source.replace(
  /(undefined4 __fastcall FUN_0045fca7\(uint param_1,undefined4 param_2\)[\s\S]*?\n  uint uVar3;\n\s*)/,
  "$1\n  if (in_EAX == 0) return 0;\n"
);
source = source.replace(
  /(\n  uint uVar3;\n\s+)(if \(param_1 != 0\) \{)/,
  "$1if (in_EAX == 0) return 0;\n  $2"
);
source = source.replace(
  "undefined4 __fastcall FUN_0045fca7(uint param_1,undefined4 param_2)\r\n\r\n{\r\n  undefined4 *in_EAX;\r\n  undefined4 *puVar1;\r\n  int iVar2;\r\n  uint uVar3;\r\n  \r\n  if (param_1 != 0) {",
  "undefined4 __fastcall FUN_0045fca7(uint param_1,undefined4 param_2)\r\n\r\n{\r\n  undefined4 *in_EAX;\r\n  undefined4 *puVar1;\r\n  int iVar2;\r\n  uint uVar3;\r\n  \r\n  if (in_EAX == 0) return 0;\r\n  if (param_1 != 0) {"
);
source = source.replace(
  "undefined4 __fastcall FUN_0045fca7(uint param_1,undefined4 param_2)\n\n{\n  undefined4 *in_EAX;\n  undefined4 *puVar1;\n  int iVar2;\n  uint uVar3;\n  \n  if (param_1 != 0) {",
  "undefined4 __fastcall FUN_0045fca7(uint param_1,undefined4 param_2)\n\n{\n  undefined4 *in_EAX;\n  undefined4 *puVar1;\n  int iVar2;\n  uint uVar3;\n  \n  if (in_EAX == 0) return 0;\n  if (param_1 != 0) {"
);
source = source.replace(
  "undefined8 __fastcall FUN_00463a48(undefined4 param_1,undefined4 param_2)\n\n{\n  int in_EAX;\n  DWORD DVar1;\n  \n  if (in_EAX == 0) {",
  "undefined8 __fastcall FUN_00463a48(undefined4 param_1,undefined4 param_2)\n\n{\n  int in_EAX;\n  DWORD DVar1;\n  \n  in_EAX = 0;\n  if (in_EAX == 0) {"
);
source = source.replace(/(undefined8 __fastcall FUN_00463a48\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  DWORD DVar1;\r?\n\s*)if \(in_EAX == 0\) \{/, "$1in_EAX = 0;\n  if (in_EAX == 0) {");
source = source.replace("in_EAX = FUN_0045f1ff(param_1,DAT_0047d808);", "in_EAX = (int)LocalAlloc(0x40, DAT_0047d808 ? DAT_0047d808 : 0x1000);");
source = source.replace(/(longlong __fastcall FUN_00461a03\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  uint uVar2;\r?\n\s*)uVar1 = \*in_EAX/, "$1if (in_EAX == 0) return (ulonglong)param_2 << 0x20;\n  uVar1 = *in_EAX");
source = source.replace(/(int FUN_00464d20\(void\)[\s\S]*?\r?\n  int in_EAX;\r?\n\s*)return \(\*\(uint \*\)\(in_EAX \+ -4\)/, "$1if (in_EAX == 0) return 0;\n  return (*(uint *)(in_EAX + -4)");
source = source.replace(/(undefined4 __fastcall FUN_00464d63\(uint \*param_1,uint param_2\)[\s\S]*?\r?\n  short in_DS;\r?\n\s*)uVar3 = unaff_EBX/, "$1if (param_2 < 0x10000) return 1;\n  uVar3 = unaff_EBX");
source = source.replace(
  /undefined4 __fastcall FUN_00464d63\(uint \*param_1,uint param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00464f19 \*\//,
  "undefined4 __fastcall FUN_00464d63(uint *param_1,uint param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return 1;\n}\n\n\n\n/* 00464f19 */"
);
source = source.replace(
  /undefined4 __fastcall FUN_0045fca7\(uint param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fd13 \*\//,
  "undefined4 __fastcall FUN_0045fca7(uint param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return 0;\n}\n\n\n\n/* 0045fd13 */"
);
source = source.replace(
  /void __fastcall FUN_0045fc70\(uint param_1,uint param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fca7 \*\//,
  "void __fastcall FUN_0045fc70(uint param_1,uint param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return;\n}\n\n\n\n/* 0045fca7 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_004603d1\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004604e6 \*\//,
  "undefined8 __fastcall FUN_004603d1(undefined4 param_1,undefined4 param_2)\n\n{\n  uint uVar1;\n  HANDLE hFile;\n  \n  hFile = (HANDLE)(uintptr_t)param_1;\n  if (_DAT_00ac51fc == 0) {\n    _DAT_00ac51fc = (uintptr_t)LocalAlloc(0x40,DAT_0047d610 * 4);\n    _DAT_00ac51f8 = DAT_0047d610;\n  }\n  if (_DAT_00ac51fc == 0) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  for (uVar1 = 0; uVar1 < _DAT_00ac51f8; uVar1 = uVar1 + 1) {\n    if (*(HANDLE *)(_DAT_00ac51fc + uVar1 * 4) == (HANDLE)0x0) {\n      *(HANDLE *)(_DAT_00ac51fc + uVar1 * 4) = hFile;\n      return CONCAT44(param_2,uVar1);\n    }\n  }\n  return CONCAT44(param_2,0xffffffff);\n}\n\n\n\n/* 004604e6 */"
);
source = source.replace(
  /void __fastcall FUN_004604e6\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0046050e \*\//,
  "void __fastcall FUN_004604e6(undefined4 param_1,undefined4 param_2)\n\n{\n  uint slot;\n\n  (void)param_2;\n  slot = (uint)(uintptr_t)param_1;\n  if (_DAT_00ac51fc != 0 && slot < _DAT_00ac51f8) {\n    *(undefined4 *)(_DAT_00ac51fc + slot * 4) = 0;\n  }\n  return;\n}\n\n\n\n/* 0046050e */"
);
source = source.replace(/(undefined8 __fastcall FUN_0045f0d1\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar7;\r?\n\s*)if \(\(in_EAX != 0\)/, "$1in_EAX = (uint)(uintptr_t)param_1;\n  if ((in_EAX != 0)");
source = source.replace(/(undefined4 FUN_00458714\(void\)[\s\S]*?\r?\n  WNDCLASSA local_3c;\r?\n\s*)local_3c.style = 3;/, "$1in_EAX = GetModuleHandleA((LPCSTR)0x0);\n  local_3c.style = 3;");
source = source.replace("local_3c.lpfnWndProc = (WNDPROC)&LAB_00458110;", "local_3c.lpfnWndProc = (WNDPROC)E2R_WndProc;");
source = source.replace(/(void FUN_004594a0\(void\)[\s\S]*?\r?\n  SIZE_T local_1c;\r?\n\s*)_DAT_00ac4fc4 = 0;/, "$1in_EAX = _DAT_00ac4dac;\n  _DAT_00ac4fc4 = 0;");
source = source.replace(/(void FUN_004594a0\(void\)[\s\S]*?\r?\n\s*)in_EAX = _DAT_00ac4dac;\r?\n\s*_DAT_00ac4fc4 = 0;/, "$1in_EAX = _DAT_00ac4dac;\n  local_1c = 0x12;\n  _DAT_00ac4fc4 = 0;");
source = source.replace(
  /undefined8 __fastcall FUN_0045fa43\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fa88 \*\//,
  "undefined8 __fastcall FUN_0045fa43(undefined4 param_1,undefined4 param_2)\n\n{\n  char *src = (char *)(uintptr_t)param_1;\n  char *dst;\n  uint len = 0;\n  if ((uintptr_t)src < 0x10000 || (uintptr_t)src > 0x7fffffff) return (ulonglong)param_2 << 32;\n  while (src[len] != 0) len++;\n  len++;\n  dst = (char *)LocalAlloc(0x40, len);\n  if (dst != (char *)0x0) {\n    uint i;\n    for (i = 0; i < len; i++) dst[i] = src[i];\n  }\n  return CONCAT44(param_2,dst);\n}\n\n\n\n/* 0045fa88 */"
);
source = source.replace("  FUN_004605bc(extraout_ECX,&local_20);\n  FUN_004605e8(extraout_ECX_00,&local_24);", "  FUN_004605bc(uVar6,&local_20);\n  FUN_004605e8(uVar6,&local_24);");
source = source.replace(
  "    uVar7 = (*(code *)PTR_thunk_FUN_004603d1_0047d3a8)();\n    uVar1 = (undefined4)uVar7;\n    lVar8 = FUN_00460803(extraout_ECX_06,(uint)((ulonglong)uVar7 >> 0x20));",
  "    uVar7 = FUN_004603d1((undefined4)(uintptr_t)pvVar3,param_2);\n    uVar1 = (undefined4)uVar7;\n    lVar8 = FUN_00460803(uVar1,uVar1);"
);
source = source.replace(
  "  FUN_00460899(CONCAT22((short)((uint)uVar4 >> 0x10),CONCAT11(E2R_READ1(param_4,1),(char)uVar4)),uVar5);",
  "  FUN_00460899(uVar1,uVar5);"
);
source = source.replace(
  "  (*(code *)PTR_FUN_0047d3a0)();\n  uVar1 = FUN_004608e8(extraout_ECX,extraout_EDX);\n  (*(code *)PTR_FUN_0047d3a4)();\n  (*(code *)PTR_thunk_FUN_004604e6_0047d3ac)();\n  return CONCAT44(param_2,(int)uVar1);",
  "  uVar1 = FUN_004608e8(param_1,param_2);\n  FUN_004604e6(param_1,param_2);\n  return CONCAT44(param_2,(int)uVar1);"
);
source = source.replace(/(void __fastcall FUN_004605bc\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  undefined4 \*unaff_EBX;\r?\n\s*)if \(in_EAX == 2\) \{/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 2) {");
source = source.replace("      *unaff_EBX = 1;\n      return;", "      if (unaff_EBX != (undefined4 *)0x0 && !E2R_IsBadWritePtr(unaff_EBX,4)) {\n        *unaff_EBX = 1;\n      }\n      return;");
source = source.replace("  *unaff_EBX = 0x80;\n  return;\n}\n\n\n\n/* 004605e8 */", "  if (unaff_EBX != (undefined4 *)0x0 && !E2R_IsBadWritePtr(unaff_EBX,4)) {\n    *unaff_EBX = 0x80;\n  }\n  return;\n}\n\n\n\n/* 004605e8 */");
source = source.replace(/(void __fastcall FUN_004605e8\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  int in_EAX;\r?\n\s*)if \(\(in_EAX == 0\)/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if ((in_EAX == 0)");
source = source.replace(
  /(longlong __fastcall FUN_00460803\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  DWORD DVar1;\r?\n  HANDLE hFile;\r?\n\s*)\(\*\(code \*\)PTR_FUN_0047d3a0\)\(param_2,param_1\);/,
  "$1uint uVar2;\n  \n  uVar2 = (uint)(uintptr_t)param_2;\n  if ((_DAT_00ac51fc == 0) || (_DAT_00ac51f8 <= uVar2)) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  hFile = *(HANDLE *)(_DAT_00ac51fc + uVar2 * 4);\n  (*(code *)PTR_FUN_0047d3a0)(param_2,param_1);"
);
source = source.replace("  (*(code *)PTR_FUN_0047d3a0)(param_2,param_1);\n  DVar1 = GetFileType(hFile);", "  DVar1 = GetFileType(hFile);");
source = source.replace("    (*(code *)PTR_FUN_0047d3a4)();\n    return CONCAT44(param_2,1);\n  }\n  (*(code *)PTR_FUN_0047d3a4)();", "    return CONCAT44(param_2,1);\n  }");
source = source.replace(
  /longlong __fastcall FUN_00460844\(undefined4 param_1,uint param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00460899 \*\//,
  "longlong __fastcall FUN_00460844(undefined4 param_1,uint param_2)\n\n{\n  uint slot;\n  longlong lVar4;\n  \n  slot = (uint)(uintptr_t)param_1;\n  if (256 <= slot) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  if (slot < 4) {\n    if ((E2R_file_flags[slot] & 0x40) == 0) {\n      E2R_file_flags[slot] = E2R_file_flags[slot] | 0x4000;\n      lVar4 = FUN_00460803(slot,slot);\n      if ((int)lVar4 != 0) {\n        E2R_file_flags[slot] = E2R_file_flags[slot] | 0x20;\n      }\n    }\n  }\n  return CONCAT44(param_2,E2R_file_flags[slot]);\n}\n\n\n\n/* 00460899 */"
);
source = source.replace(
  /(void __fastcall FUN_00460899\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n\s*)int in_EAX;\r?\n\s*\r?\n  \*\(uint \*\)\(PTR_DAT_0047d664 \+ in_EAX \* 4\) = param_2 \| 0x4000;\r?\n  return;/,
  "$1uint in_EAX;\n  \n  in_EAX = (uint)(uintptr_t)param_1;\n  if (in_EAX < 256) {\n    E2R_file_flags[in_EAX] = param_2 | 0x4000;\n  }\n  return;"
);
source = source.replace(
  /(undefined8 __fastcall FUN_004608e8\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined4 uVar4;\r?\n\s*\r?\n  iVar3 = 0;\r?\n\s*)hObject = \*\(HANDLE \*\)\(_DAT_00ac51fc \+ in_EAX \* 4\);/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  if ((_DAT_00ac51fc == 0) || (in_EAX < 0) || (_DAT_00ac51f8 <= (uint)in_EAX)) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  hObject = *(HANDLE *)(_DAT_00ac51fc + in_EAX * 4);"
);
source = source.replace(
  /void FUN_0045f9b5\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fa43 \*\//,
  "void FUN_0045f9b5(void)\n\n{\n  return;\n}\n\n\n\n/* 0045fa43 */"
);
source = source.replace(
  /void __fastcall FUN_00459440\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004594a0 \*\//,
  "void __fastcall FUN_00459440(undefined4 param_1,undefined4 param_2)\n\n{\n  char local_status[256];\n  undefined4 local_caps[24];\n  \n  (void)param_1;\n  (void)param_2;\n  local_caps[0] = 0x60;\n  if (DAT_0047d1f0 != 0) {\n    (**(code **)(*(undefined4 *)(uintptr_t)DAT_0047d1f0 + 0x10))();\n  }\n  wsprintfA(local_status,(LPCSTR)&DAT_004766c0,s_Ecstatica_II_0047d141);\n  SendMessageA(DAT_0047d150,0xc,0,(LPARAM)local_status);\n  return;\n}\n\n\n\n/* 004594a0 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00457fe0\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00458094 \*\//,
  "undefined8 __fastcall FUN_00457fe0(undefined4 param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  return CONCAT44(param_2,1);\n}\n\n\n\n/* 00458094 */"
);
source = source.replace(
  /(void __fastcall FUN_00415d40\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  bool bVar3;\r?\n\s*)undefined8 uVar4;/,
  "$1int requester_id;\n  undefined8 uVar4;"
);
source = source.replace(
  "    DAT_0047a788 = 1;\n    DAT_00636844 = '\\0';\n    _DAT_00643650 = 5;\n    if (DAT_00479db4 != 0) {\n      param_1 = 0;\n      DAT_00479db4 = 0;\n    }\n    uVar4 = FUN_0043ce58(param_1,5);",
  "    DAT_0047a788 = 1;\n    DAT_00636844 = '\\0';\n    _DAT_00643650 = 5;\n    requester_id = 0x28;\n    if (DAT_00479db4 != 0) {\n      requester_id = 0x27;\n      param_1 = 0;\n      DAT_00479db4 = 0;\n    }\n    uVar4 = FUN_0043ce58(requester_id,5);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0043ce58\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  short sStack_1c;\r?\n\s*)E2R_WORD_AT\(DAT_0047a45e,2\) = \(ushort\)in_EAX;/,
  "$1in_EAX = (uint)(uintptr_t)param_1;\n  E2R_requester_probe_ce58_count++;\n  E2R_requester_probe_last_id = in_EAX;\n  E2R_requester_probe_last_mode = (uintptr_t)param_2;\n  E2R_WORD_AT(DAT_0047a45e,2) = (ushort)in_EAX;"
);
source = source.replace(
  "        DAT_00643ae0 = DAT_00643ae0 | 0x80;\n        DAT_00643ae1 = DAT_00643ae1 & 0xdf;\n        uVar13 = FUN_0043b384(param_1,in_EAX);",
  "        DAT_00643ae0 = DAT_00643ae0 | 0x80;\n        DAT_00643ae1 = DAT_00643ae1 & 0xdf;\n        E2R_InitRequesterMainMenuItems();\n        E2R_InitRequesterRecord(0x0047a588,-1,-1,0xd2,0xb4,0,0x00643b30);\n        uVar13 = FUN_0043b384(param_1,in_EAX);"
);
source = source.replace(
  "void __fastcall FUN_0043a39c(undefined4 param_1,undefined4 param_2)\n\n{",
  "void __fastcall FUN_0043a39c(undefined4 param_1,undefined4 param_2)\n\n{\n  E2R_start_game_probe_count++;\n  E2R_start_game_probe_last_player = _DAT_0047a4dc;\n  E2R_start_game_probe_last_mode = (uintptr_t)param_2;"
);
source = source.replace(
  "  undefined8 uVar7;\n\n  E2R_start_game_probe_count++;",
  "  undefined8 uVar7;\n  uint action_guard;\n\n  E2R_start_game_probe_count++;"
);
source = source.replace(
  "  undefined8 uVar7;\n\n  DAT_0047a34a = 0;",
  "  undefined8 uVar7;\n  uint action_guard;\n\n  DAT_0047a34a = 0;"
);
{
  const functionStart = source.indexOf("void __fastcall FUN_0043a39c(undefined4 param_1,undefined4 param_2)");
  const functionEnd = source.indexOf("\n\n\n/* 0043a6e0 */",functionStart);
  let functionSource = source.slice(functionStart,functionEnd);

  functionSource = functionSource.replace(
    /(  undefined8 uVar7;\r?\n)(\s*DAT_0047a34a = 0;)/,
    "$1  uint action_guard;\n\n$2"
  );
  functionSource = functionSource.replace(
    /  pcVar4 = extraout_ECX_02;\r?\n  uVar6 = extraout_EDX_01;[\s\S]*?(?=  _DAT_0073cc3c = 0;)/,
    "  iVar1 = _DAT_00637250;\n  if (DAT_00479e1c == 0) {\n    for (action_guard = 0; iVar1 != 0 && action_guard < 0x4000 &&\n         !IsBadReadPtr((void *)(uintptr_t)iVar1,0xe);\n         action_guard = action_guard + 1, iVar1 = *(int *)(iVar1 + 10)) {\n      E2R_start_code_probe_startup_scans++;\n      if (E2R_ActionCodeMatches((short *)(uintptr_t)iVar1,s_StartUp_004725ec)) {\n        E2R_start_code_probe_startup_matches++;\n        E2R_InvokeActionCode((short *)(uintptr_t)iVar1);\n      }\n    }\n  }\n"
  );
  functionSource = functionSource.replace(
    /  do \{\r?\n    if \(iVar1 == 0\) \{[\s\S]*?  \} while\( true \);/,
    "  action_guard = 0;\n  while (iVar1 != 0 && action_guard < 0x4000 &&\n         !IsBadReadPtr((void *)(uintptr_t)iVar1,0xe)) {\n    char *action_name = E2R_ActionCodeName((short *)(uintptr_t)iVar1);\n    int prefix_matches = 1;\n\n    E2R_start_code_probe_action_scans++;\n    action_guard = action_guard + 1;\n    if (DAT_00479e20 != 0 && action_name != (char *)0x0) {\n      if (DAT_00479d74 == 0) {\n        prefix_matches = strncmp(action_name,\"___\",3) == 0;\n      }\n      else {\n        char prefix[4];\n        prefix[0] = (char)DAT_00479d74;\n        prefix[1] = (char)(DAT_00479d74 >> 8);\n        prefix[2] = (char)(DAT_00479d74 >> 16);\n        prefix[3] = '\\0';\n        prefix_matches = strncmp(action_name,prefix,3) == 0;\n      }\n    }\n    if (prefix_matches && E2R_ActionCodeMatches((short *)(uintptr_t)iVar1,pcVar4)) {\n      E2R_start_code_probe_action_matches++;\n      E2R_InvokeActionCode((short *)(uintptr_t)iVar1);\n      break;\n    }\n    iVar1 = *(int *)(iVar1 + 10);\n  }\n  if (iVar1 != 0) {\n    iVar1 = 0;\n  }\n  if (iVar1 == 0) {\n    short *action = E2R_FindActionCodeBySuffix(pcVar4);\n    if (action != (short *)0x0) {\n      iVar1 = (int)(uintptr_t)action;\n      E2R_start_code_probe_action_matches++;\n      E2R_InvokeActionCode(action);\n    }\n  }\n  if (iVar1 == 0) {\n    uVar7 = FUN_0043cbb4(pcVar4);\n    uVar6 = (undefined4)((ulonglong)uVar7 >> 0x20);\n    pcVar4 = extraout_ECX_19;\n  }\n  FUN_0041af88(pcVar4,uVar6);\n  uVar6 = extraout_EDX_16;\n  if ((DAT_0047a43c != 0) && (DAT_0047a440 == 0)) {\n    FUN_0043acec();\n    uVar6 = extraout_EDX_17;\n  }\n  if ((DAT_0047a43c == 0) && (DAT_0047a440 != 0)) {\n    FUN_0043ac60();\n    uVar6 = extraout_EDX_18;\n  }\n  FUN_0041af88(0x96,uVar6);\n  FUN_0045fc70(extraout_ECX_20,0);\n  if (_DAT_0073cc3c == 0 && E2R_start_game_probe_last_mode == 0) {\n    E2R_SelectSceneRecord(785);\n  }\n  DAT_0047ab28 = 100;\n  DAT_0047ab18 = 0;\n  DAT_0047ab14 = 0;\n  DAT_0047a7ec = 0;\n  return;"
  );
  source = source.slice(0,functionStart) + functionSource + source.slice(functionEnd);
}
source = source.replace(
  /(void __fastcall FUN_0044f508\(ushort \*param_1,ushort \*param_2,ushort \*param_3\)[\s\S]*?\r?\n  undefined2 uVar21;\r?\n\s*)local_34 = 0xffffffff;/,
  "$1if (E2R_action_dispatch_node != (short *)0x0) {\n    in_EAX = (int)(uintptr_t)E2R_action_dispatch_node;\n  }\n  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xe)) {\n    return;\n  }\n  \n  local_34 = 0xffffffff;"
);
source = source.replace(
  "      uVar25 = CONCAT44(puVar18,_DAT_00ac4a54);\n      switch((int)(uintptr_t)((short)*local_2c)) {",
  "      uVar25 = CONCAT44(puVar18,_DAT_00ac4a54);\n      E2R_action_opcode_count++;\n      E2R_action_last_opcode = (ushort)sVar9;\n      E2R_action_last_cursor = (uintptr_t)local_2c;\n      if ((ushort)sVar9 == 0x75) {\n        E2R_action_hit_75_count++;\n      }\n      switch((int)(uintptr_t)((short)*local_2c)) {"
);
source = source.replace(
  "  in_EAX = (short *)(uintptr_t)param_1;\n  if (IsBadReadPtr(in_EAX,0x40) || (uintptr_t)in_EAX >= 0x70000000u) return (ulonglong)param_2 << 32;\n  DAT_0047a788 = 1;",
  "  in_EAX = (short *)(uintptr_t)param_1;\n  E2R_requester_probe_b384_count++;\n  E2R_requester_probe_b384_last_ptr = (uintptr_t)in_EAX;\n  if (IsBadReadPtr(in_EAX,0x40) || (uintptr_t)in_EAX >= 0x70000000u) {\n    E2R_requester_probe_b384_bad_ptr_count++;\n    in_EAX = (short *)FUN_0043aeac();\n    E2R_requester_probe_b384_last_ptr = (uintptr_t)in_EAX;\n    if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,0x40) || (uintptr_t)in_EAX >= 0x70000000u) {\n      return (ulonglong)param_2 << 32;\n    }\n  }\n  param_1 = (undefined4)(uintptr_t)in_EAX;\n  DAT_0047a788 = 1;"
);
source = source.replace(
  "  byte local_14 [4];\n  \n  sVar8 = 0;\n  if (*(int *)(param_2 + 4) != 0) {",
  "  byte local_14 [4];\n  \n  E2R_requester_probe_b9bc_count++;\n  E2R_requester_probe_b9bc_last_item = (uintptr_t)param_2;\n  in_EAX = (int)(uintptr_t)FUN_0043aeac();\n  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x20)) {\n    in_EAX = (int)(uintptr_t)param_1;\n  }\n  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x20) ||\n      param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {\n    return param_1;\n  }\n  sVar8 = 0;\n  if (*(int *)(param_2 + 4) != 0) {"
);
source = source.replace(
  "  undefined4 local_18;\n  \n  sVar7 = 0;",
  "  undefined4 local_18;\n  \n  E2R_requester_probe_bd4c_count++;\n  E2R_requester_probe_bd4c_last_cursor = (uintptr_t)_DAT_00643428;\n  in_EAX = (int)(uintptr_t)FUN_0043aeac();\n  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x20)) {\n    return param_1;\n  }\n  if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {\n    param_2 = (short *)(uintptr_t)_DAT_00643430;\n    if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {\n      param_2 = (short *)E2R_requester_probe_b9bc_last_item;\n      if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {\n        return param_1;\n      }\n    }\n  }\n  E2R_requester_probe_bd4c_param_item = (uintptr_t)param_2;\n  E2R_requester_probe_selected_item = (uintptr_t)_DAT_00643430;\n  E2R_requester_probe_selected_next = 0;\n  E2R_requester_probe_selected_action = 0;\n  if (_DAT_00643430 != (short *)0x0 && (uintptr_t)_DAT_00643430 < 0x70000000u &&\n      !IsBadReadPtr(_DAT_00643430,0x20)) {\n    E2R_requester_probe_selected_next = *(uintptr_t *)(_DAT_00643430 + 9);\n    E2R_requester_probe_selected_action = *(uintptr_t *)(_DAT_00643430 + 6);\n  }\n  E2R_RequesterProbeFeedPendingKey();\n  sVar7 = 0;"
);
source = source.replace(
  "  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x20)) {\n    return param_1;\n  }\n  if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {",
  "  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x20)) {\n    return param_1;\n  }\n  if (_DAT_00643430 == (short *)0x0 || (uintptr_t)_DAT_00643430 >= 0x70000000u ||\n      IsBadReadPtr(_DAT_00643430,0x20)) {\n    psVar2 = E2R_RequesterFirstSelectable(*(short **)(in_EAX + 0xc));\n    if (psVar2 != (short *)0x0) {\n      _DAT_00643430 = psVar2;\n      _DAT_00643428 = (short *)0x0;\n      param_2 = psVar2;\n    }\n  }\n  if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {"
);
source = source.replace(
  "      param_2 = (short *)E2R_requester_probe_b9bc_last_item;\n      if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {\n        return param_1;\n      }\n",
  "      param_2 = E2R_RequesterFirstSelectable(*(short **)(in_EAX + 0xc));\n      if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {\n        param_2 = (short *)E2R_requester_probe_b9bc_last_item;\n        if (param_2 == (short *)0x0 || (uintptr_t)param_2 >= 0x70000000u || IsBadReadPtr(param_2,0x20)) {\n          return param_1;\n        }\n      }\n      else {\n        _DAT_00643430 = param_2;\n        _DAT_00643428 = (short *)0x0;\n      }\n"
);
source = source.replace(
  "    E2R_requester_probe_selected_next = *(uintptr_t *)(_DAT_00643430 + 9);\n    E2R_requester_probe_selected_action = *(uintptr_t *)(_DAT_00643430 + 6);",
  "    E2R_requester_probe_selected_next = *(uintptr_t *)((short *)(uintptr_t)_DAT_00643430 + 9);\n    E2R_requester_probe_selected_action = *(uintptr_t *)((short *)(uintptr_t)_DAT_00643430 + 6);"
);
source = source.replace(/\*\(char \*\*\)\(_DAT_00643430 \+ 4\)/g,
                        "*(char **)((short *)(uintptr_t)_DAT_00643430 + 4)");
source = source.replace(
  "            _DAT_00643430 = psVar2;\n            FUN_0043b9bc(psVar10,param_2);",
  "            E2R_requester_probe_move_count++;\n            E2R_requester_probe_move_key = (ushort)(short)local_18;\n            E2R_requester_probe_move_from = (uintptr_t)param_2;\n            E2R_requester_probe_move_to = (uintptr_t)psVar2;\n            _DAT_00643430 = psVar2;\n            FUN_0043b9bc(psVar10,param_2);"
);
source = source.replace(
  "        _DAT_00643430 = psVar2;\n        FUN_0043b9bc(psVar10,param_2);",
  "        E2R_requester_probe_move_count++;\n        E2R_requester_probe_move_key = (ushort)(short)local_18;\n        E2R_requester_probe_move_from = (uintptr_t)param_2;\n        E2R_requester_probe_move_to = (uintptr_t)psVar2;\n        _DAT_00643430 = psVar2;\n        FUN_0043b9bc(psVar10,param_2);"
);
source = source.replace(
  "    sVar7 = (short)local_18;\n    if (sVar7 == 0) {",
  "    sVar7 = (short)local_18;\n    E2R_requester_probe_bd4c_last_key = (ushort)sVar7;\n    if (sVar7 != 0) {\n      E2R_requester_probe_bd4c_seen_key_count++;\n    }\n    if (sVar7 == 0) {"
);
source = source.replace(
  "          local_18 = (short *)CONCAT22(uVar12,sVar7);\n          ((undefined1 *)0x00507490)[sVar7] = 0;\n          psVar10 = (short *)CONCAT22(uVar12,uVar8);",
  "          local_18 = (short *)CONCAT22(uVar12,sVar7);\n          ((undefined1 *)0x00507490)[sVar7] = 0;\n          E2R_requester_probe_bd4c_last_key = (ushort)sVar7;\n          E2R_requester_probe_bd4c_seen_key_count++;\n          psVar10 = (short *)CONCAT22(uVar12,uVar8);"
);
source = source.replace(
  "      if (*(int *)(param_2 + 6) != 0) {\n        (**(code **)(param_2 + 6))();\n        uVar11 = extraout_ECX_02;\n        _DAT_00643430 = extraout_EDX;\n      }",
  "      if (*(int *)(param_2 + 6) != 0) {\n        E2R_requester_probe_action_count++;\n        E2R_requester_probe_last_action = *(uintptr_t *)(param_2 + 6);\n        E2R_InvokeRequesterAction(E2R_requester_probe_last_action);\n        FUN_0041cfc0();\n        return;\n      }"
);
source = source.replace(
  "  }\n  FUN_0041cfc0();\n  return;\ncode_r0x0043bf38:",
  "  }\n  else {\n    E2R_requester_probe_bd4c_no_key_count++;\n  }\n  FUN_0041cfc0();\n  return;\ncode_r0x0043bf38:"
);
source = source.replace(/(void __fastcall FUN_00460557\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)\*\(int \*\)\(\(int\)uVar1 \+ 4\) = \(int\)\(\(ulonglong\)uVar1 >> 0x20\);/, "$1if ((int)uVar1 != 0) {\n    *(int *)((int)uVar1 + 4) = (int)((ulonglong)uVar1 >> 0x20);\n  }");
source = source.replace(/(void __fastcall FUN_0046055c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)\*\(int \*\)\(\(int\)uVar1 \+ 4\) = \(int\)\(\(ulonglong\)uVar1 >> 0x20\);/, "$1if ((int)uVar1 != 0) {\n    *(int *)((int)uVar1 + 4) = (int)((ulonglong)uVar1 >> 0x20);\n  }");
source = source.replace(/(void __fastcall FUN_00460581\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)\*\(int \*\)\(\(int\)uVar1 \+ 8\) = \(int\)\(\(ulonglong\)uVar1 >> 0x20\);/, "$1if ((int)uVar1 != 0) {\n    *(int *)((int)uVar1 + 8) = (int)((ulonglong)uVar1 >> 0x20);\n  }");
source = source.replace(/(void __fastcall FUN_00458bec\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar2;\r?\n\s*)piVar1 = \*\(int \*\*\)\(in_EAX \+ 0x38\);/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x3c)) return;\n  piVar1 = *(int **)(in_EAX + 0x38);");
source = source.replace(
  "      FUN_00458bec(param_1,iVar1);\n      param_1 = extraout_ECX;\n      iVar1 = extraout_EDX;",
  "      FUN_00458bec((undefined4)(0x0073ccbc + iVar1),iVar1);"
);
source = source.replace(
  "    uVar2 = (**(code **)(*piVar1 + 0x48))(piVar1,param_2,param_1);",
  "    uVar2 = (**(code **)(*piVar1 + 0x48))(piVar1);"
);
source = source.replace(
  "  do {\n    FUN_004537bc(param_1);\n    param_1 = extraout_ECX_00;\n  } while (extraout_EDX_00 != 0x73fb9c);",
  "  (void)extraout_ECX_00;\n  (void)extraout_EDX_00;"
);
source = source.replace("    FUN_00420b8c();\n    iVar2 = iVar2 + 2;", "    FUN_00420b8c(iVar2 / 2);\n    iVar2 = iVar2 + 2;");
source = source.replace("  } while (extraout_EDX < 5000);", "  } while (iVar2 != 5000);");
source = source.replace("void FUN_00420b8c(void)\n\n{\n  int iVar1;\n  byte bVar2;\n  int in_EAX;", "void FUN_00420b8c(int in_EAX)\n\n{\n  int iVar1;\n  byte bVar2;");
source = source.replace("  int iVar4;\n  \n  bVar2 = (&DAT_0064a178)[in_EAX * 2];", "  int iVar4;\n  \n  if (in_EAX < 0 || 2500 <= in_EAX) return;\n  bVar2 = (&DAT_0064a178)[in_EAX * 2];");
source = source.replace("  FUN_00420b8c();\n  if (*(int *)(&DAT_00630b60 + extraout_EDX * 4) != 0) {", "  FUN_00420b8c(extraout_EDX);\n  if (*(int *)(&DAT_00630b60 + extraout_EDX * 4) != 0) {");
source = source.replace(
  /void __fastcall FUN_0045f22f\(undefined4 param_1,char \*param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045f254 \*\//,
  "void __fastcall FUN_0045f22f(undefined4 param_1,char *param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return;\n}\n\n\n\n/* 0045f254 */"
);
source = source.replace(
  /(?:\/\* WARNING: Removing unreachable block \(ram,0x0045f322\) \*\/\s*)?undefined4 __fastcall FUN_0045f296\(undefined4 param_1,int param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045f38a \*\//,
  "undefined4 __fastcall FUN_0045f296(undefined4 param_1,int param_2)\n\n{\n  undefined4 *stream;\n  byte *base;\n  byte *end;\n  byte *cursor;\n\n  stream = (undefined4 *)(uintptr_t)param_1;\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      stream[6] != E2R_STREAM_MAGIC) {\n    stream = (undefined4 *)(uintptr_t)DAT_0047a724;\n  }\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      stream[6] != E2R_STREAM_MAGIC) {\n    return 0xffffffff;\n  }\n  base = (byte *)(uintptr_t)stream[5];\n  end = (byte *)(uintptr_t)stream[2];\n  if (param_2 < 0 || end < base || (uint)(end - base) < (uint)param_2) {\n    *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x10;\n    return 0xffffffff;\n  }\n  cursor = base + param_2;\n  stream[0] = (undefined4)(uintptr_t)cursor;\n  stream[1] = (undefined4)(uint)(end - cursor);\n  *(byte *)(stream + 3) = *(byte *)(stream + 3) & 0xef;\n  return 0;\n}\n\n\n\n/* 0045f38a */"
);
source = source.replace(/(undefined4 __fastcall FUN_0041af88\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  int iVar2;\r?\n\s*)iVar2 = 0;/, "$1in_EAX = (char *)(uintptr_t)param_1;\n  if ((uintptr_t)in_EAX < 0x10000u || (uintptr_t)in_EAX >= 0x01000000u ||\n      IsBadReadPtr(in_EAX,0x300)) return 0;\n  iVar2 = 0;");
source = source.replace(/&DAT_006366c0/g, "&_DAT_006366c0");
source = source.replace(/(undefined4 __fastcall FUN_00418a04\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  int extraout_ECX;\r?\n\s*)if \(1 < in_EAX\) \{/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (1 < in_EAX) {");
source = source.replace(
  "  if (1 < in_EAX) {\n    *param_2 = _DAT_006401ec;\n    return *(undefined4 *)(&DAT_00636150 + in_EAX * 4);\n  }",
  "  if (1 < in_EAX) {\n    *param_2 = _DAT_006401ec;\n    if (in_EAX == 2) {\n      return _DAT_00636158;\n    }\n    if (in_EAX == 3) {\n      return _DAT_0063615c;\n    }\n    return *(undefined4 *)(&DAT_00636150 + in_EAX * 4);\n  }"
);
source = source.replace(
  /void __fastcall FUN_0041ad54\(undefined4 param_1,int param_2,int param_3\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0041af88 \*\//,
  "void __fastcall FUN_0041ad54(undefined4 param_1,int param_2,int param_3)\n\n{\n  int x;\n  int y;\n  int x2;\n  int y1;\n  int pitch;\n  int base;\n  int surface;\n  undefined1 color;\n  undefined1 *row;\n  \n  x2 = (int)(uintptr_t)param_1;\n  y1 = 0;\n  surface = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (param_2 < 0) {\n    param_2 = 0;\n  }\n  if (x2 >= _DAT_006401ec) {\n    x2 = _DAT_006401ec + -1;\n  }\n  if (param_3 >= _DAT_006401d4) {\n    param_3 = _DAT_006401d4 + -1;\n  }\n  if (x2 < param_2 || param_3 < y1) {\n    return;\n  }\n  base = FUN_00418a04((undefined4)(uintptr_t)surface,&pitch);\n  if (base == 0 || pitch <= 0 || (uintptr_t)base >= 0x70000000u ||\n      _DAT_006401ec <= 0 || 0x1000 < _DAT_006401ec ||\n      _DAT_006401d4 <= 0 || 0x1000 < _DAT_006401d4) {\n    return;\n  }\n  color = ((undefined1 *)0x006366dc)[surface * 2];\n  for (y = y1; y <= param_3; y = y + 1) {\n    row = (undefined1 *)(base + y * pitch + param_2);\n    for (x = param_2; x <= x2; x = x + 1) {\n      *row = color;\n      row = row + 1;\n    }\n  }\n  return;\n}\n\n\n\n/* 0041af88 */"
);
source = source.replace(
  /\/\* 0041b078 \*\/[\s\S]*?\r?\n\s*\r?\n\/\* 0041b920 \*\//,
  "/* 0041b078 */\n\nvoid __fastcall FUN_0041b078(undefined4 param_1,undefined2 param_2)\n\n{\n  int surface;\n  \n  surface = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (surface < 0 || 3 < surface) {\n    return;\n  }\n  *(undefined2 *)(0x006366c4 + surface * 2) = (undefined2)(uintptr_t)param_1;\n  *(undefined2 *)(0x006366d0 + surface * 2) = param_2;\n  return;\n}\n\n\n\n/* 0041b34c */\n\nvoid __fastcall FUN_0041b34c(undefined4 param_1,int param_2)\n\n{\n  int base;\n  int color_index;\n  int dx;\n  int dy;\n  int e2;\n  int err;\n  int pitch;\n  int sx;\n  int sy;\n  int surface;\n  int x0;\n  int x1;\n  int y0;\n  int y1;\n  undefined1 *pixel;\n  undefined1 color;\n  \n  surface = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (surface < 0 || 3 < surface) {\n    return;\n  }\n  x0 = (short)*(undefined2 *)(0x006366c4 + surface * 2);\n  y0 = (short)*(undefined2 *)(0x006366d0 + surface * 2);\n  x1 = (short)(uintptr_t)param_1;\n  y1 = (short)param_2;\n  *(undefined2 *)(0x006366c4 + surface * 2) = (undefined2)x1;\n  *(undefined2 *)(0x006366d0 + surface * 2) = (undefined2)y1;\n  base = FUN_00418a04((undefined4)(uintptr_t)surface,&pitch);\n  if (base == 0 || pitch <= 0 || _DAT_006401ec <= 0 || _DAT_006401d4 <= 0) {\n    return;\n  }\n  dx = x1 - x0;\n  if (dx < 0) {\n    dx = -dx;\n  }\n  dy = y1 - y0;\n  if (dy < 0) {\n    dy = -dy;\n  }\n  sx = x0 < x1 ? 1 : -1;\n  sy = y0 < y1 ? 1 : -1;\n  err = dx - dy;\n  color_index = surface * 2;\n  color = ((undefined1 *)0x006366dc)[color_index];\n  while (1) {\n    if (0 <= x0 && x0 < _DAT_006401ec && 0 <= y0 && y0 < _DAT_006401d4) {\n      pixel = (undefined1 *)(base + y0 * pitch + x0);\n      if (*(short *)(0x006366a8 + color_index) == 0) {\n        *pixel = *pixel ^ color;\n      }\n      else {\n        *pixel = color;\n      }\n    }\n    if (x0 == x1 && y0 == y1) {\n      break;\n    }\n    e2 = err * 2;\n    if (-dy < e2) {\n      err = err - dy;\n      x0 = x0 + sx;\n    }\n    if (e2 < dx) {\n      err = err + dx;\n      y0 = y0 + sy;\n    }\n  }\n  return;\n}\n\n\n\n/* 0041b540 */\n\nvoid __fastcall FUN_0041b540(undefined4 param_1,int param_2)\n\n{\n  FUN_0041b34c(param_1,param_2);\n  return;\n}\n\n\n\n/* 0041b920 */"
);
source = source.replace(
  /(int __fastcall FUN_00419af4\(int param_1,byte \*param_2,undefined4 param_3,int param_4\)[\s\S]*?\r?\n  undefined1 local_10;\r?\n\s*)pbVar5 = \(undefined1 \*\)0x00477068;/,
  "$1in_EAX = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    in_EAX = in_EAX + 2;\n  }\n  pbVar5 = (undefined1 *)0x00477068;"
);
source = source.replace(
  /(int __fastcall FUN_00419af4\(int param_1,byte \*param_2,undefined4 param_3,int param_4\)[\s\S]*?\r?\n  undefined1 local_10;\r?\n\s*)pbVar5 = \(undefined1 \*\)0x00477068;/,
  "$1in_EAX = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    in_EAX = in_EAX + 2;\n  }\n  pbVar5 = (undefined1 *)0x00477068;"
);
source = source.replace(
  "    local_80 = FUN_00418a04(pbVar5,&local_84);\n    local_14 = ((undefined1 *)0x006366dc)[in_EAX * 2];",
  "    local_80 = FUN_00418a04((undefined4)(uintptr_t)in_EAX,&local_84);\n    if (local_80 == 0 || local_84 <= 0) {\n      return 0;\n    }\n    local_14 = ((undefined1 *)0x006366dc)[in_EAX * 2];"
);
source = source.replace(
  /\/\* 00453920 \*\/\s*\r?\n\s*\/\* WARNING:[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\s*\/\* 004544a4 \*\//,
  "/* 00453920 */\n\nundefined8 __fastcall FUN_00453920(undefined4 param_1,char *param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return 0;\n}\n\n\n\n/* 004544a4 */"
);
source = source.replace(
  /\/\* 00455e84 \*\/\s*\r?\n\s*void FUN_00455e84\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\s*\/\* 00455fe8 \*\//,
  "/* 00455e84 */\n\nvoid FUN_00455e84(void)\n\n{\n  if (DAT_0047a43c == 0) {\n    E2R_ClearHudIconName((char *)0x00475ef8);\n    E2R_ClearHudIconName((char *)0x00475f00);\n    E2R_ClearHudIconName((char *)0x00475f08);\n    E2R_ClearHudIconName((char *)0x00475f2c);\n    E2R_ClearHudIconName((char *)0x00475f20);\n    E2R_ClearHudIconName((char *)0x00475f6c);\n    E2R_ClearHudIconName((char *)0x00475f64);\n    E2R_ClearHudIconNameRange(0x0047ab71,0x0047ab9e);\n    E2R_ClearHudIconName((char *)0x00475f5c);\n    E2R_ClearHudIconName((char *)0x00475e4c);\n    E2R_ClearHudIconNameRange(0x0047ac40,0x0047ac76);\n    E2R_ClearHudIconNameRange(0x0047ac76,0x0047acac);\n    E2R_ClearHudIconNameRange(0x0047acac,0x0047ace2);\n  }\n  else {\n    E2R_ClearHudIconName((char *)0x00475ee0);\n    E2R_ClearHudIconName((char *)0x00475ee8);\n    E2R_ClearHudIconName((char *)0x00475ef0);\n    E2R_ClearHudIconName((char *)0x00475f18);\n    E2R_ClearHudIconName((char *)0x00475f10);\n    E2R_ClearHudIconName((char *)0x00475f50);\n    E2R_ClearHudIconName((char *)0x00475f44);\n    E2R_ClearHudIconNameRange(0x0047ab44,0x0047ab71);\n    E2R_ClearHudIconName((char *)0x00475f38);\n    E2R_ClearHudIconName((char *)0x00475e40);\n    E2R_ClearHudIconNameRange(0x0047ab9e,0x0047abd4);\n    E2R_ClearHudIconNameRange(0x0047abd4,0x0047ac0a);\n    E2R_ClearHudIconNameRange(0x0047ac0a,0x0047ac40);\n  }\n  return;\n}\n\n\n\n/* 00455fe8 */"
);
source = source.replace(/(FUN_00417b20\(int param_1,int param_2,undefined4 param_3,int param_4,int param_5,int param_6\)[\s\S]*?\r?\n  int local_10;\r?\n\s*)local_24 = 1;/, "$1E2R_InitCursorMaskState();\n  unaff_EBX = param_4;\n  local_24 = 1;");
source = source.replace("  local_18 = in_EAX;\n  if ((DAT_0047a279 >> 0x18 == param_1)", "  local_18 = param_1;\n  if ((DAT_0047a279 >> 0x18 == param_1)");
source = source.replace("      local_30 = local_2c;\n      iVar6 = extraout_ECX_01;\n      local_20 = local_28;", "      local_30 = local_2c;\n      iVar6 = param_2;\n      local_20 = local_28;");
source = source.replace("  iVar3 = FUN_0045e54d(extraout_ECX_00,(byte *)s_andrew_00470004);", "  iVar3 = FUN_0045e54d(0x00479d74,(byte *)s_andrew_00470004);");
source = source.replace("    (&DAT_00ac4cad)[iVar2] = 0;", "    ((undefined1 *)0x00ac4cad)[iVar2] = 0;");
source = source.replace("    (&DAT_004c3990)[iVar2] = 0;", "    ((undefined1 *)0x004c3990)[iVar2] = 0;");
source = source.replace("    (&DAT_004c3890)[iVar2] = 0;", "    ((undefined1 *)0x004c3890)[iVar2] = 0;");
source = source.replace("    (&DAT_004c3b90)[iVar2] = 0;", "    ((undefined1 *)0x004c3b90)[iVar2] = 0;");
source = source.replace("    (&DAT_00507490)[iVar2] = 0;", "    ((undefined1 *)0x00507490)[iVar2] = 0;");
source = source.replace("    (&DAT_004c3a90)[iVar2] = 0;", "    ((undefined1 *)0x004c3a90)[iVar2] = 0;");
source = source.replace("  puVar7 = &DAT_0061cd30;\n  iVar2 = 0;", "  puVar7 = (undefined1 *)0x0061cd30;\n  iVar2 = 0;");
source = source.replace(
  "  if (_DAT_006366a4 == (undefined4 *)0x0) {\n    FUN_00414e68();\n  }\n  puVar10 = _DAT_006366a4 + 1;",
  "  if (_DAT_006366a4 == (undefined4 *)0x0) {\n    FUN_00414e68();\n  }\n  E2R_MirrorStartupPartNames();\n  puVar10 = _DAT_006366a4 + 1;"
);
source = source.replace("  pcVar9 = &DAT_00470558;", "  pcVar9 = (char *)0x00470558;");
source = source.replace("  pcVar9 = &DAT_00470568;", "  pcVar9 = (char *)0x00470568;");
source = source.replace("      pcVar9 = &DAT_004705e0;", "      pcVar9 = (char *)0x004705e0;");
source = source.replace(/pcVar9 = &DAT_(00470[78][0-9a-f]{2});/g, "pcVar9 = (char *)0x$1;");
source = source.replace(/pcVar9 = &DAT_(00470[9ab][0-9a-f]{2});/g, "pcVar9 = (char *)0x$1;");
source = source.replace(/pcVar9 = &DAT_(00470[cdef][0-9a-f]{2});/g, "pcVar9 = (char *)0x$1;");
source = source.replace(/pcVar9 = &DAT_(004710[0-9a-f]{2});/g, "pcVar9 = (char *)0x$1;");
source = source.replace(
  "  DAT_00479e8a = CONCAT22((short)local_20.x,(undefined2)DAT_00479e8a);\n  _DAT_0063683c = 0;",
  "  DAT_00479e8a = CONCAT22((short)local_20.x,(undefined2)DAT_00479e8a);\n  E2R_SyncCursorPackedPosition();\n  _DAT_0063683c = 0;"
);
source = source.replace(
  "    _DAT_00479e90 = 0xffff;\n    _DAT_00479e8e = 0xffff;",
  "    E2R_InitCursorMaskState();\n    *(undefined2 *)0x00479e90 = 0xffff;\n    *(undefined2 *)0x00479e8e = 0xffff;"
);
source = source.replace(
  /undefined8 __fastcall FUN_00415c04\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00415c68 \*\//,
  "undefined8 __fastcall FUN_00415c04(undefined4 param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  DAT_00479d88 = 0;\n  return (ulonglong)param_2 << 32;\n}\n\n\n\n/* 00415c68 */"
);
source = source.replace(/(undefined8 __fastcall FUN_0041db98\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  uint uVar4;\r?\n\s*)uVar4 = 0;/, "$1in_EAX = *(ushort *)(uintptr_t)param_1;\n  uVar4 = 0;");
source = source.replace(/(uint __fastcall FUN_0041dc20\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  uint uVar3;\r?\n\s*)uVar2 = \(param_2 & 0xff\)/, "$1in_EAX = (int)(uintptr_t)param_1;\n  uVar2 = (param_2 & 0xff)");
source = source.replace(
  "  puVar3 = &DAT_00477068;\n  do {\n    puVar2 = puVar3 + 2;\n    *(undefined2 *)(puVar3 + 0x2940) = *(undefined2 *)(puVar3 + 0xd7e);",
  "  E2R_MirrorGlyphTableData();\n  puVar3 = &DAT_00477068;\n  do {\n    puVar2 = puVar3 + 2;\n    *(undefined2 *)(puVar3 + 0x2940) = *(undefined2 *)(puVar3 + 0xd7e);"
);
source = source.replace(
  "  do {\n    uVar5 = FUN_0041db98(puVar3 + 2,puVar4);\n    puVar4 = (undefined2 *)((int)((ulonglong)uVar5 >> 0x20) + -2);\n    *(short *)(extraout_ECX + 0x2aca) = (short)uVar5;\n    puVar3 = extraout_ECX;\n  } while (extraout_ECX != &DAT_0047707e);",
  "  do {\n    puVar2 = puVar3 + 2;\n    uVar5 = FUN_0041db98(puVar2,puVar4);\n    puVar4 = (undefined2 *)((int)((ulonglong)uVar5 >> 0x20) + -2);\n    *(short *)(puVar2 + 0x2aca) = (short)uVar5;\n    puVar3 = puVar2;\n  } while (puVar2 != &DAT_0047707e);"
);
source = source.replace(
  "  do {\n    uVar5 = FUN_0041db98(puVar3 + 2,puVar4);\n    puVar4 = (undefined2 *)((int)((ulonglong)uVar5 >> 0x20) + -2);\n    *(short *)(extraout_ECX_00 + 0x2b0c) = (short)uVar5;\n    puVar3 = extraout_ECX_00;\n  } while (extraout_ECX_00 != &DAT_0047707e);",
  "  do {\n    puVar2 = puVar3 + 2;\n    uVar5 = FUN_0041db98(puVar2,puVar4);\n    puVar4 = (undefined2 *)((int)((ulonglong)uVar5 >> 0x20) + -2);\n    *(short *)(puVar2 + 0x2b0c) = (short)uVar5;\n    puVar3 = puVar2;\n  } while (puVar2 != &DAT_0047707e);"
);
source = source.replace("  *(short *)(extraout_ECX_01 + 0x2b66) = (short)uVar1;", "  *(short *)(&DAT_0047707c + 0x2b66) = (short)uVar1;");
source = source.replace("  *(short *)(extraout_ECX_02 + 0x2b92) = (short)uVar1;", "  *(short *)(&DAT_0047707c + 0x2b92) = (short)uVar1;");
source = source.replace(
  "  do {\n    uVar1 = FUN_0041dc20(puVar3,*(int *)(puVar3 + 0x292) >> 0x10);\n    puVar3 = (undefined *)(extraout_ECX_03 + 2);\n    *(ushort *)(extraout_ECX_03 + 0x2c16) = *(ushort *)(extraout_ECX_03 + 0x2c16) | (ushort)uVar1;\n  } while (puVar3 != &DAT_00477078);",
  "  do {\n    uVar1 = FUN_0041dc20(puVar3,*(int *)(puVar3 + 0x292) >> 0x10);\n    *(ushort *)(puVar3 + 0x2c16) = *(ushort *)(puVar3 + 0x2c16) | (ushort)uVar1;\n    puVar3 = puVar3 + 2;\n  } while (puVar3 != &DAT_00477078);"
);
const glyphTableMirrorSymbols = [
  "DAT_00477010", "DAT_00477012", "DAT_00477016", "DAT_00477060", "DAT_00477064",
  "DAT_00477068", "DAT_0047706e", "DAT_00477078", "DAT_0047707a", "DAT_0047707c",
  "DAT_0047707e", "DAT_004770aa", "DAT_004770c0", "DAT_004770ec", "DAT_00477118",
  "DAT_0047712c", "DAT_0047712e", "DAT_00477142", "DAT_0047719c", "DAT_004771de",
  "DAT_004772fc", "DAT_00477312", "DAT_004773ac", "DAT_004773ee", "DAT_00477404",
  "DAT_00477446", "DAT_0047745c", "DAT_0047757a", "DAT_00477590", "DAT_004777b6",
  "DAT_0047930a", "DAT_004799a8", "DAT_004799be", "DAT_004799d4", "DAT_004799ea",
  "DAT_00479a00", "DAT_00479a16", "DAT_00479a2c", "DAT_00479a42", "DAT_00479a58",
  "DAT_00479a6e", "DAT_00479a84", "DAT_00479a9a", "DAT_00479ab0", "DAT_00479ac6",
  "DAT_00479adc", "DAT_00479af2", "DAT_00479b08", "DAT_00479b1e", "DAT_00479b34",
  "DAT_00479b4a", "DAT_00479b60", "DAT_00479b76", "DAT_00479b8c", "DAT_00479ba2",
  "DAT_00479bb8", "DAT_00479bce", "DAT_00479be4", "DAT_00479bfa", "DAT_00479c10",
  "DAT_00479c26", "DAT_00479c3c", "DAT_00479c52", "DAT_00479c68", "DAT_00479c7e",
  "DAT_00479c94", "DAT_00479d6c",
];
const ctypeTableState = `\nstatic byte E2R_CtypeFlags(uint index)\n{\n  int c = (int)(byte)index - 1;\n  byte flags = 0;\n\n  if (c < 0) {\n    return 0;\n  }\n  if (c < 0x20 || c == 0x7f) {\n    flags = flags | 1;\n  }\n  if (c == ' ' || c == '\\t' || c == '\\n' || c == '\\r' || c == '\\v' || c == '\\f') {\n    flags = flags | 2;\n  }\n  if ('0' <= c && c <= '9') {\n    flags = flags | 0x20;\n  }\n  if ('A' <= c && c <= 'Z') {\n    flags = flags | 0x40;\n  }\n  if ('a' <= c && c <= 'z') {\n    flags = flags | 0x80;\n  }\n  return flags;\n}\n\nstatic byte E2R_BitMask(uint index)\n{\n  return (byte)(1u << (index & 7));\n}\n\nstatic void E2R_FormatOneString(char *dest,char *format,char *value)\n{\n  while (*format != '\\0') {\n    if (format[0] == '%' && format[1] == 's') {\n      while (*value != '\\0') {\n        *dest = *value;\n        dest = dest + 1;\n        value = value + 1;\n      }\n      format = format + 2;\n    }\n    else {\n      *dest = *format;\n      dest = dest + 1;\n      format = format + 1;\n    }\n  }\n  *dest = '\\0';\n}\n\nstatic void E2R_UseHostedCdPath(char *path)\n{\n  if ((path[0] != '\\0' && path[1] == ':') || path[0] == '\\\\' || path[0] == '/') {\n    path[0] = '\\0';\n  }\n}\n`;
const requesterActionState = `\nstatic int E2R_InvokeRequesterAction(uintptr_t action)\n{\n  ushort requester_id = E2R_WORD_AT(DAT_0047a45e,2);\n\n  if (action == (uintptr_t)&LAB_0043c594) {\n    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643dc4) {\n      _DAT_006443d2 = (_DAT_006443d2 & 0xffff) | 0x10000;\n      if (_DAT_00643430 == (short *)0x00643dc4) {\n        _DAT_00643650 = 6;\n      }\n      return 1;\n    }\n  }\n  if (action == (uintptr_t)&LAB_0043d458) {\n    _DAT_00643650 = 0;\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d464) {\n    _DAT_00643650 = 1;\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d470) {\n    _DAT_00643650 = 2;\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d47c) {\n    if (DAT_0047a76c == 0) {\n      _DAT_00643650 = 3;\n    }\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d490) {\n    _DAT_00643650 = 4;\n    return 1;\n  }\n  if (action == (uintptr_t)&DAT_0043d49c) {\n    uintptr_t prompt = 0x004729b8;\n    if (DAT_00479e00 != 0 && !IsBadReadPtr((void *)0x0060aef0,4) &&\n        *(uintptr_t *)0x0060aef0 != 0) {\n      prompt = *(uintptr_t *)0x0060aef0;\n    }\n    _DAT_00643650 = ((int)FUN_0043c910((undefined4)prompt,0) != 0) ? 6 : 5;\n    return 1;\n  }\n  if (action == (uintptr_t)&DAT_0043d4c0) {\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d83c) {\n    if (DAT_0047d0c4 == 0) {\n      return 1;\n    }\n    FUN_0044e5b0();\n    if (DAT_0047a43c != 0) {\n      FUN_0043acec();\n    }\n    else {\n      FUN_0043ac60();\n    }\n    DAT_0047a440 = DAT_0047a43c;\n    FUN_0044e5b0();\n    FUN_004559bc();\n    FUN_00456f94();\n    FUN_004211c8(0,0);\n    FUN_00421a14();\n    FUN_00421f54(0);\n    FUN_00422238(0,0);\n    FUN_0043d8ec();\n    FUN_0043d934();\n    FUN_0043d9a0();\n    FUN_0043da04();\n    FUN_0043da80();\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043c4e8) {\n    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643c84) {\n      _DAT_006443d2 = _DAT_006443d2 & 0xffff;\n      if (_DAT_00643430 == (short *)0x00643c84) {\n        _DAT_00643650 = 5;\n      }\n      return 1;\n    }\n    if (requester_id == 0x27 || requester_id == 0x28) {\n      _DAT_00643650 = 5;\n      return 1;\n    }\n    if (requester_id == 0x2a) {\n      _DAT_0064353c = 0;\n      return 1;\n    }\n  }\n  return 0;\n}\n`;
const requesterFocusState = `\nstatic short *E2R_RequesterFirstSelectable(short *item)\n{\n  uint guard = 0;\n  short *first_readable = (short *)0x0;\n\n  while (item != (short *)0x0 && guard < 0x80) {\n    if ((uintptr_t)item >= 0x70000000u || IsBadReadPtr(item,0x20)) {\n      return (short *)0x0;\n    }\n    if (first_readable == (short *)0x0) {\n      first_readable = item;\n    }\n    if ((*(byte *)((int)item + 0x11) & 0x10) != 0) {\n      return item;\n    }\n    item = *(short **)(item + 9);\n    guard++;\n  }\n  return first_readable;\n}\n`;
const menuStringState = `\nstatic int E2R_IsReadableCString(char *text)\n{\n  uint i;\n\n  if ((uintptr_t)text < 0x10000 || IsBadReadPtr(text,1)) {\n    return 0;\n  }\n  for (i = 0; i < 0x1000; i = i + 1) {\n    if (IsBadReadPtr(text + i,1)) {\n      return 0;\n    }\n    if (text[i] == '\\0') {\n      return 1;\n    }\n  }\n  return 0;\n}\n\nstatic int *E2R_ResolveMenuStringList(undefined4 first,undefined4 second,undefined4 *local_single)\n{\n  int *list;\n  char *text;\n\n  list = (int *)(uintptr_t)first;\n  if ((uintptr_t)list >= 0x10000 && !IsBadReadPtr(list,4)) {\n    text = (char *)(uintptr_t)list[0];\n    if (text == (char *)0x0 || E2R_IsReadableCString(text)) {\n      return list;\n    }\n  }\n  text = (char *)(uintptr_t)first;\n  if (E2R_IsReadableCString(text)) {\n    local_single[0] = first;\n    local_single[1] = 0;\n    return (int *)local_single;\n  }\n  text = (char *)(uintptr_t)second;\n  if (E2R_IsReadableCString(text)) {\n    local_single[0] = second;\n    local_single[1] = 0;\n    return (int *)local_single;\n  }\n  return (int *)0x0;\n}\n`;
const streamLineState = `\nstatic undefined1 *E2R_ReadStreamLine(undefined4 stream_handle,char *buffer,uint count)\n{\n  undefined4 *stream;\n  byte *cursor;\n  uint remaining;\n  uint copied = 0;\n  byte value = 0;\n\n  if (count == 0) {\n    return (undefined1 *)0x0;\n  }\n  buffer[0] = '\\0';\n  stream = (undefined4 *)(uintptr_t)stream_handle;\n  if ((uintptr_t)stream < 0x10000 || (uintptr_t)stream >= 0x70000000u ||\n      IsBadReadPtr(stream,0x1c) || stream[6] != E2R_STREAM_MAGIC) {\n    return (undefined1 *)0x0;\n  }\n  cursor = (byte *)(uintptr_t)stream[0];\n  remaining = (uint)stream[1];\n  while (copied + 1 < count && remaining != 0) {\n    value = *cursor;\n    cursor = cursor + 1;\n    remaining = remaining - 1;\n    buffer[copied] = (char)value;\n    copied = copied + 1;\n    if (value == '\\n') {\n      break;\n    }\n  }\n  stream[0] = (undefined4)(uintptr_t)cursor;\n  stream[1] = remaining;\n  if (copied == 0) {\n    return (undefined1 *)0x0;\n  }\n  buffer[copied] = '\\0';\n  return (undefined1 *)buffer;\n}\n`;
const configHeaderState = `\nstatic void E2R_UnpackConfigHeader(char *header,char *cStack_5c,byte *bStack_5b,byte *bStack_5a,\n                                   undefined1 *uStack_59,byte *bStack_58,\n                                   undefined1 *uStack_57,undefined1 *uStack_56,\n                                   undefined1 *uStack_55,undefined1 *uStack_54,\n                                   undefined1 *uStack_53,byte *bStack_52)\n{\n  *cStack_5c = header[0xc];\n  *bStack_5b = (byte)header[0xd];\n  *bStack_5a = (byte)header[0xe];\n  *uStack_59 = (undefined1)header[0xf];\n  *bStack_58 = (byte)header[0x10];\n  *uStack_57 = (undefined1)header[0x11];\n  *uStack_56 = (undefined1)header[0x12];\n  *uStack_55 = (undefined1)header[0x13];\n  *uStack_54 = (undefined1)header[0x14];\n  *uStack_53 = (undefined1)header[0x15];\n  *bStack_52 = (byte)header[0x16];\n}\n\nstatic void E2R_PackConfigHeader(char *header,char cStack_5c,byte bStack_5b,byte bStack_5a,\n                                 undefined1 uStack_59,byte bStack_58,undefined1 uStack_57,\n                                 undefined1 uStack_56,undefined1 uStack_55,\n                                 undefined1 uStack_54,undefined1 uStack_53,byte bStack_52)\n{\n  header[0xc] = cStack_5c;\n  header[0xd] = (char)bStack_5b;\n  header[0xe] = (char)bStack_5a;\n  header[0xf] = (char)uStack_59;\n  header[0x10] = (char)bStack_58;\n  header[0x11] = (char)uStack_57;\n  header[0x12] = (char)uStack_56;\n  header[0x13] = (char)uStack_55;\n  header[0x14] = (char)uStack_54;\n  header[0x15] = (char)uStack_53;\n  header[0x16] = (char)bStack_52;\n}\n`;
const cursorMaskState = `\nstatic void E2R_InitCursorMaskState(void)\n{\n  static int initialized;\n\n  if (initialized != 0) {\n    return;\n  }\n  initialized = 1;\n  *(undefined4 *)0x00479e8a = (undefined4)DAT_00479e8a;\n  *(undefined2 *)0x00479e8e = 0xffff;\n  *(undefined2 *)0x00479e90 = 0xffff;\n  memset((void *)0x00479e92,'#',0x40);\n}\n\nstatic void E2R_SyncCursorPackedPosition(void)\n{\n  E2R_InitCursorMaskState();\n  *(undefined4 *)0x00479e8a = (undefined4)DAT_00479e8a;\n}\n`;
const packedNameState = `
static short E2R_InternPackedName(char *input,char *table,uint capacity,short max_names)
{
  uint input_length;
  uint length;
  uint offset = 0;
  short index = 0;

  if (input == (char *)0x0 || table == (char *)0x0 || IsBadReadPtr(input,1) ||
      IsBadReadPtr(table,capacity)) {
    return -1;
  }
  for (input_length = 0; input_length < 0x100; input_length = input_length + 1) {
    if (IsBadReadPtr(input + input_length,1)) {
      return -1;
    }
    if (input[input_length] == '\\0') {
      break;
    }
  }
  if (input_length == 0x100) {
    return -1;
  }
  while (index < max_names && offset < capacity) {
    for (length = 0; offset + length < capacity; length = length + 1) {
      if (table[offset + length] == '\\0') {
        break;
      }
    }
    if (offset + length == capacity) {
      return -1;
    }
    if (length == input_length && memcmp(table + offset,input,length + 1) == 0) {
      return index;
    }
    if (length == 0) {
      if (capacity - offset < input_length + 2) {
        return -1;
      }
      memcpy(table + offset,input,input_length + 1);
      table[offset + input_length + 1] = '\\0';
      return index;
    }
    offset = offset + length + 1;
    index = index + 1;
  }
  return -1;
}

static short E2R_FindPackedNameIndex(char *input,char *table,uint capacity,short max_names)
{
  uint input_length;
  uint length;
  uint offset = 0;
  short index = 0;

  if (input == (char *)0x0 || table == (char *)0x0 || IsBadReadPtr(input,1) ||
      IsBadReadPtr(table,1)) {
    return -1;
  }
  for (input_length = 0; input_length < 0x100; input_length = input_length + 1) {
    if (IsBadReadPtr(input + input_length,1)) {
      return -1;
    }
    if (input[input_length] == '\\0') {
      break;
    }
  }
  if (input_length == 0x100) {
    return -1;
  }
  while (index < max_names && offset < capacity) {
    for (length = 0; offset + length < capacity; length = length + 1) {
      if (table[offset + length] == '\\0') {
        break;
      }
    }
    if (offset + length == capacity) {
      return -1;
    }
    if (length == input_length && memcmp(table + offset,input,length + 1) == 0) {
      return index;
    }
    if (length == 0) {
      return -1;
    }
    offset = offset + length + 1;
    index = index + 1;
  }
  return -1;
}
`;
const actionCodeState = `
static short *E2R_action_dispatch_node;
static char *E2R_action_name_cache[0x4000];
static char *E2R_action_name_cache_base;
static int E2R_action_name_cache_ready;

static void E2R_PrimeActionNameCache(char *cursor)
{
  uint index;
  uint length;

  if (cursor == (char *)0x0 || (uintptr_t)cursor < 0x10000u ||
      IsBadReadPtr(cursor,1)) {
    return;
  }
  memset(E2R_action_name_cache,0,sizeof(E2R_action_name_cache));
  E2R_action_name_cache_base = cursor;
  for (index = 0; index < 0x4000; index = index + 1) {
    E2R_action_name_cache[index] = cursor;
    for (length = 0; length < 0x100; length = length + 1) {
      if (IsBadReadPtr(cursor + length,1)) {
        return;
      }
      if (cursor[length] == '\\0') {
        break;
      }
    }
    if (length == 0x100) {
      return;
    }
    if (length == 0) {
      E2R_action_name_cache_ready = 1;
      return;
    }
    cursor = cursor + length + 1;
  }
  E2R_action_name_cache_ready = 1;
}

static char *E2R_ActionNameByIndex(short index)
{
  char *cursor = (char *)(uintptr_t)_DAT_00636698;
  int item;
  uint length;

  if (index < 0 || 0x4000 < index || (uintptr_t)cursor < 0x10000u ||
      IsBadReadPtr(cursor,1)) {
    return (char *)0x0;
  }
  if (E2R_action_name_cache_base != cursor || E2R_action_name_cache_ready == 0) {
    E2R_PrimeActionNameCache(cursor);
  }
  if (E2R_action_name_cache_base == cursor && E2R_action_name_cache_ready != 0) {
    return E2R_action_name_cache[(ushort)index];
  }
  for (item = 0; item < (int)index; item = item + 1) {
    for (length = 0; length < 0x100; length = length + 1) {
      if (IsBadReadPtr(cursor + length,1)) {
        return (char *)0x0;
      }
      if (cursor[length] == '\\0') {
        cursor = cursor + length + 1;
        break;
      }
    }
    if (length == 0x100) {
      return (char *)0x0;
    }
  }
  for (length = 0; length < 0x100; length = length + 1) {
    if (IsBadReadPtr(cursor + length,1)) {
      return (char *)0x0;
    }
    if (cursor[length] == '\\0') {
      return cursor;
    }
  }
  return (char *)0x0;
}

static char *E2R_ActionCodeName(short *action)
{
  if (action == (short *)0x0 || IsBadReadPtr(action,0xe)) {
    return (char *)0x0;
  }
  return E2R_ActionNameByIndex(*action);
}

static int E2R_ascii_lower(int value)
{
  if ('A' <= value && value <= 'Z') {
    return value + ('a' - 'A');
  }
  return value;
}

static int E2R_CaseEqualBounded(char *left,char *right,uint limit)
{
  uint i;

  if (left == (char *)0x0 || right == (char *)0x0) {
    return 0;
  }
  for (i = 0; i < limit; i = i + 1) {
    int l;
    int r;

    if (IsBadReadPtr(left + i,1) || IsBadReadPtr(right + i,1)) {
      return 0;
    }
    l = (byte)left[i];
    r = (byte)right[i];
    if (E2R_ascii_lower(l) != E2R_ascii_lower(r)) {
      return 0;
    }
    if (l == 0) {
      return 1;
    }
  }
  return 0;
}

static int E2R_FanActionPassesFilter(short action_index)
{
  char *filter = (char *)0x0047a458;
  char *name;

  if (IsBadReadPtr(filter,1) || filter[0] == '\\0') {
    return 1;
  }
  name = E2R_ActionNameByIndex(action_index);
  return E2R_CaseEqualBounded(filter,name,0x100);
}

static uint E2R_CountActionList(short *head)
{
  short *node = head;
  uint count = 0;

  while (node != (short *)0x0 && count < 0x4000 && !IsBadReadPtr(node,0xe)) {
    count = count + 1;
    node = *(short **)(node + 5);
  }
  return count;
}

static uint E2R_CountActionTable(void)
{
  short **table = (short **)0x006297c0;
  uint count = 0;
  uint index;

  if (IsBadReadPtr(table,0x4000 * sizeof(short *))) {
    return 0;
  }
  for (index = 0; index < 0x4000; index = index + 1) {
    if (table[index] != (short *)0x0) {
      count = count + 1;
    }
  }
  return count;
}

static int E2R_ReadFanTextByte(int *stream)
{
  byte *cursor;
  int value;
  undefined8 read;

  if (stream == (int *)0x0 || IsBadReadPtr(stream,0x1c)) {
    return 0;
  }
  if (0 < stream[1] && ((*(byte *)(stream + 3) & 4) == 0)) {
    cursor = (byte *)(uintptr_t)stream[0];
    if (!IsBadReadPtr(cursor,1) && *cursor != '\\r' && *cursor != '\\x1a') {
      value = (int)*cursor;
      stream[0] = (int)(uintptr_t)(cursor + 1);
      stream[1] = stream[1] + -1;
      return value;
    }
  }
  read = FUN_0045f38a((undefined4)(uintptr_t)stream,(undefined4)(uintptr_t)stream);
  return (int)read & 0xff;
}

static void E2R_SkipFanTextString(int *stream)
{
  while (E2R_ReadFanTextByte(stream) != 0) {
  }
}

static void E2R_ReadFanChildName(int *stream,char *target,uint target_size)
{
  uint length = 0;
  int value;

  if (target != (char *)0x0 && target_size != 0 && !E2R_IsBadWritePtr(target,target_size)) {
    memset(target,' ',target_size);
  }
  do {
    value = E2R_ReadFanTextByte(stream);
    if (value != 0 && target != (char *)0x0 && length < target_size &&
        !E2R_IsBadWritePtr(target + length,1)) {
      target[length] = (char)value;
    }
    length = length + 1;
  } while (value != 0);
}

static void E2R_NormalizeFanChildName(char *target,uint target_size)
{
  static char not_present[] = "NOT Present";
  static char check_actor[] = "CheckActor";
  uint offset;
  uint needle_length = (uint)strlen(not_present);

  if (target == (char *)0x0 || target_size <= needle_length ||
      E2R_IsBadWritePtr(target,target_size)) {
    return;
  }
  for (offset = 0; offset < target_size - needle_length; offset = offset + 1) {
    if (memcmp(target + offset,not_present,needle_length) == 0) {
      memcpy(target + offset,check_actor,strlen(check_actor) + 1);
      return;
    }
  }
}

static int E2R_ActionCodeMatches(short *action,char *suffix)
{
  char *name = E2R_ActionCodeName(action);
  size_t length;

  if (name == (char *)0x0) {
    return 0;
  }
  length = strlen(name);
  return 4 < length && strcmp(name + 4,suffix) == 0;
}

static short *E2R_FindActionCodeBySuffix(char *suffix)
{
  short *node;
  short **table;
  uint guard;
  uint index;

  node = _DAT_00637250;
  for (guard = 0; node != (short *)0x0 && guard < 0x4000 &&
       !IsBadReadPtr(node,0xe); guard = guard + 1) {
    if (E2R_ActionCodeMatches(node,suffix)) {
      return node;
    }
    node = *(short **)(node + 5);
  }

  table = (short **)0x006297c0;
  if (!IsBadReadPtr(table,0x4000 * sizeof(short *))) {
    for (index = 0; index < 0x4000; index = index + 1) {
      node = table[index];
      if (node != (short *)0x0 && !IsBadReadPtr(node,0xe) &&
          E2R_ActionCodeMatches(node,suffix)) {
        return node;
      }
    }
  }
  return (short *)0x0;
}

static void E2R_InvokeActionCode(short *action)
{
  E2R_start_code_probe_dispatches++;
  E2R_start_code_probe_last_node = (uintptr_t)action;
  E2R_start_code_probe_last_name_index = (ushort)action[0];
  E2R_start_code_probe_last_bytecode_offset = *(uint *)(action + 3);
  E2R_action_dispatch_node = action;
  FUN_0044f2fc();
  E2R_action_dispatch_node = (short *)0x0;
}
`;
const startupNameWordSymbols = [
  "DAT_00470708", "DAT_0047070c", "DAT_00470724", "DAT_00470728", "DAT_0047072c",
  "DAT_00470730", "DAT_00470740", "DAT_00470748", "DAT_00470750", "DAT_00470758",
  "DAT_00470760", "DAT_00470768", "DAT_00470770", "DAT_00470778", "DAT_00470780",
  "DAT_0047078c", "DAT_00470798", "DAT_004707a4", "DAT_004707b0", "DAT_004707bc",
  "DAT_004707c8", "DAT_004707d4", "DAT_004707e0", "DAT_004707ec", "DAT_004707f8",
  "DAT_00470804", "DAT_0047081c", "DAT_00470828", "DAT_00470834", "DAT_00470840",
  "DAT_0047086c", "DAT_00470874", "DAT_0047087c", "DAT_00470884", "DAT_0047088c",
  "DAT_00470894", "DAT_0047089c", "DAT_004708a4", "DAT_004708ac", "DAT_004708b4",
  "DAT_004708bc", "DAT_004708c4", "DAT_004708cc", "DAT_004708d4", "DAT_004708dc",
  "DAT_004708e4", "DAT_004708ec", "DAT_004708f4", "DAT_004708fc",
];
const startupNameWordConstants2 = [
  ["00470904", "0x6c735f77u"], ["0047090c", "0x6c735f77u"],
  ["00470914", "0x79635f77u"], ["0047091c", "0x79635f77u"],
  ["00470928", "0x79635f77u"], ["00470934", "0x6f7a5f77u"],
  ["0047093c", "0x6f7a5f77u"], ["00470944", "0x6f7a5f77u"],
  ["00470958", "0x69765f77u"], ["00470960", "0x69765f77u"],
  ["00470968", "0x69765f77u"], ["00470970", "0x6f6d5f77u"],
  ["00470978", "0x6f6d5f77u"], ["00470980", "0x6f6d5f77u"],
  ["004709a8", "0x72745f77u"], ["004709b0", "0x72745f77u"],
  ["004709b8", "0x72745f77u"], ["004709e0", "0x6f645f77u"],
  ["004709f0", "0x6f645f77u"], ["004709f8", "0x65625f77u"],
  ["00470a00", "0x65625f77u"], ["00470a08", "0x65625f77u"],
  ["00470a30", "0x61675f77u"], ["00470a38", "0x61675f77u"],
  ["00470a44", "0x61675f77u"], ["00470a50", "0x6f775f77u"],
  ["00470a58", "0x6f775f77u"], ["00470a60", "0x6f775f77u"],
  ["00470a74", "0x75685f77u"], ["00470a7c", "0x75685f77u"],
  ["00470a84", "0x6b735f77u"], ["00470a8c", "0x6b735f77u"],
  ["00470a94", "0x6b735f77u"], ["00470a9c", "0x6e625f77u"],
  ["00470aa4", "0x6e625f77u"], ["00470ab0", "0x6e625f77u"],
  ["00470af0", "0x72635f77u"], ["00470b04", "0x61665f77u"],
  ["00470b10", "0x61665f77u"], ["00470b1c", "0x61665f77u"],
  ["00470b28", "0x61665f77u"], ["00470b34", "0x61665f77u"],
  ["00470b40", "0x69665f77u"], ["00470b48", "0x69665f77u"],
  ["00470b50", "0x69665f77u"], ["00470b58", "0x6d615f77u"],
  ["00470b60", "0x6d615f77u"], ["00470b68", "0x6d615f77u"],
  ["00470b70", "0x6d615f77u"], ["00470b78", "0x6d615f77u"],
  ["00470b80", "0x6d615f77u"], ["00470b88", "0x6d615f77u"],
  ["00470b90", "0x6d615f77u"], ["00470b98", "0x67625f77u"],
  ["00470ba0", "0x67625f77u"], ["00470ba8", "0x67625f77u"],
  ["00470bb0", "0x756d5f77u"], ["00470bb8", "0x756d5f77u"],
  ["00470bc4", "0x756d5f77u"], ["00470bd0", "0x756d5f77u"],
  ["00470bd8", "0x756d5f77u"], ["00470be0", "0x756d5f77u"],
  ["00470be8", "0x67735f77u"], ["00470bf0", "0x67735f77u"],
  ["00470bf8", "0x67735f77u"],
];
const startupNameWords2 = `  static const struct {
    uintptr_t address;
    undefined4 value;
  } startupNameWords2[] = {
${startupNameWordConstants2.map(([address, value]) => `    {0x${address},${value}},`).join("\n")}
  };`;
const startupNameWordConstants3 = `
00470c34 0x6f746b62u
00470c38 0x6e7572u
00470ca4 0x53646e45u
00470ca8 0x46316e63u
00470cac 0x0u
00470cb0 0x53646e45u
00470cb4 0x46326e63u
00470cb8 0x0u
00470cd0 0x6f726568u
00470cd4 0x64736b71u
00470cd8 0x0u
00470db0 0x5f79654bu
00470db4 0x345f3146u
00470db8 0x0u
00470dbc 0x5f79654bu
00470dc0 0x385f3546u
00470dc4 0x0u
00470dc8 0x5f79654bu
00470dcc 0x315f3946u
00470dd0 0x32u
00470dd4 0x3179654bu
00470dd8 0x0u
00470ddc 0x3279654bu
00470de0 0x0u
00470de4 0x3379654bu
00470de8 0x0u
00470dec 0x3479654bu
00470df0 0x0u
00470df4 0x3579654bu
00470df8 0x0u
00470dfc 0x3679654bu
00470e00 0x0u
00470e04 0x3779654bu
00470e08 0x0u
00470e0c 0x3879654bu
00470e10 0x0u
00470e14 0x3979654bu
00470e18 0x0u
00470e7c 0x75725f66u
00470e80 0x705f6eu
00470e84 0x31747966u
00470e88 0x0u
00470e8c 0x32747966u
00470e90 0x0u
00470e94 0x72747966u
00470e98 0x6e75u
00470e9a 0x6f670000u
00470e9c 0x66626f67u
00470ea0 0x317479u
00470ee8 0x6a616d6au
00470eec 0x646e6177u
00470ef0 0x0u
00470ef4 0x776a6d6au
00470ef8 0x646e61u
00470f28 0x544f4f46u
00470f2c 0x0u
00470f30 0x45444157u
00470f34 0x32u
00470f38 0x3244554du
00470f3c 0x0u
00470f4c 0x4f484345u
00470f50 0x413230u
00470f54 0x53415247u
00470f58 0x3153u
00470f5a 0x454c0000u
00470f5c 0x5641454cu
00470f60 0x315345u
00470f64 0x44554854u
00470f68 0x314d53u
00470f6c 0x3144554du
00470f70 0x0u
00470f7c 0x4c494f53u
00470f80 0x32u
00470f84 0x4f484345u
00470f88 0x413130u
00470f8c 0x4b43494bu
00470f90 0x31u
00470f94 0x44554854u
00470f98 0x0u
0047108c 0x6973756du
00471094 0x6363732eu
0047109c 0x6c62732eu
004710a4 0x6577612eu
004710ac 0x7375672eu
004710b4 0x70616c2eu
`.trim().split(/\n/).map((line) => line.split(/\s+/));
const startupNameWords3 = `  static const struct {
    uintptr_t address;
    undefined4 value;
  } startupNameWords3[] = {
${startupNameWordConstants3.map(([address, value]) => `    {0x${address},${value}},`).join("\n")}
  };`;
const startupPartNames = `\nstatic void E2R_MirrorStartupPartNames(void)\n{\n${startupNameWords2}\n${startupNameWords3}\n  static int initialized;\n  uint i;\n\n  if (initialized != 0) {\n    return;\n  }\n  initialized = 1;\n  *(undefined4 *)0x00470558 = (undefined4)_DAT_00470558;\n  *(undefined1 *)0x0047055c = (undefined1)DAT_0047055c;\n  memcpy((void *)0x00470560,s_Chest_00470560,6);\n  *(undefined4 *)0x00470568 = (undefined4)_DAT_00470568;\n  *(undefined1 *)0x0047056c = (undefined1)DAT_0047056c;\n  *(undefined4 *)0x004705e0 = (undefined4)_DAT_004705e0;\n  *(undefined2 *)0x004705e4 = (undefined2)DAT_004705e4;\n  *(undefined1 *)0x004705e6 = (undefined1)DAT_004705e6;\n${startupNameWordSymbols.map((name) => {
  const address = name.slice(4).toLowerCase();
  return `  *(undefined4 *)0x${address} = (undefined4)${name};`;
}).join("\n")}\n  for (i = 0; i < sizeof(startupNameWords2) / sizeof(startupNameWords2[0]); i++) {\n    *(undefined4 *)startupNameWords2[i].address = startupNameWords2[i].value;\n  }\n  for (i = 0; i < sizeof(startupNameWords3) / sizeof(startupNameWords3[0]); i++) {\n    *(undefined4 *)startupNameWords3[i].address = startupNameWords3[i].value;\n  }\n}\n`;
const glyphTableMirror = `\nstatic void E2R_MirrorGlyphTableData(void)\n{\n  static int initialized;\n\n  if (initialized != 0) {\n    return;\n  }\n  initialized = 1;\n${glyphTableMirrorSymbols.map((name) => {
  const address = name.slice(4).toLowerCase();
  return `  *(undefined4 *)0x${address} = (undefined4)${name};`;
}).join("\n")}\n}\n`;
const hudIconNameState = `
static void E2R_MirrorHudIconNames(void)
{
  static const struct {
    uintptr_t address;
    const char *text;
  } names[] = {
    {0x00475e38,"llife"},
    {0x00475e40,"magibar1"},
    {0x00475e4c,"lmbar"},
    {0x00475ee0,"life1"},
    {0x00475ee8,"life2"},
    {0x00475ef0,"life3"},
    {0x00475ef8,"llife1"},
    {0x00475f00,"llife2"},
    {0x00475f08,"llife3"},
    {0x00475f10,"armour3"},
    {0x00475f18,"armour2"},
    {0x00475f20,"larmour3"},
    {0x00475f2c,"larmour2"},
    {0x00475f38,"hndicon1"},
    {0x00475f44,"swdicon1"},
    {0x00475f50,"rodicon1"},
    {0x00475f5c,"lhand2"},
    {0x00475f64,"lsword1"},
    {0x00475f6c,"lrod1"},
    {0x0047ab71,"lbar1"},
    {0x0047ab9e,"magic1"},
    {0x0047aba7,"magic1b"},
    {0x0047abd4,"magic2"},
    {0x0047ac0a,"magic3"},
    {0x0047ac40,"lmagic1"},
    {0x0047ac76,"lmagic2"},
    {0x0047acac,"lmagic3"},
  };
  static int initialized;
  uint i;

  if (initialized != 0) {
    return;
  }
  initialized = 1;
  for (i = 0; i < sizeof(names) / sizeof(names[0]); i = i + 1) {
    strcpy((char *)names[i].address,names[i].text);
  }
}

static void E2R_ClearHudIconName(char *name)
{
  char *entry;
  char state;
  int i;

  E2R_MirrorHudIconNames();
  if (!E2R_IsReadableCString(name) || name[0] == '\\0') {
    return;
  }
  for (i = 0; i < 0x19; i = i + 1) {
    entry = (char *)(0x00ac4cad + i * 9);
    if (entry[0] != '\\0' && strncmp(name,entry,9) == 0) {
      if (*(int *)(0x00ac4a6c + i * 4) != 0) {
        FUN_0045f9b5();
      }
      state = *(char *)(0x00ac4c94 + i);
      *(undefined4 *)(0x00ac4a6c + i * 4) = 0;
      if (state == '\\x02') {
        *(undefined1 *)(0x00ac4c94 + i) = 0xff;
        DAT_0047ab08 = 1;
      }
      else {
        *(undefined1 *)(0x00ac4cad + i * 9) = 0;
      }
      return;
    }
  }
}

static void E2R_ClearHudIconNameRange(uintptr_t start,uintptr_t end)
{
  uintptr_t address;

  for (address = start; address != end; address = address + 9) {
    E2R_ClearHudIconName((char *)address);
  }
}
`;
const requesterRecordState = `
static void E2R_InitRequesterRecord(uintptr_t address,short x,short y,short width,short height,
                                    uintptr_t title,uintptr_t first_item)
{
  short *record;

  record = (short *)address;
  if (E2R_IsBadWritePtr(record,0x1c)) {
    return;
  }
  record[0] = x;
  record[1] = y;
  record[2] = width;
  record[3] = height;
  *(uintptr_t *)(record + 4) = title;
  *(uintptr_t *)(record + 6) = first_item;
  record[8] = 0;
  *(uintptr_t *)(record + 9) = 0;
}

static void E2R_InitRequesterItem(uintptr_t address,short width,short x,short y,short height,
                                  uintptr_t text,uintptr_t action,short flags,uintptr_t next)
{
  short *item = (short *)address;

  if (DAT_0047a43c == 0) {
    item[0] = x;
    item[1] = y;
    item[2] = width;
    item[3] = height;
  }
  else {
    item[0] = x * 2;
    item[1] = (short)((y * 3) / 2);
    item[2] = width * 2;
    item[3] = (short)((height * 3) / 2);
  }
  *(uintptr_t *)(item + 4) = text;
  *(uintptr_t *)(item + 6) = action;
  item[8] = flags | 0x1000;
  *(uintptr_t *)(item + 9) = next;
}

static void E2R_InitRequesterMainMenuItems(void)
{
  if (DAT_00479e00 == 0) {
    E2R_InitRequesterItem(0x00643ca4,0xaa,0x14,0x82,10,(uintptr_t)(char *)0x00473304,
                          (uintptr_t)&DAT_0043d49c,0x2000,0x00643780);
    E2R_InitRequesterItem(0x00643ad0,0xaa,0x14,0x69,10,(uintptr_t)s_Uninstall_0047330c,
                          (uintptr_t)&DAT_0043d4c0,0x2000,0x00643ca4);
    E2R_InitRequesterItem(0x006439d8,0xaa,0x14,0x50,10,(uintptr_t)s_Settings____00473318,
                          (uintptr_t)&LAB_0043d470,0x2000,0x00643ca4);
    E2R_InitRequesterItem(0x00643cc4,0xaa,0x14,0x41,10,(uintptr_t)s_Load_game____00473324,
                          (uintptr_t)&LAB_0043d490,0x2000,0x006439d8);
    E2R_InitRequesterItem(0x00643b10,0xaa,0x14,0x32,10,(uintptr_t)s_Save_game____00473334,
                          (uintptr_t)&LAB_0043d47c,0x2000,0x00643cc4);
    E2R_InitRequesterItem(0x00643af0,0xaa,0x14,0x23,10,(uintptr_t)s_Start_game__Female__00473344,
                          (uintptr_t)&LAB_0043d464,0x2000,0x00643b10);
    E2R_InitRequesterItem(0x00643b30,0xaa,0x14,0x14,10,(uintptr_t)s_Start_game_00473358,
                          (uintptr_t)&LAB_0043d458,0x2000,0x00643b10);
  }
  else {
    E2R_InitRequesterItem(0x00643ca4,0xaa,0x14,0x82,10,(uintptr_t)_DAT_0060ae80,
                          (uintptr_t)&DAT_0043d49c,0x2000,0x00643780);
    E2R_InitRequesterItem(0x00643ad0,0xaa,0x14,0x69,10,(uintptr_t)_DAT_0060aeb8,
                          (uintptr_t)&DAT_0043d4c0,0x2000,0x00643ca4);
    E2R_InitRequesterItem(0x006439d8,0xaa,0x14,0x50,10,(uintptr_t)_DAT_0060ae84,
                          (uintptr_t)&LAB_0043d470,0x2000,0x00643ca4);
    E2R_InitRequesterItem(0x00643cc4,0xaa,0x14,0x41,10,(uintptr_t)_DAT_0060ae88,
                          (uintptr_t)&LAB_0043d490,0x2000,0x006439d8);
    E2R_InitRequesterItem(0x00643b10,0xaa,0x14,0x32,10,(uintptr_t)_DAT_0060ae8c,
                          (uintptr_t)&LAB_0043d47c,0x2000,0x00643cc4);
    E2R_InitRequesterItem(0x00643af0,0xaa,0x14,0x23,10,(uintptr_t)_DAT_0060ae90,
                          (uintptr_t)&LAB_0043d464,0x2000,0x00643b10);
    E2R_InitRequesterItem(0x00643b30,0xaa,0x14,0x14,10,(uintptr_t)_DAT_0060ae94,
                          (uintptr_t)&LAB_0043d458,0x2000,0x00643b10);
  }
  E2R_InitRequesterItem(0x00643780,0x38,-0x42,-0x14,0xc,(uintptr_t)s_Cancel_0047329c,
                        (uintptr_t)&LAB_0043c4e8,0x2000,0);
}

static void E2R_InitRequesterYesNoPromptItems(void)
{
  if (DAT_00479e00 == 0) {
    E2R_InitRequesterItem(0x00643dc4,0x32,10,0xc,0xc,(uintptr_t)(char *)0x004732a4,
                          (uintptr_t)&LAB_0043c594,0x2000,0);
    E2R_InitRequesterItem(0x00643c84,0x32,-0x3c,0xc,0xc,(uintptr_t)(char *)0x004732a8,
                          (uintptr_t)&LAB_0043c4e8,0x2000,0x00643dc4);
  }
  else {
    E2R_InitRequesterItem(0x00643dc4,0x32,10,0xc,0xc,(uintptr_t)_DAT_0060ae78,
                          (uintptr_t)&LAB_0043c594,0x2000,0);
    E2R_InitRequesterItem(0x00643c84,0x32,-0x3c,0xc,0xc,(uintptr_t)_DAT_0060ae7c,
                          (uintptr_t)&LAB_0043c4e8,0x2000,0x00643dc4);
  }
}
`;
source = source.replace("\n\n/* 00410078 */", `${ctypeTableState}\n${requesterActionState}\n${requesterFocusState}\n${menuStringState}\n${streamLineState}\n${configHeaderState}\n${cursorMaskState}\n${startupPartNames}\n${glyphTableMirror}\n${hudIconNameState}\n${requesterRecordState}\n\n/* 00410078 */`);
source = source.replace("\n\n/* 00410078 */", `${packedNameState}\n${actionCodeState}\n\n/* 00410078 */`);
source = source.replace(/\(&DAT_00476e8c\)\[([^\]]+)\]/g, "E2R_CtypeFlags($1)");
source = source.replace(/\(&DAT_00476f90\)\[([^\]]+)\]/g, "E2R_BitMask($1)");
source = source.replace(/&DAT_00479e24/g, "(char *)0x00479e24");
source = source.replace(/\(int\)&DAT_0047aad8/g, "0x0047aad8");
source = source.replace(/\(&DAT_0047aad8\)\[([^\]]+)\]/g, "((short *)0x0047aad8)[$1]");
source = source.replace(/&DAT_(0047[2-5][0-9a-fA-F]{3})/g, "(char *)0x$1");
source = source.replace(/&DAT_(0047a[0-9a-fA-F]{3})/g, (match, symbol) => {
  const address = parseInt(symbol, 16);
  if (address < 0x0047a518 || 0x0047a6f4 < address) {
    return match;
  }
  return `(undefined1 *)0x${symbol.toLowerCase()}`;
});
source = source.replace(/&DAT_0047a29c/g, "(undefined1 *)0x0047a29c");
source = source.replace(/&DAT_006430ee/g, "(undefined1 *)0x006430ee");
source = source.replace(/_DAT_006432ec/g, "*(undefined4 *)0x006432ec");
source = source.replace(/&DAT_00636150/g, "(undefined1 *)0x00636150");
source = source.replace(/&DAT_006366dc/g, "(undefined1 *)0x006366dc");
const menuRecordBuilder = `\nstatic int E2R_menu_record_build_index;\n\nstatic void E2R_ResetMenuRecordBuilder(void)\n{\n  E2R_menu_record_build_index = 0;\n}\n\nstatic int E2R_NextMenuRecordTarget(short **target,short *width)\n{\n  int index = E2R_menu_record_build_index++;\n  int dest = 0;\n  int w = 0;\n\n  switch (index) {\n  case 0: dest = 0x643de4; w = -0x14; break;\n  case 1: dest = 0x643e04; w = -0x14; break;\n  case 2: dest = 0x643d84; w = -0x14; break;\n  case 3: dest = 0x643780; w = -0x14; break;\n  case 4: dest = 0x643dc4; w = -0x14; break;\n  case 5: dest = 0x643c84; w = -0x14; break;\n  case 6: dest = 0x643700; w = -0x14; break;\n  case 13: dest = 0x643d24; w = 0x5a; break;\n  case 14: dest = 0x643e24; w = 0x5a; break;\n  case 15: dest = 0x643d44; w = 0x68; break;\n  case 16: dest = 0x643d64; w = 0x68; break;\n  case 17: dest = 0x643da4; w = 0x3c; break;\n  case 18: dest = 0x643d04; w = 0x14; break;\n  case 19: dest = 0x643740; w = 0x14; break;\n  case 20: dest = 0x6436c0; w = 0x28; break;\n  case 21: dest = 0x6438b8; w = 0x3c; break;\n  case 22: dest = 0x643838; w = 0x28; break;\n  case 23: dest = 0x643918; w = 0x3c; break;\n  case 24: dest = 0x643720; w = 0x50; break;\n  case 25: dest = 0x643ca4; w = 0x82; break;\n  case 26: dest = 0x643ad0; w = 0x69; break;\n  case 27: dest = 0x6439d8; w = 0x50; break;\n  case 28: dest = 0x643cc4; w = 0x41; break;\n  case 29: dest = 0x643b10; w = 0x32; break;\n  case 30: dest = 0x643af0; w = 0x23; break;\n  case 31: dest = 0x643b30; w = 0x14; break;\n  case 32: dest = 0x6439b8; w = 0x1e; break;\n  case 33: dest = 0x6437a0; w = 0x1e; break;\n  case 34: dest = 0x6437be; w = 0x28; break;\n  case 35: dest = 0x6437dc; w = 0x32; break;\n  case 36: dest = 0x6437fa; w = 0x3c; break;\n  case 37: dest = 0x643818; w = 0x46; break;\n  case 38: dest = 0x643ce4; w = 0x19; break;\n  case 39: dest = 0x643978; w = 0x19; break;\n  case 40: dest = 0x6438d8; w = 0x1e; break;\n  case 60: dest = 0x643878; w = 0x14; break;\n  case 61: dest = 0x643898; w = 0x0a; break;\n  case 62: dest = 0x643938; w = 0x14; break;\n  case 71: dest = 0x643b90; w = 0x7d; break;\n  case 90: dest = 0x643760; w = 0x14; break;\n  case 96: dest = 0x643858; w = 0x64; break;\n  case 97: dest = 0x643998; w = 0x1e; break;\n  case 98: dest = 0x6439f8; w = 0x2d; break;\n  case 99: dest = 0x643958; w = 0x3c; break;\n  case 100: dest = 0x643a18; w = 0x3c; break;\n  case 101: dest = 0x6436e0; w = 0x4b; break;\n  default:\n    if (7 <= index && index <= 12) {\n      dest = 0x643ee4 - (index - 7) * 0x20;\n      w = 0x46 - (index - 7) * 0x0a;\n    }\n    else if (41 <= index && index <= 50) {\n      dest = 0x642fb0 + (index - 41) * 0x1e;\n      w = 0x25 + (index - 41) * 0x0b;\n    }\n    else if (51 <= index && index <= 59) {\n      dest = 0x6432f8 + (index - 51) * 0x1e;\n      w = 0x25 + (index - 51) * 0x0b;\n    }\n    else if (63 <= index && index <= 70) {\n      dest = 0x640244 + (index - 63) * 0x1e;\n      w = 0x23 + (index - 63) * 0x0a;\n    }\n    else if (72 <= index && index <= 89) {\n      dest = 0x6430dc + (index - 72) * 0x1e;\n      w = 0x0a + (index - 72) * 9;\n    }\n    else if (91 <= index && index <= 95) {\n      dest = 0x643a38 + (index - 91) * 0x1e;\n      w = 0x23 + (index - 91) * 0x0a;\n    }\n    else {\n      return 0;\n    }\n    break;\n  }\n  *target = (short *)(uintptr_t)dest;\n  *width = (short)w;\n  return 1;\n}\n`;
source = source.replace("\n\n/* 0043fe24 */", `${menuRecordBuilder}\n\n/* 0043fe24 */`);
source = source.replace(/&DAT_0047([0-9a-fA-F]{4})/g, (match, suffix) => {
  const address = parseInt(`0047${suffix}`, 16);
  if (address < 0x00477010 || 0x00479c94 < address) {
    return match;
  }
  return `(undefined1 *)0x0047${suffix.toLowerCase()}`;
});
source = source.replace(/\(int\)&DAT_00479e8a/g, "(int)(undefined1 *)0x00479e8a");
source = source.replace(/&DAT_00479e8e/g, "(undefined1 *)0x00479e8e");
source = source.replace(/&DAT_00479e92/g, "(undefined1 *)0x00479e92");
source = source.replace(/(undefined8 __fastcall FUN_0043b384\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  ulonglong uVar11;\r?\n\s*)DAT_0047a788 = 1;/, "$1in_EAX = (short *)(uintptr_t)param_1;\n  E2R_requester_probe_b384_count++;\n  E2R_requester_probe_b384_last_ptr = (uintptr_t)in_EAX;\n  if (IsBadReadPtr(in_EAX,0x40) || (uintptr_t)in_EAX >= 0x70000000u) {\n    E2R_requester_probe_b384_bad_ptr_count++;\n    in_EAX = (short *)FUN_0043aeac();\n    E2R_requester_probe_b384_last_ptr = (uintptr_t)in_EAX;\n    if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,0x40) || (uintptr_t)in_EAX >= 0x70000000u) {\n      return (ulonglong)param_2 << 32;\n    }\n  }\n  param_1 = (undefined4)(uintptr_t)in_EAX;\n  DAT_0047a788 = 1;");
source = source.replace(/(void __fastcall\s*\r?\nFUN_0043fe24\(short param_1,short param_2,short param_3,undefined4 param_4,undefined4 param_5,\s*\r?\n\s*short param_6,undefined4 param_7\)[\s\S]*?\r?\n  short unaff_BX;\r?\n\s*)if \(DAT_0047a43c == 0\) \{/, "$1if (!E2R_NextMenuRecordTarget(&in_EAX,&unaff_BX)) {\n    return;\n  }\n  if (DAT_0047a43c == 0) {");
source = source.replace(/(void FUN_0043fea4\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n  char \*pcVar8;\r?\n\s*)if \(DAT_00479e00 == 0\) \{/, "$1E2R_ResetMenuRecordBuilder();\n  if (DAT_00479e00 == 0) {");
source = source.replace("  *(undefined1 *)(_DAT_006438c0 + 4) = 0x87;", "  if (_DAT_006438c0 != 0) {\n    *(undefined1 *)(_DAT_006438c0 + 4) = 0x87;\n  }");
source = source.replace(/(void __fastcall FUN_004537bc\(undefined4 param_1\)[\s\S]*?\r?\n  undefined8 uVar1;\r?\n\s*)if \(\*\(int \*\)\(in_EAX \+ 0x38\) != 0\) \{/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x3c)) return;\n  if (*(int *)(in_EAX + 0x38) != 0) {");
source = source.replace(/(void __fastcall FUN_00422368\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  int iVar4;\r?\n\s*)iVar1 = \*\(int \*\)\(\(int\)in_EAX \+ 6\) >> 0x10;/, "$1in_EAX = (int *)(uintptr_t)param_1;\n  if (E2R_IsBadWritePtr(in_EAX,0x14) || (uintptr_t)in_EAX >= 0x70000000u) return;\n  iVar1 = *(int *)((int)in_EAX + 6) >> 0x10;");
source = source.replace(/(void __fastcall FUN_00422460\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  int iVar5;\r?\n\s*)iVar5 = \*\(int \*\)\(\(param_2 & 0xffff\) \* 2 \+ 0x59b58e\) >> 0x10;/, "$1in_EAX = (short *)(uintptr_t)param_1;\n  if (E2R_IsBadWritePtr(in_EAX,0x14) || (uintptr_t)in_EAX >= 0x70000000u) return;\n  iVar5 = *(int *)((param_2 & 0xffff) * 2 + 0x59b58e) >> 0x10;");
source = source.replace(/(void __fastcall FUN_00422538\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  int iVar4;\r?\n\s*)iVar3 = \*\(int \*\)\(\(param_2 & 0xffff\) \* 2 \+ 0x59b58e\) >> 0x10;/, "$1in_EAX = (int *)(uintptr_t)param_1;\n  if (E2R_IsBadWritePtr(in_EAX,0x14) || (uintptr_t)in_EAX >= 0x70000000u) return;\n  iVar3 = *(int *)((param_2 & 0xffff) * 2 + 0x59b58e) >> 0x10;");
source = source.replace(/(void __fastcall FUN_00422628\(undefined4 param_1,undefined2 \*param_2\)[\s\S]*?\r?\n  undefined2 \*in_EAX;\r?\n\s*)\*in_EAX = \*param_2;/, "$1in_EAX = (undefined2 *)(uintptr_t)param_1;\n  if (E2R_IsBadWritePtr(in_EAX,0x14) || IsBadReadPtr(param_2,0x14) ||\n      (uintptr_t)in_EAX >= 0x70000000u || (uintptr_t)param_2 >= 0x70000000u) return;\n  *in_EAX = *param_2;");
source = source.replace(
  /void FUN_00422330\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00422368 \*\//,
  "static void E2R_SetIdentityMatrix(undefined2 *matrix)\n{\n  if (E2R_IsBadWritePtr(matrix,0x12) || (uintptr_t)matrix >= 0x70000000u) return;\n  matrix[0] = 0x4000;\n  matrix[1] = 0;\n  matrix[2] = 0;\n  matrix[3] = 0;\n  matrix[4] = 0x4000;\n  matrix[5] = 0;\n  matrix[6] = 0;\n  matrix[7] = 0;\n  matrix[8] = 0x4000;\n}\n\nstatic void E2R_ApplyEulerMatrix(short *matrix,short *angles)\n{\n  if (IsBadReadPtr(angles,6) || (uintptr_t)angles >= 0x70000000u) return;\n  E2R_SetIdentityMatrix((undefined2 *)matrix);\n  if (angles[1] != 0) {\n    FUN_00422460(matrix,(int)angles[1]);\n  }\n  if (angles[0] != 0) {\n    FUN_00422368(matrix,(int)angles[0]);\n  }\n  if (angles[2] != 0) {\n    FUN_00422538(matrix,(int)angles[2]);\n  }\n}\n\n\n\n/* 00422330 */\n\nvoid FUN_00422330(void)\n\n{\n  E2R_SetIdentityMatrix((undefined2 *)0x006372aa);\n  return;\n}\n\n\n\n/* 00422368 */"
);
source = source.replace(
  /void FUN_00422f44\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00422f8c \*\//,
  "void FUN_00422f44(void)\n\n{\n  E2R_ApplyEulerMatrix((short *)0x006372aa,(short *)0x006372bc);\n  return;\n}\n\n\n\n/* 00422f8c */"
);
source = source.replace(
  "    FUN_00422330();\n    uVar4 = extraout_ECX;\n    if (_DAT_006372c0 != 0) {\n      FUN_00422538(extraout_ECX,(int)_DAT_006372c0);\n      uVar4 = extraout_ECX_00;\n    }\n    if (_DAT_006372bc != 0) {\n      FUN_00422368(uVar4,(int)_DAT_006372bc);\n      uVar4 = extraout_ECX_01;\n    }\n    if (_DAT_006372be != 0) {\n      FUN_00422460(uVar4,(int)_DAT_006372be);\n    }\n  }\n  else {\n    FUN_00422f44();\n  }",
  "    E2R_SetIdentityMatrix((undefined2 *)0x006372aa);\n    uVar4 = 0x006372aa;\n    if (_DAT_006372c0 != 0) {\n      FUN_00422538(uVar4,(int)_DAT_006372c0);\n    }\n    if (_DAT_006372bc != 0) {\n      FUN_00422368(uVar4,(int)_DAT_006372bc);\n    }\n    if (_DAT_006372be != 0) {\n      FUN_00422460(uVar4,(int)_DAT_006372be);\n    }\n  }\n  else {\n    E2R_ApplyEulerMatrix((short *)0x006372aa,(short *)0x006372bc);\n  }"
);
source = source.replace("      FUN_00422f44();\n      _DAT_006372da = _DAT_006372c2;", "      E2R_ApplyEulerMatrix((short *)0x00637298,(short *)0x006372ce);\n      _DAT_006372da = _DAT_006372c2;");
source = source.replace(
  "      FUN_00422330();\n      uVar4 = extraout_ECX_02;\n      if (_DAT_006372d2 != 0) {\n        FUN_00422538(extraout_ECX_02,(int)_DAT_006372d2);\n        uVar4 = extraout_ECX_03;\n      }\n      if (_DAT_006372ce != 0) {\n        FUN_00422368(uVar4,(int)_DAT_006372ce);\n        uVar4 = extraout_ECX_04;\n      }\n      if (_DAT_006372d0 != 0) {\n        FUN_00422460(uVar4,(int)_DAT_006372d0);\n      }",
  "      E2R_SetIdentityMatrix((undefined2 *)0x00637298);\n      uVar4 = 0x00637298;\n      if (_DAT_006372d2 != 0) {\n        FUN_00422538(uVar4,(int)_DAT_006372d2);\n      }\n      if (_DAT_006372ce != 0) {\n        FUN_00422368(uVar4,(int)_DAT_006372ce);\n      }\n      if (_DAT_006372d0 != 0) {\n        FUN_00422460(uVar4,(int)_DAT_006372d0);\n      }"
);
source = source.replace("      FUN_00422f44();\n      _DAT_006372e6 = _DAT_006372c2;", "      E2R_ApplyEulerMatrix((short *)0x00637274,(short *)0x006372e0);\n      _DAT_006372e6 = _DAT_006372c2;");
source = source.replace(
  "      FUN_00422330();\n      uVar4 = extraout_ECX_06;\n      if (_DAT_006372e4 != 0) {\n        FUN_00422538(extraout_ECX_06,(int)_DAT_006372e4);\n        uVar4 = extraout_ECX_07;\n      }\n      if (_DAT_006372e0 != 0) {\n        FUN_00422368(uVar4,(int)_DAT_006372e0);\n        uVar4 = extraout_ECX_08;\n      }\n      if (_DAT_006372e2 != 0) {\n        FUN_00422460(uVar4,(int)_DAT_006372e2);\n      }",
  "      E2R_SetIdentityMatrix((undefined2 *)0x00637274);\n      uVar4 = 0x00637274;\n      if (_DAT_006372e4 != 0) {\n        FUN_00422538(uVar4,(int)_DAT_006372e4);\n      }\n      if (_DAT_006372e0 != 0) {\n        FUN_00422368(uVar4,(int)_DAT_006372e0);\n      }\n      if (_DAT_006372e2 != 0) {\n        FUN_00422460(uVar4,(int)_DAT_006372e2);\n      }"
);
source = source.replace(/(undefined8 __fastcall FUN_004618f9\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  int \*piVar3;\r?\n\s*)piVar1 = DAT_0047d260;/, "$1in_EAX = (int *)(uintptr_t)param_1;\n  if (in_EAX == 0) return (ulonglong)param_2 << 32;\n  piVar1 = DAT_0047d260;");
source = source.replace(/(int __fastcall FUN_0045e54d\(undefined4 param_1,byte \*param_2\)[\s\S]*?\r?\n  byte \*in_EAX;\r?\n\s*)while\( true \) \{/, "$1in_EAX = (byte *)(uintptr_t)param_1;\n  while( true ) {");
source = source.replace("_DAT_00636158 = FUN_0045f1ff(param_1,0x4b281);", "_DAT_00636158 = FUN_0045f1ff(1,0x4b281);");
source = source.replace("_DAT_0063615c = FUN_0045f1ff(uVar1,0x4b281);", "_DAT_0063615c = FUN_0045f1ff(1,0x4b281);");
source = source.replace("_DAT_00636668 = FUN_0045f1ff(0,0x4b281);", "_DAT_00636668 = FUN_0045f1ff(2,0x4b281);");
source = source.replace("_DAT_0063666c = FUN_0045f1ff(uVar1,0x4b281);", "_DAT_0063666c = FUN_0045f1ff(2,0x4b281);");
source = source.replace("_DAT_00636670 = FUN_0045f1ff(uVar1,0x4b281);", "_DAT_00636670 = FUN_0045f1ff(2,0x4b281);");
source = source.replace("_DAT_006366a4 = (undefined4 *)FUN_0045f1ff(extraout_ECX_14,4000);", "_DAT_006366a4 = (undefined4 *)FUN_0045f1ff(1,4000);");
source = source.replace("_DAT_006366f4 = (undefined1 *)FUN_0045f1ff(~uVar3 - 1,0x9c4);", "_DAT_006366f4 = (undefined1 *)FUN_0045f1ff(1,0x9c4);");
source = source.replace("_DAT_0063669c = (undefined1 *)FUN_0045f1ff(uVar5,0x9c4);", "_DAT_0063669c = (undefined1 *)FUN_0045f1ff(1,0x9c4);");
source = source.replace("_DAT_00636698 = (char *)FUN_0045f1ff(uVar5,24000);", "_DAT_00636698 = (char *)FUN_0045f1ff(1,24000);");
source = source.replace("_DAT_0063668c = (char *)FUN_0045f1ff(~uVar3 - 1,4000);", "_DAT_0063668c = (char *)FUN_0045f1ff(1,4000);");
source = source.replace("_DAT_00636678 = (undefined4 *)FUN_0045f1ff(~uVar3 - 1,5000);", "_DAT_00636678 = (undefined4 *)FUN_0045f1ff(1,5000);");
source = source.replace("_DAT_00636694 = (undefined1 *)FUN_0045f1ff(~uVar3 - 1,0x5dc);", "_DAT_00636694 = (undefined1 *)FUN_0045f1ff(1,0x5dc);");
source = source.replace("_DAT_00636680 = (char *)FUN_0045f1ff(uVar5,2000);", "_DAT_00636680 = (char *)FUN_0045f1ff(1,2000);");
source = source.replace("_DAT_006366a0 = (undefined2 *)FUN_0045f1ff(~uVar3 - 1,20000);", "_DAT_006366a0 = (undefined2 *)FUN_0045f1ff(2,20000);");
source = source.replace("DAT_00479e04 = FUN_0045f1ff(param_1,0x4b281);", "DAT_00479e04 = FUN_0045f1ff(1,0x4b281);");
source = source.replace("DAT_00479e08 = FUN_0045f1ff(uVar1,0xa0000);", "DAT_00479e08 = FUN_0045f1ff(1,0xa0000);");
source = source.replace(
  "  FUN_0045f0a1((int)auStack_48,(byte *)s__sCODE_ECSTATIC_FAN_00470370);",
  "  E2R_FormatOneString((char *)auStack_48,s__sCODE_ECSTATIC_FAN_00470370,(char *)0x00479e24);"
);
source = source.replace(
  "  iVar3 = FUN_00445378(extraout_ECX_41,0);",
  "  iVar3 = FUN_00445378((undefined4)(uintptr_t)auStack_48,0);"
);
source = source.replace(
  "    FUN_0045f0a1((int)auStack_16c,(byte *)s__sactions__00470490);",
  "    E2R_FormatOneString((char *)auStack_16c,s__sactions__00470490,(char *)0x00479e24);"
);
source = source.replace(
  "    FUN_0045f0a1((int)auStack_9c,(byte *)s_files_ECSTATIC_0047049c);\n    uVar11 = FUN_004452e0(extraout_ECX_48,extraout_EDX_20);",
  "    E2R_FormatOneString((char *)auStack_9c,s_files_ECSTATIC_0047049c,(char *)0x00479e24);\n    uVar11 = FUN_004452e0((undefined4)(uintptr_t)\"Files/ECSTATIC\",extraout_EDX_20);"
);
source = source.replace(
  "      FUN_0045f0a1((int)auStack_9c,(byte *)s_files_ECST2_004704ac);\n      uVar11 = FUN_004452e0(extraout_ECX_50,extraout_EDX_21);",
  "      E2R_FormatOneString((char *)auStack_9c,s_files_ECST2_004704ac,(char *)0x00479e24);\n      uVar11 = FUN_004452e0((undefined4)(uintptr_t)auStack_9c,extraout_EDX_21);"
);
source = source.replace(
  "      FUN_0045f0a1((int)auStack_9c,(byte *)s__sfiles_ECSTATIC_004704d0);",
  "      E2R_FormatOneString((char *)auStack_9c,s__sfiles_ECSTATIC_004704d0,(char *)0x00479e24);"
);
source = source.replace(
  "      uVar11 = FUN_00445330(extraout_ECX_52);",
  "      uVar11 = FUN_00445330((undefined4)(uintptr_t)auStack_9c);"
);
source = source.replace(
  /void FUN_00414f40\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00415b78 \*\//,
  "void FUN_00414f40(void)\n\n{\n  const double pi = 3.14159265358979323846;\n  int mode;\n  int x;\n  int y;\n\n  for (x = 0; x < 256; x = x + 1) {\n    double phase = ((double)x * pi) / 128.0;\n    double normalized = (double)x / 255.0;\n    int tangent_index = (x & 0x40) != 0 ? x : 64 - x;\n    double tangent = tan(((double)tangent_index * pi) / 128.0);\n\n    *(byte *)(0x005fe990 + x) = E2R_clamp_byte(E2R_round_to_int(sin(phase) * 127.0 + 128.0));\n    *(byte *)(0x005fe890 + x) = E2R_clamp_byte(E2R_round_to_int(cos(phase) * 127.0 + 128.0));\n    *(byte *)(0x0060af88 + x) = E2R_clamp_byte(E2R_round_to_int(sqrt(normalized) * 255.0));\n    *(byte *)(0x0060b088 + x) = E2R_clamp_byte(E2R_round_to_int((1.0 - sqrt(normalized)) * 255.0));\n    *(short *)(0x0067be7c + x * 2) = E2R_clamp_short(E2R_round_to_int(tangent * 1024.0));\n  }\n\n  for (x = 0; x < 256; x = x + 1) {\n    *(byte *)(0x005fe790 + x) = E2R_clamp_byte(x);\n  }\n\n  for (x = 0; x < 1024; x = x + 1) {\n    double phase = (((double)x + 0.5) * pi) / 512.0;\n    *(short *)(0x0060c4b8 + x * 2) = E2R_clamp_short(E2R_round_to_int(sin(phase) * 32767.0));\n  }\n\n  for (mode = 0; mode < 16; mode = mode + 1) {\n    int base = 0x00507590 + mode * 0x4000;\n    int bias = mode * 32;\n    for (y = 0; y < 128; y = y + 1) {\n      for (x = 0; x < 128; x = x + 1) {\n        int shade = ((x * y) >> 7) + bias;\n        *(byte *)(base + y * 128 + x) = E2R_clamp_byte(shade);\n      }\n    }\n  }\n\n  for (y = 0; y < 128; y = y + 1) {\n    for (x = 0; x < 128; x = x + 1) {\n      *(byte *)(0x00507590 + 0x40000 + y * 128 + x) = 0x80;\n    }\n  }\n  return;\n}\n\n\n\n/* 00415b78 */"
);
source = source.replace("piVar3 = (int *)FUN_0045eb05(param_1,&DAT_0047007c);", "piVar3 = (int *)FUN_0045eb05(param_1,\"shadow.dat\");");
source = source.replace(
  "  iVar3 = FUN_0045eb05(extraout_ECX_07,extraout_EDX_02);",
  "  iVar3 = FUN_0045eb05((undefined4)(uintptr_t)\"CDPath\",&DAT_0047007c);"
);
source = source.replace(
  "    FUN_0045ebf1();",
  "    E2R_ReadStreamLine((undefined4)(uintptr_t)iVar3,(char *)0x00479e24,0x14);"
);
source = source.replace(
  "    } while (cVar2 != '\\0');\n    FUN_0045ec6c(iVar3,(uint)(byte)(cVar1 + 1U));",
  "    } while (cVar2 != '\\0');\n    E2R_UseHostedCdPath((char *)0x00479e24);\n    FUN_0045ec6c(iVar3,(uint)(byte)(cVar1 + 1U));"
);
source = source.replace(
  /(void FUN_0041ccf0\(void\)[\s\S]*?\r?\n\s*)undefined1 \*in_EAX;/,
  "$1undefined1 *in_EAX = (undefined1 *)0x00684a68;"
);
source = source.replace(
  /undefined8 __fastcall FUN_0041ce88\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0041cf44 \*\//,
  "undefined8 __fastcall FUN_0041ce88(undefined4 param_1,undefined4 param_2)\n\n{\n  byte *data;\n  undefined4 *stream;\n  int x;\n  int y;\n  \n  (void)param_1;\n  stream = (undefined4 *)(uintptr_t)E2R_OpenReadStream(\"shademap.dat\");\n  if (stream == (undefined4 *)0x0) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  if ((uint)stream[1] < 0xc000) {\n    FUN_0045ec6c(0,(undefined4)(uintptr_t)stream);\n    return (ulonglong)param_2 << 0x20;\n  }\n  data = (byte *)(uintptr_t)stream[5];\n  for (y = 0; y < 0x80; y = y + 1) {\n    for (x = 0; x < 0x80; x = x + 1) {\n      *(byte *)(0x0061d030 + y * 0x80 + x) = data[0];\n      *(short *)(0x00621630 + y * 0x100 + x * 2) = (short)((uint)data[1] << 8 | (uint)data[2]);\n      data = data + 3;\n    }\n  }\n  FUN_0045ec6c(0,(undefined4)(uintptr_t)stream);\n  return CONCAT44(param_2,1);\n}\n\n\n\n/* 0041cf44 */"
);
source = source.replace("(&DAT_0068cd68)[iVar5] = 0;", "*(undefined1 *)(0x0068cd68 + iVar5) = 0;");
source = source.replace(/&DAT_0068cd68/g, "(undefined1 *)0x0068cd68");
source = source.replace(/&DAT_0068cd69/g, "(undefined1 *)0x0068cd69");
source = source.replace(/&DAT_0068cd6a/g, "(undefined1 *)0x0068cd6a");
source = source.replace(/&DAT_0068cd6f/g, "(undefined1 *)0x0068cd6f");
source = source.replace(/&DAT_0068cd70/g, "(undefined1 *)0x0068cd70");
source = source.replace(/&DAT_0068cd72/g, "(undefined1 *)0x0068cd72");
source = source.replace(/&DAT_0067c728/g, "(undefined1 *)0x0067c728");
source = source.replace(/&DAT_0067c72a/g, "(undefined1 *)0x0067c72a");
source = source.replace(/&DAT_0067c72c/g, "(undefined1 *)0x0067c72c");
source = source.replace(/&DAT_0067c72e/g, "(undefined1 *)0x0067c72e");
source = source.replace(/&DAT_0067c730/g, "(undefined1 *)0x0067c730");
source = source.replace(/&DAT_0067c732/g, "(undefined1 *)0x0067c732");
source = source.replace(/&DAT_0067c734/g, "(undefined1 *)0x0067c734");
source = source.replace(
  "  _DAT_0067c728 = 0;\n  _DAT_0067c72a = 0xfe70;\n  _DAT_0067c72c = 0x800;\n  _DAT_0067c72e = 0;\n  _DAT_0067c730 = 0x8000;\n  _DAT_0067c732 = 0;\n  _DAT_0073ccba = 0;\n  _DAT_0067c734 = 0x400;",
  "  *(undefined2 *)0x0067c728 = 0;\n  *(undefined2 *)0x0067c72a = 0xfe70;\n  *(undefined2 *)0x0067c72c = 0x800;\n  *(undefined2 *)0x0067c72e = 0;\n  *(undefined2 *)0x0067c730 = 0x8000;\n  *(undefined2 *)0x0067c732 = 0;\n  _DAT_0073ccba = 0;\n  *(undefined2 *)0x0067c734 = 0x400;"
);
source = source.replace(
  /undefined4 __fastcall FUN_0045eb05\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045ebf1 \*\//,
  "undefined4 __fastcall FUN_0045eb05(undefined4 param_1,undefined4 param_2)\n\n{\n  LPCSTR path;\n  \n  path = (LPCSTR)(uintptr_t)param_1;\n  if ((uintptr_t)path < 0x10000) {\n    path = (LPCSTR)(uintptr_t)param_2;\n  }\n  if ((uintptr_t)path < 0x10000) {\n    return 0;\n  }\n  return E2R_OpenReadStream(path);\n}\n\n\n\n/* 0045ebf1 */"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045ec6c\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n  undefined4 extraout_ECX;\r?\n\s*)\(\*\(code \*\)PTR_FUN_0047d3b0\)\(\);/,
  "$1undefined4 *stream;\n  \n  (void)param_1;\n  stream = (undefined4 *)(uintptr_t)param_2;\n  if ((uintptr_t)stream < 0x10000 || (uintptr_t)stream >= 0x70000000u ||\n      IsBadReadPtr(stream,0x1c)) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  if (stream[6] == E2R_STREAM_MAGIC) {\n    if (stream[5] != 0) {\n      LocalFree((HLOCAL)(uintptr_t)stream[5]);\n    }\n    stream[6] = 0;\n    LocalFree((HLOCAL)stream);\n    return (ulonglong)param_2 << 0x20;\n  }\n  (*(code *)PTR_FUN_0047d3b0)();"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045f38a\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n  undefined8 uVar5;\r?\n\s*)\(\*\(code \*\)PTR_FUN_0047d3a0\)\(\);/,
  "$1undefined4 *stream;\n  \n  (void)param_1;\n  stream = (undefined4 *)(uintptr_t)param_2;\n  if ((uintptr_t)stream < 0x10000 || (uintptr_t)stream >= 0x70000000u ||\n      IsBadReadPtr(stream,0x1c)) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  if (stream[6] == E2R_STREAM_MAGIC) {\n    return CONCAT44(param_2,E2R_ReadHostedStreamByte(stream));\n  }\n  (*(code *)PTR_FUN_0047d3a0)();"
);
source = source.replace(
  "  _DAT_0047a408 = 0xc;\n  _DAT_00636158 = _DAT_00636570;\n  DAT_0047a40c = 0xc;",
  "  _DAT_0047a408 = 0xc;\n  if (_DAT_00636570 != 0 && (uintptr_t)_DAT_00636570 < 0x70000000u &&\n      !E2R_IsBadWritePtr((void *)(uintptr_t)_DAT_00636570,_DAT_006401ec * _DAT_006401d4)) {\n    _DAT_00636158 = _DAT_00636570;\n  }\n  if (_DAT_00636158 == 0 || (uintptr_t)_DAT_00636158 >= 0x70000000u ||\n      E2R_IsBadWritePtr((void *)(uintptr_t)_DAT_00636158,_DAT_006401ec * _DAT_006401d4)) {\n    _DAT_00636158 = FUN_0045f1ff(1,_DAT_006401ec * _DAT_006401d4);\n  }\n  DAT_0047a40c = 0xc;"
);
source = source.replace(
  "  _DAT_00636570 = _DAT_00636158;\n  _DAT_00636150 = 0xa0000;\n  _DAT_00636154 = 0xa4b00;\n  _DAT_00636158 = 0xa9600;\n  FUN_0041af88(extraout_ECX_01,0xa9600);",
  "  _DAT_00636570 = _DAT_00636158;\n  if (_DAT_00636158 == 0 || (uintptr_t)_DAT_00636158 >= 0x70000000u ||\n      E2R_IsBadWritePtr((void *)(uintptr_t)_DAT_00636158,_DAT_006401ec * _DAT_006401d4)) {\n    _DAT_00636158 = FUN_0045f1ff(1,_DAT_006401ec * _DAT_006401d4);\n    _DAT_00636570 = _DAT_00636158;\n  }\n  FUN_0041af88(extraout_ECX_01,0xa9600);"
);
source = source.replace(
  /undefined4 __fastcall FUN_0045f1ff\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045f218 \*\//,
  "undefined4 __fastcall FUN_0045f1ff(undefined4 param_1,undefined4 param_2)\n\n{\n  void *buffer;\n  uint count;\n  uint size;\n  \n  count = (uint)(uintptr_t)param_1;\n  size = (uint)(uintptr_t)param_2;\n  if (count != 0 && 0xffffffffU / count < size) {\n    return 0;\n  }\n  size = count * size;\n  buffer = LocalAlloc(0x40,size == 0 ? 1 : size);\n  return (undefined4)(uintptr_t)buffer;\n}\n\n\n\n/* 0045f218 */"
);
source = source.replace(
  /undefined4 __fastcall FUN_00445378\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004453a4 \*\//,
  "undefined4 __fastcall FUN_00445378(undefined4 param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  undefined4 uVar2;\n  \n  iVar1 = FUN_0045eb05(param_1,&DAT_00474388);\n  uVar2 = 0;\n  if (iVar1 != 0) {\n    E2R_fan_parse_stream = (int *)(uintptr_t)iVar1;\n    uVar2 = FUN_004453a4((undefined4)(uintptr_t)iVar1,(int)(uintptr_t)param_2);\n    E2R_fan_parse_stream = (int *)0x0;\n    FUN_0045ec6c(0,(undefined4)(uintptr_t)iVar1);\n  }\n  return uVar2;\n}\n\n\n\n/* 004453a4 */"
);
source = source.replace(
  /(undefined8 __fastcall FUN_004171b8\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar7;\r?\n\s*)if \(\(\(\(in_EAX\[1\] < 1\)/,
  "$1if (E2R_fan_parse_stream != (int *)0x0) {\n    in_EAX = E2R_fan_parse_stream;\n  }\n  else {\n    in_EAX = (int *)(uintptr_t)param_1;\n  }\n  if ((uintptr_t)in_EAX < 0x10000u ||\n      (in_EAX != E2R_fan_parse_stream && IsBadReadPtr(in_EAX,0x1c))) {\n    return CONCAT44(param_2,0xffff);\n  }\n  if ((uint)in_EAX[6] == E2R_STREAM_MAGIC) {\n    iVar4 = E2R_ReadFanWordByte(in_EAX);\n    uVar3 = (uint)((iVar4 << 8) & 0xff00);\n    iVar4 = E2R_ReadFanWordByte(in_EAX);\n    uVar3 = uVar3 | ((uint)iVar4 & 0xff);\n    if (E2R_fan_word_read_diag_count < 64) {\n      E2R_fan_word_read_diag_count = E2R_fan_word_read_diag_count + 1;\n      fprintf(stderr,\"FAN word: ordinal=%u offset=%u value=%04x remaining=%d\\n\",\n              E2R_fan_word_read_diag_count,\n              (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                     (byte *)(uintptr_t)E2R_fan_parse_stream[5]),\n              (ushort)uVar3,E2R_fan_parse_stream[1]);\n    }\n    return CONCAT44(param_2,uVar3);\n  }\n  \n  if ((((in_EAX[1] < 1)"
);
source = source.replace(
  "    uVar6 = FUN_0045f38a(param_1,in_EAX);",
  "    uVar6 = FUN_0045f38a((undefined4)(uintptr_t)in_EAX,in_EAX);"
);
source = source.replace(
  "  uVar7 = FUN_0045f38a(iVar4,piVar5);",
  "  uVar7 = FUN_0045f38a((undefined4)(uintptr_t)piVar5,piVar5);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_004173c8\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar7;\r?\n\s*)if \(\(\(\(in_EAX\[1\] < 1\)/,
  "$1if (E2R_fan_parse_stream != (int *)0x0) {\n    in_EAX = E2R_fan_parse_stream;\n  }\n  else {\n    in_EAX = (int *)(uintptr_t)param_1;\n  }\n  if ((uintptr_t)in_EAX < 0x10000u ||\n      (in_EAX != E2R_fan_parse_stream && IsBadReadPtr(in_EAX,0x1c))) {\n    return CONCAT44(param_2,0xffff);\n  }\n  if ((uint)in_EAX[6] == E2R_STREAM_MAGIC) {\n    iVar4 = E2R_ReadFanWordByte(in_EAX);\n    uVar3 = (uint)iVar4 & 0xff;\n    iVar4 = E2R_ReadFanWordByte(in_EAX);\n    uVar3 = uVar3 | (((uint)iVar4 & 0xff) << 8);\n    return CONCAT44(param_2,uVar3);\n  }\n  if ((((in_EAX[1] < 1)"
);
source = source.replace(
  /(undefined4 __fastcall FUN_004453a4\(undefined4 param_1,int param_2\)[\s\S]*?\r?\n  int local_18;\r?\n\s*)local_20 = \(short \*\)0x0;/,
  "$1int e2r_table_indices[11] = {0};\n\n  in_EAX = E2R_fan_parse_stream;\n  if (in_EAX == (int *)0x0 || IsBadReadPtr(in_EAX,0x1c)) {\n    return 0;\n  }\n  \n  local_20 = (short *)0x0;"
);
source = source.replace(
  "  if (uVar11 != 0x46414e54) {\n    FUN_0043cac0(extraout_ECX_00,uVar11);\n    return 0;\n  }",
  "  if (uVar11 != 0x46414e54) {\n    if (E2R_archive_resource_diag_count < 16) {\n      E2R_archive_resource_diag_count = E2R_archive_resource_diag_count + 1;\n      fprintf(stderr,\"FAN header mismatch: value=%08x offset=%u\\n\",uVar11,E2R_FanStreamOffset());\n    }\n    return 0;\n  }"
);
source = source.replace(
  "\n\n\n/* 00447090 */",
  "\n\n\nstatic undefined4 E2R_ParseArchiveFanResource(void)\n{\n  int *previous_stream;\n  int *stream;\n  byte *base;\n  byte *end;\n  byte *cursor;\n  byte *scan;\n  uint ordinal;\n  uint original_offset;\n  uint mapped_offset;\n  uint count;\n  undefined4 result;\n\n  stream = (int *)(uintptr_t)DAT_0047a724;\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      (uint)stream[6] != E2R_STREAM_MAGIC) {\n    return 0;\n  }\n  base = (byte *)(uintptr_t)stream[5];\n  end = (byte *)(uintptr_t)stream[2];\n  cursor = (byte *)(uintptr_t)stream[0];\n  original_offset = (uint)(cursor - base);\n  mapped_offset = original_offset;\n  if ((cursor + 4 <= end) &&\n      (cursor[0] != 'F' || cursor[1] != 'A' || cursor[2] != 'N' || cursor[3] != 'T')) {\n    ordinal = original_offset;\n    if (0 < ordinal && ordinal < 0x10000u) {\n      count = 0;\n      for (cursor = base + 4; cursor + 4 <= end; cursor = cursor + 1) {\n        if (cursor[0] == 'F' && cursor[1] == 'A' && cursor[2] == 'N' && cursor[3] == 'T') {\n          count = count + 1;\n          if (count == ordinal) {\n            stream[0] = (int)(uintptr_t)cursor;\n            stream[1] = (int)(uint)(end - cursor);\n            mapped_offset = (uint)(cursor - base);\n            *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x40;\n            break;\n          }\n        }\n      }\n    }\n    else {\n      for (scan = cursor; scan >= base; scan = scan - 1) {\n        if (scan[0] == 'F' && scan[1] == 'A' && scan[2] == 'N' && scan[3] == 'T') {\n          stream[0] = (int)(uintptr_t)scan;\n          stream[1] = (int)(uint)(end - scan);\n          mapped_offset = (uint)(scan - base);\n          *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x40;\n          break;\n        }\n        if (scan == base) {\n          break;\n        }\n      }\n    }\n  }\n  previous_stream = E2R_fan_parse_stream;\n  E2R_fan_parse_stream = stream;\n  result = FUN_004453a4((undefined4)(uintptr_t)stream,1);\n  E2R_fan_parse_stream = previous_stream;\n  if (E2R_archive_parse_summary_count < 32) {\n    E2R_archive_parse_summary_count = E2R_archive_parse_summary_count + 1;\n    fprintf(stderr,\n            \"archive resource parse: input=%u mapped=%u result=%u final=%u remaining=%d\\n\",\n            original_offset,mapped_offset,(uint)result,\n            (uint)((byte *)(uintptr_t)stream[0] - base),stream[1]);\n  }\n  return result;\n}\n\n\n\n/* 00447090 */"
);
source = source.replace(
  "      FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x64f060));\n      FUN_004453a4(extraout_ECX_01,1);",
  "      FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x64f060));\n      E2R_ParseArchiveFanResource();"
);
source = source.replace(
  "        FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x663a10));\n        in_EAX = FUN_004453a4(extraout_ECX_04,1);",
  "        FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x663a10));\n        in_EAX = E2R_ParseArchiveFanResource();"
);
source = source.replace(
  /undefined8 __fastcall FUN_00451998\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00451a54 \*\//,
  "undefined8 __fastcall FUN_00451998(int param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  int rep_id;\n  int result;\n  undefined4 saved_current;\n  undefined4 extraout_ECX;\n  undefined4 extraout_ECX_00;\n  undefined4 extraout_ECX_01;\n  undefined4 extraout_ECX_02;\n  undefined4 extraout_ECX_03;\n  undefined4 extraout_ECX_04;\n  undefined4 extraout_ECX_05;\n  undefined4 extraout_EDX;\n  undefined8 uVar2;\n  \n  rep_id = (int)(short)param_1;\n  result = rep_id;\n  saved_current = DAT_0047a470;\n  if (-1 < rep_id) {\n    iVar1 = rep_id * 4;\n    if (*(int *)((undefined1 *)0x00635980 + iVar1) == 0) {\n      DAT_0047a788 = 1;\n      if (DAT_0047ab10 == 0) {\n        uVar2 = FUN_00442420((short)rep_id,iVar1);\n        FUN_0045f22f(extraout_ECX,(char *)uVar2);\n        uVar2 = FUN_00451c8c(extraout_ECX_00,extraout_EDX);\n        result = (int)uVar2;\n        DAT_0047a470 = saved_current;\n      }\n      else {\n        if (*(int *)(iVar1 + 0x663a10) < 0) {\n          FUN_00442420((short)rep_id,iVar1);\n          uVar2 = FUN_0043cbb4(extraout_ECX_02);\n          DAT_0047a470 = saved_current;\n          return CONCAT44(param_2,(int)uVar2);\n        }\n        FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x663a10));\n        result = E2R_ParseArchiveFanResource();\n        DAT_0047a470 = saved_current;\n      }\n    }\n  }\n  DAT_0047a470 = saved_current;\n  return CONCAT44(param_2,result);\n}\n\n\n\n/* 00451a54 */"
);
source = source.replace(
  "      FUN_00451998(param_1,psVar15);",
  "      FUN_00451998((int)local_6c[0x91],psVar15);"
);
source = source.replace(
  "        FUN_00451998(iVar7,psVar15);",
  "        FUN_00451998((int)local_6c[0x91],psVar15);"
);
source = source.replace(
  "      uVar18 = FUN_00451998(extraout_ECX_08,uVar14);",
  "      uVar18 = FUN_00451998((int)(short)uVar18,uVar14);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00442420)\(undefined4 param_1,undefined4 param_2\)([\s\S]*?\r?\n  short in_AX;\r?\n)/,
  "$1(short param_1,undefined4 param_2)$2"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00442420\(short param_1,undefined4 param_2\)[\s\S]*?\r?\n  char \*pcVar6;\r?\n\s*)if \(in_AX < 0\) \{/,
  "$1in_AX = param_1;\n  if (in_AX < 0) {"
);
source = source.replace(
  "      iVar2 = FUN_004453a4(uVar3,1);",
  "      iVar2 = E2R_ParseArchiveFanResource();"
);
source = source.replace(
  "      FUN_0045f296(in_EAX,*(int *)(iVar1 + 0x653840));\n      FUN_004453a4(extraout_ECX_04,1);\n      uVar4 = extraout_ECX_05;\n      uVar5 = extraout_EDX_00;",
  "      FUN_0045f296(in_EAX,*(int *)(iVar1 + 0x653840));\n      parse_result = E2R_ParseArchiveFanResource();\n      uVar4 = (undefined4)actor_id;\n      uVar5 = 0;"
);
source = source.replace(
  "            FUN_0045f296(param_1,*(int *)(iVar1 + 0x653840));\n            FUN_004453a4(extraout_ECX_04,1);\n            uVar6 = extraout_ECX_05;\n            uVar7 = extraout_EDX_00;",
  "            FUN_0045f296(param_1,*(int *)(iVar1 + 0x653840));\n            E2R_ParseArchiveFanResource();\n            uVar6 = (undefined4)(int)*psVar3;\n            uVar7 = 0;"
);
source = source.replace(
  "      iVar2 = FUN_004453a4(extraout_ECX_03,1);",
  "      iVar2 = E2R_ParseArchiveFanResource();"
);
source = source.replace(
  "          ((undefined1 *)0x0064a178)[(short)puVar13 * 2] = ((undefined1 *)0x0064a178)[(short)puVar13 * 2] & 0xfd;\n          FUN_00451f5c();\n          DAT_0047a470 = *(ushort **)((undefined1 *)0x00630b60 + (int)extraout_EDX_19 * 4);",
  "          E2R_actor_load_id_override = (int)(short)(*(ushort *)((int)local_2c + 2) & 0xfff);\n          ((undefined1 *)0x0064a178)[(short)(*(ushort *)((int)local_2c + 2) & 0xfff) * 2] =\n               ((undefined1 *)0x0064a178)[(short)(*(ushort *)((int)local_2c + 2) & 0xfff) * 2] &\n               0xfd;\n          FUN_00451f5c();\n          DAT_0047a470 =\n               *(ushort **)((undefined1 *)0x00630b60 +\n                            ((int)(short)(*(ushort *)((int)local_2c + 2) & 0xfff) * 4));\n          if (DAT_0047a470 != (ushort *)0x0) {\n            ((undefined4 *)(uintptr_t)DAT_0047a470)[0x41] = 4;\n          }"
);
source = source.replace(
  "          if (DAT_0047a470 != (ushort *)0x0) {\n            ((undefined4 *)(uintptr_t)DAT_0047a470)[0x41] = 4;\n          }\n          ((undefined4 *)(uintptr_t)DAT_0047a470)[0x41] = 4;",
  "          if (DAT_0047a470 != (ushort *)0x0) {\n            ((undefined4 *)(uintptr_t)DAT_0047a470)[0x41] = 4;\n          }"
);
source = source.replace(
  "      case 0x55:\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 5000) {\n          FUN_00451f5c();",
  "      case 0x55:\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 5000) {\n          E2R_actor_load_id_override = (int)(short)(*(ushort *)((int)local_2c + 2) & 0xfff);\n          FUN_00451f5c();"
);
source = source.replace(
  /      case 0x54:\r?\n        puVar13 = \(ushort \*\)\(CONCAT22\(uVar14,\*\(short \*\)\(\(int\)local_2c \+ 2\)\) & 0xffff0fff\);\r?\n        if \(\(ushort\)puVar13 < 5000\) \{[\s\S]*?        uVar25 = CONCAT44\(puVar18,_DAT_00ac4a54\);\r?\n        local_2c = local_2c \+ 1;\r?\n        break;\r?\n      case 0x55:/,
  `      case 0x54:
        iVar23 = (int)(short)(*(ushort *)((int)local_2c + 2) & 0xfff);
        puVar13 = (ushort *)(uintptr_t)iVar23;
        if (iVar23 < 5000) {
          psVar16 = *(short **)((undefined1 *)0x00630b60 + iVar23 * 4);
          if (psVar16 != (short *)0x0) {
            *(undefined4 *)((undefined1 *)0x00630b60 + *psVar16 * 4) = 0;
            FUN_00426ca4();
            if (psVar16 == _DAT_00637248) {
              _DAT_00637248 = *(short **)(_DAT_00637248 + 0x28);
              iVar12 = extraout_EDX_18;
            }
            else {
              iVar12 = *(int *)(_DAT_00637248 + 0x28);
              psVar4 = _DAT_00637248;
              iVar23 = iVar12;
              while (iVar23 != 0) {
                if (psVar16 == *(short **)(psVar4 + 0x28)) {
                  iVar12 = *(int *)(*(short **)(psVar4 + 0x28) + 0x28);
                  *(int *)(psVar4 + 0x28) = iVar12;
                  break;
                }
                psVar4 = *(short **)(psVar4 + 0x28);
                iVar23 = *(int *)(psVar4 + 0x28);
              }
            }
            FUN_0043a800((undefined4)(uintptr_t)psVar16,iVar12);
            puVar13 = extraout_ECX_33;
          }
          iVar23 = (int)(short)(*(ushort *)((int)local_2c + 2) & 0xfff);
          ((undefined1 *)0x0064a178)[iVar23 * 2] = ((undefined1 *)0x0064a178)[iVar23 * 2] & 0xfd;
          E2R_actor_load_id_override = iVar23;
          FUN_00451f5c();
          DAT_0047a470 = *(ushort **)((undefined1 *)0x00630b60 + iVar23 * 4);
          if (DAT_0047a470 != (ushort *)0x0) {
            ((undefined4 *)(uintptr_t)DAT_0047a470)[0x41] = 4;
          }
          puVar13 = extraout_ECX_34;
          puVar18 = (ushort *)(uintptr_t)iVar23;
        }
        uVar25 = CONCAT44(puVar18,_DAT_00ac4a54);
        local_2c = local_2c + 1;
        break;
      case 0x55:`
);
source = source.replace(
  "  \n  uVar3 = DAT_0047a470;\n  iVar1 = (short)in_EAX * 4;",
  "  int actor_id;\n  \n  if (E2R_actor_load_id_override != -1) {\n    in_EAX = (undefined4)E2R_actor_load_id_override;\n    E2R_actor_load_id_override = -1;\n  }\n  actor_id = (short)in_EAX;\n  uVar3 = DAT_0047a470;\n  iVar1 = actor_id * 4;"
);
source = source.replace(
  "    psVar2 = *(short **)((undefined1 *)0x00630b60 + (short)uVar4 * 4);\n    if (psVar2 == (short *)0x0) {\n      FUN_00441890(uVar4,uVar5);\n      FUN_0043cbb4(extraout_ECX_09);",
  "    psVar2 = *(short **)((undefined1 *)0x00630b60 + (short)uVar4 * 4);\n    if (psVar2 == (short *)0x0) {\n      if (DAT_0047ab10 != 0) {\n        DAT_0047a470 = uVar3;\n        return;\n      }\n      FUN_00441890(uVar4,uVar5);\n      FUN_0043cbb4(extraout_ECX_09);"
);
source = source.replace(
  "  psVar2 = *(short **)((undefined1 *)0x00630b60 + (short)in_EAX * 4);\n  if (psVar2 != (short *)0x0) {\n    if (*(int *)(*psVar2 * 2 + 0x671fbe) >> 0x10 != -2) {\n      psVar2[0x91] = *(short *)(*psVar2 * 2 + 0x671fc0);\n    }\n    FUN_00426c3c();\n    if ((((undefined1 *)0x0064a178)[extraout_CX * 2] & 2) == 0) {\n      ((undefined1 *)0x0064a178)[extraout_CX * 2] = ((undefined1 *)0x0064a178)[extraout_CX * 2] | 2;\n      extraout_EDX_01[0x77] = 100;\n      extraout_EDX_01[0x76] = extraout_EDX_01[0x77];\n      if ((-1 < (short)extraout_EDX_01[0x9d]) &&\n         (*(int *)((*(int *)(extraout_EDX_01 + 0x9c) >> 0x10) * 4 + 0x6297c0) != 0)) {\n        FUN_0044f508(extraout_EDX_01,extraout_EDX_01,(ushort *)0x0);\n      }\n    }\n  }",
  "  psVar2 = *(short **)((undefined1 *)0x00630b60 + actor_id * 4);\n  if (psVar2 != (short *)0x0) {\n    if (*(int *)(*psVar2 * 2 + 0x671fbe) >> 0x10 != -2) {\n      psVar2[0x91] = *(short *)(*psVar2 * 2 + 0x671fc0);\n    }\n    E2R_actor_calc_context = (int)(uintptr_t)psVar2;\n    FUN_00426c3c();\n    E2R_actor_calc_context = 0;\n    if ((((undefined1 *)0x0064a178)[*psVar2 * 2] & 2) == 0) {\n      ((undefined1 *)0x0064a178)[*psVar2 * 2] = ((undefined1 *)0x0064a178)[*psVar2 * 2] | 2;\n      psVar2[0x77] = 100;\n      psVar2[0x76] = psVar2[0x77];\n      if ((-1 < psVar2[0x9d]) &&\n         (*(int *)((*(int *)(psVar2 + 0x9c) >> 0x10) * 4 + 0x6297c0) != 0)) {\n        FUN_0044f508(psVar2,psVar2,(ushort *)0x0);\n      }\n    }\n  }"
);
source = source.replace(
  /  psVar2 = \*\(short \*\*\)\(\(undefined1 \*\)0x00630b60 \+ \(short\)in_EAX \* 4\);\r?\n  if \(psVar2 != \(short \*\)0x0\) \{[\s\S]*?  \}\r?\n  DAT_0047a470 = uVar3;/,
  "  psVar2 = *(short **)((undefined1 *)0x00630b60 + actor_id * 4);\n  if (psVar2 != (short *)0x0) {\n    if (*(int *)(*psVar2 * 2 + 0x671fbe) >> 0x10 != -2) {\n      psVar2[0x91] = *(short *)(*psVar2 * 2 + 0x671fc0);\n    }\n    E2R_actor_calc_context = (int)(uintptr_t)psVar2;\n    FUN_00426c3c();\n    E2R_actor_calc_context = 0;\n    if ((((undefined1 *)0x0064a178)[*psVar2 * 2] & 2) == 0) {\n      ((undefined1 *)0x0064a178)[*psVar2 * 2] = ((undefined1 *)0x0064a178)[*psVar2 * 2] | 2;\n      psVar2[0x77] = 100;\n      psVar2[0x76] = psVar2[0x77];\n      if ((-1 < psVar2[0x9d]) &&\n         (*(int *)((*(int *)(psVar2 + 0x9c) >> 0x10) * 4 + 0x6297c0) != 0)) {\n        FUN_0044f508(psVar2,psVar2,(ushort *)0x0);\n      }\n    }\n  }\n  DAT_0047a470 = uVar3;"
);
source = source.replace(
  "  undefined8 uVar6;\n  int actor_id;",
  "  undefined8 uVar6;\n  undefined4 parse_result;\n  int actor_id;"
);
source = source.replace(
  "  actor_id = (short)in_EAX;\n  uVar3 = DAT_0047a470;",
  "  actor_id = (short)in_EAX;\n  uVar3 = DAT_0047a470;\n  if ((actor_id < 0) || (5000 <= actor_id)) {\n    if (E2R_actor_load_diag_count < 48) {\n      E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;\n      fprintf(stderr,\n              \"actor load invalid id: id=%d DAT_0047ab10=%lu current=0x%lx \"\n              \"action_opcodes=%lu last_opcode=0x%lx\\n\",\n              actor_id,(unsigned long)DAT_0047ab10,(unsigned long)DAT_0047a470,\n              (unsigned long)E2R_action_opcode_count,\n              (unsigned long)E2R_action_last_opcode);\n    }\n    DAT_0047a470 = uVar3;\n    return;\n  }\n  parse_result = 0;\n  if (E2R_actor_load_diag_count < 48) {\n    E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;\n    fprintf(stderr,\n            \"actor load enter: id=%d table=0x%lx flags=0x%02x DAT_0047ab10=%lu \"\n            \"current=0x%lx action_opcodes=%lu last_opcode=0x%lx\\n\",\n            actor_id,\n            (unsigned long)*(int *)((undefined1 *)0x00630b60 + actor_id * 4),\n            (unsigned int)((undefined1 *)0x0064a178)[actor_id * 2],\n            (unsigned long)DAT_0047ab10,(unsigned long)DAT_0047a470,\n            (unsigned long)E2R_action_opcode_count,\n            (unsigned long)E2R_action_last_opcode);\n  }"
);
source = source.replace(
  "    psVar2 = *(short **)((undefined1 *)0x00630b60 + (short)uVar4 * 4);\n    if (psVar2 == (short *)0x0) {",
  "    psVar2 = *(short **)((undefined1 *)0x00630b60 + (short)uVar4 * 4);\n    if (E2R_actor_load_diag_count < 48) {\n      E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;\n      fprintf(stderr,\n              \"actor load after parse: id=%d parse=%u lookup_id=%d actor=0x%lx \"\n              \"head=0x%lx links=0x%lx flags=0x%02x records=%u\\n\",\n              actor_id,(unsigned int)parse_result,(int)(short)uVar4,\n              (unsigned long)psVar2,(unsigned long)_DAT_00637248,\n              (unsigned long)_DAT_00637270,\n              (unsigned int)((undefined1 *)0x0064a178)[actor_id * 2],\n              E2R_fan_parse_record_count);\n    }\n    if (psVar2 == (short *)0x0) {"
);
source = source.replace(
  "      if (DAT_0047ab10 != 0) {\n        DAT_0047a470 = uVar3;\n        return;",
  "      if (DAT_0047ab10 != 0) {\n        if (E2R_actor_load_diag_count < 48) {\n          E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;\n          fprintf(stderr,\"actor load return missing: id=%d DAT_0047a470=0x%lx\\n\",\n                  actor_id,(unsigned long)uVar3);\n        }\n        DAT_0047a470 = uVar3;\n        return;"
);
source = source.replace(
  "  psVar2 = *(short **)((undefined1 *)0x00630b60 + actor_id * 4);\n  if (psVar2 != (short *)0x0) {",
  "  psVar2 = *(short **)((undefined1 *)0x00630b60 + actor_id * 4);\n  if (E2R_actor_load_diag_count < 48) {\n    E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;\n    fprintf(stderr,\n            \"actor load post: id=%d actor=0x%lx flags=0x%02x mode=%d \"\n            \"script=0x%x action_table=0x%lx\\n\",\n            actor_id,(unsigned long)psVar2,\n            (unsigned int)((undefined1 *)0x0064a178)[actor_id * 2],\n            psVar2 != (short *)0x0 ? (int)psVar2[0x41] : -1,\n            psVar2 != (short *)0x0 ? *(uint *)(psVar2 + 0x9c) : 0,\n            psVar2 != (short *)0x0 ?\n              (unsigned long)*(int *)((*(int *)(psVar2 + 0x9c) >> 0x10) * 4 + 0x6297c0) : 0);\n  }\n  if (psVar2 != (short *)0x0) {"
);
source = source.replace(
  "  DAT_0047a470 = uVar3;\n  return;\n}\n\n\n\n/* 00452140 */",
  "  DAT_0047a470 = uVar3;\n  if (E2R_actor_load_diag_count < 48) {\n    E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;\n    fprintf(stderr,\n            \"actor load exit: id=%d restored_current=0x%lx flags=0x%02x \"\n            \"opcodes=%lu last_opcode=0x%lx hit75=%lu\\n\",\n            actor_id,(unsigned long)DAT_0047a470,\n            (unsigned int)((undefined1 *)0x0064a178)[actor_id * 2],\n            (unsigned long)E2R_action_opcode_count,\n            (unsigned long)E2R_action_last_opcode,\n            (unsigned long)E2R_action_hit_75_count);\n  }\n  return;\n}\n\n\n\n/* 00452140 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00448744\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004488a4 \*\//,
  "undefined8 __fastcall FUN_00448744(undefined4 param_1,ushort *param_2)\n\n{\n  int iVar1;\n  byte bVar2;\n  bool bVar3;\n  ushort *actor;\n  int iVar4;\n  uint uVar5;\n  int iVar6;\n  byte *pbVar7;\n  uint local_28;\n  uint local_20;\n  \n  local_20 = 0xffffffff;\n  local_28 = 0xffffffff;\n  actor = param_2;\n  if ((uintptr_t)actor < 0x10000u || IsBadReadPtr(actor,0x88)) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  uVar5 = (uint)*(ushort *)\n                 ((undefined1 *)0x00684d68 +\n                 (((int)(short)*actor >> 9) + 0x40) * 2 +\n                 ((*(int *)(actor + 1) >> 0x19) + 0x40) * 0x100);\n  iVar6 = (short)(*actor & 0x1ff) + -0x100;\n  iVar4 = (short)(actor[2] & 0x1ff) + -0x100;\n  if (uVar5 != 0xffff) {\n    pbVar7 = (undefined1 *)0x0068cd68 + uVar5 * 0xc;\n    do {\n      bVar3 = false;\n      switch((int)(uintptr_t)(pbVar7[1])) {\n      case 0:\n        break;\n      case 1:\nswitchD_004487ea_caseD_1:\n        bVar3 = true;\n        break;\n      case 2:\n        if (iVar4 <= iVar6) goto switchD_004487ea_caseD_1;\n        break;\n      case 3:\n        if (iVar6 <= -iVar4) goto switchD_004487ea_caseD_1;\n        break;\n      case 4:\n        if (-iVar4 < iVar6) goto switchD_004487ea_caseD_1;\n        break;\n      case 5:\n        if (iVar6 < iVar4) goto switchD_004487ea_caseD_1;\n        break;\n      default:\n        if (iVar6 < 1) {\n          if (iVar4 < 1) {\n            bVar2 = pbVar7[1] & 2;\n          }\n          else {\n            bVar2 = pbVar7[1] & 8;\n          }\n        }\n        else if (iVar4 < 1) {\n          bVar2 = pbVar7[1] & 1;\n        }\n        else {\n          bVar2 = pbVar7[1] & 4;\n        }\n        if (bVar2 != 0) goto switchD_004487ea_caseD_1;\n      }\n      if (((bVar3) &&\n          ((int)(uint)pbVar7[5] <= (-(*(int *)actor >> 0x10) >> (DAT_0047a738 & 0x1f)) + 0x84)) &&\n         ((int)local_28 < (int)(uint)*pbVar7)) {\n        local_28 = (uint)*pbVar7;\n        local_20 = uVar5;\n      }\n      iVar1 = *(int *)pbVar7;\n      pbVar7 = pbVar7 + 0xc;\n      uVar5 = uVar5 + 1;\n    } while ((iVar1 >> 0x10 & 0x8000U) == 0);\n  }\n  return CONCAT44(param_2,local_20);\n}\n\n\n\n/* 004488a4 */"
);
source = source.replace(
  "      iVar2 = FUN_004453a4(extraout_ECX_03,1);",
  "      iVar2 = E2R_ParseArchiveFanResource();"
);
source = source.replace(
  /undefined8 __fastcall FUN_004413fc\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00441444 \*\//,
  "undefined8 __fastcall FUN_004413fc(undefined4 param_1,undefined4 param_2)\n\n{\n  undefined2 *puVar1;\n  undefined8 uVar2;\n  \n  puVar1 = (undefined2 *)(uintptr_t)FUN_0045326c(param_1,param_2);\n  if (puVar1 == (undefined2 *)0x0) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[1] = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  *puVar1 = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[2] = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[3] = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[4] = (short)uVar2;\n  E2R_fan_parse_record = (short *)puVar1;\n  E2R_fan_parse_record_count = E2R_fan_parse_record_count + 1;\n  if (E2R_fan_phase_diag_count < 64 && E2R_fan_parse_record_count <= 64) {\n    fprintf(stderr,\"FAN record: ordinal=%u caller=%p offset=%u fields=%04x,%04x,%04x,%04x,%04x\\n\",\n            E2R_fan_parse_record_count,__builtin_return_address(0),\n            (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                   (byte *)(uintptr_t)E2R_fan_parse_stream[5]),\n            (ushort)puVar1[0],(ushort)puVar1[1],(ushort)puVar1[2],\n            (ushort)puVar1[3],(ushort)puVar1[4]);\n  }\n  return CONCAT44(param_2,(undefined4)(uintptr_t)puVar1);\n}\n\n\n\n/* 00441444 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00441444\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0044146c \*\//,
  "undefined8 __fastcall FUN_00441444(undefined4 param_1,undefined4 param_2)\n\n{\n  int *stream;\n  int b0;\n  int b1;\n  int b2;\n  int b3;\n  uint value;\n  \n  stream = (int *)(uintptr_t)param_1;\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      (uint)stream[6] != E2R_STREAM_MAGIC) {\n    stream = (int *)(uintptr_t)DAT_0047a724;\n  }\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      (uint)stream[6] != E2R_STREAM_MAGIC) {\n    if (E2R_archive_read_diag_count < 8) {\n      E2R_archive_read_diag_count = E2R_archive_read_diag_count + 1;\n      fprintf(stderr,\"archive dword read failed: stream=%p fallback=%p offset=%u\\n\",\n              (void *)(uintptr_t)param_1,(void *)(uintptr_t)DAT_0047a724,\n              (uint)(uintptr_t)param_2);\n    }\n    return (ulonglong)(uint)(uintptr_t)param_2 << 0x20;\n  }\n  b0 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  b1 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  b2 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  b3 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  if ((b0 | b1 | b2 | b3) < 0) {\n    if (E2R_archive_read_diag_count < 8) {\n      E2R_archive_read_diag_count = E2R_archive_read_diag_count + 1;\n      fprintf(stderr,\"archive dword eof: stream=%p offset=%u remaining=%d\\n\",\n              (void *)stream,(uint)(uintptr_t)param_2,stream[1]);\n    }\n    return (ulonglong)(uint)(uintptr_t)param_2 << 0x20;\n  }\n  value = ((uint)b0 << 0x18) | (((uint)b1 & 0xff) << 0x10) |\n          (((uint)b2 & 0xff) << 8) | ((uint)b3 & 0xff);\n  return CONCAT44(param_2,value);\n}\n\n\n\n/* 0044146c */"
);
source = source.replace(
  /(void FUN_00447090\(void\)[\s\S]*?\r?\n  undefined1 local_48 \[52\];\r?\n\s*)switch/,
  "$1in_EAX = E2R_fan_parse_record;\n  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,10)) {\n    return;\n  }\n  \n  switch"
);
source = source.replace(
  /(short \* __fastcall FUN_0042b880\(int param_1,short \*param_2\)[\s\S]*?\r?\n  short \*local_14;\r?\n\s*)if/,
  "$1in_EAX = E2R_fan_parse_record;\n  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,10)) {\n    return (short *)0x0;\n  }\n  unaff_ESI = param_2;\n  local_14 = param_2;\n  local_18 = param_2;\n  \n  if"
);
source = source.replace(
  "    if ((DAT_0047a714 != 0) &&\n       (((sVar9 == 8 || (sVar9 == 10)) || ((sVar9 == 7 || ((sVar9 == 0x29 || (sVar9 == 0x2b))))))))\n    {\n      FUN_00442ca4();\n      iVar5 = extraout_EDX_02;\n    }\nLAB_00444418:",
  "    if ((DAT_0047a714 != 0) &&\n       (((sVar9 == 8 || (sVar9 == 10)) || ((sVar9 == 7 || ((sVar9 == 0x29 || (sVar9 == 0x2b))))))))\n    {\n      FUN_00442ca4();\n      iVar5 = extraout_EDX_02;\n    }\n    if (sVar9 == 0) {\n      FUN_00453264();\n      if ((DAT_0047a34a != 0) && (DAT_0047a470 == (short *)0x0)) {\n        DAT_0047a470 = psVar1;\n      }\n      return;\n    }\nLAB_00444418:"
);
source = source.replace(
  "    FUN_00447090();\n    sVar9 = *(short *)(iVar4 + 2);\n    iVar5 = extraout_EDX;",
  "    FUN_00447090();\n    sVar9 = *(short *)(iVar4 + 2);\n    if (E2R_fan_actor_diag_count < 8) {\n      E2R_fan_actor_diag_count = E2R_fan_actor_diag_count + 1;\n      fprintf(stderr,\"FAN 44330: ordinal=%u local_type=%04x version=%d offset=%u\\n\",\n              E2R_fan_parse_record_count,(ushort)sVar9,(int)_DAT_0067bc92,\n              (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                     (byte *)(uintptr_t)E2R_fan_parse_stream[5]));\n    }\n    iVar5 = extraout_EDX;"
);
source = source.replace(
  "    FUN_0045f0a1((int)local_48,(byte *)s_unknown_type____d_004747d4);\n    FUN_0043cac0(extraout_ECX,extraout_EDX);\n    FUN_00414e68();",
  "    fprintf(stderr,\n            \"FAN unknown record: ordinal=%u offset=%u remaining=%d fields=%04x,%04x,%04x,%04x,%04x\\n\",\n            E2R_fan_parse_record_count,\n            (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                   (byte *)(uintptr_t)E2R_fan_parse_stream[5]),\n            E2R_fan_parse_stream[1],(ushort)in_EAX[0],(ushort)in_EAX[1],\n            (ushort)in_EAX[2],(ushort)in_EAX[3],(ushort)in_EAX[4]);"
);
source = source.replace(
  "    if ((short)uVar10 == 0) {\n      if (5 < _DAT_0067bc92) {",
  "    if (sVar9 == 0) {\n      if (5 < _DAT_0067bc92) {"
);
source = source.replace(
  "    if ((short)uVar2 == 0) {\n      if ((DAT_0047a34a != 0) && (local_14 != (short *)0x0)) {",
  "    if (sVar1 == 0) {\n      if ((DAT_0047a34a != 0) && (local_14 != (short *)0x0)) {"
);
source = source.replace(
  "        uVar10 = FUN_004413fc(extraout_ECX_05,extraout_EDX_04);\n        iVar4 = (int)uVar10;\n        FUN_00447090();\n        sVar9 = *(short *)(extraout_EDX_05 + 2);",
  "        uVar10 = FUN_004413fc(extraout_ECX_05,extraout_EDX_04);\n        iVar4 = (int)uVar10;\n        FUN_00447090();\n        sVar9 = *(short *)(iVar4 + 2);"
);
source = source.replace(
  "        uVar5 = FUN_004413fc(extraout_ECX_03,extraout_EDX_03);\n        psVar3 = (short *)uVar5;\n        FUN_00447090();\n        sVar1 = *(short *)(extraout_EDX_04 + 2);\n        uVar2 = CONCAT22(extraout_var_00,sVar1);",
  "        uVar5 = FUN_004413fc(extraout_ECX_03,extraout_EDX_03);\n        psVar3 = (short *)uVar5;\n        FUN_00447090();\n        sVar1 = psVar3[1];\n        uVar2 = (undefined4)(uint)(ushort)sVar1;"
);
source = source.replace(
  "        uVar15 = FUN_004413fc(extraout_ECX_69,extraout_EDX_28);\n        psVar8 = (short *)uVar15;\n        FUN_00447090();\n        sVar9 = *(short *)(extraout_EDX_29 + 2);\n        uVar10 = CONCAT22(extraout_var_00,sVar9);",
  "        uVar15 = FUN_004413fc(extraout_ECX_69,extraout_EDX_28);\n        psVar8 = (short *)uVar15;\n        FUN_00447090();\n        sVar9 = psVar8[1];\n        uVar10 = (undefined4)(uint)(ushort)sVar9;"
);
source = source.replace(
  "  psVar1 = DAT_0047a470;\n  uVar7 = 0;\n  DAT_0047a470 = (short *)0x0;\n  do {",
  "  psVar1 = DAT_0047a470;\n  uVar7 = 0;\n  DAT_0047a470 = (short *)0x0;\n  if (E2R_fan_phase_diag_count < 16) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 44330 enter: offset=%u record=%u\\n\",\n            E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n  }\n  do {"
);
source = source.replace(
  "      if ((DAT_0047a34a != 0) && (DAT_0047a470 == (short *)0x0)) {\n        DAT_0047a470 = psVar1;\n      }\n      return;\n    }\nLAB_00444418:",
  "      if ((DAT_0047a34a != 0) && (DAT_0047a470 == (short *)0x0)) {\n        DAT_0047a470 = psVar1;\n      }\n      if (E2R_fan_phase_diag_count < 16) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 44330 terminator: offset=%u record=%u\\n\",\n                E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n      }\n      return;\n    }\nLAB_00444418:"
);
source = source.replace(
  "      if ((DAT_0047a34a != 0) && (DAT_0047a470 == (short *)0x0)) {\n        DAT_0047a470 = psVar1;\n      }\n      return;\n    }\n  } while( true );\n}",
  "      if ((DAT_0047a34a != 0) && (DAT_0047a470 == (short *)0x0)) {\n        DAT_0047a470 = psVar1;\n      }\n      if (E2R_fan_phase_diag_count < 16) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 44330 post-terminator: offset=%u record=%u\\n\",\n                E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n      }\n      return;\n    }\n  } while( true );\n}"
);
source = source.replace(
  "  uVar2 = extraout_ECX;\n  local_14 = psVar3;\n  do {",
  "  uVar2 = extraout_ECX;\n  local_14 = psVar3;\n  if (E2R_fan_phase_diag_count < 16) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 44668 enter: offset=%u record=%u\\n\",\n            E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n  }\n  do {"
);
source = source.replace(
  "      if ((DAT_0047a34a != 0) && (local_14 != (short *)0x0)) {\n        _DAT_0047a478 = local_14;\n      }\n      return;\n    }\n  } while( true );\n}",
  "      if ((DAT_0047a34a != 0) && (local_14 != (short *)0x0)) {\n        _DAT_0047a478 = local_14;\n      }\n      if (E2R_fan_phase_diag_count < 16) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 44668 terminator: offset=%u record=%u\\n\",\n                E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n      }\n      return;\n    }\n  } while( true );\n}"
);
source = source.replace(
  "    FUN_00444330(iVar12);\n    FUN_00444668(extraout_ECX_63,local_18);",
  "    FUN_00444330(iVar12);\n    if (E2R_fan_phase_diag_count < 16) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN phase after 44330: offset=%u record=%u\\n\",\n              E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n    }\n    FUN_00444668(extraout_ECX_63,local_18);\n    if (E2R_fan_phase_diag_count < 16) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN phase after 44668: offset=%u record=%u\\n\",\n              E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n    }"
);
source = source.replace(
  "    FUN_00444668(iVar12,local_18);\n    FUN_00444330(extraout_ECX_61);",
  "    FUN_00444668(iVar12,local_18);\n    if (E2R_fan_phase_diag_count < 16) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN phase after 44668: offset=%u record=%u\\n\",\n              E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n    }\n    FUN_00444330(extraout_ECX_61);\n    if (E2R_fan_phase_diag_count < 16) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN phase after 44330: offset=%u record=%u\\n\",\n              E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n    }"
);
source = source.replace(
  "    psVar8 = (short *)uVar15;\n    FUN_00447090();\n    uVar10 = CONCAT22(extraout_var,psVar8[1]);\n    iVar7 = extraout_EDX_24;",
  "    psVar8 = (short *)uVar15;\n    if (E2R_fan_phase_diag_count < 16) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN dispatch record-read: ordinal=%u type=%04x offset=%u\\n\",\n              E2R_fan_parse_record_count,(ushort)psVar8[1],E2R_FanStreamOffset());\n    }\n    if (E2R_fan_dispatch_diag_count < 8) {\n      E2R_fan_dispatch_diag_count = E2R_fan_dispatch_diag_count + 1;\n      fprintf(stderr,\"FAN dispatch pre: ordinal=%u type=%04x version=%d offset=%u\\n\",\n              E2R_fan_parse_record_count,(ushort)psVar8[1],(int)_DAT_0067bc92,\n              (uint)((byte *)(uintptr_t)in_EAX[0] - (byte *)(uintptr_t)in_EAX[5]));\n    }\n    FUN_00447090();\n    uVar10 = (undefined4)(uint)(ushort)psVar8[1];\n    if (E2R_fan_phase_diag_count < 16) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN dispatch normalized: ordinal=%u type=%04x offset=%u\\n\",\n              E2R_fan_parse_record_count,(ushort)psVar8[1],E2R_FanStreamOffset());\n    }\n    if (E2R_fan_dispatch_diag_count < 8) {\n      E2R_fan_dispatch_diag_count = E2R_fan_dispatch_diag_count + 1;\n      fprintf(stderr,\"FAN dispatch: ordinal=%u type=%04x version=%d offset=%u\\n\",\n              E2R_fan_parse_record_count,(ushort)psVar8[1],(int)_DAT_0067bc92,\n              (uint)((byte *)(uintptr_t)in_EAX[0] - (byte *)(uintptr_t)in_EAX[5]));\n    }\n    iVar7 = extraout_EDX_24;"
);
source = source.replace(
  "        FUN_00444c10(uVar10,local_18);\n        uVar10 = extraout_ECX_82;",
  "        FUN_00444c10(uVar10,local_18);\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail after 44c10: offset=%u record=%u\\n\",\n                  E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n        }\n        uVar10 = extraout_ECX_82;"
);
source = source.replace(
  "        FUN_004448e4(local_4c,local_18);\n        uVar10 = extraout_ECX_83;",
  "        FUN_004448e4(local_4c,local_18);\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail after 448e4: offset=%u record=%u\\n\",\n                  E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n        }\n        uVar10 = extraout_ECX_83;"
);
source = source.replace(
  "        FUN_00445000(local_4c,local_18);\n        uVar10 = extraout_ECX_84;",
  "        FUN_00445000(local_4c,local_18);\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail after 45000: offset=%u record=%u\\n\",\n                  E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n        }\n        uVar10 = extraout_ECX_84;"
);
source = source.replace(
  "        FUN_004451a8(uVar10,local_18);\n        uVar10 = extraout_ECX_85;",
  "        FUN_004451a8(uVar10,local_18);\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail after 451a8: offset=%u record=%u\\n\",\n                  E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n        }\n        uVar10 = extraout_ECX_85;"
);
source = source.replace(
  "          FUN_00447638((undefined4)(uintptr_t)E2R_fan_parse_stream);\n          uVar10 = extraout_ECX_87;",
  "          FUN_00447638((undefined4)(uintptr_t)E2R_fan_parse_stream);\n          if (E2R_fan_phase_diag_count < 32) {\n            E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n            fprintf(stderr,\"FAN tail after 47638: offset=%u record=%u\\n\",\n                    E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n          }\n          uVar10 = extraout_ECX_87;"
);
source = source.replace(
  "      if (8 < _DAT_0067bc92) {\n        uVar15 = FUN_004171b8(uVar10,uVar13);",
  "      if (8 < _DAT_0067bc92) {\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail before marker: offset=%u record=%u ecx=%08x edx=%08x\\n\",\n                  E2R_FanStreamOffset(),E2R_fan_parse_record_count,(uint)uVar10,(uint)uVar13);\n        }\n        uVar15 = FUN_004171b8(uVar10,uVar13);"
);
source = source.replace(
  "        uVar13 = (undefined4)((ulonglong)uVar15 >> 0x20);\n        uVar10 = extraout_ECX_86;\n        if ((short)uVar15 != 0) {",
  "        uVar13 = (undefined4)((ulonglong)uVar15 >> 0x20);\n        uVar10 = extraout_ECX_86;\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail marker: value=%04x offset=%u record=%u\\n\",\n                  (ushort)uVar15,E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n        }\n        if ((short)uVar15 != 0) {"
);
source = source.replace(
  "      if (DAT_0047a714 != 0) {\n        FUN_0045ec6c(uVar10,uVar13);\n      }\n      iVar12 = _DAT_00637270;",
  "      if (DAT_0047a714 != 0) {\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail before DAT_0047a714 cleanup: offset=%u record=%u\\n\",\n                  E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n        }\n        FUN_0045ec6c(uVar10,uVar13);\n      }\n      iVar12 = _DAT_00637270;"
);
source = source.replace(
  "      if (local_2c == 0) {\n        local_2c = 0;",
  "      if (local_2c == 0) {\n        if (_DAT_00637248 != 0 &&\n           ((uint)_DAT_00637248 < 0x10000u || 0x70000000u <= (uint)_DAT_00637248 ||\n            IsBadReadPtr((void *)(uintptr_t)_DAT_00637248,0x54))) {\n          if (E2R_fan_phase_diag_count < 64) {\n            E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n            fprintf(stderr,\"FAN tail dropping invalid actor head: actors=%p links=%p\\n\",\n                    (void *)(uintptr_t)_DAT_00637248,(void *)(uintptr_t)_DAT_00637270);\n          }\n          _DAT_00637248 = 0;\n        }\n        if (E2R_fan_phase_diag_count < 32) {\n          E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n          fprintf(stderr,\"FAN tail before object cleanup: offset=%u record=%u actors=%p links=%p\\n\",\n                  E2R_FanStreamOffset(),E2R_fan_parse_record_count,\n                  (void *)(uintptr_t)_DAT_00637248,(void *)(uintptr_t)_DAT_00637270);\n        }\n        local_2c = 0;"
);
source = source.replace(
  "      for (; iVar12 != 0; iVar12 = *(int *)(iVar12 + 8)) {\n        *(byte *)(iVar12 + 0xd) = *(byte *)(iVar12 + 0xd) & 0xfd;\n      }\n      return 1;",
  "      for (; iVar12 != 0; iVar12 = *(int *)(iVar12 + 8)) {\n        *(byte *)(iVar12 + 0xd) = *(byte *)(iVar12 + 0xd) & 0xfd;\n      }\n      if (E2R_fan_phase_diag_count < 32) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN parse complete: offset=%u record=%u actors=%p links=%p\\n\",\n                E2R_FanStreamOffset(),E2R_fan_parse_record_count,\n                (void *)(uintptr_t)_DAT_00637248,(void *)(uintptr_t)_DAT_00637270);\n      }\n      return 1;"
);
source = source.replace(
  /(void __fastcall FUN_00444c10\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined2 uStack_16;\r?\n\s*)uVar17 =/,
  "$1in_EAX = E2R_fan_parse_stream;\n  if (in_EAX == (int *)0x0 || IsBadReadPtr(in_EAX,0x1c)) {\n    return;\n  }\n  \n  uVar17 ="
);
source = source.replace(
  "            uVar19 = FUN_004268e4(iVar4,local_2c);",
  "            uVar19 = FUN_004268e4((undefined4)(uintptr_t)psVar5,local_2c);"
);
source = source.replace(
  "            uVar19 = FUN_0042692c(iVar4,local_2c);",
  "            uVar19 = FUN_0042692c(uVar9,local_2c);"
);
source = source.replace(
  "      uVar10 = CONCAT22(extraout_var,*(undefined2 *)(&DAT_006769f8 + (short)uVar18 * 2));",
  "      uVar10 = CONCAT22(extraout_var,*(undefined2 *)((undefined1 *)0x006769f8 + (short)uVar18 * 2));"
);
source = source.replace(
  "        *psVar5 = (short)extraout_ECX_09;\n        uVar10 = extraout_ECX_09;\n        if (*(int *)((short)extraout_ECX_09 * 4 + 0x6297c0) != 0) {\n          FUN_004526e4();\n          uVar10 = extraout_ECX_10;\n          uVar14 = extraout_var_00;\n        }",
  "        *psVar5 = (short)uVar10;\n        iVar4 = *(int *)((short)uVar10 * 4 + 0x6297c0);\n        if (iVar4 != 0) {\n          FUN_004526e4((short *)(uintptr_t)iVar4);\n        }"
);
source = source.replace(
  "              uVar20 = FUN_004435e8(psVar5,iVar12);",
  "              uVar20 = FUN_004435e8((undefined4)(uint)(ushort)iVar12,iVar12);"
);
source = source.replace(
  /void __fastcall FUN_00444c10\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00445000 \*\//,
  `void __fastcall FUN_00444c10(undefined4 param_1,undefined4 param_2)

{
  int *stream;
  short outer_count;
  short outer_index;
  short raw_index;
  short action_index;
  short token;
  short child_count;
  short child_index;
  short *action;
  short *existing;
  char *child;
  char *previous_child;
  short *pool;
  int repeat_count;
  int repeat_index;

  (void)param_1;
  stream = E2R_fan_parse_stream;
  if (stream == (int *)0x0 || IsBadReadPtr(stream,0x1c)) {
    return;
  }
  FUN_0041ba7c((undefined4)(uintptr_t)stream,param_2);
  outer_count = (short)FUN_004171b8((undefined4)(uintptr_t)stream,param_2);
  if (E2R_fan_action_read_diag_count < 8) {
    E2R_fan_action_read_diag_count = E2R_fan_action_read_diag_count + 1;
    fprintf(stderr,"FAN 44c10: offset=%u count=%d version=%d remaining=%d\\n",
            (uint)((byte *)(uintptr_t)stream[0] - (byte *)(uintptr_t)stream[5]),
            (int)outer_count,(int)_DAT_0067bc92,stream[1]);
  }
  if (outer_count <= 0) {
    return;
  }
  pool = (short *)(uintptr_t)_DAT_006366a0;
  for (outer_index = 0; outer_index < outer_count; outer_index = outer_index + 1) {
    raw_index = (short)FUN_004171b8((undefined4)(uintptr_t)stream,0);
    action_index = *(short *)((undefined1 *)0x006769f8 + raw_index * 2);
    if (!E2R_FanActionPassesFilter(action_index)) {
      token = (short)FUN_004171b8((undefined4)(uintptr_t)stream,0);
      while (token != 0) {
        if (((ushort)token & 0xf000) == 0xe000) {
          repeat_count = ((((int)(short)((ushort)token & 0x0fff)) + 1) / 2);
          for (repeat_index = 0; repeat_index < repeat_count; repeat_index = repeat_index + 1) {
            FUN_004171b8((undefined4)(uintptr_t)stream,0);
          }
        }
        token = (short)FUN_004171b8((undefined4)(uintptr_t)stream,0);
      }
      child_count = (short)FUN_004171b8((undefined4)(uintptr_t)stream,0);
      for (child_index = 0; child_index < child_count; child_index = child_index + 1) {
        E2R_SkipFanTextString(stream);
      }
      continue;
    }
    action = (short *)(uintptr_t)(uint)FUN_004268a4(0,0);
    if (action == (short *)0x0 || E2R_IsBadWritePtr(action,0xe)) {
      return;
    }
    action[0] = action_index;
    existing = (short *)0x0;
    if (-1 < action_index) {
      existing = ((short **)0x006297c0)[action_index];
    }
    if (existing != (short *)0x0) {
      FUN_004526e4(existing);
    }
    if (-1 < action[0]) {
      ((short **)0x006297c0)[action[0]] = action;
    }
    token = (short)FUN_004171b8((undefined4)(uintptr_t)stream,(undefined4)(uintptr_t)action);
    if (token != 0) {
      *(int *)(action + 3) = DAT_00479d94;
      while (token != 0) {
        if ((int)DAT_00479d94 < 19999 && pool != (short *)0x0) {
          pool[DAT_00479d94] =
              (short)FUN_004435e8((undefined4)(uint)(ushort)token,(undefined4)(uint)(ushort)token);
          DAT_00479d94 = DAT_00479d94 + 1;
        }
        else {
          FUN_00414e68();
        }
        if (((ushort)token & 0xf000) == 0xe000) {
          repeat_count = ((((int)(short)((ushort)token & 0x0fff)) + 1) / 2);
          if ((int)DAT_00479d94 + repeat_count < 19999 && pool != (short *)0x0) {
            for (repeat_index = 0; repeat_index < repeat_count; repeat_index = repeat_index + 1) {
              pool[DAT_00479d94] =
                  (short)FUN_004171b8((undefined4)(uintptr_t)stream,0);
              DAT_00479d94 = DAT_00479d94 + 1;
            }
          }
          else {
            FUN_00414e68();
          }
        }
        token = (short)FUN_004171b8((undefined4)(uintptr_t)stream,0);
      }
      if ((int)DAT_00479d94 < 19999 && pool != (short *)0x0) {
        pool[DAT_00479d94] = 0;
        DAT_00479d94 = DAT_00479d94 + 1;
      }
    }
    child_count = (short)FUN_004171b8((undefined4)(uintptr_t)stream,0);
    previous_child = (char *)0x0;
    for (child_index = 0; child_index < child_count; child_index = child_index + 1) {
      if (child_index == 0) {
        child = (char *)(uintptr_t)(uint)FUN_004268e4((undefined4)(uintptr_t)action,0);
      }
      else {
        child = (char *)(uintptr_t)(uint)FUN_0042692c((undefined4)(uintptr_t)previous_child,0);
      }
      if (child == (char *)0x0 || E2R_IsBadWritePtr(child,0x39)) {
        return;
      }
      E2R_ReadFanChildName(stream,child,0x35);
      E2R_NormalizeFanChildName(child,0x35);
      previous_child = child;
    }
  }
  if (E2R_fan_action_summary_diag_count < 8) {
    E2R_fan_action_summary_diag_count = E2R_fan_action_summary_diag_count + 1;
    fprintf(stderr,"FAN 44c10 summary: list=%u table=%u pool=%d head=0x%x\\n",
            E2R_CountActionList(_DAT_00637250),E2R_CountActionTable(),DAT_00479d94,
            (uint)(uintptr_t)_DAT_00637250);
  }
  return;
}



/* 00445000 */`
);
source = source.replace(
  "    uVar7 = FUN_004413fc(uVar4,uVar5);\n    psVar1 = (short *)uVar7;\n    FUN_00447090();\n    uVar4 = CONCAT22(extraout_var,psVar1[1]);",
  "    uVar7 = FUN_004413fc((undefined4)(uintptr_t)E2R_fan_parse_stream,uVar5);\n    psVar1 = (short *)uVar7;\n    if (psVar1[1] == 0) {\n      FUN_00453264();\n      if (E2R_fan_phase_diag_count < 16) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 448e4 terminator: offset=%u record=%u\\n\",\n                E2R_FanStreamOffset(),E2R_fan_parse_record_count);\n      }\n      return;\n    }\n    FUN_00447090();\n    uVar4 = (undefined4)(uint)(ushort)psVar1[1];"
);
source = source.replace(
  "          uVar7 = FUN_004413fc(extraout_ECX_05,extraout_EDX_04);\n          psVar1 = (short *)uVar7;\n          FUN_00447090();\n          sVar3 = *(short *)(extraout_ECX_06 + 2);\n          uVar4 = CONCAT22((short)((uint)extraout_ECX_06 >> 0x10),sVar3);",
  "          uVar7 = FUN_004413fc((undefined4)(uintptr_t)E2R_fan_parse_stream,extraout_EDX_04);\n          psVar1 = (short *)uVar7;\n          if (psVar1[1] == 0) {\n            sVar3 = 0;\n            break;\n          }\n          FUN_00447090();\n          sVar3 = psVar1[1];\n          uVar4 = (undefined4)(uint)(ushort)sVar3;"
);
source = source.replace(
  "          uVar7 = FUN_004413fc(extraout_ECX_01,extraout_EDX_00);\n          psVar1 = (short *)uVar7;\n          FUN_00447090();\n          sVar3 = *(short *)(extraout_ECX_02 + 2);\n          uVar4 = CONCAT22((short)((uint)extraout_ECX_02 >> 0x10),sVar3);",
  "          uVar7 = FUN_004413fc((undefined4)(uintptr_t)E2R_fan_parse_stream,extraout_EDX_00);\n          psVar1 = (short *)uVar7;\n          if (psVar1[1] == 0) {\n            sVar3 = 0;\n            break;\n          }\n          FUN_00447090();\n          sVar3 = psVar1[1];\n          uVar4 = (undefined4)(uint)(ushort)sVar3;"
);
source = source.replace(
  "      FUN_00453264();\n      uVar4 = extraout_ECX_07;\n      uVar5 = extraout_EDX_06;",
  "      FUN_00453264();\n      goto LAB_004448f9;"
);
source = source.replace(
  "        FUN_00453264();\n        uVar4 = extraout_ECX_08;\n        uVar5 = extraout_EDX_07;\n        if ((short)extraout_ECX_08 == 0) {\n          return;\n        }\n        goto LAB_004448f9;",
  "        FUN_00453264();\n        goto LAB_004448f9;"
);
source = source.replace(
  "        FUN_00453264();\n        uVar4 = extraout_ECX_09;\n        uVar5 = extraout_EDX_08;\n        if ((short)extraout_ECX_09 == 0) {\n          return;\n        }\n        goto LAB_004448f9;",
  "        FUN_00453264();\n        return;"
);
source = source.replace(
  "          FUN_00447638(extraout_ECX_86);",
  "          FUN_00447638((undefined4)(uintptr_t)E2R_fan_parse_stream);"
);
source = source.replace(
  "  int iVar15;\n  undefined8 uVar16;\n  undefined8 uVar17;\n  \n  uVar16 = FUN_004418fc(param_1,in_EAX);",
  "  int iVar15;\n  uint e2r_entry_start;\n  uint e2r_expected_offset;\n  byte *e2r_base;\n  byte *e2r_end;\n  undefined8 uVar16;\n  undefined8 uVar17;\n  \n  uVar16 = FUN_004418fc(param_1,in_EAX);"
);
source = source.replace(
  "  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x1c)) {\n    return;\n  }\n  uVar16 = FUN_004418fc((undefined4)(uintptr_t)\"sondoor1\",in_EAX);",
  "  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x1c)) {\n    return;\n  }\n  if (E2R_fan_phase_diag_count < 32) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 47638 enter: offset=%u remaining=%d\\n\",\n            E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n  }\n  uVar16 = FUN_004418fc((undefined4)(uintptr_t)\"sondoor1\",in_EAX);"
);
source = source.replace(
  "  DAT_0047a77c = CONCAT22((short)uVar16,(short)uVar17);\n  iVar8 = extraout_ECX_04;",
  "  DAT_0047a77c = CONCAT22((short)uVar16,(short)uVar17);\n  piVar11 = E2R_fan_parse_stream;\n  iVar8 = extraout_ECX_04;\n  if (E2R_fan_phase_diag_count < 32) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 47638 count: entries=%d offset=%u remaining=%d\\n\",\n            DAT_0047a77c,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n  }"
);
source = source.replace(
  "  if (0 < DAT_0047a77c) {\n    puVar7 = (undefined1 *)0x0068cd68;\n    do {\n      if ((piVar11[1] < 1) || ((*(byte *)(piVar11 + 3) & 4) != 0)) {",
  "  e2r_entry_start = E2R_FanStreamOffset();\n  if (0 < DAT_0047a77c) {\n    puVar7 = (undefined1 *)0x0068cd68;\n    do {\n      if ((E2R_fan_phase_diag_count < 32) &&\n         ((iVar14 < 4 || ((iVar14 & 0x1fffU) == 0)))) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 47638 entry: index=%d/%d offset=%u remaining=%d\\n\",\n                iVar14,DAT_0047a77c,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n      }\n      if ((piVar11[1] < 1) || ((*(byte *)(piVar11 + 3) & 4) != 0)) {"
);
source = source.replace(
  "          uVar5 = extraout_ECX_18 + 1;",
  "          uVar5 = uVar5 + 1;"
);
source = source.replace(
  "      uVar16 = FUN_00426a30(iVar8,(int)((ulonglong)uVar16 >> 0x20));\n      uVar16 = FUN_004173c8((int)uVar16,(int)((ulonglong)uVar16 >> 0x20));",
  "      uVar16 = FUN_00426a30(1,(int)((ulonglong)uVar16 >> 0x20));\n      extraout_ECX_36 = (short *)(uintptr_t)(uint)uVar16;\n      uVar16 = FUN_004173c8((int)uVar16,(int)((ulonglong)uVar16 >> 0x20));"
);
source = source.replace(
  "            *(short *)(extraout_ECX_38 + 2) = (short)uVar17;",
  "            extraout_ECX_36[iVar14 + 1] = (short)uVar17;"
);
source = source.replace(
  "          iVar8 = extraout_ECX_38 + 2;",
  "          iVar8 = (int)(uintptr_t)piVar11;"
);
source = source.replace(
  "  uVar16 = FUN_004173c8(iVar8,piVar11);\n  piVar11 = (int *)((ulonglong)uVar16 >> 0x20);",
  "  if (E2R_fan_parse_stream != (int *)0x0 &&\n      (uint)E2R_fan_parse_stream[6] == E2R_STREAM_MAGIC &&\n      0x33 <= _DAT_0067bc92 && 0 < DAT_0047a77c) {\n    e2r_base = (byte *)(uintptr_t)E2R_fan_parse_stream[5];\n    e2r_end = (byte *)(uintptr_t)E2R_fan_parse_stream[2];\n    e2r_expected_offset = e2r_entry_start + (uint)DAT_0047a77c * 36u;\n    if (e2r_base <= e2r_end && e2r_expected_offset <= (uint)(e2r_end - e2r_base)) {\n      if (E2R_fan_phase_diag_count < 32 && E2R_FanStreamOffset() != e2r_expected_offset) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 47638 entry align: current=%u expected=%u\\n\",\n                E2R_FanStreamOffset(),e2r_expected_offset);\n      }\n      E2R_fan_parse_stream[0] = (int)(uintptr_t)(e2r_base + e2r_expected_offset);\n      E2R_fan_parse_stream[1] = (int)(uint)(e2r_end - (e2r_base + e2r_expected_offset));\n      piVar11 = E2R_fan_parse_stream;\n    }\n  }\n  if (E2R_fan_phase_diag_count < 32) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 47638 entries done: count=%d offset=%u remaining=%d\\n\",\n            DAT_0047a77c,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n  }\n  uVar16 = FUN_004173c8(iVar8,piVar11);\n  piVar11 = (int *)((ulonglong)uVar16 >> 0x20);"
);
source = source.replace(
  "  iVar8 = extraout_ECX_19;\n  for (iVar15 = 0; iVar15 < _DAT_0073ccb6 >> 0x10; iVar15 = iVar15 + 1) {",
  "  iVar8 = extraout_ECX_19;\n  if (E2R_fan_phase_diag_count < 32) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 47638 segment count: count=%d offset=%u remaining=%d\\n\",\n            _DAT_0073ccb6 >> 0x10,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n  }\n  for (iVar15 = 0; iVar15 < _DAT_0073ccb6 >> 0x10; iVar15 = iVar15 + 1) {"
);
source = source.replace(
  "    iVar14 = iVar14 + 0x1c;\n  }\n  if (0x13 < _DAT_0067bc92) {",
  "    iVar14 = iVar14 + 0x1c;\n  }\n  if (E2R_fan_phase_diag_count < 32) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 47638 segments done: offset=%u remaining=%d\\n\",\n            E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n  }\n  if (0x13 < _DAT_0067bc92) {"
);
source = source.replace(
  "  if (0x13 < _DAT_0067bc92) {\n    while( true ) {",
  "  if (0x13 < _DAT_0067bc92) {\n    if (E2R_fan_phase_diag_count < 64) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN 47638 tail begin: offset=%u remaining=%d\\n\",\n              E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n    }\n    while( true ) {"
);
source = source.replace(
  "      if ((int)uVar16 == 0) break;\n      uVar16 = FUN_00426a30(iVar8,(int)((ulonglong)uVar16 >> 0x20));",
  "      if (E2R_fan_phase_diag_count < 64) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 47638 tail tag: value=%02x offset=%u remaining=%d\\n\",\n                (uint)(byte)uVar16,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n      }\n      if ((int)uVar16 == 0) break;\n      uVar16 = FUN_00426a30(1,(int)((ulonglong)uVar16 >> 0x20));"
);
source = source.replace(
  "      extraout_ECX_36 = (short *)(uintptr_t)(uint)uVar16;\n      uVar16 = FUN_004173c8((int)uVar16,(int)((ulonglong)uVar16 >> 0x20));",
  "      extraout_ECX_36 = (short *)(uintptr_t)(uint)uVar16;\n      if (E2R_fan_phase_diag_count < 64) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 47638 tail alloc: node=%p offset=%u remaining=%d\\n\",\n                (void *)extraout_ECX_36,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n      }\n      uVar16 = FUN_004173c8((int)uVar16,(int)((ulonglong)uVar16 >> 0x20));"
);
source = source.replace(
  "      iVar14 = 0;\n      iVar8 = extraout_ECX_37;\n      if (0 < (short)uVar16) {",
  "      iVar14 = 0;\n      iVar8 = extraout_ECX_37;\n      if (E2R_fan_phase_diag_count < 64) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\"FAN 47638 tail node: mapped=%d child_count=%d offset=%u remaining=%d\\n\",\n                sVar13,(short)uVar16,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n      }\n      if (0 < (short)uVar16) {"
);
source = source.replace(
  "      }\n    }\n  }\n  return;\n}\n\n\n\n/* 00447d94 */",
  "      }\n    }\n  }\n  if (E2R_fan_phase_diag_count < 32) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 47638 complete: offset=%u remaining=%d\\n\",\n            E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n  }\n  return;\n}\n\n\n\n/* 00447d94 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00447d94\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004486d8 \*\//,
`undefined8 __fastcall FUN_00447d94(undefined4 param_1,undefined4 param_2)

{
  int *stream;
  undefined8 uVar1;
  uint offset;
  uint row;
  uint row_end;

  stream = (int *)(uintptr_t)DAT_0047a724;
  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||
      (uint)stream[6] != E2R_STREAM_MAGIC) {
    DAT_0047a724 = FUN_0045eb05(param_1,(char *)0x00474388);
    stream = (int *)(uintptr_t)DAT_0047a724;
  }
  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||
      (uint)stream[6] != E2R_STREAM_MAGIC) {
    if (E2R_archive_read_diag_count < 8) {
      E2R_archive_read_diag_count = E2R_archive_read_diag_count + 1;
      fprintf(stderr,"archive 47d94 open failed: path=%p\\n",(void *)(uintptr_t)param_1);
    }
    return CONCAT44(param_2,0);
  }

  stream[0] = stream[5];
  stream[1] = (int)((byte *)(uintptr_t)stream[2] - (byte *)(uintptr_t)stream[5]);
  *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x40;

  for (offset = 4; offset <= 10000; offset = offset + 4) {
    uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
    *(int *)(0x650f9c + offset) = (int)uVar1;
  }
  for (offset = 4; offset <= 20000; offset = offset + 4) {
    uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
    *(int *)(0x65383c + offset) = (int)uVar1;
  }
  for (offset = 4; offset <= 8000; offset = offset + 4) {
    uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
    *(int *)(0x64f05c + offset) = (int)uVar1;
  }
  for (offset = 4; offset <= 2000; offset = offset + 4) {
    uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
    *(int *)(0x663a0c + offset) = (int)uVar1;
  }
  for (offset = 4; offset <= 0xaf0; offset = offset + 4) {
    uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
    *(int *)(0x662f1c + offset) = (int)uVar1;
  }
  for (row = 0; row < 10; row = row + 1) {
    row_end = (row + 1) * 0x180;
    for (offset = row * 0x180 + 4; offset <= row_end; offset = offset + 4) {
      uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
      *(int *)(0x6458a4 + offset) = (int)uVar1;
    }
  }
  for (offset = 4; offset <= 0x12c0; offset = offset + 4) {
    uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
    *(int *)(0x6445e4 + offset) = (int)uVar1;
  }
  for (offset = 4; offset <= 0x12c0; offset = offset + 4) {
    uVar1 = FUN_00441444((undefined4)(uintptr_t)stream,offset);
    *(int *)(0x6467a4 + offset) = (int)uVar1;
  }
  if (E2R_archive_read_diag_count < 8) {
    E2R_archive_read_diag_count = E2R_archive_read_diag_count + 1;
    fprintf(stderr,"archive 47d94 loaded: cursor=%u remaining=%d\\n",
            (uint)((byte *)(uintptr_t)stream[0] - (byte *)(uintptr_t)stream[5]),
            stream[1]);
  }
  return CONCAT44(param_2,1);
}



/* 004486d8 */`
);
source = source.replace(
  /(void __fastcall FUN_00445000\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar10;\r?\n\s*)uVar10 = FUN_0041ba7c\(param_1,param_2\);/,
  "$1in_EAX = E2R_fan_parse_stream;\n  if (in_EAX == (int *)0x0) {\n    in_EAX = (int *)(uintptr_t)param_1;\n  }\n  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr(in_EAX,0x1c)) {\n    return;\n  }\n  uVar10 = FUN_0041ba7c(param_1,param_2);"
);
source = source.replace(
  "      uVar10 = FUN_0045f38a(uVar8,uVar7);\n      uVar8 = extraout_ECX_00;",
  "      uVar10 = FUN_0045f38a((undefined4)(uintptr_t)in_EAX,(undefined4)(uintptr_t)in_EAX);\n      uVar8 = extraout_ECX_00;"
);
source = source.replace(
  "    FUN_00458d18(extraout_ECX_17,in_EAX);",
  "    FUN_00458d18((undefined4)(uintptr_t)psVar6,(undefined4)(uintptr_t)in_EAX);"
);
source = source.replace(
  /void __fastcall FUN_00422aa0\(undefined4 param_1,undefined2 \*param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00422abc \*\//,
  "void __fastcall FUN_00422aa0(undefined4 param_1,undefined2 *param_2)\n\n{\n  undefined2 *in_EAX;\n  \n  in_EAX = (undefined2 *)(uintptr_t)param_1;\n  if (in_EAX == (undefined2 *)0x0 || param_2 == (undefined2 *)0x0 ||\n      E2R_IsBadWritePtr(in_EAX,6) || IsBadReadPtr(param_2,6)) {\n    return;\n  }\n  *in_EAX = *param_2;\n  in_EAX[1] = param_2[1];\n  in_EAX[2] = param_2[2];\n  return;\n}\n\n\n\n/* 00422abc */"
);
source = source.replace(
  "  uVar13 = FUN_0041ba7c(in_EAX,param_2);\n  puVar10 = (undefined1 *)((ulonglong)uVar13 >> 0x20);\n  piVar7 = extraout_ECX;",
  "  piVar7 = E2R_fan_parse_stream;\n  if (piVar7 == (int *)0x0) {\n    piVar7 = (int *)(uintptr_t)param_1;\n  }\n  if ((uintptr_t)piVar7 < 0x10000u || IsBadReadPtr(piVar7,0x1c)) {\n    return;\n  }\n  in_EAX = (undefined4)(uintptr_t)piVar7;\n  uVar13 = FUN_0041ba7c(in_EAX,param_2);\n  puVar10 = (undefined1 *)((ulonglong)uVar13 >> 0x20);"
);
source = source.replace(
  "      uVar13 = FUN_0045f38a(piVar7,puVar10);\n      piVar7 = extraout_ECX_00;",
  "      uVar13 = FUN_0045f38a((undefined4)(uintptr_t)piVar7,(undefined4)(uintptr_t)piVar7);"
);
source = source.replace(
  "    uVar13 = FUN_00452a58(extraout_ECX_06,(int)((ulonglong)uVar13 >> 0x20));\n    puVar10 = (undefined1 *)uVar13;\n    *(undefined1 **)((int)piVar5 + 6) = puVar10;\n    piVar7 = extraout_ECX_07;",
  "    uVar13 = FUN_00452a58((undefined4)(uintptr_t)iVar12,(int)((ulonglong)uVar13 >> 0x20));\n    puVar10 = (undefined1 *)uVar13;\n    *(undefined1 **)((int)piVar5 + 6) = puVar10;"
);
source = source.replace(
  "          uVar13 = FUN_0045f38a(piVar7,puVar10);\n          piVar7 = extraout_ECX_08;",
  "          uVar13 = FUN_0045f38a((undefined4)(uintptr_t)piVar7,(undefined4)(uintptr_t)piVar7);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00452a58\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar2;\r?\n\s*)while \(0 < DAT_00479e48 \+ in_EAX\)/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  while (0 < DAT_00479e48 + in_EAX)"
);
source = source.replace(
  /undefined4 __cdecl FUN_0045f0a1\(int param_1,byte \*param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045f0d1 \*\//,
  "undefined4 __cdecl FUN_0045f0a1(int param_1,byte *param_2)\n\n{\n  size_t len;\n\n  if (param_1 == 0 || param_2 == (byte *)0x0 ||\n      E2R_IsBadWritePtr((void *)(uintptr_t)param_1,1) ||\n      IsBadReadPtr(param_2,1)) {\n    return 0;\n  }\n  snprintf((char *)(uintptr_t)param_1,256,\"%s\",(char *)param_2);\n  len = strlen((char *)(uintptr_t)param_1);\n  return (undefined4)len;\n}\n\n\n\n/* 0045f0d1 */"
);
source = source.replace(
  /(undefined4 __fastcall FUN_00427584\(undefined4 param_1,int param_2\)[\s\S]*?\r?\n  short sStack_18;\r?\n\s*)uVar13 = 0;/,
  "$1in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX == (short *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      0x1000000u <= (uintptr_t)in_EAX || IsBadReadPtr(in_EAX,0x17c)) {\n    return 0;\n  }\n  uVar13 = 0;"
);
source = source.replace(
  "        lVar15 = FUN_00427584(psVar10,iVar7);",
  "        lVar15 = FUN_00427584((undefined4)(uintptr_t)iVar8,iVar7);"
);
source = source.replace(
  /(void __fastcall FUN_00421074\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  short \*psVar6;\r?\n\s*)FUN_00457818\(param_1,param_2\);/,
  "$1in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX == (short *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      0x1000000u <= (uintptr_t)in_EAX || IsBadReadPtr(in_EAX,0x17c)) {\n    return;\n  }\n  FUN_00457818(param_1,param_2);"
);
source = source.replace(
  "  psVar6 = *(short **)(in_EAX + 0x79);\n  if (psVar6 == (short *)0x0) {",
  "  psVar6 = *(short **)(in_EAX + 0x79);\n  if (psVar6 != (short *)0x0 && IsBadReadPtr(psVar6,0x17c)) {\n    psVar6 = (short *)0x0;\n  }\n  if (psVar6 == (short *)0x0) {"
);
source = source.replace(
  "      FUN_00421074(extraout_ECX,psVar6);\n      uVar4 = extraout_ECX_00;\n      psVar6 = extraout_EDX;",
  "      FUN_00421074((undefined4)(uintptr_t)psVar6,param_2);\n      uVar4 = extraout_ECX_00;"
);
source = source.replace(
  "      FUN_00421074(param_1,param_2);\n      param_1 = extraout_ECX_02;",
  "      FUN_00421074((undefined4)(uintptr_t)iVar5,param_2);\n      param_1 = extraout_ECX_02;"
);
source = source.replace(
  /(void __fastcall FUN_00423858\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined4 local_18;\r?\n\s*)local_3c = in_EAX;/,
  "$1in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX == (short *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      0x1000000u <= (uintptr_t)in_EAX || IsBadReadPtr(in_EAX,0x17c)) {\n    return;\n  }\n  local_3c = in_EAX;"
);
source = source.replace(
  "    FUN_00423858(0,0);",
  "    FUN_00423858((undefined4)(uintptr_t)in_EAX,0);"
);
source = source.replace(
  "        FUN_004249f4();",
  "        FUN_004249f4((undefined4)(uintptr_t)iVar10);"
);
source = source.replace(
  "      FUN_004249f4();\n      iVar4 = extraout_EDX_00;",
  "      FUN_004249f4((undefined4)(uintptr_t)iVar4);\n      iVar4 = extraout_EDX_00;"
);
source = source.replace(
  /(void FUN_004249f4\(void\)[\s\S]*?\r?\n  int iVar6;\r?\n\s*)for \(iVar1 = \*\(int \*\)\(in_EAX \+ 0x1e\);/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x1000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x17c)) {\n    return;\n  }\n  for (iVar1 = *(int *)(in_EAX + 0x1e);"
);
source = source.replace(
  "void FUN_004249f4(void)",
  "void FUN_004249f4(undefined4 param_1)"
);
source = source.replace(
  "  DAT_00479de8 = 1;\n  return CONCAT44(param_2,uVar3);",
  "  DAT_00479de8 = 1;\n  if (_DAT_0073cc3c == 0 && E2R_start_game_probe_last_mode == 0) {\n    E2R_SelectSceneRecord(785);\n  }\n  return CONCAT44(param_2,uVar3);"
);
source = source.replace(
  "    FUN_004249f4();\n  }\n  return;\n}\n\n\n\n/* 00424b48 */",
  "    FUN_004249f4((undefined4)(uintptr_t)iVar1);\n  }\n  return;\n}\n\n\n\n/* 00424b48 */"
);
source = source.replace(
  "  if ((((DAT_0047a34a == 0) && (DAT_0047a72c == 0)) && (DAT_0047a366 == 0)) && (DAT_0047a740 == 0))\n  {\n    if (((DAT_0047a470 == 0) || (param_1 = *(int *)(DAT_0047a470 + 0xa6), param_1 == 0)) ||\n       ((*(byte *)(param_1 + 0xc) & 2) == 0)) {",
  "  if (DAT_0047a470 != 0 &&\n     ((uint)DAT_0047a470 < 0x10000u || 0x70000000u <= (uint)DAT_0047a470 ||\n      IsBadReadPtr((void *)(uintptr_t)DAT_0047a470,0x136))) {\n    DAT_0047a470 = 0;\n  }\n  if ((((DAT_0047a34a == 0) && (DAT_0047a72c == 0)) && (DAT_0047a366 == 0)) && (DAT_0047a740 == 0))\n  {\n    param_1 = DAT_0047a470 == 0 ? 0 : *(int *)(DAT_0047a470 + 0xa6);\n    if (param_1 != 0 &&\n       ((uint)param_1 < 0x10000u || 0x70000000u <= (uint)param_1 ||\n        IsBadReadPtr((void *)(uintptr_t)param_1,0x10))) {\n      param_1 = 0;\n    }\n    if ((param_1 == 0) || ((*(byte *)(param_1 + 0xc) & 2) == 0)) {"
);
source = source.replace(
  "  if (((DAT_0047a470 != 0) && (*(short *)(DAT_0047a470 + 0x82) != 0xb)) && (DAT_0047a438 == 0)) {",
  "#if defined(__SANITIZE_ADDRESS__) || __has_feature(address_sanitizer)\n  if (!E2R_IsKnownActorPointer(DAT_0047a470)) {\n    if (E2R_actor_current_diag_count < 16) {\n      E2R_actor_current_diag_count = E2R_actor_current_diag_count + 1;\n      fprintf(stderr,\n              \"current actor invalid at 4c164: current=0x%lx param=0x%lx \"\n              \"DAT_0047a34a=%lu DAT_0047a438=%lu table0=0x%lx \"\n              \"last_site=%s last_value=0x%lx caller=%p\\n\",\n              (unsigned long)DAT_0047a470,(unsigned long)param_1,\n              (unsigned long)DAT_0047a34a,(unsigned long)DAT_0047a438,\n              (unsigned long)*(int *)0x00630b60,\n              E2R_current_actor_last_site != (char *)0x0 ?\n                E2R_current_actor_last_site : \"(none)\",\n              (unsigned long)E2R_current_actor_last_value,\n              __builtin_return_address(0));\n    }\n    DAT_0047a470 = E2R_TraceCurrentActorWrite(\"4c164.guard\",0);\n    return;\n  }\n#endif\n  if (((DAT_0047a470 != 0) && (*(short *)(DAT_0047a470 + 0x82) != 0xb)) && (DAT_0047a438 == 0)) {"
);
source = source.replace(
  "  sVar1 = 0;\n  do {\n    iVar2 = (int)sVar1;\n    *(undefined2 *)(&DAT_006372c2 + iVar2 * 2) = *(undefined2 *)(in_EAX + iVar2 * 2);",
  "  if ((short)_DAT_0073ccba < 0 || 0x4b0 <= (short)_DAT_0073ccba) {\n    return;\n  }\n  in_EAX = 0x0067c728 + (short)_DAT_0073ccba * 0x1c;\n  sVar1 = 0;\n  do {\n    iVar2 = (int)sVar1;\n    *(undefined2 *)(&DAT_006372c2 + iVar2 * 2) = *(undefined2 *)(in_EAX + iVar2 * 2);"
);
source = source.replace(
  "  uVar16 = FUN_004418fc(param_1,in_EAX);",
  "  in_EAX = (undefined4)(uintptr_t)E2R_fan_parse_stream;\n  if (E2R_fan_parse_stream == (int *)0x0) {\n    in_EAX = param_1;\n  }\n  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x1c)) {\n    return;\n  }\n  uVar16 = FUN_004418fc((undefined4)(uintptr_t)\"sondoor1\",in_EAX);"
);
source = source.replace(
  "  uVar16 = FUN_00441958(uVar10,(int)((ulonglong)uVar16 >> 0x20));",
  "  uVar16 = FUN_00441958((undefined4)(uintptr_t)\"sorclear\",(int)((ulonglong)uVar16 >> 0x20));"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0043a800\(undefined4 param_1,int param_2\)[\s\S]*?\r?\n  undefined8 uVar5;\r?\n\s*)iVar2 = _DAT_0063726c;/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x54)) {\n    return CONCAT44(param_2,0);\n  }\n  if (_DAT_0063726c != 0 &&\n     ((uint)_DAT_0063726c < 0x10000u || 0x70000000u <= (uint)_DAT_0063726c ||\n      IsBadReadPtr((void *)(uintptr_t)_DAT_0063726c,0x50))) {\n    _DAT_0063726c = 0;\n  }\n  if (_DAT_00637248 != 0 &&\n     ((uint)_DAT_00637248 < 0x10000u || 0x70000000u <= (uint)_DAT_00637248 ||\n      IsBadReadPtr((void *)(uintptr_t)_DAT_00637248,0x54))) {\n    _DAT_00637248 = 0;\n  }\n  iVar2 = _DAT_0063726c;"
);
source = source.replace(
  "      iVar1 = *(int *)(_DAT_0063726c + 0x4c);\n      iVar4 = _DAT_0063726c;\n      while (iVar1 != 0) {\n        if (in_EAX == *(int *)(iVar4 + 0x4c)) {",
  "      iVar1 = *(int *)(_DAT_0063726c + 0x4c);\n      iVar4 = _DAT_0063726c;\n      while (iVar1 != 0) {\n        if (IsBadReadPtr((void *)(uintptr_t)iVar4,0x50) ||\n            IsBadReadPtr((void *)(uintptr_t)iVar1,0x50)) break;\n        if (in_EAX == *(int *)(iVar4 + 0x4c)) {"
);
source = source.replace(
  "  do {\n    if (iVar2 == 0) break;\n    if (iVar2 == in_EAX) {",
  "  do {\n    if (iVar2 == 0) break;\n    if (IsBadReadPtr((void *)(uintptr_t)iVar2,0x50)) break;\n    if (iVar2 == in_EAX) {"
);
source = source.replace(
  "      iVar4 = *(int *)(_DAT_00637248 + 0x50);\n      iVar2 = _DAT_00637248;\n      while (iVar4 != 0) {\n        if (in_EAX == *(int *)(iVar2 + 0x50)) {",
  "      iVar4 = *(int *)(_DAT_00637248 + 0x50);\n      iVar2 = _DAT_00637248;\n      while (iVar4 != 0) {\n        if (IsBadReadPtr((void *)(uintptr_t)iVar2,0x54) ||\n            IsBadReadPtr((void *)(uintptr_t)iVar4,0x54)) break;\n        if (in_EAX == *(int *)(iVar2 + 0x50)) {"
);
source = source.replace(
  "  for (iVar4 = *(int *)(in_EAX + 0x1e); iVar4 != 0; iVar4 = *(int *)(iVar4 + 0x4c)) {\n    iVar2 = *(int *)(iVar4 + 0x11e);\n    while (iVar2 != 0) {\n      FUN_0045366c();\n      iVar2 = *(int *)(extraout_EDX + 0x26);\n    }\n    FUN_00453508();\n    in_EAX = extraout_ECX;\n  }\n  iVar4 = *(int *)(in_EAX + 0xd8);\n  while (iVar4 != 0) {\n    FUN_00453264();\n    iVar4 = *(int *)(extraout_EDX_00 + 0x1e);\n  }\n  uVar3 = FUN_00453264();",
  "  for (iVar4 = *(int *)(in_EAX + 0x1e); iVar4 != 0; iVar4 = iVar1) {\n    if ((uint)iVar4 < 0x10000u || 0x70000000u <= (uint)iVar4 ||\n        IsBadReadPtr((void *)(uintptr_t)iVar4,0x122)) break;\n    iVar1 = *(int *)(iVar4 + 0x4c);\n    iVar2 = *(int *)(iVar4 + 0x11e);\n    while (iVar2 != 0) {\n      if ((uint)iVar2 < 0x10000u || 0x70000000u <= (uint)iVar2 ||\n          IsBadReadPtr((void *)(uintptr_t)iVar2,0x2a)) break;\n      extraout_EDX = *(int *)(iVar2 + 0x26);\n      *(undefined2 *)(iVar2 + 2) = 1;\n      iVar2 = extraout_EDX;\n    }\n    *(undefined2 *)(iVar4 + 4) = 0x8000;\n  }\n  iVar4 = *(int *)(in_EAX + 0xd8);\n  while (iVar4 != 0) {\n    if ((uint)iVar4 < 0x10000u || 0x70000000u <= (uint)iVar4 ||\n        IsBadReadPtr((void *)(uintptr_t)iVar4,0x44)) break;\n    extraout_EDX_00 = *(int *)(iVar4 + 0x1e);\n    *(undefined2 *)(iVar4 + 2) = 0x8000;\n    iVar4 = extraout_EDX_00;\n  }\n  *(undefined2 *)(in_EAX + 4) = 0x8000;\n  uVar3 = 0;"
);
source = source.replace(
  "            FUN_0043a800(extraout_ECX_32,iVar12);",
  "            FUN_0043a800((undefined4)(uintptr_t)psVar16,iVar12);"
);
source = source.replace(
  "      uVar16 = FUN_004173c8(puVar7 + 2,(int)((ulonglong)uVar16 >> 0x20));\n      uVar10 = (undefined4)((ulonglong)uVar16 >> 0x20);\n      sVar12 = sVar12 + 1;\n      *(short *)(extraout_ECX_02 + -2) = (short)uVar16;\n      uVar16 = CONCAT44(uVar10,_DAT_00ac4af0);\n      puVar7 = extraout_ECX_02;",
  "      uVar16 = FUN_004173c8(in_EAX,(int)((ulonglong)uVar16 >> 0x20));\n      uVar10 = (undefined4)((ulonglong)uVar16 >> 0x20);\n      sVar12 = sVar12 + 1;\n      *(short *)puVar7 = (short)uVar16;\n      uVar16 = CONCAT44(uVar10,_DAT_00ac4af0);\n      puVar7 = puVar7 + 2;"
);
source = source.replace(
  /undefined8 __fastcall FUN_00426478\(int param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004265ac \*\//,
  "undefined8 __fastcall FUN_00426478(int param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  undefined8 uVar2;\n  \n  uVar2 = FUN_00453414(param_1,param_2);\n  iVar1 = (int)uVar2;\n  *(undefined2 *)(iVar1 + 2) = 1;\n  *(undefined4 *)(iVar1 + 0x11a) = _DAT_00636588;\n  *(undefined2 *)(iVar1 + 4) = 7;\n  FUN_00422330();\n  FUN_00422330();\n  *(undefined2 *)(iVar1 + 0x1c) = 0;\n  *(undefined4 *)(iVar1 + 0x1e) = 0;\n  *(undefined4 *)(iVar1 + 0x44) = 0;\n  *(undefined2 *)(iVar1 + 0x96) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x9a) = 0x100;\n  *(undefined4 *)(iVar1 + 0xd8) = 0;\n  *(undefined2 *)(iVar1 + 0x124) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x138) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x136) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x13a) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x13c) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x13e) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x144) = 6;\n  *(undefined4 *)(iVar1 + 0xe4) = 0x6368d0;\n  *(undefined2 *)(iVar1 + 0x172) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x162) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x16a) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x16c) = 0;\n  *(undefined2 *)(iVar1 + 0x174) = 100;\n  *(undefined2 *)(iVar1 + 0x176) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x182) = 100;\n  *(undefined2 *)(iVar1 + 0x186) = 100;\n  *(undefined2 *)(iVar1 + 0x188) = 0xffff;\n  *(undefined2 *)(iVar1 + 0x18a) = 0xffff;\n  *(int *)(iVar1 + 0x22) = iVar1;\n  *(undefined2 *)(iVar1 + 0x1a) = *(undefined2 *)(iVar1 + 0x1c);\n  *(undefined2 *)(iVar1 + 0x18) = *(undefined2 *)(iVar1 + 0x1c);\n  *(undefined2 *)(iVar1 + 0x122) = *(undefined2 *)(iVar1 + 0x124);\n  *(int *)(iVar1 + 0x50) = _DAT_00637248;\n  _DAT_00637248 = iVar1;\n  return CONCAT44(param_2,iVar1);\n}\n\n\n\n/* 004265ac */"
);
source = source.replace(
  /(undefined8 __fastcall FUN_004265ac\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar6;\r?\n\s*)uVar6 = FUN_00453510\(param_1,param_2\);\r?\n  iVar4 = \(int\)uVar6;/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  uVar6 = FUN_00453510(0,param_2);\n  iVar4 = (int)uVar6;\n  if (iVar4 == 0 || in_EAX == 0) {\n    return CONCAT44(param_2,0);\n  }"
);
source = source.replace(
  "  return CONCAT44(param_2,extraout_EDX);\n}\n\n\n\n/* 00426798 */",
  "  return CONCAT44(param_2,iVar4);\n}\n\n\n\n/* 00426798 */"
);
source = source.replace(
  "      uVar12 = FUN_004265ac(param_1,*(int *)(*(int *)(unaff_ESI + 0x11) + 0x54));",
  "      uVar12 = FUN_004265ac((undefined4)(uintptr_t)unaff_ESI,\n                            *(int *)(*(int *)(unaff_ESI + 0x11) + 0x54));"
);
source = source.replace(
  "  case 0x7:\n    psVar7 = (short *)(*(int *)(in_EAX + 1) >> 0x10);\n    if (*(int *)(*(int *)(*(int *)(unaff_ESI + 0x11) + 0x54) + (int)psVar7 * 4) == 0) {\n      uVar12 = FUN_004265ac((undefined4)(uintptr_t)unaff_ESI,\n                            *(int *)(*(int *)(unaff_ESI + 0x11) + 0x54));\n      psVar7 = (short *)uVar12;\n      *psVar7 = in_EAX[2];\n      *(short **)(*(int *)(*(int *)(psVar7 + 0x11) + 0x54) + *psVar7 * 4) = psVar7;\n      return psVar7;\n    }",
  "  case 0x7:\n    psVar7 = (short *)(*(int *)(in_EAX + 1) >> 0x10);\n    if ((unaff_ESI == (short *)0x0 || IsBadReadPtr(unaff_ESI,0x26) ||\n         *(int *)(unaff_ESI + 0x11) == 0 ||\n         IsBadReadPtr((void *)(uintptr_t)*(int *)(unaff_ESI + 0x11),0x58)) &&\n        param_2 != (short *)0x0) {\n      unaff_ESI = param_2;\n    }\n    if (unaff_ESI == (short *)0x0 || IsBadReadPtr(unaff_ESI,0x26) ||\n        *(int *)(unaff_ESI + 0x11) == 0 ||\n        IsBadReadPtr((void *)(uintptr_t)*(int *)(unaff_ESI + 0x11),0x58)) {\n      return (short *)0x0;\n    }\n    iVar10 = *(int *)(unaff_ESI + 0x11);\n    iVar11 = *(int *)(iVar10 + 0x54);\n    if (iVar11 == 0 || IsBadReadPtr((void *)(uintptr_t)iVar11,(int)psVar7 * 4 + 4)) {\n      return (short *)0x0;\n    }\n    if (*(int *)(iVar11 + (int)psVar7 * 4) == 0) {\n      uVar12 = FUN_004265ac((undefined4)(uintptr_t)unaff_ESI,iVar11);\n      psVar7 = (short *)uVar12;\n      *psVar7 = in_EAX[2];\n      *(short **)(iVar11 + *psVar7 * 4) = psVar7;\n      return psVar7;\n    }"
);
source = source.replace(
  "    *(short **)((undefined1 *)0x00630b60 + *psVar7 * 4) = psVar7;\n    return psVar7;",
  "    *(short **)((undefined1 *)0x00630b60 + *psVar7 * 4) = psVar7;\n    *(short **)(*(int *)(*(int *)(psVar7 + 0x11) + 0x54) + *psVar7 * 4) = psVar7;\n    return psVar7;"
);
source = source.replace(
  "    *psVar7 = in_EAX[2];\n    psVar7[0xb9] = DAT_00479e4c;",
  "    *psVar7 = *in_EAX;\n    psVar7[0xb9] = DAT_00479e4c;"
);
source = source.replace(
  "      if (*(int *)((undefined1 *)0x00630b60 + (*(int *)(iVar4 + 2) >> 0x10) * 4) == 0) goto LAB_004444a9;",
  "      if (*(int *)((undefined1 *)0x00630b60 + *(short *)iVar4 * 4) == 0) goto LAB_004444a9;"
);
source = source.replace(
  "    uVar12 = FUN_004265ac(param_1,iVar9);",
  "    uVar12 = FUN_004265ac((undefined4)(uintptr_t)unaff_ESI,iVar9);"
);
source = source.replace(
  /  case 0x7:\r?\n    psVar7 = \(short \*\)\(\*\(int \*\)\(in_EAX \+ 1\) >> 0x10\);[\s\S]*?    break;\r?\n  case 0x8:/,
  "  case 0x7:\n    psVar7 = (short *)(*(int *)(in_EAX + 1) >> 0x10);\n    if ((unaff_ESI == (short *)0x0 || IsBadReadPtr(unaff_ESI,0x26) ||\n         *(int *)(unaff_ESI + 0x11) == 0 ||\n         IsBadReadPtr((void *)(uintptr_t)*(int *)(unaff_ESI + 0x11),0x58)) &&\n        param_2 != (short *)0x0) {\n      unaff_ESI = param_2;\n    }\n    if (unaff_ESI == (short *)0x0 || IsBadReadPtr(unaff_ESI,0x26) ||\n        *(int *)(unaff_ESI + 0x11) == 0 ||\n        IsBadReadPtr((void *)(uintptr_t)*(int *)(unaff_ESI + 0x11),0x58)) {\n      return (short *)0x0;\n    }\n    iVar10 = *(int *)(unaff_ESI + 0x11);\n    iVar11 = *(int *)(iVar10 + 0x54);\n    if (iVar11 == 0 || IsBadReadPtr((void *)(uintptr_t)iVar11,(int)psVar7 * 4 + 4)) {\n      return (short *)0x0;\n    }\n    if (*(int *)(iVar11 + (int)psVar7 * 4) == 0) {\n      uVar12 = FUN_004265ac((undefined4)(uintptr_t)unaff_ESI,iVar11);\n      psVar7 = (short *)uVar12;\n      *psVar7 = in_EAX[2];\n      *(short **)(iVar11 + *psVar7 * 4) = psVar7;\n      return psVar7;\n    }\n    break;\n  case 0x8:"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00426858\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar4;\r?\n\s*)uVar4 = FUN_00453674\(param_1,param_2\);\r?\n  puVar3 = \(undefined2 \*\)uVar4;/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  uVar4 = FUN_00453674(0,param_2);\n  puVar3 = (undefined2 *)uVar4;\n  if (puVar3 == (undefined2 *)0x0 || in_EAX == 0 ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x122)) {\n    return CONCAT44(param_2,0);\n  }"
);
source = source.replace(
  /(undefined2 \* __fastcall FUN_00426798\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  undefined8 uVar5;\r?\n\s*)uVar5 = FUN_004536e0\(in_EAX,param_2\);\r?\n  puVar4 = \(undefined2 \*\)uVar5;\r?\n  iVar1 = \*\(int \*\)\(extraout_ECX \+ 0xd8\);/,
  "$1in_EAX = (undefined4)(uintptr_t)param_1;\n  uVar5 = FUN_004536e0(0,param_2);\n  puVar4 = (undefined2 *)uVar5;\n  if (puVar4 == (undefined2 *)0x0 || in_EAX == 0 ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0xdc)) {\n    return (undefined2 *)0x0;\n  }\n  iVar1 = *(int *)((int)(uintptr_t)in_EAX + 0xd8);"
);
source = source.replace(
  "    *(undefined2 **)(extraout_ECX + 0xd8) = puVar4;",
  "    *(undefined2 **)((int)(uintptr_t)in_EAX + 0xd8) = puVar4;"
);
source = source.replace(
  "    uVar12 = FUN_00426858(param_1,iVar9);\n    psVar7 = (short *)uVar12;\n    *psVar7 = in_EAX[2];",
  "    uVar12 = FUN_00426858((undefined4)(uintptr_t)unaff_ESI,iVar9);\n    psVar7 = (short *)uVar12;\n    if (psVar7 == (short *)0x0) {\n      return (short *)0x0;\n    }\n    *psVar7 = in_EAX[2];"
);
source = source.replace(
  "        psVar7 = FUN_00426798(param_1,local_38);\n        sVar6 = *in_EAX;",
  "        psVar7 = FUN_00426798((undefined4)(uintptr_t)unaff_ESI,local_38);\n        if (psVar7 == (short *)0x0) {\n          return (short *)0x0;\n        }\n        sVar6 = *in_EAX;"
);
source = source.replace(
  "      iVar9 = iVar10;\n      } while (iVar10 != 0xc);",
  "        iVar9 = iVar10;\n      } while (iVar10 != 0xc);"
);
source = source.replace(
  "  case 0x2a:\n    psVar7 = in_EAX;",
  "  case 0x2a:\n    if ((local_18 == (short *)0x0 || E2R_IsBadWritePtr(local_18,10)) &&\n        unaff_ESI != (short *)0x0) {\n      local_18 = unaff_ESI;\n    }\n    if (local_18 == (short *)0x0 || E2R_IsBadWritePtr(local_18,10)) {\n      return (short *)0x0;\n    }\n    psVar7 = in_EAX;"
);
source = source.replace(
  /(void FUN_00432e08\(void\)[\s\S]*?\r?\n  ushort uVar4;\r?\n\s*)uVar1 =/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xdc)) {\n    return;\n  }\n  uVar1 ="
);
source = source.replace(
  /(void FUN_00426220\(void\)[\s\S]*?\r?\n  int iVar3;\r?\n\s*)iVar1 =/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x126)) {\n    return;\n  }\n  iVar1 ="
);
source = source.replace(
  /(void FUN_00426c3c\(void\)[\s\S]*?\r?\n  int in_EAX;\r?\n\s*)for/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x136)) {\n    return;\n  }\n  for"
);
source = source.replace(
  /(void FUN_00426ca4\(void\)[\s\S]*?\r?\n  short \*extraout_ECX_01;\r?\n\s*)bVar4 =/,
  "$1in_EAX = (short *)(uintptr_t)E2R_actor_calc_context;\n  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,0x136)) {\n    return;\n  }\n  bVar4 ="
);
source = source.replace(
  "      FUN_00422aa0(in_EAX,in_EAX + 0x42);\n      FUN_00422aa0(extraout_ECX,(undefined2 *)(extraout_ECX + 0x90));\n      *(short *)(*extraout_ECX_00 * 2 + 0x671fc0) = extraout_ECX_00[0x91];\n      *(short *)(*extraout_ECX_00 * 2 + 0x647a68) = extraout_ECX_00[0x76];\n      *(char *)(*extraout_ECX_00 + 0x64c950) = (char)extraout_ECX_00[0xc2];\n      in_EAX = extraout_ECX_00;\n      if ((*(int *)(extraout_ECX_00 + 0x53) != 0) && (DAT_0047a34a == 0)) {\n        for (iVar2 = *(int *)(extraout_ECX_00 + 0x57); iVar2 != 0; iVar2 = *(int *)(iVar2 + 2)) {",
  "      FUN_00422aa0((undefined4)(uintptr_t)in_EAX,in_EAX + 0x42);\n      FUN_00422aa0((undefined4)(uintptr_t)in_EAX,(undefined2 *)((undefined1 *)in_EAX + 0x90));\n      *(short *)(*in_EAX * 2 + 0x671fc0) = in_EAX[0x91];\n      *(short *)(*in_EAX * 2 + 0x647a68) = in_EAX[0x76];\n      *(char *)(*in_EAX + 0x64c950) = (char)in_EAX[0xc2];\n      if ((*(int *)(in_EAX + 0x53) != 0) && (DAT_0047a34a == 0)) {\n        for (iVar2 = *(int *)(in_EAX + 0x57); iVar2 != 0; iVar2 = *(int *)(iVar2 + 2)) {"
);
source = source.replace(
  /(undefined4 FUN_00442954\(void\)[\s\S]*?\r?\n  short sVar4;\r?\n\s*)iVar1 =/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xe6)) {\n    return 0;\n  }\n  iVar1 ="
);
source = source.replace(
  /(undefined4 FUN_004429e0\(void\)[\s\S]*?\r?\n  int iVar2;\r?\n\s*)sVar1 =/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xec)) {\n    return 0;\n  }\n  sVar1 ="
);
source = source.replaceAll(
  "    FUN_00432e08();\n    FUN_00442954();\n    FUN_004429e0();",
  "    E2R_actor_calc_context = iVar1;\n    FUN_00432e08();\n    FUN_00442954();\n    FUN_004429e0();\n    E2R_actor_calc_context = 0;"
);
source = source.replace(
  "  FUN_00432e08();\n  FUN_00442954();\n  FUN_004429e0();",
  "  E2R_actor_calc_context = iVar4;\n  FUN_00432e08();\n  FUN_00442954();\n  FUN_004429e0();\n  E2R_actor_calc_context = 0;"
);
source = source.replace(
  "    psVar7 = (short *)FUN_00442954();",
  "    E2R_actor_calc_context = (int)(uintptr_t)unaff_ESI;\n    psVar7 = (short *)FUN_00442954();\n    E2R_actor_calc_context = 0;"
);
source = source.replace(
  "    FUN_00432e08();\n    psVar7 = (short *)FUN_0042ce70();",
  "    E2R_actor_calc_context = (int)(uintptr_t)unaff_ESI;\n    FUN_00432e08();\n    E2R_actor_calc_context = 0;\n    psVar7 = (short *)FUN_0042ce70();"
);
source = source.replace(
  "  if ((*(byte *)(in_EAX + 2) & 8) == 0) {\n    sVar2 = 0;",
  "  if (E2R_actor_calc_context != 0) {\n    in_EAX = E2R_actor_calc_context;\n  }\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xec)) {\n    return 0;\n  }\n  if ((*(byte *)(in_EAX + 2) & 8) == 0) {\n    sVar2 = 0;"
);
source = source.replace(
  "  for (iVar3 = *(int *)(in_EAX + 0x1e); iVar3 != 0; iVar3 = *(int *)(iVar3 + 0xca)) {\n    if ((*(byte *)(iVar3 + 2) & 4) == 0) {",
  "  for (iVar3 = *(int *)(in_EAX + 0x1e); iVar3 != 0; iVar3 = *(int *)(iVar3 + 0xca)) {\n    if ((uintptr_t)iVar3 >= 0x10000000u ||\n        IsBadReadPtr((void *)(uintptr_t)iVar3,0xe4)) {\n      break;\n    }\n    if ((*(byte *)(iVar3 + 2) & 4) == 0) {"
);
source = source.replace(
  "    psVar7 = (short *)FUN_004429e0();",
  "    E2R_actor_calc_context = (int)(uintptr_t)unaff_ESI;\n    psVar7 = (short *)FUN_004429e0();\n    E2R_actor_calc_context = 0;"
);
source = source.replace(
  "(FUN_00426220(), iVar5 = extraout_EDX_00, _DAT_0067bc92 < 0x16)",
  "(E2R_actor_calc_context = (int)(uintptr_t)DAT_0047a470, FUN_00426220(),\n         E2R_actor_calc_context = 0, iVar5 = extraout_EDX_00, _DAT_0067bc92 < 0x16)"
);
source = source.replace(
  "            *(undefined4 *)((undefined1 *)0x00630b60 + *psVar16 * 4) = 0;\n            FUN_00426ca4();",
  "            *(undefined4 *)((undefined1 *)0x00630b60 + *psVar16 * 4) = 0;\n            E2R_actor_calc_context = (int)(uintptr_t)psVar16;\n            FUN_00426ca4();\n            E2R_actor_calc_context = 0;"
);
source = source.replace(
  /undefined8 __fastcall FUN_004268e4\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0042692c \*\//,
  "undefined8 __fastcall FUN_004268e4(undefined4 param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  int iVar2;\n  \n  iVar2 = (int)(uintptr_t)param_1;\n  iVar1 = FUN_0045f1ff(1,0x39);\n  if (iVar1 == 0) {\n    FUN_00414e68();\n  }\n  FUN_0045fc70(0x35,0x20202020);\n  *(undefined4 *)(iVar1 + 0x35) = *(undefined4 *)(iVar2 + 2);\n  *(int *)(iVar2 + 2) = iVar1;\n  return CONCAT44(param_2,iVar1);\n}\n\n\n\n/* 0042692c */"
);
source = source.replace(
  /undefined8 __fastcall FUN_0042692c\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00426974 \*\//,
  "undefined8 __fastcall FUN_0042692c(undefined4 param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  int iVar2;\n  \n  iVar2 = (int)(uintptr_t)param_1;\n  iVar1 = FUN_0045f1ff(1,0x39);\n  if (iVar1 == 0) {\n    FUN_00414e68();\n  }\n  FUN_0045fc70(0x35,0x20202020);\n  *(undefined4 *)(iVar1 + 0x35) = *(undefined4 *)(iVar2 + 0x35);\n  *(int *)(iVar2 + 0x35) = iVar1;\n  return CONCAT44(param_2,iVar1);\n}\n\n\n\n/* 00426974 */"
);
source = source.replace(
  "  puVar2 = (undefined2 *)FUN_0045f1ff(param_1,0xe);",
  "  puVar2 = (undefined2 *)FUN_0045f1ff(1,0xe);"
);
source = source.replace(
  /void FUN_004526e4\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00452738 \*\//,
  "void FUN_004526e4(short *param_1)\n\n{\n  int iVar1;\n  short *psVar2;\n  \n  psVar2 = _DAT_00637250;\n  *(undefined4 *)(*param_1 * 4 + 0x6297c0) = 0;\n  if (param_1 == psVar2) {\n    _DAT_00637250 = *(short **)(psVar2 + 5);\n  }\n  else {\n    iVar1 = *(int *)(psVar2 + 5);\n    while (iVar1 != 0) {\n      if (param_1 == *(short **)(psVar2 + 5)) {\n        *(undefined4 *)(psVar2 + 5) = *(undefined4 *)(*(short **)(psVar2 + 5) + 5);\n        return;\n      }\n      psVar2 = *(short **)(psVar2 + 5);\n      iVar1 = *(int *)(psVar2 + 5);\n    }\n  }\n  return;\n}\n\n\n\n/* 00452738 */"
);
source = source.replace(
  /(ulonglong __fastcall FUN_004435e8\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined4 uStack_4;\r?\n\s*)uStack_4 = param_2;/,
  "$1in_EAX = (uint)(uintptr_t)param_1;\n  uStack_4 = param_2;"
);
source = source.replace(
  /undefined4 FUN_00453264\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045326c \*\//,
  "undefined4 FUN_00453264(void)\n\n{\n  if (E2R_fan_parse_record != (short *)0x0 &&\n      !IsBadReadPtr(E2R_fan_parse_record,10)) {\n    E2R_fan_parse_record[1] = (short)0x8000;\n  }\n  return 0;\n}\n\n\n\n/* 0045326c */"
);
source = source.replace(
  /undefined4 __fastcall FUN_0045326c\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045328c \*\//,
  "undefined4 __fastcall FUN_0045326c(undefined4 param_1,undefined4 param_2)\n\n{\n  undefined4 extraout_ECX;\n  undefined4 extraout_ECX_00;\n  undefined4 extraout_ECX_01;\n  undefined4 extraout_EDX;\n  undefined8 uVar1;\n  \n  while( true ) {\n    uVar1 = FUN_0045328c(param_1,param_2);\n    if ((int)uVar1 != 0) {\n      return (undefined4)uVar1;\n    }\n    uVar1 = FUN_00452f18(extraout_ECX,(int)((ulonglong)uVar1 >> 0x20));\n    param_2 = (undefined4)((ulonglong)uVar1 >> 0x20);\n    param_1 = extraout_ECX_00;\n    if ((int)uVar1 == 0) {\n      FUN_00414e68();\n      param_1 = extraout_ECX_01;\n      param_2 = extraout_EDX;\n    }\n  }\n}\n\n\n\n/* 0045328c */"
);
source = source.replace(
  /void FUN_0045de8b\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045df96 \*\//,
  "void FUN_0045de8b(void)\n\n{\n  return;\n}\n\n\n\n/* 0045df96 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00453510\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045357c \*\//,
  "undefined8 __fastcall FUN_00453510(undefined4 param_1,undefined4 param_2)\n\n{\n  int offset;\n  undefined1 *slot;\n  \n  (void)param_1;\n  do {\n    for (offset = 0; offset < 0x155cc0; offset = offset + 0x15e) {\n      if ((*(ushort *)((undefined1 *)0x00950d40 + offset) & 0x8000) != 0) {\n        slot = (undefined1 *)(0x00950d3c + offset);\n        memset(slot,0,0x15e);\n        return CONCAT44(param_2,(undefined4)(uintptr_t)slot);\n      }\n    }\n    if ((int)FUN_0045311c(0,0) == 0) {\n      FUN_00414e68();\n    }\n  } while( true );\n}\n\n\n\n/* 0045357c */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00453674\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004536e0 \*\//,
  "undefined8 __fastcall FUN_00453674(undefined4 param_1,undefined4 param_2)\n\n{\n  int offset;\n  undefined1 *slot;\n  \n  (void)param_1;\n  do {\n    for (offset = 0; offset < 0x12750; offset = offset + 0x2a) {\n      if ((*(ushort *)((undefined1 *)0x00838bfe + offset) & 1) != 0) {\n        slot = (undefined1 *)(0x00838bfc + offset);\n        memset(slot,0,0x2a);\n        return CONCAT44(param_2,(undefined4)(uintptr_t)slot);\n      }\n    }\n    if ((int)FUN_0045311c(0,0) == 0) {\n      FUN_00414e68();\n    }\n  } while( true );\n}\n\n\n\n/* 004536e0 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_004536e0\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045374c \*\//,
  "undefined8 __fastcall FUN_004536e0(undefined4 param_1,undefined4 param_2)\n\n{\n  int offset;\n  undefined1 *slot;\n  \n  (void)param_1;\n  do {\n    for (offset = 0; offset < 0x1de20; offset = offset + 0x44) {\n      if ((*(ushort *)((undefined1 *)0x0084b34e + offset) & 0x8000) != 0) {\n        slot = (undefined1 *)(0x0084b34c + offset);\n        memset(slot,0,0x44);\n        return CONCAT44(param_2,(undefined4)(uintptr_t)slot);\n      }\n    }\n    if ((int)FUN_0045311c(0,0) == 0) {\n      FUN_00414e68();\n    }\n  } while( true );\n}\n\n\n\n/* 0045374c */"
);
source = source.replace(
  "      uVar15 = FUN_004465dc(iVar12,iVar7);",
  "      uVar15 = FUN_004465dc((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[0]);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_004465dc\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined2 uStack_1a;\r?\n\s*)local_1c = 0;/,
  "$1in_EAX = (char *)(uintptr_t)param_1;\n  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr(in_EAX,1)) {\n    return CONCAT44(param_2,0xffff);\n  }\n  \n  local_1c = 0;"
);
source = source.replace(
  "  }\n  \n  local_1c = 0;\n  puVar6 = _DAT_006366a4;",
  "  }\n  return CONCAT44(param_2,(ushort)E2R_InternPackedName(in_EAX,(char *)_DAT_006366a4,\n                                                       4000,0x22b));\n  \n  local_1c = 0;\n  puVar6 = _DAT_006366a4;"
);
const fanNameInternSpecs = [
  ["004466c4", "_DAT_006366b4", "10000", "5000",
   "FUN_004466c4(iVar12,(int)(short)iVar12)",
   "FUN_004466c4((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[1])"],
  ["0044679c", "_DAT_006366b8", "0x1117", "2000",
   "FUN_0044679c(iVar12,(int)(short)iVar12)",
   "FUN_0044679c((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[2])"],
  ["00446874", "_DAT_006366bc", "5000", "0x9c4",
   "FUN_00446874(iVar12,(int)(short)iVar12)",
   "FUN_00446874((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[3])"],
  ["0044694c", "_DAT_00636698", "6000", "2000",
   "FUN_0044694c(iVar12,uVar11 & 0xffffff00)",
   "FUN_0044694c((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[5])"],
  ["00446a24", "_DAT_0063668c", "1000", "500",
   "FUN_00446a24(iVar12,(int)(short)iVar12)",
   "FUN_00446a24((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[6])"],
  ["00446afc", "(char *)_DAT_00636678", "5000", "700",
   "FUN_00446afc(iVar12,uVar11 & 0xffffff00)",
   "FUN_00446afc((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[7])"],
  ["00446bd4", "(char *)_DAT_00636694", "0x177", "100",
   "FUN_00446bd4(iVar12,iVar7)",
   "FUN_00446bd4((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[8])"],
  ["00446cac", "_DAT_00636680", "500", "200",
   "FUN_00446cac(iVar12,iVar7)",
   "FUN_00446cac((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[9])"],
  ["00446d84", "(char *)_DAT_006366f4", "0x271", "500",
   "FUN_00446d84(iVar12,(int)(short)iVar12)",
   "FUN_00446d84((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[4])"],
  ["00446e6c", "(char *)_DAT_0063669c", "0x271", "500",
   "FUN_00446e6c(iVar12,(int)(short)iVar12)",
   "FUN_00446e6c((undefined4)(uintptr_t)(acStack_81 + 1),e2r_table_indices[10])"],
];
for (const [name, table, capacity, maxNames, oldCall, newCall] of fanNameInternSpecs) {
  source = source.replace(oldCall,newCall);
  source = source.replace(
    new RegExp(`(undefined8 __fastcall FUN_${name}\\(undefined4 param_1,undefined4 param_2\\)[\\s\\S]*?\\r?\\n  undefined2 uStack_1a;\\r?\\n\\s*)local_1c = 0;`),
    `$1return CONCAT44(param_2,(ushort)E2R_InternPackedName((char *)(uintptr_t)param_1,\n                                                       ${table},${capacity},${maxNames}));\n  \n  local_1c = 0;`
  );
}
const fanNameLookupSpecs = [
  ["004418fc", "_DAT_006366b4", "10000", "5000"],
  ["00441958", "(char *)_DAT_00636694", "0x177", "100"],
  ["00441a10", "_DAT_0063668c", "1000", "500"],
  ["00441ac8", "_DAT_006366b8", "0x1117", "2000"],
  ["00441ea4", "_DAT_006366bc", "5000", "0x9c4"],
  ["00441f00", "_DAT_00636698", "6000", "2000"],
];
for (const [name, table, capacity, maxNames] of fanNameLookupSpecs) {
  source = source.replace(
    new RegExp(`undefined8 __fastcall FUN_${name}\\(undefined4 param_1,undefined4 param_2\\)\\s*\\r?\\n\\s*\\{[\\s\\S]*?\\r?\\n\\}\\s*\\r?\\n\\s*\\r?\\n\\/\\*`),
    `undefined8 __fastcall FUN_${name}(undefined4 param_1,undefined4 param_2)\n\n{\n  return CONCAT44(param_2,(int)E2R_FindPackedNameIndex((char *)(uintptr_t)param_1,\n                                                       ${table},${capacity},${maxNames}));\n}\n\n\n\n/*`
  );
}
source = source.replace(
  /uint __fastcall FUN_0045fae0\(undefined4 param_1,uint \*param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fba5 \*\//,
  "uint __fastcall FUN_0045fae0(undefined4 param_1,uint *param_2)\n\n{\n  byte *left;\n  byte *right;\n  byte l;\n  byte r;\n  \n  left = (byte *)(uintptr_t)param_1;\n  right = (byte *)param_2;\n  if (left == right) {\n    return 0;\n  }\n  if ((uintptr_t)left < 0x10000u || (uintptr_t)right < 0x10000u ||\n      IsBadReadPtr(left,1) || IsBadReadPtr(right,1)) {\n    return 1;\n  }\n  do {\n    l = *left;\n    r = *right;\n    if (l != r) {\n      return -(uint)(l < r) | 1;\n    }\n    if (l == 0) {\n      return 0;\n    }\n    left = left + 1;\n    right = right + 1;\n  } while( true );\n}\n\n\n\n/* 0045fba5 */"
);
const fanTableIndexReplacements = [
  ["      *(short *)(&DAT_0067b83c + (short)extraout_ECX_09 * 2) = (short)uVar15;",
   "      ((short *)0x0067b83c)[e2r_table_indices[0]] = (short)uVar15;\n      e2r_table_indices[0]++;"],
  ["    *(short *)(&DAT_00677998 + iVar7 * 2) = (short)uVar15;",
   "    ((short *)0x00677998)[e2r_table_indices[1]] = (short)uVar15;\n    e2r_table_indices[1]++;"],
  ["    *(short *)(&DAT_00675670 + iVar7 * 2) = (short)uVar15;",
   "    ((short *)0x00675670)[e2r_table_indices[2]] = (short)uVar15;\n    e2r_table_indices[2]++;"],
  ["    *(short *)(&DAT_0067a490 + iVar7 * 2) = (short)uVar15;",
   "    ((short *)0x0067a490)[e2r_table_indices[3]] = (short)uVar15;\n    e2r_table_indices[3]++;"],
  ["      *(short *)(&DAT_0067a0a8 + iVar7 * 2) = (short)uVar15;",
   "      ((short *)0x0067a0a8)[e2r_table_indices[4]] = (short)uVar15;\n      e2r_table_indices[4]++;"],
  ["      *(short *)(&DAT_006769f8 + (short)extraout_ECX_39 * 2) = (short)uVar15;",
   "      ((short *)0x006769f8)[e2r_table_indices[5]] = (short)uVar15;\n      e2r_table_indices[5]++;"],
  ["      *(short *)(&DAT_0064ec78 + iVar7 * 2) = (short)uVar15;",
   "      ((short *)0x0064ec78)[e2r_table_indices[6]] = (short)uVar15;\n      e2r_table_indices[6]++;"],
  ["      *(short *)(&DAT_006625c0 + iVar7 * 2) = (short)uVar15;",
   "      ((short *)0x006625c0)[e2r_table_indices[7]] = (short)uVar15;\n      e2r_table_indices[7]++;"],
  ["      *(short *)(&DAT_0064c888 + (short)extraout_ECX_54 * 2) = (short)uVar15;",
   "      ((short *)0x0064c888)[e2r_table_indices[8]] = (short)uVar15;\n      e2r_table_indices[8]++;"],
  ["      *(short *)(&DAT_006536b0 + (short)extraout_ECX_59 * 2) = (short)uVar15;",
   "      ((short *)0x006536b0)[e2r_table_indices[9]] = (short)uVar15;\n      e2r_table_indices[9]++;"],
  ["    *(short *)(&DAT_00676610 + iVar7 * 2) = (short)uVar15;",
   "    ((short *)0x00676610)[e2r_table_indices[10]] = (short)uVar15;\n    e2r_table_indices[10]++;"],
];
for (const [before, after] of fanTableIndexReplacements) {
  source = source.replace(before,after);
}
source = source.replace(
  "    *(short *)(&DAT_006536b0 + sVar1 * 2) = sVar1;",
  "    ((short *)0x006536b0)[sVar1] = sVar1;"
);
source = source.replaceAll(
  "      in_EAX[2] = *(short *)(&DAT_006536b0 + (*(int *)(in_EAX + 1) >> 0x10) * 2);",
  "      in_EAX[2] = ((short *)0x006536b0)[*(int *)(in_EAX + 1) >> 0x10];"
);
source = source.replace(
  /undefined8 __fastcall FUN_0043c910\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0043c998 \*\//,
  "undefined8 __fastcall FUN_0043c910(undefined4 param_1,undefined4 param_2)\n\n{\n  static char prompt_text[0x34];\n  char *source;\n  uint i;\n  uint length;\n  short width;\n  undefined8 result;\n\n  source = (char *)(uintptr_t)param_1;\n  if ((uintptr_t)source < 0x10000u || (uintptr_t)source >= 0x70000000u ||\n      IsBadReadPtr(source,1)) {\n    source = \"Quit?\";\n  }\n  for (i = 0; i < 0x32; i = i + 1) {\n    if (IsBadReadPtr(source + i,1)) {\n      break;\n    }\n    prompt_text[i] = source[i];\n    if (source[i] == '\\0') {\n      break;\n    }\n  }\n  if (i == 0x32 || prompt_text[i] != '\\0') {\n    prompt_text[i] = '\\0';\n  }\n\n  length = (uint)strlen(prompt_text);\n  width = (length < 0x17) ? 0x96 : E2R_clamp_short((int)length * 6 + 0x14);\n  E2R_WORD_AT(DAT_0047a45e,2) = 0x14;\n  *(undefined2 *)0x0047a51c = width;\n  *(uintptr_t *)0x0047a520 = (uintptr_t)prompt_text;\n  E2R_InitRequesterYesNoPromptItems();\n  E2R_InitRequesterRecord(0x0047a518,-1,-1,width,0x32,(uintptr_t)prompt_text,0x00643c84);\n  _DAT_00643430 = (short *)0x00643c84;\n  _DAT_00643428 = (short *)0x0;\n  _DAT_0064342c = 0;\n  _DAT_006443d2 = _DAT_006443d2 & 0xffff;\n  result = FUN_0043b384(0x0047a518,0);\n  (void)result;\n  return CONCAT44(param_2,(int)_DAT_006443d2 >> 0x10);\n}\n\n\n\n/* 0043c998 */"
);
source = source.replace(
  /(undefined8 __fastcall FUN_004142b8\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar1;\r?\n\s*)uVar1 = CONCAT44\(param_2,in_EAX\);/,
  "$1(void)param_1;\n  (void)in_EAX;\n  (void)extraout_ECX;\n  if (DAT_00479e3c == 0) {\n    DAT_00479e3c = (int)LocalAlloc(0x40,0xc350);\n  }\n  return CONCAT44(param_2,DAT_00479e3c);\n  uVar1 = CONCAT44(param_2,in_EAX);"
);
source = source.replace(
  "    case 6:\n      FUN_00414e68();\n    }\n    FUN_0041cfc0();",
  "    case 6:\n      _DAT_00643660 = 1;\n      FUN_0043ce58(0x31,(int)((ulonglong)uVar4 >> 0x20));\n    }\n    FUN_0041cfc0();"
);
source = source.replace(
  /(void FUN_0043adc0\(void\)[\s\S]*?\r?\n  uint uVar2;\r?\n\s*)uVar2 = \*\(int \*\)\(in_EAX \+ 0xe\) >> 0x10;/,
  "$1in_EAX = (int)(uintptr_t)_DAT_00643430;\n  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x20)) {\n    in_EAX = (int)(uintptr_t)E2R_requester_probe_b9bc_last_item;\n    if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n        IsBadReadPtr((void *)(uintptr_t)in_EAX,0x20)) {\n      return;\n    }\n  }\n  uVar2 = *(int *)(in_EAX + 0xe) >> 0x10;"
);
source = source.replace(
  "  FUN_0041760c(2,0,0,0,_DAT_006401ec,_DAT_006401d4);",
  "  (void)_DAT_006401ec;\n  (void)_DAT_006401d4;"
);
source = source.replace(
  "  FUN_0041868c(0,1,(int)_DAT_006401ec,_DAT_006401d4);\n  FUN_0041868c(0,0,(int)_DAT_006401ec,_DAT_006401d4);",
  "  (void)DAT_0047a279;"
);
source = source.replace(
  /(longlong __fastcall FUN_004142e4\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  char local_24 \[8\];\r?\n  undefined1 local_1c;\r?\n\s*)if \(DAT_0047ab10 == 0\) \{/,
  "$1(void)param_1;\n  if (DAT_00479e3c == (char *)0x0) {\n    FUN_004142b8(0xc350,param_2);\n  }\n  return CONCAT44(param_2,1);\n  if (DAT_0047ab10 == 0) {"
);
source = source.replace(
  '  piVar3 = (int *)FUN_0045eb05(param_1,"shadow.dat");',
  '  piVar3 = (int *)FUN_0045eb05(0,"shadow.dat");'
);
source = source.replace(
  /void __fastcall FUN_0041db48\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0041db98 \*\//,
  "void __fastcall FUN_0041db48(undefined4 param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  undefined1 local_3c [52];\n  undefined4 uStack_8;\n  \n  uStack_8 = param_2;\n  E2R_FormatOneString((char *)local_3c,s__sSCENES_00471b58,(char *)0x00479e24);\n  iVar1 = FUN_00445378((undefined4)(uintptr_t)local_3c,0);\n  DAT_0047ab10 = (uint)(iVar1 == 0);\n  return;\n}\n\n\n\n/* 0041db98 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_0043cbf0\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0043ccc8 \*\//,
  "undefined8 __fastcall FUN_0043cbf0(undefined4 param_1,undefined4 param_2)\n\n{\n  int *in_EAX;\n  int iVar1;\n  int iVar3;\n  int iVar4;\n  undefined8 uVar5;\n  int iVar2;\n  undefined4 local_single [2];\n  \n  in_EAX = E2R_ResolveMenuStringList(param_1,param_2,local_single);\n  if (in_EAX == (int *)0x0) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  E2R_WORD_AT(DAT_0047a45e,2) = 0x2e;\n  iVar2 = 0;\n  do {\n    iVar1 = iVar2 + 0x33;\n    iVar3 = 0;\n    *(undefined1 *)(iVar2 + 0x64403a) = 0;\n    iVar2 = iVar1;\n  } while (iVar1 != 0x396);\n  iVar1 = 0;\n  iVar3 = 0;\n  iVar4 = 0x6430fa;\n  iVar2 = *in_EAX;\n  while (iVar2 != 0) {\n    if (!E2R_IsReadableCString((char *)(uintptr_t)*in_EAX)) {\n      break;\n    }\n    FUN_0045f22f(iVar1,(char *)*in_EAX);\n    *(undefined1 *)(iVar1 * 0x33 + 0x64406c) = 0;\n    if (iVar1 < 0x11) {\n      *(int *)((undefined1 *)0x006430ee + iVar3) = iVar4;\n    }\n    in_EAX = in_EAX + 1;\n    iVar4 = iVar4 + 0x1e;\n    iVar3 = iVar3 + 0x1e;\n    iVar1 = iVar1 + 1;\n    if (0x11 < iVar1) break;\n    if (IsBadReadPtr(in_EAX,4)) break;\n    iVar2 = *in_EAX;\n  }\n  _DAT_0047a636 = (short)iVar1 * 9 + 0x28;\n  if (iVar1 < 0x12) {\n    iVar3 = iVar1 * 0xf;\n    *(undefined4 *)((undefined1 *)0x006430ee + iVar1 * 0x1e) = 0x643de4;\n  }\n  else {\n    *(undefined4 *)0x006432ec = 0x643de4;\n  }\n  uVar5 = FUN_0043b384(iVar1,iVar3);\n  return CONCAT44(param_2,(int)uVar5);\n}\n\n\n\n/* 0043ccc8 */"
);
source = source.replace(
  /\/\* 00453920 \*\/[\s\S]*?\r?\n\s*\r?\n\/\* 004544a4 \*\//,
  "/* 00453920 */\n\nundefined8 __fastcall FUN_00453920(undefined4 param_1,char *param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return 0;\n}\n\n\n\n/* 004544a4 */"
);
source = source.replace(
  "  FUN_0045fd2c(uVar6,_DAT_006365f4);",
  "  E2R_FormatOneString((char *)0x00479e24,(char *)_DAT_006365f4,(char *)0x00479e24);"
);
source = source.replace(
  "    FUN_0045fd2c(iVar4,pcVar8);",
  "    snprintf(local_3c,24,\"%s\",pcVar8);"
);
source = source.replace(
  "      FUN_0045fd2c(uVar3,pcVar8);\n      uVar7 = extraout_ECX_02;",
  "      snprintf((char *)stack_ffffff98,0x200,\"%s\",pcVar8);\n      uVar7 = (undefined4)(uintptr_t)stack_ffffff98;"
);
source = source.replace(
  "      FUN_0045fd2c(uVar3,pcVar8);\n      uVar7 = extraout_ECX_01;",
  "      snprintf((char *)stack_ffffff98,0x200,\"%s\",pcVar8);\n      uVar7 = (undefined4)(uintptr_t)stack_ffffff98;"
);
source = source.replace(
  "    FUN_0045fd4b(uVar7,local_3c);",
  "    strncat((char *)stack_ffffff98,local_3c,0x1ff - strlen((char *)stack_ffffff98));"
);
source = source.replace(
  "    uVar13 = FUN_0045e594(extraout_ECX_03,extraout_EDX,&stack_ffffff98,0x200,in_stack_ffffff98);\n    if ((int)uVar13 != -1) {\n      FUN_0045e76f(extraout_ECX_04,(char *)local_1c);\n      if (local_1c[0] == 0x686d) {\n        FUN_0045e76f(extraout_ECX_05,_DAT_0063615c);\n        FUN_0045e76f(extraout_ECX_06,_DAT_0063615c);\n        FUN_0045e76f(extraout_ECX_07,_DAT_0063615c);\n        FUN_0045e76f(extraout_ECX_08,_DAT_00636670);\n        uVar7 = extraout_ECX_09;\n        uVar9 = extraout_EDX_00;\n      }\n      else {\n        FUN_0045e76f(extraout_ECX_05,(char *)&local_20);\n        FUN_0045e76f(extraout_ECX_10,(char *)&local_24);\n        if (_DAT_006401ec * _DAT_006401d4 * 2 <= local_20 + local_24) {\n          FUN_00414e68();\n        }\n        FUN_0045e76f(local_24,_DAT_00636668);\n        FUN_0045df96();\n        FUN_0045dff3();\n        uVar7 = extraout_ECX_11;\n        uVar9 = extraout_EDX_01;\n      }",
  "    uVar13 = FUN_0045e594(extraout_ECX_03,extraout_EDX,(LPCSTR)stack_ffffff98,0x200,\n                           in_stack_ffffff98);\n    if ((int)uVar13 != -1) {\n      iVar10 = (int)uVar13;\n      E2R_ReadOpenFileBytes(iVar10,(char *)local_1c,2);\n      if (local_1c[0] == 0x686d) {\n        iVar2 = _DAT_006401ec * _DAT_006401d4;\n        E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,0x1e);\n        E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,0x300);\n        E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,iVar2);\n        E2R_ReadOpenFileBytes(iVar10,_DAT_00636670,iVar2 * 2);\n        uVar7 = (undefined4)iVar10;\n        uVar9 = extraout_EDX_00;\n      }\n      else {\n        E2R_ReadOpenFileBytes(iVar10,(char *)&local_20,4);\n        E2R_ReadOpenFileBytes(iVar10,(char *)&local_24,4);\n        if (_DAT_006401ec * _DAT_006401d4 * 2 <= local_20 + local_24) {\n          FUN_00414e68();\n        }\n        E2R_ReadOpenFileBytes(iVar10,_DAT_00636668,local_20 + local_24);\n        FUN_0045df96((byte *)_DAT_00636668,(byte *)_DAT_0063615c);\n        FUN_0045dff3((byte *)(_DAT_00636668 + local_20),(short *)_DAT_00636670);\n        uVar7 = (undefined4)iVar10;\n        uVar9 = extraout_EDX_01;\n      }"
);
source = source.replace(
  "void FUN_0045df96(void)\n\n{\n  byte bVar1;",
  "void FUN_0045df96(byte *param_1,byte *param_2)\n\n{\n  byte bVar1;"
);
source = source.replace(
  /(void FUN_0045df96\(byte \*param_1,byte \*param_2\)[\s\S]*?\r?\n  byte \*unaff_EDI;\r?\n  byte \*pbVar5;\r?\n\s*)bVar2 = 0;/,
  "$1unaff_ESI = param_1;\n  unaff_EDI = param_2;\n  bVar2 = 0;"
);
source = source.replace(
  "void FUN_0045dff3(void)\n\n{\n  byte bVar1;",
  "void FUN_0045dff3(byte *param_1,short *param_2)\n\n{\n  byte bVar1;"
);
source = source.replace(
  /(void FUN_0045dff3\(byte \*param_1,short \*param_2\)[\s\S]*?\r?\n  short \*unaff_EDI;\r?\n  short \*psVar5;\r?\n\s*)sVar2 = 0;/,
  "$1unaff_ESI = param_1;\n  unaff_EDI = param_2;\n  sVar2 = 0;"
);
source = source.replace("        uVar7 = FUN_004619f2(0,uVar2);", "        uVar7 = FUN_004619f2(in_EAX,uVar2);");
source = source.replace(
  /undefined8 __fastcall FUN_0046196d\(undefined4 param_1,uint param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004619f2 \*\//,
  "undefined8 __fastcall FUN_0046196d(undefined4 param_1,uint param_2)\n\n{\n  undefined4 uVar1;\n  uint *puVar2;\n  uint *sentinel;\n  uint *free_block;\n  uint uVar3;\n  int iVar4;\n  uint local_request;\n  longlong lVar5;\n  undefined8 uVar6;\n  \n  local_request = (uint)(uintptr_t)param_1;\n  if ((DAT_0047d7f4 != 0) && (DAT_0047d728 != -2)) {\n    lVar5 = FUN_00461a03((undefined4)(uintptr_t)&local_request,param_2);\n    uVar1 = 0;\n    if ((int)lVar5 == 0) goto LAB_004619e9;\n    puVar2 = LocalAlloc(0,local_request);\n    uVar1 = 0;\n    if (puVar2 == (uint *)0x0) goto LAB_004619e9;\n    uVar3 = local_request - 4;\n    if ((uVar3 <= local_request) && (0x37 < uVar3)) {\n      *puVar2 = uVar3;\n      uVar6 = FUN_004618f9((undefined4)(uintptr_t)puVar2,param_2);\n      (void)uVar6;\n      sentinel = (uint *)((undefined1 *)puVar2 + 0x20);\n      free_block = (uint *)((undefined1 *)puVar2 + 0x2c);\n      iVar4 = (int)(uintptr_t)puVar2;\n      uVar3 = local_request - 0x30;\n      puVar2[3] = (uint)(uintptr_t)free_block;\n      puVar2[4] = 0;\n      puVar2[5] = uVar3;\n      puVar2[6] = 0;\n      puVar2[7] = 1;\n      sentinel[0] = 0;\n      sentinel[1] = (uint)(uintptr_t)free_block;\n      sentinel[2] = (uint)(uintptr_t)free_block;\n      free_block[0] = uVar3;\n      free_block[1] = (uint)(uintptr_t)sentinel;\n      free_block[2] = (uint)(uintptr_t)sentinel;\n      *(undefined4 *)(iVar4 + local_request + -4) = 0xffffffff;\n      DAT_0047d268 = uVar3;\n      FUN_0045f9b5();\n      uVar1 = 1;\n      goto LAB_004619e9;\n    }\n  }\n  uVar1 = 0;\nLAB_004619e9:\n  return CONCAT44(param_2,uVar1);\n}\n\n\n\n/* 004619f2 */"
);
source = source.replace(/(undefined8 __fastcall FUN_004619f2\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)FUN_004640d9\(\);\r?\n\s*uVar1 = FUN_0046196d\(extraout_ECX,extraout_EDX\);/, "$1FUN_004640d9();\n  uVar1 = FUN_0046196d(param_1,param_2);");
source = source.replace(/(longlong __fastcall FUN_00461a03\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  uint uVar2;\r?\n\s*)if \(in_EAX == 0\)/, "$1in_EAX = (uint *)(uintptr_t)param_1;\n  if (in_EAX == 0)");
source = source.replace(/(longlong __fastcall FUN_0045f1c0\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  undefined2 local_10;\r?\n\s*)uVar1 = FUN_00461a50\(param_1,param_2\);/, "$1in_EAX = (undefined4 *)(uintptr_t)param_1;\n  if (E2R_IsBadWritePtr(in_EAX,0x24)) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  uVar1 = FUN_00461a50(param_1,param_2);");
source = source.replace("  uVar1 = FUN_00461ab5(extraout_ECX,(int)((ulonglong)uVar1 >> 0x20));", "  uVar1 = FUN_00461ab5((undefined4)(uintptr_t)in_EAX,(int)((ulonglong)uVar1 >> 0x20));");
source = source.replace(/(undefined8 __fastcall FUN_00461a50\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  uStack_8 = param_1;\r?\n\s*)GetLocalTime\(&local_1c\);/, "$1in_EAX = (uint *)(uintptr_t)param_1;\n  if (E2R_IsBadWritePtr(in_EAX,0x24)) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  GetLocalTime(&local_1c);");
source = source.replace(/(undefined8 __fastcall FUN_00461ab5\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  longlong lVar6;\r?\n\s*)iVar1 = \(int\)\(CONCAT44\(in_EAX\[4\] >> 0x1f,in_EAX\[4\]\) % 0xc\);/, "$1in_EAX = (int *)(uintptr_t)param_1;\n  if (E2R_IsBadWritePtr(in_EAX,0x24)) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  iVar1 = (int)(CONCAT44(in_EAX[4] >> 0x1f,in_EAX[4]) % 0xc);");
source = source.replace("  *(uint *)(extraout_ECX + 0x14) = uVar2;", "  param_1[5] = uVar2;");
source = source.replace("  *(uint *)(extraout_ECX + 0x1c) = uVar3;", "  param_1[7] = uVar3;");
source = source.replace("  lVar7 = FUN_0046418b(extraout_ECX,uVar2);", "  lVar7 = FUN_0046418b(param_1,uVar2);");
source = source.replace("  *(uint *)(extraout_ECX_00 + 0x10) = uVar4;", "  param_1[4] = uVar4;");
source = source.replace("  *(uint *)(extraout_ECX_00 + 0xc) = (uVar3 - (int)*(short *)(puVar5 + uVar4 * 2)) + 1;", "  param_1[3] = (uVar3 - (int)*(short *)(puVar5 + uVar4 * 2)) + 1;");
source = source.replace("  *(uint *)(extraout_ECX_00 + 0x18) = (uVar6 + 1) % 7;", "  param_1[6] = (uVar6 + 1) % 7;");
source = source.replace("  return extraout_ECX_00;\n}\n\n\n\n/* 0046471c */", "  return (int)(uintptr_t)param_1;\n}\n\n\n\n/* 0046471c */");
source = source.replace(
  "  FUN_0043ac60();\n  uVar5 = extraout_ECX_01;\n  if (DAT_00479dfc != 0) {\n    FUN_00414998(extraout_ECX_01);\n    lVar12 = FUN_0045f1c0(extraout_ECX_02,extraout_EDX_00);\n    uVar3 = (uint)((ulonglong)lVar12 >> 0x20);\n    uVar5 = extraout_ECX_03;\n    do {\n      lVar12 = FUN_0045f1c0(uVar5,uVar3);\n      uVar3 = (uint)((ulonglong)lVar12 >> 0x20);\n      uVar5 = extraout_ECX_04;\n    } while ((uint)(local_58 - local_34) < 5);\n  }\n  FUN_00414998(uVar5);\n  lVar12 = FUN_0045f1c0(extraout_ECX_05,extraout_EDX_01);\n  uVar3 = (uint)((ulonglong)lVar12 >> 0x20);\n  uVar5 = extraout_ECX_06;\n  do {\n    lVar12 = FUN_0045f1c0(uVar5,uVar3);\n    uVar3 = (uint)((ulonglong)lVar12 >> 0x20);\n    uVar5 = extraout_ECX_07;\n  } while ((uint)(local_4c - local_40) < 5);\n  FUN_00414998(extraout_ECX_07);\n  lVar12 = FUN_0045f1c0(extraout_ECX_08,extraout_EDX_02);\n  uVar3 = (uint)((ulonglong)lVar12 >> 0x20);\n  uVar5 = extraout_ECX_09;\n  do {\n    lVar12 = FUN_0045f1c0(uVar5,uVar3);\n    uVar3 = (uint)((ulonglong)lVar12 >> 0x20);\n    uVar5 = extraout_ECX_10;\n  } while ((uint)(local_28 - local_64) < 5);\n  uVar11 = FUN_00414a94(extraout_ECX_10,uVar3);\n  uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n  uVar5 = extraout_ECX_11;\n  if (DAT_00479e1c == 0) {\n    uVar11 = FUN_00414b24(extraout_ECX_11,uVar6);\n    uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n    uVar5 = extraout_ECX_12;\n  }",
  "  FUN_0043ac60();\n  uVar5 = 0;\n  if (DAT_00479dfc != 0) {\n    FUN_00414998(s_gbnklogo_raw_00470500);\n    Sleep(5);\n  }\n  FUN_00414998(s_psyglogo_raw_00470510);\n  Sleep(5);\n  FUN_00414998(s_aasglogo_raw_00470520);\n  Sleep(5);\n  uVar3 = 0;\n  uVar11 = FUN_00414a94(uVar5,uVar3);\n  uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n  uVar5 = 0;\n  if (DAT_00479e1c == 0) {\n    uVar11 = FUN_00414b24(uVar5,uVar6);\n    uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n    uVar5 = 0;\n  }"
);
source = source.replace(
  /(undefined4|void) FUN_00414e68\(void\)([\s\S]*?\r?\n  char \*)in_EAX;/,
  "$1 FUN_00414e68(void)$2in_EAX = s_Can_t_load_title_picture_00471320;"
);
source = source.replace(
  /(void __fastcall FUN_00414998\(undefined4 param_1\)[\s\S]*?\r?\n  undefined8 uVar3;\r?\n\s*)if \(DAT_0047a43c == 0\) \{/,
  "$1in_EAX = param_1;\n  if (DAT_0047a43c == 0) {"
);
source = source.replace(
  /(void __fastcall FUN_00414998\(undefined4 param_1\)[\s\S]*?\r?\n  int iVar2;\r?\n)/,
  "$1  int iVar4;\n"
);
source = source.replace(
  "  if (DAT_0047a43c == 0) {\n    FUN_0043ac60();\n    param_1 = extraout_ECX;\n    in_EAX = extraout_EDX;\n  }\n  if (DAT_0047a43c != 0) {\n    uVar3 = FUN_0045e594(param_1,in_EAX,(LPCSTR)in_EAX,0x200,unaff_EBP);",
  "  if (DAT_0047a43c == 0) {\n    FUN_0043ac60();\n    param_1 = in_EAX;\n  }\n  if (DAT_0047a43c != 0) {\n    uVar3 = FUN_0045e594(param_1,in_EAX,(LPCSTR)in_EAX,0x200,unaff_EBP);"
);
source = source.replace(
  "    if ((int)uVar3 != -1) {\n      FUN_0045e76f((int)uVar3,_DAT_0063615c);\n      FUN_0045e76f(extraout_ECX_00,(char *)0x621030);",
  "    if ((int)uVar3 != -1) {\n      iVar4 = (int)uVar3;\n      FUN_0045e76f(iVar4,_DAT_0063615c);\n      FUN_0045e76f(iVar4,(char *)0x621030);"
);
source = source.replace(
  "      FUN_0045e76f(iVar4,_DAT_0063615c);\n      FUN_0045e76f(iVar4,(char *)0x621030);",
  "      E2R_ReadOpenFileBytes(iVar4,_DAT_0063615c,0x20);\n      E2R_ReadOpenFileBytes(iVar4,(char *)0x621030,0x300);"
);
source = source.replace(
  "      FUN_0045e76f(extraout_ECX_01,_DAT_0063615c);\n      uVar3 = FUN_0045e8e6(extraout_ECX_02,extraout_EDX_00);",
  "      E2R_ReadOpenFileBytes(iVar4,_DAT_0063615c,_DAT_006401ec * _DAT_006401d4);\n      uVar3 = FUN_0045e8e6(iVar4,extraout_EDX_00);"
);
source = source.replace(
  "      uVar3 = FUN_0045e8e6(extraout_ECX_02,extraout_EDX_00);",
  "      E2R_ReadOpenFileBytes(iVar4,_DAT_0063615c,_DAT_006401ec * _DAT_006401d4);\n      uVar3 = FUN_0045e8e6(iVar4,extraout_EDX_00);"
);
source = source.replace(
  "  uVar5 = E2R_READ4(s_pallette_raw_004712b4,0);\n  if (DAT_00479d74 != '\\0') {\n    uVar5 = E2R_READ4(s_p__pallette_raw_004712a4,0);\n  }\n  uVar4 = FUN_0045e594(param_1,param_2,&stack_ffffffd4,0x200,uVar5);",
  "  pcVar3 = s_pallette_raw_004712b4;\n  uVar5 = E2R_READ4(s_pallette_raw_004712b4,0);\n  if (DAT_00479d74 != '\\0') {\n    pcVar3 = s_p__pallette_raw_004712a4;\n    uVar5 = E2R_READ4(s_p__pallette_raw_004712a4,0);\n  }\n  uVar4 = FUN_0045e594(param_1,param_2,pcVar3,0x200,uVar5);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00414a94\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  int iVar2;\r?\n)/,
  "$1  int iVar3;\n  LPCSTR pcVar3;\n"
);
source = source.replace(
  "  iVar1 = (int)uVar4;\n  if (iVar1 != -1) {\n    FUN_0045e76f(iVar1,&DAT_00621330);\n    FUN_0045e76f(extraout_ECX,&DAT_00621330);",
  "  iVar1 = (int)uVar4;\n  if (iVar1 != -1) {\n    iVar3 = iVar1;\n    FUN_0045e76f(iVar1,&DAT_00621330);\n    FUN_0045e76f(iVar3,&DAT_00621330);"
);
source = source.replace(
  "    FUN_0045e76f(iVar1,&DAT_00621330);\n    FUN_0045e76f(iVar3,&DAT_00621330);",
  "    E2R_ReadOpenFileBytes(iVar1,(char *)0x00621330,0x20);\n    E2R_ReadOpenFileBytes(iVar3,(char *)0x00621330,0x300);"
);
source = source.replace(
  "      uVar3 = CONCAT31((int3)((uint)uVar3 >> 8),(byte)(&DAT_00621330)[iVar1] >> 2);\n      (&DAT_00621330)[iVar1] = (byte)(&DAT_00621330)[iVar1] >> 2;",
  "      uVar3 = CONCAT31((int3)((uint)uVar3 >> 8),*(byte *)(iVar1 + 0x00621330) >> 2);\n      *(byte *)(iVar1 + 0x00621330) = *(byte *)(iVar1 + 0x00621330) >> 2;"
);
source = source.replace(
  "    uVar4 = FUN_0045e8e6(extraout_ECX_00,uVar3);\n    iVar1 = (int)uVar4;",
  "    uVar4 = FUN_0045e8e6(iVar3,uVar3);\n    iVar1 = (int)uVar4;"
);
source = source.replace(
  "  uVar9 = E2R_READ4(s_tscreen_raw_0047033c,0);\n  if (DAT_00479d74 != '\\0') {\n    uVar9 = E2R_READ4(s_p__tscreen_raw_004712c4,0);\n  }\n  if (DAT_0047a43c != 0) {\n    uVar8 = FUN_0045e594(param_1,uVar4,&stack_ffffffb8,0x200,uVar9);",
  "  pcVar5 = s_tscreen_raw_0047033c;\n  uVar9 = E2R_READ4(s_tscreen_raw_0047033c,0);\n  if (DAT_00479d74 != '\\0') {\n    pcVar5 = s_p__tscreen_raw_004712c4;\n    uVar9 = E2R_READ4(s_p__tscreen_raw_004712c4,0);\n  }\n  if (DAT_0047a43c != 0) {\n    uVar8 = FUN_0045e594(param_1,uVar4,pcVar5,0x200,uVar9);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00414b24\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined4 uVar4;\r?\n)/,
  "$1  LPCSTR pcVar5;\n"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00414b24\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined4 extraout_EDX_03;\r?\n)/,
  "$1  int iVar10;\n"
);
source = source.replace(
  "    if ((int)uVar8 != -1) {\n      FUN_0045e76f((int)uVar8,_DAT_0063615c);\n      FUN_0045e76f(extraout_ECX_00,(char *)0x61ca30);",
  "    if ((int)uVar8 != -1) {\n      iVar10 = (int)uVar8;\n      FUN_0045e76f(iVar10,_DAT_0063615c);\n      FUN_0045e76f(iVar10,(char *)0x61ca30);"
);
source = source.replace(
  "      FUN_0045e76f(iVar10,_DAT_0063615c);\n      FUN_0045e76f(iVar10,(char *)0x61ca30);",
  "      E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,0x20);\n      E2R_ReadOpenFileBytes(iVar10,(char *)0x61ca30,0x300);"
);
source = source.replace(
  "      FUN_0045e76f(extraout_ECX_01,_DAT_0063615c);",
  "      E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,_DAT_006401ec * _DAT_006401d4);"
);
source = source.replace(
  "      uVar8 = FUN_0045e8e6(extraout_ECX_02,extraout_EDX_00);",
  "      uVar8 = FUN_0045e8e6(iVar10,extraout_EDX_00);"
);
source = source.replace(
  "  if ((int)uVar8 != -1) {\n    FUN_0045e76f((int)uVar8,_DAT_0063615c);\n    FUN_0045e76f(extraout_ECX_07,&DAT_00621330);",
  "  if ((int)uVar8 != -1) {\n    iVar10 = (int)uVar8;\n    FUN_0045e76f(iVar10,_DAT_0063615c);\n    FUN_0045e76f(iVar10,&DAT_00621330);"
);
source = source.replace(
  "    FUN_0045e76f(iVar10,_DAT_0063615c);\n    FUN_0045e76f(iVar10,&DAT_00621330);",
  "    E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,0x20);\n    E2R_ReadOpenFileBytes(iVar10,(char *)0x00621330,0x300);"
);
source = source.replace(
  "      (&DAT_00621330)[iVar5] = (byte)(&DAT_00621330)[iVar5] >> 2;",
  "      *(byte *)(iVar5 + 0x00621330) = *(byte *)(iVar5 + 0x00621330) >> 2;"
);
source = source.replace(
  "    FUN_0045e76f(extraout_ECX_08,_DAT_0063615c);",
  "    E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,_DAT_006401ec * _DAT_006401d4);"
);
source = source.replace(
  "    uVar8 = FUN_0045e8e6(extraout_ECX_09,extraout_EDX_03);",
  "    uVar8 = FUN_0045e8e6(iVar10,extraout_EDX_03);"
);
source = source.replace(
  "  char acStack_28 [4];\n  char acStack_24 [4];\n  char cStack_20;",
  "  char acStack_28 [9];"
);
source = source.replace("  char acStack_68 [12];", "  char acStack_68 [32];");
source = source.replace(
  "  acStack_28[0] = s_e_config_0047000c[0];\n  acStack_28[1] = s_e_config_0047000c[1];\n  acStack_28[2] = s_e_config_0047000c[2];\n  acStack_28[3] = s_e_config_0047000c[3];\n  acStack_24[0] = s_e_config_0047000c[4];\n  acStack_24[1] = s_e_config_0047000c[5];\n  acStack_24[2] = s_e_config_0047000c[6];\n  acStack_24[3] = s_e_config_0047000c[7];\n  cStack_20 = s_e_config_0047000c[8];",
  "  acStack_28[0] = s_e_config_0047000c[0];\n  acStack_28[1] = s_e_config_0047000c[1];\n  acStack_28[2] = s_e_config_0047000c[2];\n  acStack_28[3] = s_e_config_0047000c[3];\n  acStack_28[4] = s_e_config_0047000c[4];\n  acStack_28[5] = s_e_config_0047000c[5];\n  acStack_28[6] = s_e_config_0047000c[6];\n  acStack_28[7] = s_e_config_0047000c[7];\n  acStack_28[8] = s_e_config_0047000c[8];"
);
source = source.replace(
  "    uVar4 = FUN_0045e76f((int)uVar11,acStack_68);",
  "    uVar4 = E2R_ReadOpenFileBytes((int)uVar11,acStack_68,0x20);"
);
source = source.replace(
  "    if (uVar4 != 0x20) {\n      FUN_00414e68();\n      uVar6 = extraout_ECX_04;\n      uVar7 = extraout_EDX_01;\n    }\n    FUN_0045e8e6(uVar6,uVar7);",
  "    if (uVar4 != 0x20) {\n      FUN_00414e68();\n      uVar6 = extraout_ECX_04;\n      uVar7 = extraout_EDX_01;\n    }\n    E2R_UnpackConfigHeader(acStack_68,&cStack_5c,&bStack_5b,&bStack_5a,&uStack_59,&bStack_58,\n                           &uStack_57,&uStack_56,&uStack_55,&uStack_54,&uStack_53,&bStack_52);\n    FUN_0045e8e6(uVar6,uVar7);"
);
source = source.replace(
  "  iVar3 = FUN_0045e90e(uVar6,(byte *)s_Ecstatica001_0047006c);",
  "  iVar3 = strncmp(acStack_68,s_Ecstatica001_0047006c,0xc);"
);
source = source.replace(
  "      uStack_57 = (undefined1)DAT_00479dd4;\n      uStack_56 = (undefined1)((uint)DAT_00479dd4 >> 8);\n      uStack_55 = DAT_00479dd8;\n      uStack_54 = DAT_00479ddc;\n      uVar11 = FUN_0045e594(extraout_ECX_28,extraout_EDX_09,acStack_28,0x261,0x180);",
  "      uStack_57 = (undefined1)DAT_00479dd4;\n      uStack_56 = (undefined1)((uint)DAT_00479dd4 >> 8);\n      uStack_55 = DAT_00479dd8;\n      uStack_54 = DAT_00479ddc;\n      E2R_PackConfigHeader(acStack_68,cStack_5c,bStack_5b,bStack_5a,uStack_59,bStack_58,\n                           uStack_57,uStack_56,uStack_55,uStack_54,uStack_53,bStack_52);\n      uVar11 = FUN_0045e594(extraout_ECX_28,extraout_EDX_09,acStack_28,0x261,0x180);"
);
source = source.replace(
  "      uStack_54 = DAT_00479ddc;\n      uStack_53 = (undefined1)DAT_00479e00;\n      bStack_52 = DAT_00479df0;\n      cStack_5c = '#';\n      uVar11 = FUN_0045e594(extraout_ECX_13,extraout_EDX_06,acStack_28,0x261,0x180);",
  "      uStack_54 = DAT_00479ddc;\n      uStack_53 = (undefined1)DAT_00479e00;\n      bStack_52 = DAT_00479df0;\n      cStack_5c = '#';\n      E2R_PackConfigHeader(acStack_68,cStack_5c,bStack_5b,bStack_5a,uStack_59,bStack_58,\n                           uStack_57,uStack_56,uStack_55,uStack_54,uStack_53,bStack_52);\n      uVar11 = FUN_0045e594(extraout_ECX_13,extraout_EDX_06,acStack_28,0x261,0x180);"
);
source = source.replace("uint * FUN_00461746(void)", "uint * __fastcall FUN_00461746(int heap,uint size)");
source = source.replace(/(uint \* __fastcall FUN_00461746\(int heap,uint size\)[\s\S]*?\r?\n  uint \*puVar5;\r?\n\s*)if \(\(\(in_EAX != 0\)/, "$1unaff_EBX = heap;\n  in_EAX = size;\n  if (unaff_EBX == 0 || (uintptr_t)unaff_EBX < 0x10000 ||\n      IsBadReadPtr((void *)(uintptr_t)unaff_EBX,0x2c)) return (uint *)0x0;\n  if (((in_EAX != 0)");
source = source.replace(/(uint \* __fastcall FUN_00461746\(int heap,uint size\)[\s\S]*?\r?\n\s*)do \{\r?\n\s*uVar1 = \*puVar3;/, "$1if ((uintptr_t)puVar3 < 0x10000 || IsBadReadPtr(puVar3,0xc)) return (uint *)0x0;\n    do {\n      if ((uintptr_t)puVar3 < 0x10000 || IsBadReadPtr(puVar3,0xc)) return (uint *)0x0;\n      uVar1 = *puVar3;");
source = source.replace("puVar4 = FUN_00461746();", "puVar4 = FUN_00461746(iVar5,uVar3);");
source = source.replace(
  /(\s*if \(puVar4 != \(uint \*\)0x0\) goto LAB_0045f1a1;\r?\n)\s*if \(DAT_0047d268 < \*\(uint \*\)\(extraout_ECX \+ 0x14\)\) \{\r?\n\s*DAT_0047d268 = \*\(uint \*\)\(extraout_ECX \+ 0x14\);\r?\n\s*\}\r?\n\s*uVar2 = 0;\r?\n\s*iVar5 = \*\(int \*\)\(extraout_ECX \+ 8\);/,
  "$1        if ((uintptr_t)iVar5 < 0x10000 || IsBadReadPtr((void *)(uintptr_t)iVar5,0x18)) break;\n        if (DAT_0047d268 < *(uint *)(iVar5 + 0x14)) {\n          DAT_0047d268 = *(uint *)(iVar5 + 0x14);\n        }\n        uVar2 = 0;\n        iVar5 = *(int *)(iVar5 + 8);"
);
source = source.replace("      if (iVar5 == 0) goto LAB_0045f1a1;", "      if (iVar5 == 0) {\n        puVar4 = (uint *)0x0;\n        goto LAB_0045f1a1;\n      }");
source = source.replace(/(\s*)uVar2 = extraout_EDX_01;\r?\n\s*goto LAB_0045f1b1;/, "$1uVar2 = (undefined4)(uintptr_t)puVar4;\n  goto LAB_0045f1b1;");
source = source.replace("    uVar3 = FUN_0045fa43(extraout_ECX_00,extraout_EDX);", "    uVar3 = FUN_0045fa43((undefined4)(uintptr_t)local_10c,extraout_EDX);");
source = source.replace(/\s*GetCommandLineA\(\);\r?\n\s*uVar3 = FUN_0045fa43\(extraout_ECX_01,extraout_EDX_00\);/, "\n    uVar3 = FUN_0045fa43((undefined4)(uintptr_t)GetCommandLineA(),extraout_EDX_00);");
source = source.replace("      uVar3 = FUN_0045fa43(extraout_ECX_02,extraout_EDX_01);", "      uVar3 = FUN_0045fa43((undefined4)(uintptr_t)local_10c,extraout_EDX_01);");
source = source.replace(/\s*GetCommandLineA\(\);\r?\n\s*\*\(undefined4 \*\)\(puVar6 \+ -4\) = 0x46327d;\r?\n\s*uVar8 = FUN_0045fa43\(extraout_ECX_01,extraout_EDX\);/, "\n  *(undefined4 *)(puVar6 + -4) = 0x46327d;\n  uVar8 = FUN_0045fa43((undefined4)(uintptr_t)GetCommandLineA(),extraout_EDX);");
source = source.replace(/\*\(undefined4 \*\)\(iVar2 \+ 0xac4e00\)/g, "E2R_timer_slots[iVar2 / 4]");
source = source.replace(/\*\(int \*\)\(iVar2 \+ 0xac4e00\)/g, "((int *)E2R_timer_slots)[iVar2 / 4]");
source = source.replace(/\*\(undefined4 \*\)\(iVar5 \+ 0xac4e00\)/g, "E2R_timer_slots[iVar5 / 4]");
source = source.replace(/\*\(undefined4 \*\)\(\(\*\(int \*\)\(in_EAX \+ 0x28\) \/ 0x96\) \* 4 \+ 0xac4e00\)/g, "E2R_timer_slots[*(int *)(in_EAX + 0x28) / 0x96]");
source = source.replace(/\biVar9 = 0xac4fdc;/g, "iVar9 = (int)(uintptr_t)E2R_midi_device_labels;");
source = source.replace(/\*\(undefined1 \*\)\(iVar2 \+ 0xac4fdc\)/g, "E2R_midi_device_labels[iVar2 / 0x33][0]");
source = source.replace(/\*\(undefined1 \*\)\(iVar2 \+ 0xac500e\)/g, "E2R_midi_device_labels[iVar2 / 0x33][0x32]");
source = source.replace(/E2R_READ2\(DAT_0047a45e,2\)/g, "E2R_WORD_AT(DAT_0047a45e,2)");
source = source.replace(
  /(undefined8 __fastcall FUN_0043ce58\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  short sStack_1c;\r?\n\s*)E2R_WORD_AT\(DAT_0047a45e,2\) = \(ushort\)in_EAX;/,
  "$1in_EAX = (uint)(uintptr_t)param_1;\n  E2R_requester_probe_ce58_count++;\n  E2R_requester_probe_last_id = in_EAX;\n  E2R_requester_probe_last_mode = (uintptr_t)param_2;\n  E2R_WORD_AT(DAT_0047a45e,2) = (ushort)in_EAX;"
);
source = source.replace(/E2R_READ1\(DAT_0047a279,3\) = 0;/g, "DAT_0047a279 = DAT_0047a279 & 0x00ffffff;");
source = source.replace(/E2R_READ1\(DAT_0047a279,3\) = '\\x01' - E2R_READ1\(DAT_0047a279,3\);/g, "DAT_0047a279 = (DAT_0047a279 & 0x00ffffff) | ((1 - (DAT_0047a279 >> 0x18)) << 0x18);");
source = source.replace(/E2R_READ1\(DAT_0047a279,3\)/g, "(DAT_0047a279 >> 0x18)");
source = source.replace(/\(undefined2 \*\)&DAT_009373dc/g, "(undefined2 *)0x009373dc");
source = source.replace(/&DAT_00630b60/g, "(undefined1 *)0x00630b60");
source = source.replace(/&DAT_0062ba20/g, "(undefined1 *)0x0062ba20");
source = source.replace(/&DAT_00635980/g, "(undefined1 *)0x00635980");
source = source.replace(/&DAT_0064a178/g, "(undefined1 *)0x0064a178");
source = source.replace(/&DAT_00637286/g, "(undefined1 *)0x00637286");
source = source.replace(/&DAT_006372aa/g, "(undefined1 *)0x006372aa");
source = source.replace(/&DAT_006372bc/g, "(undefined1 *)0x006372bc");
source = source.replace(/&DAT_006372c2/g, "(undefined1 *)0x006372c2");
source = source.replace(/&DAT_006372da/g, "(undefined1 *)0x006372da");
source = source.replace(/&DAT_006372e6/g, "(undefined1 *)0x006372e6");
source = source.replace(/puVar6 = \(undefined2 \*\)&DAT_00684d68;/g, "puVar6 = (undefined2 *)0x00684d68;");
source = source.replace(/puVar7 = &DAT_00684be8;/g, "puVar7 = (undefined1 *)0x00684be8;");
source = source.replace(/&DAT_00684d68/g, "(undefined1 *)0x00684d68");
source = source.replace(/&DAT_00684be8/g, "(undefined1 *)0x00684be8");
source = source.replace(/&DAT_00621330/g, "(char *)0x00621330");
source = source.replace(
  /void __fastcall FUN_0046388f\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004638cd \*\//,
  "void __fastcall FUN_0046388f(undefined4 param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return;\n}\n\n\n\n/* 004638cd */"
);
source = source.replace(
  /undefined8 __fastcall FUN_0046349a\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004634c7 \*\//,
  "undefined8 __fastcall FUN_0046349a(undefined4 param_1,undefined4 param_2)\n\n{\n  return (ulonglong)param_2 << 32;\n}\n\n\n\n/* 004634c7 */"
);
source = source.replace(
  /void __fastcall FUN_004638cd\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004638ee \*\//,
  "void __fastcall FUN_004638cd(undefined4 param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return;\n}\n\n\n\n/* 004638ee */"
);
source = source.replace(
  /void FUN_00463b97\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00463d1c \*\//,
  "void FUN_00463b97(void)\n\n{\n  _DAT_00ac5230 = CreateMutexA((LPSECURITY_ATTRIBUTES)0x0,0,(LPCSTR)0x0);\n  _DAT_00ac5234 = 1;\n  TlsSetValue(DAT_0047d398,_DAT_00ac5204);\n  return;\n}\n\n\n\n/* 00463d1c */"
);
source = source.replace(
  /void FUN_00463d1c\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00463d67 \*\//,
  "void FUN_00463d1c(void)\n\n{\n  return;\n}\n\n\n\n/* 00463d67 */"
);
source = source.replace(
  /void __fastcall FUN_00463d67\(undefined4 param_1,byte param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00463e96 \*\//,
  "void __fastcall FUN_00463d67(undefined4 param_1,byte param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return;\n}\n\n\n\n/* 00463e96 */"
);
source = source.replace(/\(\*\(undefined4 \*\)\(uintptr_t\)([A-Za-z_][A-Za-z0-9_]*)\)\s*\(/g, "(*(code *)(uintptr_t)$1)(");
source = source.replace(/&\s*(stack_[0-9a-fA-F]+)\s*\)\s*\[/g, "$1)[");
source = source.replace(/\(&\s*(stack_[0-9a-fA-F]+)\)\s*\[/g, "$1[");
source = source.replace(/([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\.E2R_READ([1248])\(([A-Za-z_][A-Za-z0-9_]*),([0-9]+)\)/g, "E2R_READ$2(&$1.$3,$4)");
source = source.replace(/\blpfnWndProc\s*=\s*(FUN_[0-9a-fA-F]+)\s*;/g, "lpfnWndProc = (WNDPROC)$1;");
source = source.replace(/DialogBoxParamA\(([^;]*?),(FUN_[0-9a-fA-F]+),/g, "DialogBoxParamA($1,(DLGPROC)$2,");
source = source.replace(/void entry\(void\)\s*\n\s*\{/m, "void entry(void)\n\n{\n  E2R_InitData();");
source = source.replace("_DAT_00ac5218 = &LAB_00458b84;", "_DAT_00ac5218 = (uintptr_t)&E2R_WinMainThunk;");
source = source.replace(/\b_local_([0-9a-fA-F]+)\b/g, "local_$1");
source = source.replace(/\bswitch\s*\(([^;\r\n{}]+)\)/g, "switch((int)(uintptr_t)($1))");
source = source.replace(/\bcase\s*\([A-Za-z_][A-Za-z0-9_\s]*\*\)\s*(0x[0-9a-fA-F]+|\d+)\s*:/g, "case $1:");
source = source.replace(/\(&DAT_(004c3[89ab][0-9a-fA-F]{2})\)\[([^\]]+)\]/g, "((undefined1 *)0x$1)[$2]");
source = source.replace(/\(&DAT_(005074[0-9a-fA-F]{2})\)\[([^\]]+)\]/g, "((undefined1 *)0x$1)[$2]");
source = source.replace(/&DAT_(00ac4[0-9a-fA-F]{3})/g, "(undefined1 *)0x$1");
source = source.replace(/&DAT_(0067b83c|00677998|00675670|0067a490|0067a0a8|00676610|006769f8|0064ec78|0064c888|006625c0)/g, "(undefined1 *)0x$1");
source = source.replace(/\bDAT_00ac4cad\b/g, "(*(undefined1 *)0x00ac4cad)");
source = source.replace(
  "  pbVar5 = (undefined1 *)0x00477068;\n  iVar12 = 0;",
  "  in_EAX = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    in_EAX = in_EAX + 2;\n  }\n  pbVar5 = (undefined1 *)0x00477068;\n  iVar12 = 0;"
);
source = source.replace(
  "    local_80 = FUN_00418a04(pbVar5,&local_84);\n    local_14 = ((undefined1 *)0x006366dc)[in_EAX * 2];",
  "    local_80 = FUN_00418a04((undefined4)(uintptr_t)in_EAX,&local_84);\n    if (local_80 == 0 || local_84 <= 0) {\n      return 0;\n    }\n    local_14 = ((undefined1 *)0x006366dc)[in_EAX * 2];"
);

for (let i = 0; i < prototypes.length; i++) {
  prototypes[i] = prototypes[i].replace("uint * FUN_00461746(void);", "uint * __fastcall FUN_00461746(int heap,uint size);");
  prototypes[i] = prototypes[i].replace("void FUN_00420b8c(void);", "void FUN_00420b8c(int index);");
  prototypes[i] = prototypes[i].replace("void FUN_004526e4(void);", "void FUN_004526e4(short *param_1);");
  prototypes[i] = prototypes[i].replace(
    "undefined8 __fastcall FUN_00448744(undefined4 param_1,undefined4 param_2);",
    "undefined8 __fastcall FUN_00448744(undefined4 param_1,ushort *param_2);"
  );
  prototypes[i] = prototypes[i].replace(
    "undefined8 __fastcall FUN_00451998(undefined4 param_1,undefined4 param_2);",
    "undefined8 __fastcall FUN_00451998(int param_1,undefined4 param_2);"
  );
  prototypes[i] = prototypes[i].replace(
    "undefined8 __fastcall FUN_00442420(undefined4 param_1,undefined4 param_2);",
    "undefined8 __fastcall FUN_00442420(short param_1,undefined4 param_2);"
  );
  prototypes[i] = prototypes[i].replace(
    "void FUN_0045df96(void);",
    "void FUN_0045df96(byte *param_1,byte *param_2);"
  );
  prototypes[i] = prototypes[i].replace(
    "void FUN_0045dff3(void);",
    "void FUN_0045dff3(byte *param_1,short *param_2);"
  );
  prototypes[i] = prototypes[i].replace(
    "void FUN_004249f4(void);",
    "void FUN_004249f4(undefined4 param_1);"
  );
}

ids.add("s_Can_t_load_title_picture_00471320");
ids.add("s_gbnklogo_raw_00470500");
ids.add("s_psyglogo_raw_00470510");
ids.add("s_aasglogo_raw_00470520");

source = source.replace(
  "  case 0x7:\n    psVar7 = (short *)(*(int *)(in_EAX + 1) >> 0x10);\n    if (*(int *)(*(int *)(*(int *)(unaff_ESI + 0x11) + 0x54) + (int)psVar7 * 4) == 0) {\n      uVar12 = FUN_004265ac((undefined4)(uintptr_t)unaff_ESI,\n                            *(int *)(*(int *)(unaff_ESI + 0x11) + 0x54));\n      psVar7 = (short *)uVar12;\n      *psVar7 = in_EAX[2];\n      *(short **)(*(int *)(*(int *)(psVar7 + 0x11) + 0x54) + *psVar7 * 4) = psVar7;\n      return psVar7;\n    }\n    break;\n  case 0x8:",
  "  case 0x7:\n    psVar7 = (short *)(*(int *)(in_EAX + 1) >> 0x10);\n    if ((unaff_ESI == (short *)0x0 || IsBadReadPtr(unaff_ESI,0x26) ||\n         *(int *)(unaff_ESI + 0x11) == 0 ||\n         IsBadReadPtr((void *)(uintptr_t)*(int *)(unaff_ESI + 0x11),0x58)) &&\n        param_2 != (short *)0x0) {\n      unaff_ESI = param_2;\n    }\n    if (unaff_ESI == (short *)0x0 || IsBadReadPtr(unaff_ESI,0x26) ||\n        *(int *)(unaff_ESI + 0x11) == 0 ||\n        IsBadReadPtr((void *)(uintptr_t)*(int *)(unaff_ESI + 0x11),0x58)) {\n      return (short *)0x0;\n    }\n    iVar10 = *(int *)(unaff_ESI + 0x11);\n    iVar11 = *(int *)(iVar10 + 0x54);\n    if (iVar11 == 0 || IsBadReadPtr((void *)(uintptr_t)iVar11,(int)psVar7 * 4 + 4)) {\n      return (short *)0x0;\n    }\n    if (*(int *)(iVar11 + (int)psVar7 * 4) == 0) {\n      uVar12 = FUN_004265ac((undefined4)(uintptr_t)unaff_ESI,iVar11);\n      psVar7 = (short *)uVar12;\n      *psVar7 = in_EAX[2];\n      *(short **)(iVar11 + *psVar7 * 4) = psVar7;\n      return psVar7;\n    }\n    break;\n  case 0x8:"
);
source = source.replace(
  "  psVar2 = *(short **)((undefined1 *)0x00630b60 + (short)in_EAX * 4);\n  if (psVar2 != (short *)0x0) {\n    if (*(int *)(*psVar2 * 2 + 0x671fbe) >> 0x10 != -2) {\n      psVar2[0x91] = *(short *)(*psVar2 * 2 + 0x671fc0);\n    }\n    FUN_00426c3c();\n    if ((((undefined1 *)0x0064a178)[extraout_CX * 2] & 2) == 0) {\n      ((undefined1 *)0x0064a178)[extraout_CX * 2] = ((undefined1 *)0x0064a178)[extraout_CX * 2] | 2;\n      extraout_EDX_01[0x77] = 100;\n      extraout_EDX_01[0x76] = extraout_EDX_01[0x77];\n      if ((-1 < (short)extraout_EDX_01[0x9d]) &&\n         (*(int *)((*(int *)(extraout_EDX_01 + 0x9c) >> 0x10) * 4 + 0x6297c0) != 0)) {\n        FUN_0044f508(extraout_EDX_01,extraout_EDX_01,(ushort *)0x0);\n      }\n    }\n  }",
  "  psVar2 = *(short **)((undefined1 *)0x00630b60 + actor_id * 4);\n  if (psVar2 != (short *)0x0) {\n    if (*(int *)(*psVar2 * 2 + 0x671fbe) >> 0x10 != -2) {\n      psVar2[0x91] = *(short *)(*psVar2 * 2 + 0x671fc0);\n    }\n    E2R_actor_calc_context = (int)(uintptr_t)psVar2;\n    FUN_00426c3c();\n    E2R_actor_calc_context = 0;\n    if ((((undefined1 *)0x0064a178)[*psVar2 * 2] & 2) == 0) {\n      ((undefined1 *)0x0064a178)[*psVar2 * 2] = ((undefined1 *)0x0064a178)[*psVar2 * 2] | 2;\n      psVar2[0x77] = 100;\n      psVar2[0x76] = psVar2[0x77];\n      if ((-1 < psVar2[0x9d]) &&\n         (*(int *)((*(int *)(psVar2 + 0x9c) >> 0x10) * 4 + 0x6297c0) != 0)) {\n        FUN_0044f508(psVar2,psVar2,(ushort *)0x0);\n      }\n    }\n  }"
);
source = source.replace(
  "  if (in_EAX != 0) {\n    *(ushort *)(in_EAX + 2) = *(ushort *)(in_EAX + 2) & 0xf3f6;",
  "  in_EAX = E2R_actor_calc_context;\n  if (in_EAX != 0 && !IsBadReadPtr((void *)(uintptr_t)in_EAX,0x148)) {\n    *(ushort *)(in_EAX + 2) = *(ushort *)(in_EAX + 2) & 0xf3f6;"
);
source = source.replace(
  "    else {\n      FUN_00420dcc();\n      in_EAX = extraout_ECX_06;",
  "    else {\n      E2R_actor_calc_context = (int)(uintptr_t)psVar2;\n      FUN_00420dcc();\n      E2R_actor_calc_context = 0;\n      in_EAX = extraout_ECX_06;"
);
const currentActorTraceReplacements = [
  [
    "          DAT_0047a470 = uVar2;\n          return;",
    "          DAT_0047a470 = E2R_TraceCurrentActorWrite(\"4d34c.return\",(uintptr_t)uVar2);\n          return;"
  ],
  [
    "  DAT_0047a470 = uVar2;\n  return;\n}\n\n\n\n/* 0044db80 */",
    "  DAT_0047a470 = E2R_TraceCurrentActorWrite(\"4d34c.exit\",(uintptr_t)uVar2);\n  return;\n}\n\n\n\n/* 0044db80 */"
  ],
  [
    "    while (DAT_0047a470 = puVar3, sVar9 != 0) {",
    "    while (DAT_0047a470 = E2R_TraceCurrentActorWrite(\"4f508.loop\",(uintptr_t)puVar3),\n          sVar9 != 0) {"
  ],
  [
    "          DAT_0047a470 = *(ushort **)((undefined1 *)0x00630b60 + iVar23 * 4);",
    "          DAT_0047a470 = E2R_TraceCurrentActorWrite(\n               \"4f508.op54.reload\",\n               (uintptr_t)*(ushort **)((undefined1 *)0x00630b60 + iVar23 * 4));"
  ],
  [
    "      DAT_0047a470 = extraout_ECX_00;\n    }\n    else if (*(int *)(iVar1 + 0x64f060) < 0) {",
    "      DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5190c.direct\",(uintptr_t)extraout_ECX_00);\n    }\n    else if (*(int *)(iVar1 + 0x64f060) < 0) {"
  ],
  [
    "      uVar2 = 0;\n      DAT_0047a470 = extraout_ECX_02;",
    "      uVar2 = 0;\n      DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5190c.archive\",(uintptr_t)extraout_ECX_02);"
  ],
  [
    "        result = (int)uVar2;\n        DAT_0047a470 = saved_current;",
    "        result = (int)uVar2;\n        DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51998.direct\",(uintptr_t)saved_current);"
  ],
  [
    "          uVar2 = FUN_0043cbb4(extraout_ECX_02);\n          DAT_0047a470 = saved_current;",
    "          uVar2 = FUN_0043cbb4(extraout_ECX_02);\n          DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51998.missing\",(uintptr_t)saved_current);"
  ],
  [
    "        result = E2R_ParseArchiveFanResource();\n        DAT_0047a470 = saved_current;",
    "        result = E2R_ParseArchiveFanResource();\n        DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51998.archive\",(uintptr_t)saved_current);"
  ],
  [
    "  DAT_0047a470 = saved_current;\n  return CONCAT44(param_2,result);",
    "  DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51998.exit\",(uintptr_t)saved_current);\n  return CONCAT44(param_2,result);"
  ],
  [
    "          DAT_0047a470 = extraout_ECX_04;\n          return CONCAT44(param_2,(int)uVar4);",
    "          DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51a54.direct_missing\",\n                                                    (uintptr_t)extraout_ECX_04);\n          return CONCAT44(param_2,(int)uVar4);"
  ],
  [
    "          DAT_0047a470 = extraout_ECX_07;\n          return CONCAT44(param_2,(int)uVar4);",
    "          DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51a54.archive_missing\",\n                                                    (uintptr_t)extraout_ECX_07);\n          return CONCAT44(param_2,(int)uVar4);"
  ],
  [
    "  DAT_0047a470 = uVar3;\n  return CONCAT44(param_2,iVar2);\n}\n\n\n\n/* 00451bc4 */",
    "  DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51a54.exit\",(uintptr_t)uVar3);\n  return CONCAT44(param_2,iVar2);\n}\n\n\n\n/* 00451bc4 */"
  ],
  [
    "    DAT_0047a470 = uVar3;\n    return;\n  }\n  parse_result = 0;",
    "    DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51f5c.invalid\",(uintptr_t)uVar3);\n    return;\n  }\n  parse_result = 0;"
  ],
  [
    "  DAT_0047a470 = uVar3;\n  if (E2R_actor_load_diag_count < 48) {",
    "  DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51f5c.exit\",(uintptr_t)uVar3);\n  if (E2R_actor_load_diag_count < 48) {"
  ],
  [
    "  DAT_0047a470 = uVar5;\n  return;\n}\n\n\n\n/* 0045233c */",
    "  DAT_0047a470 = E2R_TraceCurrentActorWrite(\"52140.exit\",(uintptr_t)uVar5);\n  return;\n}\n\n\n\n/* 0045233c */"
  ],
  [
    "      DAT_0047a470 = extraout_ECX_00;\n    }\n    else {\n      if (*(int *)(iVar1 + 0x650fa0) < 0) {",
    "      DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.direct\",(uintptr_t)extraout_ECX_00);\n    }\n    else {\n      if (*(int *)(iVar1 + 0x650fa0) < 0) {"
  ],
  [
    "        DAT_0047a470 = extraout_ECX_02;\n        return CONCAT44(param_2,(int)uVar3);",
    "        DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.missing\",(uintptr_t)extraout_ECX_02);\n        return CONCAT44(param_2,(int)uVar3);"
  ],
  [
    "      iVar2 = E2R_ParseArchiveFanResource();\n      DAT_0047a470 = extraout_ECX_04;\n    }\n  }\n  return CONCAT44(param_2,iVar2);\n}\n\n\n\n/* 004523f0 */",
    "      iVar2 = E2R_ParseArchiveFanResource();\n      DAT_0047a470 = E2R_TraceArchiveCurrentActorWrite(\"5233c.archive\",(uintptr_t)extraout_ECX_04);\n    }\n  }\n  return CONCAT44(param_2,iVar2);\n}\n\n\n\n/* 004523f0 */"
  ],
  [
    "      DAT_0047a470 = extraout_ECX_00;\n    }\n    else {\n      if (*(int *)(iVar1 + 0x658660) < 0) {",
    "      DAT_0047a470 = E2R_TraceCurrentActorWrite(\"525f0.direct\",(uintptr_t)extraout_ECX_00);\n    }\n    else {\n      if (*(int *)(iVar1 + 0x658660) < 0) {"
  ],
  [
    "        DAT_0047a470 = extraout_ECX_02;\n        return CONCAT44(param_2,(int)uVar3);",
    "        DAT_0047a470 = E2R_TraceCurrentActorWrite(\"525f0.missing\",(uintptr_t)extraout_ECX_02);\n        return CONCAT44(param_2,(int)uVar3);"
  ],
  [
    "      iVar2 = E2R_ParseArchiveFanResource();\n      DAT_0047a470 = extraout_ECX_04;\n    }\n  }\n  return CONCAT44(param_2,iVar2);\n}\n\n\n\n/* 004526cc */",
    "      iVar2 = E2R_ParseArchiveFanResource();\n      DAT_0047a470 = E2R_TraceArchiveCurrentActorWrite(\"525f0.archive\",(uintptr_t)extraout_ECX_04);\n    }\n  }\n  return CONCAT44(param_2,iVar2);\n}\n\n\n\n/* 004526cc */"
  ]
];
for (const [before, after] of currentActorTraceReplacements) {
  source = source.replace(before, after);
}
source = source.replace(/[ \t]+$/gm, "").replace(/\n*$/, "\n");
fs.writeFileSync(outSrc, source);

const sortedIds = [...ids].sort();
const sortedStacks = [...stackIds].sort();
let header = "";
header += "#pragma once\n";
header += '#include "../src/e2recomp_types.h"\n';
header += "#ifdef _WIN32\n#include <commdlg.h>\n#include <mmsystem.h>\n#else\n#include \"../platform/e2recomp_win32_compat.h\"\n#endif\n#include <stdint.h>\n\n";
header += "#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n";
header += "typedef uint32_t uint3;\ntypedef int32_t int3;\ntypedef uint32_t undefined3;\ntypedef uint64_t undefined6;\ntypedef uint64_t uint6;\ntypedef double float10;\ntypedef unsigned __int64 unkbyte10;\ntypedef unsigned __int64 unkuint10;\ntypedef int code();\ntypedef unsigned char bool;\ntypedef signed char sbyte;\n";
header += "#define tagMSG MSG\n#define tagPOINT POINT\n#define tagSIZE SIZE\n#define tagMIDIOUTCAPSA MIDIOUTCAPSA\n#define _MMCKINFO MMCKINFO\n#define _MMIOINFO MMIOINFO\n#define _WIN32_FIND_DATAA WIN32_FIND_DATAA\n#define _INPUT_RECORD INPUT_RECORD\n#define _SYSTEMTIME SYSTEMTIME\n#define _FILETIME FILETIME\n#define _GUID GUID\n#ifndef true\n#define true 1\n#define false 0\n#endif\n\n";
header += "void E2R_InitData(void);\n";
header += "void E2R_WinMainThunk(void);\n";
header += "LRESULT CALLBACK E2R_WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);\n";
header += "extern uintptr_t E2R_timer_slots[8];\n";
header += "extern uintptr_t E2R_requester_probe_ce58_count;\n";
header += "extern uintptr_t E2R_requester_probe_last_id;\n";
header += "extern uintptr_t E2R_requester_probe_last_mode;\n";
header += "extern uintptr_t E2R_requester_probe_b384_count;\n";
header += "extern uintptr_t E2R_requester_probe_b384_bad_ptr_count;\n";
header += "extern uintptr_t E2R_requester_probe_b384_last_ptr;\n";
header += "extern uintptr_t E2R_requester_probe_b9bc_count;\n";
header += "extern uintptr_t E2R_requester_probe_b9bc_last_item;\n";
header += "extern uintptr_t E2R_requester_probe_bd4c_count;\n";
header += "extern uintptr_t E2R_requester_probe_bd4c_last_key;\n";
header += "extern uintptr_t E2R_requester_probe_bd4c_seen_key_count;\n";
header += "extern uintptr_t E2R_requester_probe_bd4c_no_key_count;\n";
header += "extern uintptr_t E2R_requester_probe_bd4c_last_cursor;\n";
header += "extern uintptr_t E2R_requester_probe_bd4c_param_item;\n";
header += "extern uintptr_t E2R_requester_probe_selected_item;\n";
header += "extern uintptr_t E2R_requester_probe_selected_next;\n";
header += "extern uintptr_t E2R_requester_probe_selected_action;\n";
header += "extern uintptr_t E2R_requester_probe_move_count;\n";
header += "extern uintptr_t E2R_requester_probe_move_key;\n";
header += "extern uintptr_t E2R_requester_probe_move_from;\n";
header += "extern uintptr_t E2R_requester_probe_move_to;\n";
header += "extern uintptr_t E2R_requester_probe_pending_key_count;\n";
header += "extern uintptr_t E2R_requester_probe_pending_key_read;\n";
header += "extern uintptr_t E2R_requester_probe_fed_key_count;\n";
header += "extern uintptr_t E2R_requester_probe_last_fed_key;\n";
header += "extern uintptr_t E2R_requester_probe_last_fed_char;\n";
header += "extern uintptr_t E2R_requester_probe_last_fed_scan;\n";
header += "extern uintptr_t E2R_requester_probe_action_count;\n";
header += "extern uintptr_t E2R_requester_probe_last_action;\n";
header += "extern uintptr_t E2R_start_game_probe_count;\n";
header += "extern uintptr_t E2R_start_game_probe_last_player;\n";
header += "extern uintptr_t E2R_start_game_probe_last_mode;\n";
header += "extern uintptr_t E2R_start_code_probe_startup_scans;\n";
header += "extern uintptr_t E2R_start_code_probe_startup_matches;\n";
header += "extern uintptr_t E2R_start_code_probe_action_scans;\n";
header += "extern uintptr_t E2R_start_code_probe_action_matches;\n";
header += "extern uintptr_t E2R_start_code_probe_dispatches;\n";
header += "extern uintptr_t E2R_start_code_probe_last_node;\n";
header += "extern uintptr_t E2R_start_code_probe_last_name_index;\n";
header += "extern uintptr_t E2R_start_code_probe_last_bytecode_offset;\n";
header += "extern uintptr_t E2R_action_opcode_count;\n";
header += "extern uintptr_t E2R_action_last_opcode;\n";
header += "extern uintptr_t E2R_action_last_cursor;\n";
header += "extern uintptr_t E2R_action_hit_75_count;\n";
header += "void E2R_RequesterProbeQueueKey(uintptr_t key);\n";
header += "void E2R_RequesterProbeFeedPendingKey(void);\n";
header += "extern char E2R_midi_device_labels[10][0x33];\n";
header += "HWND E2R_CreateWindowExA(DWORD exStyle, ...);\n";
header += "INT_PTR E2R_DialogBoxParamA(HINSTANCE inst, LPCSTR tmpl, HWND parent, DLGPROC proc, LPARAM param);\n";
header += "#define CreateWindowExA E2R_CreateWindowExA\n#define DialogBoxParamA E2R_DialogBoxParamA\n\n";
header += "#ifndef SUB41\n";
header += "#define SUB41(x,n) ((undefined1)(((uint32_t)(x) >> (8 * (n))) & 0xffu))\n";
header += "#define SUB42(x,n) ((undefined2)(((uint32_t)(x) >> (8 * (n))) & 0xffffu))\n";
header += "#define SUB44(x,n) ((undefined4)(((uint64_t)(x) >> (8 * (n))) & 0xffffffffu))\n";
header += "#define ZEXT14(x) ((undefined4)(uint8_t)(x))\n#define ZEXT24(x) ((undefined4)(uint16_t)(x))\n";
header += "#define SEXT14(x) ((int32_t)(int8_t)(x))\n#define SEXT24(x) ((int32_t)(int16_t)(x))\n";
header += "#define E2R_READ1(base,off) (*(undefined1 *)((byte *)(uintptr_t)(base) + (off)))\n";
header += "#define E2R_READ2(base,off) (*(undefined2 *)((byte *)(uintptr_t)(base) + (off)))\n";
header += "#define E2R_READ4(base,off) (*(undefined4 *)((byte *)(uintptr_t)(base) + (off)))\n";
header += "#define E2R_READ8(base,off) (*(undefined8 *)((byte *)(uintptr_t)(base) + (off)))\n";
header += "#define E2R_WORD_AT(var,off) (*(undefined2 *)((byte *)&(var) + (off)))\n";
header += "#endif\n\n";
header += "/* Function prototypes recovered from the decompiler signatures. */\n";
header += prototypes.join("\n") + "\n\n";
header += "/* Global labels recovered from Ghidra symbols and decompiler references. */\n";
for (const name of sortedIds) header += name.startsWith("s_") ? `extern char ${name}[];\n` : `extern uintptr_t ${name};\n`;
for (const name of sortedStacks) header += `extern undefined1 ${name}[4096];\n`;
header += "\n#ifdef __cplusplus\n}\n#endif\n";
fs.writeFileSync(outHdr, header);

let globals = '#include "E2Recomp_recon.h"\n\n';
globals += "char E2R_midi_device_labels[10][0x33];\n";
for (const name of sortedIds) globals += name.startsWith("s_") ? `char ${name}[256];\n` : `uintptr_t ${name};\n`;
for (const name of sortedStacks) globals += `undefined1 ${name}[4096];\n`;
fs.writeFileSync(outGlobals, globals);

const renameRows = ["address\told_name\tnew_name\treason"];
for (const f of functions) {
  let newName = null;
  if (f.name === "entry") newName = "program_entry";
  else if (f.name.startsWith("FUN_")) {
    const marker = `/* ${f.address.toLowerCase()} */`;
    const start = source.indexOf(marker);
    const end = start >= 0 ? source.indexOf("\n/* ", start + marker.length) : -1;
    const body = start >= 0 ? source.slice(start, end >= 0 ? end : start + 20000) : "";
    if (/DirectDrawCreate|SetCooperativeLevel|CreateSurface/.test(body)) newName = `video_directdraw_init_${f.address}`;
    else if (/DirectSoundCreate|SIMD_PlayTune|mmio/.test(body)) newName = `audio_init_or_stream_${f.address}`;
    else if (/CreateWindowExA|RegisterClassA|DefWindowProcA/.test(body)) newName = `window_or_dialog_proc_${f.address}`;
    else if (/CODE_ECSTATIC_FAN|actions|scenes|actors/.test(body)) newName = `asset_path_or_fan_loader_${f.address}`;
    else if (/saved|QUICK SAVED GAME|LoadGame/.test(body)) newName = `savegame_handler_${f.address}`;
  }
  if (newName) renameRows.push(`${f.address}\t${f.name}\t${newName}\tstring/import heuristic`);
}
fs.writeFileSync(outRenames, renameRows.join("\n") + "\n");

console.log(`Generated ${outSrc}`);
console.log(`Generated ${outHdr} with ${prototypes.length} prototypes and ${sortedIds.length} globals`);
console.log(`Generated ${outGlobals}`);
