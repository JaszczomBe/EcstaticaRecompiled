# Verify SDL Backend Parity

Status: completed
Parent Step: [Add SDL Host Backend](../step-13-add-sdl-host-backend.md)
Parent Implementation: [Run Reconstructed E2 On Linux](../../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Prove the SDL backend preserves the stabilized runtime loop and document what remains different from the default backend.

## Scope

1. Run the default Step 11 regression script as a baseline.
2. Run the SDL-selected build/probe commands from earlier Step 13 tasks.
3. Compare control-ready, movement, surface, and diagnostic evidence.
4. Document any remaining SDL gaps and decide whether Step 13 can close.

## Out Of Scope

1. Fixing large runtime divergences discovered during parity checks.
2. Full rendering fidelity.
3. Packaging or installer work.

## Implementation Notes

SDL parity probing exposed reconstructed-runtime hazards rather than SDL API bugs. The fixes are mirrored in `E2Recomp/tools/GenerateRecon.js` and regenerated into `E2Recomp/reconstructed/E2Recomp_recon.c`:

1. SDL event polling now returns early off the SDL main thread, avoiding SDL3's main-thread assertion when reconstructed worker paths call `PeekMessageA`.
2. `FUN_00418a04` validates cached framebuffer pointers and write spans before returning surface bases.
3. `FUN_0041b34c` validates draw pitch, dimensions, base range, and write span before line drawing.
4. `FUN_00415d40` validates the current actor/action pointer chain before reading the current action flag.
5. `FUN_0044add8` advances byte-copy destinations from the real local pointer instead of stale high halves from byte-reader return values.

## Acceptance Criteria

1. Default backend regression script still passes.
2. SDL backend reaches the documented parity target for the implemented SDL scope.
3. Remaining gaps are documented as follow-up tasks or later steps.

## Verification

1. `scripts/run-e2-runtime-regressions.sh`
2. `SDL_VIDEODRIVER=dummy build/linux-clang-sdl-debug/e2recomp --host-backend-key-probe`
3. `SDL_VIDEODRIVER=dummy build/linux-clang-sdl-debug/e2recomp --host-backend-present-probe`
4. `SDL_VIDEODRIVER=dummy build/linux-clang32-sdl-debug/e2recomp --host-backend-key-probe`
5. `SDL_VIDEODRIVER=dummy build/linux-clang32-sdl-debug/e2recomp --host-backend-present-probe`
6. `SDL_VIDEODRIVER=dummy build/linux-clang32-sdl-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step13-sdl-debug space,num8 6 10000 180 1`
7. `git diff --check`

## Review State

1. Planning state: discussed
2. Implementation state: accepted
3. Notes: SDL parity now covers key delivery, backend-owned indexed-8 presentation, default backend regressions, and a 32-bit SDL gameplay-surface proof.

## Evidence

The default regression script passed after regeneration:

```text
Runtime regressions passed.
Debug log: /tmp/e2-step11-regression-debug.log
ASan log: /tmp/e2-step11-regression-asan.log
```

SDL key probes on both SDL builds report:

```text
host backend key probe message: msg=0x0100 wParam=0x20
host backend key probe passed
```

SDL presentation probes on both SDL builds report:

```text
host backend presentation probe passed: width=64 height=64 hash=a92a7045
```

The 32-bit SDL gameplay probe reaches the same stabilized runtime shape as the default backend: `_DAT_00643650=0`, `DAT_00479de8=1`, `DAT_0047a76c=1`, `_DAT_0073cc3c=0x681d04`, `move=[1,0,0,0,0,0,0,0,0]`, and surface 3 is nonblank with hash `6e39f5ea`.

## Change Log

### 2026-07-27

1. Created task.
2. Activated after task 03 added the bounded SDL presentation proof.
3. Repaired reconstructed-runtime hazards exposed by SDL parity probing and mirrored the fixes in the generator.
4. Closed task after default regressions, SDL key/presentation probes, and 32-bit SDL gameplay parity all passed.
