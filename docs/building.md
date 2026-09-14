# Build And Debug The Developer Runtime

The everyday configuration is **Debug · Clang 21 · i386 · SDL**, selected through CMake presets. The single VS Code launch **Ecstatica Recompiled** follows the selected CMake executable and enables actor cues. The runtime remains experimental; a successful build or static capture does not prove playable behavior.

## Requirements

- Linux, CMake 3.25 or newer, Ninja, Clang, and GDB. The current validated compiler is Clang 21.1.8; shared presets resolve `clang-21` from PATH and reject a compiler whose major version is not 21. Changing compiler versions needs a separate build directory and regression verification.
- 32-bit C development libraries and the matching Clang AddressSanitizer runtime for ASan presets. On the current Debian installation the multilib prerequisites include `libc6-dev-i386` and `gcc-multilib`; ASan availability is checked by a compile/link probe at configure time.
- The SDL submodule and the full original Ecstatica II data directory.
- VS Code extensions CMake Tools and C/C++; workspace recommendations include both.

## Initial Configuration

Run from the repository root:

```sh
git submodule update --init --recursive dep/SDL
export ECSTATICA2_DATA_DIR=/path/to/Ecstatica2
cmake --preset linux-clang32-sdl-debug
cmake --build --preset linux-clang32-sdl-debug
E2R_ACTOR_CUES=1 ./build/Debug/clang21-i386-sdl/e2recomp --run-recon
```

There is no committed personal data path. CMake reads `ECSTATICA2_DATA_DIR` from the environment on first configuration and stores it in that build's cache. An explicit `-DECSTATICA2_DATA_DIR=...` overrides the cache. Existing valid caches continue to work without exporting the variable; each fresh build directory needs a data path. CMake creates the build-local `Ecstatica2` symlink.

For persistent personal overrides, use the ignored `CMakeUserPresets.json`, for example:

```json
{
  "version": 6,
  "configurePresets": [{
    "name": "local-sdl-debug",
    "inherits": "linux-clang32-sdl-debug",
    "displayName": "Debug · Clang 21 · i386 · SDL · local",
    "binaryDir": "${sourceDir}/build/Debug/clang21-i386-sdl-local",
    "cacheVariables": {
      "ECSTATICA2_DATA_DIR": "/your/path/to/Ecstatica2"
    }
  }],
  "buildPresets": [{
    "name": "local-sdl-debug",
    "configurePreset": "local-sdl-debug",
    "targets": ["e2recomp"]
  }]
}
```

This local preset explicitly uses `build/Debug/clang21-i386-sdl-local` so it cannot overwrite the standard preset’s cache. It does not configure the standard regression directories; configure those with the environment or explicit data-path argument as below.

## Configurations

| Configure/build preset | Build type | Directory under `build/` |
| --- | --- | --- |
| `linux-clang32-sdl-debug` | Debug | `Debug/clang21-i386-sdl` |
| `linux-clang32-sdl-release` | Release | `Release/clang21-i386-sdl` |
| `linux-clang32-sdl-relwithdebinfo` | RelWithDebInfo | `RelWithDebInfo/clang21-i386-sdl` |
| `linux-clang32-sdl-minsizerel` | MinSizeRel | `MinSizeRel/clang21-i386-sdl` |
| `linux-clang32-sdl-debug-asan` | Debug + ASan | `Debug/clang21-i386-sdl-asan` |
| `linux-clang32-debug` | Debug | `Debug/clang21-i386-x11` |
| `linux-clang32-debug-asan` | Debug + ASan | `Debug/clang21-i386-x11-asan` |
| `linux-clang-debug` | Debug, native build only | `Debug/clang21-native64-x11` |
| `linux-clang-sdl-debug` | Debug, native build only | `Debug/clang21-native64-sdl` |

Use matching configure and build presets (`cmake --preset NAME`, then `cmake --build --preset NAME`). Hidden bases share Ninja, compiler and architecture flags. The i386 flags apply to dependencies as well as the application. Each configuration/compiler/backend/sanitizer combination has an isolated cache and executable.

Debug remains the runtime reference. Release optimizes for execution speed; RelWithDebInfo combines optimization and debug symbols; MinSizeRel favors executable size. These use CMake's standard Clang flags. Optimized builds must be evaluated separately: unresolved decompiler inputs and undefined behavior can behave differently under optimization. A successful optimized build is not gameplay acceptance. **Current verification: all three optimized configurations build but crash during startup before a scene capture.** Debug remains the usable reference; the optimized presets retain their actual optimization flags for future investigation.

