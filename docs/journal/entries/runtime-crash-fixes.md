# Runtime Crash Fixes

Use the runtime crash fix template in [journal.template.md](../../templates/journal.template.md) for new entries.

## 2026-07-16 - Main Loop Heartbeat Sustained After Requester Id Recovery

Area: `FUN_00415d40 -> FUN_0043ce58`, loop-adjacent requester/menu state

Symptom: after the HUD icon and damage-rectangle table repairs, ASan stopped in `FUN_0043cac0` through `FUN_0043ce58 -> FUN_00414e68`, with `FUN_0043cac0` reading through `in_EAX == 0x1`.

Evidence: original disassembly at `00416278..004162b5` stores `5` in `_DAT_00643650`, but then loads requester id `0x27` or `0x28` into `EAX` before calling `0043ce58`. The reconstructed call used `FUN_0043ce58(param_1,5)`, so `FUN_0043ce58` saw the wrong requester id and fell into the original fatal `Bad request number` path at `0043d43b`.

Change: added a narrow requester-id recovery in `FUN_00415d40`, passing `0x27` when `DAT_00479db4` is set and `0x28` otherwise. Restored `FUN_0043ce58`'s lost incoming `EAX` convention by initializing its generated `in_EAX` from `param_1`. Mirrored both changes in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Bounded ASan runs of 30 seconds and 90 seconds both timed out with no sanitizer report.

Next Frontier: step 8 should move from crash stabilization to an inspectable title/menu frame, verifying what the compatibility renderer is actually presenting during the sustained loop.

Regression Risk: `FUN_0043ce58` is a shared requester/menu initializer. Initializing `in_EAX` from `param_1` is the correct recovered convention, but other callers that still pass stale `extraout_*` values may expose additional requester ids that need local call-site recovery.

## 2026-07-16 - HUD Icon Clear And Damage-Rect Table Frontiers Advanced

Area: `FUN_00455e84`, `FUN_00455940`/`FUN_0045fae0`, and the `DAT_0047a29c` damage-rectangle count table

Symptom: the first Step 7 ASan run stopped in `FUN_0045fae0` because `FUN_00455940` lost its incoming `EAX` string pointer while clearing HUD icon/action names. After recovering that path, ASan exposed a second fixed-address/global-layout failure in `FUN_00424b48`, where generated code indexed `&DAT_0047a29c` as though it were a contiguous table.

Evidence: original disassembly for `00455940` saves incoming `EAX` in `ESI`, sets `EDX` to each 9-byte entry at `0x00ac4cad`, restores `EAX` from `ESI`, and calls `0045fae0`. Original `00455e84` is a sequence of `mov eax,<icon-name>; call 00455940` operations over icon-name clusters such as `life1`, `armour3`, `hndicon1`, and magic/life bar ranges. After that repair, ASan reported:

```text
ERROR: AddressSanitizer: global-buffer-overflow
#0 FUN_00424b48 E2Recomp_recon.c:14961
#1 FUN_004211c8 E2Recomp_recon.c:12897
#2 FUN_0042a70c E2Recomp_recon.c:19414
#3 FUN_00426df8 E2Recomp_recon.c:16516
```

Redirecting `&DAT_0047a29c` to fixed address `0x0047a29c` cleared that ASan redzone read. The next bounded ASan run now reports:

```text
ERROR: AddressSanitizer: SEGV on unknown address 0x00000001
#0 FUN_0043cac0 E2Recomp_recon.c:29610
#1 FUN_00414e68 E2Recomp_recon.c:6242
#2 FUN_0043ce58 E2Recomp_recon.c:30141
#3 FUN_00415d40 E2Recomp_recon.c:6647
#4 FUN_00426df8 E2Recomp_recon.c:16515
#5 FUN_0041007c E2Recomp_recon.c:1104
eax = 0x00000001
```

Change: added hosted helpers that mirror the HUD icon name literals needed by `00455e84`, clear matching entries from the original `0x00ac4cad` table, and preserve the original status side effects at `0x00ac4a6c`, `0x00ac4c94`, and `DAT_0047ab08`. Replaced the generated `FUN_00455e84` body with the recovered icon-name clear sequence from original disassembly. Redirected `&DAT_0047a29c` table indexing to fixed legacy address `0x0047a29c`. Mirrored both repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. ASan no longer stops in `FUN_0045fae0` or `FUN_00424b48`.

