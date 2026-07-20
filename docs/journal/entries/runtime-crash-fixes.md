# Runtime Crash Fixes

Use the runtime crash fix template in [journal.template.md](../../templates/journal.template.md) for new entries.

## 2026-07-20 - Version-Gated FAN Parsers Reach Title Surface

Area: `FUN_004173c8`, `FUN_004448e4`, `FUN_00445000`, `FUN_004451a8`, `FUN_00452a58`, `FUN_00447638`, `FUN_004418fc`, `FUN_00441958`, `FUN_0045fae0`

Symptom: after the actor-list fixes, ASan reached `FUN_004453a4 -> FUN_004448e4 -> FUN_0043cac0` from stale record-type state. Once that parser advanced, ASan exposed the same hidden stream/register artifact in `FUN_00445000` and `FUN_004451a8`, then stale fixed-address table artifacts in `FUN_00447638`, packed-name lookup, and remap-table reads. Debug continued to report the bounded ordinal-4 unknown-record diagnostic at offset `104855`.

Evidence: original `004448E4` preserves the stream in `ESI`, reads records through `004413FC`, and loops or returns from the decoded record type rather than `extraout_ECX`. Original `00445000` also stores the stream in `ESI` and calls `004173C8` with that stream before building records. Original `004451A8` stores the stream in `ECX`, keeps it across `00452A58`, and reads payload bytes through that same pointer. Original `00452A58` takes its allocation size in `EAX`. Original `00447638` stores the stream in `EDX`, writes the initial `128x128` word table through the explicit `0x00684d68` destination pointer, and uses the fixed `0x0068cd68/0x0068cd6f` record table. ASan then showed the remap lookup at `0x006769f8` and the other generated remap-table globals needed the same fixed-address treatment. The previous `FUN_004418fc -> FUN_0045fae0` heap-use-after-free was caused by decompiled lookup wrappers using stale `extraout_CX` advancement and a `strcmp` shim that ignored its explicit left pointer.

Change: bound hosted `FUN_004173c8` to the active FAN stream; recovered `FUN_004448e4` record reads, skip-loop reads, and terminator handling; bound `FUN_00445000` and `FUN_004451a8` to the active stream; passed the bitmap payload size explicitly into `FUN_00452a58`; fixed the first `FUN_00447638` stream argument/table destination; added direct packed-name lookup wrappers; repaired `FUN_0045fae0` to compare explicit inputs; and redirected the remaining fixed record/remap-table accesses to literal legacy addresses. Mirrored new generator-backed repairs in `E2Recomp/tools/GenerateRecon.js`; the remap-table broad rewrite already existed and the reconstructed C was brought into line with it.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `git diff --check`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug probe `/tmp/e2-step10-remaptables-debug` still reports ordinal 4 at offset `104855`. ASan probe `/tmp/e2-step10-remaptables-asan` exits with code `0`, dumps the Ecstatica II title surface on surface 3 with hash `6e39f5ea`, and no longer reports the packed-name use-after-free or fixed-table global overflows. The requester/action state is still empty: `start_game entries=0`, `startup_scan=0`, and `dispatch=0`.

Next Frontier: recover the remaining `FUN_00444c10` action-node parser state so `_DAT_00637250` is populated before `FUN_0043a39c` scans StartUp and Start Game action codes. Original disassembly keeps the stream in `ESI` while preserving action node pointers and bytecode cursors on the stack; the current decompiled body still has `extraout_*` artifacts in that section.

Regression Risk: `FUN_00447638` and `FUN_00444c10` are still only partially recovered; ASan can render the title surface, but Start Game action dispatch is not restored. The bounded FAN diagnostics are still temporary and should remain until debug and ASan section alignment converge.

## 2026-07-20 - FAN Actor Lists And Hosted Word Reads Advance

Area: `FUN_004171b8`, `FUN_004268a4`, `FUN_004268e4`, `FUN_0042692c`, `FUN_004435e8`, `FUN_00444c10`, `FUN_004526e4`

