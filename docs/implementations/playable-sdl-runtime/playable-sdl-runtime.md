# Playable SDL Runtime

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Implementations and task state](../README.md)
<!-- /docs-tree:parent -->

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-10-28
Parent Plan: [Runtime Milestones](../../plans/runtime-milestones.md)

## Goal

Turn the reconstructed Ecstatica II Linux runtime into a practical SDL developer runtime with visible actors, usable controls, repeatable diagnostics, and recovered game behavior.

## Scope

1. Reproducible generated code and bounded runtime validation.
2. Actor/action initialization and rendering after the intro.
3. Gameplay controls, camera behavior, and requester fidelity.
4. Timing, initial audio compatibility, and developer bootstrap.
5. Functional original-format game save/load and writable runtime storage.

## Non-Goals

1. A release-ready port, full original fidelity, or 64-bit core migration.
2. Replacing recovered logic with speculative shortcuts or direct SDL calls.
3. Broad generated-file changes unrelated to a source-backed repair.

## Selected next continuation — Object models and animations

**The immediate work remains [Step 12 Task 04](steps/step-12/tasks/task-04-recover-inner-castle-progression-crash-and-models.md),
now with reproduced crash, original-backed repairs and bounded model evidence.**
The [recovery journal](../../journal/entries/inner-castle-crash-and-presentation-recovery-2026-10-28.md)
identifies slot **6**, sprite **73/w_sprit3**, node **14**, action **253** and
event **0x23**. Original EAX/node and three-node pose contracts are recovered;
signed clipping repairs prevent negative projected rectangles from corrupting
pixel/depth buffers. Both changes are mirrored and compared against original x86.
Debug strictly matches all **3,190** recovered-prefix checkpoints through
**9684450756**, then reports the incomplete tail. ASan compatible replay of that
Debug recording is not accepted; fresh native input and recordings are separate.

F5 now selects **76 explicit owners**, adding original teleport, head/gate,
armour, wizardess polygon detail, prison key, mace/sparkles and stairwell
strike/explosion resources. Fresh Debug/ASan slot-5 ascent, mace pickup,
same/fresh original-format persistence, F3/HUD and natural stairwell survival
pass within the journal's bounds; the previous five-process tower regression
also passes. Bounded post-event control/combat and same/fresh persistence also pass under
Debug/ASan, from a documented original-format diagnostic checkpoint after the
strictly matched event. Event **0x20** and its direction/roll helper required the
same original register/pose recovery. Uninterrupted human-route reproduction,
equipped-armour human review and full gate/effect composition remain open. Protect occupied runtime slots **5/123, 6, 7 and 9**;
new tests use a private game tree and a freshly empty private slot **0**.
Preserve possible original defects and require a proven reconstruction mismatch.

**Tower key/trap/door progression passes bounded Debug/ASan checks.**
[Step 12 Task 03](steps/step-12/tasks/task-03-recover-tower-key-trap-and-door-progression.md)
and its [recovery journal](../../journal/entries/tower-key-progression-recovery-2026-10-28.md)
identify the original mechanism: strike head **265**, pick up the fallen key
**264** with Space, then approach door **266** holding it. Original scene **68**
transfers the key to the door and moves blocker **443** along its authored track;
Joe actually crosses the doorway. The existing loaded-state logic works.
The subsequent [tower/storage follow-up](../../journal/entries/tower-storage-render-followup-2026-10-28.md)
adds original collection sparkle, necklace, gold sword and nearby gas/chest owners:
F5 now selects **57 explicit owners** plus 16 families. A narrow static-owner
depth-copy repair restores original register arguments and is mirrored in the
generator. Collision, pickup reach, trap timing and save format stay original.

The exact pinned human recording matches all **964 checkpoints** using private
copies of runtime saves, with loaded slot **6** established at the original menu
loader. Fresh Debug/ASan journeys verify locked-door refusal, original pixel
writes for all four owners, acquisition, door passage, three same/fresh-process
Save/Load stages, F3, HUD/F1/F2, menus and clean Quit. Source/user saves remain
unchanged. **2,720** original-x86 cases per mode cover scene phase/negation,
facing and held-key conditions. Four builds, four-artifact generation parity and
separate chunked recording/replay checks pass. The new human recording matches
all **1,803 checkpoints**; fresh Debug/ASan tower persistence and storage pixel
checks pass. The reported partly translucent door remains unresolved: captured
triangle comparisons match original x86, without establishing full original-game
composition. Preserve possible original defects; change behavior only on a
proven reconstruction mismatch. Difficult pickup, unarmed head interaction and
wider tower traversal remain unqualified. Task 02 retains
remaining decorative/acid coverage; sounds and music remain deferred.

The user selected original **item, weapon, door and acid-pool models/animations**
after HUD recovery and the recording repair. The revised next order is
**object models/animations → game sounds → music**.
[Step 12](steps/step-12/step-12-recover-object-models-and-animations.md) and
[Task 01](steps/step-12/tasks/task-01-recover-object-rendering-and-animation-contracts.md)
own the first bounded slice, now implemented: actor IDs **537,710,711,908,909,
912,980,3717** use original rounded, flat-polygon and box geometry and original
actions in F5. Other object/equipment fallbacks remain. Acid pools in scene
**350**, camera **116**, use animated flattened ellipsoids/rounded bubble nodes,
not polygon water or sprites. [Task 02](steps/step-12/tasks/task-02-qualify-object-variants-and-natural-acid-lifecycle.md)
owns remaining variants and the naturally reached acid-room lifecycle.

The [recovery journal](../../journal/entries/object-rendering-recovery-2026-10-28.md)
records **3,072** flat-pixel/depth cases and **12,288** box-face comparisons per
mode, original owner/pose contracts, four builds and independent four-artifact
parity. Native Debug/ASan checks cover potion removal followed by equipped sword
use, controlled door destruction/passage and successive pool action frames in an
explicit asset preview. Protected repeated same/fresh-process Save/Load and
HUD/F1/F2 pass in both configurations; installed saves remain intact. Two live
door attempts retain their approach/combat failures. Human visual review, natural
pool traversal/hazard behavior, textured/planar rendering and all object variants
remain unqualified. Sounds and music stay deferred.

The subsequent [human-play/F3 follow-up](../../journal/entries/object-variants-and-f3-2026-10-28.md)
adds dropped bottles **3820–3822**, smith axe **603**, door **963** and blood
owners **5/1085** to the original selection, now fifteen IDs. **F3** independently
cycles original models with unrecovered boxes, mixed models/boxes, and boxes
only. Diagnostic representations remain available for recovered characters and
objects. Debug/ASan checks include actual pixel writes, read-only mode cycling,
menus and protected Save/Load; remaining variants and natural acid traversal
stay in Task 02. The live combat failure is retained as a failure.

The [next human-play correction](../../journal/entries/animals-collectibles-and-projectiles-2026-10-28.md)
extends F5 to **35 explicit owners** plus **five collectible representation
families/65 original actor resources**. Rats **601/608**, horse **663**, courtyard
stone balls/statues, blood **1153** and armour-hit effect **1188** use their
original geometry/actions. Collectible family selection reads original requested
and saved standing representation IDs; it does not alter collection mechanics.
Debug/ASan observe original rounded/flat pixels and animation progression, retain
all F3 boxes and pass protected persistence/HUD/menu/recording checks. Natural
collection/removal journeys, complete combat effects, other unqualified assets
and the natural acid-room lifecycle remain open. Unknown sparks **1189** retains
its fallback; the green props identified near corpses are separate effect/trap
owners, not evidence for changing character/corpse classification.

The [courtyard/intro/decorative follow-up](../../journal/entries/courtyard-acid-flames-and-roof-effects-2026-10-28.md)
maps the next human recording and matches its complete pinned replay through
**2,492 checkpoints**. F5 now selects **47 explicit owners** plus **16 audited
representation families/251 original resources**: both newly visited courtyard
pool groups, scene-zero lightning, animated small/large flames, red/blue doors,
potion variants/shelf/well bottle, chalices, a roof wand and eight separate roof
glow effects join the earlier coverage. Pools remain flattened ellipsoids;
lightning and flames also use original rounded geometry. Native Debug/ASan
previews establish actual pixels and action progression, not hazard or future
door-destruction acceptance. Mixed F3 mode intentionally retains recovered
pickup boxes. Failed live/controlled navigation and cross-render-policy replay
attempts remain failures; fresh final-configuration persistence and recording
checks have separate evidence. Unknown decorative owners, sparks **1189** and
unsupported paths keep their fallbacks. Audio remains deferred.

Current handoff baseline is `990bdd9ea080ccdf434f626d4d20bf440f12a422` on
`linux-e2-reconstructed-runtime`, containing the preceding object/F3 recovery.
Its earlier implementation baseline was `a2a6043`. HUD recovery is committed in `44ebf8f` and
chunked recording/streaming replay in `a2a6043`. Preserve subsequent worktree
changes; no new commit, push or tag action is requested. The
[selection journal](../../journal/entries/object-models-and-animations-handoff-2026-10-28.md)
records this documentation-only handoff. Keep accepted characters, HUD/F1/F2,
menu/persistence, protected saves and independent diagnostics/recording intact.
The [recording journal](../../journal/entries/chunked-recording-and-streaming-replay-2026-10-28.md)
retains large-recording and replay evidence; it does not qualify object rendering.

## Previous continuation — Original game HUD

The user selected **original HUD → game sounds → music** on 2026-10-28, after
functional persistence and its menu/layout refinements. [Step 11](steps/step-11/step-11-recover-original-hud.md)
and [Task 01](steps/step-11/tasks/task-01-recover-hud-and-display-mode-ownership.md)
own the recovered player life bar, armour, hand/sword/rod, item capacity and
magic indicators. **Original HUD is the default**; **F1** selects original HUD
and **F2** selects the existing debug overlay. Display choice is process-local,
consumes both host key edges and remains independent of gameplay, original saves,
character rendering, object/equipment fallback shapes and diagnostic observation.

The [HUD recovery journal](../../journal/entries/original-hud-recovery-2026-10-28.md)
records original register/page contracts, indexed composition, the repaired live
visibility key queue, original-x86 fixtures, native switching/menu/persistence
checks, natural damage/potion outcomes and explicit indicator/visual limits.
Original legacy graphic/script/inventory leaves remain bypassed; the recovered
HUD uses immutable original assets and a fresh indexed presentation copy.

