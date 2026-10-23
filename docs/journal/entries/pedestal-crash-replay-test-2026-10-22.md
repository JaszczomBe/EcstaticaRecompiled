# Human Pedestal Crash Replay Test — 2026-10-22

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Subsequent authorized work recovers the first differing NPC inputs and a lost
crash-triggering clock boundary. A **new** recording now reproduces the native
crash; the old human capture below remains preserved and divergent. See the
[recovery continuation](replay-npc-input-and-crash-boundary-recovery-2026-10-22.md).

The user recorded an ordinary SDL Debug playthrough and reported a crash just
after the pedestal intro:

`FUN_0042db74:25289 ← FUN_0042b880 ← FUN_0042b338 ← FUN_0042ae80 ← FUN_00427584 ← FUN_0042a70c`.

## Preserved Evidence

The recording is from `~/.ecstatica2/logs/session_20261022_202026_438`.
Before further runs, exported it outside session retention and pinned the exact
Debug executable. The durable local bundle is
`.tmp/replay-bugs/pedestal-20261022-202026/` (ignored by Git). It contains the
read-only recording, original diagnostic log/session metadata, executable,
three replay logs, a GDB stack, `report.json` and verified `SHA256SUMS`.

Executable SHA-256:
`856037d87cb4d78419f50322b5d4488fb02e266b4753cec4aea0af31057d3824`.
It matches both the recording metadata and the existing SDL Debug build.
No rebuild or gameplay repair was made for this test.

The capture retains **574,557,597 clock calls** in **16,089 clock rows**, nine
delivered inputs and 19 checkpoints, through logical sequence **574,586,831**.
The CSV files total about 2.4 MiB. The incomplete marker remains and there is no
end marker, as expected after a native crash. This preserves a useful prefix;
it does not establish that the exact faulting instruction was durably recorded.
The delivered inputs include Space press/release, a mouse click and a final
Right press with no release before the crash.

## Replay Result: Fidelity Gate Failed

Three fresh processes using the pinned executable and recorded startup
environment all exit **74 (diverged)** before reaching the reported crash.
Checkpoints 1–16 match; the first service mismatch is:

| Attempt | Sequence | Expected service | Actual service | Last matching checkpoint |
| --- | ---: | --- | --- | ---: |
| 1 | 38,405,443 | `cursor_get` | `clock` | 16 |
| 2 | 28,350,578 | `cursor_get` | `clock` | 16 |
| 3 | 28,350,578 | `cursor_get` | `clock` | 16 |

A separate GDB replay stops at sequence 28,350,578 in the divergence handler.
The extra clock comes through
`FUN_00457818 → FUN_0041cf5c → thunk_FUN_004620db → FUN_004620bb → GetTickCount`,
called by `FUN_00421074` within the `FUN_004211c8` render epilogue of
`FUN_0042a70c`. The simulation counter is 156. This locates the observed
mismatch in palette-fade work; it **does not establish the root cause** or prove
that the fade helper is the first differing reconstructed operation.
Checkpoint equality covers sampled fields, not all process memory.

No service was skipped, no clock stream was resynchronized and no game state
was corrected to force progress. The differing mismatch sequences also prevent
claiming that the replay itself has a stable failure boundary.

The reported crash line separately dereferences an uninitialized reconstructed
`in_EAX` in `FUN_0042db74`. Its node/actor ownership still requires original
instruction evidence before repair. This test has not reproduced that native
crash through exact replay and includes no reconstruction changes.

## Bounded Inspection And Next Work

The stop-before-checkpoint control also works on this recording: requesting
checkpoint 16 exits **76** at sequence 19,835,423 after checkpoint 15 matches.
All three divergent runs retain diagnostic sessions without nested recordings.
Re-run the preserved case from the repository root with:

```sh
python3 scripts/replay-e2.py run \
  .tmp/replay-bugs/pedestal-20261022-202026/e2recomp \
  .tmp/replay-bugs/pedestal-20261022-202026/recording \
  --timeout 45 --data-dir /tmp/e2-pedestal-retest
```

Add `--stop-checkpoint 16` for bounded inspection. The runner restores recorded
environment values; an ASan or rebuilt executable is not this exact-build test.

The next recorder acceptance work is to isolate the first differing game path
after checkpoint 16, including population/RNG, fade state and service call
placement. Full gameplay crash reproduction remains unaccepted. Workshop
re-entry, sword pickup and full experimental ASan remain separate work.

The entry-state staged implementation remains byte-for-byte unchanged (staged
patch SHA-256
`b7b181717ceaec035bf79ae70fc8911e50a51c89057fc06efb12343f4422cca7`).
Only this test journal/index update is added unstaged. No commit is made.
