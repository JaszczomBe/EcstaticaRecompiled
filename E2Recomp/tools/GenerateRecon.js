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
  '#include "E2Recomp_recon.h"\n#include <math.h>\n#include <string.h>\n#ifdef NAN\n#undef NAN\n#endif\n#define NAN(x) isnan((double)(x))\n\nstatic uint E2R_file_flags[256];\n#define E2R_STREAM_MAGIC 0xe25eed01u\n\nstatic int E2R_round_to_int(double value)\n{\n  return (int)(value < 0.0 ? value - 0.5 : value + 0.5);\n}\n\nstatic byte E2R_clamp_byte(int value)\n{\n  if (value < 0) {\n    return 0;\n  }\n  if (255 < value) {\n    return 255;\n  }\n  return (byte)value;\n}\n\nstatic short E2R_clamp_short(int value)\n{\n  if (value < -32768) {\n    return -32768;\n  }\n  if (32767 < value) {\n    return 32767;\n  }\n  return (short)value;\n}\n\nstatic undefined4 E2R_OpenReadStream(LPCSTR path)\n{\n  HANDLE file;\n  DWORD size;\n  DWORD bytes_read = 0;\n  char *buffer;\n  undefined4 *stream;\n\n  file = CreateFileA(path,0x80000000,3,(LPSECURITY_ATTRIBUTES)0x0,3,0x80,(HANDLE)0x0);\n  if (file == INVALID_HANDLE_VALUE) {\n    return 0;\n  }\n  size = SetFilePointer(file,0,(PLONG)0x0,2);\n  if (size == 0xffffffff) {\n    CloseHandle(file);\n    return 0;\n  }\n  SetFilePointer(file,0,(PLONG)0x0,0);\n  buffer = (char *)LocalAlloc(0x40,size == 0 ? 1 : size);\n  stream = (undefined4 *)LocalAlloc(0x40,0x1c);\n  if (buffer == (char *)0x0 || stream == (undefined4 *)0x0) {\n    if (buffer != (char *)0x0) {\n      LocalFree(buffer);\n    }\n    if (stream != (undefined4 *)0x0) {\n      LocalFree(stream);\n    }\n    CloseHandle(file);\n    return 0;\n  }\n  if (size != 0 && ReadFile(file,buffer,size,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    LocalFree(buffer);\n    LocalFree(stream);\n    CloseHandle(file);\n    return 0;\n  }\n  CloseHandle(file);\n  stream[0] = (undefined4)(uintptr_t)buffer;\n  stream[1] = (undefined4)bytes_read;\n  stream[2] = (undefined4)(uintptr_t)(buffer + bytes_read);\n  stream[3] = 0;\n  stream[4] = 0xffffffff;\n  stream[5] = (undefined4)(uintptr_t)buffer;\n  stream[6] = E2R_STREAM_MAGIC;\n  return (undefined4)(uintptr_t)stream;\n}\n\nstatic uint E2R_ReadOpenFileBytes(int descriptor,char *buffer,DWORD bytes_to_read)\n{\n  DWORD bytes_read = 0;\n  HANDLE file;\n  uint slot = (uint)descriptor;\n\n  if (_DAT_00ac51fc == 0 || _DAT_00ac51f8 <= slot) {\n    return 0xffffffff;\n  }\n  file = *(HANDLE *)(_DAT_00ac51fc + slot * 4);\n  if (file == (HANDLE)0x0 || file == INVALID_HANDLE_VALUE) {\n    return 0xffffffff;\n  }\n  if (ReadFile(file,buffer,bytes_to_read,&bytes_read,(LPOVERLAPPED)0x0) == 0) {\n    return 0xffffffff;\n  }\n  return bytes_read;\n}\n'
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
source = source.replace(/(void __fastcall FUN_00460557\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)\*\(int \*\)\(\(int\)uVar1 \+ 4\) = \(int\)\(\(ulonglong\)uVar1 >> 0x20\);/, "$1if ((int)uVar1 != 0) {\n    *(int *)((int)uVar1 + 4) = (int)((ulonglong)uVar1 >> 0x20);\n  }");
source = source.replace(/(void __fastcall FUN_0046055c\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)\*\(int \*\)\(\(int\)uVar1 \+ 4\) = \(int\)\(\(ulonglong\)uVar1 >> 0x20\);/, "$1if ((int)uVar1 != 0) {\n    *(int *)((int)uVar1 + 4) = (int)((ulonglong)uVar1 >> 0x20);\n  }");
source = source.replace(/(void __fastcall FUN_00460581\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n\s*)\*\(int \*\)\(\(int\)uVar1 \+ 8\) = \(int\)\(\(ulonglong\)uVar1 >> 0x20\);/, "$1if ((int)uVar1 != 0) {\n    *(int *)((int)uVar1 + 8) = (int)((ulonglong)uVar1 >> 0x20);\n  }");
source = source.replace(/(void __fastcall FUN_00458bec\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar2;\r?\n\s*)piVar1 = \*\(int \*\*\)\(in_EAX \+ 0x38\);/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 0 || (uintptr_t)in_EAX >= 0x70000000u ||\n      IsBadReadPtr((void *)(uintptr_t)in_EAX,0x3c)) return;\n  piVar1 = *(int **)(in_EAX + 0x38);");
source = source.replace(
  "      FUN_00458bec(param_1,iVar1);\n      param_1 = extraout_ECX;\n      iVar1 = extraout_EDX;",
  "      FUN_00458bec(param_1,iVar1);"
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
source = source.replace(/(undefined4 __fastcall FUN_0041af88\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  int iVar2;\r?\n\s*)iVar2 = 0;/, "$1in_EAX = (char *)(uintptr_t)param_1;\n  if (IsBadReadPtr(in_EAX,0x300) || (uintptr_t)in_EAX >= 0x70000000u) return 0;\n  iVar2 = 0;");
source = source.replace(/&DAT_006366c0/g, "&_DAT_006366c0");
source = source.replace(/(undefined4 __fastcall FUN_00418a04\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  int extraout_ECX;\r?\n\s*)if \(1 < in_EAX\) \{/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (1 < in_EAX) {");
source = source.replace(
  "  if (1 < in_EAX) {\n    *param_2 = _DAT_006401ec;\n    return *(undefined4 *)(&DAT_00636150 + in_EAX * 4);\n  }",
  "  if (1 < in_EAX) {\n    *param_2 = _DAT_006401ec;\n    if (in_EAX == 2) {\n      return _DAT_00636158;\n    }\n    if (in_EAX == 3) {\n      return _DAT_0063615c;\n    }\n    return *(undefined4 *)(&DAT_00636150 + in_EAX * 4);\n  }"
);
source = source.replace(/(FUN_00417b20\(int param_1,int param_2,undefined4 param_3,int param_4,int param_5,int param_6\)[\s\S]*?\r?\n  int local_10;\r?\n\s*)local_24 = 1;/, "$1unaff_EBX = param_4;\n  local_24 = 1;");
source = source.replace("  local_18 = in_EAX;\n  if ((DAT_0047a279 >> 0x18 == param_1)", "  local_18 = param_1;\n  if ((DAT_0047a279 >> 0x18 == param_1)");
source = source.replace("      local_30 = local_2c;\n      iVar6 = extraout_ECX_01;\n      local_20 = local_28;", "      local_30 = local_2c;\n      iVar6 = param_2;\n      local_20 = local_28;");
source = source.replace(
  /undefined8 __fastcall FUN_00415c04\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00415c68 \*\//,
  "undefined8 __fastcall FUN_00415c04(undefined4 param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  DAT_00479d88 = 0;\n  return (ulonglong)param_2 << 32;\n}\n\n\n\n/* 00415c68 */"
);
source = source.replace(/(undefined8 __fastcall FUN_0041db98\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  uint uVar4;\r?\n\s*)uVar4 = 0;/, "$1in_EAX = *(ushort *)(uintptr_t)param_1;\n  uVar4 = 0;");
source = source.replace(/(uint __fastcall FUN_0041dc20\(undefined4 param_1,uint param_2\)[\s\S]*?\r?\n  uint uVar3;\r?\n\s*)uVar2 = \(param_2 & 0xff\)/, "$1in_EAX = (int)(uintptr_t)param_1;\n  uVar2 = (param_2 & 0xff)");
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
source = source.replace(/(undefined8 __fastcall FUN_0043b384\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  ulonglong uVar11;\r?\n\s*)DAT_0047a788 = 1;/, "$1in_EAX = (short *)(uintptr_t)param_1;\n  if (IsBadReadPtr(in_EAX,0x40) || (uintptr_t)in_EAX >= 0x70000000u) return (ulonglong)param_2 << 32;\n  DAT_0047a788 = 1;");
source = source.replace(/(void __fastcall\s*\r?\nFUN_0043fe24\(short param_1,short param_2,short param_3,undefined4 param_4,undefined4 param_5,\s*\r?\n\s*short param_6,undefined4 param_7\)[\s\S]*?\r?\n  short unaff_BX;\r?\n\s*)if \(DAT_0047a43c == 0\) \{/, "$1if (in_EAX == (short *)0x0 || E2R_IsBadWritePtr(in_EAX,0x16)) {\n    return;\n  }\n  if (DAT_0047a43c == 0) {");
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
source = source.replace(
  /void FUN_00414f40\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 00415b78 \*\//,
  "void FUN_00414f40(void)\n\n{\n  const double pi = 3.14159265358979323846;\n  int mode;\n  int x;\n  int y;\n\n  for (x = 0; x < 256; x = x + 1) {\n    double phase = ((double)x * pi) / 128.0;\n    double normalized = (double)x / 255.0;\n    int tangent_index = (x & 0x40) != 0 ? x : 64 - x;\n    double tangent = tan(((double)tangent_index * pi) / 128.0);\n\n    *(byte *)(0x005fe990 + x) = E2R_clamp_byte(E2R_round_to_int(sin(phase) * 127.0 + 128.0));\n    *(byte *)(0x005fe890 + x) = E2R_clamp_byte(E2R_round_to_int(cos(phase) * 127.0 + 128.0));\n    *(byte *)(0x0060af88 + x) = E2R_clamp_byte(E2R_round_to_int(sqrt(normalized) * 255.0));\n    *(byte *)(0x0060b088 + x) = E2R_clamp_byte(E2R_round_to_int((1.0 - sqrt(normalized)) * 255.0));\n    *(short *)(0x0067be7c + x * 2) = E2R_clamp_short(E2R_round_to_int(tangent * 1024.0));\n  }\n\n  for (x = 0; x < 256; x = x + 1) {\n    *(byte *)(0x005fe790 + x) = E2R_clamp_byte(x);\n  }\n\n  for (x = 0; x < 1024; x = x + 1) {\n    double phase = (((double)x + 0.5) * pi) / 512.0;\n    *(short *)(0x0060c4b8 + x * 2) = E2R_clamp_short(E2R_round_to_int(sin(phase) * 32767.0));\n  }\n\n  for (mode = 0; mode < 16; mode = mode + 1) {\n    int base = 0x00507590 + mode * 0x4000;\n    int bias = mode * 32;\n    for (y = 0; y < 128; y = y + 1) {\n      for (x = 0; x < 128; x = x + 1) {\n        int shade = ((x * y) >> 7) + bias;\n        *(byte *)(base + y * 128 + x) = E2R_clamp_byte(shade);\n      }\n    }\n  }\n\n  for (y = 0; y < 128; y = y + 1) {\n    for (x = 0; x < 128; x = x + 1) {\n      *(byte *)(0x00507590 + 0x40000 + y * 128 + x) = 0x80;\n    }\n  }\n  return;\n}\n\n\n\n/* 00415b78 */"
);
source = source.replace("piVar3 = (int *)FUN_0045eb05(param_1,&DAT_0047007c);", "piVar3 = (int *)FUN_0045eb05(param_1,\"shadow.dat\");");
source = source.replace(
  /(void FUN_0041ccf0\(void\)[\s\S]*?\r?\n\s*)undefined1 \*in_EAX;/,
  "$1undefined1 *in_EAX = (undefined1 *)0x00684a68;"
);
source = source.replace(
  /undefined8 __fastcall FUN_0041ce88\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0041cf44 \*\//,
  "undefined8 __fastcall FUN_0041ce88(undefined4 param_1,undefined4 param_2)\n\n{\n  byte *data;\n  undefined4 *stream;\n  int x;\n  int y;\n  \n  (void)param_1;\n  stream = (undefined4 *)(uintptr_t)E2R_OpenReadStream(\"shademap.dat\");\n  if (stream == (undefined4 *)0x0) {\n    return (ulonglong)param_2 << 0x20;\n  }\n  if ((uint)stream[1] < 0xc000) {\n    FUN_0045ec6c(0,(undefined4)(uintptr_t)stream);\n    return (ulonglong)param_2 << 0x20;\n  }\n  data = (byte *)(uintptr_t)stream[5];\n  for (y = 0; y < 0x80; y = y + 1) {\n    for (x = 0; x < 0x80; x = x + 1) {\n      *(byte *)(0x0061d030 + y * 0x80 + x) = data[0];\n      *(short *)(0x00621630 + y * 0x100 + x * 2) = (short)((uint)data[1] << 8 | (uint)data[2]);\n      data = data + 3;\n    }\n  }\n  FUN_0045ec6c(0,(undefined4)(uintptr_t)stream);\n  return CONCAT44(param_2,1);\n}\n\n\n\n/* 0041cf44 */"
);
source = source.replace("(&DAT_0068cd68)[iVar5] = 0;", "*(undefined1 *)(0x0068cd68 + iVar5) = 0;");
source = source.replace(
  /undefined4 __fastcall FUN_0045eb05\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045ebf1 \*\//,
  "undefined4 __fastcall FUN_0045eb05(undefined4 param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  return E2R_OpenReadStream((LPCSTR)(uintptr_t)param_2);\n}\n\n\n\n/* 0045ebf1 */"
);
source = source.replace(
  /(undefined8 __fastcall FUN_0045ec6c\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n  undefined4 extraout_ECX;\r?\n\s*)\(\*\(code \*\)PTR_FUN_0047d3b0\)\(\);/,
  "$1undefined4 *stream;\n  \n  (void)param_1;\n  stream = (undefined4 *)(uintptr_t)param_2;\n  if (stream != (undefined4 *)0x0 && stream[6] == E2R_STREAM_MAGIC) {\n    if (stream[5] != 0) {\n      LocalFree((HLOCAL)(uintptr_t)stream[5]);\n    }\n    stream[6] = 0;\n    LocalFree((HLOCAL)stream);\n    return (ulonglong)param_2 << 0x20;\n  }\n  (*(code *)PTR_FUN_0047d3b0)();"
);
source = source.replace(
  /undefined4 __fastcall FUN_0045f1ff\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045f218 \*\//,
  "undefined4 __fastcall FUN_0045f1ff(undefined4 param_1,undefined4 param_2)\n\n{\n  uint size;\n  undefined8 uVar1;\n  \n  size = (uint)(uintptr_t)param_1 * (uint)(uintptr_t)param_2;\n  uVar1 = FUN_0045f0d1(size,param_2);\n  if ((int)uVar1 != 0) {\n    FUN_0045f8d0((undefined4)(uintptr_t)(uint)uVar1,0);\n  }\n  return (undefined4)(uintptr_t)(uint)uVar1;\n}\n\n\n\n/* 0045f218 */"
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
source = source.replace(
  "  acStack_28[0] = s_e_config_0047000c[0];\n  acStack_28[1] = s_e_config_0047000c[1];\n  acStack_28[2] = s_e_config_0047000c[2];\n  acStack_28[3] = s_e_config_0047000c[3];\n  acStack_24[0] = s_e_config_0047000c[4];\n  acStack_24[1] = s_e_config_0047000c[5];\n  acStack_24[2] = s_e_config_0047000c[6];\n  acStack_24[3] = s_e_config_0047000c[7];\n  cStack_20 = s_e_config_0047000c[8];",
  "  acStack_28[0] = s_e_config_0047000c[0];\n  acStack_28[1] = s_e_config_0047000c[1];\n  acStack_28[2] = s_e_config_0047000c[2];\n  acStack_28[3] = s_e_config_0047000c[3];\n  acStack_28[4] = s_e_config_0047000c[4];\n  acStack_28[5] = s_e_config_0047000c[5];\n  acStack_28[6] = s_e_config_0047000c[6];\n  acStack_28[7] = s_e_config_0047000c[7];\n  acStack_28[8] = s_e_config_0047000c[8];"
);
source = source.replace(
  "    uVar4 = FUN_0045e76f((int)uVar11,acStack_68);",
  "    uVar4 = E2R_ReadOpenFileBytes((int)uVar11,acStack_68,0x20);"
);
source = source.replace(
  "  iVar3 = FUN_0045e90e(uVar6,(byte *)s_Ecstatica001_0047006c);",
  "  iVar3 = strncmp(acStack_68,s_Ecstatica001_0047006c,0xc);"
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

for (let i = 0; i < prototypes.length; i++) {
  prototypes[i] = prototypes[i].replace("uint * FUN_00461746(void);", "uint * __fastcall FUN_00461746(int heap,uint size);");
  prototypes[i] = prototypes[i].replace("void FUN_00420b8c(void);", "void FUN_00420b8c(int index);");
}

ids.add("s_Can_t_load_title_picture_00471320");
ids.add("s_gbnklogo_raw_00470500");
ids.add("s_psyglogo_raw_00470510");
ids.add("s_aasglogo_raw_00470520");

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
