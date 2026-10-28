# Recover Enter Inventory and Progress Menu

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Original Game HUD](../step-11-recover-original-hud.md)
<!-- /docs-tree:parent -->

Status: implemented; bounded Debug/ASan acceptance, human visual/low-mode/hourglass review open
Parent Step: [Recover Original Game HUD](../step-11-recover-original-hud.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-28

## Goal

Recover the original in-game status/inventory page: **Enter** opens it and
**Escape** dismisses it back to gameplay. It presents inventory/equipment,
player progress, gold, kills and the other original indicators. The user selected
this as the next task after the inner-castle recovery. The user authorized
original-backed investigation and implementation after the documentation handoff.

The [handoff journal](../../../../../journal/entries/enter-inventory-menu-handoff-2026-10-28.md)
records the original-game screenshot, baseline and preservation boundaries.
The screenshot is an original-game reference roughly halfway through the game,
not reconstructed-runtime acceptance or a save to reproduce numerically.

## Scope and original reference

1. Recover the actual input dispatch, modal lifecycle, artwork/palette, drawing
   contracts and live statistic/item ownership from original disassembly/Ghidra.
   Establish any original gameplay pause, timer, audio, focus and input rules.
2. Restore the ornate original page, retaining the upper gameplay HUD. The
   supplied screenshot shows a pink/salmon textured background, gold decorative
   border, a segmented inventory diagram at upper left, treasure chest and gold
   counter below it, eight central item/emblem panels in two columns, a circular
   progress display at upper right, and sword/shield statistic panels below.
   Visible reference values are **74250 gold**, **48% progress**, and **70** below
   the sword panel (reported as kills by the user); the shield's numeric panel
   appears blank. Recover the exact meaning of every field and dim/bright icon
   from original code. Do not invent a meaning for unlabelled artwork.
3. Read current progress, inventory, equipment, gold and kills through original
   state contracts. Verify fresh and progressed states, including after Load.
   Never hardcode the screenshot values or add fabricated progression fields.
4. Preserve original-default/F1 HUD, F2 debug overlay, F3 geometry modes, menus,
   input release, recording/replay, inspection and protected Save/Load. Determine
   original status-page HUD visibility before adapting host composition.

## First bounded investigation

Inspect a bounded fresh launch and a private copy of a progressed save with real
Enter/release/Escape/release input. Record current behavior before editing. These
are source leads, not recovered contracts:

| Lead | Investigation |
| --- | --- |
| `FUN_00455fe8`, original entry `0x455fe8` | Decompiled icon-page lifecycle loads `graphics/iconpage.raw`, handles palette and redraw, pumps input until `DAT_00636844`, then restores presentation. Recover file/stack/register arguments and cleanup from original instructions before enabling the path. |
| Caller near original `0x416112` | Reconstructed code consumes `DAT_004c39ac` and calls `FUN_00455fe8` when `DAT_0047a34a == 0`. Trace actual Enter mapping and eligibility gates; the byte's address alone is not proof of the key contract. |
| `FUN_004561c8`, original entry `0x4561c8` | Page-content candidate follows icon-page loading and calls item/graphic helpers. Recover icon predicates, numeric formats, counters and completion formula from original code. |
| `FUN_004555b0`, `FUN_00455850`, `FUN_004559bc`, `FUN_00456f94` | Registration/temporary graphics and recovered HUD/magic ownership. Audit existing bypasses and shared helpers without globally removing `E2R_PROXY_MESH_BYPASS`. |
| `E2Recomp/platform/e2recomp_hud.c` and `.h` | Existing immutable-asset indexed HUD composition and process-local display policy; preserve game-page/save-preview ownership. |
| SDL/X11 backend key translation and native input pump | Return already maps to `VK_RETURN`; prove end-to-end scan/latch dispatch, key repeat, release, Escape consumption and focus behavior. |

Use original `E2Recomp/original_disasm.txt`, Ghidra exports in
`E2Recomp/src/E2Recomp_decompiled.c` and the installed
`/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE`. Separate original facts from
unresolved decompiler registers. Preserve possible original defects; change
behavior only for a proven reconstruction mismatch. Mirror reconstructed C
repairs in `E2Recomp/tools/GenerateRecon.js` and verify independent generated
parity without unrelated churn. Keep host presentation/input below the backend
boundary and recovered game rules original-shaped.

## Acceptance and verification

1. Real Enter opens the original page and real Escape closes it repeatedly in
   Debug/ASan. No stale frames/palette, stuck keys, unintended main-menu opening,
   accidental action or hang remains; gameplay resumes under original rules.
2. Original artwork, dimensions, palette and populated/empty icon states have
   source and rendered evidence. Verify gold, kills and completion against their
   original state/formula, including representative boundary cases and a loaded
   progressed save. Report untranslated/low-mode/unexercised branches explicitly.
3. Verify movement/attack after closing, F1/F2 and F3 across transitions, and
   original-format same/fresh-process persistence with correct page values after
   Load. Protect installed and runtime saves with hash checks and private copies;
   use a verified empty private slot, never occupied slots 5/123, 6, 7 or 9.
4. Run relevant original-x86 comparisons (extend existing HUD/menu fixtures as
   needed), bounded native Debug/ASan probes, affected SDL/X11 builds, generation
   parity and a fresh recording/replay containing Enter/Escape. Existing helpers
   include `check-e2-original-hud.py`, `check-e2-hud-pixels.py`,
   `check-e2-menu-contracts.py`, `check-e2-generation-parity.py` and
   `probe-e2-game-save-load.py` under `scripts/`; existing checks alone do not
   cover the new page.
5. Human investigation uses the single **Ecstatica Recompiled** F5 launch.
   Agent probes need bounded input/timeouts, private outputs and recording off
   except an explicit bounded recording/replay check. Record fresh evidence and
   limits in this task, its step, the implementation and a dated journal.

## Boundaries and review state

Audio, music, remaining object models and extended inner-castle acceptance remain
deferred; this selection does not close their open work. Preserve existing staged
and unstaged edits. Do not commit or push. No explicit usage/token budget applies.

Implementation and bounded acceptance are recorded in the
[recovery journal](../../../../../journal/entries/enter-inventory-menu-recovery-2026-10-28.md).
The earlier handoff remains historical reference, including its screenshot description.

## Implemented result and current acceptance

The live Enter queue, synchronous Escape lifecycle, immutable original page/HUD,
fifteen scene-flag overlays, power gems, timer mask and numeric rendering are
recovered. Gold/kills/power share original mapped storage with Save/Load and
new-game/script/gameplay updates. The original 99% progress cap, five-digit
truncation and opaque-zero temporary sprites are preserved. No save repair or
fabricated screenshot state is introduced.

- Four SDL/X11 Debug/ASan builds and independent generation parity pass.
- Normal/ASan each pass 256 original-x86 content cases, 768 Enter decisions and
  81 inventory sprite pixel comparisons; the focused matrix passes 22/22.
- Debug/ASan fresh equipped and original progressed-slot-3 persistence produce
  eight clean processes and 24 status transitions, correct restored values,
  unchanged page/preview bytes, F1/F2/F3, resumed movement/attacks and actual Quit.
- Four further fresh/runtime-slot-6 processes exercise repeated Enter and
  focus/menu lifecycle. Each final Debug/ASan recording passes five strict replay
  variants through 26 checkpoints. All 199 protected files retain hashes.

Human F5 visual review, low-mode/planar play, natural hourglass lifetime and
exhaustive item acquisition remain open. The journal retains failed intermediate
routes and probe attempts. Inner-castle uninterrupted route, equipped-armour human
review, full gate/effect composition and the incomplete historical recording
remain unqualified. Audio/music stay deferred. No commit or push was made.
