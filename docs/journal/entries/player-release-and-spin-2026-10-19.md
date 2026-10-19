# 2026-10-19 — SDL Arrow Release, Frame Clock And Target Facing

Area: Step 09 Task 02, the user's manual spinning/circling report and `FUN_0042ed6c` crash.

Three recovered contracts address the report: actual SDL arrow release now clears the held key, the update loop again waits for a real clock change, and the target-facing caller/helper retain actor, elapsed time, range and angular inputs. Earlier direct-WndProc probes supplied complete key metadata and therefore missed the actual SDL release defect. Full control, collision, traversal and sustained experimental ASan acceptance remain open.

## SDL Release Reproduction And Repair

SDL sends both keyboard message types through `e2r_queue_host_message` with zero lParam. `E2R_feed_legacy_keydown` infers an extended arrow from its virtual key, setting the held byte at `0x4c3a90 + scan`. Key-up inferred the scan but selected the regular table `0x4c3b90`, leaving the arrow held. Right Alt had the same asymmetry; keypad aliases also set both held tables on press but cleared only one on release.

The actual SDL-event replay in `/tmp/e2-spin-sdl-release-before2.log` reaches:

```text
SDL_EVENT_KEY_UP → VK_LEFT → WM_KEYUP, lParam=0
WndProc did not update the requested held-key byte
```

Its saved Left-held packet has Left=1. The earlier first attempt (`/tmp/e2-spin-sdl-release-before.log`) stopped on a debugger `free` return-type issue before testing release and is superseded.

The hand-maintained compatibility bridge in `E2Recomp_stubs.c` now selects the same table on release as on press and clears the mirrored keypad held byte. Press queues remain available for their existing consumers. The SDL backend and reconstructed gameplay selection are unchanged by this bridge repair; no direct SDL calls enter game logic. The generator does not write this compatibility source.

`check-e2-key-release.py` compiles production scan mapping, the press-held fragment and release function. **114 cases pass normally and under ASan**: arrows, right/left Alt, modifiers, ordinary keys and nine keypad aliases; absent, partial and full message metadata; single/repeated presses, repeated releases and unrelated held-byte preservation.

The motion probe now has `--sdl-events`, `--release-turn-first` and `--move-key up|down`. SDL mode allocates only an event, sends SDL_PushEvent and runs the actual host pump/callback/WndProc path. It verifies the held byte after every press and release. No actor, action, camera or wait state is written.

## Frame Clock Evidence

The reconstructed `0x42a70c` loop previously broke its clock wait after **65,536 polls**, even when the clock had not advanced. A 900-update trace (`/tmp/e2-spin-ticks-debug-ticks.json`) records **566 poll-limit exits**, **570 zero-time actor updates**, and **173 zero-time facing changes**. For example, a retained motion distance of 16 repeatedly produces -256 facing changes at elapsed time 0 while turn+Up remains held. More CPU iterations could therefore amplify turning independently of elapsed game time.

Original **0x42a73e..0x42a74e** keeps polling until the clock changes. The poll-count escape is removed; clock calls receive deterministic unused arguments. The original slowdown and one-time resource-load tick reset remain intact. This is a recovered simulation wait, not an SDL frame-rate cap or an arbitrary turn-speed clamp. Some zero-time updates remain legitimate at the original resource-load reset; do not assert that every zero delta is a defect.

`check-e2-frame-clock.py` compares the production wait/tick fragment with original `0x42a720..0x42a7d1`, intercepting only the clock leaf. **560 cases pass normally/ASan**, including 100,000 unchanged polls, tick deltas 1/2/3/20, slowdown, reload reset and pending transition countdown. This proves the wait/bookkeeping contract, not full host cadence.

## Reported Target-Facing Crash

Original **0x429b1f..0x429b2a** passes range **0x500 in EBX**, the retained actor in EAX and elapsed time in EDX. Reconstruction passed a direction temporary as actor, omitted range, and the helper used uninitialized `in_EAX`/`unaff_EBX`. Its subsequent angle/distance calculation also used a phantom ECX after the legacy angle wrapper.

The caller now passes Joe, elapsed time and explicit range. `FUN_0042ed6c` retains those inputs and uses the independently recovered angle implementation while retaining the actual X delta. The target filters, candidate ranking, range/height checks, action-progress interpolation and final facing write remain original-shaped. No target-selection bypass or pointer guard replaces the computation.

