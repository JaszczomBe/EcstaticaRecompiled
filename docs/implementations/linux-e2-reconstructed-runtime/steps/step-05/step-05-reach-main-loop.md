# Reach Main Loop

Status: completed
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-13

## Goal

Advance the reconstructed runtime to the main loop without crashing.

## Scope

1. Continue from title/menu logic.
2. Fix only blockers needed to enter the main loop.
3. Record the first verified main-loop call path.

## Out Of Scope

1. Full gameplay correctness.
2. Rendering/audio accuracy beyond what is needed to enter the loop.
3. Performance tuning.

## Acceptance Criteria

1. GDB/runtime evidence shows the main loop reached. Completed: `thunk_FUN_004620db` hit from `FUN_00410a48`.
2. The main-loop entry point is documented. Completed below.
3. Debug and ASan builds compile. Completed.

## Verification

1. Build debug and ASan targets.
2. Run `./e2recomp --run-recon`.
3. Capture a GDB backtrace or log proving main-loop entry.

## Result

Completed on 2026-07-13. A debug GDB run hit the suspected main-loop entry thunk:

```text
Breakpoint 5, thunk_FUN_004620db(param_1=6517398, param_2=1449320296)
E2Recomp_recon.c:53799

#0 thunk_FUN_004620db
#1 FUN_00410a48 at E2Recomp_recon.c:4752
#2 FUN_0041007c at E2Recomp_recon.c:242
#3 E2R_WinMainThunk
#4 main
```

The startup blockers fixed for this step were:

1. Allocation call sites in `FUN_00410a48` that lost their original count arguments.
2. Title, palette, shadow, and shademap stream/file loading paths that lost filename or descriptor state.
3. Startup table initialization paths that still used fragile decompiler pseudo-registers or symbolic fixed-address writes.

Verification:

```text
cmake --build --preset linux-clang32-debug
cmake -S . -B build/linux-clang32-asan -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=clang '-DCMAKE_C_FLAGS=-m32 -fsanitize=address -fno-omit-frame-pointer' '-DCMAKE_EXE_LINKER_FLAGS=-m32 -fsanitize=address' -DECSTATICA2_DATA_DIR=/home/rgrabowski/Games/Ecstatica2
cmake --build build/linux-clang32-asan
```

Next frontier: after continuing past `thunk_FUN_004620db`, the debug run later crashes at `EIP=0xffffffff` through `FUN_0046055c`, called by `FUN_0045e5b8 -> FUN_0045e594` while opening `"e_config"` from `FUN_0041007c`.
