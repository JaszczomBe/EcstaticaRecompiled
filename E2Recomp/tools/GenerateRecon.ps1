param(
    [string]$WorkspaceRoot = "C:\ecstatica2"
)

$ErrorActionPreference = "Stop"

$root = Join-Path $WorkspaceRoot "reverse\E2Recomp"
$srcPath = Join-Path $root "src\E2Recomp_decompiled.c"
$funcPath = Join-Path $root "metadata\functions.tsv"
$symPath = Join-Path $root "metadata\symbols.tsv"
$outDir = Join-Path $root "reconstructed"
$outSrc = Join-Path $outDir "E2Recomp_recon.c"
$outHdr = Join-Path $outDir "E2Recomp_recon.h"
$outGlobals = Join-Path $outDir "E2Recomp_globals.c"
$outRenames = Join-Path $outDir "E2Recomp_names.tsv"

New-Item -ItemType Directory -Force $outDir | Out-Null

$source = [IO.File]::ReadAllText($srcPath)
$functions = Import-Csv $funcPath -Delimiter "`t"
$symbols = Import-Csv $symPath -Delimiter "`t"

$externalNames = @{}
foreach ($s in $symbols) {
    if ($s.address -like "EXTERNAL:*" -and $s.type -eq "Function") {
        $leaf = ($s.name -split "::")[-1]
        if ($leaf -match "^[A-Za-z_][A-Za-z0-9_]*$") {
            $externalNames[$leaf] = $true
        }
    }
}

# Remove import thunk functions. Their bodies recurse in Ghidra output; the
# real definitions come from Windows import libraries during linking.
foreach ($f in ($functions | Sort-Object { [Convert]::ToInt32($_.address, 16) } -Descending)) {
    if ($externalNames.ContainsKey($f.name)) {
        $addr = $f.address.ToLowerInvariant()
        $name = [Regex]::Escape($f.name)
        $pattern = "(?ms)/\*\s*$addr\s*\*/\s*(?:/\*.*?\*/\s*)*.*?\b$name\s*\([^;{}]*\)\s*\{.*?^\}"
        $source = [Regex]::Replace($source, $pattern, "/* $addr import thunk $($f.name) removed; linked from system import library. */")
    }
}

# Make Ghidra's synthetic stack placeholder names legal C identifiers.
$source = [Regex]::Replace($source, "\bstack0x([0-9a-fA-F]+)\b", 'stack_$1')

# Convert Ghidra partial-field pseudo syntax. For struct fields at offset zero,
# keep the field itself as the lvalue; for labels, emit byte reads.
$source = [Regex]::Replace($source, "\b([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\._0_([1248])_", '$1')
$source = [Regex]::Replace($source, "\b([A-Za-z_][A-Za-z0-9_]*)\._([0-9]+)_([1248])_", 'E2R_READ$3($1,$2)')

# Some functions were inferred as void even though callers use their return
# value. Promote those signatures to undefined4 for C compilation.
$valueUsed = New-Object System.Collections.Generic.HashSet[string]
foreach ($m in [Regex]::Matches($source, "(?:=\s*|\([A-Za-z_][A-Za-z0-9_\s\*]*\)\s*|return\s+|if\s*\(\s*)(FUN_[0-9a-fA-F]+|thunk_FUN_[0-9a-fA-F]+)\s*\(")) {
    [void]$valueUsed.Add($m.Groups[1].Value)
}
foreach ($name in $valueUsed) {
    $escaped = [Regex]::Escape($name)
    $source = [Regex]::Replace($source, "\bvoid(\s+(?:__fastcall|__cdecl|__stdcall)\s+$escaped\s*\()", 'undefined4$1')
    $source = [Regex]::Replace($source, "\bvoid(\s+$escaped\s*\()", 'undefined4$1')
}

$source = $source.Replace('#include "e2recomp_types.h"', '#include "E2Recomp_recon.h"')
[IO.File]::WriteAllText($outSrc, $source)

# Extract function prototypes from the post-processed source.
$protoMatches = [Regex]::Matches(
    $source,
    "(?ms)^\s*((?:[A-Za-z_][A-Za-z0-9_]*\s+|[*]\s*)+[A-Za-z_][A-Za-z0-9_]*\s*\([^;{}]*?\))\s*\r?\n\s*\{"
)

$prototypes = New-Object System.Collections.Generic.List[string]
$seenProto = @{}
foreach ($m in $protoMatches) {
    $proto = [Regex]::Replace($m.Groups[1].Value, "\s+", " ").Trim()
    if ($proto -notmatch "\b(FUN_[0-9a-fA-F]+|thunk_FUN_[0-9a-fA-F]+|entry|__[A-Za-z0-9_]+)\s*\(") {
        continue
    }
    if ($proto -match "\b(DirectDrawCreate|DirectSoundCreate|CreateFileA|ExitProcess|timeGetTime)\s*\(") {
        continue
    }
    if (-not $seenProto.ContainsKey($proto)) {
        $seenProto[$proto] = $true
        $prototypes.Add($proto + ";")
    }
}

