# Activate Scene-Backed Children

Status: planned
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

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

Validate after Tasks 01/02. Scene record `0xaba3a4` lists children 319/sword2cv, 322/burkrt, and 318/sword2. Their ordinary actor offsets are absent; scene/rep offsets exist:

| Child | Scene offset | Rep offset |
| --- | --- | --- |
| 319 | `0x216ae` | `0x890d46` |
| 322 | `0x218dc` | `0x891052` |
| 318 | `0x215ec` | `0x890bc0` |

All three have `actor=0` in the audit packet. Recover the meaning of the child and `word2` references from original scene activation; do not assume one visible enemy per listed child. Inspect `FUN_004523f8`, `FUN_00452140`, and `FUN_004533ac` with their callers. Preserve aligned archive indexing and counts (`actors=81 reps=389 scenes=1205`) unless source evidence justifies a specific change.

## Acceptance Criteria

1. Source evidence establishes child resource roles and instantiation/lifetime rules.
2. Expected instances enter appropriate update/draw lists and appear in the selected framebuffer.
3. Manual reference comparison accounts for expected living enemies/objects and any legitimate hidden children.
4. Joe remains visible/controllable; generated parity and relevant debug/ASan/SDL regressions pass.

## Verification

Compare actor census, scene-child resources, draw state, and synchronized game/SDL captures before and after activation. Run the default and opt-in scene-175 paths as applicable, then the control matrix and corrected wrapper. Record manual F5 results and the action-index promotion decision in the parent step before resuming Step 03.

## Review State

1. Planning state: agreed
2. Implementation state: not_started
3. Notes: Start after the dependency described above is satisfied.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.
