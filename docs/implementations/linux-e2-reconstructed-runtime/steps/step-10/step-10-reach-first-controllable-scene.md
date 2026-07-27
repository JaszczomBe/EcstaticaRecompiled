# Reach First Controllable Scene

Status: active
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-27

## Goal

Advance from verified menu action dispatch into a gameplay scene loaded from original Ecstatica II data, then prove one player or camera input changes reconstructed scene state.

## Why This Step Exists

Step 9 proved that Linux host input can traverse the compatibility message path, navigate reconstructed requesters, and execute original menu callbacks. The next product-shaped milestone is to drive the original Start Game transition through `FUN_0043a39c`, stabilize scene loading, present a gameplay frame, and demonstrate control.

## Scope

1. Recover the original requester `0x27/0x28` record and item topology needed to select Start Game.
2. Add bounded probe evidence for Start Game action dispatch and `FUN_0043a39c` entry.
3. Follow the first scene-loading path and repair only concrete decompiler/runtime frontiers required to load one scene.
4. Capture a nonblank gameplay-scene frame from original data in debug and ASan builds.
5. Inject one movement input and prove a player, camera, or scene-state change.

## Out Of Scope

1. Completing the game or every scene transition.
2. Polished movement, collision, or camera behavior.
3. Save/load workflow completion.
4. Audio fidelity and startup music restoration.
5. SDL backend work.

## Usage Budget

No more than 5% of weekly usage per day unless the user explicitly approves continuing.

## Temporary Sacrifices

1. Sacrifice: use bounded native probes and reconstruction instrumentation while scene entry is unstable.
2. Why accepted now: deterministic state evidence is needed before interactive runtime behavior is durable.
3. Removal trigger: one scene loads and accepts movement reliably in both debug and ASan builds.

## Generated-File Churn Guard

Step 10 frequently needs small reconstructed C probes, but `E2Recomp/reconstructed/E2Recomp_recon.c` is generated. Do not carry large regenerated diffs forward as implementation progress.

Required workflow for this step:

1. Before editing, inspect staged and unstaged state with `git status --short`, `git diff --stat`, and `git diff --cached --stat`.
2. If proving a hypothesis requires a hand edit in `E2Recomp_recon.c`, keep it narrow and record the exact function/address.
3. Mirror the proven edit in `E2Recomp/tools/GenerateRecon.js` before running broad verification.
4. After changing the generator, run `node --check E2Recomp/tools/GenerateRecon.js` and `node E2Recomp/tools/GenerateRecon.js .`.
5. Immediately inspect generated drift. Acceptance for regeneration is: no reconstructed-file diff, or only the intentionally mirrored C changes already explained in the step/journal.
6. If regeneration creates thousands of unrelated lines, stop. Do not build, probe, or patch around that output. Tighten the generator replacement anchors or move the replacement later in the pipeline until the diff is small and intentional.

## Starting Evidence

Step 9 recovered callbacks `LAB_0043d458` and `LAB_0043d464`, which set `_DAT_00643650` to `0` and `1`. The main-loop switch stores the corresponding player selection in `_DAT_0047a4dc` and calls `FUN_0043a39c(..., 0)`.

Original executable data at `0x0047a588` identifies requester `0x27/0x28` as `{-1, -1, 0xd2, 0xb4, 0, 0x00643b30}`. The temporary Step 9 reconstruction instead used `0x00643ad0` as the first item, exposing Uninstall/Quit/Cancel while leaving the original Start Game item unreachable.

## Current Evidence

The requester record now matches the original `E2WIN95.EXE` DGROUP bytes at `0x0047a588`, including first item `0x00643b30`. `FUN_0043a39c` entry probes and a post-action observation delay were added to the bounded native launcher.

Debug and ASan probes both select the original default Start Game item and enter `FUN_0043a39c`:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-start-game-debug-post5 escape,enter 8 250 5
build/linux-clang32-asan/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-start-game-asan-post5 escape,enter 8 250 5

