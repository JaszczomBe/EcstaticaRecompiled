# Recover Natural Intro Action Handoff

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
<!-- /docs-tree:parent -->

Status: completed
Parent Step: [Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Recover the invalid queued-action handoff reached before the long-delay ASan probe injects Space, so the baseline wrapper can finish.

## Scope

1. Trace the natural first-intro completion into scene pointer `0x67d0ac` (slot 87).
2. Recover the producer/type/lifetime of the action candidate used by `FUN_00427584`.
3. Mirror the narrow repair in the generator and rerun Task 02 validation.

## Out Of Scope

1. Scene-175 action 384 indexing, living-player geometry, or scene-backed child rendering (Step 08).
2. Full intro animation fidelity or shortening the ASan delay to evade natural completion.
3. Generic pointer guards that discard the candidate without recovering its intended meaning.

## Implementation Notes

Task 01 now reproduces all four generated artifacts exactly. Task 02 changes both wrapper sequences to `space,up` and asserts VK_UP delivery. Debug passes, but ASan fails before its first scheduled key (30 seconds). Both the wrapper run and a repeat without `DISPLAY` crash at the same read, ruling out live X11 keyboard events as the cause of this observation. The 6-second arrow matrix and default SDL scene-175 skip route pass.

Last useful proof: horse action `0x93a329` reaches progress 494/duration 495, completes through `FUN_0042ad60`/`FUN_0042b004`, and requester logging reports `scene=0x67d0ac current=0xaa6bd8`. ASan then reports a read of `0x8002` in `FUN_00427584` at `local_6c[0x55] = *(short *)(iVar17 + 2)` (line 20602 at discovery). This was the discovery failure; the upstream writer is now established below.

The producer is now proven: a GDB watchpoint on Joe `+0x12a` (`0xaa6d02`) catches `FUN_00423858` called with `0xaa6d00` (Joe `+0x128`). Its actor-flag write at `+3` turns the queued pointer from zero into `0x8000`. The caller used a coordinate-derived `uVar2` instead of the child actor pointer. Original `0x423c0b`/`0x423cae` select the child in EAX; the special branch at `0x424124–0x424144` selects the child, its first descendant, then its second descendant.

Five reconstructed lines now preserve those actor targets, mirrored by three checked generator replacements. No candidate guard or consumer change was added. Scratch and in-place generation preserve the exact repair; all three builds pass. GDB at the subsequent failure shows both queued-action fields zero.

Tasks 04–06 subsequently repaired default-action context, action-advance inputs, and motion-query ownership. The long-delay ASan probe and full debug/ASan wrapper now pass, along with all 8 arrow rows and the default SDL static packet. This task's source and automated acceptance criteria are met. Task 02 retains the required manual SDL F5 check. Action indexing remains disabled.

## Acceptance Criteria

1. Original-code evidence establishes the candidate's producer, representation, and ownership across the natural handoff.
2. The isolated 30-second-delay ASan probe survives, dispatches Space/Up, and supplies the expected state/surface evidence without sanitizer errors.
3. Task 02's complete wrapper passes debug and ASan; all 8 arrow rows and the default SDL scene packet remain valid.
4. Generator parity, the three builds, and `git diff --check` pass; any new independent crash is recorded separately.

## Verification

From the repository root:

```sh
env -u DISPLAY E2R_STARTUP_LOGO_DELAY_MS=0 timeout 150 build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-natural-intro-asan space,up 30 10000 60 1
```

For inspection, run the same arguments under batch GDB with a timeout and collect the candidate/actor state before the failing read. After a source-backed repair, follow [Task 02](task-02-repair-canonical-control-regressions.md) for wrapper, matrix, and SDL verification. See the [runtime journal](../../../../../journal/entries/runtime-crash-fixes.md) for the discovery stack and regression impact.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: Recursive-pointer repair and long-delay automated acceptance pass after Tasks 04–06. Task 02 and Step 07 await manual SDL F5 verification.

## Change Log

### 2026-09-14

1. Split the natural-intro ASan crash exposed when the corrected wrapper advanced past its debug numpad failure.

2. Recovered recursive actor pointers from original EAX ownership; verified queued fields remain zero and split the next default-action context failure into Task 04.
