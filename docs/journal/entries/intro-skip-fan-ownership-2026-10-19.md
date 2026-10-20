# Intro Skip FAN Ownership — 2026-10-19

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

## Report And Reproduction Limit

The user reports a crash at the beginning of the second intro after pressing Space to shorten the horseback intro. The supplied stack enters `FUN_00444330` through `FUN_004453a4 → E2R_ParseArchiveFanResource → FUN_00452140`, inside `PlayScene` and an action callback (`FUN_0044f508 → FUN_0044f320 → FUN_0042b880`). Its failing line is the type-0x15 actor postprocessing write.

The initial no-input intro and an isolated prior-source executable's third-action Space replay both complete here. Therefore the exact reported runtime failure is not claimed as reproduced. A focused fixture demonstrates the broken shared-handler selection when a FAN load runs under a suspended action event, and compares the repaired calls and field writes with original instructions. Runtime checks cover the user's confirmed Space route as well as the natural intro.

## Repairs

Original `0x44453b..0x444547` passes the actual FAN record in EAX and the parser's current actor in EDX to `0x42b880`. The reconstructed shared handler preferred `E2R_action_event_context` whenever it was nonzero. During a nested archive load this can dispatch the suspended outer event instead of the actor record; the null actor required by a constructor also trips the action-event entry guard, leaving the parser without its actor.

`E2R_DispatchFanActorRecord` now explicitly selects the FAN record while preserving/restoring the suspended event and prior FAN-record context. The parser still runs the original constructor and records; it does not skip a record, manufacture an actor or add a null guard to the failing finalizer.

The same finalizer contained incorrect widths/offsets. Original `0x444556..0x444631` updates 16-bit flags at actor+2, type/version-specific flag bytes at +2/+3, a short at +0x144 and a short at +0x146. The reconstructed casts instead masked a dword at +4, used byte +1 in several branches and wrote dwords at +0x288/+0x28c beyond the actor. `E2R_FinishFanActorRecord` restores the original short and byte writes for every version boundary.

`FUN_00452140` also normalized an uninitialized `in_EAX` before considering its argument. A coincidentally valid scene pointer could select another scene. Original `0x45214f..0x452157` uses the supplied EAX scene; the loader now normalizes that argument directly, with no camera-pointer fallback.

All three repairs are mirrored in `GenerateRecon.js`. This does not close full experimental ASan, enemy combat, other interactions or the previously failed populated return-floor checkpoint.

## Verification

`scripts/check-e2-fan-actor-record.py`, normally and with ASan, compares:

- 256 scene-input cases, including a null scene with a different valid current scene.
- 128 original FAN record/actor handoffs, including null-actor construction entries, suspended-event negative controls and nested context restoration.
- 7,168 actor-finalizer cases across versions 0–55, comparing adjacent memory as well as the actor fields.

Original x86 bytes execute with only the shared-handler entry intercepted for input observation. Finalizer instructions execute directly. Game assets remain outside the repository.

The motion probe now supports `--intro-skip-action N`, which uses the actual `--run-recon` entry, observes distinct horseback action pointers, sends/releases a real SDL Space tap at the selected action and records the checkpoints. `--natural-intro` uses the same entry without Space. Neither mode changes actor state or action progress. The default zero-logo-delay diagnostic route remains separate from physical logo skipping.

```sh
python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --intro-skip-action 3 --pedestal-guards --frames 3 \
  --output /tmp/e2-intro-skip --timeout 120
```

Initial passing captures:

| Check | Evidence prefix |
| --- | --- |
| Debug Space at actions 1, 3, 6; restrained/released guards and all arrows | `/tmp/e2-intro2-skip{1,3,6}-debug` |
| ASan Space at action 3; restrained/released guards and all arrows | `/tmp/e2-intro2-skip3-asan` |
| Natural Debug intro, guarded release and arrows | `/tmp/e2-intro2-fixed-debug` |
| Prior-source third-action Space comparison (also passes; not a reproduction) | `/tmp/e2-intro2-skip3-before` |

The first three recorded action checkpoints are views 1073, 1072 and 314. They are observed checkpoints rather than timings inferred from the reference recording. The isolated prior-source executable was built under `/tmp` from the previous C snapshot, with current unchanged support objects, without changing the working source or index.

Generator syntax, stable in-place generation and independent C/header/globals/names parity pass. All four SDL/X11 Debug/ASan targets build. Final validation logs and limits follow below.

## Final Checks

- Debug Space at action 3, both guards before/after release, camera 175→166→175, floor 3328 and five seconds idle pass: `/tmp/e2-intro2-debug-route{.json,.log}` and `/tmp/e2-intro2-final-skip3-debug-route.log`.
- Natural intro completion and all four arrows pass under ASan: `/tmp/e2-intro2-natural-asan{.json,.log}`. Both guards retain their original IDs and projected cylinders before and after release.
- Normal/ASan FAN-record fixtures, the ASan population dependency fixture and script-flow fixture pass: `/tmp/e2-intro2-{fixture-asan,final-fixture,final-population,final-script-flow}.log`.
- The baseline runtime wrapper passes: `/tmp/e2-intro2-final-baseline.log`.
- An initial matrix run on the shared X display missed the Debug Down latch while unrelated key messages (for example W/R/Z) entered the game. Keep that failure at `/tmp/e2-intro2-final-controls.log`; the rerun without DISPLAY passes all eight rows in `/tmp/e2-intro2-final-controls-headless.log`.
- Default SDL requester/OK/Escape checks pass in Debug and ASan: `/tmp/e2-intro2-requester-{debug,asan}-command.log`.
- The original staged index still matches `/tmp/e2-intro2-start-index.txt`. New fixes, fixtures and documentation remain unstaged; no commit or tag is made.

The exact user-reported launch sequence still requires physical F5 confirmation. These bounded results do not establish complete experimental ASan or general scene interaction.
