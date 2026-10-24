# Sword attacks and attached position — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The user confirms ordinary F5 sword pickup after the
[pickup repair](water-replay-and-sword-pickup-2026-10-24.md), then reports a crash
while holding Ctrl and using arrows. The original workbench sword cylinder also
remains after attachment. Exact replay reproduces the attack crash. Original
attack-query and attached-render contracts are restored; fresh Debug/ASan routes
now start all four requested attack directions, move after release and keep the
sword's world position following its attachment.

## Captured failure

Human session `session_20261024_123155_641` pins Debug executable SHA-256
`4a24c5461ed6d6bdf51f306ac63ed54cd0269f7051fdf7651728b7477e6e4ba2`.
Its replay/inspection are incomplete after SIGSEGV. The verified bundle is
`.tmp/replay-bugs/sword-swing-human-20261024`, with an additional temporary copy
at `/tmp/e2-sword-swing-human-20261024`. Export used an inactive copy under `/tmp`
so the user's retained session was not mutated. The F5 receipt and all-thread
stop evidence remain under `.tmp/f5-investigations/`.

Pinned native replay and a fresh GDB replay reproduce:

`FUN_0042e7dc(0,1) ← FUN_00427584(Joe,1) ← FUN_0042a70c`.

Both the human debugger receipt and fresh GDB stop identify sequence
**1,338,228,752**, last matching checkpoint **91**. Joe has already acquired the
sword, uses representation **9** and retains health **100**. The final input is
Ctrl held with a new Up press. Evidence is `/tmp/e2-sword-swing-exact.log` and
`/tmp/e2-sword-swing-fault-gdb.log`.

Inspection records sword actor **3717** attached to owner **Joe**, while its
position remains the original **(-972,3884,-10208)** even after Joe moves away.
This identifies stale actor coordinates behind the leftover cylinder. Actor
**602**, also present nearby in inspection, is `korc2`, not a second sword.
At the first attached render update, GDB reads a valid hand node `0x953e74`,
owner Joe, and tip **(-1080,3742,-10205)**, while the sword still has its workbench
coordinates. Returning from the old render update leaves those coordinates
unchanged. Evidence is `/tmp/e2-sword-swing-gdb.log`.

## Original behavior recovered

- **Attack target height:** both original player callers, `0x429191..0x4291b1`
  and `0x429307..0x429327`, retain Joe in EAX. `0x42e7dc` saves that actor in EDI;
  the C instead passed a direction temporary and read an uninitialized actor.
  Original `0x42e8a7..0x42e8b4` also supplies X/Z independently to the angle leaf
  and retains Z in ECX for distance. Those inputs are now explicit. Candidate
  eligibility, range 1280, facing/priority selection, model fallback and the
  ±300 height classification remain original-shaped.
- **Direction preservation:** the original query preserves ECX and EDX. The
  reconstructed callers replaced their left-direction value with undefined
  `extraout_ECX` locals after the call. They now retain the existing direction;
  the returned upper half continues to preserve EDX.
- **Attached rendering:** original `0x421091..0x4210a4` recursively updates the
  node's **owner actor**, then transforms the **attached actor** from that node.
  The C recursively passed the bone as an actor and supplied an unrelated
  register temporary as the attached actor. Both identities are corrected.
  The pose work-list counter at `0x421160..0x4211b1` is also initialized and
  preserved across child transforms, including the original five-pass limit.
- **Cylinder-mode attachment posing:** the mesh bypass omits the full bone pass.
  Before updating an attached root, it now retains that attachment's reverse
  chain and invokes the existing recovered `FUN_00424318` pose entry with its
  owner, restoring the prior context afterward. This keeps the hand's actual
  world transforms current using the original FK/IK math. Cylinder cues continue
  to read real actor coordinates. Full mesh articulation/rendering remains a
  separate acceptance boundary.

All reconstructed repairs have anchored generator mirrors. Syntax, in-place
regeneration and independent scratch reproduction match C, header, globals and
names without unrelated generated changes.

An intermediate query-only compatible replay changes behavior at the earlier
Ctrl press and correctly reports service divergence after checkpoint **85**,
sequence **1,301,484,605** (`/tmp/e2-sword-swing-target-fixed.log`). The old crashed
recording does not establish completed attacks after repair. Fresh input routes
supply that integration evidence; checkpoint matching was not relaxed.

## Verification

