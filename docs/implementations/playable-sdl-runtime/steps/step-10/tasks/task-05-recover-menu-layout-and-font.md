# Recover menu layout and original font

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
<!-- /docs-tree:parent -->

Status: complete within recorded bounds
Parent Step: [Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
Last Updated: 2026-10-28

The user supplied original/recompiled main and Load screenshots and requested
matching menu size/alignment, with a larger saved-game preview. Preserve accepted
persistence, preview cancellation and automatic dismissal behavior, all occupied
saves and all existing staged work.

Normalize screenshots to the 640×480 game viewport before comparing geometry.
Recover dimensions and title positioning from original static records/disassembly,
and recover original font pixels instead of scaling the provisional uppercase
font. Keep font assets in the installed executable. Enlarge preview display only;
retain the original 80×60 column-major save format and both hosted menu pages.
Mirror reconstructed repairs in the generator.

Acceptance: original-x86 bounds/title/font and mouse/edit-state comparisons; native main/Save/Load
layout assertions and captures; exact enlarged previews without changing gameplay
pages; cancelled previews without loader calls; repeated same/fresh-process loads
and resumed input/animation/attachments. Run Debug/ASan, affected SDL/X11 builds,
independent four-artifact parity and documentation checks. Write only private
copies of originally free slot 5; hash every installed and unowned private save.

The [dated layout journal](../../../../../journal/entries/menu-layout-and-font-2026-10-28.md)
owns original addresses, fresh evidence, the intentional preview enlargement and
remaining fidelity limits.

## Verification

The final focused suite passes **28/28** checks in Debug/ASan, including ten clean
native exits, repeated same/fresh-process restoration, attachments and resumed
input/animation/interaction. **32** previews match both hosted pages at the new
160×120 size; physical gameplay pages stay unchanged. Four cancellation journeys
record zero loader calls. Main/slot dimensions, every row and nonempty main-menu
labels have native assertions and captures. All installed and unowned private
save hashes remain intact; writes use private copies of originally free slot 5.

Original-x86 fixtures compare 600 requester geometry/initial-and-repaint title
cases, 1,520 ASCII font cases, 24 mouse/edit-state cases and the Save requester
close/state handoff. The three-stage menu sweep has **54 PASS / 48 explicitly
SKIPPED / 0 FAIL**, with both native lifecycles passing. All four SDL/X11
Debug/ASan builds, independent four-artifact parity, 67 runner contracts and
documentation checks pass. Earlier failed navigation, stale-caret and dispatch
runs remain in the journal. Broader rendering, translated/multibyte fonts,
low-mode planar preview fidelity and existing gameplay limits remain unqualified.
