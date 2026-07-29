# Map Surface And Page Ownership

Status: active
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
2. Implementation state: in_progress
3. Notes: Activated after SDL F5 stabilization. Start from `E2R_HostPresentIndexed8`, DirectDraw compatibility state, and the known nonblank surface proofs.

## Change Log

### 2026-07-28

1. Created task.
2. Activated as the next concrete task after Step 1 closed with a stable SDL launch boundary.
