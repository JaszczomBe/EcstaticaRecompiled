# Runtime Milestones

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-07-14

## Goal

Define the meaningful runtime milestones for running the decompiled Ecstatica II engine on Linux, ordered by expected project gain and unlock value. The first phase has reached the reconstructed main-loop entry; the next phase is about making that loop durable, visible, controllable, and useful for gameplay investigation.

Linux is the proving ground, not the final portability abstraction. The reconstructed game code should stay original-shaped for future reverse engineering and modding, while host-specific behavior is isolated behind Win32, DirectDraw, DirectSound, and CRT compatibility boundaries that can later be backed by SDL or another portable host library.

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
8. Present an inspectable title/menu frame through the compatibility renderer, using reconstructed surface, palette, and blit state while keeping host presentation replaceable.
9. Wire host input into the reconstructed Win32-style message pump far enough to navigate the title/menu path.
10. Reach a first controllable gameplay scene using original Ecstatica II data.
11. Harden the runtime loop with repeatable debug and ASan checks, targeted crash-frontier probes, and documented temporary shims.
12. Introduce a backend-neutral host boundary for window, input, timing, presentation, and audio so the current Linux/X11 scaffolding can be replaced without changing reconstructed game logic.
13. Add an SDL-backed host implementation once the runtime has a stable loop, inspectable frame, and understood DirectDraw/DirectSound compatibility needs.

## Rationale

The highest-gain next move is still not another defensive no-op. Reaching `thunk_FUN_004620db` proves the startup path can cross the main-loop threshold, but the immediate post-thunk `EIP=0xffffffff` crash while opening `"e_config"` shows that file/CRT callback recovery remains a durable blocker class.

A sustained loop heartbeat comes before visual correctness because it gives a stable harness for rendering, input, audio, and gameplay fixes. Once the loop can survive multiple iterations, visible frames and input become higher-value than further one-off startup repairs.

The first playable scene is the next major product-shaped proof point: it validates enough resource loading, renderer state, input, timing, and engine control flow to guide later accuracy work.

SDL or a similar library should be treated as the portable host backend, not as a replacement for the reconstructed game-facing APIs. Direct calls from reconstructed logic to SDL would make the code less faithful and less useful for modders. The intended shape is reconstructed code calling Win32/DirectX-shaped compatibility functions, those functions calling a narrow host backend interface, and the backend eventually using SDL for multi-platform window, input, presentation, and audio support.

True multi-platform support remains a later milestone because the reconstructed core still carries 32-bit pointer, fixed-address, calling-convention, and legacy memory-layout assumptions. The realistic portability ladder is Linux/i386 first, then a backend-neutral host layer, then SDL-backed platforms as the reconstructed core becomes less dependent on fixed host assumptions.

## Success Criteria

1. Each milestone has a GDB or runtime observation proving it was reached.
2. Each crash frontier change is recorded in the project journal.
3. Each reconstructed C fix that must survive regeneration is mirrored in `GenerateRecon.js`.
4. Temporary shims are documented with the condition that should retire or replace them.
5. Debug and ASan builds remain available for each completed milestone.
6. Host-specific code does not leak into reconstructed game logic when it can live behind the compatibility or backend boundary.
7. New rendering, input, timing, and audio work identifies whether it belongs to reconstructed game behavior, Win32/DirectX compatibility semantics, or the replaceable host backend.

## Change Log

### 2026-07-13

1. Created milestone plan.
2. Marked the first five milestones complete after reaching `FUN_00410a48 -> thunk_FUN_004620db`.
3. Added the next runtime milestone sequence from the post-main-loop-entry `"e_config"` crash through first controllable gameplay.

### 2026-07-14

1. Clarified that Linux is the current proving ground, while long-term portability should come from a backend-neutral host layer.
2. Reframed visible-frame and input milestones so they target compatibility-layer behavior rather than Linux/X11-specific implementation.
3. Added explicit future milestones for a replaceable host boundary and SDL-backed host implementation.
