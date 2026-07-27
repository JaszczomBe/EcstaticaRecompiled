# Run Reconstructed E2 On Linux

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-07-27
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

The original post-main-loop `"e_config"` crash through `FUN_0046055c` has been cleared. Runtime stabilization has advanced through config-header, CDPath, hosted file existence, menu/dialog string-list, fixed-address table, framebuffer fill, quick-save writer, HUD icon clear, damage-rectangle table, requester-id frontiers, and the first bounded input-flag probe. Step 7 sustains the reconstructed runtime under ASan for 90 seconds without a sanitizer crash, Step 8 captures an inspectable `640x480` Ecstatica II title-logo frame from the ASan build, and Step 9 now posts recovered key events through the compatibility queue into `E2R_WndProc`/`DAT_006368xx`, polls X11 host keypresses, and confirms the visible-menu gap is not hidden on another framebuffer page.

## Active Steps

Step 9 is complete. Its input bridge maps `WM_KEYDOWN` through the compatibility message queue into recovered input globals, feeds legacy key queues, and polls X11 keypresses into the same path. Requester-ready probes reach rendering, keyboard focus movement, action selection, and nested Quit confirmation outcomes in both debug and ASan. Exact recovery of the unnamed fixed English confirmation text at `0x004729b8` remains a fidelity backlog item.

Step 10 is active and ready for cleanup/closure review. The original requester `0x27/0x28` record selects Start Game item `0x00643b30`, and matching debug/ASan probes prove entry into `FUN_0043a39c`. The parser handoff, packed name tables, table ordinals, Start-code lookup, action-node parser, FAN section readers, archive table loader, direct archive resource wrapper, actor-loader handoffs, scene-current recovery, and current-frame guards are generator-backed. A split gameplay probe now posts `space`, waits for scene/control state, then posts `num8`. Both debug and ASan satisfy the control-ready gate with `_DAT_00643650=0`, `DAT_00479de8=1`, `_DAT_0073cc3c=0x681d04`, a nonblank surface 3 hash `6e39f5ea`, and `move=[1,0,0,0,0,0,0,0,0]`; ASan exits without a sanitizer report. The remaining Step 10 work is to trim temporary diagnostics and decide how much hidden-register fidelity to recover in the guarded surface-copy helpers before closing the step.

## Step Roadmap

Each step should be scoped so it can preferably be completed in one context window. If a step grows beyond that, split it before implementation continues.

1. [Resolve Current Startup Crash](steps/step-01/step-01-resolve-current-startup-crash.md) - completed; fixed the `FUN_00414b24 -> FUN_00414e68` `0x200` dereference.
2. [Prove First Resource Load](steps/step-02/step-02-prove-first-resource-load.md) - completed; verified loading one real file from `/home/rgrabowski/Games/Ecstatica2/`.
3. [Create Visible Window](steps/step-03/step-03-create-visible-window.md) - completed; create a Linux-hosted visible window or rendering surface.
4. [Reach Menu Or Title Logic](steps/step-04/step-04-reach-menu-or-title-logic.md) - completed; initialize enough graphics/audio stubs to reach title/menu code.
5. [Reach Main Loop](steps/step-05/step-05-reach-main-loop.md) - completed; advanced to `thunk_FUN_004620db` and documented the next crash frontier.
6. [Resolve Post Main Loop Config Open Crash](steps/step-06/step-06-resolve-post-main-loop-config-open-crash.md) - completed; old `"e_config"` file/CRT crash is cleared and the `FUN_00453920` no-op has been verified under ASan.
7. [Sustain Main Loop Heartbeat](steps/step-07/step-07-sustain-main-loop-heartbeat.md) - completed; recovered HUD icon clearing, damage-rectangle table access, and loop requester-id handoff, then verified 90 seconds under ASan.
8. [Present Inspectable Title Or Menu Frame](steps/step-08/step-08-present-inspectable-title-or-menu-frame.md) - completed; added bounded frame dumping and captured a real Ecstatica II title-logo frame from ASan surface 3.
9. [Wire Menu Input Path](steps/step-09/step-09-wire-menu-input-path.md) - completed; message-queue `WM_KEYDOWN`, X11 host-key poll, legacy key queues, requester navigation/action selection, and Quit confirmation No/Yes outcomes are verified in debug and ASan.
10. [Reach First Controllable Scene](steps/step-10/step-10-reach-first-controllable-scene.md) - active; restore the original Start Game menu path, enter scene loading, capture a gameplay frame, and prove one control-driven state change.
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
9. Avoid generated-file churn: after any `GenerateRecon.js` edit, regenerate and prove `E2Recomp/reconstructed/*` has no unrelated drift before building or probing.

