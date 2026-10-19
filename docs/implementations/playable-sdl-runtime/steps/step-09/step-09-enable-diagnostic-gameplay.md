# Enable Diagnostic Gameplay With Cylinder Actors

Status: active; bounded courtyard camera round trips pass; motion-query fidelity and sustained acceptance remain open
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-19

## Goal

Control Joe as a simple projected cylinder against the original scene backgrounds, using recovered actor position, locomotion, height queries and camera/scene selection. Walk across a view boundary and back without requiring original meshes, limb animation, lighting or full intro visuals.

The user explicitly prioritizes this intermediate result over original character rendering. This step changes execution order; it does not declare Step 08's original-rendering acceptance complete.

## Why This Step Exists

The existing input matrix proves delivery/latches, but the default runtime has no loaded actions, Joe's stored position is behind the pedestal camera, and real actor motion remains unproven. The recovered action route reaches mesh/copy failures before full gameplay can be inspected. Finishing the original renderer first is no longer a prerequisite for the user's first useful milestone.

There is useful reusable code: `E2R_GetActorCues` supplies validated live actors, world positions and camera projections; SDL already draws read-only crosses/uprights after indexed-frame conversion. Extend that path for cylinder visualization while recovering the minimum real gameplay state beneath it.

## Scope And Boundaries

1. `E2R_ACTOR_CYLINDERS=1` now selects cylinder presentation. `E2R_PROXY_MESH_BYPASS=1` omits the `FUN_00424e44` polygon dispatcher and original 2D graphics/HUD leaves; graphic script operand spans are preserved. Other render/restore paths remain active. F5 supplies both flags plus `E2R_ACTION_INDEX_PROBE=1` and `E2R_DEFER_BACKGROUND_SPAWNS=1`. The latter explicitly defers only automatic terrain-driven population creation; it is a Joe-first prototype limit, reported on screen. Existing actors, scripts, action events and player physics/view queries still run. This is an implemented diagnostic slice, not a working gameplay switch.
2. Preserve input, scripts/actions, actor position/orientation, timing needed for motion, height/collision queries, camera selection, resource activation and scene changes. Automatic background spawning may be deferred only through the explicit prototype flag; full NPC activation remains separate acceptance. A visual stand-in does not authorize replacing these with guessed movement or teleportation.
3. Keep SDL and drawing primitives in the host backend. Read world state through the snapshot boundary; mirror any reconstructed control-flow repairs or mode gates in `GenerateRecon.js`.
4. Reuse Step 08 Tasks 01/05/06 for action/pose/placement inputs and remaining Step 03 for actual movement/camera proofs. Pull basic locomotion and view-boundary tests forward; do not wait for every NPC, combat control or original mesh.

## Prioritized Work

| Slice | Deliverable | Acceptance / dependency |
| --- | --- | --- |
| G1 — Proxy visualization and render boundary | Project cylinder rings/sides from the existing cue camera math; identify and gate only visual mesh/restore work. Show actor ID, world position, source-confirmed facing, camera slot and readiness/failure state. | A drawing fixture validates projection/scale/clipping; enabling visualization alone leaves simulation state unchanged. Keep the real update loop running. |
| G2 — Minimum surface support | Fix [Step 08 Task 12](../step-08/tasks/task-12-recover-directdraw-surface-lock.md) for any Lock/Unlock calls still required by the proxy route. | First audit whether a clean-background, full-frame proxy composition removes the mesh dirty-copy dependency. If it does, defer the full-render provider; otherwise implement the smallest valid surface storage/pitch/ownership. Never silently ignore a required copy. |
| G3 — Real gameplay handoff | Make the required action/keyframe/script path survive the pedestal sequence and reach actual control readiness at a source-consistent Joe position. | No action-error modal, frozen empty action slot or unrelated initial rooftop selection. Trace `FUN_0044f508` case 0x75 / `DAT_0047a76c`, actor ownership and coordinates; do not just force the flag clear. Step 08 Tasks 01/05/06 remain the source owners. |
| G4 — Player locomotion and floor queries | Up/Down produce real forward/backward displacement; Left/Right turn; releasing input stops the relevant movement. Check floor/stair height and a blocked boundary. | Input → action/motion → coordinates/orientation → projected cylinder must agree. Recover root motion or logical pose inputs where necessary; no second host-side movement system. Collision claims require their own query/state evidence. |
| G5 — View and scene traversal | Walk from the courtyard into at least one adjacent view and back, loading/presenting the correct background and camera while retaining the player. | At least two genuine view-boundary crossings; camera changes must follow recovered queries/resources, with no permanent scene-175 lock. Distinguish camera slot from script scene-resource identity. |
| G6 — Other actors and minimum interaction | Render cylinders for actual instantiated NPCs/objects and recover activation needed on the traversal route; then one relevant interaction. | Start with Joe alone if NPC recovery does not block the route. Add the two reference creatures when their identities/lifetimes are recovered; do not manufacture instances from the video. Full combat/AI/inventory can follow. |
| G7 — Repeatable manual and automated loop | A documented launch, input/release traces, phase-aware startup and bounded traversal captures, plus an existing restart/menu route where usable. | Manual SDL run and corresponding state/presentation packets; Debug and ASan exercise the relevant path. A timeout before the path or a key latch is insufficient. |

