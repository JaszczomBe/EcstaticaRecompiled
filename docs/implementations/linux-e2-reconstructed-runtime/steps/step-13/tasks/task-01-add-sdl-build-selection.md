# Add SDL Build Selection

Status: completed
Parent Step: [Add SDL Host Backend](../step-13-add-sdl-host-backend.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Make SDL selectable as an optional host backend build path while preserving the existing default backend.

## Scope

1. Decide the CMake option name and default.
2. Add build discovery or clearly documented dependency expectations.
3. Compile a stub SDL backend path only when selected.
4. Leave the current X11 backend as the default until SDL parity is proven.

## Out Of Scope

1. SDL input mapping.
2. SDL presentation.
3. Removing X11 code.
4. Runtime behavior changes.

## Implementation Notes

Completed with `E2R_HOST_BACKEND`, a CMake cache string whose supported values are `x11` and `sdl`. The default is `x11`; `sdl` builds the vendored `dep/SDL` submodule and compiles `E2Recomp/platform/e2recomp_host_backend_sdl.c`.

Fresh checkouts need the submodule initialized before selecting the SDL backend:

```text
git submodule update --init --recursive dep/SDL
```

Verified command:

```text
cmake -S . -B build/linux-clang-sdl-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang -DE2R_HOST_BACKEND=sdl -DECSTATICA2_DATA_DIR=/home/rgrabowski/Games/Ecstatica2
cmake --build build/linux-clang-sdl-debug
```

Local SDL submodule revision: `release-3.4.12`. SDL static linking is selected and SDL's ccache option is forced off for this build subtree.

## Acceptance Criteria

1. Default builds keep their current backend behavior.
2. SDL selection either configures and builds or fails with an actionable dependency message.
3. The selected backend is visible in CMake output or documentation.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. SDL configuration/build command chosen by this task.
4. `git diff --check`

## Review State

1. Planning state: discussed
2. Implementation state: accepted
3. Notes: Completed as build-system-only selection with vendored SDL source; task 02 owns actual SDL window/input behavior.

## Change Log

### 2026-07-27

1. Created task.
2. Activated task after Step 12 closure.
3. Added and verified `E2R_HOST_BACKEND=x11|sdl` selection.
4. Replaced system SDL discovery with the `dep/SDL` submodule so the built SDL source remains inspectable.
5. Renamed the dependency root from `third_party` to `dep` and updated the SDL submodule to release 3.4.12.
