# Generated Code Repairs

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Purpose

Record transformations in `E2Recomp/tools/GenerateRecon.js` that preserve manual fixes when reconstructed C is regenerated.

## Current Groups

- Lost register/output pointer repairs: replace decompiler `extraout_*` temporaries with explicit parameters or fixed legacy addresses.
- Legacy address normalization: convert `&DAT_006372xx` and similar symbolic arithmetic to fixed mapped addresses when the original code expected absolute pointers.
- CRT/Win32 startup bypasses: no-op or redirect Windows CRT thunks that do not map cleanly to the Linux host runtime.
- Runtime stabilizers: guarded pointer writes and narrow shims such as startup `Sleep(5)` pacing.

## Recent Entries

### 2026-09-14 - Keyframe Pool Flags Use Mapped Addresses Under The Probe

`FUN_00453754` now reads the original 15-byte pool's flag bytes at `0x7c872a` and `0x7c8739 + iVar2` when `E2R_ACTION_INDEX_PROBE=1`. A function-scoped generator replacement checks two first-flag references and one indexed reference before rewriting them. Original `0x453762/0x45378b` and a four-allocation GDB comparison establish the address mismatch: legacy repeatedly returns `0x7c8758`, corrected returns successive slots from `0x7c871c`. No new sanitizer suppression or generated header/global/name change. Four-artifact scratch parity passed at `/tmp/e2-generator-audit-ptaec8gy`.

The gate-off allocator deliberately retains legacy behavior while corrected keys expose a separate scene-pose actor-input crash in `FUN_00426124`. [Task 05](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-05-recover-post-intro-scene-selection.md) remains active; [Task 06](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-06-recover-scene-activation-pose-inputs.md) is next. Host actor cues and atomic visibility-state publication live outside generated code.

### 2026-09-14 - Missing-Scene Message List And Text

One unique-anchor replacement mirrors the original two-string wrapper's local `[message, scene name, NULL]` list at `FUN_0045233c`. The message uses the executable's original literal because mapped address `0x47563c` is empty in the reconstruction. Shared wrapper callers and signatures are unchanged. All four outputs match scratch generation (`/tmp/e2-generator-audit-hl23_86h`); three builds and default checks pass. Gated ASan's stale-list read is gone, but the scene wait still exits 5; see [Task 04](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-04-recover-missing-scene-message-inputs.md) and the runtime journal.

### 2026-09-14 - Action Loader And Callback Actor Ownership

Mirrored the loader's entry-actor save/restore and the loaded-action slot/owner recovery through function-scoped checked replacements. The child-commit helper has an explicit actor parameter in generated C and the prototype list; child interpolation consumes its existing first parameter. Removed the unused phantom ECX read from the calling loop. All four scratch artifacts match (`/tmp/e2-generator-audit-_707at8m`), and all three builds/default runtime checks pass. Gated validation remains incomplete in [Step 08 Task 01](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-01-recover-action-context.md); see the runtime journal for the separate missing-scene ASan failure.

### 2026-09-14 - Diagnostic Generator Parity Restored

Mirrored the previously committed actor model/exit, action lookup, and rep-parser stop diagnostics through 23 ordered replacements with unique-anchor checks. Removed the intermediate C write/read so a failed diagnostic anchor cannot replace reconstructed output. Scratch and in-place generation now match all four generator artifacts byte-for-byte; reconstructed C behavior is unchanged. `node --check`, default debug, ASan, SDL debug builds, and `git diff --check` pass. [Step 07 Task 01](../../implementations/playable-sdl-runtime/steps/step-07/tasks/task-01-preserve-generator-diagnostics.md) is complete; the wrapper/runtime verification is separate.

### 2026-09-14 - Diagnostic Generator Drift Found (Historical Audit)

Scratch generation at `43ddc8a` matches the header, globals, and rename map but changes reconstructed C by 155 removed/12 added lines, principally actor/action/rep diagnostics. The action-index gate survives generation. See the [audit comparison recipe](runtime-audit-2026-09-14.md) and [Step 07 Task 01](../../implementations/playable-sdl-runtime/steps/step-07/tasks/task-01-preserve-generator-diagnostics.md). No generator repair was made during the documentation pass.

### 2026-07-30 - Front-Buffer Proof Stabilizers

1. Recovered `FUN_00417b20` software-surface copy source and destination indices from the explicit local page values instead of stale hidden registers.
2. Added generated `no_sanitize("address")` annotations to sparse original-global allocator helpers whose fixed-address accesses are valid for the reconstructed address space but look like global overflows to ASan.
3. Converted cleanup marker rewrites for `FUN_004533a4`, `FUN_0045357c`, and `FUN_0045374c` to regex anchors so the regenerated code consistently uses `E2R_cleanup_context` and validates the write span.
4. Restored the full `FUN_00449b4c` local path buffer and replaced fragile `FUN_0044add8` palette-path/file-read calls with explicit bounded string handling and descriptor-stable reads.
5. Recovered actor animation context in `FUN_0042d048` and `FUN_0042b004` from `E2R_actor_calc_context` when generated hidden registers are missing.
6. Published `FUN_0044add8`'s refreshed `0x0061c730` scene palette through `FUN_0041af88` so regenerated raw-view loads update the active SDL palette.

### 2026-07-15 - CDPATH And Native Stream Slow-Path Repairs

1. Recovered the post-config `CDPath` open in `FUN_0041007c` by replacing the lost-register `FUN_0045eb05(extraout_ECX_07, extraout_EDX_02)` call.
2. Changed generated `FUN_0045eb05` to treat a plausible `param_1` as the filename and fall back to `param_2` only for generated artifact call sites.
3. Added native `E2R_STREAM_MAGIC` handling to generated `FUN_0045f38a` so special bytes in read-only stream data do not enter stale-register CRT slow paths.
4. Guarded generated stream read/close shims against impossible pointers before checking the stream magic marker.

### 2026-07-15 - Post-Config Fixed-Address And Header Repairs

1. Normalized generated `&DAT_00684d68` and `&DAT_00684be8` map-table references to fixed legacy addresses so `FUN_0044c71c` does not overwrite adjacent host globals such as `PTR_FUN_0047d39c`.
2. Normalized generated `&DAT_00621330` raw-palette references to fixed legacy palette memory.
3. Preserved the native config-header path by rewriting the `e_config` read to `E2R_ReadOpenFileBytes(..., 0x20)`.
4. Replaced the lost-register `FUN_0045e90e` startup config signature check with `strncmp(acStack_68, s_Ecstatica001_0047006c, 0xc)`.
5. Added `<string.h>` to the generated reconstructed C prefix for the explicit signature comparison.

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
