# Recover Hosted Floor Byte Reads

Status: completed bounded decoder/handoff repair; gameplay acceptance remains open
Parent Step: [Diagnostic Gameplay With Cylinder Actors](../step-09-enable-diagnostic-gameplay.md)
Last Updated: 2026-10-14

## Goal And Result

Repair the FAN floor-entry byte reader so Joe's actual final release position queries the courtyard rather than the forest fallback. `FUN_0045f38a` now accepts readable hosted headers above the legacy address range under the recovered-action gate, consumes binary CR/0x1a bytes and preserves the cursor. Recovered descriptors select camera 175 without forced position/camera changes.

The [journal and continuous capture](../../../../../journal/entries/courtyard-floor-decoder-2026-10-14.md) record original instruction evidence, 4,096 floor-entry/256 byte comparisons passing normally and under ASan, the courtyard wait-zero packet and verification limits. The source repair has a narrow generator mirror.

## Boundaries And Follow-Up

The default route retains its previous high-address rejection until its placement/spawning contracts are recovered; F5 already opts in. Fixture ASan passes do not cover the full runtime, which still exposes the NPC query/spawn family. [Task 04](task-04-recover-npc-spawn-query-inputs.md) owns that stability dependency; [Task 02](task-02-recover-post-intro-placement-and-motion-queries.md) continues movement/control queries. Neither an input latch nor a single successful courtyard capture closes playability.