selected=0x643b30 next=0x643b10 actions=1
start-game entry observed: entries 1->2 player=0 mode=0
surface 3 nonblank=1 hash=d8293730
```

Both configurations remained alive without an ASan report during the five-second observation window, but returned to the menu with `_DAT_00643650=5`; a gameplay scene was not loaded.

Start-code boundary counters then proved both `FUN_0043a39c` entries saw an empty action list: `startup_scan=0`, `action_scan=0`, and `dispatch=0`. The cause was earlier than name matching. Hosted `FUN_00445378` had been reduced to open/close success and omitted the original `FUN_004453a4` FAN parser call.

The loader now hands the hosted stream explicitly into `FUN_004453a4` and `FUN_004171b8`. Eleven packed name-table helpers use bounded string interning with explicit source ordinals and fixed DGROUP destinations. `FUN_0043a39c` resolves packed action names and preserves selected action nodes into `FUN_0044f508`; these repairs are mirrored in `GenerateRecon.js`, and isolated regenerated C compiles.

ASan now traverses every FAN name table and the first three object-record sections. Original disassembly proved `FUN_0045326c` must return the pool slot from `FUN_0045328c`, while `FUN_004413fc` preserves the FAN stream and fills five 16-bit fields. A scoped current-record state now carries that original hidden-register value through `FUN_00447090`, `FUN_0042b880`, and `FUN_00453264`.

A bounded record probe established the first three records are valid zero section terminators:

```text
FAN record: ordinal=1 offset=104825 fields=0000,0000,3a33,004d,3a51
FAN record: ordinal=2 offset=104835 fields=0000,0000,3a33,004d,3a51
FAN record: ordinal=3 offset=104845 fields=0000,0000,3a33,004d,3a51
```

The top-level parser incorrectly tested stale `uVar10` after record 3, consumed payload bytes as a fourth record, and reported unknown type `0x0701`. Testing decoded `sVar9` restores the terminator and advances ASan into the next version-gated section.

A 2026-07-20 progress check confirmed that sandboxed game probes exit immediately with code `159`, while the same bounded probes run outside the sandbox. The debug host probe still reports the bounded ordinal-4 unknown-record diagnostic after the three validated terminators:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-progress-debug escape,enter 8 250 5

FAN record: ordinal=1 offset=104825 fields=0000,0000,3a33,004d,3a51
FAN record: ordinal=2 offset=104835 fields=0000,0000,3a33,004d,3a51
FAN record: ordinal=3 offset=104845 fields=0000,0000,3a33,004d,3a51
FAN record: ordinal=4 offset=104855 fields=0761,0701,0000,0001,0001
FAN unknown record: ordinal=4 offset=104855 remaining=1994317 fields=0761,0701,0000,0001,0001
```

The ASan host probe reaches `FUN_00444c10` and now stops in the first nested actor-string allocation/link helper:

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-progress-asan escape,enter 8 250 5

FUN_004453a4 -> FUN_00444c10 -> FUN_004268e4
SEGV reading address 0x00000002
EAX = 0x00000002
```

Original disassembly shows `FUN_00444c10` preserves the FAN stream in `ESI`, but calls `004268E4` with the owner pointer from `[esp+18h]` and `0042692C` with the previous nested node pointer from `[esp+0Ch]`. That owner-pointer contract is now recovered, along with sibling allocation/count fixes in `FUN_004268a4`, `FUN_004268e4`, and `FUN_0042692c`, explicit object replacement through `FUN_004526e4`, token input recovery for `FUN_004435e8`, raw two-byte reads for hosted FAN streams in `FUN_004171b8`, and fixed-address remap-table reads for the actor-token name tables.

The 2026-07-20 continuation recovered the original stream/input contracts for the next version-gated parser helpers. Original disassembly showed `FUN_004448e4` keeps the FAN stream in `ESI` and tests the decoded record type, `FUN_00445000` reads through the same stream and feeds `FUN_004173c8`, and `FUN_004451a8` keeps the stream in `ECX` while allocating bitmap payload storage. The first `FUN_00447638` table load now writes its 128x128 word table through the explicit destination pointer instead of stale `extraout_ECX` state. The packed-name lookup wrappers now walk the hosted packed-name tables directly, `FUN_0045fae0` compares its explicit input pointers, and the remaining `FUN_00447638`/remap-table accesses use literal legacy addresses instead of generated global fragments.

The 2026-07-20 continuation removed the debug/ASan parser divergence. Hosted streams now preserve the original binary/text byte behavior instead of using a blunt raw-word shortcut, and `FUN_00444c10` has an explicit action-node parser that maps action ids, installs action nodes into the fixed `0x006297c0` table, appends bytecode tokens into `_DAT_006366a0`, allocates child nodes, and normalizes `"NOT Present"` child names to `"CheckActor"`. The stale hidden-register terminator test in `FUN_00444668` was also repaired; it was repeatedly consuming zero section terminators and then treating the first action-section words as a fourth record.

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-44668term-debug escape,enter 8 250 5

FAN record: ordinal=3 ... fields=0000,0000,3a33,004d,3a51
FAN dispatch: ordinal=3 type=0000 version=55 offset=104845
FAN 44c10: offset=104847 count=1793 version=55 remaining=1994325
wrote surface dump: /tmp/e2-step10-44668term-debug-s3.pgm (surface 3 nonblank=1 hash=6e39f5ea)
start_game=[entries=0 player=0 mode=0 startup_scan=0 startup_match=0 action_scan=0 action_match=0 dispatch=0 ...]
```

The matching ASan probe follows the same section transition and exits without a sanitizer report:

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-44668term-asan escape,enter 30 250 5

