# Consumed potion removal — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The user reports that drinking leaves the bottle attached, including after
collecting the sword. The new recording confirms two separate attachments:
bottle **537** in the left hand and sword **3717** in the right. The sword does
not replace the bottle; the initial interpretation of that transition was wrong.

## Recording and original cause

Human session **20261024_145333_421** ends cleanly. Its pinned Debug executable
has SHA-256
`f6da87bca7801e420c96f8b59eb93924421cafda5cf3534c4c2b68cd83393f80`.
Exact replay matches all **549 checkpoints**, completing at sequence
**2,044,462,120**. Materialized inspection shows the bottle attach at snapshot
**285** and the sword at **540**; the final bottle still has representation
**67** and attachment owner **0** (Joe). This is pre-repair evidence.
The immutable export is `.tmp/replay-bugs/bottle-human-20261024`, created from
an inactive copy without changing the user's session.

The reconstructed animation-name interning and lookup helpers used **0x1117**
bytes, while their allocated pool and original **0x446814** use **0x445c**
(**17,500**) bytes. The installed animation directory contains **1,800 names**
occupying **16,981 bytes**. Names after the first **448** became missing IDs;
remapped script tokens consequently contained **0x3fff**, which the original
interpreter correctly ignores as an invalid animation.

For the purple-potion script, the bottle's command becomes **0x32b0** after the
repair: animation **688**, `glofade`. That original resource chains to animation
**1574**, `potvan`, whose event invokes script **491**, `ken:RemoveActor`
(serialized one-based code **492**). Its opcode **0x5c** removes the bottle,
including its representation and reciprocal hand attachment. `joedrink` itself
contains a sound event, without a bottle-removal event. Fixing the name pool
restores this existing chain instead of inventing a cleanup timer or hiding a
particular actor in the renderer.

Both animation-name helpers now use the original byte boundary. Newly interned
animation IDs also clear their own loaded-action slots, matching original
**0x446860**; duplicate names preserve an existing resource. All repairs are
mirrored in `GenerateRecon.js`, and all four scratch-generated artifacts match.

## Verification

| Check | Result |
| --- | --- |
| Pinned human replay | All 549 exact checkpoints; clean completion |
| New `check-e2-animation-names.py`, normal/ASan | All 1,800 installed names match actual original x86 append, lookup, reuse, pool bytes and slot ownership; 1,352 names exceed the former byte limit |
| Existing actor/script-name fixtures, ASan | 4,120 actor names/startup literals and 256 late script-name cases pass |
| Fresh SDL Debug/ASan potion routes | Random dispatch 189→183; `joedrink`, poison action 409, bottle representation cleared and attachment pointer zero within the 450-update observation |
| Fresh SDL Debug/ASan potion-to-sword routes | Random dispatch 189→1803; bottle removed, sword collected, all four Ctrl/arrow attacks and movement pass; bottle remains removed |
| Builds and baseline | SDL/X11 Debug/ASan build; Debug controls, ASan controls and ASan modal baseline pass |

Both longer routes finish with Joe health **100**, state **4**, sword
representation **9**, reciprocal sword attachment and no held input or sanitizer
report. Potion attachment **+0xf2** and representation **+0x11e** remain zero
after the sword checks. These routes use only bounded SDL inputs, with recording
off; they do not assign actor positions, actions, health, RNG or camera state.
Their shared `--sword-pickup` switch selects the probe's input-route branch; the
retained probe records the distinct potion and sword stages explicitly.

Final SDL SHA-256:

- Debug: `4544fc096271fb51f1430c5e295776dca58798256b6f94c5661fe11ab88dbd3c`.
- ASan: `319b6b4eff8d26d0536c89137659a7d52ae50501537c03c2dcf4df69412f7328`.

Evidence and probe copies are retained in `.tmp/bottle-review-20261024/`.
Temporary originals include `/tmp/e2-bottle-human-exact.log`,
`/tmp/e2-bottle-animation-*`, `/tmp/e2-bottle-fixed-*`,
`/tmp/e2-bottle-sword-{debug,asan}*` and `/tmp/e2-bottle-baseline*`.
Healing from below maximum health, eventual poison death/cure, invisibility
fade, other pickups and broad gameplay/full-render acceptance remain open.
Fresh human F5 repetition is still required for manual acceptance of this fix.
No commit or push is made.