Next Frontier: recover the current `FUN_0043cac0` call path from `FUN_0043ce58 -> FUN_00414e68`; the immediate bad read is through `in_EAX == 0x1` while formatting/scanning text.

Regression Risk: `FUN_00455e84` is now a narrow hosted reconstruction of the observed original icon-name clear sequence, not a full recovery of every `FUN_00455940` caller. `FUN_00455940` and `FUN_0045fae0` still have broader shared call surfaces and should be recovered separately when a future path reaches them.

## 2026-07-16 - Post Quick-Save No-Op ASan Frontier Recorded

Area: `FUN_0041007c -> FUN_00426df8 -> FUN_00415d40 -> FUN_00455e84 -> FUN_00455940 -> FUN_0045fae0`

Symptom: after the hosted no-op replacement for `FUN_00453920`, the bounded ASan run no longer stops in the quick-save writer path. The next crash is a read through an invalid `in_EAX` value inside `FUN_0045fae0`.

Evidence: the ASan run from `build/linux-clang32-asan` reported:

```text
ERROR: AddressSanitizer: SEGV on unknown address 0x27d9823c
#0 FUN_0045fae0 E2Recomp_recon.c:54618
#1 FUN_00455940 E2Recomp_recon.c:47610
#2 FUN_00455e84 E2Recomp_recon.c:47852
#3 FUN_00415d40 E2Recomp_recon.c:6544
#4 FUN_00426df8 E2Recomp_recon.c:16430
#5 FUN_0041007c E2Recomp_recon.c:1019
eax = 0x27d9823c
```

`FUN_00455940` iterates a 25-entry table beginning at `0x00ac4cad` and passes each entry as `param_2` to `FUN_0045fae0`. The callee then reads from its local `in_EAX` pseudo-register at `E2Recomp_recon.c:54618`, so the immediate frontier looks like another lost incoming string/pointer register around a strcmp-like helper or its call site.

Change: no code change in this pass. This was the bounded verification run requested after the `FUN_00453920` no-op.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. The single ASan run verifies that the quick-save no-op advances execution to the new `FUN_0045fae0` frontier.

Next Frontier: step 7 should recover the missing input pointer or call convention for `FUN_0045fae0`/`FUN_00455940`, then continue toward a sustained main-loop heartbeat.

Regression Risk: the quick-save path remains intentionally disabled by the hosted `FUN_00453920` no-op. `FUN_0045fae0` appears to be a shared comparison helper, so the next repair should be Ghidra-backed and avoid a broad guard that hides valid string/table comparisons.

## 2026-07-15 - Config, CDPath, Menu, Framebuffer, And Quick-Save Frontiers Advanced

Area: `FUN_0041007c`, hosted file/config startup, menu/dialog helpers, fixed-address framebuffer tables, and `FUN_00453920`

Symptom: after the earlier post-main-loop `"e_config"` work, ASan exposed a chain of independent generated-code failures: config header stack overwrite, lost CDPath stream-line arguments, stale CRT table reads, bad hosted CD path prefix, missing local path existence checks, menu string-list dereference through stale `in_EAX`, ASan global-buffer-overflows from fixed-address tables, a stale-register framebuffer rectangle fill in `FUN_0041ad54`, and finally `FUN_00453920` entering the quick-save writer with invalid string-copy state.

Evidence: ASan progressed through these frontiers in order:

```text
FUN_0043cbf0 -> stale in_EAX menu string-list dereference
FUN_0043cbf0 -> ASan global-buffer-overflow writing &DAT_006430ee table
FUN_00418a04 -> ASan global-buffer-overflow reading &DAT_00636150 surface table
FUN_0041ad54 -> null write in rectangle fill loop from lost in_EAX/unaff_EBX/extraout_ECX_01
FUN_0045fd2c <- FUN_00453920 -> invalid destination while copying saved_XXXX.ecs
```

Change: widened and packed/unpacked the startup config header buffer; added hosted CDPath line reading and path normalization; replaced CRT ctype/bit-table accesses with helper functions; repaired startup path formatting and file existence/open checks; improved `FindFirstFileA`/`FindClose`; recovered key fixed-address globals/tables including `0x00479e24`, `0x0047aad8`, `0x006430ee`, `0x006432ec`, `0x00636150`, and `0x006366dc`; made `FUN_0043cbf0` resolve either a string-list pointer or a direct string argument; replaced `FUN_0041ad54` with a bounded hosted framebuffer fill; and reduced `FUN_00453920` to a hosted no-op. Mirrored reconstructed C changes in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build build/linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass after the `FUN_00453920` no-op. Per stop request, ASan was not rerun after that final change.

