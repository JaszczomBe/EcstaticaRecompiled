# Activate Scene-Backed Children

Status: planned
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-14

## Goal

Instantiate and render scene 175’s dynamic children using their original resource semantics.

## Scope

1. Map scene/rep-backed children through scene activation and allocation.
2. Recover the required resource lookup and lifetime behavior.
3. Verify child instances and visible output without regressing Joe or scene transitions.

## Out Of Scope

1. Manufacturing ordinary actor archive entries for scene-backed resources.
2. Full enemy AI/combat, broad archive scanning, or unsupported object substitutions.

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

Trace both instances before and after the cinematic handoff, rather than only checking whether children appear after gameplay starts. Use their side/foreground positions and movement as visual targets once Joe/action/placement prerequisites are stable. This reference does not change the task's planned status.

## Verification

Compare actor census, scene-child resources, draw state, and synchronized game/SDL captures before and after activation. Run the default and opt-in scene-175 paths as applicable, then the control matrix and corrected wrapper. Record manual F5 results and the action-index promotion decision in the parent step before resuming Step 03.

## Review State

1. Planning state: agreed
2. Implementation state: not_started
3. Notes: Start after the dependency described above is satisfied.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.
