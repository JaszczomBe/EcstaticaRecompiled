# NPC Endpoint And Reverse-Chain Pose Recovery — 2026-10-20

The user accepted restored generic population after early Space and authorized the next bounded implementation: recover NPC node/root/IK inputs, extend original-code comparisons and verify populated traversal with sustained NPC updates. The existing index snapshot remains unchanged; this continuation is unstaged. No commits were made.

## Original-Code Evidence And Repair

The prior repeatable early-Space Debug run stopped at `0x42f9c0 → 0x424318 → 0x423674` when actor 110 (`w_fairy`) requested secondary actor 1159/action 702. The reconstructed endpoint helper had an uninitialized node, and the reverse-chain IK branch had lost its stack vectors, matrix destinations, angles and child-node inputs. The earlier native Debug failure at `0x42faf8 → 0x424318` independently lost the event node and pose owner.

Recovered from `E2Recomp/original_disasm.txt` and the original `E2WIN95.EXE`:

- `0x423674`: explicit endpoint node; frozen, owner-root, absolute and alternate-motion coordinate bases; Euler rotations and world tip.
- `0x424318` IK branch: explicit middle/endpoint nodes, transposed matrix and contiguous vectors, local yaw/pitch rotations, signed two-segment length calculation, inverse-sine bend angles, endpoint roll alignment and reverse-list advancement. Existing root/FK behavior remains covered.
- `0x424164`: retain parent and child. The relative position uses **parent extent plus child offset transformed by the parent matrix**; its matrix/Euler and type-4 tip updates remain separate.
- `0x420ec4`: retain actor/attachment, original type-dependent offset/Euler fields, world-origin/matrix/angle outputs and inherited flag propagation.
- `0x42faf8`: retain the event node, rebuild reverse links from the original endpoint, supply that endpoint's owner to the root pose, then pass each original node to `0x42efdc`. Attached child posing receives its actor explicitly. This establishes the event/pose handoff, not general hit-query/combat behavior.

The original inverse-sine initializer at `0x4154ff..0x41554d` was missing entirely. It fills 32,768 signed entries around `0x593590` using constants at `0x471391` and `0x4713a9`, then truncates. Restoring arguments alone would have read zero-filled bend values. All production changes have generator mirrors; no population whitelist, extra gameplay bypass or launch flag was added.

## Original-Code Fixtures

`scripts/check-e2-spawn-action.py` now compares the complete production reverse-chain pose instead of aborting its attachment and IK branches. Debug and ASan fixtures pass:

- 32,768 inverse-sine entries against the original x87 initializer, intercepting only its CRT `asin` call. Original arithmetic, truncation, indexing and stores execute directly.
- 4,096 endpoint poses covering the four coordinate/frozen cases.
- 8,192 IK chains with full rotations, alternate matrices, endpoint roll alignment, zero target/segment cases and reverse-link patterns; coordinates stay within bounded physical ranges.
- 1,024 attached-root poses, including inherited flags and chained owners; 256 event-node/owner handoffs with intercepted pose/query leaves.
- Existing 2,048 root/FK poses, 5,120 queued-action completions, 4,096 matrix decompositions and 768 spawn-event memory/call cases.

A first child-helper recovery used the child's extent/matrix for relative position. Original-code comparison rejected it; the final implementation uses the parent/offset contract above. Fixture setup now constructs alternate matrices in mapped storage before copying them into its host-side seed buffer, avoiding the hosted-pointer guard silently skipping initialization.

## Runtime Verification

The previously failing Debug route now executes the early Space path with the normal 5,000 ms logo delay, finds the original restrained/released guards and generic actors, survives 180 populated frames, completes **175 → 166 → 175**, then another 60 seconds with released keys. Actor 1159 is present in the census, so the old spawning frontier is crossed. A second Debug run also completes this route; its observation records 141 samples, with generated NPC movement/state changes in all 140 intervals. Moving resource IDs include 77, 78, 79 and 81. Joe remains current, wait/modal stay zero and held arrows clear.

Controlled SDL ASan also completes the same populated round trip and 60.40 seconds of released updates without a sanitizer report. Its final repeat (`/tmp/e2-npc-pose-final-asan-dummy`) records 141 observation samples and activity in all 140 intervals; generated resource IDs 77, 78, 79 and 81 move. The final native Wayland ASan run (`/tmp/e2-npc-pose-native-asan`) repeats early Space, taps/releases Shift and Alt, then presses Up+Left together. Turning resumes, released keys clear, and the following 60-second observation records activity in all 140 intervals; moving generated IDs include 30, 77, 78, 79, 106 and 112. No sanitizer report occurs. These are released-input observations after active traversal/input, not 60 seconds of continuous walking.

A native Wayland ASan scripted round trip stayed alive but did not reach camera 166 within the input limit (`/tmp/e2-npc-pose-final-asan.log`). This is a route assertion failure, not a pose crash or sanitizer failure. Different time/input paths already limit exact steering comparisons; do not claim every native scripted route succeeds or change steering speculatively from this result.

Commands (from the repository root):

```sh
python3 scripts/check-e2-spawn-action.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --intro-skip-action 1 --startup-logo-delay-ms 5000 --background-spawns \
  --pedestal-guards --require-background-population --population-frames 180 \
  --camera-round-trip --observe-seconds 60 --timeout 180 \
  --output /tmp/e2-npc-pose-final-debug
# Repeat with the SDL ASan executable for the controlled sanitizer route.
# Native activity/control continuation:
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl-asan/e2recomp \
  --intro-skip-action 1 --startup-logo-delay-ms 5000 --background-spawns \
  --pedestal-guards --require-background-population --population-frames 180 \
  --turn-forward left --simultaneous-turn --frames 30 --burst-frames \
  --tap-modifiers shift alt --observe-seconds 60 --video-driver wayland \
  --timeout 180 --output /tmp/e2-npc-pose-native-asan
```

The probe now records mapped NPC action progress and samples population throughout an observation when `--require-background-population` is set. It requires surviving generated actors and actual NPC movement/state/action changes, and reports changed IDs and active intervals. Actor state remains read-only; movement comes through actual SDL events.

All four CMake Debug/ASan SDL/X11 builds pass. Independent regeneration matches all four generated artifacts. Existing population/script fixtures pass normally and under ASan; runtime regressions, all eight control-matrix rows and both visible SDL requester checks pass. Logs use `/tmp/e2-npc-pose-*`. The index patch matches `/tmp/e2-npc-pose-start-index.patch` byte for byte.

## Acceptance And Next Frontier

This closes the reproduced endpoint/IK crash and the bounded event-node/pose-owner handoff. It establishes populated early-Space exploration and sustained NPC activity for the recorded routes. Full experimental ASan, general hit queries/combat, articulated mesh collision, original model presentation and all object interaction categories remain unaccepted.

Next choose one original scripted object at a known location. Establish its archive identity, live instance/scene ownership and presentation eligibility, then recover its first actual interaction contract. A missing cylinder alone does not establish a missing switch/door/trap/pickup; camera slots are not script IDs. Keep the NPC pose fixtures and populated crossing/return as regressions.
