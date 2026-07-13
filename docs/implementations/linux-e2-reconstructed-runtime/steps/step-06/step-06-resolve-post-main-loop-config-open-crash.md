# Resolve Post Main Loop Config Open Crash

Status: active
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-13

## Goal

Continue past the first post-main-loop-entry crash by recovering the `"e_config"` file-open path around `FUN_0046055c`, `FUN_0045e5b8`, and `FUN_0045e594`.

## Why This Step Exists

Step 5 proved that startup now reaches `FUN_00410a48 -> thunk_FUN_004620db`. Continuing execution exposes a new frontier: an indirect jump to `0xffffffff` through `FUN_0046055c` while `FUN_0041007c` opens `"e_config"`. This step turns that frontier into the next stable runtime edge before broader loop, rendering, or input work begins.

## Scope

1. Recover the original file/CRT callback or descriptor intent that leads `FUN_0046055c` to call `0xffffffff`.
2. Fix only the narrow post-main-loop-entry blocker needed to continue past the `"e_config"` open.
3. Mirror generated C repairs in `E2Recomp/tools/GenerateRecon.js`.
4. Record the next crash frontier in the runtime journal.

## Out Of Scope

1. Full CRT file API reconstruction.
2. Full config-file semantics beyond the current open/read path.
3. Rendering, audio, input, or gameplay correctness after the next frontier is reached.

## Usage Budget

Respect the active implementation budget from the parent implementation: no more than 5% weekly usage burn per day unless the user explicitly approves continuing.

## Temporary Sacrifices

1. Sacrifice: a narrow native shim may be used for the specific proven `"e_config"` open path if the callback table remains under-recovered.
2. Why accepted now: the milestone needs a stable loop frontier before broader rendering or input work can be meaningfully tested.
3. Removal trigger: replace the shim when Ghidra evidence recovers the original callback table and descriptor lifecycle.

## Acceptance Criteria

1. Debug GDB no longer crashes at `EIP=0xffffffff` from `FUN_0046055c` during the `"e_config"` open.
2. Execution advances to a new documented post-config crash frontier or proves several main-loop-adjacent calls beyond the config open.
3. Debug and ASan builds compile.
4. Any reconstructed C hand fix is mirrored in `E2Recomp/tools/GenerateRecon.js`.

## Verification

1. `cmake --build --preset linux-clang32-debug`
2. `cmake --build build/linux-clang32-asan`
3. GDB run from `build/linux-clang32-debug` with breakpoints on `FUN_0046055c`, `FUN_0045e5b8`, `FUN_0045e594`, and the next exposed frontier.

## Notes

Known starting evidence from step 5:

```text
Program received signal SIGSEGV, Segmentation fault.
0xffffffff in ?? ()
#0 0xffffffff
#1 FUN_0046055c(param_1=4149332857, param_2=512)
#2 FUN_0045e5b8(param_1=0, param_2=512, param_3="e_config", param_4=512, ...)
#3 FUN_0045e594(...)
#4 FUN_0041007c
```

The next investigation should compare the original disassembly for `FUN_0046055c` and its callers against the generated code before adding another defensive no-op.

## Change Log

### 2026-07-13

1. Created step after completing main-loop entry milestone.
