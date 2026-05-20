const fs = require("fs");
const path = require("path");

const workspaceRoot = process.argv[2] || "C:\\ecstatica2";
const root = path.join(workspaceRoot, "reverse", "E2Recomp");
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
  "undefined8 __fastcall FUN_004603d1(undefined4 param_1,undefined4 param_2)\n\n{\n  (void)param_1;\n  return (ulonglong)param_2 << 32;\n}\n\n\n\n/* 004604e6 */"
);
source = source.replace(/(undefined8 __fastcall FUN_0045f0d1\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  undefined8 uVar7;\r?\n\s*)if \(\(in_EAX != 0\)/, "$1in_EAX = (uint)(uintptr_t)param_1;\n  if ((in_EAX != 0)");
source = source.replace(/(undefined4 FUN_00458714\(void\)[\s\S]*?\r?\n  WNDCLASSA local_3c;\r?\n\s*)local_3c.style = 3;/, "$1in_EAX = GetModuleHandleA((LPCSTR)0x0);\n  local_3c.style = 3;");
source = source.replace("local_3c.lpfnWndProc = (WNDPROC)&LAB_00458110;", "local_3c.lpfnWndProc = (WNDPROC)E2R_WndProc;");
source = source.replace(/(void FUN_004594a0\(void\)[\s\S]*?\r?\n  SIZE_T local_1c;\r?\n\s*)_DAT_00ac4fc4 = 0;/, "$1in_EAX = _DAT_00ac4dac;\n  _DAT_00ac4fc4 = 0;");
source = source.replace(
  /undefined8 __fastcall FUN_0045fa43\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fa88 \*\//,
  "undefined8 __fastcall FUN_0045fa43(undefined4 param_1,undefined4 param_2)\n\n{\n  char *src = (char *)(uintptr_t)param_1;\n  char *dst;\n  uint len = 0;\n  if ((uintptr_t)src < 0x10000 || (uintptr_t)src > 0x7fffffff) return (ulonglong)param_2 << 32;\n  while (src[len] != 0) len++;\n  len++;\n  dst = (char *)LocalAlloc(0x40, len);\n  if (dst != (char *)0x0) {\n    uint i;\n    for (i = 0; i < len; i++) dst[i] = src[i];\n  }\n  return CONCAT44(param_2,dst);\n}\n\n\n\n/* 0045fa88 */"
);
source = source.replace(
  /void FUN_0045f9b5\(void\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fa43 \*\//,
  "void FUN_0045f9b5(void)\n\n{\n  return;\n}\n\n\n\n/* 0045fa43 */"
);
source = source.replace(/(undefined8 __fastcall FUN_004618f9\(undefined4 param_1,undefined4 param_2\)[\s\S]*?\r?\n  int \*piVar3;\r?\n\s*)piVar1 = DAT_0047d260;/, "$1in_EAX = (int *)(uintptr_t)param_2;\n  if (in_EAX == 0) return (ulonglong)param_2 << 32;\n  piVar1 = DAT_0047d260;");
source = source.replace("uint * FUN_00461746(void)", "uint * __fastcall FUN_00461746(int heap,uint size)");
source = source.replace(/(uint \* __fastcall FUN_00461746\(int heap,uint size\)[\s\S]*?\r?\n  uint \*puVar5;\r?\n\s*)if \(\(\(in_EAX != 0\)/, "$1unaff_EBX = heap;\n  in_EAX = size;\n  if (unaff_EBX == 0 || IsBadReadPtr((void *)(uintptr_t)unaff_EBX,0x2c)) return (uint *)0x0;\n  if (((in_EAX != 0)");
source = source.replace(/(uint \* __fastcall FUN_00461746\(int heap,uint size\)[\s\S]*?\r?\n\s*)do \{\r?\n\s*uVar1 = \*puVar3;/, "$1if ((uintptr_t)puVar3 < 0x10000 || (uintptr_t)puVar3 > 0x7fffffff || IsBadReadPtr(puVar3,0xc)) return (uint *)0x0;\n    do {\n      if ((uintptr_t)puVar3 < 0x10000 || (uintptr_t)puVar3 > 0x7fffffff || IsBadReadPtr(puVar3,0xc)) return (uint *)0x0;\n      uVar1 = *puVar3;");
source = source.replace("puVar4 = FUN_00461746();", "puVar4 = FUN_00461746(iVar5,uVar3);");
source = source.replace(
  /(\s*if \(puVar4 != \(uint \*\)0x0\) goto LAB_0045f1a1;\r?\n)\s*if \(DAT_0047d268 < \*\(uint \*\)\(extraout_ECX \+ 0x14\)\) \{\r?\n\s*DAT_0047d268 = \*\(uint \*\)\(extraout_ECX \+ 0x14\);\r?\n\s*\}\r?\n\s*uVar2 = 0;\r?\n\s*iVar5 = \*\(int \*\)\(extraout_ECX \+ 8\);/,
  "$1        if ((uintptr_t)iVar5 < 0x10000 || (uintptr_t)iVar5 > 0x7fffffff || IsBadReadPtr((void *)(uintptr_t)iVar5,0x18)) break;\n        if (DAT_0047d268 < *(uint *)(iVar5 + 0x14)) {\n          DAT_0047d268 = *(uint *)(iVar5 + 0x14);\n        }\n        uVar2 = 0;\n        iVar5 = *(int *)(iVar5 + 8);"
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
}

fs.writeFileSync(outSrc, source);

const sortedIds = [...ids].sort();
const sortedStacks = [...stackIds].sort();
let header = "";
header += "#pragma once\n";
header += '#include "../src/e2recomp_types.h"\n';
header += "#include <commdlg.h>\n#include <mmsystem.h>\n#include <stdint.h>\n\n";
header += "#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n";
header += "typedef uint32_t uint3;\ntypedef int32_t int3;\ntypedef uint32_t undefined3;\ntypedef uint64_t undefined6;\ntypedef uint64_t uint6;\ntypedef double float10;\ntypedef unsigned __int64 unkbyte10;\ntypedef unsigned __int64 unkuint10;\ntypedef int code();\ntypedef unsigned char bool;\ntypedef signed char sbyte;\n";
header += "#define tagMSG MSG\n#define tagPOINT POINT\n#define tagSIZE SIZE\n#define tagMIDIOUTCAPSA MIDIOUTCAPSA\n#define _MMCKINFO MMCKINFO\n#define _MMIOINFO MMIOINFO\n#define _WIN32_FIND_DATAA WIN32_FIND_DATAA\n#define _INPUT_RECORD INPUT_RECORD\n#define _SYSTEMTIME SYSTEMTIME\n#define _FILETIME FILETIME\n#define _GUID GUID\n#ifndef true\n#define true 1\n#define false 0\n#endif\n\n";
header += "void E2R_InitData(void);\n";
header += "void E2R_WinMainThunk(void);\n";
header += "LRESULT CALLBACK E2R_WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);\n";
header += "extern uintptr_t E2R_timer_slots[8];\n";
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
header += "#endif\n\n";
header += "/* Function prototypes recovered from the decompiler signatures. */\n";
header += prototypes.join("\n") + "\n\n";
header += "/* Global labels recovered from Ghidra symbols and decompiler references. */\n";
for (const name of sortedIds) header += name.startsWith("s_") ? `extern char ${name}[];\n` : `extern uintptr_t ${name};\n`;
for (const name of sortedStacks) header += `extern undefined1 ${name}[4096];\n`;
header += "\n#ifdef __cplusplus\n}\n#endif\n";
fs.writeFileSync(outHdr, header);

let globals = '#include "E2Recomp_recon.h"\n\n';
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
