# Recover Scene Population And Interaction

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
<!-- /docs-tree:parent -->

Status: in progress; human sword pickup, four kills and two door destructions verified; animation-cache stall repaired; typed markers and Debug/ASan gameplay menu Quit pass; human random-potion pickup verified; delayed potion effects repaired; human bottle removal/sword use confirmed; diagnostic health/effect panel added; healing/effects verification next; wider pickups, extended stability and rendering deferred
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-24

## Goal

Restore original scene objects and NPCs needed for exploration and basic interaction while retaining cylinder presentation and Joe's working movement/camera transitions. Begin with one verified original resource and behavior; original models and full combat remain later work.

## Current Continuation — Visible Health And Potion Status

The [health/status review](../../../../../journal/entries/diagnostic-health-and-potion-status-2026-10-24.md)
confirms the user's latest bottle removal and later sword attachment/attacks.
Recorded health falls **100→70** before drinking; original HUD graphics are
omitted in diagnostic gameplay. A new read-only bottom panel exposes actual
health plus poison/invisibility action/timer status. It hides during modal
menus and stays visible with Joe offscreen. Normal/ASan marker fixtures, four
builds and live Debug/ASan potion routes pass. Human health recovery and potion
lifetime/cure checks are next. Wider pickups, extended stability and rendering
are deferred at the user's explicit request.

## Prior Continuation — Consumed Bottle Removal

The [bottle-removal review](../../../../../journal/entries/consumed-potion-removal-2026-10-24.md)
confirms both left-hand bottle and right-hand sword attachments in the user's
new run; all **549** exact replay checkpoints match. Animation-name interning
and lookup incorrectly used **4,375** of the original **17,500** bytes. This
turned the bottle's `glofade`/`potvan` chain into missing actions. Restoring the
original bounds and new-animation slot ownership lets `ken:RemoveActor` clear
the bottle's representation and reciprocal attachment.

All **1,800** installed animation names match original x86 in normal/ASan
fixtures. Fresh input-only Debug/ASan routes verify drinking and bottle removal,
then sword collection, all four attack directions and movement with the bottle
still gone. Separate final routes retain poison dispatch. Four builds, generator
parity, actor/script-name fixtures and runtime baselines pass. Human F5 repetition,
healing from damage, other effects/items and broader fidelity remain open.

## Prior Continuation — Workshop Random Potion And Delayed Effects

The [potion review](../../../../../journal/entries/workshop-random-potion-and-timers-2026-10-24.md)
confirms human session **20261024_142028_732** through all **742** exact
checkpoints and clean menu exit. Bottle **537**/`fakepot2` is a random-effect
potion: the original script **189** selects **183**/`ken:purpotion` on pickup.
It attaches to Joe and starts `joedrink`. This corrects its earlier prop label.

Delayed effects lost their actor/action/delay arguments, allocated outside the
original timer pool and never passed an unsigned deadline test. Those contracts
are restored with generator parity and **12,288** original-code cases each in
normal/ASan. Fresh input-only Debug/ASan routes now queue poison/death, execute
poison action **409** and remove its timer, retaining future death, Joe health
**100**, state **4**, and no sanitizer report. Four builds, marker and scheduled
completion fixtures pass. Healing from below maximum health, final bottle
cleanup, poison death/cure/fade and broader items remain open. Current sampled
bottle attachment persists; no speculative disappearance is introduced.

## Prior Continuation — Door Marker Placement And Creature Direction

