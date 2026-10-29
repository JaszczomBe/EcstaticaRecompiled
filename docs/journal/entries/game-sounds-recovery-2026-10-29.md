# Original game sound recovery — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 05 Task 04](../../implementations/playable-sdl-runtime/steps/step-05/tasks/task-04-recover-original-game-sounds.md).
Evidence root: `.tmp/game-sounds-20261029/`. The staged documentation handoff is
preserved. No commit or push was made. Music remains later.

## Reproduction and original contracts

The first natural baseline request is **77**, from an action event through
`0x42fce0`. Its sound index is `0xffffffff`, despite a valid original `OFFSETS`
entry at **13,321,157** in `Files/ECSTATIC`. The flat-archive adapter omitted the
entire sound directory. The missing-secondary guard is not the cause and remains.
The original loader selects **0x47a724** for positive offsets and **0x47a728** for
negative encoded offsets; reconstructed calls incorrectly supplied the current
actor instead of the archive and lost the saved current actor after parsing.

| Original range | Recovered contract and repair |
| --- | --- |
| `0x447d94` sound-directory section | Read 700 big-endian offsets after 2500 scene, 5000 actor, 2000 action and 500 representation entries. The loose archive adapter now validates and imports this original directory: 404 present sounds, 296 absent entries. |
| `0x451a54..0x451bc2` | Preserve current actor/ECX, select main/secondary stream and seek the resource. Keep missing secondary/absent-ID rejection. Loose and secondary resource paths have no new native acceptance. |
| `0x445000..0x4451a5` | Read tail presence byte, little-endian mapped sound ID, flags, authored rate, 32-bit length and version-dependent volume. Subtract the 32-byte sample header before accounting and buffer creation. |
| `0x4269d4..0x426a03`, `0x4537d8..0x453840` | Return the actual sound node; allocate from 200 original 60-byte slots. The former `ZEXT48` stub destroyed the pointer and could exhaust memory through speculative heap fallback. The restored pool follows original free flags and LRU retry. |
| `0x452e5e..0x452e75` | Restore the omitted loop marking all 200 sound slots free during reset, after stopping/releasing their buffers. |
| `0x452958..0x452a55`, `0x4531bc` | Keep the original strict **less than 1 MiB** cache budget, timestamp-based eviction, list unlink, table clearing, byte accounting, Stop/Release and free flag. Bind cleanup to the evicted node. |
| `0x458d18..0x4590bf` | Bind context, resource and stream independently; create an individual secondary buffer with flags `0xe2`, copy 32 metadata bytes, then add 128 modulo 256 to every sample byte. Original buffer format is PCM **mono, unsigned 8-bit, 22,050 Hz**, independent of authored metadata. |
| `0x458c24..0x458d14` | Set volume to `(volume - 127) * 50` hundredths of a decibel. Query actual buffer status: rewind an already-playing sound; otherwise Play with flags zero. Distinct resources can overlap; repeated requests for one resource share and rewind its buffer. |
| `0x42fce0..0x42fe5d`, `0x413ea4..0x413ee0` | Retain sound/device gates, original distance/proximity attenuation, resource percentage scaling, timestamps and cinematic eligibility. Close/channel arguments do not establish a new voice scheduler: the original Windows wrapper only forwards the volume and resource to playback. |
| `0x4594a0`, `0x459440`, `0x4598c8` | Recover DirectSound creation, cooperative level 2, primary descriptor, looping primary Play, GetCaps and buffer/device cleanup arguments. The allocated stereo 16-bit primary-format structure does not establish the secondary sample format. |

The original routine ignores the source sample metadata, including headers that
start with `SIMD`. All **404** installed payloads are compared against executable
original `0x458e7c`, rather than decoding according to that label. No resampling,
ADPCM interpretation or asset replacement is introduced into reconstructed game
logic. Possible original defects remain, pending a proven mismatch and human
listening evidence.

## Compatibility and host ownership

`e2recomp_dsound.c` replaces the shared dummy DirectSound object/buffer with
separate reference-counted buffer storage and the reached vtable methods.
`e2recomp_audio.c` owns copied PCM and independent playback cursors below that
boundary. SDL mixes at 22,050 Hz into signed 16-bit stereo, with logarithmic volume,
pan, saturating overlap, loop, stop and release. Device conversion remains SDL's
responsibility. The callback never accesses game memory, RNG, clocks or replay.
The X11 backend and `E2R_AUDIO=off` retain silent game execution. An unavailable
SDL device reports its failure and continues silently; that case is not output
acceptance. The implemented compatibility surface is bounded to recovered game
calls, not a complete DirectSound implementation. The existing static ACM startup
metric success and 18-byte PCM format allocation are retained; game sounds do
not call ACM stream conversion or `mmio` decoding. Music/streaming shims and
startup allocation/device-error branches have no new acceptance.

