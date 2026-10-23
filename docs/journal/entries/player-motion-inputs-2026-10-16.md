# 2026-10-16 — Player Representation And Live Keyboard Inputs

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Area: Step 09 Task 02, Joe's representation selector and player-state-4 keyboard reads.

Joe now receives the source-selected representation, and Up reaches movement event `0x13` and the real world-motion query. Debug and ASan then fail in the unrecovered vector/query contract. Displacement, turning and traversal remain unproven; full experimental ASan runtime acceptance remains open.

## Representation Selection

Before repair, actor `+0x11e` retained representation 67 (`potion`). Its actual archive resource contains only six action mappings, slots 18–23 → action 384. Slot 39 is -1, so the final gate converts the selection to 1000 and retains the default action. A nonzero representation pointer was insufficient to establish usable locomotion metadata.

Original `0x4575c4..0x45777e` runs each frame from `FUN_004211c8`. It selects Joe's representation from the held node/actor, terrain and stance. Reconstruction defects were:

- `0x4575d6` tests the **16-bit actor ID**. The C tested a dword, including Joe's nonzero flag bytes, and returned early.
- Original stance and representation fields are words at `+0x184/+0x122`. Generated dword-array casts accessed `+0x308/+0x244` instead.
- Original transition actions are IDs 3/4 in EAX, with the actor retained in EDX across loading. C passed a stale value and actor pointer as the action ID, then recovered the actor from a phantom return register.

`E2R_SelectPlayerRepresentation` recovers these branches, word fields, mapped action-table lookup and queued action at `+0x126`. The actual courtyard state selects representation **12 (`heropunh`)**, whose slot 39 maps to action 338. This selection follows original inputs; no representation ID is forced.

The repair is gated by existing `E2R_ACTION_INDEX_PROBE`. An initial global implementation made the bare baseline crash during startup on an absent held-node table at `*(actor+0x54)+0x20`. That baseline lacks the recovered action route. The final wrapper preserves its existing implementation when the gate is off, instead of adding speculative node substitutes or broad actor-loading fixes. The four-flag F5 route uses the recovered selector.

## Live Keyboard Ownership

Selector-only Debug/ASan probes still selected slot 39/action 338 before, during and after every arrow press/release. This is **not a walking proof**. Player state 4's keyboard branch read independent generated label objects seeded with nonzero image values; for example `DAT_004c3ac8` was `0x475b3c`. The live scan-code table is mapped memory updated by `E2R_WndProc` in `E2Recomp_stubs.c`.

Original `0x429005..0x42904c` reads packed dwords at `0x4c3ad8/0x4c3ada/0x4c3add/0x4c3ad5`, then shifts to obtain direction bytes. Original `0x4290df` and `0x42914d` test bytes at `0x4c3ac8/0x4c3bba`. Six anchored replacements now read those live addresses. The stale nonzero modifier no longer wins over all arrow inputs. No host-side motion is introduced; the existing WndProc continues to own scan-code press/release updates. The joystick branch is unchanged.

Both repairs are mirrored in `GenerateRecon.js`. The generated diff is confined to this selector/gate and six keyboard reads; it does not regenerate unrelated runtime behavior.

## Original-Code And Baseline Checks

`scripts/check-e2-player-representation.py` passes **10,368 original-i386 selector/queue/owner cases** and **256 original packed-keyboard direction cases**, normally and under ASan. It compiles the production selector and keyboard-load fragment. Selector cases cover absent/non-Joe actors, nonzero flag bytes, held-item variants, stance, terrain/height thresholds, map scale and cached/missing/already-current transition actions. The intercepted loader deliberately changes the global current actor; the original owner must survive. Keyboard cases cover zero, 1, 0x80 and 0xff bytes with nonzero neighboring bytes. This fixture intercepts asset loading and does not prove motion/collision queries.

```sh
python3 scripts/check-e2-player-representation.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-player-representation.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
```

All four final X11/SDL Debug/ASan builds pass. Generator syntax/in-place generation, all four scratch outputs (`/tmp/e2-player-final-generator-htaw5w30`) and diff whitespace pass. Final default wrapper `/tmp/e2-player-livekeys-regression.log`, eight arrow rows `/tmp/e2-player-livekeys-controls.log`, and both `/tmp/e2-player-livekeys-modal-{debug,asan}-driver.log` requester checks pass. These baseline results supersede the recorded initial ungated failure, and remain separate from the experimental motion failure.

## Phase-Aware Motion Probe And Current Failure

`scripts/probe-e2-player-motion.py` waits at `FUN_00415d40` for hosted symbol `DAT_0047a76c == 0` and camera 175, allows representation binding, then sends each arrow's keydown and keyup through the real WndProc, advancing a bounded number of updates. It reads actor/action state and captures normal presentation packets; it does not write actor coordinates, angles, action state, camera or wait flags. A zero exit means the probe completed, never gameplay acceptance. Completed phases are preserved in JSON if a later input faults.

```sh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl/e2recomp \
  --output /tmp/e2-player-livekeys-debug
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --output /tmp/e2-player-livekeys-final-asan
```

This uses zero logo delay and one timed Space as a crash-probe shortcut, then an observed release checkpoint. It does not verify the reference's three logo taps, shortened horseback timing, physical SDL held keys or manual F5 acceptance.

With final reads, the before-input packet is camera 175, Joe `9988,3328,-17408`, facing -13056, wait 0/modal 0, representation 12, previous slot **1000**, input direction 1000 and idle action **871**. Slot 39 still maps to 338 but is no longer spuriously selected at rest. Prefix `/tmp/e2-player-livekeys-final-asan` retains this partial JSON and before packet. Selector-only full-phase captures `/tmp/e2-player-motion-{debug,asan}` are intermediate evidence and do not describe final input behavior.

Up now reaches `FUN_0042b880` event `0x13 → FUN_00448c1c → FUN_00448cb4 → FUN_004272a8`. Debug faults writing through `in_EAX` in `0x4272a8`, with another output passed as `0x170`; ASan reports stack-use-after-return writing a recycled stack address in the same helper. This is a lost-input reconstruction defect, not evidence of a timing-service lifetime bug. Both motion probes correctly fail and do not reach the Up-held or release captures.

Original `0x448cbf/0x448cc1` retains actor EAX in EDI and displacement EDX in ESI. `0x448cc3..0x448ce2` passes a local output at stack `+0xa8` in EAX, actor `+0x170` in EDX and the vector X/Z components in EBX/ECX to `0x4272a8`. The C has no initialized actor/output and still loses transform/vector inputs before this call. [Task 05](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-05-recover-player-motion-vector-ownership.md) owns the next bounded recovery. Do not merely guard the output or skip the query.

Previous staged root-pose work and the index remain unchanged. This continuation is unstaged; no commits were made. Cylinders, mesh/HUD omission and explicit background-spawn deferral remain active prototype limits.
