# Debugging tools implementation 2026 10 23

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Implemented the prioritized local debugging tool set described in
[the implementation record](../../implementations/debugging-tools/debugging-tools.md).
See [usage and schemas](../../debugging.md) for commands and operational limits.

## Runtime observation

The native observer shares the existing pure field sampler through a separate
sink, preserving the replay sampler's field order. Inspection adds script
diagnostics and attachment ownership, without putting diagnostic process
addresses into replay checksums. Actor-update boundaries surround the existing
`FUN_0042a70c` call; the reconstructed change is three lines, including its header,
with an anchored generator mirror. Input, update and frame observations are
correlated with existing replay progress. Rolling frame retention is independent
of the state-delta history and stops with inspection at its storage/error bound.

The reader handles deletion of actors/input entries, published-prefix recovery,
incomplete markers, frame eviction and unavailable frame backends. CLI queries
and the self-contained HTML report operate on the same capture. Report JavaScript
passes `node --check`; a converted native game frame was visually inspected.

## Original comparisons and investigation artifacts

Shared fixture loading handles the original Watcom PE's unbacked `.bss` section
without treating it as code. The detach fixture uses the shared register
trampoline and first-byte memory differences. Motion-query loading and compilation
use the same Python support. Retained fixtures include the original image hash,
code ranges and dependency interceptions.

Bundle tests verify pinned executable identity, recursive hashes, active-source
lease rejection, tamper rejection and timeout classification. A synthetic i386
SIGSEGV verifies automatic GDB thread-stack/register capture and signal metadata.
A separate three-second dummy-SDL game capture produces a verified timeout bundle
with its native replay and inspection prefix. The actual game's timeout is not
reported as a crash or successful route.

A small i386 GDB pilot records two memory writes and reverses the second,
verifying the observed value changes from 42 back to 41. The generated game
launcher starts recording at a selected replay function. `rr` capability reporting
identifies that it is not installed; its integration is available but no rr
compatibility result is claimed.

## Validation

- SDL/X11 Debug and ASan builds pass. Logger-disabled and runtime-options-disabled
  X11 configurations also build; the latter remains a C-only executable.
- Native observer/reader contracts pass normally and with ASan: delta updates and
  deletion, update/frame correlation, rolling retention, disabled capture,
  unavailable frame backend, abrupt-exit recovery and malformed rows.
- Debug and ASan SDL menu recordings each pass three fresh replays with inspection,
  a replay with inspection disabled and a replay with a two-second debugger pause.
  Each route retains 11 input deliveries and 20 strict replay checkpoints.
- Replay parser/checksum/identity/recovery/divergence contracts pass in Debug and ASan.
- Migrated detach comparisons pass 16,384 helper cases and 65,536 caller cases,
  normally and with ASan. Motion comparisons pass 394 polar cases, 92,160 query
  cases and eight recorded courtyard cases, normally and with ASan.
- The recorded intro/menu scenario passes camera 175, Joe-loaded and Up press/
  release expectations with a completed inspection and native replay exit zero.
- Existing runtime regressions and all eight Debug/ASan arrow-control cases pass.
- Targeted Clang syntax-only analysis succeeds; the recovered detach function has
  no selected warnings, while `FUN_00415d40` reports 22 unresolved-value warnings.
  These are investigation hints; no placeholder is initialized or gameplay
  behavior changed to suppress them.

Evidence lives under `/tmp/e2-debug-*`, including accepted menu captures,
`e2-debug-runtime-regressions.log`, `e2-debug-controls.log`, and the example
`e2-debug-report.html`. These scratch paths are not committed artifacts.

The user's existing staged callback repair and documentation remain staged.
This debugging implementation is unstaged. No commit or push.
