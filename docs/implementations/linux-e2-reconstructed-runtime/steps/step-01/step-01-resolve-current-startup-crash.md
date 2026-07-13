# Resolve Current Startup Crash

Status: active
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-13

## Goal

Fix the current `FUN_00414b24 -> FUN_00414e68` startup crash where `FUN_00414e68` dereferences `0x200`.

## Why This Step Exists

The runtime has advanced past several earlier reconstructed-code crashes. The next frontier is a concrete startup crash with a small call path, making it a good single-context step before broader resource/window milestones.

## Scope

1. Current crash path: `FUN_00414b24 -> FUN_00414e68`, dereferencing `0x200`.
2. Ghidra comparison against `/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` for the functions directly needed to explain this crash.
3. GDB confirmation that the `0x200` dereference no longer occurs.
4. Mirroring durable reconstructed C repairs in `GenerateRecon.js`.

## Out Of Scope

1. Fixing the full `FUN_0043b384`/`FUN_0043cac0` cluster unless it is directly required by the current crash.
2. Resource-loading milestone work.
3. Window, graphics, or audio backend work.
4. Reaching the main loop.

## Usage Budget

Hard limit: spend no more than 5% weekly usage burn per day on this step. If that budget is nearly exhausted, stop and hand off with current evidence, attempted commands, and the next recommended action.

## Temporary Sacrifices

1. Sacrifice: keep existing Linux compatibility shims and earlier runtime stabilizers in place while recovering this cluster.
2. Why accepted now: they allow execution to reach the current crash frontier.
3. Removal trigger: Ghidra evidence shows a shim is masking recoverable original behavior.

## Acceptance Criteria

1. The `FUN_00414b24 -> FUN_00414e68` crash no longer dereferences `0x200`.
2. Any recovered calling convention or pointer-intent fix is documented with Ghidra/GDB evidence.
3. Debug and ASan builds compile.
4. The next runtime frontier is recorded in the runtime crash journal.

## Verification

1. Build with `cmake --build --preset linux-clang32-debug`.
2. Build with `cmake --build build/linux-clang32-asan`.
3. Run under GDB with `./e2recomp --run-recon`.
4. Compare relevant original executable functions in Ghidra before finalizing a non-trivial fix.

## Notes

Use `analyzeHeadless` or `ghidra` from PATH. If a tool asks for the install directory, use `/home/rgrabowski/Work/ghidra_12.1.2_PUBLIC`.

## Change Log

### 2026-07-13

1. Created active step.
2. Narrowed step scope to the current startup crash.
