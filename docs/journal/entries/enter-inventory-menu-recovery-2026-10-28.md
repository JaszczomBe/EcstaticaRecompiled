# Enter inventory/status menu recovery — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 11 Task 02](../../implementations/playable-sdl-runtime/steps/step-11/tasks/task-02-recover-enter-inventory-and-progress-menu.md).
The [handoff](enter-inventory-menu-handoff-2026-10-28.md) retains the supplied
original-game screenshot description. Evidence root:
`.tmp/enter-menu-20261028/`. Existing documentation edits are preserved. No commit
or push is made.

## Reproduction and original contracts

Bounded Debug baseline probes reach fresh gameplay and load a private runtime
slot 6. Real SDL Enter sets the live byte at **0x4c39ac** to 1, but dispatch never
reaches `0x455fe8`: the reconstructed caller reads its detached, already-cleared
export. Both baseline processes finish actual menu Quit. The sandbox rejects
native i386 execution with SIGSYS; bounded native/original-x86 checks run through
the approved execution boundary, using private outputs and recording off except
for the explicit recording checks below.

Original disassembly establishes:

| Range | Recovered behavior |
| --- | --- |
| `0x4161c5..0x4161f0` | Consume the live one-byte Enter queue; dispatch only when the cinematic gate at `0x47a34a` is zero; request redraw |
| `0x455ff1..0x4561b6` | Reject during script wait, temporarily select high resolution when needed, load view-zero palette and `graphics/iconpage.raw`, draw the page/HUD, pump input until Escape, clear Escape, restore presentation, invalidate scene and clear input |
| `0x4561d7..0x45646b` | Resolve fifteen named scene conditions; draw each bright item/elder overlay only when its scene's flag byte at `0x670c38 + index*2` has bit 8 |
| `0x456478..0x45668f` | Draw `timer1` when the original total timer is nonzero; mask only index-7 pixels with original 0/11 colours and integer division |
| `0x45668f..0x4566d9` | Original power 150 selects one `powgem1`; 200 selects two; other values add none |
| `0x4566d9..0x456788` | Kill counter at `0x47ab18`; gold at `0x47ab14` multiplied by ten; completion from set bits in 150 bytes at `0xac4b00`, multiplied by 100, divided by **1001**, capped at **99** |
| `0x456874..0x456924` | Right-aligned digits with ten-pixel spacing, five positions for gold/kills and two for progress; truncate excess leading digits |
| `0x455850..0x455940` | Temporary graphics take name/x/y in EAX/EDX/EBX; index 1 becomes transparent, while index 0 stays opaque |

The eight central overlays are `ringicon`, `amuicon1`, `lampicon`, `shdicon1`,
`shdicon2`, `scrlicon`, `amuicon2`, `kingicon`; the segmented diagram uses
`elder1..7`. These are original named scene predicates, not a newly inferred held
item list. The lower shield panel carries the power-gem branch, rather than an
invented numeric statistic. The circular dial's artwork remains original; no new
radial completion animation is introduced. `0x4273cc` increments the kill counter
for eligible non-player deaths; the page does not independently establish which
combatant caused each death.

The original routine calls only the input pump while open: actor simulation,
actions and game timers do not advance through the gameplay scheduler. Existing
focus/message processing remains in that pump. It draws the gameplay HUD without
testing the ordinary HUD-hidden preference. F1/F2 and F3 remain host display
choices and are suppressed visually over the status page without losing their
selection on return.

## Implementation and proven mismatches

The Enter caller now reads/clears the live queue. The recovered synchronous
lifecycle retains the original script-wait/cinematic gates, high-mode transition,
view-zero palette selection, Escape consumption, scene invalidation and input
cleanup. Unresolved file/temporary-graphic register expressions are replaced by
explicit state/painter contracts. `E2R_GetInventoryState` and
`E2R_DrawInventoryState` are mirrored in `GenerateRecon.js` alongside the caller
and lifecycle repairs.

The host loads immutable installed RAW assets and builds a fresh indexed status
presentation, using the existing HUD boundary. `ICONPAGE.RAW` is **640×512**, but
the original reads only **640×480** screen pixels; the remaining rows stay off
screen. Ordinary HUD sprites normalize 0/1 to transparent; inventory sprites
normalize **only 1**, as the original temporary loader does. Indexed gameplay
buffers and save previews remain untouched by presentation. The legacy physical
page clear/copy operations are represented by immutable composition and the
original scene invalidation, rather than enabling unresolved legacy dirty-page
and script-graphic machinery. No global mesh bypass is removed.

SDL scene/debug overlays now recognize this modal page, just as they already
recognize requesters. The original gameplay HUD remains above the page, even
when F2 is selected; closing restores the selected gameplay display. Physical
pages never acquire status artwork or stale rectangles. X11 shares indexed
composition and builds successfully; native lifecycle checks use SDL.

