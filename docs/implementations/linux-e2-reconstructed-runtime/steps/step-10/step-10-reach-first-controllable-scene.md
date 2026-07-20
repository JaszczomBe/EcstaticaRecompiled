# Reach First Controllable Scene

Status: active
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-20

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

The next implementation step is to recover the `FUN_00447d94` archive/scene-data loader handoff after `Files/ECSTATIC` opens. The immediate crash is a bad framebuffer fill rectangle flowing through `FUN_0043cac0`; verify whether `FUN_00447d94` is invoking the error/render path because hosted archive-table reads are still stale, then repair the first explicit bad read or stale register handoff. Keep the bounded FAN diagnostics until this scene/archive loader frontier is stable, then prune the noisy entry-loop logs.

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
9. Current frontier: `FUN_00447d94` enters `FUN_0043cac0 -> FUN_0043b384 -> FUN_0041ab4c -> FUN_0041ad54` and crashes writing a framebuffer fill row with bad rectangle state (`param_1=43899`, `param_2=0`, `param_3=479`).
