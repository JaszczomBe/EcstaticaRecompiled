# Menu layout and original font — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 10 Task 05](../../implementations/playable-sdl-runtime/steps/step-10/tasks/task-05-recover-menu-layout-and-font.md).
The user supplied original screenshots 1/3 and reconstruction screenshots 2/4,
showing large typography differences, overflowing Load rows and a misplaced title.
They also requested a larger preview than the original. Earlier functional and
[presentation recovery](save-load-menu-refinements-2026-10-27.md) remain accepted;
this work preserves those changes and the pre-existing index. No commit/push/tag
change is authorized.

## Original evidence and repair

Evidence root: `build/evidence/menu-layout-2026-10-28`.
The original screenshots include a 4:3 game viewport inside a wider display;
the reconstruction images include a 640×480 viewport inside a 640×640 window.
Comparing whole image dimensions would incorrectly resize the main requester.
Its original record at **0x47a588** already specifies 210×180 low-mode units,
which become **420×270** at **(110,105)** in high mode.

The slot requester at **0x47a5a4** specifies **270×175**, becoming **540×262**
at **(50,109)**. The hosted initialization incorrectly used 240×180, shifting
rows right and leaving their right edges outside the panel. Restore the original
static dimensions. Existing original row coordinates then fit: x=254..570,
y=109+floor((37+11×slot)×3/2), height=12. Save exposes nine named rows; Load
includes the tenth quick-save row. The preview and file format remain separate.

Original **0x43b58b..0x43b5dd** (initial draw) and **0x43b09f..0x43b0f4** (repaint) center title text at panel left plus half the
unused width, with y=panel top+font height+2. The reconstructed call confused
text width, horizontal position and vertical position after losing register
arguments. Repair both callers. Remove the extra hosted label pass that
forced uppercase-font-era colors and overpainted selection/caret rendering.
Original item rendering owns its gold/selected text styles. Resolve fixed
Quit/Yes/No/OK labels before measurement/drawing; the removed duplicate pass had
supplied those labels without restoring their text pointers in the normal path.
Raised buttons and inset slots now use the distinct bevel directions from **0x43baa8..0x43bbc9**;
the previous helper mixed raised horizontal edges with inset vertical edges.

High-mode **0x418770** dispatches to **0x419af4**, whose regular font raster at
**0x41a97a..0x41aac2** consumes eleven two-byte rows per glyph, with byte-swapped
bit ordering and a **12-pixel advance**. It preserves case, paints original small
letter shapes and handles opaque text mode 2. The replacement 5×7 uppercase font
had instead painted 10×14 glyphs at that same advance. Recover the original
single-byte glyph mapping/raster and style colors. The host compatibility helper
reads the file-backed **0x477068..0x479caa** font range from the installed
`E2WIN95.EXE`, validating DOS/PE32 headers and section/file bounds. No original
bitmap is copied into the repository and no original executable code runs in
the game. Missing font assets retain the provisional fallback.

The user's requested enhancement displays saved images at **160×120**, placed
at **(72,162)**, leaving space before the first slot column. Each source pixel
becomes a 2×2 block. Save storage remains **80×60 column-major**, with the same
26-byte label and two-byte version prefix. Filled and empty previews draw both
hosted pages 2/3 and leave physical game pages untouched. Every reconstructed
change is mirrored in `GenerateRecon.js`.

## Verification

`check-e2-menu-layout.py` extracts production C and executes bounded original x86:
**600** main/slot bounds and title-position cases compare low/high modes,
explicit/centered positions and 50 title lengths, including both initial and
repaint title positions. **1,520** ASCII glyph/style/
color/text-mode cases compare whole padded-pitch buffers and both hosted pages
against original font rendering. Font reads match original asset bytes and reject
invalid ranges. `Original.MenuLayout` is a persistence-suite prerequisite in both
configurations; source hashes include the new fixture.

`check-e2-menu-contracts.py` retains the original unscaled preview as its oracle,
then compares the explicit 2× display transformation against each full hosted
page, with pitch/canaries and untouched physical pages. Its **30** preview cases,
**512** option-storage cases, **96** identity cases and **6** ten-slot label scans
pass. The native probe now checks original main/slot dimensions, every live slot
hit rectangle, and exact enlarged preview pixels, and retains menu captures.

