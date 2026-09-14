# Recover Natural Action-Advance Inputs

Status: completed
Parent Step: [Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Recover the action-slot, actor, and advance inputs lost at the natural-intro call to `FUN_0042ae80`, then reverify the baseline.

## Scope

1. Recover original EAX/EDX/EBX ownership at `FUN_00427584 -> FUN_0042ae80` and preserve the slot across helpers.
2. Mirror the focused repair in the generator and check natural completion and the existing skip route.
3. Split any further independent failure; keep full baseline acceptance open until the wrapper passes.

## Out Of Scope

1. Enabling action indexing by default, repairing action-384 parsing, or claiming visible actor geometry.
2. Broad interpolation/transform recovery before evidence shows it is needed for this path.
3. Skipping the action-advance call or guarding a guessed pointer to evade the failure.

## Evidence And Next Action

Task 04 now supplies Joe to `FUN_0042b0f4` and restores the enclosing context. GDB proves that helper returns. The next call at reconstructed line 22374 (at discovery) passes `uVar25` and the actor to `FUN_0042ae80`, whose `in_EAX` and `unaff_EBX` remain uninitialized.

Original `0x429f68–0x429f76` loads EAX = actor + `0xa6`, EDX = actor, and EBX = the local at `[ebp+0x32]`. Callee `0x42ae87–0x42ae8b` preserves all three; `0x42ae8d` tests the slot's action pointer. Recover the advance local's producer before choosing the signature; do not infer its value from the stale first reconstructed argument.

With indexing disabled, the isolated ASan probe and wrapper read `0x72` in `FUN_0042b338` at line 23425. GDB shows `FUN_0042ae80.in_EAX=0xffffb040` (stack storage), `unaff_EBX=-65469`, and downstream `puVar1=0x72`. Caller actor is `0xaa6bd8`, whose action pointer is zero. The original empty-slot path should return through `0x42afee`; the reconstruction instead interprets unrelated stack storage as an action slot.

This overlaps the helper owned by [Step 08 Task 01](../../step-08/tasks/task-01-recover-action-context.md). Reuse any recovered calling convention there, but keep the natural empty-action proof distinct from the gated action-384 parser/advance proof. Step 08's loaded-action path remains unverified.

## Result

Original `0x42759a` saves incoming EDX to `[ebp+0x32]`, reconstructed as `local_64 = param_2`; the original local has no intervening writes. The sole reconstructed caller now passes `(int *)(local_6c + 0x53)`, the actor, and `local_64` to an explicit three-argument `FUN_0042ae80` signature. Entry initializes the slot and advance locals. Generator checks preserve the call, entry, signature, and header prototype.

GDB proves `action_slot=0xaa6c7e`, actor `0xaa6bd8`, advance zero, and `*action_slot=0`; the helper returns through its original empty-slot behavior. No nested helper is entered on this route. The loaded-action branch still has unrecovered ECX/helper ownership and remains Step 08 work; this result does not establish full action advancement.

All three builds, all four generator comparisons, all 8 arrow rows, debug wrapper, and default SDL packet pass. Image hashes remain `321e33d6` / `914159a1` / `5cf799a1`. The long-delay ASan probe and wrapper now reach a separate motion-query global-buffer-overflow in `FUN_00448a48`; [Task 06](task-06-recover-natural-motion-query.md) owns it. Manual F5 was not rerun.

## Acceptance Criteria

1. Original-code evidence establishes all three inputs and preservation across relevant helpers.
2. The long-delay ASan probe reaches Space/Up and expected state/surfaces, or a new independent failure is split and baseline acceptance remains open.
3. Generator parity, three builds, all 8 arrow rows, and the default SDL packet are checked. Tasks 02/03 and Step 07 close only after the full wrapper passes.
4. Manual SDL F5 is recorded separately from dummy SDL state/surface checks.

## Verification

```sh
env -u DISPLAY E2R_STARTUP_LOGO_DELAY_MS=0 timeout 150 build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-natural-advance-asan space,up 30 10000 60 1
```

Use [Task 02](task-02-repair-canonical-control-regressions.md) for wrapper/matrix/SDL commands and the [runtime journal](../../../../../journal/entries/runtime-crash-fixes.md) for Task 04's context proof.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: Three entry inputs and the empty-action path are verified. Task 06 owns the later motion-query failure; Tasks 02/03 and Step 07 remain open.

## Change Log

### 2026-09-14

1. Split the natural action-advance input failure exposed after the default-action context repair.

2. Recovered explicit slot/actor/advance inputs and verified the original empty-slot return; split the subsequent motion-query failure into Task 06.
