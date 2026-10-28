# Inner-castle register, clipping and presentation recovery — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Scope and preserved evidence

Continuation of [Task 04](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-04-recover-inner-castle-progression-crash-and-models.md)
and the [human handoff](inner-castle-progression-handoff-2026-10-28.md).
The starting worktree/index were clean at `5ac18fa`; no commit, push or staging
change is part of this recovery.

Evidence root: `.tmp/inner-castle-20261028/`. `preserved/` contains the complete
source session, executable/source context, recording, inspection and runtime
saves, verified against `preserved/SHA256.json` (**94 files**) and made read-only.
The original session and runtime saves also match that inventory after probes.
The bundle command initially attempted the source retention lock; the sandbox
rejected that write, so preservation used a verified read-only copy instead.
Source metadata, incomplete markers and unsealed tails were not changed.

User slots **5/123, 6, 7 and 9** remain protected. Installed slots **0–4/8/9**
are occupied too: the union has no empty slot. Persistence fixtures therefore use
`private-game/`, with symlinks to original assets and a private Saved directory
exposing only copied user saves plus a newly empty private **0**. Installed saves
are not exposed as fallback slots in that fixture. No occupied installed slot is
replaced or written. The initial attempt to use installed slot 0 failed its
empty-slot assertion before writing anything.

## Crash reproduction and actual owner

Pinned executable: SHA-256
`33c4ce05ad0722a60e3b748a52b502f06069f7b638c1af44ad862ebab02b6d2e`.
`pinned-replay-exact.log` reproduces SIGSEGV. `pinned-gdb.log` identifies loaded
slot **6**, camera **54**, owner **73/w_sprit3**, node **14** at `0xa350fe`,
root `0xaaeab0`, action **253/sprisqaush**, event **0x23**. The selected node's
flags are **0xa000**: byte `+2` has **no 0x20 bit**. The crash is not assigned to
the last head lever or gate.

Original **0x42c098** executes `mov eax,esi` before calling **0x42d61c**.
Original **0x42d627** tests that node's flag and returns immediately when clear.
Reconstruction lost the argument and dereferenced uninitialized `in_EAX=0x148`.
The repaired dispatch passes the selected node explicitly. No pointer guard,
flag clearing, action suppression or puzzle shortcut substitutes for that call.

The flagged branch also lost its owner and matrix registers. Its reconstruction
now retains both linked nodes, rebuilds the reverse chain, evaluates the endpoint
owner's original pose, transposes parent matrices, multiplies signed Q14 matrices
with original 32-bit wrap, restores all three local rotations, then clears 0x20.
`0x42d36c` uses the already compared `0x42d46c` decomposition with destination
`node+0x26`. The local transpose follows original **0x422628** directly: the
legacy wrapper excludes stack addresses, which is unsuitable for these original
stack matrices. The repair is mirrored in `GenerateRecon.js`.

Expanded `check-e2-spawn-action.py` passes **8,192** chain restoration cases and
**256** original caller handoffs per mode, alongside the existing original
FK/IK/attached-root, matrix-angle, queued-action, RNG and spawn comparisons. Pose
is intercepted in the new event fixture; the existing pose fixtures exercise its
actual original instructions. These are bounded contracts, not an entire game.

`fixed-debug-replay.log` and the final `final-prefix2.log` match all **3,190**
checkpoints and reach **sequence 9684450756** after repair, then report
**INCOMPLETE: recovered prefix exhausted** (exit 75). This is prefix acceptance,
not a completed recording or evidence of controls after the unrecorded tail.
The first i386 sandbox attempt received SIGSYS; native probes require the host
execution permission already used by existing fixtures. A dummy-driver override
was rejected by strict startup identity. Neither failure is a gameplay result.

## Companion event and bounded post-event acceptance

The diagnostic checkpoint exposed the next dependency: ordinary Up input then
crashed in **0x42d554**, event **0x20**. Original **0x42c087** also passes the
selected node in EAX. Reconstruction lost that input and the **0x42d948**
direction/roll helper's owner, vector and matrix registers. The repair retains
the original endpoint pose, derives owner-relative endpoint position/rotation,
sets the original constraint bit and computes authored twist/roll. It shares the
explicit transpose/Q14 multiplication with event 0x23; it does not bypass IK.

Additional original comparisons pass **4,096 direction/roll** and **4,096
endpoint/constraint** cases plus **256 event-0x20 caller** cases per mode. Both
helpers and dispatch are mirrored in the generator. `enable-fixture-final.log`
and its ASan counterpart retain the full original regression results.

