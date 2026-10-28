# Original HUD recovery — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 11 Task 01](../../implementations/playable-sdl-runtime/steps/step-11/tasks/task-01-recover-hud-and-display-mode-ownership.md).
The user authorizes implementation after the documentation-only handoff at
`22c36a3f70bef9467e62299376905cbb5552dd71`. All staged documentation is preserved;
no commit, push or tag change is performed. Order remains **original HUD → game
sounds → music**. Evidence root: `build/evidence/hud-2026-10-28`.

## Original contracts and indicator meaning

The external `E2WIN95.EXE` is inspected with bounded disassembly and executed only
in isolated fixtures through `scripts/e2_original.py`. Runtime does not execute
original machine code. The following contracts come from original instructions,
not from the lost `extraout` register expressions in the export.

| Original range | Recovered contract |
| --- | --- |
| `0x4559bc..0x455e84` | Actor-0/intro gate; life frame, armour and hand/held-item selection |
| `0x4555b0..0x455850` | EAX=name, EDX=x, EBX=y, ECX=centered; only centered graphics scale input coordinates |
| `0x44a178..0x44a2ac` | `graphics/` or `lowgraph/`, 32-byte RAW header, BE width/height at +8/+10, skip 768 palette bytes, then row-major indexed pixels |
| `0x45563e..0x455706` | Convert indices 0/1 to transparent 255; find a free named slot and retain dimensions/pixel ownership |
| `0x455094..0x455294` | Draw pending graphics to the back physical page and decorated background page 2; update life/magic fills and dirty rectangles |
| `0x455294..0x455424` | Restore removed graphics from clean page 3 into decorated page 2 and physical pages; retain queued redraw ownership |
| `0x4554cc..0x4555b0`, `0x455850..0x455940` | Preload and temporary-graphic paths have distinct register/transparent-index contracts |
| `0x455940..0x4559bc`, `0x455e84..0x455fe8` | Release a named graphic; drawn slots become pending removal; HUD cleanup enumerates resolution-specific names |
| `0x456a3c..0x456f94` | Current/max life scaling, timer-5 poison limit and three page-specific fill draws |
| `0x456f94..0x457410`, `0x457410..0x4575c4` | Player magic groups and held-item magic fill |
| `0x41b540..0x41b740` | Linear indexed line raster excludes the final endpoint, including zero-length segments |
| `0x416221..0x416255` | Original visibility toggle consumes live one-byte keyboard queue `0x4c39a7` |

`FUN_004559bc` chooses `life1/2/3` from actor **+0xee maximum life**:
100 selects frame 1, 200 frame 2, otherwise frame 3. High-mode origin is **(25,8)**;
low mode uses `llife1/2/3` at **(12,4)**. Actual fill reads signed current life at
**+0xec**, divided by `maximum_life/100`. High-mode bars start at x=69 and span
100 pixels, with three/five/seven rows for the recovered 100/200/300 maxima.
The 300 frame starts at y=22; the others at y=24. Low-mode widths/coordinates
and its separate poison branch are retained exactly by comparison.

Player **+0x182** selects `armour2` above 100 or `armour3` above 200, at
**(395,15)** in high mode. The default value 100 adds no armour icon. Player
**+0x184** supplies up to 24 magic units: six groups of four, with `magic1*`
full, `magic2*` for a remainder of two/three and `magic3*` for one. The first
high-mode icon is at **(223,10)**, advancing 27 pixels; the suffix identifies the
original named slot, rather than six different player fields.

Actor **+0x54 → node+0x20 → held node+0x13a** identifies the item in the hand.
The empty hand uses `hndicon1`; held flag **+2 & 0x10** selects `rodicon1`,
otherwise `swdicon1`, all at **(531,7)**. Capacity/status frames `bar1..5` use
held **+0x182**, or **+0x186** when the held magic field **+0x184** is nonzero.
The tier is `min(capacity/100-1,4)` above 100, at **(468,20)**. A nonzero held
magic field adds `magibar1` at **(565,21)** and a fill scaled by 5/2, capped at
50 pixels. Low mode uses the original `l*` asset names and positions. These
fields are established by code; further item-specific gameplay semantics are
not inferred from the meter artwork alone.