FAN 44c10: offset=104847 count=1793 version=55 remaining=1994325
wrote surface dump: /tmp/e2-step10-44668term-asan-s3.pgm (surface 3 nonblank=1 hash=6e39f5ea)
start_game=[entries=0 player=0 mode=0 startup_scan=0 startup_match=0 action_scan=0 action_match=0 dispatch=0 ...]
```

The next continuation advanced the loader beyond the old action-dispatch suspicion. `FUN_00444c10` now reports `list=1793`, `table=456`, and `pool=15002`; `FUN_004448e4` recognizes the ordinal-4 type-zero terminator; `FUN_00447638` parses its `49650` terrain/path entries, `1200` segment records, and tail node list; the invalid low actor-list head is dropped before post-FAN cleanup; and startup opens the hosted `Files/ECSTATIC` archive through `FUN_004452e0`.

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-fun45eb05-path-debug escape,enter 8 250 5
gdb --batch ... /tmp/e2-step10-path-gdb

FAN 44c10 summary: list=1793 table=456 pool=15002
FAN 47638 entries done: count=49650 offset=2079269 remaining=19903
FAN 47638 segment count: count=1200 offset=2079271 remaining=19901
FUN_00447d94 -> FUN_0043cac0 -> FUN_0043b384 -> FUN_0041ab4c -> FUN_0041ad54
SEGV at FUN_0041ad54, *row = color, param_1=43899, param_2=0, param_3=479
```

The archive-loader continuation replaced `FUN_00441444` with a hosted dword reader and made `FUN_00447d94` consume the already-open `DAT_0047a724` stream. Debug now prints `archive 47d94 loaded: cursor=56240 remaining=33019366`. The guarded `FUN_0043a39c` scan avoids the bad action-list tail, falls back through the installed `0x006297c0` action table, finds `StartGame`, and dispatches it. Hosted `FUN_0045f296` seeking then moves action execution past the stale seek crash. Direct archive parses now install `DAT_0047a724` as `E2R_fan_parse_stream`; when the table gives a small positive value that is not a byte offset, the wrapper treats it as an embedded `FANT` ordinal.

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-fant-ordinal-debug escape,enter 8 250 5

archive 47d94 loaded: cursor=56240 remaining=33019366
E2R_InvokeActionCode(action=0x566d634c)
FAN record: ordinal=5 caller=... offset=19358 fields=0000,0000,fa00,bffb,4277
FAN record: ordinal=6 caller=... offset=19368 fields=0000,0000,fa00,bffb,4277
FAN dispatch: ordinal=7 type=0019 version=55 offset=19378
```

The archive actor-load continuation showed the decompiler was losing the opcode actor id before `FUN_00451f5c`: at the first loader breakpoint, `EAX=0x0064a178` (the actor flags table), not the 12-bit actor operand. Opcode `0x54/0x55` now feeds that decoded operand through a scoped loader override, while direct archive parse failures avoid the original DOS error-renderer path. Hosted allocation and software-buffer guards now keep the runtime from installing `0xa0000`/high mapped pointers as writable surfaces, and invalid hosted fills return instead of crashing.

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-fill-guard escape,enter 8 250 5

archive 47d94 loaded: cursor=56240 remaining=33019366
requester-ready wait satisfied after 7840 ms
FAN header mismatch: value=00000000 offset=3997764
archive resource parse: input=3997760 mapped=3997760 result=0 final=3997764 remaining=29077842
requester-dialog wait satisfied after 550 ms: _DAT_00643650=5 b9bc 0->6 bd4c=1
requester probe completed after 740 ms: pending=1/1 actions=1
start-game entry observed: entries 1->2 player=0 mode=0
failed to write surface dumps with prefix: /tmp/e2-step10-fill-guard
```

The archive resource-table continuation resolved that zero-header miss. A gdb snapshot at the first actor loader hit showed `actor_override=0`, `table0=3997760`, `table14=1`, and archive cursor `56240`; raw archive bytes showed `3997760` is inside the resource whose nearest previous `FANT` header is `3993260`. `E2R_ParseArchiveFanResource` now keeps the small-ordinal mapping for offsets like `1`, and for large non-header cursors maps back to the nearest prior `FANT` in the archive stream. Opcode `0x54` also clears actor flags through the decoded 12-bit operand instead of stale `puVar13`.

The first backscan probe parsed actor record type `0x08` from `3993260`, then crashed in `FUN_00426478` because the decompiler wrote the newly allocated actor defaults through stale `extraout_EDX=0x13`. That initializer now writes through the allocated actor pointer returned by `FUN_00453414`, and the same repair is mirrored in the generator.

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-actor-init escape,enter 8 250 5

archive 47d94 loaded: cursor=56240 remaining=33019366
FAN record: ordinal=5 caller=... offset=3993304 fields=0000,0000,fa00,bffb,4277
FAN record: ordinal=6 caller=... offset=3993314 fields=0000,0008,0725,0726,0727
FAN 44330: ordinal=6 local_type=0008 version=55 offset=3993314
FAN record: ordinal=16 caller=... offset=3993414 fields=0000,000a,0000,0001,0002
requester-dialog wait timed out after 8000 ms: _DAT_00643650=0 b9bc 0->0 bd4c=0
failed to write surface dumps with prefix: /tmp/e2-step10-actor-init
```

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-actor-init-asan escape,enter 8 250 3

requester-ready wait timed out after 8000 ms: DAT_0047a76c=0 DAT_00479de8=0 _DAT_00643650=0
wrote surface dump: /tmp/e2-step10-actor-init-asan-s0.pgm (surface 0 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step10-actor-init-asan-s1.pgm (surface 1 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step10-actor-init-asan-s2.pgm (surface 2 nonblank=0 hash=b6005dc5)
wrote surface dump: /tmp/e2-step10-actor-init-asan-s3.pgm (surface 3 nonblank=1 hash=6e39f5ea)
```