`E2R_AUDIO_TRACE=1` records sound ID/length/volume/status/result. Optional
`E2R_AUDIO_TAP=/new/path.s16` captures mixer PCM, exclusively creates a new file,
and caps it at **8 MiB**. Audio mode, trace and tap are host-only replay metadata;
all game settings, strict checkpoints and sound-request identity/volume checks
remain enforced. The SDL audio driver itself remains part of startup identity.

## Fresh verification

- Four SDL/X11 Debug/ASan builds pass. Independent scratch generation matches
  all four artifacts; generator syntax and scoped generated changes pass.
- `check-e2-game-sounds.py`, Debug and ASan: **404** original resources and
  **15,303,877** PCM bytes match, including header bytes and buffer format;
  **1,024** volume/status/retrigger cases; **3,840** event gate/attenuation cases
  with polar conversion intercepted at its explicit dependency boundary;
  **200** original pool-slot comparisons; head/middle/tail cache removal and
  original Stop/Release/free-flag comparisons. Fixtures retain external original
  executable hashes, code ranges and intercepted-dependency provenance.
- `check-e2-dsound.py`, Debug and ASan: production buffer ownership and exact
  mixer PCM, overlap/clipping, gain/pan, loop, stop, position, invalid format/range
  rejection and release pass without a physical device.
- Input-only `probe-e2-game-sounds.py` passes under Debug with actual
  **PulseAudio**, and under ASan with SDL dummy audio. Each observes **49** natural
  requests across **16** sound IDs and compares every submitted sample to the
  original archive conversion. Sound off blocks new requests; on resumes them.
  Already-playing sounds finish naturally, following the original gate behavior.
  Music control state toggles without claiming music output. Enter/Escape,
  original/F1/F2 HUD, all F3 modes, focus events, menus and actual menu Quit pass.
- The real-device Debug probe observes **573,941** mixed frames, **222,867**
  nonzero; ASan observes **589,312**, **221,278** nonzero. Saved taps continue
  through Quit: **2,604,344** and **2,666,496** bytes respectively. This proves
  real device submission/consumption, not human auditory review or speaker routing.
- Protected `--equipment --hud --inventory --population-profile noncombat-opening`
  persistence passes same/fresh processes in Debug and ASan: four clean processes,
  copied source saves, verified empty **private slot 5**, thumbnails, original
  format, repeated loads and resumed input. This is isolated persistence evidence,
  not live combat or extended castle-route acceptance.
- Fresh Debug and ASan recordings each pass **six strict replay variants**:
  three independent runs, inspection disabled, debugger pause, and audio disabled.
  Debug matches **27** checkpoints and **22** sound requests; ASan matches **26**
  checkpoints and **22** requests. IDs, lengths and volumes match the respective
  recording exactly; callback status/capture duration may differ. Audio-enabled
  variants require nonzero PCM. Recordings are separate per configuration.
- Host DirectSound and original sound fixtures join the registered regression
  catalogue. Existing DirectDraw extraction follows its new boundary after the
  dummy DirectSound definitions were removed. Focused HUD/inventory/menu/save
  fixtures pass **20/20**; suite contracts pass **67/67**. The standalone replay
  contract also matches **2,000,001** clock calls with host audio settings changed.

Raw reports, original harnesses, native logs/taps, replay recordings, preservation
inventories and build logs remain under the evidence root. Earlier successful
inventory/rendering probes are not counted as new audio acceptance.

## Counterexamples and remaining limits

The first enabled native parser attempts exposed the allocator and omitted reset
loop above; their crash logs remain. The initial fixture adapters needed correct
mapping bounds, calling convention and stack alignment; failed attempts are
retained. A live Debug persistence route lost Joe before saving; live ASan lost
him after restored input. Neither is reclassified as success. The subsequent
isolated profile proves persistence independently of live combat survival.
The first audio replay attempt correctly rejected a changed tap filename in
startup metadata; the explicit host-only classification above repairs that
boundary, with fresh complete recordings and strict checks. A standalone replay-contract
invocation without its required arguments also aborted; the correctly parameterized
record/play contract passes, with the failed invocation log retained.

Human audible review through the single **Ecstatica Recompiled** F5 launch is
still open, including sample loudness, possible original noisy/`SIMD` payloads,
natural pickup/door/water/late-game event classes, uninterrupted extended routes
and device-loss/reopen behavior. Native tests cover generated focus events, not
all physical desktop/device transitions. Sample-format parity covers all indexed
assets; it does not establish that every authored event can be naturally reached.
Music output, low-mode/planar play, human inventory screenshot/hourglass review,
unresolved tower-door appearance, remaining object/acid coverage, equipped-armour
review and full inner-castle gate/effect composition remain open. The historical
inner-castle recording remains incomplete despite 3,190 matching checkpoints.

## Protection

All **5,843** inventoried files retain their size and SHA-256: installed saves,
occupied runtime slots **5/123, 6, 7 and 9**, crash session
`session_20261028_173846_961`, `.tmp/inner-castle-20261028/preserved/` and the entire
pre-existing `.tmp/enter-menu-20261028/` tree. Original assets remain external.
New probes use private runtime directories and recording off except the explicit
recording/replay checks. No occupied source save or protected evidence is written.
