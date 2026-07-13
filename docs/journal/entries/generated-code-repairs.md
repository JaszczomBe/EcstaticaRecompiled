# Generated Code Repairs

## Purpose

Record transformations in `E2Recomp/tools/GenerateRecon.js` that preserve manual fixes when reconstructed C is regenerated.

## Current Groups

- Lost register/output pointer repairs: replace decompiler `extraout_*` temporaries with explicit parameters or fixed legacy addresses.
- Legacy address normalization: convert `&DAT_006372xx` and similar symbolic arithmetic to fixed mapped addresses when the original code expected absolute pointers.
- CRT/Win32 startup bypasses: no-op or redirect Windows CRT thunks that do not map cleanly to the Linux host runtime.
- Runtime stabilizers: guarded pointer writes and narrow shims such as startup `Sleep(5)` pacing.

Use the generated code repair template in [journal.template.md](../../templates/journal.template.md) for new entries.
