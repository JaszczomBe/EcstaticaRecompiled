# Recover Release Gravity And Floor Query Ownership

Status: completed for the observed release-height failure; full motion acceptance remains Task 02
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-19

## Goal

Preserve valid floor/gravity inputs after action motion and input release, then prove the same displacement, turning and release boundaries in Debug and ASan. Retain genuine floor failures and scene transitions; do not clamp height or force courtyard camera 175.

## Evidence

[Motion query recovery](../../../../../journal/entries/player-motion-query-2026-10-16.md) closes Task 05's vector/output contracts. Debug completes the corrected arrow probe: Up displaces, Left/Right turn and release stops those changes. Down selects action 13/slot 183 but has no observed displacement in 60 updates. ASan displaces under Up, then faults after release; full experimental sanitizer acceptance remains open.

`/tmp/e2-motion-query-release-asan` preserves before/Up-held packets and the later stack. `/tmp/e2-motion-release-watch.log` catches the first bad height write: `FUN_00449680(actor=0xaa6bd8, factor=6)` stores `local_18=-16000` at actor `+0x86`, through `FUN_004495e0 → FUN_00427584`. Position becomes `9800,-16000,-17354`. A subsequent no-view selection enters fallback resource 7; action advance/event `0x16` then faults in the root-pose child walk. Diagnose the first height/query producer before expanding into fallback teardown.

The durable motion probe now uses extended arrow messages and verifies actual held bytes. Earlier zero-lParam release probes left arrows held and are superseded. Their simultaneous-input path exposed another lost actor at two `FUN_00427584 → FUN_0042b074` calls (actor 1). The user subsequently reported the same stack after rotation then Up. The [turn-caller continuation](../../../../../journal/entries/player-turn-callers-2026-10-16.md) now repairs both actor arguments from original `0x429653/0x429687`, with 1,296 original-code cases normally/ASan. Debug Left+Up and Right+Up move/release correctly in bounded probes. Both ASan combinations retain Joe through 20 turn calls; release still produces bad heights (-6400/-16000) and Right later faults in fallback teardown. This caller repair does not close the gravity task.

## Resolution — 2026-10-19

The [queued idle-action investigation](../../../../../journal/entries/player-idle-action-2026-10-19.md) traces the failure upstream of gravity. The initial floor query is 3328 and Joe's cell is 27625. On release, `FUN_00427584` passes the representation pointer as the action ID to `FUN_00451880`; an unrelated FAN load replaces that cell with 4. Its floor byte 253 produces -16000 through the existing height arithmetic. Gravity consumes the already replaced map.

Original `0x429bcc..0x429bd5` loads the queued action word at actor **+0x162**. The one-line caller repair and generator mirror restore that input. The new original-code fixture passes 1,440 cases normally and under ASan. Both full arrow probes now complete with height 3328 and camera 175. This closes the observed bad-height producer without changing gravity, clamping coordinates, retaining a map across legitimate loads, or forcing a camera.

Task 02 remains active: Up release now executes a queued action with additional displacement, so earlier claims of immediate release stopping are superseded. Establish its source-consistent completion and settled state, Down displacement, real floor/stair/blocked-boundary behavior, two view crossings and 60 seconds after observed readiness. The unexercised lower gravity/landing branches and fallback child conversion retain their separate limits; the full experimental runtime is not declared sanitizer-clean.

## Verification And Limits

Use the four F5 experiment flags. Keep all synthetic fixture results distinct from original-data/runtime proof. Preserve default wrapper, eight arrow rows, SDL requester checks, four generated artifacts and staged/unstaged separation. Full NPC activation, original meshes/HUD, manual startup timings and full runtime ASan remain separate acceptance.
