# Original Music Recovery — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user selected music after accepting the sound recovery. Start at README,
HANDOFF, the active runtime implementation and [Step 05 Task 05](../../implementations/playable-sdl-runtime/steps/step-05/tasks/task-05-recover-original-music.md).
The earlier [sound evidence](game-sounds-recovery-2026-10-29.md) remains historical
acceptance with its existing limits. Existing staged work is preserved; no commit
or push is performed.

## Original evidence and repairs

Private evidence: `.tmp/music-20261029/`. Original code and assets remain external
under `/home/rgrabowski/Games/Ecstatica2/`.

`SIMD_W95.DLL` SHA-256:
`a61b3c390fe8b4da064c40076df0d3c0e1e90cd19da8e615df0b055518d9106f`.
The fixture copies bounded external PE sections into private executable memory;
only MIDI short-message delivery is intercepted. It executes the original timer,
float conversion, event dispatch, Play and Stop instructions. Windows driver
initialization and OS timer scheduling are outside that fixture boundary.

- EXE `0x4142e4..0x41468d`: track ID in EAX; archive lookup at
  `0x6458a4 + (deviceClass-1)*384 + track*4`, BE32 length, 48000-byte cap,
  signed missing-offset success retaining the old buffer. The original oversized-track
  error requester is retained alongside its zero return and post-length stream cursor. The reconstructed loader
  previously returned success without reading any music.
- Original `0x447d94` directory order: the music table follows 2500 scene,
  5000 actor, 2000 action, 500 graphic and 700 sound entries. Ten banks each
  have 96 entries; the first actual track is 1 at destination `0x6458a8`.
  The installed flat archive adapter omitted this table.
- `0x4597dc`: selected MIDI device in EAX, chosen by startup from `0x479dac`.
  The C register local was unresolved. Enabling enumeration also exposed invalid
  reconstructed capabilities/name locals in `0x4594a0`; those now use real
  52-byte MIDI capabilities and retain the original class selection rules.
- Script `0x450303..0x450365`: requested track remains in EDX across loader/player
  calls. Reconstructed extra-register locals lost it. The saved current-track
  mapped address and exported C value now share writes and synchronize on Load,
  matching original `0x4542b4`, `0x454d86`, `0x454f35`.
- Music setting `0x43d728..0x43d772`: original device gates, stop on disable,
  load/play the current track on enable. The reconstructed requester action
  formerly changed only its label/flag.
- SIMD DLL `0x100011e0..0x10001b2b`: 20 ms sequencing, authored track loops,
  MIDI channel/program/note/controller/pitch/tempo/sync commands, signed volume
  arithmetic and timer rounding. Play argument 1 is a subtune number, not a loop
  flag. The recovered core preserves the original repeated-track-zero defects,
  cached channel/note values and fractional phase across restarts. Opcode `0x9a`
  redirects to the original long-delay idle stream; it does not terminate a track.

All C repairs are mirrored in `E2Recomp/tools/GenerateRecon.js`. The software
instruments use unmodified TinySoundFont commit
`853a0a171759f1ddba0de1442133a75912bbeffa` under MIT; provenance and license are in
`dep/TinySoundFont/`. The external TimGM6mb bank supplies this machine's timbre.
One virtual General MIDI port selects original bank 1. Audio output is stereo
22050 Hz with -6 dB host gain, separate from original MIDI volume. The shared
SDL callback owns sequence bytes and synthesizer state; it never reads game state.
Physical output failure/off does not remove the logical MIDI port. Missing bank
loading reports unavailability and preserves the original music-disabled path.

## Verification

Commands use native i386/ptrace access, explicit time bounds, private runtime
storage and recording off except the named recording/replay checks.

```sh
python3 scripts/check-e2-music.py /path/to/SIMD_W95.DLL
python3 scripts/check-e2-music-loader.py /path/to/E2WIN95.EXE
python3 scripts/check-e2-music-output.py /path/to/E2WIN95.EXE
# Repeat each with --asan; --keep-harness retains provenance privately.
python3 scripts/probe-e2-game-sounds.py /path/to/e2recomp \
  --game-data /path/to/Ecstatica2 --output /private/new-directory --music
# Add --audio-driver default for actual system output.
python3 scripts/probe-e2-game-save-load.py /path/to/e2recomp \
  --game-data /path/to/Ecstatica2 --output /private/new-directory \
  --equipment --hud --inventory --music --population-profile noncombat-opening
python3 scripts/check-e2-replay.py /path/to/e2recomp --inventory \
  --background-spawns --character-meshes --inspect --audio --music \
  --output /private/new-directory
```

Original sequencing passes for **91 GM resources × 10,000 timer ticks** in both
Debug and ASan, comparing **180,624 MIDI messages** plus state and stop/restart.
Original loader comparison passes **960 entries** in both modes: **647** loaded,
**312** missing, **one** oversize rejection. The oversized error requester call also matches. Production synthesis fixtures pass
nonzero PCM, exact copied-buffer ownership, deterministic synthesis, stop/remove,
missing-bank fallback and logical availability with output disabled.

