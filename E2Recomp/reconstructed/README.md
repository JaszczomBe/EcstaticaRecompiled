# Reconstructed Build

<!-- docs-tree:parent -->
[Project README](../../README.md) · [Parent: E2Recomp.exe Reconstruction](../README.md)
<!-- /docs-tree:parent -->

This folder contains the generated Ecstatica II reconstruction and supporting runtime files. Current Linux/i386 builds execute recovered engine logic with original game data. See the [active implementation](../../docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md) for limitations and next tasks.

## Files

- `E2Recomp_recon.c`: normalized Ghidra decompilation.
- `E2Recomp_recon.h`: recovered prototypes, global declarations, Win32 aliases, and decompiler helper macros.
- `E2Recomp_globals.c`: recovered global/data-label definitions.
- `E2Recomp_stubs.c`: isolated stubs for unresolved hardware, x87, SIMD, and decompiler helper symbols.
- `E2Recomp_names.tsv`: first-pass function rename map from string/import heuristics.
- `Build-Reconstructed.ps1`: reproducible 32-bit MSVC build.
- `E2Recomp_rebuilt.exe`: linked reconstructed executable.

## Build

Historical Windows/MSVC route (not reverified by the 2026-09-14 audit), from `C:\ecstatica2`:

```powershell
.\reverse\E2Recomp\reconstructed\Build-Reconstructed.ps1
```

Follow [build setup and editor workflow](../../docs/building.md) for CMake 3.25+, data-path setup, presets and F5. Run Linux commands from the repository root. The 64-bit scaffold initializes data tables but does not execute the reconstructed runtime:

```sh
cmake --preset linux-clang-debug
cmake --build --preset linux-clang-debug
./build/Debug/clang21-native64-x11/e2recomp
```

The recovered executable code still assumes a 32-bit pointer model. Use the
32-bit preset for the experimental startup path:

```sh
cmake --preset linux-clang32-debug
cmake --build --preset linux-clang32-debug
./build/Debug/clang21-i386-x11/e2recomp --run-recon
```

CMake creates `Ecstatica2` inside the selected build directory as a symlink to the
Ecstatica II CD data directory. Override it with:

```sh
cmake --preset linux-clang-debug -DECSTATICA2_DATA_DIR=/path/to/Ecstatica2
```

For the documented Debian setup, install the host tools:

```sh
sudo apt install cmake ninja-build gdb
```

For the 32-bit preset on Debian Trixie, install the i386 development runtime:

```sh
sudo apt install libc6-dev-i386 gcc-multilib
```

Install Clang 21 separately if needed: shared presets require `clang-21` on PATH and reject other major versions. ASan presets also need the matching Clang sanitizer runtime with i386 support. See the [requirements and compiler override workflow](../../docs/building.md#requirements).

The Linux target is a native compile/link scaffold with Win32 compatibility
stubs. It initializes the recovered data tables by default. Pass `--run-recon`
to enter the reconstructed game startup thunk while bypassing the recovered
Windows C runtime startup wrapper. This requires the 32-bit preset; the 64-bit
binary refuses `--run-recon` because the decompiled code contains packed
32-bit function-pointer and COM-vtable assumptions. That path is still
experimental and is not a behavior-complete Linux game port yet.

## SDL Developer Route

Initialize the [SDL submodule](../../dep/README.md), then configure and build with the existing SDL preset:

```sh
git submodule update --init --recursive dep/SDL
cmake --preset linux-clang32-sdl-debug -DECSTATICA2_DATA_DIR=/path/to/Ecstatica2
cmake --build --preset linux-clang32-sdl-debug
./build/Debug/clang21-i386-sdl/e2recomp --run-recon
```

SDL is pinned to 3.4.12. Select `linux-clang32-sdl-debug` in CMake Tools and launch **Ecstatica Recompiled**. The executable follows the selected preset. Supply original data through `ECSTATICA2_DATA_DIR`, an explicit cache argument, or an ignored local user preset; there is no committed personal path.

The single **Ecstatica Recompiled** launch enables `E2R_ACTOR_CYLINDERS=1`, `E2R_ACTION_INDEX_PROBE=1`, `E2R_PROXY_MESH_BYPASS=1` and `E2R_DEFER_BACKGROUND_SPAWNS=0`. It follows the selected SDL Debug executable and requires restarting F5 after a rebuild. Bare terminal launches keep the older baseline. See [launch usage and limits](../README.md#rebuild-status-and-next-recovery).

## Verification and current status

F5 also enables `E2R_RECORD=auto` and `E2R_INSPECT=1`, pins the actual running
executable through its debugger startup hook, and retains debugger stops and an
inspection report. See [build setup](../../docs/building.md) and
[debugging usage](../../docs/debugging.md) for the ordinary investigation workflow.

Follow the [active implementation](../../docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md)
for current runtime acceptance and next tasks. Diagnostic locomotion, populated
camera crossings and bounded workshop activation have evidence. Manual workshop
re-entry, sword pickup, broader interactions/combat, the populated Debug
floor-return issue and full experimental ASan acceptance remain open. Original
actor rendering, audio and save/load are incomplete.

Builds and bounded fixtures do not prove complete gameplay. Use original-code
comparisons, scoped generator parity and relevant regression checks as described
in the root documentation tree. Historical evidence remains in the
[journal](../../docs/journal/journal.md).
