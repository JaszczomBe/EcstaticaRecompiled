# Recover Original Game Sounds

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Begin DirectSound Compatibility](../step-05-begin-directsound-compatibility.md)
<!-- /docs-tree:parent -->

Status: implemented with bounded original/PCM/device acceptance; human listening and broader events open
Parent Step: [Begin DirectSound Compatibility](../step-05-begin-directsound-compatibility.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-29

## Continuation

The user subsequently selected [Task 05: original music](task-05-recover-original-music.md).
The music-later statements below describe this sound task's original scope;
its acceptance and remaining sound limits are unchanged.

## Goal

Restore audible original game sounds after the inventory/status menu recovery.
The user selected sounds as the next implementation focus on 2026-10-29 and
requested a written continuation handoff. Music remains separate later work.
This selection supersedes Step 05's former silent/first-buffer-only stopping
rule: silent operation is an intermediate compatibility and test mode, not
acceptance of restored game sound.

The [sound handoff](../../../../../journal/entries/game-sounds-handoff-2026-10-29.md)
records the committed baseline, source leads and protected evidence. This task
is an end-to-end continuation of the existing startup, backend-contract and
first-buffer tasks; step/task numbers remain stable.

## Current acceptance

Original game sound output is implemented. The [recovery journal](../../../../../journal/entries/game-sounds-recovery-2026-10-29.md)
records the first natural request (77), original directory/parser/pool repairs,
separate DirectSound buffers, SDL mixing and exact preserved sample conversion.
Debug/ASan compare all **404** assets / **15,303,877** PCM bytes, playback,
attenuation, allocation and cleanup. Real PulseAudio Debug and dummy-device ASan
routes verify **49** natural requests each, sound off/on, focus, HUD/F3,
inventory, menus and Quit. Four builds, independent generation parity, protected
same/fresh persistence and six strict sound-event replay variants per mode pass.

Human F5 listening, broad natural event classes, loose/secondary resource routes
and device-loss recovery remain open; music remains later. The isolated persistence
profile does not replace the retained failed live combat attempts. All **5,843**
protected files retain their hashes, including occupied runtime slots and prior
crash evidence. The prior visual, inventory and incomplete-recording limits below
remain unchanged.

## Recovery scope

1. Trace original sound event → sound ID/name → archive offset/record → decoded
   sample → DirectSound buffer → playback, stop and release. Recover compression,
   signedness, sample rate, channel count, bit depth, lengths, alignment, looping,
   retriggering and buffer ownership from original disassembly/Ghidra and data.
   A primary-output format is not proof of each asset's source format.
2. Recover original eligibility gates, Settings sound toggle, volume/distance
   rules, channel selection, overlap/preemption and cleanup. Include representative
   movement, combat, pickup, door, creature and environmental events when the
   original game actually supplies them; do not invent missing event sounds.
   Determine menu, Enter-page, focus, Load and shutdown behavior from original
   code instead of assuming all audio pauses or continues together.
3. Implement the required DirectSound-facing semantics in compatibility code and
   replaceable host audio below that boundary. Reconstructed game rules retain
   original-shaped calls; do not put SDL APIs or asynchronous callback decisions
   into game logic. Callback/device timing must not drive scripts, RNG, game
   clocks or replay checkpoints. Preserve deterministic silent/headless testing.
4. Preserve possible original defects. Require a proven reconstruction mismatch
   before changing event selection, distance/volume arithmetic, channel behavior,
   assets, rejection paths or game state. Do not globally remove missing-archive
   guards or mesh/diagnostic bypasses to make sound appear enabled.

## Read-only source leads

These leads come from current source inspection, not a recovered original sound
contract or a diagnosis. Re-establish register/stack arguments and data ownership
from `E2Recomp/original_disasm.txt`, the Ghidra export and external
`/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` before changing behavior.

| Lead | First question |
| --- | --- |
| `E2Recomp/reconstructed/E2Recomp_stubs.c`: `DirectSoundCreate`, `E2R_DS_CreateSoundBuffer` | Generic no-op vtable entries and a shared dummy buffer currently stand in for audio objects. Which methods, return values, buffer instances and lifetimes do the original callers require? |
| `FUN_004594a0`, original `0x4594a0` | Trace startup/device gates, ACM, cooperative level, primary format/buffer and cleanup; recover unresolved call arguments before enabling playback. |
| `FUN_0042fce0`, original `0x42fce0` | Existing generator repair retains sound/node/proximity/volume/channel arguments. Verify their downstream ownership and original attenuation; do not discard that repair. |
| `FUN_00413ea4`, original `0x413ea4` | Current wrapper passes a sound resource onward but ignores close/channel arguments. Recover original scheduling, duplicate/voice policy and timestamp ownership. |
| `FUN_00451a54`, original `0x451a54` | Audit archive handle `DAT_0047a728`, offset table `0x662f20`, sound table `0x62d960`, resource parsing and the current missing-archive guard. Identify whether silence starts before a valid resource reaches playback. |
| `FUN_00458c24`, original `0x458c24`, and surrounding buffer helpers | Recover actual buffer/volume/status/position/play/stop arguments from original instructions, rather than unresolved decompiler registers. |
| `E2Recomp/platform/e2recomp_win32_compat.c`: `mmio*`; host backend header/SDL implementation | Establish the minimal decoding/device API required by proven callers and the ownership boundary for sample memory, voices and device shutdown. |
| `SIMD_*` imports and `Music/` assets | Separate music initialization/cleanup dependencies from game-sound restoration. Music playback itself remains deferred. |

The installed `Files/` directory contains `ECSTATIC`; inspect its actual resource
index and any original archive-opening paths. Do not assume a separate sound
file exists or conclude from the Trace-level missing-sound message alone that
an asset is absent. The [diagnostic-severity journal](../../../../../journal/entries/input-log-transitions-and-missing-sound-severity-2026-10-21.md)
explains that `Runtime.MissingSound` is Trace-level, not current audio acceptance.

## First bounded action

Read the active implementation and handoff, inspect staged/unstaged changes,
and refresh a read-only hash inventory of installed/runtime saves and protected
crash/session evidence. In private output, map one real startup/gameplay sound
request through the above pipeline, retaining the first missing/incorrect
contract with exact original addresses and resource bytes. Use explicit bounded
input, timeouts and recording off. Prefer a naturally reached event and private
save copies; never force a sound ID, actor state or final playback flag as
native gameplay acceptance.

Compare the smallest suspected mismatch with original x86 before repairing it.
Then mirror reconstructed C changes in `E2Recomp/tools/GenerateRecon.js` and
verify independent four-artifact parity without unrelated generated churn.
Continue through actual decoded sample submission and original-triggered
playback; report remaining event classes or formats explicitly.

## Acceptance and verification

1. Original-backed tests verify representative resource lookup/decoding, PCM
   bytes and format, bounds, volume/pan/channel rules where used, play/retrigger/
   loop/stop and buffer release. Retain original rejection cases and any possible
   defects; a successful no-op or nonzero dummy sample is not sound fidelity.
2. Bounded Debug/ASan native routes connect real game events to the correct
   original sample and actual backend consumption. Retain a PCM capture/tap or
   equivalent measurable output evidence, plus sample/voice identity and bounds.
   Dummy-device tests prove submission/lifecycle only. Human audible F5 review
   remains separate and must not be claimed from a silent driver or logs.
3. Verify Settings sound off/on, overlap and stopping where original-backed,
   Enter/Escape, menus, focus loss/gain, Load and clean Quit. No hung device,
   stale voices, use-after-free or stuck gameplay input should remain in the
   tested routes. Music toggles/dependencies must not regress or become falsely
   reported as restored music.
4. Preserve original-default/F1 HUD, F2 debug display, independent F3 modes,
   original inventory/statistics and thumbnails. Run protected same/fresh-process
   original-format persistence on verified empty private slots, with source and
   unowned-slot hashes. Existing helpers include `probe-e2-game-save-load.py`
   with `--hud --inventory` and the original HUD/menu/save fixtures.
5. Run affected SDL/X11 Debug/ASan builds, relevant original-x86 fixtures,
   generator syntax/parity and documentation checks. Verify a fresh bounded
   recording/replay with sound events and headless/device-disabled operation;
   never relax strict replay or let callback scheduling change game state.
   Existing `check-e2-replay.py --inventory --inspect --character-meshes` covers
   a menu route, not sound events until explicitly extended and observed.
6. Record fresh acceptance, counterexamples and limits in this task, its step,
   active implementation and a dated recovery journal. Historical inventory,
   rendering and persistence checks are regression baselines, not sound proof.

## Protection and retained limits

Preserve occupied runtime slots **5/123, 6, 7 and 9**, installed saves,
`~/.ecstatica2/logs/session_20261028_173846_961/`, the preservation tree under
`.tmp/inner-castle-20261028/preserved/` and inventory evidence under
`.tmp/enter-menu-20261028/`. Recheck actual occupancy and hashes before testing;
never assume an old empty-slot list is still valid.

Keep inventory human visual/low-mode/hourglass limits, unresolved tower-door
appearance, remaining object/acid coverage and inner-castle extended-route,
equipped-armour and full gate/effect limits open. The historical inner-castle
recording remains incomplete despite its 3,190 matching prefix checkpoints.
Do not alter protected evidence to make a new replay pass.

Human investigation uses the single **Ecstatica Recompiled** F5 launch. Agent
probes remain bounded and recording off except explicit recording/replay checks.
No explicit usage/token budget applies. Preserve existing changes; do not commit
or push. The handoff remains historical; fresh acceptance and limits are recorded above.
