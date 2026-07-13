# Runtime Crash Fixes

Use the runtime crash fix template in [journal.template.md](../../templates/journal.template.md) for new entries.

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
