# Courtyard Camera Traversal — 2026-10-19

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user confirms that input now works and reports no view change when Joe leaves the pedestal. This continuation recovers the required camera and terrain-script contracts. SDL Debug and ASan both complete **camera 175 → 166 → 175** using actual SDL keys, retaining Joe with wait/modal zero. This is bounded view traversal; movement fidelity, complete collisions, sustained-time acceptance and full experimental ASan remain open.

## First Divergence: Camera Slot Used As Script Resource

An input-only Debug probe reaches `8984,3712,-15975` in camera 175, then selects courtyard camera 166. It stops advancing because `FUN_0044c224` calls the added `E2R_ActivateSelectedSceneRecord(166)`. That helper treats a camera slot as a FAN script-resource ID. `FUN_0045233c` cannot find the resource and enters its missing-scene requester before background loading. An interrupted stack identifies `0x45233c → E2R_ActivateSelectedSceneRecord → 0x44c224`; the high-CPU host event loop is the requester, not a camera-query failure.

Original **0x44c2e5..0x44c302** writes the selected view and reload-tick flag, calls `0x44c6bc` to install the camera, then calls `0x449b4c` to load its background. It does not activate a script resource using that view number. The extra helper call is removed from ordinary camera changes. Existing script-owned activation and the earlier one-shot Start_sc handoff remain unchanged; this repair does not invent scene-resource identities or activate NPCs.

The selector also read `DAT_0047a778`, a separate generated variable, after writing/testing `_DAT_0047a778`. Original **0x44c296/0x44c29d/0x44c2a6** use the same cached dword and its low word. The read now uses `(ushort)_DAT_0047a778`. This fixes a separately demonstrated cached-camera branch; it was not the first failure on this stair route.

## Required Terrain Script Entry

Removing the wrong resource activation allows camera 166/background loading, then exposes a crash in `FUN_0044f508` through **0x44c164 → 0x44f310**. The reconstruction called the wrapper without its EAX code record or EDX actor. Original **0x44c206..0x44c218** selects `code_table[(descriptor_script & 0x3fff)-1]` and passes the current actor. Original `0x44f310` forwards that actor twice and clears the child/node arguments.

The terrain caller now uses the already recovered `FUN_0044f320(code,current_actor,NULL)` contract, which supplies those inputs and retains nested dispatch ownership. Terrain scripts still execute; they are not bypassed to obtain a camera change. Both reconstructed repairs and the removal of the unsupported activation are mirrored in `GenerateRecon.js`.

## Original-Code Comparisons

`scripts/check-e2-scene-grid.py` retains the original unsigned grid tests and now also extracts the production camera selector, transition dispatch and terrain-script caller. Normally and with ASan it passes:

- 16,384 descriptor/grid cases, including 32,845 high-ceiling descriptors.
- 16,384 camera/hint cases, poisoning the separate generated alias to detect stale reads.
- 1,199 camera/background dispatch cases, checking the original view/tick writes, call order and absence of script-resource activation.
- 16,384 terrain-script cases, with 5,646 dispatches checking the selected code, actor and descriptor flags.
- Four original no-view fallback cases; resource 7 routing remains intact.

The existing script-flow comparisons also pass normally/ASan: 176 cursor cases, 64 wrapper inputs, 32 nested ownership cases and 243 diagnostic graphics operand spans.

## Actual SDL Crossing And Return

`scripts/probe-e2-player-motion.py --camera-round-trip` starts at the observed release checkpoint, tries Up for at most 120 updates, then tries Down if still in camera 175. Once the adjacent camera is observed it releases input, reverses the successful movement key, and checks camera 175 and floor height 3328. It verifies Joe remains current, wait/modal stay zero and all arrow bytes clear after release. The report records actual held-key and camera/position samples; all coordinates, facing and cameras are read-only.

| Runtime | Outward camera 166, held | Return camera 175, released |
| --- | --- | --- |
| Debug | Up: `8541,4096,-15319` | Down: `9915,3328,-16926` |
| ASan | Down after the initial Up attempt: `7361,4096,-16900` | Up: `7967,3328,-19358` |

Prefixes `/tmp/e2-traversal-route-{debug,asan}-final` contain JSON, logs and normal game/SDL visibility packets. Both complete without sanitizer diagnostics. Debug courtyard and return images were inspected: the overhead courtyard background replaces the pedestal background, then the pedestal view returns with Joe's cylinder visible. A longer Debug exploration also reaches camera 167 (`/tmp/e2-traversal-grid-code-debug`).

The ASan route differs substantially from Debug and returns to a different location within camera 175, not Joe's exact starting coordinates. An Up-only attempt did not cross within its bound; Down did. This is camera/resource traversal evidence, not proof of identical steering, exact retracing or full gameplay. [Task 07](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-07-recover-motion-query-steering.md) retains the motion-query input/fidelity investigation. Floor heights change on the stairs, but complete collision/falling behavior is not established.

```sh
python3 scripts/check-e2-scene-grid.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-scene-grid.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
python3 scripts/check-e2-script-flow.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp --camera-round-trip --timeout 110 \
  --output /tmp/e2-traversal-route-debug-final
DBUS_SESSION_BUS_ADDRESS=disabled: python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl-asan/e2recomp --camera-round-trip --timeout 110 \
  --output /tmp/e2-traversal-route-asan-final
```

The probe uses dummy SDL, zero logo delay and timed Space, followed by an observed action/release checkpoint. It does not reproduce the recording's two launches or exact logo/horseback timing. D-Bus is disabled only for these headless processes. Cylinder/action-index/mesh-bypass/background-spawn-deferral flags remain explicit; original models/HUD and full NPC activation are still omitted. No 60-second-after-readiness or full experimental ASan acceptance is claimed.

## Verification And Worktree

All four SDL/X11 Debug/ASan builds pass. Generator syntax, in-place regeneration and independent four-artifact parity pass; the reconstructed C diff contains only the terrain caller, cached hint and ordinary camera activation removal. Baseline runtime wrapper, all eight Debug/ASan arrow rows and both SDL requester/OK/Escape drivers pass. Logs use `/tmp/e2-traversal-{build-*,regression,controls,modal-*}` prefixes.

The starting worktree and index were clean. `/tmp/e2-traversal-start-index.txt` remains unchanged; this continuation leaves its changes unstaged and makes no commits. [Task 08](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-08-recover-courtyard-camera-transitions.md) records the completed bounded transition repair. Task 02 retains broader control/collision/sustained-runtime acceptance.
