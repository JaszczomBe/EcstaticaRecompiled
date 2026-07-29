# Playable SDL Runtime

Status: active
Priority: top
Owner: mixed
Last Updated: 2026-07-29
Parent Plan: [Runtime Milestones](../../plans/runtime-milestones.md)

## Goal

Turn the reconstructed Ecstatica II Linux runtime from a proven first-gameplay/live-frame milestone into a practical SDL-backed developer runtime that can be launched, observed, controlled, debugged, and improved through repeatable bounded checks.

## Scope

1. Interactive SDL F5 stability and crash-frontier triage.
2. DirectDraw page, palette, and front-buffer fidelity.
3. Gameplay input, camera, and control-state proof expansion.
4. Runtime timing and frame pacing ownership.
5. Initial DirectSound/audio compatibility boundary.
6. Repeatable developer bootstrap, launch, and validation workflow.

## Non-Goals

1. Shipping a polished multi-platform release.
2. Replacing original-shaped reconstructed game logic with host-library shortcuts.
3. Pixel-perfect rendering or full audio fidelity in the first pass.
4. Removing 32-bit/fixed-address assumptions before they are mapped.
5. Broad generated-file churn outside focused, Ghidra-backed repairs.

## Current Baseline

The completed [Run Reconstructed E2 On Linux](../linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md) implementation proves the first runtime horizon:

1. Original Ecstatica II data loads from `/home/rgrabowski/Games/Ecstatica2/`.
2. The reconstructed main loop survives under debug and ASan probes.
3. Menu input reaches requester navigation and Start Game.
4. Gameplay control-ready probes reach `_DAT_00643650=0`, `_DAT_0073cc3c=0x681d04`, nonblank surface 3 `hash=6e39f5ea`, and `move=[1,0,0,0,0,0,0,0,0]`.
5. Host window/input/presentation behavior is isolated behind a backend boundary.
6. SDL 3.4.12 is vendored under `dep/SDL`.
7. The SDL backend can receive real recovered `640x480` runtime frames.
8. VS Code exposes `Ecstatica Recompiled (SDL)` for the live-presentation backend.

## Step Roadmap

Each step should be small enough for a single context window. If a step starts collecting unrelated fixes, split it before implementation continues.

1. [Stabilize Interactive SDL F5 Runtime](steps/step-01/step-01-stabilize-interactive-sdl-f5-runtime.md) - completed; captured the user's F5 behavior, reproduced the stable SDL boundary, and classified the first frontier as DirectDraw page/palette/front-buffer fidelity.
2. [Recover DirectDraw Page And Palette Semantics](steps/step-02/step-02-recover-directdraw-page-and-palette-semantics.md) - active; replace grayscale page heuristics with recovered front-buffer/page/palette ownership.
3. [Expand Gameplay Control And Camera Proofs](steps/step-03/step-03-expand-gameplay-control-and-camera-proofs.md) - planned; grow from one movement latch to a compact control-state matrix.
4. [Define Runtime Timing And Frame Pacing](steps/step-04/step-04-define-runtime-timing-and-frame-pacing.md) - planned; identify timing ownership and add a backend timing contract only where needed.
5. [Begin DirectSound Compatibility](steps/step-05/step-05-begin-directsound-compatibility.md) - planned; map startup sound behavior and define the first replaceable audio boundary.
6. [Package Reproducible Developer Runtime](steps/step-06/step-06-package-reproducible-developer-runtime.md) - planned; make clone/submodule/build/launch validation boring and repeatable.

## Active Frontier

The current user-facing target is E2WIN95 startup-sequence parity, not only palette or front-buffer selection. The expected reference path is:

1. Psygnosis logo.
2. Andrew Spencer Studios logo.
3. Ecstatica II loading/logo screen.
4. Engine intro sequence starting with the horseback/credits scene.
5. `Esc` can enter the menu during the intro; `Space` skips toward the first gameplay sequence.

Current rebuilt SDL behavior has advanced past several crash boundaries, but it still does not match that sequence. Startup diagnostics now prove the route finds and dispatches `ken:StartUp`, and `FUN_00447d94` now recognizes the flat `FANT` layout in `Files/ECSTATIC` instead of treating it as an offset-indexed archive. The flat-FANT scan populates the scene offset table at `0x650fa0`, so opcode-`0x4d` preloads install matching scene records and child-list passes execute instead of walking empty table slots. Follow-up generated repairs stabilized scene removal/list cleanup, scene activation, and actor/name lookup; bounded SDL/gdb now reaches all startup actions, reaches `mar:StartGame`, logs through `before-return`, and then survives until the frame loop.

