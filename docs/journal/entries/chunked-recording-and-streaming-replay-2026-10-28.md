# Chunked recording and streaming replay — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user repeatedly encountered `RECORDING INCOMPLETE: capture file limit
reached` and requested a repair. The writer stopped at 256 MiB in either event
or checkpoint storage. Increasing that limit alone would retain the existing
whole-recording event/checkpoint memory cost in i386 playback.

## Storage and ownership

New recordings rotate each stream at 16 MiB between complete CSV records.
`events.csv`/`checkpoints.csv` continue through numbered files; every physical
file has its stream header, and individual checkpoints can cross files.
`storage,chunked.csv.1` identifies this physical layout in metadata. Logical
schema `e2replay.csv.1`, event sequence/count semantics, checkpoint field order
and logical signatures remain unchanged. The optional capture threshold
`E2R_REPLAY_CHUNK_BYTES` is excluded from gameplay identity. Existing recordings
without the storage field retain their legacy layout and remain readable.

`chunks.csv` records each sealed stream/index/name/size/SHA-256. Rotation
synchronizes and closes the old file, then publishes and synchronizes its
manifest entry, before opening the next file exclusively. Successful completion
seals both final files before removing `recording.incomplete`. An interrupted
manifest row or unsealed final file is recoverable only with that marker.
Recovery ignores unfinished CSV tails and tolerates an empty/unfinished header
created at rotation. Missing/reordered/orphan/misnamed chunks, symlinks,
sealed-file corruption and malformed complete records are rejected.

Preparation holds the existing inactive-source/retention lease while freezing
canonical rows into two anonymous temporary disk files and validating the full
logical recording. It releases the source locks before logger startup. Playback
reads those immutable spools sequentially, retaining a pending event and current
sampled checkpoint rather than all historical events/snapshots. Source retention
can remove the original without invalidating playback. Native spool offsets use
64-bit file operations. No reconstructed C or generator changes were needed for
this host tooling repair; the prior staged HUD work remains preserved.

The Python inventory verifies all sealed chunks with streaming hashes. Inspect,
replay snapshot/export, and portable investigation bundles include the complete
manifest and chunk inventory. Replay bytes are exempt from the separate
non-replay bundle budget, so long recordings do not encounter a replacement
768 MiB aggregate ceiling. Bundles include the shared inventory helper alongside
their replay launcher. Existing source lease and executable identity checks stay
in force. Human F5 still uses the single selected-target launch and automatic
recording policy.

## Fresh verification

Evidence is under `build/evidence/replay-chunks-2026-10-28/`; real SDL capture,
GDB scripts and replay output also remain under
`/tmp/e2-replay-chunks-native-{debug,asan}-rotated/`.

- Debug and ASan native parser contracts pass exact capture/playback, expanded
  clock runs, changed-clock crash publication, legacy input, identity/signature
  rejection, divergence and unfinished-tail handling.
- The new chunk contract passes exact replay across **69 event files and 526
  checkpoint files** at a forced 512-byte threshold. It covers split/quoted
  checkpoints, nested pumps, legacy flattening across CSV reader-buffer
  boundaries, missing/reordered/corrupted/symlinked chunks, an interrupted
  manifest and CSV tail, empty/partial new headers, and full replay/bundle export.
- `check-e2-replay-chunks.py --large` records and exactly replays **281,272,574
  event bytes plus 309,587,622 checkpoint bytes** in both Debug and ASan. Each
  stream independently exceeds the former 256 MiB ceiling and every file stays
  within the default 16 MiB threshold. Peak child RSS for the contract/tool run
  is **24,436 KiB Debug** and **1,094,128 KiB ASan**, including sanitizer allocator
  overhead. These are measured process peaks, not a promise about total game RSS.
- Fresh SDL Debug/ASan intro/menu captures force 64 KiB rotation: each spans
  **15 event files and 10 checkpoint files**, retains 11 inputs and matches all
  **20 checkpoints** in three independent exact replays, an inspection-disabled
  replay, and a replay with a two-second debugger pause. Every replay exits zero.
  `native-reports.json` retains binary hashes and per-run results.
- Debug/ASan lifecycle checks pass abrupt kill and partial-tail recovery, replay
  after startup retention deletes its source, no nested/probe recording, and
  file-size write failure continuing gameplay with incomplete status. They use
  private temporary directories and dummy SDL drivers.
- SDL/X11 Debug/ASan builds pass. Independent generation matches all four
  reconstructed artifacts. All 67 suite contracts, bundle/F5 contracts and
  31 developer-launch/logging cases per native configuration pass.

Useful commands are in [the replay guide](../../replay.md#recovery-retention-and-limits).
The [tooling implementation](../../implementations/debugging-tools/debugging-tools.md)
owns current acceptance. Installed saves were not written, no persistence route
was invoked, and no commits, pushes or tag changes were made.

## Limits

There is no fixed total recording-size/duration cap, but disk capacity and I/O
failures remain real limits. Native preparation needs temporary disk space
approximately equal to its logical input; the Python runner also takes a frozen
snapshot. Buffered clock suffixes and other unpublished crash tails can still
be lost under the existing publication contract. Directory/power-loss durability
is not expanded into a filesystem transaction guarantee.

This work cannot restore events that an older capped writer never captured.
Large deterministic fixture success and bounded menu replay do not establish
arbitrary long human-route fidelity or resolve previously recorded gameplay
divergence. Inspection has its own independent storage policy. No audio, gameplay,
HUD, save format or installed asset behavior was changed by this repair.
