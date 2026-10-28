# Original HUD handoff — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 11: recover original HUD](../../implementations/playable-sdl-runtime/steps/step-11/step-11-recover-original-hud.md).

The user selects original HUD recovery, including the player life bar, before
sounds. Default presentation should use original HUD with the current debug
overlay off; F1 selects original HUD and F2 selects the existing debug overlay.
The requested work for this context is documentation, handoff and a continuation
message. Implementation is assigned to the next context, already authorized to
proceed. Revised sequence: **original HUD → game sounds → music**.

The worktree is clean at inspection, on `linux-e2-reconstructed-runtime`, HEAD
`22c36a3f70bef9467e62299376905cbb5552dd71`. The user committed functional
persistence in `35be1cc` and menu/layout refinements in `22c36a3`. Existing
v0.1.0/v0.2.0 tags remain unchanged; this inspection makes no claim about pushing
the newer commits. This handoff adds uncommitted documentation only.

Read-only source inspection locates the current SDL overlay in
`e2r_sdl_actor_cues` / `e2r_cue_player_status`, painted after indexed-page
conversion. Its enablement is tied to actor-cue/cylinder flags, while original
2D graphics are omitted by `E2R_PROXY_MESH_BYPASS` in `FUN_004555b0` and script
graphic leaves. `FUN_004559bc` is the original HUD update entry, with intro and
actor-0 gating visible in the decompiled body. Graphic helpers, icon-name
cleanup, icon-page loading, original HUD/intro reference and F1–F12 mapping are
inspection leads captured in the [first task](../../implementations/playable-sdl-runtime/steps/step-11/tasks/task-01-recover-hud-and-display-mode-ownership.md).
Their argument/data/page contracts have not been recovered by this handoff.

The next context must recover original behavior instead of replacing the debug
health text with another host-drawn approximation. Separate display selection
from game state, object/equipment fallback rendering, character meshes, replay
and inspection. Preserve the accepted save/load paths and installed saves. The
step records default/F1/F2 behavior, first investigation, bounded original/native
verification, four-artifact parity and remaining rendering/gameplay limits.

No runtime, input bindings, launch settings or tests change in this turn. F1/F2
selection and default original HUD are requested future behavior, not currently
implemented features. Only documentation/tree/whitespace verification applies to
this handoff; historical runtime results do not establish HUD acceptance.

Verification: `python3 scripts/check-docs-tree.py --update`, the subsequent check
without `--update` (**270** connected Markdown documents), and `git diff --check`
pass. The final changed/new file inventory contains Markdown only. No builds or
runtime probes are claimed for this documentation-only assignment.
