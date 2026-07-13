# Run Reconstructed E2 On Linux

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-07-13
Parent Plan: [Runtime Milestones](../../plans/runtime-milestones.md)

## Goal

Bring the reconstructed Ecstatica II runtime far enough on Linux that it can load original CD data, initialize host-compatible platform services, and advance toward menu/title or main-loop execution without relying on one-off untracked patches.

## Scope

1. Linux CMake and Clang build/run workflow.
2. Win32 compatibility shims needed by the reconstructed runtime.
3. GDB crash-loop investigation.
4. Ghidra-backed recovery of lost register, calling convention, and pointer intent.
5. Journaling each exploratory fix and exposed regression.

## Non-Goals

1. Perfect original Windows behavior in the first pass.
2. Full graphics/audio backend implementation before startup is stable.
3. Committing or pushing changes without explicit user approval.

## Current State

Steps 1 through 4 are complete. Debug and ASan 32-bit builds compile. The runtime enters the Ecstatica II data directory through the build-tree `Ecstatica2` symlink, resolves read-only paths case-insensitively, creates a Linux-hosted X11 window from the original Ecstatica II window path, and now reaches title logic after startup logo loading.

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

The reached title path is:

```text
FUN_00410a48 -> FUN_00414a94
FUN_00410a48 -> FUN_00414b24
```

The latest debug GDB run hit both title functions and exited with code `0340` rather than crashing in the prior DirectDraw/surface frontier.

## Active Steps

No implementation step is currently active. Step 4 is complete; step 5 is the next planned step when work resumes.

## Step Roadmap

Each step should be scoped so it can preferably be completed in one context window. If a step grows beyond that, split it before implementation continues.

1. [Resolve Current Startup Crash](steps/step-01/step-01-resolve-current-startup-crash.md) - completed; fixed the `FUN_00414b24 -> FUN_00414e68` `0x200` dereference.
2. [Prove First Resource Load](steps/step-02/step-02-prove-first-resource-load.md) - completed; verified loading one real file from `/home/rgrabowski/Games/Ecstatica2/`.
3. [Create Visible Window](steps/step-03/step-03-create-visible-window.md) - completed; create a Linux-hosted visible window or rendering surface.
4. [Reach Menu Or Title Logic](steps/step-04/step-04-reach-menu-or-title-logic.md) - completed; initialize enough graphics/audio stubs to reach title/menu code.
5. [Reach Main Loop](steps/step-05/step-05-reach-main-loop.md) - planned; advance to the main loop without crashing.

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
