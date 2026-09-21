# Project Actor Cues Into The Scene

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-15

## Goal

Replace the X/Z inset with primitives projected from actual actor positions through the game's camera arithmetic.

## Scope

1. Recover trigonometry, fixed-point rotations, vector transform and perspective from original code.
2. Draw a ground cross, upright and label in SDL presentation for each valid visible actor.
3. Report behind-camera/offscreen/unavailable data honestly and preserve game pixels and actor state.

## Implementation And Evidence

Implemented in the reconstructed math helpers, native snapshot and SDL backend, with generator mirrors. See the [projection and recovery journal](../../../../../journal/entries/actor-cues-and-projection-2026-09-15.md) for original addresses, formulas, commands and observed state.

The default camera-175 packet contains only Joe at `12800,256,-3584`, camera depth -3062. Thus the expected settled status is **0 VISIBLE / 1 BEHIND**. No enemy instances or credible pedestal positions have been recovered. The cue is a ground cross plus a 1024-unit upright, with no environment occlusion or recovered character bounds.

## Acceptance And Verification

1. Original-machine-code arithmetic comparison: passed 4,096 cases plus in-place transforms and event metadata comparison.
2. Default SDL capture: passed, indexed frame unchanged (`321e33d6`), one behind-camera Joe reported.
3. Synthetic presentation-only fixture: visible cyan/amber primitives inspected; game pixels unchanged. This does not establish character placement.
4. Generator parity and four Debug builds pass; default isolated Debug/ASan wrapper passes. The final isolated arrow-control matrix passes all eight Debug/ASan rows.
5. Manual F5 confirmation of the grid replacement and crash-free default route: pending. Correctly placed living actors remain Tasks 02/05/03, not a completed cue acceptance claim.

## Review State

1. Implementation state: implemented; manual verification pending.
2. Next source work: Task 02 geometry inputs, then Task 05/01 placement/action validation and Task 03 child-resource recovery.