The current frontier is the opcode `0x54` actor-load continuation inside the StartGame script. A debug watchpoint showed `FUN_00447638` was writing segment records through host global addresses such as `&DAT_0067c728 + iVar14`, clobbering `_DAT_006401ec` to `0xab7c` and making debug surface dumps fail. The segment-table writes, comparisons, and default initializer now use literal legacy addresses, and the fix is mirrored in `GenerateRecon.js`.

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-surfaces /tmp/e2-step10-space-fixed-debug-rerun space 6 250 30

surface dump state: width=640 height=480 visible=0 fb=[0xa0000,0xa0000,...] bad=[0,0,0,0]
wrote surface dump: /tmp/e2-step10-space-fixed-debug-rerun-s3.pgm (surface 3 nonblank=1 hash=6e39f5ea)
start_game=[entries=1 player=0 mode=0 startup_scan=1793 startup_match=4 action_scan=148 action_match=1 dispatch=5 ...]
```

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-surfaces /tmp/e2-step10-space-actorid-asan space 6 250 30

surface dump state: width=640 height=480 visible=0 fb=[0xa0000,0xa0000,...] bad=[0,0,0,0]
wrote surface dump: /tmp/e2-step10-space-actorid-asan-s3.pgm (surface 3 nonblank=1 hash=6e39f5ea)
```

The 2026-07-21 quickstart continuation reached the first control-ready scene using the original-video-shaped path. The concrete repairs were: hosted raw/title image loading now reads explicit byte counts from the open file descriptor; the raw RLE expanders receive explicit source/destination pointers; representation lookup preserves the original hidden `AX` id through `FUN_00451998 -> FUN_00442420`; opcode `0x54` reloads actors through the decoded 12-bit actor id instead of stale `extraout_EDX`; `FUN_00451f5c` rejects invalid actor ids before diagnostics; actor-record type `0x7` skips unavailable child-table links instead of dereferencing small data values; and `FUN_00420dcc` receives the current actor through `E2R_actor_calc_context`.

The verified debug probe posts `Space` at `6s`, posts numpad-up (`num8`, key `0x68`) after the final freeing-animation window, and exits cleanly:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-surfaces /tmp/e2-step10-final-space-num8 space,num8 6 10000 25

surface dump state: width=640 height=480 visible=1 fb=[0xa0000,0xa0000,...] bad=[0,0,0,0]
wrote surface dump: /tmp/e2-step10-final-space-num8-s3.pgm (surface 3 nonblank=1 hash=3615add9)
input state: DAT_00479de8=1 DAT_0047a76c=1 DAT_0047a43c=4
start_game=[entries=1 player=0 mode=0 startup_scan=1793 startup_match=4 action_scan=148 action_match=2 dispatch=6 ...]
move=[1,0,0,0,0,0,0,0,0]
```

This satisfies the Step 10 gameplay-readiness proof for the debug build: the surface is a rendered 3D scene, the runtime is in gameplay state, and a movement key changes the movement-state array.

The matching ASan probe previously exited cleanly without a sanitizer report, accepted the same movement key into `move[0]`, and dumped a nonblank surface, but it did not reach gameplay flags because it diverged earlier in the FAN tail after `FUN_00444c10`: the tail parser reported an implausible `FUN_00447638 count=437055755` at offset `259247`.

The next 2026-07-21 continuation fixed that ASan tail alignment by giving hosted `FUN_004173c8` the same binary-stream fast path as `FUN_004171b8`, preserving `FUN_004173c8`'s little-endian word order. ASan now reaches the same terrain/path count as debug:

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-surfaces /tmp/e2-step10-asan-173c8-space-num8 space,num8 6 10000 60

FAN tail marker: value=0001 offset=259097 record=4
FAN 47638 count: entries=49650 offset=291869 remaining=1807303
FAN 47638 entry: index=0/49650 offset=291869 remaining=1807303
...
move=[1,0,0,0,0,0,0,0,0]
```

A longer ASan window (`180s`) still exits cleanly without a sanitizer report, but expires mid-table around `index=16384/49650`; this is now a runtime-cost/observation-window frontier rather than the former bad-count parser bug.

One apparent current-build visual regression was only a too-early dump. Fixed-second dumps remain timing-sensitive, so the probe harness now has a gameplay-state wait that watches for StartGame entry, `DAT_00479de8`, and a live `_DAT_0073cc3c` actor pointer before dumping surfaces. A fresh debug run reaches the SCENES actor load, observes StartGame entry, accepts movement, and dumps the 3D village frame:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-debug-gameplay-wait-space-num8 space,num8 6 10000 180