`prefix-save2.log` stops immediately after the repaired event at sequence
**9684450756** / checkpoint **3190**, verifies that its selected node's **0x15a
bytes remain unchanged** (the original clear-bit no-op), then generates a private
original-format checkpoint with **0x453920**. Only the private host replay
reader is detached before that diagnostic Save; no game frame is resumed, no
coordinates/actions/timers/flags are assigned, and no source recording metadata
or completion status is changed. This is a diagnostic Save after a matched
prefix, not a completed input recording or an ordinary menu Save at the crash.
It was generated by the intermediate Debug executable
`e577c027b000776262526c2ca0ea017b6f95c123a389b17ed4e687fbe3197217`.

`post-event2-debug-same/-fresh` and `post-event2-asan-same/-fresh` pass fresh menu
Load of that checkpoint, full serialized actor/timer/attachment comparison,
movement, original attack selection, animation, F3/HUD, actual menu Save/Load,
subsequent fresh-process restoration and clean Quit. The main processes naturally
execute sprite **73**, node **14**, event 0x23 again at update **3**. Debug runs
**762** update boundaries; ASan **777**. Both fresh-process continuations cover
**591** more. Joe moves and survives real combat (Debug health **52→47→42**;
ASan **50** at the sampled movement checkpoints), with the mace attached
reciprocally to Joe's node **8** and magic owner 3776 to node **1**.

This accepts bounded post-event control and persistence. It does not establish
an uninterrupted fresh-input reproduction of the entire human journey, successful
bashing of the later castle gate, or complete original-game visual fidelity.
The longer waypoint routes retain navigation failures and one **600-second**
ASan timeout; no gate/collision/gameplay flags were forced to make them pass.

Final executable hashes after the companion repair:

- Debug: `d2a6af587bd3138c0e9af2c40c163cef700d7d127490529d4d88e15625e75c88`.
- ASan: `9d1d93aec52dfd92516b945f4c03a134c8c5f0cfc0fc9e39f397503516c55ba4`.

## Original signed clipping, not a cosmetic gate change

Fresh key and stairwell checks exposed heap corruption through `0x418514` and
`E2R_CopyDepthRect`. Static and dynamic projected rectangles could retain negative
edges and corrupt surface/depth allocations, later failing in malloc/inspection.
A captured key rectangle had **X=-78**, Y=0, width=286, height=186.

Original **0x421aee–0x421b52** and **0x4221af–0x422213** use signed `jge/jl`
comparisons. Generated clip globals are `uintptr_t`; C promoted negative edges
to unsigned. The repair casts bounds to signed int at these eight comparisons,
without adding clipping to original copy leaves or changing geometry/materials.
Both sites are mirrored in the generator.

`check-e2-render-copies.py` now preserves the production unsigned clip-global
types. Negative-rectangle cases fail before the repair (`clip-fixture-before.log`)
and pass afterward. Both modes pass **256 static** and **4,096 dynamic** original
clipping cases, plus **1,536 pixel-copy**, **1,152 depth-copy** and **256 dirty-list**
cases. Native key/stairwell activation previews pass after the repair
(`clipped-report.json`). No original-game defect or fully corrected gate
appearance is inferred from these comparisons.

## Original presentation owners

F5 selects **76 explicit owners**, adding the following **19** to the earlier
57; the 16 representation families remain unchanged. Assets are original,
untextured FANT geometry. Unknown owners retain fallbacks.

