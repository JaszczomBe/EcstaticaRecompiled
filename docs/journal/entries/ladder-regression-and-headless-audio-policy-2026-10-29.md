# Ladder regression and headless audio policy — 2026-10-29

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 12 Task 05](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-05-recover-object-behavior-rendering-and-interactions.md).
Evidence: `.tmp/ladder-regression-20261029/`. No commit or push.

The subsequent [visible-run correction](ladder-regression-continuous-traversal-2026-10-29.md)
supersedes the separate floor-planned stop/start navigator described below.
The ladder case now uses the existing continuous shared traversal helper with
session-guided position waypoints; fresh visible/headless evidence is recorded
there. Earlier results below retain their original scope.

## User acceptance and requested regression

The user reports that ladder interaction works perfectly. They request silent
headless agent work, except when sound/music is the test subject, and a required
ladder descent/ascent regression. The reported ladder session should guide
navigation rather than supply literal timed input, and unrelated enemy spawning
should be controlled to avoid stochastic combat breaking the test.

This follows the [save-state integrity correction](invalid-court-save-retirement-and-persistence-audit-2026-10-29.md).
No retired COURT/150 state or descendant is loaded, restored or re-created.
The old session182427_259 supplies region landmarks only; all tested gameplay
starts fresh with original life100/power100. The user report is human acceptance
of the interaction; it does not supply a newly identified save/session chain or
qualify the retired save-based acceptance.

## Quiet headless output

`e2recomp_audio.c` now keeps SDL audio output closed by default for headless
`dummy`/`offscreen` video. `E2R_AUDIO=off` explicitly disables host sound and music;
`E2R_AUDIO=on` explicitly opts in, including headless sound/music tests. The check
uses the active SDL video driver, falling back to the configured driver before
video initialization. Normal human F5 output retains its existing default.
Game Sound/Music controls, saved preferences and original game code are unchanged.

The suite and non-audio suite player probe explicitly select output off even if
the parent environment requests audio. The persistence probe selects output off
unless `--music` is the subject, then opts in using dummy audio. Dedicated sound
and sound/music replay probes explicitly opt in. The strict output-disabled
replay variant remains present. The agent instructions and test/build guides
record the same rule; agent tests use dummy audio unless an audible check is
requested.

The DirectSound fixture exercises actual production policy: default headless
opens no output device/audio subsystem, explicit opt-in opens a dummy device,
and explicit off also overrides visible output. Existing manual PCM mixing,
clipping, voices, looping and buffer lifetime checks remain.

## Required ladder case and population fixture

`Interaction.StablesLadder` is required for both Debug and ASan in the full
suite. The new `ladders` block and **Regression 12: Ladders (down and up)** launch
select it with pinned-build, original Space-condition and population-contract
prerequisites. Both shared and isolated execution plans count it as one gameplay
process per configuration. Run:

```sh
python3 scripts/run-e2-suite.py --build --configurations debug asan --block ladders
```

The standalone `probe-e2-ladder.py` launches `e2_ladder_steps.py` in bounded GDB,
with private storage, recording off and host audio off. Save/Load entry guards
reject any persistence call. Source installed save hashes must remain unchanged
and the private save directory must stay empty. No original/user slot is written.

The explicit `noncombat-ladder` profile reuses the audited opening exclusions
**284/gob3,293/gob3b,602/korc2** and existing random terrain-population gate.
It does not infer hostility from collision flags or remove props, doors, items,
animals or authored scene effects. A census at each reached waypoint and climb
completion rejects excluded/scripted IDs or generated-actor leakage and requires
Joe. The production load-gate fixture now checks all5000 IDs in five profiles,
**25,000 cases** per configuration. Normal gameplay does not enable this profile.

Navigation starts through the original intro/pedestal release. A few session
landmarks guide the stairs and scripted stables approach. The courtyard route
uses original floor-map planning and closed-loop observations of position/yaw to
steer SDL input. Bounds limit route updates, waypoint attempts, facing, climb
completion and host runtime. No recording timestamps, snapshot sequence, RNG
values, forced coordinates, health, progression flags or scene-start calls are
used. Temporary input-event allocation and host pumping follow the existing
recording-off regression boundary.

