# First object playthrough session: garden teleport, courtyard head and boots — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Continuation of [Step 12 Task 05](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md).
The user supplies sessions oldest to newest. This is the first supplied session;
later sessions must be linked to their actual loaded checkpoints separately.

## Session and checkpoint

| Field | Preserved evidence |
| --- | --- |
| Human session | `/home/rgrabowski/.ecstatica2/logs/session_20261029_160059_508` |
| Source context | `38d79da2276c2baef8e0fceec46f0f7557cb8192`, `v0.3.0`; startup working tree contains the documentation handoff |
| Pinned Debug executable SHA-256 | `ab3c66eccdfa1eca96c2a2185664dbe22100d37e91165c19b0e5301cf08a07e2` |
| Recording and exit | Clean exit 0; recording and inspection complete |
| Actual Load | Installed slot **2**, label **g3**, `/home/rgrabowski/Games/Ecstatica2/Saved/0002.ECS`; no runtime slot-2 override |
| Save identity | **211,193 bytes**, SHA-256 `1c884e338a2d746d3a7a53bc1ccde62e4417e768fd9a34f8d2cbc124674b75fd` |
| Strict reproduction | All **1,386** checkpoints match; clean completion at sequence **1,269,259,350** |
| Preserved investigation | `.tmp/object-behavior-session1-20261029/`: complete source copy, verified `bundle/`, pinned executable, fourteen save snapshots and manifests |

The bundle was exported from the private session copy because exporting directly
from the source tried to acquire a retention lock outside writable storage.
The original session was not changed. Source-save identity is supported by exact
replay from the preserved checkpoint, not merely by the current slot number.

The route goes from garden cameras **978 → 965 → 980**, teleports to **136**,
returns through **142/143/132/161**, climbs to **546**, enters **341/342**,
and returns to the courtyard. The final human view is camera **161**.
No new human Save is established by this recording; installed slot 2 remains the
identified reproducible starting checkpoint. Existing runtime slot 7 is a
different, older checkpoint and is not this session's end save.

## Findings and changes

| Report | Original owner and result |
| --- | --- |
| Missing garden teleport | **2927/prtpad13**, scene **1251**, camera **980**, representation **256**, and separate animated glow **796/tglo2** in scene **1252**. This differs from the previously selected castle pad 2864. The human recording completes authored teleport scene **1252**, then scene **1253** at the courtyard destination. |
| Missing gold head above the stairs | **2926/botswch2**, scene **1250**, camera **546**, representation **322**, hit action **1295**. The recording observes its health **100 → 0** and the action; this differs from castle heads 2876/2877. |
| Missing hut box and boots | **505/kchest5**, scene **1856**, camera **342**, representation **404/botchest**; **948/boots1**, scene **214**, representation **124**. Their original geometry exists. The session's checkpoint already has the chest open and the boots spent, as detailed below. |

F5 now selects these five original owners, raising its explicit selection from
**76 to 81**. Debug/ASan asset previews observe pad **23 flat** changed pixels,
gold head **317 rounded / 8 flat**, chest **361 flat / 3 rounded**, and boots
**96 rounded** on representative first writes. These are bounded original-asset
previews, not full human visual acceptance or a newly completed boots pickup.
F3 retains independent original/mixed/boxes behavior and unrecovered fallbacks.

The glow needs its authored scene timeline: its resource starts with zero-size
nodes, then scene 1252 changes dimensions, positions, material and visibility
between ticks **30 and 116**. Static/activated previews alone miss its useful
window. Fresh ordinary-input garden routes from copied installed slot 2 finish
at camera **136**, position **(-15096,4096,-2304)**, health **171**, with the wait
gate clear, and exit through the real Quit menu in Debug/ASan.
Read-only raster observations on these routes record glow-owner 796 rounded
writes: **3** first changed pixels in Debug and **72** in ASan, at different
sampled times. The first observed dimensions include node 140 **(22,9,19)**,
145 **(14,7,15)** and 147 **(10,4,10)**; later authored sizes and removal are not
forced. Evidence is `garden-route5{-asan}-raster.json`, route/state captures and
native logs. First-write counts are not an equality comparison or full visual
composition acceptance. No replacement teleport art or timing change is made.

No reconstructed C or game mechanic changes are made. There is consequently no
new C repair to mirror; independent generation matches all four artifacts.

## Boots state belongs to the original checkpoint

Read-only native Load of the preserved installed save records:

| Owner | Persisted state |
| --- | --- |
| Chest 505 | Table flags **0x52**, representation **0**, stored track **1484** = action **1483/bootchestopn** + 1 |
| Boots 948 | Table flags **0x60**, stored position **(-20472,2313,-8878)**, representation **124**, track **686** = action **685/bootvanish** + 1 |
| Scene 214 | Flags **6**: the original boots scene has already run |
| Scene 342 | Protection bit **8** is clear |

Boots 948 lack the persistent live-object bit **2**. The actor is absent when the
human revisits the hut; the chest has its post-opening representation. Original
action **1483** calls **1419/ken:playboot**, which loads scene **214**.
Pickup script **357/ken:boots1** sets scene-342 bit 8, schedules Joe's
**623/bootsturn**, and requests boots **685/bootvanish**. Original
**1417/ken:bootvan** schedules **684/bootsgone** with operand **900**;
**277/ken:bootsgone** clears scene-342 bit 8. The state therefore supports an
already consumed pickup with expired protection, rather than an untouched box
whose boots should respawn. This does not establish the wall-clock lifetime or
new natural pickup/hazard acceptance.

