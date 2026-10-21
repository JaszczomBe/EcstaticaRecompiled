# Build And Debug The Developer Runtime

The everyday configuration is **Debug · Clang 21 · i386 · SDL**, selected through CMake presets. The single VS Code launch **Ecstatica Recompiled** follows the selected CMake executable and enables the experimental cylinder/action route. The runtime remains experimental; a successful build or static capture does not prove playable behavior.

## Requirements

- Linux, CMake 3.25 or newer, Ninja, Clang, and GDB. The current validated compiler is Clang 21.1.8; shared presets resolve `clang-21` from PATH and reject a compiler whose major version is not 21. Changing compiler versions needs a separate build directory and regression verification.
- 32-bit C and C++ development libraries and the matching Clang AddressSanitizer runtime for ASan presets. Debian's usual prerequisites include `libc6-dev-i386` and `g++-multilib`. The logger needs C++20 and a standard library with `std::format`; configure checks compilation and linking. Where only the i386 C++ runtime is installed, CMake can discover the matching installed GCC headers and runtime without versioned paths in the presets. Configure reports any fallback it uses.
- The SDL submodule and the full original Ecstatica II data directory, including root `OFFSETS` alongside `Files/ECSTATIC`; the recovered-action route uses its original visibility directory for placed objects.
- VS Code extensions CMake Tools and C/C++; workspace recommendations include both.

## Initial Configuration

Run from the repository root:

```sh
git submodule update --init --recursive dep/SDL
mkdir -p ~/.ecstatica2
printf '%s\n' /path/to/Ecstatica2 > ~/.ecstatica2/game-data-dir
cmake --preset linux-clang32-sdl-debug
cmake --build --preset linux-clang32-sdl-debug
E2R_ACTOR_CYLINDERS=1 E2R_ACTION_INDEX_PROBE=1 E2R_PROXY_MESH_BYPASS=1 \
  E2R_DEFER_BACKGROUND_SPAWNS=0 \
  ./build/Debug/clang21-i386-sdl/e2recomp --run-recon
```

There is no committed personal data path. Save the full original-data path on one line in `~/.ecstatica2/game-data-dir` once; all presets, including VS Code launched from the desktop, can then configure without a terminal environment. CMake creates the build-local `Ecstatica2` symlink.

An explicit/nonempty `ECSTATICA2_DATA_DIR` cache value takes precedence. When that value is absent or empty, CMake tries the `ECSTATICA2_DATA_DIR` environment variable, then the saved file. This also repairs a cache left empty by an earlier failed configure. `-DECSTATICA2_DATA_DIR=...` remains a per-build override; `ECSTATICA2_DATA_CONFIG` can select a different local text file. To change a populated cache to the saved setting, remove its data-path entry with `cmake --preset NAME -U ECSTATICA2_DATA_DIR`.

F5 supplies projected cylinders, recovered action indexing/expanded script names, diagnostic mesh/HUD omission and enabled background population (`E2R_DEFER_BACKGROUND_SPAWNS=0`). Original preloaded objects also activate through their placement and visibility records; the sword beside the blacksmith workbench has [bounded Debug/ASan evidence](journal/entries/blacksmith-sword-activation-2026-10-20.md). Movement and courtyard round trips are verified, while pickup, combat, original models and full experimental ASan acceptance remain open. `E2R_ACTOR_CUES=1` retains the earlier crosses for baseline investigation.

Cylinder labels describe runtime state: cyan `JOE`, amber `SPAWN` for terrain-generated actors, amber `ACTOR` for other represented/scripted actors, and neutral green-grey `OBJECT` for actors without an installed representation or owning script scene. They do not classify hostility. The overlay respects the original actor visibility flag; `ACTIVE` includes objects and hidden actors, while `GENERATED` separately counts terrain-generated actors. Wall occlusion and real mesh bounds remain absent. The [workshop crash/visibility continuation](journal/entries/workshop-initialization-and-actor-visibility-2026-10-20.md) records the matching initialization crash repair and original four-generated-actor cap audit.

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

This local preset explicitly uses `build/Debug/clang21-i386-sdl-local` so it cannot overwrite the standard preset’s cache. Its override applies only to that preset. The saved `~/.ecstatica2/game-data-dir` setting also supplies the standard regression presets.

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

