# 2026-10-14 — Documentation and next-step review

Area: handoff, current implementation state, build guidance and Step 08 Task 11.

Question: does the documentation match the latest source, and what evidence is needed next?

## Evidence

The worktree was clean on branch `linux-e2-reconstructed-runtime`, at `4fb151a` (2026-09-21). Reviewed the handoff/resume chain, recent commits, generator mirrors, reconstructed helpers, host cue/backend declarations, CMake presets, VS Code launch and regression scripts.

The latest three runtime commits recover projection/pose/event inputs, the formerly invisible action-error requester, and polygon dispatch/flat-lighting inputs. The detailed Step 08 task and journal records largely match those changes. Living Joe, correct placement/scene selection and child activation remain unproven. The gate remains disabled by default; recorded gated SDL evidence stops in `FUN_00418514`, while gated SDL ASan times out in camera 1073 before geometry.

Direct source review confirms `FUN_00418484` / `FUN_00418514` still have three-argument signatures and lost register state. The original disassembly establishes five copy inputs and saved surface/base ownership at unlock. `FUN_00418b00` still uses uninitialized `in_EAX`; Task 11 must include the required unlock input rather than treating the copy crash as only a missing row coordinate. The expanded [Task 11 plan](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-11-recover-dirty-rectangle-copy-inputs.md) records exact original addresses and comparison coverage.

## Documentation changes

- Corrected the handoff's stable build coordinates and linked the current build guide. Structural reason: the old ASan directory is no longer a preset output, and the everyday SDL build was missing. The user's instruction to reconcile documentation authorizes this correction; changing runtime state remains in implementation/task documents.
- Removed obsolete hollow enemy-icon guidance from the build guide; current cues are projected crosses/uprights and the default settled Joe is behind the camera.
- Corrected configured-data-path and Clang 21 setup guidance, current verification commands, implementation summary/date and Task 11 planning detail. Historical proof results remain dated.
- Added [original-game capture requirements](../../implementations/playable-sdl-runtime/steps/step-08/step-08-recover-scene-175-actors.md#original-game-reference-capture): natural and skipped intro routes, first controllable scene, isolated arrows/camera crossing, and timestamped native-resolution stills. These help behavioral/visual acceptance; executable evidence is sufficient to start the copy repair.

## Verification

```sh
node --check E2Recomp/tools/GenerateRecon.js
cmake --list-presets=all
python3 scripts/check-e2-polygon-inputs.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-polygon-inputs.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
python3 scripts/check-e2-polygon-lighting.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-polygon-lighting.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
```

All pass. Polygon comparisons cover 576 routing/restoration cases and twelve temporary-record cases. Lighting comparisons cover 10,240 angles, 16,384 rotations and 8,192 lighting-index cases. The i386 test harnesses initially received SIGSYS in the sandbox; the same checks passed outside it, including ASan.

The [scratch generation recipe](runtime-audit-2026-09-14.md#scratch-generator-comparison) matches all four outputs: `E2Recomp_globals.c`, `E2Recomp_names.tsv`, `E2Recomp_recon.c` and `E2Recomp_recon.h`. Scratch evidence is under `/tmp/e2-doc-review-generator-hl9866by`; repository artifacts were not regenerated in place.

`git diff --check` passes, and all 129 relative Markdown link targets in the changed documents exist.

No runtime implementation changed. Full builds, runtime wrapper/matrix, SDL requester tests, gated readiness and manual F5 were not repeated; their latest recorded results remain the 2026-09-21 evidence. Bounded comparison passes do not establish rendered actors or playable behavior.

Next: implement Task 11, verify source-consistent rectangle bytes and lock/unlock ownership, then repeat bounded gated execution and relevant regressions. Retain the action-index gate and record any new independent failure before resuming placement/action validation and children.