The regression must observe:

- Descent through original scenes **761→762**, ending in kitchen camera723 at
  **(-18104,6656,-14136)** with scene/wait ownership released.
- Ascent through **763→764**, returning to stables camera725 at
  **(-18240,4096,-13712)** with scene/wait ownership released.
- A living, nonmodal player and unchanged starting health for each climb,
  resumed turning at each landing, zero rendered host-audio frames, and normal
  Quit with native exit0. Missing direction/scene, wrong landing, death or lost
  control fails. The suite also rejects partial or inconsistent probe reports.

This verifies the interaction under controlled population. It does not establish
landing Save/Load, other ladders, full animation/composition or combat behavior.

## Retained failures and environmental hazards

All attempts use fresh output directories. `debug-r1` follows one long planned
courtyard shortcut and rejects health loss. `debug-r2` adds region guidance but
still sees a five-point hit. Random/spawned enemies do not leak; a health-write
diagnostic is used to identify the source before changing the fixture.

`debug-r3` stops because its watch expression also tracks the temporary global
actor pointer during resource loading. `debug-r4` watches Joe's concrete life
address instead and records attacker **1127**, damage5, at `FUN_0042efdc`.
This is an authored courtyard projectile, independently mapped in prior object
work. No game/combat defect or new spawn failure is inferred.

The final fixture retains those environmental effects. It requires living arrival
and unchanged health through each ladder climb rather than a fixed full-health
arrival. Both final configurations arrive at life95, descend95→95 and ascend95→95.
No health is repaired, healed or assigned. The temporary diagnostic watchpoint
is removed from the production regression.

## Fresh results

`both-r5/report.json` records **8/8 PASS**, no failures, blocks or skips, in
**68.03 seconds** with concurrent configurations. Debug completes4564 updates;
ASan4479. Both record the required scene sequences, both landings, resumed input,
empty private save directories, preserved source saves and zero host-audio frames.
Binaries are pinned under their build-case directories:

- Debug SHA-256 `b5c9e35185ffc5a9537e7b784759802f71a99641d2b5a091d5e25203ccc19c9d`.
- ASan SHA-256 `3859e20206af1083c9190e262af1651d35903f53aec203f92162135802005ca8`.

The separate final `isolated-final/` run also passes **8/8** in **68.07 seconds**,
using independent fresh starts. It exercises the standalone catalogue path as
well as the default shared plan. All four ladder processes finish with life95
at both landings, without loading any privately saved endpoint. Final evidence
is indexed in `final-report.json`.

`audio-validation.json` records all six Debug/ASan mixer, real-menu sound/music
and replay checks passing. Native audio subjects explicitly use dummy audio;
PCM and software MIDI output remain nonzero. Six strict replay variants per
configuration each match **26 checkpoints**, including audio output disabled,
without relaxing checkpoints or editing source recordings. The changed
music-specific persistence probe also passes in Debug/ASan with private
fresh-game same/fresh Save/Load and inventory/music restoration; all four native
processes exit0 with original/unowned save hashes preserved.

All four SDL/X11 Debug/ASan builds pass. Four-artifact scratch generation parity
matches, with no reconstructed game-code or generator edit in this continuation.
All **69 suite contracts** pass, including inherited-audio suppression, required
ladder registration, profile selection and rejection of partial/asymmetric
results, wrong scenes/landings, lost control, death, invalid seed and audible
non-audio reports. Python syntax, whitespace and the **304-document** README tree pass.

The initial staged patch is preserved byte-for-byte. Existing human saves,
recordings, protection markers and earlier evidence remain untouched. F5 remains
the single ordinary human gameplay launch; only a regression block is added.

## Next continuation and limits

Keep the ladder case required and non-audio agent work quiet. Continue the user's
next object report using an actual valid save/build/session chain. Fresh-game
controlled ladder acceptance does not reinstate old COURT/150,123 orDFGSDRG
progression evidence. Valid-state landing persistence, other ladders, fresh
boots/acid lifetime, full visuals, zero-life control and wider human play remain
open. The full regression suite and visible ladder run are not claimed here.