# Collect global/data labels that are referenced by the decompiler output.
$idMatches = [Regex]::Matches($source, "\b_?(?:DAT|PTR|s|u|UNK|FLOAT|DOUBLE|LAB)_[A-Za-z0-9_%]+_[0-9a-fA-F]{8}\b|\b_?DAT_[0-9a-fA-F]{8}\b|\bLAB_[0-9a-fA-F]{8}\b|\bPTR_[A-Za-z0-9_]+_[0-9a-fA-F]{8}\b|\b[A-Za-z]*Ram[0-9a-fA-F]{8}\b")
$ids = New-Object System.Collections.Generic.SortedSet[string]
foreach ($m in $idMatches) {
    $name = $m.Value
    if ($name -notmatch "^FUN_") {
        [void]$ids.Add($name)
    }
}

$stackMatches = [Regex]::Matches($source, "\bstack_[0-9a-fA-F]+\b")
$stackIds = New-Object System.Collections.Generic.SortedSet[string]
foreach ($m in $stackMatches) {
    [void]$stackIds.Add($m.Value)
}

$arrayLike = @{}
$pointerLike = @{}
foreach ($name in $ids) {
    $escapedName = [Regex]::Escape($name)
    if ([Regex]::IsMatch($source, "\b" + $escapedName + "\s*\[")) {
        $arrayLike[$name] = $true
    }
    if ([Regex]::IsMatch($source, "(\*\s*" + $escapedName + "\b|\b" + $escapedName + "\s*\+|\(int\)\s*" + $escapedName + "\b|\b" + $escapedName + "\s*=\s*FUN_0045f1ff\s*\()")) {
        $pointerLike[$name] = $true
    }
}

$nonStringIdPattern = "(?:_?(?:DAT|PTR|u|UNK|FLOAT|DOUBLE|LAB)_[A-Za-z0-9_%]+_[0-9a-fA-F]{8}|_?DAT_[0-9a-fA-F]{8}|LAB_[0-9a-fA-F]{8}|PTR_[A-Za-z0-9_]+_[0-9a-fA-F]{8}|[A-Za-z]*Ram[0-9a-fA-F]{8})"
$source = [Regex]::Replace($source, "\b($nonStringIdPattern)\s*\[", '((undefined4 *)(uintptr_t)$1)[')
$source = [Regex]::Replace($source, "(^|[^A-Za-z0-9_\)\]])\*\s*($nonStringIdPattern)\b", '$1*(undefined4 *)(uintptr_t)$2')

# Undo false dereference rewrites where the star was a multiplication operator.
$source = [Regex]::Replace($source, "([A-Za-z0-9_\)\]])\s*\*\(undefined4 \*\)\(uintptr_t\)([A-Za-z_][A-Za-z0-9_]*)", '$1 * $2')

# Ghidra sometimes names partial locals as _local_xx after field extraction.
$source = [Regex]::Replace($source, "\b_local_([0-9a-fA-F]+)\b", 'local_$1')

# Switches over recovered pointer-looking temporaries need integral selectors.
$source = [Regex]::Replace($source, "\bswitch\s*\(([^;\r\n{}]+)\)", 'switch((int)(uintptr_t)($1))')
$source = [Regex]::Replace($source, "\bcase\s*\([A-Za-z_][A-Za-z0-9_\s]*\*\)\s*(0x[0-9a-fA-F]+|\d+)\s*:", 'case $1:')

[IO.File]::WriteAllText($outSrc, $source)

