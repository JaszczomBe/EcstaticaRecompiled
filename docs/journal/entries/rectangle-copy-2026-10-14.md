# 2026-10-14 — Dirty-rectangle copy inputs and surface ownership

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Area: `FUN_00418484`, `FUN_00418514`, their four callers and directly required lock/unlock inputs.

Symptom: gated actor recovery reached framebuffer copying with lost surface/row state. The worktree already contained the documentation and original-video analysis from this session; those changes are preserved.

## Original Evidence And Repair

Original `0x418484..0x418588` takes **EAX surface, EDX X, EBX Y, ECX width and one stack height**. Both reconstructed helpers now receive those inputs explicitly. The high-resolution source is `_DAT_00636158` with pitch `DAT_00477060`; destination base/pitch come from `FUN_00418a04`. Copy order remains forward bytes. Zero/negative height still follows the original lock/unlock behavior. The planar branch retains 80-byte row strides and four-pixel horizontal group rounding rather than borrowing high-resolution pitch/clipping rules.

The four direct calls at `0x421bf5`, `0x421e11`, `0x424c95`, and `0x455340` all supply the opposite physical page and their actual row. Actor/dirty-list rectangles retain signed coordinates and inclusive endpoints; the text-row call restores its saved row, and the UI rectangle call restores its saved Y. Original `0x424c17..0x424c1e` complements the current page before calling the copy. A new original-instruction caller fixture caught an initially incorrect current-page interpretation; that repair is corrected before final validation.

Original Lock `0x418a07..0x418a38` preserves its selector across clearing a **108-byte mapped descriptor at `0x636864`**. The reconstruction previously passed lost clear arguments, used an independent host scalar as the descriptor and read separate host globals as pitch/base. It now clears/passes the mapped descriptor and reads mapped `+0x10` pitch / `+0x24` base. Existing cached-surface guards remain. Original Unlock `0x418b00..0x418b97` receives the saved selector and returned base; the C now initializes that selector and removes a spurious third COM argument. Surface-lost restore/retry flow is preserved.

The planar setup helper `FUN_0045cf10` now receives its mask. Both original direct callers (`0x417772`, `0x4184b5`) pass `0xf`; its port sequence and reset are retained. This is no implementation of VGA hardware emulation.

All changes, including the three revised prototypes, reproduce from checked, function-scoped patches in `GenerateRecon.js`. No action gate, actor position, scene selection or broad invalid-pointer skip is added.

## Bounded Original-Code Comparison

`scripts/check-e2-rectangle-copy.py` copies original instructions into a temporary i386 harness and runs the original copy, Lock/Unlock and dirty-list dispatch routines. COM surface methods and privileged port/CRT operations are mocked; originals use their register/stdcall contracts while recovered C uses the native compatibility calling convention.

Both normal and ASan runs pass:

- **2,048 copy/ownership cases:** planar/high-resolution dispatch, front-page flag 0/1, selectors 0–3, aligned/odd/zero widths, zero/negative heights, nonzero X/Y, asymmetric pitches, forward overlap in both directions, full-buffer/padding comparison, descriptor clear, matched lock/unlock base/object, surface-lost retries and port writes.
- **256 dirty-list dispatch cases:** original `FUN_00424bd8`, four mixed valid/invalid rectangles per case, signed bounds, inclusive extents and opposite-page selection.

These comparisons prove the bounded C contract with working mock surfaces. They do not establish valid living-actor vertices, real host surface storage or rendered pixels in the runtime. The other three direct call sites have disassembly/input audits, not full original-caller execution fixtures.

