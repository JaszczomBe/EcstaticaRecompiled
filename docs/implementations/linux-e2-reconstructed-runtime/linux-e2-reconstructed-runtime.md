# Run Reconstructed E2 On Linux

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-07-16
Parent Plan: [Runtime Milestones](../../plans/runtime-milestones.md)

## Goal

Bring the reconstructed Ecstatica II runtime far enough on Linux that it can load original CD data, initialize host-compatible platform services, run a durable main loop, present inspectable frames, accept input, and advance toward a controllable gameplay scene without relying on one-off untracked patches.

Linux is the current proof platform. Portability work should preserve reconstructed game logic as an original-shaped source base for reverse engineering and modding, while moving host behavior behind compatibility and backend boundaries that can later be implemented with SDL or an equivalent multi-platform library.

## Scope

1. Linux CMake and Clang build/run workflow.
2. Win32 compatibility shims needed by the reconstructed runtime.
3. GDB crash-loop investigation.
4. Ghidra-backed recovery of lost register, calling convention, and pointer intent.
5. Journaling each exploratory fix and exposed regression.
6. Main-loop durability, frame presentation, input, and first-scene progression.
7. Separation of reconstructed game behavior, Win32/DirectX compatibility semantics, and host backend implementation.

## Non-Goals

1. Perfect original Windows behavior in the first pass.
2. Full graphics/audio backend implementation before startup is stable.
3. Committing or pushing changes without explicit user approval.
4. Calling SDL or any other host library directly from reconstructed game logic.
5. True multi-platform release support before 32-bit, fixed-address, and legacy memory-layout assumptions are understood well enough to relax.

## Current State

Steps 1 through 5 are complete. Debug and ASan 32-bit builds compile. The runtime enters the Ecstatica II data directory through the build-tree `Ecstatica2` symlink, resolves read-only paths case-insensitively, creates a Linux-hosted X11 window from the original Ecstatica II window path, reaches title logic after startup logo loading, and now reaches the suspected main-loop entry thunk.

```text
/home/rgrabowski/Games/Ecstatica2/PSYGLOGO.RAW
requested as: psyglogo.raw
call path: FUN_00410a48 -> FUN_00414998 -> FUN_0045e594 -> CreateFileA
```

The proven window path is:

```text
FUN_00458714 -> RegisterClassA -> CreateWindowExA
title: Ecstatica II
size: 640x640
```

The reached title and main-loop-entry paths are:

```text
FUN_00410a48 -> FUN_00414a94
FUN_00410a48 -> FUN_00414b24
FUN_00410a48 -> thunk_FUN_004620db
```

The original post-main-loop `"e_config"` crash through `FUN_0046055c` has been cleared. Runtime stabilization has advanced through config-header, CDPath, hosted file existence, menu/dialog string-list, fixed-address table, framebuffer fill, quick-save writer, HUD icon clear, damage-rectangle table, and requester-id frontiers. Step 7 now sustains the reconstructed runtime under ASan for 90 seconds without a sanitizer crash.

## Active Steps

Step 7 is complete. Step 8 is active and should turn the sustained heartbeat into an inspectable title/menu frame.

## Step Roadmap

Each step should be scoped so it can preferably be completed in one context window. If a step grows beyond that, split it before implementation continues.

1. [Resolve Current Startup Crash](steps/step-01/step-01-resolve-current-startup-crash.md) - completed; fixed the `FUN_00414b24 -> FUN_00414e68` `0x200` dereference.
2. [Prove First Resource Load](steps/step-02/step-02-prove-first-resource-load.md) - completed; verified loading one real file from `/home/rgrabowski/Games/Ecstatica2/`.
3. [Create Visible Window](steps/step-03/step-03-create-visible-window.md) - completed; create a Linux-hosted visible window or rendering surface.
4. [Reach Menu Or Title Logic](steps/step-04/step-04-reach-menu-or-title-logic.md) - completed; initialize enough graphics/audio stubs to reach title/menu code.
5. [Reach Main Loop](steps/step-05/step-05-reach-main-loop.md) - completed; advanced to `thunk_FUN_004620db` and documented the next crash frontier.
6. [Resolve Post Main Loop Config Open Crash](steps/step-06/step-06-resolve-post-main-loop-config-open-crash.md) - completed; old `"e_config"` file/CRT crash is cleared and the `FUN_00453920` no-op has been verified under ASan.
7. [Sustain Main Loop Heartbeat](steps/step-07/step-07-sustain-main-loop-heartbeat.md) - completed; recovered HUD icon clearing, damage-rectangle table access, and loop requester-id handoff, then verified 90 seconds under ASan.
8. [Present Inspectable Title Or Menu Frame](steps/step-08/step-08-present-inspectable-title-or-menu-frame.md) - active; show a real reconstructed title/menu frame through the compatibility renderer while keeping host presentation replaceable.
9. Wire Menu Input Path - planned; map host keyboard/mouse events into the reconstructed Win32-style input path far enough to navigate title/menu logic.
10. Reach First Controllable Scene - planned; load a gameplay scene and prove basic player-control or camera-control progression.
11. Harden Runtime Loop Regression Checks - planned; make debug/ASan/GDB probes repeatable for the stabilized loop path.
12. Define Replaceable Host Backend Boundary - planned; isolate window, input, timing, presentation, and audio backend calls below the compatibility layer.
13. Add SDL Host Backend - planned; replace or supplement Linux/X11 scaffolding with SDL once loop, frame, and compatibility semantics are stable enough to specify.