ASan (AddressSanitizer) adds compiler/runtime checks for memory errors, such as out-of-bounds accesses and expired object lifetimes. It has time/memory overhead and changes instrumentation and memory layout, so it gets its own build directory. It is independent of build type; the provided sanitizer presets are explicitly Debug + ASan. `E2R_ENABLE_ASAN` instruments the application and host code; SDL itself is not instrumented by that option. Existing generated-code sanitizer exclusions remain unchanged.

The X11 presets supply the established regression-script baseline, using the same game code with another host backend. Their display names no longer say “regression”; their descriptions explain that role. The 64-bit executables refuse reconstructed game execution. Ghidra export and reconstruction generation remain explicit targets; normal builds do not regenerate source.

## Compiler Selection

The preset selector/status bar now names **Clang 21**. This is a checked compiler-family label, not a dynamically detected patch-version widget. Configuration reports the full resolved version/path; the current baseline is 21.1.8.

To try another installed Clang version, inherit a shared preset in `CMakeUserPresets.json` and explicitly override all of these:

- `CMAKE_C_COMPILER`, for example `clang-20` if installed.
- `E2R_EXPECTED_CLANG_MAJOR`, for example `20`.
- `displayName`, including the actual compiler family.
- `binaryDir`, for example `${sourceDir}/build/Debug/clang20-i386-sdl-local`.

Also give the local configure/build presets distinct names. Alternative compiler versions are experiments until their builds and runtime regressions pass. CMake Tools' separate compiler-kit picker is unavailable in preset mode; selecting a version-specific preset provides the choice without a launch script.

## Migration From The Flat Build Layout

Reconfigure the desired presets before using F5 or the scripts. New output directories do not inherit cached game-data paths: provide `ECSTATICA2_DATA_DIR` or an explicit/local cache value. The old `build/linux-clang*` directories are left untouched as previous-build evidence; current presets and regression scripts use the configuration-first paths above.

The former `linux-clang32-asan` and `linux-clang32-sdl-asan` preset names are replaced by `linux-clang32-debug-asan` and `linux-clang32-sdl-debug-asan`. Reselect a matching configure/build preset in VS Code if it remembered a removed name. Historical journals retain their original commands and paths; use this guide for current commands.

## VS Code

1. After initial configuration, run **CMake: Select Configure Preset** and choose **Debug · Clang 21 · i386 · SDL**. Existing VS Code selections may still point to an older/native preset; make this selection once.
2. Select the matching build preset if prompted, and select the `e2recomp` launch target.
3. Press F5 using **Ecstatica Recompiled**. CMake Tools builds the selected target, resolves its executable and working directory, and launches GDB with `--run-recon` and `E2R_ACTOR_CUES=1`.
4. Ctrl+Shift+B uses the single CMake build task for the active build preset. There are no shell configure/build launch wrappers or duplicate SDL/X11 launch entries.

Changing the selected preset changes F5's executable. CMake Tools must have successfully configured that preset before its target commands can resolve. F5 uses its build-before-run integration; no additional pre-launch build task is attached.

Workspace settings show the configure preset, Build, and launch target in the status bar. Other controls remain in the CMake Tools sidebar/Command Palette. The kit/Debug-selector pair in undertone belongs to its non-preset VS Code mode; this workspace deliberately stays in preset mode. IntelliSense uses CMake Tools' selected configuration and compile commands.

The cue map is a host diagnostic: cyan Joe, amber other live actors. Two hollow enemy-status icons mean the expected enemies are not instantiated. They do not establish enemy positions or actual character rendering. Cues are enabled by F5; terminal launches remain opt-in.

## Verification

From the repository root, with the data environment set for fresh directories:

```sh
export ECSTATICA2_DATA_DIR=/path/to/Ecstatica2
scripts/run-e2-runtime-regressions.sh
scripts/run-e2-control-matrix.sh
cmake --preset linux-clang32-sdl-debug-asan
cmake --build --preset linux-clang32-sdl-debug-asan
SDL_VIDEODRIVER=dummy E2R_ACTOR_CUES=1 timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-build-cues 120 7000
```

The existing regression scripts now configure/build both standard X11 presets, including ASan; `E2R_SKIP_BUILD=1` skips that preparation when builds are current. They retain their input, surface, and sanitizer assertions. There are no CTest/package/workflow presets yet. Runtime probe execution requires an environment that supports the reconstruction's i386 fixed-address mappings.

Use fresh capture prefixes and inspect the actual scene/actor state. ASan and gated action-index paths have known runtime limitations documented in the [active implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md). Manual F5 is still the final check of the actual editor integration; shell probes cannot establish VS Code's selected state.