| Check | Result |
| --- | --- |
| `check-e2-attack-target.py E2WIN95.EXE [--asan]` | **65,536** original query cases pass normally and under ASan, including eligibility/range/facing/priority/model/height boundaries and both actor/direction-preserving caller contracts |
| `check-e2-attached-render.py E2WIN95.EXE [--asan]` | **4,096** original owner/root/recursion/work-list/memory cases and **1,024** original reverse-chain/pose-owner handoffs pass normally and under ASan |
| Existing `check-e2-spawn-action.py [--asan]` | Actual root/FK, endpoint, IK, attached-root and angle math, event handoffs and queued actions pass against original code in both modes |
| Four SDL/X11 Debug/ASan builds | Pass |
| Runtime baseline and arrow matrix | Pass; all **eight** control rows pass |
| SDL requester, OK, resumed update and Escape | Debug/ASan pass |
| Final sword route | Debug/ASan acquire the sword, start all four requested Ctrl/arrow directions, release Ctrl/arrows, move and retain health **100**, state **4**, equipped kind **3**, representation **9**, reciprocal attachment ownership and no modal |

The render fixture intercepts palette, full bone posing and matrix-to-angle
leaves; it checks ownership, root math, work-list bounds and complete actor memory.
The existing pose fixture separately executes the real recovered math against
original x86, including **8,192 IK** and **1,024 attached-root** cases. These
fixtures do not establish damage, enemy deaths or door destruction.

The existing input-only motion probe now supports:

```sh
python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --sword-pickup --sword-attacks \
  --intro-skip-action 1 --intro-skip-progress 83 \
  --background-spawns --burst-frames --timeout 220 \
  --output /tmp/e2-sword-swing-final-debug
```

Use the ASan executable and a 240-second bound for its counterpart. The probe
uses SDL key events, waits for the requested attack direction to start within
12 bounded 30-update batches, then releases it. It verifies released movement,
attachment ownership and changing sword world coordinates. Recording is explicitly
off; it writes no actor coordinates, angles, action, camera or attachment state.

Final Debug observes Up/Left/Right/Down slots **184/185/186/187**; ASan observes
**188/189/190/191**. These are the original context-dependent height/action groups.
Both directions and their grouping come from live game selection. The sword
moves from **(-1115,3751,-10124)** to **(-1344,3739,-9564)** in Debug, and from
**(-1106,3751,-10122)** to **(-494,3738,-10039)** in ASan. It leaves the original
workbench position and follows the hand rather than remaining there. The Debug
SDL workshop frame was visually inspected after movement.

Final executable hashes:

- Debug: `c7c2001a5bc3499e693a25ef1112293108ad4beb88012743ef125fd9f1657a6e`.
- ASan: `3e6954e61c482206073b52f59d0692e869aaea531d0eac734ac47de8147fcbbb`.

Evidence prefixes are `/tmp/e2-sword-swing-final-{debug,asan}`,
`/tmp/e2-sword-swing-{baseline,controls,parity.log}`,
`/tmp/e2-sword-swing-requester-{debug,asan}` and the focused fixture logs.
Final logs, JSON and selected frame/state packets are also retained in
`.tmp/sword-swing-20261024/final/`.

## Route limits and next acceptance

The populated Debug courtyard crossing/return plus five seconds idle passes at
floor 3328 (`/tmp/e2-sword-swing-courtyard-debug`). The generic ASan automatic
steering route misses its camera-166 assertion: its last outward sample remains
in camera **175**, at **(8173,3328,-19139)**, health **100**, state **4**, no modal
and no sanitizer report (`/tmp/e2-sword-swing-courtyard-asan`). A second ASan
route using the recorded **83/495** early-skip timing crosses to camera 166 and
returns to camera **175**, but stops at **(7775,4096,-18016)** rather than the
expected floor **3328**. Health stays **100**, state **4**, modal zero and no
sanitizer error (`/tmp/e2-sword-swing-courtyard-progress83-asan`). Both failed
route assertions are retained; neither establishes a passing ASan return.
The broader floor-return
and full-gameplay limits remain separate from the passing sword route.

Next human acceptance is ordinary F5 pickup, Ctrl-plus-arrow swings, release and
movement, checking that the sword marker follows Joe. Then recover and verify
one actual weapon contact/damage or door interaction from its original action
and script before claiming combat. Human pickup is confirmed by this report;
full weapon meshes, broad combat and armed swimming remain unaccepted.
No commit or push was made.
