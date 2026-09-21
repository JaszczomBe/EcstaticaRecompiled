# Recover Post-Intro Scene Selection

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-21

## Goal

Explain and recover the position/scene-selection inputs that send the gated post-intro actor from scene 175 through 87 to missing scene 40, before claiming stable gameplay or visible Joe.

## Scope

1. Trace Joe's live coordinates and scene selection from sub-intro completion, before action-384 loading and its first child commit.
2. Compare the first divergent position/query/scene-descriptor operation with the original executable and recover the directly responsible inputs or layout.
3. Rerun gated debug/ASan scene readiness and Task 01 acceptance, with generator parity and default regressions.

## Out Of Scope

1. Forcing scene 175, inventing a scene-40 resource, or suppressing the missing-scene branch.
2. Broad requester rendering, combat, or replacing the renderer.
3. Assuming source-consistent scene selection means every animation, query, or geometry helper is recovered; split independent failure families.

## Evidence And Starting Point

Task 04 identifies the missing resource as scene id 40 (`mtorc4`): table `0x62e450 + 40*4` is zero and archive offset `0x650fa0 + 40*4` is -1. The message now receives valid strings and a live three-word list. Its former ASan stack-use-after-return is resolved, but at Task 04 completion gated SDL/ASan scene waits still expired with scene slot 40. The error requester also retains unrelated rendering/dispatch limitations; reaching it is not gameplay success.

The prior diagnostic packet records Joe `0xaa6bd8`, action 384 at `0xac263c`, live coordinates `-11792,-16256,-8160`, and home `12800,256,-3584`. Earlier query tracing returned height -16256; that was a calling-convention proof, not height/collision fidelity. Follow `FUN_004495e0/FUN_00449680`, the actual writers to actor `+0x84..+0x88`, and `FUN_004211c8 → FUN_0044c224 → E2R_ActivateSelectedSceneRecord` according to the first divergence.

A watch on actor X installed only at the first `FUN_0042b5fc` call did not fire before the scene-40 packet (`/tmp/e2-scene-drift-watch.log`). Start earlier; this late watch does not identify the writer or prove no coordinate corruption. Logging and GDB pauses affect whether automation catches transient scene-175 readiness. Inspect the actual packet's scene slot, not its filename.

The user’s subsequent manual screenshot matches the gate-off scene-175 static capture, and its log reports scene pointer `0x67da4c`. This completes Step 07’s final-image comparison; do not equate that manual result with the gated scene-40 failure.

## Recovery Evidence

An X watch installed at the action-384 loader entry catches `FUN_0042b880` event type `0x16` writing Joe X from 12800 to -11792. The event contains `0xd1f0,0x0a0c,0xe020`; the coordinate copy matches original `0x42bb4b..0x42bb82`. The action data reaching this interpreter is wrong: action 384 in `Files/ECSTATIC` at offset 9790200 has keyframes at 0, `0x8000`, and `0xc100`, with event types 3/4/14, and no type-0x16 coordinate event. Use the 33075606-byte game archive, not the smaller `Code/ECSTATIC.FAN`.

The first allocator divergence is `FUN_00453754`. Original `0x453762/0x45378b` scans flags at mapped `0x7c872a + slot_offset`, inside the 15-byte keyframe pool starting at `0x7c871c` (60000 bytes). Generated C instead scans host globals `DAT_007c872a` and `(&DAT_007c8739)[iVar2]`, then clears a different, mapped slot. Four successive legacy allocations all return `0x7c8758`; the corrected scan returns `0x7c871c`, `0x7c872b`, `0x7c873a`, `0x7c8749`. Shared keyframe storage explains why action 384 and scene children acquire the same key head and unrelated events overwrite each other.

The three flag reads are normalized in C and mirrored through checked, function-scoped generator replacements. The correction shares **`E2R_ACTION_INDEX_PROBE=1`** while its newly reachable scene-pose path is unrecovered. Gate-off deliberately retains the legacy allocator for the current static baseline; this is a temporary compromise, not correct allocation semantics. Pool exhaustion/reclamation remains unverified.

With distinct keys, gated SDL/GDB and ASan now fail earlier during `FUN_004523f8` scene activation: `FUN_00426124` dereferences its uninitialized actor input (zero, read at `0x1e`). Original `0x452553..0x452555` passes the table-resolved actor in EAX. [Task 06](task-06-recover-scene-activation-pose-inputs.md) owns this separate failure family. Task 05 remains active: unique allocations are proven, but a correct final scene/position and full gated route are not.