G1 is implemented and [Task 01](tasks/task-01-recover-action-event-node-removal.md) closes event-node removal. [Task 03](tasks/task-03-recover-hosted-floor-byte-reads.md) restores courtyard floor decoding; [Task 04](tasks/task-04-recover-npc-spawn-query-inputs.md) implements bounded NPC inputs with full activation deferred. The terminal root-pose repair restores the event-link writer and matching Debug/ASan release chains. [Task 02](tasks/task-02-recover-post-intro-placement-and-motion-queries.md) still owns complete motion/control acceptance, ahead of meshes/NPC fidelity.

The [player-input continuation](../../../../journal/entries/player-motion-inputs-2026-10-16.md) supplies representation 12 and live keyboard reads. [Task 05](tasks/task-05-recover-player-motion-vector-ownership.md) now recovers action vectors and world queries with original-code comparisons. The corrected extended-arrow probe demonstrates Debug Up displacement, Left/Right turning and release stopping; Down displacement remains unverified. ASan reaches Up displacement, then gravity writes height -16000 after release. [Task 06](tasks/task-06-recover-release-gravity-query-ownership.md) is next. See the [motion-query evidence](../../../../journal/entries/player-motion-query-2026-10-16.md); full sanitizer/traversal acceptance remains open.

The [2026-10-19 idle-action repair](../../../../journal/entries/player-idle-action-2026-10-19.md) closes Task 06's observed ASan height failure. A release caller passed the representation pointer as an action ID and loaded a FAN that replaced the floor grid; the caller now reads the original queued action word at +0x162. Debug/ASan complete all arrow phases and both combined turn/Up probes at height 3328/camera 175. Up release executes a queued action with further displacement, superseding the earlier immediate-stop result. Task 02 now owns settled stopping, Down displacement and real-map collision/traversal. No 60-second or full experimental sanitizer acceptance is claimed.

The [SDL release/clock/target-facing continuation](../../../../journal/entries/player-release-and-spin-2026-10-19.md) follows the user's manual spinning/crash report. Actual SDL key-up now clears the same held table as key-down, the simulation again waits for a clock change, and `0x42ed6c` retains its original actor/time/range inputs. Original-code and bridge fixtures pass normally/ASan. Actual SDL turn-release-then-move probes complete in both builds; turn release stops turning at rest, and longer Down presses now displace. Up/Down still produce motion-query steering with Left/Right clear. [Task 07](tasks/task-07-recover-motion-query-steering.md) owns the remaining motion-query steering; Task 02 retains real-map traversal/full sanitizer acceptance; do not call the circling report fully resolved yet. Four final builds, generator parity and baseline wrapper/eight-arrow/SDL requester checks pass.

