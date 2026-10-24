# Random potion outcomes — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The user reports a potion producing no visible effect and identifies healing,
poison and no effect as possible original outcomes. The latest recording selects
a valid conditional cure/no-op branch. Repeated fresh input routes are used to
seek the other outcomes; exact replay preserves recorded RNG and cannot provide
new random selections by repetition.

## Latest human recording

Session **20261024_153511_995** is complete and exits normally. The pinned Debug
SHA-256 is
`e1f0f48dfc4d14ecbdfdc313adff596193d43d9d20035b72ac425703776f5465`,
at revision **eff8ef3**. Its inactive copy is exported as
`.tmp/replay-bugs/potion-no-effect-human-20261024`.

A read-only GDB observer replays that pinned executable and matches all **135
checkpoints**, ending cleanly at sequence **1,704,839,921**. At checkpoint **122**,
sequence **1,472,734,230**, scripts **189**/`ken:fakepot` and **1803**/`ken:potmagic`
run with owner Joe and target/child **537**. Joe has health **85**. No potion timer
is scheduled and the effect-adjustment helper is not called during this pickup.

Materialized inspection shows health **100→95→90→85** before drinking, then
unchanged **85** through the end. The bottle attaches at snapshot **796**, enters
`glofade` (**688**), chains to `potvan` (**1574**) at **807**, and loses attachment
and representation at **809**. Joe enters `joedrink` (**369**) at **801**.
This is successful consumption, without a healing or poison effect.

## What the selector can choose

The original name directory and loaded script tokens identify four destinations:

| Script | Requested behavior |
| --- | --- |
| 183 / `ken:purpotion` | Poison action 409 and delayed `poisondie` action 5 |
| 156 / `ken:greenpotion` | Health action 391 / `gethealth` |
| 157 / `ken:blupotion` | Invisibility action 383 and delayed fade 387 |
| 1803 / `ken:potmagic` | Conditional poison cure or invisibility cleanup; otherwise no effect |

The last branch still requests drinking and bottle removal. Its remaining work
is inside timer conditions: opcode **0x6b** checks Joe's scheduled action **5**,
otherwise scheduled **387**. With neither present, both effect bodies are skipped.
The poison body cancels action **5** and schedules **459**/`joedetox`; the
invisibility body reschedules fade and adjusts its effect value. Thus unchanged
health with no poison/invisibility indicator is valid for this branch. The
recording does not establish cure behavior with an existing affliction.

## Fresh outcome checks

Fresh routes keep RNG and the clock live, use normal SDL movement/Space and
disable recording. Different idle waits before pickup sample different branches;
no random value, health, actor/action or camera state is assigned. Full-health
trials establish branch dispatch and cleanup only, not healing from damage.

The original human keyboard holds can also be applied by update counts in a
fresh process, followed by adaptive walking to the workshop. This reproduces
natural damage to **85** before pickup. Applying those holds by raw clock ticks
was insufficient because debugger pauses distort wall-clock timing. Earlier
enemy-contact routes also failed to produce damage and are excluded from healing
acceptance.

Current completed checks:

- The human no-op branch completes with health **85**, bottle removal and clean
  exit; all exact replay checkpoints match.
- Fresh poison routes run **189→183**, start **409**, retain the future death
  timer and remove the bottle. A damaged-player route preserves health **85**
  during this bounded onset observation.
- Fresh invisibility routes run **189→157**, execute **383**, queue fade **387**
  and remove the bottle. Original mesh appearance and final expiry remain separate.
- Two fresh damaged-player runs select **189→156**, execute health action
  **391**, and increase health **85→100** by the **225-update** sample. Both
  finish the **450-update** observation alive, controllable, with no pending
  potion timer and the bottle detached/unrepresented. Observed selector values
  **44804** (**68%**) and **43816** (**66%**) take the original healing branch;
  these values are read, not assigned.

There are **17 successful fresh pickups** in this review: **2 healing, 10 poison,
4 invisibility and 1 conditional no-op**. Eleven started at full health; six
used the naturally damaged input route. Eight earlier routing/damage attempts
stopped before pickup and are excluded. Trial counts are observations, not an
estimate of independent probabilities: scripted starts and pickup waits can
correlate selections. Fresh checks use the pinned-equivalent current Debug
binary; this is not new ASan acceptance.

Healing, poison onset and the healthy/no-affliction no-op are now distinguished
by actual state changes. Final poison death, invisibility expiry/cure and
original mesh appearance remain unaccepted. The existing health/status panel
correctly reports the onset states; poison need not immediately reduce health.

No runtime repair is justified by the human no-effect result. Broader pickups,
extended stability and original rendering remain deferred. Evidence, input-route
copies and trial summaries are retained in `.tmp/potion-outcomes-review-20261024/`;
the matching temporary files use `/tmp/e2-potion-{latest,wait,outcome,human,damaged}*`.
