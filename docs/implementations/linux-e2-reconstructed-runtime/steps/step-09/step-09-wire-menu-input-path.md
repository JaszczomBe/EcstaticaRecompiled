# Wire Menu Input Path

Status: active
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-17

## Goal

Map enough host keyboard or mouse input into the reconstructed Win32-style input path to navigate past the inspectable title/menu state.

## Why This Step Exists

Step 8 proved the runtime is presenting a real Ecstatica II title-logo frame in memory. The next proof is interaction: recover how the original loop consumes keyboard/mouse state and feed it from the Linux host without hardwiring reconstructed game logic to a final backend.

## Scope

1. Trace the current input globals and message paths around `E2R_WndProc`, `PeekMessageA`, and the `DAT_006368xx` input flags consumed by `FUN_00415d40`.
2. Add the smallest host-side input bridge needed to trigger one menu/title transition.
3. Keep the bridge behind compatibility or native launcher code, not inside recovered game logic unless the change repairs a decompiler artifact.
4. Preserve `--dump-frame` as the visual verification probe.
5. Document the first navigated state or the next concrete input frontier.

## Out Of Scope

1. Full keyboard/mouse coverage.
2. Configurable key binding UI.
3. SDL backend replacement.
4. Gameplay scene control polish.

## Starting Evidence

Step 8 ASan probe:

```text
./e2recomp --dump-frame /tmp/e2-step08-frame-asan.pgm 5
wrote frame dump: /tmp/e2-step08-frame-asan.pgm (surface 3)
```

The dumped frame is a valid `640x480` PGM showing the Ecstatica II title logo.

## Current Evidence

The first bounded input bridge maps `WM_KEYDOWN` through the Win32 compatibility message path:

1. `PostMessageA`, `PeekMessageA`, `GetMessageA`, and `DispatchMessageA` now use a small compatibility queue instead of dropping messages.
2. `RegisterClassA` remembers the recovered window proc for `DispatchMessageA`.
3. The recovered keydown table maps `VK_ESCAPE` to `DAT_00636844`, the flag consumed by the title/menu wait and requester path.
4. The bridge also covers recovered command/movement flags including `VK_SPACE -> DAT_00636850`, `Q -> DAT_00636853`, and numpad movement keys into the `DAT_00636854..5c` cluster consumed by `FUN_00415d40`.
5. The X11-backed host window selects keypress events and polls them before `PeekMessageA`/`GetMessageA`, translating X11 keysyms into the recovered virtual-key table.
6. `--inject-key-dump <path.pgm> <key|vk> [inject_seconds] [dump_seconds]` posts one key through the queue, drains one queued probe message, then writes the existing bounded frame dump.
7. `--dump-surfaces` and `--inject-key-surfaces`/`--inject-key-sequence-surfaces` dump all four legacy framebuffer pages with a per-surface hash.

ASan probe from `build/linux-clang32-asan` on 2026-07-17:

```text
./e2recomp --inject-key-dump /tmp/e2-step09-escape-hostpoll.pgm escape 2 3
Ecstatica II data: /home/rgrabowski/Work/EcstaticaRecompiled/build/linux-clang32-asan/Ecstatica2
posted key 0x1b through the Win32 message queue
dispatched one queued probe message
input state after dispatch wait: keydowns 0->1 last_key=0x1b DAT_00636844=1 DAT_00636853=0 DAT_00479de8=1 move=[0,0,0,0,0,0,0,0,0] DAT_0047a76c=1 DAT_0047a43c=4 _DAT_0073cc3c=0x0
wrote frame dump: /tmp/e2-step09-escape-hostpoll.pgm (surface 3)
input state: DAT_00636844=0 DAT_00636853=0 _DAT_00643650=5 DAT_00479de8=1 DAT_0047a76c=1 DAT_0047a43c=4 DAT_0047a730=0 DAT_00479de4=0 DAT_0047a788=1 _DAT_00636690=0 _DAT_0073cc3c=0x0 move=[0,0,0,0,0,0,0,0,0]
```

Movement probe from the same ASan build:

```text
./e2recomp --inject-key-dump /tmp/e2-step09-num8-hostpoll.pgm num8 2 3
posted key 0x68 through the Win32 message queue
dispatched one queued probe message
input state after dispatch wait: keydowns 0->1 last_key=0x68 DAT_00636844=0 DAT_00636853=0 DAT_00479de8=1 move=[1,0,0,0,0,0,0,0,0] DAT_0047a76c=1 DAT_0047a43c=4 _DAT_0073cc3c=0x0
```

The injected and no-input control dumps at three seconds are byte-identical, so the events now reach the compatibility queue, `DispatchMessageA`, `E2R_WndProc`, and recovered input globals, but have not yet produced a visible title/menu transition. The host window now has a real keypress poll path; the remaining frontier is repeated/timed event delivery far enough to drive a visible title/menu transition.

Surface probe from the same ASan build:

