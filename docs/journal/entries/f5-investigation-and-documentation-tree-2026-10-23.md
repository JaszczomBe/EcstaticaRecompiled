# F5 investigation and documentation tree — 2026-10-23

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The existing **Ecstatica Recompiled** launch now enables the investigation tools
for normal gameplay. It keeps the CMake-selected executable, working directory
and diagnostic gameplay options; recording and inspection are enabled and an
inherited replay path is cleared. See [normal F5 usage](../../debugging.md#normal-gameplay-investigation-in-vs-code).

## Debugger integration

The GDB setup hook waits for target symbols and observes the first inspection
sample. At that boundary it pins `/proc/PID/exe` and source/build context inside
the native session. Using a sampler boundary after the ASan startup prologue
avoids reading an uninitialized argument slot from entry-line DWARF.

Signal and breakpoint stops retain thread stacks, registers and replay progress;
they leave GDB stopped. Exit metadata distinguishes an observed exit code from
an ambiguous debugger termination. A post-debug process task finalizes inactive
sessions into an inspection report; the GDB-exit hook provides another attempt.
Active leases prevent finalizing another running session. Artifacts follow normal
session retention until explicitly exported; exports include the F5 artifacts.

## README-rooted project information

The central README links current capabilities, handoff, build/tool usage, active
implementations and tasks, plans, journal, formatting, contribution rules, agent
instructions and code of conduct. Original control tables and existing project
images remain under the reference branch. Project documents have reciprocal
parent/child navigation; dependency documentation is indexed without changing
upstream files.

The tree checker validates reachability, ownership cycles and project local link
targets. Its update mode refreshes breadcrumbs and missing child links and is
idempotent. Historical links to the absent post-pedestal continuation now lead
to the available task/replay record, which explicitly identifies missing journal
and raw artifacts. No missing historical evidence was invented.

## Verification and limits

- The installed `cppdbg` adapter passes final three-second SDL Debug and ASan
  launches using the actual launch configuration, automatic recording and
  investigation verification. Both produce matching executable hashes,
  inspection, debugger evidence and finalized HTML reports.
- A small native i386 SIGSEGV fixture verifies stack/signal capture, the pinned
  process image and that GDB remains stopped after the signal. Contract tests
  cover active-source rejection, repeatable finalization and verified bundle
  export containing F5 artifacts.
- Existing developer-launch/logging regressions pass all 30 cases in Debug and
  all 30 in ASan. Agent helpers explicitly override human automatic recording.
- Documentation contracts cover orphan and broken-target detection, cycles,
  template/fence handling, unchanged upstream files and repeatable updates.
  All 222 Markdown documents currently present pass the local-link and
  parent/child check. Vendored SDL files remain unchanged.

Adapter evidence is under `/tmp/e2-f5-debug-final-probe*` and
`/tmp/e2-f5-asan-final-probe*`; captured sessions use the corresponding
`/tmp/e2-f5-debug-final` and `/tmp/e2-f5-asan-final` roots. These dummy-SDL runs
verify bounded startup and debugger Stop, not a manual full gameplay session or
the editor's selected preset. Debugger Stop correctly leaves partial replay and
inspection marked incomplete. Native game behavior was not changed by this
integration. The user's staged callback repair remains staged; no commit or push.
