# Recover Scene-Activation Pose Inputs

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-21

## Goal

Recover actor and output ownership in scene activation's initial-pose branch so the corrected keyframe pool can reach post-intro scene-selection validation.

## Scope

1. Recover the actor input to `FUN_00426124` and the corresponding `FUN_00426010` branch from original call sites.
2. Preserve the caller's saved actor state and explicit destinations for directly adjacent pose initialization. Audit nested helper context only where this branch requires it.
3. Rerun gated debug/ASan scene readiness, Task 05 position/event tracing, and Task 01 action advancement.

## Out Of Scope

1. Forcing scene 175, bypassing pose restoration, adding broad pointer guards, or enabling action indexing by default.
2. Full geometry/combat/rendering recovery; split independent next failures.
3. Treating the host actor cues as evidence that game geometry or enemies render.

## Evidence And Starting Point

Task 05 fixes keyframe flag reads under `E2R_ACTION_INDEX_PROBE=1`. Four allocations now have distinct 15-byte slots. The corrected keys expose `FUN_004523f8 → FUN_00426124`; SDL/GDB reports `in_EAX=0`, and ASan reports a read at `0x1e`. This happens during scene activation before the former action-384/scene-40 endpoint, so the earlier missing-scene timeout is no longer the current gated failure.

Original `0x4524f1..0x4524f4` resolves ESI from the actor table; `0x452553..0x452555` passes it in EAX to `0x426124`, and the alternate branch does the same for `0x426010` at `0x45255c..0x45255e`. The current caller already holds this actor as `psVar4`, but both helpers retain hidden-register artifacts. Original `0x452540..0x45254c` saves actor `+0x122` in DX before the call and restores it at `0x45256b`; generated `extraout_DX` is not a recovered return value. Original subsequent destinations are actor `+0x90` for the six-byte clear and `+0xc6` for `0x422330`. Confirm helper semantics and context preservation before editing.

## 2026-09-15 Result

Both helpers now accept the actor explicitly and restore entry context around node helpers. Activation preserves actor `+0x122`, clears the actual `+0x90` vector and initializes the actual `+0xc6` matrix. The other `FUN_00426010` callers now supply the actor too. Original `0x420c2c` resolves the actor from the table; scene-transition code already holds its actor locally. The adjacent root-matrix simple branch now targets actor `+6`, as original `0x4210b8..0x421101` requires, preventing scene child-head corruption.

Gated SDL passes the former zero-actor read. Subsequent event metadata and node-matrix recovery now reach `FUN_00431a7c` with an invalid polygon input; Joe's live position has changed to `9184,3328,-17416` at that stop. This is not proof of correct placement. Gated headless ASan exits 5 waiting in camera 1073, without a sanitizer report. Default isolated Debug/ASan wrapper, four builds and generator parity pass; new manual F5 verification remains pending. See the [journal](../../../../../journal/entries/actor-cues-and-projection-2026-09-15.md). Task 02 owns the next source failure.

## Acceptance Criteria

1. Every changed input/output has original executable evidence, including saved state across pose helpers.
2. The gated route passes the current pose entry without invalid reads/writes; record the next independent failure if full scene readiness remains incomplete.
3. Reassess Tasks 05 and 01 with actual scene slots, positions, key/event ownership, and action progress; a nonblank static packet is insufficient.
4. Generator syntax and four-artifact parity, all three builds, default debug/ASan wrapper, arrow matrix, and default SDL capture pass. Recheck manual visuals after runtime behavior changes; the prior static-baseline comparison is complete.

## Verification

```sh
objdump -d -Mintel --start-address=0x4524d0 --stop-address=0x4525e6 /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
objdump -d -Mintel --start-address=0x426124 --stop-address=0x426268 /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
env -u DISPLAY E2R_ACTION_INDEX_PROBE=1 timeout 140 build/Debug/clang21-i386-x11-asan/e2recomp --auto-scene175-visibility /tmp/e2-scene-pose-asan 120 7000
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 timeout 140 gdb -q -batch -ex 'set pagination off' -ex run -ex 'bt 8' -ex 'frame 0' -ex 'info locals' --args build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-scene-pose-sdl 120 7000
```

GDB can exit zero after catching SIGSEGV; inspect the inferior stop reason and actual capture, not just the shell status. Current evidence: `/tmp/e2-keyframes-probe.log` and `/tmp/e2-step05-gated-asan.log`.

## 2026-09-21 Follow-Up

Task 02 has passed the polygon reference-pointer failure, and Task 10 subsequently recovered the flat-lighting inputs. The next minimally interrupted gated SDL stop is in framebuffer copying at `FUN_00418514`, owned by [Task 11](task-11-recover-dirty-rectangle-copy-inputs.md). Gated SDL ASan still times out in camera 1073. Default regressions pass; placement and living actors remain unproven. See the [lighting evidence](../../../../../journal/entries/polygon-lighting-2026-09-21.md).

## Review State

1. Planning state: bounded scene-activation pose-input failure split from Task 05
2. Implementation state: implemented; full-route/manual verification incomplete
3. Notes: Pose entry now passes in gated SDL. Task 02 geometry inputs precede Task 05/01 full-route validation; action indexing remains opt-in.

## Change Log

### 2026-09-14

1. Recorded the first scene-pose crash exposed by distinct keyframe allocation and its original register/destination inputs.