The HUD pass started from `22c36a3f70bef9467e62299376905cbb5552dd71` on
`linux-e2-reconstructed-runtime`; persistence is in `35be1cc`, and menu/layout
refinements are in `22c36a3`. Its historical
[handoff journal](../../journal/entries/original-hud-handoff-2026-10-28.md) records
this priority change and observed source entry points. Keep existing character,
menu/persistence and save-protection behavior intact. Historical tower/rendering
limits and closed investigation/replay/regression milestones remain as recorded.

## Previous continuation — Functional game save/load

The user has selected **game save/load** after accepting player/enemy recovery
and committing the subsequent gameplay repairs. Baseline **v0.2.0** is commit
`ae54e6f8e4dcb3570625c4780cfaf74ca252ecd1`; both version tags were pushed to
`origin`. [Step 10](steps/step-10/step-10-recover-game-save-load.md) owns the
implementation, bounded acceptance and remaining persistence limits.
[Task 01](steps/step-10/tasks/task-01-map-original-save-load-contracts.md) starts
with original callbacks, writer/reader contracts and safe writable path ownership.

The [save/load journal](../../journal/entries/game-save-load-recovery-2026-10-27.md)
records the recovered mixed-endian version-4 format, protected writable slot
storage, normal/ASan original-code fixtures, repeated actual menu Save/change/Load
and fresh-process restoration. Player/world fields, action ownership and sword
attachments restore; input, animation, camera crossing and attack interaction
resume. Installed save hashes remain intact; tests use private copies of free
slot 5. Nonempty timers have original-code fixture evidence; corrupt-file fatal
cleanup and arbitrary original progressions remain unqualified. HUD recovery now
precedes game sounds and music.

The user accepted functional persistence, then requested three menu refinements.
[Task 04](steps/step-10/tasks/task-04-refine-save-load-menu-presentation.md) and the
[refinement journal](../../journal/entries/save-load-menu-refinements-2026-10-27.md)
record exact saved-thumbnail pixels in both displayed menu buffers, unchanged
physical gameplay pages after cancelled previews, and automatic dismissal after
successful same/fresh-process Load. Fresh Debug/ASan evidence qualifies these
refinements; broader persistence/gameplay limits above remain.

The screenshot follow-up is verified within recorded bounds:
[Task 05](steps/step-10/tasks/task-05-recover-menu-layout-and-font.md) restores original
main/slot geometry, initial/repaint title alignment and mixed-case font, with a
160×120 preview display. Its [journal](../../journal/entries/menu-layout-and-font-2026-10-28.md)
records 28/28 focused Debug/ASan checks, protected saves, native layout assertions,
original edit-state/Save handoff repairs and a three-stage menu sweep with no
failures and explicit skips. Broader visual/gameplay limits remain; Step 11 HUD
recovery is the selected next work.

## Previous continuation — Tower actor eviction

The user accepts the preceding enemy-play/potion repairs and reaches the top of
the tower in a longer F5 session. The new failure occurs while loading
**264/key3**: the fixed node pool fills and eviction loses its selected actor
pointer. `FUN_0045282c` now retains that actor and recovers original attachment
recursion, list/table removal and error arguments. Root cleanup marks the
original **+2** free field and preserves its return pointer. No pool enlargement
or eviction bypass is added.

