# Inner-castle progression crash and rendering handoff — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Result and scope

The user reports substantial progression beyond the previously bounded tower
key/door route: magic armour, gargoyles, tower prison key, wizardess instructions,
tower-top magical mace, descent, two gold head levers and a later dark head lever,
with both gates opening. The mace is described as enabling the inner-castle gate
to be bashed open; completion of that separate bashing action was not reported.
The game subsequently crashes in `FUN_0042d61c`.

The user requests an updated handoff, a message for the next context and a commit
message for the changed files. This turn inspects existing evidence and updates
documentation only. It introduces no runtime fix, new model selection, replay
acceptance, commit, push or staging change. Previously staged work is preserved.

[Step 12 Task 04](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-04-recover-inner-castle-progression-crash-and-models.md)
is the selected continuation: reproduce and recover the crash first, then recover
the eight reported original presentation paths. Task 03's bounded tower evidence
and the [storage/sparkle follow-up](tower-storage-render-followup-2026-10-28.md)
remain historical acceptance within their limits. Task 02's variants/acid work
and audio remain subsequent priorities.

## Human presentation findings

1. Teleport has only a box overlay and no model.
2. Head switches have only box overlays and no models.
3. Magic armour has only a box overlay; after pickup Joe gains another box.
4. Gates near the armour render incorrectly.
5. The wizardess has a visible model that lacks details.
6. The spawned tower prison key has no model.
7. The magical mace and its magical blinking effects have only box overlays.
8. During descent from the tower top, the stairwell lightning sequence produces
   a flash but no visible lightning or rubble.

These are human observations, not yet assigned to original runtime identities
or reproduced in agent probes. Preserve original behavior, including possible
original defects. Do not infer that the prison key is earlier key 264, that the
strike uses the intro lightning owner, or that equipping armour merely requires
suppressing Joe's additional box. Recover actual owners and source contracts.

## Located session and stopped-thread evidence

Source: `~/.ecstatica2/logs/session_20261028_173846_961/`.
The manifest identifies Debug SDL executable
`build/Debug/clang21-i386-sdl/e2recomp`, SHA-256
`33c4ce05ad0722a60e3b748a52b502f06069f7b638c1af44ad862ebab02b6d2e`,
with source revision **990bdd9ea080ccdf434f626d4d20bf440f12a422**.
The pinned executable and startup working-tree patch are under `investigation/`.
Current repository HEAD is still that revision on `linux-e2-reconstructed-runtime`;
the working tree/index already contain the preceding tower recovery and tests.

`investigation/manifest.json` is finalized, retention-protected, records
**SIGSEGV** / `terminated-by-debugger-or-signal`, and has no normal exit code.
`replay_complete=false` and `inspection_complete=false`; their incomplete markers
remain present. Finalization of debugger evidence does not make these streams
complete. No replay was attempted during this documentation handoff.

`investigation/debugger.log` records crash sequence **9684450756** and last
checkpoint **3190**. The reported main-thread chain is confirmed:
`FUN_0042d61c → FUN_0042b880 → FUN_0042b338 → FUN_0042ae80 → FUN_00427584 →
FUN_0042a70c → FUN_00426df8 → FUN_0041007c → E2R_WinMainThunk → main`.
The top frame is reconstructed C line **24944**, first dereference of its
unresolved local `in_EAX`, captured as **328/0x148**. Caller event **0x23**
invokes this no-argument function at line **23657**; the saved caller has root
argument **0xaaeab0** and selected `unaff_ESI=0xa350fe`. The original EAX/node
contract and linked helpers require recovery; this is not yet a proven root cause.

The last published inspection state reports camera **54**; its tail has frame
**1450**, snapshot **6184**, and an input-before Up press at sequence
**9684450751**. Do not treat this preceding observation as exact faulting state or
assume the last lever caused the crash. Earlier actor/scene transitions and the
actual loaded slot remain to be established from the recording and loader.

## Current save inventory and continuation constraints

Read-only inventory of `~/.ecstatica2/Saved/` at handoff:

| Slot | Label | SHA-256 |
| --- | --- | --- |
| **5** | **123** | `2fe5bae205ba421375468958af2742cb7389cd1c196e6706be6b70fd433d1079` |
| **6** | **DFGSDRG** | `5da846d89e4fae206e87ac9016d0f006e6790c9d6547c285e4e73d2f79442e8a` |
| **7** | **COURT** | `880abe065c2fd9c5bd255550f93694216cd3e66e66888b4d7fe12aa9e84dca64` |
| **9** | **Quick save** | `a314c1287b937cf9f95f360fe3539b01c6ebd412d9629f55fa5333c41c3167c0` |

Slot **5** is now user-owned and occupied; the preceding tower fixture's choice
of private slot 5 is not reusable for this save set. Preserve and hash all source
saves and source session files before native work. Use private copies, identify
the recorded loaded slot, and choose a freshly confirmed free private slot for
any later persistence test. The session's new slot 5 may be useful but has not
been proven to contain the pre-crash progression or the initial replay state.

The next context should perform bounded pinned crash-prefix reproduction,
recover original register/owner/transform behavior and mirror any repair in
`GenerateRecon.js`, then verify Debug/ASan survival and original effects beyond
the event. Recover the reported render owners individually and preserve original
game defects unless a reconstruction mismatch is demonstrated. Retain F3, HUD,
Save/Load, source assets and recording checks. No cosmetic replacement, forced
gate opening, skipped action or speculative pointer guard is accepted recovery.

Documentation-tree update/check and whitespace checks validate this handoff.
Runtime builds/tests from preceding entries remain historical; none is new
acceptance of this longer route or crash repair.
