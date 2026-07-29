# Recover Palette Update Path

Status: completed
Parent Step: [Recover DirectDraw Page And Palette Semantics](../step-02-recover-directdraw-page-and-palette-semantics.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Recover enough palette state for SDL presentation to color indexed-8 frames intentionally.

## Scope

1. Find palette creation and update entry points.
2. Map the active palette owner used by presented surfaces.
3. Add a backend-facing palette handoff only after compatibility ownership is clear.

## Subtasks

1. Inspect DirectDraw palette shim functions.
2. Trace palette writes during title/menu startup.
3. Trace palette writes during Start Game transition.
4. Define the minimal palette data passed to the host backend.
5. Verify colorized output against stable hashes or screenshots.

## Out Of Scope

1. Palette animation perfection.
2. Gamma/monitor calibration.
3. Audio.

## Implementation Notes

Do not bake palette behavior into SDL. The compatibility layer should expose the active palette to the backend because other backends need the same information.

2026-07-28 implementation result:

1. `FUN_0041af88` was identified as the recovered palette path. It builds 256 DirectDraw `PALETTEENTRY` slots at `0x00636168`, creates/sets a DirectDraw palette, and later updates entries through the palette vtable.
2. The DirectDraw compatibility shim now captures palette ownership through `E2R_DD_CreatePalette`, `E2R_DDS_SetPalette`, and `E2R_DDP_SetEntries`.
3. The active palette is exposed as `E2R_active_palette[256]` plus validity/update counters, using backend-facing `0x00RRGGBB` values.
4. `E2R_HostPresentIndexed8` accepts an optional palette pointer. SDL maps indexed pixels through the recovered palette when available and preserves grayscale conversion when the palette is absent.
5. Follow-up visual comparison showed the first palette capture was incomplete: `palette_nonzero=6` produced a black logo with sparse blue/green pixels. The fix recovered lost palette-source pointers at raw-image call sites, passing the fixed 0x300-byte palette buffers (`0x621030`, `0x61ca30`, `0x00621330`) and fade palette buffer (`0xab9fac`) into `FUN_0041af88`.
6. Surface dumps now also write palette-applied `.ppm` artifacts beside the indexed `.pgm` files when a valid palette is active.

The recovered palette is deliberately separate from the remaining page-selection issue: title/menu reports `visible=0`, the gameplay probe can report `visible=1`, and surface 3 is still the only nonblank candidate.

## Acceptance Criteria

1. Active palette state is identified - satisfied by DirectDraw palette creation/update interception and `E2R_active_palette`.
2. SDL presentation can use recovered palette data - satisfied by backend palette handoff and SDL indexed-color mapping.
3. Grayscale fallback remains available for missing palette state - satisfied by `NULL` palette fallback.

## Verification

1. `cmake --build --preset linux-clang32-sdl-debug` - passed.
2. `cmake --build --preset linux-clang32-debug` - passed.
3. `cmake --build build/linux-clang32-asan` - passed.
4. `env SDL_VIDEODRIVER=dummy ./e2recomp --host-backend-present-probe` - passed outside the sandbox.
5. `env SDL_VIDEODRIVER=dummy E2R_PRESENT_DIAG=1 build/linux-clang32-sdl-debug/e2recomp --dump-surfaces /tmp/e2-step02-palette-fix-title-rgb 6` - passed outside the sandbox with `palette=1`, `updates=11`, `palette_nonzero=254`, and `palette_hash=29b6fa49`; surface 3 remained the nonblank title/menu frame (`hash=6e39f5ea`) and `/tmp/e2-step02-palette-fix-title-rgb-s3.ppm` visually matches the beige-on-black original logo.
6. `env SDL_VIDEODRIVER=dummy E2R_PRESENT_DIAG=1 build/linux-clang32-sdl-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step02-palette-fix-gameplay space,num8 6 10000 180 1` - passed outside the sandbox with `palette=1`, `updates=11`, `palette_nonzero=254`, and `palette_hash=29b6fa49`; surface 3 remained the nonblank gameplay frame (`hash=3615add9`) and movement latch stayed `move=[1,0,0,0,0,0,0,0,0]`.
7. `scripts/run-e2-runtime-regressions.sh` - passed outside the sandbox. The sandboxed run still fails at the runtime probe with the known `Bad system call`/159 sandbox behavior.

## Review State

1. Planning state: discussed
2. Implementation state: implemented
3. Notes: Palette recovery now includes the raw-image palette-source pointer repair and is visually verified against the title logo. Front-buffer/page ownership remains the active Step 2 frontier.

## Change Log

### 2026-07-28

1. Created task.
2. Activated after Task 1 mapped `visible=0` with surface 3 as the current nonblank heuristic presentation candidate.
3. Implemented DirectDraw palette capture and SDL palette presentation handoff.
4. User screenshot comparison exposed the incomplete six-entry palette as incorrect.
5. Recovered raw-image and fade palette-source call sites.
6. Verified recovered palette state in title/menu and gameplay probes.
