# Recover The Post-Intro Action Error Requester

Status: active
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-14

## Goal

Expose and dismiss the invisible modal error that makes the default F5 pedestal scene appear frozen after the intro.

## Evidence

The supplied 35-second F5 recording confirms the new cue overlay and Space transition to camera 175. It also shows arrows and Escape reaching the window procedure without a visible response. This is manual survival evidence, not playable-gameplay acceptance.

The bounded reproduction completes `Start_sc` at progress/duration 1102/1102, then requests action 384 (`dav:heropick`). Default indexing is disabled, so its archive offset is -1. A breakpoint at the later Escape shows requester ID **0x2e**, state **0**, and this stack:

`E2R_WndProc → FUN_0041ba7c → FUN_0043b384 → FUN_0043cbf0 → FUN_0043cbb4 → FUN_00451880 → FUN_00427584 → FUN_0042a70c`.

Thus ID 46 is an active blocking message, not a stale ID. The game loop is suspended in that modal wait; the host pump remains responsive. Do not relax the WndProc idle-requester guard to bypass it. Evidence: `/tmp/e2-escape-before.log`.

## Scope

1. Recover the original action-error name/id formatting and local message-list lifetime (`0x4518a4..0x4518f3`, `0x43cbb4`).
2. Restore mapped message-line copies, the original requester record and item layout, and the explicit requester argument (`0x43cbf0..0x43ccb8`).
3. Validate visible presentation and the original OK callback, followed by game-update and Escape handling.
4. Preserve action indexing as opt-in; do not fabricate missing actions, move Joe, suppress repeated errors, or expand into geometry recovery.

## Acceptance

1. The actual action title/name/id appears in the SDL presentation surface.
2. OK dismisses the message and the game loop returns; any immediate retry/reopened dialog is recorded honestly.
3. Relevant Debug/ASan builds and bounded probes pass, with generator parity. Revise old static-hash/input-latch assertions if they measured the invisible modal, preserving their useful intent.
4. Record manual F5 confirmation separately from automated surface and debugger evidence.

## Manual F5 Follow-Up — 2026-09-21

The user confirms that the dialog appears over camera 175 and clicking OK changes the view to the unintended camera 87 rooftops. The second screenshot still shows the action-384 error. This proves visible error presentation and advancement after OK; it does not establish a sustained return to gameplay. The screenshots alone cannot distinguish a newly opened error from retained dialog pixels.

The cue status changes from **0 visible / 1 behind** at camera 175 to **0 visible / 1 offscreen** at camera 87. Neither view contains a visible Joe marker or rendered hero. These are camera-relative diagnostics, not evidence that Joe moved. The log’s `scene=0x67d0ac` agrees with camera 87; Shift and focus events confirm host input delivery, not gameplay control or manual Escape behavior.

Manual dialog/OK coverage is now recorded. Escape remains verified only by the automated test; repeated-error behavior, actor rendering and scene fidelity remain open. Task 11 copy inputs are implemented; Task 12 DirectDraw Lock storage is next within Task 02, before action/placement validation.

## Review State

Implementation: implemented; automated verification passes, manual dialog presentation and advancement after OK confirmed; manual Escape confirmation remains pending. Four Debug/ASan builds, four-artifact generator parity, the revised wrapper and all eight arrow rows pass. The new SDL Debug/ASan regression captures the dialog, clicks OK, reaches a game update at camera 87, and verifies Escape enters main-menu ID 0x28. Full menu navigation and playable movement are not established. The hosted font still has punctuation/spacing limitations. See the [requester journal](../../../../../journal/entries/post-intro-requester-2026-09-15.md) for commands and risks. Task 12 is the next bounded compatibility Lock repair within Task 02, after Task 11's copy-input comparison passes.
