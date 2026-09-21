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

The single **Ecstatica Recompiled** launch enables `E2R_ACTOR_CUES=1`: camera-projected ground crosses and uprights, cyan for Joe and amber for other live actors. The grid and fixed enemy-status icons are removed. Default Joe still projects behind the pedestal camera, so expect **0 VISIBLE / 1 BEHIND** until placement/action recovery progresses. See [cue usage and limits](../README.md#rebuild-status-and-next-recovery). Game framebuffer pixels are unchanged; SDL dump hashes change when cues are enabled.

## Verification And Status

The 2026-09-15 continuation builds X11/SDL Debug and ASan and passes the isolated default Debug/ASan wrapper. Projection arithmetic matches 4,096 original-x86 cases; pose and matrix destinations plus mapped event metadata are recovered. The default route still contains only a static Joe position. The gated action route changes that position but crashes in `FUN_00431a7c` polygon inputs; gated headless ASan instead times out in camera 1073. Living actors, correct final placement and full scene-175 ASan readiness remain unproven. Audio is stubbed and quick-save is a no-op. See the [detailed evidence](../../docs/journal/entries/actor-cues-and-projection-2026-09-15.md).

```sh
scripts/run-e2-control-matrix.sh
SDL_VIDEODRIVER=dummy timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-scene175 120 7000
```

The regression scripts configure and build the standard Debug and ASan presets unless `E2R_SKIP_BUILD=1`. Both X11 and SDL ASan presets now exist. CTest integration and unified developer validation remain Step 06 work. `scripts/run-e2-runtime-regressions.sh` uses canonical Up and now passes both debug and ASan after Step 07’s actor/action/motion repairs. All 8 arrow rows and the static SDL packet pass. Step 07 Task 02 is complete: the manual screenshot/log agrees with the static scene-175 baseline.

Generator syntax and scratch regeneration of all four artifacts match the working reconstruction. Follow the [audit's scratch comparison](../../docs/journal/entries/runtime-audit-2026-09-14.md) for future generator changes. The next source task is [Step 08 Task 02](../../docs/implementations/playable-sdl-runtime/steps/step-08/tasks/task-02-recover-joe-geometry-and-rendering.md); Tasks 05 and 01 retain incomplete gated validation. The new cue manual F5 check is pending. Build commands do not require Ghidra export or regeneration.