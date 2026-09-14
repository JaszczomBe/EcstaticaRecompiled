# Linux Portability


## 2026-09-14 - Build Types, Configuration-First Directories And Clang Family Selection

Area: preset hierarchy, compiler visibility and regression path migration.

Problem: all exposed configurations were Debug, output paths did not group by build type, and the unversioned `clang` selector did not identify its compiler family in the status bar. ASan names omitted their Debug build type.

Change: added SDL Release/RelWithDebInfo/MinSizeRel presets; renamed ASan presets to explicit `*-debug-asan`; shared presets use `clang-21` and `E2R_EXPECTED_CLANG_MAJOR=21`, checked against CMake's actual compiler identity/version. Outputs now use `build/<configuration>/clang21-<architecture>-<backend>[-asan]`. Display names begin with the configuration and include Clang 21; X11 names omit the “regression” suffix while descriptions retain their testing role. The two regression scripts and current Step 08 commands follow the new paths. Old build directories and historical journal commands are preserved. No reconstruction or generator code was changed in this pass.

Developer Workflow Impact: reselect/reconfigure **Debug · Clang 21 · i386 · SDL** and its matching build preset in VS Code. Fresh directories require a data-path setting. Alternative compiler families can be selected through a local inherited preset with explicit compiler, expected major, display name and isolated binary directory; exact patch versions remain in configure diagnostics. See [build setup](../../building.md).

Validation: all nine configure/build presets pass with Clang 21.1.8. Compile commands confirm Debug, Release `-O3`, RelWithDebInfo `-O2 -g`, MinSizeRel `-Os`, and separate Debug ASan instrumentation. A deliberate advertised-major mismatch (20 versus installed 21) is rejected at configure time. The complete configure/build/debug-ASan regression wrapper and all eight arrow cases pass from the new directories. SDL Debug captures scene 175 with Joe cues; SDL Debug ASan's canonical-control probe passes without sanitizer errors on its known scene-87 route and emits cue state. Logs: `/tmp/e2-config-types-*.log`, `/tmp/e2-types-{regression,controls,debug,sdl-asan}.log`.

Optimized runtime limit: Release, RelWithDebInfo and MinSizeRel each terminate with SIGSEGV before producing a scene capture. A bounded RelWithDebInfo GDB run stops at libc's `stderr` address with an unusable backtrace containing argument-string words; it does not identify a reliable source-level cause. These are failed runtime probes despite successful compilation, explicitly stated in preset descriptions and build documentation. No `-O0` override or game-code workaround hides the result. Optimized startup recovery is a separate investigation; everyday recovery stays on Debug. Evidence: `/tmp/e2-types-{Release,RelWithDebInfo,MinSizeRel}.log`, `/tmp/e2-types-optimized-gdb.log`.

Reproduce an optimized probe with `SDL_VIDEODRIVER=dummy timeout 80 build/RelWithDebInfo/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-opt-check 60 1000`. A debugger can exit zero after catching SIGSEGV; inspect the inferior stop reason. Actual editor F5 interaction remains a manual check; target/path/settings contracts were verified without changing persisted VS Code selections.


## 2026-09-14 - Presets Own Builds And The Single F5 Launch

Area: CMake configuration, VS Code integration, and developer bootstrap.

Problem: duplicated presets omitted ASan, committed a personal data path, and advertised CMake 3.20 despite schema 6 requiring 3.25. Fixed F5 executable/build paths could disagree with the selected preset. Two SDL launch entries had become identical. Global CMake status visibility exposed unused test/package/workflow selectors.

Change: shared Linux/Clang/i386 preset bases preserve existing output directories; SDL Debug is listed first, with SDL ASan and standard X11 Debug/ASan alongside clearly labelled native build-only diagnostics. ASan is a target-scoped option with a configure-time link check. Compiler and pointer-width diagnostics make the Clang/i386 policy explicit. Personal data paths come from environment, cache arguments or ignored CMakeUserPresets.json. One F5 entry resolves the selected CMake executable/directory with build-before-run, keeps GDB and actor cues, and uses no shell pre-launch wrapper. Ctrl+Shift+B builds the selected preset. Workspace settings select preset mode, compact status visibility and CMake-driven IntelliSense.

The only source change moves two existing host input-probe extern declarations outside an i386-only block. Native 64-bit compilation exposed their existing shared use; their definitions and behavior are unchanged. No reconstructed C/header/generator changes were made.

Developer Workflow Impact: select **Clang · i386 · SDL · Debug** once in CMake Tools, select `e2recomp`, and use the single **Ecstatica Recompiled** F5 entry. Existing editor preset selections are not overwritten. A fresh build directory needs its own data-path configuration. [Build instructions](../../building.md) cover environment/local presets and diagnostic configurations. Regression scripts now configure and build their existing Debug/ASan presets unless explicitly skipped.

