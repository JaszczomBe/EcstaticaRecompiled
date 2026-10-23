# Native F5 File-Open Heap Corruption — 2026-10-21

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Report And Reproduction

After the logger/configuration continuation, the user's actual F5 launch aborts during startup, following both logos and `E2R open failed: path=rb`, with **`malloc(): unaligned tcache chunk detected`**. The earlier dummy-SDL startup/presentation and debugger smoke tests did not establish this native startup path.

The exact Debug executable, `--run-recon` arguments, build-directory cwd and environment from `.vscode/launch.json` reproduce the failure on the current Wayland desktop. SDL detects the damaged allocator while creating its window framebuffer/renderer, through `SDL_GetWindowSurface → SDL_CreateWindowTexture → SDL_CreateRenderer → malloc`. That is the detecting allocation, not the corrupting writer. The native ASan build initially survives because its allocation layout differs; it does not reproduce the Debug tcache failure.

GDB first identifies a malformed small-bin free-list link after the first logo. A watchpoint armed on the actual current tcache head then catches a write of **1** in `FUN_004605bc`, called by `FUN_0045e5b8 → FUN_0045e594 → FUN_00414998`. The pointer is a freed native heap block accepted by the old writable-memory guard. Evidence: `/tmp/e2-f5-tcache-stages.log` and `/tmp/e2-f5-writer.log`.

## Original Contract And Repair

Original `0x4605bc..0x4605e7` receives the access mode in EAX and two live output pointers: EDX for the desired Win32 access mask, EBX for the CRT attributes/mode word. Mode 2 writes `0xc0000000/0x80`; mode 1 writes `0x40000000/0x80`; other values write `0x80000000/1`.

The original caller at `0x45e5e2..0x45e5f3` supplies stack destinations `ESP+4` and `ESP+8`. In reconstructed `FUN_0045e5b8` these are `local_20` and `local_1c`. The C helper retained the first output but dereferenced an uninitialized `unaff_EBX` for the second. Testing whether that address was writable did not establish ownership and permitted the heap corruption.

The helper now has an explicit third output argument, and its caller passes `&local_1c`. Both output writes retain the original values; no file open is skipped and no allocator behavior is changed. The generator mirrors the signature before prototype collection so the generated header also retains the third argument. Regeneration changes only the helper, its caller and its prototype: six insertions and 23 deletions across reconstructed C/header.

## Verification

`scripts/check-e2-file-open-mode.py EXE [--asan]` executes the original helper bytes and compares both output fields, aliasing and surrounding canaries against production C. All **360 cases** pass normally and under ASan. The fixture also requires the recovered caller's second output destination.

All four SDL/X11 Debug/ASan builds pass. Generator syntax and independent C/header/globals/names regeneration parity pass. The established runtime wrapper and all eight control-matrix rows pass against the repaired file-open path; their evidence prefixes are `/tmp/e2-f5-fixed-regression` and `/tmp/e2-f5-fixed-controls`.

The fixed Debug game survives 25 seconds on the real desktop under GDB. It then survives 25 seconds through the **installed VS Code `cppdbg` adapter**, using the resolved actual launch entry, with no stopped/failed event. The retained `scripts/probe-e2-vscode-launch.py` repeats this check on the native backend, recording incoming adapter protocol events, the launch parameters, bounded duration and any crash stack. It leaves the game command and gameplay state alone. The final Debug and ASan native adapter checks both pass 30 seconds, with no stopped/failed event; evidence is `/tmp/e2-f5-fixed-vscode-{debug,asan}*`.

The nonfatal `path=rb` diagnostic also appears in successful startup and is not removed by this repair. The captured invalid writer, rather than that nearby log message, establishes the reported heap-abort cause.

## Scope And Limits

The native adapter check launches the actual installed debugger and game configuration; it does not press the F5 button or change VS Code's active preset selection. Bounded startup survival does not establish complete manual exploration, workshop re-entry, sword pickup or full experimental sanitizer acceptance. The native probe uses the current desktop and can receive physical keyboard input while its window is open.

Automatic merge results remain byte-identical in the index. This repair, generator mirror, probes and documentation stay unstaged on `feature/logger`. No commits are made.
