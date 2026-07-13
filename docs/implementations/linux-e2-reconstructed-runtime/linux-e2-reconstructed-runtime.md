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

Debug and ASan 32-bit builds compile. The runtime uses the Ecstatica II data symlink under the build tree. The latest known crash is:

```text
FUN_00414e68()
FUN_00414b24(param_1=0, param_2=0)
FUN_00410a48()
```

The fault dereferences `0x200` in `FUN_00414e68`.

## Active Steps

1. [Resolve Current Startup Crash](steps/step-01/step-01-resolve-current-startup-crash.md) - active

## Step Roadmap

Each step should be scoped so it can preferably be completed in one context window. If a step grows beyond that, split it before implementation continues.

1. [Resolve Current Startup Crash](steps/step-01/step-01-resolve-current-startup-crash.md) - fix the current `FUN_00414b24 -> FUN_00414e68` `0x200` dereference.
2. [Prove First Resource Load](steps/step-02/step-02-prove-first-resource-load.md) - reach and verify loading one real file from `/home/rgrabowski/Games/Ecstatica2/`.
3. [Create Visible Window](steps/step-03/step-03-create-visible-window.md) - create a Linux-hosted visible window or rendering surface.
4. [Reach Menu Or Title Logic](steps/step-04/step-04-reach-menu-or-title-logic.md) - initialize enough graphics/audio stubs to reach title/menu code.
5. [Reach Main Loop](steps/step-05/step-05-reach-main-loop.md) - advance to the main loop without crashing.

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