Poison does not replace the actual life field. `DAT_0047ab2c` and timer type 5
supply `(deadline-clock)*100/duration`; the original uses indices **11,12,13,15**
for life/poison/remainder segments. Missing timers read as the normal limit 100.
The observer deliberately does not clear the duration or advance any timer.

## Rendering and display ownership

The original graphic table has 25 nine-byte names, pixel pointers at `0xac4a6c`,
packed dimension/position arrays, and states loaded/pending/drawn/removing.
Enabling its current reconstructed provider would expose unresolved names,
coordinates, allocator/free ownership, sprite inputs and restore callers.
`FUN_00455fe8` also belongs to the separate icon/inventory page, including
`graphics/iconpage.raw` and palette operations. Script opcodes **0x27** (centered
registration), **0x29** (removal), **0x2a** (preload) retain their diagnostic
operand-span skips. None is globally enabled by this recovery.

Instead, `E2R_GetOriginalHudState` observes the live actor table at **0x630b60**;
`E2R_DrawOriginalHudState` reproduces the original final named-slot selections
and bar commands with explicit arguments. Both are durable generator output.
The host loads immutable original assets, retains their indexed colours and
clips their raster into a fresh copy of the selected indexed game page before
SDL RGB conversion. This replaces legacy dirty-page mutation for this HUD only.
Every frame rebuilds the visual state, so switching, damage, camera changes and
Load cannot reuse old bar or icon rectangles. Physical game pages, depth buffers,
backgrounds and saved thumbnails remain untouched by HUD presentation. The
32-byte RAW header and palette skip match the original loader; assets are not
copied into the repository or replaced with host-drawn approximations.

A process-local host selector defaults to original HUD. **F1** selects original;
**F2** selects the existing debug overlay. Both key edges are consumed before
replay/game input; repeats are idempotent, and no held-mode latch needs release
on focus loss. The replay physical-control path supports the same presentation
choice without changing deterministic game events. F12 bookmark/capture and the
single F5 launch remain in place. Selection is absent from original saves.

Original mode hides diagnostic labels, top panels and bottom health/status text.
It preserves the diagnostic scene shapes used by objects/equipment, original
player/NPC bodies and all read-only replay/inspection observation. Menus suppress
both HUD presentations. Intro, cinematic and original visibility gates remain.

## Counterexamples and repairs

`native-debug-01` passes switching/private persistence but captures reveal the
original HUD is absent. Its initial assertion was insufficient: it compared the
two display modes without requiring original life pixels. The decompiler's
standalone `_DAT_00630b60` stays zero; the actual actor table is populated.
The snapshot now reads that original memory owner and tests require composition.

`native-debug-02/03` then fail the stronger assertion. Live state establishes
`DAT_0047a448=1` with no user HUD key. Its exported standalone keyboard symbol
starts with unrelated image value `0xaba2fcba`, while original startup clears the
mapped queue. Recover `FUN_00415d40`'s **live byte** read/clear at `0x4c39a7`;
do not force the visibility flag or change saves. The added fixture compares
512 original toggle decisions. `native-debug-04` then shows the original skull,
life artwork/fill and hand indicator, with clean switching and private persistence.

`native-asan-05` reaches equipped persistence but Joe dies during restored live
movement. This is a failed gameplay route, not an ASan report or HUD acceptance.
`native-asan-07` passes with the established noncombat equipment profile. Final
runs below use that explicit profile in both configurations. Natural combat
routes remain live. `damage-heal-debug-16` fails to uniquely observe potion
consumption after a 300-update wait; retain its journal and pixel samples.
No failing route is relabelled as a passing healing check.

## Fresh verification

`check-e2-original-hud.py` passes normally and with ASan:

- **600** final life/armour/hand/capacity/player-magic selections across both
  resolutions, all three life maxima, empty/held hands and every player magic value.
- **1,056** life/poison line sequences across original pages 0/1/2.
- **212** held-magic meter sequences, including signed/zero/clamped values.
- **512** original live-keyboard visibility-toggle decisions.
- Read-only actor/timer snapshots and intro/modal/cinematic suppression checks.

