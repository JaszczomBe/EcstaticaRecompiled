# Reconstructed Build

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

## SDL Developer Route

Initialize the [SDL submodule](../../dep/README.md), then configure and build with the existing SDL preset:

```sh
git submodule update --init --recursive dep/SDL
cmake --preset linux-clang32-sdl-debug -DECSTATICA2_DATA_DIR=/path/to/Ecstatica2
cmake --build --preset linux-clang32-sdl-debug
./build/Debug/clang21-i386-sdl/e2recomp --run-recon
```

SDL is pinned to 3.4.12. Select `linux-clang32-sdl-debug` in CMake Tools and launch **Ecstatica Recompiled**. The executable follows the selected preset. Supply original data through `ECSTATICA2_DATA_DIR`, an explicit cache argument, or an ignored local user preset; there is no committed personal path.

The single **Ecstatica Recompiled** launch enables `E2R_ACTOR_CUES=1`: a host X/Z map with a cyan Joe square and amber other-actor diamonds. Two hollow enemy-status icons in the current Joe-only scene-175 capture mean **not loaded**, not recovered enemy positions. See [cue usage and limits](../README.md#rebuild-status-and-next-recovery). Game framebuffer pixels are unchanged; SDL dump hashes change when cues are enabled.

## Verification And Status

The 2026-09-14 audit rebuilt default debug, ASan, and SDL debug, passed all 8 arrow-state matrix rows, and captured the scene-175 room background. Living actors remain absent. The later action-context repair verifies the first action-384 update, and the missing-scene message lifetime error is repaired; Task 05 identifies aliased keyframe allocation behind corrupt position events. The corrected mapped-pool scan is gated with action indexing and now exposes an earlier missing actor input in scene-pose restoration (`FUN_00426124`) under SDL/GDB and ASan. Gate-off retains the legacy allocator temporarily. Audio is stubbed and quick-save is a no-op.

```sh
scripts/run-e2-control-matrix.sh
SDL_VIDEODRIVER=dummy timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-scene175 120 7000
```

The regression scripts configure and build the standard Debug and ASan presets unless `E2R_SKIP_BUILD=1`. Both X11 and SDL ASan presets now exist. CTest integration and unified developer validation remain Step 06 work. `scripts/run-e2-runtime-regressions.sh` uses canonical Up and now passes both debug and ASan after Step 07’s actor/action/motion repairs. All 8 arrow rows and the static SDL packet pass. Step 07 Task 02 is complete: the manual screenshot/log agrees with the static scene-175 baseline.

Generator parity is restored: all four artifacts match the committed reference. Follow the [audit's scratch comparison](../../docs/journal/entries/runtime-audit-2026-09-14.md) for future generator changes and [Step 07](../../docs/implementations/playable-sdl-runtime/steps/step-07/step-07-restore-reproducible-runtime-baseline.md) for the completed manual static-scene comparison. The next source task is [Step 08 Task 06](../../docs/implementations/playable-sdl-runtime/steps/step-08/tasks/task-06-recover-scene-activation-pose-inputs.md); Tasks 05 and 01 retain incomplete gated validation. Build commands do not require Ghidra export or regeneration.
