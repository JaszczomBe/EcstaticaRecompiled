# Enter inventory and progress menu handoff — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 11 Task 02](../../implementations/playable-sdl-runtime/steps/step-11/tasks/task-02-recover-enter-inventory-and-progress-menu.md).

## User selection and original screenshot

The user requests a written handoff and a continuation message for recovering
the original in-game inventory/status submenu. **Enter opens it; Escape dismisses
it.** It displays inventory, user progress, gold, kills and related original
indicators. The next context is authorized to investigate and implement it without
another confirmation. This turn changes documentation only.

The user attached an original-game screenshot from approximately halfway through
the game (2560×1440 attachment, displayed at 2048×1152). It has black side borders,
the original gameplay HUD across the top, pink/salmon textured page artwork and a
large ornate gold frame. Upper left is a segmented circular inventory diagram
with bright and dim sections; below is an open treasure chest with **74250**.
The middle contains eight item/emblem panels in two columns, including a ring,
radial symbols, a pendant-like object, armour/shield, scroll and round emblem.
Upper right is a circular progress dial with **48%** below it. Bottom right are
sword and shield panels; the sword has **70** below it and the shield's number
panel appears blank. The user identifies kills among the menu's statistics;
exact icon/counter meanings require original-code proof.

The screenshot is visual reference, not a target reconstructed state. Do not
hardcode its values, infer that every item is held equipment, or derive a new
completion algorithm from its appearance. No repository image path is established
by this handoff; the written description above survives a context reset even if
the conversation attachment is unavailable.

## Baseline and first action

Inspection found a clean worktree/index on `linux-e2-reconstructed-runtime`, HEAD
`969af3bfbdd6aefc7345fa07db3b415151f87a1a`, containing inner-castle recovery.
Recheck actual state when resuming; preserve any subsequent user edits and do not
commit or push. The [inner-castle recovery journal](inner-castle-crash-and-presentation-recovery-2026-10-28.md)
retains original event 0x20/0x23 and clipping repairs, 76 selected owners,
Debug/ASan bounded progression/persistence, and all 3,190 matching source replay
checkpoints. The source recording remains incomplete; uninterrupted route,
equipped-armour human review and full gate/effect composition remain open.

The recovered gameplay HUD does not establish inventory-page acceptance. Its
[recovery record](original-hud-recovery-2026-10-28.md) explicitly leaves legacy
inventory/icon-page paths unqualified. Read-only inspection identifies
`FUN_00455fe8` (`0x455fe8`, `graphics/iconpage.raw` lifecycle),
`FUN_004561c8` (`0x4561c8`, page-content candidate), and the caller consuming
`DAT_004c39ac` near `0x416112`. Numerous file/draw helper arguments remain
unresolved in decompiled output; these are leads, not proven contracts or a
diagnosis. The task owns the detailed inspection and acceptance sequence.

First capture bounded current Enter/Escape behavior in a fresh game and with a
private progressed save; then trace original key dispatch, page lifecycle,
assets/palette and live icon/statistic ownership before changing runtime code.
Preserve original behavior, including possible defects, unless comparison proves
a reconstruction mismatch. Mirror reconstructed repairs in `GenerateRecon.js`.

## Evidence protection and remaining work

Preserve `~/.ecstatica2/logs/session_20261028_173846_961/`, its pinned executable,
source context, recording, saves and existing read-only preservation inventory
under `.tmp/inner-castle-20261028/preserved/`. Runtime slots **5/123, 6, 7 and 9**
are occupied; installed saves also remain protected. Refresh the inventory before
testing. Use private save copies and a newly verified empty private slot.

Keep original-default/F1 HUD, F2 debug overlay, F3 geometry, menus, previews,
input release, inspection and replay working. Require bounded Debug/ASan native
checks, relevant original-x86 fixtures, affected builds, independent generation
parity, protected same/fresh-process Save/Load and fresh Enter/Escape
recording/replay. Human checks use the single F5 launch. Audio/music and remaining
object/route work stay deferred, retaining their existing acceptance limits.

## Handoff verification

Only documentation changed. `python3 scripts/check-docs-tree.py --update`, the
subsequent check without `--update` (**289** connected Markdown documents), and
`git diff --check` pass. No runtime tests or new inventory-menu acceptance are
claimed. No commit or push was made.