ASan (AddressSanitizer) adds compiler/runtime checks for memory errors, such as out-of-bounds accesses and expired object lifetimes. It has time/memory overhead and changes instrumentation and memory layout, so it gets its own build directory. It is independent of build type; the provided sanitizer presets are explicitly Debug + ASan. `E2R_ENABLE_ASAN` instruments the application, host code, runtime options and logger; SDL itself is not instrumented by that option. Logger and runtime options are enabled in both Debug and ASan presets. Existing generated-code sanitizer exclusions remain unchanged.

The X11 presets supply the established regression-script baseline, using the same game code with another host backend. Their display names no longer say “regression”; their descriptions explain that role. The 64-bit executables refuse reconstructed game execution. Ghidra export and reconstruction generation remain explicit targets; normal builds do not regenerate source.

## Compiler Selection

The preset selector/status bar now names **Clang 21**. This is a checked compiler-family label, not a dynamically detected patch-version widget. Configuration reports the full resolved version/path; the current baseline is 21.1.8.

To try another installed Clang version, inherit a shared preset in `CMakeUserPresets.json` and explicitly override all of these:

- `CMAKE_C_COMPILER`, for example `clang-20` if installed.
- `CMAKE_CXX_COMPILER`, for example `clang++-20`, matching the C compiler.
- `E2R_EXPECTED_CLANG_MAJOR`, for example `20`.
- `displayName`, including the actual compiler family.
- `binaryDir`, for example `${sourceDir}/build/Debug/clang20-i386-sdl-local`.

Also give the local configure/build presets distinct names. Alternative compiler versions are experiments until their builds and runtime regressions pass. CMake Tools' separate compiler-kit picker is unavailable in preset mode; selecting a version-specific preset provides the choice without a launch script.

## Migration From The Flat Build Layout

Reconfigure the desired presets before using F5 or the scripts. New output directories read the saved `~/.ecstatica2/game-data-dir` setting, or an environment/explicit cache override. The old `build/linux-clang*` directories are left untouched as previous-build evidence; current presets and regression scripts use the configuration-first paths above.

The former `linux-clang32-asan` and `linux-clang32-sdl-asan` preset names are replaced by `linux-clang32-debug-asan` and `linux-clang32-sdl-debug-asan`. Reselect a matching configure/build preset in VS Code if it remembered a removed name. Historical journals retain their original commands and paths; use this guide for current commands.

## VS Code

1. After initial configuration, run **CMake: Select Configure Preset** and choose **Debug · Clang 21 · i386 · SDL**. Existing VS Code selections may still point to an older/native preset; make this selection once.
2. Select the matching build preset if prompted, and select the `e2recomp` launch target.
3. Press F5 using **Ecstatica Recompiled**. CMake Tools builds the selected target, resolves its executable and working directory, and launches GDB with `--run-recon` and `E2R_ACTOR_CYLINDERS=1 E2R_ACTION_INDEX_PROBE=1 E2R_PROXY_MESH_BYPASS=1 E2R_DEFER_BACKGROUND_SPAWNS=0 E2R_STARTUP_LOGO_DELAY_MS=0`.
4. Ctrl+Shift+B uses the single CMake build task for the active build preset. There are no shell configure/build launch wrappers or duplicate SDL/X11 launch entries.

Changing the selected preset changes F5's executable. CMake Tools must have successfully configured that preset before its target commands can resolve. F5 uses its build-before-run integration; no additional pre-launch build task is attached.

The logger starts automatically for that same launch, including Debug + ASan. It needs no extra F5 arguments or separate logger build task. Reconfigure the selected preset after updating this branch so its logger and C++ settings take effect.

F5 appends `detect_leaks=0` to inherited `ASAN_OPTIONS`: LeakSanitizer cannot check leaks while GDB uses ptrace. AddressSanitizer memory checks remain enabled. Terminal launches keep their normal leak-checking behavior unless explicitly overridden.

`E2R_STARTUP_LOGO_DELAY_MS=0` removes the startup logo waits while retaining logo/resource initialization. Set it to `5000` or remove it to restore the default waits. Space still skips the horseback sequence through its original skip script; the pedestal release sequence continues normally. There is no supported full-intro skip flag yet. See the [startup-skip assessment and measured Debug/ASan results](journal/entries/startup-skip-feasibility-2026-10-20.md).

