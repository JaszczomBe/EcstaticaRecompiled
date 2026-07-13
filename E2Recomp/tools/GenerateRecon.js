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
source = source.replace(/(void FUN_004594a0\(void\)[\s\S]*?\r?\n\s*)in_EAX = _DAT_00ac4dac;\r?\n\s*_DAT_00ac4fc4 = 0;/, "$1in_EAX = _DAT_00ac4dac;\n  local_1c = 0x12;\n  _DAT_00ac4fc4 = 0;");
source = source.replace(
  /undefined8 __fastcall FUN_0045fa43\(undefined4 param_1,undefined4 param_2\)\s*\r?\n\s*\{[\s\S]*?\r?\n\}\s*\r?\n\s*\r?\n\/\* 0045fa88 \*\//,
  "undefined8 __fastcall FUN_0045fa43(undefined4 param_1,undefined4 param_2)\n\n{\n  char *src = (char *)(uintptr_t)param_1;\n  char *dst;\n  uint len = 0;\n  if ((uintptr_t)src < 0x10000 || (uintptr_t)src > 0x7fffffff) return (ulonglong)param_2 << 32;\n  while (src[len] != 0) len++;\n  len++;\n  dst = (char *)LocalAlloc(0x40, len);\n  if (dst != (char *)0x0) {\n    uint i;\n    for (i = 0; i < len; i++) dst[i] = src[i];\n  }\n  return CONCAT44(param_2,dst);\n}\n\n\n\n/* 0045fa88 */"
);
source = source.replace("  FUN_004605bc(extraout_ECX,&local_20);\n  FUN_004605e8(extraout_ECX_00,&local_24);", "  FUN_004605bc(uVar6,&local_20);\n  FUN_004605e8(uVar6,&local_24);");
source = source.replace(/(void __fastcall FUN_004605bc\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  undefined4 \*unaff_EBX;\r?\n\s*)if \(in_EAX == 2\) \{/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if (in_EAX == 2) {");
source = source.replace("      *unaff_EBX = 1;\n      return;", "      if (unaff_EBX != (undefined4 *)0x0 && !E2R_IsBadWritePtr(unaff_EBX,4)) {\n        *unaff_EBX = 1;\n      }\n      return;");
source = source.replace("  *unaff_EBX = 0x80;\n  return;\n}\n\n\n\n/* 004605e8 */", "  if (unaff_EBX != (undefined4 *)0x0 && !E2R_IsBadWritePtr(unaff_EBX,4)) {\n    *unaff_EBX = 0x80;\n  }\n  return;\n}\n\n\n\n/* 004605e8 */");
source = source.replace(/(void __fastcall FUN_004605e8\(undefined4 param_1,undefined4 \*param_2\)[\s\S]*?\r?\n  int in_EAX;\r?\n\s*)if \(\(in_EAX == 0\)/, "$1in_EAX = (int)(uintptr_t)param_1;\n  if ((in_EAX == 0)");
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
  "  FUN_0043ac60();\n  uVar5 = 0;\n  if (DAT_00479dfc != 0) {\n    FUN_00414998(0);\n    Sleep(5);\n  }\n  FUN_00414998(uVar5);\n  Sleep(5);\n  FUN_00414998(uVar5);\n  Sleep(5);\n  uVar3 = 0;\n  uVar11 = FUN_00414a94(uVar5,uVar3);\n  uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n  uVar5 = 0;\n  if (DAT_00479e1c == 0) {\n    uVar11 = FUN_00414b24(uVar5,uVar6);\n    uVar6 = (undefined4)((ulonglong)uVar11 >> 0x20);\n    uVar5 = 0;\n  }"
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
