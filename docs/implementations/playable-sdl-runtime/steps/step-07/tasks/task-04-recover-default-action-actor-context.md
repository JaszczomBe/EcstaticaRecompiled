# Recover Default-Action Actor Context

Status: completed
Parent Step: [Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Recover the actor input to `FUN_0042b0f4` reached after natural intro completion, then reverify the baseline wrapper.

## Scope

1. Trace the default-action call from `FUN_00427584` and recover the original EAX actor input and ownership across helpers.
2. Mirror the narrow repair in `GenerateRecon.js`, preserving generated-file parity.
3. Rerun the long-delay ASan probe and Task 02 regression checks; split any further independent failure.

## Out Of Scope

1. Action-384 indexing or broad geometry/scene-child recovery (Step 08).
2. Shortening the 30-second delay, weakening assertions, or adding pointer guards in place of recovering actor ownership.
3. Unrelated transform/animation helper families.

## Implementation Notes

Task 03 repaired `FUN_00423858` recursive actor arguments. A watchpoint had proven it wrote `0x8000` into Joe's `+0x12a` queued-action pointer by recursing into Joe `+0x128`. After the repair, GDB shows both queued-action fields zero and `FUN_00427584` reaches its default-action helper with `local_6c=0xaa6bd8` and `iVar17=0`.

The isolated ASan probe and full wrapper now crash in `FUN_0042b0f4` from `FUN_00427584` (reconstructed caller line 22280 at discovery). ASan stops at line 23264; GDB can stop later at line 23309 because the uninitialized `in_EAX` varies. In GDB, `E2R_actor_calc_context=0`, `in_EAX=-15512`, and Joe's `+0x126`/`+0x12a` both remain zero.

Original `0x429d52` loads EAX from the actor local before the call at `0x429d55`; sibling calls at `0x427ad9` and `0x429ed5` also receive actor EAX. The callee saves EAX into EBX at `0x42b0f9`. Reconstructed `FUN_0042b0f4(void)` only initializes `in_EAX` when the global fallback context is nonzero. Audit its callers and nested helper expectations before selecting an explicit signature or bounded context restoration. Do not assume the entry-input repair also recovers child transforms.


## Result

The three `FUN_00427584` calls now save `E2R_actor_calc_context`, set it to `local_6c`, call `FUN_0042b0f4`, and restore the saved owner. Original calls at `0x427ad9`, `0x429d55`, and `0x429ed5` all pass this actor in EAX. This bounded bridge uses the existing callee context mechanism; other callers and transform helpers were not rewritten.

GDB at the default-action call shows actor/context `0xaa6bd8`, saved context zero, a successful return, and restoration to zero. The probe then reaches a separate lost-input failure in `FUN_0042ae80 -> FUN_0042b338`; [Task 05](task-05-recover-natural-action-advance-inputs.md) owns it. The complete wrapper still fails ASan before its 30-second key delay.

Generator syntax, scratch/in-place parity for all four outputs, three builds, all 8 arrow rows, debug wrapper, and the default SDL packet pass. Selected/present/window hashes remain `321e33d6` / `914159a1` / `5cf799a1`. Manual F5 was not rerun. See the runtime journal for commands and the GDB proof.

## Acceptance Criteria

1. Original-code evidence establishes actor input and helper ownership for the reached call path.
2. The 30-second-delay ASan probe reaches Space/Up and required state/surfaces without sanitizer errors, or any newly exposed independent failure is split with evidence and baseline acceptance remains open.
3. Generator parity, three builds, all 8 arrow rows, and default SDL scene packet are checked; the complete wrapper must pass before Tasks 02/03 and Step 07 close.
4. Record the manual SDL F5 visual check separately; dummy SDL captures do not establish manual playability.

## Verification

```sh
env -u DISPLAY E2R_STARTUP_LOGO_DELAY_MS=0 timeout 150 build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-default-action-asan space,up 30 10000 60 1
```

Follow [Task 02](task-02-repair-canonical-control-regressions.md) for wrapper, matrix, and SDL commands. See the [runtime journal](../../../../../journal/entries/runtime-crash-fixes.md) for watchpoint and disassembly evidence.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: Scoped caller repair verified; subsequent action-advance failure split into Task 05. Tasks 02/03 remain deferred and Step 07 remains open.

## Change Log

### 2026-09-14

1. Split the missing default-action actor context exposed after Task 03's recursive-pointer repair.

2. Restored and verified actor context at all three source-backed caller sites; split the later action-advance input failure into Task 05.