Workspace settings show the configure preset, Build, and launch target in the status bar. Other controls remain in the CMake Tools sidebar/Command Palette. The kit/Debug-selector pair in undertone belongs to its non-preset VS Code mode; this workspace deliberately stays in preset mode. IntelliSense uses CMake Tools' selected configuration and compile commands.

Cylinders are host diagnostics tied to validated actor coordinates. Movement, populated courtyard crossings and bounded workshop activation are verified; manual workshop re-entry, sword pickup and full experimental ASan acceptance remain open. Follow [Step 09 Task 09](implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md) for the current gameplay frontier. Restart F5 after rebuilding.

## Runtime Logging

F5 and terminal launches write rotating `e2recomp_*.log` files under `~/.ecstatica2/logs`. The output directory resolves before entering the original game-data directory, so changing the selected build or launch working directory does not relocate logs. Each file rotates at 5 MiB. This is file logging, not a route recorder or a guarantee that asynchronous records survive a crash.

The file includes the startup record and existing diagnostics emitted through the runtime's stderr wrapper, under `Runtime.Diagnostic`. Console diagnostics still appear once, with their existing text. This does not capture arbitrary library stderr, ASan's own reports, or every gameplay event; keep the debugger/probe output for sanitizer failures.

Override output and filtering with `E2R_DATA_DIR`, `E2R_LOG_LEVEL` and `E2R_LOG_DISABLE_MODULES`, or pass the corresponding CLI options **before** the runtime command. CLI options take precedence over environment defaults. For example:

```sh
./build/Debug/clang21-i386-sdl/e2recomp \
  --data-dir /tmp/e2-session --log-level Info --run-recon
```

`--log-level Off` suppresses logger records while retaining the existing console diagnostics. `--log-disable-modules Runtime` suppresses startup and the mirrored diagnostics. The game-data directory still comes from the selected CMake configuration; `--game-data-dir` is an optional launch override. Missing option values and invalid output/log directories fail at startup with an explicit error.

`E2R_ENABLE_LOGGER=OFF` selects a C-only logging stub while retaining runtime options. Turning off both logger and runtime options remains available for isolated compatibility experiments; the shared presets enable both.

## Verification

From the repository root, with the data environment set for fresh directories:

```sh
export ECSTATICA2_DATA_DIR=/path/to/Ecstatica2
scripts/run-e2-runtime-regressions.sh
scripts/run-e2-control-matrix.sh
cmake --preset linux-clang32-sdl-debug-asan
cmake --build --preset linux-clang32-sdl-debug-asan
python3 scripts/check-e2-developer-launch.py build/Debug/clang21-i386-sdl/e2recomp
python3 scripts/check-e2-developer-launch.py build/Debug/clang21-i386-sdl-asan/e2recomp
SDL_VIDEODRIVER=dummy E2R_ACTOR_CUES=1 timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-build-cues 120 7000
```

The existing regression scripts now configure/build both standard X11 presets, including ASan; `E2R_SKIP_BUILD=1` skips that preparation when builds are current. They retain their input, surface, and sanitizer assertions. There are no CTest/package/workflow presets yet. Runtime probe execution requires an environment that supports the reconstruction's i386 fixed-address mappings.

The developer-launch checks read the single VS Code launch configuration and exercise the built executable from its build directory using dummy SDL. They check automatic logging, diagnostic mirroring (including variadic game-state messages), clean debugger exit, path overrides, filters and failure reporting. They use temporary output roots and do not drive the VS Code UI.

Also exercise the actual game entry on the desktop through the installed `cppdbg` adapter:

```sh
python3 scripts/probe-e2-vscode-launch.py build/Debug/clang21-i386-sdl/e2recomp --seconds 30
```

This opens the normal game window using `launch.json` arguments/environment and the supplied CMake executable's working directory. It uses the current desktop backend and physical input, without substituting a smoke-test command, dummy video or gameplay breakpoints. It records adapter events and any stopped-thread stack. A pass establishes survival of that interval; it does not verify the editor's current preset selection or complete gameplay. Repeat with the ASan executable when checking that preset.

Use fresh capture prefixes and inspect the actual scene/actor state. ASan and gated action-index paths have known runtime limitations documented in the [active implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md). Manual F5 is still the final check of the actual editor integration; shell probes cannot establish VS Code's selected state.