The active frontier is no longer `PlayScene "horse"` resolution or empty actor/current ownership. Original `E2WIN95.EXE` disassembly proves script opcodes `0x07` and `0x0c` should pass the loaded scene record to `FUN_004523f8`; the generated reconstruction now mirrors that register flow. `E2R_SCRIPT_DIAG=1` proves token `0x061c` resolves to `horse`, loads from flat-FANT offset `607214`, installs slot `0xac2594`, and gains active flag `0x02` after activation. Flat-FANT type `0x08` actor records are now scanned into `0x653840`, so `mar:StartGame` loads actor `0` from offset `12773490` and the frame loop starts with `DAT_0047a470=0xaa6bd8`, `_DAT_0063726c=0xaa6bd8`, and `_DAT_00637248=0xaa6bd8`.

Raw view/camera ownership is now recovered for the normal startup route. Original `E2WIN95.EXE` disassembly proves `FUN_004211c8` and the `FUN_004523f8` current-actor child pass load the active scene id from the actor/scene record before calling `FUN_0044be20`; the generated reconstruction now passes that scene id explicitly. `FUN_0044add8` also rebuilds its palette filename in a real stack buffer, and the shared `FUN_0045fd2c`/`FUN_0045fd4b` string helpers now honor their destination argument. A regenerated 30-frame dummy-SDL probe survives with `view raw open: scene=1073 camera=1073 hires=1 path=hires\1073.raw`, reaches stable actor updates with `_DAT_0073cc3c=0x683c84`, and writes nonblank surface 3 (`hash=44b33248`). The next slice should compare that output against the E2WIN95 horseback/credits path and settle which DirectDraw page should be presented.

## Invariants

1. Keep SDL below the host backend; reconstructed C must not call SDL directly.
2. Keep the default debug route available until SDL is intentionally promoted to default.
3. Treat visual/audio fidelity fixes as compatibility semantics unless original logic evidence says otherwise.
4. Mirror durable reconstructed fixes in `E2Recomp/tools/GenerateRecon.js`.
5. Record every new crash frontier with command, call stack, last useful proof line, and regression impact.
6. Prefer bounded probes that terminate automatically; manual F5 findings should become reproducible commands when feasible.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. `cmake --build --preset linux-clang32-sdl-debug`
4. `scripts/run-e2-runtime-regressions.sh`
5. SDL backend probes relevant to the active step.
6. Manual VS Code F5 check when a step changes interactive behavior.
7. `git diff --check`

## Change Log

### 2026-07-28

1. Created implementation after the reconstructed-runtime plan reached first gameplay, live SDL presentation, and an SDL F5 launch route.
2. Completed Step 1 with a stable SDL F5/no-crash boundary and activated DirectDraw page/palette/front-buffer recovery.
3. Step 2 advanced post-logo startup scene selection by initializing archive-loaded actor live positions through the original `FUN_0044146c` helper.

### 2026-07-29

1. Reframed the active frontier around E2WIN95 startup-sequence parity after palette recovery proved the logo colors but F5 still skipped the Psygnosis/Andrew Spencer screens and entered the wrong scene/stall path.
2. Recorded the latest bounded result: SDL startup survives to timeout after archive load with crash fixes applied, but does not reach `mar:StartGame` or the expected horseback intro yet.
3. Recovered flat-FANT startup preloads by scanning `Files/ECSTATIC` scene records into `0x650fa0`; opcode-`0x4d` now installs requested scene ids, and the active crash frontier moved to `FUN_0043aa98` scene-removal/list unlinking while loading scene id `1424` before `mar:StartGame`.
4. Cleared the pre-`mar:StartGame` crash chain: bounded SDL/gdb reaches `mar:StartGame` `before-return` and later interrupts in the frame loop. The active frontier is now scene-current ownership and the missing horseback/credits intro route.
5. Repaired generated opcode `0x07`/`0x0c` scene activation to match original `E2WIN95.EXE` register flow by passing the loaded scene record into `FUN_004523f8`. The `horse` scene now activates, exposing the next non-crash frontier: empty actor/current ownership after activation.
6. Recovered flat-FANT actor offsets and hidden actor context through the `FUN_004523f8` activation pass. The normal route now loads actor `0` and reaches the frame loop with nonzero actor/current ownership; the next crash frontier is bogus raw-view/camera selection in the render epilogue.
7. Recovered raw-view scene id and palette filename construction for the render epilogue. Regenerated SDL debug probes now survive 30 frames after `mar:StartGame`, load `hires\1073.raw`, and dump nonblank surface 3; the active frontier moves back to visual/front-buffer parity.