The [courtyard-camera continuation](../../../../journal/entries/courtyard-camera-traversal-2026-10-19.md) implements [Task 08](tasks/task-08-recover-courtyard-camera-transitions.md). Ordinary camera changes no longer treat a camera slot as a script-resource ID, the cached-camera word reads its real dword, and terrain scripts receive their code record/current actor. Original-code comparisons pass normally/ASan. Actual SDL Debug and ASan both complete **175 → 166 → 175**, retain Joe and wait/modal zero, release all keys and load the new background. Debug also explores camera 167. ASan takes a different movement route and returns to another location in camera 175; identical steering, exact retracing, complete collisions and 60-second/full experimental ASan acceptance remain open under Tasks 02/07. The user reports input now works and prioritizes exploration. Four builds, generator parity and baseline regressions pass.

## Implemented Slice — 2026-10-14

The [F5 correction and continuous captures](../../../../journal/entries/f5-diagnostic-route-2026-10-14.md) supersede the earlier debugger-stopped proof. Projected wireframes use actual validated actor state and approximate radius 256/height 1024, clipping, a local +Z axis and no background occlusion. Control remains explicitly unverified.

Matching F5 launch from the repository root:

```sh
E2R_ACTION_INDEX_PROBE=1 E2R_ACTOR_CYLINDERS=1 E2R_PROXY_MESH_BYPASS=1 \
  E2R_DEFER_BACKGROUND_SPAWNS=1 \
  ./build/Debug/clang21-i386-sdl/e2recomp --run-recon
```

Select the SDL i386 Debug preset and restart F5. Its launch now includes these flags; previously it enabled crosses only. Bare terminal launches keep flags off and can still reach the action-384 modal. The expanded 24,000-byte script-name set is gated with the recovered action route to retain the earlier baseline during recovery.

The [2026-10-14 continuous packet](../../../../journal/entries/courtyard-floor-decoder-2026-10-14.md) shows Joe `9988,3328,-17408`, depth 4739, camera 175, wait 0/modal 0 after release. Restored palette/floor data remove the initial forest fallback; the panel reports deferred background spawning. The subsequent root-pose/input/query continuations above supersede that packet's immobile representation-67 result. No traversal or full runtime sanitizer acceptance is claimed.

## Implementation Evidence And Pitfalls

- `E2Recomp/native/e2recomp_native_main.c:E2R_GetActorCues` already projects six diagnostic points per actor through a private recovered camera matrix. Extend its read-only snapshot to project top/bottom rings and any source-confirmed orientation data; do not repair game state while reading a cue.
- `E2Recomp/platform/e2recomp_host_backend_sdl.c:e2r_sdl_actor_cues` already draws onto the freshly converted RGB presentation surface. It is a small candidate for wireframe or simply filled cylinders, with perspective scaling, near-plane handling and explicit approximate dimensions. Fixed-size screen icons are insufficient for movement/camera testing.
- `FUN_00424e44` is now gated at a source-audited terminal polygon boundary. Earlier mesh transforms, other render leaves and dirty restoration remain active. Full background/restore and surface dependency auditing continues as the route reaches those calls. Fresh RGB conversion prevents host-cylinder trails without driving gameplay from draw bookkeeping.
- **Do not skip all of `FUN_004211c8`.** It also calls camera selection `FUN_0044c224`, actor updates and other shared stages before dirty copying. Classify effects of the bypass at an earlier/later narrow boundary with state comparisons.
- Root motion, action timing/events, logical pose transforms or attachment data can affect gameplay even when no animated mesh is shown. Recover the minimal required subset; "no visible animation" is not evidence that all animation/action evaluation can be disabled.
- The bare baseline Joe has camera depth -3062. The current diagnostic route keeps Joe visible in the courtyard after release; bounded Debug/ASan locomotion survives release, with settled stopping and full traversal still open. Do not clamp the marker into the viewport or infer coordinates from the reference pixels.
- Task 12 is a precise known failure for the full-render route. It is not yet proven mandatory for every possible proxy renderer. Keep the independent compatibility task rather than making all DirectDraw/blit/flip fidelity a blanket prerequisite.

## Lowest-Hanging Fruit

