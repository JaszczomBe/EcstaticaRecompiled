# 2026-09-21 — Polygon inputs and reference-plane ownership

Area: `FUN_00424e44 → FUN_00433d30 → FUN_00431a7c` and adjacent polygon callers.

Symptom: gated SDL crashes on `*(int *)(unaff_EBX + 4)` with `unaff_EBX=1`, while drawing polygon `0x84b34c`. This is the source task following the post-intro requester repair. The worktree was clean at entry.

## Original evidence and repair

Original `0x424e4b..0x424e68` clears EBX, then, for a nonnegative signed polygon index at `+0x1c`, reads `owner(+0x22)->polygon_table(+0xdc)[index]`. EAX is the submitted polygon, EDX is the drawing mode, and EBX is this optional reference polygon. It is not another mode value or the current actor.

`0x433d37..0x433d3b` preserves all three inputs. The triangle/quad dispatcher forwards them unchanged to both flat and textured leaves, including both halves of a quad, then restores the submitted polygon's vertices, UVs and flags. `0x431a86..0x431a8c` and `0x437aee..0x437af4` preserve the same inputs at leaf entry.

The reconstruction now supplies the reference explicitly through all these boundaries. The textured leaf also retains its polygon across the texture lookup and supplies the signed texture ID at `+0x2c`, as established by `0x437af8..0x437b09`. Lighting, rasterization and other lost helper inputs inside these leaves are not recovered by this change.

The remaining direct flat-polygon caller is `FUN_00425018`. Original `0x42548c..0x4254b9` passes two stack records: submitted polygon at stack `+0x194`, reference polygon at `+0x150`, following eight vertices of stride `0x2a`. The reconstruction's separate tiny local arrays did not preserve that layout and it passed a vertex index as the polygon address. One contiguous `0x1d8`-byte scratch allocation now holds those vertices and records, and calls pass the two actual addresses. Unused bytes are initialized; the pre-existing unrecovered vertex transform remains a stub. The flat leaf accepts readable stack records instead of rejecting all addresses above the fixed game arena. This recovers storage and arguments, not the temporary geometry's transforms or textured path.

All changes are mirrored in `GenerateRecon.js`, including the three revised prototypes. No action gate, scene selection or actor position is forced.

## Verification

`scripts/check-e2-polygon-inputs.py` executes the original selector and triangle/quad dispatcher from the supplied executable in a temporary i386 harness. Intercepted rendering calls are compared with recovered C for **576 cases**: absent/two indexed reference pointers, triangles/quads, texture availability, both texture-disable conditions, owner rendering flags, mode selection and quad flag/UV restoration. A separate twelve-face fixture checks the temporary caller's live record/vertex/reference storage, with projection and rasterization intercepted. Both checks pass normally and with recovered C instrumented by ASan. They do not prove rendered pixels or actual vertex transforms.

```sh
python3 scripts/check-e2-polygon-inputs.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-polygon-inputs.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
cmake --build --preset linux-clang32-debug
cmake --build --preset linux-clang32-debug-asan
cmake --build --preset linux-clang32-sdl-debug
cmake --build --preset linux-clang32-sdl-debug-asan
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_REGRESSION_TMP=/tmp/e2-polygon-regressions scripts/run-e2-runtime-regressions.sh
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_CONTROL_MATRIX_TMP=/tmp/e2-polygon-matrix scripts/run-e2-control-matrix.sh
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl/e2recomp --output /tmp/e2-polygon-requester-debug
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl-asan/e2recomp --output /tmp/e2-polygon-requester-asan
```

All four builds, generator syntax, four-artifact scratch parity, the default regression wrapper, all eight arrow rows and both SDL requester tests pass. The requester tests still resume camera 87 and reach Escape main-menu entry. The later 2026-09-21 manual report confirms Task 09's dialog and transition to camera 87 after OK, with the same error still visible and no hero. Manual Escape remains unconfirmed; no visible-player claim is made.

## Runtime result and next failure

Bounded gated SDL/GDB reproduction:

```sh
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 E2R_STARTUP_LOGO_DELAY_MS=0 timeout 55 gdb -q -batch -ex 'set pagination off' -ex run -ex 'bt 12' -ex 'info locals' --args build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-polygon-after 40 7000
```

Before: `/tmp/e2-polygon-before.log` stops at the invalid reference read. After: `/tmp/e2-polygon-after.log` confirms polygon `0x84b34c`, reference **0**, and the later stack `FUN_00431a7c → FUN_004226bc → FUN_004228b8 → FUN_0045dd04`. The matrix helper dereferences unrecovered register pointers. GDB's shell exit 0 does not mean this game run passed.

A gated SDL ASan readiness probe (`--auto-scene175-visibility /tmp/e2-polygon-gated-asan 35 7000`, same environment) exits **5** after 35 seconds in camera 1073, without an ASan report. It never reaches the fixed draw path and therefore does not validate gated geometry under ASan.

Next: [Task 10 — recover polygon lighting inputs](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-10-recover-polygon-lighting-inputs.md). Recover normal-vector storage, angle arguments and matrix destinations from the original callers before touching rasterization. [Task 02](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-02-recover-joe-geometry-and-rendering.md) remains active: living Joe, faithful placement and visible motion are still unproven. Action indexing remains opt-in.

Regression risk: restored arguments allow previously unreachable lighting/raster helpers to execute. Temporary vertices still have unrecovered transforms, and the textured leaf has further lost helper inputs. Keep these limits separate from the proven polygon-routing and storage contract.

Same-day continuation: [flat-polygon lighting inputs](polygon-lighting-2026-09-21.md) are subsequently recovered and verified; Task 11 rectangle-copy inputs becomes the next bounded source task.
