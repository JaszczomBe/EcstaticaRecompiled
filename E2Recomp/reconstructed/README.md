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

On Linux, the repository root now has a CMake/Clang scaffold:

```sh
cmake --preset linux-clang-debug
cmake --build --preset linux-clang-debug
./build/linux-clang-debug/e2recomp
```

The recovered executable code still assumes a 32-bit pointer model. Use the
32-bit preset for the experimental startup path:

```sh
cmake --preset linux-clang32-debug
cmake --build --preset linux-clang32-debug
./build/linux-clang32-debug/e2recomp --run-recon
```

CMake creates `build/linux-clang-debug/Ecstatica2` as a symlink to the
Ecstatica II CD data directory. Override it with:

```sh
cmake --preset linux-clang-debug -DECSTATICA2_DATA_DIR=/path/to/Ecstatica2
```

For a fresh Debian Trixie install, the expected packages are:

```sh
sudo apt install cmake ninja-build clang gdb
```

For the 32-bit preset on Debian Trixie, install the i386 development runtime:

```sh
sudo apt install libc6-dev-i386 gcc-multilib
```

The Linux target is a native compile/link scaffold with Win32 compatibility
stubs. It initializes the recovered data tables by default. Pass `--run-recon`
to enter the reconstructed game startup thunk while bypassing the recovered
Windows C runtime startup wrapper. This requires the 32-bit preset; the 64-bit
binary refuses `--run-recon` because the decompiled code contains packed
32-bit function-pointer and COM-vtable assumptions. That path is still
experimental and is not a behavior-complete Linux game port yet.

## Status

The project now compiles and links with MSVC x86. The result is a rebuildable reconstruction scaffold, not a behavior-complete port. The stubs in `E2Recomp_stubs.c` must be replaced with real implementations or import-library bindings before runtime behavior can be expected to match the original executable.
