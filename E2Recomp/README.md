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

## Rebuild Status And Next Recovery

The current priority is [Step 09 diagnostic gameplay](../docs/implementations/playable-sdl-runtime/steps/step-09/step-09-enable-diagnostic-gameplay.md). F5 now selects projected cylinders, action indexing/expanded script names and diagnostic mesh/HUD omission. Source-backed node removal and script/event inputs advance Debug past the action-384 modal to the real wait-ending instruction. The [floor-decoder continuation](../docs/journal/entries/courtyard-floor-decoder-2026-10-14.md) restores valid hosted byte reads, removing the forest fallback. Continuous Debug keeps Joe visible in the courtyard after release. F5 explicitly defers automatic background NPC spawning with `E2R_DEFER_BACKGROUND_SPAWNS=1`; existing actors/scripts still update. Up latches without displacement. Experimental ASan reaches a corrupted terminal event link. Movement and traversal remain unresolved.

Linux/i386 default debug, ASan, and SDL debug builds passed the 2026-09-14 audit. The 64-bit executable refuses reconstructed runtime execution. The MSVC x86 script is retained as a historical build route; it was not reverified in the audit.

Recovering behavior still requires original calling conventions, typed data ownership, and accurate helper semantics. The current code includes compatibility implementations alongside unresolved hardware, x87, SIMD, audio, and decompiler-helper stubs. It is not a behavior-complete port.

Generator parity and the full canonical-control debug/ASan wrapper pass again in the 2026-10-14 verification after the actor/action/motion, requester, polygon and rectangle-copy repairs. All 8 arrow rows pass. The current wrapper separates early ASan movement-latch coverage from the later missing-action modal; historical static SDL hashes do not establish current playability. [Task 02](../docs/implementations/playable-sdl-runtime/steps/step-07/tasks/task-02-repair-canonical-control-regressions.md) is complete after the manual screenshot/log confirmed the static scene-175 baseline. Use the [scratch comparison recipe](../docs/journal/entries/runtime-audit-2026-09-14.md) to verify generation changes.

Action ownership, scene-pose inputs, fixed-point camera arithmetic and mapped event metadata are recovered. The corrected action/keyframe/event path remains opt-in (`E2R_ACTION_INDEX_PROBE=1`): polygon/flat-lighting and rectangle-copy inputs are repaired. [Task 11](../docs/implementations/playable-sdl-runtime/steps/step-08/tasks/task-11-recover-dirty-rectangle-copy-inputs.md) passes original-x86 copy/caller comparisons, but real DirectDraw Lock returns destination base/pitch 0/0 and gated SDL still faults at the copy. [Task 12](../docs/implementations/playable-sdl-runtime/steps/step-08/tasks/task-12-recover-directdraw-surface-lock.md) is the next compatibility task within Task 02, before geometry/placement/action validation and child activation. Action indexing remains off for bare terminal launches; F5 now explicitly enables it. The default route now exposes the formerly invisible post-intro action error for `dav:heropick` (384); OK resumes updates at camera 87, whose selection remains unresolved. The new SDL Debug/ASan interaction regression verifies dialog capture, OK dismissal and Escape main-menu entry; see the [requester follow-up](../docs/journal/entries/post-intro-requester-2026-09-15.md). Mirror source-backed repairs in `tools/GenerateRecon.js`; see the [2026-09-15 evidence](../docs/journal/entries/actor-cues-and-projection-2026-09-15.md) for the projection baseline and the [2026-10-14 rectangle evidence](../docs/journal/entries/rectangle-copy-2026-10-14.md) for current verification and remaining limits. Original-x86 lighting comparisons pass normally and with ASan, but the first runtime normal is degenerate and no rendered hero is established.

The single **Ecstatica Recompiled** launch in VS Code supplies `E2R_ACTOR_CYLINDERS=1`, `E2R_ACTION_INDEX_PROBE=1`, `E2R_PROXY_MESH_BYPASS=1` and `E2R_DEFER_BACKGROUND_SPAWNS=1`. Select the SDL i386 Debug preset and restart F5; see [build and editor setup](../docs/building.md). The earlier cue-only F5 configuration caused the user's reported mismatch. The diagnostic state panel reports actual coordinates, action and camera with **CONTROL UNVERIFIED**. It does not force Joe into view. The current next task is post-intro placement/control and motion-query ownership; original DirectDraw Lock and rendering remain separate work.