Do not reset the chest, reinsert boots, grant permanent immunity or repair this
save to satisfy the expectation. A fresh, originally eligible checkpoint is
needed for new acquisition/protection/expiry acceptance.

## Separate stability finding and failed probes

A bounded input route from the older runtime **7/COURT** stalls at an incorrect
stair approach. A corrected approach reaches the stairs but later receives
**SIGFPE** in `FUN_0042efdc` while an enemy hits Joe. Its stopped-thread evidence
is retained in `boots-route2-stopped.json`; this is an agent reproduction failure,
not a crash in the clean human session.

That older reconstructed checkpoint has player power **0**. The
[inventory recovery](enter-inventory-menu-recovery-2026-10-28.md) already records
that corrected scalar ownership cannot restore values lost in old saves.
Original **0x42f396..0x42f429** divides damage by mapped **0x47ab28** without a
zero guard, including normal-difficulty `idiv ecx` at **0x42f3e3**.
Preserve that arithmetic and the occupied save; no guard or power normalization
is introduced. The human session's installed slot 2 has power **200** and does
not encounter this fault.

Explicit activated-scene previews of teleport glow **796/tglo2** do not observe
nonzero shapes. A diagnostic replay changing only the host model selector after
startup diverges at sequence **177,501,608**, last matching checkpoint **831**;
it is excluded from strict acceptance. A first diagnostic attempt stalls inside
a debugger callback, and a prefix stopped at checkpoint 699 never reaches Load.
All are retained separately from the exact 1,386-checkpoint source replay.
Two fresh garden-route attempts reach the pad approach without completing the
trigger. A third reaches the authored teleport track but its 100-update
observation stops at progress **114**, before the end at **116**. Extending the
bounded observation to 240 updates completes the fourth route; the fifth
Debug/ASan routes additionally observe real glow pixels. These are probe
navigation/window corrections, not game repairs. The earlier incomplete
recordings remain incomplete. The fourth route's separate recording fails
standalone replay at sequence **21,973**, checkpoint **11**, with expected
`pump_begin` versus actual `clock`; its debugger-driven host input pumping is
not strict replay acceptance. The successful natural routes remain bounded
native evidence, separate from passing strict generic regressions and the
exact human recording. No source recording or checkpoint rule is weakened.

## Verification and continuation

Debug/ASan native asset previews pass for the pad/head/chest/boots; separate
natural routes qualify the glow and teleport completion. Original-x86
object activation comparisons pass **8,192** field/callback/action cases,
**1,024** visibility cases and **1,024** preload-position cases per configuration.
The initial sandbox attempts terminate with SIGSYS; native reruns pass.

Protected private persistence from copied installed slot 2 passes repeated
same-process and fresh-process Load under Debug/ASan, including resumed movement,
attacks, gold-sword attachment, HUD/F1/F2, F3, Enter/Escape inventory, preview
ownership, music state and real menu Quit. Only confirmed-empty private slot **5**
is written; occupied user runtime slot 5 is a different file. Slot-2 Music is off;
audible music acceptance is not inferred from that persistence result.

With the intermediate **80-owner** selection, separate fresh audio/music
recordings pass **six strict replay variants** in each configuration: Debug **27** checkpoints, ASan **26**. Sound/music event and PCM
checks, inspection on/off and device-disabled routes retain their existing
bounds. Human listening and wider audio transitions remain open.

Adding the separately qualified glow produces the final **81-owner** F5 list.
Final native reruns now pass for that exact list:

- Debug/ASan repeated same-process and fresh-process private persistence, with
  resumed controls/attacks, HUD/F1/F2, F3, inventory, preview ownership and Quit:
  **four clean native exits**. Evidence: `persistence-final-{debug,asan}/report.json`.
- Separate Debug/ASan recordings each pass **six strict replay variants**, each
  with **27 checkpoints**, including sound/music event and PCM comparisons.
  Evidence: `replay-final-{debug,asan}/report.json`.
- Original ellipsoid comparisons pass **3,072** pixel/depth/rectangle/lock cases
  (**1,902 draw pixels**) in both configurations. Dependency limits remain the
  fixture-owned surfaces and intercepted DirectDraw Lock/Unlock.
- SDL/X11 Debug/ASan builds pass. Independent generation parity matches all four
  artifacts; no reconstructed C or generator changes occur.
- All **14** source saves and **58** human-session files retain their sizes and
  SHA-256 hashes. The source bundle verifies. Documentation checks connect
  **298** Markdown documents to README; whitespace and launch JSON checks pass.

Automatic approval review initially returned capacity errors and a deadline
timeout for the final native commands, so those attempts did not execute.
The service later approved a retry; it exposed that the temporary runner had
not been created because its earlier launch was rejected. After preparing that
runner inside the workspace, the complete final checks above pass. These failed
launches and intermediate results are retained, rather than presented as test
failures or omitted from the evidence. No approval check was bypassed.

Final Debug binary SHA-256 remains the pinned human image above; ASan is
`ce12e56dcebe60f9ed765870b1be7ede7715cb41f9581d9fad2f20e2d6ffea50`.
A shared owner such as glow 796 is reused by other original teleport scenes;
only the garden route is newly qualified here. Wider portal composition and
human visual review remain open.

Current continuation: link the next supplied human session to its actual loaded
save. Boots acquisition, hazard protection/expiry, ladder use and extended
stability remain open. Prior castle,
translucency, inventory, acid and audio limits remain in force. No commit, push
or tag change is made.
