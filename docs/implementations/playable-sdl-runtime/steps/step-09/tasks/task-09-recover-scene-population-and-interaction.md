# Recover Scene Population And Interaction

Status: next priority; manual castle locomotion/collision confirmed
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-19

## Goal

Restore original scene objects and NPCs needed for exploration and basic interaction while retaining cylinder presentation and Joe's working movement/camera transitions. Begin with one verified original resource and behavior; original models and full combat remain later work.

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
