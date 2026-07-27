# Define Replaceable Host Backend Boundary

Status: completed
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Define the boundary between game-facing compatibility semantics and replaceable host backend services, then make the smallest code/documentation move that lets future SDL or alternate Linux backend work plug in without disturbing reconstructed game logic.

## Why This Step Exists

The runtime now reaches a controllable scene under repeatable debug/ASan probes. The next architectural risk is that X11 window/input details, framebuffer dump helpers, timing, and future presentation/audio work could grow directly into compatibility shims. Step 12 exists to name the ownership layers before adding more host behavior.

## Scope

1. Inventory the current host-facing surfaces in `E2Recomp/platform/e2recomp_win32_compat.*` and `E2Recomp/native/e2recomp_native_main.c`.
2. Define which calls are game-facing Win32/DirectDraw/DirectSound compatibility semantics and which are host backend services.
3. Introduce a narrow backend boundary only where it reduces immediate coupling; avoid moving behavior speculatively.
4. Keep the Step 11 regression script passing after any code movement.

## Out Of Scope

1. Implementing an SDL backend.
2. Replacing the current X11 scaffold.
3. Changing reconstructed game logic or probe evidence.
4. Pixel-perfect presentation or audio fidelity work.

## Usage Budget

Stay within the parent implementation's daily 5% weekly usage burn limit. If boundary work becomes a broad refactor, split a smaller task first.

## Temporary Sacrifices

1. Sacrifice: Keep the current X11 dynamic-loading scaffold as the only real host window backend during this step.
2. Why accepted now: Runtime behavior is stable and protected; replacing X11 before defining the seam would mix design and migration risk.
3. Removal trigger: A later SDL backend step has a documented backend interface and matching regression coverage.

## Acceptance Criteria

1. The implementation document names Step 12 as active and Step 11 as completed.
2. The current backend ownership inventory is documented.
3. Any introduced backend API has one owner, one current implementation, and preserves existing behavior.
4. `scripts/run-e2-runtime-regressions.sh` passes after changes.

## Tasks

1. [Inventory Backend Ownership](tasks/task-01-inventory-backend-ownership.md) - completed; record what belongs to compatibility, probes, and host backend.
2. [Extract Window Input Backend](tasks/task-02-extract-window-input-backend.md) - completed; move X11 window/input details behind `e2recomp_host_backend.*`.
3. [Define Remaining Backend Contracts](tasks/task-03-define-remaining-backend-contracts.md) - completed; specified timing, presentation, and audio ownership before implementation.
4. [Close Backend Boundary Step](tasks/task-04-close-backend-boundary-step.md) - completed; verified regressions and prepared Step 13 handoff.

