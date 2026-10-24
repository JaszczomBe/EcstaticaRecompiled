# Workshop random potion and delayed effects — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The new human recording confirms pickup of workshop bottle **537**/`fakepot2`.
The original script chooses a random potion effect; its name does not mean a
noninteractive prop. This corrects that interpretation in the
[earlier review](long-play-cache-reclamation-and-markers-2026-10-24.md).
Pickup and the drinking action work, but delayed effects were broken. Three
original contracts are restored, with generator mirrors and original-code
comparisons. Fresh Debug/ASan input routes now execute the poison action.
Healing from below maximum health and final bottle disappearance remain open.

The [bottle-removal continuation](consumed-potion-removal-2026-10-24.md)
subsequently resolves the persistent attachment through the original fade/removal
chain. Bottle-cleanup limits below describe this earlier snapshot.

## Human recording

Session **`session_20261024_142028_732`** is complete and exits with code **0**.
Its pinned Debug SHA-256 is
`90557987e6b86f22c6a34b67c24b50a8ece77bb672462bafd9d4df852ad07aef`.
The immutable export is `.tmp/replay-bugs/potion-human-20261024`, made from an
inactive temporary copy without altering the user's session.

Exact replay using that pinned executable matches all **742 checkpoints** and
finishes cleanly at sequence **2,210,449,273**. Inspection deltas were materialized
before comparing actors. Bottle **537**, representation **67**/`potion`, attaches
to Joe at snapshot **502**. Joe later enters action **369**/`joedrink`; the bottle
moves from its original placement with the hand attachment. Joe retains health
**100** throughout and quits using the menu normally.

A read-only GDB observer records `ken:fakepot` (**189**) entering at checkpoint
**109**, sequence **1,511,632,163**, with owner **0**, target **537**, child **537**.
It dispatches `ken:purpotion` (**183**) with the same arguments. Its commands
request drinking, poison action **409** after delay **5**, and `poisondie` action
**5** after delay **1500**. The scheduler converts each delay to **7 × delay**
engine ticks. Lack of immediate health loss alone does not prove poison failed;
the missing scheduled records and dispatch are the relevant failures.

The user supplies original-game screenshots and identifies the same floor
bottle as a random health/poison pickup. Runtime script **189** independently
confirms randomized dispatch. Earlier workshop attempts really left this actor
unchanged, but calling it a decorative prop was incorrect. Its diagnostic marker
now uses the potion bottle shape/category, without exposing the random outcome
before interaction.

## Original contracts and repairs

1. **Timer opcode arguments.** Original **0x44fb4f–0x44fb84** separately decodes
   actor, action and signed delay words, then supplies EAX, EDX and EBX. The
   reconstruction passed only two arguments and retained unrelated upper bits
   in the actor ID. Observed failing calls used actor values **3448569856** and
   **4102029312**, instead of Joe **0**. `FUN_00457cf0` now receives all three
   arguments, retains the selected actor across allocation and uses the original
   delay. Its other caller preserves original **0x416190–0x4161b8** inputs
   **actor 0, action 6, delay 1**.
2. **Timer pool address.** Original **0x4538c0–0x45391c** scans **100 records** of
   **10 bytes** at **0x009373dc**. Initialization already uses this mapped pool,
   but allocation used unrelated scalar host globals. Enabling real scheduling
   exposed an ASan global-buffer overflow when writing the returned record.
   Allocation now reads, clears and returns the original mapped pool addresses.
   No new sanitizer exclusion is added.
3. **Due-time comparison.** Original **0x4279e3–0x4279ed** subtracts the deadline
   with wrapping arithmetic and tests a signed result greater than zero. The
   reconstructed clock global is unsigned, making the old `−1 < difference`
   expression false. Timers could be queued yet remain pending after their due
   times. The selection condition now explicitly tests the signed wrapped
   difference, retaining original queue priority and action loading.

All C changes are mirrored in `GenerateRecon.js`; all four scratch-generated
artifacts match. No random result, actor coordinates, health or potion script is
replaced with a shortcut.

## Verification and limits

| Check | Result |
| --- | --- |
| Pinned original human replay | Complete, all 742 exact checkpoints match; clean exit |
| `check-e2-potion-timers.py`, normal/ASan | 4,096 actual original timer/list/allocator cases, 4,096 original script argument cases and 4,096 original deadline/priority selections pass |
| Existing queued-action/pose fixture, ASan | Original scheduled completion and pose/spawn contracts pass |
| Marker fixture, normal/ASan | Random workshop bottle classifies as potion; projection/read-only/presentation checks pass |
| Fresh SDL Debug/ASan poison routes | Real SDL movement/Space selects scripts 189→183, attaches bottle, starts `joedrink`, queues actions 409/5, starts action 409 and removes its timer |
| Builds | SDL/X11 Debug/ASan build |
| Baseline wrapper | Debug, ASan controls and ASan modal checks pass |

The final routes wait **90 update frames** before Space and observe **450**
updates afterward. Both retain Joe health **100**, state **4**, with the future
poison-death timer still pending and no sanitizer report. An earlier separate
ASan route selects **157**/`ken:blupotion`, confirming another random branch and
its fade timer; it preceded the final due-time repair. It is not final invisibility
or fade acceptance. The route probes disable recording and use input only;
health, RNG, action, position and camera state are not assigned.

The timer fixture executes original timer allocation/insertion, intercepting an
unreached error requester. Its selection comparison intercepts action loading;
live routes supplement that bounded contract. Synthetic clock cases use the
production unsigned clock type, including equal, overdue, future and queue
priority cases. Fixtures do not establish all potion types or full scene logic.

Final bottle actor **537** still has representation **67** and a live attachment
in the sampled state. The current proxy renderer does not establish original
bottle disappearance/empty-hand presentation. No speculative deactivation is
added. The provided original-game purple appearance also remains outside full
mesh/shading acceptance. Healing from below health 100, the delayed poison death,
cure/fade behavior and bottle cleanup need separate bounded checks. The full
human replay above is evidence for the pinned pre-fix executable; corrected
runtime acceptance comes from the new input routes and comparisons.

Final SDL SHA-256:

- Debug: `f6da87bca7801e420c96f8b59eb93924421cafda5cf3534c4c2b68cd83393f80`.
- ASan: `b91bb1ba0af75cf79e7811666ddc05a0c8d558740ef7c996e665b1480253a9e4`.

Evidence: `/tmp/e2-potion-human-exact.log`,
`/tmp/e2-potion-human-transitions.json`, `/tmp/e2-potion-detail-trace*`,
`/tmp/e2-potion-original-*`, `/tmp/e2-potion-timers-fixture*`,
`/tmp/e2-potion-final-{debug,asan}*` and `/tmp/e2-potion-baseline*`.
The bounded input probes and selected artifacts are retained in
`.tmp/potion-review-20261024/`. No commit or push is made.
