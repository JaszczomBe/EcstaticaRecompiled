# Save/load menu refinements — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 10 Task 04](../../implementations/playable-sdl-runtime/steps/step-10/tasks/task-04-refine-save-load-menu-presentation.md).
The user accepted the functional save/load recovery, then reported absent saved
images, the parent menu remaining open after loading, and an image-sized flicker
in gameplay after cancelling Load. Earlier persistence evidence remains in the
[base recovery journal](game-save-load-recovery-2026-10-27.md).
All earlier work was staged at the start of this refinement. Preserve that index;
no commit, push or tag change is authorized.

## Counterexample and original ownership

Evidence root: `build/evidence/save-menu-refinements-2026-10-27`.
`installed-before.json` records all ten installed save sizes/hashes. The bounded
`baseline-01` probe copies every slot privately and writes only originally free
slot **5**. It saves through the actual menu, opens Load and selects that save.
The 80×60 thumbnail exactly matches physical page **1**, while **neither** displayed
auxiliary page **2/3** matches. Physical page 1 changes during selection; page 0
does not. The captured menu has a black preview rectangle. This is a native
presentation counterexample; the earlier per-function thumbnail fixture did not
exercise the hosted requester's displayed buffers.

Original `0x43c2b8..0x43c453` skips the 26-byte label and two-byte version, then
writes an 80×60 column-major image at high-mode coordinates **(116,162)**, using
the selected surface/pitch. Original `0x43b632..0x43b637` explicitly passes the
selected slot (`0x64353c`) on initial requester drawing. The generated caller
still passed a scratch value. The hosted menus draw their rectangles/text into
auxiliary pages 2/3, and their backdrop stack restores those pages. A thumbnail
written to physical game storage is therefore hidden from the menu and survives
that backdrop restoration, explaining the flicker footprint.

Original `0x43d490` sets menu state **4** and returns; `0x416349..0x41637c`
handles Load before resuming play. The hosted nested callback explicitly restores
parent requester **0x28** after any Load. Successful restoration must instead
unwind both requesters. State **5** is the existing resume path in `0x415d40`;
state **0** starts a new game and must not be used to hide the menu.

## Scoped repair

High-mode preview decoding retains the original header, order, coordinates and
pitch but writes both hosted menu pages. Physical game pages are untouched.
Version skipping uses the explicit preview stream instead of an unrelated FAN
parse context. Initial drawing receives the actual selection sentinel/slot.
A successful loader return closes the parent and child requesters through the
resume path. Cancel and failed/unsupported Load retain the existing parent-menu
return behavior. All reconstructed changes are mirrored in `GenerateRecon.js`.

`check-e2-menu-contracts.py` retains original x86 as the pixel oracle. Its host
mapping now compares each auxiliary page against the original image, with padded
pitch, full-surface canaries and an unchanged physical page. **30** thumbnail/
missing/empty cases pass normally and with ASan, alongside **512** option-storage,
**96** word-identity and **6** ten-slot label cases. CRT/surface calls remain
intercepted; real menu presentation is qualified separately.

## Native verification and probe correction

`native-debug-02/03` pass exact preview and physical-page checks but the first
automatic-dismissal assertion fails after twelve `FUN_0041ba7c` stops. Captured
state is already **modal 0 / requester 0 / successful load 1**. The stack has no
requester: those event pumps belong to animation resource **564** loading during
resumed gameplay. The probe now requires modal/requester/backdrop-depth all zero,
then disables the menu breakpoint and waits for normal gameplay updates. It
still sends no extra Escape. This is an observation correction; no speculative
menu-loop rewrite was needed.

`native-debug-04` and `native-asan-05` pass two real Save/change/Load cycles and a
fresh-process Load, with exact preview pixels, preserved physical preview regions,
automatic dismissal, restored state, input/animation/attack and actual menu Quit
(native exit **0** for all four processes). Captures show the saved view in the
preview rectangle. The strengthened final probe additionally switches between
filled/empty/filled slots and counts loader calls during cancellation (must be
**zero**). The `persistence` suite now requires `Original.Menus` as the preview
pixel oracle in each configuration.

All four affected SDL/X11 Debug/ASan presets build. Independent scratch generation
`generation-06` matches all four artifacts; normal and ASan menu fixtures pass.
The final focused suite and preservation results follow below. Low-resolution planar fidelity, arbitrary corrupt-file
cleanup and broader gameplay limits remain as recorded in the base journal.

## Final evidence

`focused-suite-07` passes **26/26** cases in **122.88 seconds**, including all
**22** persistence-block cases, generation parity, all **67** suite contracts and
both DirectDraw provider checks. Its ten native processes exit through actual
menu Quit with exit **0**. The same/fresh-process world and sword journeys record
**32** exact saved/blank-thumbnail comparisons: both displayed pages match, and
both physical gameplay preview rectangles remain unchanged. Four cancellation
journeys switch filled/empty/filled slots and observe **zero** loader calls,
then resume play. Successful loads record automatic dismissal and continue the
existing state, reciprocal attachment, movement, animation and attack checks.

`rejection-{debug,asan}-{empty,unsupported}-08` all pass: rejection/cancel returns
to the parent menu, with playable world and clean Quit. Failed or cancelled Load
does not take the new success-only dismissal path. The saved image has been
inspected in captured menu frames; larger menu-label/layout fidelity is separate.

All installed save sizes and SHA-256 hashes exactly match `installed-before.json`
and `installed-after.json`, including occupied slots **0–4, 8, 9** and empty
**5–7**. Native writes use only private slot **5**; private empty slot **6** is
selected but never written. Unowned private save hashes also match in every
report. `final-summary.json` records counts, checks and all four executable
hashes; both final SDL binaries match the suite's pinned copies. Syntax,
whitespace and the **265-document** README tree checks pass. No commit, push,
tag or staging change was made by the agent.