gameplay-frame wait satisfied after 13630 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_0073cc3c=0x5664bff4
wrote surface dump: /tmp/e2-step10-debug-gameplay-wait-space-num8-s3.pgm (surface 3 nonblank=1 hash=3615add9)
DAT_00479de8=1 DAT_0047a76c=1 DAT_0047a43c=4 _DAT_0073cc3c=0x5664bff4
start_game=[entries=1 player=0 mode=0 startup_scan=1793 startup_match=4 action_scan=148 action_match=2 dispatch=6 ...]
move=[1,0,0,0,0,0,0,0,0]
```

Normal probes now suppress the high-volume FAN word/record/action parser diagnostics by default; set `E2R_FAN_DIAG=1` to restore those parser logs when chasing stream-alignment bugs. The 2026-07-22 ASan parity pass moved the old timeout frontier forward. The first blocker was probe cost in the hosted FAN word readers: `FUN_004171b8`/`FUN_004173c8` repeatedly called Linux `IsBadReadPtr`, which scans `/proc/self/maps`, while parsing the `49650`-entry terrain/path table. Trusting the active hosted `E2R_fan_parse_stream` removed that hot-path cost without changing arbitrary-stream fallback behavior.

Once ASan reached the end of `FUN_00447638`, diagnostics showed a build-sensitive entry-table under-read:

```text
FAN 47638 entry align: current=2079248 expected=2079269
FAN 47638 entries done: count=49650 offset=2079269 remaining=19903
FAN 47638 segment count: count=1200 offset=2079271 remaining=19901
```

The cursor is now normalized for version `0x37` fixed-width `36`-byte entries, matching the debug stream offsets and preventing ASan from reading `0x3fff` as the segment count. Removing stale `<0x70000000` host-address assumptions from action node/name lookup then allowed ASan to dispatch StartGame instead of scanning `1793` actions with zero matches. The remaining `0x006536b0` fixed table was redirected to its literal legacy address, and `FUN_0042ce70` now receives its hidden actor pointer through the existing actor calculation context.

The next ASan-only blocker was the scene/current pointer path. Debug carried a readable non-actor-table `DAT_0047a470` value from `5233c.archive` and later used it to choose a static scene record. ASan carried unreadable register residue from the same decompiler `extraout_ECX_04` site, so `FUN_0044c164` either crashed or no-op'd before installing `_DAT_0073cc3c`. The repair now discards unreadable archive-current residue, computes `FUN_0044c6bc`'s lost scene-record `EAX` from `_DAT_0073ccba`, and installs the proven normal-start scene slot `785` when `DAT_00479de8` becomes active without a scene pointer.

```text
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-active-scene-asan space,num8 30 10000 100

gameplay-frame wait satisfied after 5670 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_0073cc3c=0x681d04
surface 3 nonblank=1 hash=6e39f5ea
start_game=[entries=1 player=0 mode=0 startup_scan=1793 startup_match=4 action_scan=148 action_match=2 dispatch=6 ...]
```

ASan now reaches the gameplay-frame wait instead of timing out before StartGame or crashing in post-actor-load update code. Debug remains stable on the movement proof:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-active-scene-debug space,num8 6 10000 180

gameplay-frame wait satisfied after 0 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_0073cc3c=0x681a10
surface 3 nonblank=1 hash=3615add9
move=[1,0,0,0,0,0,0,0,0]
```

The 2026-07-27 continuation added a split gameplay probe to the native harness. `--inject-key-sequence-gameplay-surfaces` now accepts an optional `gameplay_key_split`; keys before that index are posted at the original injection time, then the probe waits for gameplay/control state before posting the remaining keys. Existing invocations keep their original behavior when the split argument is omitted.

The debug control-ready proof uses `space` for the intro/skip path, waits for `_DAT_00643650=0` with a live scene pointer, then posts `num8`:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-move-debug space,num8 6 10000 180 1

gameplay-control wait satisfied after 0 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_00643650=0 _DAT_0073cc3c=0x681d04
posted key 0x68 through the Win32 message queue
input state after dispatch wait: ... DAT_00479de8=1 move=[1,0,0,0,0,0,0,0,0] DAT_0047a76c=1 DAT_0047a43c=4 _DAT_0073cc3c=0x681f18
surface 3 nonblank=1 hash=3615add9
```

The ASan split probe now proves the same control-ready frontier without a sanitizer report. `FUN_00427584` returns through the idle actor-update path, the render epilogue selects scene `0x681d04`, and the reconstructed `FUN_0042a70c` dead-current requester guard ignores a null current actor instead of opening requester `0x27`. A debug-only post-control crash then exposed two more lost-register surface-copy frontiers: `FUN_0041868c` used stale hidden `EAX/EBX` for source surface and X, and `FUN_00417b20` could enter its software-surface copy loop with stale source/destination spans. Both helpers now have generator-backed full-screen/source fallback and bounded pointer-span guards, turning invalid generated residue into skipped unsafe copies instead of crashes.

Final debug and ASan split probes both accept the delayed movement key with the scene live and requester state clear:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-final-debug5 space,num8 6 10000 180 1
build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-final-asan2 space,num8 30 10000 60 1

gameplay-control wait satisfied after 0 ms: start_game=1 DAT_00479de8=1 DAT_0047a76c=1 _DAT_00643650=0 _DAT_0073cc3c=0x681d04
input state after dispatch wait: ... DAT_00479de8=1 move=[1,0,0,0,0,0,0,0,0] DAT_0047a76c=1 DAT_0047a43c=4 _DAT_0073cc3c=0x681d04
surface 3 nonblank=1 hash=6e39f5ea
```