Symptom: the first 2026-07-20 ASan probe reached `FUN_00444c10 -> FUN_004268e4` with hidden owner `EAX=0x2`. After recovering that helper, subsequent probes exposed the same decompiler artifact class in `FUN_004526e4`, `FUN_004435e8`, and `FUN_004268a4`. Once those were cleared, hosted FAN word reads stuck on an embedded `0x1a` byte and filled the script pool with repeated `0xffff` tokens. After raw hosted word reads were recovered, ASan exposed fixed-address remap-table reads in `FUN_004435e8`.

Evidence: original disassembly at `00444ED0..00444EDF` passes owner pointers from `[esp+18h]` and `[esp+0Ch]` into `004268E4`/`0042692C`. Original `004268A4`, `004268E4`, and `0042692C` all allocate a single object/list node after preserving incoming state. Original `00444D66..00444D7B` writes the current `CX` object id, looks up an existing object through `006297C0`, and passes that object pointer in `EAX` to `004526E4`. Original `00444DCB..00444DD0` zero-extends the current token into `EAX` before calling `004435E8`, while preserving the original token in `EDX` for repeat handling. A bounded word trace showed hosted `FUN_004171b8` stuck at offset `104855` on an embedded `0x1a`; reading two raw bytes for hosted `E2R_STREAM_MAGIC` streams advanced past that point. ASan then stopped on `FUN_004435e8` remap-table reads through generated globals instead of literal fixed addresses.

Change: recovered the hidden owner pointer and one-record allocation contracts for `FUN_004268a4`, `FUN_004268e4`, and `FUN_0042692c`; made `FUN_004526e4` accept the object pointer explicitly; restored the `FUN_00444c10` object-id write and existing-object removal call; passed current tokens explicitly into `FUN_004435e8`; added raw two-byte hosted FAN word reads for `FUN_004171b8`; and redirected the immediate actor-token remap-table reads to fixed legacy addresses. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. A short ASan Start Game readiness probe now exits without a sanitizer report while parsing is still in progress and dumps nonblank surfaces. A longer ASan probe advances beyond the earlier `FUN_00444c10` frontiers to records near offset `259113`, then stops through `FUN_004453a4 -> FUN_004448e4 -> FUN_0043cac0` with `EAX=0x1`. The matching debug probe still reports the ordinal-4 unknown-record diagnostic after the three zero terminators.

Next Frontier: recover the original input/register contract for `FUN_004448e4` and reconcile debug/ASan parser alignment after the third zero terminator.

Regression Risk: hosted raw word reads are scoped to native `E2R_STREAM_MAGIC` FAN streams and bypass the CRT text-mode `0x1a` behavior only for those hosted buffers. The first-sixty-four-word diagnostic is temporary and should be removed once the FAN section alignment is stable.

## 2026-07-20 - FAN Actor String Owner Frontier Recorded

Area: `FUN_004453a4`, `FUN_00444c10`, `FUN_004268e4`, `FUN_0042692c`

Symptom: after three validated zero section terminators, sandboxed bounded game probes exit immediately with code `159`. Running the same probes outside the sandbox reaches the FAN version-gated section. The debug probe still reports bounded ordinal-4 unknown-record diagnostics, and the ASan probe stops in `FUN_004268e4` while reading through hidden `EAX=0x2`.

Evidence: original disassembly at `00444C10` preserves the FAN stream in `ESI`. At `00444ED0..00444EDF`, it loads `EAX` from `[esp+18h]` before calling `004268E4` for the first nested node, and from `[esp+0Ch]` before calling `0042692C` for subsequent nodes. Original `004268E4` and `0042692C` save incoming `EAX` in `ESI`, then allocate exactly one `0x39`-byte record with `FUN_0045F1FF`. The generated C instead passed stale state into the helpers and let `FUN_004268e4` dereference `in_EAX == 0x2`.

Change: no code change in the progress-check pass. Documentation was updated before continuing with the recovered owner-pointer repair.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass before the repair. Host debug probe reports ordinal 4 at offset `104855`; host ASan probe reports `FUN_004453a4 -> FUN_00444c10 -> FUN_004268e4` with a zero-page read at `0x00000002`.

Next Frontier: recover the hidden owner-pointer input and fixed allocation count for `FUN_004268e4` and `FUN_0042692c`, then rerun the bounded Start Game ASan probe.

