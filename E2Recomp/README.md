# E2Recomp.exe Reconstruction

<!-- docs-tree:parent -->
[Project README](../README.md)
<!-- /docs-tree:parent -->

This directory contains Ghidra export artifacts, generated reconstruction, Linux native probes, and compatibility/host backends for Ecstatica II. The current export route targets original `E2WIN95.EXE`; older Windows commands below refer to the historical `E2Recomp.exe` input. See the [active implementation](../docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md) for current status and [build instructions](reconstructed/README.md) for Linux launch.

## What Was Recovered

- `src/E2Recomp_decompiled.c`: Ghidra C-like output; `metadata/functions.tsv` records the exported function inventory.
- `src/e2recomp_types.h`: type shim for Ghidra primitive types.
- `reconstructed/E2Recomp_recon.c`: compileable normalized reconstruction.
- `reconstructed/E2Recomp_rebuilt.exe`: linked 32-bit rebuilt executable.
- `metadata/functions.tsv`: function address, generated name, body size, and decompile status.
- `metadata/symbols.tsv`: all symbols recovered by Ghidra, including imports and data labels.
- `metadata/references.tsv`: address references from the analyzed program.
- `../ghidra_project/E2RecompProject`: saved Ghidra project for interactive cleanup.
- `../ghidra_scripts/ExportDecomp.java`: reproducible headless export script.

## Binary Facts

- Format: 32-bit native PE executable.
- Image base: `0x00400000`.
- Entry RVA: `0x0006030e`.
- Entry VA: `0x0046030e`.
- Timestamp: `1997-10-09 19:10:32 UTC`.
- Subsystem: Windows GUI.
- CLI/.NET metadata: none.

Imported libraries observed by Ghidra:

- `COMDLG32.DLL`
- `DDRAW.DLL`
- `DSOUND.DLL`
- `GDI32.DLL`
- `KERNEL32.DLL`
- `MSACM32.DLL`
- `SIMD_W95.DLL`
- `USER32.DLL`
- `WINMM.DLL`

## Regenerate The Decompilation

On Linux, configure the project and run the explicit Ghidra export target:

```sh
cmake --preset linux-clang32-debug
cmake --build --preset linux-clang32-debug --target ghidra-export
```

By default this imports `E2WIN95.EXE` from the configured `ECSTATICA2_DATA_DIR` and writes
the exported C and TSV metadata back into this `E2Recomp` directory. Ghidra is
found via `GHIDRA_ANALYZE_HEADLESS`, `GHIDRA_HOME`, `analyzeHeadless` on `PATH`,
or a local `dep/ghidra` checkout/unpacked release.

To regenerate the normalized reconstruction from the export:

```sh
cmake --build --preset linux-clang32-debug --target ghidra-generate-recon
```

That target intentionally rewrites `reconstructed/E2Recomp_recon.c`,
`reconstructed/E2Recomp_recon.h`, and related generated artifacts, so use it when
you want a fresh Ghidra-derived reconstruction pass.

Historical Windows export route (not reverified by the 2026-09-14 audit), from `C:\ecstatica2`:

```powershell
.\reverse\E2Recomp\tools\ReExport.ps1
```

Equivalent direct Ghidra command:

```powershell
& 'C:\Users\patte\QeffectsGL\reverse\ghidra_12.1_PUBLIC\support\analyzeHeadless.bat' `
  'C:\ecstatica2\reverse\ghidra_project' E2RecompProject `
  -import 'C:\ecstatica2\E2Recomp.exe' `
  -overwrite `
  -scriptPath 'C:\ecstatica2\reverse\ghidra_scripts' `
  -postScript ExportDecomp.java 'C:\ecstatica2\reverse\E2Recomp'
```

## Current runtime and recovery work

The current developer route is the single **Ecstatica Recompiled** VS Code F5
entry with SDL/i386 Debug, diagnostic cylinders, action indexing, mesh/HUD bypass
and original population enabled. Logging, replay, state/frame inspection and
matching-binary/debugger evidence are part of that launch. Follow
[build and editor setup](../docs/building.md) and [debugging usage](../docs/debugging.md).

The [active implementation](../docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md)
and [population and interaction task](../docs/implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
own current acceptance and the next recovery action. Movement and bounded camera
crossings are recovered; workshop re-entry, pickup, broader interaction/combat,
the populated Debug floor-return issue and full experimental ASan acceptance remain
open. Bare terminal launches without the F5 flags retain their separate baseline.

Original meshes/animation, audio, persistence, optimized-runtime recovery and
64-bit migration remain incomplete. The completed reconstruction milestone and
older journals retain their historical evidence and limits. Keep generated C
repairs scoped and mirrored in `tools/GenerateRecon.js`; verify syntax,
regeneration parity and relevant original-code/runtime regressions.
