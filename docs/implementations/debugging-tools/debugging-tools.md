# Debugging tools for Ecstatica II

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Implementations and task state](../README.md)
<!-- /docs-tree:parent -->

Status: initial tool set implemented
Last Updated: 2026-10-23
Usage: [Debugging the reconstructed runtime](../../debugging.md)

## Goal

Reduce repeated investigation work by connecting replay, engine observations,
original-code comparisons and native debugging. Keep recovered game behavior and
existing replay acceptance rules intact. The user authorized the six additions
in priority order; gameplay recovery remains under the active SDL implementation.

## Delivery sequence

| Order | Addition | Implemented slice |
| --- | --- | --- |
| 1 | State inspector and timeline | Independent delta snapshots, replay/update/presentation coordinates, actor/script/attachment inspection, rolling SDL frames, JSON queries and interactive HTML report |
| 2 | Original-code framework | Shared PE32 loader, C extraction/compiler, register trampoline, memory differences and retained provenance; detach and motion fixtures migrated |
| 3 | Investigation bundle | Bounded normal-run capture, optional GDB stacks/registers, binary pinning, logs/replay/inspection/context, recursive integrity verification and raw-evidence retention after export failure |
| 4 | Reverse debugging | Replay-aware GDB recording-window launcher and verified i386 reverse-write pilot; optional rr integration with explicit capability reporting |
| 5 | Recorded-route expectations | Declarative sampled-state/event assertions plus native completion gate; verified intro/menu scenario |
| 6 | Recovery evidence and diagnostics | Address/signature/fixture/journal/generator index, placeholder ranking, missing-link findings and analysis-only Clang diagnostics |

## Acceptance and limits

The observer adds no game-visible clock calls, state repair or reconstructed
projection calls. Generated update-boundary hooks have matching generator
patches. Existing replay schema and checkpoint field ordering remain intact;
inspection environment options are excluded from replay identity. Inspection
files use their own completion marker and bounded storage.

The original-function framework verifies explicit register/memory/dependency
contracts. Other fixtures can migrate incrementally. The scenario runner gates
recorded routes; new populated traversal and interaction fixtures still require
their own gameplay evidence. Sampled state does not establish continuous-state
invariants. A clean inspection alone does not establish successful replay.

GDB process recording has instruction/device limitations. `rr` is absent on this
host, so its native pilot remains dependent on installation and CPU/kernel/ptrace
compatibility. SDL frames represent actual successful presentations; a fast
replay may present fewer images. X11 retains state observations without SDL
frame capture. Continuous video and synchronized whole-process original-game
tracing remain future extensions of these tools.

The README-rooted documentation tree links current implementation records and
historical evidence. Former links to the absent post-pedestal continuation now
lead to the available task/replay record, which identifies the missing artifacts.
Normal human F5 sessions enable recording/inspection, pin the running binary,
retain debugger stops and finalize their report inside ordinary session retention.
The [human-run retention assessment](../../journal/entries/investigation-retention-2026-10-23.md)
adds a newest-five floor, separate 2 GiB older budget, failed/pending capture
protection and durable signal evidence. The surviving human replay matches
1,158 checkpoints, but its event-file limit demonstrates that longer recording
duration needs further work. The absent reported crash awaits a new capture.

## Verification

The [large human replay/requester investigation](../../journal/entries/blank-requester-and-large-replay-2026-10-23.md)
adds row-wise i386 CSV validation, larger capture/export limits, modal-entry
observations and quiet console action traces. The old route's divergence remains
explicit; the user repeat at camera 722 completes without the reported prompt
and passes three exact replays with 120 matching checkpoints each.

Tool verification commands and current evidence are recorded in the
[2026-10-23 journal](../../journal/entries/debugging-tools-2026-10-23.md).
The [F5 and documentation integration record](../../journal/entries/f5-investigation-and-documentation-tree-2026-10-23.md)
covers the normal selected-target launch, Debug/ASan adapter verification and the
README-rooted navigation checks.

The [water-entry investigation](../../journal/entries/water-entry-and-player-resource-2026-10-23.md)
uses a complete replay, state timeline and pinned GDB watchpoints to distinguish
an incorrect actor death from a crash. New observational health/terrain/resource
fields expose the missing context; canonical replay sampling stays unchanged.
The final Debug/ASan keyboard routes demonstrate forward swimming, while the old
recording correctly diverges after loading changes. Agent motion probes isolate
their sessions under the output prefix and use hardware release watchpoints for
natural-intro readiness where no earlier guard checkpoint is needed.