[Step 09 Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
and the [tower journal](../../journal/entries/tower-actor-eviction-crash-2026-10-27.md)
own this repair. Normal/ASan original-code comparisons each pass **163 cases**,
including actual allocation under full node-pool pressure. The captured Debug
route matches **1088 checkpoints**, correctly evicts **3030/trelim10**, then
strictly diverges from the recorded fatal requester. This is scoped recovery,
not full replay or further tower gameplay acceptance. Restart F5 after rebuilding.

## Previous continuation — Human crash and dropped potion

The user likes the recovered enemies and reports a short-play bitmap-disposal
crash plus a dropped yellow pickup that stays attached without healing.
[Step 09 Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md)
owns these gameplay repairs. The action index had accepted false headers inside
sound payload, redirecting animation **1256** to a sound resource. Indexing now
uses the actual version-55 action header and matches all **2000** original
`OFFSETS` entries. Representation-name interning/lookup now uses the original
**4000-byte** pool, restoring dropped `w_pot` **424** in script conditions instead
of the invalid token **0x8fff**. New representation slots receive original cache
clearing; existing slots remain intact.

The [follow-up journal](../../journal/entries/enemy-play-crash-and-dropped-potion-2026-10-27.md)
owns the captured reproduction, original instructions, fresh original-code/native
checks and explicit replay/fixture limits. This is a continuation of accepted
character rendering, not a restart of the closed investigation or suite milestones.

## Previous continuation — Original enemy bodies and animations

The user accepted the repaired player on 2026-10-27 (“perfection, works as a
charm”) and requested enemy animations next. Current order is **enemy animation
→ functional game save/load → game sounds → music**. Session saving, replay
and the gameplay regression suite are closed milestones with minor follow-ups
deferred.

[Step 08 Task 03](steps/step-08/tasks/task-03-activate-scene-backed-children.md)
owns this pass. F5 enables `E2R_NPC_MESH=1` alongside `E2R_PLAYER_MESH=1`.
Original character ellipsoids and full bone poses now use the player's recovered
camera, shading, depth and physical-page path. Character diagnostic shapes are
hidden; objects and equipment keep diagnostic rendering. The original scheduler,
actions, AI, damage and animation resources remain in control. NPC polygon/box
leaves and original HUD graphics remain bypassed.

Both original pedestal guards render articulated green bodies; ASan samples
**52/53 nodes and 12 distinct poses each**, from restrained/released frames through
movement and a five-second observation. A live attack route proves guard 284
inflicts actual damage **100 → 95** and exits normally through the menu. Workshop
captures also show smith 602's changing **56-node** body and final corpse. Broad
combat journeys retain failures (navigation, missed attack/death, bitmap pool and
another enemy landing the final blow); those are not passing kill regressions.
The [enemy journal](../../journal/entries/enemy-model-and-animation-2026-10-27.md)
owns commands, fresh validation and limits.

The accepted [player task](steps/step-08/tasks/task-02-recover-joe-geometry-and-rendering.md)
and [player journal](../../journal/entries/player-model-and-animation-2026-10-27.md)
retain the projection correction, original-x86 fixtures and earlier bounded
qualification. These remain separate from exhaustive enemy species/actions,
human enemy visual review and a full regression sweep with NPC bodies enabled.
Historical sections below retain their dated acceptance boundaries.

## Previous milestone — Door approach reliability regression

The user's full visible-Debug/two-worker run fails door approach and blocks
Debug stability on exactly the same sources and binaries as the earlier green
headless run. Full-suite reliability is **open**; the historical single-run pass
does not establish repeatability. The [reliability journal](../../journal/entries/regression-door-approach-reliability-2026-10-27.md)
owns the counterexample, scene-planned approach repair, required displaced-start
regression and qualification limits. Task 10 owns this test-driver correction;
recovered runtime and generator are unchanged.

A separate diagnostic setup variant also captures a bitmap-disposal fatal path
before door setup; its stopped evidence remains open. Passing navigation runs
do not repair or supersede that runtime counterexample.

The correction now has an old-code failing control, passing paced Debug/ASan
probes and a concurrent headless integration: **148 PASS / 57 optional SKIPPED**,
all **143 required**, zero failures/blocked checks, **1112.78 s**, exit **0**.
All **26** native journeys quit and complete inspection; **34** hashes and both
executables match. The new required distant-start case reaches its measured
precondition through real input before testing a fresh door. **113** contracts
pass. This is scoped door-driver acceptance; actual desktop SDL and broader
runtime reliability remain open. The journal retains every failed attempt.

## Previous evidence — Single invisible regression sweep

The authorized sequential **01–10** sweep and final integration are complete.
`full-final-07/` passes all **141 required** checks: **144 PASS / 59 optional
SKIPPED**, no failures or blocked checks, **1795.66 s**, exit **0**. All **24**
Debug/ASan native journeys quit normally and complete inspection. Every one of
**203** catalogue cases is owned once; all **34** source hashes, pinned/live
executables and JSON/JUnit results agree. SDL is dummy, one worker, recording off.
The [execution journal](../../journal/entries/headless-regression-sweep-2026-10-27.md)
owns exact identities, block subsets, failed attempts and acceptance limits.

Original-backed repairs restore live menu item storage, restart dispatch/word
identity, binary slot labels/previews, actual DirectDraw surfaces/callers,
terminal **0x16/0x17** actor ownership and bitmap-record return/pool/disposal
ownership. All reconstructed repairs are mirrored in the generator; exact
four-artifact parity passes. Normal/ASan fixtures include **3072** pose events,
**1152** root-pose cases and **14,208** bitmap-record cases per mode.

Input guidance now uses scene/actor planning, bounded clearance waits, original
pickup geometry, live smith tracking and original-melee kill attribution.
Receive-hit uses early eligible-encounter handoff and an outside-clearance front
point with tighter settling; actual surviving enemy damage stays mandatory.
Unarmed contact has its own compatible lifecycle. All **66 suite / 46 navigation
= 112** contracts pass. Existing staged/unstaged work is preserved; no commit/push.

Portable replay remains optional/unqualified because historical recordings reject
the SDL-dummy environment field under strict native validation. Broader rendering,
persistence/audio, shore exit, live water-enemy damage, final potion lifetime/cure,
guard-293 actual damage, longer stability and new human F5 acceptance remain open.
The extended unarmed-prefix door **−100** deactivation still has no captured
writer; route separation does not repair that runtime gap. Capturing that writer
is the next bounded diagnostic. The earlier screenshot freeze remains unconfirmed.

## Current continuation — Receive-hit strike alignment

The supplied next potion block stops ASan D's receive-hit setup while pursuing
a guard. Test navigation now approaches in front of the observed opponent and
lets original melee inflict the required damage. The eligible-opponent goal
allows audited guards **284/293**, requiring same-floor attack capability and
identity, with bounded reselection when an opponent disappears. Explicit fixed
targets and actual melee attribution remain required. All **99** contracts pass.
The [contact-navigation journal](../../journal/entries/receive-hit-contact-navigation-2026-10-26.md)
owns native results and retained attempts. Reconstructed runtime, generator and
normal F5 behavior are unchanged; the earlier screenshot freeze remains unconfirmed.
Final visible-Debug/headless-ASan potion qualification passes **26 results / 6
optional skips**, all **22 required** checks, ten native menu exits and completed
inspection in **317.58 s**. Receive-hit after movement passes **8/8** in **57.01 s**,
including an actual displaced Debug scene-floor join. Both runs match all **21**
source hashes; the journal records unexercised guard-293/reselection limits.


## Previous continuation — Regression 08 freeze investigation

The user confirms stopping the suite after the in-game freeze; its later
`SIGKILL` is not evidence of an OOM kill. New diagnostic runs capture a separate
event-7 `FUN_0042f85c` crash from an uninitialized node. Original instructions
now drive its explicit dispatcher/node, pose, resource and action contracts,
mirrored in the generator. **6144** additional original-x86 cases pass in
normal/ASan fixtures; regeneration has exact parity. Agent probes now retain
bounded stacks for signals/allocation exceptions and capture before stalled
process cleanup. All **91** suite/navigation contracts pass. The
[freeze investigation](../../journal/entries/regression-08-freeze-and-event-callback-2026-10-26.md)
owns new native qualification, identities and retained failures. The screenshot
freeze's root cause remains unconfirmed; this callback repair does not by itself
establish that cause.
The full visible-Debug/headless-ASan potion block passes **27 results / 5 optional
skips**, all **22 required** checks, with ten clean native exits and complete
inspection in **343.22 s**. A final diagnostic-output cleanup also passes native
GDB fixtures and fresh startup/menu lifecycles in both builds (**4/4**).

## Previous continuation — Natural potion consumption

Potion trials now accept their naturally selected effect, including a valid
no-op; all four random-branch summaries are optional. Required checks retain
drinking, reciprocal attachment, bottle removal and actual health/action/timer
assertions. The supplied lingering-bottle failure restores the three original
animation-name repair hunks already emitted by the generator, resolving the
previous source/generator drift. All **1,800** original-x86 name comparisons pass
in normal/ASan fixtures and all four generated artifacts match. Potion traversal
after real damage shares the navigator's height-compatible workshop join.
The [potion-consumption journal](../../journal/entries/natural-potion-consumption-2026-10-26.md)
owns native qualification, source identities, failed attempts and remaining
effect-lifetime limits. Headless Debug/ASan qualification passes **27 results**,
with **5 optional skips**, no failures/blocked checks, ten clean native exits
and complete inspection. All **89** suite/navigation contracts pass. The full
visible Debug block retains a startup/input interruption; the farther scene
join is planned and contract-tested but not exercised by final native runs.

## Previous continuation — Scene-planned water objectives

Swimming now uses the shared navigator with read-only live scene-floor planning,
replacing the archived human water corridor. Required checkpoints cover unarmed
and sword-equipped entry, four original swimming combat directions and a
camera-crossing return journey, with real mode/displacement/equipment assertions.
**84** suite/navigation contracts pass. The
[water-goal journal](../../journal/entries/water-goals-and-scene-navigation-2026-10-26.md)
owns current native qualification, source/asset identities and retained failures.
Headless and visible-Debug full-block selections pass **22 required checks**
with **2** optional shore-exit skips; focused visible displaced-pedestal
entry/traversal passes **5/5**. All nine final processes quit natively and complete
inspection.
The catalogue now has **195** logical cases / **22** full shared gameplay
processes. Runtime/generator/F5 and population policy are unchanged; shore exit,
live-water-enemy damage and the full-suite run remain open.

## Previous continuation — Swimming route approach

The user's visible Debug water route stalls after movement leaves Joe west of
the recorded pedestal anchor. Swimming now follows that anchor and the full
height-aware route through the bounded navigator, with an explicit final
water-entry height interval and tighter final dry-bank corner. Actual camera
**543**, representation **13** and swimming displacement remain required.
Headless and visible-Debug selections pass all **8 required checks** in both
builds, with **2** unchanged optional armed/shore skips and clean native
Quit/inspection. The [swimming-route journal](../../journal/entries/swimming-route-navigation-2026-10-26.md)
owns current visible qualification, source/binary identities and retained failures.
All **72** suite/navigation contracts pass. Runtime/generator/population/F5
behavior is unchanged; the full suite and wider water interactions remain open.

## Current continuation — Workshop door passage

The user's workshop block passes destruction of door **980** in both builds but
fails passage: a fixed forward hold leaves the opening as recovered movement
changes heading. Test navigation now aligns and steers through a required gate,
then verifies actual released displacement beyond the destroyed door on its
floor. Headless Debug/ASan pass **16/16** workshop checks with native Quit and
complete inspection. [Door-passage evidence](../../journal/entries/workshop-door-passage-navigation-2026-10-26.md)
records the visible Debug startup `FUN_0042f85c` crash and BLOCKED door
acceptance; ASan again passes. It owns identities and limits. All **67** suite/navigation
contracts pass. Runtime/generator/F5 behavior is unchanged; this is guidance for
one verified opening, with broader door/progression planning still open.

## Current continuation — Goal-driven regression navigator

[Step 09 Task 10](steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md)
implements bounded state-aware test navigation for receive-hit setup, workshop
routes, fixed unarmed contact and sword approach. Live Debug/ASan guard-284 hits
now prove Joe health **100→95**, original melee attribution and native clean exit.
Final Regression **05** passes **14/14** in **137.77 s**, four gameplay processes;
fixed smith damage is **100→80** in both builds. Controlled pickup reuse passes
**10/10**. All **62** runner/navigation contracts pass.
The [navigator journal](../../journal/entries/goal-driven-navigation-2026-10-26.md)
records current qualification, failed development attempts and live-navigation
limits. Unknown blockers remain unknown; broader pathfinding and automatic
progression interactions are not accepted. Task 09 owns recovered runtime
behavior; this continuation changes test tooling, with **185** catalogue cases
and the same **20** planned full gameplay processes. Existing runtime faults and
source/generator drift remain untouched; the full suite is not rerun.

## Current regression fixture — 2026-10-26

The [current population task](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md#current-continuation--controlled-opening-test-population)
now distinguishes controlled opening journeys from live population/combat.
Noncombat tests prevent original guard/smith and terrain creation; normal F5 and
combat retain live actors. Controlled movement/pickup/menu examples pass in
Debug/ASan, while live ASan approach failure and interrupted visible-input evidence
remain red. Shared movement uses **2** processes / **60.96 s**, versus **6** /
**102.21 s** isolated. Normal logo waits are restored; automated tests present
and tap each actual logo separately. The
[population/logo journal](../../journal/entries/noncombat-population-and-logos-2026-10-26.md)
records **46** passing contracts, source/fixture evidence, new **184**-case
catalogue and the unrerun full-suite / preserved generator-drift limits.

## Bare Terminal Baseline

The 2026-09-14 audit rebuilt commit `43ddc8a`; the same-day Step 07 continuations restored generator parity, repaired recursive actor ownership, and reran the corrected wrapper, matrix, and SDL packet. See the [audit evidence and commands](../../journal/entries/runtime-audit-2026-09-14.md). The earlier [Linux reconstruction implementation](../linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) remains a historical milestone record.

| Area | Verified state | Limit |
| --- | --- | --- |
| Builds | X11/SDL Debug and ASan compile | Runtime remains Linux/i386 with fixed-address assumptions |
| Controls | All four arrow rows pass in debug and ASan (8/8) | Checks establish input-state latches, not actor motion or visible gameplay |
| Intro route | First-intro Space enters `Start_sc`; completion reaches action-error requester 0x2e | OK resumes updates at camera 87; original reference instead shows release/HUD in the pedestal courtyard; actor/query inputs remain unresolved |
| Presentation | Action error visible over camera 175; selected surface `c2a56a11`, cue-enabled SDL present/window `fd124785` / `ef9e0785` | Static actor position; hosted dialog typography remains rough |
| Joe | Actor 0 has render rep 67 and a render tree | `model=0xffffffff`, root update list empty, draw vertices zero |
| Scene children | Camera and script-resource namespaces distinguished; Start_sc resource 0 traced | Original video confirms two green creatures; their resource identities/activation remain unresolved; 319/322/318 belonged to an unproven lookup |
| Regression wrapper | Debug/early ASan canonical-Up latches and long-delay ASan error-modal checks pass; arrow matrix 8/8 | State/surface checks do not prove actor motion; separate SDL test covers OK and Escape menu entry |
| Generator | Syntax and all four artifact comparisons pass, including polygon/lighting/copy mirrors | Scoped repairs reproduce; broader helper inputs and behavior remain incomplete |
| Audio/save | Original-format gameplay serialization and menu restoration; audio compatibility stubs | Repeated same/fresh-process Debug/ASan loading passes within Step 10’s bounds; malformed-file recovery remains unqualified; MIDI/audio remain silent |

SDL 3.4.12 is vendored in `dep/SDL`. The host backend presents 640x480 frames centered in the 640x640 window and owns window/input/presentation services. X11 remains the default backend; VS Code offers one `Ecstatica Recompiled` launch following the selected CMake preset; select SDL/i386 Debug for everyday use. The September audit used dummy SDL; subsequent manual evidence is recorded below. F5 now supplies the cylinder/action/proxy flags and differs from this bare terminal baseline. Its current Debug result and ASan limits are recorded in Step 09 and the F5 journal.

The 2026-10-14 [documentation review](../../journal/entries/documentation-review-2026-10-14.md) checked the latest commit `4fb151a` against source and setup. Generator syntax, four-artifact scratch parity, and polygon/lighting original-x86 comparisons pass again, normally and under ASan. Full-runtime checks and manual F5 were not repeated in that initial review. The subsequent Task 11 continuation rebuilds all four Debug configurations and reruns the wrapper, eight arrow rows and both SDL requester checks successfully; manual F5, living actors and gameplay remain unproven.

## Step Roadmap

Step numbers are stable identifiers, not execution order. Player/enemy recovery
has user acceptance with recorded fidelity limits. Save/load and HUD are
implemented within their recorded bounds. The next order is
**12 object models/animations → game sounds → music**. Step 09's accepted diagnostic
gameplay and the completed regression tools supply verification; their minor
gaps remain tracked. Steps 01/02/07 and Step 03 Tasks 01/02 retain their bounded
historical completions.

| Step | Status | Outcome / dependency |
| --- | --- | --- |
| [01 — Interactive SDL stability](steps/step-01/step-01-stabilize-interactive-sdl-f5-runtime.md) | completed | Historical bounded startup/F5 investigation |
| [02 — DirectDraw page and palette semantics](steps/step-02/step-02-recover-directdraw-page-and-palette-semantics.md) | completed | Recovered front source, palette, aspect-fit presentation |
| [07 — Restore reproducible baseline](steps/step-07/step-07-restore-reproducible-runtime-baseline.md) | completed | Automated checks pass; manual screenshot/log confirms scene-175 baseline |
| [09 — Diagnostic gameplay with cylinders](steps/step-09/step-09-enable-diagnostic-gameplay.md) | follow-ups retained | Accepted gameplay milestone and subsequent crash repairs support persistence; broader gameplay limits remain recorded |
| [08 — Recover scene-175 actors](steps/step-08/step-08-recover-scene-175-actors.md) | follow-ups retained | Player/enemy body and animation direction accepted; exhaustive animation, equipment and other rendering remain separate |
| [10 — Functional game save/load](steps/step-10/step-10-recover-game-save-load.md) | implemented within recorded bounds | Original writer/reader/menu recovery, repeated same-process and fresh-process restoration; corrupt-file recovery and broad progression remain limited |
| [11 — Original HUD](steps/step-11/step-11-recover-original-hud.md) | implemented within recorded bounds | Original-default/F1/F2 presentation, original-code/raster and bounded native evidence; unexercised indicators remain recorded |
| [12 — Object models and animations](steps/step-12/step-12-recover-object-models-and-animations.md) | active; first slice verified | Eight original item/weapon/door/pool assets; source map, flat/box recovery and Debug/ASan evidence; Task 02 retains variants and natural pool lifecycle before audio |
| [03 — Gameplay control and camera proofs](steps/step-03/step-03-expand-gameplay-control-and-camera-proofs.md) | partially deferred | Input mapping/matrix complete; basic locomotion/camera proofs join 09, broader controls follow readiness |
| [04 — Timing and frame pacing](steps/step-04/step-04-define-runtime-timing-and-frame-pacing.md) | planned | Recover game timing ownership after visible control proofs |
| [05 — DirectSound compatibility](steps/step-05/step-05-begin-directsound-compatibility.md) | planned | Map sound calls before implementing an audio boundary |
| [06 — Developer runtime packaging](steps/step-06/step-06-package-reproducible-developer-runtime.md) | planned | Consolidate existing setup docs, add unified validation, define release gate |

## Earlier gameplay frontier — historical evidence

The [recorded courtyard route](../../journal/entries/recorded-courtyard-route-2026-10-26.md)
replaces Regression **04**'s guessed crossing with the user's pedestal/central
courtyard round trip. Startup, movement and traversal pass **8/8** in **69.68 s**,
one shared Debug and one shared ASan process. Both central camera **125** / floor
**4096** and return **175** / **3328** are asserted. A bounded input detour handles
an observed guard at the return stairs; source timing alone cannot reproduce
fresh population. No runtime C/generator or game-state restoration is involved.
The owning task and journal retain development failures and acceptance limits.

The [menu/parallel continuation](../../journal/entries/menu-stages-and-parallel-suite-2026-10-25.md)
expands the suite to **182** logical cases and **20** shared gameplay processes
versus **96** isolated scenarios. Debug/ASan run concurrently by default, with
headless, either visible configuration or both windows; each build's journeys
remain sequential. The old six-case menu selection passes in **26.19 seconds**
versus the user's **53.04** sequential result. Three-stage menu coverage exposes
stale option labels, pedestal restart failure, Debug gameplay Start Game SIGSEGV
and an ASan intro Load stack-buffer overflow. These failures remain open and
preserve earlier checkpoint passes; audio, resolution and functional save/load
retain explicit per-stage skips. The owning task records evidence and limits.

The earlier [shared-journey suite continuation](../../journal/entries/shared-gameplay-journeys-2026-10-24.md)
retained **86** logical cases while planning **18** fresh gameplay processes
instead of **42**, with individual checkpoint results and shared evidence.
Debug/ASan workshop chains pass eight logical checks in one process each;
a larger Debug chain times out during workshop traversal after preserving its
startup/movement/unarmed passes. Repeated retention `std::bad_alloc` reports
survive without abort, but allocation pressure and the stalled update remain
unexplained. Full combined-route acceptance is open. The owning task records
results and limits; isolated diagnostic execution remains available.

The [visible-block/unarmed continuation](../../journal/entries/suite-visible-unarmed-and-retention-abort-2026-10-24.md)
adds sequential SDL watching and prerequisite-aware suite launches. Unarmed
attack/contact cases are independent of sword pickup. Session-retention error
reporting now survives repeated allocation and reporter failure in i386
Debug/ASan contracts; the allocation failure preceding the reported abort remains
unexplained. Broader gameplay stability and the earlier ASan event fault remain
open.

The [automated gameplay suite](../../gameplay-tests.md) now exercises recovered
capabilities in shared, input-only journeys. Its separate full-suite
launch runs Debug/ASan and reports failed prerequisites as blocked checkpoints,
with explicit unfinished/random coverage skips. The
[suite journal](../../journal/entries/gameplay-regression-suite-2026-10-24.md)
records current results and distinguishes route qualification from runtime
regressions. That initial suite preserved a failing animation-name drift;
the current potion continuation restores it with original-code comparison and
complete generated parity. Historical success alone is not current acceptance.

The [extended-gameplay crash investigation](../../journal/entries/alternate-target-crash-2026-10-24.md)
now takes priority over the earlier stability deferral. Original EAX actor and
X/Z angle contracts repair `FUN_0042e684`, with normal/ASan original-code
comparisons. Isolated generated Debug/ASan builds match all **204** checkpoints
and return from the exact former fault at sequence **2,260,310,849**, then report
**75/INCOMPLETE** at the recorded boundary. Complete replay and extended gameplay
acceptance remain open. The animation-name regression committed in **e2c4acd**
is preserved and independently fails its existing fixture; normal current-source
replays diverge at checkpoint **155**. Generator delta parity passes with exactly
that pre-existing drift retained. Task 09 and the linked journal distinguish the
ordinary builds from isolated generated acceptance. Wider interaction coverage
and original rendering remain later work.

The [random-outcome review](../../journal/entries/random-potion-outcomes-2026-10-24.md)
confirms all **135** exact checkpoints of the user's no-effect recording. It
selects `ken:potmagic`: without an existing poison/invisibility timer, drinking
and bottle removal complete while health stays **85**. The selector also contains
healing, poison and invisibility branches. Fresh inputs sample new outcomes;
exact replay preserves the recorded RNG. Fresh routes confirm poison onset
(including Joe health **85**) and invisibility dispatch/cleanup. Two fresh healing
selections now execute `gethealth` and restore naturally damaged Joe **85→100**,
with bottle removal and continued control. All four branches appear across **17**
successful fresh pickups. Final effect lifetime/cure checks remain open. Wider
work stays deferred.

The [health/status continuation](../../journal/entries/diagnostic-health-and-potion-status-2026-10-24.md)
confirms bottle removal followed by sword use in human session
**20261024_152305_822**. Its health falls from **100 to 70** before drinking;
the omitted original HUD prevented the user from observing this. The diagnostic
view now shows large health text and poison/invisibility indicators derived
from Joe's current action and timers. Read-only/modal/offscreen fixtures pass
normally/ASan, all four configurations build, and fresh Debug/ASan potion routes
verify the display. Next is healing from damage and potion lifetime/cure checks.
The user explicitly defers wider pickups, extended stability and original
rendering work. The following entries retain their historical acceptance limits.

The [bottle-removal continuation](../../journal/entries/consumed-potion-removal-2026-10-24.md)
confirms simultaneous bottle/sword attachments in the new human recording,
matching all **549** replay checkpoints. Animation-name helpers now use the
original **17,500-byte** pool instead of **4,375**, restoring the potion's
`glofade` → `potvan` → `ken:RemoveActor` chain. Fresh Debug/ASan input routes
remove the bottle, then collect the sword, execute four-direction attacks and
move with the bottle still gone. All 1,800 original animation-name comparisons,
actor/script-name fixtures, four builds, generator parity and baselines pass.
Manual F5 repetition, healing from damage and other effects/items remain open.

The [workshop potion review](../../journal/entries/workshop-random-potion-and-timers-2026-10-24.md)
confirms the new human pickup and clean exit through **742** exact replay
checkpoints. Actor **537**/`fakepot2` is a random-effect potion; this recording
selects the original poison branch. Three recovered contracts repair delayed
argument passing, timer pool allocation and signed deadline dispatch. Fresh
Debug/ASan input routes now start poison action **409** and remove its timer,
leaving the original future death timer queued. Original-code comparisons,
four builds and marker checks pass. Healing from below full health, eventual
poison death/cure/fade remain open. The bottle attachment persisted in that
earlier snapshot; the continuation above restores its cleanup. See the journals
for binary identities and acceptance limits.

The [longer-playthrough review](../../journal/entries/long-play-cache-reclamation-and-markers-2026-10-24.md)
verifies four enemy deaths, two door destructions and sword attachment. The
reported Escape freeze is reproduced before Escape reaches the input pump:
animation-cache reclamation drops the selected action and fails to release its
keyframe/event records. Original selected-resource and disposal contracts are
restored. Final Debug replay passes the stalled load and all **469** checkpoints,
then correctly ends at the incomplete recording boundary.

Host diagnostics now use distinct shapes/colors and original-name labels for
creatures, corpses, doors, debris, potions, weapons, items and props. Dimensions
remain illustrative; collision behavior is unchanged. Active menus suppress the
overlay. Fresh Debug/ASan input routes complete sword pickup, door destruction
and passage, Escape cancellation, reopened Quit and actual Yes confirmation,
with normal process exit. Original comparisons, four builds, parity and runtime
regressions pass. The long ASan replay is incomplete at 180 seconds/checkpoint **308** with Joe alive and no sanitizer report; the late cache boundary is established by Debug replay and original-code/ASan fixtures.

The [marker follow-up](../../journal/entries/long-play-cache-reclamation-and-markers-2026-10-24.md#follow-up-door-marker-placement-and-creature-direction)
restores living creatures' projected local +Z lines and places intact door slabs
using their original first model node's offset, dimensions and rotation. This
corrects the centred slab's axis and hinge placement in the workshop. Debug/ASan
marker fixtures and four builds pass; fresh bounded workshop evidence is in the
same journal. Markers remain host diagnostics rather than collision authority.

The earlier workshop Space attempts did not collect the bottle. The new run
above confirms pickup and identifies `ken:fakepot` as randomized effect dispatch;
the previous interpretation as a prop is superseded. Human F5 repetition,
healing from damage and other potion effects are next, alongside wider
combat/items, original meshes, armed swimming and prior ASan courtyard
steering/floor-return limits.

Prior door recovery:

The [workshop door continuation](../../journal/entries/workshop-door-hit-callback-2026-10-24.md)
confirms human sword swings and the smith's death, then reproduces the left-door
hit crash at checkpoint **125**. Original selected attack/hit script records are
now passed to the interpreter with the correct owner/target/child and cleared
node. Normal/ASan original-code comparisons and generator parity pass. Fresh
Debug/ASan SDL routes reduce door **980** to health **−20**, finish collapse and
deactivation, then walk through its opening into camera **164**, with Joe health
**100**, state **4** and no modal or sanitizer report. Four builds and runtime
regressions pass. Next is human F5 door-collapse/passage repetition, followed by
another bounded interaction if exploration exposes one. Other objects, area
attacks, wider combat and original meshes remain unaccepted. Prior ASan courtyard
steering/floor-return limits remain open.

Prior attack recovery:

The [sword attack and attached-position continuation](../../journal/entries/sword-attacks-and-attached-position-2026-10-24.md)
confirms the user's F5 pickup, then exactly reproduces the Ctrl/arrow crash at
checkpoint **91**. Original attack-query actor/XZ and preserved direction inputs,
attached-render owner/actor identities and the pose work-list counter are restored.
Cylinder mode retains the held item's original pose chain. Fresh Debug/ASan SDL
routes start all four requested attack directions, release and move with health
**100**, state **4**, equipped representation **9**, no modal, and the sword's
world position following Joe. Builds, original comparisons and baselines pass.
Debug's populated courtyard return passes; ASan steering attempts miss the
outward-camera or return-floor assertion with Joe alive and no sanitizer error. The newer door continuation above supplies human swing/death evidence and a
source-backed door contact/damage interaction.
Full combat, weapon meshes and broader gameplay remain separate acceptance.


The [water replay and sword pickup continuation](../../journal/entries/water-replay-and-sword-pickup-2026-10-24.md)
confirms the user's swimming session through all **565 exact replay checkpoints**
and ordinary workshop re-entry through camera 347. The later Space crash is
reproduced and the original pickup actor/polar, first-model origin, attachment
event and Space-release contracts are restored. Fresh SDL Debug/ASan keyboard
routes acquire sword actor **3717**, select equipped kind **3** / representation
**9**, and retain movement with health **100**, state **4**, and no modal. Original
comparisons, populated courtyard returns, builds and baselines passed for that
slice. The newer report above confirms ordinary pickup; combat,
shore exit, armed swimming and general interaction remain separate acceptance.


The [early-skip startup repair](../../journal/entries/pedestal-intro-restart-2026-10-24.md)
exactly reproduces the user's pedestal-to-horseback restart and later death/menu
through all 1,810 replay checkpoints. Original actor-name capacity and 108 complete
startup literals restore the skip script's nine cleanup references. Fresh
Debug/ASan early skips, including the recorded 83/495 timing, complete the
pedestal scene and populated courtyard return; 60-second released-input checks
also pass. Natural-startup water/swimming regressions pass in both builds.
The complete 83/495 skip-to-water route passes in Debug; its ASan counterpart
times out before water with health 100 and remains incomplete.
The newer human sessions above confirm resumed traversal and swimming after
this startup repair. The repaired executable correctly diverges from the
old recording after cleanup changes; broader floor-return/full-gameplay limits
remain separate.

The [water-entry continuation](../../journal/entries/water-entry-and-player-resource-2026-10-23.md)
reproduces the user's death/menu in complete exact replay. Gameplay now loads
Joe's original resource instead of potion actor `fpot6`, reads live swimming
flags and restores the packed reload-state write. Fresh Debug/ASan SDL routes
reach camera 543, finish the original transition and swim forward at height
5120 with health 100, state 4 and wait/modal zero. The newer exact human replay
above confirms water entry/swimming; shore exit and held-weapon swimming remain
separate acceptance. Task 09 still
owns broader population/object interactions and workshop sword pickup.

The [camera-722 requester investigation](../../journal/entries/blank-requester-and-large-replay-2026-10-23.md)
recovers the original eight-direction reaction table after large-capture replay
exposes an earlier native fault. The user repeated the route without the blank
prompt; requester fallback/evidence and reader/logging improvements are verified
within their recorded limits. The old capture diverges after the table repair,
so its terminating caller is not claimed reproduced or identified.

Developer tooling is available through the [debugging tools implementation](../debugging-tools/debugging-tools.md)
and [usage guide](../../debugging.md): opt-in state/frame observations, native bug
bundles, original-code fixture support, reverse-debugging launchers, recorded-route
assertions and recovery/diagnostic queries. This tooling preserves the gameplay
frontier and replay acceptance distinctions below.

The [post-pedestal callback continuation](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md#callback-contract) exactly reproduces the user's new script-deactivation crash and restores its original code/actor/node contract. Debug/ASan natural intros plus 60-second idle checks pass; compatible replay returns from the formerly faulting callbacks before reporting incomplete-prefix exhaustion. An additional populated Debug traversal fails its floor-return check; the ASan round trip passes. Workshop re-entry, sword pickup and full experimental ASan acceptance remain separate under Step 09 / Task 09.

At Step 07 completion, all automated baseline checks passed. Tasks 03–06 repaired recursive actor corruption, default-action context, action-advance inputs, and motion-query ownership. The long-delay ASan probe dispatches Space/Up and captures a nonblank scene-87 surface (`bf4a8e25`) without sanitizer errors. The then-current default SDL skip route captured scene 175 with the recorded static hashes. Task 09 below supersedes that capture after making the blocking dialog visible. The user’s crash-free F5 report and subsequent screenshot/log confirm the static scene-175 final image, completing [Task 02’s manual check](steps/step-07/tasks/task-02-repair-canonical-control-regressions.md) and Step 07. Original scene-selection fidelity and living actors remain Step 08 work.

[Step 08 Task 01](steps/step-08/tasks/task-01-recover-action-context.md) now restores the current actor across action parsing, preserves the action slot across helpers, and supplies Joe to child updates. GDB verifies action 384 at `0xac263c`, Joe `0xaa6bd8`, slot `0xaa6c7e`, and progress 0 → 1638 with context restored. Generator parity, three builds, the default wrapper, all 8 arrow rows, and the default SDL packet pass again.

[Task 04](steps/step-08/tasks/task-04-recover-missing-scene-message-inputs.md) now supplies a live `["Can't find scene", "mtorc4", NULL]` list and eliminates the missing-scene ASan lifetime error. GDB confirms scene 40 has resource pointer 0 and archive offset -1. At Task 04 completion, both gated SDL and ASan checks exited 5 waiting for scene 175; the recovered list reaches requester code, whose visible message rendering/dismissal is not validated.

[Task 05](steps/step-08/tasks/task-05-recover-post-intro-scene-selection.md) traced corrupt coordinate events to aliased keyframe allocation. [Task 06](steps/step-08/tasks/task-06-recover-scene-activation-pose-inputs.md) now supplies the pose actor/state and real output destinations. The projection continuation also repaired two matrix destinations that corrupted a scene child head and a node attachment; [Task 08](steps/step-08/tasks/task-08-recover-packed-event-metadata.md) restored packed dispatch metadata under the action-index gate. Task 02’s 2026-09-21 continuation restores polygon/mode/reference arguments, quad dispatch and temporary record storage, with generator mirrors. The original-x86 comparison passes 576 routing cases plus twelve temporary-record checks, normally and under ASan. Task 10 subsequently recovers the flat-lighting normal, angle and rotation contract plus mapped byte color reads. Its original-x86 comparisons pass 10,240 angles, 16,384 rotations and 8,192 lighting-index cases normally and under ASan. Gated SDL returns from lighting with a degenerate normal, then stops in framebuffer copying at `FUN_00418514`; this does not prove valid geometry. That checkpoint led to [Task 11 rectangle-copy inputs](steps/step-08/tasks/task-11-recover-dirty-rectangle-copy-inputs.md); its later result is recorded below within [Task 02 geometry](steps/step-08/tasks/task-02-recover-joe-geometry-and-rendering.md). Gated SDL ASan instead times out in camera 1073 without reaching geometry. Four builds, parity, default wrapper, eight arrow rows and both SDL requester checks pass; see the [lighting evidence](../../journal/entries/polygon-lighting-2026-09-21.md). The gate remains off by default.

[Task 07](steps/step-08/tasks/task-07-project-actor-cues-into-scene.md) replaces the inset with read-only scene-projected crosses/uprights (`E2R_ACTOR_CUES=1`). Recovered trigonometry, rotations, vector transforms and perspective are checked against original machine code. Default Joe's stored position is behind the pedestal camera (depth -3062), so the settled cue reports **0 VISIBLE / 1 BEHIND**; enemies remain absent. A synthetic drawing fixture verifies the primitives, not actual character placement. The supplied 35-second recording confirms grid replacement and bounded default-route survival, completing the cue check. It does not establish character placement. See the [2026-09-15 journal](../../journal/entries/actor-cues-and-projection-2026-09-15.md) for exact tests and remaining limitations.

[Task 09](steps/step-08/tasks/task-09-recover-post-intro-action-error-requester.md) diagnoses the video’s apparent freeze: `Start_sc` completes at 1102/1102, then missing action 384 (`dav:heropick`) opens an invisible modal. The repair restores its live message list, mapped record/text/items and OK routing. SDL Debug and ASan capture the visible error, dismiss it, resume a game update at camera 87, and verify Escape enters the main menu. The revised wrapper retains early ASan input-latch coverage and explicitly checks the later modal. The 2026-09-21 manual result confirms dialog presentation and advancement to camera 87 after OK, with the error still visible and Joe absent. Manual Escape confirmation remains pending; see the [requester journal](../../journal/entries/post-intro-requester-2026-09-15.md).

[Task 11](steps/step-08/tasks/task-11-recover-dirty-rectangle-copy-inputs.md) now supplies surface/X/Y/width/height across four callers, preserves opposite-page selection and recovers mapped lock-descriptor/unlock ownership. Original-x86 comparisons pass 2,048 copy/ownership cases and 256 dirty-list dispatch cases normally and under ASan. Four builds, generator parity, the default wrapper, eight arrow rows and both requester checks pass. Gated Debug still stops in `FUN_00418514`, now because compatibility DirectDraw Lock returns destination base/pitch **0/0**; its vtable slot is a generic no-op. [Task 12](steps/step-08/tasks/task-12-recover-directdraw-surface-lock.md) owns this provider failure. Gated SDL ASan exits 5 in camera 1073 without reaching the copy. Full-route and living-actor acceptance remain open; see the [rectangle evidence](../../journal/entries/rectangle-copy-2026-10-14.md).

Keep action indexing/expanded scripts opt-in during recovery; the single F5 configuration now opts in together with cylinders and mesh/HUD omission. Bare baseline actions remain unavailable, so dismissing its error cannot prove gameplay. [Step 09](steps/step-09/step-09-enable-diagnostic-gameplay.md) and [Task 01](steps/step-09/tasks/task-01-recover-action-event-node-removal.md) recover node removal plus required action/script inputs. Continuous Debug execution shows Joe on the pedestal without the action-384 modal and reaches opcode `0x75`, wait 0/modal 0. The [floor-decoder continuation](../../journal/entries/courtyard-floor-decoder-2026-10-14.md) restores high-address hosted byte reads with bounded original-x86 comparisons, removing the forest fallback. It also recovers NPC spawn query/range/placement inputs; full activation/loading remains open. F5 adds `E2R_DEFER_BACKGROUND_SPAWNS=1`, with on-screen status, to keep the first prototype focused on Joe. Existing actors/scripts and player queries remain active. Continuous Debug keeps Joe `9988,3328,-17408` visible in camera 175 after wait zero, but Up produces no displacement. The [2026-10-16 root-pose repair](../../journal/entries/terminal-root-pose-2026-10-16.md) fixes the watched terminal event-link writer. Debug/ASan execute matching 30-event chains and retain representation 67 at `+0x11e`, but Up/Left press/release still leaves Joe immobile. Full experimental ASan runtime acceptance remains open. [Task 02](steps/step-09/tasks/task-02-recover-post-intro-placement-and-motion-queries.md) owns motion/control and required event recovery; [Task 04](steps/step-09/tasks/task-04-recover-npc-spawn-query-inputs.md) records implemented spawn contracts and deferred full activation. Decoder/spawn fixtures, four builds, generator parity and default wrapper/SDL modal regressions pass; runtime playability remains open. Original DirectDraw Lock remains Step 08 Task 12; other rendering/copies remain active. No gameplay/traversal acceptance is claimed.

The [player-input continuation](../../journal/entries/player-motion-inputs-2026-10-16.md) supersedes the retained-representation frontier: Joe receives representation 12, and live keyboard reads remove a false modifier action. Debug/ASan now reach movement event `0x13` after Up, then fail in `0x4272a8` through the world-motion query. [Step 09 Task 05](steps/step-09/tasks/task-05-recover-player-motion-vector-ownership.md) owns explicit actor/vector/output inputs. New original-code comparisons and final baseline checks pass; movement/traversal and full experimental ASan remain open.

The [motion-query continuation](../../journal/entries/player-motion-query-2026-10-16.md) supersedes that first-query failure. Task 05 recovers event/vector/output ownership with original-code comparisons. A corrected Debug probe demonstrates Up displacement, Left/Right turning and release stopping; Down displacement remains unproven. ASan reaches Up, then a watched gravity write changes height to -16000 after release. [Step 09 Task 06](steps/step-09/tasks/task-06-recover-release-gravity-query-ownership.md) owns that first producer before subsequent fallback/action teardown. Full experimental ASan, real-map collision/traversal and 60-second acceptance remain open; baseline regressions and four-artifact parity pass.

The [2026-10-19 idle-action continuation](../../journal/entries/player-idle-action-2026-10-19.md) resolves that observed height failure at its upstream caller. The queued action ID comes from actor +0x162; passing the representation pointer instead loaded an unrelated FAN and replaced Joe's floor cell. Both Debug/ASan arrow probes and four combined turn/Up probes now retain height 3328/camera 175. Up release has further queued-action displacement, so stopping acceptance must be re-established. Task 02 retains settled stopping, Down, collision, traversal and sustained-time proof; full experimental ASan acceptance remains open. The new original-code caller fixture, four builds, generator parity and baseline checks pass.

The [manual spinning/input continuation](../../journal/entries/player-release-and-spin-2026-10-19.md) repairs actual SDL key-up table selection, restores the original frame-clock wait and recovers the target-facing crash's actor/time/range/angle inputs. Original-code/bridge fixtures and actual SDL Debug/ASan replays pass; releasing turn keys settles facing at rest and longer Down presses displace. Motion queries still steer during Up/Down with turn keys clear, so straight controls and the circling report remain open alongside collision/traversal and full experimental ASan acceptance. Final four builds, generator parity and baseline checks pass.


The [courtyard-camera continuation](../../journal/entries/courtyard-camera-traversal-2026-10-19.md) removes an unsupported camera-slot-to-script-resource activation, recovers the cached camera hint and supplies the terrain trigger's code/actor inputs. [Step 09 Task 08](steps/step-09/tasks/task-08-recover-courtyard-camera-transitions.md) completes bounded actual-SDL **175 → 166 → 175** traversal in Debug and ASan, with Joe retained, wait/modal zero and all keys released. Debug also reaches 167. ASan follows a different route, so identical steering, exact retracing, complete collision behavior and sustained/full experimental ASan acceptance remain open. Original-code fixtures, all four builds, generator parity and baseline regressions pass; the user now confirms practical input and prioritizes further exploration.

The [live steering audit](../../journal/entries/courtyard-steering-audit-2026-10-19.md) verifies 128 captured steering outcomes and 896 real floor responses against original code normally/ASan. Different time/vector inputs precede different Debug/ASan paths; no steering change is warranted for that first-turn family. Both builds pass a camera round trip followed by 60 seconds with released keys and stable Joe state. Reusable capture/replay and saved cases now support further investigation. Task 02 retains physical collision assertions, wider active exploration and full experimental ASan acceptance; this is not sustained continuous-walking proof.

The [manual castle exploration report](../../journal/entries/manual-castle-exploration-2026-10-19.md) confirms practical stairs, angled ledges, collisions and extended free movement. The next priority is [Step 09 Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md): restore original scene population and basic interaction using cylinders. F5 still defers automatic background spawning; missing scripted objects require separate activation/presentation evidence. Full models, exhaustive physics and full experimental ASan remain later acceptance.

[Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md) now identifies the actual pedestal enemies: original `St_gobsc` tracks 284/`gob3` and 293/`gob3b`. Ordinary F5 shows both orange cylinders alongside Joe before and after release. Cylinder mode retains root/motion updates while omitting articulated bones/IK and mesh drawing; bone collision/combat remains unaccepted. The earlier terrain-population probe stays opt-in and did not establish this fixed pair. See the [guard recovery and verification limits](../../journal/entries/pedestal-guard-activation-2026-10-19.md).

The [intro-skip parser continuation](../../journal/entries/intro-skip-fan-ownership-2026-10-19.md) repairs FAN record selection during action callbacks, scene argument ownership and actor finalizer write widths. Space skips at distinct horseback action checkpoints retain both guards and reach release in Debug/ASan. The exact user-reported launch crash has not reproduced in local runtime comparisons; the ownership failure and corrected writes have original-code fixture coverage.

The [general-population continuation](../../journal/entries/general-population-and-direction-audit-2026-10-19.md) supersedes the retained F5 deferral and spawn-event failure: F5 now sets `E2R_DEFER_BACKGROUND_SPAWNS=0`. Original scheduler/event loads scope global archive identity without enabling the old population probe at startup. Generic NPCs and a secondary splash resource activate; populated Debug/ASan camera round trips and released-input observations pass. The user confirms pedestal guard wandering but reports a new immediate post-release direction/arrow regression. Local combined-input replays do not reproduce it; that report remains open alongside general object interaction, combat, articulated collision and full experimental ASan acceptance.

The [2026-10-20 direction continuation](../../journal/entries/direction-modifier-release-2026-10-20.md) reproduces a matching Up+Left/YROT freeze after released Shift/Alt flags remain set in the compatibility bridge. Modifier release now clears those flags; deterministic Debug/ASan and native Wayland ASan replays turn, and the user reports no freezes anymore. A longer native Debug run later fails in the NPC pose-event path `0x42faf8 → 0x424318`. That event handoff, broader interactions and full experimental ASan remain open. F12 packets now retain yaw, matrices and held-arrow bytes for physical reports.

The [early-Space population continuation](../../journal/entries/early-intro-skip-population-2026-10-20.md) reproduces why F5 can still show only the pedestal pair: an early skip omitted `dav:skipsc`'s population-enable opcode. The recovered skip now dispatches that original script, restoring extra actors at release with the existing launch flags. Bounded ASan population passes; Debug later fails in the IK node-pose path `0x42f9c0 → 0x424318 → 0x423674`. Stable early-skip populated Debug exploration and full experimental ASan remain open.

The [NPC pose continuation](../../journal/entries/npc-pose-chain-recovery-2026-10-20.md) closes the early-Space endpoint/IK failure and recovers event-node/pose-owner handoffs. Original-code pose/table fixtures, four builds, independent generator parity and baselines pass. Populated Debug/ASan round trips plus 60-second observations pass, with continuing NPC activity. Native scripted camera steering retains a route limit. [Task 09](steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md) next owns one original object interaction; full experimental ASan and broader combat/model fidelity remain unaccepted.

The [stables crash continuation](../../journal/entries/stables-node-hit-query-2026-10-20.md) repairs missing X/Z and distinct output pointers in `0x42efdc → 0x427160`, plus its adjacent facing vector. Original-code contact/filter fixtures pass normally/ASan; the recorded courtyard checks do not replace manual camera-177 re-entry. Horse presence, scripted/weapon contacts and full experimental ASan remain open.

The [blacksmith sword continuation](../../journal/entries/blacksmith-sword-activation-2026-10-20.md) restores scene-1909/actor-3717 activation and cylinder presentation using original placement and visibility data. Debug/ASan resource integration and populated courtyard round trips pass. The diagnostic probe selects the workshop camera without moving Joe; ordinary F5 workshop re-entry and sword pickup remain unaccepted under Task 09.

The [workshop initialization/visibility continuation](../../journal/entries/workshop-initialization-and-actor-visibility-2026-10-20.md) reproduces the user's camera-350 crash in the prior source and repairs object durability helper/script arguments. Original actor visibility coordinates and separate object/generated cue labels are restored; the original four-generated-actor cap remains unchanged. Debug/ASan view activation 356→350→347, populated courtyard returns and baselines pass. Manual walking re-entry and sword pickup remain Task 09's next acceptance.

## Original-Game Reference — 2026-10-14

The supplied original-game recording now has a [timestamped observation log, contact sheet and code correlations](../../journal/entries/original-game-reference-2026-10-14.md). Joe is restrained in the rear wooden stocks, the restraint opens around 31.4 seconds, Joe leaves/lands/stands, and the HUD appears around 33.4–33.5 seconds. Two green creatures animate before and after that handoff. The first visible gameplay stays in the pedestal courtyard; the reconstructed action-error/rooftop route does not match this reference. The persistent blue foreground form is not evidence of a rendered living Joe. The user's lightning/power-surge explanation is retained separately from directly isolated visual events.

Use restrained, release, free-before-HUD and HUD-with-movement checkpoints during Tasks 02/05/01/03 and Step 09. This reference supplies visual targets, not new reconstructed-runtime acceptance or exact internal scene/resource IDs. Step 09's node repair is complete; post-intro placement/motion queries are next. Task 12 remains the known full-render provider blocker. The user confirms skip taps advance all three logos and shorten the horseback intro; probes must separate those stages and wait for pedestal/action/HUD state. Duplicate instances/foreground switches still limit timing comparisons, and the recording has no audio stream or explicit key timings.

## Deferred Fidelity Work

Earlier reference reports describe three logos, a 30–40 second horseback/castle intro (Space-skippable), then a pedestal/lightning sub-intro (wait-only) and gameplay. The 2026-10-14 clip shows about 16 seconds from the pedestal fade-in to the full HUD, so the older roughly 10-second sub-intro estimate is not an acceptance deadline. Full animation/procession, effects and source-consistent handoff remain incomplete; route/timer progression alone is insufficient.

Historical menu probes show readable Esc contents, mouse-only intro-menu routing to Settings/Load, Music toggling, Settings OK, and Quit confirmation. Load title/slot overlap, a black slot-area rectangle, modal artifacts, and font/color/layout remain unresolved. Task 09 repairs the shared message-copy/requester-pointer defects and verifies the default action-error dialog. Other message callers, keyboard-only modal interaction and typography remain incomplete; the historical gated missing-scene route has not been revalidated through dismissal. These are follow-ups after actor recovery unless they block a specific proof. Full save/load implementation needs a separate task before it is attempted.

## Invariants

1. Keep SDL below the host backend and preserve default X11 builds.
2. Recover calling conventions and data ownership from original disassembly/Ghidra; mirror durable fixes and diagnostics in `GenerateRecon.js`.
3. Distinguish a state latch, a visible actor, actual movement, and faithful gameplay in acceptance claims.
4. Record bounded commands, failures, last useful evidence, and regression impact in the journal.
5. Split new crash families into narrow tasks instead of expanding the control matrix indefinitely.

## Verification

Run from the repository root:

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build --preset linux-clang32-debug-asan`
4. `cmake --build --preset linux-clang32-sdl-debug` and `cmake --build --preset linux-clang32-sdl-debug-asan`
5. `env -u DISPLAY scripts/run-e2-control-matrix.sh`
6. `env -u DISPLAY scripts/run-e2-runtime-regressions.sh` — isolated debug and ASan pass in the 2026-10-14 verification.
7. `SDL_VIDEODRIVER=dummy timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-scene175 120 7000`
8. `python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl/e2recomp` — repeat with the SDL ASan executable; requires GDB/ptrace.
9. `python3 scripts/check-e2-polygon-inputs.py /path/to/E2WIN95.EXE` — repeat with `--asan`; routing/storage checks, not rasterization.
10. `python3 scripts/check-e2-polygon-lighting.py /path/to/E2WIN95.EXE` — repeat with `--asan`; original-x86 angle/rotation/lighting indices, not rendered actors.
11. `python3 scripts/check-e2-rectangle-copy.py /path/to/E2WIN95.EXE` — repeat with `--asan`; copy/ownership and dirty-list dispatch checks with mock COM surfaces.
12. `git diff --check`

Configure each fresh build with its matching preset and game-data path; see [build setup](../../building.md). Use the [audit](../../journal/entries/runtime-audit-2026-09-14.md) for safe scratch regeneration and the gated GDB repro. Manual F5 remains a separate visual check when runtime behavior changes.

## Manual Follow-Up — 2026-09-14

The user’s 2026-09-14 screenshot matches the automated scene-175 static capture (red sky, central horned skull, stone platforms and straw); the accompanying input log reports `scene=0x67da4c`, the scene-175 slot address. Together with the earlier crash-free manual F5 report, this resolves the pending final-image comparison and completes the Step 07 baseline check. It does not establish original scene-selection fidelity or visible living actors; those remain Step 08 work. The missing cue panel was traced to the usual SDL launch leaving `E2R_ACTOR_CUES` unset; the launch at that time enabled cues with an SDL preset after restarting the session. The 2026-10-14 F5 correction below now selects the diagnostic cylinder/action route.

## Change Log

### 2026-10-19

Recovered actual SDL release handling, the original clock wait and target-facing inputs after the user's spinning/crash report. Both runtimes pass SDL release/movement replays and all final baseline checks; motion-query steering remains the next gameplay boundary. See [Step 09](steps/step-09/step-09-enable-diagnostic-gameplay.md) and the [journal](../../journal/entries/player-release-and-spin-2026-10-19.md).

Recovered the queued idle-action ID and traced its wrong FAN load as the source of the ASan release-height failure. Bounded Debug/ASan arrow and combined-input probes now survive with valid height; full controls/traversal acceptance stays open. See [Step 09](steps/step-09/step-09-enable-diagnostic-gameplay.md) and the [journal](../../journal/entries/player-idle-action-2026-10-19.md).

### 2026-10-16 — Player Motion Inputs

Recovered packed player representation selection and live scan-code reads, with original-i386 comparisons and a release-checkpoint press/release probe. Up now reaches an unrecovered world-motion query rather than a false modifier action; Task 05 owns its actor/vector/output contract. Final builds, parity and baseline regressions pass. See the [input journal](../../journal/entries/player-motion-inputs-2026-10-16.md).

### 2026-10-16 — Terminal Root-Pose Ownership

Recovered actor-matrix and saved-position destinations that corrupted the terminal ASan event chain. Original-code fixtures, matching bounded Debug/ASan courtyard release, four builds, generator parity and baseline checks pass. Motion/traversal remain open; representation 67 is bound after release. See the [root-pose journal](../../journal/entries/terminal-root-pose-2026-10-16.md).

### 2026-10-14 — F5 Diagnostic Route Correction

Corrected the cue-only editor launch after the user's screenshots exposed the mismatch with a stopped opt-in capture. Recovered bounded node-removal, action/actor and script-input contracts. Continuous Debug shows Joe during the pedestal action and executes the wait-ending script without the old action error; invalid height/placement and motion-query inputs now block visibility/control. Expanded script names remain gated, baseline checks pass with the noted isolated arrow-row rerun, and gated ASan has a separate query failure. See [historical F5 evidence](../../journal/entries/f5-diagnostic-route-2026-10-14.md); the [floor-decoder continuation](../../journal/entries/courtyard-floor-decoder-2026-10-14.md) supersedes the placement/ASan frontier.


### 2026-10-14 — Cylinder Implementation

Implemented opt-in cylinder presentation, raw state labels/sidecars and a source-audited polygon gate. Drawing/state-preservation fixtures, polygon comparisons, four builds, generator parity, wrapper, eight arrow rows and SDL requester checks pass. A real paused capture shows Joe during the pedestal action; event-0x3f node removal blocked that initial diagnostic route. The later F5 continuation below supersedes that frontier. Full gameplay and original rendering remain open.

### 2026-10-14 — Diagnostic Gameplay Priority

Added Step 09 at the user's request: prioritize controllable cylinder actors, recovered locomotion and view traversal over original meshes/visible animation. Basic Step 03 movement/camera proofs move forward with the necessary Step 08 logic repairs. The rendering bypass and its minimum surface dependencies require audit; this planning update implements no runtime mode and closes no gameplay acceptance.

### 2026-10-14 — Documentation Review

Checked `4fb151a`, corrected build/cue guidance and stale summaries, reverified generator parity and bounded polygon/lighting comparisons, and expanded Task 11's source-backed plan. Original-game capture requirements are recorded in [Step 08](steps/step-08/step-08-recover-scene-175-actors.md#original-game-reference-capture). No runtime implementation or full-route acceptance changed.

Analyzed the subsequently supplied original-game clip and recorded the screen/actor timeline, release/HUD checkpoints, two visible creatures, initial courtyard continuity and code connections. Linked those targets into the actor/action/placement tasks; the reference analysis itself did not change runtime behavior. The subsequent authorized Task 11 repair restores copy/lock inputs and passes original-x86 comparisons and regressions; real surface Lock storage is split into Task 12. Logo/horseback skip taps are recorded explicitly for future probes.

### 2026-07-28

1. Created implementation after the reconstructed-runtime plan reached first gameplay, live SDL presentation, and an SDL F5 launch route.
2. Completed Step 1 with a stable SDL F5/no-crash boundary and activated DirectDraw page/palette/front-buffer recovery.
3. Step 2 advanced post-logo startup scene selection by initializing archive-loaded actor live positions through the original `FUN_0044146c` helper.

### 2026-07-29

1. Reframed the active frontier around E2WIN95 startup-sequence parity after palette recovery proved the logo colors but F5 still skipped the Psygnosis/Andrew Spencer screens and entered the wrong scene/stall path.
2. Recorded the latest bounded result: SDL startup survives to timeout after archive load with crash fixes applied, but does not reach `mar:StartGame` or the expected horseback intro yet.
3. Recovered flat-FANT startup preloads by scanning `Files/ECSTATIC` scene records into `0x650fa0`; opcode-`0x4d` now installs requested scene ids, and the active crash frontier moved to `FUN_0043aa98` scene-removal/list unlinking while loading scene id `1424` before `mar:StartGame`.
4. Cleared the pre-`mar:StartGame` crash chain: bounded SDL/gdb reaches `mar:StartGame` `before-return` and later interrupts in the frame loop. The active frontier is now scene-current ownership and the missing horseback/credits intro route.
5. Repaired generated opcode `0x07`/`0x0c` scene activation to match original `E2WIN95.EXE` register flow by passing the loaded scene record into `FUN_004523f8`. The `horse` scene now activates, exposing the next non-crash frontier: empty actor/current ownership after activation.
6. Recovered flat-FANT actor offsets and hidden actor context through the `FUN_004523f8` activation pass. The normal route now loads actor `0` and reaches the frame loop with nonzero actor/current ownership; the next crash frontier is bogus raw-view/camera selection in the render epilogue.
7. Recovered raw-view scene id and palette filename construction for the render epilogue. Regenerated SDL debug probes now survive 30 frames after `mar:StartGame`, load `hires\1073.raw`, and dump nonblank surface 3; the active frontier moves back to visual/front-buffer parity.

### 2026-07-30

1. Completed DirectDraw front-buffer recovery: hires/full-frame presentation uses recovered surface `3`, with diagnostics reporting `front=3` and palette-applied surface hash `44b33248`.
2. Kept the default runtime regression green by adding generated ASan-safe repairs for surface blits, sparse original globals, raw-view path buffers, palette reads, cleanup marker helpers, and actor animation context.
3. Activated the next implementation step around gameplay control/camera proof expansion and remaining startup-logo timing parity.
4. Fixed the first-scene color mismatch reported by screenshot comparison by publishing `FUN_0044add8`'s freshly loaded `Views/1073.PA2` palette through `FUN_0041af88`; the scene dump now reports palette hash `de4e4c5d`.
5. Fixed the user-reported horizontal squeeze by making SDL presentation aspect-fit source frames instead of stretching `640x480` content to the full `640x640` host window.

### 2026-07-31

1. Reclassified the active input problem: SDL/window event delivery is proven, but intro `Esc`/`Space` game behavior is still wrong.
2. Recorded that `Space` latches in game state during the horseback/credits intro yet is not consumed as a skip; natural completion dispatches opcode `0x07` to scene `7`, which then tries to load missing actor `3853`.
3. Recorded that `Esc` enters the reconstructed menu/requester state path and shows a menu with broken contents, making requester drawing/content presentation the likely next proof area.
4. Paused broader runtime edits and generator work until the action-dispatch/requester-presentation cause is isolated with smaller evidence.

### 2026-08-04

1. Restored hosted high-res requester label visibility for the intro `Esc` path, including a conservative ASCII fallback renderer, requester-item text y-coordinate correction, and a final label redraw after item rectangles are painted.
2. Hardened SDL event polling against injected Win32 probe dispatch from a non-main thread; bounded probes now avoid the SDL main-thread assertion while still delivering queued keys.
3. Added a narrow `FUN_00423858` child/linked actor readability guard after the full wrapper exposed an ASan-only actor-transform crash; the wrapper now fails at the known ASan scene-control gate instead of a sanitizer report.
4. Completed Step 3 Task 01 and activated Task 02 for the compact control probe matrix, carrying the `Space` action-dispatch/completion frontier as the remaining intro-control split.
5. Added and passed `scripts/run-e2-control-matrix.sh`, then corrected it to the Ecstatica II manual mapping: arrow keys are canonical movement and numpad keys are not original controls.
6. Fixed SDL/X11 host key translation so physical arrows reach WndProc as `VK_UP`, `VK_DOWN`, `VK_LEFT`, and `VK_RIGHT` instead of masquerading as numpad keys. Added parser/scan coverage for `ctrl`, `shift`, `alt`, `ralt`, `s`, `i`, and `l`; Task 03 owns modifier, status/icon, save/load behavior classification.
7. Added bounded intro-menu mouse-click probes and fixed the requester mouse path. `--inject-intro-menu-click-surfaces` now proves Settings (`320,225`) routes to requester id `0x31`/state `2`, and Load (`320,203`) routes to requester id `0x29`/state `4` without crashing. The sequence probe `--inject-intro-menu-click-sequence-surfaces` now proves the Settings Music row dispatches through item `0x643998` and flips `settings.music=1`, and its target-requester Esc mode proves Settings/Load submenu close paths finish with `DAT_00636844=0` and `_DAT_00643650=0`.
8. Repaired the manual intro-menu artifact/crash repro: Start Game now guards the stale-current actor write in `FUN_0043a39c` and routes to `action.restart_intro` during the intro, high-res requester panel/item rectangles draw from explicit hosted bounds instead of hidden-register coordinates, disabled Save is consumed without closing requester `0x28`, active main-menu Escape unwinds as cancel/no-selection, and Settings row/OK clicks dispatch in bounded probes. Submenu opening now passes explicit requester records for Settings and Load/Save; Load/Save uses the wider slot-list record so it is visible and framed, with title/slot overlap and the left black rectangle still pending. Keep manual real-SDL confirmation as the next acceptance check before moving on to Load slot/OK fidelity.

### 2026-08-17

1. Folded the latest manual real-SDL report into Task 03: startup logo order is now correct, the intro still lacks character animation/scene progression, main menu Esc/Cancel works basically, Quit/Settings/Load remain rough, and Save is inert in the intro menu.
2. Repaired requester label fallbacks for fixed-address `OK`, `Yes`, and `No` text, redraws Settings row toggles in place, names Load/Save slot actions in diagnostics, consumes slot-row clicks without closing the active Load/Save requester, and logs requester `0x28` item bounds for future probes.
3. Verified with `linux-clang32-sdl-debug` dummy-SDL probes: Settings Music toggles to `settings.music=1`, Settings OK returns to the main menu, Load slot clicks report `action_name=load_slot` while staying in requester `0x29`, Quit Yes exits cleanly, and Quit No returns to requester `0x28`.
4. Moved first-intro `Space` from input-delivery proof to action-completion proof: the skip helper now consumes Space and sets action `0x937800` to duration `495`, `FUN_0042b004` breaks on the observed self-loop sentinel, and the active frontier is the post-completion `FUN_00421f54` actor/list-context crash before the pedestal/lightning sub-intro is reached.

### 2026-08-18

1. Recovered the pragmatic first-intro skip route: `Space` during the `horse` scene-child action wrapper now logs `intro skip request` and loads `Start_sc`; `Space` during `Start_sc` is consumed as wait-only.
2. Repaired supporting generated frontiers exposed by the skip path: fixed scene-child allocation, skipped unresolved no-archive startup children, preserved action-event actor context, added a CRT RNG fallback, and recovered the sound id for `FUN_0042b880` subcase `5`.
3. Recovered `Start_sc` completion into gameplay: scene-child actor live-vector initialization now preserves Joe at `12800,256,-3584`, signed scene-height lookup treats descriptor byte `0xff` as passable, and the later handoff repair preserves scene `175` when `FUN_0044c224` tries to switch to scene `87`.
4. Added grouped held-key probe notation and repaired the ASan render/action helper crash chain exposed while re-running the movement matrix. `scripts/run-e2-control-matrix.sh` now passes all debug and ASan rows for `up/down/left/right` after the explicit-context and packed-table fixes.

### 2026-08-20

1. Repaired the post-`Start_sc` wrong-location handoff reported from manual SDL: the exact action `0x9377e3` completion now sets a one-shot guard, and `FUN_0044c224` preserves current scene slot `175` when descriptor `48771` proposes scene `87`.
2. Verified `node --check`, regeneration, `git diff --check`, `cmake --build --preset linux-clang32-sdl-debug`, and the long dummy-SDL route. The route exits with `_DAT_0073cc3c=0x67da4c`, `hires\0175.raw`, surface 3 hash `321e33d6`. The initial Joe-visible interpretation was disproved by the 2026-08-21 packets.

### 2026-08-21

1. Added a post-handoff visibility packet probe with F12 and env triggers. It captures game framebuffer pages, SDL converted presentation, SDL final window surface, and a state sidecar so the current manual no-player report can be classified by layer.
2. Verified the post-handoff dummy-SDL packet: scene slot `175`, action pointer cleared, selected surface `3` hash `321e33d6`, SDL present hash `914159a1`, SDL window hash `5cf799a1`, and contact/diff artifacts generated by `scripts/e2r_visibility_sheet.py`.

### 2026-09-14

1. Reconciled current claims against the audit, retracted living-Joe visibility, and separated input proof from playability.
2. Added Steps 07/08 and deferred remaining Step 03 controls behind baseline and actor recovery.
3. Recorded generator drift and the current debug numpad-wrapper failure; source repairs remain pending.

4. Completed generator diagnostic mirrors and canonical wrapper correction; split the ASan natural-intro action-candidate crash into Step 07 Task 03. All 8 arrow rows and the SDL static packet remain passing; Step 07 is not complete.

### 2026-09-14 — SDL Cue Launch Follow-Up

The usual SDL F5 launch now enables actor cues. The supplied screenshot/log resolves the manual static-scene comparison and closes Step 07; Step 08 remains active.

### 2026-09-14 — Build And Editor Workflow

Consolidated F5 around the selected CMake target, shared preset settings, added X11/SDL ASan presets, and moved personal data paths to environment/cache/local overrides. See [build and editor setup](../../building.md). Step 08 source recovery is unchanged; Step 06 still owns unified validation and broader bootstrap acceptance.

### 2026-09-14 — Build Types And Compiler Visibility

Added SDL Debug/Release/RelWithDebInfo/MinSizeRel choices, explicit Debug + ASan names, and configuration-first output directories. Shared presets use `clang-21` with a major-version check; local presets can select another installed Clang in an isolated directory. Regression scripts and current Step 08 commands follow the new paths. All nine configurations build; the Debug wrapper/matrix and SDL probes pass. Release, RelWithDebInfo and MinSizeRel currently crash during startup, so their runtime recovery remains separate from the active Debug scene-pose work. See [build setup](../../building.md).
