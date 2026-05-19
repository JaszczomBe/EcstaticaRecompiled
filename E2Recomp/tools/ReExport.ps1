param(
    [string]$GhidraRoot = "C:\Users\patte\QeffectsGL\reverse\ghidra_12.1_PUBLIC",
    [string]$WorkspaceRoot = "C:\ecstatica2",
    [string]$ProjectName = "E2RecompProject"
)

$ErrorActionPreference = "Stop"

$headless = Join-Path $GhidraRoot "support\analyzeHeadless.bat"
$projectDir = Join-Path $WorkspaceRoot "reverse\ghidra_project"
$scriptDir = Join-Path $WorkspaceRoot "reverse\ghidra_scripts"
$outDir = Join-Path $WorkspaceRoot "reverse\E2Recomp"
$exe = Join-Path $WorkspaceRoot "E2Recomp.exe"

New-Item -ItemType Directory -Force $projectDir | Out-Null
New-Item -ItemType Directory -Force $outDir | Out-Null

& $headless $projectDir $ProjectName `
    -import $exe `
    -overwrite `
    -scriptPath $scriptDir `
    -postScript ExportDecomp.java $outDir
