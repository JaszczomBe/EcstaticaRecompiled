# Recover Action Context

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Load and advance action 384 with explicit, source-backed actor and action-slot ownership.

## Scope

1. Recover `FUN_00451880 → FUN_0045190c` parser/current-actor ownership.
2. Recover `FUN_00427584 → FUN_0042ae80` inputs and directly required helper context.
3. Mirror exact repairs in the generator and verify the gated route.

## Out Of Scope

1. Claiming a successful action load fixes all missing geometry.
2. Generic invalid-pointer guards, unrelated helper rewrites, or enabling action indexing by default.

## Implementation Notes

[Step 07 Task 05](../../step-07/tasks/task-05-recover-natural-action-advance-inputs.md) has recovered the three entry inputs and verified the default empty-slot return. Reuse its explicit signature here and rerun the gated probe; the earlier entry crash is historical. ECX/actor ownership across loaded-action helpers and action-384 parsing remain this task’s responsibility.

Step 07's automated baseline is green. Its manual final-scene comparison remains open; the user's continuation request authorized this isolated gated recovery without closing that manual item.

Recovered from the original executable:

- `0x451914` saves `DAT_0047a470` in ECX; `0x451988` restores it on every loader exit. `FUN_0045190c` now retains `entry_actor` across parsing and cached/missing lookups.
- `0x42ae87` preserves the action slot in ECX across helpers. Reset at `0x42aeeb` receives the owning actor in EDX; update at `0x42afdd` receives it in EBX. The C preserves the slot and saves/restores `E2R_actor_calc_context` around those calls. `0x42af03` supplies the next action id from the current action's signed word at `+0x10`.
- `FUN_0042b338` retains the actor in EDI and passes it in EAX to child commit (`0x42b3ed`) and interpolation (`0x42b470`). Both child helpers now receive that actor, and the unused phantom ECX read is removed.

GDB proves action 384 installs at `0xac263c`; child callback actor/current/context are all Joe `0xaa6bd8`. Slot `0xaa6c7e` advances from 0 to 1638 with duration 40, and the enclosing call restores context to zero while retaining Joe as current. This is a bounded first-update proof; chained actions and every nested transform branch are not validated.

The earlier `rep_id=-2991` diagnostic is not evidence of rep payload corruption: it reads actor word `+0x120`, overlapping the high half of the runtime rep pointer at `+0x11e` (`0xf451b008`). The pointed-to rep starts with id 67. A hardware watch on that first word did not fire before the former callback crash. This does not validate the entire rep layout or every possible write.

Before Task 04, the full gated route remained unverified. A diagnostic GDB run captured a packet and exited normally, but its final scene slot was 40, not 175. The plain SDL rerun missed the transient scene-175 completion window and exited 5 after the scene wait expired. ASan independently reached the missing-scene message branch and reported stack-use-after-return in `E2R_ResolveMenuStringList`, called through `FUN_0045233c → FUN_0043cbb4 → FUN_0043cbf0`. [Task 04](task-04-recover-missing-scene-message-inputs.md) has now fixed that separate message-input failure. At Task 04 completion, its gated SDL/ASan reruns both exited 5 waiting for scene 175, with missing scene 40 (`mtorc4`) selected and no sanitizer error. Task 05 has since traced corrupt events to aliased keyframe allocation. Its gated repair now exposes an earlier missing actor input in scene-pose restoration, reproduced by SDL/GDB and ASan. Keep this task active through [Task 06](task-06-recover-scene-activation-pose-inputs.md) and [Task 05](task-05-recover-post-intro-scene-selection.md) validation; the debugger packet is not a stable scene-175 result.

## Acceptance Criteria

1. Original call-site/register evidence names each repaired parameter and actor ownership rule.
2. Action 384 installs and advances; actor ownership remains valid across parse and callback operations.
3. The gated bounded route reaches its settle packet without the current crash; new independent failures are split and recorded.
4. Generator reproduction, builds, default baseline, and applicable debug/ASan checks pass.

## Verification

Use the gated GDB command in the [audit](../../../../../journal/entries/runtime-audit-2026-09-14.md), then repeat without GDB after a candidate repair. Batch GDB can return zero after a caught SIGSEGV; inspect the log and require a completed packet. Compare actor/current pointers before parse, after parse, and at advancement. Run generator checks and applicable Step 07 regressions before closing this task.

Latest checks: generator syntax and all four scratch outputs match (`/tmp/e2-generator-audit-_707at8m`); default debug, ASan, and SDL debug build; default debug/ASan wrapper and all 8 arrow rows pass; default SDL packet exits zero with scene 175 and hashes `321e33d6` / `914159a1` / `5cf799a1`. At the action-owner repair, gated ASan exited 1 and plain SDL exited 5. After Task 04 both gated checks exit 5 without sanitizer errors; full-route acceptance remains open. See the [runtime journal](../../../../../journal/entries/runtime-crash-fixes.md) for commands and evidence.

## Review State

1. Planning state: agreed
2. Implementation state: implemented; gated validation incomplete
3. Notes: Baseline checks pass. Task 04 is complete. Task 06 and Task 05 precede remaining gated validation; scene/position drift and geometry are still unresolved.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.

2. Restored loader actor ownership and direct action-helper inputs; recorded bounded progress and split the missing-scene message failure without closing gated acceptance.