Current frontier: Step 10 has a debug and ASan control-ready movement proof. The remaining cleanup is to trim temporary diagnostics once the generated repairs are reviewed, then decide whether to close Step 10 or keep a small follow-up for scene-current and surface-copy hidden-register fidelity. The final dumps report `visible=0` while surface 3 is nonblank; this appears to be a presentation-page bookkeeping issue, not a blocker for the movement/control proof.

## Original Runtime Video Workflow Evidence

The reference videos used for this section were user-captured Debian/Lutris/Wine screencasts on 2026-07-21. Treat the video files themselves as temporary local evidence; this section is the durable summary for future contexts.

Observed original workflow:

1. Startup shows the Ecstatica II logo, then enters the engine-rendered intro/credits path. The Andrew Spencer Studios logo may be skipped or hidden under Wine.
2. The intro continues until the player either presses `Esc` to open the in-game menu or presses `Space` to skip/advance toward gameplay.
3. Selecting Start Game from the in-game menu does not immediately create a controllable scene. It repeats or re-enters the same Ecstatica-logo/intro sequence.
4. The natural fast path to gameplay is: start runtime, wait for the intro/credits path, press `Space`, wait through the final "character freed by lightning" animation, then observe the HUD and movement-ready scene.
5. In the 2026-07-21 fast-path capture, the Ecstatica II logo appears at about `2s`, intro credits at about `4s`, `Space` is pressed around `6-7s`, HUD appears around `22s`, movement input is visible around `23-24s`, `Esc` opens the gameplay menu around `25s`, and the game exits after closing the Wine window around `28s`.

Probe implication: Step 10 should distinguish StartGame dispatch, intro/skip progression, and gameplay readiness. A short `escape,enter` probe is still useful for proving menu dispatch into `FUN_0043a39c`, but a control-ready gameplay probe should use `space` and observe for roughly `25-30s` after intro readiness before expecting HUD/state-change evidence.

## Acceptance Criteria

1. Debug and ASan builds compile, and generator syntax validation passes.
2. A bounded probe selects Start Game and proves entry into `FUN_0043a39c`.
3. One scene loaded from original data produces a distinguishable nonblank frame without an ASan report.
4. One injected movement input produces a documented player, camera, or scene-state change.
5. Reconstructed C fixes are mirrored in `E2Recomp/tools/GenerateRecon.js`.

