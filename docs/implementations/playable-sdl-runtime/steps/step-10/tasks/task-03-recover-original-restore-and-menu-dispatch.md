# Recover original restore and menu dispatch

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
<!-- /docs-tree:parent -->

Status: complete within recorded bounds; malformed-file cleanup remains unqualified
Parent Step: [Recover Functional Game Save And Load](../step-10-recover-game-save-load.md)
Last Updated: 2026-10-27

Recover `0x4544a4..0x454fa1`, slot selection/editing and confirmation using the
[original contract map](../../../../../journal/entries/game-save-load-recovery-2026-10-27.md).
Restore resource hierarchy before actor state, then action ownership, signed
relative timers, reciprocal attachments, caches, visibility, globals and current
player/presentation. Preserve the original destructive-load boundary and record
failure limits. Temporary stream context must not redirect nested resource loads
to the save file.

Acceptance requires real menu Save into an originally free private slot, changed
state through real input, Load and resumed gameplay, followed by a fresh process
loading the same save. Observe player/world fields, attachments and timers; do
not assign gameplay state to manufacture success. Verify input, animation and
interaction after restore, repeated cycles, normal/ASan checks, affected builds
and independent generation parity. Protect every occupied original and private
reference slot. Dialog/thumbnail-only success does not pass this task.

## Verification

Debug/ASan persistence journeys perform two real menu Save/change/Load cycles,
then load the final save in a fresh process. Exact loader-return comparisons
cover active actor fields, matrix, actions, script ownership/progress, relative
timers and reciprocal attachment identity. Sword 3717 restores on Joe's bone 8
and follows subsequent movement; original attack animation/input and a workshop
camera crossing work after loading. All successful processes exit through menu
Quit. Opening saves contain no active timers; 210 original loader timer-block
cases qualify nonempty timer reconstruction separately.

The [journal](../../../../../journal/entries/game-save-load-recovery-2026-10-27.md)
records source-backed empty/missing/unsupported/truncated/write-failure checks.
Unsupported and write-open errors resume play. Missing/truncated probes stop
before generic fatal cleanup; there is no rollback claim after destructive reset.
Arbitrary malformed files, all installed original progressions and further tower
play remain unqualified. No installed save or occupied private reference slot was
changed. The new `persistence` suite block owns focused regressions; old dialog
probes retain `state_round_trip=False`.
