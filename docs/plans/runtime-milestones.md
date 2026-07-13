# Runtime Milestones

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-07-13

## Goal

Define the meaningful runtime milestones for running the decompiled Ecstatica II engine on Linux, ordered by expected project gain and unlock value. The first phase has reached the reconstructed main-loop entry; the next phase is about making that loop durable, visible, controllable, and useful for gameplay investigation.

## Recommended Order

Completed first-phase milestones:

1. Recover the lost-register and calling-convention cluster around startup/menu initialization crashes.
2. Load the first real resource file from `/home/rgrabowski/Games/Ecstatica2/`.
3. Create a visible Linux-hosted window or rendering surface.
4. Initialize enough graphics and audio stubs to reach menu or title logic.
5. Reach the main-loop entry point.

Next recommended milestones:

6. Stabilize the post-main-loop-entry configuration/file frontier, starting with the `"e_config"` crash through `FUN_0046055c`.
7. Prove a sustained loop heartbeat by running several consecutive loop iterations without crashing or corrupting process state.
8. Present an inspectable title/menu frame in the Linux window from reconstructed surface, palette, and blit state.
9. Wire host input and the Win32-style message pump far enough to navigate the title/menu path.
10. Reach a first controllable gameplay scene using original Ecstatica II data.
11. Harden the runtime loop with repeatable debug and ASan checks, targeted crash-frontier probes, and documented temporary shims.

## Rationale

The highest-gain next move is still not another defensive no-op. Reaching `thunk_FUN_004620db` proves the startup path can cross the main-loop threshold, but the immediate post-thunk `EIP=0xffffffff` crash while opening `"e_config"` shows that file/CRT callback recovery remains a durable blocker class.

A sustained loop heartbeat comes before visual correctness because it gives a stable harness for rendering, input, audio, and gameplay fixes. Once the loop can survive multiple iterations, visible frames and input become higher-value than further one-off startup repairs.

The first playable scene is the next major product-shaped proof point: it validates enough resource loading, renderer state, input, timing, and engine control flow to guide later accuracy work.

## Success Criteria

1. Each milestone has a GDB or runtime observation proving it was reached.
2. Each crash frontier change is recorded in the project journal.
3. Each reconstructed C fix that must survive regeneration is mirrored in `GenerateRecon.js`.
4. Temporary shims are documented with the condition that should retire or replace them.
5. Debug and ASan builds remain available for each completed milestone.

## Change Log

### 2026-07-13

1. Created milestone plan.
2. Marked the first five milestones complete after reaching `FUN_00410a48 -> thunk_FUN_004620db`.
3. Added the next runtime milestone sequence from the post-main-loop-entry `"e_config"` crash through first controllable gameplay.