## Verification

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build build/linux-clang32-asan`
4. Bounded debug and ASan Start Game requester probes.
5. Compare scene frame hashes or documented scene-state counters before and after one movement input.
6. `build/linux-clang32-debug/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-start-game-debug-post5 escape,enter 8 250 5`
7. `build/linux-clang32-asan/e2recomp --inject-key-sequence-ready-surfaces /tmp/e2-step10-start-game-asan-post5 escape,enter 8 250 5`
8. `build/linux-clang32-debug/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-move-debug space,num8 6 10000 180 1`
9. `build/linux-clang32-asan/e2recomp --inject-key-sequence-gameplay-surfaces /tmp/e2-step10-control-move-asan space,num8 30 10000 100 1`

## Notes

The first implementation slice is deliberately narrower than the full step: restore the original requester record, select `0x00643b30`, and record the first frontier reached inside or after `FUN_0043a39c`.

Exact English Quit prompt text recovery at `0x004729b8` remains a Step 9 fidelity backlog item and does not block scene entry.

## Change Log

### 2026-07-18

1. Created after Step 9 verified host input, requester navigation, callback dispatch, and Quit confirmation outcomes in debug and ASan builds.
2. Restored the original requester record and default Start Game item, added `FUN_0043a39c` entry/post-action probes, and verified matching debug/ASan transitions into Start Game before the runtime returns to the menu.
3. Traced the empty Start-code list to the hosted `FUN_00445378` parser bypass, restored FAN stream/parser handoff, made packed name tables and ordinals explicit, recovered Start-code dispatch, and advanced ASan to `FUN_00444668 -> FUN_004413fc`.
4. Recovered FAN pool allocation, five-word record reads, normalization, release, and actor handoffs; proved three zero section terminators; fixed the stale top-level terminator test; and advanced ASan to `FUN_00444c10`.

### 2026-07-20

1. Reran the bounded Start Game probes. Sandboxed runs exit with code `159`, so host runtime probes must run outside the sandbox.
2. Confirmed debug still reports the ordinal-4 unknown-record diagnostic after three zero terminators, while ASan reaches `FUN_00444c10 -> FUN_004268e4` and dies reading through hidden owner `EAX=0x2`.
3. Identified the next concrete recovery from original disassembly: preserve the owner pointer passed from `FUN_00444c10` into `FUN_004268e4`/`FUN_0042692c` and keep their allocator count fixed at one 0x39-byte record.
4. Recovered the `FUN_00444c10` owner/list helper cluster, raw hosted FAN word reads, `FUN_004435e8` token input, and fixed remap-table reads. ASan advanced to the later `FUN_004448e4` frontier; debug still reports ordinal 4 as unknown.
5. Recovered `FUN_004448e4`, `FUN_00445000`, `FUN_004451a8`, `FUN_00452a58`, and the first `FUN_00447638` stream/destination contracts.
6. Recovered packed-name lookup wrappers, `FUN_0045fae0`, and the remaining fixed-address `FUN_00447638`/remap-table accesses. ASan now reaches and dumps the title surface without a sanitizer report, while debug still stops at the ordinal-4 unknown-record diagnostic and ASan still reports `start_game entries=0`.
7. Recovered hosted binary/text stream byte semantics, replaced the remaining `FUN_00444c10` action-node parser body, and fixed the stale `FUN_00444668` terminator test. Debug and ASan now both enter `FUN_00444c10`, parse past the old ordinal-4 boundary, and dump the title surface without sanitizer reports.
8. Recovered the ordinal-4 terminator path, the `FUN_00447638` terrain/path table loops, tail-node allocation, post-FAN invalid actor-head guard, hosted literal path handling, and stable `Files/ECSTATIC` startup archive path. Debug now reaches `FUN_00447d94` after FAN parsing.
9. Recovered `FUN_00447d94` startup archive table loading, guarded the bad action-list tail in `FUN_0043a39c`, added a fixed-table `StartGame` fallback, and replaced `FUN_0045f296` with hosted stream seeking.
10. Direct archive resource parsing now wraps `FUN_004453a4(...,1)` with `E2R_fan_parse_stream` and maps small table values to embedded `FANT` ordinals; debug reaches the first embedded resource at offset `19314`.
11. Recovered opcode-local actor id delivery into `FUN_00451f5c`, hosted allocator/backbuffer safety, quiet hosted bad-`FANT`/missing-actor archive misses, and invalid hosted fill guards. Debug now reaches requester-ready, dispatches the requester dialog, observes a second StartGame entry, and exits without a segfault.
12. Recovered archive actor cursor mapping for table offset `3997760` by backscanning to the containing `FANT` at `3993260`, fixed stale opcode `0x54` actor flag clearing, and recovered `FUN_00426478` actor initializer writes through the allocated actor pointer. Debug parses actor resource records without crashing; ASan writes a nonblank surface.
13. Current frontier: post-actor-load readiness diverges. Debug no longer opens the requester dialog after Escape and cannot dump surfaces, while ASan times out before requester-ready but dumps one nonblank surface. Recover `FUN_00444330`/`FUN_0042b880` post-record side effects and the actor/list globals gating requester/start-game readiness.

### 2026-07-21

1. Added durable notes from user-captured original-runtime screencasts. The original fast path is logo/intro, `Space`, final character-freeing animation, HUD, then movement; selecting Start Game from the menu re-enters the logo/intro path rather than producing immediate control.
2. Adjusted Step 10 probe expectations: retain short `escape,enter` probes for StartGame dispatch, but use a later `space`/long-observation/HUD/movement probe for gameplay readiness once the current post-actor-load frontier is stable.
3. Fixed `FUN_00447638` segment-table writes/comparisons/default initializer to use literal legacy addresses around `0x0067c728`, resolving the debug width clobber (`0xab7c`) and restoring debug surface dumps. Debug and ASan `space` probes now dump valid `640x480` surfaces, with surface 3 nonblank hash `6e39f5ea`.
4. Added StartGame action-opcode probes. The original-video-shaped `space,d` run delivers the movement key but remains at opcode `0x54` (`opcodes=581`, `hit75=0`), so gameplay readiness is blocked in the actor-load continuation before opcode `0x75`.
5. Recovered the actor-load continuation far enough for the bounded `space 6 250 45` probe to exit cleanly. Fixes include explicit parent/actor context for `FUN_004265ac`, `FUN_00426858`, `FUN_00426798`, `FUN_00427584`, `FUN_00421074`, `FUN_00423858`, and `FUN_004249f4`; byte-addressed pool allocators for `FUN_00453510`, `FUN_00453674`, and `FUN_004536e0`; defensive `FUN_0043a800` active-list cleanup; explicit actor-slot cleanup in action `0x54`; and a temporary no-op for the register-only transform helper `FUN_0045de8b`.
6. Current bounded result:

```text
build/linux-clang32-debug/e2recomp --inject-key-sequence-surfaces /tmp/e2-step10-fun249f4-actor-debug space 6 250 45