Next Frontier: the next session should start with one bounded ASan run to verify the `FUN_00453920` no-op and record the next crash frontier. Do not broaden investigation unless the user explicitly approves more budget.

Regression Risk: `FUN_0041ad54` and `FUN_00453920` are hosted stabilizers, not faithful reconstructions. The quick-save path is intentionally disabled for now. Later save-game work should recover the original file/stream conventions instead of depending on the no-op.

## 2026-07-15 - CDPATH And Native Stream Reader Frontier Cleared

Area: `FUN_0041007c -> FUN_0045eb05/FUN_0045f38a/FUN_0045ec6c`, post-config CD path and native read-only stream handling

Symptom: after the config-header repair, execution fell into `FUN_00414e68` because `FUN_0045eb05(extraout_ECX_07, extraout_EDX_02)` tried to open a null/bogus path. After recovering the intended `CDPath` open, the next runtime crashes were in the generated stream slow paths: `FUN_0045f38a` used stale `extraout_EDX` when binary data hit special byte values, and `FUN_0045ec6c` dereferenced `param_2=2` while checking the native stream magic.

Evidence: `CDPATH` exists in the data directory and contains the original install path text `d:\Games\Ecstatica2\`. Original/rebuilt disassembly around the shared fopen wrapper shows the filename in `ECX` and mode in `EDX` for normal call sites, while the generated wrapper was opening `param_2` as the filename. `SHADOW.DAT` is exactly `12288` bytes, matching the `FUN_00415b78` loop, so the `FUN_0045f38a` crash was not EOF but a slow-path artifact on data bytes. ASan then showed the next independent frontier at `FUN_0041dc8c:9932`.

Change: replaced the lost-register `CDPath` open in `FUN_0041007c`, made `FUN_0045eb05` prefer a plausible `param_1` filename with fallback to `param_2`, added native `E2R_STREAM_MAGIC` handling to `FUN_0045f38a`, and guarded `FUN_0045ec6c`/`FUN_0045f38a` against impossible stream pointers. Mirrored these repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build build/linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. A bounded debug GDB run no longer crashes in the `CDPath`, `FUN_0045f38a`, or stream-close frontier; it exits with code `0340` and no stack.

Next Frontier: direct escalated runtime still crashes, and ASan reports a global-buffer-overflow at `FUN_0041dc8c:9932`, reading two bytes before `DAT_0047a2b4` while copying through legacy ranges based at `DAT_00477068`. The next step should treat this as a fixed-address/global-layout issue in the `0x00477068..0x0047a2xx` tables, not as another file I/O failure.

Regression Risk: the native stream helpers are still narrow adapters for `E2R_OpenReadStream` buffers. The pointer guards intentionally avoid dereferencing impossible decompiler artifacts; if later paths need true CRT stream descriptors, recover those call conventions separately instead of broadening the shim blindly.

## 2026-07-15 - Post Main Loop Config Open Crash Cleared

Area: `FUN_0041007c -> FUN_0045e594/FUN_0045e5b8`, post-main-loop `e_config` open and header read

Symptom: continuing past main-loop entry crashed at `EIP=0xffffffff` through `FUN_0046055c` while opening `"e_config"`. GDB showed `PTR_FUN_0047d39c`, `DAT_0047d398`, and `_DAT_00ac5204` had been overwritten with `0xffffffff`-style values before the config open.

Evidence: a hardware watchpoint showed `PTR_FUN_0047d39c` changed from the initialized `FUN_00460623` callback address to a corrupted value inside `FUN_0044c71c`. That initializer was still writing the 0x00684d68/0x00684be8 map tables through host globals, while the Linux runtime maps the original `0x00400000..0x00b00000` legacy address range for these fixed-address tables. After the repair, a debug GDB run stopped at `FUN_0045e5b8` for `param_3="e_config"` with `PTR_FUN_0047d39c=0x565db870` instead of `0xffffffff`.

Change: redirected `FUN_0044c71c` and related map-table readers to fixed legacy addresses for `0x00684d68`, `0x00684be8`, and raw palette reads from `0x00621330`. Replaced the decompiler-lost `FUN_0045e76f` read at the startup config header with `E2R_ReadOpenFileBytes(..., 0x20)`, and replaced the lost-register `FUN_0045e90e` signature comparison with a 12-byte `strncmp` against `Ecstatica001`. Mirrored the repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. Debug GDB no longer crashes through `FUN_0046055c`; it opens `E_CONFIG`, reads the 32-byte header beginning `Ecstatica001d`, and passes the `Ecstatica001` signature check.

Next Frontier: execution now exits through `FUN_00414e68` from `FUN_0041007c:303` after `FUN_0045eb05(extraout_ECX_07, extraout_EDX_02)` returns null. Live GDB values at that call are `extraout_ECX_07=0x62` and `extraout_EDX_02=NULL`, so the next investigation should recover the fopen-like filename/mode arguments for `FUN_0045eb05` rather than treating this as a missing data file.

Regression Risk: these are fixed-address and narrow config-header repairs, not a full CRT stream reconstruction. The follow-up `FUN_0045eb05` frontier is a shared wrapper and should be repaired with call-site/disassembly evidence before broadening its native adapter.

## 2026-07-13 - Main Loop Entry Reached

Area: `FUN_00410a48 -> FUN_0041ce88 -> thunk_FUN_004620db`, post-title startup transition

Symptom: after title/shadow startup fixes, execution still took the `Can't find shading data file` fatal branch from `FUN_00410a48` because `FUN_0041ce88` returned zero before the suspected main-loop call.

