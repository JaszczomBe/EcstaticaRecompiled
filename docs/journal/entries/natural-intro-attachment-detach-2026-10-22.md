# Natural Intro Attachment Detach — 2026-10-22

The user reports the same `FUN_0042db74:25297` crash after the recorder work and
asks to reproduce it by starting normally and waiting through the intros.
Recording/replay is not used in this continuation. All runs explicitly set
`E2R_RECORD=off`; the natural-intro checks inject no input or game-state edits.

## Reproduction And Original Contract

The entry-state Debug executable reproduces the reported stack after a normal
desktop launch with the F5 environment:

`FUN_0042db74 ← FUN_0042b880 ← FUN_0042b338 ← FUN_0042ae80 ← FUN_00427584 ← FUN_0042a70c`.

GDB identifies event node `0x97c522`, owner `0xaa893c`, action `0xac284c` and **no
attached actor** at node `+0x13a`. Original code returns immediately in that case.
The C instead receives the action pointer and dereferences an uninitialized
`in_EAX`. Evidence: `/tmp/e2-detach-natural-before.log`.

Original `E2WIN95.EXE` disassembly establishes:

- `0x42c42b..0x42c43a` masks action flag 2 into EDX and passes the selected event
  node from ESI in EAX. The event caller now supplies `unaff_ESI` as that node.
- `0x42db74..0x42db84` retains the node in EBX and placement mode in ESI, returning
  when node `+0x13a` is zero.
- `0x42db8a..0x42dbb9` rebuilds reverse links, poses the node owner and updates the
  attached actor root through that node. C now retains those identities; the
  existing pose-context bridge is saved/restored around the owner pose.
- `0x42dbc2..0x42dc21` queries the attached actor's position with actor argument
  zero. When placement is requested, floor-minus-30 within 64 units updates Y;
  otherwise the owner position is copied and Y reduced by 30. Pitch and roll
  clear in this branch only.
- `0x42dc28..0x42dc92` clears both attachment links, then adjusts owner class
  3/4/5 to 0/1/2 and refreshes the HUD only for the current actor in gameplay.

The entire detach helper and its single event caller are recovered together.
There is no speculative null guard, skipped attachment operation, forced Joe
position or recorder change. The generated C hand edit has an anchored generator
mirror. Syntax/regeneration reproduce the hand edit exactly; generated headers,
globals and name mappings have no drift.

## Verification

`scripts/check-e2-attachment-detach.py EXE [--asan]` passes **16,384** original-x86
helper cases and **65,536** original caller/flag cases, normally and under ASan.
The helper fixture compares complete memory changes and ordered pose/root/floor/
copy/HUD arguments, including empty attachments, reverse-chain lengths, floor
threshold boundaries, preserved-placement mode and owner-class/HUD conditions.
Named dependencies are intercepted; the existing spawn-action ASan fixture also
passes its actual endpoint/IK/attached-root pose comparisons.

The repaired Debug desktop run finishes both intros naturally and observes Joe
released at 58.822 seconds. That run subsequently receives physical arrow input
and hits a distinct scene-deactivation/error-reporting path. It is not evidence
of idle survival; the input log is retained in `/tmp/e2-detach-natural-debug.log`.

A repeat uses dummy SDL solely to isolate the ordinary `--run-recon` route from
desktop input. It finishes both intros naturally at **57.414 seconds** and
survives another **15.012 seconds**:

- Camera 175; actor-table ID 0 remains Joe at `(9988,3328,-17408)`.
- Script wait remains zero, state advances to control-ready state 4, and the
  simulation counter advances from 11,643 to 14,685.
- All **four** native detach calls select the same empty-attachment node and
  return correctly. No input is delivered, no recording is created and no
  debugger state writes are used.

Evidence: `/tmp/e2-detach-natural-debug-isolated.json` and its `.log`.
Read-only GDB observers and launch scripts are retained in
`.tmp/attachment-detach/`. The native desktop and isolated runs use the normal F5
flags; neither skips the horseback or pedestal sequence.

All four SDL/X11 Debug/ASan builds pass without warnings. Existing runtime
regressions and all eight Debug/ASan control matrix rows pass:
`/tmp/e2-detach-runtime-check.log`, `/tmp/e2-detach-controls-check.log`.
Focused logs: `/tmp/e2-attachment-detach{,-asan}-check.log` and
`/tmp/e2-detach-spawn-action-asan.log`.

## Separate Frontier And Worktree

Full experimental ASan remains unaccepted. Its natural desktop run passes the
reported detach failure, then faults in `FUN_0044f508 ← FUN_0044f310 ← FUN_00426ca4
← FUN_0044e238` during automatic actor deactivation, before the observation gate.
The desktop Debug run with arrow input reaches the related scene-deactivation
path through `FUN_0044d3e8`, then `FUN_00414e68 → FUN_0043cac0`. Those script
callback/error inputs are not changed or hidden by this patch. Evidence:
`/tmp/e2-detach-natural-{asan,debug}.log`.

Workshop walking re-entry, sword pickup and full experimental ASan remain
separate gameplay work. The preserved older replay bundle still pins the
pre-detach-fix executable and remains historical crash evidence.

The user staged the previous recorder and NPC-input work before this turn.
That staged patch remains byte-for-byte unchanged, SHA-256
`610c18a0a76c21f71cd20ff1d57af4348da5747c6b6aa464bc4e57fb58193253`.
This detach repair, fixture and documentation remain unstaged. No commit.