$header = New-Object System.Text.StringBuilder
[void]$header.AppendLine("#pragma once")
[void]$header.AppendLine("#include `"../src/e2recomp_types.h`"")
[void]$header.AppendLine("#include <commdlg.h>")
[void]$header.AppendLine("#include <mmsystem.h>")
[void]$header.AppendLine("")
[void]$header.AppendLine("#ifdef __cplusplus")
[void]$header.AppendLine("extern `"C`" {")
[void]$header.AppendLine("#endif")
[void]$header.AppendLine("")
[void]$header.AppendLine("typedef uint32_t uint3;")
[void]$header.AppendLine("typedef int32_t int3;")
[void]$header.AppendLine("typedef uint32_t undefined3;")
[void]$header.AppendLine("typedef uint64_t undefined6;")
[void]$header.AppendLine("typedef uint64_t uint6;")
[void]$header.AppendLine("typedef double float10;")
[void]$header.AppendLine("typedef int code();")
[void]$header.AppendLine("typedef unsigned char bool;")
[void]$header.AppendLine("typedef signed char sbyte;")
[void]$header.AppendLine("#define tagMSG MSG")
[void]$header.AppendLine("#define tagPOINT POINT")
[void]$header.AppendLine("#define tagMIDIOUTCAPSA MIDIOUTCAPSA")
[void]$header.AppendLine("#define _GUID GUID")
[void]$header.AppendLine("#ifndef true")
[void]$header.AppendLine("#define true 1")
[void]$header.AppendLine("#define false 0")
[void]$header.AppendLine("#endif")
[void]$header.AppendLine("")
[void]$header.AppendLine("#ifndef SUB41")
[void]$header.AppendLine("#define SUB41(x,n) ((undefined1)(((uint32_t)(x) >> (8 * (n))) & 0xffu))")
[void]$header.AppendLine("#define SUB42(x,n) ((undefined2)(((uint32_t)(x) >> (8 * (n))) & 0xffffu))")
[void]$header.AppendLine("#define SUB44(x,n) ((undefined4)(((uint64_t)(x) >> (8 * (n))) & 0xffffffffu))")
[void]$header.AppendLine("#define ZEXT14(x) ((undefined4)(uint8_t)(x))")
[void]$header.AppendLine("#define ZEXT24(x) ((undefined4)(uint16_t)(x))")
[void]$header.AppendLine("#define SEXT14(x) ((int32_t)(int8_t)(x))")
[void]$header.AppendLine("#define SEXT24(x) ((int32_t)(int16_t)(x))")
[void]$header.AppendLine("#define E2R_READ1(base,off) (*(undefined1 *)((byte *)(base) + (off)))")
[void]$header.AppendLine("#define E2R_READ2(base,off) (*(undefined2 *)((byte *)(base) + (off)))")
[void]$header.AppendLine("#define E2R_READ4(base,off) (*(undefined4 *)((byte *)(base) + (off)))")
[void]$header.AppendLine("#define E2R_READ8(base,off) (*(undefined8 *)((byte *)(base) + (off)))")
[void]$header.AppendLine("#endif")
[void]$header.AppendLine("")
[void]$header.AppendLine("/* Function prototypes recovered from the decompiler signatures. */")
foreach ($p in $prototypes) {
    [void]$header.AppendLine($p)
}
[void]$header.AppendLine("")
[void]$header.AppendLine("/* Global labels recovered from Ghidra symbols and decompiler references. */")
foreach ($name in $ids) {
    if ($name.StartsWith("s_")) {
        [void]$header.AppendLine("extern char $name[];")
    } else {
        [void]$header.AppendLine("extern uintptr_t $name;")
    }
}
foreach ($name in $stackIds) {
    [void]$header.AppendLine("extern undefined1 $name[4096];")
}
[void]$header.AppendLine("")
[void]$header.AppendLine("#ifdef __cplusplus")
[void]$header.AppendLine("}")
[void]$header.AppendLine("#endif")
[IO.File]::WriteAllText($outHdr, $header.ToString())

$globals = New-Object System.Text.StringBuilder
[void]$globals.AppendLine("#include `"E2Recomp_recon.h`"")
[void]$globals.AppendLine("")
foreach ($name in $ids) {
    if ($name.StartsWith("s_")) {
        [void]$globals.AppendLine("char $name[256];")
    } else {
        [void]$globals.AppendLine("uintptr_t $name;")
    }
}
foreach ($name in $stackIds) {
    [void]$globals.AppendLine("undefined1 $name[4096];")
}
[IO.File]::WriteAllText($outGlobals, $globals.ToString())

$renameRows = New-Object System.Collections.Generic.List[string]
$renameRows.Add("address`told_name`tnew_name`treason")
foreach ($f in $functions) {
    $newName = $null
    if ($f.name -eq "entry") {
        $newName = "program_entry"
    } elseif ($f.name -match "^FUN_" -and $source -match "(/\*\s*$($f.address.ToLowerInvariant())\s*\*/(?s).*?\n\n)") {
        # Conservative automated names for well-known string/import clusters.
        $addrPattern = [Regex]::Escape("/* " + $f.address.ToLowerInvariant() + " */")
        $bodyMatch = [Regex]::Match($source, "(?ms)$addrPattern.*?(?=^/\*\s*[0-9a-f]{8}\s*\*/|\z)")
        $body = $bodyMatch.Value
        if ($body -match "DirectDrawCreate|SetCooperativeLevel|CreateSurface") { $newName = "video_directdraw_init_$($f.address)" }
        elseif ($body -match "DirectSoundCreate|SIMD_PlayTune|mmio") { $newName = "audio_init_or_stream_$($f.address)" }
        elseif ($body -match "CreateWindowExA|RegisterClassA|DefWindowProcA") { $newName = "window_or_dialog_proc_$($f.address)" }
        elseif ($body -match "CODE_ECSTATIC_FAN|actions|scenes|actors") { $newName = "asset_path_or_fan_loader_$($f.address)" }
        elseif ($body -match "saved|QUICK SAVED GAME|LoadGame") { $newName = "savegame_handler_$($f.address)" }
    }
    if ($newName) {
        $renameRows.Add("$($f.address)`t$($f.name)`t$newName`tstring/import heuristic")
    }
}
[IO.File]::WriteAllLines($outRenames, $renameRows)

Write-Host "Generated $outSrc"
Write-Host "Generated $outHdr with $($prototypes.Count) prototypes and $($ids.Count) globals"
Write-Host "Generated $outGlobals"
