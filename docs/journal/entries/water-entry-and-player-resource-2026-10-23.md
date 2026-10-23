# Water entry and Joe's original resource — 2026-10-23

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user's water-entry menu is reproduced from a complete recording. The menu
follows an incorrect death transition: gameplay loaded potion actor `fpot6` as
Joe, omitting his original water capability. Correct resource identity restores
survival, and Debug/ASan keyboard-only routes now enter the water, complete the
original transition and swim forward with health 100 and no modal.

## Recorded failure

Session `session_20261023_145025_911` is complete. Its pinned executable SHA-256 is
`1abe5444be92c92843c9a1062df9286c757bc2412c957d8ea670f7b0c661d393`.
The immutable export is preserved locally at
`.tmp/replay-bugs/water-entry-20261023`; its manifest verifies successfully.

An exact replay reaches requester **0x27**, the post-death menu, at sequence
**2,106,281,413 / checkpoint 144**. It is different from manual Escape's 0x28.
A hardware watchpoint identifies the first fatal write at sequence
**1,966,422,222 / checkpoint 133**:

- `FUN_00448cb4` queries target `(-1161,5120,-3574)`, terrain type 7.
- Joe is still at land height 4096, state 4 and health 100.
- Original `0x449533..0x449574` gives state 8, reaction 3 and health -100 to
  actors without flag 0x100. The native branch matches those instructions.
- The next update enters dying state 5. Falling to height 5120 and the later
  death/menu are consequences. Suppressing the menu would leave the producer.

Inspection correlated the camera, actor state and replay checkpoints. The saved
binary plus GDB watchpoints established the writer without repeating the route
by hand. Initial health was absent from inspection; it is included now.

## Recovered behavior

The actor section header's global name is word 2; word 1 is a local node number.
The earlier recovery applied that distinction only inside population/event load
contexts and selected scene loads. Ordinary initial loading still indexed local
zero. The final such resource in the archive is **4119 / `fpot6`**.

| Resource | Archive offset | Flags in type-0x15 record |
| --- | ---: | --- |
| Joe / 0 | 1,017,590 | 0x3109, including water capability 0x100 |
| fpot6 / 4119, formerly loaded as 0 | 12,773,490 | 0x0029, without water capability |

The existing recovered gameplay gate (`E2R_ACTION_INDEX_PROBE`, enabled by F5)
now enables global actor identities throughout archive indexing/loading. All
1,922 original actor headers are indexed by their names. The bare historical
baseline retains its existing gate. No player-only immunity, coordinate write,
forced swimming state or terrain change is introduced.

Two adjacent original contracts are also restored:

- Original `0x457715/0x45774f` reads the live swimming-scene flag byte at
  `0x670c44`. The selector used an independent generated scalar that stayed
  stale. It now observes the script table, allowing the transition to finish
  and ordinary swimming actions to remain selected.
- Reload opcode `0x54`, original `0x44fd93`, writes a **word at actor +0x82**.
  A generated dword-array cast wrote +0x104 instead. The packed state write is
  recovered and checked with adjacent memory intact.

Every reconstructed change has a checked generator mirror. Syntax and in-place
regeneration retain exactly the intended C changes; headers/globals/name mappings
have no unrelated drift.

## Verification

`check-e2-water-entry.py EXE ARCHIVE [--asan]` passes normally and under ASan:
all **1,922 actor headers**, **216 original-x86 flag/water-damage cases** and
**256 original-x86 packed reload-state cases**. It reads the installed names and
archive externally; original code/data are not added to the repository.

The selector fixture passes **10,368 original-x86 cases** and **256 packed-key
cases**, normally/ASan, with the generated scene-flag scalar deliberately set
opposite to live script memory. Existing full motion-query comparisons pass
**92,160 cases plus eight saved courtyard samples**. FAN record/finalizer and
population/constructor/callback comparisons also pass.

Fresh natural-intro Debug movement exercises all four SDL arrows with the correct
Joe resource. Separate Debug/ASan routes follow waypoints derived from the user's
path through real SDL key events. They never assign coordinates, angles, camera,
health, action or script flags. These are new input-driven acceptance routes,
not exact replays of the old state.

Both reach **camera 543**, complete action 3's water-entry transition and observe
swimming-scene flag 8, representation 13, state 4, health 100 and wait/modal zero.
Forward input then moves Joe while he remains at water height 5120:

| Build | Before swimming input | After input/release |
| --- | --- | --- |
| Debug | `(-1190,5120,-3328)` | `(-1282,5120,-3011)` |
| ASan | `(-1457,5120,-2754)` | `(-1615,5120,-2380)` |

Initial movement checks stopped before the 57-tick entry action completed and
correctly failed their displacement assertion. The final checks wait for the
original swimming-scene activation before applying movement. Natural startup
with conditional breakpoints at every frame also timed out; using a hardware
watchpoint for script release removes that debugger overhead. The ordinary
motion probe now uses this approach for natural intros without guard checkpoints.

All four SDL/X11 Debug/ASan builds, the existing runtime regression wrapper and
**31 developer-launch cases per SDL build** pass. ASan reports no memory error in
the final swimming route. Original capture replay with the repaired executable
correctly returns **74 / DIVERGED**, sequence 21,659 / last matching checkpoint 11;
changed loading invalidates old service/state history. Compatibility mode does
not bypass that result.

Local route helper, waypoints, final logs/JSON and failure stacks are retained in
`.tmp/water-entry-20261023`. Final `/tmp` evidence prefixes are
`/tmp/e2-water-swim-final-{debug,asan}`; the Debug executable used there has SHA-256
`73b05ac8d616c27867682dbd5914758f6372e493a20570a2e852f34dc742a758`.

## Tool refinements and remaining limits

Inspection now adds observational actor `health`, `water_capable`,
`archive_offset`, plus world `terrain_type`, `map_height_shift` and
`swimming_scene_flags`. These fields stay outside canonical replay sampling;
checkpoint schema/order are unchanged. The observer/reader regression passes.
Agent motion probes place sessions under `<output>-runtime`, keeping ordinary
human-session retention independent of these probes.

Replay and inspection proved useful for a non-crashing gameplay error: a clean
process exit was not mistaken for gameplay success. Water survival and forward
swimming now have native Debug/ASan evidence. Manual F5 confirmation, leaving the
water, held-weapon swimming, combat, original meshes/animation and broader gameplay
fidelity remain separate acceptance. The next object-interaction work remains
workshop re-entry and sword pickup.