The original Task 05 cue was a read-only X/Z inset. On 2026-09-15, Task 07 replaced it with camera-projected ground crosses and uprights. Default Joe is behind camera 175; no enemy instances or source-consistent pedestal positions are established. The old panel hashes and rectangle below are historical verification only.

## Acceptance Criteria

1. Record the first divergent coordinate or scene-descriptor operation and original-source evidence for the repair.
2. The resulting scene choice and actor position have source support; missing-scene errors are not bypassed.
3. Gated debug/ASan reach a bounded capture without sanitizer faults or scene-readiness timeout; record any independent next failure explicitly.
4. Generator syntax/parity, all three builds, the default wrapper and arrow matrix pass. Reassess Task 01 before advancing to Joe geometry.

## Verification

Generator syntax, in-place regeneration and all four scratch artifacts match (`/tmp/e2-generator-audit-ptaec8gy`). Three builds, the default debug/ASan wrapper and all eight arrow rows pass. Final default SDL and cue-enabled captures both exit 0 in scene 175, with Joe alone at `12800,256,-3584`. The indexed surface retains hash `321e33d6`; default SDL present/window retain `914159a1` / `5cf799a1`. Cue-enabled RGB differences are confined to the panel rectangle `(396,10)..(630,206)` on the 640×480 present surface, with identical game-surface pixels. Final artifacts: `/tmp/e2-step05-final-{default,cues}-state.txt` and `/tmp/e2-step05-final-cues.png`.

Headless gate-off ASan scene-175 waits exit 5 in scene 87; these are failed readiness probes, separate from the passing canonical-control wrapper. A cue-enabled canonical-control rerun exits 0, but headless mode never presents and therefore does not emit a visibility packet. Do not claim that run exercised the snapshot or SDL overlay. Gated ASan exits 1 at the scene-pose read, as described above.

A separate focused ASan/GDB call at the pose-entry breakpoint exercises `E2R_GetActorCues` directly and exits 0: scene 1073, one Joe actor at `12800,256,-3584`, origin `12800,-3584`, no address-sanitizer error. This validates the snapshot at that stop, not full SDL/ASan rendering. Evidence: `/tmp/e2-cue-snapshot-asan-final.log`; leak detection was disabled for the ptrace probe only.

Use the Task 04 gated commands with a fresh `/tmp` prefix and a watchpoint started before the first post-intro motion/selection update. Preserve a no-input position/scene timeline and compare original call-site registers and packed record offsets. Keep action indexing opt-in until the step's remaining criteria pass.

## Current Follow-Up — 2026-09-15

The pose-input crash described above is historical: Task 06 now supplies the actor and explicit destinations. Camera/math and matrix-destination recovery plus Task 08 packed event metadata move gated SDL into a polygon-input crash in `FUN_00431a7c`; gated headless ASan times out in camera 1073. Resume Task 02 geometry inputs before Task 05/01 final placement/action validation. The new cue projection does not establish living actors or correct movement. Default isolated Debug/ASan regressions pass; the new manual F5 check remains pending. See the [2026-09-15 journal](../../../../../journal/entries/actor-cues-and-projection-2026-09-15.md).

## 2026-09-21 Follow-Up

Task 02 has passed the polygon reference-pointer failure, and Task 10 subsequently recovered the flat-lighting inputs. The next minimally interrupted gated SDL stop is in framebuffer copying at `FUN_00418514`, owned by [Task 11](task-11-recover-dirty-rectangle-copy-inputs.md). Gated SDL ASan still times out in camera 1073. Default regressions pass; placement and living actors remain unproven. See the [lighting evidence](../../../../../journal/entries/polygon-lighting-2026-09-21.md).

## Review State

1. Planning state: first corrupt event and allocator address mismatch identified
2. Implementation state: gated allocator repair implemented; final scene validation incomplete
3. Notes: Task 02 geometry recovery now precedes Task 05/01 full-route validation. Joe geometry and child activation remain pending.

## Change Log

### 2026-09-14

1. Split the unresolved scene-selection failure from the completed missing-scene message-input repair.

2. Traced the corrupt event to shared keyframe allocation, gated the original-address repair, and split newly exposed scene-pose inputs into Task 06. Added optional host actor cues with explicit absent-enemy status.
