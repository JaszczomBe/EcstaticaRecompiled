# Water replay and sword pickup — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The user confirmed swimming in ordinary F5, then reported a Space-interaction
crash beside the workshop sword. The water recording replays exactly. The sword
recording reproduces a lost player argument in pickup selection. Recovering that
query, the first model origin, the attachment event and Space release now allows
fresh SDL Debug/ASan input routes to acquire the sword and move while equipped.
Human repetition of the repaired pickup, combat, shore exit and armed swimming
remain separate acceptance.

## Preserved human sessions

Both recordings pin the same Debug executable, SHA-256
`a66c1240697042ec42a9274892bd5af44705c8feaccedc4eb9e25acc516ecda5`.
Verified bundles are retained independently of session retention:

| Session | Bundle | Result |
| --- | --- | --- |
| `session_20261024_115621_101` | `.tmp/replay-bugs/water-human-20261024` | Complete; exact replay matches all **565 checkpoints**, through sequence **1,524,012,871**, clean exit |
| `session_20261024_115718_697` | `.tmp/replay-bugs/sword-human-20261024` | Incomplete after SIGSEGV; exact replay reaches the same crash, last matching checkpoint **62**, sequence **1,051,977,974** |

Temporary copies are `/tmp/e2-{water,sword}-human-20261024`. F5 receipts remain in
`.tmp/f5-investigations/`, including the sword debugger signal evidence. Export
used inactive copies under `/tmp`, avoiding mutation of the user's retained
sessions. Original game data remains external.

Water evidence is `/tmp/e2-water-human-exact-20261024{.log,/}`. Its inspection
contains **59 distinct swimming positions**, from camera 543 at
`(-937,5120,-2107)` to camera 545 at `(1881,5120,-1657)`. Joe retains health **100**,
state **4**, representation **13** and swimming flag **8**. The later Escape menu
and quit are ordinary user input. This confirms the reported water entry and
swimming route; it does not establish shore exit or swimming while armed.

The sword recording also confirms ordinary walking through cameras
**175→166→176→350→348→347** to the workshop. At Space, Joe is at
`(-871,4096,-10006)` and original sword actor **3717** is present at
`(-972,3884,-10208)`. This closes the earlier human workshop re-entry uncertainty.

## Original contracts recovered

1. **Pickup query:** original `0x4290c4..0x4290cc` passes the saved player actor
   to `0x42dc9c`. The reconstruction supplied a stale register and left its
   `in_EAX` uninitialized. Original `0x42ddbb` also supplies separate angle and
   distance outputs plus both X/Z deltas to the polar helper. The repaired query
   retains the original candidate flags, owner/model checks, radius, height
   interval, nearest selection and pickup action class.
2. **First model origin:** the cylinder bypass returned before
   `0x42391b..0x423a64`, leaving the sword's first model node at world height zero.
   The original query reads that node's height, so repairing the crash alone
   selected no object. Cylinder mode now retains that first node's transformed
   origin and inherited/alternate matrix. Remaining mesh articulation is still
   bypassed. No synthetic height or pickup range is substituted.
3. **Attachment event:** fresh input selects the sword and then exposes
   `FUN_0042deb8 → FUN_00424318` with a missing owner. Original `0x42c417` passes
   the event node in EAX. The repair preserves that node, scopes its root owner
   through pose calculation, supplies the replacement actor/floor/copy inputs,
   and dispatches the selected script record with owner, target, child and null
   node arguments from `0x42e021..0x42e029`. Reverse links, attachment links and
   equipped-kind changes retain their original control flow.
4. **Space release:** the first equipped-movement check survived but remained
   in repeated interaction, with the Space flag still set after key-up. Original
   `0x45836e..0x458376` clears `0x636850`. The hosted key-up bridge now does so as
   well, allowing movement after releasing Space. Existing modifier and raw held
   table behavior is retained.

Reconstructed C/header changes are mirrored in `GenerateRecon.js`. The Space
release belongs to the existing host compatibility bridge in `E2Recomp_stubs.c`.
Generator syntax, in-place generation and independent scratch reproduction match
all four generated artifacts without unrelated changes.

## Comparisons and fresh runtime evidence

