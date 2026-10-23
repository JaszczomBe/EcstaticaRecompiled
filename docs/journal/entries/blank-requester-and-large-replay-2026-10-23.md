# Blank requester, directional reaction and large replay — 2026-10-23

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user reported a blank OK-only message at camera 722. Clicking OK closed the
game. The F5 session `session_20261023_141553_315` records exit zero, completed
inspection and incomplete replay: the event file reached its 128 MiB cap at
14:17:42. Its 2,882,061 physical events and 4,544,966 checkpoint rows are preserved
with the matching binary in `/tmp/e2-blank-prompt-human-20261023`.

## What the tooling revealed

The pinned i386 reader rejected this large capture with `std::bad_alloc` before
gameplay. Keeping parsed CSV strings, raw files and logical events/snapshots at
once exhausted its address space. The revised reader visits one CSV row at a
time, releases checkpoint text after constructing expectations, and reserves
logical event storage once. The complete human input now validates and stops at
the requested first event, with measured peak child RSS 794,920 KiB. Strict
identity/checksum/sequence validation and incomplete-prefix rules remain active.
The ASan i386 reader also validates this capture, peaking at 1,668,324 KiB;
the remaining memory cost reinforces the need for eventual streaming storage.

Replay then exposes a native fault before the reported prompt, at sequence
971,335,150 after matching checkpoint 49 in `FUN_00427584`. Original
`0x42980e..0x42981e` copies eight integers from `0x427140`: **5, 8, 7, 6, 3, 0,
1, 2**. Reconstructed code copied eight integers from one generated scalar,
reading unrelated neighboring globals. A complete constant table restores that
original contract. The original-x86 branch fixture covers all 32,768 random
results, eight direction sectors and both postures: 524,288 cases pass normally
and under ASan. The repair is mirrored in `GenerateRecon.js`.

The repaired executable crosses that native fault but the old capture then
diverges at sequence 971,335,156: expected clock versus actual cursor_get. This
is not accepted replay reproduction of the screenshot or its terminating caller.
A scratch GDB experiment released only already-copied temporary parser rows in
the pinned image; it also encounters the earlier native fault. No game state,
checkpoint expectations or recorded input was patched to pass that frontier.

## User repeat and presentation/observation repairs

The user repeated the route in the repaired build and reports no OK prompt at
the same location. Inspection confirms camera 722 was reached twice. The new
`session_20261023_143834_521` exits zero with complete replay and inspection;
its files total about 16 MiB. It is preserved at `/tmp/e2-postfix-human-20261023`.
Three fresh exact replays of this new human recording complete successfully,
each matching all 120 checkpoints through sequence 2,064,043,107. That supports
the repaired route; it does not identify the old prompt's caller.

Empty/unreadable message lists now display readable error text and emit an Error
record with call-site evidence. The fallback preserves the caller's modal/exit
behavior. Requester ID is part of inspection, and a requester event samples state
before the blocking loop while requesting the next actual frame. F5 silently
observes message/fatal-requester entry and saves bounded stacks both in the
session and beside its workspace receipt. This evidence survives replay limits
and distinguishes a fatal caller with exit zero from ordinary completion.

Frequent action-event/completion traces move to `Runtime.Actor` Trace and stay in
Trace-level files, with console output opt-in through
`E2R_GAMEPLAY_CONSOLE_VERBOSE=1`. Recording-incomplete notices become warnings.
Replay files now allow 256 MiB each and bundle exports 768 MiB total. These are
additional headroom, not a duration guarantee. Compressed/streamed recording and
playback remain useful follow-up work because event/snapshot storage still grows.

## Verification

Generator regeneration reproduces the four reconstructed artifacts without drift.
SDL Debug/ASan builds and the established X11 runtime regressions pass. Direction
and empty-message fixtures pass normally and with ASan. Parser contracts cover
ordering, checksum/identity rejection, tail recovery and extra data after end;
lifecycle checks retain crash prefixes, source freezing and write-failure status.
Both native parser contract configurations pass. Developer-launch/logging checks
pass 31 cases in Debug and 31 in ASan, including quiet console defaults, verbose
opt-in, retained Trace file output and Warning severity for incomplete recording.
Fresh Debug and ASan menu recordings each pass three independent replays,
inspection-off replay and a debugger-pause replay. The F5 native fixture verifies
requester stacks alongside preserved SIGSEGV stops. Real SDL Debug/ASan empty-list
injection tests capture the rendered fallback, click OK, resume updates and reach
the Escape menu. The resulting frame was visually checked. The actual `cppdbg`
launch captures/finalizes successfully. Evidence is under `/tmp/e2-requester-*`,
`/tmp/e2-empty-requester-*` and `/tmp/e2-blank-prompt-investigation/`.

See [tool usage](../../debugging.md) and the
[active population/interaction task](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