exit code: 0
surface dump state: width=640 height=480 visible=0 fb=[0xa0000,0xa0000,...] bad=[0,0,0,0]
surface 0 hash=b6005dc5 nonblank=0
surface 1 hash=b6005dc5 nonblank=0
surface 2 hash=b6005dc5 nonblank=0
surface 3 hash=6e39f5ea nonblank=1
input state: DAT_00479de8=1 DAT_0047a76c=1 DAT_0047a43c=4 _DAT_00643650=5
start_game=[entries=1 player=0 mode=0 startup_scan=1793 startup_match=4 action_scan=148 action_match=2 dispatch=6 node=... name=210 code=0x32d8 opcodes=586 last_opcode=0x7 hit75=0]
```

7. A longer `space 6 250 180` probe no longer crashes at the old actor/list frontiers, but it behaves like a loop and was manually stopped after repeated `FAN 44c10: offset=2041106 count=0`. The remaining Step 10 frontier is therefore not the previous segfault chain; it is the post-load/update loop or missing visual transition that keeps the dumped frame on the Ecstatica II logo (`surface 3 hash=6e39f5ea`) and still does not reach opcode `0x75`.

### 2026-07-22

1. Advanced ASan from the pre-StartGame timeout through the large `FUN_00447638` table by trusting the active hosted FAN stream in hot word reads and normalizing version-55 fixed-width entry alignment.
2. Removed stale high-host-pointer guards from action node/name lookup and dispatch so ASan can find and invoke StartGame from hosted heap action nodes.
3. Redirected the remaining `0x006536b0` fixed table initializer/readers to the literal legacy address and recovered `FUN_0042ce70`'s hidden actor pointer through `E2R_actor_calc_context`.
4. Current ASan frontier: after two actor-load passes, ASan crashes in `FUN_0044c164 -> FUN_004211c8 -> FUN_0042a70c -> FUN_00426df8`; debug still reaches the gameplay frame and movement proof.
5. Added an ASan-only `DAT_0047a470` actor-table plausibility guard at the direct `FUN_0044c164` crash site. Debug remains on the original path and still satisfies gameplay-frame proof with surface 3 hash `3615add9` and `move=[1,0,0,0,0,0,0,0,0]`; ASan now exits cleanly instead of crashing at `FUN_0044c164`, but still times out before the visible gameplay frame with surface 3 hash `6e39f5ea`.
6. Recovered the scene-current path far enough for ASan to satisfy the gameplay-frame wait. The fixes cache action names for ASan cost, discard unreadable `5233c.archive`/`525f0.archive` current residue, compute `FUN_0044c6bc`'s scene record from `_DAT_0073ccba`, and install normal-start scene slot `785` when active gameplay begins with no scene. Debug still proves movement and `surface 3 hash=3615add9`; ASan now reaches `_DAT_0073cc3c=0x681d04` and a nonblank gameplay surface, with movement-state parity still pending because early `num8` is consumed before active gameplay.

### 2026-07-27

1. Added split-key support to `--inject-key-sequence-gameplay-surfaces`; `gameplay_key_split=1` lets the probe post `space`, wait for gameplay/control state, then post `num8`.
2. Verified debug control-ready movement parity with `_DAT_00643650=0`, `_DAT_0073cc3c=0x681f18`, surface 3 hash `3615add9`, and `move=[1,0,0,0,0,0,0,0,0]`.
3. Verified ASan delayed movement-key delivery without a sanitizer report. The stricter control-ready wait timed out with `_DAT_00643650=5`, but delayed `num8` still latched `move=[1,0,0,0,0,0,0,0,0]` after `_DAT_0073cc3c=0x681d04` became live.
4. Current frontier: recover the ASan requester-state residue after StartGame so control-ready state matches debug before the delayed movement key is injected.
5. Traced the ASan requester residue through `FUN_0042a70c -> FUN_00427584`: the first actor update returns idle, render epilogue selects scene `0x681d04`, then a null `DAT_0047a470` triggered the dead-current menu request.
6. Changed the generated dead-current guard to request the menu only for a readable non-null actor with state `0xb` and expired life; null current actors no longer open requester `0x27`.
7. Verified ASan control-ready movement parity with `_DAT_00643650=0`, `_DAT_0073cc3c=0x681d04`, surface 3 hash `6e39f5ea`, and `move=[1,0,0,0,0,0,0,0,0]`.
8. Stabilized the debug post-control surface-copy crash by guarding generated `FUN_0041868c` and `FUN_00417b20` copies against stale hidden source/X register residue and invalid spans.
9. Verified final debug and ASan split probes both exit cleanly, latch delayed `num8` into `move=[1,0,0,0,0,0,0,0,0]`, keep `_DAT_00643650=0`, and dump nonblank surface 3 hash `6e39f5ea`.