## Generated Code Workflow

Use this workflow for every reconstructed-runtime change:

1. Check `git status --short`, `git diff --stat`, and `git diff --cached --stat` before editing.
2. Use a minimal hand edit in `E2Recomp/reconstructed/E2Recomp_recon.c` only when needed to prove a runtime hypothesis.
3. Mirror the proven hand edit in `E2Recomp/tools/GenerateRecon.js` before treating the fix as durable.
4. Prefer precise source replacements, regexes scoped to one function, or ordered replacement tables. Avoid giant `apply_patch` blocks over generated C.
5. Run `node --check E2Recomp/tools/GenerateRecon.js`, then `node E2Recomp/tools/GenerateRecon.js .`.
6. Inspect `git diff --stat` and targeted generated-file diffs immediately. If regeneration produces thousands of unrelated lines, stop and fix the generator anchors instead of accepting the churn.

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
8. Added bounded `--dump-frame` support and captured a real `640x480` Ecstatica II title-logo frame from the ASan build.
9. Closed step 8 and opened step 9 for host input/menu navigation.

### 2026-07-17

1. Advanced step 9 through legacy key queue bridging, requester instrumentation, raw requester-record repair, item traversal, and text-draw surface fixes.
2. Verified ASan `escape,num8,space` reaches `FUN_0043ce58`, records `b9bc=18`, and changes surface 3 to hash `9042c4ed`.
3. Added requester-ready key-sequence probes, bypassed the hosted startup music path for Step 9, pinned the shadow-table preload to literal `shadow.dat`, and verified requester rendering in both debug and ASan.
4. Advanced requester input through `FUN_0043bd4c` key consumption and Enter/action selection in both debug and ASan, recording raw callback labels instead of calling unrecovered label pointers.
5. Added a first recovered dispatcher for simple requester callback labels, keeping harder callbacks recorded while focus/selection fidelity is investigated.
6. Recovered requester focus movement by locally initializing the fixed-address main-menu item chain, seeding `_DAT_00643430`, and fixing selected-item pointer arithmetic; debug and ASan now verify one-step and two-step Down/Enter requester probes.
7. Recovered the `DAT_0043d49c` Quit callback's original no-confirm branch; debug and ASan `escape,num2,enter` now select the Quit item and return through `_DAT_00643650=5`, leaving `FUN_0043c910` yes/no prompt recovery as the active frontier.
8. Recovered the `FUN_0043c910` Quit confirmation prompt path and original state switch case `6`; debug and ASan now verify default No (`_DAT_00643650=5`) and Down+Enter Yes (`_DAT_00643650=6`) outcomes.

### 2026-07-18

1. Closed Step 9 after all input-path acceptance criteria passed and retained exact English Quit prompt text recovery as a fidelity backlog item.
2. Opened Step 10 with an initial bounded target: restore requester `0x27/0x28` from original executable data, select Start Game, and record the first `FUN_0043a39c` scene-loading frontier.
3. Restored the original Start Game requester record and verified debug/ASan `escape,enter` probes enter `FUN_0043a39c`; recorded the action-name lookup/dispatch cluster as the next frontier.

### 2026-07-20