| Candidate | Expected relative effort | Practical benefit / limit |
| --- | --- | --- |
| Cylinders and state labels using existing cues | Small | Visualizes live positions without original model/lighting recovery. Does not fix actions, placement or motion. |
| Stage/readiness and position-delta logging | Small | Separates an input latch, blocked action, wrong camera, no movement and projection failure. Reuses existing traces/packets. |
| Narrow model-render gate | Small to medium, audit required | Can remove a large rendering dependency from the gameplay investigation. Must retain logic/root-motion work and handle the clean background. |
| Minimal valid DirectDraw Lock/Unlock provider | Small to medium, ownership audit required | Fixes the concrete 0/0 destination on the current route. Broad surface fidelity is larger and can wait if the proxy route avoids it. |
| Reuse the known intro skips and restart path | Small once readiness is reliable | Faster reproducible attempts without guessed post-intro state or a new save format. Actual logo/horseback taps and diagnostic delay overrides are distinct test routes. |

The action-to-motion handoff, correct floor/collision results and scene/resource ownership have greater uncertainty. They remain real reconstruction work even with cylinders; no reliable completion time is inferred from this code review.

## Temporary Sacrifices

1. Cylinders replace meshes, skinning, visible limb animation, shadows and original shading in the explicit diagnostic mode. Dimensions are diagnostic until recovered bounds are available.
2. Background occlusion can initially remain unavailable and clearly marked, as in current cues. Cylinder size/visual overlap must not become collision authority.
3. Exact intro presentation, creature models, sound, polished menus and save/load may remain incomplete. Use legitimate skip/action transitions; do not bypass missing logical progression by repeatedly writing final state.
4. Keep action-index/pool repairs opt-in until their behavioral coverage justifies promotion. The diagnostic mode can require the recovered route without changing the default baseline globally.
5. Remove/disable proxy substitution when the original renderer becomes usable; retain it as a developer diagnostic if useful. Original-render fidelity remains a separate acceptance claim.

## Acceptance Criteria

1. Joe's cylinder is visibly tied to the actual player state after genuine control readiness; arrow press/release changes the appropriate coordinates/orientation and rendered output.
2. The initial gameplay position/view follows recovered actor/query state and the reference courtyard, without a permanent camera guard or an error modal standing in for successful progression.
3. Traversal crosses a real view boundary and returns with coherent background, projection, actor ownership and position continuity. Note any unverified collision/interaction separately.
4. The mode survives a bounded session of at least 60 seconds after control readiness and the traversal test, with no required-path crash or sanitizer error. Timing starts at the observed phase, not application launch.
5. Default behavior remains separately testable; generator reproduction and relevant baseline checks pass. A proxy result does not close original model/animation acceptance.

## Verification

Use actor state and synchronized selected-game/SDL/window packets to distinguish raw-frame content from the proxy presentation. Record camera slot, resource owner, action slot/progress, control flag, position/orientation, queries and input release. `scripts/check-e2-actor-cylinders.py` now verifies real projection/snapshot/backend code with synthetic actors, normally and under ASan. Polygon checks verify bypass-off original routing and bypass-on omission without polygon mutation. `scripts/probe-e2-player-motion.py` now captures real press/release state and presentation, with correct extended-arrow metadata. Its completion is separate from behavioral acceptance. Traversal and sustained-time assertions still need implementation; keep these separate from the latch matrix.

Startup automation must model separate logo taps and horseback skip, release those taps, then wait through pedestal/action readiness. The user skipped all three logos and shortened the horseback intro in the reference recording. A diagnostic zero-logo-delay route is useful for crash probes but does not validate key-driven skipping or natural timings.

## Later Work

After diagnostic locomotion/traversal: required NPC activation and interaction; additional scene/resource variants and combat/inventory state; stable runtime cadence; original model/animation/rendering fidelity; sound/music; functional save/load; broader control/menu polish; optimized-build recovery, packaging and portability. Reorder only when one of these blocks the current playable milestone. The 64-bit and optimized runtimes are not current prerequisites.

## Usage Budget