Native routes naturally request tracks **12** (7139 bytes, FNV `1faa26ea`),
**96** (10076 bytes, `34d22833`) and **70** (393 bytes, `93d2a903`). A music-only
bounded PCM tap distinguishes synthesized output from existing sound effects.
The original per-track loops remain responsible for repetition; no host whole-file
loop is added. Trace/tap files use exclusive creation and an 8 MiB PCM bound.
`E2R_MUSIC_TRACE` and `E2R_MUSIC_TAP` are observational replay environment keys.

Four SDL/X11 Debug/ASan builds and independent generation of all four reconstructed
artifacts pass. The three music fixtures per configuration join the registered
suite; **67** suite contracts pass with **253** registered cases. Focused current
regression results and final protected manifests are retained in the private root.
These checks do not claim a full regression-suite gameplay run.

## Final native and preservation evidence

The `*-current` directories qualify the final rebuilt binaries; `final-summary.json`
records their exact hashes, route counts, PCM measurements and retained artifacts.
Earlier attempts are retained separately. Native music/sound routes have a 180 s
process bound; persistence uses 240 s per private process, and replay uses 150 s
for recording and 100 s per playback. Native ASan retains the existing
`detect_leaks=0` policy; no AddressSanitizer errors appear in these final logs.

- `native-debug-current`: actual PulseAudio output, **50** natural sound requests,
  **298,563** nonzero music frames at the observed checkpoint and **396** MIDI
  messages. `native-asan-current`: dummy device, **49** natural sound requests,
  **298,489** nonzero music frames and **396** MIDI messages. Both compare natural
  music bytes to the GM archive, observe stop deactivating tracks, and require
  new nonzero gameplay music after the setting restarts track 70. Existing sound
  off/on, HUD/F3, inventory, input focus latch, menus and normal Quit pass.
- `persist-debug-current` and `persist-asan-current`: four clean native exits,
  two same-process save/load cycles per configuration and a fresh-process Load.
  The original current track is **88**, shared by mapped/exported state. Cycle 1
  restores music enabled; cycle 2 and fresh Load restore music disabled with no
  active tracks. Equipped actor fields, status values, HUD selections and resumed
  movement/interaction pass under the explicit noncombat-opening profile.
- `replay-debug-current`: **27** checkpoints and **22** sound requests.
  `replay-asan-current`: **26** checkpoints and **32** sound requests. Each fresh
  recording independently passes **six** strict playback variants, preserving
  its exact sound requests and three original music resource/start calls:
  three plain processes, inspection off, debugger pause and physical audio off.
  These are separate recordings; their cross-configuration route counts are not
  asserted equal. Each checks nonzero music-only PCM when output is active.
- Current focused checks pass **24/24** across Debug/ASan. The three new music
  fixtures add **6/6** comparisons/output checks. All four SDL/X11 builds,
  independent four-artifact generation, JavaScript/Python syntax, diff whitespace,
  **67** suite contracts and the **295-document** README tree pass.
- All **8,486** protected files retain their sizes and SHA-256 hashes, including
  occupied runtime slots **5/123, 6, 7, 9**, installed saves, crash evidence and the
  entire previous sound evidence tree. Persistence writes only a fresh private
  copy of installed slot **5**, whose source was the confirmed empty four-byte
  marker; the occupied normal-runtime slot 5 is unrelated and unchanged.

`music-preview.wav` is an eight-second excerpt of the music-only Debug PulseAudio
capture for human listening. It is private evidence, not a distributed game asset.

## Failed attempts and limits

The first sequencer comparison corrected an incorrect initial fractional phase
before integration. The first music-specific native probe found no loaded track:
my index validation rejected all banks because unused bank 8 track 88 is 54645
bytes. Original directory import accepts that entry; the original loader alone
rejects it. The corrected comparison also retains the stream position after the
length word on that rejection. Failed harness/native outputs remain in the private
root and are not counted as acceptance.

Software-bank timbre is a host choice, not proof of a particular historical MIDI
card's sound. Human listening, exhaustive transitions, FM/AWE/other hardware banks,
loose resources, device loss and latency remain open. SDL focus events currently
exercise the existing input latch; they do not qualify the original Windows
focus/surface-loss restart path. That original conditional restart is preserved.
Strict replay compares game checkpoints and resource/start/stop identities;
audio callback wall time and PCM are not asserted equal across processes.

Protected occupied saves, the 2026-10-28 crash session, inner-castle and Enter-menu
evidence, and the full prior sound evidence tree are hashed before/after this
work. Private persistence uses only a confirmed empty copied slot, with the
explicit noncombat-opening profile. Previous failed live-combat persistence,
visual/model acceptance, inventory limits and the incomplete original recording
retain their prior status.
