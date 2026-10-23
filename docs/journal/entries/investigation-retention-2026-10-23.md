# Investigation retention and human replay assessment — 2026-10-23

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user reported a crash in the second-to-last F5 run and subsequently deferred
that game repair until a new recording is available. Its receipt identifies
`session_20261023_135943_604`, but the session directory and pinned binary are
absent. No recoverable copy or matching core was found in the checked local
artifact locations. The following session's log confirms cleanup removed three
older sessions at 14:04:20, freeing 81.3 MiB while retaining its active 192.5 MiB.
The old 128 MiB total retention budget was unsuitable for these captures.

## Retention repair

The newest five sessions now survive every cleanup regardless of size or an
explicit lower count cap. Older sessions have a separate default 2 GiB budget,
roughly eight additional captures at the observed 247 MiB/session size. The
newest five consume none of that budget. Default count limiting is effectively
disabled; an explicit count limit still respects the five-session floor. Startup
and periodic cleanup delete eligible older sessions oldest first.

F5 creates `investigation.keep` while its active lease protects startup. Signals,
unsuccessful/unknown termination retain the marker; observed clean exits release
it during finalization under retention serialization, even if recording reached
its file limit. Incomplete capture is reported separately.
Markers require explicit removal after review/export. Protected older data can
exceed the budget, with the overrun reported. Signal stacks/registers also have
a bounded workspace receipt sidecar. Finalization records replay completion and
protection state, warns about incomplete evidence and detects expired receipts.
No reconstructed game logic or generator was changed.

## Assessment of the surviving human run

The later `session_20261023_140320_197` exited zero and completed inspection, but
its replay reached the 128 MiB event-file limit at 14:04:21. Recording stopped
while gameplay continued; its native incomplete marker correctly remained.
This is a recording-duration limitation, separate from retention. Longer routes
need a future storage/compression improvement with replay-format and export
validation; increasing retention alone does not extend recordings.

The surviving session was exported and integrity-verified at
`/tmp/e2-human-latest-20261023`. Exact replay with its pinned image matched
1,158 checkpoints and reached sequence 1,722,732,210 before returning
75/INCOMPLETE at prefix exhaustion without divergence. Inspection is under
`/tmp/e2-human-latest-replay`. This validates that human prefix, not the missing
crash or clean full-route replay completion.

## Verification

SDL Debug and ASan builds pass. Both native retention checks cover the
newest-five floor under count/byte pressure, separate older-byte accounting,
oldest-first deletion, retained investigation markers, active and legacy leases,
explicit marker release and periodic cleanup. Sparse large fixtures avoid
allocating real gigabytes. F5 contract/native SIGSEGV checks cover preserved
stops, independent signal evidence, protection/release and expired receipt state.
The updated Debug and ASan developer-launch regressions pass 30 cases each,
including default retention metadata and 2 GiB sparse-file cleanup. The real
`cppdbg` launch passes a bounded capture/finalization check; tree validation
passes for all 223 Markdown documents.

See [retention usage](../../building.md#runtime-logging) and
[F5 artifacts](../../debugging.md#normal-gameplay-investigation-in-vs-code).