Implement one bounded slice/failure family at a time. Preserve the existing baseline and split newly exposed action/query/compatibility errors. The cylinder and F5/script slices are implemented; Task 01 closes node removal. Task 03 closes hosted floor-byte decoding; Task 04 splits NPC input recovery/full activation. Task 02 owns player motion/control. Task 05 recovers action vectors and world queries with original-code coverage; Task 06 closes the observed release-height failure at its upstream queued-action caller. Task 02 retains motion-query steering, straight forward/backward control, collision and traversal acceptance. Automatic background spawning is explicitly deferred for the Joe-first prototype. Do not expand into every remaining graphics/helper family at once.

## Change Log

### 2026-10-19

Recovered SDL key-release table selection, removed the clock poll-count escape that caused zero-time turning, and restored target-facing actor/time/range and angle inputs at the user's reported crash. New fixtures and actual SDL replay pass in Debug/ASan; no-input turn release settles, Down displacement is now observed, and remaining motion-query steering stays open. See the [release/spin journal](../../../../journal/entries/player-release-and-spin-2026-10-19.md).

Recovered the queued idle-action ID from original +0x162, preventing a wrong FAN load from replacing the live floor grid on release. The 1,440-case caller fixture passes normally/ASan; both arrow probes and all four combined-input probes retain valid height. Four builds, baseline checks and generator parity pass. Up release has additional queued-action displacement; stopping, Down, collision, traversal and full experimental ASan acceptance remain open. See the [idle-action journal](../../../../journal/entries/player-idle-action-2026-10-19.md).

### 2026-10-16

Reproduced the user's Up-after-rotation crash and repaired two forward/turn callers passing direction byte 1 as the actor. Original-code comparisons and Debug combined-input movement/release pass; ASan passes the repaired calls then retains its separate bad-height release frontier. See the [turn-caller journal](../../../../journal/entries/player-turn-callers-2026-10-16.md).

Recovered action motion/vector/query ownership and compared original code. The corrected extended-arrow probe shows Debug Up displacement, Left/Right turning and release stopping; ASan reaches Up, then gravity writes height -16000 on release. [Task 06](tasks/task-06-recover-release-gravity-query-ownership.md) splits that frontier. Down displacement/traversal/full ASan remain open. See the [motion-query journal](../../../../journal/entries/player-motion-query-2026-10-16.md). Baseline checks and generator parity pass.

Recovered Joe's representation selector and live scan-code reads with 10,368/256 original-code comparison cases. Both runtimes now enter the movement query after Up and expose lost vector/output ownership in `0x4272a8`; split Task 05. Baseline checks pass; actual motion remains unproven.

Recovered root-pose matrix and previous-position destinations from the watched ASan event-link writer. Original-code comparisons, matching Debug/ASan release chains, four builds, parity, wrapper, arrow and SDL modal checks pass. Motion remains unresolved with representation 67 bound; full runtime sanitizer/traversal acceptance stays open.

### 2026-10-14

1. Added the user's cylinder-first gameplay priority and moved basic locomotion/view traversal ahead of full model, animation and NPC recovery. Recorded reusable code, conditional surface dependency, verification and limits.
2. Implemented cylinder presentation/state snapshots and a narrow polygon gate; fixtures, builds, parity and baseline checks pass. A real capture shows Joe during the pedestal action, then event 0x3f faults before readiness; split its node-removal contract into Task 01.

3. Aligned F5 with the three diagnostic flags; recovered event-node, retained action/actor and script inputs. Continuous Debug captures advance past the action error to wait 0 but reveal invalid post-intro height and no locomotion; activated Task 02. Kept the expanded script set gated and recorded separate ASan failure/physical editor acceptance limits.

4. Restored palette fades/frame caller inputs; recovered experimental unsigned descriptor selection, no-view resource 7 and actor deactivation. Original-x86 comparisons and baseline checks pass; split the remaining no-floor release/menu and ASan query inputs into Task 02.

5. Restored hosted floor reads and source-backed NPC query/range/placement contracts; added explicit background-spawn deferral with on-screen status. Debug remains in the courtyard after release; movement and terminal ASan event ownership stay open.