Evidence: original disassembly for `FUN_0041ce88` loads `EAX = 0x471890` and `EDX = 0x47007c` before calling `FUN_0045eb05`; metadata names `0x471890` as `s_shademap.dat_00471890` and the data file exists as `/home/rgrabowski/Games/Ecstatica2/SHADEMAP.DAT` with size `49152`. The original loop consumes three bytes per `128 x 128` pixel: one byte into `0x0061d030` and two bytes as a big-endian short into `0x00621630`.

Change: replaced the fragile `FUN_0041ce88` decompiler body with a native `shademap.dat` loader that fills the same legacy byte and short tables, after earlier startup repairs for allocation count arguments, raw-image descriptor reads, `shadow.dat` stream loading, `FUN_0041ccf0` lost destination, and a fixed-address clear in `FUN_0044c71c`. Mirrored generated-C repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` compiles. ASan was configured because `build/linux-clang32-asan` was absent, then `cmake --build build/linux-clang32-asan` compiles. Debug GDB hit `thunk_FUN_004620db` at `E2Recomp_recon.c:53799`, called from `FUN_00410a48` at `E2Recomp_recon.c:4752`.

Next Frontier: after continuing past the main-loop thunk, execution later crashes at `EIP=0xffffffff` in `FUN_0046055c`, called by `FUN_0045e5b8 -> FUN_0045e594` while opening `"e_config"` from `FUN_0041007c`. The next investigation should recover the indirect CRT/file callback or descriptor state around `FUN_0046055c`.

Regression Risk: the new shademap loader is purpose-built for the proven startup file format and bypasses the broken text-stream helper body. The trigonometric table initializer in `FUN_00414f40` remains an approximate native stabilizer, not a byte-perfect reconstruction.

## 2026-07-13 - Title Logic Reached

Area: `FUN_00414998 -> FUN_0041760c -> FUN_00417b20`, startup logo blit and title transition

Symptom: after the visible-window milestone, execution crashed in DirectDraw/palette and startup blit code before reaching title logic.

Evidence: `FUN_0041af88` first called the DirectDraw palette creation slot at vtable offset `0x14`, but the existing stub only implemented `CreateSurface`, leaving `_DAT_006366c0` null. After palette creation was stubbed, the next crashes exposed generated overlap/register artifacts: palette out-pointer writes targeted `DAT_006366c0` while reads used `_DAT_006366c0`; `FUN_00418a04` lost incoming `EAX` as the buffer index; `FUN_00417b20` lost incoming `EBX` as a blit coordinate; and generated `DAT_00636150` table reads did not see the `_DAT_0063615x` buffer aliases.

Change: added a minimal DirectDraw palette object and `CreatePalette` stub, redirected palette out-pointer writes to `_DAT_006366c0`, recovered the `FUN_00418a04` index and `FUN_00417b20` coordinate for the startup blit path, mapped the legacy VGA `0xa0000..0x100000` range, and mirrored reconstructed-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. GDB breakpoints hit `FUN_00414a94` and then `FUN_00414b24` from `FUN_00410a48`; the process exited with code `0340` instead of crashing in the DirectDraw/surface frontier.

Next Frontier: step 5 should continue from reached title logic toward the reconstructed main loop.

Regression Risk: DirectDraw behavior is still intentionally skeletal. Palette creation, surface methods, VGA mapping, and startup blit coordinate recovery are sufficient for this milestone but not accurate rendering.

## 2026-07-13 - Visible Window Path Proven

Area: `FUN_00458714 -> RegisterClassA -> CreateWindowExA`, initial Ecstatica II window creation

Symptom: after the first resource open was proven, execution could not advance to the window milestone because file descriptor/open-mode bookkeeping still read decompiler pseudo-registers and stale pointer-shaped values.

Evidence: original disassembly for `FUN_0045e5b8` shows the final stream-state call passes the descriptor in `EAX` and flags in `EDX`; the reconstructed code instead built an argument from `E2R_READ1(param_4,1)` with `param_4 == 0x200`. Original close helpers `FUN_0045e8e6` and `FUN_004608e8` likewise carry the descriptor in `EAX`. After repairing those paths, GDB reached `RegisterClassA` and `CreateWindowExA` from `FUN_00458714`; the top-level request used class `Ecstatica2`, title `Ecstatica II`, and size `640x640`.

Change: recovered descriptor registration/status/close bookkeeping around `FUN_004603d1`, `FUN_00460803`, `FUN_00460899`, `FUN_0045e5b8`, `FUN_0045e8e6`, and `FUN_004608e8`; mirrored those repairs in `E2Recomp/tools/GenerateRecon.js`. Added a minimal Linux X11 implementation behind `CreateWindowExA` so the original top-level window request maps a real host window.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. GDB showed `CreateWindowExA` returning the platform HWND and `e2r_x11_window.window == 20971521`, proving that the X11 window was created and mapped.

Next Frontier: after window creation, execution now crashes in `FUN_0041af88` at `E2Recomp_recon.c:8567`, calling through a DirectDraw/surface vtable during the startup logo path. The next step should recover enough DirectDraw surface behavior to reach menu/title logic.

Regression Risk: the file descriptor table repair allocates a fixed Win32-like handle table sized from `DAT_0047d610`. If later runtime paths require exact CRT descriptor growth semantics, replace it with a fuller reconstruction. The X11 window shim intentionally covers only top-level visibility, not complete Win32 message or rendering behavior.

## 2026-07-13 - First Resource Open Proven

Area: `FUN_00410a48 -> FUN_00414998 -> FUN_0045e594`, startup logo/config resource loading

Symptom: after the title-error pointer repair, tracing showed the first `CreateFileA` request was an empty string from `FUN_00414998`, so no real data file was opened.

Evidence: original disassembly for `FUN_00410a48` loads `EAX = 0x470510` before the first unconditional `FUN_00414998` call, which metadata names `s_psyglogo.raw_00470510`. Original `FUN_00414998` copies incoming `EAX` to `EDX` at entry and uses that preserved filename after `FUN_0043ac60`. GDB tracing after the repair shows `CreateFileA request: "psyglogo.raw"` and a valid non-`INVALID_HANDLE_VALUE` handle. The runtime is started from `build/linux-clang32-debug`, then enters the `Ecstatica2` data symlink before reconstructed startup.

Change: restored the lost `FUN_00414998` filename input from `param_1`, preserved it across `FUN_0043ac60`, recovered the three startup logo filename symbols used by `FUN_00410a48`, converted the split `E_CONFIG` stack filename into a contiguous 9-byte buffer, changed the Linux launcher to enter `E2RECOMP_DATA_DIR`, and made `CreateFileA` normalize backslashes plus resolve read-only paths case-insensitively. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. The first proven real resource open is `/home/rgrabowski/Games/Ecstatica2/PSYGLOGO.RAW`, requested by reconstructed code as `psyglogo.raw`.

Next Frontier: after the successful open, debug GDB now stops in `FUN_0045e5b8` at `E2Recomp_recon.c:52844`, where the decompiled code reads `E2R_READ1(param_4,1)` with `param_4 == 0x200`. The next investigation should recover the file-handle/open-mode bookkeeping around `FUN_0045e5b8` instead of treating `param_4` as a pointer.

Regression Risk: the `CreateFileA` compatibility fallback is intentionally Win32-like for read-only opens; if write/create paths later need case handling, extend it carefully without redirecting writes to unintended files.

## 2026-07-13 - Title Error Exit Lost EAX Message Pointer

Area: `FUN_00414b24 -> FUN_00414e68`, title picture load failure path

Symptom: `FUN_00414e68` dereferenced `0x200` while scanning its shutdown message string.

Evidence: original disassembly shows `FUN_00414e68` saves `EAX` into `EBP` at entry and later scans that pointer. The failing `FUN_00414b24` branch at `00414e43` loads `EAX = 0x471320` before calling `00414e68`; metadata names that string `s_Can't_load_title_picture_00471320`. GDB stopped at the reconstructed `FUN_00414e68` with the stale local still showing `0x200` before the new assignment, then after one step `in_EAX` pointed at `s_Can_t_load_title_picture_00471320` with contents `Can't load title picture`.

Change: initialized the lost `in_EAX` pseudo-register in `FUN_00414e68` to the recovered title-load error string, added the missing generated string declaration/global/data initialization, and mirrored the function-body repair in `E2Recomp/tools/GenerateRecon.js`.

Result: `cmake --build --preset linux-clang32-debug` and `cmake --build build/linux-clang32-asan` both compile. Debug GDB run no longer faults on the `0x200` dereference; it exits through the recovered fatal shutdown path with code `0364`.

Next Frontier: the runtime now reaches a clean fatal exit for `Can't load title picture`, meaning the next startup investigation should focus on why `FUN_0045e594(..., s_title_s_raw_00471314, 0x200, ...)` fails to load `title_s.raw` from the Ecstatica II data path. ASan execution still aborts earlier in `FUN_0041dc8c` on a global-buffer-overflow around overlapping globals near `DAT_0047a2b4`; the ASan build itself compiles.

