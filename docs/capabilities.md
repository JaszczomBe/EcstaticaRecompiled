# Project state and capabilities

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

The active target is Ecstatica II on Linux/i386 with original external game data.
The completed reconstruction milestone is a historical bounded state/surface
proof. Everyday development now uses SDL, original backgrounds and typed
diagnostic object markers alongside recovered animated character bodies.

| Area | Available capability | Acceptance boundary |
| --- | --- | --- |
| Build and editor | Clang 21 i386 Debug/ASan, SDL/X11 builds, selected-target F5 | Debug is the everyday choice; optimized runtime and 64-bit execution remain experimental/incomplete |
| Gameplay | Recovered movement, camera crossings, NPC/object population and bounded workshop activation | Human swimming, sword pickup, four kills and two broken doors verified; animation-cache stall repaired; Debug/ASan door passage and actual menu Quit pass; human random-potion pickup verified and delayed effects repaired with live Debug/ASan poison dispatch; bottle removal and subsequent sword use confirmed in the latest human run; visible health/potion diagnostics added; fresh Debug healing 85→100, poison onset, invisibility dispatch and conditional no-op verified; final effect expiry/cure remains open; latest alternate-target crash repaired with isolated generated Debug/ASan prefix evidence; extended stability remains a follow-up; animation-name parity restored for potion cleanup; natural effect summaries are optional; wider pickups/rendering remain deferred |
| Rendering and audio | Original animated characters, 76 selected object/animal/effect owners and 16 representation families (251 original resources), independent F3 geometry modes, backgrounds and palette/depth/page presentation; diagnostic fallbacks for remaining objects/equipment | Bounded Debug/ASan pixels cover animals, intro lightning, courtyard pools, flames, doors, roof effects, collection sparkle, storage gold sword/necklace and collectible representatives; tower door appearance and broader natural pickup/combat lifetimes remain unqualified; game sounds have bounded original/PCM/SDL-device coverage; software GM music has bounded original/MIDI/PCM coverage; human listening, broad audio events/transitions and remaining rendering are incomplete; original HUD artwork/default and F1/F2 retain bounded original-code/native evidence |
| Persistence | Original-format gameplay Save/Load, writable runtime slots and original read fallback | Debug/ASan repeated same-process and fresh-process loads restore active actors and sword ownership, then resume input/animation/attacks; saved previews display at 160×120 without dirtying game pages, original menu geometry/font and title alignment are restored, successful Load dismisses the menu; installed saves remain intact; arbitrary original progressions and malformed-file recovery remain unqualified |
| Investigation | Automatic F5 logging, replay, state timeline, rolling frames, pinned binary and debugger evidence | 16 MiB recording chunks and streaming replay remove the former 256 MiB ceiling; disk capacity, incomplete prefixes and strict replay divergence remain explicit |
| Recovery tools | Original-x86 fixtures, crash export, state/report queries, route expectations, dependency-aware Debug/ASan gameplay suite with concurrent configurations, shared checkpoints, three-stage menu coverage, one/two visible windows, unarmed combat and host allocation-fault checks, recovery/diagnostic index | Headless menu labels, three-stage restarts and Load/Save dialog checks pass after original-backed menu/surface repairs; broader persistence, audio and exhaustive rendering remain unqualified; sampled/fixture evidence does not establish complete game behavior; rr is optional and currently absent |

## Current implementation and next work

**Original music now plays through software General MIDI and SDL.**
[Step 05 Task 05](implementations/playable-sdl-runtime/steps/step-05/tasks/task-05-recover-original-music.md)
and the [music journal](journal/entries/music-recovery-2026-10-29.md) record original
DLL equivalence for 91 GM tracks, all 960 loader entries, music-only PCM,
independent settings, protected persistence and strict recording/replay. An
external SoundFont supplies instruments. Human listening, broader transitions,
hardware timbre and focus/device-loss recovery remain open; earlier limits remain.

**Original game sounds now play through SDL.** [Step 05 Task 04](implementations/playable-sdl-runtime/steps/step-05/tasks/task-04-recover-original-game-sounds.md)
and the [recovery journal](journal/entries/game-sounds-recovery-2026-10-29.md)
record exact original conversion for all 404 assets, real PulseAudio output,
Debug/ASan sound toggles and lifecycle, protected persistence, HUD/F3/inventory,
generation parity and six strict sound-event replay variants per configuration.
Human F5 listening, broader natural event classes and device-loss recovery remain
open. Music continues in Task 05 above; existing gameplay/visual limits and protected evidence
remain. No commit or push is made.

