param(
    [string]$WorkspaceRoot = "C:\ecstatica2",
    [string]$VcVars32 = "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars32.bat"
)

$ErrorActionPreference = "Stop"

$root = Join-Path $WorkspaceRoot "reverse\E2Recomp\reconstructed"
$srcRoot = Join-Path $WorkspaceRoot "reverse\E2Recomp\src"

cmd /c "call `"$VcVars32`" >nul && cl /nologo /w /std:clatest /TC /c `"$root\E2Recomp_recon.c`" /I `"$root`" /I `"$srcRoot`" /Fo:`"$root\E2Recomp_recon.obj`""
cmd /c "call `"$VcVars32`" >nul && cl /nologo /w /std:clatest /TC /c `"$root\E2Recomp_globals.c`" /I `"$root`" /I `"$srcRoot`" /Fo:`"$root\E2Recomp_globals.obj`""
cmd /c "call `"$VcVars32`" >nul && cl /nologo /w /std:clatest /TC /c `"$root\E2Recomp_data_init.c`" /I `"$root`" /I `"$srcRoot`" /Fo:`"$root\E2Recomp_data_init.obj`""
cmd /c "call `"$VcVars32`" >nul && cl /nologo /w /std:clatest /TC /c `"$root\E2Recomp_stubs.c`" /I `"$root`" /I `"$srcRoot`" /Fo:`"$root\E2Recomp_stubs.obj`""
cmd /c "call `"$VcVars32`" >nul && link /nologo /SUBSYSTEM:WINDOWS /ENTRY:entry /BASE:0x10000000 /DYNAMICBASE:NO /NXCOMPAT:NO /MAP:`"$root\E2Recomp_rebuilt.map`" /OUT:`"$root\E2Recomp_rebuilt.exe`" `"$root\E2Recomp_recon.obj`" `"$root\E2Recomp_globals.obj`" `"$root\E2Recomp_data_init.obj`" `"$root\E2Recomp_stubs.obj`" user32.lib gdi32.lib kernel32.lib winmm.lib comdlg32.lib dsound.lib ddraw.lib msacm32.lib"
