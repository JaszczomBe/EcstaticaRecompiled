# Generated Code Repairs

## Purpose

Record transformations in `E2Recomp/tools/GenerateRecon.js` that preserve manual fixes when reconstructed C is regenerated.

## Current Groups

- Lost register/output pointer repairs: replace decompiler `extraout_*` temporaries with explicit parameters or fixed legacy addresses.
- Legacy address normalization: convert `&DAT_006372xx` and similar symbolic arithmetic to fixed mapped addresses when the original code expected absolute pointers.
- CRT/Win32 startup bypasses: no-op or redirect Windows CRT thunks that do not map cleanly to the Linux host runtime.
- Runtime stabilizers: guarded pointer writes and narrow shims such as startup `Sleep(5)` pacing.

## Recent Entries

### 2026-07-13

1. Added the generated string symbol for `s_Can_t_load_title_picture_00471320` and mirrored the `FUN_00414e68` lost-`EAX` message pointer repair.
2. Preserved `FUN_00414998` filename input across `FUN_0043ac60` so startup logo opens use the original `EAX` filename flow.
3. Recovered startup logo filename symbols for `gbnklogo.raw`, `psyglogo.raw`, and `aasglogo.raw`.
4. Replaced the split `E_CONFIG` stack filename artifact with one contiguous 9-byte buffer.

Use the generated code repair template in [journal.template.md](../../templates/journal.template.md) for new entries.