```sh
python3 scripts/check-e2-rectangle-copy.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-rectangle-copy.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
node --check E2Recomp/tools/GenerateRecon.js
node E2Recomp/tools/GenerateRecon.js .
cmake --build --preset linux-clang32-debug -j 4
cmake --build --preset linux-clang32-debug-asan -j 4
cmake --build --preset linux-clang32-sdl-debug -j 4
cmake --build --preset linux-clang32-sdl-debug-asan -j 4
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_REGRESSION_TMP=/tmp/e2-rectangles-final-regressions scripts/run-e2-runtime-regressions.sh
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_CONTROL_MATRIX_TMP=/tmp/e2-rectangles-final-matrix scripts/run-e2-control-matrix.sh
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl/e2recomp --output /tmp/e2-rectangles-final-requester-debug
python3 scripts/check-e2-postintro-requester.py build/Debug/clang21-i386-sdl-asan/e2recomp --output /tmp/e2-rectangles-final-requester-asan
```

Four builds, the default regression wrapper, all eight arrow rows and both SDL requester checks pass on the final source. Final full-runtime probes ran serially. An initial SDL build found stale generated PCH files after a system-header mtime change; invalidating only those Debug/ASan PCH artifacts and rebuilding resolved it. No compiler flags or dependency source were changed.

Generator syntax and four-artifact scratch parity pass; regeneration has no unrelated C/header drift. Final scratch evidence after the opposite-page correction is `/tmp/e2-rectangle-final-parity-qbu5m946`. The source contains no generated globals/name-map changes. `git diff --check` and all 209 local Markdown link targets in changed documents pass.

## Real Runtime Result And Next Boundary

```sh
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 E2R_STARTUP_LOGO_DELAY_MS=0 timeout 55 gdb -q -batch -ex 'set pagination off' -ex run -ex 'bt 12' -ex 'info locals' --args build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-rectangles-final-gated 40 7000
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 E2R_STARTUP_LOGO_DELAY_MS=0 timeout 45 build/Debug/clang21-i386-sdl-asan/e2recomp --auto-scene175-visibility /tmp/e2-rectangles-final-gated-asan 35 7000
```

Final gated Debug still catches **SIGSEGV in `FUN_00418514`**, now with coherent inputs **surface=0, X=284, Y=254, width=1, height=1**, and explicit **destination base=0, pitch=0**. The source pointer is nonzero. GDB's shell exit 0 is not a passed game run. The actual copy has not completed and no scene-ready capture is accepted.

The remaining provider is identifiable in `E2Recomp/reconstructed/E2Recomp_stubs.c`: `DirectDrawCreate` fills `E2R_surf_obj` with `E2R_DD_Generic`; CreateSurface returns that shared object, and only SetPalette gets a specific surface implementation. **Lock (slot 25), Restore (27) and Unlock (32) remain generic no-ops.** Lock reports success but never populates storage/pitch. This is a separate compatibility failure, split into [Task 12 — recover DirectDraw surface Lock](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-12-recover-directdraw-surface-lock.md), rather than hiding the invalid destination or fabricating its address in game logic.

Final gated SDL ASan exits **5**, timing out after 35 seconds in camera **1073**, with no ASan report. It does not reach the copy path and supplies no full-route memory-safety proof. Existing default action-error/OK/Escape regressions remain passing; manual F5, valid actor geometry, release animation and gameplay remain unproven.

## Probe Interpretation And Regression Risk

The user clarifies that **all three logos are advanced by skip taps and the horseback first intro is cut short by another tap**. Recorded startup/intro timings are therefore not natural durations. Future skip probes must distinguish those stages, release taps and wait on actual scene/action/HUD checkpoints through the pedestal sequence. The commands above intentionally accelerate logo delays, wait for camera 1073 before the existing Space injection and then wait for scene/action readiness; they do not test key-driven logo skipping or natural timing. Copy arithmetic fixtures have no startup/input timing dependency.

Risk: fixing the shared descriptor/selector helpers can expose other unrecovered caller arguments and real DirectDraw/blit lifetime defects. Keep those failures distinct from this copy contract and from already incomplete vertex generation, lighting, actor placement and children. Task 11's input repair is implemented; full-route execution awaits Task 12's actual provider, then Task 02/05/01 validation resumes.