```text
./e2recomp --inject-key-sequence-surfaces /tmp/e2-step09-surfaces-seq-esc-num8-space escape,num8,space 2 250 5
posted key 0x1b through the Win32 message queue
input state after dispatch wait: keydowns 0->1 last_key=0x1b DAT_00636844=1 ...
posted key 0x68 through the Win32 message queue
input state after dispatch wait: keydowns 1->2 last_key=0x68 ... move=[1,0,0,0,0,0,0,0,0] ...
posted key 0x20 through the Win32 message queue
input state after dispatch wait: keydowns 2->3 last_key=0x20 ...
wrote surface dump: /tmp/e2-step09-surfaces-seq-esc-num8-space-s0.pgm (surface 0 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step09-surfaces-seq-esc-num8-space-s1.pgm (surface 1 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step09-surfaces-seq-esc-num8-space-s2.pgm (surface 2 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step09-surfaces-seq-esc-num8-space-s3.pgm (surface 3 nonblank=1 hash=6e39f5ea)
```

Requester surface probe from the same ASan build after raw requester-record and item-list repair:

```text
./e2recomp --inject-key-sequence-surfaces /tmp/e2-step09-requester-stringraw-esc-num8-space escape,num8,space 2 250 5
wrote surface dump: /tmp/e2-step09-requester-stringraw-esc-num8-space-s0.pgm (surface 0 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step09-requester-stringraw-esc-num8-space-s1.pgm (surface 1 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step09-requester-stringraw-esc-num8-space-s2.pgm (surface 2 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step09-requester-stringraw-esc-num8-space-s3.pgm (surface 3 nonblank=1 hash=9042c4ed)
input state: ... requester=[ce58=6 id=0x27 mode=5 b384=9 bad=9 ptr=0x47a588 b9bc=18 item=0x643780 bd4c=9 key=0x0] ...
```

This proves the path now reaches `FUN_0043ce58`, resolves the requester parent record through `FUN_0043aeac`, renders requester items through `FUN_0043b9bc`, and produces a changed surface-3 framebuffer hash. The next implementation target is requester fidelity and non-ASan timing: the normal debug build still misses this path at the old two-second injection timing and can hit an immediate exit-112 path with later injection.

## Acceptance Criteria

1. Debug and ASan builds compile.
2. A bounded run can inject or receive one meaningful input event.
3. A frame dump, log, or documented state change proves the event reached the reconstructed menu/title path.
4. Any reconstructed C hand fix is mirrored in `E2Recomp/tools/GenerateRecon.js`.

## Verification

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build build/linux-clang32-asan`
4. `./e2recomp --inject-key-dump /tmp/e2-step09-escape-hostpoll.pgm escape 2 3` from `build/linux-clang32-asan`
5. `./e2recomp --inject-key-dump /tmp/e2-step09-num8-hostpoll.pgm num8 2 3` from `build/linux-clang32-asan`
6. `./e2recomp --dump-surfaces /tmp/e2-step09-surfaces-control 3` from `build/linux-clang32-asan`
7. `./e2recomp --inject-key-sequence-surfaces /tmp/e2-step09-surfaces-seq-esc-num8-space escape,num8,space 2 250 5` from `build/linux-clang32-asan`
8. `./e2recomp --inject-key-sequence-surfaces /tmp/e2-step09-requester-stringraw-esc-num8-space escape,num8,space 2 250 5` from `build/linux-clang32-asan`

## Change Log

### 2026-07-17

1. Added minimal Win32 key constants and mapped `WM_KEYDOWN` through `E2R_WndProc` to recovered `DAT_006368xx` input globals, including `Escape -> DAT_00636844`, `Q -> DAT_00636853`, and numpad movement flags.
2. Added a small Win32 compatibility message queue for `PostMessageA`, `PeekMessageA`, `GetMessageA`, `DispatchMessageA`, `PostQuitMessage`, and `RegisterClassA` window-proc dispatch.
3. Added X11 keypress polling before `PeekMessageA`/`GetMessageA`, translating host keysyms into recovered virtual keys without adding an Xlib build dependency.
4. Added `--inject-key-dump` as a bounded native launcher probe that posts and dispatches one key through the compatibility queue, logs input state, and preserves the Step 8 frame-dump artifact.
5. Added all-surface and key-sequence surface probes, then fixed probe dispatch to remove exactly one queued message with `PM_REMOVE`.
6. Verified debug and ASan builds, plus ASan Escape, num8, and `escape,num8,space` injections showing `E2R_WndProc` keydowns, recovered key IDs, and expected input flags after dispatch.
7. Recorded that all four surface hashes are unchanged from the no-input control; the next work is requester/menu presentation rather than hidden framebuffer-page selection.
8. Added a legacy key queue bridge for `WM_KEYDOWN`/`WM_KEYUP`/`WM_CHAR`, feeding the recovered `0x004c3890`, `0x004c3990`, `0x004c3a90`, `0x004c3b90`, and `0x00507490` queues.
9. Instrumented requester entry, renderer, item renderer, and key handler counters, then fixed raw-address rewrites for the `0x00ac4xxx`, requester-record, input-queue, and menu-label tables.
10. Recovered enough requester rendering to traverse 18 item draws under ASan and produce a changed surface-3 hash (`9042c4ed`) for the `escape,num8,space` sequence; normal debug timing remains a frontier.

### 2026-07-16

1. Created after Step 8 captured a real title-logo frame from the ASan build.
