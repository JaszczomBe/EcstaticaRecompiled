# Add SDL Developer Launch Route

Status: completed
Parent Step: [Present Live Runtime Frames And SDL F5 Route](../step-14-present-live-runtime-frames.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-28

## Goal

Make the live SDL backend available through repeatable CMake presets and a normal VS Code F5 launch entry.

## Scope

1. Add SDL CMake configure/build presets.
2. Add VS Code SDL configure/build tasks.
3. Add a VS Code launch entry for the SDL runtime.
4. Keep the existing default launch entry unchanged.
5. Track the `dep/SDL` gitlink.

## Subtasks

1. Add a 64-bit SDL configure/build preset for fast host-backend probes.
2. Add a 32-bit SDL configure/build preset for the reconstructed runtime path.
3. Preserve the existing default `linux-clang32-debug` preset.
4. Add a VS Code configure task that runs `cmake --preset linux-clang32-sdl-debug`.
5. Add a VS Code build task that depends on the SDL configure task.
6. Add `Ecstatica Recompiled (SDL)` as a separate launch configuration.
7. Point the SDL launch `program` and `cwd` at `build/linux-clang32-sdl-debug`.
8. Keep `--run-recon` as the launch argument so it matches the existing F5 route.
9. Track the `dep/SDL` gitlink so the vendored backend source is reproducible from a fresh clone.
10. Validate JSON and CMake preset discovery after editing.

## Out Of Scope

1. Changing the default backend.
2. Runtime crash repair.
3. Presentation fidelity beyond using the existing live-frame hook.

## Implementation Notes

This task is workflow wiring, not a runtime behavior change. The existing `Ecstatica Recompiled` entry stays on `build/linux-clang32-debug` so there is still a known raw debug baseline. The new SDL route selects the backend by choosing the SDL build tree, not by passing runtime flags.

The CMake presets carry `E2R_HOST_BACKEND=sdl` and keep the Ecstatica II data directory pointed at `/home/rgrabowski/Games/Ecstatica2`. The 32-bit SDL preset also carries `-m32` compile and link flags because reconstructed runtime execution still depends on the 32-bit/fixed-address environment.

The vendored SDL source belongs under `dep/SDL`. Tracking the submodule gitlink is part of this task because without it the new launch route cannot be recreated by another checkout.

## Acceptance Criteria

1. Presets parse through CMake.
2. VS Code task/launch JSON remains valid.
3. Existing `Ecstatica Recompiled` entry remains available.
4. `Ecstatica Recompiled (SDL)` has a matching SDL 32-bit pre-launch build task.
5. The SDL launch route does not require changing user environment variables in VS Code.

## Verification

1. `cmake --list-presets`
2. `cmake --list-presets=build`
3. `jq empty .vscode/launch.json .vscode/tasks.json CMakePresets.json`
4. `git submodule status`
5. `git diff --check`

## Review State

1. Planning state: agreed
2. Implementation state: accepted
3. Notes: Added SDL CMake presets, VS Code SDL tasks, and a separate SDL launch entry without removing the default launch route.

## Evidence

1. `CMakePresets.json` exposes `linux-clang-sdl-debug` and `linux-clang32-sdl-debug` configure/build presets.
2. `.vscode/tasks.json` exposes `CMake: Configure SDL 32-bit` and `CMake: Build SDL 32-bit`.
3. `.vscode/launch.json` exposes `Ecstatica Recompiled (SDL)` using `build/linux-clang32-sdl-debug/e2recomp --run-recon` from the SDL build directory.
4. The existing `Ecstatica Recompiled` launch entry remains available.
5. `git submodule status` reports `dep/SDL` at `f87239e71e42da91ca317a12eefb82cfbf3393eb`, matching SDL release 3.4.12.

## Change Log

### 2026-07-28

1. Created task by merging the former Step 15 launch-wiring work into Step 14.
