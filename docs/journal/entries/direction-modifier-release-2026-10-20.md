# Direction Freeze And Modifier Release — 2026-10-20

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

## Result And User Confirmation

A matching immediate post-intro Up+Left failure is reproduced and repaired. **YROT also freezes in this reproduction.** The user subsequently reports **“there are no freezes anymore.”** This confirms the current no-freeze observation; it does not establish every direction/animation contract or full populated-runtime acceptance.

The first-frame and held-through-release probes with only arrow keys continue to turn. A native Wayland ASan replay finally exposes the missing condition: physical Shift/Alt press and release events during the intro leave the gameplay modifier flags set even though SDL has delivered key-up and its keyboard snapshot is empty. Subsequent Up+Left selects action 480/slot 196, keeps yaw at -13056 and moves only a short distance before settling. The projected local +Z line also retains its heading. This explains why fresh arrow-only and dummy-driver probes missed the matching failure.

## Cause And Repair

The hand-maintained compatibility `E2R_feed_legacy_keyup` clears the raw held table but previously omitted the logical modifier flags set by `E2R_WndProc`. Original Win32 `0x458378..0x4583f7` clears logical modifier state as well as held-table entries; its nonextended Alt release clears `0x63684a` at `0x4583e5`. Original scan release `0x45c9e0..0x45ca10` also clears the logical Space/Shift/Control/Alt bytes.

The compatibility bridge now releases the existing hosted Shift/Control/Alt mappings and the conditional X/Z aliases. It preserves unrelated modifiers and the press queues. No change is made to actor steering, root motion, arrow orientation, population flags or generated gameplay code. `GenerateRecon.js` does not write this compatibility source; independent C/header/globals/names generation parity still passes.

`check-e2-key-release.py` now includes 336 logical-modifier release/preservation cases across both control modes, all initial modifier combinations, host metadata variants and repeated releases, alongside its 114 raw held-table cases. Both suites pass normally and under ASan. The unchanged original-x86 forward/turn caller fixture passes 1,296 cases normally and under ASan.

## Repeatable Reproduction And Verification

`probe-e2-player-motion.py --tap-modifiers shift alt` sends actual SDL press/release events before the arrow route and records the logical flags. With the old bridge, both Debug and ASan retain Shift=1/Alt=1 and freeze YROT at -13056 through both held phases. With the repaired bridge, the flags are zero and both builds select forward action 193/slot 180, change yaw/root/motion matrices and displace Joe. All arrow held bytes are zero after release.

| Route | Evidence prefix | Result |
| --- | --- | --- |
| First-frame Up+Left, no modifier history | `/tmp/e2-direction-oct20-initial` | Turns; no reproduction |
| Keys held while restrained, Debug/ASan | `/tmp/e2-direction-oct20-held`, `/tmp/e2-direction-oct20-held-asan` | Turns after release |
| Natural intro with keys held through release | `/tmp/e2-direction-oct20-natural-held` | Turns after release |
| Native Wayland, original bridge | `/tmp/e2-direction-oct20-wayland-asan` | Frozen YROT; stale modifiers recorded |
| Deterministic modifier taps, original bridge | `/tmp/e2-direction-oct20-modifiers-before-{debug,asan}` | Both reproduce action 480 and frozen YROT |
| Same modifier taps, repaired bridge | `/tmp/e2-direction-oct20-modifiers-after-{debug,asan}` | Both complete held/released phases with turning |
| Native Wayland ASan, repaired bridge, 120 updates per phase | `/tmp/e2-direction-oct20-wayland-after-asan` | Completes; yaw -13056 → 13632 → -31680; release retains -31680 |
| Native Wayland Debug, repaired bridge, 60 updates per phase | `/tmp/e2-direction-oct20-wayland-after-debug-60` | Completes; yaw -13056 → -31472 → 13472; release retains 13472 |
| Native Wayland Debug, repaired bridge, 120 updates per phase | `/tmp/e2-direction-oct20-wayland-after-debug` | Both held phases turn; later released phase crashes in an NPC pose event |
| Ordinary four-arrow route under ASan | `/tmp/e2-direction-oct20-arrows-asan` | Completes; this preceding diagnostic-only check predates the modifier repair |

Example for the repaired runtime:

```sh
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --intro-skip-action 3 --background-spawns \
  --turn-forward left --simultaneous-turn --tap-modifiers shift alt \
  --burst-frames --release-delay 0 --frames 90 --timeout 150 \
  --output /tmp/e2-direction-modifiers
```

Use `--video-driver wayland` to exercise a native desktop window; the default remains dummy SDL. The current SDL build does not include its X11 video driver, so the attempted SDL/X11 desktop replay fails initialization and is not runtime evidence. The separate X11 host-backend builds still compile and pass their baselines.

Desktop libraries also exposed a probe bug: a GDB auto-loaded Python helper overwrote the probe's global `prefix` with `/usr/`. The probe now executes in a private Python namespace. The failed native attempt is `/tmp/e2-direction-oct20-wayland`; the corrected pre-repair Debug replay is `/tmp/e2-direction-oct20-wayland-fixed`.

F12 visibility packets now add Joe's Euler angles, root and motion matrices, motion flags, attachment pointer, clock values and raw held-arrow bytes. These records agree with independent GDB snapshots in Debug/ASan. The existing packet already includes logical Shift/Control/Alt flags. Default F5 F12 captures can therefore distinguish a stopped simulation, stale modifiers, unchanged yaw and a stale projected axis without frame-stepping the runtime.

Final four SDL/X11 Debug/ASan builds, generator syntax, independent four-artifact parity, the baseline runtime wrapper, all eight headless arrow rows and both default SDL requester/OK/Escape checks pass. Final baseline prefixes are `/tmp/e2-direction-oct20-final-{regression,controls,requester-debug,requester-asan}`. No full experimental ASan acceptance is claimed.

## Remaining Populated Frontier And Worktree

The longer native Debug repaired-input route reaches both turning checkpoints, then SIGSEGV during its released phase: `FUN_0042b880 → FUN_0042faf8 → FUN_00424318`, with NPC actor `0xaa8c54` in the update caller. `FUN_00424318` dereferences its unrecovered `in_EAX` at actor +0xf2. This is a failed populated route, not a passing release observation. Recover its original actor/node handoff before extending that event family; do not hide the failure behind the successful bounded ASan route.

Broader population/action coverage, object interactions, combat, articulated collision, original meshes and full experimental ASan remain open. The user's no-freeze confirmation closes the current freeze observation, not those acceptance requirements.

The worktree and index were clean on entry, with local commits `6a3b574` and `fc03cae` already present. This continuation makes no commits or index changes; its changes remain unstaged.
