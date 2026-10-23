# Recover Packed Event Metadata

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
<!-- /docs-tree:parent -->

Status: completed
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-15

## Goal And Scope

Restore the original packed event priority/dispatch flags at `0x636700..0x63683a` so the action dispatcher selects the correct target type. This task does not establish complete event handling or action-route readiness.

## Evidence And Change

After pose recovery, event `0x3f` reached `FUN_0042b880 → FUN_0043ab74 → FUN_0043cac0` and blocked in a requester. `FUN_00416cb4` initialized separate C globals, while dispatch read zeroed mapped memory. Its original initializer at `0x416cb4..0x4171b8` supplies the missing packed 16-bit table.

The 158-word table is now copied to the original mapped address under `E2R_ACTION_INDEX_PROBE=1`, shared with the corrected action/keyframe path. Existing separate-global initialization remains for unrecovered readers. The change is mirrored in `GenerateRecon.js`.

## Acceptance And Result

1. All table words compare equal to execution of the original initializer in `scripts/check-e2-projection.py`.
2. Gated SDL passes the incorrect event-0x3f actor/requester route and reaches node handling.
3. The following attachment corruption was traced to `FUN_00423858` rotating node `+0x136` instead of `+6`; Task 02 records that repair and the newly exposed polygon-input crash.
4. Generator parity, four Debug builds and default isolated Debug/ASan wrapper pass. Full gated readiness remains open: SDL/GDB crashes in geometry; headless ASan times out in camera 1073 without a sanitizer report.

## Review State

Implementation state: completed for packed metadata only. Keep the gate until Tasks 02/05/01/03 validate the full route. See the [journal](../../../../../journal/entries/actor-cues-and-projection-2026-09-15.md) for evidence and reproduction commands.