`check-e2-target-facing.py` compares the production helper with original `0x42ed6c..0x42efdb` and the actual caller with its instruction block. **49,152 helper cases and 12,288 caller cases pass normally/ASan**, covering actor lists, representation/flag exclusions, ranges, height/direction differences, action durations and progress. These are synthetic actor fixtures. The normal cylinder replays do not establish that this conditional target-facing branch is reached with the same world state as the user's crash; its recovered input contract is the evidence for this repair.

## Bounded Gameplay Results And Remaining Steering

The initial post-clock probes hold a turn for 300 updates, add Up/Down for 300, then release for 300. Both Debug/ASan Left+Up and Right+Down complete (`/tmp/e2-spin-after-{debug,asan}-{left-up,right-down}`). The Left-only endpoints match across Debug/ASan: position 9878,3328,-17406 and facing -7195. Moving farther changes floor height to 4096 in those Left+Up runs; this is actual query state, not a substituted height. No view crossing/return is established.

Final SDL-event probes release the turn key, wait 150 updates, press Up/Down for 150, then release and wait another 150. All four complete, with every released held byte zero and wait/modal zero. Prefixes `/tmp/e2-spin-sdl-{debug,asan}-{left-up,right-down}` contain JSON and normal presentation packets.

| Runtime / route | After turn release | After movement release |
| --- | --- | --- |
| Debug Left → release → Up | 9916,3328,-17406; facing -13205 | 8892,3328,-18403; facing -27541 |
| ASan Left → release → Up | 9916,3328,-17408; facing -14601 | 8840,3328,-18481; facing -30473 |
| Debug Right → release → Down | 9912,3328,-17408; facing -12624 | 9077,3328,-18204; facing 8368 |
| ASan Right → release → Down | 9912,3328,-17408; facing -11839 | 9025,3328,-18225; facing 8641 |

Turn release preserves its facing throughout the no-input phase, and later release also settles facing. Down now has substantial displacement in the longer real-tick probe, superseding the earlier short/no-displacement observation. Up/Down still change facing while moving despite cleared Left/Right bytes. The caller-traced repeat `/tmp/e2-spin-sdl-steering-asan` completes and identifies all 39 turns as **FUN_00448cb4** (36 at -512, three at +512). Its blocker/tangent branch requires real-map ownership evidence before claiming straight forward/backward controls or complete elimination of circling. [Task 07](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-07-recover-motion-query-steering.md) owns that next bounded family. Raw final angles wrap and are not a turn-rate measurement.

```sh
python3 scripts/check-e2-key-release.py
python3 scripts/check-e2-key-release.py --asan
python3 scripts/check-e2-frame-clock.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
python3 scripts/check-e2-target-facing.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --sdl-events --turn-forward left --release-turn-first --frames 150 \
  --output /tmp/e2-spin-sdl-asan-left-up
```

These startup probes use zero logo delay and a timed Space, followed by the observed courtyard release checkpoint. They do not reproduce the recording's two launches, individual logo taps or natural shortened horseback timing. Cylinders/mesh bypass and automatic background-spawn deferral stay explicit; NPC activation remains incomplete. No 60-second-after-readiness/traversal or full experimental ASan acceptance is claimed.

## Verification And Worktree

All four X11/SDL Debug/ASan builds pass. The existing action motion, interpolation, reset, idle caller, representation/keys, forward-turn caller, root-pose and motion-query comparisons pass normally/ASan. Generator syntax/in-place generation, independent four-artifact parity and whitespace checks pass. Reconstructed changes from this continuation are limited to the clock wait, target-facing caller/helper/prototype and compatibility release bridge; new reconstructed behavior is mirrored in `GenerateRecon.js`.

Final baseline logs are `/tmp/e2-spin-final-regression.log`, `/tmp/e2-spin-final-controls.log` and `/tmp/e2-spin-final-modal-{debug,asan}-driver.log`. All pass, including the eight arrow rows and both SDL requester drivers. The earlier post-clock baseline suite also passed before the release bridge change.

The starting index (`/tmp/e2-spin-start-index.txt`) remains unchanged. Earlier staged/unstaged work is preserved, and no commits were made. Next bounded action is Task 07's motion-query steering with clear turn keys, before accepting straight locomotion, floor/stair collisions and scene traversal.
