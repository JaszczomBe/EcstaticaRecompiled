# Recover Action Context

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-14

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

## Current Follow-Up — 2026-09-15

The pose-input crash described above is historical: Task 06 now supplies the actor and explicit destinations. Camera/math and matrix-destination recovery plus Task 08 packed event metadata move gated SDL into a polygon-input crash in `FUN_00431a7c`; gated headless ASan times out in camera 1073. Resume Task 02 geometry inputs before Task 05/01 final placement/action validation. The new cue projection does not establish living actors or correct movement. Default isolated Debug/ASan regressions pass; the new manual F5 check remains pending. See the [2026-09-15 journal](../../../../../journal/entries/actor-cues-and-projection-2026-09-15.md).

## 2026-09-21 Follow-Up

Task 02 has passed the polygon reference-pointer failure, and Task 10 subsequently recovered the flat-lighting inputs. The next minimally interrupted gated SDL stop is in framebuffer copying at `FUN_00418514`, owned by [Task 11](task-11-recover-dirty-rectangle-copy-inputs.md). Gated SDL ASan still times out in camera 1073. Default regressions pass; placement and living actors remain unproven. See the [lighting evidence](../../../../../journal/entries/polygon-lighting-2026-09-21.md).

## Original-Game Action/HUD Checkpoints — 2026-10-14

The [reference sequence](../../../../../journal/entries/original-game-reference-2026-10-14.md) progresses from restraint opening/release to free standing Joe, then HUD and visible movement in the same courtyard without an action-error dialog. Compare action ownership/advancement and key/event ownership at each phase. Do not assign the whole release sequence to action 384 from `dav:heropick`'s name alone.

`FUN_0044f508` case `0x75` clears `DAT_0047a76c` and calls `FUN_004559bc`, whose HUD path checks that flag and actor 0. Trace actual script completion/flag state and rendered HUD with actor progress; input latches or `Start_sc` reaching 1102/1102 do not satisfy the observed handoff. Task 12/02 still precede full-route acceptance.

## 2026-10-14 Copy Follow-Up

Task 11 now recovers copy/page/descriptor inputs and passes 2,048 original-x86 copy/ownership plus 256 dirty-list dispatch cases, normally and with ASan. The real gated copy still faults because DirectDraw Lock returns base/pitch 0/0 from a generic compatibility stub. [Task 12](task-12-recover-directdraw-surface-lock.md) owns the next provider failure; Task 02/05/01 full-route validation remains incomplete. Default regressions pass, and gated SDL ASan still times out in camera 1073. See the [rectangle journal](../../../../../journal/entries/rectangle-copy-2026-10-14.md).

## Review State

The [Step 09 continuation](../../step-09/step-09-enable-diagnostic-gameplay.md) now reaches action event `0x3f → FUN_0043ab74` with a visible projected Joe and script wait still set. [Step 09 Task 01](../../step-09/tasks/task-01-recover-action-event-node-removal.md) owns the newly exposed node-input/unlink contract. Original geometry and surface-copy acceptance remain separate; they no longer have to complete before that diagnostic action repair.

1. Planning state: agreed
2. Implementation state: implemented; gated validation incomplete
3. Notes: Baseline checks pass. Task 04 is complete. Task 02 and Task 05 precede remaining gated validation; scene/position drift and geometry are still unresolved.

## Change Log

### 2026-09-14

1. Created from the runtime/documentation audit and the approved task split.

2. Restored loader actor ownership and direct action-helper inputs; recorded bounded progress and split the missing-scene message failure without closing gated acceptance.

## F5 Continuation — 2026-10-14

[Step 09's continuous-runtime continuation](../../../../../journal/entries/f5-diagnostic-route-2026-10-14.md) supersedes the old event-0x3f diagnostic crash. F5 now selects cylinders/action indexing/mesh and HUD omission; node-removal, retained action/actor and script-input comparisons pass. Debug reaches the wait-ending script, then selects an invalid height and leaves Joe behind camera 83 without motion. Step 09 Task 02 owns that placement/query/control work. Original-render acceptance and compatibility Lock remain open; gated ASan faults in a motion query.
