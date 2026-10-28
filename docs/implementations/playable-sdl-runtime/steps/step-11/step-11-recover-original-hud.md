# Recover Original Game HUD

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: implemented; bounded verification and remaining branches recorded
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-28

## Goal

Restore the original game HUD, starting with the player's life bar and recovering
its other indicators from original assets and behavior. Make it the default
presentation, with F1 selecting the original HUD and F2 selecting the existing
debug overlay. The original selection order was **original HUD → game sounds →
music**. After implementation, the user selected
[Step 12 object models/animations](../step-12/step-12-recover-object-models-and-animations.md)
(items, weapons, doors and acid pools) next, before sounds and music. This step
retains HUD ownership and its recorded limits.

The original HUD is now implemented. [Task 01](tasks/task-01-recover-hud-and-display-mode-ownership.md)
and the [recovery journal](../../../../journal/entries/original-hud-recovery-2026-10-28.md)
own fresh evidence: original asset/state-to-pixel recovery, default original HUD,
F1/F2 display ownership, native repaint/menu/persistence checks and explicit limits.

## Baseline and retained acceptance

Repository: `/home/rgrabowski/Work/EcstaticaRecompiled`.
Branch: `linux-e2-reconstructed-runtime`.
Current implementation baseline: `22c36a3f70bef9467e62299376905cbb5552dd71`.
Functional persistence is committed in `35be1cc`; menu/layout refinements are in
`22c36a3`. The worktree was clean before this documentation handoff. Inspect
actual status at continuation and preserve these new, uncommitted documents.
Do not commit, push or change tags unless requested. Existing v0.1.0/v0.2.0 tags
remain historical release coordinates; do not infer a new release or push.

[Step 10](../step-10/step-10-recover-game-save-load.md) retains persistence ownership.
Its [layout journal](../../../../journal/entries/menu-layout-and-font-2026-10-28.md)
records 28/28 focused Debug/ASan checks, 32 previews checked on both menu pages,
10 clean native exits, original-save preservation, independent four-artifact
parity and four affected builds. Three-stage menus have 54 passes and 48 explicit
skips. Those results are historical baseline evidence, not acceptance for HUD
changes. Preserve automatic dismissal after Load and clean preview cancellation.

Player/enemy recovery is accepted within its bounds. Investigation session saving,
replay and the gameplay regression suite remain closed milestones with minor
follow-ups deferred. Equipment polygons, further tower gameplay, exhaustive
rendering and arbitrary original-save progressions remain unqualified.

## Scope and display contract

1. Recover original HUD assets, registration, layout, palettes, values and update
   timing from original disassembly/Ghidra. Trace life-bar current/maximum values
   and the other visible indicators; do not assume every bar measures health or
   that 100 is always the maximum.
2. Default each new process to original HUD presentation, with the current debug
   text/status panels and labels off. F1 selects that mode; F2 selects the existing
   debug overlay. These are explicit, repeatable selections rather than cycling
   keys. Avoid painting both HUD presentations together.
3. Keep the selected presentation across menu open/close and Save/Load within the
   process. It is a host presentation choice, not a new field in original saves.
   Preserve original cinematic/modal HUD visibility rules and usable requesters.
4. Keep mode selection read-only with respect to game state: no health, timers,
   actor scripts, input ownership or save-format changes. Audit existing F1/F2
   bindings, key repeats, key-up handling and focus changes before wiring them.
   Keep F5 launching and F12 investigation/bookmarks working.
5. Separate HUD/overlay visibility from character/object rendering, diagnostic
   observation and existing mesh bypasses. Do not disable all diagnostic actor
   rendering or globally remove `E2R_PROXY_MESH_BYPASS` as a shortcut. In
   particular, preserve visibility/interaction of unrecovered objects/equipment
   through their existing scene-rendering fallback while hiding debug HUD text.
6. Mirror reconstructed C repairs in `E2Recomp/tools/GenerateRecon.js`; keep host
   presentation/input policy below the compatibility/backend boundary.

## First investigation and evidence

The [first task](tasks/task-01-recover-hud-and-display-mode-ownership.md) owns the
source map, known bypasses, concrete inspection order and verification sequence.
The [handoff journal](../../../../journal/entries/original-hud-handoff-2026-10-28.md)
records this priority change and its documentation-only status.

Original executable/data:

```text
/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
/home/rgrabowski/Games/Ecstatica2/
```

Installed `Saved/*.ECS` files remain protected. If a HUD regression needs Save/Load,
use private copies and verify an originally empty slot at test time. The existing
installation has occupied slots 0–4, 8, 9 and empty slots 5–7; never assume that
inventory remains unchanged. Do not write installed saves or use occupied slot 9.
Retain the existing `--data-dir/Saved` boundary and file hash guards.