**The original Enter inventory/status menu is recovered.**
[Step 11 Task 02](implementations/playable-sdl-runtime/steps/step-11/tasks/task-02-recover-enter-inventory-and-progress-menu.md)
and its [recovery journal](journal/entries/enter-inventory-menu-recovery-2026-10-28.md)
record original artwork, scene-based inventory icons, gold, kills, power and
visited-bit progress. Real Enter/Escape, modal HUD/F3, protected same/fresh
Debug/ASan persistence and separate strict recordings pass. The original
99% completion cap and five-digit truncation remain. Human screenshot review,
low-mode gameplay and natural nonzero hourglass lifetime remain open. Existing
inner-castle acceptance limits are unchanged.

**Inner-castle recovery now has original-backed repairs and model selection.**
[Step 12 Task 04](implementations/playable-sdl-runtime/steps/step-12/tasks/task-04-recover-inner-castle-progression-crash-and-models.md)
and its [recovery journal](journal/entries/inner-castle-crash-and-presentation-recovery-2026-10-28.md)
identify loaded slot 6, sprite **73**, node **14**, action **253**, event **0x23**.
The original node/transform inputs and signed rectangle clipping are restored.
Debug matches all **3,190** recovered-prefix checkpoints; the source recording
remains incomplete. F5 selects **76** original owners, with all eight reported
presentation paths mapped. Fresh Debug/ASan mace pickup/persistence and stairwell
survival pass. Bounded post-event control/combat and same/fresh persistence also
pass from an explicitly documented diagnostic checkpoint; uninterrupted route,
equipped-armour human review and full gate/effect composition remain open. Runtime slots **5/123, 6, 7 and 9** remain protected.

**Tower progression now has bounded Debug/ASan acceptance.** The original head
hit drops key **264**, Space acquires it, the original door scene transfers it to
door **266**, and blocker **443** follows its authored track to permit passage.
F5 includes tower owners **259/264/265/266**. [Step 12 Task 03](implementations/playable-sdl-runtime/steps/step-12/tasks/task-03-recover-tower-key-trap-and-door-progression.md)
and the [recovery journal](journal/entries/tower-key-progression-recovery-2026-10-28.md)
record exact replay of session **20261028_161516_514**, identification of loaded
slot **6**, original-code conditions, locked-door refusal, real pixels, same/fresh
persistence at three puzzle stages and protected source saves. The needed change
was model selection; no puzzle logic or save repair was required. The subsequent
[tower/storage follow-up](journal/entries/tower-storage-render-followup-2026-10-28.md)
raises selection to **57 owners**, adding original collection sparkle, storage
gold sword/necklace and nearby gas/chest assets. Its **1,803-checkpoint** recording
replays exactly; Debug/ASan checks pass. A source-backed static-owner depth-copy
argument repair is included. The partly translucent door remains unresolved;
matching leaf comparisons do not prove full original-game appearance. Preserve
possible original defects and require a proven reconstruction mismatch before
changing rendering or pickup behavior. Broader tower journeys remain open.

The user selected **item, weapon, door and acid-pool models/animations → game
sounds → music** after HUD and recording recovery on 2026-10-28.
[Step 12](implementations/playable-sdl-runtime/steps/step-12/step-12-recover-object-models-and-animations.md)
and its [first task](implementations/playable-sdl-runtime/steps/step-12/tasks/task-01-recover-object-rendering-and-animation-contracts.md)
own the implemented first slice: original actor IDs **537,710,711,908,909,912,
980,3717** use recovered flat/box/rounded geometry and actions. Acid pools in
scene **350**, camera **116**, use animated flattened ellipsoids and rounded
bubbles. [Task 02](implementations/playable-sdl-runtime/steps/step-12/tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md)
retains variants and natural hazard/lifecycle acceptance. The
[recovery journal](journal/entries/object-rendering-recovery-2026-10-28.md) records
original-code parity, bounded Debug/ASan potion/sword/controlled-door/pool pixels,
protected persistence/HUD and retained live door failures. The [handoff journal](journal/entries/object-models-and-animations-handoff-2026-10-28.md)
records the selection.

The [latest human-play follow-up](journal/entries/animals-collectibles-and-projectiles-2026-10-28.md)
adds rats **601/608**, stable horse **663**, courtyard stone-ball/statue owners,
second blood squirt **1153** and armour-hit effect **1188**. Source-audited coin,
red/blue gem, trophy and crown representation families select their variants
without a per-instance ID list. F3 retains boxes for every recovered model;
unknown paths keep their fallbacks. Fresh Debug/ASan pixel/action, HUD/menu,
protected persistence, recording and generation checks are recorded there.

