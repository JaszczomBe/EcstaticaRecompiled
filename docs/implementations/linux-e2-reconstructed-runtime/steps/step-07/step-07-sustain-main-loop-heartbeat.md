# Sustain Main Loop Heartbeat

Status: completed
Parent Implementation: [Run Reconstructed E2 On Linux](../../linux-e2-reconstructed-runtime.md)
Last Updated: 2026-07-16

## Goal

Advance from the first post-step-6 ASan frontier to a repeatable main-loop heartbeat that survives several consecutive loop-adjacent calls.

## Why This Step Exists

Step 6 cleared the post-main-loop config/file frontier and verified the hosted `FUN_00453920` no-op. The next bounded ASan run now stops in `FUN_0045fae0`, called from `FUN_00455940` while `FUN_00415d40` handles loop-adjacent state after `FUN_00426df8`.

## Scope

1. Recover the missing input pointer or call convention around `FUN_0045fae0` and `FUN_00455940`.
2. Fix only the narrow blocker needed to continue past the current table/string comparison frontier.
3. Mirror generated C repairs in `E2Recomp/tools/GenerateRecon.js` if reconstructed C changes are made.
4. Record the next stable runtime frontier or heartbeat evidence in the runtime journal.

## Out Of Scope

1. Full menu/dialog semantics.
2. Full input, rendering, or audio correctness.
3. Save-game reconstruction beyond preserving the current `FUN_00453920` no-op until that path is deliberately revisited.

## Usage Budget

Respect the active implementation budget from the parent implementation: no more than 5% weekly usage burn per day unless the user explicitly approves continuing.

## Starting Frontier

Bounded ASan run from `build/linux-clang32-asan` on 2026-07-16:

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

The first suspect was a lost incoming pointer for the strcmp-like `FUN_0045fae0` helper. `FUN_00455940` passes table entries beginning at `0x00ac4cad` as `param_2`; `FUN_0045fae0` then dereferences its local `in_EAX` pseudo-register.

This frontier has been cleared for the current `FUN_00455e84` path. Original disassembly shows `FUN_00455940` receives the target icon/action name in `EAX`, saves it in `ESI`, iterates 25 table entries at `0x00ac4cad`, and calls `FUN_0045fae0` with `EAX=target` and `EDX=current entry`.

## Cleared Frontier

After recovering `FUN_00455e84` and redirecting `&DAT_0047a29c` to fixed address `0x0047a29c`, the next bounded ASan frontier was:

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

This was not a `FUN_0043cac0` text-rendering bug on the current path. Original disassembly showed the immediate caller in `FUN_00415d40` should load requester id `0x27` or `0x28` in `EAX` before calling `FUN_0043ce58`; generated C passed the unrelated `5` that original code stores in `_DAT_00643650`. Recovering that requester id and restoring `FUN_0043ce58`'s incoming `EAX` from `param_1` cleared the fatal `Bad request number` path.

## Result

Step 7 reached a sustained main-loop heartbeat. A bounded 30-second ASan run and a longer 90-second ASan run both exited by timeout with no sanitizer report:

```text
timeout --preserve-status 90s ./e2recomp --run-recon
Ecstatica II data: /home/rgrabowski/Work/EcstaticaRecompiled/build/linux-clang32-asan/Ecstatica2
exit code 143
```

## Acceptance Criteria

1. Runtime no longer crashes at `E2Recomp_recon.c:54618` in `FUN_0045fae0`.
2. Execution either survives several main-loop-adjacent calls or advances to a new documented frontier.
3. Debug and ASan builds compile.
4. Any reconstructed C hand fix is mirrored in `E2Recomp/tools/GenerateRecon.js`.

## Verification

1. `node --check E2Recomp/tools/GenerateRecon.js`
2. `cmake --build --preset linux-clang32-debug`
3. `cmake --build build/linux-clang32-asan`
4. Bounded ASan run from `build/linux-clang32-asan`: `timeout --preserve-status 30s ./e2recomp --run-recon`
5. Longer bounded ASan run from `build/linux-clang32-asan`: `timeout --preserve-status 90s ./e2recomp --run-recon`

## Change Log

### 2026-07-16

1. Created after step 6 verification exposed the `FUN_0045fae0` frontier.
2. Recovered the current `FUN_00455e84` icon-name clear sequence so the path no longer crashes in `FUN_0045fae0`.
3. Redirected `DAT_0047a29c` damage-rectangle count table indexing to fixed address `0x0047a29c`.
4. Recovered the loop-adjacent requester id handoff in `FUN_00415d40` and restored `FUN_0043ce58`'s lost incoming `EAX` from `param_1`.
5. Verified the ASan runtime survives 30-second and 90-second bounded runs without a sanitizer crash.