`native-debug-01` exhausted the live equipment route's six-replan navigation
budget before reaching persistence. Preserve that failure; it is not save/load
acceptance. `native-debug-02` uses the established noncombat equipment profile and
passes repeated same-process and fresh-process loads with attachments;
`native-asan-03` passes the live world route. These preliminary runs precede the
final bevel correction and explicit layout assertions.

`final-suite-04` passes 24/24 cases, but capture inspection then detects the
missing Quit label. `final-suite-05` restores that fixed label and exposes a real
ASan overflow: all three ASan native routes can render Quit with the stale
seven-character save-name cursor, reading beyond the five-byte literal. Debug
success does not qualify this state error. Preserve the failing logs and captures.

Original **0x43b660..0x43b6cc** keeps **ECX=0** across the event pump; the pump
preserves that register at **0x41ba7d/0x41bcc2**. **EAX** carries independent mouse
bits. An earlier hosted loop repair substituted those mouse bits for ECX and
wrote them into the edit-state flag, enabling a caret on a non-editable button.
Recover the original zero comparison/assignment and parent record arguments.
Do not clamp the cursor or pad fixed labels to hide the ownership error.
The expanded layout fixture compares **24** original-x86 mouse/edit-state
combinations, with event/draw/key/publication services intercepted. Mouse clicks
clear editing before drawing the selected label, matching the original loop.

`final-suite-06` then exposes a hosted Save dispatch dependency on the previous
loop error: the state becomes **3**, but requester **0x28** remains active with
exit/edit flags both zero. `menu-trace-07/08` retain native state/stack evidence.
Original Save is a closing **0x2000** button: **0x43b8b4..0x43b8cd** writes the
requester exit flag before the callback at **0x43d47c** selects state 3. Recover
that handoff in the hosted Save action bridge. The layout fixture now compares
this combined original close/state contract as well. `native-debug-exit-09`
passes repeated same/fresh-process persistence afterwards. The repaint title
caller receives the same original position repair as initial drawing.

`final-suite-10` passes **28/28** checks in **124.28 seconds**, with no failures,
blocked cases or skips. It includes original-code menu/layout/persistence
fixtures, both DirectDraw checks, independent four-artifact parity and **67**
runner contracts. Six persistence probes yield **10** clean native exits. World
and attachment routes each repeat two Save/change/Load cycles and then load in a
fresh process, resume input/animation/attacks and dismiss both menus automatically.

**32** preview selections compare all **64** displayed-page images at 160×120 and
preserve both physical gameplay rectangles. Four filled/empty/filled cancellation
journeys record **zero** loader calls, then resume play. Save failure dialogs
remain usable and quit cleanly in both configurations. Native assertions verify
main/slot bounds, every slot row and nonempty main labels. Captures confirm the
original mixed-case font, contained rows, centered titles, corrected bevels,
restored Quit label and larger preview.

All writes use private copies of originally free slot **5**. Every installed
save and every unowned private slot keeps its original size/SHA-256; the final
installed snapshot also matches the first pre-investigation snapshot. All four
SDL/X11 Debug/ASan builds pass. Build logs, executable hashes, native report paths,
pixel/cancellation counts and installed preservation are retained in
`final-summary.json`, `installed-after.json` and `build-*.log`. Generated drift is
limited to the intended reconstructed C; all four generated artifacts match.
Documentation update/check and `git diff --check` pass. No staged work is changed
and no commit, push or tag is created.

## Three-stage menu regression

`menu-stages-11` verifies both Debug/ASan menu journeys through horseback intro,
pedestal intro and gameplay: **54 PASS / 48 SKIPPED / 0 FAIL / 0 BLOCKED**, with
both journey lifecycles passing and clean Quit. It opens/cancels dialogs without
selecting or writing slots. The skips retain explicit audio, resolution,
subtitles, female-restart and menu-only state-round-trip limits. Legacy menu
`LoadState`/`SaveState` skip text predates the accepted persistence milestone;
actual state restoration is owned by the separate `Persistence.*` checks, not
by those menu-only placeholders. This run does not qualify skipped behavior.

## Limits

These comparisons qualify main/slot geometry, ASCII menu font rendering, preview
pixels and bounded persistence flows. They do not establish exhaustive rendering,
all translated/multibyte fonts, low-mode planar preview fidelity, arbitrary
original progressions or corrupt-save fatal cleanup. Further tower gameplay
remains unqualified. The preview enlargement intentionally differs from original
80×60 display size. Historical full-suite success remains historical evidence.
