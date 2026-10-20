# Recover Scene Population And Interaction

Status: in progress; generic F5 population enabled; direction report and wider interaction open
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-19

## Goal

Restore original scene objects and NPCs needed for exploration and basic interaction while retaining cylinder presentation and Joe's working movement/camera transitions. Begin with one verified original resource and behavior; original models and full combat remain later work.

## Current Continuation — Generic Spawns And Direction Report

The user confirms the two pedestal guards wander after intro 2. [General population and direction audit](../../../../../journal/entries/general-population-and-direction-audit-2026-10-19.md) now recovers the first `0x42f9c0` spawn event and queued-action failure, including root/FK pose and angle conversion inputs. Correct archive identity is scoped to original scheduler/event loads. F5 sets `E2R_DEFER_BACKGROUND_SPAWNS=0`, with no population-probe flag or per-enemy whitelist. Populated Debug/ASan 175→166→175 routes and released-input observations pass. Earlier deferral, opt-in-only and failed-return statements below describe the prior slice.

The user's new immediate post-release direction/arrow failure remains unresolved: combined Up+Left replays, including normal-speed bursts, update yaw/matrices and displacement locally. Keep physical F5 confirmation/reproduction open. General object interactions, broader enemy actions/combat and full experimental ASan are still unaccepted.

## Evidence And Dependencies

The [manual castle report](../../../../../journal/entries/manual-castle-exploration-2026-10-19.md) confirms practical stairs, angled ledges, collisions and extended free movement, but no switches, doors, traps, enemies or pickups. The existing F5 launch explicitly defers automatic background population. [Task 04](task-04-recover-npc-spawn-query-inputs.md) recovers its bounded inputs; full loading/activation remains unresolved. [Step 08 Task 03](../../step-08/tasks/task-03-activate-scene-backed-children.md) owns original scene-child identities and activation.

Automatic NPC population and scripted objects are separate paths. An empty cylinder overlay alone does not prove no interaction state exists. Establish resource identity, live instance/scene membership and presentation eligibility before classifying each missing category. Do not infer script resources from camera slots or manufacture the reference creatures/objects.

## First Bounded Action

1. Capture an actor/scene-child census after release and at a known castle object location. Inspect loaded instances, active/update lists, flags, representation and diagnostic drawing eligibility. Distinguish loading/activation failure from omitted presentation or script/dynamic-background state.
2. In a separate bounded probe, turn off only background-spawn deferral. Trace `0x44dca4 → 0x44db80 → 0x451f5c` and the first required resource/query/activation failure. Preserve the everyday F5 flags until that path is stable.
3. Trace script-owned scene activation independently through `0x452140`, `0x4523f8` and `0x4533ac` as required. Choose one original object/NPC whose identity and source path are established; repair its first proven contract rather than enabling unrelated resources.
4. Mirror reconstructed repairs in GenerateRecon.js, add focused original-code comparisons, regenerate with four-artifact parity and verify the required Debug/ASan route plus baseline regressions.

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