Regression Risk: `FUN_00414e68` is a shared fatal-exit helper whose original convention carries the message pointer in `EAX`. This repair recovers the current title-load call path only; future fatal-exit call sites may need their own `EAX` message recovery instead of reusing this default.

## 2026-07-13 - Startup Wait-Loop Stack Corruption

Area: `FUN_00410a48`, startup pacing around `FUN_00414998`

Symptom: after the date conversion helper repair, the program reached `FUN_0043ac60` and then crashed with `EIP=0x0`. The raw stack showed return addresses around `FUN_00410a48:570`, where startup wait loops called `FUN_0045f1c0` with decompiler `extraout_ECX` values.

Evidence: GDB showed the first `FUN_0043ac60` return had a sane frame, but the later crash involved a `FUN_0045f1c0` call with a stack/frame pointer-like output address. That helper writes a 0x24-byte time structure, so using a phantom register as the destination can overwrite caller stack state.

Change: replaced the fragile 5 ms busy-wait loops in `FUN_00410a48` with explicit `Sleep(5)` pacing and stable zero arguments for the adjacent calls. Mirrored the transformation in `E2Recomp/tools/GenerateRecon.js`.

Result: both `linux-clang32-debug` and `linux-clang32-asan` rebuilt. The runtime moved past the null instruction pointer crash and now stops in `FUN_00414e68` via `FUN_00414b24`, dereferencing `0x200`.

Regression Risk: this is a Linux runtime stabilization, not a perfect reconstruction of the original timing code. If menu/intro pacing behaves oddly later, recover the original local time-buffer addresses with Ghidra and replace the `Sleep(5)` shim.

## 2026-07-13 - Date Helper Lost Output Pointer

Area: `FUN_004645d2`, called from `FUN_00461ab5`/`FUN_0045f1c0`

Symptom: crash writing through `extraout_ECX_00 + 0x10` inside `FUN_004645d2`.

Evidence: GDB stopped at `E2Recomp_recon.c:60066`; the destination pointer resolved to unrelated executable memory rather than the time output structure.

Change: rewired `FUN_004645d2` to write year/month/day/week fields through `param_1` and to return `param_1`. Mirrored the replacement in `GenerateRecon.js`.

Result: the program advanced to the startup wait-loop stack corruption described above.

Regression Risk: `FUN_004645d2` still contains unrecovered `in_EAX`/`unaff_EBX` inputs. It may need a fuller Ghidra-backed signature recovery when date/time behavior matters.
