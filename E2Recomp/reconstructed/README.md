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

The single **Ecstatica Recompiled** launch enables `E2R_ACTOR_CYLINDERS=1`, `E2R_ACTION_INDEX_PROBE=1`, `E2R_PROXY_MESH_BYPASS=1` and `E2R_DEFER_BACKGROUND_SPAWNS=1`. It follows the selected SDL Debug executable and requires restarting F5 after a rebuild. Bare terminal launches keep the older baseline. See [launch usage and limits](../README.md#rebuild-status-and-next-recovery).

## Verification And Status

The 2026-10-14 [F5 correction](../../docs/journal/entries/f5-diagnostic-route-2026-10-14.md) supersedes the earlier debugger-stopped cylinder result. Event-node removal, retained action/actor inputs, expanded script names and selected script/cursor ownership have bounded original-x86 coverage. Debug now continuously shows Joe during the pedestal action and reaches opcode `0x75`, wait 0/modal 0. The [floor-decoder continuation](../../docs/journal/entries/courtyard-floor-decoder-2026-10-14.md) accepts valid hosted byte streams and restores courtyard floor/view selection. F5 explicitly defers automatic background spawning while its full activation path remains unrecovered. Debug remains in the courtyard after release, but movement is unproven; experimental ASan faults in a terminal action-event link. NPC range/query/placement comparisons pass normally and under ASan. Original rendering and gameplay remain open.

The 2026-09-15 continuation builds X11/SDL Debug and ASan and passes the isolated default Debug/ASan wrapper. Projection arithmetic matches 4,096 original-x86 cases; pose and matrix destinations plus mapped event metadata are recovered. The default route still contains only a static Joe position. After the sub-intro, it now displays the previously invisible “Can’t load action” error for `dav:heropick` (384). Click OK to resume updates; the resulting camera-87 rooftop transition remains unresolved. The 2026-09-21 continuation restores polygon/mode/reference inputs and passes 576 original-x86 routing cases plus twelve temporary-record checks, normally and under ASan. The subsequent flat-lighting repair passes 10,240 original-x86 angle cases, 16,384 rotations and 8,192 lighting-index cases, normally and under ASan. Gated SDL now returns from lighting and crashes later in framebuffer copying at `FUN_00418514`; gated SDL ASan instead times out in camera 1073 before reaching geometry. See the [lighting evidence](../../docs/journal/entries/polygon-lighting-2026-09-21.md). The first proven runtime normal is degenerate, so passing lighting does not prove valid geometry. Living actors, correct final placement and full scene-175 ASan readiness remain unproven. Audio is stubbed and quick-save is a no-op. See the [detailed evidence](../../docs/journal/entries/actor-cues-and-projection-2026-09-15.md).

```sh
scripts/run-e2-control-matrix.sh
SDL_VIDEODRIVER=dummy timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-scene175 120 7000
```

The regression scripts configure and build the standard Debug and ASan presets unless `E2R_SKIP_BUILD=1`. Both X11 and SDL ASan presets now exist. CTest integration and unified developer validation remain Step 06 work. `scripts/run-e2-runtime-regressions.sh` passes canonical-Up latch checks in Debug and early ASan, plus a long-delay ASan missing-action/modal check. All 8 arrow rows pass. These checks establish input state, not actor motion. Step 07’s static baseline remains a historical completed milestone; the repaired error dialog now changes the captured game pixels.

The new `python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl/e2recomp` check captures the actual SDL dialog, clicks OK and verifies resumed updates plus Escape main-menu entry. It also passes against `build/Debug/clang21-i386-sdl-asan/e2recomp`. It requires GDB/ptrace and original data; only LeakSanitizer is disabled under ptrace. See the [requester evidence and limits](../../docs/journal/entries/post-intro-requester-2026-09-15.md).

Generator syntax and scratch regeneration of all four artifacts match the working reconstruction. Follow the [audit's scratch comparison](../../docs/journal/entries/runtime-audit-2026-09-14.md) for future generator changes. The 2026-10-14 rectangle-copy repair passes 2,048 original-x86 copy/ownership cases and 256 dirty-list dispatch cases, normally and with ASan. Four builds, parity, default regressions, eight arrow rows and both requester checks pass again. The actual gated copy still faults because DirectDraw Lock is a generic no-output stub returning base/pitch 0/0. The next task is [Step 08 Task 12 compatibility Lock](../../docs/implementations/playable-sdl-runtime/steps/step-08/tasks/task-12-recover-directdraw-surface-lock.md), within Task 02 geometry recovery; Tasks 05 and 01 retain incomplete gated validation. The earlier reconstruction recording confirms cue replacement; the 2026-09-21 screenshots confirm dialog presentation and the camera-87 transition after OK, with the error still visible and Joe absent. Manual Escape confirmation remains pending. Build commands do not require Ghidra export or regeneration.
