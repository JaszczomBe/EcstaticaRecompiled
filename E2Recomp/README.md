# E2Recomp.exe Reconstruction

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

By default this imports `/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` and writes
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

## Rebuild Status And Next Recovery

Linux/i386 default debug, ASan, and SDL debug builds passed the 2026-09-14 audit. The 64-bit executable refuses reconstructed runtime execution. The MSVC x86 script is retained as a historical build route; it was not reverified in the audit.

Recovering behavior still requires original calling conventions, typed data ownership, and accurate helper semantics. The current code includes compatibility implementations alongside unresolved hardware, x87, SIMD, audio, and decompiler-helper stubs. It is not a behavior-complete port.

Generator parity and the full canonical-control debug/ASan wrapper now pass after Step 07’s actor/action/motion repairs. All 8 arrow rows and the default SDL static packet pass. [Task 02](../docs/implementations/playable-sdl-runtime/steps/step-07/tasks/task-02-repair-canonical-control-regressions.md) is complete after the manual screenshot/log confirmed the static scene-175 baseline. Use the [scratch comparison recipe](../docs/journal/entries/runtime-audit-2026-09-14.md) to verify generation changes.

Action 384's loader/callback ownership and the missing-scene message list are recovered. [Step 08 Task 05](../docs/implementations/playable-sdl-runtime/steps/step-08/tasks/task-05-recover-post-intro-scene-selection.md) traces bad position events to a keyframe allocator reading host globals instead of mapped pool flags. Its corrected scan shares `E2R_ACTION_INDEX_PROBE=1`; distinct keys now expose an earlier actor-input crash in scene-pose restoration under SDL/GDB and ASan. [Task 06](../docs/implementations/playable-sdl-runtime/steps/step-08/tasks/task-06-recover-scene-activation-pose-inputs.md) is next, then Task 05/01 validation and Joe geometry. The default allocator remains a temporary baseline compromise. Mirror source-backed repairs in `tools/GenerateRecon.js`; global renaming, broad struct cleanup, and platform migration remain later work.

Both **Ecstatica Recompiled (SDL)** and **Ecstatica Recompiled (SDL + actor cues)** in VS Code enable visual cues. Restart the debug session after changing launch settings. For a terminal launch, run `E2R_ACTOR_CUES=1 ./build/linux-clang32-sdl-debug/e2recomp --run-recon`. A cyan square marks Joe on a top-down X/Z map; amber diamonds mark other table-confirmed live actors. It is centered on Joe's home with a ±8192 range; `+` marks clipped positions. The current scene-175 runtime has no instantiated enemies, so two hollow status icons say **2 ENEMIES NOT LOADED**. These are not enemy positions or camera-projected game geometry. The overlay changes only SDL presentation; visibility packets keep the original game surfaces and add `actor_cue` state when enabled.
