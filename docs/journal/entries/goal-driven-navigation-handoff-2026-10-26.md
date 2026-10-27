# Regression 05 investigation and navigator handoff — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Goal-driven regression navigation](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Runtime owner: [Population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The user reports that live spawning, moving enemies and obstructed traversal make
combat/damage checks unpredictable. They propose a goal-driven navigator that
can avoid obstacles, detect stuck movement and recognize interaction requirements.
They request a written handoff tasking the next context with that approach.
This continuation inspects existing artifacts and writes documentation only;
it does not implement navigation, repair runtime behavior or rerun gameplay.

Latest inspected evidence:
`.tmp/gameplay-suite/run_20261026_135535_282152/`. The run selected block
`unarmed`, shared execution, visible Debug/Wayland plus headless ASan, two
configuration workers, recording **off**. It reports **12 PASS / 2 FAIL** in
**173.27 seconds**. Both configurations pass startup/movement, eight unarmed
attack combinations, workshop traversal and smith **602** contact **100→80**.
Both unarmed-contact processes exit natively **0** with complete inspection.
Sword pickup is deliberately absent from this block; block **06** covers it.

Both receive-damage checks fail with Joe at health **100**. Their inspections
remain incomplete after assertion failure. No native damage-runtime crash is
demonstrated. The source hashes for the gameplay steps, suite, profile and probe
match current files at investigation time.

`Journey.damage()` runs **98** historical transitions over **2506** updates,
including **815** holding Ctrl, then chases guards **284/293** using only X/Z
distance/heading. Guard health falls **100→60** for 293 in Debug and **100→40**
for 284 in ASan while Joe stays healthy. The recorded sequence does not reliably
establish a receive-hit encounter; these health observations do not attribute
every hit's source. ASan ends with Joe at height **4096** and guard 293 at
**3328**, illustrating why planar pursuit is insufficient.

The handoff specifies a bounded observation → planning → SDL input → progress
verification loop, starting with a receive-one-hit objective. It preserves
checkpoint assertions, original state/physics/AI, shared-journey execution,
failure evidence and separate controlled/live coverage. A failed approach must
leave unexercised combat assertions BLOCKED while failing the journey through
its setup/lifecycle result. Unknown blockers cannot be guessed progression-locked;
that diagnosis needs original script/state evidence. A targeted encounter fixture
is a possible complement, not implemented or accepted by this investigation.

All pre-existing implementation work is staged at handoff, HEAD `39b0f41`.
New documentation remains unstaged. No staging, commit or push is performed.
Existing animation-name generator drift and other runtime faults remain open;
the full **184**-case suite is not rerun. The owning task records implementation
scope, source locations, validation criteria and the first bounded next action.
