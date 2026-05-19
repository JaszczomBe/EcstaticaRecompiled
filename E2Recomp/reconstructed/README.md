# Reconstructed Build

This folder contains the current compileable reconstruction of `E2Recomp.exe`.

## Files

- `E2Recomp_recon.c`: normalized Ghidra decompilation.
- `E2Recomp_recon.h`: recovered prototypes, global declarations, Win32 aliases, and decompiler helper macros.
- `E2Recomp_globals.c`: recovered global/data-label definitions.
- `E2Recomp_stubs.c`: isolated stubs for unresolved hardware, x87, SIMD, and decompiler helper symbols.
- `E2Recomp_names.tsv`: first-pass function rename map from string/import heuristics.
- `Build-Reconstructed.ps1`: reproducible 32-bit MSVC build.
- `E2Recomp_rebuilt.exe`: linked reconstructed executable.

## Build

From `C:\ecstatica2`:

```powershell
.\reverse\E2Recomp\reconstructed\Build-Reconstructed.ps1
```

## Status

The project now compiles and links with MSVC x86. The result is a rebuildable reconstruction scaffold, not a behavior-complete port. The stubs in `E2Recomp_stubs.c` must be replaced with real implementations or import-library bindings before runtime behavior can be expected to match the original executable.
