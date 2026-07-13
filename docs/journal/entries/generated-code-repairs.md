# Generated Code Repairs

## Purpose

Record transformations in `E2Recomp/tools/GenerateRecon.js` that preserve manual fixes when reconstructed C is regenerated.

## Current Groups

- Lost register/output pointer repairs: replace decompiler `extraout_*` temporaries with explicit parameters or fixed legacy addresses.
- Legacy address normalization: convert `&DAT_006372xx` and similar symbolic arithmetic to fixed mapped addresses when the original code expected absolute pointers.
- CRT/Win32 startup bypasses: no-op or redirect Windows CRT thunks that do not map cleanly to the Linux host runtime.
- Runtime stabilizers: guarded pointer writes and narrow shims such as startup `Sleep(5)` pacing.

## Recent Entries

### 2026-07-13 - Main Loop Entry Repairs

1. Added generated top-of-file helpers for native math tables, read-only stream loading, stream cleanup, descriptor reads, and local descriptor flags.
2. Preserved startup allocation count arguments in `FUN_00410a48`, including the 2-byte table allocation for `_DAT_006366a0`.
3. Replaced fragile generated startup table initialization in `FUN_00414f40` with a native initializer and linked Linux builds with `m`.
4. Recovered raw-image and palette/title file reads by preserving descriptors and reading exact byte counts through `E2R_ReadOpenFileBytes`.
5. Redirected `FUN_0045eb05` and `FUN_0045ec6c` through the native read-only stream adapter for startup data files.
6. Recovered `shadow.dat` and `shademap.dat` loading paths, including the native `FUN_0041ce88` shademap table loader.
7. Fixed additional lost-register/fixed-address startup writes in `FUN_0041ccf0`, `FUN_004604e6`, `FUN_00460803`, `FUN_00460844`, `FUN_00460899`, `FUN_0045e8e6`, and the `FUN_0044c71c` object-array clear.

### 2026-07-13

1. Added the generated string symbol for `s_Can_t_load_title_picture_00471320` and mirrored the `FUN_00414e68` lost-`EAX` message pointer repair.
2. Preserved `FUN_00414998` filename input across `FUN_0043ac60` so startup logo opens use the original `EAX` filename flow.
3. Recovered startup logo filename symbols for `gbnklogo.raw`, `psyglogo.raw`, and `aasglogo.raw`.
4. Replaced the split `E_CONFIG` stack filename artifact with one contiguous 9-byte buffer.
5. Recovered file descriptor registration, stream-state, and close bookkeeping around `FUN_0045e5b8`, `FUN_004603d1`, `FUN_00460803`, `FUN_00460899`, and `FUN_004608e8`.
6. Recovered startup title/blit artifacts for `_DAT_006366c0`, `FUN_00418a04`, and `FUN_00417b20`.

Use the generated code repair template in [journal.template.md](../../templates/journal.template.md) for new entries.
