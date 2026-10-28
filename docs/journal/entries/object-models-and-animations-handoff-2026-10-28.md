# Object models and animations handoff — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Selection and scope

After HUD recovery and the recording repair, the user selected original models
and animations for **items, weapons, doors and acid pools** as the next work and
asked to park it in handoff/documentation for a new context. The next sequence
is **object models/animations → game sounds → music**. No runtime implementation
or new gameplay acceptance is claimed by this documentation change.

[Step 12](../../implementations/playable-sdl-runtime/steps/step-12/step-12-recover-object-models-and-animations.md)
owns the selected scope and verification boundaries. Its
[first task](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-01-recover-object-rendering-and-animation-contracts.md)
starts with original resource/owner/primitive/material/action mapping and the
smallest bounded object rendering repair. Acid-pool identity, scene and actual
rendering/animation method remain unmapped; neither water rendering nor an
illustrative marker establishes that contract.

## Observed baseline

Branch `linux-e2-reconstructed-runtime`, HEAD
`a2a6043ed2def4ca6babf9cc8a6ef45587e0431b`. The user committed HUD recovery in
`44ebf8f` and chunked recording/streaming replay in `a2a6043`. The worktree was
clean when this handoff began. Persistence/menu commits remain `35be1cc` and
`22c36a3`; historical release tags are unchanged by this work.

Read the [HUD journal](original-hud-recovery-2026-10-28.md) and
[recording journal](chunked-recording-and-streaming-replay-2026-10-28.md) for their
fresh evidence and limits. Keep accepted character rendering, default/F1/F2 HUD,
menu/persistence behavior, save protection and investigation tooling intact.
Do not overwrite occupied/installed saves or quick-save slot 9. Native agent
probes remain bounded, isolated and recording-off except explicit replay tests;
human investigation retains the single Ecstatica Recompiled F5 launch.

## Source clues and next context

The existing character-selection helper `E2R_UseProxyMesh` leaves object/equipment
fallbacks in place. Inspect `FUN_00424cbc`, polygon dispatch
`FUN_00424e44 → FUN_00433d30`, alternate `FUN_00425018`/`FUN_00425538`, pose
`FUN_00423858`, and redraw `FUN_004211c8`, together with their generator mirrors.
These are current source anchors, not a newly recovered acid-pool/object contract.
The [enemy journal](enemy-model-and-animation-2026-10-27.md) retains the earlier
unfinished polygon/surface failure and class-selection limits. Recover original
inputs rather than globally disabling bypasses or guessing a valid surface.

The first task retains these clues, prerequisite journals and concrete acceptance
checks. Use original disassembly/Ghidra and bounded `scripts/e2_original.py`
comparisons. Mirror reconstructed repairs in `GenerateRecon.js`, verify all four
generated artifacts independently, and record fresh Debug/ASan pixels/animations
and affected builds. Remove a class's fallback only after its original pixels
are qualified; keep gameplay scripts, collision, damage and timing independent.

## Documentation and verification

The user explicitly requested the handoff update. Its structural reason is that
the resume links still selected HUD, while object models/animations are now the
next continuation. Updated README navigation, HANDOFF resume links, capabilities,
the active implementation/roadmap, milestones and the prior HUD step pointer.
Durable working rules remain owned by HANDOFF; changing baseline and rendering
acceptance remain owned by Step 12 and its task.

Documentation-tree update/check and whitespace validation are the relevant
checks for this documentation-only handoff. Historical runtime evidence is linked
without rerunning or promoting it to object-rendering acceptance. No executable,
asset, save, launch, commit, push or tag action is performed.
