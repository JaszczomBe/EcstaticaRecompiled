# Recover Scene Population And Interaction

Status: in progress; workshop initialization crash reproduced/repaired and object/actor visibility audited; manual location re-entry and sword pickup remain open
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-22

## Goal

Restore original scene objects and NPCs needed for exploration and basic interaction while retaining cylinder presentation and Joe's working movement/camera transitions. Begin with one verified original resource and behavior; original models and full combat remain later work.

## Current Continuation — NPC Poses And Object Interaction

The [post-pedestal callback repair](../../../../../journal/entries/post-pedestal-deactivation-callback-2026-10-22.md) reproduces the user's new `FUN_0043cac0 ← FUN_00414e68 ← FUN_0044f508 ← FUN_0044f310 ← FUN_00426ca4` stack by exact replay at sequence 890,925,953/checkpoint 47. Original instructions recover selected code/actor arguments, cleared script node and retained actor lifetime. Compatible replay returns from four callbacks before incomplete-prefix exhaustion; natural Debug/ASan intros and 60-second released idle observations pass. Original callback comparisons and baselines pass. An additional populated Debug traversal remains failing its floor-return assertion; ASan's bounded round trip passes. Workshop re-entry, pickup and full experimental ASan acceptance remain open.

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

The [blacksmith sword capture](../../../../../journal/entries/blacksmith-sword-location-2026-10-20.md) selects a concrete target: original scene **1909** / actor **3717**, both `nschwrt1`, in **camera 347**, positioned at **(-972, 3884, -10208)** beside the workbench. The user's F12 packet has no sword on the active actor list, but does not establish whether it is loaded elsewhere. Switches are quest gated; doors require sword attacks. Restore this sword's presence and then pickup before using either as a first interaction target.

1. Confirm ordinary F5 re-entry through cameras 356/350 to the user's camera-347 location, with actor 3717 visible beside the workbench; retain an F12 packet. The reported initialization crash is reproduced/repaired and automated view activation/return passes, but this manual walking route remains open. Object markers now use neutral `OBJECT` labels; their cylinders do not indicate enemies.
2. Trace the sword's original proximity/input script and pickup action. Establish the expected original input and acquired/equipped state before implementing that first pickup; retain generic NPC updates and Joe's movement. The sword mesh and its attack/door-destruction animations remain separate work.
3. Mirror any repair in `GenerateRecon.js`, compare the recovered pickup contract with original instructions and rerun populated Debug/ASan crossing/return plus baseline regressions. Keep combat, full models and broad category coverage separate.

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
