# Prove First Resource Load

Status: completed
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-13

## Goal

Reach and verify loading one real Ecstatica II resource file from `/home/rgrabowski/Games/Ecstatica2/`.

## Scope

1. Identify the first file-open/resource-load path reached after startup crash fixes.
2. Confirm the build-tree `Ecstatica2` symlink resolves to the CD data.
3. Record the first successfully opened file path and call stack.

## Out Of Scope

1. Rendering or audio output.
2. Full resource format parsing.
3. Main loop stabilization.

## Acceptance Criteria

1. GDB/log evidence shows at least one real data file opened from the Ecstatica II data directory.
2. Any path or case-sensitivity fix is mirrored in generator/platform code if needed.
3. Journal records the first resource-load evidence.

## Verification

1. Build debug and ASan targets.
2. Run `./e2recomp --run-recon` under GDB or equivalent tracing.
3. Capture the file path and owning reconstructed function.

## Result

First proven resource open: `/home/rgrabowski/Games/Ecstatica2/PSYGLOGO.RAW`, requested as `psyglogo.raw`.

Evidence: GDB breakpoint on `CreateFileA` showed the request from `FUN_00410a48 -> FUN_00414998 -> FUN_0045e594` and a valid returned handle.

Next frontier: `FUN_0045e5b8` now crashes after the successful open by reading `param_4 == 0x200` as a pointer.

## Change Log

### 2026-07-13

1. Recovered first startup logo filename flow into `FUN_00414998`.
2. Added Linux read-only `CreateFileA` path normalization/case-insensitive resolution and startup data-directory entry.
3. Verified first real Ecstatica II data file open.
