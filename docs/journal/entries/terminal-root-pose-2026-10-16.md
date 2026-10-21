# 2026-10-16 — Terminal Root-Pose Ownership

Area: `FUN_0042b004 → FUN_0042b880 → FUN_0042b0f4`, Step 09 Task 02.

The terminal ASan event-link fault is repaired. Debug and ASan now execute the same 30 terminal events and reach the courtyard release. Joe remains immobile; this closes the observed corruption family, not gameplay or full experimental ASan acceptance.

## Writer Evidence And Repair

The original four-flag ASan route reproduced the fault: event `0x776434`, type `0x17`, returned with next link `0x77643a` instead of `0x776442`, then reset read an invalid address. A hardware watch on `*(int *)0x77643e`, installed at `FUN_0042b004`, caught the write in `FUN_00422368(param_1=0x776434,param_2=256)`. Its matrix pointed at the event itself. Stack: rotation → root pose → event 0x17 → action reset → action advance. The link was valid before dispatch; the event parser and reset traversal did not create this corruption.

Original `0x42b143..0x42b18c` sends actor `+6` to identity and Y/X/Z rotations, using angles at `+0x92/+0x90/+0x94`. The attached-root branch at `0x42b26b..0x42b2b4` uses the same offsets on its selected actor. Reconstructed C instead initialized the unrelated global matrix and passed uninitialized `extraout_ECX` destinations to rotations. ASan happened to preserve the event address in one of those stack slots.

Both branches now use the existing `E2R_ApplyEulerMatrix(actor+6,actor+0x90)`. Original `0x42b1f8..0x42b204` and `0x42b320..0x42b32c` also copy live position `+0x84` to saved position `+0x8a`; the reconstruction incorrectly used the final matrix word as the destination. Those two destinations are recovered as part of this helper contract. The matrix copy to `+0xc6` remains intact. Four anchored replacements in `GenerateRecon.js` reproduce the hand repair; there are no event-link pointer guards, forced positions or camera changes.

The caller's existing retained actor context is unchanged. Child conversion through `0x42d860` still has lost inputs and remains outside this bounded repair. Do not interpret these root-pose results as complete hierarchy/root-motion recovery.

## Original-Code Fixture

`scripts/check-e2-root-pose.py` compiles the actual reconstructed helper and matrix/copy leaves into an i386 harness, loads original executable instructions into temporary mappings, and compares all 64 KiB of fixture actor/neighbor memory. It passes **1,152 cases**, normally and with ASan: zero/nonzero Euler angles, root skip flags, absent/inactive/active attached roots, untransformed child bookkeeping, saved matrices/positions and the three camera modes. Neighboring event bytes/links and actor context remain intact. Child world-to-local conversion is deliberately excluded; no original instruction bytes are checked into the repository.

```sh
python3 scripts/check-e2-root-pose.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-root-pose.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
```

The existing action-reset fixture passes 96 cases and interpolation passes 576 cases, each normally and under ASan. Those fixtures retain their existing boundaries; the reset fixture intercepts pose work, while the new fixture validates the real root-pose body.

## Continuous Runtime Result

Matching Debug and ASan probes execute all **30 identical terminal event addresses/types in order**, including `0x776434 → 0x776442` and the wait-ending event `0x7765ca`, then retain camera 175, Joe `9988,3328,-17408`, wait 0/modal 0. Prefixes `/tmp/e2-root-after-debug` and `/tmp/e2-root-after-asan` contain logs and 35-second visibility packets. Both bounded probe processes exit successfully; no sanitizer error appears in the ASan log. The repaired terminal chain occurs about 19 seconds after launch. This is shorter than the required 60 seconds after actual control readiness and has no traversal.

```sh
# Substitute clang21-i386-sdl-asan for the matching sanitizer probe.
env -u DISPLAY SDL_VIDEODRIVER=dummy E2R_STARTUP_LOGO_DELAY_MS=0 \
  E2R_ACTION_INDEX_PROBE=1 E2R_ACTOR_CYLINDERS=1 E2R_PROXY_MESH_BYPASS=1 \
  E2R_DEFER_BACKGROUND_SPAWNS=1 \
  E2R_VISIBILITY_DUMP_PREFIX=/tmp/e2-root-after-debug \
  E2R_VISIBILITY_DUMP_AFTER_MS=35000 \
  timeout 50 build/Debug/clang21-i386-sdl/e2recomp \
  --inject-key-sequence-surfaces /tmp/e2-root-after-debug-surfaces \
  space,space,up 3 10000 44
```

This zero-logo-delay route is a crash probe. It does not reproduce the reference recording's separate logo taps/shortened horseback intro, or validate manual F5 input. The original recording has two launches; use action/release checkpoints rather than absolute video time.

## Motion Inputs And Next Frontier

The repaired route does **not** retain a zero motion-reference field: `FUN_00427584` binds actor `+0x11e` to the loaded representation 67 after release, and a fixed-address watch sees no later clear during the probe. Both continuous packets retain that representation at a valid high hosted address. The separately named `attached_rep=0` field is `+0xf2`, not `+0x11e`. The former handoff's zero-reference observation is superseded for this route; do not populate a replacement pointer based on it.

A separate ASan/GDB probe waits for **hosted symbol** `DAT_0047a76c == 0` and camera pointer `0x67da4c` at `FUN_00415d40`, then sends Up/Left keydown and keyup through `E2R_WndProc`. After 45 update entries per phase, position stays `9988,3328,-17408` and facing stays `-13056`; representation 67 remains bound. Up reaches selected slot **39** at `27584.check-final-gate`, with previous slot 1000/state 4. A first exploratory probe used the mapped original address for the wait flag and stopped too early; only the symbolic-wait rerun at `/tmp/e2-motion-checkpoints-final.log` supplies these post-release observations. Hosted globals and original-address table mappings must be distinguished in GDB conditions.

The selected action remains `0xac263c`, duration 40; its progress is normalized Q16 in `FUN_0042ae80`, so values such as 63882/65520 must not be compared directly with the duration. The earlier suggestion that progress had run far beyond duration is not established. Input latches and a nonzero representation still do not prove movement. Follow selected slot 39 through representation metadata, action lookup/events, root-motion vectors and the real `0x448c1c/0x448cb4` query contract. Record press/release consumption as well as coordinates; do not add host movement or rebind the actor to its renderer tree. Strict completion and retained-slot recovery in `0x42ad60` remain separate source-backed candidates.

## Baseline And Limits

All four X11/SDL Debug/ASan builds pass. Generator syntax, in-place generation, all four scratch artifacts and `git diff --check` pass. The default runtime wrapper (`/tmp/e2-root-regression.log`), all eight arrow rows (`/tmp/e2-root-controls.log`), and both SDL requester checks (`/tmp/e2-root-modal-{debug,asan}.log`) pass. Arrow rows remain input-latch coverage. The new behavior is confined to root-pose destinations, including their attached-root equivalents; generator diff remains small.

Automatic background spawning remains explicitly deferred and displayed as such. Models/HUD, full NPC activation, child world-to-local conversion, actual locomotion/turning, collision and scene traversal remain open. The full experimental ASan runtime is **not** declared passing. No commits or index changes were made in this continuation; it started from clean commit `67ffb9b`.