| Check | Result |
| --- | --- |
| `check-e2-pickup.py E2WIN95.EXE [--asan]` | **4,096** original first-model origin/matrix cases and **12,288** pickup-query/caller cases pass normally and under ASan; **5,068** select a candidate |
| `check-e2-pickup-attachment.py E2WIN95.EXE [--asan]` | **16,384** original attachment/replacement/pose/polar/callback/HUD contracts and **256** event handoffs pass normally and under ASan |
| `check-e2-key-release.py [--asan]` | **114** raw held-table cases and **384** modifier/Space release/preservation cases pass normally and under ASan |
| Existing population fixture | Original actor, callback, root-reference, sound and NPC comparisons pass normally and under ASan |
| Existing detach fixture | Complementary detach/caller comparison passes under ASan |
| Four SDL/X11 Debug/ASan builds | Pass |
| Runtime baseline and arrow matrix | Pass; all eight arrow rows pass after the Space repair |
| SDL requester, OK, resumed update and Escape | Pass in Debug/ASan |
| Fresh natural-startup water route | Debug/ASan enter camera 543, finish the swimming transition and move forward at height 5120 with health 100/state 4, representation 13 and no modal |
| Populated courtyard crossing/return | Debug/ASan pass at floor 3328, with both guards and five seconds released-input observation |

The attachment fixture intercepts pose, polar, floor, script and HUD leaves; it
compares leaf arguments and complete actor memory, not their full implementation.
Missing-code error presentation and the helper's incidental return register are
outside that fixture. The first-model comparison ends before articulation.

A repeatable route is now part of the existing motion probe:

```sh
python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --sword-pickup --intro-skip-action 1 --intro-skip-progress 83 \
  --background-spawns --burst-frames --timeout 200 \
  --output /tmp/e2-sword-pickup-release-debug
```

Use the ASan executable and a 220-second bound for its counterpart. The route uses
SDL arrows to follow waypoints sampled from the human recording, aims at the live
sword position, presses/releases SDL Space, waits for the action and sends Down.
It writes no actor position, angle, camera, attachment or equipped state. Agent
recording is explicitly off; per-phase JSON, visibility packets and logs remain.

Both runs complete with reciprocal node/sword attachment links, node owner Joe,
equipped kind **3**, representation **9**, health **100**, state **4**, no wait or
modal, and all arrow keys released. Debug moves from `(-984,4096,-9989)` to
`(-1035,4096,-9954)`; ASan moves to `(-1068,4096,-9926)`. The Debug SDL workshop
image was visually inspected; cylinder presentation remains diagnostic.

Final verified executable hashes:

- Debug: `4a24c5461ed6d6bdf51f306ac63ed54cd0269f7051fdf7651728b7477e6e4ba2`.
- ASan: `b23ebb9a7b1f276ab824aaa0357e242ea80943bca3bb9f5474b7f587f5dfaf31`.

Evidence prefixes: `/tmp/e2-sword-pickup-release-{debug,asan}`,
`/tmp/e2-sword-courtyard-{debug,asan}`, `/tmp/e2-sword-final-baseline`,
`/tmp/e2-sword-controls`, `/tmp/e2-sword-final-requester-{debug,asan}` and
`/tmp/e2-sword-generator-parity.log`. Final compatible replay also crosses
the captured fault and exhausts the recovered prefix at checkpoint 62, sequence
1,051,977,974 (`/tmp/e2-sword-final-compatible.log`); the
crashed recording has no continuation from which to prove completed pickup.
Fresh input supplies the post-crash integration evidence. Current water
regressions are `/tmp/e2-sword-final-water-{debug,asan}`; these both pass after
the pickup and Space-release changes. A copy of the final logs, JSON and selected
visibility packets is retained in `.tmp/sword-pickup-20261024/final/`.

## Remaining acceptance

Repeat the ordinary F5 workshop Space pickup and continued movement with the
rebuilt Debug executable. The automated acquisition establishes the bounded
interaction; it does not establish combat, sword attacks/door destruction,
original weapon meshes, arbitrary object interactions or full-gameplay fidelity.
Keep the separate broader Debug floor-return issue and the earlier combined
skip-to-water ASan timeout explicit. No commit or push was made.
