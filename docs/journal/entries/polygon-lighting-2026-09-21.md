# 2026-09-21 — Flat-polygon lighting inputs

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Area: the normal/lighting block in `FUN_00431a7c`, its angle lookup and local rotations.

Symptom: after polygon argument recovery, gated SDL reached `FUN_004226bc → FUN_004228b8 → FUN_0045dd04` with unrecovered matrix pointers. The existing polygon-input changes were unstaged at entry and are preserved.

## Source evidence and repair

Original `0x431f2d..0x431f4f` stores the reduced normal as three contiguous signed words and calls `0x432c64` with X/Z. `0x431f59..0x431f60` passes the normal and negative returned angle to the Y rotation. `0x431f65..0x431f9d` then computes the angle from **negative rotated Y / rotated Z** and applies the X rotation. The reconstruction had independent locals, uninitialized pseudo-register arguments and a no-argument rotation call.

The original single-axis wrappers (`0x422674`, `0x4226bc`) use local matrix/output buffers through `0x4228b8` and `0x45de8b`. The recovered flat-polygon helper builds those explicit single-axis matrices and uses the already recovered alias-safe Q14 vector transform. It preserves the original reduced X/Y numerators and uses the rotated Z divisor for the clamped 0..127 lighting indices (`0x431faa..0x432007`). A zero divisor yields 64/64, matching the original.

The angle routine also needs real atan lookup values. Original `0x414f5d..0x414fd8` builds two rounded atan tables with scales 1/64 and 1/4. The mapped reconstruction tables currently contain placeholder sine/cosine values. The new helper uses private copies of the recovered atan tables so this bounded repair does not activate unrecovered shared callers. Other legacy angle/rotation callers and their mapped tables remain incomplete. The helper's input domain is the reduced normal (components within +/-0x4000) and its rotations; it is not a general replacement for every signed-short call site.

Once the normal path returned, a subsequent failure exposed `(&DAT_00507590)[index]` reading a host scalar as an array, with host-word stride. Original `0x43206f` and `0x43207f` read bytes from fixed mapped tables `0x507590` / `0x50b510`. Those two reads are corrected in the flat leaf. The broader lighting/color-table initialization still contains approximations; this is no claim of original shading fidelity.

`E2R_PolygonAngle16`, `E2R_RotatePolygonNormal` and `E2R_PolygonLightingIndices` are private to this recovered path. Shared legacy signatures are unchanged. All reconstruction changes are mirrored in `GenerateRecon.js`; no action gate, scene selection or actor coordinates are forced.

## Verification

`scripts/check-e2-polygon-lighting.py` runs original i386 instructions in a temporary harness. It executes the original x87 atan-table initialization, original angle/rotation functions and original lighting block, rather than using a rewritten formula as its reference. Comparisons pass both normally and with ASan on the recovered C:

- **10,240 angle cases**, including all reachable fine/coarse lookup entries, quadrants and zero cases.
- **16,384 single-axis rotations**.
- **8,192 complete normal-to-lighting-index cases**, including degenerate and boundary normals.

```sh
python3 scripts/check-e2-polygon-lighting.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-polygon-lighting.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
cmake --build --preset linux-clang32-debug
cmake --build --preset linux-clang32-debug-asan
cmake --build --preset linux-clang32-sdl-debug
cmake --build --preset linux-clang32-sdl-debug-asan
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_REGRESSION_TMP=/tmp/e2-lighting-regressions scripts/run-e2-runtime-regressions.sh
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_CONTROL_MATRIX_TMP=/tmp/e2-lighting-matrix scripts/run-e2-control-matrix.sh
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl/e2recomp --output /tmp/e2-lighting-requester-debug
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl-asan/e2recomp --output /tmp/e2-lighting-requester-asan
```

Four builds, generator syntax, four-artifact scratch parity, the default regression wrapper, eight arrow rows and both SDL requester checks pass. These establish bounded arithmetic and regression coverage, not visible actors.

## Runtime evidence and next boundary

The standard gated SDL/GDB reproduction now stops later at `FUN_004211c8 → FUN_00424bd8 → FUN_00418484 → FUN_00418514`, copying bytes through an invalid pointer (`/tmp/e2-lighting-mapped.log`). A minimal breakpoint run explicitly reaches the new lighting helper with normal **0,0,0**, returns **64,64**, and then reaches that same framebuffer-copy crash (`/tmp/e2-lighting-once.log`). This proves execution past the repaired lighting boundary; the degenerate normal does not establish valid living-actor geometry.

```sh
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 E2R_STARTUP_LOGO_DELAY_MS=0 timeout 55 gdb -q -batch -ex 'set pagination off' -ex run -ex 'bt 12' -ex 'info locals' --args build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-lighting-mapped 40 7000
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 E2R_STARTUP_LOGO_DELAY_MS=0 timeout 45 build/Debug/clang21-i386-sdl-asan/e2recomp --auto-scene175-visibility /tmp/e2-lighting-gated-asan 35 7000
```

The SDL ASan probe still exits **5**, timing out in camera 1073 before geometry, without an ASan report. A heavily instrumented polygon-entry/return run instead stops in action-channel handling at `FUN_0042c790` (`/tmp/e2-lighting-trace.log`); it records 768 polygon returns but **zero lighting calls**, so it is not lighting-path proof. Timing-dependent gated failures remain; GDB's shell exit 0 is not a successful game run.

Next: [Task 11 — recover dirty-rectangle copy inputs](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-11-recover-dirty-rectangle-copy-inputs.md). Task 10 is complete for the bounded flat-polygon lighting inputs; Task 02 remains active for geometry and visible Joe. Action indexing stays opt-in. The default F5 route still exposes action error 384 and the unintended rooftop transition recorded in the user's screenshots.

Regression risk: passing this block exposes further framebuffer, action and rasterization failures. Textured lighting, general matrix wrappers, vertex generation and full color fidelity remain incomplete. No screenshot or framebuffer hash is claimed as proof of a rendered hero.