Validation: all six configure/build presets pass with Clang 21.1.8; fresh i386 Debug configuration/build and fresh SDL ASan configuration/build pass. Compile commands confirm i386 flags on the executable and SDL, and ASan instrumentation only in the ASan application targets. Missing data and a wrong required pointer width fail configuration with actionable messages. Native 64-bit executables still reject `--run-recon`. JSON/settings schema inspection, shell syntax, documentation links and whitespace checks pass.

The standard debug/ASan regression wrapper and all eight arrow-matrix rows pass. A final wrapper run with build skipping disabled also passes the complete configure/build/run flow (`/tmp/e2-presets-integrated.log`). SDL Debug captures scene 175 with Joe cues and indexed hash `321e33d6`. SDL ASan's canonical Space/Up probe exits 0 without a sanitizer report, captures a nonblank scene-87 surface (`bf4a8e25`) and emits cue state. This preserves the known scene distinction; it does not resolve action-index/scene-pose fidelity. Evidence: `/tmp/e2-presets-{regression,controls,sdl,sdl-asan}.log`, `/tmp/e2-presets-sdl-state.txt`, `/tmp/e2-presets-sdl-asan-cues-state.txt`, and `/tmp/e2-final-build-*.log`.

Limits: shell checks verify binaries, launch arguments/environment and CMake target-resolution contracts, not the actual VS Code F5 interaction or its persisted selection. That manual editor check remains user-visible. Step 06's unified validation/packaging acceptance and Step 08's source recovery remain open. The undertone reference was read-only; no launch scripts or kit/variant mode were imported.

## Purpose

Track non-gameplay scaffolding needed to build and launch the reconstructed runtime on Linux with CMake, Clang, Ninja, and VS Code.

## Current Topics

- 32-bit Linux Clang preset and dependency notes.
- Automatic Ecstatica II data symlink under the CMake build tree.
- VS Code `tasks.json` and single F5 launch entry.
- Win32 compatibility stubs in `E2Recomp/platform`.
- Address-space mapping for legacy `0x00400000..0x00b00000` data/code expectations.

## Recent Entries

### 2026-07-16

1. Added `--dump-frame <path.pgm> [seconds]` to the native Linux launcher as a bounded host-side inspection hook.
2. The probe starts the reconstructed runtime, waits for the requested delay, scans the known legacy surface pages for a nonblank frame, writes a raw PGM dump, and exits without adding backend-specific presentation calls to reconstructed game logic.
3. Verified the ASan build can dump a coherent `640x480` Ecstatica II title-logo frame from surface 3. The image artifact was written to `/tmp/e2-step08-frame-asan.pgm` and locally converted to `/tmp/e2-step08-frame-asan.png` with `pnmtopng`.
4. The debug build compiles, but its `--dump-frame` mode currently exits immediately with code `112` before the delayed dump thread fires. Treat this as a runtime parity caveat for the next input/presentation stabilization pass.

### 2026-07-14

1. Reframed Linux portability as the current proof platform rather than the final host abstraction.
2. Adopted a layered direction: reconstructed game logic remains original-shaped; Win32, DirectDraw, DirectSound, and CRT shims remain the game-facing compatibility surface; host-specific implementation should move behind a replaceable backend boundary.
3. Deferred SDL until the runtime has a stable loop, inspectable frame path, and clearer DirectDraw/DirectSound compatibility needs. SDL should back window, input, timing, presentation, and audio, not be called directly from reconstructed game logic.
4. Recorded the portability ladder as Linux/i386 first, backend-neutral host layer second, SDL-backed multi-platform work later, because fixed-address, 32-bit pointer, and legacy memory-layout assumptions still constrain true multi-platform support.

### 2026-07-13

1. The native Linux launcher now enters `E2RECOMP_DATA_DIR` before reconstructed startup, so relative game-data opens resolve through the build-tree `Ecstatica2` symlink.
2. `CreateFileA` now normalizes backslashes and resolves read-only file paths case-insensitively, matching the original Windows data-open behavior closely enough to open uppercase CD assets from lowercase reconstructed requests.
3. Top-level `CreateWindowExA` now dynamically loads X11 and maps a visible host window for the original Ecstatica II window request, with a headless HWND fallback when X11 is unavailable.
4. The Linux launcher now maps the legacy VGA-style `0xa0000..0x100000` address range used by startup blits.

Use the Linux portability template in [journal.template.md](../../templates/journal.template.md) for new entries.