The retained [Step 11](implementations/playable-sdl-runtime/steps/step-11/step-11-recover-original-hud.md)
and its [first task](implementations/playable-sdl-runtime/steps/step-11/tasks/task-01-recover-hud-and-display-mode-ownership.md)
own recovered life/armour/hand/capacity/magic graphics and original-default/F1/F2
presentation. Original visual state is composed onto an indexed presentation copy;
game pages, diagnostic observations and original saves remain independent.
Fresh evidence and remaining native indicator branches are recorded in the
[HUD recovery journal](journal/entries/original-hud-recovery-2026-10-28.md).
Investigation session saving, replay and the
gameplay regression suite remain closed milestones with minor limits deferred.

The [runtime implementation](implementations/playable-sdl-runtime/playable-sdl-runtime.md)
owns current acceptance. Current handoff HEAD is `a1898a8745e8d42cec9741d25ca37433db2a3a57`
on `linux-e2-reconstructed-runtime`, containing inventory/status recovery.
Inner-castle recovery is in `969af3b`; object/F3 recovery is in `990bdd9`, HUD recovery is in `44ebf8f`, chunked
recording/streaming replay in `a2a6043`, functional persistence in `35be1cc` and
menu/layout refinements in `22c36a3`. The historical v0.2.0 tag
remains at `ae54e6f8e4dc`; no newer release/push is inferred.

The [persistence step](implementations/playable-sdl-runtime/steps/step-10/step-10-recover-game-save-load.md)
and [save/load journal](journal/entries/game-save-load-recovery-2026-10-27.md)
retain version-4 serialization, actual repeated menu round trips, fresh-process
restoration and file-rejection limits. Saves write to `--data-dir/Saved`
(normally `~/.ecstatica2/Saved`); installed saves are read-only fallbacks. Tests
use private copies and confirmed originally empty slots only. The
[menu layout/font follow-up](implementations/playable-sdl-runtime/steps/step-10/tasks/task-05-recover-menu-layout-and-font.md)
passes 28 focused Debug/ASan checks and preserves the original saved-image format;
its three-stage menu sweep retains explicit unsupported checks. Object-model
recovery must preserve these paths and verify affected behavior afresh.

F5 enables `E2R_PLAYER_MESH=1`, `E2R_NPC_MESH=1` and the explicit owner/family
selection in the [build guide](building.md). The [courtyard/intro/decorative
follow-up](journal/entries/courtyard-acid-flames-and-roof-effects-2026-10-28.md)
records the latest full pinned replay, additional acid styles, scene-zero lightning,
potion shelf/well bottle, animated flames, red/blue doors and separate roof glows.
The original recording ends in mixed mode: recovered coins/potions intentionally
retain boxes there. Fresh render previews and a new recording are separate from
replaying an old input stream with a changed render-call sequence.
**F3** cycles original models with boxes for unrecovered actors, models plus all
boxes, and boxes only. It preserves original poses, game pixel/depth pages,
HUD/F1/F2 and saves; original background artwork remains in all three modes.
The [variant/F3 follow-up](journal/entries/object-variants-and-f3-2026-10-28.md)
records the human-reported omissions, exact additional owners, bounded pixel
checks and retained natural-gameplay limits. Earlier eight-asset evidence above
remains the first slice rather than exhaustive coverage.
The [enemy recovery journal](journal/entries/enemy-model-and-animation-2026-10-27.md)
records live guard poses, actual enemy-inflicted damage, retained combat failures
and current acceptance limits. The [player journal](journal/entries/player-model-and-animation-2026-10-27.md)
retains the original projection correction and user acceptance.

The subsequent [human-play follow-up](journal/entries/enemy-play-crash-and-dropped-potion-2026-10-27.md)
repairs false animation-directory entries that led into bitmap eviction and
restores the full original representation-name pool for dropped-potion script
conditions. Fresh original-code and bounded native evidence remain distinct from
full-suite, complete replay and long-play acceptance.

The [tower eviction repair](journal/entries/tower-actor-eviction-crash-2026-10-27.md)
is also included in v0.2.0: actor removal and root reuse pass original-code
comparisons, while Debug and ASan replay limits and further tower acceptance
remain recorded. These limits remain alongside the selected object-model recovery.

The prior [door approach correction](journal/entries/regression-door-approach-reliability-2026-10-27.md)
and [headless sweep](journal/entries/headless-regression-sweep-2026-10-27.md) retain
historical suite results and counterexamples. They do not establish full-suite
acceptance for the newly enabled player renderer. Follow the
[tooling implementation](implementations/debugging-tools/debugging-tools.md) for
debugger and replay limits.

The [milestone plan](plans/runtime-milestones.md) owns later rendering, control,
timing, sound, persistence and portability direction. The
[journal](journal/journal.md) records recent changes. Check working-tree and commit
state as described in the root README; local repairs can be newer than the last commit.