`check-e2-hud-pixels.py` executes the original sprite and line raster with
intercepted lock/unlock/synchronization services. Normal/ASan each pass **96**
installed high-mode sprite comparisons (all 32 HUD assets at three positions)
and **10,332** horizontal line cases with clipping, reverse and zero-length
segments, padded pitch and untouched surrounding pixels. Composition tests prove
source pages unchanged, idempotent mode keys, identical restored pixels and
modal suppression. Line endpoint comparisons caught and corrected the initial
inclusive-end implementation. The marker fixture passes normal/ASan and checks
original-mode panel suppression while preserving the exact object fallback pixel.

`final-debug-25` and `final-asan-26` each Save/change/Load twice with actual sword
ownership, then restore in a fresh process and resume movement/attacks. **Four
native processes exit zero**. **Eight** gameplay F1/F2/F1 round trips reproduce
identical final SDL pixels and leave gameplay/four indexed pages unchanged.
Repeated downs, key release and SDL focus loss/gain are exercised. Two modal
switching sequences produce identical requester pixels in all three selections.
Both modes survive actual menus and Save/Load; each fresh process defaults to
original. Captures include physical/background indexed pages, composed indexed
HUD and final SDL/window pixels.

**16** preview selections compare all **32** displayed-page images at 160×120,
with physical game-page preservation; filled/empty/filled cancellation performs
no load. Automatic successful-Load dismissal remains verified. All writes use
private copies of freshly confirmed empty slot **5**, never installed saves or
quick-save slot 9. Installed and every unowned private slot retain size/hash;
per-run preservation reports are retained.

The focused original HUD/menu/save/DirectDraw matrix passes **22/22** in **4.74 s**.
Separate parity/runner checks pass, including **67** runner contracts. The two
HUD fixtures are registered in the regression catalogue; normal persistence
journeys now include HUD checks and prerequisites. Independent scratch generation
matches **all four artifacts**. SDL/X11 Debug/ASan builds pass. Evidence logs
record executable hashes, original fixture ranges and dependency interceptions.

## Native damage/potion observations and limits

Fresh input-only routes retain original NPCs, physics, potion selection and RNG.
Every checkpoint verifies the actual life/max fill when the poison limit is
inactive and saves indexed/RGB captures. Debug 06 observes **100→95→90** and
invisibility; Debug 12 observes **100→95→65** and poison; Debug 13 observes
**100→95→70** and the conditional no-op. ASan 08/14 observe **100→95** and poison;
ASan 17 observes **100→95→60** and poison. All these complete real menu Quit.
These runs qualify damage and their observed branches. Debug 22 then selects
**189→156**, executes action **391** (the low word of the recorded argument),
heals **70→100**, removes the bottle and verifies the
real indexed fill before/after healing, menu cancellation and resumed movement.
It completes real Quit with exit zero on the final binary. This establishes a
fresh recovered healing route with actual HUD pixels.

Further retained outcomes: Debug 18 poison **65→65**; ASan 19 poison **95→95**.
Debug 20 dies during potion traversal; ASan 21 rejects damage without an attributed
eligible hit; ASan 23 exhausts the navigation update budget. These failures do not
qualify healing and are not sanitizer findings. ASan healing remains unexercised;
its damage, poison, persistence and original-code/raster checks pass. The final
focused matrix `final-suite-24` passes **24/24** in **14.27 s**, with no failures,
blocks or skips; it includes parity and all 67 runner contracts. The final SDL
marker checks also prove F2 can show diagnostics without scene-cue environment
flags, while preserving the independent scene-rendering selection.

Native evidence exercises high-mode life, empty hand, sword and potion status.
Higher maximum life, upgraded armour, rod/capacity tiers and nonzero player magic
have original-code fixtures but no native item/progression journey in this pass.
Low-mode selections are compared; low-mode planar gameplay is unqualified.
Poison expiry/cure, exhaustive cinematics, all translated UI, icon/inventory
recovery, arbitrary original saves and further tower gameplay remain outside
this acceptance. A human F5 visual review is still distinct from agent captures.
Sounds and music remain later selected work.

Final documentation/tree and whitespace checks pass. The evidence summary lists
all native reports, original installed-save preservation, final source/binary
hashes and the explicit difference between fixture, native and human acceptance.