## Journals

1. [Runtime crash fixes](../../journal/entries/runtime-crash-fixes.md)
2. [Generated code repairs](../../journal/entries/generated-code-repairs.md)
3. [Linux portability](../../journal/entries/linux-portability.md)
4. [Reverse engineering workflow](../../journal/entries/reverse-engineering-workflow.md)

## Invariants

1. Prefer Ghidra-backed fixes over broad defensive no-ops when a crash belongs to a recurring decompiler artifact class.
2. Keep hand fixes mirrored in `E2Recomp/tools/GenerateRecon.js` when applicable.
3. Keep `/home/rgrabowski/Games/Ecstatica2/` as the source CD data path.
4. Keep VS Code F5 and CMake preset workflow functional.
5. Keep implementation steps small enough for a single context window whenever practical.
6. Keep reconstructed C focused on recovered original behavior; host-library calls belong behind compatibility or backend boundaries.
7. Treat DirectDraw, DirectSound, Win32, and CRT shims as game-facing compatibility surfaces, not as disposable shortcuts to SDL.
8. When adding rendering, input, timing, or audio behavior, record which layer owns it: reconstructed game logic, compatibility semantics, or host backend.

## Usage Budget

The active implementation step has a hard limit of 5% weekly usage burn per day. If the next investigation would exceed that, stop and report the remaining scope, current evidence, and recommended next action.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. GDB run from `build/linux-clang32-debug`: `./e2recomp --run-recon`
4. Journal the next crash frontier after each successful repair.

## Change Log

### 2026-07-13

1. Created implementation handoff.
2. Completed step 1 by recovering the lost title-error `EAX` message pointer.
3. Completed step 2 by proving the first real resource open and recording the next `FUN_0045e5b8` frontier.
4. Completed step 3 by mapping the original Ecstatica II window request to a Linux X11 window and recording the next DirectDraw/surface frontier.
5. Completed step 4 by adding minimal DirectDraw palette/surface startup support and reaching `FUN_00414a94 -> FUN_00414b24` title logic.
6. Completed step 5 by repairing startup allocation, stream, shadow, and shademap blockers; GDB reached `FUN_00410a48 -> thunk_FUN_004620db`.
7. Extended the implementation roadmap beyond main-loop entry: post-loop config/file recovery, loop heartbeat, visible frame, input, first scene, and regression hardening.

### 2026-07-14

1. Clarified the portability direction: Linux remains the runtime proof target, but host work should prepare for a replaceable backend and future SDL implementation.
2. Added explicit non-goals against direct SDL calls from reconstructed logic and premature true multi-platform promises.
3. Extended the roadmap and invariants with backend-boundary milestones so future graphics, input, timing, and audio work stays layered.

### 2026-07-15

1. Advanced step 6 beyond the old `FUN_0046055c`/`"e_config"` crash through hosted config, CDPath, menu/dialog, fixed-address table, and framebuffer frontiers.
2. Added a hosted no-op for `FUN_00453920` to stop the quick-save writer from crashing through invalid generated string-copy state.
3. Recorded that ASan was not rerun after the final `FUN_00453920` no-op; the next session should start with one bounded verification run.

### 2026-07-16

1. Verified the `FUN_00453920` no-op with one bounded ASan run.
2. Recorded the next frontier at `FUN_0045fae0`, called from `FUN_00455940 -> FUN_00455e84 -> FUN_00415d40 -> FUN_00426df8 -> FUN_0041007c`.
3. Closed step 6 and opened step 7 for sustaining the main-loop heartbeat from the comparison-helper frontier.
4. Recovered the current `FUN_00455e84` HUD icon clear path and redirected the `DAT_0047a29c` fixed-address table.
5. Recorded the next frontier at `FUN_0043cac0`, reached from `FUN_0043ce58 -> FUN_00414e68`.
6. Recovered the `FUN_00415d40 -> FUN_0043ce58` requester id handoff and verified 30-second and 90-second ASan runs without a sanitizer crash.
7. Closed step 7 and opened step 8 for making the sustained title/menu loop inspectable.
