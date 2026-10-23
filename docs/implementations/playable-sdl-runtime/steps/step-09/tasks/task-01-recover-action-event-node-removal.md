# Recover Action Event 0x3f Node Removal

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Enable Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
<!-- /docs-tree:parent -->

Status: completed for node-input/unlink ownership; gameplay acceptance remains open
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-14

## Goal

Recover the node input and unlink/cleanup ownership for action event `0x3f`, allowing the pedestal action to advance beyond its current failure without discarding the event.

## Evidence

Two SDL Debug runs with action indexing, cylinders and the polygon bypass reach `FUN_0042b880` case `0x3f → FUN_0043ab74`, then fault on the helper's uninitialized `in_EAX`. The capture has action `0x9377e3`, progress `779/1102`, camera 175, Joe at `9184,3328,-17416`, and `DAT_0047a76c=1`. See the [cylinder journal and screenshot](../../../../../journal/entries/diagnostic-cylinders-2026-10-14.md). The second run first confirms entry to the polygon boundary; both retain the same action failure.

Original `0x42c041..0x42c043` passes **ESI in EAX** to `0x43ab74`. The callee preserves that node input in EDX at `0x43ab79`, then inspects its owner/parent links. The earlier reconstruction passed event bytes and `iVar9` as generic parameters, while the callee never initialized its actual node input. Do not assume either current parameter has the correct meaning until the dispatcher's ESI selection is traced.

## Scope

1. Trace event-to-node selection in original `FUN_0042b880`, including ESI, actor ownership and the event's target fields.
2. Recover the helper's explicit node input, parent/root list unlinking and directly required cleanup context. Compare owner flags and list topology against the original routine with bounded fixtures.
3. Hand-prove the smallest repair, mirror it in `GenerateRecon.js`, regenerate and verify all four artifacts.
4. Rerun the actual diagnostic route and record the next boundary. This repair alone does not establish completed release, control readiness or locomotion.

## Out Of Scope

1. Dropping event `0x3f`, returning success on unreadable nodes, clearing script-wait flags, or forcing a final position/camera.
2. Original meshes, full DirectDraw fidelity, unrelated cleanup families or enabling action indexing by default.

## Verification

Use the gated SDL Debug route from the journal, first with a bounded event breakpoint to confirm the intended node and then with minimal interruption. Capture action progression, surviving actor/owner lists and real cylinder positions. Debug/ASan must reach the repaired event before counting as runtime coverage; a camera-1073 timeout is insufficient. Preserve the wrapper, arrow matrix, SDL requester checks and polygon bypass comparison.

Keep broader action ownership in [Step 08 Task 01](../../step-08/tasks/task-01-recover-action-context.md). Surface Lock remains [Step 08 Task 12](../../step-08/tasks/task-12-recover-directdraw-surface-lock.md) and must be implemented if a required copy is reached; it is not repaired or proven dispensable here.

## Result — 2026-10-14

Selected-node input, owner table clearing, active/sibling unlinking, recursive children, vertex/polygon dependencies and deletion marks are recovered in the generator and generated C. `scripts/check-e2-node-removal.py` passes 768 original-x86 memory/topology cases plus null/error routing, normally and under ASan. The actual Debug route returns past event `0x3f`; later retained action/actor and script-input repairs reach the real wait-ending opcode. This closes this bounded failure family, not gameplay.

See the [continuous runtime journal](../../../../../journal/entries/f5-diagnostic-route-2026-10-14.md). [Task 02](task-02-recover-post-intro-placement-and-motion-queries.md) owns the invalid height/placement and motion-query inputs now blocking visibility and locomotion. Full-runtime ASan coverage of the complete handoff remains unproven.
