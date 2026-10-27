# Recover the original save writer

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
<!-- /docs-tree:parent -->

Status: complete within recorded bounds
Parent Step: [Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
Last Updated: 2026-10-27

Recover `0x453920..0x45442f` and resource record writers using the
[contract map and dated evidence](../../../../../journal/entries/game-save-load-recovery-2026-10-27.md).
Both no-op generator patches are removed. New production binary streams use the
configured `--data-dir/Saved` compatibility boundary. The installed game saves
remain read-only; native probes use private copies and free slots 5–7 only.

Normal/ASan leaf and 24 complete original-writer comparisons pass. Real menu
Save types `E2RTEST`, writes version 4 and trailer 0x1234, returns actual close
result zero, and overwrites only the probe-owned runtime slot on its second
cycle. Save-open failure presents the original message without truncation;
host fixtures cover sticky write and close failures. Both SDL and X11 Debug/ASan
builds and independent four-artifact generation parity pass. The journal retains
commands, intermediate failed probes and exact acceptance limits.

Continue with [restore and menu dispatch](task-03-recover-original-restore-and-menu-dispatch.md).
