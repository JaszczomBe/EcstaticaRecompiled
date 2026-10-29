# Recover Original Music

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Begin DirectSound Compatibility](../step-05-begin-directsound-compatibility.md)
<!-- /docs-tree:parent -->

Status: implemented with bounded original MIDI and software output verification; human listening open
Parent Step: [Begin DirectSound Compatibility](../step-05-begin-directsound-compatibility.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-29

## Goal

The user selected music immediately after [original game sounds](task-04-recover-original-game-sounds.md)
on 2026-10-29. Recover original track selection, loading, sequencing, authored
loops and transitions through audible playback. Preserve possible original defects;
change game behavior only with a demonstrated reconstruction mismatch. Do not
commit or push, overwrite occupied saves, or replace earlier acceptance limits.

## Implementation

The installed archive carries proprietary SIMD sequences. The original Windows
`SIMD_W95.DLL` converts them to MIDI messages; these are not streamed PCM or
standard MIDI files. The host now exposes one software General MIDI port and uses
the original GM bank, a recovered 20 ms sequencer and external SoundFont instruments.
The pinned, unmodified MIT [TinySoundFont dependency](../../../../../../dep/README.md)
provides synthesis. No original DLL, sequence or instrument bank is added to the repository.

Original-backed repairs restore the missing music directory, real archive loading,
selected-device input, MIDI enumeration locals, script track arguments and preserved
register values, current-track save ownership and the Music setting's stop/restart
calls. Every reconstructed repair is mirrored in `GenerateRecon.js`.

The callback owns a copy of each sequence and touches no reconstructed state,
RNG or replay clock. It mixes with existing sound effects through SDL. The fixed
host output is stereo 22050 Hz, with -6 dB software-instrument gain for headroom.
The original master/channel MIDI volume remains intact. `E2R_AUDIO=off` suppresses
physical output while retaining logical MIDI device availability and track calls.

An external `.sf2` bank is required. Set `E2R_SOUNDFONT` to select one; otherwise
Linux checks `/usr/share/sounds/sf2/TimGM6mb.sf2`, then `FluidR3_GM.sf2` in the
same directory. If loading fails, music remains unavailable and the original
no-MIDI-device path continues with sound effects. F5 uses the existing single
**Ecstatica Recompiled** launch.

## Verification and retained behavior

All **8,486** protected files retain their original hashes. The [music recovery journal](../../../../../journal/entries/music-recovery-2026-10-29.md)
owns commands, private evidence, failures, final counts and limitations.

- All 91 installed GM resources match the original DLL for 10,000 ticks each:
  180,624 MIDI messages, event order, track pointers/delays, tempo/fractional timing,
  sync, stops and restarts in Debug and ASan.
- All 960 directory entries match the original archive loader: 647 loaded resources,
  312 missing entries retaining the previous buffer, and one oversized entry
  rejected at load time. Exact bytes, return values and stream positions match.
- Production synthesis checks nonzero PCM, copied sequence ownership, deterministic
  rendering, stop/remove, missing-bank fallback and logical playback with physical
  output disabled.
- Bounded native music/sound routes check original archive bytes, real Debug
  PulseAudio output, ASan dummy output, independent Music/Sound settings, restarted
  gameplay music, HUD/F3, Enter/Escape inventory, menus and Quit.
- Protected private persistence checks music's current track and enabled state,
  equipped actors, HUD/inventory and same/fresh-process restoration. Fresh strict
  recordings check original resource/start/stop calls with inspection, pause and
  physical audio disabled.

Retain authored per-track loops, strict negative-delay event dispatch, cached
channels/notes and fractional phase across restarts. The original DLL repeatedly
updates track zero in its volume helper and reentrant timer branch; those defects
are preserved. A missing archive entry still leaves the previous sequence loaded.
The oversized track belongs to hardware bank 8, track 88; it must not invalidate
other banks during directory import.

## Acceptance limits

Software SoundFont timbre is not equivalence to a particular 1990s MIDI device.
Human F5 listening, exhaustive in-world transitions, hardware FM/AWE banks,
loose/secondary resource routes, device-loss recovery and latency remain open.
SDL focus latch checks do not qualify the legacy Windows focus/surface-loss music
restart path; original restart is conditional on lost-surface restoration and is
not broadened here. MIDI timing/state equivalence is established by bounded original
DLL fixtures; wall-clock PCM is not compared across replay processes.

Earlier sound event/device, inventory/hourglass/low-mode, visual/model, castle
route/armour/gate and incomplete-recording limits remain. Isolated noncombat
persistence does not supersede previous failed live-combat attempts. Preserve the
occupied runtime slots 5/123, 6, 7 and 9 and all protected crash/session evidence.
