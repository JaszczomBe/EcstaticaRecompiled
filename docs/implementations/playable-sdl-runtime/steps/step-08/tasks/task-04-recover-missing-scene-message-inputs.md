# Recover Missing-Scene Message Inputs

Status: completed
Parent Step: [Recover Scene 175 Actors](../step-08-recover-scene-175-actors.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-09-14

## Goal

Recover the missing-scene error message's string inputs and list lifetime so the gated action route can report the requested missing resource safely.

## Scope

1. Identify the requested scene id and missing archive/table entry at `FUN_0045233c`.
2. Recover its `FUN_00441e38 → FUN_0043cbb4 → FUN_0043cbf0` string inputs and local list layout from the original executable; audit affected direct callers before changing shared signatures.
3. Mirror the focused repair, then rerun gated debug/ASan and default regressions.

## Out Of Scope

1. Masking the error with another pointer guard or disabling ASan.
2. Broad requester/menu reconstruction, fabricated scene resources, or assuming the observed scene drift is correct.
3. Expanding this task into motion, scene-selection, or geometry recovery; record those as separate follow-ups if needed.

## Original Failure And Source Evidence

This failure was exposed after Task 01 restored the action owner's callback inputs. `/tmp/e2-action384-asan.log` reports stack-use-after-return at `E2R_ResolveMenuStringList`, with a stale address in a returned `FUN_00422abc` frame. The call stack is `FUN_0045233c → FUN_0043cbb4 → FUN_0043cbf0 → E2R_ResolveMenuStringList`; do not assume the named old stack frame is the producer of a legitimate retained pointer.

Original `0x4523a2` calls `FUN_00441e38`, `0x4523a7` moves its returned scene name to EDX, and `0x4523a9` loads EAX with `0x47563c` (`Can't find scene`). `FUN_0043cbb4` builds three contiguous pointer words `[EAX, EDX, 0]` on its stack before calling `FUN_0043cbf0`. The reconstruction instead passes `extraout_ECX_01` to a one-argument wrapper. This identifies the calling-convention/lifetime repair to investigate, not permission to rewrite the whole dialog system.

The diagnostic SDL run moves 175 → 87 → 40 after activation and captures Joe at live `-11792,-16256,-8160`, home `12800,256,-3584`; these are observations, not validated coordinates. At task creation the missing scene id had not yet been established; the verification below now identifies it. Recovering the error report does not establish that scene 40 is intended or that the user's manual rooftop view is the same failure.

## Implementation And Result

The repair is confined to the missing-scene branch in `FUN_0045233c`: retain `FUN_00441e38`'s returned name, inline the original wrapper's three-word list, and call `FUN_0043cbf0` with that live list. Direct-caller inspection found many other one-argument `FUN_0043cbb4` uses with unrecovered inputs; their signatures/behavior were not guessed. The message text at original address `0x47563c` was empty in the reconstructed address map, so this branch uses the exact original string literal, verified with `objdump -s`.

GDB now proves scene id **40**, name **`mtorc4`**, resource table entry **0**, archive offset **-1**, and current actor **`0xaa6bd8`**. The list is `["Can't find scene", "mtorc4", NULL]`; `E2R_ResolveMenuStringList` returns that same live stack address, and execution reaches `FUN_0043b384`.

At Task 04 completion, the gated ASan run no longer reported stack-use-after-return or another sanitizer error. Both plain SDL and ASan runs exited **5** after the 120-second scene-readiness wait, with scene slot 40. This is a resolved message-input failure, not a passing gameplay route. Task 01 stays active; [Task 05](task-05-recover-post-intro-scene-selection.md) owns the remaining position/scene-selection investigation.

Visible error presentation is not validated: `FUN_0043cbf0` still copies through the no-op `FUN_0045f22f`, and passes line count 2 to `FUN_0043b384`, where the original passes requester pointer `0x47a630`. The proof stops at requester entry; dismissal and loader return were not established. Those existing requester limitations are separate from the recovered string inputs and remain deferred UI work.

Subsequent Task 05 recovery identifies aliased keyframe allocation. With its gated pool repair, the current endpoint is an earlier scene-pose actor-input crash, owned by [Task 06](task-06-recover-scene-activation-pose-inputs.md). The scene-40 timeout above records this task's historical verification, not the latest gated result.

## Acceptance Criteria

1. Original-source evidence establishes the message/name arguments and list lifetime; no stale pseudo-register supplies a string/list pointer.
2. The gated ASan route no longer reports this stack-use-after-return. Record the actual requested scene and any new independent failure.
3. Generator parity, three builds, and the default debug/ASan wrapper and arrow matrix pass.
4. Rerun Task 01's gated packet requirement; retain it as open if scene readiness or another failure prevents completion.

## Verification

```sh
env -u DISPLAY E2R_ACTION_INDEX_PROBE=1 timeout 140 build/Debug/clang21-i386-x11-asan/e2recomp --auto-scene175-visibility /tmp/e2-action384-missing-scene 120 7000
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 timeout 140 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-action384-scene-check 120 7000
```

Inspect logs and actual `scene_slot`; a GDB pause or logging can let the probe observe transient readiness, and a packet's filename does not establish its scene. The plain SDL reference exits 5 after missing that window. Keep indexing opt-in.

Latest verification: all three builds and generator syntax pass; all four scratch outputs match (`/tmp/e2-generator-audit-hl23_86h`). The final default debug/ASan wrapper passes; all 8 arrow cases and the default SDL packet pass. Default scene 175 hashes remain `321e33d6` / `914159a1` / `5cf799a1`. See the [runtime journal](../../../../../journal/entries/runtime-crash-fixes.md) for exact evidence and bounded limitations.

## Review State

1. Planning state: split from Task 01 under the step's one-family rule
2. Implementation state: completed for the message-input/lifetime scope
3. Notes: All four task criteria were checked; the required Task 01 rerun remains unsuccessful and is retained as open. Task 05 repair has since exposed Task 06; resume there before Task 05/01 validation.

## Change Log

### 2026-09-14

1. Recorded the independent missing-scene message failure exposed by action-context recovery.

2. Recovered the live two-string list and original message text, identified missing scene 40 (`mtorc4`), and eliminated the gated ASan lifetime error. Recorded the continuing scene timeout and requester limitations.
