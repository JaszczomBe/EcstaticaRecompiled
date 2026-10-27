# Natural potion consumption — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Runtime owner: [Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Navigation owner: [Task 10](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).

The user requests consumption and observation of the naturally selected potion
effect, including no effect. A regression run must not require a particular
random type or inject a replacement pickup. The four fresh trials retain their
bounded waits and live RNG; their four branch summaries are now optional.
Required trials still verify pickup, drinking, reciprocal bottle attachment,
removal and the actual branch's health/action/timer outcome. A healing draw at
full health and an unafflicted conditional no-op are valid consumption; only
the informational healing-from-damage summary requires initial health below 100.

## Reported failure and repair

The supplied run is `.tmp/gameplay-suite/run_20261026_193419_969857/`:
**12 PASS / 8 FAIL / 10 BLOCKED / 2 SKIPPED**, **242.71 seconds**. Trial A/B/D
dispatch potion scripts and effects but leave actor **537** attached and
represented. Trial C fails a fixed return toward the pedestal after receiving
real damage, at actual height **4096**. The four branch gates then block.

Read-only inspection confirms that actor **537** remains in action **384**,
instead of the bottle fade/removal chain. Current reconstructed C retains the
previously documented three animation-name regressions: lookup/intern use
**0x1117** bytes instead of the allocated/original **0x445c**, and a newly
interned animation does not clear its resource slot. The original-x86 fixture
reproduces the slot-ownership failure before repair. Original append/lookup
instructions **0x44679c–0x446874**, **0x441ac8–0x441b24** and original new-slot
clear **0x446860** establish the existing generator repair. Restoring those
three C hunks matches `GenerateRecon.js` exactly; no new generator change or
unrelated regeneration is needed.

Both normal and ASan original-x86 fixtures now pass all **1,800** installed
animation names, including **1,352** beyond the smaller limit, with append,
lookup, reuse, byte-pool parity and resource-slot ownership. All four scratch
generated artifacts match current source. Damaged potion traversal now shares
the existing bounded navigator and nearest height-compatible workshop join;
the selected bottle and its assertions retain their original identities.

The first modified visible-Debug/headless-ASan run, `visible-debug/`, retains
**20 PASS / 5 FAIL / 5 BLOCKED / 2 SKIPPED**, **275.01 seconds**. All eight
bottles disappear. It exposes a stale direct bottle-to-sword leg in both builds,
plus three false effect failures: Debug C heals **95→100**, ASan D heals
**90→100**, and Debug D queues invisibility fade **387**. Their observed loader
arguments are **0xf37e0187**, **0xf7370187** and **0xf37e017f**. The production
loader explicitly consumes `(short)param_2`, so the observer now checks its
low-word action identity (**391** or **383**), retaining raw arguments as
evidence. This is a test-observer correction, without changing effect logic.

Potion-to-sword now returns around workshop geometry through the established
bottle/prop corridor with the shared navigator. Its setup has a separate
checkpoint; actual sword attachment, four attacks and the final removed-bottle
assertion remain required. Shared and isolated execution call the same helper.

The next run, `visible-final/`, retains **23 PASS / 1 FAIL / 3 BLOCKED /
5 SKIPPED**, **326.57 seconds**. Both sword continuations and all reached
consumption/effect assertions pass. ASan C receives its real hit at
**(3611,4096,-17894)** after a longer guard chase. Its nearest workshop join is
**4257** units away, beyond the existing **4000**-unit local boundary. The final
driver retains the accepted local joins and uses the existing read-only scene
planner for farther connections, within the same navigator update/replan/host
bounds. A saved real-grid plan connects this failed position to corridor node
**(7170,4096,-15558)** through **23** points, with no script-policy expansion.

An exploratory always-planned join (`scene-join-final/`) is interrupted after
**54.61 seconds**, exit **130**, and is not acceptance. Offline validation shows
that its conservative script/terrain policy rejects some already accepted local
corridor connections. This approach is narrowed to farther joins before final
qualification. The interrupted report and all failed attempts remain retained.

