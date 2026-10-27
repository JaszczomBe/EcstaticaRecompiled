# Activate Scene-Backed Children and Recover Enemy Animation

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
<!-- /docs-tree:parent -->

Status: original enemy ellipsoid bodies/poses enabled; bounded validation and visual follow-ups
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-27

## Goal

Instantiate and render scene 175’s dynamic children using their original resource semantics.

## Scope

1. Map scene/rep-backed children through scene activation and allocation.
2. Recover the required resource lookup and lifetime behavior.
3. Verify child instances and visible output without regressing Joe or scene transitions.

## Out Of Scope

1. Manufacturing ordinary actor archive entries for scene-backed resources.
2. Full enemy AI/combat, broad archive scanning, or unsupported object substitutions.

## Current enemy recovery — 2026-10-27

The user accepted the corrected player and requested enemy animation next,
ahead of save/load. Existing original actors now render through the recovered
player bone/camera/ellipsoid path with `E2R_NPC_MESH=1` in F5 and suite journeys.
The selector resolves node ownership at `+0x22`, reuses the existing original
name/representation/flag presentation category, and retains character identity
through death. This is host presentation selection, not a replacement AI or a
complete resource taxonomy. Original actions, timing, movement and damage remain
unchanged. Full poses run for selected character trees; their rounded primitives
are rasterized into the physical game pages and their diagnostic shapes hidden.
Objects/equipment remain diagnostic; NPC polygon/box leaves and the original HUD
remain bypassed. Enabling NPC polygons exposed an unfinished flat-polygon surface
input, so that independent raster family is deferred rather than guarded with a
guessed surface pointer.

Current live ASan evidence includes pedestal actors **284/293**, their **52/53**
nodes and **12** distinct poses each, restrained/released presentation and a
five-second input-release observation. Guard 284's actual attack reduces Joe's
health **100 → 95**, followed by a normal menu exit. Workshop samples contain
smith 602's **56-node** body, changing poses, actual health loss and final corpse.
Broader combat attempts retain navigation, attack, bitmap-pool and kill-attribution
failures; they do not establish passing whole-game combat. The
[journal](../../../../../journal/entries/enemy-model-and-animation-2026-10-27.md)
owns exact routes, final checks, original-code evidence and retained failures.

Original scene identities/activation established below remain valid; this pass
restores presentation of those existing actors. It does not manufacture missing
children or resolve the historical 319/322/318 association. Human enemy visual
review, exhaustive species/actions, equipment and polygon/box recovery remain
separate. Game save/load follows this enemy milestone, then sounds and music.

## Subsequent human play

The user likes the recovered enemies and reports two gameplay failures during a
short run. [Task 09](../../step-09/tasks/task-09-recover-scene-population-and-interaction.md)
and the [follow-up journal](../../../../../journal/entries/enemy-play-crash-and-dropped-potion-2026-10-27.md)
own the false action-index/bitmap crash and dropped-potion name/consumption repair.
These do not require reverting character animation recovery.

The user then accepted those repairs and reached the top of the tower.
The [tower journal](../../../../../journal/entries/tower-actor-eviction-crash-2026-10-27.md)
records the subsequent actor-eviction repair and remaining replay/human limits.
Character recovery and these follow-ups are committed in **v0.2.0**. The selected
next milestone is [Step 10 functional game save/load](../../step-10/step-10-recover-game-save-load.md);
exhaustive enemy animation, equipment and other fidelity follow-ups stay separate.

## Implementation Notes

Validate after Tasks 01/02 and Task 05 placement. **Correction from 2026-09-15:** camera slot 175 is not script scene-resource ID 175. The historical lookup of scene record `0xaba3a4` was not sufficient to associate it with the pedestal scene. That record lists children 319/sword2cv, 322/burkrt, and 318/sword2. Their ordinary actor offsets are absent; scene/rep offsets exist:

| Child | Scene offset | Rep offset |
| --- | --- | --- |
| 319 | `0x216ae` | `0x890d46` |
| 322 | `0x218dc` | `0x891052` |
| 318 | `0x215ec` | `0x890bc0` |

All three have `actor=0` in the historical audit packet, but they are not established pedestal enemies. Activation tracing instead identifies `Start_sc` resource 0 with children 261 (`spide_w3`, hidden), 0 (Joe), and 3551 (secondary reference 695 / `wdpile2`). The settled default Joe has no scene owner at `+0x132`; the corrected sidecar reports that absence instead of inferring ownership from the camera. Establish the actual post-intro scene resource and expected enemy identities first. Recover the meaning of the child and `word2` references from original scene activation; do not assume one visible enemy per listed child. Inspect `FUN_004523f8`, `FUN_00452140`, and `FUN_004533ac` with their callers. Preserve aligned archive indexing and counts (`actors=81 reps=389 scenes=1205`) unless source evidence justifies a specific change.

## 2026-10-19 Pedestal Identity Correction

The actual pair is established by original `St_gobsc` resource 101, view 175: `gob3` (284) and `gob3b` (293). Step 09 now loads their original tracks and presents cylinders before/after Joe's release. Original global names also identify Start_sc child 261 as `stok1`; the historical `spide_w3` label came from a malformed hosted actor-name pool. The earlier 319/322/318 association remains unproven. See the [guard evidence](../../../../../journal/entries/pedestal-guard-activation-2026-10-19.md). This resolves the pair's identity/diagnostic presence; original articulated-model rendering and full acceptance of this task remain open.

## Acceptance Criteria

1. Source evidence establishes child resource roles and instantiation/lifetime rules.
2. Expected instances enter appropriate update/draw lists and appear in the selected framebuffer.
3. Manual reference comparison accounts for expected living enemies/objects and any legitimate hidden children.
4. Joe remains visible/controllable; generated parity and relevant debug/ASan/SDL regressions pass.

## Original-Game Instance Evidence — 2026-10-14

The [recording/contact sheet](../../../../../journal/entries/original-game-reference-2026-10-14.md) shows **two green creatures** on opposite sides of the pedestal while Joe is restrained. They change pose and move at the stairs/foreground, continue through release, and remain present after HUD entry. This establishes expected visible non-player instances for the recorded sequence; their exact species, resource IDs, scripted/AI ownership and instantiation triggers remain unproven. Do not equate them with 319/322/318 or with the currently traced `Start_sc` child IDs without source evidence.

Trace both instances before and after the cinematic handoff, rather than only checking whether children appear after gameplay starts. Use their side/foreground positions and movement as visual targets once Joe/action/placement prerequisites are stable. This historical reference predates the current enemy rendering pass.

## Verification

Compare actor census, scene-child resources, draw state, and synchronized game/SDL captures before and after activation. Run the default and opt-in scene-175 paths as applicable, then the control matrix and corrected wrapper. Record manual F5 results and the action-index promotion decision in the parent step before resuming Step 03.

## Review State

1. Planning state: agreed
2. Implementation state: original character ellipsoid bodies and bone poses enabled; original guard/attack and workshop evidence recorded.
3. Notes: player prerequisite accepted by the user; retain broad combat, polygon/equipment and human visual limits.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.
