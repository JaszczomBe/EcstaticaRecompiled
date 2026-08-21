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
  '#include "E2Recomp_recon.h"\n#include <math.h>\n#include <stdarg.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include "e2recomp_log.h"\n#ifdef NAN\n#undef NAN\n#endif\n#define NAN(x) isnan((double)(x))\n\nstatic uint E2R_file_flags[256];\n#define E2R_STREAM_MAGIC 0xe25eed01u\n\nstatic int E2R_round_to_int(double value)\n{\n  return (int)(value < 0.0 ? value - 0.5 : value + 0.5);\n}\n\nstatic byte E2R_clamp_byte(int value)\n{\n  if (value < 0) {\n    return 0;\n  }\n  if (255 < value) {\n    return 255;\n  }\n  return (byte)value;\n}\n\nstatic short E2R_clamp_short(int value)\n{\n  if (value < -32768) {\n    return -32768;\n  }\n  if (32767 < value) {\n    return 32767;\n  }\n  return (short)value;\n}\n\nstatic undefined4 E2R_OpenReadStream(LPCSTR path)\n{\n  HANDLE file;\n  DWORD size;\n  DWORD bytes_read = 0;\n  char *buffer;\n  undefined4 *stream;\n\n  file = CreateFileA(path,0x80000000,3,(LPSECURITY_ATTRIBUTES)0x0,3,0x80,(HANDLE)0x0);\n  if (file == INVALID_HANDLE_VALUE) {\n    return 0;\n  }\n  size = SetFilePointer(file,0,(PLONG)0x0,2);\n  if (size == 0xffffffff) {\n    CloseHandle(file);\n    return 0;\n  }\n  SetFilePointer(file,0,(PLONG)0x0,0);\n  buffer = (char *)LocalAlloc(0x40,size == 0 ? 1 : size);\n  stream = (undefined4 *)LocalAlloc(0x40,0x1c);\n  if (buffer == (char *)0x0 || stream == (undefined4 *)0x0) {\n    if (buffer != (char *)0x0) {\n      LocalFree(buffer);\n    }\n    if (stream != (undefined4 *)0x0) {\n      LocalFree(stream);\n    }\n    CloseHandle(file);\n    return 0;\n  }\n  if (size != 0 && ReadFile(file,buffer,size,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    LocalFree(buffer);\n    LocalFree(stream);\n    CloseHandle(file);\n    return 0;\n  }\n  CloseHandle(file);\n  stream[0] = (undefined4)(uintptr_t)buffer;\n  stream[1] = (undefined4)bytes_read;\n  stream[2] = (undefined4)(uintptr_t)(buffer + bytes_read);\n  stream[3] = 0;\n  stream[4] = 0xffffffff;\n  stream[5] = (undefined4)(uintptr_t)buffer;\n  stream[6] = E2R_STREAM_MAGIC;\n  return (undefined4)(uintptr_t)stream;\n}\n\nstatic uint E2R_ReadOpenFileBytes(int descriptor,char *buffer,DWORD bytes_to_read)\n{\n  DWORD bytes_read = 0;\n  HANDLE file;\n  uint slot = (uint)descriptor;\n\n  if (_DAT_00ac51fc == 0 || _DAT_00ac51f8 <= slot) {\n    return 0xffffffff;\n  }\n  file = *(HANDLE *)(_DAT_00ac51fc + slot * 4);\n  if (file == (HANDLE)0x0 || file == INVALID_HANDLE_VALUE) {\n    return 0xffffffff;\n  }\n  if (ReadFile(file,buffer,bytes_to_read,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    return 0xffffffff;\n  }\n  return bytes_read;\n}\n'
);
source = source.replace(
  "#define NAN(x) isnan((double)(x))\n\nstatic uint E2R_file_flags",
  "#define NAN(x) isnan((double)(x))\n#ifndef __has_feature\n#define __has_feature(x) 0\n#endif\n\nstatic uint E2R_file_flags"
);
source = source.replace(
  "static uint E2R_file_flags[256];\n#define E2R_STREAM_MAGIC",
  "static uint E2R_file_flags[256];\nstatic uint E2R_open_diag_count;\nstatic uint E2R_archive_read_diag_count;\nstatic uint E2R_archive_resource_diag_count;\nstatic uint E2R_archive_parse_summary_count;\nstatic uint E2R_scene_load_diag_count;\nstatic uint E2R_actor_load_diag_count;\nstatic int E2R_actor_load_id_override = -1;\nstatic int *E2R_fan_parse_stream;\nstatic short *E2R_fan_parse_record;\nstatic uint E2R_fan_parse_record_count;\nstatic uint E2R_fan_word_read_diag_count;\nstatic uint E2R_fan_action_read_diag_count;\nstatic uint E2R_fan_dispatch_diag_count;\nstatic uint E2R_fan_actor_diag_count;\nstatic uint E2R_fan_action_summary_diag_count;\nstatic uint E2R_fan_phase_diag_count;\nstatic uint E2R_actor_current_diag_count;\nstatic uint E2R_current_actor_trace_diag_count;\nstatic const char *E2R_current_actor_last_site;\nstatic uintptr_t E2R_current_actor_last_value;\nstatic int E2R_actor_calc_context;\n\nstatic void E2R_InitDiagnostics(void) __attribute__((constructor));\nstatic void E2R_InitDiagnostics(void)\n{\n  char *fan_diag = getenv(\"E2R_FAN_DIAG\");\n\n  if (fan_diag != (char *)0x0 && fan_diag[0] != '\\0' && fan_diag[0] != '0') {\n    return;\n  }\n\n  E2R_fan_word_read_diag_count = 0x7fffffff;\n  E2R_fan_action_read_diag_count = 0x7fffffff;\n  E2R_fan_dispatch_diag_count = 0x7fffffff;\n  E2R_fan_actor_diag_count = 0x7fffffff;\n  E2R_fan_action_summary_diag_count = 0x7fffffff;\n  E2R_fan_phase_diag_count = 0x7fffffff;\n}\n\nstatic uint E2R_FanStreamOffset(void)\n{\n  if (E2R_fan_parse_stream == (int *)0x0 || IsBadReadPtr(E2R_fan_parse_stream,0x1c)) {\n    return 0;\n  }\n  return (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                (byte *)(uintptr_t)E2R_fan_parse_stream[5]);\n}\n#define E2R_STREAM_MAGIC"
);
source = source.replace(
  "static uint E2R_actor_current_diag_count;\nstatic uint E2R_current_actor_trace_diag_count;",
  "static uint E2R_actor_current_diag_count;\nstatic int E2R_runtime_diag_enabled;\nstatic int E2R_game_state_log_enabled;\nstatic uint E2R_game_state_log_count;\nstatic uint E2R_current_actor_trace_diag_count;"
);
source = source.replace(
  "static uint E2R_actor_load_diag_count;\nstatic int E2R_actor_load_id_override",
  "static uint E2R_actor_load_diag_count;\nstatic uint E2R_rep_load_diag_count;\nstatic int E2R_actor_load_id_override"
);
source = source.replace(
  "static int E2R_actor_load_id_override = -1;\nstatic int *E2R_fan_parse_stream;",
  "static int E2R_actor_load_id_override = -1;\nstatic short E2R_actor_visible_rep_fallback[5000];\nstatic byte E2R_actor_visible_rep_fallback_valid[5000];\nstatic int *E2R_fan_parse_stream;"
);
source = source.replace(
  "static int E2R_actor_calc_context;\n\nstatic void E2R_InitDiagnostics",
  "static int E2R_actor_calc_context;\nstatic int E2R_action_event_context;\nstatic uintptr_t E2R_hosted_streams[1024];\n\nstatic void E2R_InitDiagnostics"
);
source = source.replace(
  "  char *fan_diag = getenv(\"E2R_FAN_DIAG\");\n\n  if (fan_diag != (char *)0x0 && fan_diag[0] != '\\0' && fan_diag[0] != '0') {",
  "  char *fan_diag = getenv(\"E2R_FAN_DIAG\");\n  char *runtime_diag = getenv(\"E2R_RUNTIME_DIAG\");\n\n  if (runtime_diag != (char *)0x0 && runtime_diag[0] != '\\0' && runtime_diag[0] != '0') {\n    E2R_runtime_diag_enabled = 1;\n  }\n\n  if (fan_diag != (char *)0x0 && fan_diag[0] != '\\0' && fan_diag[0] != '0') {"
);
source = source.replace(
  "  E2R_fan_phase_diag_count = 0x7fffffff;\n}",
  "  E2R_fan_phase_diag_count = 0x7fffffff;\n  E2R_archive_resource_diag_count = 0x7fffffff;\n  E2R_archive_parse_summary_count = 0x7fffffff;\n}"
);
source = source.replace(
  "static uint E2R_FanStreamOffset(void)",
  "static int E2R_RuntimeDiagEnabled(void)\n{\n  return E2R_runtime_diag_enabled;\n}\n\ntypedef struct E2R_SceneGridSnapshot {\n  int active;\n  int count;\n  uint desc_bytes;\n  void *grid;\n  void *desc;\n} E2R_SceneGridSnapshot;\n\nstatic E2R_SceneGridSnapshot E2R_CaptureSceneGridSnapshot(void)\n{\n  E2R_SceneGridSnapshot snapshot;\n\n  memset(&snapshot,0,sizeof(snapshot));\n  if (E2R_action_last_opcode != 0x4d || DAT_0047a77c <= 0 ||\n      0x10000 < DAT_0047a77c) {\n    return snapshot;\n  }\n  snapshot.count = DAT_0047a77c;\n  snapshot.desc_bytes = (uint)DAT_0047a77c * 0xc;\n  snapshot.grid = LocalAlloc(0x40,0x8000);\n  snapshot.desc = LocalAlloc(0x40,snapshot.desc_bytes);\n  if (snapshot.grid == (void *)0x0 || snapshot.desc == (void *)0x0) {\n    if (snapshot.grid != (void *)0x0) {\n      LocalFree(snapshot.grid);\n    }\n    if (snapshot.desc != (void *)0x0) {\n      LocalFree(snapshot.desc);\n    }\n    memset(&snapshot,0,sizeof(snapshot));\n    return snapshot;\n  }\n  memcpy(snapshot.grid,(void *)0x00684d68,0x8000);\n  memcpy(snapshot.desc,(void *)0x0068cd68,snapshot.desc_bytes);\n  snapshot.active = 1;\n  return snapshot;\n}\n\nstatic void E2R_RestoreSceneGridSnapshot(E2R_SceneGridSnapshot *snapshot)\n{\n  if (snapshot == (E2R_SceneGridSnapshot *)0x0 || snapshot->active == 0) {\n    return;\n  }\n  memcpy((void *)0x00684d68,snapshot->grid,0x8000);\n  memcpy((void *)0x0068cd68,snapshot->desc,snapshot->desc_bytes);\n  DAT_0047a77c = snapshot->count;\n  if (E2R_RuntimeDiagEnabled()) {\n    fprintf(stderr,\"scene grid restore: opcode=0x%lx count=%d bytes=%u\\n\",\n            (unsigned long)E2R_action_last_opcode,snapshot->count,\n            snapshot->desc_bytes);\n  }\n  LocalFree(snapshot->grid);\n  LocalFree(snapshot->desc);\n  memset(snapshot,0,sizeof(*snapshot));\n  E2R_PumpHost();\n}\n\nstatic void E2R_LogSceneGridProbe(const char *site,int x,int z)\n{\n  int x_cell;\n  int z_cell;\n  uint direct_cell;\n  uint swapped_cell;\n  uintptr_t direct_desc;\n  uintptr_t swapped_desc;\n  uintptr_t known_desc;\n\n  if (!E2R_RuntimeDiagEnabled()) {\n    return;\n  }\n  x_cell = (x >> 9) + 0x40;\n  z_cell = (z >> 9) + 0x40;\n  if (x_cell < 0 || 0x80 <= x_cell || z_cell < 0 || 0x80 <= z_cell) {\n    fprintf(stderr,\"scene grid probe: site=%s x=%d z=%d x_cell=%d z_cell=%d out_of_range=1 count=%d\\n\",\n            site,x,z,x_cell,z_cell,DAT_0047a77c);\n    return;\n  }\n  direct_cell = (uint)*(ushort *)((undefined1 *)0x00684d68 + x_cell * 2 + z_cell * 0x100);\n  swapped_cell = (uint)*(ushort *)((undefined1 *)0x00684d68 + z_cell * 2 + x_cell * 0x100);\n  direct_desc = 0x0068cd68 + (uintptr_t)direct_cell * 0xc;\n  swapped_desc = 0x0068cd68 + (uintptr_t)swapped_cell * 0xc;\n  known_desc = 0x0068cd68 + (uintptr_t)0x5b96 * 0xc;\n  fprintf(stderr,\n          \"scene grid probe: site=%s x=%d z=%d x_cell=%d z_cell=%d \"\n          \"direct=0x%x swapped=0x%x count=%d direct_words=%04x,%04x \"\n          \"swapped_words=%04x,%04x known5b96_words=%04x,%04x\\n\",\n          site,x,z,x_cell,z_cell,(unsigned int)direct_cell,\n          (unsigned int)swapped_cell,DAT_0047a77c,\n          !IsBadReadPtr((void *)direct_desc,0xc) ? (unsigned int)*(ushort *)(direct_desc + 8) : 0xffff,\n          !IsBadReadPtr((void *)direct_desc,0xc) ? (unsigned int)*(ushort *)(direct_desc + 10) : 0xffff,\n          !IsBadReadPtr((void *)swapped_desc,0xc) ? (unsigned int)*(ushort *)(swapped_desc + 8) : 0xffff,\n          !IsBadReadPtr((void *)swapped_desc,0xc) ? (unsigned int)*(ushort *)(swapped_desc + 10) : 0xffff,\n          !IsBadReadPtr((void *)known_desc,0xc) ? (unsigned int)*(ushort *)(known_desc + 8) : 0xffff,\n          !IsBadReadPtr((void *)known_desc,0xc) ? (unsigned int)*(ushort *)(known_desc + 10) : 0xffff);\n}\n\nstatic uint E2R_FanStreamOffset(void)"
);
source = source.replace(
  "#define E2R_STREAM_MAGIC 0xe25eed01u\n\nstatic int E2R_round_to_int",
  "#define E2R_STREAM_MAGIC 0xe25eed01u\n\nstatic int E2R_RegisterHostedStream(undefined4 *stream)\n{\n  unsigned i;\n\n  for (i = 0; i < 1024; i++) {\n    if (E2R_hosted_streams[i] == 0 || E2R_hosted_streams[i] == (uintptr_t)stream) {\n      E2R_hosted_streams[i] = (uintptr_t)stream;\n      return 1;\n    }\n  }\n  return 0;\n}\n\nstatic int E2R_UnregisterHostedStream(undefined4 *stream)\n{\n  unsigned i;\n\n  for (i = 0; i < 1024; i++) {\n    if (E2R_hosted_streams[i] == (uintptr_t)stream) {\n      E2R_hosted_streams[i] = 0;\n      return 1;\n    }\n  }\n  return 0;\n}\n\nstatic int E2R_IsKnownActorPointer(int actor)\n{\n  short actor_id;\n\n  if (actor == 0) {\n    return 1;\n  }\n  if ((uint)actor < 0x10000u || 0x70000000u <= (uint)actor ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x136)) {\n    return 0;\n  }\n  actor_id = *(short *)(uintptr_t)actor;\n  if (actor_id < 0 || 5000 <= actor_id) {\n    return 0;\n  }\n  return *(int *)((undefined1 *)0x00630b60 + actor_id * 4) == actor;\n}\n\nstatic int E2R_CurrentSceneTableSlot(uintptr_t value)\n{\n  uintptr_t offset;\n\n  if (value < (uintptr_t)0x0067c728 ||\n      (uintptr_t)(0x0067c728 + 0x4b0 * 0x1c) <= value) {\n    return -1;\n  }\n  offset = value - (uintptr_t)0x0067c728;\n  if (offset % 0x1c != 0) {\n    return -1;\n  }\n  return (int)(offset / 0x1c);\n}\n\nstatic int E2R_IsReadableCurrentPointer(uintptr_t value)\n{\n  return value != 0 && 0x10000u <= (uint)value && (uint)value < 0x70000000u &&\n         !IsBadReadPtr((void *)value,0xaa);\n}\n\nstatic void E2R_PrintCurrentPointerShape(const char *site, uintptr_t value)\n{\n  int readable;\n  short word0 = 0;\n  short word82 = 0;\n  int dword84 = 0;\n  int dworda6 = 0;\n\n  readable = E2R_IsReadableCurrentPointer(value);\n  if (readable) {\n    word0 = *(short *)value;\n    word82 = *(short *)(value + 0x82);\n    dword84 = *(int *)(value + 0x84);\n    dworda6 = *(int *)(value + 0xa6);\n  }\n  fprintf(stderr,\n          \"current pointer shape: site=%s value=0x%lx readable=%d \"\n          \"known_actor=%d scene=0x%lx eq_scene=%d scene_slot=%d \"\n          \"w0=%d w82=0x%x d84=0x%lx da6=0x%lx table0=0x%lx\\n\",\n          site,(unsigned long)value,readable,E2R_IsKnownActorPointer((int)value),\n          (unsigned long)_DAT_0073cc3c,value == (uintptr_t)_DAT_0073cc3c,\n          E2R_CurrentSceneTableSlot(value),(int)word0,(unsigned int)(ushort)word82,\n          (unsigned long)(uint)dword84,(unsigned long)(uint)dworda6,\n          (unsigned long)*(int *)0x00630b60);\n}\n\nstatic uintptr_t E2R_TraceCurrentActorWrite(const char *site, uintptr_t value)\n{\n  E2R_current_actor_last_site = site;\n  E2R_current_actor_last_value = value;\n  if (value != 0 && E2R_current_actor_trace_diag_count < 32 &&\n      (strcmp(site,\"5233c.archive\") == 0 || strcmp(site,\"525f0.archive\") == 0)) {\n    E2R_current_actor_trace_diag_count = E2R_current_actor_trace_diag_count + 1;\n    E2R_PrintCurrentPointerShape(site,value);\n  }\n  return value;\n}\n\nstatic uintptr_t E2R_TraceArchiveCurrentActorWrite(const char *site, uintptr_t value)\n{\n  if (value != 0 && !E2R_IsReadableCurrentPointer(value)) {\n    E2R_current_actor_last_site = site;\n    E2R_current_actor_last_value = 0;\n    if (E2R_current_actor_trace_diag_count < 32) {\n      E2R_current_actor_trace_diag_count = E2R_current_actor_trace_diag_count + 1;\n      E2R_PrintCurrentPointerShape(site,value);\n    }\n    return 0;\n  }\n  return E2R_TraceCurrentActorWrite(site,value);\n}\n\nstatic void E2R_SelectSceneRecord(short scene_id)\n{\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return;\n  }\n  _DAT_0073ccba = (ushort)scene_id;\n  FUN_0044c6bc();\n}\n\nstatic int E2R_round_to_int"
);
source = source.replace(
  "static undefined4 E2R_OpenReadStream(LPCSTR path)",
  "static int E2R_ReadHostedStreamByte(undefined4 *stream)\n{\n  byte *cursor;\n  int value;\n\n  if (stream == (undefined4 *)0x0 || IsBadReadPtr(stream,0x1c)) {\n    return -1;\n  }\n  if ((int)stream[1] < 1) {\n    *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x10;\n    return -1;\n  }\n  cursor = (byte *)(uintptr_t)stream[0];\n  value = (int)*cursor;\n  stream[0] = (undefined4)(uintptr_t)(cursor + 1);\n  stream[1] = stream[1] + -1;\n  if ((*(byte *)(stream + 3) & 0x40) == 0) {\n    if (value == '\\r') {\n      if ((int)stream[1] < 1) {\n        *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x10;\n        return -1;\n      }\n      cursor = (byte *)(uintptr_t)stream[0];\n      value = (int)*cursor;\n      stream[0] = (undefined4)(uintptr_t)(cursor + 1);\n      stream[1] = stream[1] + -1;\n    }\n    if (value == '\\x1a') {\n      *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x10;\n      return -1;\n    }\n  }\n  return value;\n}\n\nstatic int E2R_ReadFanWordByte(int *stream)\n{\n  byte *cursor;\n\n  if (stream == E2R_fan_parse_stream && stream != (int *)0x0 &&\n      (uint)stream[6] == E2R_STREAM_MAGIC) {\n    if (0 < stream[1] && ((*(byte *)(stream + 3) & 4) == 0)) {\n      cursor = (byte *)(uintptr_t)stream[0];\n      if (*cursor != '\\r' && *cursor != '\\x1a') {\n        stream[0] = (int)(uintptr_t)(cursor + 1);\n        stream[1] = stream[1] + -1;\n        return (int)*cursor;\n      }\n    }\n    return E2R_ReadHostedStreamByte((undefined4 *)stream);\n  }\n  if (stream == (int *)0x0 || IsBadReadPtr(stream,0x1c)) {\n    return -1;\n  }\n  if (0 < stream[1] && ((*(byte *)(stream + 3) & 4) == 0)) {\n    cursor = (byte *)(uintptr_t)stream[0];\n    if (!IsBadReadPtr(cursor,1) && *cursor != '\\r' && *cursor != '\\x1a') {\n      stream[0] = (int)(uintptr_t)(cursor + 1);\n      stream[1] = stream[1] + -1;\n      return (int)*cursor;\n    }\n  }\n  return E2R_ReadHostedStreamByte((undefined4 *)stream);\n}\n\nstatic void E2R_MarkVisibilityRecords(byte *records,int record_count)\n{\n  byte b0;\n  byte b1;\n  byte *desc;\n  int guard;\n  int i;\n  uint slot;\n\n  for (i = 0; i < record_count; i = i + 1) {\n    slot = (uint)*(ushort *)((undefined1 *)0x00684d68 +\n                             (uint)records[0] * 2 + (uint)records[1] * 0x100);\n    b0 = records[2];\n    b1 = records[3];\n    desc = (byte *)0x0068cd68 + slot * 0xc;\n    guard = 0;\n    while (slot != 0xffff && guard < 0x10000) {\n      if (desc[0] == b0 && desc[1] == b1) {\n        desc[3] = desc[3] | 0x40;\n      }\n      if ((*(int *)desc >> 0x10 & 0x8000U) != 0) {\n        break;\n      }\n      desc = desc + 0xc;\n      slot = slot + 1;\n      guard = guard + 1;\n    }\n    records = records + 4;\n  }\n}\n\nstatic int E2R_ReadHostedVisibilityFromArchive(void)\n{\n  byte magic_bytes[4];\n  undefined4 *stream;\n  int byte_value;\n  int count;\n  int i;\n  int offset;\n  int scene_id;\n  uint magic;\n\n  scene_id = (int)(_DAT_0073ccb8 >> 0x10);\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return 0;\n  }\n  offset = *(int *)((undefined1 *)0x006467a8 + scene_id * 4);\n  if (offset < 0 || (int)FUN_0045f296(DAT_0047a724,offset) == -1) {\n    return 0;\n  }\n  stream = (undefined4 *)(uintptr_t)DAT_0047a724;\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      stream[6] != E2R_STREAM_MAGIC) {\n    return 0;\n  }\n  for (i = 0; i < 4; i = i + 1) {\n    byte_value = E2R_ReadHostedStreamByte(stream);\n    if (byte_value < 0) {\n      return 0;\n    }\n    magic_bytes[i] = (byte)byte_value;\n  }\n  magic = (uint)magic_bytes[0] | ((uint)magic_bytes[1] << 8) |\n          ((uint)magic_bytes[2] << 0x10) | ((uint)magic_bytes[3] << 0x18);\n  if (magic != 0x4d736956U) {\n    if (E2R_RuntimeDiagEnabled()) {\n      fprintf(stderr,\"visibility magic mismatch: scene=%d offset=%d value=%08x\\n\",\n              scene_id,offset,magic);\n    }\n    return 0;\n  }\n  byte_value = E2R_ReadHostedStreamByte(stream);\n  if (byte_value < 0) {\n    return 0;\n  }\n  count = byte_value;\n  byte_value = E2R_ReadHostedStreamByte(stream);\n  if (byte_value < 0) {\n    return 0;\n  }\n  count = count | (byte_value << 8);\n  if (0x1f3ff < count * 4) {\n    if (E2R_RuntimeDiagEnabled()) {\n      fprintf(stderr,\"visibility info too big: scene=%d count=%d\\n\",scene_id,count);\n    }\n    return 0;\n  }\n  for (i = 0; i < count * 4; i = i + 1) {\n    byte_value = E2R_ReadHostedStreamByte(stream);\n    if (byte_value < 0) {\n      return 0;\n    }\n    ((byte *)(uintptr_t)_DAT_00636668)[i] = (byte)byte_value;\n  }\n  E2R_MarkVisibilityRecords((byte *)(uintptr_t)_DAT_00636668,count);\n  return count;\n}\n\nstatic undefined4 E2R_OpenReadStream(LPCSTR path)"
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
source = source.replace(
  "  stream[5] = (undefined4)(uintptr_t)buffer;\n  stream[6] = E2R_STREAM_MAGIC;\n  return (undefined4)(uintptr_t)stream;",
  "  stream[5] = (undefined4)(uintptr_t)buffer;\n  stream[6] = E2R_STREAM_MAGIC;\n  E2R_RegisterHostedStream(stream);\n  return (undefined4)(uintptr_t)stream;"
);

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
  "undefined8 __fastcall FUN_004603d1(undefined4 param_1,undefined4 param_2)\n\n{\n  uint uVar1;\n  uint old_capacity;\n  uint new_capacity;\n  uintptr_t new_table;\n  HANDLE hFile;\n  \n  hFile = (HANDLE)(uintptr_t)param_1;\n  if (_DAT_00ac51fc == 0) {\n    old_capacity = DAT_0047d610 == 0 ? 0x14 : (uint)DAT_0047d610;\n    if (0x100 < old_capacity) {\n      old_capacity = 0x100;\n    }\n    _DAT_00ac51fc = (uintptr_t)LocalAlloc(0x40,old_capacity * 4);\n    _DAT_00ac51f8 = old_capacity;\n  }\n  if (_DAT_00ac51fc == 0) {\n    CloseHandle(hFile);\n    return CONCAT44(param_2,0xffffffff);\n  }\n  for (uVar1 = 0; uVar1 < _DAT_00ac51f8; uVar1 = uVar1 + 1) {\n    if (*(HANDLE *)(_DAT_00ac51fc + uVar1 * 4) == (HANDLE)0x0) {\n      *(HANDLE *)(_DAT_00ac51fc + uVar1 * 4) = hFile;\n      return CONCAT44(param_2,uVar1);\n    }\n  }\n  if (_DAT_00ac51f8 < 0x100) {\n    old_capacity = (uint)_DAT_00ac51f8;\n    new_capacity = old_capacity * 2;\n    if (new_capacity <= old_capacity) {\n      new_capacity = old_capacity + 1;\n    }\n    if (0x100 < new_capacity) {\n      new_capacity = 0x100;\n    }\n    new_table = (uintptr_t)LocalAlloc(0x40,new_capacity * 4);\n    if (new_table != 0) {\n      memcpy((void *)new_table,(void *)_DAT_00ac51fc,old_capacity * 4);\n      LocalFree((void *)_DAT_00ac51fc);\n      _DAT_00ac51fc = new_table;\n      _DAT_00ac51f8 = new_capacity;\n      if (E2R_RuntimeDiagEnabled()) {\n        fprintf(stderr,\"file table grow: old=%u new=%u\\n\",old_capacity,new_capacity);\n      }\n      *(HANDLE *)(_DAT_00ac51fc + old_capacity * 4) = hFile;\n      return CONCAT44(param_2,old_capacity);\n    }\n  }\n  CloseHandle(hFile);\n  return CONCAT44(param_2,0xffffffff);\n}\n\n\n\n/* 004604e6 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_0046038c\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004603d1 \*\//,
  "undefined8 __fastcall FUN_0046038c(undefined4 param_1,undefined4 param_2)\n\n{\n  undefined4 uVar1;\n  uint i;\n\n  (void)param_1;\n  if (_DAT_00ac51f8 < 0x100) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  uVar1 = 1;\n  if (_DAT_00ac51fc != 0) {\n    for (i = 0; i < _DAT_00ac51f8; i = i + 1) {\n      if (*(HANDLE *)(_DAT_00ac51fc + i * 4) == (HANDLE)0x0) {\n        uVar1 = 0;\n        break;\n      }\n    }\n  }\n  return CONCAT44(param_2,uVar1);\n}\n\n\n\n/* 004603d1 */"
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
  "$1int current_action_flag;\n  int requester_id;\n  undefined8 uVar4;\n\n  E2R_TraceInputFlags(\"15d40.enter\");"
);
source = source.replace(
  "  int requester_id;\n  undefined8 uVar4;\n\n  if (_DAT_00636690 != 0) {",
  "  int requester_id;\n  undefined8 uVar4;\n\n  E2R_TraceInputFlags(\"15d40.enter\");\n  if (_DAT_00636690 != 0) {"
);
source = source.replace(
  "  E2R_TraceInputFlags(\"15d40.enter\");\n  if (_DAT_00636690 != 0) {",
  "  E2R_TraceInputFlags(\"15d40.enter\");\n  if (DAT_00636850 != '\\0') {\n    E2R_RequestIntroSkip();\n  }\n  if (_DAT_00636690 != 0) {"
);
source = source.replace(
  "  E2R_TraceInputFlags(\"15d40.enter\");\n\n  if (_DAT_00636690 != 0) {",
  "  E2R_TraceInputFlags(\"15d40.enter\");\n  if (DAT_00636850 != '\\0') {\n    E2R_RequestIntroSkip();\n  }\n\n  if (_DAT_00636690 != 0) {"
);
source = source.replace(
  /  E2R_TraceInputFlags\("15d40\.enter"\);\r?\n\s*\r?\n  if \(_DAT_00636690 != 0\) \{/,
  "  E2R_TraceInputFlags(\"15d40.enter\");\n  if (DAT_00636850 != '\\0') {\n    E2R_RequestIntroSkip();\n  }\n\n  if (_DAT_00636690 != 0) {"
);
source = source.replace(
  "    else {\n      if (((((DAT_0063685c != '\\0') || (DAT_0063685a != '\\0')) || (DAT_00636855 != '\\0')) ||\n          (((DAT_00636854 != '\\0' || (DAT_00636856 != '\\0')) ||\n           ((DAT_00636857 != '\\0' || ((DAT_00636859 != '\\0' || (DAT_00636858 != '\\0')))))))) ||\n         ((DAT_0063685b != '\\0' ||\n          ((DAT_00636850 != '\\0' ||\n           ((*(int *)(DAT_0047a470 + 0xa6) != 0 &&\n            ((*(byte *)(*(int *)(DAT_0047a470 + 0xa6) + 0xc) & 2) != 0)))))))) {",
  "    else {\n      current_action_flag = 0;\n      if (E2R_IsReadableCurrentPointer(DAT_0047a470)) {\n        iVar2 = *(int *)(DAT_0047a470 + 0xa6);\n        if (iVar2 != 0 && 0x10000u <= (uint)iVar2 && (uint)iVar2 < 0x70000000u &&\n            !IsBadReadPtr((void *)(uintptr_t)iVar2,0x10)) {\n          current_action_flag = (*(byte *)(iVar2 + 0xc) & 2) != 0;\n        }\n      }\n      if (DAT_0063685c != '\\0' || DAT_0063685a != '\\0' || DAT_00636855 != '\\0' ||\n          DAT_00636854 != '\\0' || DAT_00636856 != '\\0' || DAT_00636857 != '\\0' ||\n          DAT_00636859 != '\\0' || DAT_00636858 != '\\0' || DAT_0063685b != '\\0' ||\n          DAT_00636850 != '\\0' || current_action_flag != 0) {\n        if (DAT_00636850 != '\\0') {\n          E2R_GameStateLog(\"15d40.space activity reset action_timer current_action_flag=%d\",\n                           current_action_flag);\n        }"
);
source = source.replace(
  "        if (DAT_00636850 != '\\0') {\n          E2R_GameStateLog(\"15d40.space activity reset action_timer current_action_flag=%d\",\n                           current_action_flag);\n        }\n        _DAT_00636860 = _DAT_00636588;",
  "        if (DAT_00636850 != '\\0') {\n          E2R_GameStateLog(\"15d40.space activity reset action_timer current_action_flag=%d\",\n                           current_action_flag);\n          E2R_RequestIntroSkip();\n        }\n        _DAT_00636860 = _DAT_00636588;"
);
source = source.replace(
  "    DAT_0047a788 = 1;\n    DAT_00636844 = '\\0';\n    _DAT_00643650 = 5;\n    if (DAT_00479db4 != 0) {\n      param_1 = 0;\n      DAT_00479db4 = 0;\n    }\n    uVar4 = FUN_0043ce58(param_1,5);",
  "    E2R_GameStateLog(\"15d40.escape/menu accepted esc=%u menu_request=%lu mode=%lu\",\n                     (unsigned int)(byte)DAT_00636844,\n                     (unsigned long)DAT_00479db4,(unsigned long)DAT_00479de8);\n    DAT_0047a788 = 1;\n    DAT_00636844 = '\\0';\n    E2R_TraceInputFlags(\"15d40.after-escape-clear\");\n    _DAT_00643650 = 5;\n    requester_id = 0x28;\n    if (DAT_00479db4 != 0) {\n      requester_id = 0x27;\n      param_1 = 0;\n      DAT_00479db4 = 0;\n    }\n    E2R_GameStateLog(\"15d40.open requester begin id=0x%x state=%lu dialog=%lu space=%u\",\n                     requester_id,(unsigned long)_DAT_00643650,\n                     (unsigned long)DAT_0047a76c,(unsigned int)(byte)DAT_00636850);\n    uVar4 = FUN_0043ce58(requester_id,5);\n    E2R_GameStateLog(\n        \"15d40.open requester end id=0x%x ret=0x%lx:%lx state=%lu dialog=%lu ce58=%lu b384=%lu b9bc=%lu bd4c=%lu\",\n        requester_id,(unsigned long)(uint)uVar4,\n        (unsigned long)(uint)((ulonglong)uVar4 >> 0x20),\n        (unsigned long)_DAT_00643650,(unsigned long)DAT_0047a76c,\n        (unsigned long)E2R_requester_probe_ce58_count,\n        (unsigned long)E2R_requester_probe_b384_count,\n        (unsigned long)E2R_requester_probe_b9bc_count,\n        (unsigned long)E2R_requester_probe_bd4c_count);"
);
source = source.replace(
  "    FUN_0041cfc0();\n    param_1 = extraout_ECX_11;",
  "    E2R_GameStateLog(\"15d40.switch done state=%lu dialog=%lu space=%u\",\n                     (unsigned long)_DAT_00643650,(unsigned long)DAT_0047a76c,\n                     (unsigned int)(byte)DAT_00636850);\n    E2R_GameStateLog(\"15d40.clear input begin esc=%u space=%u\",\n                     (unsigned int)(byte)DAT_00636844,\n                     (unsigned int)(byte)DAT_00636850);\n    FUN_0041cfc0();\n    E2R_GameStateLog(\"15d40.clear input end esc=%u space=%u\",\n                     (unsigned int)(byte)DAT_00636844,\n                     (unsigned int)(byte)DAT_00636850);\n    E2R_TraceInputFlags(\"15d40.after-menu\");\n    param_1 = extraout_ECX_11;"
);
source = source.replace(
  "    case 6:\n      FUN_00414e68();\n    }\n    E2R_GameStateLog(\"15d40.switch done state=%lu dialog=%lu space=%u\",",
  "    case 6:\n      DestroyWindow(_DAT_00ac4dac);\n    }\n    E2R_GameStateLog(\"15d40.switch done state=%lu dialog=%lu space=%u\","
);
source = source.replace(
  "  if (DAT_00636845 != '\\0') {\n    DAT_00636845 = '\\0';\n  }\n  return;\n}\n\n\n\n/* 0041643c */",
  "  if (DAT_00636845 != '\\0') {\n    DAT_00636845 = '\\0';\n  }\n  E2R_TraceInputFlags(\"15d40.exit\");\n  return;\n}\n\n\n\n/* 0041643c */"
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
  functionSource = functionSource.replace(
    "  DAT_0047a76c = 1;\n  iVar1 = _DAT_00637250;",
    "  DAT_0047a76c = 1;\n  E2R_TraceStartGameStage(\"after-setup\");\n  iVar1 = _DAT_00637250;"
  );
  functionSource = functionSource.replace(
    "        E2R_start_code_probe_startup_matches++;\n        E2R_InvokeActionCode((short *)(uintptr_t)iVar1);\n      }\n    }\n  }\n  _DAT_0073cc3c = 0;",
    "        E2R_start_code_probe_startup_matches++;\n        E2R_TraceStartGameStage(\"before-startup-action\");\n        E2R_InvokeActionCode((short *)(uintptr_t)iVar1);\n        E2R_TraceStartGameStage(\"after-startup-action\");\n      }\n    }\n  }\n  E2R_TraceStartGameStage(\"after-startup-loop\");\n  _DAT_0073cc3c = 0;"
  );
  functionSource = functionSource.replace(
    "      E2R_start_code_probe_action_matches++;\n      E2R_InvokeActionCode((short *)(uintptr_t)iVar1);\n      break;",
    "      E2R_start_code_probe_action_matches++;\n      E2R_TraceStartGameStage(\"before-list-action\");\n      E2R_InvokeActionCode((short *)(uintptr_t)iVar1);\n      E2R_TraceStartGameStage(\"after-list-action\");\n      break;"
  );
  functionSource = functionSource.replace(
    "      E2R_start_code_probe_action_matches++;\n      E2R_InvokeActionCode(action);\n    }\n  }\n  if (iVar1 == 0) {",
    "      E2R_start_code_probe_action_matches++;\n      E2R_TraceStartGameStage(\"before-suffix-action\");\n      E2R_InvokeActionCode(action);\n      E2R_TraceStartGameStage(\"after-suffix-action\");\n    }\n  }\n  if (iVar1 == 0) {"
  );
  functionSource = functionSource.replace(
    "  FUN_0041af88(pcVar4,uVar6);\n  uVar6 = extraout_EDX_16;",
    "  E2R_TraceStartGameStage(\"before-script-name\");\n  FUN_0041af88(pcVar4,uVar6);\n  E2R_TraceStartGameStage(\"after-script-name\");\n  uVar6 = extraout_EDX_16;"
  );
  functionSource = functionSource.replace(
    "    FUN_0043acec();\n    uVar6 = extraout_EDX_17;",
    "    E2R_TraceStartGameStage(\"before-acec\");\n    FUN_0043acec();\n    E2R_TraceStartGameStage(\"after-acec\");\n    uVar6 = extraout_EDX_17;"
  );
  functionSource = functionSource.replace(
    "    FUN_0043ac60();\n    uVar6 = extraout_EDX_18;",
    "    E2R_TraceStartGameStage(\"before-ac60\");\n    FUN_0043ac60();\n    E2R_TraceStartGameStage(\"after-ac60\");\n    uVar6 = extraout_EDX_18;"
  );
  functionSource = functionSource.replace(
    "  FUN_0041af88(0x96,uVar6);\n  FUN_0045fc70(extraout_ECX_20,0);",
    "  E2R_TraceStartGameStage(\"before-script-150\");\n  FUN_0041af88(0x96,uVar6);\n  E2R_TraceStartGameStage(\"after-script-150\");\n  E2R_TraceStartGameStage(\"before-5fc70\");\n  FUN_0045fc70(extraout_ECX_20,0);\n  E2R_TraceStartGameStage(\"after-5fc70\");"
  );
  functionSource = functionSource.replace(
    "  if (_DAT_0073cc3c == 0 && E2R_start_game_probe_last_mode == 0) {\n    E2R_SelectSceneRecord(785);\n  }\n  DAT_0047ab28 = 100;",
    "  if (_DAT_0073cc3c == 0 && E2R_start_game_probe_last_mode == 0 &&\n      E2R_ShouldForceScene785Fallback()) {\n    E2R_TraceStartGameStage(\"before-select-785\");\n    E2R_SelectSceneRecord(785);\n    E2R_TraceStartGameStage(\"after-select-785\");\n  }\n  E2R_TraceStartGameStage(\"before-return\");\n  DAT_0047ab28 = 100;"
  );
  source = source.slice(0,functionStart) + functionSource + source.slice(functionEnd);
}
source = source.replace(
  "  if (iVar1 != 0) {\n    iVar1 = 0;\n  }\n  if (iVar1 == 0) {\n    short *action = E2R_FindActionCodeBySuffix(pcVar4);",
  "  if (iVar1 != 0) {\n    iVar1 = 1;\n  }\n  if (iVar1 == 0) {\n    short *action = E2R_FindActionCodeBySuffix(pcVar4);"
);
source = source.replace(
  /(void __fastcall FUN_0044f508\(ushort \*param_1,ushort \*param_2,ushort \*param_3\)[\s\S]*?\r?\n  undefined2 uVar21;\r?\n\s*)local_34 = 0xffffffff;/,
  "$1uint preload_child_guard;\n  uint preload_token;\n\n  if (E2R_action_dispatch_node != (short *)0x0) {\n    in_EAX = (int)(uintptr_t)E2R_action_dispatch_node;\n  }\n  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xe)) {\n    return;\n  }\n  \n  local_34 = 0xffffffff;"
);
source = source.replace(
  "      uVar25 = CONCAT44(puVar18,_DAT_00ac4a54);\n      switch((int)(uintptr_t)((short)*local_2c)) {",
  "      uVar25 = CONCAT44(puVar18,_DAT_00ac4a54);\n      E2R_action_opcode_count++;\n      E2R_action_last_opcode = (ushort)sVar9;\n      E2R_action_last_cursor = (uintptr_t)local_2c;\n      if (E2R_RuntimeDiagEnabled() &&\n          (E2R_action_opcode_count < 16 ||\n           (E2R_action_opcode_count & 0x1ffu) == 0)) {\n        fprintf(stderr,\"action opcode: ordinal=%lu cursor=0x%lx pool=0x%lx op=%04x next=%04x scene=0x%lx mode=%lu dispatch=%lu\\n\",\n                (unsigned long)E2R_action_opcode_count,\n                (unsigned long)(uintptr_t)local_2c,\n                (unsigned long)((byte *)(uintptr_t)local_2c - (byte *)(uintptr_t)_DAT_006366a0),\n                (unsigned int)(ushort)sVar9,\n                (unsigned int)*(ushort *)((int)local_2c + 2),\n                (unsigned long)_DAT_0073cc3c,(unsigned long)DAT_0047a76c,\n                (unsigned long)E2R_start_code_probe_dispatches);\n      }\n      if ((ushort)sVar9 == 0x75) {\n        E2R_action_hit_75_count++;\n      }\n      switch((int)(uintptr_t)((short)*local_2c)) {"
);
source = source.replace(
  /(\s+uVar25 = CONCAT44\(puVar18,_DAT_00ac4a54\);\r?\n)\s+switch\(\(int\)\(uintptr_t\)\(\(short\)\*local_2c\)\) \{/,
  "$1      E2R_action_opcode_count++;\n      E2R_action_last_opcode = (ushort)sVar9;\n      E2R_action_last_cursor = (uintptr_t)local_2c;\n      if (E2R_RuntimeDiagEnabled() &&\n          (E2R_action_opcode_count < 16 ||\n           (E2R_action_opcode_count & 0x1ffu) == 0)) {\n        fprintf(stderr,\"action opcode: ordinal=%lu cursor=0x%lx pool=0x%lx op=%04x next=%04x scene=0x%lx mode=%lu dispatch=%lu\\n\",\n                (unsigned long)E2R_action_opcode_count,\n                (unsigned long)(uintptr_t)local_2c,\n                (unsigned long)((byte *)(uintptr_t)local_2c - (byte *)(uintptr_t)_DAT_006366a0),\n                (unsigned int)(ushort)sVar9,\n                (unsigned int)*(ushort *)((int)local_2c + 2),\n                (unsigned long)_DAT_0073cc3c,(unsigned long)DAT_0047a76c,\n                (unsigned long)E2R_start_code_probe_dispatches);\n      }\n      if ((ushort)sVar9 == 0x75) {\n        E2R_action_hit_75_count++;\n      }\n      switch((int)(uintptr_t)((short)*local_2c)) {"
);
source = source.replace(
  "                FUN_00420dcc();\n                puVar13 = extraout_ECX_19;\n                psVar16 = extraout_EDX_11;",
  "                FUN_00420dcc();\n                puVar13 = extraout_ECX_19;"
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
  "    if (*(int *)(param_2 + 6) != 0) {\n      (**(code **)(param_2 + 6))();\n      uVar6 = extraout_ECX_00;\n      uVar8 = extraout_DX_00;\n    }",
  "    if (*(int *)(param_2 + 6) != 0) {\n      E2R_requester_probe_action_count++;\n      E2R_requester_probe_last_action = *(uintptr_t *)(param_2 + 6);\n      if (E2R_InvokeRequesterAction(E2R_requester_probe_last_action)) {\n        return 1;\n      }\n    }"
);
source = source.replace(
  "  if (*(int *)(param_2 + 6) != 0) {\n    (**(code **)(param_2 + 6))();\n    uVar6 = extraout_ECX;\n    _DAT_006443d0 = extraout_DX;\n  }",
  "  if (*(int *)(param_2 + 6) != 0) {\n    E2R_requester_probe_action_count++;\n    E2R_requester_probe_last_action = *(uintptr_t *)(param_2 + 6);\n    if (E2R_InvokeRequesterAction(E2R_requester_probe_last_action)) {\n      return 1;\n    }\n  }"
);
source = source.replace(
  "  }\n  FUN_0041cfc0();\n  return;\ncode_r0x0043bf38:",
  "  }\n  else {\n    E2R_requester_probe_bd4c_no_key_count++;\n  }\n  FUN_0041cfc0();\n  return;\ncode_r0x0043bf38:"
);
source = source.replace(
  "  _DAT_0064342c = 0;\n  _DAT_006443d0 = (ushort)(in_EAX == (short *)(undefined1 *)0x0047a684);\n  iVar2 = 0;",
  "  _DAT_0064342c = 0;\n  _DAT_006443d0 = (ushort)(in_EAX == (short *)(undefined1 *)0x0047a684);\n  E2R_RequesterProbeFeedPendingMouse(E2R_WORD_AT(DAT_0047a45e,2));\n  iVar2 = 0;"
);
source = source.replace(
  "  param_2[0xd] = sVar6 + param_2[1];\n  param_2[0xe] = param_2[0xd] + param_2[3];\n  param_2[0xc] = param_2[0xb] + param_2[2];\n  iVar3 = DAT_0047a279 >> 0x18;",
  "  param_2[0xd] = sVar6 + param_2[1];\n  param_2[0xe] = param_2[0xd] + param_2[3];\n  param_2[0xc] = param_2[0xb] + param_2[2];\n  E2R_RequesterProbeLogItemLayout(E2R_WORD_AT(DAT_0047a45e,2),(uintptr_t)param_2);\n  iVar3 = DAT_0047a279 >> 0x18;"
);
source = source.replace(
  "        FUN_0043d8ec();\n        FUN_0043d934();\n        FUN_0043d9a0();\n        FUN_0043da04();\n        FUN_0043da80();\n        uVar13 = FUN_0043b384(extraout_ECX_04,extraout_EDX_00);",
  "        FUN_0043d8ec();\n        FUN_0043d934();\n        FUN_0043d9a0();\n        FUN_0043da04();\n        FUN_0043da80();\n        E2R_InitRequesterSettingsItems();\n        uVar13 = FUN_0043b384(0x0047a668,extraout_EDX_00);"
);
source = source.replace(
  "\n\n\n/* 0043af98 */",
  "\n\nint E2R_RequesterHandleMouseClick(uintptr_t x, uintptr_t y)\n{\n  short *record;\n  short *item;\n  uintptr_t action;\n  ushort requester_id;\n  uint guard;\n\n  requester_id = E2R_WORD_AT(DAT_0047a45e,2);\n  if (_DAT_00643650 == 0 ||\n      (requester_id != 0x28 && requester_id != 0x29 &&\n       requester_id != 0x2a && requester_id != 0x31)) {\n    return 0;\n  }\n  record = (short *)FUN_0043aeac();\n  if (record == (short *)0x0 || (uintptr_t)record >= 0x70000000u ||\n      IsBadReadPtr(record,0x20)) {\n    return 0;\n  }\n  item = *(short **)(record + 6);\n  for (guard = 0; item != (short *)0x0 && guard < 0x40; guard = guard + 1) {\n    if ((uintptr_t)item >= 0x70000000u || IsBadReadPtr(item,0x20)) {\n      return 0;\n    }\n    if ((short)x >= item[0xb] && (short)x < item[0xc] &&\n        (short)y >= item[0xd] && (short)y < item[0xe]) {\n      action = *(uintptr_t *)(item + 6);\n      if (action == 0) {\n        return 0;\n      }\n      _DAT_00643430 = item;\n      E2R_requester_probe_action_count++;\n      E2R_requester_probe_last_action = action;\n      return E2R_InvokeRequesterAction(action);\n    }\n    item = *(short **)(item + 9);\n  }\n  return 0;\n}\n\n\n/* 0043af98 */"
);
source = source.replace(
  "  if (_DAT_00643650 == 0 ||\n      (requester_id != 0x28 && requester_id != 0x29 &&\n       requester_id != 0x2a && requester_id != 0x31)) {\n    return 0;\n  }",
  "  if (_DAT_00643650 == 0 ||\n      (requester_id != 0x14 && requester_id != 0x28 &&\n       requester_id != 0x29 && requester_id != 0x2a && requester_id != 0x31)) {\n    if (E2R_MenuDiagEnabled()) {\n      fprintf(stderr,\n              \"menu click: phase=requester-direct outcome=ignored x=%ld y=%ld \"\n              \"state=%lu requester=0x%x selected=0x%lx\\n\",\n              (long)x,(long)y,(unsigned long)_DAT_00643650,\n              (unsigned int)requester_id,(unsigned long)_DAT_00643430);\n    }\n    return 0;\n  }"
);
source = source.replace(
  "  if (record == (short *)0x0 || (uintptr_t)record >= 0x70000000u ||\n      IsBadReadPtr(record,0x20)) {\n    return 0;\n  }",
  "  if (record == (short *)0x0 || (uintptr_t)record >= 0x70000000u ||\n      IsBadReadPtr(record,0x20)) {\n    if (E2R_MenuDiagEnabled()) {\n      fprintf(stderr,\n              \"menu click: phase=requester-direct outcome=bad-record x=%ld y=%ld \"\n              \"state=%lu requester=0x%x record=0x%lx\\n\",\n              (long)x,(long)y,(unsigned long)_DAT_00643650,\n              (unsigned int)requester_id,(unsigned long)record);\n    }\n    return 0;\n  }"
);
source = source.replace(
  "    if ((uintptr_t)item >= 0x70000000u || IsBadReadPtr(item,0x20)) {\n      return 0;\n    }",
  "    if ((uintptr_t)item >= 0x70000000u || IsBadReadPtr(item,0x20)) {\n      if (E2R_MenuDiagEnabled()) {\n        fprintf(stderr,\n                \"menu click: phase=requester-direct outcome=bad-item x=%ld y=%ld \"\n                \"state=%lu requester=0x%x record=0x%lx item=0x%lx guard=%lu\\n\",\n                (long)x,(long)y,(unsigned long)_DAT_00643650,\n                (unsigned int)requester_id,(unsigned long)record,\n                (unsigned long)item,(unsigned long)guard);\n      }\n      return 0;\n    }"
);
source = source.replace(
  "      if (action == 0) {\n        return 0;\n      }\n      _DAT_00643430 = item;",
  "      if (action == 0) {\n        if (E2R_MenuDiagEnabled()) {\n          fprintf(stderr,\n                  \"menu click: phase=requester-direct outcome=no-action x=%ld y=%ld \"\n                  \"state=%lu requester=0x%x item=0x%lx bounds=[%d,%d..%d,%d]\\n\",\n                  (long)x,(long)y,(unsigned long)_DAT_00643650,\n                  (unsigned int)requester_id,(unsigned long)item,\n                  (int)item[0xb],(int)item[0xd],(int)item[0xc],(int)item[0xe]);\n        }\n        return 0;\n      }\n      if (E2R_MenuDiagEnabled()) {\n        fprintf(stderr,\n                \"menu click: phase=requester-direct outcome=hit x=%ld y=%ld \"\n                \"state=%lu requester=0x%x item=0x%lx bounds=[%d,%d..%d,%d] \"\n                \"action=0x%lx action_name=%s\\n\",\n                (long)x,(long)y,(unsigned long)_DAT_00643650,\n                (unsigned int)requester_id,(unsigned long)item,\n                (int)item[0xb],(int)item[0xd],(int)item[0xc],(int)item[0xe],\n                (unsigned long)action,E2R_RequesterActionName(action));\n      }\n      _DAT_00643430 = item;"
);
source = source.replace(
  "      _DAT_00643430 = item;\n      E2R_requester_probe_action_count++;\n      E2R_requester_probe_last_action = action;\n      return E2R_InvokeRequesterAction(action);",
  "      _DAT_00643430 = item;\n      E2R_requester_probe_action_count++;\n      E2R_requester_probe_last_action = action;\n      if ((requester_id == 0x29 && action == (uintptr_t)&LAB_0043fadc) ||\n          (requester_id == 0x2a && action == (uintptr_t)&LAB_0043fb58)) {\n        _DAT_0064353c = (int)(ushort)item[8] & 0xff;\n        E2R_RedrawActiveRequesterItem();\n        return 1;\n      }\n      if (requester_id == 0x28) {\n        if (action == (uintptr_t)&LAB_0043d47c &&\n            !(DAT_0047a76c == 0 && _DAT_0073cc3c != 0 &&\n              E2R_IsReadableCurrentPointer(DAT_0047a470))) {\n          E2R_InvokeRequesterAction(action);\n          return 1;\n        }\n        return 0;\n      }\n      return E2R_InvokeRequesterAction(action);"
);
source = source.replace(
  "  return 0;\n}\n\n\n/* 0043af98 */",
  "  if (E2R_MenuDiagEnabled()) {\n    fprintf(stderr,\n            \"menu click: phase=requester-direct outcome=miss x=%ld y=%ld \"\n            \"state=%lu requester=0x%x record=0x%lx items_checked=%lu selected=0x%lx\\n\",\n            (long)x,(long)y,(unsigned long)_DAT_00643650,\n            (unsigned int)requester_id,(unsigned long)record,(unsigned long)guard,\n            (unsigned long)_DAT_00643430);\n  }\n  return 0;\n}\n\n\n/* 0043af98 */"
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
source = source.replace(
  "  } while (local_3c < 0x80);\n  if (DAT_0047ab10 == 0) {",
  "  } while (local_3c < 0x80);\n  if (DAT_0047ab10 != 0) {\n    iVar14 = E2R_ReadHostedVisibilityFromArchive();\n    return CONCAT44(param_2,iVar14);\n  }\n  if (DAT_0047ab10 == 0) {"
);
source = source.replace(
  /void __fastcall FUN_0044d34c\(undefined4 param_1\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0044d3e8 \*\//,
  "void __fastcall FUN_0044d34c(undefined4 param_1)\n\n{\n  int actor;\n  int actor_id;\n  int cell;\n  int link;\n  short visible;\n  undefined8 result;\n\n  actor_id = (int)(short)(uintptr_t)param_1;\n  if (actor_id < 0 || 5000 <= actor_id) {\n    return;\n  }\n  actor = *(int *)((undefined1 *)0x00630b60 + actor_id * 4);\n  if (actor == 0 || (uintptr_t)actor < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x188)) {\n    return;\n  }\n  if (*(int *)(actor + 0xf2) != 0 || actor == DAT_0047a470) {\n    return;\n  }\n  link = *(int *)(actor + 0xa6);\n  if (link != 0 && ((uintptr_t)link < 0x10000u || IsBadReadPtr((void *)(uintptr_t)link,0x10) ||\n                    ((*(byte *)(link + 0xc) & 2) != 0))) {\n    return;\n  }\n  result = FUN_004488a4((undefined4)(uintptr_t)(actor + 0x84),actor);\n  if ((int)result < 0) {\n    visible = 0;\n  }\n  else {\n    cell = (int)result;\n    visible = (*(ushort *)((undefined1 *)0x0068cd6a + cell * 0xc) >> 8 & 0x40) << 8;\n  }\n  if (visible == 0) {\n    *(byte *)(actor + 2) = *(byte *)(actor + 2) & 0xf7;\n    actor_id = (int)*(short *)(actor + 0);\n    if (0 <= actor_id && actor_id < 5000 &&\n        (((undefined1 *)0x0064a178)[actor_id * 2] & 8) == 0 &&\n        *(short *)(actor + 0x82) != 5) {\n      FUN_0044d3e8((undefined4)(uintptr_t)actor);\n    }\n  }\n  return;\n}\n\n\n\n/* 0044d3e8 */"
);
source = source.replace(
  /void FUN_0044d3e8\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0044d4b4 \*\//,
  "void __fastcall FUN_0044d3e8(undefined4 param_1)\n\n{\n  int actor;\n  int actor_id;\n  int child;\n  int link;\n  int rep;\n  undefined2 rep_id;\n\n  actor = (int)(uintptr_t)param_1;\n  if (actor == 0 || (uintptr_t)actor < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x188)) {\n    return;\n  }\n  actor_id = (int)*(short *)actor;\n  if (actor_id < 0 || 5000 <= actor_id) {\n    return;\n  }\n  FUN_00422aa0((undefined4)(uintptr_t)(actor_id * 6 + 0x669708),(undefined2 *)(actor + 0x84));\n  FUN_00422aa0((undefined4)(uintptr_t)(actor_id * 6 + 0x658980),(undefined2 *)(actor + 0x90));\n  *(short *)(actor_id * 2 + 0x671fc0) = *(short *)(actor + 0x122);\n  *(short *)(actor_id * 2 + 0x647a68) = *(short *)(actor + 0xec);\n  *(char *)(actor_id + 0x64c950) = *(char *)(actor + 0x184);\n  rep = *(int *)(actor + 0xf2);\n  if (rep == 0 || (uintptr_t)rep < 0x10000u || IsBadReadPtr((void *)(uintptr_t)rep,0x26)) {\n    rep_id = 0xffff;\n    *(undefined2 *)(actor_id * 2 + 0x6648e8) = 0xffff;\n  }\n  else {\n    *(undefined2 *)(actor_id * 2 + 0x6648e8) = *(undefined2 *)rep;\n    if (*(int *)(rep + 0x22) == 0 || IsBadReadPtr((void *)(uintptr_t)*(int *)(rep + 0x22),2)) {\n      rep_id = 0xffff;\n    }\n    else {\n      rep_id = *(undefined2 *)(uintptr_t)*(int *)(rep + 0x22);\n    }\n  }\n  *(undefined2 *)(actor_id * 2 + 0x65feb0) = rep_id;\n  *(byte *)(actor + 2) = *(byte *)(actor + 2) & 0xf7;\n  E2R_actor_calc_context = actor;\n  FUN_00426ca4();\n  E2R_actor_calc_context = 0;\n  for (link = *(int *)(actor + 0x1e); link != 0; link = *(int *)(link + 0x4c)) {\n    if ((uintptr_t)link < 0x10000u || IsBadReadPtr((void *)(uintptr_t)link,0x140)) {\n      break;\n    }\n    child = *(int *)(link + 0x13a);\n    if (child != 0) {\n      FUN_0044d3e8((undefined4)(uintptr_t)child);\n    }\n  }\n  return;\n}\n\n\n\n/* 0044d4b4 */"
);
source = source.replace(
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar1) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(uVar3);",
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar1) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(iVar2);"
);
source = source.replace(
  "      if ((*(ushort *)(&DAT_0064a178 + iVar1) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(uVar3);",
  "      if ((*(ushort *)(&DAT_0064a178 + iVar1) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(iVar2);"
);
source = source.replace(
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(uVar3);",
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(iVar1);"
);
source = source.replace(
  "      if ((*(ushort *)(&DAT_0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(uVar3);",
  "      if ((*(ushort *)(&DAT_0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(iVar1);"
);
source = source.replace(
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(uVar3);",
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(iVar1);"
);
source = source.replace(
  "      if ((*(ushort *)(&DAT_0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(uVar3);",
  "      if ((*(ushort *)(&DAT_0064a178 + iVar4) & (ushort)uVar3) != 0) {\n        FUN_0044d34c(iVar1);"
);
source = source.replace(
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar6) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(uVar3);",
  "      if ((*(ushort *)((undefined1 *)0x0064a178 + iVar6) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(iVar4);"
);
source = source.replace(
  "      if ((*(ushort *)(&DAT_0064a178 + iVar6) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(uVar3);",
  "      if ((*(ushort *)(&DAT_0064a178 + iVar6) & (ushort)uVar3) != 0) {\n        FUN_0044d4b4(iVar4);"
);
source = source.replace(
  "        FUN_0044d34c(iVar2);\n        uVar3 = extraout_ECX_02;\n        iVar2 = extraout_EDX_03;",
  "        FUN_0044d34c(iVar2);"
);
source = source.replace(
  "        FUN_0044d4b4(iVar1);\n        uVar3 = extraout_ECX_03;\n        iVar1 = extraout_EDX_04;",
  "        FUN_0044d4b4(iVar1);"
);
source = source.replace(
  "        FUN_0044d34c(iVar1);\n        uVar3 = extraout_ECX_01;\n        iVar1 = extraout_EDX_02;",
  "        FUN_0044d34c(iVar1);"
);
source = source.replace(
  "        FUN_0044d4b4(iVar4);\n        uVar3 = extraout_ECX_02;\n        iVar4 = extraout_EDX_03;",
  "        FUN_0044d4b4(iVar4);"
);
source = source.replace(
  /(void __fastcall FUN_0044d4b4\(undefined4 param_1\)[\s\S]*?\r?\n  undefined8 uVar4;\r?\n\s*)iVar3 = \*\(int \*\)\(\(undefined1 \*\)0x00630b60 \+ in_AX \* 4\);/,
  "$1in_AX = (short)(uintptr_t)param_1;\n  iVar3 = *(int *)((undefined1 *)0x00630b60 + in_AX * 4);"
);
source = source.replace(
  /(void __fastcall FUN_0044d4b4\(undefined4 param_1\)[\s\S]*?\r?\n  undefined8 uVar4;\r?\n\s*)iVar3 = \*\(int \*\)\(&DAT_00630b60 \+ in_AX \* 4\);/,
  "$1in_AX = (short)(uintptr_t)param_1;\n  iVar3 = *(int *)(&DAT_00630b60 + in_AX * 4);"
);
source = source.replace(
  /void __fastcall FUN_0044d4b4\(undefined4 param_1\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0044d608 \*\//,
  "void __fastcall FUN_0044d4b4(undefined4 param_1)\n\n{\n  int actor;\n  int actor_id;\n  int cell;\n  int child;\n  int link;\n  int link_flags;\n  short visible;\n  undefined8 result;\n\n  actor_id = (int)(short)(uintptr_t)param_1;\n  if (actor_id < 0 || 5000 <= actor_id) {\n    return;\n  }\n  actor = *(int *)((undefined1 *)0x00630b60 + actor_id * 4);\n  if (actor == 0 || (uintptr_t)actor < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x188)) {\n    if ((*(int *)(actor_id * 2 + 0x666ff6) >> 0x10 & 0xc000U) == 0xc000) {\n      result = FUN_004488a4(param_1,(undefined4)actor_id);\n      visible = (int)result < 0 ? 0 :\n        ((*(ushort *)((undefined1 *)0x0068cd6a + (int)result * 0xc) >> 8 & 0x40) << 8);\n      if (visible != 0 && *(short *)(actor_id * 2 + 0x65feb0) < 0) {\n        FUN_0044d634();\n      }\n    }\n    return;\n  }\n  if (*(int *)(actor + 0xf2) != 0) {\n    return;\n  }\n  link = *(int *)(actor + 0xa6);\n  link_flags = 0;\n  if (link != 0 && 0x10000u <= (uintptr_t)link &&\n      (uintptr_t)link < 0x70000000u && !IsBadReadPtr((void *)(uintptr_t)link,0x10)) {\n    link_flags = *(byte *)(link + 0xc) & 2;\n  }\n  if (actor != DAT_0047a470 && link_flags == 0) {\n    result = FUN_004488a4((undefined4)(uintptr_t)(actor + 0x84),(undefined4)actor);\n    visible = (int)result < 0 ? 0 :\n      ((*(ushort *)((undefined1 *)0x0068cd6a + (int)result * 0xc) >> 8 & 0x40) << 8);\n    if (visible == 0) {\n      return;\n    }\n  }\n  *(byte *)(actor + 2) = *(byte *)(actor + 2) | 8;\n  E2R_actor_calc_context = actor;\n  FUN_00426c3c();\n  E2R_actor_calc_context = 0;\n  for (link = *(int *)(actor + 0x1e); link != 0; link = *(int *)(link + 0x4c)) {\n    if ((uintptr_t)link < 0x10000u || IsBadReadPtr((void *)(uintptr_t)link,0x140)) {\n      break;\n    }\n    child = *(int *)(link + 0x13a);\n    if (child != 0) {\n      FUN_0044d608(0,(undefined4)(uintptr_t)link);\n    }\n  }\n  return;\n}\n\n\n\n/* 0044d608 */"
);
source = source.replace(
  "      result = FUN_004488a4(param_1,(undefined4)actor_id);",
  "      result = FUN_004488a4((undefined4)(uintptr_t)(actor_id * 6 + 0x669708),\n" +
  "                            (undefined4)actor_id);"
);
source = source.replace(
  /void __fastcall FUN_0044d608\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0044d634 \*\//,
  "void __fastcall FUN_0044d608(undefined4 param_1,undefined4 param_2)\n\n{\n  int actor;\n  int child;\n  int link;\n\n  (void)param_1;\n  link = (int)(uintptr_t)param_2;\n  actor = link;\n  if (0x10000u <= (uintptr_t)link && (uintptr_t)link < 0x70000000u &&\n      !IsBadReadPtr((void *)(uintptr_t)link,0x140) && *(int *)(link + 0x13a) != 0) {\n    actor = *(int *)(link + 0x13a);\n  }\n  if (actor == 0 || (uintptr_t)actor < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x188)) {\n    return;\n  }\n  E2R_actor_calc_context = actor;\n  FUN_00426c3c();\n  E2R_actor_calc_context = 0;\n  for (link = *(int *)(actor + 0x1e); link != 0; link = *(int *)(link + 0x4c)) {\n    if ((uintptr_t)link < 0x10000u || IsBadReadPtr((void *)(uintptr_t)link,0x140)) {\n      break;\n    }\n    child = *(int *)(link + 0x13a);\n    if (child != 0) {\n      FUN_0044d608(0,(undefined4)(uintptr_t)link);\n    }\n  }\n  return;\n}\n\n\n\n/* 0044d634 */"
);
source = source.replace(/(undefined4 __fastcall FUN_0041af88\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  int iVar2;\r?\n\s*)iVar2 = 0;/, "$1in_EAX = (char *)(uintptr_t)param_1;\n  if ((uintptr_t)in_EAX < 0x10000u || (uintptr_t)in_EAX >= 0x01000000u ||\n      IsBadReadPtr(in_EAX,0x300)) return 0;\n  iVar2 = 0;");
source = source.replace(/&DAT_006366c0/g, "&_DAT_006366c0");
source = source.replace(
  /(undefined4 __fastcall FUN_00418a04\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  int iVar1;\r?\n\s*)int extraout_ECX;/,
  "$1uintptr_t cached;\n  int extraout_ECX;\n  size_t span;"
);
source = source.replace(/(undefined4 __fastcall FUN_00418a04\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  int extraout_ECX;\r?\n\s*)if \(1 < in_EAX\) \{/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (1 < in_EAX) {");
source = source.replace(
  "  size_t span;\n\n  if (1 < in_EAX) {",
  "  size_t span;\n\n  in_EAX = (int)(uintptr_t)param_1;\n  if (1 < in_EAX) {"
);
source = source.replace(
  "  if (1 < in_EAX) {\n    *param_2 = _DAT_006401ec;\n    return *(undefined4 *)(&DAT_00636150 + in_EAX * 4);\n  }",
  "  if (1 < in_EAX) {\n    *param_2 = _DAT_006401ec;\n    if (in_EAX == 2) {\n      cached = _DAT_00636158;\n    }\n    else if (in_EAX == 3) {\n      cached = _DAT_0063615c;\n    }\n    else {\n      cached = *(undefined4 *)((undefined1 *)0x00636150 + in_EAX * 4);\n    }\n    if (cached < 0x10000u) {\n      return 0;\n    }\n    if (_DAT_006401ec > 0 && _DAT_006401d4 > 0 &&\n        _DAT_006401ec <= 0x1000 && _DAT_006401d4 <= 0x1000) {\n      span = ((size_t)_DAT_006401d4 - 1u) * (size_t)_DAT_006401ec +\n             (size_t)_DAT_006401ec;\n      if (E2R_IsBadWritePtr((void *)cached,span)) {\n        return 0;\n      }\n    }\n    else if (E2R_IsBadWritePtr((void *)cached,1)) {\n      return 0;\n    }\n    return (undefined4)cached;\n  }"
);
source = source.replace(
  "  size_t span;\n\n  if (1 < in_EAX) {",
  "  size_t span;\n\n  in_EAX = (int)(uintptr_t)param_1;\n  if (1 < in_EAX) {"
);
source = source.replace(
  /void __fastcall FUN_0041ad54\(undefined4 param_1,int param_2,int param_3\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0041af88 \*\//,
  "void __fastcall FUN_0041ad54(undefined4 param_1,int param_2,int param_3)\n\n{\n  int x;\n  int y;\n  int x2;\n  int y1;\n  int pitch;\n  int base;\n  int surface;\n  undefined1 color;\n  undefined1 *row;\n  \n  x2 = (int)(uintptr_t)param_1;\n  y1 = 0;\n  surface = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (param_2 < 0) {\n    param_2 = 0;\n  }\n  if (x2 >= _DAT_006401ec) {\n    x2 = _DAT_006401ec + -1;\n  }\n  if (param_3 >= _DAT_006401d4) {\n    param_3 = _DAT_006401d4 + -1;\n  }\n  if (x2 < param_2 || param_3 < y1) {\n    return;\n  }\n  base = FUN_00418a04((undefined4)(uintptr_t)surface,&pitch);\n  if (base == 0 || pitch <= 0 || (uintptr_t)base >= 0x70000000u ||\n      _DAT_006401ec <= 0 || 0x1000 < _DAT_006401ec ||\n      _DAT_006401d4 <= 0 || 0x1000 < _DAT_006401d4) {\n    return;\n  }\n  color = ((undefined1 *)0x006366dc)[surface * 2];\n  for (y = y1; y <= param_3; y = y + 1) {\n    row = (undefined1 *)(base + y * pitch + param_2);\n    for (x = param_2; x <= x2; x = x + 1) {\n      *row = color;\n      row = row + 1;\n    }\n  }\n  return;\n}\n\n\n\n/* 0041af88 */"
);
source = source.replace(
  "  undefined1 color;\n  undefined1 *row;\n  \n  x2 = (int)(uintptr_t)param_1;",
  "  undefined1 color;\n  undefined1 *row;\n  size_t write_span;\n  \n  x2 = (int)(uintptr_t)param_1;"
);
source = source.replace(
  "  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (param_2 < 0) {",
  "  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (surface < 0 || 3 < surface) {\n    return;\n  }\n  if (param_2 < 0) {"
);
source = source.replace(
  "  if (base == 0 || pitch <= 0 || (uintptr_t)base >= 0x70000000u ||\n      _DAT_006401ec <= 0 || 0x1000 < _DAT_006401ec ||\n      _DAT_006401d4 <= 0 || 0x1000 < _DAT_006401d4) {\n    return;\n  }\n  color = ((undefined1 *)0x006366dc)[surface * 2];",
  "  if ((uintptr_t)base < 0x10000u || pitch < _DAT_006401ec ||\n      (uintptr_t)base >= 0x70000000u || _DAT_006401ec <= 0 ||\n      0x1000 < _DAT_006401ec || _DAT_006401d4 <= 0 ||\n      0x1000 < _DAT_006401d4) {\n    return;\n  }\n  write_span = (size_t)param_3 * (size_t)pitch + (size_t)x2 + 1;\n  if (E2R_IsBadWritePtr((void *)(uintptr_t)base,write_span)) {\n    return;\n  }\n  color = ((undefined1 *)0x006366dc)[surface * 2];"
);
source = source.replace(
  /(void __fastcall FUN_0041ad54\(undefined4 param_1,int param_2,int param_3\)[\s\S]*?\r?\n  int surface;\r?\n\s*)undefined1 color;/,
  "$1int style_surface;\n  undefined1 color;"
);
source = source.replace(
  /(void __fastcall FUN_0041ad54\(undefined4 param_1,int param_2,int param_3\)[\s\S]*?\r?\n  x2 = \(int\)\(uintptr_t\)param_1;\r?\n  y1 = 0;\r?\n\s*)surface = DAT_0047a279 >> 0x18;/,
  "$1style_surface = DAT_0047a279 >> 0x18;\n  surface = style_surface;"
);
source = source.replace(
  /(void __fastcall FUN_0041ad54\(undefined4 param_1,int param_2,int param_3\)[\s\S]*?\r?\n  if \(\(uintptr_t\)base < 0x10000u \|\| pitch < _DAT_006401ec \|\|\r?\n\s*)\(uintptr_t\)base >= 0x70000000u \|\| /,
  "$1"
);
source = source.replace(
  /(void __fastcall FUN_0041ad54\(undefined4 param_1,int param_2,int param_3\)[\s\S]*?\r?\n  \}\r?\n\s*)color = \(\(undefined1 \*\)0x006366dc\)\[surface \* 2\];/,
  "$1color = ((undefined1 *)0x006366dc)[style_surface * 2];"
);
source = source.replace(
  /\/\* 0041b078 \*\/[\s\S]*?\r?\n\s*\r?\n\/\* 0041b920 \*\//,
  "/* 0041b078 */\n\nvoid __fastcall FUN_0041b078(undefined4 param_1,undefined2 param_2)\n\n{\n  int surface;\n  \n  surface = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (surface < 0 || 3 < surface) {\n    return;\n  }\n  *(undefined2 *)(0x006366c4 + surface * 2) = (undefined2)(uintptr_t)param_1;\n  *(undefined2 *)(0x006366d0 + surface * 2) = param_2;\n  return;\n}\n\n\n\n/* 0041b34c */\n\nvoid __fastcall FUN_0041b34c(undefined4 param_1,int param_2)\n\n{\n  int base;\n  int color_index;\n  int dx;\n  int dy;\n  int e2;\n  int err;\n  int pitch;\n  int sx;\n  int sy;\n  int surface;\n  int x0;\n  int x1;\n  int y0;\n  int y1;\n  undefined1 *pixel;\n  undefined1 color;\n  \n  surface = DAT_0047a279 >> 0x18;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (surface < 0 || 3 < surface) {\n    return;\n  }\n  x0 = (short)*(undefined2 *)(0x006366c4 + surface * 2);\n  y0 = (short)*(undefined2 *)(0x006366d0 + surface * 2);\n  x1 = (short)(uintptr_t)param_1;\n  y1 = (short)param_2;\n  *(undefined2 *)(0x006366c4 + surface * 2) = (undefined2)x1;\n  *(undefined2 *)(0x006366d0 + surface * 2) = (undefined2)y1;\n  base = FUN_00418a04((undefined4)(uintptr_t)surface,&pitch);\n  if (base == 0 || pitch <= 0 || _DAT_006401ec <= 0 || _DAT_006401d4 <= 0) {\n    return;\n  }\n  dx = x1 - x0;\n  if (dx < 0) {\n    dx = -dx;\n  }\n  dy = y1 - y0;\n  if (dy < 0) {\n    dy = -dy;\n  }\n  sx = x0 < x1 ? 1 : -1;\n  sy = y0 < y1 ? 1 : -1;\n  err = dx - dy;\n  color_index = surface * 2;\n  color = ((undefined1 *)0x006366dc)[color_index];\n  while (1) {\n    if (0 <= x0 && x0 < _DAT_006401ec && 0 <= y0 && y0 < _DAT_006401d4) {\n      pixel = (undefined1 *)(base + y0 * pitch + x0);\n      if (*(short *)(0x006366a8 + color_index) == 0) {\n        *pixel = *pixel ^ color;\n      }\n      else {\n        *pixel = color;\n      }\n    }\n    if (x0 == x1 && y0 == y1) {\n      break;\n    }\n    e2 = err * 2;\n    if (-dy < e2) {\n      err = err - dy;\n      x0 = x0 + sx;\n    }\n    if (e2 < dx) {\n      err = err + dx;\n      y0 = y0 + sy;\n    }\n  }\n  return;\n}\n\n\n\n/* 0041b540 */\n\nvoid __fastcall FUN_0041b540(undefined4 param_1,int param_2)\n\n{\n  FUN_0041b34c(param_1,param_2);\n  return;\n}\n\n\n\n/* 0041b920 */"
);
source = source.replace(
  "  undefined1 *pixel;\n  undefined1 color;\n  \n  surface = DAT_0047a279 >> 0x18;",
  "  undefined1 *pixel;\n  undefined1 color;\n  size_t write_span;\n  \n  surface = DAT_0047a279 >> 0x18;"
);
source = source.replace(
  "  if (base == 0 || pitch <= 0 || _DAT_006401ec <= 0 || _DAT_006401d4 <= 0) {\n    return;\n  }\n  dx = x1 - x0;",
  "  if ((uintptr_t)base < 0x10000u || pitch < _DAT_006401ec ||\n      (uintptr_t)base >= 0x70000000u || _DAT_006401ec <= 0 ||\n      0x1000 < _DAT_006401ec || _DAT_006401d4 <= 0 ||\n      0x1000 < _DAT_006401d4) {\n    return;\n  }\n  write_span = ((size_t)_DAT_006401d4 - 1u) * (size_t)pitch +\n               (size_t)_DAT_006401ec;\n  if (E2R_IsBadWritePtr((void *)(uintptr_t)base,write_span)) {\n    return;\n  }\n  dx = x1 - x0;"
);
source = source.replace(
  "  else {\n    FUN_00419af4(1,param_2,0,0);\n  }\n  return;\n}\n\n\n\n/* 00418a04 */",
  "  else {\n    E2R_DrawHostedText(param_2);\n  }\n  return;\n}\n\n\n\n/* 00418a04 */"
);
source = source.replace(
  "    FUN_0041b078(iVar3,(short)iVar3);\n    FUN_00418770(extraout_ECX_05,*(byte **)(param_2 + 4));",
  "    FUN_0041b078(iVar3,(short)(param_2[0xd] + 1));\n    FUN_00418770(extraout_ECX_05,*(byte **)(param_2 + 4));"
);
source = source.replace(
  "      iVar3 = extraout_ECX_06 + (uint)uVar2;\n      FUN_0041b078(iVar3,(short)iVar3);",
  "      iVar3 = extraout_ECX_06 + (uint)uVar2;\n      FUN_0041b078(iVar3,(short)(param_2[0xd] + 1));"
);
source = source.replace(
  "  for (psVar8 = *(short **)(in_EAX + 6); psVar8 != (short *)0x0; psVar8 = *(short **)(psVar8 + 9)) {\n    FUN_0043b9bc(uVar4,psVar8);\n    uVar4 = extraout_ECX_08;\n    uVar7 = extraout_EDX_01;\n    uVar5 = extraout_var_01;\n  }\n  uVar11 = CONCAT44(uVar7,CONCAT22(uVar5,E2R_WORD_AT(DAT_0047a45e,2)));",
  "  for (psVar8 = *(short **)(in_EAX + 6); psVar8 != (short *)0x0; psVar8 = *(short **)(psVar8 + 9)) {\n    FUN_0043b9bc(uVar4,psVar8);\n    uVar4 = extraout_ECX_08;\n    uVar7 = extraout_EDX_01;\n    uVar5 = extraout_var_01;\n  }\n  E2R_DrawHostedRequesterLabels(in_EAX);\n  uVar11 = CONCAT44(uVar7,CONCAT22(uVar5,E2R_WORD_AT(DAT_0047a45e,2)));"
);
source = source.replace(
  /(void __fastcall FUN_0041b34c\(undefined4 param_1,int param_2\)[\s\S]*?\r?\n  int surface;\r?\n\s*)int x0;/,
  "$1int style_surface;\n  int x0;"
);
source = source.replace(
  /(void __fastcall FUN_0041b34c\(undefined4 param_1,int param_2\)[\s\S]*?\r?\n  size_t write_span;\r?\n\s*)surface = DAT_0047a279 >> 0x18;/,
  "$1style_surface = DAT_0047a279 >> 0x18;\n  surface = style_surface;"
);
source = source.replace(
  /(void __fastcall FUN_0041b34c\(undefined4 param_1,int param_2\)[\s\S]*?\r?\n  if \(\(uintptr_t\)base < 0x10000u \|\| pitch < _DAT_006401ec \|\|\r?\n\s*)\(uintptr_t\)base >= 0x70000000u \|\| /,
  "$1"
);
source = source.replace(
  /(void __fastcall FUN_0041b34c\(undefined4 param_1,int param_2\)[\s\S]*?\r?\n  err = dx - dy;\r?\n\s*)color_index = surface \* 2;/,
  "$1color_index = style_surface * 2;"
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
  /(int __fastcall FUN_00419af4\(int param_1,byte \*param_2,undefined4 param_3,int param_4\)[\s\S]*?\r?\n  int local_7c;\r?\n\s*)uint local_78;/,
  "$1int style_index;\n  int style_surface;\n  uint local_78;"
);
source = source.replace(
  /(int __fastcall FUN_00419af4\(int param_1,byte \*param_2,undefined4 param_3,int param_4\)[\s\S]*?\r?\n  undefined1 local_10;\r?\n\s*)in_EAX = DAT_0047a279 >> 0x18;/,
  "$1style_surface = DAT_0047a279 >> 0x18;\n  in_EAX = style_surface;"
);
source = source.replace(
  /(int __fastcall FUN_00419af4\(int param_1,byte \*param_2,undefined4 param_3,int param_4\)[\s\S]*?\r?\n    if \(local_80 == 0 \|\| local_84 <= 0\) \{\r?\n      return 0;\r?\n    \}\r?\n\s*)local_14 = \(\(undefined1 \*\)0x006366dc\)\[in_EAX \* 2\];\r?\n    local_10 = \*\(undefined1 \*\)\(in_EAX \* 2 \+ 0x6366e8\);/,
  "$1style_index = style_surface * 2;\n    local_14 = ((undefined1 *)0x006366dc)[style_index];\n    local_10 = *(undefined1 *)(style_index + 0x6366e8);"
);
source = source.replace(
  /  in_EAX = DAT_0047a279 >> 0x18;\r?\n  if \(DAT_0047a43c != 0\) \{/,
  "  style_surface = DAT_0047a279 >> 0x18;\n  in_EAX = style_surface;\n  if (DAT_0047a43c != 0) {"
);
source = source.replace(
  /    local_14 = \(\(undefined1 \*\)0x006366dc\)\[in_EAX \* 2\];\r?\n    local_10 = \*\(undefined1 \*\)\(in_EAX \* 2 \+ 0x6366e8\);/,
  "    style_index = style_surface * 2;\n    local_14 = ((undefined1 *)0x006366dc)[style_index];\n    local_10 = *(undefined1 *)(style_index + 0x6366e8);"
);
source = source.replace(/\*\(short \*\)\(local_7c \+ 0x6366a8\)/g,
                        "*(short *)(style_index + 0x6366a8)");
source = source.replace(
  /\/\* 00453920 \*\/\s*\r?\n\s*\/\* WARNING:[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\s*\/\* 004544a4 \*\//,
  "/* 00453920 */\n\nundefined8 __fastcall FUN_00453920(undefined4 param_1,char *param_2)\n\n{\n  (void)param_1;\n  (void)param_2;\n  return 0;\n}\n\n\n\n/* 004544a4 */"
);
source = source.replace(
  /\/\* 00455e84 \*\/\s*\r?\n\s*void FUN_00455e84\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\s*\/\* 00455fe8 \*\//,
  "/* 00455e84 */\n\nvoid FUN_00455e84(void)\n\n{\n  if (DAT_0047a43c == 0) {\n    E2R_ClearHudIconName((char *)0x00475ef8);\n    E2R_ClearHudIconName((char *)0x00475f00);\n    E2R_ClearHudIconName((char *)0x00475f08);\n    E2R_ClearHudIconName((char *)0x00475f2c);\n    E2R_ClearHudIconName((char *)0x00475f20);\n    E2R_ClearHudIconName((char *)0x00475f6c);\n    E2R_ClearHudIconName((char *)0x00475f64);\n    E2R_ClearHudIconNameRange(0x0047ab71,0x0047ab9e);\n    E2R_ClearHudIconName((char *)0x00475f5c);\n    E2R_ClearHudIconName((char *)0x00475e4c);\n    E2R_ClearHudIconNameRange(0x0047ac40,0x0047ac76);\n    E2R_ClearHudIconNameRange(0x0047ac76,0x0047acac);\n    E2R_ClearHudIconNameRange(0x0047acac,0x0047ace2);\n  }\n  else {\n    E2R_ClearHudIconName((char *)0x00475ee0);\n    E2R_ClearHudIconName((char *)0x00475ee8);\n    E2R_ClearHudIconName((char *)0x00475ef0);\n    E2R_ClearHudIconName((char *)0x00475f18);\n    E2R_ClearHudIconName((char *)0x00475f10);\n    E2R_ClearHudIconName((char *)0x00475f50);\n    E2R_ClearHudIconName((char *)0x00475f44);\n    E2R_ClearHudIconNameRange(0x0047ab44,0x0047ab71);\n    E2R_ClearHudIconName((char *)0x00475f38);\n    E2R_ClearHudIconName((char *)0x00475e40);\n    E2R_ClearHudIconNameRange(0x0047ab9e,0x0047abd4);\n    E2R_ClearHudIconNameRange(0x0047abd4,0x0047ac0a);\n    E2R_ClearHudIconNameRange(0x0047ac0a,0x0047ac40);\n  }\n  return;\n}\n\n\n\n/* 00455fe8 */"
);
source = source.replace(/(FUN_00417b20\(int param_1,int param_2,undefined4 param_3,int param_4,int param_5,int param_6\)[\s\S]*?\r?\n  int local_10;\r?\n\s*)local_24 = 1;/, "$1E2R_InitCursorMaskState();\n  unaff_EBX = param_4;\n  local_24 = 1;");
source = source.replace(
  /(FUN_00417b20\(int param_1,int param_2,undefined4 param_3,int param_4,int param_5,int param_6\)[\s\S]*?\r?\n  undefined4 uVar5;\r?\n\s*)int iVar6;/,
  "$1size_t read_span;\n  size_t write_span;\n  int iVar6;"
);
source = source.replace("  local_18 = in_EAX;\n  if ((DAT_0047a279 >> 0x18 == param_1)", "  local_18 = param_1;\n  if ((DAT_0047a279 >> 0x18 == param_1)");
source = source.replace("      local_30 = local_2c;\n      iVar6 = extraout_ECX_01;\n      local_20 = local_28;", "      local_30 = local_2c;\n      iVar6 = param_2;\n      local_20 = local_28;");
source = source.replace(
  "    local_28 = FUN_00418a04(param_3,&local_2c);\n    if (local_18 == local_1c) {",
  "    if (local_18 < 0 || 3 < local_18 || local_1c < 0 || 3 < local_1c) {\n      return 0;\n    }\n    local_28 = FUN_00418a04((undefined4)(uintptr_t)local_18,&local_2c);\n    if (local_18 == local_1c) {"
);
source = source.replace(
  "      local_20 = FUN_00418a04(extraout_ECX_01,&local_30);\n      iVar6 = extraout_ECX_02;",
  "      local_20 = FUN_00418a04((undefined4)(uintptr_t)local_1c,&local_30);\n      iVar6 = (int)(uintptr_t)param_3;"
);
const sparseGlobalAllocatorFunctions = [
  "void __fastcall FUN_0041868c(int param_1,int param_2,int param_3,int param_4)",
  "void __fastcall FUN_00426ac4(undefined4 param_1,int param_2)",
  "undefined8 __fastcall FUN_004533ac(undefined4 param_1,undefined4 param_2)",
  "undefined8 __fastcall FUN_00453588(undefined4 param_1,undefined4 param_2)",
  "undefined8 __fastcall FUN_00453600(undefined4 param_1,undefined4 param_2)",
  "undefined8 __fastcall FUN_00453754(undefined4 param_1,undefined4 param_2)",
  "undefined8 __fastcall FUN_0045384c(undefined4 param_1,undefined4 param_2)",
  "undefined8 __fastcall FUN_004538c0(undefined4 param_1,undefined4 param_2)"
];
for (const signature of sparseGlobalAllocatorFunctions) {
  source = source.replace(
    `${signature}\n\n{`,
    `#if defined(__clang__) || defined(__GNUC__)\n__attribute__((no_sanitize("address")))\n#endif\n${signature}\n\n{`
  );
}
source = source.replace(
  "    puVar4 = (undefined1 *)(local_2c * unaff_EBX + param_2 + local_28);\n    local_14 = local_2c - param_5;\n    local_10 = local_30 - param_5;\n    puVar7 = (undefined1 *)(local_30 * param_4 + iVar6 + local_20);\n    iVar9 = 0;",
  "    puVar4 = (undefined1 *)(local_2c * unaff_EBX + param_2 + local_28);\n    local_14 = local_2c - param_5;\n    local_10 = local_30 - param_5;\n    puVar7 = (undefined1 *)(local_30 * param_4 + iVar6 + local_20);\n    if (local_28 == 0 || local_20 == 0 || local_2c <= 0 || local_30 <= 0 ||\n        param_2 < 0 || iVar6 < 0 || unaff_EBX < 0 || param_4 < 0 ||\n        param_5 <= 0 || param_6 <= 0 || local_2c - param_2 < param_5 ||\n        local_2c - unaff_EBX < param_6 || local_30 - iVar6 < param_5 ||\n        local_30 - param_4 < param_6) {\n      return 0;\n    }\n    read_span = (size_t)(param_6 - 1) * (size_t)local_2c + (size_t)param_5;\n    write_span = (size_t)(param_6 - 1) * (size_t)local_30 + (size_t)param_5;\n    if (IsBadReadPtr(puVar4,read_span) || E2R_IsBadWritePtr(puVar7,write_span)) {\n      return 0;\n    }\n    iVar9 = 0;"
);
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
source = source.replace(/E2R_READ2\(DAT_00479e8a,2\)/g, "(undefined2)(DAT_00479e8a >> 0x10)");
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
const ctypeTableState = `\nstatic byte E2R_CtypeFlags(uint index)\n{\n  int c = (int)(byte)index - 1;\n  byte flags = 0;\n\n  if (c < 0) {\n    return 0;\n  }\n  if (c < 0x20 || c == 0x7f) {\n    flags = flags | 1;\n  }\n  if (c == ' ' || c == '\\t' || c == '\\n' || c == '\\r' || c == '\\v' || c == '\\f') {\n    flags = flags | 2;\n  }\n  if ('0' <= c && c <= '9') {\n    flags = flags | 0x20;\n  }\n  if ('A' <= c && c <= 'Z') {\n    flags = flags | 0x40;\n  }\n  if ('a' <= c && c <= 'z') {\n    flags = flags | 0x80;\n  }\n  return flags;\n}\n\nstatic byte E2R_BitMask(uint index)\n{\n  return (byte)(1u << (index & 7));\n}\n\nstatic void E2R_CopyCStringBounded(char *dest,char *source,uint size)\n{\n  uint i;\n\n  if (dest == (char *)0x0 || source == (char *)0x0 || size == 0 ||\n      E2R_IsBadWritePtr(dest,size) || IsBadReadPtr(source,1)) {\n    return;\n  }\n  memset(dest,0,size);\n  for (i = 0; i + 1 < size; i = i + 1) {\n    if (IsBadReadPtr(source + i,1) || source[i] == '\\0') {\n      break;\n    }\n    dest[i] = source[i];\n  }\n}\n\nstatic void E2R_FormatOneString(char *dest,char *format,char *value)\n{\n  while (*format != '\\0') {\n    if (format[0] == '%' && format[1] == 's') {\n      while (*value != '\\0') {\n        *dest = *value;\n        dest = dest + 1;\n        value = value + 1;\n      }\n      format = format + 2;\n    }\n    else {\n      *dest = *format;\n      dest = dest + 1;\n      format = format + 1;\n    }\n  }\n  *dest = '\\0';\n}\n\nstatic void E2R_UseHostedCdPath(char *path)\n{\n  if ((path[0] != '\\0' && path[1] == ':') || path[0] == '\\\\' || path[0] == '/') {\n    path[0] = '\\0';\n  }\n}\n`;
let requesterActionState = `\nstatic int E2R_InvokeRequesterAction(uintptr_t action)\n{\n  ushort requester_id = E2R_WORD_AT(DAT_0047a45e,2);\n\n  if (action == (uintptr_t)&LAB_0043c594) {\n    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643dc4) {\n      _DAT_006443d2 = (_DAT_006443d2 & 0xffff) | 0x10000;\n      if (_DAT_00643430 == (short *)0x00643dc4) {\n        _DAT_00643650 = 6;\n      }\n      return 1;\n    }\n  }\n  if (action == (uintptr_t)&LAB_0043d458) {\n    _DAT_00643650 = 0;\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d464) {\n    _DAT_00643650 = 1;\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d470) {\n    _DAT_00643650 = 2;\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d47c) {\n    if (DAT_0047a76c == 0) {\n      _DAT_00643650 = 3;\n    }\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d490) {\n    _DAT_00643650 = 4;\n    return 1;\n  }\n  if (action == (uintptr_t)&DAT_0043d49c) {\n    uintptr_t prompt = 0x004729b8;\n    if (DAT_00479e00 != 0 && !IsBadReadPtr((void *)0x0060aef0,4) &&\n        *(uintptr_t *)0x0060aef0 != 0) {\n      prompt = *(uintptr_t *)0x0060aef0;\n    }\n    _DAT_00643650 = ((int)FUN_0043c910((undefined4)prompt,0) != 0) ? 6 : 5;\n    return 1;\n  }\n  if (action == (uintptr_t)&DAT_0043d4c0) {\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d83c) {\n    if (DAT_0047d0c4 == 0) {\n      return 1;\n    }\n    FUN_0044e5b0();\n    if (DAT_0047a43c != 0) {\n      FUN_0043acec();\n    }\n    else {\n      FUN_0043ac60();\n    }\n    DAT_0047a440 = DAT_0047a43c;\n    FUN_0044e5b0();\n    FUN_004559bc();\n    FUN_00456f94();\n    FUN_004211c8(0,0);\n    FUN_00421a14();\n    FUN_00421f54(0);\n    FUN_00422238(0,0);\n    FUN_0043d8ec();\n    FUN_0043d934();\n    FUN_0043d9a0();\n    FUN_0043da04();\n    FUN_0043da80();\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043c4e8) {\n    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643c84) {\n      _DAT_006443d2 = _DAT_006443d2 & 0xffff;\n      if (_DAT_00643430 == (short *)0x00643c84) {\n        _DAT_00643650 = 5;\n      }\n      return 1;\n    }\n    if (requester_id == 0x27 || requester_id == 0x28) {\n      _DAT_00643650 = 5;\n      return 1;\n    }\n    if (requester_id == 0x2a) {\n      _DAT_0064353c = 0;\n      return 1;\n    }\n  }\n  return 0;\n}\n`;
requesterActionState = requesterActionState.replace(
  "  if (action == (uintptr_t)&LAB_0043d83c) {",
  "  if (action == (uintptr_t)&LAB_0043d728) {\n    DAT_0047a49c = DAT_0047a49c == 0;\n    FUN_0043d934();\n    E2R_RedrawActiveRequesterItem();\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d7a0) {\n    DAT_0047a4a0 = DAT_0047a4a0 == 0;\n    FUN_0043d9a0();\n    E2R_RedrawActiveRequesterItem();\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d7f0) {\n    DAT_0047a4a4 = (DAT_0047a4a4 + 1) % 3;\n    FUN_0043da04();\n    E2R_RedrawActiveRequesterItem();\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d6e4) {\n    if (DAT_0047d0c4 != 0) {\n      DAT_0047a43c = DAT_0047a43c == 0;\n      FUN_0043da80();\n    }\n    E2R_RedrawActiveRequesterItem();\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d83c) {"
);
requesterActionState = requesterActionState.replace(
  "    if (requester_id == 0x2a) {",
  "    if (requester_id == 0x29 || requester_id == 0x2a) {"
);
requesterActionState = requesterActionState.replace(
  "  if (action == (uintptr_t)&LAB_0043d47c) {\n    if (DAT_0047a76c == 0) {\n      _DAT_00643650 = 3;\n    }\n    return 1;\n  }",
  "  if (action == (uintptr_t)&LAB_0043d47c) {\n    if (DAT_0047a76c == 0 && _DAT_0073cc3c != 0 &&\n        E2R_IsReadableCurrentPointer(DAT_0047a470)) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.save\",3);\n    }\n    else {\n      E2R_TraceRequesterState(\"action.save_disabled_intro\",_DAT_00643650);\n      return 0;\n    }\n    return 1;\n  }"
);
requesterActionState = requesterActionState.replace(
  "  if (action == (uintptr_t)&LAB_0043d83c) {\n    if (DAT_0047d0c4 == 0) {",
  "  if (action == (uintptr_t)&LAB_0043d83c) {\n    if (requester_id == 0x31) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings_ok\",0);\n      return 1;\n    }\n    if (DAT_0047d0c4 == 0) {"
);
requesterActionState = requesterActionState.replace(
  "    if (requester_id == 0x29 || requester_id == 0x2a) {\n      _DAT_0064353c = 0;\n      return 1;\n    }\n",
  "    if (requester_id == 0x29 || requester_id == 0x2a) {\n      _DAT_0064353c = 0;\n      return 1;\n    }\n    if (requester_id == 0x31) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings_cancel\",0);\n      return 1;\n    }\n"
);
const requesterFocusState = `\nstatic short *E2R_RequesterFirstSelectable(short *item)\n{\n  uint guard = 0;\n  short *first_readable = (short *)0x0;\n\n  while (item != (short *)0x0 && guard < 0x80) {\n    if ((uintptr_t)item >= 0x70000000u || IsBadReadPtr(item,0x20)) {\n      return (short *)0x0;\n    }\n    if (first_readable == (short *)0x0) {\n      first_readable = item;\n    }\n    if ((*(byte *)((int)item + 0x11) & 0x10) != 0) {\n      return item;\n    }\n    item = *(short **)(item + 9);\n    guard++;\n  }\n  return first_readable;\n}\n`;
const menuStringState = `\nstatic int E2R_IsReadableCString(char *text)\n{\n  uint i;\n\n  if ((uintptr_t)text < 0x10000 || IsBadReadPtr(text,1)) {\n    return 0;\n  }\n  for (i = 0; i < 0x1000; i = i + 1) {\n    if (IsBadReadPtr(text + i,1)) {\n      return 0;\n    }\n    if (text[i] == '\\0') {\n      return 1;\n    }\n  }\n  return 0;\n}\n\nstatic int *E2R_ResolveMenuStringList(undefined4 first,undefined4 second,undefined4 *local_single)\n{\n  int *list;\n  char *text;\n\n  list = (int *)(uintptr_t)first;\n  if ((uintptr_t)list >= 0x10000 && !IsBadReadPtr(list,4)) {\n    text = (char *)(uintptr_t)list[0];\n    if (text == (char *)0x0 || E2R_IsReadableCString(text)) {\n      return list;\n    }\n  }\n  text = (char *)(uintptr_t)first;\n  if (E2R_IsReadableCString(text)) {\n    local_single[0] = first;\n    local_single[1] = 0;\n    return (int *)local_single;\n  }\n  text = (char *)(uintptr_t)second;\n  if (E2R_IsReadableCString(text)) {\n    local_single[0] = second;\n    local_single[1] = 0;\n    return (int *)local_single;\n  }\n  return (int *)0x0;\n}\n`;
let hostedTextState = `\nstatic const byte *E2R_HostedGlyphRows(byte ch)\n{\n  static const byte space[7] = {0,0,0,0,0,0,0};\n  static const byte unknown[7] = {0x0e,0x11,0x01,0x06,0x04,0,0x04};\n\n  switch (ch) {\n  case '0': { static const byte r[7] = {0x0e,0x11,0x13,0x15,0x19,0x11,0x0e}; return r; }\n  case '1': { static const byte r[7] = {0x04,0x0c,0x04,0x04,0x04,0x04,0x0e}; return r; }\n  case '2': { static const byte r[7] = {0x0e,0x11,0x01,0x02,0x04,0x08,0x1f}; return r; }\n  case '3': { static const byte r[7] = {0x1e,0x01,0x01,0x0e,0x01,0x01,0x1e}; return r; }\n  case '4': { static const byte r[7] = {0x02,0x06,0x0a,0x12,0x1f,0x02,0x02}; return r; }\n  case '5': { static const byte r[7] = {0x1f,0x10,0x1e,0x01,0x01,0x11,0x0e}; return r; }\n  case '6': { static const byte r[7] = {0x06,0x08,0x10,0x1e,0x11,0x11,0x0e}; return r; }\n  case '7': { static const byte r[7] = {0x1f,0x01,0x02,0x04,0x08,0x08,0x08}; return r; }\n  case '8': { static const byte r[7] = {0x0e,0x11,0x11,0x0e,0x11,0x11,0x0e}; return r; }\n  case '9': { static const byte r[7] = {0x0e,0x11,0x11,0x0f,0x01,0x02,0x0c}; return r; }\n  case 'A': { static const byte r[7] = {0x0e,0x11,0x11,0x1f,0x11,0x11,0x11}; return r; }\n  case 'B': { static const byte r[7] = {0x1e,0x11,0x11,0x1e,0x11,0x11,0x1e}; return r; }\n  case 'C': { static const byte r[7] = {0x0f,0x10,0x10,0x10,0x10,0x10,0x0f}; return r; }\n  case 'D': { static const byte r[7] = {0x1e,0x11,0x11,0x11,0x11,0x11,0x1e}; return r; }\n  case 'E': { static const byte r[7] = {0x1f,0x10,0x10,0x1e,0x10,0x10,0x1f}; return r; }\n  case 'F': { static const byte r[7] = {0x1f,0x10,0x10,0x1e,0x10,0x10,0x10}; return r; }\n  case 'G': { static const byte r[7] = {0x0f,0x10,0x10,0x13,0x11,0x11,0x0f}; return r; }\n  case 'H': { static const byte r[7] = {0x11,0x11,0x11,0x1f,0x11,0x11,0x11}; return r; }\n  case 'I': { static const byte r[7] = {0x0e,0x04,0x04,0x04,0x04,0x04,0x0e}; return r; }\n  case 'J': { static const byte r[7] = {0x01,0x01,0x01,0x01,0x11,0x11,0x0e}; return r; }\n  case 'K': { static const byte r[7] = {0x11,0x12,0x14,0x18,0x14,0x12,0x11}; return r; }\n  case 'L': { static const byte r[7] = {0x10,0x10,0x10,0x10,0x10,0x10,0x1f}; return r; }\n  case 'M': { static const byte r[7] = {0x11,0x1b,0x15,0x15,0x11,0x11,0x11}; return r; }\n  case 'N': { static const byte r[7] = {0x11,0x19,0x15,0x13,0x11,0x11,0x11}; return r; }\n  case 'O': { static const byte r[7] = {0x0e,0x11,0x11,0x11,0x11,0x11,0x0e}; return r; }\n  case 'P': { static const byte r[7] = {0x1e,0x11,0x11,0x1e,0x10,0x10,0x10}; return r; }\n  case 'Q': { static const byte r[7] = {0x0e,0x11,0x11,0x11,0x15,0x12,0x0d}; return r; }\n  case 'R': { static const byte r[7] = {0x1e,0x11,0x11,0x1e,0x14,0x12,0x11}; return r; }\n  case 'S': { static const byte r[7] = {0x0f,0x10,0x10,0x0e,0x01,0x01,0x1e}; return r; }\n  case 'T': { static const byte r[7] = {0x1f,0x04,0x04,0x04,0x04,0x04,0x04}; return r; }\n  case 'U': { static const byte r[7] = {0x11,0x11,0x11,0x11,0x11,0x11,0x0e}; return r; }\n  case 'V': { static const byte r[7] = {0x11,0x11,0x11,0x11,0x11,0x0a,0x04}; return r; }\n  case 'W': { static const byte r[7] = {0x11,0x11,0x11,0x15,0x15,0x1b,0x11}; return r; }\n  case 'X': { static const byte r[7] = {0x11,0x11,0x0a,0x04,0x0a,0x11,0x11}; return r; }\n  case 'Y': { static const byte r[7] = {0x11,0x11,0x0a,0x04,0x04,0x04,0x04}; return r; }\n  case 'Z': { static const byte r[7] = {0x1f,0x01,0x02,0x04,0x08,0x10,0x1f}; return r; }\n  case '.': { static const byte r[7] = {0,0,0,0,0,0x0c,0x0c}; return r; }\n  case '(': { static const byte r[7] = {0x02,0x04,0x08,0x08,0x08,0x04,0x02}; return r; }\n  case ')': { static const byte r[7] = {0x08,0x04,0x02,0x02,0x02,0x04,0x08}; return r; }\n  case '-': { static const byte r[7] = {0,0,0,0x1f,0,0,0}; return r; }\n  case '_': { static const byte r[7] = {0,0,0,0,0,0,0x1f}; return r; }\n  case ' ': return space;\n  default: return unknown;\n  }\n}\n\nstatic void E2R_DrawHostedText(byte *text)\n{\n  byte ch;\n  const byte *rows;\n  int advance;\n  int base;\n  byte color;\n  uint col;\n  uint i;\n  int pitch;\n  uint row;\n  int scale;\n  int style_surface;\n  int surface;\n  int x;\n  int y;\n  uint yy;\n  uint xx;\n\n  if (text == (byte *)0x0 || IsBadReadPtr(text,1)) {\n    return;\n  }\n  style_surface = DAT_0047a279 >> 0x18;\n  surface = style_surface;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (surface < 0 || 3 < surface) {\n    return;\n  }\n  base = FUN_00418a04((undefined4)(uintptr_t)surface,&pitch);\n  if ((uintptr_t)base < 0x10000u || pitch <= 0 || _DAT_006401ec <= 0 ||\n      _DAT_006401d4 <= 0) {\n    return;\n  }\n  x = (short)*(undefined2 *)(0x006366c4 + surface * 2);\n  y = (short)*(undefined2 *)(0x006366d0 + surface * 2);\n  color = ((byte *)0x006366dc)[style_surface * 2];\n  if (color == 0) {\n    color = 0xf;\n  }\n  advance = DAT_0047a408 == 0 ? 12 : DAT_0047a408;\n  scale = DAT_0047a43c == 0 ? 1 : 2;\n  for (i = 0; i < 10000 && !IsBadReadPtr(text + i,1); i = i + 1) {\n    ch = text[i];\n    if (ch == 0) {\n      break;\n    }\n    if ('a' <= ch && ch <= 'z') {\n      ch = ch - ('a' - 'A');\n    }\n    rows = E2R_HostedGlyphRows(ch);\n    for (row = 0; row < 7; row = row + 1) {\n      for (col = 0; col < 5; col = col + 1) {\n        if ((rows[row] & (byte)(1u << (4 - col))) != 0) {\n          for (yy = 0; yy < (uint)scale; yy = yy + 1) {\n            for (xx = 0; xx < (uint)scale; xx = xx + 1) {\n              int px = x + (int)(col * (uint)scale + xx);\n              int py = y + (int)(row * (uint)scale + yy);\n              if (0 <= px && px < _DAT_006401ec && 0 <= py && py < _DAT_006401d4) {\n                *(byte *)(base + py * pitch + px) = color;\n              }\n            }\n          }\n        }\n      }\n    }\n    x = x + advance;\n  }\n  *(undefined2 *)(0x006366c4 + surface * 2) = (undefined2)x;\n}\n`;
hostedTextState = hostedTextState.replace(
  "if (color == 0) {\\n    color = 0xf;",
  "if (color == 0 || color == 10 || color == 0xf) {\\n    color = 8;"
);
hostedTextState = hostedTextState.replace(
  "\n\nstatic void E2R_DrawHostedText(byte *text)",
  "\n\nstatic void E2R_FillHostedRect(int left,int top,int right,int bottom)\n{\n  int base;\n  byte color;\n  int pitch;\n  int style_surface;\n  int surface;\n  int x;\n  int y;\n\n  style_surface = DAT_0047a279 >> 0x18;\n  surface = style_surface;\n  if (DAT_0047a43c != 0) {\n    surface = surface + 2;\n  }\n  if (surface < 0 || 3 < surface || right < left || bottom < top) {\n    return;\n  }\n  if (left < 0) left = 0;\n  if (top < 0) top = 0;\n  if (_DAT_006401ec <= right) right = _DAT_006401ec - 1;\n  if (_DAT_006401d4 <= bottom) bottom = _DAT_006401d4 - 1;\n  if (right < left || bottom < top) {\n    return;\n  }\n  base = FUN_00418a04((undefined4)(uintptr_t)surface,&pitch);\n  if ((uintptr_t)base < 0x10000u || pitch < _DAT_006401ec ||\n      _DAT_006401ec <= 0 || _DAT_006401d4 <= 0 ||\n      0x1000 < _DAT_006401ec || 0x1000 < _DAT_006401d4 ||\n      E2R_IsBadWritePtr((void *)(uintptr_t)base,\n                        ((size_t)_DAT_006401d4 - 1u) * (size_t)pitch +\n                        (size_t)_DAT_006401ec)) {\n    return;\n  }\n  color = ((byte *)0x006366dc)[style_surface * 2];\n  for (y = top; y <= bottom; y = y + 1) {\n    byte *row = (byte *)(base + y * pitch + left);\n    for (x = left; x <= right; x = x + 1) {\n      *row = color;\n      row = row + 1;\n    }\n  }\n}\n\nstatic void E2R_DrawHostedRectBorder(int left,int top,int right,int bottom)\n{\n  int style_surface;\n\n  if (right < left || bottom < top) {\n    return;\n  }\n  style_surface = DAT_0047a279 >> 0x18;\n  *(undefined2 *)((undefined1 *)0x006366dc + style_surface * 2) = 8;\n  FUN_0041b078(left,top);\n  FUN_0041b34c(right,top);\n  FUN_0041b34c(right,bottom);\n  *(undefined2 *)((undefined1 *)0x006366dc + style_surface * 2) = 0xe;\n  FUN_0041b078(right - 1,bottom);\n  FUN_0041b34c(left,bottom);\n  FUN_0041b34c(left,top);\n}\n\nstatic void E2R_DrawHostedText(byte *text)"
);
hostedTextState = hostedTextState.replace(
  /static void E2R_FillHostedRect\(int left,int top,int right,int bottom\)[\s\S]*?\n\nstatic void E2R_DrawHostedText\(byte \*text\)/,
  `static void E2R_CopyHostedSurface(int dst,int src)
{
  int dst_base;
  int dst_pitch;
  int src_base;
  int src_pitch;
  int y;

  if (dst == src || dst < 0 || 3 < dst || src < 0 || 3 < src ||
      _DAT_006401ec <= 0 || _DAT_006401d4 <= 0 ||
      0x1000 < _DAT_006401ec || 0x1000 < _DAT_006401d4) {
    return;
  }
  src_base = FUN_00418a04((undefined4)(uintptr_t)src,&src_pitch);
  dst_base = FUN_00418a04((undefined4)(uintptr_t)dst,&dst_pitch);
  if ((uintptr_t)src_base < 0x10000u || (uintptr_t)dst_base < 0x10000u ||
      src_pitch < _DAT_006401ec || dst_pitch < _DAT_006401ec ||
      IsBadReadPtr((void *)(uintptr_t)src_base,
                   ((size_t)_DAT_006401d4 - 1u) * (size_t)src_pitch +
                   (size_t)_DAT_006401ec) ||
      E2R_IsBadWritePtr((void *)(uintptr_t)dst_base,
                        ((size_t)_DAT_006401d4 - 1u) * (size_t)dst_pitch +
                        (size_t)_DAT_006401ec)) {
    return;
  }
  for (y = 0; y < _DAT_006401d4; y = y + 1) {
    memcpy((void *)(uintptr_t)(dst_base + y * dst_pitch),
           (void *)(uintptr_t)(src_base + y * src_pitch),
           (size_t)_DAT_006401ec);
  }
}

#define E2R_REQUESTER_BACKDROP_MAX 8
static byte E2R_requester_backdrop_pixels[E2R_REQUESTER_BACKDROP_MAX][2][640 * 480];
static int E2R_requester_backdrop_width[E2R_REQUESTER_BACKDROP_MAX];
static int E2R_requester_backdrop_height[E2R_REQUESTER_BACKDROP_MAX];
static int E2R_requester_backdrop_depth;

static void E2R_SaveHostedRequesterBackdrop(void)
{
  int base;
  int pitch;
  int slot;
  int surface;
  int y;

  if (DAT_0047a43c == 0 || _DAT_006401ec <= 0 || _DAT_006401d4 <= 0 ||
      640 < _DAT_006401ec || 480 < _DAT_006401d4) {
    return;
  }
  if (E2R_requester_backdrop_depth >= E2R_REQUESTER_BACKDROP_MAX) {
    return;
  }
  slot = E2R_requester_backdrop_depth;
  E2R_requester_backdrop_width[slot] = _DAT_006401ec;
  E2R_requester_backdrop_height[slot] = _DAT_006401d4;
  for (surface = 0; surface < 2; surface = surface + 1) {
    base = FUN_00418a04((undefined4)(uintptr_t)(surface + 2),&pitch);
    if ((uintptr_t)base < 0x10000u || pitch < _DAT_006401ec ||
        IsBadReadPtr((void *)(uintptr_t)base,
                     ((size_t)_DAT_006401d4 - 1u) * (size_t)pitch +
                     (size_t)_DAT_006401ec)) {
      return;
    }
    for (y = 0; y < _DAT_006401d4; y = y + 1) {
      memcpy(E2R_requester_backdrop_pixels[slot][surface] + y * 640,
             (void *)(uintptr_t)(base + y * pitch),
             (size_t)_DAT_006401ec);
    }
  }
  E2R_requester_backdrop_depth = E2R_requester_backdrop_depth + 1;
}

static void E2R_RestoreHostedRequesterBackdrop(void)
{
  int base;
  int height;
  int pitch;
  int slot;
  int surface;
  int width;
  int y;

  if (DAT_0047a43c == 0 || E2R_requester_backdrop_depth <= 0) {
    return;
  }
  slot = E2R_requester_backdrop_depth - 1;
  width = E2R_requester_backdrop_width[slot];
  height = E2R_requester_backdrop_height[slot];
  if (width <= 0 || height <= 0 || 640 < width || 480 < height) {
    E2R_requester_backdrop_depth = slot;
    return;
  }
  for (surface = 0; surface < 2; surface = surface + 1) {
    base = FUN_00418a04((undefined4)(uintptr_t)(surface + 2),&pitch);
    if ((uintptr_t)base < 0x10000u || pitch < width ||
        E2R_IsBadWritePtr((void *)(uintptr_t)base,
                          ((size_t)height - 1u) * (size_t)pitch +
                          (size_t)width)) {
      E2R_requester_backdrop_depth = slot;
      return;
    }
    for (y = 0; y < height; y = y + 1) {
      memcpy((void *)(uintptr_t)(base + y * pitch),
             E2R_requester_backdrop_pixels[slot][surface] + y * 640,
             (size_t)width);
    }
  }
  E2R_requester_backdrop_depth = slot;
  DAT_0047a788 = 1;
}

static void E2R_ResetHostedRequesterBackdrop(void)
{
  E2R_requester_backdrop_depth = 0;
}

static int E2R_HostedSurfaceScore(int surface)
{
  int base;
  int pitch;
  int score;
  int x;
  int y;

  if (surface < 0 || 3 < surface || _DAT_006401ec <= 0 || _DAT_006401d4 <= 0 ||
      0x1000 < _DAT_006401ec || 0x1000 < _DAT_006401d4) {
    return -1;
  }
  base = FUN_00418a04((undefined4)(uintptr_t)surface,&pitch);
  if ((uintptr_t)base < 0x10000u || pitch < _DAT_006401ec ||
      IsBadReadPtr((void *)(uintptr_t)base,
                   ((size_t)_DAT_006401d4 - 1u) * (size_t)pitch +
                   (size_t)_DAT_006401ec)) {
    return -1;
  }
  score = 0;
  for (y = 0; y < _DAT_006401d4; y = y + 8) {
    for (x = 0; x < _DAT_006401ec; x = x + 8) {
      if (*(byte *)(base + y * pitch + x) != 0) {
        score = score + 1;
      }
    }
  }
  return score;
}

static void E2R_FillHostedRect(int left,int top,int right,int bottom)
{
  int base;
  byte color;
  int count;
  int i;
  int pitch;
  int style_surface;
  int surface;
  int targets[2];
  int x;
  int y;

  style_surface = DAT_0047a279 >> 0x18;
  surface = style_surface;
  if (DAT_0047a43c != 0) {
    surface = surface + 2;
  }
  if (surface < 0 || 3 < surface || right < left || bottom < top) {
    return;
  }
  targets[0] = surface;
  count = 1;
  if (DAT_0047a43c != 0) {
    if (E2R_HostedSurfaceScore(surface == 2 ? 3 : 2) > E2R_HostedSurfaceScore(surface)) {
      E2R_CopyHostedSurface(surface,surface == 2 ? 3 : 2);
    }
    else {
      E2R_CopyHostedSurface(surface == 2 ? 3 : 2,surface);
    }
    targets[0] = 2;
    targets[1] = 3;
    count = 2;
  }
  if (left < 0) left = 0;
  if (top < 0) top = 0;
  if (_DAT_006401ec <= right) right = _DAT_006401ec - 1;
  if (_DAT_006401d4 <= bottom) bottom = _DAT_006401d4 - 1;
  if (right < left || bottom < top) {
    return;
  }
  color = ((byte *)0x006366dc)[style_surface * 2];
  for (i = 0; i < count; i = i + 1) {
    base = FUN_00418a04((undefined4)(uintptr_t)targets[i],&pitch);
    if ((uintptr_t)base < 0x10000u || pitch < _DAT_006401ec ||
        _DAT_006401ec <= 0 || _DAT_006401d4 <= 0 ||
        0x1000 < _DAT_006401ec || 0x1000 < _DAT_006401d4 ||
        E2R_IsBadWritePtr((void *)(uintptr_t)base,
                          ((size_t)_DAT_006401d4 - 1u) * (size_t)pitch +
                          (size_t)_DAT_006401ec)) {
      continue;
    }
    for (y = top; y <= bottom; y = y + 1) {
      byte *row = (byte *)(base + y * pitch + left);
      for (x = left; x <= right; x = x + 1) {
        *row = color;
        row = row + 1;
      }
    }
  }
}

static void E2R_DrawHostedRectBorder(int left,int top,int right,int bottom)
{
  int base;
  int count;
  int i;
  int pitch;
  int style_surface;
  int targets[2];
  int x;
  int y;

  if (right < left || bottom < top) {
    return;
  }
  style_surface = DAT_0047a279 >> 0x18;
  targets[0] = style_surface;
  count = 1;
  if (DAT_0047a43c != 0) {
    targets[0] = 2;
    targets[1] = 3;
    count = 2;
  }
  for (i = 0; i < count; i = i + 1) {
    base = FUN_00418a04((undefined4)(uintptr_t)targets[i],&pitch);
    if ((uintptr_t)base < 0x10000u || pitch < _DAT_006401ec ||
        _DAT_006401ec <= 0 || _DAT_006401d4 <= 0 ||
        0x1000 < _DAT_006401ec || 0x1000 < _DAT_006401d4 ||
        E2R_IsBadWritePtr((void *)(uintptr_t)base,
                          ((size_t)_DAT_006401d4 - 1u) * (size_t)pitch +
                          (size_t)_DAT_006401ec)) {
      continue;
    }
    if (left < 0) left = 0;
    if (top < 0) top = 0;
    if (_DAT_006401ec <= right) right = _DAT_006401ec - 1;
    if (_DAT_006401d4 <= bottom) bottom = _DAT_006401d4 - 1;
    for (x = left; x <= right; x = x + 1) {
      *(byte *)(base + top * pitch + x) = 8;
      *(byte *)(base + bottom * pitch + x) = 0xe;
    }
    for (y = top; y <= bottom; y = y + 1) {
      *(byte *)(base + y * pitch + right) = 8;
      *(byte *)(base + y * pitch + left) = 0xe;
    }
  }
}

static void E2R_DrawHostedText(byte *text)`
);
hostedTextState = hostedTextState.replace(
  /(static void E2R_DrawHostedText\(byte \*text\)\n\{\n[\s\S]*?  int base;\n)  byte color;/,
  "$1  int base2;\n  byte color;"
);
hostedTextState = hostedTextState.replace(
  /(static void E2R_DrawHostedText\(byte \*text\)\n\{\n[\s\S]*?  int pitch;\n)  uint row;/,
  "$1  int pitch2;\n  uint row;"
);
hostedTextState = hostedTextState.replace(
  /(static void E2R_DrawHostedText\(byte \*text\)\n\{\n[\s\S]*?  int surface;\n)  int x;/,
  "$1  int surface2;\n  int x;"
);
hostedTextState = hostedTextState.replace(
  "  if ((uintptr_t)base < 0x10000u || pitch <= 0 || _DAT_006401ec <= 0 ||\n      _DAT_006401d4 <= 0) {\n    return;\n  }\n  x = (short)*(undefined2 *)(0x006366c4 + surface * 2);",
  "  if ((uintptr_t)base < 0x10000u || pitch <= 0 || _DAT_006401ec <= 0 ||\n      _DAT_006401d4 <= 0) {\n    return;\n  }\n  base2 = 0;\n  pitch2 = 0;\n  surface2 = -1;\n  if (DAT_0047a43c != 0) {\n    surface2 = surface == 2 ? 3 : 2;\n    base2 = FUN_00418a04((undefined4)(uintptr_t)surface2,&pitch2);\n    if ((uintptr_t)base2 < 0x10000u || pitch2 <= 0) {\n      base2 = 0;\n    }\n  }\n  x = (short)*(undefined2 *)(0x006366c4 + surface * 2);"
);
hostedTextState = hostedTextState.replace(
  "                *(byte *)(base + py * pitch + px) = color;",
  "                *(byte *)(base + py * pitch + px) = color;\n                if (base2 != 0) {\n                  *(byte *)(base2 + py * pitch2 + px) = color;\n                }"
);
const hostedRequesterLabelState = `\nstatic byte *E2R_RequesterTextOrFallback(byte *text);\n\nstatic void E2R_DrawHostedRequesterLabels(short *record)\n{\n  byte *text;\n  byte color;\n  int item_width;\n  int text_width;\n  int x;\n  short *item;\n  uint guard;\n  uint len;\n  int style_surface;\n\n  if (DAT_0047a43c == 0 || record == (short *)0x0 || IsBadReadPtr(record,0x10)) {\n    return;\n  }\n  style_surface = DAT_0047a279 >> 0x18;\n  item = *(short **)(record + 6);\n  for (guard = 0; item != (short *)0x0 && guard < 0x40; guard = guard + 1) {\n    if ((uintptr_t)item >= 0x70000000u || IsBadReadPtr(item,0x20)) {\n      break;\n    }\n    text = E2R_RequesterTextOrFallback(*(byte **)(item + 4));\n    if (text != (byte *)0x0 && !IsBadReadPtr(text,1) && text[0] != 0) {\n      len = 0;\n      while (len < 0x100 && !IsBadReadPtr(text + len,1) && text[len] != 0) {\n        len = len + 1;\n      }\n      text_width = (DAT_0047a408 == 0 ? 12 : DAT_0047a408) * (int)len;\n      item_width = (int)item[2];\n      if ((*(byte *)((int)item + 0x11) & 0x40) == 0) {\n        x = item[0xb] + (item_width - text_width) / 2;\n      }\n      else {\n        x = item[0xb] + 4;\n      }\n      color = item == _DAT_00643430 ? 0xe : 8;\n      *(undefined2 *)((undefined1 *)0x006366dc + style_surface * 2) = color;\n      FUN_0041b078(x,(short)(item[0xd] + 1));\n      E2R_DrawHostedText(text);\n    }\n    item = *(short **)(item + 9);\n  }\n}\n\nstatic byte *E2R_RequesterTextOrFallback(byte *text)\n{\n  uintptr_t address = (uintptr_t)text;\n\n  if (address == 0x00473298u) return (byte *)\"OK\";\n  if (address == 0x004732a4u) return (byte *)\"Yes\";\n  if (address == 0x004732a8u) return (byte *)\"No\";\n  if (address == 0x00473304u) return (byte *)\"Quit\";\n  return text;\n}\n\nstatic void E2R_RedrawActiveRequesterItem(void)\n{\n  short *record;\n  short *item;\n\n  record = (short *)FUN_0043aeac();\n  item = (short *)_DAT_00643430;\n  if (record == (short *)0x0 || item == (short *)0x0 ||\n      (uintptr_t)record >= 0x70000000u || (uintptr_t)item >= 0x70000000u ||\n      IsBadReadPtr(record,0x20) || IsBadReadPtr(item,0x20)) {\n    return;\n  }\n  FUN_0043b9bc(0,item);\n  E2R_DrawHostedRequesterLabels(record);\n  DAT_0047a788 = 1;\n}\n`;
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

static int E2R_ScriptDiagEnabled(void)
{
  char *value = getenv("E2R_SCRIPT_DIAG");

  return value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';
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
  char *name;
  short *pool;
  uint offset;
  uint token_count;

  E2R_start_code_probe_dispatches++;
  E2R_start_code_probe_last_node = (uintptr_t)action;
  E2R_start_code_probe_last_name_index = (ushort)action[0];
  E2R_start_code_probe_last_bytecode_offset = *(uint *)(action + 3);
  name = E2R_ActionCodeName(action);
  if ((E2R_RuntimeDiagEnabled() && E2R_action_invoke_diag_count < 64) ||
      (E2R_ScriptDiagEnabled() && name != (char *)0x0 &&
       strcmp(name,"mar:StartGame") == 0)) {
    offset = *(uint *)(action + 3);
    pool = (short *)(uintptr_t)_DAT_006366a0;
    fprintf(stderr,
            "action invoke: node=0x%lx name_index=%u name=%s code=0x%x tokens=",
            (unsigned long)(uintptr_t)action,(unsigned int)(ushort)action[0],
            name != (char *)0x0 ? name : "(null)",offset);
    if (pool != (short *)0x0 && offset < 19999 &&
        !IsBadReadPtr(pool + offset,8 * sizeof(short))) {
      for (token_count = 0; token_count < 8; token_count = token_count + 1) {
        fprintf(stderr,"%s%04x",token_count == 0 ? "" : ",",
                (unsigned int)(ushort)pool[offset + token_count]);
        if (pool[offset + token_count] == 0) {
          break;
        }
      }
    }
    else {
      fprintf(stderr,"(unreadable)");
    }
    fprintf(stderr,"\\n");
    E2R_action_invoke_diag_count = E2R_action_invoke_diag_count + 1;
  }
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

static void E2R_InitRequesterSettingsItems(void)
{
  uintptr_t ok_text;

  ok_text = DAT_00479e00 == 0 ? (uintptr_t)(char *)0x00473298 : (uintptr_t)_DAT_0060ae70;
  E2R_InitRequesterItem(0x00643998,0xde,0x13,0x1e,10,(uintptr_t)_DAT_006439a0,
                        (uintptr_t)&LAB_0043d728,0,0x006439f8);
  E2R_InitRequesterItem(0x006439f8,0xde,0x13,0x2d,10,(uintptr_t)_DAT_00643a00,
                        (uintptr_t)&LAB_0043d7a0,0,0x00643958);
  E2R_InitRequesterItem(0x00643958,0xde,0x13,0x3c,10,(uintptr_t)_DAT_00643960,
                        (uintptr_t)&LAB_0043d7f0,0,0x006436e0);
  E2R_InitRequesterItem(0x006436e0,0xde,0x13,0x4b,10,(uintptr_t)_DAT_006436e8,
                        (uintptr_t)&LAB_0043d6e4,0,0x00643de4);
  E2R_InitRequesterItem(0x00643de4,0x38,10,0x5f,0xc,ok_text,
                        (uintptr_t)&LAB_0043d83c,0x2000,0);
  E2R_InitRequesterRecord(0x0047a668,-1,-1,0xf0,0x78,(uintptr_t)DAT_0047a670,0x00643998);
}
`;
source = source.replace("\n\n/* 00410078 */", `${ctypeTableState}\n${requesterActionState}\n${requesterFocusState}\n${menuStringState}\n${hostedTextState}\n${hostedRequesterLabelState}\n${streamLineState}\n${configHeaderState}\n${cursorMaskState}\n${startupPartNames}\n${glyphTableMirror}\n${hudIconNameState}\n${requesterRecordState}\n\n/* 00410078 */`);
source = source.replace(
  "static int E2R_InvokeRequesterAction(uintptr_t action)",
  "static int E2R_requester_continue_after_action;\nstatic void E2R_RedrawActiveRequesterItem(void);\n\nstatic int E2R_InvokeRequesterAction(uintptr_t action)"
);
source = source.replace("\n\n/* 00410078 */", `${packedNameState}\n${actionCodeState}\n\n/* 00410078 */`);
source = source.replace(
  "static uint E2R_current_actor_trace_diag_count;\nstatic const char *E2R_current_actor_last_site;",
  "static uint E2R_current_actor_trace_diag_count;\nstatic uint E2R_requester_state_diag_count;\nstatic uint E2R_start_game_stage_diag_count;\nstatic uint E2R_scene_pointer_diag_count;\nstatic uint E2R_frame_stage_diag_count;\nstatic const char *E2R_current_actor_last_site;"
);
source = source.replace(
  "static uint E2R_frame_stage_diag_count;\nstatic const char *E2R_current_actor_last_site;",
  "static uint E2R_frame_stage_diag_count;\nstatic uint E2R_actor_loop_diag_count;\nstatic const char *E2R_current_actor_last_site;"
);
source = source.replace(
  "static uint E2R_actor_loop_diag_count;\nstatic const char *E2R_current_actor_last_site;",
  "static uint E2R_actor_loop_diag_count;\nstatic uint E2R_actor_update_diag_count;\nstatic const char *E2R_current_actor_last_site;"
);
source = source.replace(
  "static uint E2R_actor_update_diag_count;\nstatic const char *E2R_current_actor_last_site;",
  "static uint E2R_actor_update_diag_count;\nstatic uint E2R_action_invoke_diag_count;\nstatic const char *E2R_current_actor_last_site;"
);
source = source.replace(
  "static uint E2R_action_invoke_diag_count;\nstatic const char *E2R_current_actor_last_site;",
  "static uint E2R_action_invoke_diag_count;\nstatic uint E2R_scene_lookup_diag_count;\nstatic const char *E2R_current_actor_last_site;"
);
source = source.replace(
  "static uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)",
  "static int E2R_ShouldForceScene785Fallback(void)\n{\n  char *value = getenv(\"E2R_FORCE_SCENE_785\");\n\n  return value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n}\n\nstatic void E2R_WaitStartupLogo(void)\n{\n  char *value = getenv(\"E2R_STARTUP_LOGO_DELAY_MS\");\n  unsigned long delay_ms = 5000;\n\n  if (value != (char *)0x0 && value[0] != '\\0') {\n    delay_ms = strtoul(value,(char **)0x0,10);\n  }\n  if (delay_ms != 0) {\n    Sleep((DWORD)delay_ms);\n  }\n}\n\nstatic uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)"
);
source = source.replace(
  "if ((uint)actor < 0x10000u || 0x70000000u <= (uint)actor ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x136)) {",
  "if ((uint)actor < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)actor,0x136)) {"
);
source = source.replace(
  "return value != 0 && 0x10000u <= (uint)value && (uint)value < 0x70000000u &&\n         !IsBadReadPtr((void *)value,0xaa);",
  "return value != 0 && 0x10000u <= (uint)value &&\n         !IsBadReadPtr((void *)value,0xaa);"
);
source = source.replace(
  "static void E2R_SelectSceneRecord(short scene_id)\n{\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return;\n  }\n  _DAT_0073ccba = (ushort)scene_id;\n  FUN_0044c6bc();\n}\n\nstatic int E2R_round_to_int",
  "static void E2R_SelectSceneRecord(short scene_id)\n{\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return;\n  }\n  _DAT_0073ccba = (ushort)scene_id;\n  FUN_0044c6bc();\n}\n\nstatic uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)\n{\n  uintptr_t old_value = _DAT_0073cc3c;\n\n  if (E2R_scene_pointer_diag_count < 96 && old_value != value) {\n    E2R_scene_pointer_diag_count = E2R_scene_pointer_diag_count + 1;\n    fprintf(stderr,\n            \"scene pointer write: site=%s old=0x%lx new=0x%lx \"\n            \"DAT_00479de8=%lu DAT_0047a76c=%lu requester_state=%lu \"\n            \"start_game=%lu dispatch=%lu caller=%p\\n\",\n            site,(unsigned long)old_value,(unsigned long)value,\n            (unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n            (unsigned long)_DAT_00643650,\n            (unsigned long)E2R_start_game_probe_count,\n            (unsigned long)E2R_start_code_probe_dispatches,\n            __builtin_return_address(0));\n  }\n  return value;\n}\n\nstatic void E2R_TraceStartGameStage(const char *stage)\n{\n  if (E2R_start_game_stage_diag_count < 64) {\n    E2R_start_game_stage_diag_count = E2R_start_game_stage_diag_count + 1;\n    fprintf(stderr,\n            \"start-game stage: %s count=%lu mode=%lu DAT_00479de8=%lu \"\n            \"DAT_0047a76c=%lu scene=0x%lx startup=%lu/%lu action=%lu/%lu \"\n            \"dispatch=%lu caller=%p\\n\",\n            stage,(unsigned long)E2R_start_game_probe_count,\n            (unsigned long)E2R_start_game_probe_last_mode,\n            (unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n            (unsigned long)_DAT_0073cc3c,\n            (unsigned long)E2R_start_code_probe_startup_scans,\n            (unsigned long)E2R_start_code_probe_startup_matches,\n            (unsigned long)E2R_start_code_probe_action_scans,\n            (unsigned long)E2R_start_code_probe_action_matches,\n            (unsigned long)E2R_start_code_probe_dispatches,\n            __builtin_return_address(0));\n  }\n}\n\nstatic uintptr_t E2R_TraceRequesterState(const char *site, uintptr_t value)\n{\n  uintptr_t old_value = _DAT_00643650;\n\n  if (E2R_requester_state_diag_count < 64) {\n    E2R_requester_state_diag_count = E2R_requester_state_diag_count + 1;\n    fprintf(stderr,\n            \"requester state write: site=%s old=%lu new=%lu \"\n            \"DAT_00479de8=%lu DAT_0047a76c=%lu DAT_0047a788=%lu \"\n            \"DAT_00479db4=%lu requester=0x%x start_game=%lu \"\n            \"dispatch=%lu scene=0x%lx caller=%p\\n\",\n            site,(unsigned long)old_value,(unsigned long)value,\n            (unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n            (unsigned long)DAT_0047a788,(unsigned long)DAT_00479db4,\n            (unsigned int)E2R_WORD_AT(DAT_0047a45e,2),\n            (unsigned long)E2R_start_game_probe_count,\n            (unsigned long)E2R_start_code_probe_dispatches,\n            (unsigned long)_DAT_0073cc3c,__builtin_return_address(0));\n  }\n  return value;\n}\n\nstatic int E2R_round_to_int"
);
source = source.replace(
  "static void E2R_SelectSceneRecord(short scene_id)\n{\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return;\n  }\n  _DAT_0073ccba = (ushort)scene_id;\n  FUN_0044c6bc();\n}\n\nstatic uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)",
  "static void E2R_SyncSceneViewId(void)\n{\n  _DAT_0073ccb8 = CONCAT22((ushort)_DAT_0073ccba,(ushort)_DAT_0073ccb8);\n}\n\nstatic void E2R_SelectSceneRecord(short scene_id)\n{\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return;\n  }\n  _DAT_0073ccba = (ushort)scene_id;\n  E2R_SyncSceneViewId();\n  FUN_0044c6bc();\n}\n\nstatic int E2R_ActivateSelectedSceneRecord(short scene_id)\n{\n  int scene_record;\n  int child;\n  int actor;\n  int selected_actor;\n  uint guard;\n\n  if (scene_id < 0 || 0x4b0 <= scene_id) {\n    return 0;\n  }\n  FUN_0045233c((undefined4)(int)scene_id,(undefined4)(int)scene_id);\n  scene_record = *(int *)((undefined1 *)0x0062e450 + scene_id * 4);\n  if (scene_record == 0 || IsBadReadPtr((void *)(uintptr_t)scene_record,0x20)) {\n    return 0;\n  }\n  FUN_00452140((undefined4)(uintptr_t)scene_record);\n  selected_actor = 0;\n  guard = 0;\n  for (child = *(int *)(scene_record + 4);\n       child != 0 && guard < 0x4000 &&\n       !IsBadReadPtr((void *)(uintptr_t)child,0x1c);\n       child = *(int *)(child + 0x18)) {\n    guard = guard + 1;\n    if (((*(byte *)(child + 0xe) & 0x20) != 0) || *(short *)child < 0) {\n      continue;\n    }\n    actor = *(int *)((undefined1 *)0x00630b60 + *(short *)child * 4);\n    if (actor == 0) {\n      continue;\n    }\n    if ((uintptr_t)actor == (uintptr_t)DAT_0047a470) {\n      selected_actor = actor;\n      break;\n    }\n    if (selected_actor == 0 || *(short *)child == 0) {\n      selected_actor = actor;\n    }\n  }\n  if (selected_actor != 0) {\n    DAT_0047a470 = (short *)(uintptr_t)\n      E2R_TraceCurrentActorWrite(\"scene.activate-selected\",(uintptr_t)selected_actor);\n  }\n  FUN_004523f8((undefined4)(uintptr_t)scene_record);\n  if (E2R_RuntimeDiagEnabled() && E2R_scene_load_diag_count < 128) {\n    E2R_scene_load_diag_count = E2R_scene_load_diag_count + 1;\n    fprintf(stderr,\n            \"scene activate selected: scene=%d record=0x%lx current=0x%lx actor_head=0x%lx\\n\",\n            (int)scene_id,(unsigned long)(uintptr_t)scene_record,\n            (unsigned long)DAT_0047a470,(unsigned long)_DAT_0063726c);\n  }\n  return 1;\n}\n\nstatic int E2R_ShouldForceScene785Fallback(void)\n{\n  char *value = getenv(\"E2R_FORCE_SCENE_785\");\n\n  return value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n}\n\nstatic void E2R_WaitStartupLogo(void)\n{\n  char *value = getenv(\"E2R_STARTUP_LOGO_DELAY_MS\");\n  unsigned long delay_ms = 5000;\n\n  if (value != (char *)0x0 && value[0] != '\\0') {\n    delay_ms = strtoul(value,(char **)0x0,10);\n  }\n  if (delay_ms != 0) {\n    Sleep((DWORD)delay_ms);\n  }\n}\n\nstatic uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)"
);
source = source.replace(
  "static void E2R_WaitStartupLogo(void)\n{\n  char *value = getenv(\"E2R_STARTUP_LOGO_DELAY_MS\");\n  unsigned long delay_ms = 5000;\n\n  if (value != (char *)0x0 && value[0] != '\\0') {\n    delay_ms = strtoul(value,(char **)0x0,10);\n  }\n  if (delay_ms != 0) {\n    Sleep((DWORD)delay_ms);\n  }\n}\n\nstatic uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)",
  "static void E2R_TraceInputFlags(const char *site);\n\nstatic void E2R_WaitStartupLogo(void)\n{\n  char *value = getenv(\"E2R_STARTUP_LOGO_DELAY_MS\");\n  unsigned long delay_ms = 5000;\n  unsigned long elapsed_ms;\n  unsigned long slice_ms;\n\n  if (value != (char *)0x0 && value[0] != '\\0') {\n    delay_ms = strtoul(value,(char **)0x0,10);\n  }\n  if (delay_ms != 0) {\n    E2R_GameStateLog(\"startup logo wait begin ms=%lu\",delay_ms);\n    elapsed_ms = 0;\n    while (elapsed_ms < delay_ms) {\n      if (DAT_00636850 != '\\0' || DAT_00636844 != '\\0') {\n        E2R_GameStateLog(\"startup logo wait skipped elapsed=%lu esc=%u space=%u\",\n                         elapsed_ms,(unsigned int)(byte)DAT_00636844,\n                         (unsigned int)(byte)DAT_00636850);\n        DAT_00636844 = '\\0';\n        DAT_00636850 = '\\0';\n        E2R_TraceInputFlags(\"startup-logo.skip-clear\");\n        break;\n      }\n      slice_ms = delay_ms - elapsed_ms;\n      if (16 < slice_ms) {\n        slice_ms = 16;\n      }\n      Sleep((DWORD)slice_ms);\n      elapsed_ms = elapsed_ms + slice_ms;\n    }\n    E2R_GameStateLog(\"startup logo wait end ms=%lu\",delay_ms);\n  }\n}\n\nstatic const char *E2R_StartupLogoName(undefined4 path)\n{\n  uintptr_t ptr = (uintptr_t)path;\n\n  if (ptr == (uintptr_t)s_gbnklogo_raw_00470500) {\n    return \"gbnklogo.raw\";\n  }\n  if (ptr == (uintptr_t)s_psyglogo_raw_00470510 ||\n      ptr == (uintptr_t)s_psyglogo_raw_00472f98) {\n    return \"psyglogo.raw\";\n  }\n  if (ptr == (uintptr_t)s_aasglogo_raw_00470520 ||\n      ptr == (uintptr_t)s_aasglogo_raw_00472fa8) {\n    return \"aasglogo.raw\";\n  }\n  if (ptr != 0 && !IsBadReadPtr((void *)ptr,1)) {\n    return (const char *)ptr;\n  }\n  return \"<unknown>\";\n}\n\nstatic void E2R_TraceInputFlags(const char *site)\n{\n  static byte last_escape;\n  static byte last_space;\n  static uintptr_t last_requester_state;\n  static uintptr_t last_scene;\n\n  if (!E2R_GameStateLogEnabled()) {\n    return;\n  }\n  if (DAT_00636844 == last_escape && DAT_00636850 == last_space &&\n      _DAT_00643650 == last_requester_state && _DAT_0073cc3c == last_scene) {\n    return;\n  }\n  E2R_GameStateLog(\n      \"%s input esc=%u space=%u menu_request=%lu requester_state=%lu mode=%lu scene=0x%lx current=0x%lx\",\n      site,(unsigned int)(byte)DAT_00636844,(unsigned int)(byte)DAT_00636850,\n      (unsigned long)DAT_00479db4,(unsigned long)_DAT_00643650,\n      (unsigned long)DAT_00479de8,(unsigned long)_DAT_0073cc3c,\n      (unsigned long)DAT_0047a470);\n  last_escape = DAT_00636844;\n  last_space = DAT_00636850;\n  last_requester_state = _DAT_00643650;\n  last_scene = _DAT_0073cc3c;\n}\n\nstatic uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)"
);
source = source.replace(
  "static uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)",
  "static short E2R_FindPackedNameIndex(char *input,char *table,uint capacity,short max_names);\n\nstatic int E2R_RequestIntroSkip(void)\n{\n  int actor;\n  int *slot;\n  int action;\n  short scene_id;\n  ushort duration;\n  ushort progress;\n\n  if (DAT_00636850 == '\\0') {\n    return 0;\n  }\n  actor = DAT_0047a470;\n  E2R_GameStateLog(\"intro skip inspect actor=0x%lx scene=0x%lx space=%u\",\n                   (unsigned long)(uintptr_t)actor,(unsigned long)_DAT_0073cc3c,\n                   (unsigned int)(byte)DAT_00636850);\n  if (actor == 0 || (uintptr_t)actor < 0x10000u) {\n    return 0;\n  }\n  slot = (int *)(uintptr_t)(actor + 0xa6);\n  if (IsBadReadPtr(slot,0x12)) {\n    return 0;\n  }\n  action = *slot;\n  if (action != 0x937800 || ((*(byte *)((int)slot + 0xc) & 2) == 0)) {\n    return 0;\n  }\n  duration = *(ushort *)(slot + 1);\n  progress = *(ushort *)((int)slot + 6);\n  if (duration == 0 || duration <= progress) {\n    return 0;\n  }\n  scene_id = E2R_FindPackedNameIndex(s_Start_sc_00470c80,_DAT_006366bc,20000,0x9c4);\n  if (scene_id < 0) {\n    E2R_GameStateLog(\"intro skip missing Start_sc scene actor=0x%lx action=0x%lx\",\n                     (unsigned long)(uintptr_t)actor,\n                     (unsigned long)(uintptr_t)action);\n    return 0;\n  }\n  DAT_00636850 = '\\0';\n  E2R_GameStateLog(\"intro skip request scene=0x%lx actor=0x%lx action=0x%lx progress=%u duration=%u Start_sc=%d offset=%ld record=0x%lx\",\n                   (unsigned long)_DAT_0073cc3c,(unsigned long)(uintptr_t)actor,\n                   (unsigned long)(uintptr_t)action,(unsigned int)progress,\n                   (unsigned int)duration,(int)scene_id,\n                   (long)*(int *)(scene_id * 4 + 0x650fa0),\n                   (unsigned long)*(int *)(scene_id * 4 + 0x62e450));\n  if (E2R_StartupDiagEnabled()) {\n    E2R_archive_parse_summary_count = 0;\n    E2R_fan_phase_diag_count = 0;\n    E2R_fan_dispatch_diag_count = 0;\n    E2R_scene_load_diag_count = 0;\n    E2R_scene_record_install_diag_count = 0;\n    E2R_scene_child_diag_count = 0;\n  }\n  FUN_0043a6e0((undefined4)(int)scene_id,(undefined4)(int)scene_id);\n  E2R_GameStateLog(\"intro skip subintro scene=%d current=0x%lx actors=0x%lx scene_ptr=0x%lx\",\n                   (int)scene_id,(unsigned long)DAT_0047a470,\n                   (unsigned long)_DAT_0063726c,(unsigned long)_DAT_0073cc3c);\n  return 1;\n}\n\nstatic uintptr_t E2R_TraceScenePointerWrite(const char *site, uintptr_t value)"
);
source = source.replace(
  "static short E2R_FindPackedNameIndex(char *input,char *table,uint capacity,short max_names);\n\nstatic int E2R_RequestIntroSkip(void)",
  "static short E2R_FindPackedNameIndex(char *input,char *table,uint capacity,short max_names);\nstatic char *E2R_ActionCodeName(short *action);\nstatic short *E2R_FindActionCodeBySuffix(char *suffix);\n\nstatic void E2R_TraceIntroActionCandidate(char *suffix)\n{\n  short *action;\n  short *pool;\n  char *name;\n  uint offset;\n  uint token_count;\n\n  if (!E2R_StartupDiagEnabled()) {\n    return;\n  }\n  action = E2R_FindActionCodeBySuffix(suffix);\n  if (action == (short *)0x0 || IsBadReadPtr(action,0xe)) {\n    fprintf(stderr,\"intro action candidate: suffix=%s node=0x0 name=(null) code=-1 tokens=(missing)\\n\",\n            suffix != (char *)0x0 ? suffix : \"(null)\");\n    return;\n  }\n  name = E2R_ActionCodeName(action);\n  offset = *(uint *)(action + 3);\n  pool = (short *)(uintptr_t)_DAT_006366a0;\n  fprintf(stderr,\"intro action candidate: suffix=%s node=0x%lx name=%s code=0x%x tokens=\",\n          suffix != (char *)0x0 ? suffix : \"(null)\",\n          (unsigned long)(uintptr_t)action,\n          name != (char *)0x0 ? name : \"(null)\",offset);\n  if (pool != (short *)0x0 && offset < 19984 &&\n      !IsBadReadPtr(pool + offset,16 * sizeof(short))) {\n    for (token_count = 0; token_count < 16; token_count = token_count + 1) {\n      fprintf(stderr,\"%s%04x\",token_count == 0 ? \"\" : \",\",\n              (unsigned int)(ushort)pool[offset + token_count]);\n      if (pool[offset + token_count] == 0) {\n        break;\n      }\n    }\n  }\n  else {\n    fprintf(stderr,\"(unreadable)\");\n  }\n  fprintf(stderr,\"\\n\");\n}\n\nstatic int E2R_RequestIntroSkip(void)"
);
source = source.replace(
  "  scene_id = E2R_FindPackedNameIndex(s_Start_sc_00470c80,_DAT_006366bc,20000,0x9c4);",
  "  if (E2R_StartupDiagEnabled()) {\n    E2R_TraceIntroActionCandidate(s_StartGame_004725f4);\n    E2R_TraceIntroActionCandidate(\"horse6\");\n    E2R_TraceIntroActionCandidate(\"horse7\");\n    E2R_TraceIntroActionCandidate(\"horse8\");\n  }\n  scene_id = E2R_FindPackedNameIndex(s_Start_sc_00470c80,_DAT_006366bc,20000,0x9c4);"
);
source = source.replace(
  "  short scene_id;\n  ushort duration;\n  ushort progress;",
  "  short scene_id;\n  short horse_scene_id;\n  short actor_scene_id;\n  int actor_scene;\n  int is_direct_intro_action;\n  int is_horse_intro_scene;\n  ushort duration;\n  ushort progress;"
);
source = source.replace(
  "  action = *slot;\n  if (action != 0x937800 || ((*(byte *)((int)slot + 0xc) & 2) == 0)) {\n    return 0;\n  }\n  duration = *(ushort *)(slot + 1);",
  "  action = *slot;\n  actor_scene = 0;\n  actor_scene_id = -1;\n  if (!IsBadReadPtr((void *)(uintptr_t)(actor + 0x132),4)) {\n    actor_scene = E2R_NormalizeSceneRecordPointer(*(int *)(actor + 0x132));\n    if (actor_scene != 0) {\n      actor_scene_id = *(short *)(uintptr_t)actor_scene;\n    }\n  }\n  horse_scene_id = E2R_FindPackedNameIndex(\"horse\",_DAT_006366bc,20000,0x9c4);\n  is_direct_intro_action = action == 0x937800 && ((*(byte *)((int)slot + 0xc) & 2) != 0);\n  is_horse_intro_scene = horse_scene_id >= 0 && actor_scene_id == horse_scene_id;\n  if (!is_direct_intro_action && !is_horse_intro_scene) {\n    E2R_GameStateLog(\"intro skip ignored actor=0x%lx action=0x%lx actor_scene=0x%lx actor_scene_id=%d horse_scene=%d flags=0x%x\",\n                     (unsigned long)(uintptr_t)actor,\n                     (unsigned long)(uintptr_t)action,(unsigned long)(uintptr_t)actor_scene,\n                     (int)actor_scene_id,(int)horse_scene_id,\n                     (unsigned int)*(byte *)((int)slot + 0xc));\n    return 0;\n  }\n  duration = *(ushort *)(slot + 1);"
);
source = source.replace(
  "  E2R_GameStateLog(\"intro skip request scene=0x%lx actor=0x%lx action=0x%lx progress=%u duration=%u Start_sc=%d offset=%ld record=0x%lx\",\n                   (unsigned long)_DAT_0073cc3c,(unsigned long)(uintptr_t)actor,\n                   (unsigned long)(uintptr_t)action,(unsigned int)progress,\n                   (unsigned int)duration,(int)scene_id,",
  "  E2R_GameStateLog(\"intro skip request scene=0x%lx actor=0x%lx action=0x%lx progress=%u duration=%u Start_sc=%d horse_scene=%d actor_scene_id=%d direct=%d horse=%d offset=%ld record=0x%lx\",\n                   (unsigned long)_DAT_0073cc3c,(unsigned long)(uintptr_t)actor,\n                   (unsigned long)(uintptr_t)action,(unsigned int)progress,\n                   (unsigned int)duration,(int)scene_id,(int)horse_scene_id,\n                   (int)actor_scene_id,is_direct_intro_action,is_horse_intro_scene,"
);
source = source.replace(
  "    E2R_scene_child_diag_count = 0;\n  }\n  FUN_0043a6e0((undefined4)(int)scene_id,(undefined4)(int)scene_id);",
  "    E2R_scene_child_diag_count = 0;\n    E2R_scene_child_activate_diag_count = 0;\n  }\n  FUN_0043a6e0((undefined4)(int)scene_id,(undefined4)(int)scene_id);"
);
source = source.replace(
  "  horse_scene_id = E2R_FindPackedNameIndex(\"horse\",_DAT_006366bc,20000,0x9c4);\n  is_direct_intro_action = action == 0x937800 && ((*(byte *)((int)slot + 0xc) & 2) != 0);\n  is_horse_intro_scene = horse_scene_id >= 0 && actor_scene_id == horse_scene_id;\n  if (!is_direct_intro_action && !is_horse_intro_scene) {",
  "  horse_scene_id = E2R_FindPackedNameIndex(\"horse\",_DAT_006366bc,20000,0x9c4);\n  scene_id = E2R_FindPackedNameIndex(s_Start_sc_00470c80,_DAT_006366bc,20000,0x9c4);\n  is_direct_intro_action = action == 0x937800 && ((*(byte *)((int)slot + 0xc) & 2) != 0);\n  is_horse_intro_scene = horse_scene_id >= 0 && actor_scene_id == horse_scene_id;\n  if (scene_id >= 0 && actor_scene_id == scene_id) {\n    DAT_00636850 = '\\0';\n    E2R_GameStateLog(\"intro skip ignored wait-only subintro actor=0x%lx action=0x%lx actor_scene_id=%d\",\n                     (unsigned long)(uintptr_t)actor,\n                     (unsigned long)(uintptr_t)action,(int)actor_scene_id);\n    return 0;\n  }\n  if (!is_direct_intro_action && !is_horse_intro_scene) {"
);
source = source.replace(
  "  if (E2R_StartupDiagEnabled()) {\n    E2R_TraceIntroActionCandidate(s_StartGame_004725f4);\n    E2R_TraceIntroActionCandidate(\"horse6\");\n    E2R_TraceIntroActionCandidate(\"horse7\");\n    E2R_TraceIntroActionCandidate(\"horse8\");\n  }\n  scene_id = E2R_FindPackedNameIndex(s_Start_sc_00470c80,_DAT_006366bc,20000,0x9c4);\n  if (scene_id < 0) {",
  "  if (E2R_StartupDiagEnabled()) {\n    E2R_TraceIntroActionCandidate(s_StartGame_004725f4);\n    E2R_TraceIntroActionCandidate(\"horse6\");\n    E2R_TraceIntroActionCandidate(\"horse7\");\n    E2R_TraceIntroActionCandidate(\"horse8\");\n  }\n  if (scene_id < 0) {"
);
source = source.replace(
  /(_DAT_0073ccba = (?!\(ushort\)scene_id\b)[^;\n]+;\n)/g,
  "$1  E2R_SyncSceneViewId();\n"
);
source = source.replace(
  "static int E2R_round_to_int",
  "static uintptr_t E2R_TraceMenuRequestFlag(const char *site, uintptr_t value)\n{\n  uintptr_t old_value = DAT_00479db4;\n  uintptr_t current = DAT_0047a470;\n  short word82 = 0;\n  short worde8 = 0;\n  int readable = E2R_IsReadableCurrentPointer(current);\n\n  if (readable) {\n    word82 = *(short *)(current + 0x82);\n    worde8 = *(short *)(current + 0xe8);\n  }\n  if (E2R_requester_state_diag_count < 64) {\n    E2R_requester_state_diag_count = E2R_requester_state_diag_count + 1;\n    fprintf(stderr,\n            \"menu request flag write: site=%s old=%lu new=%lu \"\n            \"current=0x%lx readable=%d known_actor=%d w82=0x%x we8=%d \"\n            \"DAT_00479de8=%lu DAT_0047a76c=%lu requester_state=%lu \"\n            \"scene=0x%lx caller=%p\\n\",\n            site,(unsigned long)old_value,(unsigned long)value,\n            (unsigned long)current,readable,E2R_IsKnownActorPointer((int)current),\n            (unsigned int)(ushort)word82,(int)worde8,\n            (unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n            (unsigned long)_DAT_00643650,(unsigned long)_DAT_0073cc3c,\n            __builtin_return_address(0));\n  }\n  return value;\n}\n\nstatic int E2R_round_to_int"
);
source = source.replace(
  "  uintptr_t old_value = _DAT_00643650;\n\n  if (E2R_requester_state_diag_count < 64) {",
  "  uintptr_t old_value = _DAT_00643650;\n\n  E2R_GameStateLog(\"requester state write site=%s old=%lu new=%lu mode=%lu dialog=%lu requester=0x%x scene=0x%lx\",\n                   site,(unsigned long)old_value,(unsigned long)value,\n                   (unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n                   (unsigned int)E2R_WORD_AT(DAT_0047a45e,2),\n                   (unsigned long)_DAT_0073cc3c);\n  if (E2R_requester_state_diag_count < 64) {"
);
source = source.replace(
  "static uintptr_t E2R_TraceRequesterState(const char *site, uintptr_t value)\n{",
  "static int E2R_MenuDiagEnabled(void)\n{\n  static int initialized;\n  static int enabled;\n  char *value;\n\n  if (initialized == 0) {\n    value = getenv(\"E2R_MENU_DIAG\");\n    enabled = value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n    initialized = 1;\n  }\n  return enabled;\n}\n\nstatic const char *E2R_RequesterActionName(uintptr_t action)\n{\n  if (action == (uintptr_t)&LAB_0043c594) return \"confirm_yes\";\n  if (action == (uintptr_t)&LAB_0043d458) return \"start_male\";\n  if (action == (uintptr_t)&LAB_0043d464) return \"start_female\";\n  if (action == (uintptr_t)&LAB_0043d470) return \"settings\";\n  if (action == (uintptr_t)&LAB_0043d47c) return \"save\";\n  if (action == (uintptr_t)&LAB_0043d490) return \"load\";\n  if (action == (uintptr_t)&DAT_0043d49c) return \"quit_prompt\";\n  if (action == (uintptr_t)&DAT_0043d4c0) return \"noop\";\n  if (action == (uintptr_t)&LAB_0043d728) return \"settings_music\";\n  if (action == (uintptr_t)&LAB_0043d7a0) return \"settings_sfx\";\n  if (action == (uintptr_t)&LAB_0043d7f0) return \"settings_difficulty\";\n  if (action == (uintptr_t)&LAB_0043d6e4) return \"settings_resolution\";\n  if (action == (uintptr_t)&LAB_0043d83c) return \"ok\";\n  if (action == (uintptr_t)&LAB_0043c4e8) return \"cancel\";\n  if (action == (uintptr_t)&LAB_0043fadc) return \"load_slot\";\n  if (action == (uintptr_t)&LAB_0043fb58) return \"save_slot\";\n  return \"unknown\";\n}\n\nstatic uintptr_t E2R_TraceRequesterState(const char *site, uintptr_t value)\n{"
);
source = source.replace(
  "  uintptr_t old_value = _DAT_00643650;\n\n  E2R_GameStateLog(\"requester state write site=%s old=%lu new=%lu mode=%lu dialog=%lu requester=0x%x scene=0x%lx\",",
  "  uintptr_t old_value = _DAT_00643650;\n\n  if (E2R_MenuDiagEnabled()) {\n    fprintf(stderr,\n            \"menu state: site=%s old=%lu new=%lu requester=0x%x selected=0x%lx \"\n            \"mode=%lu dialog=%lu menu_request=%lu scene=0x%lx current=0x%lx\\n\",\n            site,(unsigned long)old_value,(unsigned long)value,\n            (unsigned int)E2R_WORD_AT(DAT_0047a45e,2),\n            (unsigned long)_DAT_00643430,\n            (unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n            (unsigned long)DAT_00479db4,(unsigned long)_DAT_0073cc3c,\n            (unsigned long)DAT_0047a470);\n  }\n  E2R_GameStateLog(\"requester state write site=%s old=%lu new=%lu mode=%lu dialog=%lu requester=0x%x scene=0x%lx\","
);
source = source.replace(
  "    word82 = *(short *)(current + 0x82);\n    worde8 = *(short *)(current + 0xe8);\n  }\n  if (E2R_requester_state_diag_count < 64) {",
  "    word82 = *(short *)(current + 0x82);\n    worde8 = *(short *)(current + 0xe8);\n  }\n  E2R_GameStateLog(\"menu request flag write site=%s old=%lu new=%lu current=0x%lx readable=%d known_actor=%d mode=%lu dialog=%lu state=%lu scene=0x%lx\",\n                   site,(unsigned long)old_value,(unsigned long)value,\n                   (unsigned long)current,readable,E2R_IsKnownActorPointer((int)current),\n                   (unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n                   (unsigned long)_DAT_00643650,(unsigned long)_DAT_0073cc3c);\n  if (E2R_requester_state_diag_count < 64) {"
);
source = source.replace(
  "static void E2R_TraceStartGameStage(const char *stage)",
  "static void E2R_TraceFrameStage(const char *stage)\n{\n  if (E2R_frame_stage_diag_count < 96) {\n    E2R_frame_stage_diag_count = E2R_frame_stage_diag_count + 1;\n    fprintf(stderr,\n            \"frame stage: %s DAT_00479de8=%lu DAT_0047a76c=%lu \"\n            \"DAT_0047a3b4=%lu DAT_0047a428=%lu DAT_0047ab20=%ld \"\n            \"current=0x%lx actors=0x%lx links=0x%lx scene=0x%lx caller=%p\\n\",\n            stage,(unsigned long)DAT_00479de8,(unsigned long)DAT_0047a76c,\n            (unsigned long)DAT_0047a3b4,(unsigned long)DAT_0047a428,\n            (long)DAT_0047ab20,(unsigned long)DAT_0047a470,\n            (unsigned long)_DAT_0063726c,(unsigned long)_DAT_00637248,\n            (unsigned long)_DAT_0073cc3c,__builtin_return_address(0));\n  }\n}\n\nstatic void E2R_TraceStartGameStage(const char *stage)"
);
source = source.replace(
  "static void E2R_TraceStartGameStage(const char *stage)",
  "static void E2R_TraceActorLoopStage(const char *stage, uintptr_t actor, uint guard)\n{\n  int actor_bad = actor == 0 || IsBadReadPtr((void *)actor,0x136);\n  uintptr_t dep = 0;\n  uintptr_t next = 0;\n  uintptr_t local_132 = 0;\n  int dep_bad = 1;\n  unsigned byte2 = 0;\n  unsigned byte3 = 0;\n  unsigned byteb3 = 0;\n  unsigned dep_c = 0;\n  short word82 = 0;\n\n  if (!actor_bad) {\n    dep = *(uint *)(actor + 0xa6);\n    next = *(uint *)(actor + 0x4c);\n    local_132 = *(uint *)(actor + 0x132);\n    byte2 = *(byte *)(actor + 2);\n    byte3 = *(byte *)(actor + 3);\n    byteb3 = *(byte *)(actor + 0xb3);\n    word82 = *(short *)(actor + 0x82);\n    dep_bad = dep == 0 || IsBadReadPtr((void *)dep,0x10);\n    if (!dep_bad) {\n      dep_c = *(byte *)(dep + 0xc);\n    }\n  }\n  if (E2R_actor_loop_diag_count < 128) {\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    fprintf(stderr,\n            \"actor loop: %s guard=%lu actor=0x%lx bad=%d next=0x%lx \"\n            \"dep=0x%lx dep_bad=%d dep_c=0x%x w82=0x%x b2=0x%x b3=0x%x \"\n            \"bb3=0x%x p132=0x%lx scene=0x%lx caller=%p\\n\",\n            stage,(unsigned long)guard,(unsigned long)actor,actor_bad,\n            (unsigned long)next,(unsigned long)dep,dep_bad,dep_c,\n            (unsigned int)(ushort)word82,byte2,byte3,byteb3,\n            (unsigned long)local_132,(unsigned long)_DAT_0073cc3c,\n            __builtin_return_address(0));\n  }\n}\n\nstatic void E2R_TraceStartGameStage(const char *stage)"
);
source = source.replace(
  "static void E2R_TraceStartGameStage(const char *stage)",
  "static void E2R_TraceActorUpdateStage(const char *stage, short *actor)\n{\n  uintptr_t value = (uintptr_t)actor;\n  int actor_bad = value == 0 || IsBadReadPtr(actor,0x180);\n  uintptr_t action = 0;\n  uintptr_t rep = 0;\n  uintptr_t target = 0;\n  uintptr_t queued1 = 0;\n  uintptr_t queued2 = 0;\n  uintptr_t late = 0;\n  short state = 0;\n  short rep_id = 0;\n  short state91 = 0;\n  short word74 = 0;\n  short word76 = 0;\n  short wordba = 0;\n  unsigned byte2 = 0;\n  unsigned byte3 = 0;\n  unsigned bytea3 = 0;\n  unsigned byteb3 = 0;\n  unsigned byteb6 = 0;\n\n  if (!actor_bad) {\n    action = *(uint *)(value + 0xa6);\n    rep = *(uint *)(value + 0x11e);\n    target = *(uint *)(value + 0x1e);\n    queued1 = *(uint *)(value + 0x126);\n    queued2 = *(uint *)(value + 0x12a);\n    late = *(uint *)(value + 0x17c);\n    state = actor[0x41];\n    rep_id = actor[0x90];\n    state91 = actor[0x91];\n    word74 = actor[0x74];\n    word76 = actor[0x76];\n    wordba = actor[0xba];\n    byte2 = *(byte *)(value + 2);\n    byte3 = *(byte *)(value + 3);\n    bytea3 = *(byte *)(value + 0xa3);\n    byteb3 = *(byte *)(value + 0xb3);\n    byteb6 = *(byte *)(value + 0xb6);\n  }\n  if (E2R_actor_update_diag_count < 192) {\n    E2R_actor_update_diag_count = E2R_actor_update_diag_count + 1;\n    fprintf(stderr,\n            \"actor update: %s actor=0x%lx bad180=%d current=0x%lx scene=0x%lx \"\n            \"state=%d action=0x%lx rep=0x%lx rep_id=%d state91=%d \"\n            \"target=0x%lx queued=%lx/%lx late=0x%lx w74=%d w76=%d wba=%d \"\n            \"b2=0x%x b3=0x%x ba3=0x%x bb3=0x%x bb6=0x%x caller=%p\\n\",\n            stage,(unsigned long)value,actor_bad,(unsigned long)DAT_0047a470,\n            (unsigned long)_DAT_0073cc3c,(int)state,(unsigned long)action,\n            (unsigned long)rep,(int)rep_id,(int)state91,(unsigned long)target,\n            (unsigned long)queued1,(unsigned long)queued2,(unsigned long)late,\n            (int)word74,(int)word76,(int)wordba,byte2,byte3,bytea3,byteb3,byteb6,\n            __builtin_return_address(0));\n  }\n}\n\nstatic void E2R_TraceStartGameStage(const char *stage)"
);
source = source.replace(
  "static void E2R_TraceStartGameStage(const char *stage)",
  "static int E2R_RepIdIsMissing(short rep_id)\n{\n  if (rep_id < 0 || 500 <= rep_id) {\n    return 0;\n  }\n  return *(int *)((undefined1 *)0x00635980 + rep_id * 4) == 0 &&\n         *(int *)(0x00663a10 + rep_id * 4) < 0;\n}\n\nstatic int E2R_ActorMotionRef(short *actor)\n{\n  int side;\n  int ref;\n\n  if (actor == (short *)0x0 || IsBadReadPtr(actor,0x58)) {\n    return 0;\n  }\n  side = *(int *)(actor + 0x2a);\n  ref = 0;\n  if (side != 0 && !IsBadReadPtr((void *)(uintptr_t)side,0xc)) {\n    ref = *(int *)(side + 8);\n  }\n  if (ref == 0) {\n    ref = *(int *)(actor + 0xf);\n  }\n  if (ref != 0 && IsBadReadPtr((void *)(uintptr_t)ref,0x86)) {\n    ref = 0;\n  }\n  return ref;\n}\n\nstatic int E2R_ActorSideLinkedAction(short *actor, int offset)\n{\n  int side;\n  int linked;\n\n  if (actor == (short *)0x0 || IsBadReadPtr(actor,0x58)) {\n    return 0;\n  }\n  side = *(int *)(actor + 0x2a);\n  if (side == 0 || IsBadReadPtr((void *)(uintptr_t)side,(UINT_PTR)(offset + 4))) {\n    return 0;\n  }\n  linked = *(int *)(side + offset);\n  if (linked == 0 || IsBadReadPtr((void *)(uintptr_t)linked,0x13e)) {\n    return 0;\n  }\n  return *(int *)(linked + 0x13a);\n}\n\nstatic void E2R_RetainCurrentRepForMissingTarget(const char *site, short *actor)\n{\n  uintptr_t rep;\n  short current_rep;\n  short desired_rep;\n  short actor_id;\n\n  if (actor == (short *)0x0 || IsBadReadPtr(actor,0x124)) {\n    return;\n  }\n  rep = *(uint *)((uintptr_t)actor + 0x11e);\n  actor_id = *actor;\n  if (rep != 0 && !IsBadReadPtr((void *)rep,2)) {\n    current_rep = *(short *)rep;\n    if (-1 < actor_id && actor_id < 5000 && 0 <= current_rep && current_rep < 500) {\n      E2R_actor_visible_rep_fallback[actor_id] = current_rep;\n      E2R_actor_visible_rep_fallback_valid[actor_id] = 1;\n    }\n  }\n  else if (-1 < actor_id && actor_id < 5000 &&\n           E2R_actor_visible_rep_fallback_valid[actor_id] != 0) {\n    current_rep = E2R_actor_visible_rep_fallback[actor_id];\n  }\n  else {\n    return;\n  }\n  desired_rep = actor[0x91];\n  if (current_rep < 0 || 500 <= current_rep || current_rep == desired_rep ||\n      !E2R_RepIdIsMissing(desired_rep)) {\n    return;\n  }\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_update_diag_count < 192) {\n    E2R_actor_update_diag_count = E2R_actor_update_diag_count + 1;\n    fprintf(stderr,\n            \"actor rep retain: site=%s actor=0x%lx rep=0x%lx current=%d missing=%d\\n\",\n            site,(unsigned long)(uintptr_t)actor,(unsigned long)rep,\n            (int)current_rep,(int)desired_rep);\n  }\n  actor[0x91] = current_rep;\n}\n\nstatic void E2R_TraceStartGameStage(const char *stage)"
);
for (const [from, to] of [
  ["        _DAT_00643650 = 6;", "        _DAT_00643650 = E2R_TraceRequesterState(\"action.confirm_yes\",6);"],
  ["    _DAT_00643650 = 0;", "    _DAT_00643650 = E2R_TraceRequesterState(\"action.start_male\",0);"],
  ["    _DAT_00643650 = 1;", "    _DAT_00643650 = E2R_TraceRequesterState(\"action.start_female\",1);"],
  ["    _DAT_00643650 = 2;", "    _DAT_00643650 = E2R_TraceRequesterState(\"action.load\",2);"],
  ["      _DAT_00643650 = 3;", "      _DAT_00643650 = E2R_TraceRequesterState(\"action.save\",3);"],
  ["    _DAT_00643650 = 4;", "    _DAT_00643650 = E2R_TraceRequesterState(\"action.options\",4);"],
  [
    "    _DAT_00643650 = ((int)FUN_0043c910((undefined4)prompt,0) != 0) ? 6 : 5;",
    "    _DAT_00643650 = E2R_TraceRequesterState(\"action.quit_prompt\",\n                                            ((int)FUN_0043c910((undefined4)prompt,0) != 0) ? 6 : 5);"
  ],
  ["        _DAT_00643650 = 5;", "        _DAT_00643650 = E2R_TraceRequesterState(\"action.confirm_no\",5);"],
  ["      _DAT_00643650 = 5;", "      _DAT_00643650 = E2R_TraceRequesterState(\"action.cancel_start\",5);"],
  [
    "    _DAT_00643650 = 5;\n    requester_id = 0x28;",
    "    _DAT_00643650 = E2R_TraceRequesterState(\"15d40.open_menu_default\",5);\n    requester_id = 0x28;"
  ],
]) {
  source = source.replace(from, to);
}
for (const [from, to] of [
  ["      DAT_00479db4 = 0;", "      DAT_00479db4 = E2R_TraceMenuRequestFlag(\"15d40.consume_menu_request\",0);"],
  ["      DAT_00479db4 = 1;", "      DAT_00479db4 = E2R_TraceMenuRequestFlag(\"42a70c.dead_current\",1);"],
  ["          DAT_00479db4 = 1;", "          DAT_00479db4 = E2R_TraceMenuRequestFlag(\"44f508.op44_menu_request\",1);"],
]) {
  source = source.replace(from, to);
}
for (const [from, to] of [
  ["_DAT_0073cc3c = 0;", "_DAT_0073cc3c = E2R_TraceScenePointerWrite(\"scene.clear\",0);"],
  ["_DAT_0073cc3c = extraout_EDX;", "_DAT_0073cc3c = E2R_TraceScenePointerWrite(\"scene.extraout_EDX\",extraout_EDX);"],
  ["_DAT_0073cc3c = in_EAX;", "_DAT_0073cc3c = E2R_TraceScenePointerWrite(\"scene.select_record\",in_EAX);"],
]) {
  source = source.split(from).join(to);
}
source = source.replace(
  "  if (DAT_0047a3b4 == 0) {\n    FUN_004211c8((int)psVar10,psVar12);",
  "  E2R_TraceFrameStage(\"42a70c.before-render-epilogue\");\n  if (DAT_0047a3b4 == 0) {\n    E2R_TraceFrameStage(\"42a70c.enter-render-epilogue\");\n    FUN_004211c8((int)psVar10,psVar12);\n    E2R_TraceFrameStage(\"42a70c.after-211c8\");"
);
source = source.replace(
  "    FUN_00421a14();\n    FUN_00421f54(extraout_ECX_12);\n    E2R_TraceFrameStage(\"42a70c.before-22238\");",
  "    FUN_00421a14();\n    E2R_TraceFrameStage(\"42a70c.after-21a14\");\n    FUN_00421f54(extraout_ECX_12);\n    E2R_TraceFrameStage(\"42a70c.after-21f54\");\n    E2R_TraceFrameStage(\"42a70c.before-22238\");"
);
source = source.replace(
  "      FUN_004249f4((undefined4)(uintptr_t)iVar4);\n      iVar4 = extraout_EDX_00;\n    }\n    iVar4 = *(int *)(iVar4 + 0x4c);",
  "      FUN_004249f4((undefined4)(uintptr_t)iVar4);\n    }\n    iVar4 = *(int *)(iVar4 + 0x4c);"
);
source = source.replace(
  "    uVar14 = FUN_00422238(extraout_ECX_13,extraout_EDX_01);\n    psVar12 = (short *)((ulonglong)uVar14 >> 0x20);",
  "    E2R_TraceFrameStage(\"42a70c.before-22238\");\n    uVar14 = FUN_00422238(extraout_ECX_13,extraout_EDX_01);\n    E2R_TraceFrameStage(\"42a70c.after-22238\");\n    psVar12 = (short *)((ulonglong)uVar14 >> 0x20);"
);
source = source.replace(
  "  if (DAT_0047ab20 < 0) {\n    DAT_0047ab20 = 0;",
  "  E2R_TraceFrameStage(\"42a70c.before-ab20-branch\");\n  if (DAT_0047ab20 < 0) {\n    E2R_TraceFrameStage(\"42a70c.enter-ab20-negative\");\n    DAT_0047ab20 = 0;"
);
source = source.replace(
  "  else {\n    iVar9 = DAT_0047a470;",
  "  else {\n    E2R_TraceFrameStage(\"42a70c.enter-ab20-nonnegative\");\n    iVar9 = DAT_0047a470;"
);
source = source.replace(
  "    if ((DAT_0047a470 == 0) ||\n       ((*(short *)(DAT_0047a470 + 0x82) == 0xb && (*(short *)(DAT_0047a470 + 0xe8) < 1)))) {\n      DAT_00479db4 = E2R_TraceMenuRequestFlag(\"42a70c.dead_current\",1);\n    }",
  "    if (DAT_0047a470 != 0 && !IsBadReadPtr((void *)(uintptr_t)DAT_0047a470,0xea) &&\n        *(short *)(DAT_0047a470 + 0x82) == 0xb && *(short *)(DAT_0047a470 + 0xe8) < 1) {\n      DAT_00479db4 = E2R_TraceMenuRequestFlag(\"42a70c.dead_current\",1);\n    }"
);
source = source.replace(
  "void __fastcall FUN_0041868c(int param_1,int param_2,int param_3,int param_4)\n\n{\n  int in_EAX;\n  int iVar1;\n  int iVar2;\n  undefined4 *puVar3;",
  "void __fastcall FUN_0041868c(int param_1,int param_2,int param_3,int param_4)\n\n{\n  int in_EAX;\n  int iVar1;\n  int iVar2;\n  int row_bytes;\n  int src_surface;\n  int dst_surface;\n  size_t copy_span;\n  undefined4 *puVar3;"
);
source = source.replace(
  "  iVar2 = param_1 * _DAT_006401ec * 2;\n  puVar4 = (undefined4 *)(unaff_EBX * 2 + *(int *)(&DAT_00636668 + param_2 * 4) + iVar2);\n  iVar7 = 0;\n  iVar1 = param_3 + 1 >> 1;\n  puVar5 = (undefined4 *)(*(int *)(&DAT_00636668 + in_EAX * 4) + unaff_EBX * 2 + iVar2);",
  "  dst_surface = param_2;\n  src_surface = in_EAX;\n  if ((uint)dst_surface > 3 || _DAT_006401ec <= 0 || _DAT_006401d4 <= 0 ||\n      param_1 < 0 || param_3 <= 0 || param_4 <= 0 || _DAT_006401ec > 0x1000 ||\n      _DAT_006401d4 > 0x1000) {\n    return;\n  }\n  if ((uint)src_surface > 3) {\n    src_surface = dst_surface == 0 ? 1 : 0;\n  }\n  if (param_1 == 0 && param_3 == _DAT_006401ec && param_4 == _DAT_006401d4) {\n    unaff_EBX = 0;\n  }\n  if (unaff_EBX < 0 || _DAT_006401ec <= unaff_EBX ||\n      _DAT_006401ec - unaff_EBX < param_3 || _DAT_006401d4 - param_1 < param_4 ||\n      *(int *)(&DAT_00636668 + dst_surface * 4) == 0 ||\n      *(int *)(&DAT_00636668 + src_surface * 4) == 0) {\n    return;\n  }\n  row_bytes = ((param_3 + 1) >> 1) * 4;\n  copy_span = (size_t)(param_4 - 1) * (size_t)_DAT_006401ec * 2 + (size_t)row_bytes;\n  iVar2 = param_1 * _DAT_006401ec * 2;\n  puVar4 = (undefined4 *)(unaff_EBX * 2 + *(int *)(&DAT_00636668 + dst_surface * 4) + iVar2);\n  iVar7 = 0;\n  iVar1 = param_3 + 1 >> 1;\n  puVar5 = (undefined4 *)(*(int *)(&DAT_00636668 + src_surface * 4) + unaff_EBX * 2 + iVar2);\n  if (E2R_IsBadWritePtr(puVar4,copy_span) || IsBadReadPtr(puVar5,copy_span)) {\n    return;\n  }"
);
source = source.replace(
  "    _DAT_0073cc3c = E2R_TraceScenePointerWrite(\"scene.clear\",0);\n    _DAT_0047a3be = 0;",
  "    _DAT_0073cc3c = E2R_TraceScenePointerWrite(\"scene.clear\",0);\n    E2R_TraceFrameStage(\"26df8.after-scene-clear\");\n    _DAT_0047a3be = 0;"
);
source = source.replace(
  "        FUN_00415d40(extraout_ECX,iVar1);\n        uVar3 = FUN_0042a70c(extraout_ECX_00,extraout_EDX);",
  "        E2R_TraceFrameStage(\"26df8.before-15d40\");\n        FUN_00415d40(extraout_ECX,iVar1);\n        E2R_TraceFrameStage(\"26df8.after-15d40\");\n        E2R_TraceFrameStage(\"26df8.before-42a70c\");\n        uVar3 = FUN_0042a70c(extraout_ECX_00,extraout_EDX);\n        E2R_TraceFrameStage(\"26df8.after-42a70c\");"
);
source = source.replace(
  "  int iVar9;\n  undefined4 extraout_ECX;",
  "  int iVar9;\n  int next_actor;\n  uint actor_loop_guard;\n  undefined4 extraout_ECX;"
);
source = source.replace(
  "  int next_actor;\n  uint actor_loop_guard;\n  undefined4 extraout_ECX;",
  "  int next_actor;\n  uint actor_loop_guard;\n  uint timing_loop_guard;\n  undefined4 extraout_ECX;"
);
source = source.replace(
  "  uVar13 = extraout_ECX;\n  uVar4 = _DAT_00640194;\n  while (_DAT_00640194 = uVar4, _DAT_0063737c == iVar7) {",
  "  E2R_TraceFrameStage(\"42a70c.entry\");\n  uVar13 = extraout_ECX;\n  uVar4 = _DAT_00640194;\n  timing_loop_guard = 0;\n  while (_DAT_00640194 = uVar4, _DAT_0063737c == iVar7) {\n    if (0x10000 <= timing_loop_guard) {\n      E2R_TraceFrameStage(\"42a70c.timer-loop-break\");\n      break;\n    }\n    timing_loop_guard = timing_loop_guard + 1;"
);
source = source.replace(
  "  iVar7 = _DAT_0063737c - iVar7;\n  if ((_DAT_006365a4 != 0) && (iVar7 = iVar7 / 3, iVar7 == 0)) {",
  "  E2R_TraceFrameStage(\"42a70c.after-timer-loop\");\n  iVar7 = _DAT_0063737c - iVar7;\n  if ((_DAT_006365a4 != 0) && (iVar7 = iVar7 / 3, iVar7 == 0)) {"
);
source = source.replace(
  "  _DAT_00637378 = iVar7;\n  if (DAT_0047a35c != 0) {",
  "  _DAT_00637378 = iVar7;\n  E2R_TraceFrameStage(\"42a70c.before-debug-fps\");\n  if (DAT_0047a35c != 0) {"
);
source = source.replace(
  "  lVar15 = FUN_0044e354();\n  psVar10 = extraout_ECX_03;",
  "  E2R_TraceFrameStage(\"42a70c.before-4e354\");\n  lVar15 = FUN_0044e354();\n  E2R_TraceFrameStage(\"42a70c.after-4e354\");\n  psVar10 = extraout_ECX_03;"
);
source = source.replace(
  "  iVar8 = _DAT_0063726c;\n  while( true ) {\n    if (iVar8 == 0) break;",
  "  iVar8 = _DAT_0063726c;\n  actor_loop_guard = 0;\n  while( true ) {\n    if (iVar8 == 0) break;\n    if (0x4000 <= actor_loop_guard || IsBadReadPtr((void *)(uintptr_t)iVar8,0x136)) {\n      E2R_TraceActorLoopStage(\"42a70c.actor-loop-break\",(uintptr_t)iVar8,actor_loop_guard);\n      break;\n    }\n    actor_loop_guard = actor_loop_guard + 1;\n    E2R_TraceActorLoopStage(\"42a70c.actor-loop-top\",(uintptr_t)iVar8,actor_loop_guard);"
);
source = source.replace(
  "    iVar8 = *(int *)(iVar8 + 0x4c);\n  }\n  local_3c = (short *)0x0;",
  "    next_actor = *(int *)(iVar8 + 0x4c);\n    if (next_actor == iVar8) {\n      E2R_TraceActorLoopStage(\"42a70c.actor-loop-self-link\",(uintptr_t)iVar8,actor_loop_guard);\n      break;\n    }\n    iVar8 = next_actor;\n  }\n  local_3c = (short *)0x0;"
);
source = source.replace(
  "        lVar15 = FUN_00427584((undefined4)(uintptr_t)iVar8,iVar7);\n        psVar10 = extraout_ECX_10;",
  "        E2R_TraceActorLoopStage(\"42a70c.before-27584\",(uintptr_t)iVar8,actor_loop_guard);\n        E2R_TraceFrameStage(\"42a70c.before-27584\");\n        lVar15 = FUN_00427584((undefined4)(uintptr_t)iVar8,iVar7);\n        E2R_TraceFrameStage(\"42a70c.after-27584\");\n        E2R_TraceActorLoopStage(\"42a70c.after-27584\",(uintptr_t)iVar8,actor_loop_guard);\n        psVar10 = extraout_ECX_10;"
);
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
source = source.replace(
  /(undefined8 __fastcall FUN_0043b384\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined4 extraout_EDX_02;\r?\n\s*)short \*psVar8;/,
  "$1int mouse_state;\n  short *psVar8;"
);
source = source.replace(
  "  if (DAT_0047a470 != (short *)0x0) {\n    ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] = ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] | 2;\n  }",
  "  if (DAT_0047a470 != (short *)0x0 && E2R_IsReadableCurrentPointer(DAT_0047a470)) {\n    ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] = ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] | 2;\n  }"
);
source = source.replace(
  "  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 0xf;\n  FUN_0041ab4c((*(int *)(in_EAX + 8) >> 0x10) + -1,*(int *)(in_EAX + 7) >> 0x10,\n               (*(int *)(in_EAX + 10) >> 0x10) + -1);\n  *(undefined2 *)((DAT_0047a279 >> 0x18) * 2 + 0x6366a8) = 1;\n  FUN_0041b078(extraout_ECX_00,(short)((uint)*(undefined4 *)(in_EAX + 7) >> 0x10));\n  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 8;\n  FUN_0041b34c(extraout_ECX_01,*(int *)(in_EAX + 7) >> 0x10);\n  FUN_0041b34c(extraout_ECX_02,*(int *)(in_EAX + 8) >> 0x10);\n  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 0xe;\n  FUN_0041b078(extraout_ECX_03,(short)((uint)*(undefined4 *)(in_EAX + 8) >> 0x10) + -1);\n  FUN_0041b34c(extraout_ECX_04,(*(int *)(in_EAX + 8) >> 0x10) + -1);\n  FUN_0041b34c(extraout_ECX_05,*(int *)(in_EAX + 7) >> 0x10);",
  "  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 0xf;\n  E2R_FillHostedRect(*(int *)(in_EAX + 7) >> 0x10,*(int *)(in_EAX + 9) >> 0x10,\n                     (*(int *)(in_EAX + 8) >> 0x10) + -1,\n                     (*(int *)(in_EAX + 10) >> 0x10) + -1);\n  *(undefined2 *)((DAT_0047a279 >> 0x18) * 2 + 0x6366a8) = 1;\n  E2R_DrawHostedRectBorder(*(int *)(in_EAX + 7) >> 0x10,*(int *)(in_EAX + 9) >> 0x10,\n                           (*(int *)(in_EAX + 8) >> 0x10) + -1,\n                           (*(int *)(in_EAX + 10) >> 0x10) + -1);"
);
source = source.replace(
  "  FUN_0041bcc8(param_1);\n  bVar10 = DAT_0047a4f8 != 0;",
  "  FUN_0041bcc8(param_1);\n  E2R_SaveHostedRequesterBackdrop();\n  bVar10 = DAT_0047a4f8 != 0;"
);
source = source.replace(
  "  for (psVar8 = *(short **)(in_EAX + 6); psVar8 != (short *)0x0; psVar8 = *(short **)(psVar8 + 9)) {\n    FUN_0043b9bc(uVar4,psVar8);\n    uVar4 = extraout_ECX_08;\n    uVar7 = extraout_EDX_01;\n    uVar5 = extraout_var_01;\n  }\n  uVar11 = CONCAT44(uVar7,CONCAT22(uVar5,E2R_WORD_AT(DAT_0047a45e,2)));",
  "  for (psVar8 = *(short **)(in_EAX + 6); psVar8 != (short *)0x0; psVar8 = *(short **)(psVar8 + 9)) {\n    FUN_0043b9bc(uVar4,psVar8);\n    uVar4 = extraout_ECX_08;\n    uVar7 = extraout_EDX_01;\n    uVar5 = extraout_var_01;\n  }\n  E2R_DrawHostedRequesterLabels(in_EAX);\n  uVar11 = CONCAT44(uVar7,CONCAT22(uVar5,E2R_WORD_AT(DAT_0047a45e,2)));"
);
source = source.replace(
  "  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 0xf;\n  FUN_0041ab4c((*(int *)(puVar3 + 8) >> 0x10) + -1,*(int *)(puVar3 + 7) >> 0x10,\n               (*(int *)(puVar3 + 10) >> 0x10) + -1);\n  *(undefined2 *)((DAT_0047a279 >> 0x18) * 2 + 0x6366a8) = 1;\n  FUN_0041b078(extraout_ECX,(short)((uint)*(undefined4 *)(puVar3 + 7) >> 0x10));\n  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 8;\n  FUN_0041b34c(extraout_ECX_00,*(int *)(puVar3 + 7) >> 0x10);\n  FUN_0041b34c(extraout_ECX_01,*(int *)(puVar3 + 8) >> 0x10);\n  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 0xe;\n  FUN_0041b078(extraout_ECX_02,(short)((uint)*(undefined4 *)(puVar3 + 8) >> 0x10) + -1);\n  FUN_0041b34c(extraout_ECX_03,(*(int *)(puVar3 + 8) >> 0x10) + -1);\n  FUN_0041b34c(extraout_ECX_04,*(int *)(puVar3 + 7) >> 0x10);",
  "  *(undefined2 *)((undefined1 *)0x006366dc + (DAT_0047a279 >> 0x18) * 2) = 0xf;\n  E2R_FillHostedRect(*(int *)(puVar3 + 7) >> 0x10,*(int *)(puVar3 + 9) >> 0x10,\n                     (*(int *)(puVar3 + 8) >> 0x10) + -1,\n                     (*(int *)(puVar3 + 10) >> 0x10) + -1);\n  *(undefined2 *)((DAT_0047a279 >> 0x18) * 2 + 0x6366a8) = 1;\n  E2R_DrawHostedRectBorder(*(int *)(puVar3 + 7) >> 0x10,*(int *)(puVar3 + 9) >> 0x10,\n                           (*(int *)(puVar3 + 8) >> 0x10) + -1,\n                           (*(int *)(puVar3 + 10) >> 0x10) + -1);"
);
source = source.replace(
  "    FUN_0041ab4c((*(int *)(param_2 + 0xb) >> 0x10) + -1,*(int *)(param_2 + 10) >> 0x10,\n                 (*(int *)(param_2 + 0xd) >> 0x10) + -1);",
  "    E2R_FillHostedRect(param_2[0xb],param_2[0xd],param_2[0xc] + -1,param_2[0xe] + -1);"
);
source = source.replace(
  "    FUN_0041b078(extraout_ECX,(short)((uint)*(undefined4 *)(param_2 + 10) >> 0x10) + -1);\n    FUN_0041b34c(extraout_ECX_00,(*(int *)(param_2 + 10) >> 0x10) + -1);\n    uVar4 = extraout_ECX_01;\n    if ((*(byte *)((int)param_2 + 0x11) & 4) == 0) {\n      FUN_0041b34c(extraout_ECX_01,(*(int *)(param_2 + 0xb) >> 0x10) + 1);\n      uVar4 = extraout_ECX_02;\n    }",
  "    E2R_DrawHostedRectBorder(param_2[0xb],param_2[0xd],param_2[0xc] + -1,param_2[0xe] + -1);\n    uVar4 = extraout_ECX_02;"
);
source = source.replace(
  "    FUN_0041b078(uVar4,(short)((uint)*(undefined4 *)(param_2 + 0xb) >> 0x10));\n    FUN_0041b34c(extraout_ECX_03,*(int *)(param_2 + 0xb) >> 0x10);\n    if ((*(byte *)((int)param_2 + 0x11) & 2) == 0) {\n      FUN_0041b34c(extraout_ECX_04,(*(int *)(param_2 + 10) >> 0x10) + -1);\n    }\n",
  ""
);
source = source.replace(
  "  int extraout_ECX_06;\n  uint uVar5;",
  "  int extraout_ECX_06;\n  int text_x;\n  uint uVar5;"
);
source = source.replace(
  "    FUN_0041b078(iVar3,(short)(param_2[0xd] + 1));\n    FUN_00418770(extraout_ECX_05,*(byte **)(param_2 + 4));",
  "    text_x = iVar3;\n    FUN_0041b078(text_x,(short)(param_2[0xd] + 1));\n    FUN_00418770(extraout_ECX_05,*(byte **)(param_2 + 4));"
);
source = source.replace(
  "      iVar3 = extraout_ECX_06 + (uint)uVar2;",
  "      iVar3 = text_x + (uint)uVar2;"
);
source = source.replace(
  "        uVar11 = FUN_0041ba7c(iVar2,(int)(uVar11 >> 0x20));\n        if ((uVar11 & 2) != 0) break;\n        if (extraout_ECX_09 == _DAT_0064342c) {\n          uVar11 = FUN_0041cfc0();\n          iVar2 = extraout_ECX_13;\n        }\n        else {\n          uVar11 = FUN_0043bd4c(extraout_ECX_09,_DAT_00643430);\n          iVar2 = extraout_ECX_12;\n        }\n      }\n      iVar2 = extraout_ECX_09;\n      if (extraout_ECX_09 != _DAT_0064342c) {\n        _DAT_0064342c = extraout_ECX_09;\n        uVar11 = FUN_0043b9bc(extraout_ECX_09,_DAT_00643430);\n        iVar2 = extraout_ECX_10;\n      }",
  "        uVar11 = FUN_0041ba7c(iVar2,(int)(uVar11 >> 0x20));\n        mouse_state = (int)uVar11;\n        if ((uVar11 & 2) != 0) break;\n        if (mouse_state == _DAT_0064342c) {\n          uVar11 = FUN_0041cfc0();\n          iVar2 = mouse_state;\n        }\n        else {\n          uVar11 = FUN_0043bd4c(mouse_state,_DAT_00643430);\n          iVar2 = mouse_state;\n        }\n      }\n      iVar2 = mouse_state;\n      if (mouse_state != _DAT_0064342c) {\n        _DAT_0064342c = mouse_state;\n        uVar11 = FUN_0043b9bc(mouse_state,_DAT_00643430);\n        iVar2 = mouse_state;\n      }"
);
source = source.replace(
  "      iVar3 = FUN_0043b708(iVar2,psVar8);\n      iVar2 = extraout_ECX_11;\n      uVar11 = CONCAT44(extraout_EDX_02,iVar3);",
  "      iVar3 = FUN_0043b708(iVar2,psVar8);\n      iVar2 = mouse_state;\n      uVar11 = CONCAT44(extraout_EDX_02,iVar3);\n      if (E2R_requester_continue_after_action != 0) {\n        E2R_requester_continue_after_action = 0;\n        _DAT_0064342c = 0;\n        _DAT_006443d0 = 0;\n        iVar2 = 0;\n        uVar11 = 0;\n      }"
);
source = source.replace(
  "          if (in_EAX != (short *)(undefined1 *)0x0047a684) {\n            uVar4 = FUN_0041bcfc(iVar2);\n          }",
  "          if (in_EAX != (short *)(undefined1 *)0x0047a684) {\n            E2R_RestoreHostedRequesterBackdrop();\n            uVar4 = FUN_0041bcfc(iVar2);\n          }"
);
source = source.replace(
  "  _DAT_0064342c = 0;\n  _DAT_006443d0 = (ushort)(in_EAX == (short *)(undefined1 *)0x0047a684);\n  iVar2 = 0;",
  "  _DAT_0064342c = 0;\n  _DAT_006443d0 = (ushort)(in_EAX == (short *)(undefined1 *)0x0047a684);\n  E2R_RequesterProbeFeedPendingMouse(E2R_WORD_AT(DAT_0047a45e,2));\n  iVar2 = 0;"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0043b384\(undefined4 param_1,undefined4 param_2\)[\s\S]*?for \(psVar8 = \*\(short \*\*\)\(in_EAX \+ 6\); psVar8 != \(short \*\)0x0; psVar8 = \*\(short \*\*\)\(psVar8 \+ 9\)\) \{\r?\n    FUN_0043b9bc\(uVar4,psVar8\);\r?\n    uVar4 = extraout_ECX_08;\r?\n    uVar7 = extraout_EDX_01;\r?\n    uVar5 = extraout_var_01;\r?\n  \})\r?\n  uVar11 = CONCAT44/,
  "$1\n  E2R_DrawHostedRequesterLabels(in_EAX);\n  uVar11 = CONCAT44"
);
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
source = source.replace(/&DAT_0061c730/g, "(undefined1 *)0x0061c730");
source = source.replace(/&DAT_0047a4e0/g, "(undefined4 *)0x0047a4e0");
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
  "$1undefined4 *stream;\n  \n  (void)param_1;\n  stream = (undefined4 *)(uintptr_t)param_2;\n  if ((uintptr_t)stream < 0x10000 || (uintptr_t)stream >= 0x70000000u ||\n      IsBadReadPtr(stream,0x1c)) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  if (stream[6] == E2R_STREAM_MAGIC) {\n    if (!E2R_UnregisterHostedStream(stream)) {\n      return CONCAT44(param_2,0xffffffff);\n    }\n    if (stream[5] != 0) {\n      LocalFree((HLOCAL)(uintptr_t)stream[5]);\n    }\n    stream[6] = 0;\n    LocalFree((HLOCAL)stream);\n    return (ulonglong)param_2 << 0x20;\n  }\n  (*(code *)PTR_FUN_0047d3b0)();"
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
  "\n\n\nstatic undefined4 E2R_ParseArchiveFanResource(void)\n{\n  int *previous_stream;\n  int *stream;\n  byte *base;\n  byte *end;\n  byte *cursor;\n  byte *scan;\n  byte *scan_limit;\n  uint ordinal;\n  uint original_offset;\n  uint mapped_offset;\n  uint count;\n  undefined4 result;\n\n  stream = (int *)(uintptr_t)DAT_0047a724;\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      (uint)stream[6] != E2R_STREAM_MAGIC) {\n    return 0;\n  }\n  base = (byte *)(uintptr_t)stream[5];\n  end = (byte *)(uintptr_t)stream[2];\n  cursor = (byte *)(uintptr_t)stream[0];\n  original_offset = (uint)(cursor - base);\n  mapped_offset = original_offset;\n  if ((*(byte *)(stream + 3) & 0x10) != 0) {\n    if (E2R_archive_parse_summary_count < 32) {\n      E2R_archive_parse_summary_count = E2R_archive_parse_summary_count + 1;\n      fprintf(stderr,\n              \"archive resource parse: input=%u mapped=%u result=0 final=%u remaining=%d\\n\",\n              original_offset,mapped_offset,(uint)((byte *)(uintptr_t)stream[0] - base),\n              stream[1]);\n    }\n    return 0;\n  }\n  if ((cursor + 4 <= end) &&\n      (cursor[0] != 'F' || cursor[1] != 'A' || cursor[2] != 'N' || cursor[3] != 'T')) {\n    ordinal = original_offset;\n    if (0 < ordinal && ordinal < 0x10000u) {\n      count = 0;\n      for (cursor = base + 4; cursor + 4 <= end; cursor = cursor + 1) {\n        if (cursor[0] == 'F' && cursor[1] == 'A' && cursor[2] == 'N' && cursor[3] == 'T') {\n          count = count + 1;\n          if (count == ordinal) {\n            stream[0] = (int)(uintptr_t)cursor;\n            stream[1] = (int)(uint)(end - cursor);\n            mapped_offset = (uint)(cursor - base);\n            *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x40;\n            break;\n          }\n        }\n      }\n    }\n    else {\n      scan_limit = (uint)(cursor - base) > 0x10000u ? cursor - 0x10000 : base;\n      for (scan = cursor; scan >= scan_limit; scan = scan - 1) {\n        if (scan[0] == 'F' && scan[1] == 'A' && scan[2] == 'N' && scan[3] == 'T') {\n          stream[0] = (int)(uintptr_t)scan;\n          stream[1] = (int)(uint)(end - scan);\n          mapped_offset = (uint)(scan - base);\n          *(byte *)(stream + 3) = *(byte *)(stream + 3) | 0x40;\n          break;\n        }\n        if (scan == scan_limit) {\n          break;\n        }\n      }\n    }\n  }\n  previous_stream = E2R_fan_parse_stream;\n  E2R_fan_parse_stream = stream;\n  result = FUN_004453a4((undefined4)(uintptr_t)stream,1);\n  E2R_fan_parse_stream = previous_stream;\n  if (E2R_archive_parse_summary_count < 32) {\n    E2R_archive_parse_summary_count = E2R_archive_parse_summary_count + 1;\n    fprintf(stderr,\n            \"archive resource parse: input=%u mapped=%u result=%u final=%u remaining=%d\\n\",\n            original_offset,mapped_offset,(uint)result,\n            (uint)((byte *)(uintptr_t)stream[0] - base),stream[1]);\n  }\n  return result;\n}\n\n\n\n/* 00447090 */"
);
source = source.replace(
  "\n\n\nstatic undefined4 E2R_ParseArchiveFanResource(void)",
  "\n\n\nstatic ushort E2R_ReadFanRecordWord(byte *record,int index)\n{\n  record = record + index * 2;\n  return (ushort)(((uint)record[0] << 8) | (uint)record[1]);\n}\n\nstatic short *E2R_AllocateArchiveRep(void)\n{\n  short *rep;\n\n  rep = (short *)(uintptr_t)FUN_0045f1ff(1,0x1a0);\n  if (rep == (short *)0x0) {\n    return (short *)0x0;\n  }\n  memset(rep,0xff,0x1a0);\n  *(short **)(rep + 0xd3) = _DAT_00637254;\n  _DAT_00637254 = rep;\n  rep[0xd5] = 3;\n  *(undefined4 *)(rep + 0xd6) = _DAT_00636588;\n  return rep;\n}\n\nstatic int E2R_ParseArchiveRepResource(short expected_rep_id)\n{\n  int *stream;\n  byte *base;\n  byte *end;\n  byte *cursor;\n  byte *limit;\n  byte *scan;\n  byte *record;\n  short *rep;\n  ushort type;\n  ushort id;\n  short field2;\n  short field3;\n  int slot;\n  uint record_count;\n\n  stream = (int *)(uintptr_t)DAT_0047a724;\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      (uint)stream[6] != E2R_STREAM_MAGIC) {\n    return 0;\n  }\n  base = (byte *)(uintptr_t)stream[5];\n  end = (byte *)(uintptr_t)stream[2];\n  cursor = (byte *)(uintptr_t)stream[0];\n  if (cursor + 0x4c > end || cursor[0] != 'F' || cursor[1] != 'A' ||\n      cursor[2] != 'N' || cursor[3] != 'T') {\n    return 0;\n  }\n  limit = end;\n  for (scan = cursor + 4; scan + 4 <= end; scan = scan + 1) {\n    if (scan[0] == 'F' && scan[1] == 'A' && scan[2] == 'N' && scan[3] == 'T') {\n      limit = scan;\n      break;\n    }\n  }\n  rep = (short *)0x0;\n  record_count = 0;\n  for (record = cursor + 0x42; record + 10 <= limit && record_count < 512;\n       record = record + 10) {\n    record_count = record_count + 1;\n    type = E2R_ReadFanRecordWord(record,0);\n    id = E2R_ReadFanRecordWord(record,1);\n    field2 = (short)E2R_ReadFanRecordWord(record,2);\n    field3 = (short)E2R_ReadFanRecordWord(record,3);\n    if (type == 0) {\n      break;\n    }\n    if (type == 0x35 && id < 500 &&\n        (expected_rep_id < 0 || id == (ushort)expected_rep_id)) {\n      rep = E2R_AllocateArchiveRep();\n      if (rep == (short *)0x0) {\n        return 0;\n      }\n      *rep = (short)id;\n      *(short **)((undefined1 *)0x00635980 + id * 4) = rep;\n      rep[0xd1] = field2 + -1;\n      rep[0xd2] = field3 + -1;\n      continue;\n    }\n    if (type == 0x36 && rep != (short *)0x0 && id == (ushort)*rep) {\n      slot = (int)field2 + 1;\n      if (0 <= slot && slot < 0xd1) {\n        rep[slot] = field3;\n        if (0x31 < _DAT_0067bc92 && 0x4f < field2 && field2 < 0x6b) {\n          rep[slot] = -1;\n        }\n      }\n      continue;\n    }\n    break;\n  }\n  if (rep == (short *)0x0) {\n    return 0;\n  }\n  stream[0] = (int)(uintptr_t)record;\n  stream[1] = (int)(uint)(end - record);\n  if (E2R_RuntimeDiagEnabled() && E2R_rep_load_diag_count < 64) {\n    E2R_rep_load_diag_count = E2R_rep_load_diag_count + 1;\n    fprintf(stderr,\n            \"rep archive direct: id=%d table=0x%lx records=%u final=%u limit=%u\\n\",\n            (int)*rep,(unsigned long)(uintptr_t)rep,record_count,\n            (uint)(record - base),(uint)(limit - base));\n  }\n  return 1;\n}\n\nstatic undefined4 E2R_ParseArchiveFanResource(void)"
);
source = source.replace(
  "  byte *scan_limit;\n  uint ordinal;\n  uint original_offset;",
  "  byte *scan_limit;\n  byte *resource_end;\n  uint ordinal;\n  uint original_offset;"
);
source = source.replace(
  "  previous_stream = E2R_fan_parse_stream;\n  E2R_fan_parse_stream = stream;",
  "  cursor = (byte *)(uintptr_t)stream[0];\n  resource_end = end;\n  if ((cursor + 4 <= end) && cursor[0] == 'F' && cursor[1] == 'A' &&\n      cursor[2] == 'N' && cursor[3] == 'T') {\n    for (scan = cursor + 4; scan + 4 <= end; scan = scan + 1) {\n      if (scan[0] == 'F' && scan[1] == 'A' && scan[2] == 'N' && scan[3] == 'T') {\n        resource_end = scan;\n        break;\n      }\n    }\n    stream[1] = (int)(uint)(resource_end - cursor);\n  }\n  previous_stream = E2R_fan_parse_stream;\n  E2R_fan_parse_stream = stream;"
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
  "          FUN_00442420((short)rep_id,iVar1);\n          uVar2 = FUN_0043cbb4(extraout_ECX_02);",
  "          uVar2 = FUN_00442420((short)rep_id,iVar1);\n          if (E2R_RuntimeDiagEnabled() && E2R_rep_load_diag_count < 64) {\n            E2R_rep_load_diag_count = E2R_rep_load_diag_count + 1;\n            fprintf(stderr,\"rep load missing: id=%d name=%s offset=%d current=0x%lx\\n\",\n                    rep_id,\n                    (char *)uVar2 != (char *)0x0 &&\n                    !IsBadReadPtr((void *)(uintptr_t)(char *)uVar2,1) ?\n                    (char *)uVar2 : \"(bad)\",\n                    *(int *)(iVar1 + 0x663a10),(unsigned long)DAT_0047a470);\n          }\n          uVar2 = FUN_0043cbb4(extraout_ECX_02);"
);
source = source.replace(
  "  if (-1 < rep_id) {\n    iVar1 = rep_id * 4;\n    if (*(int *)((undefined1 *)0x00635980 + iVar1) == 0) {",
  "  if (-1 < rep_id) {\n    iVar1 = rep_id * 4;\n    if (E2R_RuntimeDiagEnabled() && E2R_rep_load_diag_count < 64) {\n      E2R_rep_load_diag_count = E2R_rep_load_diag_count + 1;\n      fprintf(stderr,\n              \"rep load enter: id=%d table=0x%lx offset=%d current=0x%lx scene=0x%lx\\n\",\n              rep_id,\n              (unsigned long)*(int *)((undefined1 *)0x00635980 + iVar1),\n              *(int *)(iVar1 + 0x663a10),(unsigned long)DAT_0047a470,\n              (unsigned long)_DAT_0073cc3c);\n    }\n    if (*(int *)((undefined1 *)0x00635980 + iVar1) == 0) {"
);
source = source.replace(
  "        FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x663a10));\n        result = E2R_ParseArchiveFanResource();",
  "        FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x663a10));\n        if (E2R_RuntimeDiagEnabled() && E2R_rep_load_diag_count < 16) {\n          E2R_archive_parse_summary_count = 0;\n          E2R_fan_phase_diag_count = 0;\n          E2R_fan_dispatch_diag_count = 0;\n        }\n        result = E2R_ParseArchiveFanResource();"
);
source = source.replace(
  "    }\n  }\n  DAT_0047a470 = saved_current;\n  return CONCAT44(param_2,result);\n}",
  "    }\n    if (E2R_RuntimeDiagEnabled() && E2R_rep_load_diag_count < 64) {\n      int rep = *(int *)((undefined1 *)0x00635980 + iVar1);\n      E2R_rep_load_diag_count = E2R_rep_load_diag_count + 1;\n      fprintf(stderr,\n              \"rep load exit: id=%d result=%d table=0x%lx first=%d records=%u final_current=0x%lx\\n\",\n              rep_id,result,(unsigned long)rep,\n              rep != 0 && !IsBadReadPtr((void *)(uintptr_t)rep,2) ? (int)*(short *)rep : -9999,\n              E2R_fan_parse_record_count,(unsigned long)saved_current);\n    }\n  }\n  DAT_0047a470 = saved_current;\n  return CONCAT44(param_2,result);\n}"
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
  /(undefined8 __fastcall FUN_00441e38)\(undefined4 param_1,undefined4 param_2\)([\s\S]*?\r?\n  short in_AX;\r?\n)/,
  "$1(short param_1,undefined4 param_2)$2"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00441e38\(short param_1,undefined4 param_2\)[\s\S]*?\r?\n  char \*pcVar6;\r?\n\s*)if \(in_AX < 0\) \{/,
  "$1in_AX = param_1;\n  if (in_AX < 0) {"
);
source = source.replace(
  "uVar3 = FUN_00441e38(DAT_0047a470,iVar1);",
  "uVar3 = FUN_00441e38((short)iVar2,iVar1);"
);
source = source.replace(
  "FUN_00441e38(DAT_0047a470,iVar1);",
  "FUN_00441e38((short)iVar2,iVar1);"
);
source = source.replace(
  "      iVar2 = FUN_004453a4(uVar3,1);",
  "      iVar2 = E2R_ParseArchiveFanResource();"
);
source = source.replace(
  "      FUN_0045f296(in_EAX,*(int *)(iVar1 + 0x653840));\n      FUN_004453a4(extraout_ECX_04,1);\n      uVar4 = extraout_ECX_05;\n      uVar5 = extraout_EDX_00;",
  "      FUN_0045f296(in_EAX,*(int *)(iVar1 + 0x653840));\n      if (E2R_RuntimeDiagEnabled()) {\n        E2R_fan_phase_diag_count = 0;\n        E2R_fan_actor_diag_count = 0;\n        E2R_fan_dispatch_diag_count = 0;\n        E2R_archive_parse_summary_count = 0;\n      }\n      parse_result = E2R_ParseArchiveFanResource();\n      {\n        short *loaded_actor = *(short **)((undefined1 *)0x00630b60 + actor_id * 4);\n        if (parse_result != 0 && loaded_actor != (short *)0x0 &&\n            loaded_actor[0x42] == 0 && loaded_actor[0x43] == 0 && loaded_actor[0x44] == 0 &&\n            (loaded_actor[0x4e] != 0 || loaded_actor[0x4f] != 0 || loaded_actor[0x50] != 0)) {\n          FUN_0044146c();\n        }\n        if (E2R_RuntimeDiagEnabled() && E2R_actor_load_diag_count < 48) {\n          E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;\n          fprintf(stderr,\n                  \"actor load archive: id=%d offset=%d result=%lu table=0x%lx live=%d,%d,%d stand=%d,%d,%d old=%d,%d,%d\\n\",\n                  actor_id,*(int *)(iVar1 + 0x653840),\n                  (unsigned long)(uint)parse_result,(unsigned long)loaded_actor,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x42] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x43] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x44] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x4e] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x4f] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x50] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x7e] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x7f] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x80] : -9999);\n        }\n      }\n      uVar4 = (undefined4)actor_id;\n      uVar5 = 0;"
);
source = source.replace(
  "            FUN_0045f296(param_1,*(int *)(iVar1 + 0x653840));\n            FUN_004453a4(extraout_ECX_04,1);\n            uVar6 = extraout_ECX_05;\n            uVar7 = extraout_EDX_00;",
  "            FUN_0045f296(param_1,*(int *)(iVar1 + 0x653840));\n            E2R_ParseArchiveFanResource();\n            uVar6 = (undefined4)(int)*psVar3;\n            uVar7 = 0;"
);
source = source.replace(
  "  case 0x37:\n    psVar7 = (short *)(uint)(ushort)in_EAX[2];\n    param_2[0x91] = in_EAX[2];\n    if (in_EAX[3] != 0) {",
  "  case 0x37:\n    psVar7 = (short *)(uint)(ushort)in_EAX[2];\n    param_2[0x91] = in_EAX[2];\n    E2R_RetainCurrentRepForMissingTarget(\"2b880.case37\",param_2);\n    if (in_EAX[3] != 0) {"
);
source = source.replace(
  "                  \"actor load archive: id=%d offset=%d result=%lu table=0x%lx live=%d,%d,%d stand=%d,%d,%d old=%d,%d,%d\\n\",",
  "                  \"actor load archive: id=%d offset=%d result=%lu table=0x%lx live=%d,%d,%d stand=%d,%d,%d old=%d,%d,%d rep=0x%lx rep_id=%d state91=%d static=%d/%d/%d\\n\","
);
source = source.replace(
  "                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x7e] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x7f] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x80] : -9999);",
  "                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x7e] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x7f] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x80] : -9999,\n                  loaded_actor != (short *)0x0 ?\n                    (unsigned long)*(int *)(loaded_actor + 0x8f) : 0,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x90] : -9999,\n                  loaded_actor != (short *)0x0 ? (int)loaded_actor[0x91] : -9999,\n                  loaded_actor != (short *)0x0 ?\n                    (int)*(short *)(*loaded_actor * 2 + 0x6648e8) : -9999,\n                  loaded_actor != (short *)0x0 ?\n                    (int)*(short *)(*loaded_actor * 2 + 0x65feb0) : -9999,\n                  loaded_actor != (short *)0x0 ?\n                    (int)*(short *)(*loaded_actor * 2 + 0x671fc0) : -9999);"
);
source = source.replace(
  "        if (E2R_RuntimeDiagEnabled() && E2R_actor_load_diag_count < 48) {\n          E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;",
  "        E2R_RetainCurrentRepForMissingTarget(\"51f5c.archive\",loaded_actor);\n        if (E2R_RuntimeDiagEnabled() && E2R_actor_load_diag_count < 48) {\n          E2R_actor_load_diag_count = E2R_actor_load_diag_count + 1;"
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
  "        FUN_00422aa0(extraout_ECX_06,(undefined2 *)(*psVar2 * 6 + 0x669708));\n        FUN_00422aa0(extraout_ECX_07,(undefined2 *)(*psVar2 * 6 + 0x658980));",
  "        FUN_00422aa0((undefined4)(uintptr_t)(psVar2 + 0x42),\n                    (undefined2 *)(*psVar2 * 6 + 0x669708));\n        FUN_00422aa0((undefined4)(uintptr_t)(psVar2 + 0x48),\n                    (undefined2 *)(*psVar2 * 6 + 0x658980));"
);
source = source.replace(
  "              FUN_00422aa0(extraout_ECX_06,(undefined2 *)(*psVar4 * 6 + 0x669708));\n              FUN_00422aa0(extraout_ECX_07,(undefined2 *)(*psVar4 * 6 + 0x658980));",
  "              FUN_00422aa0((undefined4)(uintptr_t)(psVar4 + 0x42),\n                          (undefined2 *)(*psVar4 * 6 + 0x669708));\n              FUN_00422aa0((undefined4)(uintptr_t)(psVar4 + 0x48),\n                          (undefined2 *)(*psVar4 * 6 + 0x658980));"
);
source = source.replace(
  /undefined8 __fastcall FUN_00448744\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004488a4 \*\//,
  "undefined8 __fastcall FUN_00448744(undefined4 param_1,ushort *param_2)\n\n{\n  int iVar1;\n  byte bVar2;\n  bool bVar3;\n  ushort *actor;\n  int iVar4;\n  uint uVar5;\n  int iVar6;\n  byte *pbVar7;\n  uint local_28;\n  uint local_20;\n  \n  local_20 = 0xffffffff;\n  local_28 = 0xffffffff;\n  actor = (ushort *)(uintptr_t)param_1;\n  if ((uintptr_t)actor < 0x10000u || IsBadReadPtr(actor,0x6)) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  uVar5 = (uint)*(ushort *)\n                 ((undefined1 *)0x00684d68 +\n                 (((int)(short)*actor >> 9) + 0x40) * 2 +\n                 ((*(int *)(actor + 1) >> 0x19) + 0x40) * 0x100);\n  iVar6 = (short)(*actor & 0x1ff) + -0x100;\n  iVar4 = (short)(actor[2] & 0x1ff) + -0x100;\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    fprintf(stderr,\n            \"scene lookup 48744: coord=0x%lx x=%d z=%d cell=0x%x current=0x%lx\\n\",\n            (unsigned long)actor,(int)(short)*actor,(int)(short)actor[2],\n            (unsigned int)uVar5,(unsigned long)DAT_0047a470);\n  }\n  if (uVar5 != 0xffff) {\n    pbVar7 = (undefined1 *)0x0068cd68 + uVar5 * 0xc;\n    do {\n      bVar3 = false;\n      switch((int)(uintptr_t)(pbVar7[1])) {\n      case 0:\n        break;\n      case 1:\nswitchD_004487ea_caseD_1:\n        bVar3 = true;\n        break;\n      case 2:\n        if (iVar4 <= iVar6) goto switchD_004487ea_caseD_1;\n        break;\n      case 3:\n        if (iVar6 <= -iVar4) goto switchD_004487ea_caseD_1;\n        break;\n      case 4:\n        if (-iVar4 < iVar6) goto switchD_004487ea_caseD_1;\n        break;\n      case 5:\n        if (iVar6 < iVar4) goto switchD_004487ea_caseD_1;\n        break;\n      default:\n        if (iVar6 < 1) {\n          if (iVar4 < 1) {\n            bVar2 = pbVar7[1] & 2;\n          }\n          else {\n            bVar2 = pbVar7[1] & 8;\n          }\n        }\n        else if (iVar4 < 1) {\n          bVar2 = pbVar7[1] & 1;\n        }\n        else {\n          bVar2 = pbVar7[1] & 4;\n        }\n        if (bVar2 != 0) goto switchD_004487ea_caseD_1;\n      }\n      if (((bVar3) &&\n          ((int)(uint)pbVar7[5] <= (-(*(int *)actor >> 0x10) >> (DAT_0047a738 & 0x1f)) + 0x84)) &&\n         ((int)local_28 < (int)(uint)*pbVar7)) {\n        local_28 = (uint)*pbVar7;\n        local_20 = uVar5;\n      }\n      iVar1 = *(int *)pbVar7;\n      pbVar7 = pbVar7 + 0xc;\n      uVar5 = uVar5 + 1;\n    } while ((iVar1 >> 0x10 & 0x8000U) == 0);\n  }\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    fprintf(stderr,\"scene lookup 48744 result: result=%d coord=0x%lx\\n\",\n            (int)local_20,(unsigned long)actor);\n  }\n  return CONCAT44(param_2,local_20);\n}\n\n\n\n/* 004488a4 */"
);
source = source.replace(
  "    fprintf(stderr,\n            \"scene lookup 48744: coord=0x%lx x=%d z=%d cell=0x%x current=0x%lx\\n\",\n            (unsigned long)actor,(int)(short)*actor,(int)(short)actor[2],\n            (unsigned int)uVar5,(unsigned long)DAT_0047a470);\n  }\n  if (uVar5 != 0xffff) {",
  "    fprintf(stderr,\n            \"scene lookup 48744: coord=0x%lx x=%d z=%d cell=0x%x current=0x%lx\\n\",\n            (unsigned long)actor,(int)(short)*actor,(int)(short)actor[2],\n            (unsigned int)uVar5,(unsigned long)DAT_0047a470);\n    {\n      uint swapped_cell = (uint)*(ushort *)\n        ((undefined1 *)0x00684d68 +\n         ((*(int *)(actor + 1) >> 0x19) + 0x40) * 2 +\n         (((int)(short)*actor >> 9) + 0x40) * 0x100);\n      uintptr_t desc = 0x0068cd68 + (uintptr_t)uVar5 * 0xc;\n      uintptr_t swapped_desc = 0x0068cd68 + (uintptr_t)swapped_cell * 0xc;\n      if (swapped_cell != uVar5 && swapped_cell != 0xffff &&\n          !IsBadReadPtr((void *)desc,0xc) && !IsBadReadPtr((void *)swapped_desc,0xc)) {\n        fprintf(stderr,\n                \"scene lookup 48744 alt: swapped_cell=0x%x desc_words=%04x,%04x swapped_words=%04x,%04x\\n\",\n                (unsigned int)swapped_cell,\n                (unsigned int)*(ushort *)(desc + 8),(unsigned int)*(ushort *)(desc + 10),\n                (unsigned int)*(ushort *)(swapped_desc + 8),\n                (unsigned int)*(ushort *)(swapped_desc + 10));\n      }\n    }\n    E2R_LogSceneGridProbe(\"48744.lookup\",(int)(short)*actor,(int)(short)actor[2]);\n  }\n  if (uVar5 != 0xffff) {"
);
source = source.replace(
  "  if (uVar5 != 0xffff) {\n    pbVar7 = (undefined1 *)0x0068cd68 + uVar5 * 0xc;",
  "  if (E2R_RuntimeDiagEnabled() && E2R_scene_lookup_diag_count < 256) {\n    uint swapped_cell = (uint)*(ushort *)\n      ((undefined1 *)0x00684d68 +\n       ((*(int *)(actor + 1) >> 0x19) + 0x40) * 2 +\n       (((int)(short)*actor >> 9) + 0x40) * 0x100);\n    uintptr_t desc = 0x0068cd68 + (uintptr_t)uVar5 * 0xc;\n    uintptr_t swapped_desc = 0x0068cd68 + (uintptr_t)swapped_cell * 0xc;\n    E2R_scene_lookup_diag_count = E2R_scene_lookup_diag_count + 1;\n    fprintf(stderr,\n            \"scene lookup detail: coord=0x%lx x=%d y=%d z=%d cell=0x%x swapped=0x%x \"\n            \"frac=%d,%d height_gate=%d count=%d desc_bad=%d swapped_bad=%d \"\n            \"desc_words=%04x,%04x swapped_words=%04x,%04x current=0x%lx scene=0x%lx\\n\",\n            (unsigned long)actor,(int)(short)*actor,(int)(short)actor[1],\n            (int)(short)actor[2],(unsigned int)uVar5,(unsigned int)swapped_cell,\n            iVar6,iVar4,(-(*(int *)actor >> 0x10) >> (DAT_0047a738 & 0x1f)) + 0x84,\n            DAT_0047a77c,IsBadReadPtr((void *)desc,0xc),\n            IsBadReadPtr((void *)swapped_desc,0xc),\n            !IsBadReadPtr((void *)desc,0xc) ? (unsigned int)*(ushort *)(desc + 8) : 0xffff,\n            !IsBadReadPtr((void *)desc,0xc) ? (unsigned int)*(ushort *)(desc + 10) : 0xffff,\n            !IsBadReadPtr((void *)swapped_desc,0xc) ? (unsigned int)*(ushort *)(swapped_desc + 8) : 0xffff,\n            !IsBadReadPtr((void *)swapped_desc,0xc) ? (unsigned int)*(ushort *)(swapped_desc + 10) : 0xffff,\n            (unsigned long)DAT_0047a470,(unsigned long)_DAT_0073cc3c);\n  }\n  if (uVar5 != 0xffff) {\n    pbVar7 = (undefined1 *)0x0068cd68 + uVar5 * 0xc;"
);
source = source.replace(
  "  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    fprintf(stderr,\"scene lookup 48744 result: result=%d coord=0x%lx\\n\",\n            (int)local_20,(unsigned long)actor);\n  }\n  return CONCAT44(param_2,local_20);",
  "  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    fprintf(stderr,\"scene lookup 48744 result: result=%d coord=0x%lx\\n\",\n            (int)local_20,(unsigned long)actor);\n  }\n  if (E2R_RuntimeDiagEnabled() && E2R_scene_lookup_diag_count < 256) {\n    uintptr_t result_desc = 0x0068cd68 + (uintptr_t)local_20 * 0xc;\n    E2R_scene_lookup_diag_count = E2R_scene_lookup_diag_count + 1;\n    fprintf(stderr,\n            \"scene lookup detail result: result=%d best_word=0x%x coord=0x%lx result_bad=%d scene_word=%04x hint_word=%04x\\n\",\n            (int)local_20,(unsigned int)local_28,(unsigned long)actor,\n            (int)local_20 < 0 || IsBadReadPtr((void *)result_desc,0xc),\n            (int)local_20 < 0 || IsBadReadPtr((void *)result_desc,0xc) ? 0xffff :\n              (unsigned int)*(ushort *)(result_desc + 8),\n            (int)local_20 < 0 || IsBadReadPtr((void *)result_desc,0xc) ? 0xffff :\n              (unsigned int)*(ushort *)(result_desc + 10));\n  }\n  return CONCAT44(param_2,local_20);"
);
source = source.replaceAll("(int)(uint)pbVar7[5] <=", "(int)(char)pbVar7[5] <=");
source = source.replace(
  "      iVar2 = FUN_004453a4(extraout_ECX_03,1);",
  "      iVar2 = E2R_ParseArchiveFanResource();"
);
source = source.replace(
  /undefined8 __fastcall FUN_004413fc\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00441444 \*\//,
  "undefined8 __fastcall FUN_004413fc(undefined4 param_1,undefined4 param_2)\n\n{\n  undefined2 *puVar1;\n  undefined8 uVar2;\n  \n  puVar1 = (undefined2 *)(uintptr_t)FUN_0045326c(param_1,param_2);\n  if (puVar1 == (undefined2 *)0x0) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[1] = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  *puVar1 = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[2] = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[3] = (short)uVar2;\n  uVar2 = FUN_004171b8((undefined4)(uintptr_t)E2R_fan_parse_stream,param_2);\n  puVar1[4] = (short)uVar2;\n  E2R_fan_parse_record = (short *)puVar1;\n  E2R_fan_parse_record_count = E2R_fan_parse_record_count + 1;\n  if (E2R_fan_phase_diag_count < 64 &&\n      (E2R_fan_parse_record_count <= 64 ||\n       (640 <= E2R_fan_parse_record_count && E2R_fan_parse_record_count <= 690))) {\n    fprintf(stderr,\"FAN record: ordinal=%u caller=%p offset=%u fields=%04x,%04x,%04x,%04x,%04x\\n\",\n            E2R_fan_parse_record_count,__builtin_return_address(0),\n            (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                   (byte *)(uintptr_t)E2R_fan_parse_stream[5]),\n            (ushort)puVar1[0],(ushort)puVar1[1],(ushort)puVar1[2],\n            (ushort)puVar1[3],(ushort)puVar1[4]);\n  }\n  return CONCAT44(param_2,(undefined4)(uintptr_t)puVar1);\n}\n\n\n\n/* 00441444 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00441444\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0044146c \*\//,
  "undefined8 __fastcall FUN_00441444(undefined4 param_1,undefined4 param_2)\n\n{\n  int *stream;\n  int b0;\n  int b1;\n  int b2;\n  int b3;\n  uint value;\n  \n  stream = (int *)(uintptr_t)param_1;\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      (uint)stream[6] != E2R_STREAM_MAGIC) {\n    stream = (int *)(uintptr_t)DAT_0047a724;\n  }\n  if ((uintptr_t)stream < 0x10000u || IsBadReadPtr(stream,0x1c) ||\n      (uint)stream[6] != E2R_STREAM_MAGIC) {\n    if (E2R_archive_read_diag_count < 8) {\n      E2R_archive_read_diag_count = E2R_archive_read_diag_count + 1;\n      fprintf(stderr,\"archive dword read failed: stream=%p fallback=%p offset=%u\\n\",\n              (void *)(uintptr_t)param_1,(void *)(uintptr_t)DAT_0047a724,\n              (uint)(uintptr_t)param_2);\n    }\n    return (ulonglong)(uint)(uintptr_t)param_2 << 0x20;\n  }\n  b0 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  b1 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  b2 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  b3 = E2R_ReadHostedStreamByte((undefined4 *)stream);\n  if ((b0 | b1 | b2 | b3) < 0) {\n    if (E2R_archive_read_diag_count < 8) {\n      E2R_archive_read_diag_count = E2R_archive_read_diag_count + 1;\n      fprintf(stderr,\"archive dword eof: stream=%p offset=%u remaining=%d\\n\",\n              (void *)stream,(uint)(uintptr_t)param_2,stream[1]);\n    }\n    return (ulonglong)(uint)(uintptr_t)param_2 << 0x20;\n  }\n  value = ((uint)b0 << 0x18) | (((uint)b1 & 0xff) << 0x10) |\n          (((uint)b2 & 0xff) << 8) | ((uint)b3 & 0xff);\n  return CONCAT44(param_2,value);\n}\n\n\n\n/* 0044146c */"
);
source = source.replace(
  "    *(undefined2 *)(iVar1 + 0xee) = 0;\n  }\n  return;\n}\n\n\n\n/* 004414c4 */",
  "    *(undefined2 *)(iVar1 + 0xee) = 0;\n  }\n  if (E2R_RuntimeDiagEnabled()) {\n    short *actor0 = *(short **)0x00630b60;\n    if (actor0 != (short *)0x0) {\n      fprintf(stderr,\n              \"4146c actor0: actor=0x%lx head=0x%lx live=%d,%d,%d stand=%d,%d,%d\\n\",\n              (unsigned long)actor0,(unsigned long)_DAT_00637248,\n              (int)actor0[0x42],(int)actor0[0x43],(int)actor0[0x44],\n              (int)actor0[0x4e],(int)actor0[0x4f],(int)actor0[0x50]);\n    }\n  }\n  return;\n}\n\n\n\n/* 004414c4 */"
);
source = source.replace(
  "  if (E2R_fan_phase_diag_count < 64 &&\n      (E2R_fan_parse_record_count <= 64 ||\n       (640 <= E2R_fan_parse_record_count && E2R_fan_parse_record_count <= 690))) {",
  "  if (E2R_fan_phase_diag_count < 64 &&\n      (E2R_fan_parse_record_count <= 64 ||\n       (640 <= E2R_fan_parse_record_count && E2R_fan_parse_record_count <= 690))) {"
);
source = source.replace(
  /(void FUN_00447090\(void\)[\s\S]*?\r?\n  undefined1 local_48 \[52\];\r?\n\s*)switch/,
  "$1in_EAX = E2R_fan_parse_record;\n  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,10)) {\n    return;\n  }\n  \n  switch"
);
source = source.replace(
  /(short \* __fastcall FUN_0042b880\(int param_1,short \*param_2\)[\s\S]*?\r?\n  short \*local_14;\r?\n\s*)if/,
  "$1if (E2R_action_event_context != 0) {\n    in_EAX = (short *)(uintptr_t)E2R_action_event_context;\n    if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,10) ||\n        param_2 == (short *)0x0 || (uintptr_t)param_2 < 0x10000u ||\n        IsBadReadPtr(param_2,0x148)) {\n      return (short *)0x0;\n    }\n  }\n  else {\n    in_EAX = E2R_fan_parse_record;\n    if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,10)) {\n      return (short *)0x0;\n    }\n  }\n  unaff_ESI = param_2;\n  local_14 = param_2;\n  local_18 = param_2;\n  \n  if"
);
source = source.replace(
  "    if ((DAT_0047a714 != 0) &&\n       (((sVar9 == 8 || (sVar9 == 10)) || ((sVar9 == 7 || ((sVar9 == 0x29 || (sVar9 == 0x2b))))))))\n    {\n      FUN_00442ca4();\n      iVar5 = extraout_EDX_02;\n    }\nLAB_00444418:",
  "    if ((DAT_0047a714 != 0) &&\n       (((sVar9 == 8 || (sVar9 == 10)) || ((sVar9 == 7 || ((sVar9 == 0x29 || (sVar9 == 0x2b))))))))\n    {\n      FUN_00442ca4();\n      iVar5 = extraout_EDX_02;\n    }\n    if (sVar9 == 0) {\n      FUN_00453264();\n      if ((DAT_0047a34a != 0) && (DAT_0047a470 == (short *)0x0)) {\n        DAT_0047a470 = psVar1;\n      }\n      return;\n    }\nLAB_00444418:"
);
source = source.replace(
  "    FUN_00447090();\n    sVar9 = *(short *)(iVar4 + 2);\n    iVar5 = extraout_EDX;",
  "    FUN_00447090();\n    sVar9 = *(short *)(iVar4 + 2);\n    if (E2R_fan_actor_diag_count < 128) {\n      E2R_fan_actor_diag_count = E2R_fan_actor_diag_count + 1;\n      fprintf(stderr,\"FAN 44330: ordinal=%u local_type=%04x version=%d offset=%u\\n\",\n              E2R_fan_parse_record_count,(ushort)sVar9,(int)_DAT_0067bc92,\n              (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                     (byte *)(uintptr_t)E2R_fan_parse_stream[5]));\n    }\n    iVar5 = extraout_EDX;"
);
source = source.replace(
  "      FUN_00422aa0(extraout_ECX,DAT_0047a470 + 0x7e);\n      FUN_00422aa0(extraout_ECX_00,DAT_0047a470 + 0x7b);\n      iVar5 = extraout_EDX_01;",
  "      FUN_00422aa0((undefined4)(uintptr_t)((short *)(uintptr_t)DAT_0047a470 + 0x84),\n                  (short *)(uintptr_t)DAT_0047a470 + 0x7e);\n      FUN_00422aa0((undefined4)(uintptr_t)((short *)(uintptr_t)DAT_0047a470 + 0x81),\n                  (short *)(uintptr_t)DAT_0047a470 + 0x7b);\n      if (E2R_fan_actor_diag_count < 16) {\n        E2R_fan_actor_diag_count = E2R_fan_actor_diag_count + 1;\n        fprintf(stderr,\n                \"FAN 44330 coord copy: actor=0x%lx type=%04x pos=%d,%d,%d src=%d,%d,%d\\n\",\n                (unsigned long)DAT_0047a470,(ushort)sVar9,\n                (int)((short *)(uintptr_t)DAT_0047a470)[0x84],\n                (int)((short *)(uintptr_t)DAT_0047a470)[0x85],\n                (int)((short *)(uintptr_t)DAT_0047a470)[0x86],\n                (int)((short *)(uintptr_t)DAT_0047a470)[0x7e],\n                (int)((short *)(uintptr_t)DAT_0047a470)[0x7f],\n                (int)((short *)(uintptr_t)DAT_0047a470)[0x80]);\n      }\n      iVar5 = extraout_EDX_01;"
);
source = source.replace(
  "    FUN_0042b880(0,DAT_0047a470);\n    sVar3 = _DAT_0067bc92;",
  "    FUN_0042b880(0,DAT_0047a470);\n    if (E2R_RuntimeDiagEnabled() && DAT_0047a470 != 0 &&\n        *(short *)(uintptr_t)DAT_0047a470 == 0 &&\n        (sVar9 == 0x14 || sVar9 == 0x16 || sVar9 == 0x31 || sVar9 == 0x32)) {\n      short *actor0 = (short *)(uintptr_t)DAT_0047a470;\n      fprintf(stderr,\n              \"FAN 44330 actor0 after type=%04x live=%d,%d,%d stand=%d,%d,%d old=%d,%d,%d\\n\",\n              (ushort)sVar9,(int)actor0[0x42],(int)actor0[0x43],\n              (int)actor0[0x44],(int)actor0[0x4e],(int)actor0[0x4f],\n              (int)actor0[0x50],(int)actor0[0x7e],(int)actor0[0x7f],\n              (int)actor0[0x80]);\n    }\n    sVar3 = _DAT_0067bc92;"
);
source = source.replace(
  "    FUN_0045f0a1((int)local_48,(byte *)s_unknown_type____d_004747d4);\n    FUN_0043cac0(extraout_ECX,extraout_EDX);\n    FUN_00414e68();",
  "    fprintf(stderr,\n            \"FAN unknown record: ordinal=%u offset=%u remaining=%d fields=%04x,%04x,%04x,%04x,%04x\\n\",\n            E2R_fan_parse_record_count,\n            (uint)((byte *)(uintptr_t)E2R_fan_parse_stream[0] -\n                   (byte *)(uintptr_t)E2R_fan_parse_stream[5]),\n            E2R_fan_parse_stream[1],(ushort)in_EAX[0],(ushort)in_EAX[1],\n            (ushort)in_EAX[2],(ushort)in_EAX[3],(ushort)in_EAX[4]);"
);
source = source.replace(
  "      FUN_0043cac0(uVar4,iVar2);\n      FUN_00414e68();\n      uVar4 = extraout_ECX_10;\n      uVar5 = extraout_EDX_09;",
  "      if (E2R_fan_phase_diag_count < 32) {\n        E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n        fprintf(stderr,\n                \"FAN 448e4 unsupported record: ordinal=%u offset=%u fields=%04x,%04x,%04x,%04x,%04x\\n\",\n                E2R_fan_parse_record_count,E2R_FanStreamOffset(),\n                (ushort)psVar1[0],(ushort)psVar1[1],(ushort)psVar1[2],\n                (ushort)psVar1[3],(ushort)psVar1[4]);\n      }\n      FUN_00453264();\n      return;"
);
source = source.replace(
  "    if ((short)uVar10 == 0) {\n      if (5 < _DAT_0067bc92) {",
  "    if (e2r_record_type == 0) {\n      if (5 < _DAT_0067bc92) {"
);
source = source.replace(
  "  ulonglong uVar17;\n  undefined1 local_e8 [103];",
  "  ulonglong uVar17;\n  short e2r_record_type;\n  undefined1 local_e8 [103];"
);
source = source.replace(
  "LAB_00446189:\n    sVar9 = (short)uVar10;\n    if (sVar9 == 0x19) {",
  "LAB_00446189:\n    sVar9 = (short)uVar10;\n    e2r_record_type = sVar9;\n    if (sVar9 == 0x19) {"
);
source = source.replace(
  "  int iVar1;\n  int in_EAX;\n  int iVar2;\n  \n  iVar1 = *(int *)(param_2 + 6);",
  "  int iVar1;\n  int in_EAX;\n  int iVar2;\n  \n  in_EAX = (int)(uintptr_t)param_1;\n  iVar1 = *(int *)(param_2 + 6);"
);
source = source.replace(
  "  ushort uVar5;\n  undefined8 uVar6;\n  \n  uVar6 = FUN_00453754(param_1,param_2);",
  "  ushort uVar5;\n  undefined8 uVar6;\n  \n  in_EAX = (int)(uintptr_t)param_1;\n  uVar6 = FUN_00453754(param_1,param_2);"
);
source = source.replace(
  "      local_1c = FUN_00426b54(uVar2,*(int *)(psVar3 + 1) >> 0x10);",
  "      local_1c = FUN_00426b54((undefined4)(uintptr_t)local_14,*(int *)(psVar3 + 1) >> 0x10);"
);
source = source.replace(
  "      FUN_00426ac4(uVar2,(int)local_1c);",
  "      FUN_00426ac4((undefined4)(uintptr_t)psVar3,(int)local_1c);"
);
source = source.replace(
  "      local_1c = FUN_00426b54(uVar10,*(int *)(psVar8 + 1) >> 0x10);",
  "      local_1c = FUN_00426b54((undefined4)(uintptr_t)(local_24 + 1),\n                              *(int *)(psVar8 + 1) >> 0x10);"
);
source = source.replace(
  "      uVar15 = FUN_004263ac(uVar10,iVar7);\n      local_24 = (short *)uVar15;",
  "      uVar15 = FUN_004263ac((undefined4)(uintptr_t)local_20,iVar7);\n      local_24 = (short *)uVar15;"
);
source = source.replace(
  "      uVar15 = FUN_004263ac((undefined4)(uintptr_t)local_20,iVar7);\n      local_24 = (short *)uVar15;\n      if (local_24 != (short *)0x0) {",
  "      uVar15 = FUN_004263ac((undefined4)(uintptr_t)local_20,iVar7);\n      local_24 = (short *)uVar15;\n      if (E2R_StartupDiagEnabled() && E2R_scene_record_install_diag_count < 128) {\n        fprintf(stderr,\n                \"scene child record 1a: requested=%d scene=0x%lx node=0x%lx raw=%04x,%04x,%04x,%04x,%04x\\n\",\n                E2R_scene_load_request_id,(unsigned long)(uintptr_t)local_20,\n                (unsigned long)(uintptr_t)local_24,\n                (unsigned int)(ushort)psVar8[0],(unsigned int)(ushort)psVar8[1],\n                (unsigned int)(ushort)psVar8[2],(unsigned int)(ushort)psVar8[3],\n                (unsigned int)(ushort)psVar8[4]);\n      }\n      if (local_24 != (short *)0x0) {"
);
source = source.replace(
  "        local_24[2] = psVar8[2];\n        local_24[7] = psVar8[3];\n        *local_24 = psVar8[4];",
  "        local_24[2] = psVar8[2];\n        local_24[7] = psVar8[3];\n        *local_24 = psVar8[4];\n        if (E2R_StartupDiagEnabled() && E2R_scene_record_install_diag_count < 128) {\n          fprintf(stderr,\n                  \"scene child record 1a install: requested=%d actor=%d word2=%d flags=0x%04x\\n\",\n                  E2R_scene_load_request_id,(int)*local_24,(int)local_24[2],\n                  (unsigned int)(ushort)local_24[7]);\n        }"
);
source = source.replace(
  "      uVar15 = FUN_0041ba7c(uVar10,iVar7);\n      uVar15 = FUN_00426320(extraout_ECX_70,(int)((ulonglong)uVar15 >> 0x20));",
  "      FUN_0041ba7c(uVar10,iVar7);\n      uVar15 = FUN_00426320(0,0);"
);
source = source.replace(
  /undefined8 __fastcall FUN_00426320\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004263ac \*\//,
  "undefined8 __fastcall FUN_00426320(undefined4 param_1,undefined4 param_2)\n\n{\n  byte *node;\n  int offset;\n  int i;\n\n  (void)param_1;\n  do {\n    node = (byte *)0x0;\n    for (offset = 0; offset < 0x8340; offset = offset + 0xa8) {\n      if ((*(ushort *)((byte *)0x00aba392 + offset) & 0x8000U) != 0) {\n        node = (byte *)0x00aba2fc + offset;\n        memset(node,0,0xa8);\n        break;\n      }\n    }\n    if (node != (byte *)0x0) {\n      *(ushort *)(node + 0x00) = 0xffff;\n      *(ushort *)(node + 0x02) = 0xffff;\n      *(int *)(node + 0x04) = 0;\n      *(int *)(node + 0x08) = (int)(uintptr_t)_DAT_0063725c;\n      *(ushort *)(node + 0x0c) = 0xffff;\n      *(ushort *)(node + 0x96) = 2;\n      *(ushort *)(node + 0x98) = 0xffff;\n      *(ushort *)(node + 0x9a) = 0xffff;\n      *(int *)(node + 0xa0) = _DAT_00636588;\n      *(ushort *)(node + 0xa6) = 0xffff;\n      _DAT_0063725c = (short *)(uintptr_t)node;\n      for (i = 0; i < 0x12; i = i + 1) {\n        *(ushort *)(node + 0x0e + i * 2) = 0xffff;\n      }\n      for (i = 0; i < 4; i = i + 1) {\n        node[0x32 + i * 0x19] = 0;\n      }\n      return CONCAT44(param_2,(undefined4)(uintptr_t)node);\n    }\n    if ((int)FUN_00452ebc(0,0) == 0) {\n      return CONCAT44(param_2,0);\n    }\n  } while( true );\n}\n\n\n\n/* 004263ac */"
);
source = source.replace(
  /undefined8 __fastcall FUN_004263ac\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00426410 \*\//,
  "undefined8 __fastcall FUN_004263ac(undefined4 param_1,undefined4 param_2)\n\n{\n  int cursor;\n  int next;\n  int parent;\n  undefined2 *node;\n  undefined8 result;\n\n  parent = (int)(uintptr_t)param_1;\n  if ((uintptr_t)parent < 0x10000u || IsBadReadPtr((void *)(uintptr_t)parent,0x8)) {\n    return CONCAT44(param_2,0);\n  }\n  result = FUN_004533ac(param_1,param_2);\n  node = (undefined2 *)result;\n  if (node == (undefined2 *)0x0) {\n    return CONCAT44(param_2,0);\n  }\n  *node = 0xffff;\n  cursor = *(int *)(parent + 4);\n  if (cursor == 0) {\n    *(undefined2 **)(parent + 4) = node;\n  }\n  else {\n    if ((uintptr_t)cursor < 0x10000u || IsBadReadPtr((void *)(uintptr_t)cursor,0x1c)) {\n      return CONCAT44(param_2,node);\n    }\n    next = *(int *)(cursor + 0x18);\n    while (next != 0) {\n      cursor = next;\n      if ((uintptr_t)cursor < 0x10000u || IsBadReadPtr((void *)(uintptr_t)cursor,0x1c)) {\n        return CONCAT44(param_2,node);\n      }\n      next = *(int *)(cursor + 0x18);\n    }\n    *(undefined2 **)(cursor + 0x18) = node;\n  }\n  *(undefined4 *)(node + 0xc) = 0;\n  node[1] = 0xffff;\n  node[2] = 0;\n  *(undefined4 *)(node + 3) = 0;\n  node[7] = 2;\n  *(undefined4 *)(node + 5) = 0;\n  return CONCAT44(param_2,node);\n}\n\n\n\n/* 00426410 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_004533ac\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00453414 \*\//,
  "undefined8 __fastcall FUN_004533ac(undefined4 param_1,undefined4 param_2)\n\n{\n  byte *node;\n  int offset;\n\n  (void)param_1;\n  do {\n    node = (byte *)0x0;\n    for (offset = 0; offset < 0x43f8; offset = offset + 0x1d) {\n      if ((((byte *)0x009377c4)[offset + 0x1c] & 0x80) != 0) {\n        node = (byte *)0x009377c4 + offset;\n        memset(node,0,0x1d);\n        break;\n      }\n    }\n    if (node != (byte *)0x0) {\n      if (E2R_StartupDiagEnabled() && E2R_scene_load_request_id == 0) {\n        fprintf(stderr,\"scene child alloc: requested=%d node=0x%lx offset=%d\\n\",\n                E2R_scene_load_request_id,(unsigned long)(uintptr_t)node,offset);\n      }\n      return CONCAT44(param_2,(undefined4)(uintptr_t)node);\n    }\n    if ((int)FUN_00452ebc(0,0) == 0) {\n      return CONCAT44(param_2,0);\n    }\n  } while( true );\n}\n\n\n\n/* 00453414 */"
);
source = source.replace(
  "      FUN_00426ac4(uVar10,(int)local_1c);",
  "      FUN_00426ac4((undefined4)(uintptr_t)psVar8,(int)local_1c);"
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
  "  if ((0x21 < _DAT_0067bc92) && (_DAT_0067bc92 < 0x28)) {",
  "  if (E2R_fan_parse_stream != (int *)0x0 &&\n      (uint)E2R_fan_parse_stream[6] == E2R_STREAM_MAGIC &&\n      0x33 <= _DAT_0067bc92 && 0 < DAT_0047a77c &&\n      (uint)DAT_0047a77c > (uint)E2R_fan_parse_stream[1] / 36u) {\n    if (E2R_fan_phase_diag_count < 32) {\n      E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n      fprintf(stderr,\"FAN 47638 invalid count: entries=%d offset=%u remaining=%d\\n\",\n              DAT_0047a77c,E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n    }\n    *(byte *)(E2R_fan_parse_stream + 3) = *(byte *)(E2R_fan_parse_stream + 3) | 0x10;\n    return;\n  }\n  if ((0x21 < _DAT_0067bc92) && (_DAT_0067bc92 < 0x28)) {"
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
  "      }\n    }\n  }\n  if (E2R_fan_phase_diag_count < 32) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN 47638 complete: offset=%u remaining=%d\\n\",\n            E2R_FanStreamOffset(),E2R_fan_parse_stream[1]);\n  }\n  E2R_LogSceneGridProbe(\"47638.complete\",-8448,-15616);\n  return;\n}\n\n\n\n/* 00447d94 */"
);
source = source.replace(
  /undefined8 __fastcall FUN_00447d94\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004486d8 \*\//,
`undefined8 __fastcall FUN_00447d94(undefined4 param_1,undefined4 param_2)

{
  byte *base;
  byte *end;
  byte *limit;
  byte *rec;
  byte *scan;
  int *stream;
  undefined8 uVar1;
  uint id;
  uint offset;
  uint resource_offset;
  uint action_count;
  uint actor_count;
  uint rep_count;
  uint row;
  uint row_end;
  uint scene_count;
  uint type;

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
  base = (byte *)(uintptr_t)stream[5];
  end = (byte *)(uintptr_t)stream[2];

  if (base + 4 <= end && base[0] == 'F' && base[1] == 'A' &&
      base[2] == 'N' && base[3] == 'T') {
    for (offset = 0; offset < 2500; offset = offset + 1) {
      *(int *)(0x650fa0 + offset * 4) = -1;
    }
    for (offset = 0; offset < 5000; offset = offset + 1) {
      *(int *)(0x653840 + offset * 4) = -1;
    }
    for (offset = 0; offset < 2000; offset = offset + 1) {
      *(int *)(0x64f060 + offset * 4) = -1;
    }
    for (offset = 0; offset < 500; offset = offset + 1) {
      *(int *)(0x663a10 + offset * 4) = -1;
    }
    for (offset = 0; offset < 700; offset = offset + 1) {
      *(int *)(0x662f20 + offset * 4) = -1;
    }
    for (offset = 0; offset < 1200; offset = offset + 1) {
      *(int *)(0x6445e8 + offset * 4) = -1;
      *(int *)(0x6467a8 + offset * 4) = -1;
    }
    action_count = 0;
    actor_count = 0;
    rep_count = 0;
    scene_count = 0;
    for (scan = base; scan + 14 <= end; scan = scan + 1) {
      if (scan[0] != 'F' || scan[1] != 'A' || scan[2] != 'N' || scan[3] != 'T') {
        continue;
      }
      resource_offset = (uint)(scan - base);
      limit = scan + 0x4000;
      if (end < limit) {
        limit = end;
      }
      for (rec = scan + 4; rec + 10 <= limit; rec = rec + 10) {
        type = ((uint)rec[0] << 8) | (uint)rec[1];
        id = ((uint)rec[2] << 8) | (uint)rec[3];
        if (type == 0x08 && id < 5000) {
          if (*(int *)(0x653840 + id * 4) < 0) {
            actor_count = actor_count + 1;
          }
          *(int *)(0x653840 + id * 4) = (int)resource_offset;
          break;
        }
        if (type == 0x19 && id < 0x9c4) {
          if (*(int *)(0x650fa0 + id * 4) < 0) {
            scene_count = scene_count + 1;
          }
          *(int *)(0x650fa0 + id * 4) = (int)resource_offset;
          break;
        }
        if (E2R_ActionIndexProbeEnabled() && type == 0x0b && id < 2000) {
          if (*(int *)(0x64f060 + id * 4) < 0) {
            action_count = action_count + 1;
          }
          *(int *)(0x64f060 + id * 4) = (int)resource_offset;
          break;
        }
      }
      rec = scan + 0x42;
      if (rec + 4 <= limit) {
        type = ((uint)rec[0] << 8) | (uint)rec[1];
        id = ((uint)rec[2] << 8) | (uint)rec[3];
        if (type == 0x35 && id < 500) {
          if (*(int *)(0x663a10 + id * 4) < 0) {
            rep_count = rep_count + 1;
          }
          *(int *)(0x663a10 + id * 4) = (int)resource_offset;
        }
      }
    }
    stream[0] = (int)(uintptr_t)base;
    stream[1] = (int)(uint)(end - base);
    if (E2R_archive_read_diag_count < 8) {
      E2R_archive_read_diag_count = E2R_archive_read_diag_count + 1;
      fprintf(stderr,"archive 47d94 flat FANT: actions=%u actors=%u reps=%u scenes=%u bytes=%u\\n",
              action_count,actor_count,rep_count,scene_count,(uint)(end - base));
    }
    return CONCAT44(param_2,1);
  }

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
  "  uVar13 = 0;\n  local_58 = 0;",
  "  E2R_TraceActorUpdateStage(\"27584.entry\",in_EAX);\n  uVar13 = 0;\n  local_58 = 0;"
);
source = source.replace(
  "  psVar8 = DAT_0047a470;",
  "  E2R_TraceActorUpdateStage(\"27584.after-debug\",local_6c);\n  psVar8 = DAT_0047a470;"
);
source = source.replace(
  "  if (local_6c[0x91] < 0) {",
  "  E2R_TraceActorUpdateStage(\"27584.before-rep\",local_6c);\n  E2R_RetainCurrentRepForMissingTarget(\"27584.before-rep-missing\",local_6c);\n  if (local_6c[0x91] < 0) {"
);
source = source.replace(
  "      FUN_00451998((int)local_6c[0x91],psVar15);\n      *(undefined4 *)(local_6c + 0x8f) =",
  "      E2R_TraceActorUpdateStage(\"27584.before-51998-nullrep\",local_6c);\n      FUN_00451998((int)local_6c[0x91],psVar15);\n      E2R_TraceActorUpdateStage(\"27584.after-51998-nullrep\",local_6c);\n      *(undefined4 *)(local_6c + 0x8f) ="
);
source = source.replace(
  "        FUN_00451998((int)local_6c[0x91],psVar15);\n        *(undefined4 *)(local_6c + 0x8f) =",
  "        E2R_TraceActorUpdateStage(\"27584.before-51998-switch\",local_6c);\n        FUN_00451998((int)local_6c[0x91],psVar15);\n        E2R_TraceActorUpdateStage(\"27584.after-51998-switch\",local_6c);\n        *(undefined4 *)(local_6c + 0x8f) ="
);
source = source.replace(
  "  if (((local_70 != (short *)0x0) &&\n      (local_54 = *(int *)(*(int *)(local_70 + 0x2a) + 8), local_54 == 0)) &&\n     (local_54 = *(int *)(local_70 + 0xf), local_54 == 0)) {\n    local_70 = (short *)0x0;\n  }\n  local_60 = *(int *)(*(int *)(local_6c + 0x2a) + 8);\n  if ((local_60 == 0) && (local_60 = *(int *)(local_6c + 0xf), local_60 == 0)) {\n    local_70 = (short *)0x0;\n  }",
  "  local_54 = E2R_ActorMotionRef(local_70);\n  if (local_54 == 0) {\n    local_70 = (short *)0x0;\n  }\n  local_60 = E2R_ActorMotionRef(local_6c);\n  if (local_60 == 0) {\n    local_70 = (short *)0x0;\n  }"
);
source = source.replace(
  "            if ((*(int *)(*(int *)(local_6c + 0x2a) + 0x1c) == 0) ||\n               (*(int *)(*(int *)(*(int *)(local_6c + 0x2a) + 0x1c) + 0x13a) == 0)) {\n              if ((*(int *)(*(int *)(local_6c + 0x2a) + 0x20) == 0) ||\n                 (*(int *)(*(int *)(*(int *)(local_6c + 0x2a) + 0x20) + 0x13a) == 0)) {",
  "            if (E2R_ActorSideLinkedAction(local_6c,0x1c) == 0) {\n              if (E2R_ActorSideLinkedAction(local_6c,0x20) == 0) {"
);
source = source.replace(
  "      iVar7 = CONCAT22((short)((uint)param_1 >> 0x10),local_6c[0x91]);\n      if (*psVar8 != local_6c[0x91]) {",
  "      iVar7 = CONCAT22((short)((uint)param_1 >> 0x10),local_6c[0x91]);\n      E2R_RetainCurrentRepForMissingTarget(\"27584.switch-missing\",local_6c);\n      if (*psVar8 != local_6c[0x91]) {"
);
source = source.replace(
  "  iVar17 = *(int *)(local_6c + 0x93);",
  "  E2R_TraceActorUpdateStage(\"27584.before-action-select\",local_6c);\n  iVar17 = *(int *)(local_6c + 0x93);"
);
source = source.replace(
  "  if (((*(short **)(local_6c + 0x8f) == (short *)0x0) || (**(short **)(local_6c + 0x8f) == 0)) &&",
  "  E2R_TraceActorUpdateStage(\"27584.before-idle-test\",local_6c);\n  if (((*(short **)(local_6c + 0x8f) == (short *)0x0) || (**(short **)(local_6c + 0x8f) == 0)) &&"
);
source = source.replace(
  "    *(byte *)((int)local_6c + 3) = *(byte *)((int)local_6c + 3) | 4;\n    return;",
  "    *(byte *)((int)local_6c + 3) = *(byte *)((int)local_6c + 3) | 4;\n    E2R_TraceActorUpdateStage(\"27584.return-idle\",local_6c);\n    return;"
);
source = source.replace(
  "  uVar19 = 1000;",
  "  E2R_TraceActorUpdateStage(\"27584.before-target\",local_6c);\n  uVar19 = 1000;"
);
source = source.replace(
  "LAB_00427d14:\n  psVar15 = (short *)((ulonglong)lVar28 >> 0x20);",
  "LAB_00427d14:\n  E2R_TraceActorUpdateStage(\"27584.after-target-select\",local_6c);\n  psVar15 = (short *)((ulonglong)lVar28 >> 0x20);"
);
source = source.replace(
  "        lVar15 = FUN_00427584(psVar10,iVar7);",
  "        E2R_TraceActorLoopStage(\"42a70c.before-27584\",(uintptr_t)iVar8,actor_loop_guard);\n        E2R_TraceFrameStage(\"42a70c.before-27584\");\n        lVar15 = FUN_00427584((undefined4)(uintptr_t)iVar8,iVar7);\n        E2R_TraceFrameStage(\"42a70c.after-27584\");\n        E2R_TraceActorLoopStage(\"42a70c.after-27584\",(uintptr_t)iVar8,actor_loop_guard);"
);
source = source.replace(
  /(void __fastcall FUN_00421074\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  short \*psVar6;\r?\n\s*)FUN_00457818\(param_1,param_2\);/,
  "$1in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX == (short *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      0x1000000u <= (uintptr_t)in_EAX || IsBadReadPtr(in_EAX,0x17c)) {\n    return;\n  }\n  FUN_00457818(param_1,param_2);"
);
source = source.replace(
  "  FUN_00457818(param_1,param_2);\n  psVar6 = *(short **)(in_EAX + 0x79);",
  "  E2R_TraceActorLoopStage(\"21074.entry\",(uintptr_t)in_EAX,0);\n  FUN_00457818(param_1,param_2);\n  E2R_TraceActorLoopStage(\"21074.after-57818\",(uintptr_t)in_EAX,0);\n  psVar6 = *(short **)(in_EAX + 0x79);"
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
  "      do {\n        iVar10 = local_54;\n        psVar9 = (short *)(local_54 + 0x10);",
  "      do {\n        if ((uintptr_t)local_54 < 0x10000u || 0x70000000u <= (uintptr_t)local_54 ||\n            IsBadReadPtr((void *)(uintptr_t)local_54,0x2a)) {\n          break;\n        }\n        iVar10 = local_54;\n        psVar9 = (short *)(local_54 + 0x10);"
);
source = source.replace(
  "  else {\n    iVar10 = *(int *)(*(int *)(local_3c + 0x1e) + 0xca);\n  }",
  "  else {\n    iVar10 = *(int *)(local_3c + 0x1e);\n    if (iVar10 == 0 || (uintptr_t)iVar10 < 0x10000u || 0x70000000u <= (uintptr_t)iVar10 ||\n        IsBadReadPtr((void *)(uintptr_t)iVar10,0xce)) {\n      return;\n    }\n    iVar10 = *(int *)(iVar10 + 0xca);\n  }"
);
source = source.replace(
  "  do {\n    local_4c = (short *)(iVar10 + 0x50);",
  "  do {\n    if ((uintptr_t)iVar10 < 0x10000u || 0x70000000u <= (uintptr_t)iVar10 ||\n        IsBadReadPtr((void *)(uintptr_t)iVar10,0x136)) {\n      return;\n    }\n    local_4c = (short *)(iVar10 + 0x50);"
);
source = source.replace(
  "    FUN_00423858(0,0);",
  "    FUN_00423858((undefined4)(uintptr_t)in_EAX,0);"
);
source = source.replace(
  "    FUN_00423858((undefined4)(uintptr_t)in_EAX,0);\n    iVar5 = extraout_ECX_04;",
  "    E2R_TraceActorLoopStage(\"21074.before-23858-root\",(uintptr_t)in_EAX,0);\n    FUN_00423858((undefined4)(uintptr_t)in_EAX,0);\n    E2R_TraceActorLoopStage(\"21074.after-23858-root\",(uintptr_t)in_EAX,0);\n    iVar5 = extraout_ECX_04;"
);
source = source.replace(
  "        FUN_00423858(iVar5,0);\n        iVar5 = extraout_ECX_05;",
  "        E2R_TraceActorLoopStage(\"21074.before-23858-linked\",(uintptr_t)*(int *)(iVar1 + 0x44),0);\n        FUN_00423858((undefined4)(uintptr_t)*(int *)(iVar1 + 0x44),0);\n        E2R_TraceActorLoopStage(\"21074.after-23858-linked\",(uintptr_t)*(int *)(iVar1 + 0x44),0);\n        iVar5 = extraout_ECX_05;"
);
source = source.replace(
  "  *(byte *)(in_EAX + 0xa3) = *(byte *)(in_EAX + 0xa3) | 0x80;\n  return;\n}\n\n\n\n/* 004211c8 */",
  "  *(byte *)(in_EAX + 0xa3) = *(byte *)(in_EAX + 0xa3) | 0x80;\n  E2R_TraceActorLoopStage(\"21074.exit\",(uintptr_t)in_EAX,0);\n  return;\n}\n\n\n\n/* 004211c8 */"
);
source = source.replace(
  "        FUN_004249f4();",
  "        FUN_004249f4((undefined4)(uintptr_t)iVar10);"
);
source = source.replace(
  "      FUN_004249f4();\n      iVar4 = extraout_EDX_00;",
  "      FUN_004249f4((undefined4)(uintptr_t)iVar4);"
);
source = source.replace(
  "            FUN_00424d58();\n            iVar2 = extraout_EDX_02;",
  "            FUN_00424d58();"
);
source = source.replace(
  "            FUN_00424d14();\n            FUN_00424dd8(extraout_ECX_01);\n            iVar4 = extraout_EDX_03;",
  "            FUN_00424d14();\n            FUN_00424dd8(extraout_ECX_01);"
);
source = source.replace(
  "            FUN_00424d98();\n            iVar2 = extraout_EDX_04;",
  "            FUN_00424d98();"
);
source = source.replace(
  "            FUN_00424cbc();\n            FUN_00424dd8(extraout_ECX_00);\n            iVar2 = extraout_EDX_01;",
  "            FUN_00424cbc();\n            FUN_00424dd8(extraout_ECX_00);"
);
source = source.replace(
  "        FUN_00424d58();\n        FUN_00424d14();\n        FUN_00424dd8(extraout_ECX);\n        FUN_00424d98();",
  "        FUN_00424d58(iVar10);\n        FUN_00424d14(iVar10);\n        FUN_00424dd8(extraout_ECX,iVar10);\n        FUN_00424d98(iVar10);"
);
source = source.replaceAll("FUN_00424d58();", "FUN_00424d58(iVar2);");
source = source.replaceAll("FUN_00424d14();\n            FUN_00424dd8(extraout_ECX_01);",
                           "FUN_00424d14(iVar4);\n            FUN_00424dd8(extraout_ECX_01,iVar4);");
source = source.replaceAll("FUN_00424d98();", "FUN_00424d98(iVar2);");
source = source.replaceAll("FUN_00424cbc();\n            FUN_00424dd8(extraout_ECX_00);",
                           "FUN_00424cbc(iVar2);\n            FUN_00424dd8(extraout_ECX_00,iVar2);");
source = source.replace(
  "if (*(short *)(in_EAX + 0x96) != 0) {\n    FUN_00423070();",
  "if (*(short *)(in_EAX + 0x96) != 0) {\n    FUN_00423070((int *)(uintptr_t)(in_EAX + 0x92));"
);
source = source.replaceAll("FUN_00423070();", "FUN_00423070((int *)(uintptr_t)in_EAX);");
source = source.replaceAll("FUN_00425538();", "FUN_00425538(iVar1);");
source = source.replaceAll("FUN_00425018();", "FUN_00425018(iVar1);");
source = source.replaceAll("        FUN_00425538(iVar1);\n        iVar1 = extraout_EDX;",
                           "        FUN_00425538(iVar1);");
source = source.replaceAll("        FUN_00425018(iVar1);\n        iVar1 = extraout_EDX_00;",
                           "        FUN_00425018(iVar1);");
source = source.replaceAll("      FUN_00425538(iVar1);\n      iVar1 = extraout_EDX;",
                           "      FUN_00425538(iVar1);");
source = source.replace(
  /void FUN_00423070\(void\)\s*\{\s*int \*in_EAX;\s*int iVar1;\s*int iVar2;\s*int iVar3;\s*iVar1 = DAT_0047a2a4 \/ \(\*\(int \*\)\(\(int\)in_EAX \+ 2\) >> 0x10\);/,
  "void FUN_00423070(int *coord)\n\n{\n  int *in_EAX;\n  int iVar1;\n  int iVar2;\n  int iVar3;\n\n  in_EAX = coord;\n  if (in_EAX == (int *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      0x70000000u <= (uintptr_t)in_EAX || IsBadReadPtr(in_EAX,6) ||\n      (*(int *)((int)in_EAX + 2) >> 0x10) == 0) {\n    return;\n  }\n  iVar1 = DAT_0047a2a4 / (*(int *)((int)in_EAX + 2) >> 0x10);"
);
source = source.replace(
  /void FUN_00425018\(void\)\s*\{\s*(?:int|undefined4) in_EAX;\s*int iVar1;/,
  "void FUN_00425018(int actor)\n\n{\n  int in_EAX;\n  int iVar1;"
);
source = source.replace(
  "  local_76 = 0;\n  local_56 = *(undefined4 *)(in_EAX + 0x22);",
  "  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0xd2)) {\n    return;\n  }\n  local_76 = 0;\n  local_56 = *(undefined4 *)(in_EAX + 0x22);"
);
source = source.replace(
  /void FUN_00425538\(void\)\s*\{\s*(?:int|undefined4) in_EAX;\s*int iVar1;/,
  "void FUN_00425538(int actor)\n\n{\n  int in_EAX;\n  int iVar1;"
);
source = source.replace(
  "  if (*(short *)(in_EAX + 0x96) != 0) {\n    FUN_00423070((int *)(uintptr_t)(in_EAX + 0x92));",
  "  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x9a)) {\n    return;\n  }\n  if (*(short *)(in_EAX + 0x96) != 0) {\n    FUN_00423070((int *)(uintptr_t)(in_EAX + 0x92));"
);
source = source.replace(
  /void FUN_00424cbc\(void\)\s*\{\s*(?:int|undefined4) in_EAX;\s*int extraout_EDX;\s*int extraout_EDX_00;\s*int iVar1;\s*for \(iVar1 = \*\(int \*\)\(in_EAX \+ 0x1e\);/,
  "void FUN_00424cbc(int actor)\n\n{\n  int in_EAX;\n  int extraout_EDX;\n  int extraout_EDX_00;\n  int iVar1;\n\n  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x22)) {\n    return;\n  }\n  for (iVar1 = *(int *)(in_EAX + 0x1e);"
);
source = source.replace(
  /void FUN_00424d14\(void\)\s*\{\s*(?:int|undefined4) in_EAX;\s*int extraout_EDX;\s*int extraout_EDX_00;\s*int iVar1;\s*for \(iVar1 = \*\(int \*\)\(in_EAX \+ 0x1e\);/,
  "void FUN_00424d14(int actor)\n\n{\n  int in_EAX;\n  int extraout_EDX;\n  int extraout_EDX_00;\n  int iVar1;\n\n  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x22)) {\n    return;\n  }\n  for (iVar1 = *(int *)(in_EAX + 0x1e);"
);
source = source.replace(
  /void FUN_00424d58\(void\)\s*\{\s*(?:int|undefined4) in_EAX;\s*int extraout_EDX;\s*int iVar1;\s*for \(iVar1 = \*\(int \*\)\(in_EAX \+ 0x1e\);/,
  "void FUN_00424d58(int actor)\n\n{\n  int in_EAX;\n  int extraout_EDX;\n  int iVar1;\n\n  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x22)) {\n    return;\n  }\n  for (iVar1 = *(int *)(in_EAX + 0x1e);"
);
source = source.replace(
  /void FUN_00424d98\(void\)\s*\{\s*(?:int|undefined4) in_EAX;\s*int extraout_EDX;\s*int iVar1;\s*for \(iVar1 = \*\(int \*\)\(in_EAX \+ 0x1e\);/,
  "void FUN_00424d98(int actor)\n\n{\n  int in_EAX;\n  int extraout_EDX;\n  int iVar1;\n\n  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x22)) {\n    return;\n  }\n  for (iVar1 = *(int *)(in_EAX + 0x1e);"
);
source = source.replace(
  /void __fastcall FUN_00424dd8\(int param_1\)\s*\{\s*byte bVar1;\s*(?:int|undefined4) in_EAX;\s*int extraout_ECX;\s*int extraout_EDX;\s*int iVar2;\s*iVar2 = \*\(int \*\)\(in_EAX \+ 0xd8\);/,
  "void __fastcall FUN_00424dd8(int param_1,int actor)\n\n{\n  byte bVar1;\n  int in_EAX;\n  int extraout_ECX;\n  int extraout_EDX;\n  int iVar2;\n\n  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0xdc)) {\n    return;\n  }\n  iVar2 = *(int *)(in_EAX + 0xd8);"
);
source = source.replace(
  "      FUN_00424e44(param_1);\n      param_1 = extraout_ECX;\n      iVar2 = extraout_EDX;",
  "      FUN_00424e44(param_1,iVar2);"
);
source = source.replace(
  /void __fastcall FUN_00424e44\(int param_1\)\s*\{\s*(?:int|undefined4) in_EAX;\s*int iVar1;\s*if \(-1 < \*\(short \*\)\(in_EAX \+ 0x1c\)\) \{/,
  "void __fastcall FUN_00424e44(int param_1,int node)\n\n{\n  int in_EAX;\n  int iVar1;\n\n  in_EAX = node;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x26) ||\n      IsBadReadPtr((void *)(uintptr_t)*(int *)(in_EAX + 0x22),4)) {\n    return;\n  }\n  if (-1 < *(short *)(in_EAX + 0x1c)) {"
);
source = source.replace(
  "  FUN_00433d30(param_1,iVar1);",
  "  FUN_00433d30(in_EAX,iVar1);"
);
source = source.replace(
  /void __fastcall FUN_00431a7c\(undefined4 param_1,int param_2\)\s*\{\s*byte bVar1;\s*short sVar2;\s*int in_EAX;/,
  "void __fastcall FUN_00431a7c(int actor,int param_2)\n\n{\n  byte bVar1;\n  short sVar2;\n  int in_EAX;"
);
source = source.replace(
  "  FUN_00457818(param_1,param_2);\n  iVar10 = *(int *)(in_EAX + 4);",
  "  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x2c)) {\n    return;\n  }\n  FUN_00457818((undefined4)(uintptr_t)in_EAX,param_2);\n  if (IsBadReadPtr((void *)(uintptr_t)in_EAX,0x10) || *(int *)(in_EAX + 4) == 0 ||\n      *(int *)(in_EAX + 8) == 0 || *(int *)(in_EAX + 0xc) == 0 ||\n      IsBadReadPtr((void *)(uintptr_t)*(int *)(in_EAX + 4),0x1c) ||\n      IsBadReadPtr((void *)(uintptr_t)*(int *)(in_EAX + 8),0x1c) ||\n      IsBadReadPtr((void *)(uintptr_t)*(int *)(in_EAX + 0xc),0x1c)) {\n    return;\n  }\n  iVar10 = *(int *)(in_EAX + 4);"
);
source = source.replace(
  /void __fastcall FUN_00433d30\(undefined4 param_1,int param_2\)\s*\{\s*undefined2 uVar1;/,
  "void __fastcall FUN_00433d30(int actor,int param_2)\n\n{\n  undefined2 uVar1;"
);
source = source.replace(
  "  if (*(int *)(in_EAX + 0x28) != 0) {",
  "  in_EAX = actor;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x40)) {\n    return;\n  }\n  if (*(int *)(in_EAX + 0x28) != 0) {"
);
source = source.replaceAll(
  "      FUN_00431a7c(in_EAX,param_2);\n      iVar8 = extraout_ECX_00;",
  "      FUN_00431a7c(in_EAX,param_2);\n      iVar8 = in_EAX;"
);
source = source.replaceAll(
  "      FUN_00437ae4(in_EAX,param_2);\n      iVar8 = extraout_ECX;",
  "      FUN_00437ae4(in_EAX,param_2);\n      iVar8 = in_EAX;"
);
source = source.replaceAll(
  "      FUN_00431a7c(iVar8,param_2);\n      iVar8 = extraout_ECX_02;",
  "      FUN_00431a7c(iVar8,param_2);"
);
source = source.replaceAll(
  "      FUN_00437ae4(iVar8,param_2);\n      iVar8 = extraout_ECX_01;",
  "      FUN_00437ae4(iVar8,param_2);"
);
source = source.replace(
  /(void FUN_004249f4\(void\)[\s\S]*?\r?\n  int iVar6;\r?\n\s*)for \(iVar1 = \*\(int \*\)\(in_EAX \+ 0x1e\);/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 0 || (uint)in_EAX < 0x10000u || 0x1000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x17c)) {\n    return;\n  }\n  for (iVar1 = *(int *)(in_EAX + 0x1e);"
);
source = source.replace(
  "    FUN_00424ed0();\n    iVar6 = extraout_ECX;",
  "    E2R_actor_calc_context = iVar1;\n    FUN_00424ed0();\n    E2R_actor_calc_context = 0;\n    iVar6 = extraout_ECX;"
);
source = source.replace(
  /(void FUN_00424ed0\(void\)[\s\S]*?\r?\n  short local_20 \[4\];\r?\n\s*)if \(\(DAT_0047a34a == 0\) \|\| \(DAT_0047a366 != 0\)\) \{/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || (uintptr_t)in_EAX < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x12c)) {\n    return;\n  }\n  if ((DAT_0047a34a == 0) || (DAT_0047a366 != 0)) {"
);
source = source.replace(
  "void FUN_004249f4(void)",
  "void FUN_004249f4(undefined4 param_1)"
);
source = source.replace(
  "  DAT_00479de8 = 1;\n  return CONCAT44(param_2,uVar3);",
  "  DAT_00479de8 = 1;\n  if (_DAT_0073cc3c == 0 && E2R_start_game_probe_last_mode == 0 &&\n      E2R_ShouldForceScene785Fallback()) {\n    E2R_SelectSceneRecord(785);\n  }\n  return CONCAT44(param_2,uVar3);"
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
  "        FUN_0044c224(param_1);\n        param_1 = extraout_ECX;\n      }\n      FUN_0044c164(param_1);",
  "        FUN_0044c224((undefined4)(uintptr_t)DAT_0047a470);\n        param_1 = extraout_ECX;\n      }\n      FUN_0044c164((undefined4)(uintptr_t)DAT_0047a470);"
);
source = source.replace(
  "  if (DAT_0047a470 != 0 &&\n     ((uint)DAT_0047a470 < 0x10000u || 0x70000000u <= (uint)DAT_0047a470 ||",
  "  E2R_TraceFrameStage(\"211c8.entry\");\n  if (DAT_0047a470 != 0 &&\n     ((uint)DAT_0047a470 < 0x10000u || 0x70000000u <= (uint)DAT_0047a470 ||"
);
source = source.replace(
  "        FUN_0044c224((undefined4)(uintptr_t)DAT_0047a470);\n        param_1 = extraout_ECX;",
  "        E2R_TraceFrameStage(\"211c8.before-4c224\");\n        FUN_0044c224((undefined4)(uintptr_t)DAT_0047a470);\n        E2R_TraceFrameStage(\"211c8.after-4c224\");\n        param_1 = extraout_ECX;"
);
source = source.replace(
  "      FUN_0044c164((undefined4)(uintptr_t)DAT_0047a470);\n    }\n    else if",
  "      E2R_TraceFrameStage(\"211c8.before-4c164\");\n      FUN_0044c164((undefined4)(uintptr_t)DAT_0047a470);\n      E2R_TraceFrameStage(\"211c8.after-4c164\");\n    }\n    else if"
);
source = source.replaceAll(
  "FUN_00448744(param_1,DAT_0047a470)",
  "FUN_00448744((undefined4)(uintptr_t)(DAT_0047a470 + 0x84),DAT_0047a470)"
);
source = source.replace(
  "      FUN_0043a6e0(uVar3,(int)sVar2);",
  "      FUN_0043a6e0(uVar3,(int)sVar2);"
);
source = source.replace(
  "  sVar2 = (short)uVar3;\n  if ((undefined1 *)0x0067c728 + sVar2 * 0x1c == _DAT_0073cc3c) {",
  "  sVar2 = (short)uVar3;\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {\n    uintptr_t desc = 0x0068cd68 + (uintptr_t)((int)uVar7 * 0xc);\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    if ((int)uVar7 < 0 || IsBadReadPtr((void *)desc,0xc)) {\n      fprintf(stderr,\"scene select 4c224: lookup=%d scene_id=%d desc=0x%lx bad_desc=1 current=0x%lx scene=0x%lx\\n\",\n              (int)uVar7,(int)sVar2,(unsigned long)desc,\n              (unsigned long)DAT_0047a470,(unsigned long)_DAT_0073cc3c);\n    }\n    else {\n      fprintf(stderr,\"scene select 4c224: lookup=%d scene_id=%d desc=0x%lx bytes=%02x,%02x,%02x,%02x words=%04x,%04x current=0x%lx scene=0x%lx\\n\",\n              (int)uVar7,(int)sVar2,(unsigned long)desc,\n              (unsigned int)*(byte *)desc,(unsigned int)*(byte *)(desc + 1),\n              (unsigned int)*(byte *)(desc + 2),(unsigned int)*(byte *)(desc + 3),\n              (unsigned int)*(ushort *)(desc + 8),(unsigned int)*(ushort *)(desc + 10),\n              (unsigned long)DAT_0047a470,(unsigned long)_DAT_0073cc3c);\n    }\n  }\n  if ((undefined1 *)0x0067c728 + sVar2 * 0x1c == _DAT_0073cc3c) {"
);
source = source.replace(
  "  sVar2 = (short)uVar3;\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {",
  "  sVar2 = (short)uVar3;\n  if (E2R_scene_select_diag_count < 64 && (E2R_RuntimeDiagEnabled() || sVar2 < 1)) {\n    E2R_scene_select_diag_count = E2R_scene_select_diag_count + 1;\n    fprintf(stderr,\n            \"scene select 4c224 compact: lookup=%d scene_id=%d uVar3=0x%x current=0x%lx scene=0x%lx \"\n            \"pos=%d,%d,%d last_scene_hint=%lu\\n\",\n            (int)uVar7,(int)sVar2,(unsigned int)uVar3,\n            (unsigned long)DAT_0047a470,(unsigned long)_DAT_0073cc3c,\n            DAT_0047a470 != 0 && !IsBadReadPtr((void *)(uintptr_t)DAT_0047a470,0x8a) ?\n            (int)*(short *)(DAT_0047a470 + 0x84) : 0,\n            DAT_0047a470 != 0 && !IsBadReadPtr((void *)(uintptr_t)DAT_0047a470,0x8a) ?\n            (int)*(short *)(DAT_0047a470 + 0x86) : 0,\n            DAT_0047a470 != 0 && !IsBadReadPtr((void *)(uintptr_t)DAT_0047a470,0x8a) ?\n            (int)*(short *)(DAT_0047a470 + 0x88) : 0,\n            (unsigned long)_DAT_0047a778);\n  }\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {"
);
source = source.replace(
  "  FUN_0044c6bc();\n  lVar8 = FUN_00449b4c(extraout_ECX,extraout_EDX);",
  "  FUN_0044c6bc();\n  E2R_ActivateSelectedSceneRecord(sVar2);\n  lVar8 = FUN_00449b4c(extraout_ECX,extraout_EDX);"
);
source = source.replace(
  "    FUN_004575c4();\n    FUN_00457780(extraout_ECX_00,extraout_EDX);",
  "    E2R_TraceFrameStage(\"211c8.before-575c4\");\n    FUN_004575c4();\n    E2R_TraceFrameStage(\"211c8.after-575c4\");\n    FUN_00457780(extraout_ECX_00,extraout_EDX);\n    E2R_TraceFrameStage(\"211c8.after-57780\");"
);
source = source.replace(
  "  iVar7 = _DAT_0063726c;\n  if (_DAT_00636690 != 0) {",
  "  E2R_TraceFrameStage(\"211c8.before-list-pass\");\n  iVar7 = _DAT_0063726c;\n  if (_DAT_00636690 != 0) {"
);
source = source.replace(
  "  for (; iVar5 = _DAT_0063726c, iVar7 != 0; iVar7 = *(int *)(iVar7 + 0x4c)) {\n    *(byte *)(iVar7 + 0x146) = *(byte *)(iVar7 + 0x146) & 0x7f;\n  }\n  for (; iVar5 != 0; iVar5 = *(int *)(iVar5 + 0x4c)) {",
  "  for (; iVar5 = _DAT_0063726c, iVar7 != 0; iVar7 = *(int *)(iVar7 + 0x4c)) {\n    *(byte *)(iVar7 + 0x146) = *(byte *)(iVar7 + 0x146) & 0x7f;\n  }\n  E2R_TraceFrameStage(\"211c8.after-clear-146\");\n  for (; iVar5 != 0; iVar5 = *(int *)(iVar5 + 0x4c)) {"
);
source = source.replace(
  "      FUN_00421074((undefined4)(uintptr_t)iVar5,param_2);\n      param_1 = extraout_ECX_02;",
  "      E2R_TraceActorLoopStage(\"211c8.before-21074\",(uintptr_t)iVar5,0);\n      FUN_00421074((undefined4)(uintptr_t)iVar5,param_2);\n      E2R_TraceActorLoopStage(\"211c8.after-21074\",(uintptr_t)iVar5,0);\n      param_1 = extraout_ECX_02;"
);
source = source.replace(
  /undefined8 __fastcall FUN_0043a6e0\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0043a800 \*\//,
  "undefined8 __fastcall FUN_0043a6e0(undefined4 param_1,undefined4 param_2)\n\n{\n  int scene_id;\n  int scene_record;\n  int scene_offset;\n  int first_entry;\n  undefined4 uVar1;\n\n  scene_id = (int)(short)param_2;\n  if (scene_id == 0 && param_1 != 0) {\n    scene_id = (int)(short)param_1;\n  }\n  scene_offset = *(int *)(scene_id * 4 + 0x650fa0);\n  DAT_0047a788 = 1;\n  DAT_0047a428 = 1;\n  FUN_00413e88();\n  FUN_0043a1fc();\n  FUN_0045233c((undefined4)scene_id,(undefined4)scene_id);\n  scene_record = *(int *)(scene_id * 4 + 0x62e450);\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    fprintf(stderr,\"scene fallback 3a6e0: scene_id=%d offset=%d record=0x%lx before_current=0x%lx\\n\",\n            scene_id,scene_offset,(unsigned long)scene_record,(unsigned long)DAT_0047a470);\n  }\n  uVar1 = (undefined4)scene_id;\n  if (scene_record != 0) {\n    _DAT_0073cc3c = E2R_TraceScenePointerWrite(\"scene.clear\",0);\n    FUN_00452140((undefined4)(uintptr_t)scene_record);\n    first_entry = *(int *)(scene_record + 4);\n    if (first_entry != 0 && !IsBadReadPtr((void *)(uintptr_t)first_entry,2)) {\n      DAT_0047a470 = *(undefined4 *)((undefined1 *)0x00630b60 + *(short *)first_entry * 4);\n    }\n    uVar1 = FUN_004523f8((undefined4)(uintptr_t)scene_record);\n  }\n  if (E2R_RuntimeDiagEnabled() && E2R_actor_loop_diag_count < 128) {\n    E2R_actor_loop_diag_count = E2R_actor_loop_diag_count + 1;\n    fprintf(stderr,\"scene fallback 3a6e0 exit: current=0x%lx actors=0x%lx scene=0x%lx\\n\",\n            (unsigned long)DAT_0047a470,(unsigned long)_DAT_0063726c,\n            (unsigned long)_DAT_0073cc3c);\n  }\n  return CONCAT44(param_2,uVar1);\n}\n\n\n\n/* 0043a800 */"
);
source = source.replace(
  "  int first_entry;\n  undefined4 uVar1;\n\n  scene_id = (int)(short)param_2;",
  "  int first_entry;\n  int child;\n  int actor;\n  uint guard;\n  undefined4 uVar1;\n\n  scene_id = (int)(short)param_2;"
);
source = source.replace(
  "    first_entry = *(int *)(scene_record + 4);\n    if (first_entry != 0 && !IsBadReadPtr((void *)(uintptr_t)first_entry,2)) {\n      DAT_0047a470 = *(undefined4 *)((undefined1 *)0x00630b60 + *(short *)first_entry * 4);\n    }\n    uVar1 = FUN_004523f8((undefined4)(uintptr_t)scene_record);",
  "    first_entry = *(int *)(scene_record + 4);\n    child = first_entry;\n    guard = 0;\n    while (child != 0 && guard < 0x4000 &&\n           !IsBadReadPtr((void *)(uintptr_t)child,0x1c)) {\n      if (((*(byte *)(child + 0xe) & 0x20) == 0) && -1 < *(short *)child) {\n        actor = *(int *)((undefined1 *)0x00630b60 + *(short *)child * 4);\n        if (actor != 0) {\n          DAT_0047a470 = actor;\n          break;\n        }\n      }\n      child = *(int *)(child + 0x18);\n      guard = guard + 1;\n    }\n    if (_DAT_0073cc3c == 0 && 0 <= scene_id && scene_id < 0x4b0) {\n      _DAT_0073ccba = (ushort)scene_id;\n      E2R_SyncSceneViewId();\n      FUN_0044c6bc();\n    }\n    uVar1 = FUN_004523f8((undefined4)(uintptr_t)scene_record);"
);
source = source.replace(
  "undefined4 FUN_004523f8(void)",
  "undefined4 FUN_004523f8(undefined4 param_1)"
);
source = source.replace(
  /(\s+short extraout_DX_00;\r?\n\s+short sVar5;\r?\n\s*)if \(in_EAX != \(short \*\)0x0\) \{/,
  "$1in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX != (short *)0x0 && !IsBadReadPtr(in_EAX,0x20)) {"
);
source = source.replace(
  "undefined4 FUN_004523f8(void);",
  "undefined4 FUN_004523f8(undefined4 param_1);"
);
source = source.replaceAll(
  "FUN_004523f8();",
  "FUN_004523f8((undefined4)(uintptr_t)_DAT_0073cc3c);"
);
source = source.replace(
  "void FUN_0044be20(void)",
  "void FUN_0044be20(undefined4 param_1)"
);
source = source.replace(
  /(void __fastcall FUN_004211c8\(int param_1,undefined4 param_2\)\s*\n\s*\{\s*\n  int iVar1;\n)/,
  "$1  int iVar4;\n"
);
source = source.replace(
  "    else if (*(int *)(DAT_0047a470 + 0x132) != 0) {\n      FUN_0044be20();\n    }",
  "    else if (*(int *)(DAT_0047a470 + 0x132) != 0) {\n      iVar4 = *(int *)(DAT_0047a470 + 0x132);\n      if (0x10000u <= (uint)iVar4 && (uint)iVar4 < 0x70000000u &&\n         !IsBadReadPtr((void *)(uintptr_t)iVar4,4)) {\n        FUN_0044be20((undefined4)(uintptr_t)(short)(*(int *)iVar4 >> 0x10));\n      }\n    }"
);
source = source.replace(
  /(void FUN_0044be20\(undefined4 param_1\)[\s\S]*?\r?\n  undefined4 \*puVar7;\r?\n  longlong lVar8;\r?\n\s*)if \(\(undefined1 \*\)0x0067c728 \+ in_AX \* 0x1c == _DAT_0073cc3c\) \{/,
  "$1in_AX = (short)param_1;\n  if ((undefined1 *)0x0067c728 + in_AX * 0x1c == _DAT_0073cc3c) {"
);
source = source.replace(
  "        FUN_0044be20();\n      }\n    }\n    for (psVar2 = *(short **)(in_EAX + 2); psVar2 != (short *)0x0;",
  "        FUN_0044be20((undefined4)(uintptr_t)(short)(*(int *)in_EAX >> 0x10));\n      }\n    }\n    for (psVar2 = *(short **)(in_EAX + 2); psVar2 != (short *)0x0;"
);
source = source.replace(
  "  char local_40 [6];\n  char acStack_3a [18];",
  "  char local_40 [64];\n  char acStack_3a [18];"
);
source = source.replace(
  "    FUN_0045fd2c(param_1,pcVar6);\n    cStack_1c = (char)((uint)_DAT_0073ccb8 >> 0x10);\n    uStack_1b = (undefined1)((uint)_DAT_0073ccb8 >> 0x18);\n    iVar10 = 9;\n    do {\n      iVar4 = (CONCAT13(uStack_1b,CONCAT12(cStack_1c,uStack_1e)) >> 0x10) / 10;\n      cVar3 = (char)iVar4;\n      iVar9 = iVar10 + -1;\n      uStack_1b = (undefined1)((uint)iVar4 >> 8);\n      local_40[iVar10] = cStack_1c + cVar3 * -10 + '0';\n      iVar10 = iVar9;\n      cStack_1c = cVar3;\n    } while (iVar9 != 5);\n    FUN_0045fd2c(10,_DAT_006365e0);\n    FUN_0045fd4b(extraout_ECX,local_40);\n    uVar12 = FUN_0045e594(extraout_ECX_00,extraout_EDX,&stack_ffffff94,0x200,in_stack_ffffff94);",
  "    FUN_0045fd2c((undefined4)(uintptr_t)local_40,pcVar6);\n    iVar10 = (int)(short)_DAT_0073ccba;\n    for (iVar9 = 9; 5 < iVar9; iVar9 = iVar9 + -1) {\n      local_40[iVar9] = (char)(iVar10 % 10) + '0';\n      iVar10 = iVar10 / 10;\n    }\n    FUN_0045fd2c((undefined4)(uintptr_t)stack_ffffff94,_DAT_006365e0);\n    FUN_0045fd4b((undefined4)(uintptr_t)stack_ffffff94,local_40);\n    uVar12 = FUN_0045e594(extraout_ECX_00,extraout_EDX,(LPCSTR)stack_ffffff94,0x200,\n                           in_stack_ffffff94);"
);
source = source.replace(
  "    FUN_0045fd2c((undefined4)(uintptr_t)local_40,pcVar6);",
  "    snprintf(local_40,64,\"%s\",pcVar6);"
);
source = source.replace(
  "    FUN_0045fd2c((undefined4)(uintptr_t)stack_ffffff94,_DAT_006365e0);\n    FUN_0045fd4b((undefined4)(uintptr_t)stack_ffffff94,local_40);",
  "    snprintf((char *)stack_ffffff94,0x200,\"%s\",_DAT_006365e0);\n    strncat((char *)stack_ffffff94,local_40,0x1ff - strlen((char *)stack_ffffff94));"
);
source = source.replace(
  "    else {\n      FUN_0045e76f(extraout_ECX_01,(undefined1 *)0x0061c730);\n      FUN_0045e76f(extraout_ECX_02,(char *)(undefined4 *)0x0047a4e0);\n      FUN_0045e76f(extraout_ECX_03,(undefined1 *)0x0061c730);\n      uVar12 = FUN_0045e8e6(extraout_ECX_04,extraout_EDX_00);\n      iVar4 = (int)uVar12;",
  "    else {\n      iVar10 = (int)uVar12;\n      E2R_ReadOpenFileBytes(iVar10,(char *)0x0061c730,2);\n      E2R_ReadOpenFileBytes(iVar10,(char *)0x0047a4e0,0x18);\n      E2R_ReadOpenFileBytes(iVar10,(char *)0x0061c730,0x300);\n      uVar12 = FUN_0045e8e6(iVar10,extraout_EDX_00);\n      iVar4 = (int)uVar12;"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0044add8\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)return CONCAT44\(param_2,iVar4\);/,
  "$1FUN_0041af88(0x0061c730,param_2);\n  return CONCAT44(param_2,iVar4);"
);
source = source.replace(
  /(char \* __fastcall FUN_0045fd2c\(undefined4 param_1,char \*param_2\)[\s\S]*?\r?\n  char \*pcVar2;\r?\n\s*)pcVar2 = in_EAX;/,
  "$1in_EAX = (char *)(uintptr_t)param_1;\n  pcVar2 = in_EAX;"
);
source = source.replace(
  /(char \* __fastcall FUN_0045fd4b\(undefined4 param_1,char \*param_2\)[\s\S]*?\r?\n  char \*pcVar3;\r?\n  char \*pcVar4;\r?\n\s*)iVar2 = -1;/,
  "$1in_EAX = (char *)(uintptr_t)param_1;\n  iVar2 = -1;"
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
  "$1in_EAX = (undefined4)(uintptr_t)param_1;\n  uVar5 = FUN_004536e0(0,param_2);\n  puVar4 = (undefined2 *)uVar5;\n  if (puVar4 == (undefined2 *)0x0 || in_EAX == 0 ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0xdc)) {\n    return (undefined2 *)0x0;\n  }\n  iVar1 = *(int *)((int)(uintptr_t)in_EAX + 0xd8);\n  if (iVar1 != 0 &&\n      ((uint)iVar1 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)iVar1,0x22))) {\n    iVar1 = 0;\n    *(undefined4 *)((int)(uintptr_t)in_EAX + 0xd8) = 0;\n  }"
);
source = source.replace(
  "    *(undefined2 **)(extraout_ECX + 0xd8) = puVar4;",
  "    *(undefined2 **)((int)(uintptr_t)in_EAX + 0xd8) = puVar4;"
);
source = source.replace(
  "  *(int *)(puVar4 + 0x11) = extraout_ECX;\n  return puVar4;",
  "  *(undefined4 *)(puVar4 + 0x11) = in_EAX;\n  return puVar4;"
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
  "  iVar1 = *(int *)(in_EAX + 0x1e);\n  *(undefined2 *)(in_EAX + 0x124) = *(undefined2 *)(in_EAX + 0x122);\n  for (; iVar1 != 0; iVar1 = *(int *)(iVar1 + 0x4c)) {\n    iVar3 = iVar1;",
  "  iVar1 = *(int *)(in_EAX + 0x1e);\n  *(undefined2 *)(in_EAX + 0x124) = *(undefined2 *)(in_EAX + 0x122);\n  for (; iVar1 != 0; iVar1 = *(int *)(iVar1 + 0x4c)) {\n    if ((uint)iVar1 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)iVar1,0xca)) break;\n    iVar3 = iVar1;"
);
source = source.replace(
  "    iVar3 = *(int *)(iVar1 + 0x11e);\n    *(undefined2 *)(iVar1 + 0xc4) = *(undefined2 *)(iVar1 + 0xce);\n    for (; iVar3 != 0; iVar3 = *(int *)(iVar3 + 0x26)) {\n      iVar2 = iVar3;",
  "    iVar3 = *(int *)(iVar1 + 0x11e);\n    *(undefined2 *)(iVar1 + 0xc4) = *(undefined2 *)(iVar1 + 0xce);\n    for (; iVar3 != 0; iVar3 = *(int *)(iVar3 + 0x26)) {\n      if ((uint)iVar3 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)iVar3,0x20)) break;\n      iVar2 = iVar3;"
);
source = source.replace(
  "  for (iVar1 = *(int *)(in_EAX + 0xd8); iVar1 != 0; iVar1 = *(int *)(iVar1 + 0x1e)) {\n    *(undefined2 *)(iVar1 + 0x14) = *(undefined2 *)(iVar1 + 0x10);",
  "  for (iVar1 = *(int *)(in_EAX + 0xd8); iVar1 != 0; iVar1 = *(int *)(iVar1 + 0x1e)) {\n    if ((uint)iVar1 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)iVar1,0x1a)) break;\n    *(undefined2 *)(iVar1 + 0x14) = *(undefined2 *)(iVar1 + 0x10);"
);
source = source.replace(
  /(void FUN_00426c3c\(void\)[\s\S]*?\r?\n  int in_EAX;\r?\n\s*)for/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x136)) {\n    return;\n  }\n  for"
);
source = source.replace(
  /(undefined4 FUN_0042d048\(void\)[\s\S]*?\r?\n  int in_EAX;\r?\n  int iVar2;\r?\n\s*)iVar1 = \*\(int \*\)\(in_EAX \+ 0xa2\);/,
  "$1in_EAX = E2R_actor_calc_context;\n  if (in_EAX == 0 || E2R_IsBadWritePtr((void *)(uintptr_t)in_EAX,0xa6)) {\n    return 0;\n  }\n  iVar1 = *(int *)(in_EAX + 0xa2);"
);
source = source.replace(
  /(void FUN_00426ca4\(void\)[\s\S]*?\r?\n  short \*extraout_ECX_01;\r?\n\s*)bVar4 =/,
  "$1in_EAX = (short *)(uintptr_t)E2R_actor_calc_context;\n  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,0x136)) {\n    return;\n  }\n  bVar4 ="
);
source = source.replace(
  "      FUN_00422aa0(in_EAX,in_EAX + 0x42);\n      FUN_00422aa0(extraout_ECX,(undefined2 *)(extraout_ECX + 0x90));\n      *(short *)(*extraout_ECX_00 * 2 + 0x671fc0) = extraout_ECX_00[0x91];\n      *(short *)(*extraout_ECX_00 * 2 + 0x647a68) = extraout_ECX_00[0x76];\n      *(char *)(*extraout_ECX_00 + 0x64c950) = (char)extraout_ECX_00[0xc2];\n      in_EAX = extraout_ECX_00;\n      if ((*(int *)(extraout_ECX_00 + 0x53) != 0) && (DAT_0047a34a == 0)) {\n        for (iVar2 = *(int *)(extraout_ECX_00 + 0x57); iVar2 != 0; iVar2 = *(int *)(iVar2 + 2)) {",
  "      FUN_00422aa0((undefined4)(uintptr_t)(*in_EAX * 6 + 0x669708),in_EAX + 0x42);\n      FUN_00422aa0((undefined4)(uintptr_t)(*in_EAX * 6 + 0x658980),in_EAX + 0x48);\n      *(short *)(*in_EAX * 2 + 0x671fc0) = in_EAX[0x91];\n      *(short *)(*in_EAX * 2 + 0x647a68) = in_EAX[0x76];\n      *(char *)(*in_EAX + 0x64c950) = (char)in_EAX[0xc2];\n      if ((*(int *)(in_EAX + 0x53) != 0) && (DAT_0047a34a == 0)) {\n        for (iVar2 = *(int *)(in_EAX + 0x57); iVar2 != 0; iVar2 = *(int *)(iVar2 + 2)) {"
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
  /void FUN_00426a80\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00426ac4 \*\//,
  "void FUN_00426a80(void)\n\n{\n  int iVar1;\n  int iVar2;\n  int *in_EAX;\n\n  if (E2R_actor_calc_context != 0) {\n    in_EAX = (int *)(uintptr_t)(E2R_actor_calc_context + 0xa6);\n  }\n  if (in_EAX == (int *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      IsBadReadPtr(in_EAX,0x12)) {\n    return;\n  }\n  iVar1 = *in_EAX;\n  if (iVar1 != 0) {\n    if ((uintptr_t)iVar1 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)iVar1,0xe)) {\n      return;\n    }\n    *(undefined2 *)((int)in_EAX + 6) = 0;\n    *(undefined2 *)(in_EAX + 1) = *(undefined2 *)(iVar1 + 2);\n    *(undefined2 *)(in_EAX + 3) = *(undefined2 *)(iVar1 + 0xc);\n    iVar2 = *(int *)(iVar1 + 4);\n    *(undefined2 *)((int)in_EAX + 0xe) = 0;\n    in_EAX[2] = iVar2;\n    if ((*(byte *)(iVar1 + 0xc) & 1) != 0) {\n      *(undefined2 *)(in_EAX + 4) = 0;\n      return;\n    }\n    *(undefined2 *)(in_EAX + 4) = 1;\n  }\n  return;\n}\n\n\n\n/* 00426ac4 */"
);
source = source.replace(
  /void __fastcall FUN_0042ad60\(undefined4 param_1,int param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0042ae80 \*\//,
  "void __fastcall FUN_0042ad60(undefined4 param_1,int param_2)\n\n{\n  int *in_EAX;\n  int extraout_ECX;\n  int extraout_ECX_00;\n  int *extraout_ECX_01;\n  int *extraout_ECX_02;\n  int *extraout_ECX_03;\n  int unaff_EBX;\n  uint uVar1;\n\n  unaff_EBX = _DAT_00637378;\n  if (param_2 != 0 && 0x10000u <= (uintptr_t)param_2 &&\n      !IsBadReadPtr((void *)(uintptr_t)param_2,0xb8)) {\n    in_EAX = (int *)(uintptr_t)(param_2 + 0xa6);\n  }\n  else if (E2R_actor_calc_context != 0) {\n    in_EAX = (int *)(uintptr_t)(E2R_actor_calc_context + 0xa6);\n  }\n  if (in_EAX == (int *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      IsBadReadPtr(in_EAX,0x12)) {\n    return;\n  }\n  if (*in_EAX != 0) {\n    if ((uintptr_t)*in_EAX < 0x10000u ||\n        IsBadReadPtr((void *)(uintptr_t)*in_EAX,0x12)) {\n      return;\n    }\n    if ((*(byte *)(*in_EAX + 0xc) & 2) == 0) {\n      uVar1 = (uint)*(ushort *)((int)in_EAX + 6) +\n              (unaff_EBX << 0x10) / (int)(uint)*(ushort *)(in_EAX + 1);\n      do {\n        if (uVar1 < 0x10000) {\nLAB_0042ae53:\n          if ((*(byte *)((int)in_EAX + 0xd) & 4) == 0) {\n            FUN_0042b338(in_EAX,(ushort)uVar1);\n          }\n          *(byte *)(param_2 + 3) = *(byte *)(param_2 + 3) & 0xfb;\n          return;\n        }\n        if (*(ushort *)(in_EAX + 4) < 2) {\n          if (*(ushort *)(in_EAX + 4) != 0) {\n            FUN_0042b004();\n            *(undefined2 *)((int)extraout_ECX_02 + 6) = 0xffff;\n            *(byte *)((int)extraout_ECX_02 + 0xd) = *(byte *)((int)extraout_ECX_02 + 0xd) | 4;\n            in_EAX = extraout_ECX_02;\n            goto LAB_0042ae53;\n          }\n          FUN_0042b004();\n          in_EAX = extraout_ECX_03;\n        }\n        else {\n          FUN_0042b004();\n          *(short *)(extraout_ECX_01 + 4) = (short)extraout_ECX_01[4] + -1;\n          in_EAX = extraout_ECX_01;\n        }\n        uVar1 = uVar1 - 0x10000;\n      } while( true );\n    }\n    uVar1 = unaff_EBX + (uint)*(ushort *)((int)in_EAX + 6);\n    if (*(ushort *)(in_EAX + 1) < uVar1) {\n      FUN_0042b004();\n      *(undefined2 *)(extraout_ECX + 6) = *(undefined2 *)(extraout_ECX + 4);\n      *(byte *)(extraout_ECX + 0xd) = *(byte *)(extraout_ECX + 0xd) | 4;\n    }\n    else {\n      FUN_0042b338(in_EAX,(ushort)uVar1);\n      if ((in_EAX[2] != 0) && 0x10000u <= (uintptr_t)in_EAX[2] &&\n          !IsBadReadPtr((void *)(uintptr_t)in_EAX[2],0xa) &&\n          (*(int *)(in_EAX[2] + 6) == 0)) goto joined_r0x0042ae76;\n    }\n    *(byte *)(param_2 + 3) = *(byte *)(param_2 + 3) & 0xfb;\n    return;\n  }\njoined_r0x0042ae76:\n  if (DAT_0047a3b4 == 0) {\n    *(byte *)(param_2 + 3) = *(byte *)(param_2 + 3) | 4;\n  }\n  return;\n}\n\n\n\n/* 0042ae80 */"
);
source = source.replace(
  "            FUN_0042b004();\n            *(undefined2 *)((int)extraout_ECX_02 + 6) = 0xffff;\n            *(byte *)((int)extraout_ECX_02 + 0xd) = *(byte *)((int)extraout_ECX_02 + 0xd) | 4;\n            in_EAX = extraout_ECX_02;",
  "            E2R_actor_calc_context = param_2;\n            FUN_0042b004();\n            E2R_actor_calc_context = 0;\n            *(undefined2 *)((int)in_EAX + 6) = 0xffff;\n            *(byte *)((int)in_EAX + 0xd) = *(byte *)((int)in_EAX + 0xd) | 4;"
);
source = source.replace(
  "          FUN_0042b004();\n          in_EAX = extraout_ECX_03;",
  "          E2R_actor_calc_context = param_2;\n          FUN_0042b004();\n          E2R_actor_calc_context = 0;"
);
source = source.replace(
  "          FUN_0042b004();\n          *(short *)(extraout_ECX_01 + 4) = (short)extraout_ECX_01[4] + -1;\n          in_EAX = extraout_ECX_01;",
  "          E2R_actor_calc_context = param_2;\n          FUN_0042b004();\n          E2R_actor_calc_context = 0;\n          *(short *)(in_EAX + 4) = (short)in_EAX[4] + -1;"
);
source = source.replace(
  "    if (*(ushort *)(in_EAX + 1) < uVar1) {\n      FUN_0042b004();\n      *(undefined2 *)(extraout_ECX + 6) = *(undefined2 *)(extraout_ECX + 4);\n      *(byte *)(extraout_ECX + 0xd) = *(byte *)(extraout_ECX + 0xd) | 4;",
  "    if (*(ushort *)(in_EAX + 1) <= uVar1) {\n      E2R_GameStateLog(\"42ad60.complete begin actor=0x%lx slot=0x%lx action=0x%lx progress=%u duration=%u scene=0x%lx\",\n                       (unsigned long)(uintptr_t)param_2,\n                       (unsigned long)(uintptr_t)in_EAX,\n                       (unsigned long)(uintptr_t)*in_EAX,\n                       (unsigned int)*(ushort *)((int)in_EAX + 6),\n                       (unsigned int)*(ushort *)(in_EAX + 1),\n                       (unsigned long)_DAT_0073cc3c);\n      E2R_actor_calc_context = param_2;\n      FUN_0042b004();\n      E2R_actor_calc_context = 0;\n      E2R_GameStateLog(\"42ad60.complete end actor=0x%lx slot=0x%lx action=0x%lx progress=%u duration=%u flags=0x%x scene=0x%lx\",\n                       (unsigned long)(uintptr_t)param_2,\n                       (unsigned long)(uintptr_t)in_EAX,\n                       (unsigned long)(uintptr_t)*in_EAX,\n                       (unsigned int)*(ushort *)((int)in_EAX + 6),\n                       (unsigned int)*(ushort *)(in_EAX + 1),\n                       (unsigned int)*(byte *)((int)in_EAX + 0xd),\n                       (unsigned long)_DAT_0073cc3c);\n      *(undefined2 *)((int)in_EAX + 6) = *(undefined2 *)(in_EAX + 1);\n      *(byte *)((int)in_EAX + 0xd) = *(byte *)((int)in_EAX + 0xd) | 4;"
);
source = source.replace(
  "    uVar1 = unaff_EBX + (uint)*(ushort *)((int)in_EAX + 6);\n    if (*(ushort *)(in_EAX + 1) <= uVar1) {",
  "    uVar1 = unaff_EBX + (uint)*(ushort *)((int)in_EAX + 6);\n    E2R_TraceActionAdvance(\"42ad60.linear\",param_2,in_EAX,(uint)unaff_EBX,uVar1);\n    if (*(ushort *)(in_EAX + 1) <= uVar1) {"
);
source = source.replace(
  "            FUN_0042b338(in_EAX,(ushort)uVar1);",
  "            E2R_actor_calc_context = param_2;\n            FUN_0042b338(in_EAX,(ushort)uVar1);\n            E2R_actor_calc_context = 0;"
);
source = source.replace(
  "      FUN_0042b338(in_EAX,(ushort)uVar1);\n      if ((in_EAX[2] != 0)",
  "      E2R_actor_calc_context = param_2;\n      FUN_0042b338(in_EAX,(ushort)uVar1);\n      E2R_actor_calc_context = 0;\n      if ((in_EAX[2] != 0)"
);
source = source.replace(
  /void FUN_0042b004\(void\)\s*\r?\n\s*\{\r?\n  int iVar1;\r?\n  int iVar2;\r?\n  int \*in_EAX;\r?\n  short \*in_EDX;/,
  "void FUN_0042b004(void)\n\n{\n  int iVar1;\n  int iVar2;\n  int *in_EAX;\n  short *in_EDX;\n  int e2r_event_guard;"
);
source = source.replace(
  /(void FUN_0042b004\(void\)[\s\S]*?\r?\n  int \*in_EAX;\r?\n  short \*in_EDX;\r?\n(?:  int e2r_event_guard;\r?\n)?\s*)for \(iVar1 = in_EAX\[2\];/,
  "$1if (E2R_actor_calc_context != 0) {\n    in_EAX = (int *)(uintptr_t)(E2R_actor_calc_context + 0xa6);\n  }\n  if (in_EAX == (int *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      IsBadReadPtr(in_EAX,0x12) || *in_EAX == 0 ||\n      IsBadReadPtr((void *)(uintptr_t)*in_EAX,0x10)) {\n    return;\n  }\n  for (iVar1 = in_EAX[2];"
);
source = source.replace(
  "  for (iVar1 = in_EAX[2]; iVar1 != 0; iVar1 = *(int *)(iVar1 + 2)) {\n    for (iVar2 = *(int *)(iVar1 + 6); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {",
  "  for (e2r_event_guard = 0, iVar1 = in_EAX[2];\n       iVar1 != 0 && e2r_event_guard < 256;\n       e2r_event_guard = e2r_event_guard + 1, iVar1 = *(int *)(iVar1 + 2)) {\n    E2R_GameStateLog(\"42b004.key node=0x%lx w0=0x%x next=0x%lx events=0x%lx guard=%d\",\n                     (unsigned long)(uintptr_t)iVar1,\n                     (unsigned int)*(ushort *)(uintptr_t)iVar1,\n                     (unsigned long)(uintptr_t)*(int *)(iVar1 + 2),\n                     (unsigned long)(uintptr_t)*(int *)(iVar1 + 6),\n                     e2r_event_guard);\n    for (iVar2 = *(int *)(iVar1 + 6); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {"
);
source = source.replace(
  "      FUN_0042b880(*in_EAX,in_EDX);",
  "      E2R_action_event_context = iVar2;\n      E2R_GameStateLog(\"42b004.event begin action=0x%lx event=0x%lx w0=0x%x w1=0x%x actor=0x%lx scene=0x%lx\",\n                       (unsigned long)(uintptr_t)*in_EAX,\n                       (unsigned long)(uintptr_t)iVar2,\n                       (unsigned int)*(ushort *)(uintptr_t)iVar2,\n                       (unsigned int)*(ushort *)(uintptr_t)(iVar2 + 2),\n                       (unsigned long)(uintptr_t)E2R_actor_calc_context,\n                       (unsigned long)_DAT_0073cc3c);\n      FUN_0042b880(*in_EAX,\n                   E2R_actor_calc_context != 0 ?\n                   (short *)(uintptr_t)E2R_actor_calc_context : in_EDX);\n      E2R_GameStateLog(\"42b004.event end action=0x%lx event=0x%lx actor=0x%lx scene=0x%lx\",\n                       (unsigned long)(uintptr_t)*in_EAX,\n                       (unsigned long)(uintptr_t)iVar2,\n                       (unsigned long)(uintptr_t)E2R_actor_calc_context,\n                       (unsigned long)_DAT_0073cc3c);\n      E2R_action_event_context = 0;"
);
source = source.replace(
  "      E2R_action_event_context = 0;\n    }\n  }\n  in_EAX[2] = *(int *)(*in_EAX + 4);",
  "      E2R_action_event_context = 0;\n    }\n    if (*(int *)(iVar1 + 2) == iVar1) {\n      break;\n    }\n  }\n  in_EAX[2] = *(int *)(*in_EAX + 4);"
);
source = source.replace(
  "  if ((*(byte *)(in_EAX + 0x146) & 1) == 0) {",
  "  if (E2R_actor_calc_context != 0) {\n    in_EAX = E2R_actor_calc_context;\n  }\n  if (in_EAX == 0 || (uintptr_t)in_EAX < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x148)) {\n    return 0;\n  }\n  if ((*(byte *)(in_EAX + 0x146) & 1) == 0) {"
);
source = source.replace(
  /void __fastcall FUN_0042b338\(undefined4 param_1,ushort param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0042b490 \*\//,
  "void __fastcall FUN_0042b338(undefined4 param_1,ushort param_2)\n\n{\n  ushort *puVar1;\n  int iVar2;\n  int *in_EAX;\n  uint uVar3;\n  uint uVar4;\n  uint extraout_ECX;\n  short *unaff_EBX;\n\n  in_EAX = (int *)(uintptr_t)param_1;\n  if (in_EAX == (int *)0x0 || (uintptr_t)in_EAX < 0x10000u ||\n      IsBadReadPtr(in_EAX,0x12)) {\n    return;\n  }\n  if (*in_EAX != 0 && ((uintptr_t)*in_EAX < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)*in_EAX,0xe))) {\n    return;\n  }\n  if (param_2 < *(ushort *)((int)in_EAX + 6)) {\n    FUN_0042b004();\n  }\n  for (puVar1 = (ushort *)in_EAX[2]; (puVar1 != (ushort *)0x0 && (*puVar1 <= param_2));\n      puVar1 = *(ushort **)(puVar1 + 1)) {\n    for (iVar2 = *(int *)(puVar1 + 3); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {\n      E2R_action_event_context = iVar2;\n      FUN_0042b880(*in_EAX,\n                   E2R_actor_calc_context != 0 ?\n                   (short *)(uintptr_t)E2R_actor_calc_context : unaff_EBX);\n      E2R_action_event_context = 0;\n    }\n    if ((puVar1 == (ushort *)in_EAX[2]) && ((*(byte *)(*in_EAX + 0xc) & 2) == 0)) {\n      FUN_0042b5fc();\n    }\n    *(ushort *)((int)in_EAX + 6) = *puVar1;\n  }\n  if (puVar1 != (ushort *)0x0) {\n    uVar4 = (uint)*puVar1 - (uint)*(ushort *)((int)in_EAX + 6);\n    uVar3 = (((uint)param_2 - (uint)*(ushort *)((int)in_EAX + 6)) * 0x4000) / uVar4;\n    if (uVar3 != 0) {\n      for (iVar2 = *(int *)(puVar1 + 3); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {\n        FUN_0042c790(*in_EAX,uVar3);\n        uVar4 = extraout_ECX;\n      }\n      if ((*(byte *)(*in_EAX + 0xc) & 2) == 0) {\n        FUN_0042b490(uVar4,uVar3);\n      }\n    }\n  }\n  in_EAX[2] = (int)puVar1;\n  *(ushort *)((int)in_EAX + 6) = param_2;\n  return;\n}\n\n\n\n/* 0042b490 */"
);
source = source.replace(
  "  short *unaff_EBX;\n\n  in_EAX = (int *)(uintptr_t)param_1;",
  "  short *unaff_EBX;\n  uint e2r_key_guard;\n  ushort *next_key;\n\n  in_EAX = (int *)(uintptr_t)param_1;"
);
source = source.replace(
  "  for (puVar1 = (ushort *)in_EAX[2]; (puVar1 != (ushort *)0x0 && (*puVar1 <= param_2));\n      puVar1 = *(ushort **)(puVar1 + 1)) {\n    for (iVar2 = *(int *)(puVar1 + 3); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {",
  "  for (e2r_key_guard = 0, puVar1 = (ushort *)in_EAX[2];\n      puVar1 != (ushort *)0x0 && e2r_key_guard < 256 &&\n      !IsBadReadPtr(puVar1,0xa) && *puVar1 <= param_2;\n      e2r_key_guard = e2r_key_guard + 1, puVar1 = next_key) {\n    next_key = *(ushort **)(puVar1 + 1);\n    for (iVar2 = *(int *)(puVar1 + 3); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {"
);
source = source.replace(
  "    *(ushort *)((int)in_EAX + 6) = *puVar1;\n  }\n  if (puVar1 != (ushort *)0x0) {",
  "    *(ushort *)((int)in_EAX + 6) = *puVar1;\n    if (next_key == puVar1) {\n      puVar1 = (ushort *)0x0;\n      break;\n    }\n  }\n  if (puVar1 != (ushort *)0x0) {"
);
source = source.replace(
  "      for (iVar2 = *(int *)(puVar1 + 3); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {\n        FUN_0042c790(*in_EAX,uVar3);\n        uVar4 = extraout_ECX;",
  "      for (iVar2 = *(int *)(puVar1 + 3); iVar2 != 0; iVar2 = *(int *)(iVar2 + 10)) {\n        E2R_action_event_context = iVar2;\n        FUN_0042c790(*in_EAX,uVar3);\n        E2R_action_event_context = 0;\n        uVar4 = extraout_ECX;"
);
source = source.replace(
  "  if ((DAT_0047a7e0 != 0) && ((*(byte *)((uint)(ushort)in_EAX[1] * 2 + 0x63679f) & 1) == 0)) {\n    return;\n  }",
  "  if (E2R_action_event_context != 0) {\n    in_EAX = (short *)(uintptr_t)E2R_action_event_context;\n  }\n  else {\n    in_EAX = E2R_fan_parse_record;\n  }\n  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,10)) {\n    return;\n  }\n  if (E2R_actor_calc_context != 0 && 0x10000u <= (uintptr_t)E2R_actor_calc_context &&\n      !IsBadReadPtr((void *)(uintptr_t)E2R_actor_calc_context,0x148)) {\n    unaff_EBX = E2R_actor_calc_context;\n  }\n  else if ((uintptr_t)param_1 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)param_1,0x148)) {\n    return;\n  }\n  else {\n    unaff_EBX = param_1;\n  }\n  if ((DAT_0047a7e0 != 0) && ((*(byte *)((uint)(ushort)in_EAX[1] * 2 + 0x63679f) & 1) == 0)) {\n    return;\n  }"
);
source = source.replaceAll("(&DAT_0063679e)[iVar6]", "*(byte *)(iVar6 + 0x63679e)");
source = source.replaceAll("E2R_READ1(DAT_004c3ad5,3)", "(DAT_004c3ad5 >> 0x18)");
source = source.replace(
  "  local_28 = 0xffffffff;\n  local_20 = 0xffffffff;\n  iVar6 =",
  "  local_28 = 0xffffffff;\n  local_20 = 0xffffffff;\n  in_EAX = (ushort *)(uintptr_t)param_1;\n  if ((uintptr_t)in_EAX < 0x10000u || IsBadReadPtr(in_EAX,0x6)) {\n    return CONCAT44(param_2,0xffffffff);\n  }\n  iVar6 ="
);
source = source.replace(
  "  if (in_AX < 0) {\n    pcVar2 = &DAT_0047a710;",
  "  in_AX = (short)param_2;\n  if (in_AX < 0) {\n    pcVar2 = &DAT_0047a710;"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0044248c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  short sVar5;\r?\n  char \*pcVar6;\r?\n\s*)if \(in_AX < 0\) \{/,
  "$1in_AX = (short)param_2;\n  if (in_AX < 0) {"
);
source = source.replace(
  "  uStack_4 = param_2;\n  uVar4 = FUN_0045190c(param_1,(int)in_AX);",
  "  uStack_4 = param_2;\n  in_AX = (short)param_2;\n  uVar4 = FUN_0045190c(param_1,(int)in_AX);"
);
source = source.replace(
  "  uVar2 = 0;\n  if ((-1 < in_AX) && (iVar1 = in_AX * 4, *(int *)((undefined1 *)0x0062ba20 + iVar1) == 0)) {",
  "  uVar2 = 0;\n  in_AX = (short)param_2;\n  if ((-1 < in_AX) && (iVar1 = in_AX * 4, *(int *)((undefined1 *)0x0062ba20 + iVar1) == 0)) {"
);
source = source.replace(
  /(undefined8 __fastcall FUN_00441b24\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined1 local_48 \[52\];\r?\n\r?\n)\s*if \(in_AX < 0\) \{/,
  "$1  in_AX = (short)param_2;\n  if (in_AX < 0) {"
);
source = source.replace(
  "  undefined1 local_7c [52];\n  undefined1 local_48 [52];\n\n  if (in_AX < 0) {",
  "  undefined1 local_7c [52];\n  undefined1 local_48 [52];\n\n  in_AX = (short)param_2;\n  if (in_AX < 0) {"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045190c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar3;\r?\n\r?\n)\s*uVar2 = 0;\r?\n\s*if \(\(-1 < in_AX\)/,
  "$1  uVar2 = 0;\n  in_AX = (short)param_2;\n  if ((-1 < in_AX)"
);
source = source.replace(
  "  undefined8 uVar3;\n\n  uVar2 = 0;\n  if ((-1 < in_AX) &&",
  "  undefined8 uVar3;\n\n  uVar2 = 0;\n  in_AX = (short)param_2;\n  if ((-1 < in_AX) &&"
);
source = source.replace(
  "  iVar2 = in_EAX;\n  uVar3 = DAT_0047a470;",
  "  in_EAX = (int)(uintptr_t)param_2;\n  iVar2 = in_EAX;\n  uVar3 = DAT_0047a470;"
);
source = source.replace(
  /undefined8 __fastcall FUN_004268e4\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0042692c \*\//,
  "undefined8 __fastcall FUN_004268e4(undefined4 param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  int iVar2;\n  \n  iVar2 = (int)(uintptr_t)param_1;\n  if ((uint)iVar2 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)iVar2,6)) {\n    return CONCAT44(param_2,0);\n  }\n  iVar1 = FUN_0045f1ff(1,0x39);\n  if (iVar1 == 0) {\n    return CONCAT44(param_2,0);\n  }\n  FUN_0045fc70(0x35,0x20202020);\n  *(undefined4 *)(iVar1 + 0x35) = *(undefined4 *)(iVar2 + 2);\n  *(int *)(iVar2 + 2) = iVar1;\n  return CONCAT44(param_2,iVar1);\n}\n\n\n\n/* 0042692c */"
);
source = source.replace(
  /undefined8 __fastcall FUN_0042692c\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00426974 \*\//,
  "undefined8 __fastcall FUN_0042692c(undefined4 param_1,undefined4 param_2)\n\n{\n  int iVar1;\n  int iVar2;\n  \n  iVar2 = (int)(uintptr_t)param_1;\n  if ((uint)iVar2 < 0x10000u || IsBadReadPtr((void *)(uintptr_t)iVar2,0x39)) {\n    return CONCAT44(param_2,0);\n  }\n  iVar1 = FUN_0045f1ff(1,0x39);\n  if (iVar1 == 0) {\n    return CONCAT44(param_2,0);\n  }\n  FUN_0045fc70(0x35,0x20202020);\n  *(undefined4 *)(iVar1 + 0x35) = *(undefined4 *)(iVar2 + 0x35);\n  *(int *)(iVar2 + 0x35) = iVar1;\n  return CONCAT44(param_2,iVar1);\n}\n\n\n\n/* 00426974 */"
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
  /undefined8 __fastcall FUN_00426410\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00426478 \*\//,
  "undefined8 __fastcall FUN_00426410(undefined4 param_1,undefined4 param_2)\n\n{\n  int action;\n  int cursor;\n  \n  action = (int)FUN_00453338(param_1,param_2);\n  *(undefined2 *)(action + 2) = 0x100;\n  *(undefined4 *)(action + 4) = 0;\n  *(undefined4 *)(action + 8) = 0;\n  *(undefined2 *)(action + 0xe) = 0xffff;\n  *(undefined2 *)(action + 0x10) = 0xffff;\n  *(undefined4 *)(action + 0x12) = _DAT_00636588;\n  *(undefined2 *)(action + 0xc) = 0x200;\n  cursor = (int)(uintptr_t)_DAT_00637270;\n  if (cursor == 0) {\n    _DAT_00637270 = (short *)(uintptr_t)action;\n  }\n  else {\n    while (*(int *)(cursor + 8) != 0) {\n      cursor = *(int *)(cursor + 8);\n    }\n    *(int *)(cursor + 8) = action;\n  }\n  return CONCAT44(param_2,action);\n}\n\n\n\n/* 00426478 */"
);
source = source.replace(
  /void __fastcall FUN_00452c70\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00452d3c \*\//,
  "void __fastcall FUN_00452c70(undefined4 param_1,undefined4 param_2)\n\n{\n  short *action;\n  short *cursor;\n  short *previous;\n  \n  (void)param_2;\n  action = (short *)(uintptr_t)param_1;\n  if ((uintptr_t)action < 0x10000u || IsBadReadPtr(action,0x16)) {\n    return;\n  }\n  if (*action >= 0) {\n    *(undefined4 *)((undefined1 *)0x0062ba20 + *action * 4) = 0;\n  }\n  if (action == _DAT_00637270) {\n    _DAT_00637270 = *(short **)(action + 4);\n  }\n  else {\n    previous = _DAT_00637270;\n    while (previous != (short *)0x0 && !IsBadReadPtr(previous,0x16)) {\n      cursor = *(short **)(previous + 4);\n      if (cursor == action) {\n        *(undefined4 *)(previous + 4) = *(undefined4 *)(action + 4);\n        break;\n      }\n      previous = cursor;\n    }\n  }\n  *(undefined4 *)(action + 2) = 0;\n  *(undefined4 *)(action + 4) = 0;\n  action[6] = (short)0x8000;\n  return;\n}\n\n\n\n/* 00452d3c */"
);
source = source.replace(
  /(ulonglong __fastcall FUN_004435e8\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined4 uStack_4;\r?\n\s*)uStack_4 = param_2;/,
  "$1in_EAX = (uint)(uintptr_t)param_1;\n  uStack_4 = param_2;"
);
source = source.replace(
  "  FUN_0045f0a1((int)local_38,(byte *)s_Unknown_name_indicator_in_token___00474158);\n  uVar4 = FUN_0043cac0(extraout_ECX,extraout_EDX);\n  FUN_00460215(extraout_ECX_00,(int)((ulonglong)uVar4 >> 0x20));\n  FUN_00414e68();\n  in_EAX = extraout_EDX_00;",
  "  if (E2R_fan_phase_diag_count < 64) {\n    E2R_fan_phase_diag_count = E2R_fan_phase_diag_count + 1;\n    fprintf(stderr,\"FAN action token passthrough: token=%04x class=%04x offset=%u\\n\",\n            (ushort)in_EAX,uVar2,E2R_FanStreamOffset());\n  }"
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
  /undefined8 __fastcall FUN_00453338\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 004533a4 \*\//,
  "undefined8 __fastcall FUN_00453338(undefined4 param_1,undefined4 param_2)\n\n{\n  int offset;\n  undefined1 *slot;\n  \n  (void)param_1;\n  do {\n    for (offset = 0; offset < 0x2260; offset = offset + 0x16) {\n      if ((*(ushort *)((undefined1 *)0x00ac2648 + offset) & 0x8000) != 0) {\n        slot = (undefined1 *)(0x00ac263c + offset);\n        memset(slot,0,0x16);\n        return CONCAT44(param_2,(undefined4)(uintptr_t)slot);\n      }\n    }\n    if ((int)FUN_00452fe8(0,0) == 0) {\n      FUN_00414e68();\n    }\n  } while( true );\n}\n\n\n\n/* 004533a4 */"
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
  ["00446874", "_DAT_006366bc", "20000", "0x9c4",
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
  ["00441ea4", "_DAT_006366bc", "20000", "0x9c4"],
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
  "    case 6:\n      DestroyWindow(_DAT_00ac4dac);\n    }\n    FUN_0041cfc0();"
);
source = source.replace(
  "    case 2:\n      _DAT_00643660 = 1;\n      FUN_0043ce58(extraout_ECX_06,(int)((ulonglong)uVar4 >> 0x20));",
  "    case 2:\n      _DAT_00643660 = 1;\n      FUN_0043ce58(0x31,(int)((ulonglong)uVar4 >> 0x20));"
);
source = source.replace(
  "    case 3:\n      _DAT_0064353c = -1;\n      iVar2 = 0;\n      uVar1 = extraout_ECX_06;",
  "    case 3:\n      _DAT_0064353c = -1;\n      iVar2 = 0;\n      uVar1 = 0x2a;"
);
source = source.replace(
  "    case 4:\n      _DAT_0064353c = -1;\n      iVar2 = 0;\n      uVar1 = extraout_ECX_06;",
  "    case 4:\n      _DAT_0064353c = -1;\n      iVar2 = 0;\n      uVar1 = 0x29;"
);
source = source.replace(
  "    case 6:\n      DestroyWindow(_DAT_00ac4dac);\n    }\n    E2R_GameStateLog(\"15d40.switch done state=%lu dialog=%lu space=%u\",",
  "    case 6:\n      DestroyWindow(_DAT_00ac4dac);\n    }\n    if (_DAT_00643650 == 2 || _DAT_00643650 == 3 ||\n        _DAT_00643650 == 4 || _DAT_00643650 == 5) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"15d40.menu_complete\",0);\n    }\n    E2R_GameStateLog(\"15d40.switch done state=%lu dialog=%lu space=%u\","
);
source = source.replace(
  /(longlong __fastcall FUN_0043c1b8\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  uint local_20;\r?\n  uint local_1c;\r?\n\s*)if \(9 < in_EAX\) \{\r?\n    FUN_00414e68\(\);\r?\n  \}/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  if (9 < in_EAX) {\n    in_EAX = -1;\n  }"
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
  "        puVar8 = (undefined1 *)((ulonglong)uVar12 >> 0x20);\n        puVar7 = puVar8 + 1;",
  "        puVar8 = puVar7;\n        puVar7 = puVar7 + 1;"
);
source = source.replaceAll(
  "        iVar10 = (int)((ulonglong)uVar12 >> 0x20) + 1;",
  "        iVar10 = iVar10 + 1;"
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
  "  char local_3c [6];\n  char acStack_36 [18];",
  "  char local_3c [24];"
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
  `  FUN_0045fd2c(0xd02,s_Vil_Zombi_00474b6c);
  FUN_0045fd2c(extraout_ECX,s_Vil_SmGal_00474b78);
  FUN_0045fd2c(extraout_ECX_00,s_Vil_Galag_00474b84);
  FUN_0045fd2c(extraout_ECX_01,s_Vil_Cyclo_00474b90);
  FUN_0045fd2c(extraout_ECX_02,s_Vil_Wolf_00474b9c);
  FUN_0045fd2c(extraout_ECX_03,s_Vil_Red_D_00474ba8);
  FUN_0045fd2c(extraout_ECX_04,s_Sml_Galag_00474bb4);
  FUN_0045fd2c(extraout_ECX_05,s_Mushroom_00474bc0);
  FUN_0045fd2c(extraout_ECX_06,s_Mummy_00474bcc);
  FUN_0045fd2c(extraout_ECX_07,s_Galagon_00474bd8);
  FUN_0045fd2c(extraout_ECX_08,s_Amazon_00474be4);
  FUN_0045fd2c(extraout_ECX_09,s_Fish_00474bf0);
  FUN_0045fd2c(extraout_ECX_10,s_Fairy_Blu_00474bfc);
  FUN_0045fd2c(extraout_ECX_11,s_Fairy_Grn_00474c08);
  FUN_0045fd2c(extraout_ECX_12,s_Red_Devil_00474c14);
  FUN_0045fd2c(extraout_ECX_13,s_Good_Nite_00474c20);
  FUN_0045fd2c(extraout_ECX_14,s_Bad_Nite_00474c2c);
  FUN_0045fd2c(extraout_ECX_15,s_Skeleton_00474c38);
  FUN_0045fd2c(extraout_ECX_16,s_Hunchback_00474c44);
  FUN_0045fd2c(extraout_ECX_17,s_Werewolf_00474c50);
  FUN_0045fd2c(extraout_ECX_18,s_Bat_Stone_00474c5c);
  FUN_0045fd2c(extraout_ECX_19,s_Demon_00474c68);
  FUN_0045fd2c(extraout_ECX_20,s_Eel_Eye_00474c74);
  FUN_0045fd2c(extraout_ECX_21,s_Ken_Dorc_00474c80);
  FUN_0045fd2c(extraout_ECX_22,s_Statue_00474c8c);
  FUN_0045fd2c(extraout_ECX_23,s_Red_Dwarf_00474c98);
  FUN_0045fd2c(extraout_ECX_24,s_Sprite_00474ca4);
  FUN_0045fd2c(extraout_ECX_25,s_Monk_00474cb0);
  FUN_0045fd2c(extraout_ECX_26,s_Sml_Grn_S_00474cbc);
  FUN_0045fd2c(extraout_ECX_27,s_Sml_Blk_S_00474cc8);
  FUN_0045fd2c(extraout_ECX_28,s_Grn_Spidr_00474cd4);
  FUN_0045fd2c(extraout_ECX_29,s_Zombie_00474ce0);
  FUN_0045fd2c(extraout_ECX_30,s_Cyclops_00474cec);
  FUN_0045fd2c(extraout_ECX_31,s_Stone_Trl_00474cf8);
  FUN_0045fd2c(extraout_ECX_32,s_Orc_00474d04);
  FUN_0045fd2c(extraout_ECX_33,s_Barbarian_00474d10);
  FUN_0045fd2c(extraout_ECX_34,s_Blk_Spidr_00474d1c);
  FUN_0045fd2c(extraout_ECX_35,s_Blob_00474d28);
  FUN_0045fd2c(extraout_ECX_36,s_Slime_00474d34);
  FUN_0045fd2c(extraout_ECX_37,s_Beholder_00474d40);
  FUN_0045fd2c(extraout_ECX_38,s_Ghost_00474d4c);
  FUN_0045fd2c(extraout_ECX_39,s_Goblin_00474d58);
  iVar3 = 0xc;
  FUN_0045fd2c(extraout_ECX_40,s__nothing__00474d64);`,
  `  E2R_CopyCStringBounded((char *)0x0067c328,s_Vil_Zombi_00474b6c,0xc);
  E2R_CopyCStringBounded((char *)0x0067c334,s_Vil_SmGal_00474b78,0xc);
  E2R_CopyCStringBounded((char *)0x0067c340,s_Vil_Galag_00474b84,0xc);
  E2R_CopyCStringBounded((char *)0x0067c34c,s_Vil_Cyclo_00474b90,0xc);
  E2R_CopyCStringBounded((char *)0x0067c358,s_Vil_Wolf_00474b9c,0xc);
  E2R_CopyCStringBounded((char *)0x0067c364,s_Vil_Red_D_00474ba8,0xc);
  E2R_CopyCStringBounded((char *)0x0067c370,s_Sml_Galag_00474bb4,0xc);
  E2R_CopyCStringBounded((char *)0x0067c37c,s_Mushroom_00474bc0,0xc);
  E2R_CopyCStringBounded((char *)0x0067c388,s_Mummy_00474bcc,0xc);
  E2R_CopyCStringBounded((char *)0x0067c394,s_Galagon_00474bd8,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3a0,s_Amazon_00474be4,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3ac,s_Fish_00474bf0,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3b8,s_Fairy_Blu_00474bfc,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3c4,s_Fairy_Grn_00474c08,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3d0,s_Red_Devil_00474c14,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3dc,s_Good_Nite_00474c20,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3e8,s_Bad_Nite_00474c2c,0xc);
  E2R_CopyCStringBounded((char *)0x0067c3f4,s_Skeleton_00474c38,0xc);
  E2R_CopyCStringBounded((char *)0x0067c400,s_Hunchback_00474c44,0xc);
  E2R_CopyCStringBounded((char *)0x0067c40c,s_Werewolf_00474c50,0xc);
  E2R_CopyCStringBounded((char *)0x0067c418,s_Bat_Stone_00474c5c,0xc);
  E2R_CopyCStringBounded((char *)0x0067c424,s_Demon_00474c68,0xc);
  E2R_CopyCStringBounded((char *)0x0067c430,s_Eel_Eye_00474c74,0xc);
  E2R_CopyCStringBounded((char *)0x0067c43c,s_Ken_Dorc_00474c80,0xc);
  E2R_CopyCStringBounded((char *)0x0067c448,s_Statue_00474c8c,0xc);
  E2R_CopyCStringBounded((char *)0x0067c454,s_Red_Dwarf_00474c98,0xc);
  E2R_CopyCStringBounded((char *)0x0067c460,s_Sprite_00474ca4,0xc);
  E2R_CopyCStringBounded((char *)0x0067c46c,s_Monk_00474cb0,0xc);
  E2R_CopyCStringBounded((char *)0x0067c478,s_Sml_Grn_S_00474cbc,0xc);
  E2R_CopyCStringBounded((char *)0x0067c484,s_Sml_Blk_S_00474cc8,0xc);
  E2R_CopyCStringBounded((char *)0x0067c490,s_Grn_Spidr_00474cd4,0xc);
  E2R_CopyCStringBounded((char *)0x0067c49c,s_Zombie_00474ce0,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4a8,s_Cyclops_00474cec,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4b4,s_Stone_Trl_00474cf8,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4c0,s_Orc_00474d04,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4cc,s_Barbarian_00474d10,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4d8,s_Blk_Spidr_00474d1c,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4e4,s_Blob_00474d28,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4f0,s_Slime_00474d34,0xc);
  E2R_CopyCStringBounded((char *)0x0067c4fc,s_Beholder_00474d40,0xc);
  E2R_CopyCStringBounded((char *)0x0067c508,s_Ghost_00474d4c,0xc);
  E2R_CopyCStringBounded((char *)0x0067c514,s_Goblin_00474d58,0xc);
  iVar3 = 0xc;
  E2R_CopyCStringBounded((char *)0x0067c520,s__nothing__00474d64,0xc);`
);
source = source.replace(
  "    uVar13 = FUN_0045e594(extraout_ECX_03,extraout_EDX,&stack_ffffff98,0x200,in_stack_ffffff98);\n    if ((int)uVar13 != -1) {\n      FUN_0045e76f(extraout_ECX_04,(char *)local_1c);\n      if (local_1c[0] == 0x686d) {\n        FUN_0045e76f(extraout_ECX_05,_DAT_0063615c);\n        FUN_0045e76f(extraout_ECX_06,_DAT_0063615c);\n        FUN_0045e76f(extraout_ECX_07,_DAT_0063615c);\n        FUN_0045e76f(extraout_ECX_08,_DAT_00636670);\n        uVar7 = extraout_ECX_09;\n        uVar9 = extraout_EDX_00;\n      }\n      else {\n        FUN_0045e76f(extraout_ECX_05,(char *)&local_20);\n        FUN_0045e76f(extraout_ECX_10,(char *)&local_24);\n        if (_DAT_006401ec * _DAT_006401d4 * 2 <= local_20 + local_24) {\n          FUN_00414e68();\n        }\n        FUN_0045e76f(local_24,_DAT_00636668);\n        FUN_0045df96();\n        FUN_0045dff3();\n        uVar7 = extraout_ECX_11;\n        uVar9 = extraout_EDX_01;\n      }",
  "    if (E2R_RuntimeDiagEnabled()) {\n      fprintf(stderr,\"view raw open: scene=%d camera=%d hires=%d path=%s\\n\",\n              (int)(short)_DAT_0073ccba,(int)(_DAT_0073ccb8 >> 0x10),\n              DAT_0047a43c != 0,(char *)stack_ffffff98);\n    }\n    uVar13 = FUN_0045e594(extraout_ECX_03,extraout_EDX,(LPCSTR)stack_ffffff98,0x200,\n                           in_stack_ffffff98);\n    if ((int)uVar13 != -1) {\n      iVar10 = (int)uVar13;\n      E2R_ReadOpenFileBytes(iVar10,(char *)local_1c,2);\n      if (local_1c[0] == 0x686d) {\n        iVar2 = _DAT_006401ec * _DAT_006401d4;\n        E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,0x1e);\n        E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,0x300);\n        E2R_ReadOpenFileBytes(iVar10,_DAT_0063615c,iVar2);\n        E2R_ReadOpenFileBytes(iVar10,_DAT_00636670,iVar2 * 2);\n        uVar7 = (undefined4)iVar10;\n        uVar9 = extraout_EDX_00;\n      }\n      else {\n        E2R_ReadOpenFileBytes(iVar10,(char *)&local_20,4);\n        E2R_ReadOpenFileBytes(iVar10,(char *)&local_24,4);\n        if (_DAT_006401ec * _DAT_006401d4 * 2 <= local_20 + local_24) {\n          FUN_00414e68();\n        }\n        E2R_ReadOpenFileBytes(iVar10,_DAT_00636668,local_20 + local_24);\n        FUN_0045df96((byte *)_DAT_00636668,(byte *)_DAT_0063615c);\n        FUN_0045dff3((byte *)(_DAT_00636668 + local_20),(short *)_DAT_00636670);\n        uVar7 = (undefined4)iVar10;\n        uVar9 = extraout_EDX_01;\n      }"
);
source = source.replace(
  "    FUN_0043cbb4(extraout_ECX_04);\n  }\n  return CONCAT44(param_2,0xffffffff);\n}\n\n\n\n/* 0044a178 */",
  "    FUN_0043cbb4(0x004749e0);\n  }\n  return CONCAT44(param_2,0xffffffff);\n}\n\n\n\n/* 0044a178 */"
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
  "  FUN_0043ac60();\n  uVar5 = 0;\n  if (DAT_00479dfc != 0) {\n    FUN_00414998(s_gbnklogo_raw_00470500);\n    E2R_WaitStartupLogo();\n  }\n  FUN_00414998(s_psyglogo_raw_00470510);\n  E2R_WaitStartupLogo();\n  FUN_00414998(s_aasglogo_raw_00470520);\n  E2R_WaitStartupLogo();\n  uVar3 = 0;\n  uVar11 = FUN_00414a94(uVar5,uVar3);\n  uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n  uVar5 = 0;\n  if (DAT_00479e1c == 0) {\n    uVar11 = FUN_00414b24(uVar5,uVar6);\n    uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n    uVar5 = 0;\n  }"
);
source = source.replace(
  /(undefined4|void) FUN_00414e68\(void\)([\s\S]*?\r?\n  char \*)in_EAX;/,
  "$1 FUN_00414e68(void)$2in_EAX = s_Can_t_load_title_picture_00471320;"
);
source = source.replace(
  /(void __fastcall FUN_00414998\(undefined4 param_1\)[\s\S]*?\r?\n  undefined8 uVar3;\r?\n\s*)if \(DAT_0047a43c == 0\) \{/,
  "$1in_EAX = param_1;\n  E2R_GameStateLog(\"startup logo show begin name=%s ptr=0x%lx\",\n                   E2R_StartupLogoName(param_1),(unsigned long)(uintptr_t)param_1);\n  if (DAT_0047a43c == 0) {"
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
  "      FUN_0041af88(extraout_ECX_03,(int)((ulonglong)uVar3 >> 0x20));",
  "      FUN_0041af88(0x621030,(int)((ulonglong)uVar3 >> 0x20));"
);
source = source.replace(
  "      FUN_0041af88(extraout_ECX_04,extraout_EDX_01);",
  "      FUN_0041af88(0x621030,extraout_EDX_01);\n      E2R_GameStateLog(\"startup logo show end name=%s size=%ldx%ld\",\n                       E2R_StartupLogoName(param_1),\n                       (long)_DAT_006401ec,(long)_DAT_006401d4);"
);
source = source.replace(
  "      FUN_0041af88(extraout_ECX_03,(int)((ulonglong)uVar8 >> 0x20));",
  "      FUN_0041af88(0x61ca30,(int)((ulonglong)uVar8 >> 0x20));"
);
source = source.replace(
  "      uVar4 = FUN_0041af88(extraout_ECX_04,extraout_EDX_01);",
  "      uVar4 = FUN_0041af88(0x61ca30,extraout_EDX_01);"
);
source = source.replace(
  "    FUN_0041af88(extraout_ECX_10,(int)((ulonglong)uVar8 >> 0x20));",
  "    FUN_0041af88(0x00621330,(int)((ulonglong)uVar8 >> 0x20));"
);
source = source.replace(
  "      FUN_0041af88(extraout_ECX_07,(int)((ulonglong)uVar5 >> 0x20));",
  "      FUN_0041af88(0x621030,(int)((ulonglong)uVar5 >> 0x20));"
);
source = source.replace(
  "      FUN_0041af88(extraout_ECX_09,extraout_EDX_02);",
  "      FUN_0041af88(0x621030,extraout_EDX_02);"
);
source = source.replace(
  "    FUN_0041af88(extraout_ECX_11,uVar4);",
  "    FUN_0041af88(0xab9fac,uVar4);"
);
source = source.replace(
  "    FUN_0041af88(100 - in_EAX,iVar2 % 100);",
  "    FUN_0041af88(0xab9fac,iVar2 % 100);"
);
source = source.replace(
  "    FUN_0041af88((uint)bVar1,iVar3 % 100);",
  "    FUN_0041af88(0xab9fac,iVar3 % 100);"
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
source = source.replace(
  "            uVar13 = FUN_0043b384(pbVar6,pcVar8);\n            return CONCAT44(param_2,(int)uVar13);",
      "            E2R_InitRequesterRecord(0x0047a5a4,-1,-1,0xf0,0xb4,\n                                      (uintptr_t)_DAT_006438a0,_DAT_0047a5b0);\n            uVar13 = FUN_0043b384(0x0047a5a4,pcVar8);\n            return CONCAT44(param_2,(int)uVar13);"
);
source = source.replace(
  "      FUN_0043d8ec();\n      FUN_0043d934();\n      FUN_0043d9a0();\n      FUN_0043da04();\n      FUN_0043da80();\n      uVar13 = FUN_0043b384(extraout_ECX_04,extraout_EDX_00);",
  "      FUN_0043d8ec();\n      FUN_0043d934();\n      FUN_0043d9a0();\n      FUN_0043da04();\n      FUN_0043da80();\n      E2R_InitRequesterSettingsItems();\n      uVar13 = FUN_0043b384(0x0047a668,extraout_EDX_00);"
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
  "  style_surface = DAT_0047a279 >> 0x18;\n  in_EAX = style_surface;\n  if (DAT_0047a43c != 0) {\n    in_EAX = in_EAX + 2;\n  }\n  pbVar5 = (undefined1 *)0x00477068;\n  iVar12 = 0;"
);
source = source.replace(
  "    local_80 = FUN_00418a04(pbVar5,&local_84);\n    local_14 = ((undefined1 *)0x006366dc)[in_EAX * 2];",
  "    local_80 = FUN_00418a04((undefined4)(uintptr_t)in_EAX,&local_84);\n    if (local_80 == 0 || local_84 <= 0) {\n      return 0;\n    }\n    style_index = style_surface * 2;\n    local_14 = ((undefined1 *)0x006366dc)[style_index];\n    local_10 = *(undefined1 *)(style_index + 0x6366e8);"
);
source = source.replace(
  "    local_10 = *(undefined1 *)(style_index + 0x6366e8);\n    local_10 = *(undefined1 *)(in_EAX * 2 + 0x6366e8);",
  "    local_10 = *(undefined1 *)(style_index + 0x6366e8);"
);

for (let i = 0; i < prototypes.length; i++) {
  prototypes[i] = prototypes[i].replace("uint * FUN_00461746(void);", "uint * __fastcall FUN_00461746(int heap,uint size);");
  prototypes[i] = prototypes[i].replace("void FUN_00420b8c(void);", "void FUN_00420b8c(int index);");
  prototypes[i] = prototypes[i].replace("void FUN_00423070(void);", "void FUN_00423070(int *coord);");
  prototypes[i] = prototypes[i].replace("void FUN_00424cbc(void);", "void FUN_00424cbc(int actor);");
  prototypes[i] = prototypes[i].replace("void FUN_00424d14(void);", "void FUN_00424d14(int actor);");
  prototypes[i] = prototypes[i].replace("void FUN_00424d58(void);", "void FUN_00424d58(int actor);");
  prototypes[i] = prototypes[i].replace("void FUN_00424d98(void);", "void FUN_00424d98(int actor);");
  prototypes[i] = prototypes[i].replace(
    "void __fastcall FUN_00424dd8(int param_1);",
    "void __fastcall FUN_00424dd8(int param_1,int actor);"
  );
  prototypes[i] = prototypes[i].replace(
    "void __fastcall FUN_00424e44(int param_1);",
    "void __fastcall FUN_00424e44(int param_1,int node);"
  );
  prototypes[i] = prototypes[i].replace(
    "void __fastcall FUN_00431a7c(undefined4 param_1,int param_2);",
    "void __fastcall FUN_00431a7c(int actor,int param_2);"
  );
  prototypes[i] = prototypes[i].replace(
    "void __fastcall FUN_00433d30(undefined4 param_1,int param_2);",
    "void __fastcall FUN_00433d30(int actor,int param_2);"
  );
  prototypes[i] = prototypes[i].replace("void FUN_00425018(void);", "void FUN_00425018(int actor);");
  prototypes[i] = prototypes[i].replace("void FUN_00425538(void);", "void FUN_00425538(int actor);");
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
    "undefined8 __fastcall FUN_00441e38(undefined4 param_1,undefined4 param_2);",
    "undefined8 __fastcall FUN_00441e38(short param_1,undefined4 param_2);"
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
  prototypes[i] = prototypes[i].replace(
    "undefined4 FUN_004523f8(void);",
    "undefined4 FUN_004523f8(undefined4 param_1);"
  );
  prototypes[i] = prototypes[i].replace(
    "void FUN_0044be20(void);",
    "void FUN_0044be20(undefined4 param_1);"
  );
  prototypes[i] = prototypes[i].replace(
    "void FUN_0044d3e8(void);",
    "void __fastcall FUN_0044d3e8(undefined4 param_1);"
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
  "          else {\n            FUN_00420dcc();\n            param_1 = extraout_ECX_06;",
  "          else {\n            E2R_actor_calc_context = (int)(uintptr_t)psVar4;\n            FUN_00420dcc();\n            E2R_actor_calc_context = 0;\n            param_1 = extraout_ECX_06;"
);
source = source.replace(
  "        if (*(int *)((undefined1 *)0x00630b60 + *psVar3 * 4) != 0) {\n          FUN_00426c3c();\n          bVar2 = ((undefined1 *)0x0064a178)[*psVar3 * 2];\n          param_1 = CONCAT22((short)((uint)extraout_ECX_11 >> 0x10),\n                             CONCAT11(bVar2,(char)extraout_ECX_11));\n          if ((bVar2 & 2) == 0) {\n            ((undefined1 *)0x0064a178)[*psVar3 * 2] = bVar2 | 2;\n            extraout_EDX_01[0x77] = 100;\n            extraout_EDX_01[0x76] = extraout_EDX_01[0x77];\n            if ((-1 < (short)extraout_EDX_01[0x9d]) &&\n               (*(int *)((*(int *)(extraout_EDX_01 + 0x9c) >> 0x10) * 4 + 0x6297c0) != 0)) {\n              FUN_0044f508(extraout_EDX_01,extraout_EDX_01,(ushort *)0x0);\n              param_1 = extraout_ECX_12;\n            }\n          }\n        }",
  "        if (*(int *)((undefined1 *)0x00630b60 + *psVar3 * 4) != 0) {\n          psVar4 = *(short **)((undefined1 *)0x00630b60 + *psVar3 * 4);\n          E2R_actor_calc_context = (int)(uintptr_t)psVar4;\n          FUN_00426c3c();\n          E2R_actor_calc_context = 0;\n          bVar2 = ((undefined1 *)0x0064a178)[*psVar3 * 2];\n          param_1 = CONCAT22((short)((uint)extraout_ECX_11 >> 0x10),\n                             CONCAT11(bVar2,(char)extraout_ECX_11));\n          if ((bVar2 & 2) == 0) {\n            ((undefined1 *)0x0064a178)[*psVar3 * 2] = bVar2 | 2;\n            psVar4[0x77] = 100;\n            psVar4[0x76] = psVar4[0x77];\n            if ((-1 < psVar4[0x9d]) &&\n               (*(int *)((*(int *)(psVar4 + 0x9c) >> 0x10) * 4 + 0x6297c0) != 0)) {\n              FUN_0044f508(psVar4,psVar4,(ushort *)0x0);\n              param_1 = extraout_ECX_12;\n            }\n          }\n        }"
);
source = source.replace(
  "  if (in_EAX != 0) {\n    *(ushort *)(in_EAX + 2) = *(ushort *)(in_EAX + 2) & 0xf3f6;",
  "  in_EAX = E2R_actor_calc_context;\n  if (in_EAX != 0 && !IsBadReadPtr((void *)(uintptr_t)in_EAX,0x148)) {\n    *(ushort *)(in_EAX + 2) = *(ushort *)(in_EAX + 2) & 0xf3f6;"
);
source = source.replace(
  "  uVar6 = FUN_00453588(param_1,param_2);\n  puVar4 = (undefined2 *)uVar6;\n  *puVar4 = 0xffff;",
  "  uVar6 = FUN_00453588(param_1,param_2);\n  puVar4 = (undefined2 *)uVar6;\n  if (puVar4 == (undefined2 *)0x0) {\n    return CONCAT44(param_2,0);\n  }\n  *puVar4 = 0xffff;"
);
source = source.replace(
  "      local_20 = (short *)uVar15;\n      *local_20 = *psVar8;\n      local_20[1] = psVar8[2];\n      local_20[6] = psVar8[3];\n      if (_DAT_0067bc92 < 8) {\n        local_20[0x4c] = -1;\n      }\n      else {\n        local_20[0x4c] = psVar8[4];\n      }\n      local_20[0x53] = DAT_00479e50;\n      *(short **)(*local_20 * 4 + 0x62e450) = local_20;",
  "      local_20 = (short *)uVar15;\n      if (local_20 != (short *)0x0) {\n        *local_20 = *psVar8;\n        local_20[1] = psVar8[2];\n        local_20[6] = psVar8[3];\n        if (_DAT_0067bc92 < 8) {\n          local_20[0x4c] = -1;\n        }\n        else {\n          local_20[0x4c] = psVar8[4];\n        }\n        local_20[0x53] = DAT_00479e50;\n        *(short **)(*local_20 * 4 + 0x62e450) = local_20;\n        E2R_TraceSceneRecordInstall(\"install\",local_20,psVar8);\n      }"
);
source = source.replace(
  "    else if (sVar9 == 0x34) {\n      local_20[0x4d] = psVar8[2];",
  "    else if (sVar9 == 0x34) {\n      if (local_20 != (short *)0x0) {\n        local_20[0x4d] = psVar8[2];\n        E2R_TraceSceneRecordInstall(\"action-ref\",local_20,psVar8);\n      }"
);
source = source.replace(
  "    else if (sVar9 == 0x1b) {\n      local_20[*psVar8 + 7] = psVar8[2];",
  "    else if (sVar9 == 0x1b) {\n      if (local_20 != (short *)0x0) {\n        local_20[*psVar8 + 7] = psVar8[2];\n      }"
);
source = source.replace(
  "    else if (sVar9 == 0x1b) {\n      if (local_20 != (short *)0x0) {",
  "    else if (sVar9 == 0x1b) {\n      if (E2R_StartupDiagEnabled() && E2R_scene_record_install_diag_count < 128) {\n        fprintf(stderr,\n                \"scene field record 1b: requested=%d scene=0x%lx target_index=%d raw=%04x,%04x,%04x,%04x,%04x\\n\",\n                E2R_scene_load_request_id,(unsigned long)(uintptr_t)local_20,\n                (int)*psVar8,(unsigned int)(ushort)psVar8[0],\n                (unsigned int)(ushort)psVar8[1],(unsigned int)(ushort)psVar8[2],\n                (unsigned int)(ushort)psVar8[3],(unsigned int)(ushort)psVar8[4]);\n      }\n      if (local_20 != (short *)0x0) {"
);
source = source.replace(
  "          if (sVar9 < 0x19) {\n            *(char *)((int)local_20 + (int)sVar9 + (*psVar8 + -1) * 0x19 + 0x32) = (char)local_30;",
  "          if (local_20 != (short *)0x0 && sVar9 < 0x19) {\n            *(char *)((int)local_20 + (int)sVar9 + (*psVar8 + -1) * 0x19 + 0x32) = (char)local_30;"
);
source = source.replace(
  "          E2R_READ1(local_30,0) = (char)uVar15;",
  "          local_30 = (local_30 & 0xffffff00) | ((uint)uVar15 & 0xff);"
);
source = source.replace(
  "        *(undefined1 *)((int)local_20 + (*psVar8 + -1) * 0x19 + 0x4a) = 0;",
  "        if (local_20 != (short *)0x0) {\n          *(undefined1 *)((int)local_20 + (*psVar8 + -1) * 0x19 + 0x4a) = 0;\n        }"
);
source = source.replace(
  "      local_24 = (short *)uVar15;\n      local_24[2] = psVar8[2];\n      local_24[7] = psVar8[3];\n      *local_24 = psVar8[4];",
  "      local_24 = (short *)uVar15;\n      if (E2R_StartupDiagEnabled() && E2R_scene_record_install_diag_count < 128) {\n        fprintf(stderr,\n                \"scene child record 1a: requested=%d scene=0x%lx node=0x%lx raw=%04x,%04x,%04x,%04x,%04x\\n\",\n                E2R_scene_load_request_id,(unsigned long)(uintptr_t)local_20,\n                (unsigned long)(uintptr_t)local_24,\n                (unsigned int)(ushort)psVar8[0],(unsigned int)(ushort)psVar8[1],\n                (unsigned int)(ushort)psVar8[2],(unsigned int)(ushort)psVar8[3],\n                (unsigned int)(ushort)psVar8[4]);\n      }\n      if (local_24 != (short *)0x0) {\n        local_24[2] = psVar8[2];\n        local_24[7] = psVar8[3];\n        *local_24 = psVar8[4];\n        if (E2R_StartupDiagEnabled() && E2R_scene_record_install_diag_count < 128) {\n          fprintf(stderr,\n                  \"scene child record 1a install: requested=%d actor=%d word2=%d flags=0x%04x\\n\",\n                  E2R_scene_load_request_id,(int)*local_24,(int)local_24[2],\n                  (unsigned int)(ushort)local_24[7]);\n        }\n      }"
);
source = source.replace(
  "    if ((puVar3 == (undefined1 *)0x0) &&\n       (lVar5 = FUN_00452ebc(param_1,0), param_1 = extraout_ECX, (int)lVar5 == 0)) {\n      FUN_00414e68();\n      lVar5 = (ulonglong)extraout_EDX << 0x20;\n      param_1 = extraout_ECX_00;\n    }",
  "    if ((puVar3 == (undefined1 *)0x0) &&\n       (lVar5 = FUN_00452ebc(param_1,0), param_1 = extraout_ECX, (int)lVar5 == 0)) {\n      puVar3 = (undefined1 *)FUN_0045f1ff(1,0xa8);\n      if (puVar3 == (undefined1 *)0x0) {\n        return CONCAT44(param_2,0);\n      }\n      memset(puVar3,0,0xa8);\n      lVar5 = ZEXT48(puVar3) << 0x20;\n    }"
);
source = source.replace(
  "    if ((puVar3 == (undefined1 *)0x0) &&\n       (lVar5 = FUN_004531bc(param_1,0), param_1 = extraout_ECX, (int)lVar5 == 0)) {\n      FUN_00414e68();\n      lVar5 = (ulonglong)extraout_EDX << 0x20;\n      param_1 = extraout_ECX_00;\n    }",
  "    if ((puVar3 == (undefined1 *)0x0) &&\n       (lVar5 = FUN_004531bc(param_1,0), param_1 = extraout_ECX, (int)lVar5 == 0)) {\n      puVar3 = (undefined1 *)FUN_0045f1ff(1,0x3c);\n      if (puVar3 == (undefined1 *)0x0) {\n        return CONCAT44(param_2,0);\n      }\n      memset(puVar3,0,0x3c);\n      lVar5 = ZEXT48(puVar3) << 0x20;\n    }"
);
source = source.replace(
  "    if ((puVar3 == (undefined1 *)0x0) &&\n       (lVar5 = FUN_00453210(param_1,0), param_1 = extraout_ECX, (int)lVar5 == 0)) {\n      FUN_00414e68();\n      lVar5 = (ulonglong)extraout_EDX << 0x20;\n      param_1 = extraout_ECX_00;\n    }",
  "    if ((puVar3 == (undefined1 *)0x0) &&\n       (lVar5 = FUN_00453210(param_1,0), param_1 = extraout_ECX, (int)lVar5 == 0)) {\n      puVar3 = (undefined1 *)FUN_0045f1ff(1,0x14);\n      if (puVar3 == (undefined1 *)0x0) {\n        return CONCAT44(param_2,0);\n      }\n      memset(puVar3,0,0x14);\n      lVar5 = ZEXT48(puVar3) << 0x20;\n    }"
);
source = source.replace(
  "  uVar2 = FUN_004537d8(param_1,param_2);\n  puVar1 = (undefined2 *)uVar2;\n  *puVar1 = 0xffff;",
  "  uVar2 = FUN_004537d8(param_1,param_2);\n  puVar1 = (undefined2 *)uVar2;\n  if (puVar1 == (undefined2 *)0x0) {\n    puVar1 = (undefined2 *)FUN_0045f1ff(1,0x3c);\n    if (puVar1 == (undefined2 *)0x0) {\n      return 0;\n    }\n    memset(puVar1,0,0x3c);\n  }\n  *puVar1 = 0xffff;"
);
source = source.replace(
  "      piVar5 = (int *)(_DAT_006366a0 + iVar4 * 2);",
  "      piVar5 = (int *)((byte *)(uintptr_t)_DAT_006366a0 + iVar4 * 2);"
);
source = source.replace(
  "    puVar18 = (ushort *)(*(int *)(in_EAX + 6) * 2);\n    local_2c = (int *)(_DAT_006366a0 + (int)puVar18);",
  "    puVar18 = (ushort *)(*(int *)(in_EAX + 6) * 2);\n    local_2c = (int *)((byte *)(uintptr_t)_DAT_006366a0 + (uintptr_t)puVar18);"
);
source = source.replace(
  "  uVar2 = FUN_0045384c(param_1,param_2);\n  puVar1 = (undefined2 *)uVar2;\n  *puVar1 = 0xffff;",
  "  uVar2 = FUN_0045384c(param_1,param_2);\n  puVar1 = (undefined2 *)uVar2;\n  if (puVar1 == (undefined2 *)0x0) {\n    puVar1 = (undefined2 *)FUN_0045f1ff(1,0x14);\n    if (puVar1 == (undefined2 *)0x0) {\n      return 0;\n    }\n    memset(puVar1,0,0x14);\n  }\n  *puVar1 = 0xffff;"
);
source = source.replace(
  "    uVar10 = FUN_004269d4(uVar8,uVar7);\n    psVar6 = (short *)uVar10;\n    uVar10 = FUN_004173c8(extraout_ECX_06,(int)((ulonglong)uVar10 >> 0x20));",
  "    uVar10 = FUN_004269d4(uVar8,uVar7);\n    psVar6 = (short *)uVar10;\n    if (psVar6 == (short *)0x0) {\n      return;\n    }\n    uVar10 = FUN_004173c8(extraout_ECX_06,(int)((ulonglong)uVar10 >> 0x20));"
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
    "        result = E2R_ParseArchiveRepResource((short)rep_id);\n        if (result == 0) {\n          result = E2R_ParseArchiveFanResource();\n        }\n        DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51998.archive\",(uintptr_t)saved_current);"
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
source = source.replace(
  "          FUN_0044248c(DAT_0047a470,in_EAX);\n          uVar4 = FUN_0043cbb4(extraout_ECX_06);\n          DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51a54.archive_missing\",\n                                                    (uintptr_t)extraout_ECX_07);\n          return CONCAT44(param_2,(int)uVar4);",
  "          E2R_GameStateLog(\"sound archive missing ignored id=%d archive=0x%x current=0x%lx scene=0x%lx\",\n                           (int)(short)in_EAX,(unsigned int)uVar1,\n                           (unsigned long)DAT_0047a470,(unsigned long)_DAT_0073cc3c);\n          DAT_0047a470 = E2R_TraceCurrentActorWrite(\"51a54.archive_missing\",\n                                                    (uintptr_t)uVar3);\n          return CONCAT44(param_2,0);"
);
source = source.replace(
  "            E2R_TraceSceneChildActivate(\"52140.loaded-after-load\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n            E2R_actor_calc_context = (int)(uintptr_t)psVar4;",
  "            E2R_TraceSceneChildActivate(\"52140.loaded-after-load\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n            if (psVar4[0x42] == 0 && psVar4[0x43] == 0 && psVar4[0x44] == 0 &&\n                (psVar4[0x4e] != 0 || psVar4[0x4f] != 0 || psVar4[0x50] != 0)) {\n              FUN_0044146c();\n            }\n            E2R_actor_calc_context = (int)(uintptr_t)psVar4;"
);
source = source.replace(
  "  if (in_EAX == (short *)0x0) {\n    FUN_00414e68();\n    param_1 = extraout_ECX;\n    param_2 = extraout_EDX;\n  }\n  FUN_00441e38(param_1,param_2);",
  "  in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,0xa8)) {\n    return;\n  }\n  FUN_00441e38((undefined4)(int)*in_EAX,param_2);"
);
source = source.replace(
  "  *(undefined4 *)(*in_EAX * 4 + 0x62e450) = 0;\n  FUN_0043aa98();",
  "  *(undefined4 *)(*in_EAX * 4 + 0x62e450) = 0;\n  E2R_scene_remove_context = in_EAX;\n  FUN_0043aa98();\n  E2R_scene_remove_context = (short *)0x0;"
);
source = source.replace(
  "  undefined4 extraout_ECX_04;\n  undefined8 uVar3;\n  \n  iVar2 = (int)(short)param_2;\n  iVar1 = iVar2 * 4;",
  "  undefined4 extraout_ECX_04;\n  undefined8 uVar3;\n  E2R_SceneGridSnapshot grid_snapshot;\n  short *saved_current;\n  \n  iVar2 = (int)(short)param_2;\n  iVar1 = iVar2 * 4;\n  memset(&grid_snapshot,0,sizeof(grid_snapshot));\n  saved_current = DAT_0047a470;"
);
source = source.replace(
  "  undefined4 extraout_ECX_04;\n  undefined8 uVar3;\n  undefined1 local_58 [60];\n  undefined1 local_1c;\n  \n  iVar2 = (int)in_AX;\n  iVar1 = iVar2 * 4;",
  "  undefined4 extraout_ECX_04;\n  undefined8 uVar3;\n  undefined1 local_58 [60];\n  short *saved_current;\n  undefined1 local_1c;\n  \n  iVar2 = (int)in_AX;\n  iVar1 = iVar2 * 4;\n  saved_current = DAT_0047a470;"
);
source = source.replace(
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.direct\",(uintptr_t)extraout_ECX_00);",
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.direct\",(uintptr_t)saved_current);"
);
source = source.replace(
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.missing\",(uintptr_t)extraout_ECX_02);",
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.missing\",(uintptr_t)saved_current);"
);
source = source.replace(
  "DAT_0047a470 = E2R_TraceArchiveCurrentActorWrite(\"5233c.archive\",(uintptr_t)extraout_ECX_04);",
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.archive\",(uintptr_t)saved_current);"
);
source = source.replace(
  "  undefined8 uVar3;\n\n  short *saved_current;\n  \n  iVar2 = (int)(short)param_2;",
  "  undefined8 uVar3;\n  E2R_SceneGridSnapshot grid_snapshot;\n\n  short *saved_current;\n  \n  memset(&grid_snapshot,0,sizeof(grid_snapshot));\n  iVar2 = (int)(short)param_2;"
);
source = source.replace(
  "      FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x650fa0));\n      iVar2 = E2R_ParseArchiveFanResource();\n      DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.archive\",(uintptr_t)saved_current);",
  "      if (E2R_RuntimeDiagEnabled() && E2R_scene_load_diag_count < 128) {\n        E2R_scene_load_diag_count = E2R_scene_load_diag_count + 1;\n        fprintf(stderr,\"scene load enter: id=%d offset=%d action_op=%lu cursor=0x%lx\\n\",\n                iVar2,*(int *)(iVar1 + 0x650fa0),\n                (unsigned long)E2R_action_last_opcode,\n                (unsigned long)E2R_action_last_cursor);\n      }\n      grid_snapshot = E2R_CaptureSceneGridSnapshot();\n      FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x650fa0));\n      iVar2 = E2R_ParseArchiveFanResource();\n      E2R_RestoreSceneGridSnapshot(&grid_snapshot);\n      if (E2R_RuntimeDiagEnabled() && E2R_scene_load_diag_count < 128) {\n        E2R_scene_load_diag_count = E2R_scene_load_diag_count + 1;\n        fprintf(stderr,\"scene load exit: id=%d result=%d action_count=%lu\\n\",\n                (int)(short)param_2,iVar2,\n                (unsigned long)E2R_action_opcode_count);\n      }\n      DAT_0047a470 = E2R_TraceCurrentActorWrite(\"5233c.archive\",(uintptr_t)saved_current);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045233c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?  undefined8 uVar3;\r?\n)/,
  "$1  E2R_SceneGridSnapshot grid_snapshot;\n"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045233c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?  E2R_SceneGridSnapshot grid_snapshot;\r?\n)/,
  "$1  short *saved_current;\n"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045233c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?  iVar1 = iVar2 \* 4;\r?\n)/,
  "$1  memset(&grid_snapshot,0,sizeof(grid_snapshot));\n"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045233c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?  memset\(&grid_snapshot,0,sizeof\(grid_snapshot\)\);\r?\n)/,
  "$1  saved_current = DAT_0047a470;\n"
);
source = source.replace(
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"525f0.direct\",(uintptr_t)extraout_ECX_00);",
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"525f0.direct\",(uintptr_t)saved_current);"
);
source = source.replace(
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"525f0.missing\",(uintptr_t)extraout_ECX_02);",
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"525f0.missing\",(uintptr_t)saved_current);"
);
source = source.replace(
  "DAT_0047a470 = E2R_TraceArchiveCurrentActorWrite(\"525f0.archive\",(uintptr_t)extraout_ECX_04);",
  "DAT_0047a470 = E2R_TraceCurrentActorWrite(\"525f0.archive\",(uintptr_t)saved_current);"
);
source = source.replace(
  "  uVar2 = FUN_0045233c(extraout_ECX,extraout_EDX);",
  "  uVar2 = FUN_0045233c(extraout_ECX,param_2);"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045233c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\n)  short in_AX;\n  int iVar2;/,
  "$1  int iVar2;"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045233c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\n)  iVar2 = \(int\)in_AX;\n  iVar1 = iVar2 \* 4;/,
  "$1  iVar2 = (int)(short)param_2;\n  iVar1 = iVar2 * 4;"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045233c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?  undefined4 extraout_ECX_04;\r?\n  undefined8 uVar3;\r?\n\s*)iVar2 = \(int\)\(short\)param_2;\r?\n  iVar1 = iVar2 \* 4;\r?\n  if \(\*\(int \*\)\(iVar1 \+ 0x62e450\) == 0\) \{/,
  "$1short *saved_current;\n\n  iVar2 = (int)(short)param_2;\n  iVar1 = iVar2 * 4;\n  saved_current = DAT_0047a470;\n  if (*(int *)(iVar1 + 0x62e450) == 0) {"
);
source = source.replace(
  "          FUN_0045233c(puVar13,puVar18);",
  "          FUN_0045233c(puVar13,uVar7);"
);
source = source.replace(
  "      case 0x48:\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 0x9c4) {\n          uVar24 = FUN_0043a6e0(puVar13,puVar18);",
  "      case 0x48:\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 0x9c4) {\n          uVar19 = (uint)(short)(*(ushort *)((int)local_2c + 2) & 0xfff);\n          uVar24 = FUN_0043a6e0(puVar13,uVar19);"
);
source = source.replace(
  "      case 0x4d:\n        local_12 = CONCAT22(*(ushort *)((int)local_2c + 2),(undefined2)local_12) & 0xfffffff;\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 0x9c4) {\n          uVar24 = FUN_0045233c(puVar13,puVar18);",
  "      case 0x4d:\n        local_12 = CONCAT22(*(ushort *)((int)local_2c + 2),(undefined2)local_12) & 0xfffffff;\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 0x9c4) {\n          uVar24 = FUN_0045233c(puVar13,(int)((uint)local_12 >> 0x10));"
);
source = source.replace(
  /if \(E2R_(actor_current_diag_count|actor_load_diag_count|actor_loop_diag_count|actor_update_diag_count|current_actor_trace_diag_count|frame_stage_diag_count|requester_state_diag_count|scene_pointer_diag_count|start_game_stage_diag_count) < ([0-9]+)\)/g,
  "if (E2R_RuntimeDiagEnabled() && E2R_$1 < $2)"
);
source = source.replace(
  /if \(value != 0 && E2R_current_actor_trace_diag_count < ([0-9]+) &&/g,
  "if (value != 0 && E2R_RuntimeDiagEnabled() && E2R_current_actor_trace_diag_count < $1 &&"
);
source = source.replace(
  /if \(E2R_scene_pointer_diag_count < ([0-9]+) &&/g,
  "if (E2R_RuntimeDiagEnabled() && E2R_scene_pointer_diag_count < $1 &&"
);
source = source.replace(
  /(undefined4 __fastcall FUN_00418a04\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?size_t span;\r?\n\s*)if \(1 < in_EAX\) \{/,
  "$1in_EAX = (int)(uintptr_t)param_1;\n  if (1 < in_EAX) {"
);
source = source.replace(
  /(\s+uVar25 = CONCAT44\(puVar18,_DAT_00ac4a54\);\r?\n)\s+switch\(\(int\)\(uintptr_t\)\(\(short\)\*local_2c\)\) \{/,
  "$1      E2R_action_opcode_count++;\n      E2R_action_last_opcode = (ushort)sVar9;\n      E2R_action_last_cursor = (uintptr_t)local_2c;\n      if (E2R_RuntimeDiagEnabled() &&\n          (E2R_action_opcode_count < 16 ||\n           (E2R_action_opcode_count & 0x1ffu) == 0)) {\n        fprintf(stderr,\"action opcode: ordinal=%lu cursor=0x%lx pool=0x%lx op=%04x next=%04x scene=0x%lx mode=%lu dispatch=%lu\\n\",\n                (unsigned long)E2R_action_opcode_count,\n                (unsigned long)(uintptr_t)local_2c,\n                (unsigned long)((byte *)(uintptr_t)local_2c - (byte *)(uintptr_t)_DAT_006366a0),\n                (unsigned int)(ushort)sVar9,\n                (unsigned int)*(ushort *)((int)local_2c + 2),\n                (unsigned long)_DAT_0073cc3c,(unsigned long)DAT_0047a76c,\n                (unsigned long)E2R_start_code_probe_dispatches);\n      }\n      if ((ushort)sVar9 == 0x75) {\n        E2R_action_hit_75_count++;\n      }\n      switch((int)(uintptr_t)((short)*local_2c)) {"
);

// Keep the startup-preload frontier observable without enabling the broad runtime
// diagnostics used by older crash hunts.
source = source.replace(
  "static uint E2R_action_invoke_diag_count;\nstatic uint E2R_scene_lookup_diag_count;\nstatic const char *E2R_current_actor_last_site;",
  "static uint E2R_action_invoke_diag_count;\nstatic uint E2R_scene_lookup_diag_count;\nstatic uint E2R_action_advance_diag_count;\nstatic uint E2R_scene_child_diag_count;\nstatic uint E2R_scene_select_diag_count;\nstatic uint E2R_scene_child_activate_diag_count;\nstatic uint E2R_rand_seed_fallback = 0x2a13f00d;\nstatic int E2R_startup_diag_enabled;\nstatic int E2R_scene_load_request_id = -1;\nstatic short *E2R_scene_remove_context;\nstatic int E2R_cleanup_context;\nstatic uint E2R_startup_action_diag_count;\nstatic uint E2R_startup_preload_diag_count;\nstatic uint E2R_scene_record_install_diag_count;\nstatic uint E2R_scene_grid_restore_diag_count;\nstatic uint E2R_script_scene_diag_count;\nstatic const char *E2R_current_actor_last_site;"
);
source = source.replace(
  "static uint E2R_action_invoke_diag_count;\nstatic uint E2R_scene_child_diag_count;",
  "static uint E2R_action_invoke_diag_count;\nstatic uint E2R_action_advance_diag_count;\nstatic uint E2R_scene_child_diag_count;"
);
source = source.replace(
  "static uint E2R_action_advance_diag_count;\nstatic uint E2R_scene_child_diag_count;",
  "static uint E2R_action_advance_diag_count;\nstatic uint E2R_scene_child_diag_count;\nstatic uint E2R_scene_select_diag_count;"
);
source = source.replace(
  "static uint E2R_scene_select_diag_count;\nstatic int E2R_startup_diag_enabled;",
  "static uint E2R_scene_select_diag_count;\nstatic uint E2R_scene_child_activate_diag_count;\nstatic uint E2R_rand_seed_fallback = 0x2a13f00d;\nstatic int E2R_startup_diag_enabled;"
);
source = source.replace(
  "  char *fan_diag = getenv(\"E2R_FAN_DIAG\");\n  char *runtime_diag = getenv(\"E2R_RUNTIME_DIAG\");\n\n  if (runtime_diag != (char *)0x0 && runtime_diag[0] != '\\0' && runtime_diag[0] != '0') {\n    E2R_runtime_diag_enabled = 1;\n  }",
  "  char *fan_diag = getenv(\"E2R_FAN_DIAG\");\n  char *runtime_diag = getenv(\"E2R_RUNTIME_DIAG\");\n  char *startup_diag = getenv(\"E2R_STARTUP_DIAG\");\n  char *game_state_log = getenv(\"E2R_GAME_STATE_LOG\");\n\n  if (runtime_diag != (char *)0x0 && runtime_diag[0] != '\\0' && runtime_diag[0] != '0') {\n    E2R_runtime_diag_enabled = 1;\n  }\n#ifndef NDEBUG\n  E2R_game_state_log_enabled =\n      game_state_log == (char *)0x0 || game_state_log[0] == '\\0' ||\n      game_state_log[0] != '0';\n#else\n  E2R_game_state_log_enabled =\n      game_state_log != (char *)0x0 && game_state_log[0] != '\\0' &&\n      game_state_log[0] != '0';\n#endif\n  if (startup_diag != (char *)0x0 && startup_diag[0] != '\\0' && startup_diag[0] != '0') {\n    E2R_startup_diag_enabled = 1;\n  }"
);
source = source.replace(
  "static int E2R_RuntimeDiagEnabled(void)\n{\n  return E2R_runtime_diag_enabled;\n}\n\ntypedef struct E2R_SceneGridSnapshot",
  "static int E2R_RuntimeDiagEnabled(void)\n{\n  return E2R_runtime_diag_enabled;\n}\n\nstatic int E2R_GameStateLogEnabled(void)\n{\n  return E2R_game_state_log_enabled;\n}\n\nstatic void E2R_GameStateLog(const char *format,...)\n{\n  va_list ap;\n\n  if (!E2R_GameStateLogEnabled() || 512 <= E2R_game_state_log_count) {\n    return;\n  }\n  E2R_game_state_log_count = E2R_game_state_log_count + 1;\n  fprintf(stderr,\"game state: \");\n  va_start(ap,format);\n  vfprintf(stderr,format,ap);\n  va_end(ap);\n  fprintf(stderr,\"\\n\");\n}\n\nstatic int E2R_StartupDiagEnabled(void)\n{\n  return E2R_startup_diag_enabled || E2R_runtime_diag_enabled;\n}\n\nstatic int E2R_ShouldTraceStartupProgress(uint count,uint first,uint interval)\n{\n  return count <= first || (interval != 0 && (count % interval) == 0);\n}\n\nstatic int E2R_NormalizeSceneListNode(int scene)\n{\n  if (scene == 0 || IsBadReadPtr((void *)(uintptr_t)scene,0xc)) {\n    return 0;\n  }\n  return scene;\n}\n\nstatic int E2R_SceneListNext(int scene)\n{\n  int next;\n\n  scene = E2R_NormalizeSceneListNode(scene);\n  if (scene == 0) {\n    return 0;\n  }\n  next = *(int *)(scene + 8);\n  if (next == scene) {\n    return 0;\n  }\n  return E2R_NormalizeSceneListNode(next);\n}\n\ntypedef struct E2R_SceneGridSnapshot"
);
source = source.replace(
  "static int E2R_StartupDiagEnabled(void)\n{\n  return E2R_startup_diag_enabled || E2R_runtime_diag_enabled;\n}\n\nstatic int E2R_ShouldTraceStartupProgress",
  "static int E2R_ActionDiagEnabled(void)\n{\n  static int initialized;\n  static int enabled;\n  char *value;\n\n  if (!initialized) {\n    value = getenv(\"E2R_ACTION_DIAG\");\n    enabled = value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n    initialized = 1;\n  }\n  return enabled;\n}\n\nstatic void E2R_TraceActionAdvance(const char *site,int actor,int *slot,uint delta,uint next)\n{\n  if (!E2R_ActionDiagEnabled() || 256 <= E2R_action_advance_diag_count) {\n    return;\n  }\n  E2R_action_advance_diag_count = E2R_action_advance_diag_count + 1;\n  fprintf(stderr,\n          \"action advance: %s actor=0x%lx slot=0x%lx action=0x%lx \"\n          \"duration=%u progress=%u delta=%u next=%u slot_flags=0x%x actor_flags=0x%x scene=0x%lx\\n\",\n          site,(unsigned long)(uintptr_t)actor,(unsigned long)(uintptr_t)slot,\n          (unsigned long)(uintptr_t)*slot,(unsigned int)*(ushort *)(slot + 1),\n          (unsigned int)*(ushort *)((int)slot + 6),delta,next,\n          (unsigned int)*(byte *)((int)slot + 0xc),\n          (unsigned int)*(byte *)(actor + 3),(unsigned long)_DAT_0073cc3c);\n}\n\nstatic int E2R_StartupDiagEnabled(void)\n{\n  return E2R_startup_diag_enabled || E2R_runtime_diag_enabled;\n}\n\nstatic int E2R_ShouldTraceStartupProgress"
);
source = source.replace(
  /static void E2R_TraceActionAdvance\(const char \*site,int actor,int \*slot,uint delta,uint next\)\n\{[\s\S]*?\n\}\n\nstatic int E2R_StartupDiagEnabled/,
  "static void E2R_TraceActionAdvance(const char *site,int actor,int *slot,uint delta,uint next)\n{\n  uint duration;\n  uint progress;\n  uint actor_flags = 0;\n\n  if (!E2R_ActionDiagEnabled() || 256 <= E2R_action_advance_diag_count ||\n      slot == (int *)0x0 || (uintptr_t)slot < 0x10000u || IsBadReadPtr(slot,0x12) ||\n      *slot == 0 || (uintptr_t)*slot < 0x10000u ||\n      IsBadReadPtr((void *)(uintptr_t)*slot,0x12)) {\n    return;\n  }\n  duration = (uint)*(ushort *)(slot + 1);\n  progress = (uint)*(ushort *)((int)slot + 6);\n  if (DAT_00636850 == '\\0' && progress < duration - 16) {\n    return;\n  }\n  if (actor != 0 && 0x10000u <= (uintptr_t)actor &&\n      !IsBadReadPtr((void *)(uintptr_t)actor,4)) {\n    actor_flags = (uint)*(byte *)(actor + 3);\n  }\n  E2R_action_advance_diag_count = E2R_action_advance_diag_count + 1;\n  fprintf(stderr,\n          \"action advance: %s actor=0x%lx slot=0x%lx action=0x%lx \"\n          \"duration=%u progress=%u delta=%u next=%u slot_flags=0x%x actor_flags=0x%x scene=0x%lx space=%u\\n\",\n          site,(unsigned long)(uintptr_t)actor,(unsigned long)(uintptr_t)slot,\n          (unsigned long)(uintptr_t)*slot,duration,progress,delta,next,\n          (unsigned int)*(byte *)((int)slot + 0xc),actor_flags,\n          (unsigned long)_DAT_0073cc3c,(unsigned int)(byte)DAT_00636850);\n}\n\nstatic int E2R_StartupDiagEnabled"
);
source = source.replace(
  "static uint E2R_scene_child_activate_diag_count;\nstatic uint E2R_rand_seed_fallback = 0x2a13f00d;",
  "static uint E2R_scene_child_activate_diag_count;\nstatic int E2R_start_sc_handoff_pending;\nstatic int E2R_start_sc_handoff_activate_current;\nstatic uint E2R_rand_seed_fallback = 0x2a13f00d;"
);
source = source.replace(
  "static int E2R_ShouldForceScene785Fallback(void)\n{",
  "static void E2R_MarkStartScHandoffIfNeeded(short *actor,int *slot)\n{\n  if (actor == (short *)0x0 || slot == (int *)0x0 ||\n      IsBadReadPtr(actor,2) || IsBadReadPtr(slot,4)) {\n    return;\n  }\n  if (*actor != 0 || *slot != 0x9377e3 ||\n      E2R_CurrentSceneTableSlot((uintptr_t)_DAT_0073cc3c) != 175) {\n    return;\n  }\n  E2R_start_sc_handoff_pending = 1;\n  E2R_GameStateLog(\"start-sc handoff pending actor=0x%lx action=0x%lx scene=0x%lx\",\n                   (unsigned long)(uintptr_t)actor,\n                   (unsigned long)(uintptr_t)*slot,\n                   (unsigned long)_DAT_0073cc3c);\n}\n\nstatic short E2R_AdjustStartScHandoffScene(short selected_scene)\n{\n  int current_slot;\n\n  if (E2R_start_sc_handoff_pending == 0) {\n    return selected_scene;\n  }\n  E2R_start_sc_handoff_pending = 0;\n  current_slot = E2R_CurrentSceneTableSlot((uintptr_t)_DAT_0073cc3c);\n  if (current_slot == 175 && selected_scene == 87 &&\n      DAT_0047a470 != 0 && !IsBadReadPtr((void *)(uintptr_t)DAT_0047a470,2) &&\n      *(short *)(uintptr_t)DAT_0047a470 == 0) {\n    E2R_GameStateLog(\"start-sc handoff preserve scene current=%d selected=%d actor=0x%lx\",\n                     current_slot,(int)selected_scene,\n                     (unsigned long)DAT_0047a470);\n    E2R_start_sc_handoff_activate_current = 1;\n    return (short)current_slot;\n  }\n  E2R_start_sc_handoff_activate_current = 0;\n  E2R_GameStateLog(\"start-sc handoff pass current=%d selected=%d actor=0x%lx\",\n                   current_slot,(int)selected_scene,(unsigned long)DAT_0047a470);\n  return selected_scene;\n}\n\nstatic int E2R_ShouldForceScene785Fallback(void)\n{"
);
source = source.replace(
  "  sVar2 = (short)uVar3;\n  if (E2R_scene_select_diag_count < 64 && (E2R_RuntimeDiagEnabled() || sVar2 < 1)) {",
  "  sVar2 = (short)uVar3;\n  sVar2 = E2R_AdjustStartScHandoffScene(sVar2);\n  if (E2R_scene_select_diag_count < 64 && (E2R_RuntimeDiagEnabled() || sVar2 < 1)) {"
);
source = source.replace(
  "  if ((undefined1 *)0x0067c728 + sVar2 * 0x1c == _DAT_0073cc3c) {\n    return;\n  }\n  if (sVar2 < 1) {",
  "  if ((undefined1 *)0x0067c728 + sVar2 * 0x1c == _DAT_0073cc3c) {\n    if (E2R_start_sc_handoff_activate_current != 0) {\n      E2R_start_sc_handoff_activate_current = 0;\n      E2R_GameStateLog(\"start-sc handoff activate preserved scene=%d actor=0x%lx\",\n                       (int)sVar2,(unsigned long)DAT_0047a470);\n      E2R_ActivateSelectedSceneRecord(sVar2);\n    }\n    return;\n  }\n  E2R_start_sc_handoff_activate_current = 0;\n  if (sVar2 < 1) {"
);
source = source.replace(
  "                       (unsigned int)*(ushort *)((int)in_EAX + 6),\n                       (unsigned int)*(ushort *)(in_EAX + 1),\n                       (unsigned long)_DAT_0073cc3c);\n      E2R_actor_calc_context = param_2;",
  "                       (unsigned int)*(ushort *)((int)in_EAX + 6),\n                       (unsigned int)*(ushort *)(in_EAX + 1),\n                       (unsigned long)_DAT_0073cc3c);\n      E2R_MarkStartScHandoffIfNeeded((short *)(uintptr_t)param_2,in_EAX);\n      E2R_actor_calc_context = param_2;"
);
source = source.replace(
  "static int E2R_SceneListNext(int scene)\n{\n  int next;\n\n  scene = E2R_NormalizeSceneListNode(scene);\n  if (scene == 0) {\n    return 0;\n  }\n  next = *(int *)(scene + 8);\n  if (next == scene) {\n    return 0;\n  }\n  return E2R_NormalizeSceneListNode(next);\n}\n\ntypedef struct E2R_SceneGridSnapshot",
  "static int E2R_SceneListNext(int scene)\n{\n  int next;\n\n  scene = E2R_NormalizeSceneListNode(scene);\n  if (scene == 0) {\n    return 0;\n  }\n  next = *(int *)(scene + 8);\n  if (next == scene) {\n    return 0;\n  }\n  return E2R_NormalizeSceneListNode(next);\n}\n\nstatic int E2R_NormalizeSceneRecordPointer(int scene)\n{\n  short scene_id;\n\n  if ((uint)scene < 0x10000u || 0x70000000u <= (uint)scene ||\n      IsBadReadPtr((void *)(uintptr_t)scene,0xa8)) {\n    return 0;\n  }\n  scene_id = *(short *)(uintptr_t)scene;\n  if (scene_id < 0 || 0x9c4 <= scene_id) {\n    return 0;\n  }\n  if (*(int *)(scene_id * 4 + 0x62e450) != scene) {\n    return 0;\n  }\n  return scene;\n}\n\ntypedef struct E2R_SceneGridSnapshot"
);
source = source.replace(
  "static int E2R_NormalizeSceneRecordPointer(int scene)\n{\n  short scene_id;\n\n  if ((uint)scene < 0x10000u || 0x70000000u <= (uint)scene ||\n      IsBadReadPtr((void *)(uintptr_t)scene,0xa8)) {\n    return 0;\n  }\n  scene_id = *(short *)(uintptr_t)scene;\n  if (scene_id < 0 || 0x9c4 <= scene_id) {\n    return 0;\n  }\n  if (*(int *)(scene_id * 4 + 0x62e450) != scene) {\n    return 0;\n  }\n  return scene;\n}\n\ntypedef struct E2R_SceneGridSnapshot",
  "static int E2R_NormalizeSceneRecordPointer(int scene)\n{\n  short scene_id;\n\n  if ((uint)scene < 0x10000u || 0x70000000u <= (uint)scene ||\n      IsBadReadPtr((void *)(uintptr_t)scene,0xa8)) {\n    return 0;\n  }\n  scene_id = *(short *)(uintptr_t)scene;\n  if (scene_id < 0 || 0x9c4 <= scene_id) {\n    return 0;\n  }\n  if (*(int *)(scene_id * 4 + 0x62e450) != scene) {\n    return 0;\n  }\n  return scene;\n}\n\nstatic void E2R_TraceSceneChildren(const char *stage,short *scene)\n{\n  char *scene_child_diag;\n  short *child;\n  uintptr_t actor;\n  uintptr_t actor_next;\n  uintptr_t actor_dep;\n  uintptr_t actor_scene;\n  uint guard;\n  short scene_id;\n\n  scene_child_diag = getenv(\"E2R_SCENE_CHILD_DIAG\");\n  if ((!E2R_RuntimeDiagEnabled() &&\n       (scene_child_diag == (char *)0x0 || scene_child_diag[0] == '\\0' ||\n        scene_child_diag[0] == '0')) || scene == (short *)0x0 ||\n      IsBadReadPtr(scene,0xa8) || E2R_scene_child_diag_count >= 128) {\n    return;\n  }\n  scene_id = *scene;\n  if (_DAT_0073cc3c != 0 && (uintptr_t)scene != (uintptr_t)_DAT_0073cc3c && scene_id != 1564) {\n    return;\n  }\n  E2R_scene_child_diag_count = E2R_scene_child_diag_count + 1;\n  fprintf(stderr,\n          \"scene children: %s scene=%d ptr=0x%lx child_head=0x%lx active_next=0x%lx current=0x%lx actor_head=0x%lx\\n\",\n          stage,(int)scene_id,(unsigned long)(uintptr_t)scene,\n          (unsigned long)*(int *)(scene + 2),(unsigned long)*(int *)(scene + 0x4e),\n          (unsigned long)_DAT_0073cc3c,(unsigned long)_DAT_0063726c);\n  guard = 0;\n  for (child = *(short **)(scene + 2);\n       child != (short *)0x0 && guard < 32 && !IsBadReadPtr(child,0x1c) &&\n       E2R_scene_child_diag_count < 128; child = *(short **)(child + 0xc)) {\n    actor = 0;\n    actor_next = 0;\n    actor_dep = 0;\n    actor_scene = 0;\n    if (0 <= *child && *child < 5000) {\n      actor = *(uint *)((undefined1 *)0x00630b60 + *child * 4);\n      if (actor != 0 && !IsBadReadPtr((void *)actor,0x136)) {\n        actor_next = *(uint *)(actor + 0x4c);\n        actor_dep = *(uint *)(actor + 0xa6);\n        actor_scene = *(uint *)(actor + 0x132);\n      }\n    }\n    E2R_scene_child_diag_count = E2R_scene_child_diag_count + 1;\n    fprintf(stderr,\n            \"scene child: %s #%lu child=0x%lx actor_id=%d flags=0x%02x actions=0x%lx next=0x%lx table=0x%lx actor_next=0x%lx dep=0x%lx p132=0x%lx\\n\",\n            stage,(unsigned long)guard,(unsigned long)(uintptr_t)child,\n            (int)*child,(unsigned int)*(byte *)(child + 7),\n            (unsigned long)*(int *)(child + 3),(unsigned long)*(int *)(child + 0xc),\n            (unsigned long)actor,(unsigned long)actor_next,\n            (unsigned long)actor_dep,(unsigned long)actor_scene);\n    guard = guard + 1;\n  }\n}\n\ntypedef struct E2R_SceneGridSnapshot"
);
source = source.replace(
  "static void E2R_TraceSceneChildren(const char *stage,short *scene)\n{\n  char *scene_child_diag;\n  short *child;",
  "static char *E2R_PackedNameByIndex(char *table,uint capacity,short max_names,short index);\n\nstatic void E2R_TraceSceneChildren(const char *stage,short *scene)\n{\n  char *scene_child_diag;\n  char *actor_name;\n  short *child;"
);
source = source.replace(
  "  uintptr_t actor_scene;\n  uint guard;",
  "  uintptr_t actor_scene;\n  int actor_offset;\n  int rep_offset;\n  int scene_offset;\n  uint guard;"
);
source = source.replace(
  "    actor_dep = 0;\n    actor_scene = 0;\n    if (0 <= *child && *child < 5000) {\n      actor = *(uint *)((undefined1 *)0x00630b60 + *child * 4);",
  "    actor_dep = 0;\n    actor_scene = 0;\n    actor_offset = 0;\n    rep_offset = -1;\n    scene_offset = -1;\n    actor_name = (char *)0x0;\n    if (0 <= *child && *child < 5000) {\n      actor = *(uint *)((undefined1 *)0x00630b60 + *child * 4);\n      actor_offset = *(int *)(*child * 4 + 0x653840);\n      if (*child < 0x9c4) {\n        scene_offset = *(int *)(*child * 4 + 0x650fa0);\n      }\n      if (*child < 500) {\n        rep_offset = *(int *)(*child * 4 + 0x663a10);\n      }\n      actor_name = E2R_PackedNameByIndex(_DAT_006366b4,10000,5000,*child);"
);
source = source.replace(
  "            \"scene child: %s #%lu child=0x%lx actor_id=%d flags=0x%02x actions=0x%lx next=0x%lx table=0x%lx actor_next=0x%lx dep=0x%lx p132=0x%lx\\n\",\n            stage,(unsigned long)guard,(unsigned long)(uintptr_t)child,\n            (int)*child,(unsigned int)*(byte *)(child + 7),",
  "            \"scene child: %s #%lu child=0x%lx actor_id=%d actor_name=%s actor_offset=%ld scene_offset=%ld rep_offset=%ld flags=0x%02x actions=0x%lx next=0x%lx table=0x%lx actor_next=0x%lx dep=0x%lx p132=0x%lx\\n\",\n            stage,(unsigned long)guard,(unsigned long)(uintptr_t)child,\n            (int)*child,actor_name != (char *)0x0 ? actor_name : \"(null)\",\n            (long)actor_offset,(long)scene_offset,(long)rep_offset,\n            (unsigned int)*(byte *)(child + 7),"
);
source = source.replace(
  "  if (E2R_RuntimeDiagEnabled()) {\n    fprintf(stderr,\"scene grid restore: opcode=0x%lx count=%d bytes=%u\\n\",",
  "  if (E2R_StartupDiagEnabled() && E2R_scene_grid_restore_diag_count < 64) {\n    E2R_scene_grid_restore_diag_count = E2R_scene_grid_restore_diag_count + 1;\n    fprintf(stderr,\"scene grid restore: opcode=0x%lx count=%d bytes=%u\\n\","
);
source = source.replace(
  "\n\nstatic short *E2R_action_dispatch_node;",
  "\n\nstatic char *E2R_PackedNameByIndex(char *table,uint capacity,short max_names,short index)\n{\n  uint length;\n  uint offset = 0;\n  short item = 0;\n\n  if (index < 0 || max_names <= index || table == (char *)0x0 ||\n      IsBadReadPtr(table,1)) {\n    return (char *)0x0;\n  }\n  while (item < max_names && offset < capacity) {\n    for (length = 0; offset + length < capacity; length = length + 1) {\n      if (IsBadReadPtr(table + offset + length,1)) {\n        return (char *)0x0;\n      }\n      if (table[offset + length] == '\\0') {\n        break;\n      }\n    }\n    if (offset + length == capacity || length == 0) {\n      return (char *)0x0;\n    }\n    if (item == index) {\n      return table + offset;\n    }\n    offset = offset + length + 1;\n    item = item + 1;\n  }\n  return (char *)0x0;\n}\n\nstatic short *E2R_action_dispatch_node;"
);
source = source.replace(
  "static int E2R_ScriptDiagEnabled(void)\n{\n  char *value = getenv(\"E2R_SCRIPT_DIAG\");\n\n  return value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n}\n\nstatic short *E2R_FindActionCodeBySuffix",
  "static int E2R_ScriptDiagEnabled(void)\n{\n  char *value = getenv(\"E2R_SCRIPT_DIAG\");\n\n  return value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n}\n\nstatic void E2R_TraceStartupActionNode(const char *stage,uint guard,short *action,int match)\n{\n  char *name;\n  uint offset = 0;\n\n  if (!E2R_StartupDiagEnabled() || E2R_startup_action_diag_count >= 192) {\n    return;\n  }\n  if (!match && !E2R_ShouldTraceStartupProgress(guard,16,0x100)) {\n    return;\n  }\n  name = E2R_ActionCodeName(action);\n  if (action != (short *)0x0 && !IsBadReadPtr(action,0xe)) {\n    offset = *(uint *)(action + 3);\n  }\n  E2R_startup_action_diag_count = E2R_startup_action_diag_count + 1;\n  fprintf(stderr,\n          \"startup action: %s guard=%lu node=0x%lx name_index=%d name=%s \"\n          \"code=0x%x match=%d startup=%lu/%lu action=%lu/%lu dispatch=%lu\\n\",\n          stage,(unsigned long)guard,(unsigned long)(uintptr_t)action,\n          action != (short *)0x0 && !IsBadReadPtr(action,2) ? (int)(ushort)action[0] : -1,\n          name != (char *)0x0 ? name : \"(null)\",offset,match,\n          (unsigned long)E2R_start_code_probe_startup_scans,\n          (unsigned long)E2R_start_code_probe_startup_matches,\n          (unsigned long)E2R_start_code_probe_action_scans,\n          (unsigned long)E2R_start_code_probe_action_matches,\n          (unsigned long)E2R_start_code_probe_dispatches);\n}\n\nstatic void E2R_TraceScenePreload(const char *stage,uint token,uintptr_t scene,uintptr_t cursor,uint count)\n{\n  char *name;\n  byte flags = 0;\n\n  if (!E2R_StartupDiagEnabled() || E2R_startup_preload_diag_count >= 256) {\n    return;\n  }\n  if (stage[0] == 'c' && !E2R_ShouldTraceStartupProgress(count,16,0x80)) {\n    return;\n  }\n  name = E2R_PackedNameByIndex(_DAT_006366bc,20000,0x9c4,(short)token);\n  if (token < 0x9c4) {\n    flags = *(byte *)(token * 2 + 0x670c38);\n  }\n  E2R_startup_preload_diag_count = E2R_startup_preload_diag_count + 1;\n  fprintf(stderr,\n          \"startup preload: %s token=%04x name=%s scene=0x%lx cursor=0x%lx \"\n          \"child=%lu flags=0x%02x opcodes=%lu dispatch=%lu\\n\",\n          stage,(unsigned int)token,name != (char *)0x0 ? name : \"(null)\",\n          (unsigned long)scene,(unsigned long)cursor,(unsigned long)count,\n          (unsigned int)flags,(unsigned long)E2R_action_opcode_count,\n          (unsigned long)E2R_start_code_probe_dispatches);\n}\n\nstatic short *E2R_FindActionCodeBySuffix"
);
source = source.replace(
  "          (unsigned int)flags,(unsigned long)E2R_action_opcode_count,\n          (unsigned long)E2R_start_code_probe_dispatches);\n}\n\nstatic short *E2R_FindActionCodeBySuffix",
  `          (unsigned int)flags,(unsigned long)E2R_action_opcode_count,
          (unsigned long)E2R_start_code_probe_dispatches);
}

static void E2R_TraceScriptSceneOpcode(const char *stage,uint opcode,uint token,uintptr_t cursor)
{
  char *name;
  int offset = -1;
  uintptr_t slot = 0;
  byte flags = 0;

  if (!E2R_ScriptDiagEnabled() || E2R_script_scene_diag_count >= 64) {
    return;
  }
  token = token & 0xfff;
  if (token < 0x9c4) {
    name = E2R_PackedNameByIndex(_DAT_006366bc,20000,0x9c4,(short)token);
    offset = *(int *)(token * 4 + 0x650fa0);
    slot = *(int *)(token * 4 + 0x62e450);
    flags = *(byte *)(token * 2 + 0x670c38);
  }
  else {
    name = (char *)0x0;
  }
  E2R_script_scene_diag_count = E2R_script_scene_diag_count + 1;
  fprintf(stderr,
          "script scene: %s op=%04x token=%04x name=%s slot=0x%lx offset=%d "
          "flags=0x%02x current_scene=0x%lx current_actor=0x%lx cursor=0x%lx "
          "opcodes=%lu dispatch=%lu\\n",
          stage,(unsigned int)opcode,(unsigned int)token,
          name != (char *)0x0 ? name : "(null)",(unsigned long)slot,offset,
          (unsigned int)flags,(unsigned long)_DAT_0073cc3c,
          (unsigned long)DAT_0047a470,(unsigned long)cursor,
          (unsigned long)E2R_action_opcode_count,
          (unsigned long)E2R_start_code_probe_dispatches);
}

static void E2R_TraceSceneRecordInstall(const char *stage,short *record,short *source)
{
  int requested;
  int record_id = -1;
  int source_id = -1;
  int source_type = -1;
  int requested_slot = 0;
  int record_slot = 0;
  int offset = -1;
  char *requested_name;
  char *record_name;

  if (!E2R_StartupDiagEnabled() || E2R_scene_record_install_diag_count >= 128) {
    return;
  }
  requested = E2R_scene_load_request_id;
  if (record != (short *)0x0 && !IsBadReadPtr(record,0xa8)) {
    record_id = (int)(ushort)record[0];
    record_slot = *(int *)(record_id * 4 + 0x62e450);
  }
  if (source != (short *)0x0 && !IsBadReadPtr(source,4)) {
    source_id = (int)(ushort)source[0];
    source_type = (int)(ushort)source[1];
  }
  if (requested >= 0 && requested < 0x9c4) {
    requested_slot = *(int *)(requested * 4 + 0x62e450);
    offset = *(int *)(requested * 4 + 0x650fa0);
  }
  requested_name = E2R_PackedNameByIndex(_DAT_006366bc,20000,0x9c4,(short)requested);
  record_name = E2R_PackedNameByIndex(_DAT_006366bc,20000,0x9c4,(short)record_id);
  E2R_scene_record_install_diag_count = E2R_scene_record_install_diag_count + 1;
  fprintf(stderr,
          "scene record %s: requested=%d/%s offset=%d record=%d/%s ptr=0x%lx "
          "requested_slot=0x%lx record_slot=0x%lx source=%d type=%04x action_ref=%d "
          "action_op=%lu opcodes=%lu\\n",
          stage,requested,requested_name != (char *)0x0 ? requested_name : "(null)",
          offset,record_id,record_name != (char *)0x0 ? record_name : "(null)",
          (unsigned long)(uintptr_t)record,(unsigned long)requested_slot,
          (unsigned long)record_slot,source_id,source_type,
          record != (short *)0x0 && !IsBadReadPtr(record,0x9c) ? (int)record[0x4d] : -1,
          (unsigned long)E2R_action_last_opcode,
          (unsigned long)E2R_action_opcode_count);
}

static short *E2R_FindActionCodeBySuffix`
);
source = source.replace(
  "  if (E2R_RuntimeDiagEnabled() && E2R_start_game_stage_diag_count < 64) {",
  "  if (E2R_StartupDiagEnabled() && E2R_start_game_stage_diag_count < 64) {"
);
source = source.replace(
  "  if (_DAT_0063725c != 0) {\n    if (in_EAX == _DAT_0063725c) {",
  "  if (E2R_scene_remove_context != (short *)0x0) {\n    in_EAX = (int)(uintptr_t)E2R_scene_remove_context;\n  }\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xa8)) {\n    return;\n  }\n  if (_DAT_0063725c != 0) {\n    if (in_EAX == _DAT_0063725c) {"
);
source = source.replace(
  "      if (E2R_RuntimeDiagEnabled() &&\n          (E2R_action_opcode_count < 16 ||",
  "      if (E2R_StartupDiagEnabled() &&\n          (E2R_action_opcode_count < 16 ||"
);
source = source.replace(
  /if \(E2R_RuntimeDiagEnabled\(\) && E2R_scene_load_diag_count < 128\)/g,
  "if (E2R_StartupDiagEnabled() && E2R_scene_load_diag_count < 128)"
);
source = source.replace(
  "        fprintf(stderr,\"scene load exit: id=%d result=%d action_count=%lu\\n\",\n                (int)(short)param_2,iVar2,\n                (unsigned long)E2R_action_opcode_count);",
  "        fprintf(stderr,\"scene load exit: id=%d result=%d table=0x%lx action_count=%lu\\n\",\n                (int)(short)param_2,iVar2,\n                (unsigned long)*(int *)((int)(short)param_2 * 4 + 0x62e450),\n                (unsigned long)E2R_action_opcode_count);"
);
source = source.replace(
  "      grid_snapshot = E2R_CaptureSceneGridSnapshot();\n      FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x650fa0));\n      iVar2 = E2R_ParseArchiveFanResource();\n      E2R_RestoreSceneGridSnapshot(&grid_snapshot);",
  "      grid_snapshot = E2R_CaptureSceneGridSnapshot();\n      E2R_scene_load_request_id = (int)(short)param_2;\n      FUN_0045f296(DAT_0047a470,*(int *)(iVar1 + 0x650fa0));\n      iVar2 = E2R_ParseArchiveFanResource();\n      E2R_scene_load_request_id = -1;\n      E2R_RestoreSceneGridSnapshot(&grid_snapshot);"
);
source = source.replace(
  "      E2R_start_code_probe_startup_scans++;\n      if (E2R_ActionCodeMatches((short *)(uintptr_t)iVar1,s_StartUp_004725ec)) {",
  "      E2R_start_code_probe_startup_scans++;\n      E2R_TraceStartupActionNode(\"startup-scan\",action_guard,(short *)(uintptr_t)iVar1,0);\n      if (E2R_ActionCodeMatches((short *)(uintptr_t)iVar1,s_StartUp_004725ec)) {"
);
source = source.replace(
  "        E2R_start_code_probe_startup_matches++;\n        E2R_TraceStartGameStage(\"before-startup-action\");",
  "        E2R_start_code_probe_startup_matches++;\n        E2R_TraceStartupActionNode(\"startup-match\",action_guard,(short *)(uintptr_t)iVar1,1);\n        E2R_TraceStartGameStage(\"before-startup-action\");"
);
source = source.replace(
  "    E2R_start_code_probe_action_scans++;\n    action_guard = action_guard + 1;",
  "    E2R_start_code_probe_action_scans++;\n    E2R_TraceStartupActionNode(\"start-scan\",action_guard,(short *)(uintptr_t)iVar1,0);\n    action_guard = action_guard + 1;"
);
source = source.replace(
  "      E2R_start_code_probe_action_matches++;\n      E2R_TraceStartGameStage(\"before-list-action\");",
  "      E2R_start_code_probe_action_matches++;\n      E2R_TraceStartupActionNode(\"start-match\",action_guard,(short *)(uintptr_t)iVar1,1);\n      E2R_TraceStartGameStage(\"before-list-action\");"
);
source = source.replace(
  "      case 0x4d:\n        local_12 = CONCAT22(*(ushort *)((int)local_2c + 2),(undefined2)local_12) & 0xfffffff;\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 0x9c4) {\n          uVar24 = FUN_0045233c(puVar13,(int)((uint)local_12 >> 0x10));\n          puVar3 = *(ushort **)(((int)local_12 >> 0x10) * 4 + 0x62e450);",
  "      case 0x4d:\n        local_12 = CONCAT22(*(ushort *)((int)local_2c + 2),(undefined2)local_12) & 0xfffffff;\n        preload_token = (uint)local_12 >> 0x10;\n        E2R_TraceScenePreload(\"enter\",preload_token,0,(uintptr_t)local_2c,0);\n        if ((*(ushort *)((int)local_2c + 2) & 0xfff) < 0x9c4) {\n          uVar24 = FUN_0045233c(puVar13,(int)((uint)local_12 >> 0x10));\n          puVar3 = *(ushort **)(((int)local_12 >> 0x10) * 4 + 0x62e450);\n          E2R_TraceScenePreload(\"after-load\",preload_token,(uintptr_t)puVar3,(uintptr_t)local_2c,0);"
);
source = source.replace(
  "          if (puVar3 != (ushort *)0x0) {\n            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {",
  "          if (puVar3 != (ushort *)0x0) {\n            preload_child_guard = 0;\n            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {\n              preload_child_guard = preload_child_guard + 1;\n              E2R_TraceScenePreload(\"child-reset\",preload_token,(uintptr_t)puVar3,\n                                    (uintptr_t)psVar16,preload_child_guard);"
);
source = source.replace(
  "            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {",
  "            preload_child_guard = 0;\n            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {\n              preload_child_guard = preload_child_guard + 1;\n              E2R_TraceScenePreload(\"child-actions\",preload_token,(uintptr_t)puVar3,\n                                    (uintptr_t)psVar16,preload_child_guard);"
);
source = source.replace(
  "            *(int *)(puVar3 + 0x50) = _DAT_00636588 + -1;\n            puVar18 = puVar3;",
  "            E2R_TraceScenePreload(\"done\",preload_token,(uintptr_t)puVar3,(uintptr_t)local_2c,0);\n            *(int *)(puVar3 + 0x50) = _DAT_00636588 + -1;\n            puVar18 = puVar3;"
);
source = source.replace(
  "            preload_child_guard = 0;\n            preload_child_guard = 0;\n            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {\n              preload_child_guard = preload_child_guard + 1;\n              E2R_TraceScenePreload(\"child-actions\",preload_token,(uintptr_t)puVar3,\n                                    (uintptr_t)psVar16,preload_child_guard);\n              preload_child_guard = preload_child_guard + 1;\n              E2R_TraceScenePreload(\"child-reset\",preload_token,(uintptr_t)puVar3,\n                                    (uintptr_t)psVar16,preload_child_guard);",
  "            preload_child_guard = 0;\n            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {\n              preload_child_guard = preload_child_guard + 1;\n              E2R_TraceScenePreload(\"child-reset\",preload_token,(uintptr_t)puVar3,\n                                    (uintptr_t)psVar16,preload_child_guard);"
);
source = source.replace(
  "            }\n            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {\n              if ((*(int *)(psVar16 + 3) != 0) &&",
  "            }\n            preload_child_guard = 0;\n            for (psVar16 = *(short **)(puVar3 + 2); psVar16 != (short *)0x0;\n                psVar16 = *(short **)(psVar16 + 0xc)) {\n              preload_child_guard = preload_child_guard + 1;\n              E2R_TraceScenePreload(\"child-actions\",preload_token,(uintptr_t)puVar3,\n                                    (uintptr_t)psVar16,preload_child_guard);\n              if ((*(int *)(psVar16 + 3) != 0) &&"
);
source = source.replace(
  /void FUN_0043aa14\(void\)\r?\n\r?\n\{[\s\S]*?\r?\n\}\r?\n\r?\n\r?\n\r?\n\/\* 0043aa98 \*\//,
`void FUN_0043aa14(void)

{
  short *psVar1;
  int iVar2;
  int next_item;
  uint guard;
  short *in_EAX;
  int extraout_EDX;

  if (in_EAX == (short *)0x0 || IsBadReadPtr(in_EAX,0x10)) {
    return;
  }
  if (_DAT_00637270 != (short *)0x0) {
    if (in_EAX == _DAT_00637270) {
      _DAT_00637270 = *(short **)(_DAT_00637270 + 4);
    }
    else {
      iVar2 = *(int *)(_DAT_00637270 + 4);
      psVar1 = _DAT_00637270;
      while (iVar2 != 0) {
        if (in_EAX == *(short **)(psVar1 + 4)) {
          *(undefined4 *)(psVar1 + 4) = *(undefined4 *)(*(short **)(psVar1 + 4) + 4);
          break;
        }
        psVar1 = *(short **)(psVar1 + 4);
        iVar2 = *(int *)(psVar1 + 4);
      }
    }
  }
  iVar2 = *(int *)(in_EAX + 2);
  guard = 0;
  while (iVar2 != 0 && guard < 0x4000 &&
         !IsBadReadPtr((void *)(uintptr_t)iVar2,6)) {
    next_item = *(int *)(iVar2 + 2);
    E2R_cleanup_context = iVar2;
    FUN_0043ab38();
    E2R_cleanup_context = 0;
    if (next_item == iVar2) {
      break;
    }
    iVar2 = next_item;
    guard = guard + 1;
  }
  *(undefined4 *)((undefined1 *)0x0062ba20 + *in_EAX * 4) = 0;
  E2R_cleanup_context = (int)(uintptr_t)in_EAX;
  FUN_00453330();
  E2R_cleanup_context = 0;
  return;
}



/* 0043aa98 */`
);
source = source.replace(
  /void FUN_0043aa98\(void\)\r?\n\r?\n\{[\s\S]*?\r?\n\}\r?\n\r?\n\r?\n\r?\n\/\* 0043ab38 \*\//,
`void FUN_0043aa98(void)

{
  int iVar1;
  int iVar2;
  int in_EAX;
  int current_child;
  int next_item;
  uint guard;
  uint item_guard;

  if (E2R_scene_remove_context != (short *)0x0) {
    in_EAX = (int)(uintptr_t)E2R_scene_remove_context;
  }
  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xa8)) {
    return;
  }
  _DAT_0063725c = (short *)(uintptr_t)E2R_NormalizeSceneListNode((int)(uintptr_t)_DAT_0063725c);
  if (_DAT_0063725c != 0) {
    if (in_EAX == _DAT_0063725c) {
      _DAT_0063725c = (short *)(uintptr_t)E2R_SceneListNext((int)(uintptr_t)_DAT_0063725c);
    }
    else {
      iVar2 = E2R_SceneListNext((int)(uintptr_t)_DAT_0063725c);
      iVar1 = (int)(uintptr_t)_DAT_0063725c;
      guard = 0;
      while (iVar2 != 0 && guard < 0x1000 &&
             !IsBadReadPtr((void *)(uintptr_t)iVar1,0xc)) {
        if (in_EAX == *(int *)(iVar1 + 8)) {
          *(undefined4 *)(iVar1 + 8) = E2R_SceneListNext(*(int *)(iVar1 + 8));
          break;
        }
        iVar1 = E2R_SceneListNext(iVar1);
        guard = guard + 1;
        if (iVar1 == 0 || IsBadReadPtr((void *)(uintptr_t)iVar1,0xc)) {
          break;
        }
        iVar2 = E2R_SceneListNext(iVar1);
      }
    }
  }
  iVar2 = *(int *)(in_EAX + 4);
  guard = 0;
  while (iVar2 != 0 && guard < 0x4000 &&
         !IsBadReadPtr((void *)(uintptr_t)iVar2,0x1c)) {
    current_child = iVar2;
    iVar1 = *(int *)(iVar2 + 0x18);
    iVar2 = *(int *)(iVar2 + 6);
    item_guard = 0;
    while (iVar2 != 0 && item_guard < 0x4000 &&
           !IsBadReadPtr((void *)(uintptr_t)iVar2,6)) {
      next_item = *(int *)(iVar2 + 2);
      E2R_cleanup_context = iVar2;
      FUN_0043ab38();
      E2R_cleanup_context = 0;
      if (next_item == iVar2) {
        break;
      }
      iVar2 = next_item;
      item_guard = item_guard + 1;
    }
    E2R_cleanup_context = current_child;
    FUN_004533a4();
    E2R_cleanup_context = 0;
    iVar2 = iVar1;
    guard = guard + 1;
  }
  E2R_cleanup_context = in_EAX;
  FUN_0045357c();
  E2R_cleanup_context = 0;
  return;
}



/* 0043ab38 */`
);
source = source.replace(
  /void FUN_0043ab38\(void\)\r?\n\r?\n\{[\s\S]*?\r?\n\}\r?\n\r?\n\r?\n\r?\n\/\* 0043ab74 \*\//,
`void FUN_0043ab38(void)

{
  int iVar1;
  int in_EAX;
  int next_item;
  uint guard;

  if (E2R_cleanup_context != 0) {
    in_EAX = E2R_cleanup_context;
  }
  if (in_EAX != 0) {
    if (IsBadReadPtr((void *)(uintptr_t)in_EAX,0xe)) {
      return;
    }
    iVar1 = *(int *)(in_EAX + 6);
    guard = 0;
    while (iVar1 != 0 && guard < 0x4000 &&
           !IsBadReadPtr((void *)(uintptr_t)iVar1,0xe)) {
      next_item = *(int *)(iVar1 + 10);
      E2R_cleanup_context = iVar1;
      FUN_00453264();
      E2R_cleanup_context = in_EAX;
      if (next_item == iVar1) {
        break;
      }
      iVar1 = next_item;
      guard = guard + 1;
    }
    iVar1 = *(int *)(in_EAX + 10);
    guard = 0;
    while (iVar1 != 0 && guard < 0x4000 &&
           !IsBadReadPtr((void *)(uintptr_t)iVar1,0x11)) {
      next_item = *(int *)(iVar1 + 0xd);
      FUN_0045f9b5();
      if (next_item == iVar1) {
        break;
      }
      iVar1 = next_item;
      guard = guard + 1;
    }
    E2R_cleanup_context = in_EAX;
    FUN_0045374c();
  }
  return;
}



/* 0043ab74 */`
);
source = source.replace(
  "undefined4 FUN_00453264(void)\n\n{\n  if (E2R_fan_parse_record != (short *)0x0 &&",
  "undefined4 FUN_00453264(void)\n\n{\n  if (E2R_cleanup_context != 0 &&\n      !IsBadReadPtr((void *)(uintptr_t)E2R_cleanup_context,4)) {\n    *(undefined2 *)(E2R_cleanup_context + 2) = 0x8000;\n    return 0;\n  }\n  if (E2R_fan_parse_record != (short *)0x0 &&"
);
source = source.replace(
  /void FUN_004533a4\(void\)\s*\r?\n\s*\{\s*\r?\n\s*int in_EAX;\s*\r?\n\s*\*\(undefined1 \*\)\(in_EAX \+ 0x1c\) = 0x80;\s*\r?\n\s*return;\s*\r?\n\s*\}/,
  "void FUN_004533a4(void)\n\n{\n  int in_EAX;\n\n  if (E2R_cleanup_context != 0) {\n    in_EAX = E2R_cleanup_context;\n  }\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x1d)) {\n    return;\n  }\n  *(undefined1 *)(in_EAX + 0x1c) = 0x80;\n  return;\n}"
);
source = source.replace(
  /void FUN_0045357c\(void\)\s*\r?\n\s*\{\s*\r?\n\s*int in_EAX;\s*\r?\n\s*\*\(undefined2 \*\)\(in_EAX \+ 0x96\) = 0x8000;\s*\r?\n\s*return;\s*\r?\n\s*\}/,
  "void FUN_0045357c(void)\n\n{\n  int in_EAX;\n\n  if (E2R_cleanup_context != 0) {\n    in_EAX = E2R_cleanup_context;\n  }\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0x98)) {\n    return;\n  }\n  *(undefined2 *)(in_EAX + 0x96) = 0x8000;\n  return;\n}"
);
source = source.replace(
  /void FUN_0045374c\(void\)\s*\r?\n\s*\{\s*\r?\n\s*int in_EAX;\s*\r?\n\s*\*\(undefined1 \*\)\(in_EAX \+ 0xe\) = 0x80;\s*\r?\n\s*return;\s*\r?\n\s*\}/,
  "void FUN_0045374c(void)\n\n{\n  int in_EAX;\n\n  if (E2R_cleanup_context != 0) {\n    in_EAX = E2R_cleanup_context;\n  }\n  if (in_EAX == 0 || IsBadReadPtr((void *)(uintptr_t)in_EAX,0xf)) {\n    return;\n  }\n  *(undefined1 *)(in_EAX + 0xe) = 0x80;\n  return;\n}"
);
source = source.replace(
  "      *(int *)(node + 0x08) = (int)(uintptr_t)_DAT_0063725c;",
  "      *(int *)(node + 0x08) = E2R_NormalizeSceneListNode((int)(uintptr_t)_DAT_0063725c);"
);
source = source.replace(
  "  if (in_EAX == _DAT_0063725c) {\n    _DAT_0063725c = *(short **)(_DAT_0063725c + 4);\n  }\n  else {\n    psVar2 = *(short **)(_DAT_0063725c + 4);\n    psVar1 = _DAT_0063725c;\n    while (in_EAX != psVar2) {\n      psVar1 = *(short **)(psVar1 + 4);\n      psVar2 = *(short **)(psVar1 + 4);\n    }\n    *(undefined4 *)(psVar1 + 4) = *(undefined4 *)(in_EAX + 4);\n  }",
  "  _DAT_0063725c = (short *)(uintptr_t)E2R_NormalizeSceneListNode((int)(uintptr_t)_DAT_0063725c);\n  if (in_EAX == _DAT_0063725c) {\n    _DAT_0063725c = (short *)(uintptr_t)E2R_SceneListNext((int)(uintptr_t)_DAT_0063725c);\n  }\n  else {\n    psVar2 = (short *)(uintptr_t)E2R_SceneListNext((int)(uintptr_t)_DAT_0063725c);\n    psVar1 = _DAT_0063725c;\n    while (psVar1 != (short *)0x0 && in_EAX != psVar2) {\n      psVar1 = (short *)(uintptr_t)E2R_SceneListNext((int)(uintptr_t)psVar1);\n      psVar2 = (short *)(uintptr_t)E2R_SceneListNext((int)(uintptr_t)psVar1);\n    }\n    if (psVar1 != (short *)0x0) {\n      *(undefined4 *)(psVar1 + 4) = E2R_SceneListNext((int)(uintptr_t)in_EAX);\n    }\n  }"
);
source = source.replace(
  "  for (iVar1 = _DAT_0063725c; iVar1 != 0; iVar1 = *(int *)(iVar1 + 8)) {",
  "  _DAT_0063725c = (short *)(uintptr_t)E2R_NormalizeSceneListNode((int)(uintptr_t)_DAT_0063725c);\n  for (iVar1 = (int)(uintptr_t)_DAT_0063725c; iVar1 != 0; iVar1 = E2R_SceneListNext(iVar1)) {"
);
source = source.replace(
  "  for (iVar4 = _DAT_0063725c; iVar3 = _DAT_00637270, iVar4 != 0; iVar4 = *(int *)(iVar4 + 8)) {",
  "  _DAT_0063725c = (short *)(uintptr_t)E2R_NormalizeSceneListNode((int)(uintptr_t)_DAT_0063725c);\n  for (iVar4 = (int)(uintptr_t)_DAT_0063725c; iVar3 = _DAT_00637270, iVar4 != 0; iVar4 = E2R_SceneListNext(iVar4)) {"
);
source = source.replace(
  "              FUN_00452140(extraout_ECX_06);",
  "              FUN_00452140((undefined4)(uintptr_t)*(int *)((short)((ulonglong)uVar24 >> 0x20) * 4 + 0x62e450));"
);
source = source.replace(
  "        uVar19 = CONCAT22(uVar20,*(short *)((int)local_2c + 2)) & 0xffff0fff;\n        if (((ushort)uVar19 < 0x9c4)",
  "        uVar19 = CONCAT22(uVar20,*(short *)((int)local_2c + 2)) & 0xffff0fff;\n        E2R_TraceScriptSceneOpcode(\"op07-enter\",0x7,uVar19,(uintptr_t)local_2c);\n        if (((ushort)uVar19 < 0x9c4)"
);
source = source.replace(
  "          uVar24 = FUN_0045233c(puVar13,uVar19);\n          if (*(int *)((short)((ulonglong)uVar24 >> 0x20) * 4 + 0x62e450) == 0) {",
  "          uVar24 = FUN_0045233c(puVar13,uVar19);\n          E2R_TraceScriptSceneOpcode(\"op07-after-load\",0x7,(uint)((ulonglong)uVar24 >> 0x20),\n                                     (uintptr_t)local_2c);\n          if (*(int *)((short)((ulonglong)uVar24 >> 0x20) * 4 + 0x62e450) == 0) {"
);
source = source.replace(
  "              FUN_00452140((undefined4)(uintptr_t)*(int *)((short)((ulonglong)uVar24 >> 0x20) * 4 + 0x62e450));\n              FUN_004523f8((undefined4)(uintptr_t)_DAT_0073cc3c);",
  "              FUN_00452140((undefined4)(uintptr_t)*(int *)((short)((ulonglong)uVar24 >> 0x20) * 4 + 0x62e450));\n              FUN_004523f8((undefined4)(uintptr_t)*(int *)((short)((ulonglong)uVar24 >> 0x20) * 4 + 0x62e450));\n              E2R_TraceScriptSceneOpcode(\"op07-after-activate\",0x7,\n                                         (uint)((ulonglong)uVar24 >> 0x20),\n                                         (uintptr_t)local_2c);"
);
source = source.replace(
  "              FUN_00452140(extraout_ECX_11);\n              FUN_004523f8((undefined4)(uintptr_t)_DAT_0073cc3c);",
  "              FUN_00452140((undefined4)(uintptr_t)*(int *)((short)uVar7 * 4 + 0x62e450));\n              FUN_004523f8((undefined4)(uintptr_t)*(int *)((short)uVar7 * 4 + 0x62e450));"
);
source = source.replace(
  "        uVar7 = *(ushort *)((int)local_2c + 2) & 0xfff;\n        if (uVar7 < 0x9c4) {",
  "        uVar7 = *(ushort *)((int)local_2c + 2) & 0xfff;\n        E2R_TraceScriptSceneOpcode(\"op0c-enter\",0xc,uVar7,(uintptr_t)local_2c);\n        if (uVar7 < 0x9c4) {"
);
source = source.replace(
  "              FUN_00452140((undefined4)(uintptr_t)*(int *)((short)uVar7 * 4 + 0x62e450));\n              FUN_004523f8((undefined4)(uintptr_t)*(int *)((short)uVar7 * 4 + 0x62e450));\n              puVar13 = extraout_ECX_12;",
  "              FUN_00452140((undefined4)(uintptr_t)*(int *)((short)uVar7 * 4 + 0x62e450));\n              FUN_004523f8((undefined4)(uintptr_t)*(int *)((short)uVar7 * 4 + 0x62e450));\n              E2R_TraceScriptSceneOpcode(\"op0c-after-activate\",0xc,uVar7,\n                                         (uintptr_t)local_2c);\n              puVar13 = extraout_ECX_12;"
);
source = source.replace(
  "        FUN_00452140(extraout_ECX_11);\n        uVar9 = extraout_ECX_12;",
  "        FUN_00452140((undefined4)(uintptr_t)*(int *)((short)uVar18 * 4 + 0x62e450));\n        uVar9 = extraout_ECX_12;"
);
source = source.replace(
  "  ushort *extraout_EDX_01;\n  undefined8 uVar8;\n\n  uVar5 = DAT_0047a470;",
  "  ushort *extraout_EDX_01;\n  uint guard;\n  undefined8 uVar8;\n\n  uVar5 = DAT_0047a470;"
);
source = source.replace(
  "  uVar5 = DAT_0047a470;\n  if (in_EAX != 0) {\n    for (psVar3 = *(short **)(in_EAX + 4); psVar3 != (short *)0x0;\n        psVar3 = *(short **)(psVar3 + 0xc)) {\n      if ((*(byte *)(psVar3 + 7) & 0x20) == 0) {",
  "  uVar5 = DAT_0047a470;\n  in_EAX = E2R_NormalizeSceneRecordPointer(in_EAX);\n  if (in_EAX == 0) {\n    in_EAX = E2R_NormalizeSceneRecordPointer((int)(uintptr_t)param_1);\n  }\n  if (in_EAX == 0) {\n    in_EAX = E2R_NormalizeSceneRecordPointer(_DAT_0073cc3c);\n  }\n  if (in_EAX != 0) {\n    E2R_TraceSceneChildren(\"52140.enter\",(short *)(uintptr_t)in_EAX);\n    guard = 0;\n    for (psVar3 = *(short **)(in_EAX + 4);\n        psVar3 != (short *)0x0 && guard < 0x4000 &&\n        !IsBadReadPtr(psVar3,0x1c); psVar3 = *(short **)(psVar3 + 0xc)) {\n      guard = guard + 1;\n      if ((*(byte *)(psVar3 + 7) & 0x20) == 0) {"
);
source = source.replace(
  "      }\n    }\n  }\n  DAT_0047a470 = E2R_TraceCurrentActorWrite(\"52140.exit\",(uintptr_t)uVar5);",
  "      }\n    }\n    E2R_TraceSceneChildren(\"52140.exit\",(short *)(uintptr_t)in_EAX);\n  }\n  DAT_0047a470 = E2R_TraceCurrentActorWrite(\"52140.exit\",(uintptr_t)uVar5);"
);
source = source.replace(
  "}\n\ntypedef struct E2R_SceneGridSnapshot",
  "}\n\nstatic void E2R_TraceSceneChildActivate(const char *stage,int scene_id,short *child)\n{\n  char *scene_child_diag;\n  char *actor_name;\n  char *word2_name;\n  int actor_offset;\n  int actor_rep_offset;\n  int actor_scene_offset;\n  int word2_offset;\n  int word2_rep_offset;\n  int word2_scene_offset;\n  uintptr_t actor;\n  uintptr_t word2_actor;\n  short actor_id;\n  short word2_id;\n\n  scene_child_diag = getenv(\"E2R_SCENE_CHILD_DIAG\");\n  if ((!E2R_RuntimeDiagEnabled() &&\n       (scene_child_diag == (char *)0x0 || scene_child_diag[0] == '\\0' ||\n        scene_child_diag[0] == '0')) || child == (short *)0x0 ||\n      IsBadReadPtr(child,0x1c) || E2R_scene_child_activate_diag_count >= 192) {\n    return;\n  }\n  actor_id = *child;\n  word2_id = child[2];\n  actor = 0;\n  word2_actor = 0;\n  actor_offset = -1;\n  actor_rep_offset = -1;\n  actor_scene_offset = -1;\n  word2_offset = -1;\n  word2_rep_offset = -1;\n  word2_scene_offset = -1;\n  actor_name = (char *)0x0;\n  word2_name = (char *)0x0;\n  if (0 <= actor_id && actor_id < 5000) {\n    actor = *(uint *)((undefined1 *)0x00630b60 + actor_id * 4);\n    actor_offset = *(int *)(actor_id * 4 + 0x653840);\n    if (actor_id < 0x9c4) {\n      actor_scene_offset = *(int *)(actor_id * 4 + 0x650fa0);\n    }\n    if (actor_id < 500) {\n      actor_rep_offset = *(int *)(actor_id * 4 + 0x663a10);\n    }\n    actor_name = E2R_PackedNameByIndex(_DAT_006366b4,10000,5000,actor_id);\n  }\n  if (0 <= word2_id && word2_id < 5000) {\n    word2_actor = *(uint *)((undefined1 *)0x00630b60 + word2_id * 4);\n    word2_offset = *(int *)(word2_id * 4 + 0x653840);\n    if (word2_id < 0x9c4) {\n      word2_scene_offset = *(int *)(word2_id * 4 + 0x650fa0);\n    }\n    if (word2_id < 500) {\n      word2_rep_offset = *(int *)(word2_id * 4 + 0x663a10);\n    }\n    word2_name = E2R_PackedNameByIndex(_DAT_006366b4,10000,5000,word2_id);\n  }\n  E2R_scene_child_activate_diag_count = E2R_scene_child_activate_diag_count + 1;\n  fprintf(stderr,\n          \"scene child activate: %s scene=%d child=0x%lx actor=%d/%s actor_offset=%ld scene_offset=%ld rep_offset=%ld table=0x%lx word2=%d/%s actor_offset=%ld scene_offset=%ld rep_offset=%ld word2_table=0x%lx flags=0x%02x actions=0x%lx next=0x%lx DAT_0047ab10=%lu\\n\",\n          stage,scene_id,(unsigned long)(uintptr_t)child,\n          (int)actor_id,actor_name != (char *)0x0 ? actor_name : \"(null)\",\n          (long)actor_offset,(long)actor_scene_offset,(long)actor_rep_offset,\n          (unsigned long)actor,\n          (int)word2_id,word2_name != (char *)0x0 ? word2_name : \"(null)\",\n          (long)word2_offset,(long)word2_scene_offset,(long)word2_rep_offset,\n          (unsigned long)word2_actor,\n          (unsigned int)*(byte *)(child + 7),(unsigned long)*(int *)(child + 3),\n          (unsigned long)*(int *)(child + 0xc),(unsigned long)DAT_0047ab10);\n}\n\ntypedef struct E2R_SceneGridSnapshot"
);
source = source.replace(
  "                \"scene child record 1a: requested=%d scene=0x%lx node=0x%lx raw=%04x,%04x,%04x,%04x,%04x\\n\",\n                E2R_scene_load_request_id,(unsigned long)(uintptr_t)local_20,\n                (unsigned long)(uintptr_t)local_24,\n                (unsigned int)(ushort)psVar8[0],(unsigned int)(ushort)psVar8[1],\n                (unsigned int)(ushort)psVar8[2],(unsigned int)(ushort)psVar8[3],\n                (unsigned int)(ushort)psVar8[4]);",
  "                \"scene child record 1a: requested=%d scene=0x%lx node=0x%lx raw=%04x,%04x,%04x,%04x,%04x actor2=%d/%s/%ld actor4=%d/%s/%ld\\n\",\n                E2R_scene_load_request_id,(unsigned long)(uintptr_t)local_20,\n                (unsigned long)(uintptr_t)local_24,\n                (unsigned int)(ushort)psVar8[0],(unsigned int)(ushort)psVar8[1],\n                (unsigned int)(ushort)psVar8[2],(unsigned int)(ushort)psVar8[3],\n                (unsigned int)(ushort)psVar8[4],(int)psVar8[2],\n                E2R_PackedNameByIndex(_DAT_006366b4,10000,5000,psVar8[2]) != (char *)0x0 ?\n                E2R_PackedNameByIndex(_DAT_006366b4,10000,5000,psVar8[2]) : \"(null)\",\n                0 <= psVar8[2] && psVar8[2] < 5000 ?\n                (long)*(int *)(psVar8[2] * 4 + 0x653840) : -1L,(int)psVar8[4],\n                E2R_PackedNameByIndex(_DAT_006366b4,10000,5000,psVar8[4]) != (char *)0x0 ?\n                E2R_PackedNameByIndex(_DAT_006366b4,10000,5000,psVar8[4]) : \"(null)\",\n                0 <= psVar8[4] && psVar8[4] < 5000 ?\n                (long)*(int *)(psVar8[4] * 4 + 0x653840) : -1L);"
);
source = source.replace(
  "      if ((*(byte *)(psVar3 + 7) & 0x20) == 0) {\n        iVar1 = *psVar3 * 4;",
  "      if ((*(byte *)(psVar3 + 7) & 0x20) == 0) {\n        E2R_TraceSceneChildActivate(\"52140.child\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n        iVar1 = *psVar3 * 4;"
);
source = source.replace(
  "        if (*(int *)((undefined1 *)0x00630b60 + iVar1) == 0) {\n          if (DAT_0047ab10 == 0) {",
  "        if (*(int *)((undefined1 *)0x00630b60 + iVar1) == 0) {\n          E2R_TraceSceneChildActivate(\"52140.missing\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n          if (DAT_0047ab10 == 0) {\n            E2R_TraceSceneChildActivate(\"52140.missing-dat0\",(int)*(short *)(uintptr_t)in_EAX,psVar3);"
);
source = source.replace(
  "          else if (*(int *)(iVar1 + 0x653840) < 0) {\n            FUN_00441890(param_1,iVar1);",
  "          else if (*(int *)(iVar1 + 0x653840) < 0) {\n            E2R_TraceSceneChildActivate(\"52140.missing-no-archive\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n            continue;\n            FUN_00441890(param_1,iVar1);"
);
source = source.replace(
  "          else {\n            FUN_0045f296(param_1,*(int *)(iVar1 + 0x653840));",
  "          else {\n            E2R_TraceSceneChildActivate(\"52140.missing-archive\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n            FUN_0045f296(param_1,*(int *)(iVar1 + 0x653840));"
);
source = source.replace(
  "          if (psVar4 == (short *)0x0) {\n            FUN_00441890(uVar6,uVar7);",
  "          if (psVar4 == (short *)0x0) {\n            E2R_TraceSceneChildActivate(\"52140.unresolved-after-load\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n            FUN_00441890(uVar6,uVar7);"
);
source = source.replace(
  "          else {\n            E2R_actor_calc_context = (int)(uintptr_t)psVar4;",
  "          else {\n            E2R_TraceSceneChildActivate(\"52140.loaded-after-load\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n            if (psVar4[0x42] == 0 && psVar4[0x43] == 0 && psVar4[0x44] == 0 &&\n                (psVar4[0x4e] != 0 || psVar4[0x4f] != 0 || psVar4[0x50] != 0)) {\n              psVar4[0x42] = psVar4[0x4e];\n              psVar4[0x43] = psVar4[0x4f];\n              psVar4[0x44] = psVar4[0x50];\n              psVar4[0x41] = 6;\n              psVar4[0x75] = 0x7fff;\n              psVar4[0x76] = 0;\n              psVar4[0x77] = 0;\n            }\n            E2R_actor_calc_context = (int)(uintptr_t)psVar4;"
);
source = source.replace(
  "        if (*(int *)((undefined1 *)0x00630b60 + *psVar3 * 4) != 0) {\n          psVar4 = *(short **)((undefined1 *)0x00630b60 + *psVar3 * 4);",
  "        if (*(int *)((undefined1 *)0x00630b60 + *psVar3 * 4) != 0) {\n          E2R_TraceSceneChildActivate(\"52140.update\",(int)*(short *)(uintptr_t)in_EAX,psVar3);\n          psVar4 = *(short **)((undefined1 *)0x00630b60 + *psVar3 * 4);"
);
source = source.replace(
  "  ushort *extraout_EDX_01;\n  undefined8 uVar8;\n\n  uVar5 = DAT_0047a470;\n  in_EAX = E2R_NormalizeSceneRecordPointer(in_EAX);",
  "  ushort *extraout_EDX_01;\n  uint guard;\n  undefined8 uVar8;\n\n  uVar5 = DAT_0047a470;\n  in_EAX = E2R_NormalizeSceneRecordPointer(in_EAX);"
);
source = source.replace(
  "  ushort *extraout_EDX_01;\n  uint guard;\n  undefined8 uVar8;\n\n  uVar5 = DAT_0047a470;\n  in_EAX = E2R_NormalizeSceneRecordPointer(in_EAX);",
  "  ushort *extraout_EDX_01;\n  uint guard;\n  undefined8 uVar8;\n\n  uVar5 = DAT_0047a470;\n  in_EAX = E2R_NormalizeSceneRecordPointer(in_EAX);"
);
source = source.replace(
  "        FUN_0042b0f4();\n        *(byte *)(psVar4 + 1) = *(byte *)(psVar4 + 1) | 8;",
  "        E2R_actor_calc_context = (int)(uintptr_t)psVar4;\n        FUN_0042b0f4();\n        *(byte *)(psVar4 + 1) = *(byte *)(psVar4 + 1) | 8;"
);
source = source.replace(
  "        FUN_0042ad60(extraout_ECX,(int)psVar4);\n      }\n    }\n  }\n  return;",
  "        FUN_0042ad60(extraout_ECX,(int)psVar4);\n        E2R_actor_calc_context = 0;\n      }\n    }\n  }\n  return;"
);
source = source.replace(
  "  in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX != (short *)0x0 && !IsBadReadPtr(in_EAX,0x20)) {\n    pbVar1 = (byte *)(*in_EAX * 2 + 0x670c38);",
  "  in_EAX = (short *)(uintptr_t)param_1;\n  if (in_EAX != (short *)0x0 && !IsBadReadPtr(in_EAX,0x20)) {\n    E2R_TraceSceneChildren(\"523f8.enter\",in_EAX);\n    pbVar1 = (byte *)(*in_EAX * 2 + 0x670c38);"
);
source = source.replace(
  "        FUN_0042ad60(extraout_ECX,(int)psVar4);\n        E2R_actor_calc_context = 0;\n      }\n    }\n  }\n  return;",
  "        FUN_0042ad60(extraout_ECX,(int)psVar4);\n        E2R_actor_calc_context = 0;\n      }\n    }\n    E2R_TraceSceneChildren(\"523f8.exit\",in_EAX);\n  }\n  return;"
);
source = source.replace(
  /(\/\* 00452140 \*\/[\s\S]*?  ushort \*extraout_EDX_01;\r?\n)(  undefined8 uVar8;\r?\n\r?\n  uVar5 = DAT_0047a470;\r?\n  in_EAX = E2R_NormalizeSceneRecordPointer\(in_EAX\);)/,
  "$1  uint guard;\n$2"
);
source = source.replace(
  /  ushort \*extraout_EDX_01;\r?\n  undefined8 uVar8;\r?\n/g,
  "  ushort *extraout_EDX_01;\n  uint guard;\n  undefined8 uVar8;\n"
);
source = source.replace(
  /undefined8 __fastcall FUN_00441890\(undefined4 param_1,undefined4 param_2\)\r?\n\r?\n\{[\s\S]*?\r?\n\}\r?\n\r?\n\r?\n\r?\n\/\* 004418fc \*\//,
`undefined8 __fastcall FUN_00441890(undefined4 param_1,undefined4 param_2)

{
  char *pcVar2;
  short in_AX;
  int candidate;
  int length;
  short sVar5;

  in_AX = -1;
  candidate = (int)param_2;
  if (0 <= candidate && candidate < 5000 * 4 && (candidate & 3) == 0) {
    in_AX = (short)(candidate / 4);
  }
  else if (0 <= (short)param_2 && (short)param_2 < 5000) {
    in_AX = (short)param_2;
  }
  else if (0 <= (short)param_1 && (short)param_1 < 5000) {
    in_AX = (short)param_1;
  }
  if (in_AX < 0 || _DAT_006366b4 == (char *)0x0 || IsBadReadPtr(_DAT_006366b4,1)) {
    pcVar2 = &DAT_0047a710;
  }
  else {
    sVar5 = 0;
    pcVar2 = _DAT_006366b4;
    while (sVar5 < in_AX) {
      length = 0;
      while (length < 40000 && !IsBadReadPtr(pcVar2 + length,1) &&
             pcVar2[length] != '\\0') {
        length = length + 1;
      }
      if (length == 0 || length >= 40000 || IsBadReadPtr(pcVar2 + length,1)) {
        pcVar2 = &DAT_0047a710;
        break;
      }
      pcVar2 = pcVar2 + length + 1;
      sVar5 = sVar5 + 1;
    }
    length = 0;
    while (length < 40000 && !IsBadReadPtr(pcVar2 + length,1) &&
           pcVar2[length] != '\\0') {
      length = length + 1;
    }
    if (length >= 40000 || IsBadReadPtr(pcVar2 + length,1)) {
      pcVar2 = &DAT_0047a710;
    }
  }
  return CONCAT44(param_2,pcVar2);
}



/* 004418fc */`
);
source = source.replace(
  "\n\n\n/* 00410078 */",
  `\n\nstatic void E2R_RestartIntroSequence(void)
{
  uintptr_t slot;

  DAT_00636844 = 0;
  DAT_00636850 = 0;
  DAT_00479db4 = 0;
  DAT_0047a788 = 1;
  DAT_0047a76c = 1;
  _DAT_006443d0 = 1;
  E2R_WORD_AT(DAT_0047a45e,2) = 0;
  _DAT_00643650 = E2R_TraceRequesterState("action.restart_intro_complete",0);
  E2R_TraceStartGameStage("restart-intro-begin");
  if (E2R_IsReadableCurrentPointer(DAT_0047a470)) {
    slot = (uintptr_t)DAT_0047a470 + 0xa6;
    if (!IsBadReadPtr((void *)slot,0x12) && *(uintptr_t *)slot != 0) {
      *(undefined2 *)(slot + 6) = 0;
    }
  }
  E2R_TraceStartGameStage("restart-intro-end");
}\n\n\n/* 00410078 */`
);
source = source.replace(
  "  if (action == (uintptr_t)&LAB_0043d458) {\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.start_male\",0);\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d464) {\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.start_female\",1);\n    return 1;\n  }",
  "  if (action == (uintptr_t)&LAB_0043d458) {\n    if (requester_id == 0x28 && DAT_0047a76c != 0) {\n      _DAT_006443d0 = 1;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.restart_intro\",7);\n      return 1;\n    }\n    _DAT_006443d0 = 1;\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.start_male\",0);\n    return 1;\n  }\n  if (action == (uintptr_t)&LAB_0043d464) {\n    if (requester_id == 0x28 && DAT_0047a76c != 0) {\n      _DAT_006443d0 = 1;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.restart_intro\",7);\n      return 1;\n    }\n    _DAT_006443d0 = 1;\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.start_female\",1);\n    return 1;\n  }"
);
source = source.replace(
  "    if (requester_id == 0x31) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings_ok\",0);\n      return 1;\n    }",
  "    if (requester_id == 0x31) {\n      _DAT_006443d0 = 1;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings_ok\",0);\n      E2R_WORD_AT(DAT_0047a45e,2) = 0;\n      return 1;\n    }"
);
source = source.replace(
  "    if (requester_id == 0x29 || requester_id == 0x2a) {\n      _DAT_0064353c = 0;\n      return 1;\n    }\n    if (requester_id == 0x31) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings_cancel\",0);\n      return 1;\n    }",
  "    if (requester_id == 0x29 || requester_id == 0x2a) {\n      _DAT_0064353c = 0;\n      _DAT_006443d0 = 1;\n      E2R_WORD_AT(DAT_0047a45e,2) = 0;\n      return 1;\n    }\n    if (requester_id == 0x31) {\n      _DAT_006443d0 = 1;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings_cancel\",0);\n      E2R_WORD_AT(DAT_0047a45e,2) = 0;\n      return 1;\n    }"
);
source = source.replace(
  "  if (action == (uintptr_t)&LAB_0043d470) {\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.load\",2);\n    return 1;\n  }",
  "  if (action == (uintptr_t)&LAB_0043d470) {\n    if (requester_id == 0x28) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings\",2);\n      FUN_0043ce58(0x31,5);\n      E2R_WORD_AT(DAT_0047a45e,2) = 0x28;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.settings_return\",5);\n      _DAT_006443d0 = 0;\n      _DAT_0064342c = 0;\n      DAT_00636844 = 0;\n      DAT_0047a788 = 1;\n      E2R_requester_continue_after_action = 1;\n      return 1;\n    }\n    _DAT_006443d0 = 1;\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.settings\",2);\n    return 1;\n  }"
);
source = source.replace(
  "  if (action == (uintptr_t)&LAB_0043d490) {\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.options\",4);\n    return 1;\n  }",
  "  if (action == (uintptr_t)&LAB_0043d490) {\n    if (requester_id == 0x28) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.load\",4);\n      FUN_0043ce58(0x29,5);\n      E2R_WORD_AT(DAT_0047a45e,2) = 0x28;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.load_return\",5);\n      _DAT_006443d0 = 0;\n      _DAT_0064342c = 0;\n      DAT_00636844 = 0;\n      DAT_0047a788 = 1;\n      E2R_requester_continue_after_action = 1;\n      return 1;\n    }\n    _DAT_006443d0 = 1;\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.load\",4);\n    return 1;\n  }"
);
source = source.replace(
  "  if (action == (uintptr_t)&DAT_0043d49c) {\n    uintptr_t prompt = 0x004729b8;\n    if (DAT_00479e00 != 0 && !IsBadReadPtr((void *)0x0060aef0,4) &&\n        *(uintptr_t *)0x0060aef0 != 0) {\n      prompt = *(uintptr_t *)0x0060aef0;\n    }\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.quit_prompt\",\n                                            ((int)FUN_0043c910((undefined4)prompt,0) != 0) ? 6 : 5);\n    return 1;\n  }",
  "  if (action == (uintptr_t)&DAT_0043d49c) {\n    uintptr_t prompt = 0x004729b8;\n    int confirmed;\n    if (DAT_00479e00 != 0 && !IsBadReadPtr((void *)0x0060aef0,4) &&\n        *(uintptr_t *)0x0060aef0 != 0) {\n      prompt = *(uintptr_t *)0x0060aef0;\n    }\n    confirmed = (int)FUN_0043c910((undefined4)prompt,0) != 0;\n    if (requester_id == 0x28) {\n      if (confirmed) {\n        _DAT_006443d0 = 1;\n        E2R_WORD_AT(DAT_0047a45e,2) = 0;\n        _DAT_00643650 = E2R_TraceRequesterState(\"action.quit_confirmed\",6);\n        return 1;\n      }\n      E2R_WORD_AT(DAT_0047a45e,2) = 0x28;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.quit_return\",5);\n      _DAT_006443d0 = 0;\n      _DAT_0064342c = 0;\n      DAT_00636844 = 0;\n      DAT_0047a788 = 1;\n      E2R_requester_continue_after_action = 1;\n      return 1;\n    }\n    _DAT_006443d0 = 1;\n    _DAT_00643650 = E2R_TraceRequesterState(\"action.quit_prompt\",confirmed ? 6 : 5);\n    return 1;\n  }"
);
source = source.replace(
  "    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643dc4) {\n      _DAT_006443d2 = (_DAT_006443d2 & 0xffff) | 0x10000;\n      if (_DAT_00643430 == (short *)0x00643dc4) {\n        _DAT_00643650 = E2R_TraceRequesterState(\"action.confirm_yes\",6);\n      }\n      return 1;\n    }",
  "    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643dc4) {\n      _DAT_006443d2 = (_DAT_006443d2 & 0xffff) | 0x10000;\n      _DAT_006443d0 = 1;\n      E2R_WORD_AT(DAT_0047a45e,2) = 0;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.confirm_yes\",6);\n      return 1;\n    }"
);
source = source.replace(
  "    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643c84) {\n      _DAT_006443d2 = _DAT_006443d2 & 0xffff;\n      if (_DAT_00643430 == (short *)0x00643c84) {\n        _DAT_00643650 = E2R_TraceRequesterState(\"action.confirm_no\",5);\n      }\n      return 1;\n    }",
  "    if (requester_id == 0x14 || _DAT_00643430 == (short *)0x00643c84) {\n      _DAT_006443d2 = _DAT_006443d2 & 0xffff;\n      _DAT_006443d0 = 1;\n      E2R_WORD_AT(DAT_0047a45e,2) = 0;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.confirm_no\",5);\n      return 1;\n    }"
);
source = source.replace(
  "    if (requester_id == 0x27 || requester_id == 0x28) {\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.cancel_start\",5);\n      return 1;\n    }",
  "    if (requester_id == 0x27 || requester_id == 0x28) {\n      _DAT_006443d0 = 1;\n      _DAT_00643650 = E2R_TraceRequesterState(\"action.cancel_start\",5);\n      return 1;\n    }"
);
source = source.replace(
  "  if (DAT_0047a470 != (short *)0x0) {\n    ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] = ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] | 2;\n  }",
  "  if (DAT_0047a470 != (short *)0x0 && E2R_IsReadableCurrentPointer(DAT_0047a470)) {\n    ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] = ((undefined1 *)0x0064a178)[*(undefined4 *)(uintptr_t)DAT_0047a470 * 2] | 2;\n  }"
);
source = source.replace(
  "  sVar2 = DAT_0047a34a;\n  piVar3 = (int *)(in_EAX + 0x112);",
  "  if ((uint)in_EAX < 0x10000u || 0x70000000u <= (uint)in_EAX ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x118)) {\n    return;\n  }\n  sVar2 = DAT_0047a34a;\n  piVar3 = (int *)(in_EAX + 0x112);"
);
source = source.replace(
  "      FUN_00421684();\n      *(byte *)(extraout_ECX_03 + 3) = *(byte *)(extraout_ECX_03 + 3) & 0xf7;\n      iVar5 = extraout_ECX_03;\n      iVar7 = extraout_EDX_03;",
  "      FUN_00421684();\n      if (0x10000u <= (uint)iVar5 && (uint)iVar5 < 0x70000000u &&\n          !IsBadReadPtr((void *)(uintptr_t)iVar5,0x50)) {\n        *(byte *)(iVar5 + 3) = *(byte *)(iVar5 + 3) & 0xf7;\n      }\n      iVar7 = extraout_EDX_03;"
);
source = source.replace(
  "    case 6:\n      DestroyWindow(_DAT_00ac4dac);\n    }",
  "    case 6:\n      DestroyWindow(_DAT_00ac4dac);\n      break;\n    case 7:\n      E2R_RestartIntroSequence();\n      break;\n    }"
);
source = source.replace(
  /undefined8 __fastcall FUN_0045fc10\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fc44 \*\//,
  "undefined8 __fastcall FUN_0045fc10(undefined4 param_1,undefined4 param_2)\n\n{\n  uint *puVar1;\n  uint uVar2;\n\n  (void)param_1;\n  puVar1 = (uint *)FUN_0045fc06();\n  if (puVar1 == (uint *)0x0 || (uintptr_t)puVar1 < 0x10000u ||\n      IsBadReadPtr(puVar1,4)) {\n    puVar1 = &E2R_rand_seed_fallback;\n  }\n  uVar2 = *puVar1 * 0x41c64e6d + 0x3039;\n  *puVar1 = uVar2;\n  uVar2 = uVar2 >> 0x10 & 0x7fff;\n  return CONCAT44(param_2,uVar2);\n}\n\n\n\n/* 0045fc44 */"
);
source = source.replace(
  "        uVar12 = FUN_0045fc10(0,unaff_ESI);\n        psVar7 = (short *)FUN_0042fce0(extraout_ECX_04,(int)((ulonglong)uVar12 >> 0x20),1);",
  "        uVar12 = FUN_0045fc10(0,unaff_ESI);\n        (void)uVar12;\n        psVar7 = (short *)FUN_0042fce0((int)in_EAX[3],(int)unaff_ESI,1);"
);
source = source.replace(
  "      if (*(int *)((int)uVar3 * 4 + 0x62d960) != 0) {",
  "      if (0 <= iVar2 && iVar2 < 5000 &&\n          *(int *)(iVar2 * 4 + 0x62d960) != 0) {"
);
source = source.replace(
  "  if (actor == 0 || (uintptr_t)actor < 0x10000u) {\n    return 0;\n  }\n  slot = (int *)(uintptr_t)(actor + 0xa6);",
  "  if (actor == 0 || (uintptr_t)actor < 0x10000u) {\n    if (_DAT_0073cc3c == 0) {\n      DAT_00636850 = '\\0';\n      E2R_GameStateLog(\"intro skip ignored wait-only subintro\");\n    }\n    return 0;\n  }\n  slot = (int *)(uintptr_t)(actor + 0xa6);"
);
source = source.replace(
  "  case 0x37:\n    psVar7 = (short *)(uint)(ushort)in_EAX[2];\n    param_2[0x91] = in_EAX[2];\n    if (in_EAX[3] != 0) {",
  "  case 0x37:\n    psVar7 = (short *)(uint)(ushort)in_EAX[2];\n    param_2[0x91] = in_EAX[2];\n    E2R_RetainCurrentRepForMissingTarget(\"2b880.case37\",param_2);\n    if (in_EAX[3] != 0) {"
);
source = source.replace(
  "static int E2R_ParseArchiveRepResource(short expected_rep_id)\n{",
  "static int E2R_RepRecordDiagEnabled(void)\n{\n  char *value = getenv(\"E2R_REP_RECORD_DIAG\");\n\n  return value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n}\n\nstatic int E2R_ParseArchiveRepResource(short expected_rep_id)\n{"
);
source = source.replace(
  "      slot = (int)field2 + 1;\n      if (0 <= slot && slot < 0xd1) {\n        rep[slot] = field3;\n        if (0x31 < _DAT_0067bc92 && 0x4f < field2 && field2 < 0x6b) {\n          rep[slot] = -1;\n        }\n      }\n      continue;",
  "      if (E2R_RepRecordDiagEnabled()) {\n        fprintf(stderr,\"rep archive record: rep=%d type=%04x field2=%d field3=%d slot=%d version=%d\\n\",\n                (int)*rep,(unsigned int)type,(int)field2,(int)field3,\n                (int)field2 + 1,(int)_DAT_0067bc92);\n      }\n      slot = (int)field2 + 1;\n      if (0 <= slot && slot < 0xd1) {\n        rep[slot] = field3;\n        if (0x31 < _DAT_0067bc92 && 0x4f < field2 && field2 < 0x6b) {\n          rep[slot] = -1;\n        }\n      }\n      continue;"
);
source = source.replace(
  /(\n\/\* 00441b24 \*\/[\s\S]*?undefined1 local_48 \[52\];\r?\n\r?\n)\s*if \(in_AX < 0\) \{/,
  "$1  in_AX = (short)param_2;\n  if (in_AX < 0) {"
);
source = source.replace(
  /(\n\/\* 0045190c \*\/[\s\S]*?undefined8 uVar3;\r?\n\r?\n)\s*uVar2 = 0;\r?\n\s*if \(\(-1 < in_AX\)/,
  "$1  uVar2 = 0;\n  in_AX = (short)param_2;\n  if ((-1 < in_AX)"
);
source = source.replace(
  "static int E2R_RepIdIsMissing(short rep_id)\n{",
  "static int E2R_ActionIndexProbeEnabled(void)\n{\n  static int cached = -1;\n  char *value;\n\n  if (cached < 0) {\n    value = getenv(\"E2R_ACTION_INDEX_PROBE\");\n    cached = value != (char *)0x0 && value[0] != '\\0' && value[0] != '0';\n  }\n  return cached;\n}\n\nstatic int E2R_RepIdIsMissing(short rep_id)\n{"
);
source = source.replace(/[ \t]+$/gm, "").replace(/\n*$/, "\n");
fs.writeFileSync(outSrc, source);
source = fs.readFileSync(outSrc, "utf8");
source = source.replace(
  /(\n\/\* 00441b24 \*\/[\s\S]*?undefined1 local_48 \[52\];\r?\n\r?\n)\s*if \(in_AX < 0\) \{/,
  "$1  in_AX = (short)param_2;\n  if (in_AX < 0) {"
);
source = source.replace(
  /(\n\/\* 0045190c \*\/[\s\S]*?undefined8 uVar3;\r?\n\r?\n)\s*uVar2 = 0;\r?\n\s*if \(\(-1 < in_AX\)/,
  "$1  uVar2 = 0;\n  in_AX = (short)param_2;\n  if ((-1 < in_AX)"
);
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
header += "void E2R_RequesterProbeQueueMouseClick(uintptr_t requester_id, uintptr_t x, uintptr_t y);\n";
header += "void E2R_RequesterProbeFeedPendingMouse(uintptr_t requester_id);\n";
header += "void E2R_RequesterProbeLogItemLayout(uintptr_t requester_id, uintptr_t item);\n";
header += "int E2R_RequesterHandleMouseClick(uintptr_t x, uintptr_t y);\n";
header += "void E2R_RequesterProbeQueueKey(uintptr_t key);\n";
header += "void E2R_RequesterProbeQueueTargetKey(uintptr_t requester_id, uintptr_t key);\n";
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