The final-code visible-Debug/headless-ASan run, `bounded-join-final/`, retains
**25 PASS / 0 FAIL / 3 BLOCKED / 4 SKIPPED**, **437.26 seconds**, exit **1**
because Debug B never reaches startup acceptance. Its runtime input log records
desktop **Space/C/A/N/Alt** events outside the scripted input stream. Frames stop
during the intro, simulation time remains zero, and no potion input is exercised.
The stalled GDB is explicitly interrupted after **173.08 seconds**; its retained
`SIGINT` is agent-generated, not a spontaneous runtime crash. The other final-code
visible Debug trials, both sword continuations and the full ASan block pass.
ASan's lane finishes **13 PASS / 3 optional SKIPPED**, exit **0**, with five clean
native menu exits and complete inspection. Debug D selects a valid no-op at
health **95**, with bottle removal and no health change.

Debug qualification now uses a headless full block to exclude desktop input;
the ASan lane already passes on the same source and binary. The visible run is
retained as failed lifecycle evidence rather than relabeled as accepted.

## Qualification

Evidence is retained under `.tmp/potion-consumption-20261026/`, including the
sandbox `SIGSYS` fixture attempt, actual pre-repair assertion failure, both
passing original-x86 fixtures and before/after generation comparisons.
The runner contracts pass **58** tests, including every natural outcome,
no change, missing effects, lingering bottles, optional branch reporting and
post-hit height-aware corridor joins, 16-bit action IDs and the sword sequence.
All **31** navigation contracts also pass: **89** contracts in total.

Final qualification uses the same frozen sources and pinned binaries:

| Accepted selection | Result | Time |
| --- | --- | --- |
| `bounded-join-final/asan/report.html`, full headless ASan lane | **13 PASS / 3 optional SKIPPED**, exit **0** | **254.74 s** |
| `headless-debug-final/report.html`, full headless Debug block | **14 PASS / 2 optional SKIPPED**, exit **0** | **243.94 s** |

Combined qualification is **27 PASS / 0 FAIL / 0 BLOCKED / 5 optional SKIPPED**:
all **22 required** results pass. The skips are three unobserved random outcomes
and two unfinished death/expiry/cure cases. The eight fresh pickups naturally
observe all four branches across the two builds, without requiring that result:
ASan heals **95→100**; Debug B selects no-op at **100**; invisibility and poison
retain their respective fade/death timers. All bottles disappear, both sword
continuations pass, and all **ten** qualifying native processes exit zero through
the actual menu and complete inspection. All **20** recorded test-source hashes
match current files. The receipt is `validation.json`, with native outcomes,
source/binary identities and retained attempts.

The farther scene join is covered by its real-grid plan and driver contract;
none of the final accepted native processes needs that fallback. Actual traversal
of that farther connection remains unaccepted. The final visible Debug run
retains its startup/input interruption described above; it is not a full visible
block pass. Its successful A/C/D trials separately retain natural invisibility
and no-op consumption evidence on current source.

Pinned SDL executable SHA-256:

- Debug: `3fd32dbed0c840075030d758d00fbeadd0c31a3982666e2bff98cde2c11e80aa`.
- ASan: `66a16a3259591de06821e51c94b9e045c13f24e2acc7cbe8cc125f6af6935ce2`.

Source SHA-256:

- Reconstructed C: `347b93b627ed54ed907888c9d65ad8e16aa79556ded9692d84063b56a56c6377`.
- Existing generator: `bfaac9a9462d20e470e300439d5392cfb33f42215097f310ccbce4eb06e2c0e2`.
- Original executable: `737e27ddfb76501ba6caf4f504b0c128854a36733526b17d30f635a1c255025b`.

This does not establish every random branch in every run, final poison death,
invisibility expiry/cure, arbitrary other pickups, human F5 acceptance or the
full regression suite. Random branch coverage is recorded without promising
unobserved behavior. No commit or push is made.