The [marker follow-up](../../../../../journal/entries/long-play-cache-reclamation-and-markers-2026-10-24.md#follow-up-door-marker-placement-and-creature-direction)
corrects intact doors to follow the first model node's offset, half-extents and
rotation. Workshop door **980** is broad along local Z and offset from its actor;
the previous centred X-wide slab misrepresented its placement. Living creature
markers again draw their projected local +Z line. Corpse markers remain low.
The host computes these cues privately, without changing actor/collision state.
Debug/ASan marker fixtures verify both hinge-side headings, visible creature
direction pixels, corpse suppression and unchanged game memory. Four builds
pass; fresh Debug/ASan input routes confirm sword pickup, collapse and passage
with health **100** and no sanitizer report. Evidence and limits are recorded
in the linked journal.

## Prior Continuation — Longer Playthrough, Cache Reclamation And Markers

The [2026-10-24 review](../../../../../journal/entries/long-play-cache-reclamation-and-markers-2026-10-24.md)
verifies deaths of actors **602, 293, 284, 74**, destruction of doors **980, 963**
and attached sword **3717**. Potion pickup is not confirmed: the two workshop
Space attempts leave **537**/`fakepot2` unchanged; its original handler is
`ken:fakepot`.

Exact replay reaches checkpoint **469**, then exhausts the temporary record pool
while loading enemy animation **1439**. Escape is never delivered. Cache eviction
now retains the selected action and releases its keyframes/event records, with
original-code comparisons and generator mirrors. Final Debug replay passes the
load and all **469** checkpoints, ending at the incomplete recording boundary.

Host-only shapes distinguish creatures, corpses, doors, debris, bottles, blades,
items and props, with original-name labels. Modal menus suppress the overlay.
Fresh Debug/ASan input routes acquire the sword, destroy/pass the door, cancel
Escape, reopen Quit, confirm Yes and exit normally. Four builds, parity,
original comparisons, marker fixtures and runtime regressions pass. The long ASan replay is incomplete at 180 seconds/checkpoint **308** with Joe alive and no sanitizer report; the late cache boundary is established by Debug replay and original-code/ASan fixtures. Genuine
potion effects, other items/points, wider combat and full rendering remain open;
prior ASan courtyard steering/floor-return limits remain separate.

## Prior Continuation — Workshop Door Hit Callback

The [2026-10-24 door journal](../../../../../journal/entries/workshop-door-hit-callback-2026-10-24.md)
confirms the human smith kill (actor **602**, health **−20**, state **11**) and
exactly reproduces the door crash at checkpoint **125**, sequence
**1,768,693,458**. Target **980**/`kdorr` still has health **60**: this is a hit
callback failure before collapse. The selected attack and target-hit script
records were lost entering the interpreter. Both original handoffs are restored
with scoped code/owner/target/child/node contexts and generator parity.

The expanded original-code fixture passes **32,768** cases normally/ASan,
including **37,188** scripted callback handoffs. Fresh SDL Debug/ASan routes
reduce the left door **100 → 60 → 20 → −20**, execute hit action **370** and
collapse action **377**, then observe state **11** with no representation.
Released forward movement passes through the opening into camera **164** with
Joe health **100**, state **4** and no modal or sanitizer report. Four builds,
baseline/control and requester checks pass. Next is human F5 door collapse and
passage repetition; other objects, area attacks, wider combat and full rendering
remain separate acceptance. Prior ASan courtyard steering/floor-return limits
remain open.

## Prior Continuation — Sword Attacks And Attached Position

The [2026-10-24 attack journal](../../../../../journal/entries/sword-attacks-and-attached-position-2026-10-24.md)
confirms human pickup and exactly reproduces the subsequent Ctrl/arrow crash in
`FUN_0042e7dc` at checkpoint **91**, sequence **1,338,228,752**. Original actor/XZ
and direction-preservation contracts are restored. The sword's persistent
workbench cylinder reflects stale actor coordinates: attached rendering lost
owner/actor arguments and cylinder mode omitted the moving hand pose. Those
contracts and the original bounded pose work-list are restored, with generator
parity and normal/ASan original-code comparisons.

Fresh SDL Debug/ASan input routes acquire the sword, start all four requested
Ctrl/arrow attack directions, release and move with health **100**, state **4**,
representation **9**, no modal and reciprocal attachment links. The sword's
world coordinates change with its hand attachment. Builds, baseline/control and
requester checks pass. Debug's populated courtyard return passes; ASan steering
attempts miss the outward camera or return floor while retaining health 100 and
no sanitizer report. Human swing/marker repetition and actual weapon contact/damage remain open.

## Prior Continuation — Water Replay And Sword Pickup

The [2026-10-24 pickup journal](../../../../../journal/entries/water-replay-and-sword-pickup-2026-10-24.md)
confirms human session `20261024_115621_101`: all **565** exact checkpoints match,
including swimming across cameras 543→545 with health **100**, state **4** and
representation **13**. Session `20261024_115718_697` confirms walking through
350/348 into workshop camera **347**, then exactly reproduces the Space pickup
crash at checkpoint **62**. Both pinned recordings are preserved independently
of session retention.

Original player/polar arguments, the first model-node origin needed for pickup
height, the attachment event's node/owner/script handoff, and hosted Space release
are restored. Fresh SDL Debug/ASan input routes acquire actor **3717**, verify
reciprocal attachment links to Joe, equipped kind **3** and representation **9**,
then move while retaining health **100**, state **4** and no modal. Original-code
comparisons, generation parity, populated courtyard returns and baseline checks
pass. The crashed recording ends at its fault; fresh input supplies pickup
completion evidence. The newer human report above confirms pickup; the attack
and attached-position continuation owns the next acceptance.

## Prior Continuation — Early-Skip Startup Regression

The [2026-10-24 startup repair](../../../../../journal/entries/pedestal-intro-restart-2026-10-24.md)
reproduces the user's pedestal-to-horseback restart, rooftop displacement and
later death/menu in a complete exact replay (1,810 matching checkpoints). The
original skip script's nine actor cleanup references were unresolved because
actor names were truncated at 10,000 rather than 40,000 bytes and 108 startup
literal suffixes were absent. Both contracts and new actor-slot ownership are
restored, with generator parity and original-code comparisons.

Fresh Debug/ASan early skips finish the pedestal scene, retain movement and pass
60-second released-input checks. Skipping at the recorded first-action progress
83/495 also passes populated crossing/return with health 100 in both builds.
Natural-intro water/swimming checks pass again. The complete 83/495 skip-to-water
route passes in Debug; ASan times out before water with health 100 and remains
incomplete. The newer human sessions confirm traversal, swimming and workshop
re-entry after the startup repair; pickup repetition and the separate broader
Debug floor-return issue remain open. Old recordings
correctly diverge after changed cleanup; no checkpoint acceptance is weakened.

## Prior Continuation — Water Entry And Object Interaction

The [water-entry repair](../../../../../journal/entries/water-entry-and-player-resource-2026-10-23.md)
restores original actor identity for ordinary gameplay loading: local node zero
formerly aliased potion actor 4119/`fpot6` as Joe, losing his swimming capability.
Live swimming-scene reads and opcode-0x54's packed state write are also recovered.
All 1,922 actor headers and bounded original-x86 water/selector/reload contracts
pass. Natural-startup Debug/ASan input routes reach camera 543 and swim forward
with health 100, state 4, representation 13 and no modal. The newer human replay
confirms water entry/swimming; shore exit and held-item swimming remain open.

## Prior Continuations — NPC Poses And Object Interaction

The [camera-722 continuation](../../../../../journal/entries/blank-requester-and-large-replay-2026-10-23.md)
restores the full original directional-reaction table and passes 524,288 x86
comparisons normally/ASan. The user repeated the location without the blank OK
prompt; the new recording completes and passes three exact replays with all 120
checkpoints matching. The old recording's post-repair divergence
keeps its original terminating caller unproven. Requester text/evidence and
console/reader improvements are documented with the tool acceptance.

The [post-pedestal callback repair](../../../../../replay.md#status-and-current-acceptance) reproduces the user's new `FUN_0043cac0 ← FUN_00414e68 ← FUN_0044f508 ← FUN_0044f310 ← FUN_00426ca4` stack by exact replay at sequence 890,925,953/checkpoint 47. Original instructions recover selected code/actor arguments, cleared script node and retained actor lifetime. Compatible replay returns from four callbacks before incomplete-prefix exhaustion; natural Debug/ASan intros and 60-second released idle observations pass. Original callback comparisons and baselines pass. An additional populated Debug traversal remains failing its floor-return assertion; ASan's bounded round trip passes. Workshop re-entry, pickup and full experimental ASan acceptance remain open.

The [natural-intro detach repair](../../../../../journal/entries/natural-intro-attachment-detach-2026-10-22.md) recovers the reported `FUN_0042db74` event node and attached-actor inputs. Its original checkpoint completes both intros in Debug without input or recording, followed by a verified 15-second idle observation. Original detach/caller comparisons pass normally and under ASan. The separate actor-deactivation script failure exposed then is addressed by the callback continuation above; workshop re-entry, sword pickup and broader interaction acceptance remain open.

The user confirms the two pedestal guards wander after intro 2. [General population and direction audit](../../../../../journal/entries/general-population-and-direction-audit-2026-10-19.md) now recovers the first `0x42f9c0` spawn event and queued-action failure, including root/FK pose and angle conversion inputs. Correct archive identity is scoped to original scheduler/event loads. F5 sets `E2R_DEFER_BACKGROUND_SPAWNS=0`, with no population-probe flag or per-enemy whitelist. Populated Debug/ASan 175→166→175 routes and released-input observations pass. Earlier deferral, opt-in-only and failed-return statements below describe the prior slice.

The [2026-10-20 modifier-release continuation](../../../../../journal/entries/direction-modifier-release-2026-10-20.md) reproduces a matching immediate Up+Left freeze after released desktop modifiers remain logically held. YROT also freezes. The compatibility key-up repair clears those flags; deterministic Debug/ASan and native Wayland ASan replays turn again, and the user reports no freezes anymore. The longer native Debug route later fails in an NPC pose event (`0x42faf8 → 0x424318`), whose node/pose handoff is recovered by the NPC pose continuation below. General object interactions, broader enemy actions/combat, complete directional fidelity and full experimental ASan remain unaccepted.

The [NPC pose continuation](../../../../../journal/entries/npc-pose-chain-recovery-2026-10-20.md) recovers endpoint/root/IK inputs and the node-chain event's pose owner from original instructions. Original x87 table initialization, endpoint/IK/attachment memory comparisons and event handoffs pass normally/ASan. The prior early-Space Debug spawn frontier is crossed; populated Debug/ASan round trips and 60-second observations pass. Native scripted camera steering retains a route limit; wider combat/interaction and full experimental ASan remain open.

The [stables crash continuation](../../../../../journal/entries/stables-node-hit-query-2026-10-20.md) follows the user's camera-177 report at `0x427160 ← 0x42efdc ← 0x42faf8`. The hit-query caller now retains X/Z and separate polar outputs; the adjacent owner-to-target facing vector also has both coordinates. Normal/ASan original-code comparisons cover 16,384 filter/contact cases. Exact manual stable re-entry, horse presence and broader scripted/weapon contacts remain separate acceptance.

The [blacksmith sword activation](../../../../../journal/entries/blacksmith-sword-activation-2026-10-20.md) restores placement caching, the original loose-archive visibility index and retained actor/action inputs. Scene 1909's sword actor 3717 activates at its original workbench position and projects as an orange cylinder in Debug/ASan. The integration probe selects camera 347 through the normal visibility sweep, then restores the prior view without moving Joe; it does not establish walking into the workshop or pickup. Populated courtyard round trips pass afterward. F12 now includes preloaded script scenes for the current camera, including resource IDs above 1199.

The [workshop initialization/visibility continuation](../../../../../journal/entries/workshop-initialization-and-actor-visibility-2026-10-20.md) follows the user's failed approach at camera 350. An isolated prior-source build reproduces `0x456924` during object initialization; the helper and opcodes `0x66`/`0x68` now retain their actor/value/action inputs. The actor visibility updater also retains the original world-position argument. Neutral object markers, separate generated counts and visibility filtering address the misleading enemy density; the scheduler still matches the original four-generated-actor cap and 50-tick cadence. Debug/ASan view sweeps 356→350→347 activate the sword and pass populated courtyard returns, with the real durability call observed under ASan. Exact F5 walking re-entry and pickup remain open.

## Evidence And Dependencies

The [early-Space continuation](../../../../../journal/entries/early-intro-skip-population-2026-10-20.md) reproduces the user's remaining F5 population difference: an early skip leaves the original script population gate set even with the correct launch flags. Space now dispatches the original `dav:skipsc` script, including its population-enable opcode. Additional actors appear at release and the bounded ASan census passes. Debug then reached `0x42f9c0 → 0x424318 → 0x423674` in an unrecovered IK branch. The NPC pose continuation above supersedes that failed exploration result and recovers this node/root/IK family plus the preceding node-chain event pose handoff. Broader interactions remain the next bounded work.

The [manual castle report](../../../../../journal/entries/manual-castle-exploration-2026-10-19.md) confirms practical stairs, angled ledges, collisions and extended free movement, but no switches, doors, traps, enemies or pickups. The existing F5 launch explicitly defers automatic background population. [Task 04](task-04-recover-npc-spawn-query-inputs.md) recovers its bounded inputs; full loading/activation remains unresolved. [Step 08 Task 03](../../step-08/tasks/task-03-activate-scene-backed-children.md) owns original scene-child identities and activation.

Automatic NPC population and scripted objects are separate paths. An empty cylinder overlay alone does not prove no interaction state exists. Establish resource identity, live instance/scene membership and presentation eligibility before classifying each missing category. Do not infer script resources from camera slots or manufacture the reference creatures/objects.

## Next Bounded Action

The user confirms bottle removal and subsequent sword use in the latest F5 run.
Use the new **HEALTH / POISON / INVISIBILITY** panel to verify healing from
naturally received damage, then poison lifetime/cure and invisibility expiry.
Record the actual random branch and state change; drinking alone does not prove
a particular effect. Current evidence and indicator semantics belong to the
[health/status journal](../../../../../journal/entries/diagnostic-health-and-potion-status-2026-10-24.md).

Defer broader items/points, prolonged stability investigation and original mesh
work until these focused checks are complete or the user changes priorities.
Retain existing courtyard steering and full-render limits without reopening
those tasks during this continuation.

## Acceptance And Limits

The first slice requires a source-confirmed resource to instantiate/activate, appear as a suitable diagnostic cue when applicable, and perform one expected behavior or player interaction. Joe must remain controllable, and the courtyard crossing/return must still work. Record loading, actor/script state and normal SDL presentation together. Full category coverage, enemy AI/combat, original models and full experimental ASan remain separate acceptance; do not remove population deferral globally based only on intercepted fixture success.

## Pedestal Pair Correction — 2026-10-19

The original terrain experiment below did **not** establish the two pedestal enemies. The user's screenshot comparison is the acceptance target: Joe plus two enemies while still restrained. Original `St_gobsc` resource 101/view 175 owns actor 284 (`gob3`) and 293 (`gob3b`), independently of terrain spawning.

Scoped scene-child archive loading now preserves their original identities/tracks. Ordinary four-flag F5 presents three cylinders before and after Joe's release; no population flag or debugger activation is required. Root-reference, sound-event and node-scale inputs have original-code coverage. Cylinder mesh bypass now omits child-bone/IK posing as well as alternate mesh raster paths; articulated collision/combat and attachments remain unverified. General object interaction and complete Task 09 acceptance remain open.

Run `scripts/probe-e2-player-motion.py EXE --pedestal-guards --camera-round-trip --observe-seconds 5 --timeout 120` for restrained/released guard presence, projection and the SDL route. Follow the [guard journal](../../../../../journal/entries/pedestal-guard-activation-2026-10-19.md) for final verification and remaining limits. Older census names come from a malformed hosted name pool; verify original resource names by archive ID.

A subsequent user Space-skip crash report led to [FAN/action parser ownership and finalizer repairs](../../../../../journal/entries/intro-skip-fan-ownership-2026-10-19.md). `--intro-skip-action N` now tests the real SDL Space handoff at observed horseback actions; `--natural-intro` tests completion without a skip. Keep the runtime reproduction limit and broader acceptance limits explicit.

## Implemented Population Slice — 2026-10-19

Before the companion-loader fix, the release census found only Joe in the loaded/active actor tables and no active script-scene children. The original population scheduler is reached; it was not an input or scheduling gate. Its floor wrapper discarded the valid height return. After that repair, actor loading exposes an archive identity error: the binary header's local node field was used as the global actor name, and payload bytes were accepted as headers. A header-aware lookup finds 1,922 actual actor resources, including the previously missing terrain-selected resources.

`E2R_POPULATION_PROBE` isolates corrected archive actor identity. The repeatable probe enables it **after observed release**, then disables spawn deferral through configuration only. Actor construction uses the normalized name field only while parsing the requested archive actor. The existing intro/action resources keep their earlier behavior. This boundary is necessary: applying all corrected actor identities at startup exposes unrecovered skeletal transform inputs. Do not add the flag to the everyday F5 environment yet.

The slice also restores the initial script's code/actor inputs, contiguous line-of-sight vectors, NPC wandering terrain samples, distance outputs, persistent pose destinations and deactivation ownership. Two byte-offset mistakes in actor-list removal could discard Joe when a new spawn was rejected or culled; both now compare with original instructions. Cylinder mode also omits the actor pixel-rectangle overlap pass, extending its existing graphics bypass while actor updates, physics, scene selection and scripts continue.

The new `scripts/check-e2-population.py` compares original actor construction and script handoffs, 512 line-of-sight traces, 4,096 wander traces, 65,536 distance vectors and actor removal/deactivation. It checks 40 real archive lookups among 1,922 headers. The scene-grid fixture now compares the floor wrapper return as well as its helper.

```sh
python3 scripts/check-e2-population.py \
  /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE \
  /home/rgrabowski/Games/Ecstatica2/Files/ECSTATIC --asan
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl-asan/e2recomp \
  --population-frames 300 --population-only --output /tmp/e2-population-census
```

The live census records resource names, loaded instances, active membership, positions, actions and states alongside SDL visibility packets. ASan survives 300 population frames with Joe active and original resources entering state 3 (wander) and changing position. A longer ASan input probe reaches camera 166 with additional projected cylinders in the normal SDL window. This establishes a bounded population/behavior/presentation recovery, not general interaction or full experimental sanitizer acceptance.

## Prior Slice Failure And Acceptance Still Open

- Debug's extended population probe reaches an attachment/spawn action through `0x427584 → 0x42ae80 → 0x42b338 → 0x42b880 → 0x42f9c0`; that helper still loses its node/actor/action inputs. Recover this event family before enabling population in F5.
- The population-enabled ASan camera probe crosses to 166 but its reverse-input route does not return to pedestal camera/floor within the probe limit. Existing Joe-only Debug/ASan crossing/return remains verified. Do not treat either the longer probe or the full task as passing.
- Script-owned scene activation remains independent: the original empty release census predates the fixed guard companion. Switches, doors, traps and pickups still require a source-confirmed resource and one verified interaction. Camera slots are not script IDs.

See the [population recovery journal](../../../../../journal/entries/scene-population-recovery-2026-10-19.md) for evidence and commands. Keep the original Task 09 acceptance criteria and F5 spawn deferral in place.

## Callback contract

The post-pedestal repair supplies the selected script code and actor to
`FUN_0044f310`, clears the script node/child arguments, and preserves actor ownership
across the callback. The durable repair is mirrored in `GenerateRecon.js` and
covered by the script-flow and population fixtures. The replay guide records the
historical exact-crash and compatible-prefix results; native completion and wider
traversal remain separate acceptance gates.

The originally referenced continuation journal and its local bug bundle are not
present in this checkout. This task and the replay status are the available
implementation record; they do not replace the missing raw historical artifacts.