1. Reran bounded Start Game probes outside the sandbox after sandboxed runs exited with code `159`.
2. Confirmed ASan reaches `FUN_00444c10 -> FUN_004268e4` and dies reading through hidden owner `EAX=0x2`; original disassembly shows the helper needs the owner pointer from `FUN_00444c10` stack state, not the stale generated argument.
3. Recovered the `FUN_00444c10` owner/list helper cluster, raw hosted FAN word reads, token remapping input, and fixed remap-table reads; ASan now reaches the later `FUN_004448e4` frontier while debug remains at the ordinal-4 unknown-record diagnostic.
4. Recovered the `FUN_004448e4`, `FUN_00445000`, and `FUN_004451a8` stream/input contracts plus the first `FUN_00447638` table write. ASan now reaches `FUN_00447638 -> FUN_004418fc -> FUN_0045fae0`; debug still stops at the ordinal-4 unknown-record diagnostic.
5. Recovered packed-name lookup wrappers, the hosted `FUN_0045fae0` compare contract, and remaining fixed-address `FUN_00447638`/remap-table reads. ASan now exits cleanly and dumps the Ecstatica II title surface, but requester/action probes still report `start_game entries=0`; debug still stops at the ordinal-4 unknown-record diagnostic.
6. Recovered hosted binary/text stream byte semantics, replaced `FUN_00444c10` with an explicit action-node parser, and fixed the stale hidden-register terminator test in `FUN_00444668`. Debug and ASan now both enter `FUN_00444c10` at offset `104847`, parse through the old ordinal-4 boundary, dump the title surface, and still report empty requester/start-game action state.
7. Recovered the later FAN tail path through ordinal-4 termination, `FUN_00447638` `49650` terrain/path entries, `1200` segment records, tail-node allocation, post-FAN invalid actor-head cleanup, hosted literal path validation, stable `Files/ECSTATIC` archive opening, `FUN_00447d94` archive table loading, guarded `StartGame` action lookup, action-table fallback dispatch, hosted archive seeking, and direct embedded `FANT` resource parsing.
8. Recovered opcode-local actor id delivery into `FUN_00451f5c`, hosted allocator/backbuffer handling, quiet hosted bad-`FANT` and missing-actor archive misses, and invalid hosted fill guards. Debug now reaches requester-ready, dispatches the requester dialog, observes a second StartGame entry, and exits without a segfault.
9. Recovered archive actor cursor mapping for table offset `3997760` by backscanning to the containing `FANT` at `3993260`, fixed stale opcode `0x54` actor flag clearing, and recovered `FUN_00426478` actor initializer writes through the allocated actor pointer. Debug parses the first actor resource without crashing; ASan writes one nonblank surface. The current frontier is post-actor-load readiness: debug no longer opens the requester after Escape and still cannot dump surfaces, while ASan times out before requester-ready but produces a nonblank dump.

### 2026-07-22

1. Advanced ASan through the hosted FAN reader cost and version-55 `FUN_00447638` entry alignment, removed stale high-host-pointer guards from action lookup/dispatch, repaired the remaining `0x006536b0` fixed table references, and recovered `FUN_0042ce70` actor context.
2. Verified debug gameplay proof still reaches surface 3 hash `3615add9` with movement state set.
3. Recorded the new ASan frontier after two actor-load passes: `FUN_0044c164 -> FUN_004211c8 -> FUN_0042a70c -> FUN_00426df8`.
4. Added an ASan-only actor-table plausibility guard at `FUN_0044c164`. Debug remains at the stable gameplay-frame proof (`3615add9`, movement set); ASan now exits without a sanitizer report but still times out before the visible gameplay frame (`6e39f5ea`).
5. Repaired the scene-current path by discarding unreadable archive-current residue, deriving `FUN_0044c6bc`'s scene record from `_DAT_0073ccba`, and installing the normal-start scene slot when active gameplay starts without a scene. ASan now satisfies the gameplay-frame wait with `_DAT_0073cc3c=0x681d04` and a nonblank surface; the remaining Step 10 task is ASan movement-state parity with delayed/ready movement input.

### 2026-07-27

1. Added a split gameplay probe path so early intro keys can be posted before gameplay readiness and later movement keys can be posted after the gameplay/control wait.
2. Verified debug control-ready movement parity: `space,num8 ... gameplay_key_split=1` reaches `_DAT_00643650=0`, `_DAT_0073cc3c=0x681f18`, surface 3 hash `3615add9`, and `move=[1,0,0,0,0,0,0,0,0]`.
3. Verified ASan delayed movement latch without a sanitizer report: the stricter control-ready wait times out with `_DAT_00643650=5`, but the delayed `num8` still posts through the Win32 queue and records `move=[1,0,0,0,0,0,0,0,0]` with `_DAT_0073cc3c=0x681d04`.
4. Recorded the new frontier as ASan requester-state residue after StartGame, not a missing movement-key delivery path.
5. Recovered the ASan requester-state residue by tracing `FUN_0042a70c -> FUN_00427584` and narrowing the dead-current requester guard to readable non-null actors. ASan now satisfies the control-ready movement probe with `_DAT_00643650=0`, `_DAT_0073cc3c=0x681d04`, surface 3 hash `6e39f5ea`, and `move=[1,0,0,0,0,0,0,0,0]`.
6. Stabilized the debug post-control surface-copy path by guarding generated `FUN_0041868c` and `FUN_00417b20` against stale hidden source/X register residue and invalid copy spans. Final debug and ASan split probes both exit cleanly, keep requester state clear, latch delayed movement, and dump nonblank surface 3 hash `6e39f5ea`.
