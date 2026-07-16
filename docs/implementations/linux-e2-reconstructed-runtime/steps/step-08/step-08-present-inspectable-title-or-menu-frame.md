# Present Inspectable Title Or Menu Frame

Status: active
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-16

## Goal

Turn the sustained reconstructed runtime heartbeat into an inspectable title/menu frame that can be verified from the host side.

## Why This Step Exists

Step 7 proved that the reconstructed runtime can survive at least 90 seconds under ASan after the HUD icon, damage-rectangle table, and requester-id repairs. The next useful proof is visual: confirm what the compatibility renderer presents during that stable loop and recover only the missing presentation path needed to inspect a real title/menu frame.

## Scope

1. Identify the current host presentation path and whether a real frame buffer or surface is being updated.
2. Add a bounded inspection hook, screenshot path, or window-present repair that makes the current title/menu output observable.
3. Keep the reconstructed game logic separate from host/backend presentation code.
4. Mirror generated C repairs in `E2Recomp/tools/GenerateRecon.js` if reconstructed C changes are made.
5. Record visual verification evidence or the next concrete rendering frontier.

## Out Of Scope

1. Full menu input navigation.
2. Full DirectDraw correctness.
3. SDL backend replacement.
4. Gameplay scene entry.

## Starting Evidence

Step 7 verification from `build/linux-clang32-asan`:

```text
timeout --preserve-status 90s ./e2recomp --run-recon
Ecstatica II data: /home/rgrabowski/Work/EcstaticaRecompiled/build/linux-clang32-asan/Ecstatica2
exit code 143
```

No sanitizer report was emitted during the 90-second bounded run.

## Acceptance Criteria

1. Runtime still builds in debug and ASan configurations.
2. A real title/menu frame or the next specific rendering/presentation frontier is documented.
3. Any host-side inspection hook is bounded and does not hardwire reconstructed logic to a final backend choice.
4. Any reconstructed C hand fix is mirrored in `E2Recomp/tools/GenerateRecon.js`.

## Verification

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build build/linux-clang32-asan`
4. Bounded runtime or screenshot/presentation probe from the relevant build directory.

## Change Log

### 2026-07-16

1. Created after Step 7 sustained a 90-second ASan heartbeat without a sanitizer crash.