## Acceptance criteria

1. A fresh normal launch presents the original HUD at the original gameplay
   handoff, without debug panels/text. Original life-bar artwork, placement,
   palette, scale, clipping and value changes have source and rendered evidence.
   Enumerate the other original HUD elements and verify their recovered meaning.
2. Real F2 input enables the current debug overlay; real F1 input restores the
   original HUD. Repeated switching, key repeats/release and menu transitions
   leave no stale rectangles, ghost text, duplicate HUDs or input latches.
3. Damage and a recovered healing route update the real life bar consistently
   with original state. Verify any recovered status/equipment indicators through
   the corresponding original conditions. Report unexercised branches explicitly.
4. Movement, animation, interaction and accepted Save/Load still work in both
   modes; restored values redraw correctly after Load, including fresh-process
   loading with the default original HUD. Preserve saved preview pixels and
   original files if exercising persistence.
5. Run relevant original-code fixtures, bounded native Debug/ASan checks, affected
   SDL/X11 builds, independent four-artifact generation parity and documentation
   checks. Keep current evidence separate from historical suite success.

## Workflow and limits

Use the single **Ecstatica Recompiled** F5 launch for human investigation. Agent
probes must specify bounded input/timeouts, recording disabled and private output.
Use `scripts/e2_original.py` for bounded original-code comparisons. Recover missing
argument/ownership contracts instead of filling unresolved registers speculatively.
Incrementally qualify rendering and mode transitions; a visible host-drawn health
number does not establish original HUD recovery.

No explicit usage/token budget was requested. Sounds, music, a new debug UI,
full object/equipment mesh recovery and broad stability/tooling projects are out
of scope unless a concrete dependency blocks this HUD step. Update the task,
step and dated journal with fresh implementation evidence and limitations.

## Change log

### 2026-10-28

1. Selected HUD recovery before sounds and music; recorded default original HUD,
   F1 original HUD and F2 debug overlay requirements for the next context.
2. Prepared the original-code investigation task; runtime remains unchanged.

## Implementation evidence — 2026-10-28

The original `0x4555b0` contract is EAX=name, EDX=x, EBX=y, ECX=centered;
`0x4559bc` selects life frame, armour and held-item indicators. Original
`0x456a3c`, `0x456f94` and `0x457410` own life/poison fill, player magic and
held-magic fill. The recovered read-only visual leaves are mirrored in the
generator. Host loading/rasterization uses installed original RAW assets and the
current indexed palette. A fresh presentation copy replaces the legacy dirty
rectangle/page mutations; original game pages and save thumbnails remain intact.
Script graphics, inventory/icon-page and unrelated mesh bypasses remain in place.

Default/F1 original and F2 debug mode consume both key edges before gameplay and
replay input. Labels/panels hide in original mode while character bodies and
object/equipment shapes remain visible. Modal/intro/cinematic gates suppress the
HUD; menu entry does not reset mode. The original visibility toggle now reads its
live keyboard byte rather than nonzero standalone image data.

Original-code comparisons pass in normal/ASan: 600 final graphic selections,
1,056 life/poison sequences, 212 held-magic sequences, 512 live visibility-toggle
decisions, 96 installed-sprite raster comparisons and 10,332 line pixel cases.
Final Debug/ASan private-slot probes each repeat two equipped Save/change/Load
cycles and load in a fresh process, with four clean native exits overall.
Eight F1/F2/F1 round trips restore identical final pixels and leave state/four
indexed pages unchanged; modal switching is pixel-identical. Installed saves and
all unowned private slots retain their hashes. Focus/repeat/release input, preview
cancellation, automatic Load dismissal and subsequent movement/attacks pass.

The focused HUD/menu/save/DirectDraw matrix passes 22/22; parity and 67 runner
contracts pass separately. All four SDL/X11 Debug/ASan builds pass. Natural damage and Debug healing **70→100** have verified real indexed bar
pixels; poison/invisibility/no-op observations and failed routes remain recorded
in the journal. Final focused integration passes **24/24**, including parity and
67 runner contracts. ASan healing remains unexercised.

High-mode native life, empty-hand and sword indicators are exercised. Higher
maximum life, armour upgrades, rod/capacity and nonzero player-magic branches have
original-code fixture evidence, with native gameplay journeys still unexercised.
Low-mode selection is compared, but low-mode planar gameplay and exhaustive
cinematic/translated/inventory UI are unqualified. Human F5 visual review and
broader rendering/tower/persistence limits remain separate from bounded tests.