Regression Risk: the ordinal-4 diagnostic is still temporary. The next code change touches actor string/node linking during FAN parsing, so it must be generator-backed and verified with both debug and ASan probes.

## 2026-07-18 - FAN Record Sections Preserve Hidden State

Area: `FUN_004413fc`, `FUN_0045326c`, `FUN_00453264`, `FUN_00447090`, `FUN_0042b880`, `FUN_004453a4`

Symptom: after all packed FAN name tables loaded, ASan first reported a use-after-free write in `FUN_004413fc`, then stale-pointer failures in record normalization and actor construction. Once those were cleared, the top-level loop decoded payload bytes as unknown record type `0x0701`.

Evidence: original disassembly shows `FUN_0045326c` returns the pool slot from `FUN_0045328c`; `FUN_004413fc` preserves the stream in `EDX`, reads five words, and returns the slot in `EAX`; callers pass that record in `EAX` to `FUN_00447090`, `FUN_0042b880`, and `FUN_00453264`. A bounded record probe reported three consecutive type-zero records at offsets `104825`, `104835`, and `104845`. The parser then tested stale `uVar10` rather than decoded `sVar9`, ignored the third terminator, and read mixed payload at offset `104855`.

Change: returned the actual pool slot from `FUN_0045326c`; made the five-word stream read explicit; preserved the current FAN record across normalization, actor construction, and pool release; bound `FUN_0042b880` to that record; added bounded record diagnostics; and changed the top-level terminator condition to use `sVar9`. Mirrored all generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: debug and ASan builds pass, generator syntax validation passes, and ASan consumes all three zero terminators without treating payload as an unknown record. The runtime now enters the next version-gated FAN section.

Next Frontier: recover the original entry/input contract for `FUN_00444c10`, currently reached from `FUN_004453a4` and failing with a global-buffer-overflow near `_DAT_0047a47c`.

Regression Risk: current-record state is scoped to active FAN parsing and models a register lifetime lost by decompilation. The first-sixteen-record and unknown-record stderr diagnostics are temporary and must be removed once section alignment is stable.

## 2026-07-18 - FAN Parser Reaches Object Records

Area: `FUN_00445378`, `FUN_004453a4`, FAN packed name tables, `FUN_0043a39c`, `FUN_0044f508`

Symptom: recovered Start Game selection entered `FUN_0043a39c` but returned to the requester. New boundary counters reported `startup_scan=0`, `action_scan=0`, and `dispatch=0`, proving `_DAT_00637250` was never populated.

Evidence: original `FUN_00445378` disassembly opens the FAN stream, preserves it in `EAX`, calls `FUN_004453a4` with mode in `EDX`, then closes the stream. The hosted reconstruction only opened and closed the file. After restoring the parser call, `Code/ECSTATIC.FAN` passed its `FANT` header and exposed repeated lost token-pointer, packed-table length, source-ordinal, and scalar-global array artifacts. Original helper bounds identify eleven packed name-table capacities and entry limits.

Change: restored explicit FAN stream handoff through `FUN_00445378`, `FUN_004453a4`, and `FUN_004171b8`; replaced the eleven hidden-register string intern paths with one bounded packed-name helper; preserved source table ordinals in dedicated counters; wrote mappings to literal DGROUP addresses; recovered Start-code name matching and action-node handoff into `FUN_0044f508`; and added bounded lookup/dispatch counters. Mirrored the repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: generator syntax validation and the ASan build pass. An isolated generated `E2Recomp_recon.c` also compiles. ASan progresses through all FAN name tables and now stops in the first object-record phase at `FUN_004453a4 -> FUN_00444668 -> FUN_004413fc`, rather than returning from an empty action list.

Next Frontier: recover the original object pointer passed in `EAX` from `FUN_00444668` to `FUN_004413fc`. The current decompile writes through a stale freed pointer at reconstructed line 32711.

Regression Risk: FAN parsing is now active during startup, so the bounded runtime currently reaches the new ASan frontier before requester readiness. Packed-name comparison is explicit and case-sensitive; `FUN_00446afc` used a distinct original comparison helper and may require case-folding if later evidence shows mismatched names.

