# 2026-10-16 — Forward/Turn Caller Actor Ownership

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user reports that cylinder rotation works after the intro, but pressing Up then crashes in `FUN_0042b074`, called by `FUN_00427584` at line 21323. This matches the previously recorded combined-input failure and is now repaired in both player-state-4 forward/turn branches. The independent ASan gravity/release frontier remains open.

## Cause And Repair

The player update reads direction bytes into `uVar25` and related locals. Two combined forward/turn branches passed that byte as the actor argument to `FUN_0042b074`. The observed value is **1**, so the turn helper writes to `1 + 0x92` instead of Joe's facing field.

Original `0x429645..0x42965e` and `0x42967b..0x429692` read the signed rate at actor `+0x170`, scale it by ±16, and explicitly reload EAX from the retained actor at stack `+0x2a` before calling `0x42b074`. Both C callers now pass `local_6c`. The existing angle arithmetic remains unchanged. `GenerateRecon.js` mirrors exactly these two substitutions; generated source changes from the prior continuation are two argument replacements.

## Verification

`scripts/check-e2-player-turn-callers.py` compares the two production call statements with original i386 instruction blocks, intercepting the turn leaf. **1,296 cases pass normally and under ASan**: both directions, three actor addresses, signed rate boundaries, unrelated neighboring words and poisoned direction values. Existing motion-query comparisons also pass normally/ASan (394 polar and 92,160 actor/query/matrix cases).

Before repair, `/tmp/e2-player-turn-before-debug.log` reproduces the user's exact stack by holding Left, then adding Up: `FUN_0042b074(param_1=1,param_2=0)`, through the same player-update call site. No game coordinates, facing or camera are forced.

The durable motion probe adds `--turn-forward left|right`, which holds the turn key before adding Up, then releases both. A debugger breakpoint records every turn helper's actor/angle and stops if the actor differs from Joe. Raw held-key assertions and normal presentation packets remain active.

```sh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl/e2recomp \
  --turn-forward left --frames 20 --output /tmp/e2-player-turn-debug-left
# Repeat with right, and with clang21-i386-sdl-asan.
```

| Runtime / turn | Combined-input result | Release result |
| --- | --- | --- |
| Debug Left+Up | 20 calls retain actor `0xaa6bd8`; Joe moves to `9938,3328,-17413`, facing -19773 | Position/facing unchanged; both held bytes clear |
| Debug Right+Up | 20 calls retain actor `0xaa6bd8`; Joe moves to `9951,3328,-17376`, facing -5418 | Position/facing unchanged; both held bytes clear |
| ASan Left+Up | 20 calls retain Joe; moves to `9932,3328,-17426`, facing -22022 | Probe completes but height becomes **-6400**, so this is not valid release behavior |
| ASan Right+Up | 20 calls retain Joe and a combined-input packet is captured | Height becomes **-16000**, fallback resource 7 starts, then the root-pose child walk faults |

Prefixes are `/tmp/e2-player-turn-{debug,asan}-{left,right}`. The ASan Right probe correctly returns failure and retains its completed phases/call records. Fixing the reported caller crash does not fix the separate floor/gravity producer in [Task 06](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-06-recover-release-gravity-query-ownership.md). Full experimental ASan, sustained playability and traversal remain unproven.

All four builds and generator syntax/four-artifact parity pass (`/tmp/e2-player-turn-generator-el5o_9x3`). Default runtime wrapper (`/tmp/e2-player-turn-regression.log`), all eight arrow rows (`/tmp/e2-player-turn-controls.log`) and both SDL requester drivers (`/tmp/e2-player-turn-modal-{debug,asan}-driver.log`) also pass. These baseline checks do not close experimental ASan acceptance.

The starting index is preserved (`/tmp/e2-player-turn-start-index.txt`); all continuation changes remain unstaged, and no commits were made.