| Human finding | Original owners and evidence |
| --- | --- |
| Teleport | **2863/portst9** and **2864/prtpad12**, scene 1215, camera 8: original structure and pad, rounded/flat writes in Debug/ASan. |
| Head switches | **2874/2875** ordinary heads and **2876/2877** gold heads, scenes 1219/1220, camera 34. The reported later dark head is **806/switch4**, scene 318, camera 50; it is not lower-level owner 2925 from an unrelated camera. All have rounded/flat pixels in both modes. |
| Armour and overlay | **255/armor3**, scenes 1227/1228, camera 18, representation 48. Source inspection records its real attachment to Joe at snapshot **1844**, removed at **2242**. Loose geometry writes pixels; attachment uses the same explicit owner selection, without hiding Joe's marker globally. An explicitly activated armour-on scene also attaches this same owner to Joe in both modes (`armour-long-report.json`); human visual review remains separate. |
| Gates | **2882/armculis** (18), **2911/twrculis** (34), **3989/twrcul** (35), **794/kpculis2** (49). Native/preview captures show original rounded/flat pixels. Original authored tracks and collisions remain in charge; opacity and damage are unchanged. |
| Wizardess | **2656/freegirl**, scene 1161, camera 882: 53 nodes and **145 stored polygon faces**. NPC rendering already admitted rounded body geometry but suppressed these polygon details. Explicit selection admits the original faces; Debug/ASan observe both primitive paths. No substitute character body was made. |
| Prison key | **278/key4**, scene 1247, camera 180; distinct from earlier key 264. Rounded/flat writes pass after the signed clipping repair. |
| Mace and magic | **1252/joewand**, scene 528, camera 44, action **773/wandbob**. Its own animated nodes include blinking geometry. Separate naturally spawned sparkles **3839/jsparkle** and **3840/jspark2** also write rounded pixels after pickup. Original data names the human-described mace joewand. |
| Stairwell lightning/rubble | **290/muztwr** is the strike and **260/xplod** the separate explosion/debris owner in scene **97**, camera **42**. Native descent observes rounded writes from both in Debug/ASan. **288/289** are separate step owners; their missing pixel qualification is retained, rather than substituting intro lightning or calling a static preview natural debris acceptance. |

Representative first observed writes agree between Debug/ASan: teleport pad
**663 flat**, structure **184 rounded**; gold heads **386/170 rounded** plus
**39/5 flat**; dark head **297 rounded / 5 flat**; armour **336 rounded**;
wizardess **381 rounded / 11 flat**; key **4 rounded / 3 flat**; mace **44 rounded**
in an activated scene and **98** on the fresh route; stairwell strike **74 rounded**.
The first explosion and sparkle primitive can be only a few pixels. These are
bounded actual writes, not proof of complete composition, brilliance or lifetime.

`actual-report.json` qualifies the dark head and adjacent gate. Portal light
owners 808/809, flash 2922, wizardess disappearance 2657, effect 3776, step owners
288/289 and lower head 2925 are not newly selected by F5. A name or empty template
is not sufficient pixel evidence. In `post-event3-*`, owner 3776 is confirmed
attached to Joe's node 1, but its bounded raster attempts do not change pixels;
its body nodes are authored hidden/dormant in these observations. It remains a
fallback; no visibility or material flag is forced to make it draw.

## Native progression, persistence and limits

Fresh `live-route6-debug/-asan` load protected slot 5, ascend from camera 38 to
44 with ordinary arrows, pick up the mace with one Space tap, verify its real
attachment, exercise F3/HUD, and save/load through actual menus in private slot 0.
Fresh processes restore that mace checkpoint with ownership and controls intact.
Descent crosses the stairwell sequence with real strike/explosion/sparkle pixels
and no previous clipping corruption. Subsequent route attempts remain bounded
navigation failures, not completed journeys. Some observed gold-head hits set
health to zero and authored gates move; their full script dependencies and the
camera-50 dark-head route are not established by proximity alone.

`live-route*`, `activated-*`, `clipped-*`, `preview-*` and `armour-*` retain
unsuccessful attempts. Dormant scene previews initially had no active child;
explicit `--inspect-start-scene` now installs/starts the original scene for asset
fixtures. It can run authored Joe motion and is not traversal evidence. The
ordinary visibility-only preview retains its unchanged-position assertion.

An ASan compatible replay of the Debug recording fails earlier in the Load
preview, and a GDB variant diverges at checkpoint 7. This is not exact ASan replay
acceptance. Fresh ASan input and independent ASan recording checks are separate.

The established tower regression passes all five processes in Debug and ASan
with the final model selection/repairs (`tower-final2-debug/-asan`): locked refusal,
head/drop/pickup/keyed passage, three same/fresh persistence stages, F3, HUD,
menus and clean Quit. Source/user saves remain unchanged. Fresh `final-recording2-debug/-asan` chunked recording
checks retain five independent replay variants with the final 76-owner selection; source prefix, new recording
completion and live gameplay acceptance are distinct claims.

All four SDL/X11 Debug/ASan builds, generator syntax, independent four-artifact
parity, original fixtures and whitespace checks pass. Documentation-tree checking
is run with the final documentation update. Extended human play, complete gate
composition, equipped-armour human visual review and unqualified owner lifetimes remain
open; preserve possible original defects until a reconstruction mismatch is proved.