## 2026-07-18 - Start Game Requester Record Recovered

Area: requester ids `0x27/0x28`, record `0x0047a588`, item `0x00643b30`, `FUN_0043a39c`

Symptom: Step 9 could navigate reconstructed requester input but initialized requester `0x27/0x28` with first item `0x00643ad0`, exposing Uninstall/Quit/Cancel and leaving Start Game unreachable.

Evidence: `E2WIN95.EXE` DGROUP bytes at `0x0047a588` decode as `{-1, -1, 0xd2, 0xb4, 0, 0x00643b30}`. Original menu construction links `0x00643b30` to Save, Load, Settings, Quit, and Cancel. The Start Game callback `LAB_0043d458` sets `_DAT_00643650=0`, whose main-loop switch enters `FUN_0043a39c(..., 0)`.

Change: initialized requester `0x0047a588` from the original dimensions and first-item pointer, mirrored the recovery in `E2Recomp/tools/GenerateRecon.js`, added `FUN_0043a39c` entry counters, and made ready-sequence probes preserve a bounded post-Start observation delay.

Result: generator syntax validation and debug/ASan builds pass. Debug and ASan `escape,enter` probes select `0x00643b30`, dispatch one action, advance the `FUN_0043a39c` entry count from `1` to `2` with player/mode `0`, and remain free of sanitizer reports for five seconds. Both produce nonblank surface-3 hash `d8293730` but return to the menu with `_DAT_00643650=5` rather than loading a scene.

Next Frontier: recover the Start-code action-name lookup/dispatch cluster in `FUN_0043a39c`. `Code/ECSTATIC.FAN` contains `mar:StartGame`, but the reconstructed path loses the original string index passed in `EAX` to `FUN_00442128`, crosses the hosted no-op `FUN_0045f22f`, and does not preserve the selected action-node `EAX` into `FUN_0044f2fc`.

Regression Risk: requester ids `0x27/0x28` now expose the original full Start Game chain instead of the narrower Step 9 test chain. Quit remains reachable through the restored links, and debug/ASan Start Game probes cover the new default action.

## 2026-07-17 - Quit Confirmation Prompt Recovered

Area: `FUN_0043c910`, `DAT_0043d49c`, requester id `0x14`, `_DAT_00643650`

Symptom: Quit selection could safely take the original cancel/no branch, but the actual confirmation prompt was still unrecovered and confirmed Quit could not reach `_DAT_00643650=6`.

Evidence: original disassembly at `0043c910..0043c995` builds requester id `0x14`, copies a bounded prompt string into a stack buffer, stores the prompt pointer at `0x0047a520`, sizes `0x0047a51c`, clears word `006443D4`, runs `FUN_0043b384`, and returns the high word of `_DAT_006443d2`. Original callbacks `LAB_0043c594` and `LAB_0043c4e8` set or clear that high word for id `0x14`. Original state switch case `6` at `0041638a..0041639a` sets `_DAT_00643660=1` and opens requester id `0x31`; the decompiler had reconstructed that arm as a fatal `FUN_00414e68()` call.

Change: recovered `FUN_0043c910` with a stable hosted prompt buffer, initialized the fixed Yes/No prompt item records, wired id/item-aware prompt callbacks, made the Quit action call the prompt helper, fixed the native requester-sequence probe to wait per queued key, and corrected the original switch case `6` behavior. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug and ASan `escape,num2,enter,enter` select Quit then default No and finish with `_DAT_00643650=5`. Debug and ASan `escape,num2,enter,num2,enter` move from No to Yes, dispatch the Yes callback, open requester id `0x31`, and finish with `_DAT_00643650=6` without sanitizer reports.

Next Frontier: the prompt text at fixed English address `0x004729b8` is still unnamed in generated data, so the recovery uses the localized pointer at `0x0060aef0` when available and a bounded fallback string otherwise. Future work can recover the missing raw data symbol/text exactly.

Regression Risk: confirmed Quit now reaches the original state `6` transition and id `0x31` requester path. That broadens executable behavior beyond the previous safe cancel fallback, but debug and ASan probes cover both No and Yes outcomes.

