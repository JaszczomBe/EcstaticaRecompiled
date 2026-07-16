# Wire Menu Input Path

Status: active
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-16

## Goal

Map enough host keyboard or mouse input into the reconstructed Win32-style input path to navigate past the inspectable title/menu state.

## Why This Step Exists

Step 8 proved the runtime is presenting a real Ecstatica II title-logo frame in memory. The next proof is interaction: recover how the original loop consumes keyboard/mouse state and feed it from the Linux host without hardwiring reconstructed game logic to a final backend.

## Scope

1. Trace the current input globals and message paths around `E2R_WndProc`, `PeekMessageA`, and the `DAT_006368xx` input flags consumed by `FUN_00415d40`.
2. Add the smallest host-side input bridge needed to trigger one menu/title transition.
3. Keep the bridge behind compatibility or native launcher code, not inside recovered game logic unless the change repairs a decompiler artifact.
4. Preserve `--dump-frame` as the visual verification probe.
5. Document the first navigated state or the next concrete input frontier.

## Out Of Scope

1. Full keyboard/mouse coverage.
2. Configurable key binding UI.
3. SDL backend replacement.
4. Gameplay scene control polish.

## Starting Evidence

Step 8 ASan probe:

```text
./e2recomp --dump-frame /tmp/e2-step08-frame-asan.pgm 5
wrote frame dump: /tmp/e2-step08-frame-asan.pgm (surface 3)
```

The dumped frame is a valid `640x480` PGM showing the Ecstatica II title logo.

## Acceptance Criteria

1. Debug and ASan builds compile.
2. A bounded run can inject or receive one meaningful input event.
3. A frame dump, log, or documented state change proves the event reached the reconstructed menu/title path.
4. Any reconstructed C hand fix is mirrored in `E2Recomp/tools/GenerateRecon.js`.

## Verification

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build build/linux-clang32-asan`
4. Bounded input/presentation probe using `--dump-frame` or a follow-on inspection mode.

## Change Log

### 2026-07-16

1. Created after Step 8 captured a real title-logo frame from the ASan build.
