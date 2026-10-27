# Refine save/load menu presentation

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
<!-- /docs-tree:parent -->

Status: complete within recorded bounds
Parent Step: [Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
Last Updated: 2026-10-27

The user accepted functional persistence and requested three refinements: show
saved thumbnails in Save and Load, dismiss the whole menu after successful Load,
and remove a flickering image-sized patch after cancelling without loading.

Recover original preview bytes/order/coordinates and initial selection ownership.
Adapt drawing to the same hosted buffers as the rest of the requester, preserving
physical game pages. Dismiss both requesters on successful restoration without
starting a new game. Keep cancellation and unsupported-version rejection usable.
Mirror reconstructed changes in the generator; preserve all staged work.

Acceptance: compare saved thumbnail bytes with both displayed menu pages, observe
unchanged gameplay pages during selection/cancellation, repeat previews and
cancel/resume play without loading, then verify real same/fresh-process Load
returns automatically to playable state. Retain Debug/ASan state, attachment and
input/animation assertions. Use private copies of originally free slots only,
record all installed save hashes, and run affected original-code checks/builds,
independent four-artifact parity and documentation checks.

The [dated refinement journal](../../../../../journal/entries/save-load-menu-refinements-2026-10-27.md)
owns the counterexample, original addresses, fresh evidence and remaining limits.

## Verification

The focused suite passes **26/26** cases in Debug/ASan, including ten clean
native exits and **32** exact thumbnail comparisons with both displayed menu
pages. Every preview leaves the physical gameplay preview rectangles unchanged.
Four cancellation journeys switch filled/empty/filled previews and record zero
loader calls, then resume gameplay. Successful same/fresh-process loads dismiss
both menus without another Escape and retain state/attachment/input assertions.
Empty-slot and unsupported-version rejections still return to the parent menu in
both configurations. All installed and unowned private save hashes are intact.

Original-code menu fixtures, all four SDL/X11 Debug/ASan builds, independent
four-artifact parity, runner contracts and documentation checks pass. See the
journal for retained baseline and probe-observation failures. Further visual
layout, low-resolution planar fidelity and broader gameplay remain outside this
refinement's acceptance.
