# Recover Natural Motion Query

Status: completed
Parent Step: [Restore Reproducible Runtime Baseline](../step-07-restore-reproducible-runtime-baseline.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Recover the first invalid ownership/table access in the natural-intro motion-query chain after action selection.

## Scope

1. Trace `FUN_00427584 -> FUN_004495e0 -> FUN_00449680 -> FUN_00448a48` against original code, including actor/coordinate inputs and the optional query output pointer.
2. Establish the intended flag-table base, element width, and signed index before repairing the observed read.
3. Mirror one focused source repair, then rerun the long-delay ASan probe and baseline checks; split further independent failures.

## Out Of Scope

1. Suppressing ASan, accepting a guessed output pointer, or clamping a negative index without original-code evidence.
2. Full motion/collision fidelity, loaded action-384 parsing, or visible actor geometry.
3. Treating a debugger exit code as a runtime pass.

## Evidence And Next Action

Task 05 restores the natural action-advance call. GDB observes actor `0xaa6bd8`, empty slot `0xaa6c7e`, advance zero, and a normal return. The next call to `FUN_004495e0` reaches a global-buffer-overflow in `FUN_00448a48` at reconstructed line 42957 (at discovery): `(&DAT_00636624)[iVar4 * 2]`, with `iVar4=-1` and query result `iVar3=42278`.

The regular ASan report aborts with a nested error before a useful stack. Break on `__asan_report_load4` under GDB to capture the first read. The observed `unaff_EBX=0xffffb038` is a stack-shaped output pointer and the caller unwind is already damaged; trace that earlier write before assuming only the table read is wrong.

Original `0x429fde` loads actor EAX before calling `0x4495e0`. Reconstructed `FUN_004495e0(void)` and `FUN_00449680` still use uninitialized EAX/ECX placeholders. Original `FUN_00448a48` saves optional output EBX in EBP at `0x448a55`, writes the signed result at `0x448b62`, and tests a **byte at fixed address `0x636624 + index*2`** at `0x448b65`. Its signed shift at `0x448b5b` is original. The reconstruction instead indexes a host `uintptr_t` global. Recover ownership and address representation; do not assume `-1` should be rejected merely because it triggers ASan on that generated expression.

## Result

GDB caught the optional-output write replacing `0xffffc368` with `0xffffffff` at `0xffffb038`, damaging the caller frame before the ASan read. Original `0x449691` clears EBX for this call. All eleven direct query callers were inspected: ten pass null; `0x449529` supplies the local corresponding to `local_58`.

`FUN_00448a48` now has an explicit optional output parameter, and its flag lookup reads the original fixed-address byte. `FUN_004495e0` receives and retains its actor; `FUN_00449680` retains actor ECX ownership, queries position `+0x84`, and uses a contiguous three-short candidate buffer. The final position copy writes `actor + 0x64`, matching `0x449671`. The generator mirrors the repair through 19 unique anchors and two prototype updates.

Post-repair GDB observes query position `0xaa6c5c` = Joe `0xaa6bd8` + `0x84`, coordinates `12800,256,-3584`, and null actor-filter/output inputs. Query, motion step, and motion wrapper return with an intact caller stack.

The isolated long-delay ASan probe and full debug/ASan wrapper both exit zero with VK_UP, movement state, requester clear, nonblank surface, and no sanitizer error. ASan finishes in scene slot 87 with surface hash `bf4a8e25`; this is separate from the scene-175 skip-route packet. All 8 arrow rows, three builds, all four generator comparisons, and the SDL scene-175 packet pass. Scene-175 selected/present/window hashes remain `321e33d6` / `914159a1` / `5cf799a1`.

These are bounded state/surface proofs. Other query callers retain unrecovered coordinate inputs, nested movement/action helpers remain incomplete, and the observed query height does not establish collision fidelity. Manual SDL F5 survives the pedestal intro, but agreement of its final scene with the packet remains unresolved; Task 02 and Step 07 remain open only for that required check.

## Acceptance Criteria

1. Original-code and debugger evidence identify the first invalid access/producer and support the focused repair.
2. The long-delay ASan probe reaches Space/Up with required evidence, or another independent failure is split while the baseline remains open.
3. Generator parity, three builds, all 8 arrow rows, and the default SDL packet are checked; Tasks 02/03 and Step 07 close only after the full wrapper passes.
4. Manual SDL F5 is recorded separately from dummy SDL captures.

## Verification

```sh
env -u DISPLAY E2R_STARTUP_LOGO_DELAY_MS=0 timeout 150 build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-natural-motion-asan space,up 30 10000 60 1
```

Follow [Task 02](task-02-repair-canonical-control-regressions.md) for wrapper/matrix/SDL commands and the [runtime journal](../../../../../journal/entries/runtime-crash-fixes.md) for the first ASan breakpoint evidence.

## Review State

1. Planning state: discussed
2. Implementation state: completed
3. Notes: Motion-query repair and all automated baseline checks pass. Task 03 closes; Task 02 and Step 07 await the required manual SDL F5 check.

## Manual Follow-Up — 2026-09-14

The user reports that manual SDL F5 reaches the pedestal intro without crashing, then changes to an “unrelated castle rooftops” view after completion. This establishes survival but does not yet establish agreement with the automated packet or correct scene selection. The automated scene-175 capture itself shows a ruined castle interior with red sky, a horned skull above the central doorway, and straw-covered stone platforms. Visual matching and skip timing were requested; do not classify the report as a proven different scene until those observations agree. A 30-second settle capture also retains scene 175 and the same image hashes. Step 07 remains open while the manual view is identified.

## Change Log

### 2026-09-14

1. Split the motion-query failure reached after Task 05 restores the empty-action return.

2. Recovered motion/query ownership and byte-table access; all automated baseline checks now pass.
