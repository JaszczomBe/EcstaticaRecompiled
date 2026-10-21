# Logger Developer Workflow — 2026-10-21

## Problem And Scope

After preparing the uncommitted `linux-e2-reconstructed-runtime` merge into `feature/logger`, the user requested functional integration with the current CMake/VS Code workflow. The logger branch's old presets, launch paths and opt-in bootstrap were insufficient: the current single F5 launch passed only `--run-recon`, so it never started the logger. ASan presets disabled runtime options and logging, and the C++ toolchain settings embedded this machine's GCC 14 header and library paths.

The automatic merge content stays staged. Conflict resolutions and this continuation stay unstaged. No branch tip moves and no commit is made.

## Changes

- The existing configure/build presets, configuration-first build directories and single selected-target F5 launch remain the entry points. Both C and C++ use the advertised Clang major version. Presets carry architecture flags; CMake discovers an installed i386 C++ runtime/header fallback when development links are absent and checks architecture agreement and C++20 `std::format` linking. Normal multilib installations use compiler defaults.
- Logger and runtime options are enabled in the shared Debug and ASan presets. ASan instruments the logger, runtime options and C diagnostic adapter as well as the application/host code. `E2R_ENABLE_LOGGER=OFF` still builds a C-only stub with runtime options available.
- Logging starts without extra CLI switches. The default output root is `~/.ecstatica2`, resolved before entering the original data directory. `E2R_DATA_DIR`, `E2R_LOG_LEVEL` and `E2R_LOG_DISABLE_MODULES` supply environment defaults; CLI switches before the runtime command override them. Files and invalid parent/log directories fail explicitly rather than silently producing no log.
- Existing stderr diagnostics are mirrored to the rotating file sink under `Runtime.Diagnostic`. Both `fprintf` and `vfprintf` share the adapter, including fragmented game-state records. The original console text appears once. Bootstrap checks that the file sink opens before starting the worker; normal shutdown flushes the partial diagnostic line and pending records.
- F5 appends `detect_leaks=0` to inherited `ASAN_OPTIONS` because LeakSanitizer cannot run under GDB's ptrace. AddressSanitizer remains enabled. No additional launch entry or build wrapper is added.

No generated reconstruction or gameplay logic changes are needed.

## Verification

All four existing SDL/X11 Debug/ASan presets configure and build. Fresh X11 build directories also verify C++ toolchain discovery and the C-only logging-stub configuration. Compile commands confirm instrumentation of the logger, runtime options and diagnostic adapter in both ASan builds.

The installed CMake Tools extension exposes the configured selected-target path/directory commands and honors `cmake.buildBeforeRun`. The new executable check reads the actual VS Code environment and uses its build-directory cwd:

```sh
python3 scripts/check-e2-developer-launch.py build/Debug/clang21-i386-sdl/e2recomp
python3 scripts/check-e2-developer-launch.py build/Debug/clang21-i386-sdl-asan/e2recomp
```

Each passes **16 cases**: automatic startup/file logging, one console copy, GDB exit, real startup with variadic game-state records, cwd-independent and relative output paths, CLI/environment precedence, level/module filtering, missing/empty option values, and invalid output/game/log directories. Evidence: `/tmp/e2-logger-vscode-launch-{debug,asan}`. An additional ordinary SDL presentation probe with no data-dir override confirms the actual `~/.ecstatica2/logs` default; its console is `/tmp/e2-logger-default-root-check.log`.

The final runtime wrapper and all eight Debug/ASan arrow rows pass with logging active: `/tmp/e2-logger-final-regression-check.log` and `/tmp/e2-logger-final-controls-check.log`. Generator syntax passes; generated sources are untouched.

The populated Debug workshop/courtyard probe completes 356→350→347 activation, original sword visibility, camera restoration, courtyard crossing/return and five seconds of released-input observation. The earlier ASan integration run also completes that route. The final ASan rerun reaches workshop activation but fails **“Reverse input did not return to pedestal camera and floor level”**, without an ASan report. This same bounded-return limit occurred before the logger integration; no movement repair is attempted here. Final evidence: `/tmp/e2-logger-final-workshop-{debug,asan}*` and `/tmp/e2-logger-final-game-{debug,asan}/logs`.

Comparison with those final probe consoles finds all **854 Debug** and **795 ASan** timestamped runtime diagnostic messages in the corresponding file logs, including the variadic bodies previously missed by the first adapter.

The staged binary patch remains byte-identical to the entry snapshot (SHA-256 `0640e32c9735a2195965d344603ad5fcebfdeb493c84ba7dff2bb3c4f77fcbf2`).

## Limits

The checks exercise the configured executable/environment and GDB, not clicks in the VS Code UI or its current preset selection. Manual F5 remains a separate editor check. Manual workshop re-entry, sword pickup and full experimental ASan remain unaccepted.

These are rotating runtime logs, not a recorder/replayer or a complete run-artifact bundle. Arbitrary library stderr and ASan's own report stream are not mirrored; retain probe/debugger output. Asynchronous logging can lose records on abrupt process termination. Deterministic input/timing/state replay and comprehensive event instrumentation remain subsequent work.

## VS Code Configure Follow-up

The user's actual CMake Tools logs expose a missed initial-configuration condition: both Release and Debug have an empty cached `ECSTATICA2_DATA_DIR`, and the desktop-launched editor has no corresponding environment variable. The earlier checks reused populated caches or supplied a data path explicitly. The resulting configure failure explains the subsequent missing/undefined executable target.

CMake now initializes an absent or empty cache value from the environment, then the optional plain-text `~/.ecstatica2/game-data-dir` setting. A nonempty cache or explicit `-D` override keeps precedence. The known original-data path is saved locally in that file, outside Git. This allows the same standard presets to work in the editor and after cache resets. The invalid `/E2WIN95.EXE` default left by an earlier empty-path configure is also reset when absent, allowing the original-executable path to follow the recovered data root.

`scripts/check-e2-game-data-config.py` passes ten resolution/precedence cases, including fresh and already-empty caches. Both exact CMake Tools configure commands from the user's attachment succeed without `ECSTATICA2_DATA_DIR` in the environment. A fresh `build/Debug/clang21-i386-sdl-editor-clean` directory configures under the same condition. The standard SDL Debug build passes, its File API exports `e2recomp` as an executable, and all sixteen developer-launch cases pass again.

Evidence: `/tmp/e2-vscode-configure-{debug,release,fresh}.log`, `/tmp/e2-vscode-build-debug.log` and `/tmp/e2-vscode-data-path-launch`. Staged merge content remains unchanged; the repair stays unstaged.

The subsequent [native F5 heap-corruption continuation](native-f5-file-open-heap-corruption-2026-10-21.md) supersedes startup confidence based only on dummy-SDL smoke checks. It reproduces the user's desktop abort, recovers the original file-open helper's lost output pointer and adds a launch probe through the actual installed VS Code debug adapter on the native backend.
