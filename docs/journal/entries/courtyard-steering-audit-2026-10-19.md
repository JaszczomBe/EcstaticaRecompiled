# Courtyard Steering Replay And Sustained Observation — 2026-10-19

The user authorized the next bounded Step 09 task after tagging the first playable courtyard milestone. The first differing Debug/ASan steering events now have live input, terrain and original-code replay evidence. **No mismatch was found in this captured steering family.** Both builds also complete a camera round trip followed by 60 seconds with released input, without a required-path crash or sanitizer diagnostic. Complete collision/falling behavior, wider exploration and continuous active-play acceptance remain open.

## First Differing Turn

Initial read-only GDB traces (`/tmp/e2-steering-before-{debug,asan}-queries.json`) begin with identical Joe position `9988,3328,-17408`, facing -13056, radius 256, slot 180, flags 192 and vector `-16,0,5`. The first measured frame delta is **4 ticks in Debug and 5 in ASan**. The next vectors already differ (`-17,0,5` versus `-24,0,7`). These captures therefore do not feed identical time/vector inputs to the query.

| Initial trace | First turn input | Floor blocker | Result |
| --- | --- | --- | --- |
| Debug query 32 | Position `9470,3328,-17254`, vector `-15,0,4` | Side sample `9215,3328,-17286` returns 2688; center returns 3328 | Facing -13056 → -12544 (+512) |
| ASan query 37 | Position `9456,3328,-17250`, vector `-2,0,0` | Center sample `9200,3328,-17250` returns 2688 | Facing -13056 → -13568 (-512) |

Both have only Joe in the actor list and no retained Left/Right input. The sampled height difference is 640, beyond the original 256-unit threshold. The differing blocker directions select opposite tangents. This is different query input, not evidence that ASan executes the same query differently.

The first scalar/terrain-output capture (`/tmp/e2-steering-record-{debug,asan}-queries.json`) replays **128 queries** through original `0x448cb4..0x4495dd` and production C. For every case, the original reproduces the live final coordinates/facing, and reconstructed actor output matches the original. The existing polar/synthetic comparisons also pass normally/ASan. This includes the observed +512 and -512 turns.

## Actual Terrain And Complete Replay Boundary

`scripts/probe-e2-player-motion.py --trace-queries N` now records query state, vectors, elapsed ticks, list ownership, five perimeter samples, both target samples, terrain output, selected descriptors, complete local descriptor chains, shift and relevant terrain flags. Joe's coordinates, facing and camera remain read-only. GDB breakpoints and visibility captures consume wall time, which the original clock measures; tracing can change the subsequent input path. It does not establish deterministic paths across builds.

The final capture (`/tmp/e2-steering-audit-{debug,asan}-queries.json`) records 64 queries per build:

- `check-e2-scene-grid.py --replay` compares **896 recorded floor calls** through original `0x448744`/`0x448a48` and production functions, using captured coordinates, descriptor chains and terrain flags. Every returned height and requested terrain output matches both original code and the live observation.
- `check-e2-motion-query.py --replay` compares **128 complete steering queries**, asserting their seven floor-call coordinates/actor/output arguments, original final position/facing, and full reconstructed actor output against the original. All pass normally/ASan.

The observed floor cases have no selected terrain-script predicate and the motion cases have only Joe in the list. Replay rejects unsupported scripted-floor or multi-actor cases rather than silently substituting their inputs. Existing synthetic scene-script and actor-obstacle fixtures retain their separate coverage.

The final Debug trace's first turn has a **zero motion vector**, producing -2560 with five elapsed ticks. Original code produces the same result. A zero-vector early return or steering clamp would change recovered behavior. No such gameplay change is introduced. The results establish this bounded family; they do not rule out other timing, animation or physical-input defects outside the captured cases.

Eight representative captures, including the first straight query and samples around the first turn in each final trace, are retained in `scripts/fixtures/e2-courtyard-steering.json`. Both comparison scripts use these by default: **8 motion replays and 56 real terrain cases** supplement the existing suites. Explicit `--replay` files replace that default set.

## Sixty Seconds After The Round Trip

`--observe-seconds 60` resumes game updates after the input route with all movement keys released. It checks Joe remains current, script wait/modal stay zero, and captures normal game/SDL presentation at the end. Both final runs use `--camera-round-trip --trace-queries 64 --observe-seconds 60` and complete 175 → 166 → 175 before observation.

| Build | Observation duration | Released and final position | Released and final facing |
| --- | --- | --- | --- |
| SDL Debug | 60.42 seconds | `10211,3328,-17190` | 24320 |
| SDL ASan | 60.40 seconds | `10201,3328,-17184` | 24320 |

Final held-key bytes are all zero; no sanitizer diagnostics occur. The heavier trace makes both runs use Down after the initial Up attempt, then Up to return. The earlier lightly instrumented Debug Up/Down round trip remains valid. This is explicitly **released-input observation after traversal**, not 60 seconds of continuous walking or proof that every runtime path passes ASan.

```sh
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl-asan/e2recomp --camera-round-trip \
  --trace-queries 64 --observe-seconds 60 --timeout 180 \
  --output /tmp/e2-steering-audit-asan
python3 scripts/check-e2-motion-query.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan \
  --replay /tmp/e2-steering-audit-debug-queries.json \
  --replay /tmp/e2-steering-audit-asan-queries.json
python3 scripts/check-e2-scene-grid.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan \
  --replay /tmp/e2-steering-audit-debug-queries.json \
  --replay /tmp/e2-steering-audit-asan-queries.json
```

The probe retains dummy SDL, zero logo delay and timed Space, then waits for observed release. Natural logo/horseback timing and the recording's two launches are not validated. Cylinders, original mesh/HUD omission and background-spawn deferral remain explicit; full NPC activation remains separate.

## Verification And Next Work

Normal/ASan original-code checks pass with both full captures and saved samples. Existing counts remain 394 polar and 92,160 split/query cases; scene-grid checks retain 16,384 grid, 16,384 camera/hint, 1,199 camera dispatch, 16,384 grid-script and four fallback cases. The baseline runtime wrapper and all eight arrow rows pass (`/tmp/e2-steering-{regression,controls}.log`). Python syntax, whitespace, generator syntax and independent four-artifact parity pass.

Runtime/generated sources are unchanged, so no new generator mirror or runtime rebuild is required. The starting index remains unchanged (`/tmp/e2-steering-start-index.txt`); changes are unstaged and no commits/tags were made. [Task 07](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-07-recover-motion-query-steering.md) closes the captured first-turn investigation. [Task 02](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-02-recover-post-intro-placement-and-motion-queries.md) now prioritizes physical stair/wall/blocked-boundary assertions and wider active exploration. Full experimental ASan acceptance remains open.
