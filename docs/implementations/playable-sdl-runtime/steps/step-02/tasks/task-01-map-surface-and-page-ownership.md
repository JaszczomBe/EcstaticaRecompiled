# Map Surface And Page Ownership

Status: completed
Parent Step: [Recover DirectDraw Page And Palette Semantics](../step-02-recover-directdraw-page-and-palette-semantics.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-07-28

## Goal

Identify which recovered DirectDraw surface/page should be treated as the visible page during title and gameplay.

## Scope

1. Inspect compatibility DirectDraw surface allocation and blit paths.
2. Trace current-frame writes around known title/gameplay proofs.
3. Record the page identity and owner globals.

## Subtasks

1. Locate surface creation and page-switching call sites.
2. Add opt-in diagnostics for page ownership if existing traces are insufficient.
3. Run one title/menu probe and one gameplay probe.
4. Compare selected page ids with dumped nonblank surfaces.
5. Remove or gate any temporary diagnostics.

## Out Of Scope

1. Palette conversion.
2. SDL scaling.
3. Renderer accuracy beyond page ownership.

## Implementation Notes

Prefer compatibility-layer instrumentation. Generated C tracing belongs here only when the DirectDraw-facing call site is not enough.

No new instrumentation was needed for this slice. Existing bounded surface dumps already print the DirectDraw-visible page byte, framebuffer pointers, bad-read status, and per-surface nonblank/hash evidence.

## Mapping Evidence

Source-level owner candidates:

1. `DAT_0047a279 >> 0x18` is the recovered low-page selector. It is used throughout draw/blit helpers as the current visible page, with `1 - (DAT_0047a279 >> 0x18)` used as the alternate page.
2. `DAT_0047a43c != 0` switches several software draw helpers to `surface = (DAT_0047a279 >> 0x18) + 2`, making surfaces 2/3 high-resolution software-page aliases for low pages 0/1.
3. `_DAT_00636150`, `_DAT_00636154`, `_DAT_00636158`, and `_DAT_0063615c` are the four framebuffer pointers surfaced by native probes.
4. `e2r_select_framebuffer` still presents by starting at the low visible page and falling forward to the first readable nonblank page. This is useful evidence, not recovered DirectDraw front-buffer ownership.

Bounded title/menu probe, run from `build/linux-clang32-sdl-debug`:

```text
env SDL_VIDEODRIVER=dummy ./e2recomp --dump-surfaces /tmp/e2-step02-title 6
```

Result: exit `0`.

```text
surface dump state: width=640 height=480 visible=0 fb=[0xa0000,0xa0000,0xf6960010,0xf6b71010] bad=[0,0,0,0]
surface 0 nonblank=0 hash=b6005dc5
surface 1 nonblank=0 hash=b6005dc5
surface 2 nonblank=0 hash=b6005dc5
surface 3 nonblank=1 hash=6e39f5ea
DAT_0047a43c=4 DAT_0047a76c=1 DAT_00479de8=0
```

Bounded gameplay probe, run from `build/linux-clang32-sdl-debug`:

```text
env SDL_VIDEODRIVER=dummy ./e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step02-gameplay space,num8 6 10000 180 1
```

Result: exit `0`.

```text
gameplay-control wait satisfied after 1150 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_00643650=0 _DAT_0073cc3c=0x681d04
move=[1,0,0,0,0,0,0,0,0]
surface dump state: width=640 height=480 visible=0 fb=[0xa0000,0xa0000,0xf699c010,0xf6bad010] bad=[0,0,0,0]
surface 0 nonblank=0 hash=b6005dc5
surface 1 nonblank=0 hash=b6005dc5
surface 2 nonblank=0 hash=b6005dc5
surface 3 nonblank=1 hash=3615add9
DAT_0047a43c=4 DAT_0047a76c=1 DAT_00479de8=1
```

Mapping result:

1. The recovered DirectDraw visible-page byte is `0` in both title/menu and gameplay probes.
2. The current high-resolution mode flag is nonzero (`DAT_0047a43c=4`), so helpers that use the high-resolution convention would target surface `2` for visible page `0`.
3. The only nonblank frame candidate observed in both probes is surface `3` (`_DAT_0063615c`).
4. Surface `3` is therefore the current heuristic presentation candidate, but it is not yet proven to be the recovered DirectDraw front buffer.

Next frontier: inspect the page-copy/update path that should move or expose the loaded `_DAT_0063615c` frame through the recovered visible/front-buffer page. Likely source clusters are `FUN_0041760c`, `FUN_0041868c`, `FUN_00418a04`, `FUN_00418b00`, and the `DAT_0047a279` flip in `FUN_00422238`. Palette recovery can proceed after preserving this page mismatch as expected evidence.

## Acceptance Criteria

1. The visible page candidate is documented for title/menu and gameplay.
2. The result is backed by bounded probe output.
3. Diagnostics remain quiet by default.

## Verification

1. Title/menu frame dump probe.
2. Gameplay surface probe.
3. `git diff --check`.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: Surface/page ownership mapped. Recovered visible page is `0`, but current nonblank heuristic presentation page is surface `3`; front-buffer recovery remains open for later Step 2 work.

## Change Log

### 2026-07-28

1. Created task.
2. Activated as the next concrete task after Step 1 closed with a stable SDL launch boundary.
3. Completed with title/menu and gameplay SDL dummy-driver probes. Both show `visible=0`, `DAT_0047a43c=4`, surfaces 0/1/2 blank, and surface 3 nonblank.
