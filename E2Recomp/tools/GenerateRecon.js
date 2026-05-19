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
source = source.replace(/\(\*\(undefined4 \*\)\(uintptr_t\)([A-Za-z_][A-Za-z0-9_]*)\)\s*\(/g, "(*(code *)(uintptr_t)$1)(");
source = source.replace(/&\s*(stack_[0-9a-fA-F]+)\s*\)\s*\[/g, "$1)[");
source = source.replace(/\(&\s*(stack_[0-9a-fA-F]+)\)\s*\[/g, "$1[");
source = source.replace(/([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\.E2R_READ([1248])\(([A-Za-z_][A-Za-z0-9_]*),([0-9]+)\)/g, "E2R_READ$2(&$1.$3,$4)");
source = source.replace(/\blpfnWndProc\s*=\s*(FUN_[0-9a-fA-F]+)\s*;/g, "lpfnWndProc = (WNDPROC)$1;");
source = source.replace(/DialogBoxParamA\(([^;]*?),(FUN_[0-9a-fA-F]+),/g, "DialogBoxParamA($1,(DLGPROC)$2,");
source = source.replace(/\b_local_([0-9a-fA-F]+)\b/g, "local_$1");
source = source.replace(/\bswitch\s*\(([^;\r\n{}]+)\)/g, "switch((int)(uintptr_t)($1))");
source = source.replace(/\bcase\s*\([A-Za-z_][A-Za-z0-9_\s]*\*\)\s*(0x[0-9a-fA-F]+|\d+)\s*:/g, "case $1:");

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
header += "static HWND E2R_CreateWindowExA(DWORD exStyle, ...) { (void)exStyle; return (HWND)0; }\n";
header += "static INT_PTR E2R_DialogBoxParamA(HINSTANCE inst, LPCSTR tmpl, HWND parent, DLGPROC proc, LPARAM param) { (void)inst; (void)tmpl; (void)parent; (void)proc; (void)param; return 0; }\n";
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