## Verification

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build build/linux-clang32-asan`
4. `scripts/run-e2-runtime-regressions.sh`
5. `git diff --check`

## Notes

Current ownership shape:

1. `E2Recomp/platform/e2recomp_win32_compat.h` defines the game-facing compatibility API and Win32-like types consumed by reconstructed code.
2. `E2Recomp/platform/e2recomp_win32_compat.c` owns compatibility semantics: HWND stubs, message queue, Win32 message dispatch, legacy address mapping, filesystem/path shims, timers, memory, and pointer-probe helpers. Before this step, it also owned X11 dynamic loading/window polling.
3. `E2Recomp/native/e2recomp_native_main.c` owns developer probes: frame/surface dumps, key-injection workflows, gameplay/requester waits, and command-line probe entry points.
4. The first practical boundary candidate is host window/input polling below the compatibility message queue. The queue and `WM_KEYDOWN` semantics are compatibility behavior; X11 display/window/key-symbol details are backend behavior.

## Current Evidence

The first Step 12 slice introduced:

```text
E2Recomp/platform/e2recomp_host_backend.h
E2Recomp/platform/e2recomp_host_backend.c
```

The new backend API owns host window creation, show/destroy operations, and host event polling:

```text
E2R_HostCreateWindow
E2R_HostDestroyWindow
E2R_HostShowWindow
E2R_HostPollEvents
```

`E2Recomp/platform/e2recomp_win32_compat.c` still owns the game-facing HWND stub, message queue, `PeekMessageA`/`GetMessageA`, `DispatchMessageA`, and `WM_KEYDOWN` semantics. The X11 dynamic loader, display/window state, key-symbol mapping, and X11 event loop now live below the backend boundary.

## Backend Contracts

The remaining backend boundary should expand only where a host-specific implementation is required. The compatibility layer remains responsible for the game-facing API shape and return semantics.

### Timing

Current state:

1. `Sleep`, `GetTickCount`, `timeGetTime`, `SetTimer`, and `KillTimer` live in `E2Recomp/platform/e2recomp_win32_compat.c`.
2. `Sleep` currently maps directly to `usleep`.
3. `GetTickCount`/`timeGetTime` currently return coarse wall-clock milliseconds.
4. `SetTimer`/`KillTimer` are compatibility stubs and do not schedule backend callbacks.

Ownership decision:

1. The Win32 function names and return semantics stay in the compatibility layer.
2. Host waiting and monotonic-time reads may become backend services when SDL or another backend needs to own event-loop timing.
3. Timer callback delivery is deferred until a runtime path proves it is needed; it should be added as a compatibility behavior backed by host timing, not as direct SDL calls from reconstructed logic.

Potential backend API, deferred:

```text
E2R_HostSleepMilliseconds
E2R_HostMonotonicMilliseconds
```

### Presentation

Current state:

1. Legacy framebuffer pages are still the reconstructed runtime's compatibility-facing state: `_DAT_00636150`, `_DAT_00636154`, `_DAT_00636158`, `_DAT_0063615c`, `_DAT_006401ec`, `_DAT_006401d4`, and `DAT_0047a279`.
2. `E2Recomp/native/e2recomp_native_main.c` owns developer-only PGM frame and surface dumps.
3. The Step 11 regression proof depends on surface dump summaries and should remain independent of live host presentation.

Ownership decision:

1. Legacy framebuffer page selection and DirectDraw-like semantics stay in compatibility/reconstructed state until recovered more precisely.
2. Host presentation belongs behind the backend boundary and should consume already-established framebuffer/palette state.
3. Probe dumps remain developer tooling and must not be replaced by live presentation.

Potential backend API, deferred to Step 13 task 03:

```text
E2R_HostPresentIndexedFrame
```

### Audio

Current state:

1. `midiOutGetNumDevs`, `midiOutGetDevCapsA`, and MMIO helpers live in `E2Recomp/platform/e2recomp_win32_compat.c`.
2. MIDI device enumeration currently reports no devices.
3. MMIO helpers provide file-oriented compatibility behavior used by legacy resource/audio paths.
4. DirectSound fidelity is not yet recovered enough to specify a full host mixer contract.

Ownership decision:

1. MIDI, MMIO, DirectSound, and wave-style API shapes stay in compatibility.
2. Actual audio device creation, buffer submission, and mixing belong behind backend APIs once a real runtime path needs them.
3. SDL audio should not be introduced until a focused audio task names the compatibility calls it backs.

Potential backend API, deferred:

```text
E2R_HostAudioInit
E2R_HostAudioSubmit
E2R_HostAudioShutdown
```

Deferred risks:

1. Presentation may expose palette/page-flip fidelity issues that belong to DirectDraw compatibility, not the backend.
2. Timer callbacks may require recovered Win32 message semantics before backend timing is useful.
3. Audio may need original DirectSound buffer semantics before an SDL queue can be correct.

Verification passed after the move:

```text
cmake --build --preset linux-clang32-debug
cmake --build build/linux-clang32-asan
scripts/run-e2-runtime-regressions.sh

Runtime regressions passed.
Debug log: /tmp/e2-step11-regression-debug.log
ASan log: /tmp/e2-step11-regression-asan.log
```

Final Step 12 verification also passed before closure:

```text
scripts/run-e2-runtime-regressions.sh

Runtime regressions passed.
Debug log: /tmp/e2-step11-regression-debug.log
ASan log: /tmp/e2-step11-regression-asan.log
```

## Change Log

### 2026-07-27

1. Created Step 12 after Step 11 completed repeatable runtime-loop regression checks.
2. Moved X11 host window/input handling behind `e2recomp_host_backend.*`, leaving Win32 compatibility message semantics in `e2recomp_win32_compat.c`.
3. Reverified debug/ASan builds and the Step 11 regression script after the backend seam.
4. Completed the remaining backend contract inventory for timing, presentation, and audio without adding speculative APIs.
5. Closed Step 12 after the backend ownership inventory, first host seam, remaining contract notes, and final runtime regression verification were complete.
