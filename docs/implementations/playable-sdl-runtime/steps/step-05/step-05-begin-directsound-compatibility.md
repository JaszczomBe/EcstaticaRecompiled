# Begin DirectSound Compatibility

<!-- docs-tree:parent -->
[Project README](../../../../../README.md) · [Parent: Playable SDL Runtime](../../playable-sdl-runtime.md)
<!-- /docs-tree:parent -->

Status: game sounds and software General MIDI music implemented; bounded source/PCM/device verification, human listening open
Parent Implementation: [Playable SDL Runtime](../../playable-sdl-runtime.md)
Last Updated: 2026-10-29

## Goal

Restore audible original **game sounds** after the Enter inventory/status menu
recovery. On 2026-10-29 the user selected sounds as the next implementation
focus; the subsequent music selection is now owned by [Task 05](tasks/task-05-recover-original-music.md). [Task 04](tasks/task-04-recover-original-game-sounds.md)
owns end-to-end sound recovery, using the existing startup, backend and first-buffer
tasks as dependencies. The [handoff](../../../../journal/entries/game-sounds-handoff-2026-10-29.md)
records the committed baseline and preservation requirements.

## Current result

[Task 04](tasks/task-04-recover-original-game-sounds.md) now restores original
sound lookup, parsing, buffers and SDL playback. Its [recovery evidence](../../../../journal/entries/game-sounds-recovery-2026-10-29.md)
records exact original comparisons for all 404 assets, real PulseAudio output,
Debug/ASan native sound toggles/lifecycle, protected persistence, HUD/F3/inventory,
four builds, generation parity and strict audio-on/off replay. Human listening,
remaining natural event classes and device-loss behavior remain open. Music continues
in [Task 05](tasks/task-05-recover-original-music.md), with original DLL sequencing,
software instruments, independent settings and protected regression evidence;
earlier gameplay and visual limits are retained.

## Why This Step Exists

Audio was intentionally stubbed while startup, gameplay, input, and presentation were unstable. With live SDL runtime work underway, sound can be introduced as a bounded compatibility surface instead of a source of opaque crashes.

## Scope

1. Map DirectSound creation, buffer, and playback calls reached during startup/gameplay.
2. Decide which behavior belongs to DirectSound compatibility and which belongs to the host backend.
3. Recover original sample loading/decoding and buffer lifecycle, then restore
   actual original-triggered playback, volume/channel rules and stopping.
4. Verify silent/headless operation as a regression mode alongside real output;
   retain deterministic replay and keep device callbacks outside game state.
5. Recover original music selection, resource loading and SIMD sequencing through
   software General MIDI output, with original defects preserved.

## Out Of Scope

1. Complete audio fidelity.
2. Exact timbre of every historical MIDI device and exhaustive music transitions.
3. Mixer latency tuning.

## Usage Budget

No explicit usage/token budget applies. The 2026-10-29 user selection supersedes
the earlier instruction to stop after first-buffer-safe behavior. Investigate
required assets/formats and proceed to actual playback, retaining bounded probes
and honest limits.

## Temporary Sacrifices

1. Sacrifice: Silent success is an intermediate development/test mode only.
2. Why accepted now: Startup and gameplay stability matter more than noisy partial audio.
3. Removal trigger: Buffer format and ownership are recovered enough to submit PCM to a backend.

## Tasks

1. [Map DirectSound Startup Calls](tasks/task-01-map-directsound-startup-calls.md) - recovered within Task 04.
2. [Define Audio Backend Contract](tasks/task-02-define-audio-backend-contract.md) - recovered within Task 04.
3. [Verify Silent And First Buffer Paths](tasks/task-03-verify-silent-and-first-buffer-paths.md) - bounded verification complete; wider fidelity open.
4. [Recover Original Game Sounds](tasks/task-04-recover-original-game-sounds.md) - implemented with bounded acceptance; human listening and broader events open.
5. [Recover Original Music](tasks/task-05-recover-original-music.md) - implemented with original SIMD/GM output verification; human listening and broader transitions open.

## Acceptance Criteria

1. DirectSound call ownership is documented.
2. Startup/gameplay audio calls no longer rely on unexplained stubs.
3. Actual original game events produce the recovered samples through a real
   backend; source/PCM/lifecycle and native Debug/ASan evidence qualify the route.
4. Sound settings, stopping/overlap and original menu/focus/Load rules are
   verified where recovered. Silent logs alone cannot establish audible fidelity.
5. Existing persistence, HUD/F3/inventory, headless and strict replay checks stay
   qualified within their bounds. Tasks 04 and 05 own detailed acceptance and limits.

## Verification

1. Startup/F5 route.
2. Runtime regression script.
3. Affected SDL/X11 Debug/ASan builds, original-code and resource/PCM checks.
4. Protected same/fresh-process persistence, Enter/Escape, F1/F2/F3 and fresh
   sound-event recording/replay; independent generation parity.
5. Human audible review through F5, distinct from dummy-device/native submission
   tests. Keep inventory and inner-castle acceptance limits open.

## Notes

This step should not start by wiring SDL audio directly. Recover the DirectSound-facing contract first.

## Change Log

### 2026-10-29

1. Subsequently selected Task 05 and restored original SIMD music through software
   General MIDI; its task and journal retain bounded acceptance and limits.
1. Selected original game sounds after inventory recovery; added Task 04 and its
   continuation handoff. Silent/first-buffer success is now intermediate only.
2. Kept music later and retained original behavior, save/crash protection,
   generated parity, bounded verification and prior gameplay acceptance limits.

### 2026-07-28

1. Created step.