A second proven mismatch is scalar ownership. The original-format serializer
reads/writes mapped **0x47ab14/18/28**, while gameplay originally updated detached
exports. All reconstructed uses of these three fields now share mapped storage,
including new-game initialization, collection, death counting, script updates,
combat power and status observation. Native fresh power is **100**, and original
progressed saves restore their actual counters/power. This preserves the original
format and arithmetic; it does not reconstruct values already lost in older
reconstructed saves, normalize zero power or rewrite occupied files. A generator
scanner preserves comments and string/character literals while replacing only
these three identifiers. Independent generation matches all four artifacts.

## Fresh acceptance

All final SDL/X11 Debug/ASan builds pass. The focused matrix passes **22/22** in
**5.54 seconds**, with no failures, blocks or skips. The suite catalogue includes
`Original.Inventory` for Debug and ASan; successful persistence journeys now
include native status checks. All **67** runner contracts pass after updating
the catalogue count to 243 logical cases.

Normal and ASan original-x86 checks each pass:

- **256** status selection/digit/progress/timer-mask cases, including missing
  scene names, differing scene flags, negative/overflowing digit inputs,
  0/1000/1001/1200 visited bits and power branches. Detached statistic exports
  deliberately differ from mapped state.
- **768** live Enter consumption/eligibility decisions.
- **81** installed inventory sprite/padded-pitch pixel comparisons, plus the
  original **96** HUD sprite and **10,332** line pixel comparisons. Immutable
  page cropping, source preservation and modal F1/F2/F3 composition pass.
- Existing HUD selections/fills, full original writer bytes, menu geometry/font,
  slot callbacks and signed/wrapping timer restoration pass in the focused matrix.

`final-persistence-{debug,asan}` each perform two actual equipped Save/change/Load
cycles, then fresh-process restoration. `progressed-persistence-{debug,asan}`
repeat that journey starting with a private installed **slot 3**, label
`last stop`, with live population. All **eight native processes exit zero**.
Every Load compares original actor/script/timer/attachment state and status values;
movement, original attack actions, HUD switching, requester cancellation, saved
previews and actual Quit pass. Only verified empty **private slot 0** is written.

The progressed page has **93%**, **728** kills, original gold value **192750**,
power **200** and thirteen active item/elder predicates. The original five-digit
gold renderer displays **92750**; the excess leading digit is deliberately
preserved as truncation. Fresh pages show 0%/0 kills/0 gold with power 100. No
screenshot values are hardcoded. Across these eight processes, **24** page
open/close checks verify stable live values, frozen actor bytes, unchanged four
indexed pages and HUD/F3 modal composition, including after fresh Load.

`debug-final-{fresh,loaded}` and `asan-final-{fresh,loaded}` add four clean native
exits with repeated Enter downs while modal, repeated open/close, SDL focus loss/
gain, F1/F2/F3, resumed movement and real main-menu cancellation/Quit. These use a
private runtime slot 6 as well as fresh gameplay; attack acceptance belongs to
the separate equipped/progressed persistence routes.

`final-recording-debug` and `final-recording-asan` each capture **15 input events**
and **26 checkpoints**, including actual Enter/release/Escape/release. Each passes
**five strict replay variants**, including inspection off and a debugger pause,
with 64 KiB chunk rotation. The reports retain recording identities, row counts,
clock-run counts and byte totals. No compatibility relaxation or incomplete-tail
acceptance is used for these recordings.

`preservation-before.json` / `preservation-after.json` verify **199 protected
files unchanged**: installed saves, occupied runtime slots **5/123, 6, 7, 9**,
crash session `session_20261028_173846_961` and the prior preservation tree,
including pinned binary, source context and recording. Each persistence report
also verifies source and every unowned private save hash.

## Counterexamples and remaining limits

The first pixel check exposed SDL debug/scene overlays over the page; the modal
suppression repair precedes final passing captures. An initial persistence probe
stalled because its Save breakpoint callback attempted a nested inferior function
call. The probe now observes save-time status directly from memory; production
behavior was not changed for that tooling fault. An intermediate generator pass
missed identifiers around comment apostrophes; the final comment-aware scanner,
fresh-power checks and final builds/recordings supersede that incomplete pass.
One intermediate ASan replay correctly rejected a binary replaced during the
build; the final binary is held fixed through all five successful replay variants.

Early slot-6 attack and menu-resume route assertions failed; their logs are
retained. Final slot-6 acceptance covers menu lifecycle and movement, while the
independent equipped and original-slot-3 routes prove post-close attacks. These
failures do not authorize changing original navigation, combat or save values.

Human F5 visual review against the supplied screenshot is still open. The
installed RAW artwork/palette is retained; no recolouring is inferred from the
handoff's salmon-background description. Low-resolution mode switching/planar
play, natural nonzero hourglass lifetime, every equipment acquisition, translated
UI and arbitrary original saves remain unqualified; timer/power/icon boundaries
have original-code/raster evidence as specified above. Audio remains deferred.

Inner-castle limits are unchanged: all 3,190 historical prefix checkpoints match,
but that source recording is incomplete. Uninterrupted extended route,
equipped-armour human review and full gate/effect composition remain open.
