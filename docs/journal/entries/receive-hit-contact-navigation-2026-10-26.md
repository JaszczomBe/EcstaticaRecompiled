# Receive-hit contact navigation — 2026-10-26

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Task 10](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Runtime context: [Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Previous evidence: [Regression 08 freeze investigation](regression-08-freeze-and-event-callback-2026-10-26.md).

## Reported result and boundary

The user's fresh visible-Debug/headless-ASan potion block,
`.tmp/gameplay-suite/run_20261026_214715_005779/`, finishes **25 PASS / 0 FAIL /
3 BLOCKED / 4 SKIPPED**, **322.26 s**, exit **1**. ASan Trial D never starts
potion traversal: `setup.ReceiveHitEncounter` fails with **target disappeared
or left active table**. The healing/no-op informational summaries then block
because that trial is incomplete. The other seven consumption trials, both
sword continuations and the Debug block complete. No signal, allocation exception,
watchdog stop or sanitizer error is recorded at the failed boundary.

The fixed opponent is original guard **284**. The navigator follows the courtyard
corridor in **204 updates**, then chases the guard while requiring centers within
**240** units. At its first detour, update **423**, Joe is
**(7126,4096,-17215)** and the guard **(7023,4096,-17574)**: centers are about
**373** units apart, with both observed actor **+0x9a** radii **256**. Joe keeps
steering instead of releasing for the original AI attack. Six detours follow;
at update **1677**, camera **169→166**, guard 284 is absent from the active list
and the driver stops. Joe still has health **100** and no attributed hit.
This does not establish why the original game deactivated that actor.

The same run's successful C encounters receive hits at center distances
**381** (Debug) and **379** (ASan), before reaching the old center threshold.
This explains why the overly narrow input policy often passed anyway.

## Investigation and final input policy

A first radius-only experiment releases movement at **512** units. Its full
block, `potions/`, retains **22 PASS / 2 FAIL / 6 BLOCKED / 2 SKIPPED**,
**320.81 s**, exit **1**. ASan C receives no hit within **2400 updates**; Debug C
receives a later hit after six detours, then exhausts potion-route replans from
that displaced position. Debug D passes. This experiment is not acceptance:
nearby actor centers alone do not establish original melee contact.

Original **0x42f075–0x42f0ad** compares the actual melee-node position with Joe
and his **+0x9a** radius. It does not use center-to-center nearness as a hit.
The input controller now aims in front of the observed opponent, offset along
its live heading by its own radius, with the existing **240-unit** approach
band. Waiting retains **100-unit** hysteresis in front and resumes pursuit when
Joe falls behind. This is steering guidance; actual health loss and the original
melee stack/node-owner attribution remain the success predicate. A bounded
read-only observer also retains up to **64** original melee-node position samples.

A focused fixed-284 selection, `facing-damage/`, retains **7 PASS / 1 BLOCKED**,
**48.28 s**, exit **1**. Debug receives original guard damage and quits normally.
ASan reaches the corridor but guard **284** is already absent; guard **293** is
active at **(8738,4096,-16987)** on Joe's floor. A newly started full block,
`facing-potions/`, is intentionally interrupted at **77.68 s**, exit **130**,
when this eligibility restriction is identified. It is not qualification.

The declared receive-one-hit goal now allows the two original audited guards
**284/293**. Selection still rejects missing, dead, unrepresented, nonattacking,
misidentified and different-height actors. If a chosen opponent becomes
unavailable, reselection consumes the existing shared replan budget and repeats
those checks. A replaced instance still fails. Explicit fixed-target goals,
including smith contact and sword pickup, cannot substitute targets. This follows
Task 10's original eligible-opponent objective; the prior fixed-284 policy was an
implementation restriction, not a user requirement for the logical damage case.

Nearness never passes damage: the selected opponent must inflict surviving real
health loss through the original melee handler. No scenario retry, health/RNG or
actor write, potion-type injection, recovered-runtime or generator change is
introduced. Other navigation goals keep their existing center/waypoint guidance.
The update, replan and host bounds are unchanged.

Seven added deterministic contracts cover successful and failed recorded
geometry, facing guidance, released input, real-hit requirements, other goals,
moving behind an opponent, same-floor eligibility, permitted/bounded reselection,
fixed targets and replaced instances. All **38** navigation and **61** suite
contracts pass (**99 total**).

An eligible-guard focused run, `eligible-damage/`, retains **7 PASS / 1 BLOCKED**,
**55.22 s**, exit **1**. ASan receives attributed original damage and quits;
Debug's preceding movement leaves Joe at **(7854,3328,-18678)**, beyond the old
**1800-unit** local courtyard join. The final corridor helper prefers the closest
observed height and uses the established read-only scene-floor planner beyond
that local boundary, sharing the same navigator's budgets. A retained real-grid
plan connects this displaced position to the pedestal anchor in **13 points**;
a new driver contract checks that dispatch and rejects unmatched heights. No
script policy or movement limits are expanded.

## Qualification

Artifacts are retained under `.tmp/regression08-contact-20261026/`, including
`reported-failure.json`, `displaced-corridor-plan.json`, contracts and every
failed/interrupted attempt above. Final qualification uses the same frozen
sources and unchanged pinned binaries, with visible Debug and headless ASan:

| Selection | Result | Time |
| --- | --- | --- |
| `final-potions/report.html`, full potion block | **26 PASS / 6 optional SKIPPED / 0 FAIL / 0 BLOCKED**, all **22 required** checks | **317.58 s** |
| `final-damage/report.html`, receive-hit after movement | **8 PASS / 0 FAIL / 0 BLOCKED / 0 SKIPPED** | **57.01 s** |

All **twelve** native game processes exit zero through the menu and complete
inspection. All **21** test-source hashes in both final selections match current
files; `validation.json` verifies those hashes, pinned/live binary identity,
required-result status, original melee attribution and inspection completion.
There are no native signal, allocation exception, watchdog or sanitizer captures.
All six final receive-hit encounters establish original guard **284** damage
**100→95**, and all eight potion pickups are consumed and removed. Debug D draws
healing **95→100**; Debug A draws invisibility; Debug B/C and all ASan trials draw
poison. Six optional skips cover four unobserved branch summaries and the two
unfinished death/expiry/cure cases. These random outcomes are observed, not forced.

The focused Debug journey actually exercises the new scene-floor join from
**(7787,3328,-18661)**, **2533** units from the pedestal anchor, and then receives
attributed damage. ASan joins the corridor on floor **3712** before the same
successful goal. The final native runs need no opponent reselection and select
284 throughout; guard-293 selection and bounded reselection retain deterministic
contract/asset evidence, without a native 293 hit claim in these selections.

Executable SHA-256 remains identical to the user's failed run:

- Debug: `18d276951a842ac75a8e59dde47783e7ce3e59a7bf8b3bf71c895146221b7fd0`.
- ASan: `7212786677358c0e0ac614a88dbd9a7e24abd38a81192f3c3a75a04eadbbf487`.

Final source SHA-256:

- Navigator: `85a7953cd591b6d611b5d1726f6beed8ab885897ae2974c5bc6941c89a00ebb6`.
- Gameplay steps: `e590c1591e1f64cec6b5435df2eed8cc4c10e8677b7eb48966f111e953c5eb84`.
- Reconstructed C (unchanged): `04b41b3fec5f293e215dce2ab188cf8dc029ba2bf8cc2f59f576c7d8c5c1bcab`.
- Generator (unchanged): `248d310bb6dccec17169d95e08c98057430e91fd68b9d1d6cf146311bffc16ea`.

These selections do not establish arbitrary route/enemy reliability, the full
regression suite, human F5 acceptance or final potion death/expiry/cure. The earlier
screenshot freeze remains unconfirmed. No commit or push is made.