## 2026-07-17 - Quit Callback No-Confirm Path Recovered

Area: `DAT_0043d49c`, `E2R_InvokeRequesterAction`, main-menu requester callbacks

Symptom: `escape,num2,enter` could select the fixed-address Quit item at `0x643ca4`, but the selected action `DAT_0043d49c` was still only recorded by the simple dispatcher and left unhandled.

Evidence: original disassembly at `0043d49c..0043d4e4` shows the Quit action calls `FUN_0043c910` with localized text from `0x0060aef0` or fixed text at `0x004729b8`, then sets `_DAT_00643650=6` when the prompt returns nonzero and `_DAT_00643650=5` otherwise. The current reconstructed `FUN_0043c910` path still depends on unrecovered prompt/string-copy behavior, so the bounded safe branch is the original declined/cancel result.

Change: added a `DAT_0043d49c` case to `E2R_InvokeRequesterAction` that applies the original no-confirm result by setting `_DAT_00643650=5` and returning handled. Mirrored the dispatcher case in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, `cmake --build build/linux-clang32-asan`, and `git diff --check` pass. Debug and ASan `escape,num2,enter` probes both select `0x643ca4`, record one action with `selected_action`/`last_action` pointing at `DAT_0043d49c`, keep `_DAT_00643650=5`, write surface 3 with hash `9042c4ed`, and finish without sanitizer reports.

Next Frontier: recover the `FUN_0043c910` yes/no prompt helper and the source text at `0x004729b8`/`0x0060aef0` so Quit can display the original confirmation and take the `_DAT_00643650=6` branch only when the user confirms.

Regression Risk: this intentionally preserves the original cancel/no outcome for Quit until prompt handling is recovered. It avoids crashing or exiting through an unrecovered confirmation path, but it does not yet implement confirmed quit behavior.

## 2026-07-17 - Requester Focus Movement Recovered

Area: `FUN_0043bd4c`, fixed-address requester item records, `_DAT_00643430`

Symptom: requester-ready `escape,num2,enter` still selected cancel because `_DAT_00643430` was unset and the key handler trusted a stale `param_2`/last-rendered item. After seeding focus, Down exposed garbage `next` and action slots for the fixed-address requester item records.

Evidence: debug and ASan probes showed `selected=0x0`, `param=0x643780`, `moves=0` before the focus seed. After seeding, `selected=0x643ad0` but `next`/`selected_action` were garbage until the main-menu item chain was initialized locally. A two-Down probe then exposed integer-global pointer arithmetic on `_DAT_00643430 + 4`.

Change: added a guarded first-item focus seed for `FUN_0043bd4c`, initialized the fixed-address main-menu requester item chain at requester open, marked those local records keyboard-focusable for the recovered movement branch, and cast `_DAT_00643430` back to `short *` before item-slot pointer arithmetic. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, `cmake --build build/linux-clang32-asan`, and `git diff --check` pass. Debug and ASan `escape,num2,enter` move from `0x643ad0` to `0x643ca4` and dispatch `DAT_0043d49c`. Debug and ASan `escape,num2,num2,enter` move through `0x643ca4` to cancel `0x643780` and dispatch `LAB_0043c4e8` without crashing.

Next Frontier: reconstruct complex callback `DAT_0043d49c`; it is now selectable and recorded but intentionally not executed by the simple dispatcher.

Regression Risk: the main-menu item chain initializer is scoped to requester ids `0x27/0x28` via the existing open branch. It is still a fixed-address reconstruction shim; broader requester families may need their own item-chain recovery.

## 2026-07-17 - Requester Input Reaches Action Selection

Area: `FUN_0043bd4c`, `FUN_0043b9bc`, `FUN_0043adc0`, `FUN_0041af88`, requester-ready input probes

Symptom: requester-ready probes could render the requester, but `escape,num8,enter` did not reliably reach the requester key-consume path. Once keys were fed directly into `FUN_0043bd4c`, Enter advanced into raw decompiler label callbacks and malformed requester restore copies.

