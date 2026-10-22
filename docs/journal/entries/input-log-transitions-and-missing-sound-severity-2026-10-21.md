# Input Log Transitions And Missing-Sound Severity — 2026-10-21

The user requested lower severity and separate tags for input and missing sound, plus compact key logs showing pressed/released/held state. The existing output duplicated each input across SDL events, key translation, host dispatch, legacy entry/exit, flag writes and keyboard snapshots, mostly at Info.

## Behavior

- Input records use `Runtime.Input` at **Debug**. Missing sound archive diagnostics use `Runtime.MissingSound` at **Trace**, preserving their original message fields. Other diagnostics retain their existing severity rules. `Info` hides both; `Debug` retains input while hiding missing sound. The logger's existing default threshold remains unchanged.
- The Win32 compatibility boundary observes delivered virtual-key messages. Each key logs one `pressed` record, one `held` record on its first repeat, and one `released` record, with elapsed `held_ms`. Later repeats and duplicate releases produce no additional records. Overlapping keys track independently; release duration remains available for modifiers without autorepeat.
- Input delivery remains untouched: folding applies only to diagnostics. Both direct host dispatch and queued `DispatchMessageA` dispatch use the observer. Diagnostic state uses the existing message mutex and never writes legacy key queues, actor state or reconstructed game state. It has no lifetime event cap.
- Detailed SDL/window messages, keyboard snapshots, legacy input entry/exit and input-flag traces are hidden unless `E2R_INPUT_DIAG_VERBOSE=1`, then emitted at Debug with the Input tag. Explicit probe snapshots remain available at Debug. Existing `E2R_INPUT_DIAG` enable/disable behavior remains in place.

The logger's supplied rate limiter samples one record in N; it does not fold consecutive records while preserving press/release edges. State transitions are therefore detected at the input boundary rather than sampled. This is a diagnostic view of delivered virtual keys, not physical keyboard recording or periodic held-key snapshots. Reconstructed C and the generator are untouched.

## Verification

- All four SDL/X11 Debug/ASan preset builds pass.
- `check-e2-developer-launch.py`: **26 cases per build**, **52 total**, pass. The new cases call the production dispatcher and legacy handler under GDB at Info, Debug, Trace and verbose Debug. Each sends **605 keydowns**, including **600 Up repeats**, overlapping Down/Shift, duplicate release and a later A press/release. Every keydown reaches the handler, while compact logs retain exactly the expected key transitions. Missing-sound severity/tag and opt-in detailed diagnostics are checked in both console and session files. Reports: `/tmp/e2-input-final-launch-{debug,asan}/`.
- Existing key-release fixtures pass normally and under ASan: **114** held-key release cases and **336** modifier cases per build. Reports: `/tmp/e2-input-key-release.log`, `/tmp/e2-input-key-release-asan.log`.
- Runtime regression wrapper and all **eight** control matrix rows pass: `/tmp/e2-input-regression-check.log`, `/tmp/e2-input-controls-check.log`.
- Actual native `.vscode/launch.json` startup is checked through the installed cppdbg adapter for Debug and ASan; evidence is `/tmp/e2-input-vscode-{debug,asan}.json` and corresponding adapter/event logs. These are bounded startup observations, with input transitions verified separately by the dispatcher checks.
- Earlier logger work is already staged. The staged patch SHA-256 remains `1a541eb546e857642918343a09c0baae4501167a38968fca08888eb13160135c`; these follow-up changes remain unstaged. No commit is made.

Manual workshop re-entry, sword pickup, full experimental ASan and route recording/replay retain their existing acceptance limits.
