# 2026-10-16 — Player Motion Vectors And World Query

Area: Step 09 Task 05, action motion event `0x13` through `0x448c1c/0x448cb4`.

Up now changes Joe's real position in both Debug and ASan. A corrected Debug press/release probe also turns Left/Right and stops those changes on release. This is bounded movement evidence, not playable/traversal acceptance: Down has no observed displacement in the short probe, and ASan fails after Up release in a separate gravity/floor path.

## Original Contracts Recovered

- Terminal `0x42baef..0x42bb3c` and interpolated `0x42c97c..0x42ca14` retain the selected actor, optionally select its attached owner, and reset pose with that owner. Three local translation deltas are transformed through **actor `+0xc6`** into a separate contiguous three-word world vector. Interpolation retains its Q14 factor across pose reset. `E2R_ApplyActionMotion13` implements this shared contract and restores the caller's pose context.
- `0x448c21..0x448ca8` retains the actor through both recursive calls. Components exceeding 64 are arithmetically halved and submitted twice; original odd-component truncation is preserved.
- `0x448cbf..0x448ce2` retains actor/vector and passes stack angle output, actor distance output **`+0x170`**, and actual X/Z components. Scoped `E2R_MotionPolar` recovers `0x4272a8`; `E2R_MotionPolar16` recovers the opposite angle convention of `0x427214`. They reuse the independently recovered original angle-table implementation. Other legacy polar callers still have unresolved register inputs.
- `0x448cb4..0x4495dd` now has explicit actor/vector ownership, contiguous sample/target coordinates, actual floor-query actor and terrain-output arguments, and retained obstacle angles/distances. Original non-gameplay modes, actor exclusion/range tests, five perimeter samples, opposing blockers, sliding, turn limits, terrain-state writes and final height acceptance remain active.
- `0x42b074..0x42b0ee` receives its actor explicitly, updates facing/flag, and builds the rotation matrix at **`+0xc6`**. `0x44d2b4` initializes its actor from the event argument. Its separate NPC visibility-return inputs remain outside this Joe-path proof.

Both source and generator contain the repair. No host movement, coordinate substitution, query suppression or camera lock was added.

## Original-Code Fixtures

```sh
python3 scripts/check-e2-action-motion.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-action-motion.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
python3 scripts/check-e2-motion-query.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-motion-query.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
```

All pass normally and under ASan:

| Fixture | Compared cases | Boundary |
| --- | ---: | --- |
| Action motion | 1,920 | Original terminal/interpolated event dispatch and transform versus production helper; attached owners, reset contexts, translation wrap, Q14 factors and matrices. Pose reset, query and visibility are intercepted leaves. |
| Polar outputs | 394 | Original dual-output routines, zero/quadrants, scale limits, signed inputs through ±65535 for scaling and ±32767 for the word entry. SHRT_MIN word-angle inputs are outside the fixture. |
| Split/world query | 92,160 | Complete actor bytes and floor-call coordinates/arguments; six modes, 16 vectors through ±129, collision lists/attachment exclusions, turn/slide matrices and floor thresholds. Floor/terrain service is synthetic and intercepted. |

Existing interpolation (576) and root-pose (1,152) comparisons also pass normally/ASan. The interpolation fixture now explicitly excludes the separately tested motion helper.

## Corrected Input Probe And Runtime Evidence

The previous motion probe sent `WM_KEYUP` with zero `lParam`. Keydown infers extended arrows, but keyup selects its held table from bit 24. Consequently, earlier `/tmp/e2-motion-query-{input,final}-*` runs left Up/Down held and eventually faulted at a simultaneous-input turn caller (`FUN_00427584 → FUN_0042b074`, actor argument 1). They do **not** prove a normal release defect. That simultaneous-input caller remains unrecovered; original `0x429653/0x429687` reloads the actor before its two calls.

The durable probe now sends scan code, extended bit and key-up transition bits, checks the actual held byte immediately, records all four held bytes in phase snapshots, and prints a backtrace on an unexpected stop. It only injects WndProc input; game state remains read-only.

```sh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl/e2recomp \
  --output /tmp/e2-motion-query-release-debug
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --output /tmp/e2-motion-query-release-asan
```

Debug completes all phases, 60 update entries per phase. Camera stays 175, wait/modal remain zero and representation stays 12:

| Phase | Position | Facing | Selected slot / action |
| --- | --- | ---: | --- |
| Before | 9988,3328,-17408 | -13056 | 1000 / 871 |
| Up held | 9921,3328,-17392 | -13056 | 180 / 8 |
| Up released | 9921,3328,-17392 | -13056 | 1000 / -1 |
| Down held | 9921,3328,-17392 | -13056 | 183 / 13 |
| Down released | 9921,3328,-17392 | -13056 | 1000 / 11 |
| Left held / released | 9921,3328,-17392 | -20728 | 181 / 9, then 1000 / 871 |
| Right held / released | 9921,3328,-17392 | -10658 | 182 / 10, then 1000 / 11 |

Raw held bytes match every press/release. Normal presentation packets report Joe at the changed world coordinates with a valid projected cylinder. Down displacement, steady cadence, manual F5, real-map boundary/stair collisions, two camera crossings and 60 seconds after readiness remain unverified. The zero-logo-delay/shortened-intro startup remains a crash-probe shortcut, not the reference recording's two-launch timing.

ASan reaches Up-held position **9759,3328,-17341**, then fails before its released packet. The later actor height is -16000, camera fallback enters scene resource 7, and `FUN_0042b0f4` faults walking children via event `0x16 → FUN_0042ad60 → FUN_004523f8`. A hardware watch identifies the **first** height change in `/tmp/e2-motion-release-watch.log`: `FUN_00449680(actor=0xaa6bd8, factor=6)` writes `local_18=-16000` to actor `+0x86`, called by `FUN_004495e0 → FUN_00427584`. The watched position was `9800,-16000,-17354`. Do not treat the later root-pose fault as the first cause, or clamp the floor/actor height. [Task 06](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-06-recover-release-gravity-query-ownership.md) owns this next bounded family. **Full experimental ASan runtime does not pass.**

## Baseline And Worktree

All four Debug/ASan X11/SDL builds pass. Default wrapper `/tmp/e2-motion-query-regression.log`, all eight arrow rows `/tmp/e2-motion-query-controls.log`, and both SDL requester drivers `/tmp/e2-motion-query-modal-{debug,asan}-driver.log` pass. Generator syntax, regeneration, four-artifact scratch parity and whitespace checks pass; these are separate from the failing experimental runtime.

The starting index remains byte-for-byte unchanged (`/tmp/e2-motion-query-start-index.txt`). This continuation remains unstaged. No commits were made; prior staged work and drafted commit messages are preserved. Cylinders, mesh/HUD omission and automatic background-spawn deferral remain explicit prototype limits.