Evidence: debug runs showed `bd4c` being called with `key=0x0` until requester keys were staged on the game thread. GDB then showed Num8 reaching the requester movement branch with a stale hidden requester-record register, Enter crashing first in `FUN_0043adc0` restore copies, and then in raw label callback `LAB_0043c4e8`. ASan additionally exposed `FUN_0043b9bc` accepting a mapped but wrong requester-record pointer and `FUN_0041af88` accepting a stray high palette pointer.

Change: added requester-local pending key staging for ready probes, so post-Escape keys are fed at `FUN_0043bd4c` entry on the game thread. Reconstructed hidden requester-record inputs for `FUN_0043bd4c` and `FUN_0043b9bc` via `FUN_0043aeac`, added a rendered-item fallback for the current requester item, stabilized `FUN_0043adc0` by reconstructing the current item and skipping malformed screen-copy calls, recorded raw action callback labels, dispatched the simple state-setting labels recovered from original disassembly, and tightened `FUN_0041af88` palette source guards. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, `cmake --build build/linux-clang32-asan`, and `git diff --check` pass. Debug and ASan `escape,num8,enter` requester-ready probes both finish with surface-3 hash `9042c4ed`, `key=0xd`, `pending=2/2`, `fed=2`, and `actions=1`.

Next Frontier: `escape,num8,enter` and `escape,num2,enter` both still land on the cancel record at `0x643780`, so focus/selection fidelity is now the immediate frontier. The harder callback labels, especially `DAT_0043d49c`, still need full reconstruction once probes can select them.

Regression Risk: raw requester callbacks are intentionally not invoked yet, and `FUN_0043adc0` restore copies are no-oped for stability. These are Step 9 stabilizers around known decompiler artifacts, not final menu/action behavior.

## 2026-07-17 - Debug Requester Timing Parity Recovered

Area: `FUN_004142b8`, `FUN_004142e4`, `FUN_00415b78`, requester-ready input probes

Symptom: ASan could reach requester rendering for the `escape,num8,space` sequence, but the debug build either missed requester readiness or exited through a stale high-code `ExitProcess` path before the delayed input probe fired.

Evidence: extended `ExitProcess` caller logging mapped the debug-only high-code exit first to `FUN_004142e4 -> FUN_0045f38a` while reading startup music data, then to `FUN_00415b78 -> FUN_00414e68` while opening the shadow table. A direct GDB run after the first bypass showed `FUN_004142b8` still using stale allocation arguments before formatting a bogus fatal message. The successful debug requester-ready probe later reported `requester-ready wait satisfied after 20 ms`, `_DAT_00643650=5`, `DAT_00479de8=1`, requester counters `ce58=12`, `b9bc=36`, and surface-3 hash `af17b505`.

Change: added `--inject-key-sequence-ready-surfaces` so probes wait for requester/menu readiness instead of relying on a fixed startup delay. Hosted the startup music buffer allocation in `FUN_004142b8`, made `FUN_004142e4` a temporary success no-op for Step 9, and forced `FUN_00415b78` to open literal `shadow.dat` instead of accepting a stale first argument. Mirrored generated-code repairs in `E2Recomp/tools/GenerateRecon.js`. `ExitThread` now terminates only the calling pthread on Linux, and high stale `ExitProcess` codes are treated as thread termination for diagnostics instead of killing the whole process.

Result: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build --preset linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. Debug `--inject-key-sequence-ready-surfaces /tmp/e2-step09-ready-debug-music-alloc-shadow escape,num8,space 8 250 3` reaches requester rendering and writes surface 3 with hash `af17b505`. ASan `--inject-key-sequence-ready-surfaces /tmp/e2-step09-ready-asan-music-alloc-shadow escape,num8,space 6 250 5` still reaches requester rendering with surface-3 hash `9042c4ed`.

Next Frontier: requester fidelity and actual menu navigation are now the Step 9 frontier. Audio stream reconstruction remains intentionally deferred; the current music loader bypass is a hosted runtime stabilization, not a faithful audio implementation.

Regression Risk: `FUN_004142e4` is intentionally bypassed, so startup music playback is disabled. The `FUN_00415b78` literal-path recovery is narrow to `shadow.dat`; other callers of `FUN_0045eb05` may still need call-site-specific argument recovery if they pass readable stale pointers.

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
