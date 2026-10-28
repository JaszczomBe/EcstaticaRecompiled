# Tower key progression and original models — 2026-10-28

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Result and implementation

The loaded tower puzzle works through its original mechanism. From the user's
slot **6/DFGSDRG**, ordinary sword input strikes head **265**, the key-drop scene
lowers key **264**, Space acquires it, and approaching door **266** with that key
starts the original opening sequence. The key transfers from Joe's hand to the
door socket, blocker **443** moves along its authored track, and Joe actually
passes through the doorway. Bounded Debug and ASan acceptance now cover these
stages, unsuccessful locked behavior and persistence before/after acquisition
and door passage. Human F5 visual review and wider tower journeys remain open.

The missing render selection obscured the head, key and trap mechanism. F5 now
adds original owners **259/pike, 264/key3, 265/keyhed3 and 266/door3**, bringing
explicit selection from 47 to **51 owners**, alongside the existing 16 families.
This is a selective launch configuration change using the existing recovered
renderers. No reconstructed C or `GenerateRecon.js` repair was needed. No key
was spawned, repositioned or forced into inventory; no trap condition, collision,
damage, loaded progress, door condition or blocker was bypassed.

[Step 12 Task 03](../../implementations/playable-sdl-runtime/steps/step-12/tasks/task-03-recover-tower-key-trap-and-door-progression.md)
owns this bounded acceptance. The [handoff](tower-key-progression-handoff-2026-10-28.md)
remains the historical human report and source/save inventory. Existing staged
handoff changes were preserved, with subsequent current-state edits left unstaged.
No commit, push or tag action was requested or performed.

## Evidence preservation and exact reproduction

Source session **20261028_161516_514**, its pinned Debug executable and all three
occupied runtime saves were copied into `/tmp/e2-tower-20261028/`. The 46 copied
files have a read-only SHA-256 inventory in `source-sha256.json`; source data and
session metadata were not changed. The ordinary exporter could not create its
retention lock in the read-only source directory, so preservation used a direct
copy before native execution. Test runs use private data directories throughout.

The pinned executable SHA-256 is
`d4af20e324efe494a22c8efb69fce69faf5b95efb0d183cf4dd7206e5e5c8a00`.
The corrected exact replay, using all preserved runtime saves and the recorded
startup environment, **MATCHED** sequence **432662539**, last matching checkpoint
**964**, and exited zero. Evidence is in `replay-protected-result.txt` and
`replay-protected/logs/`. A separate read-only GDB replay stopped at
`FUN_004544a4(param_1=6)` with menu selection **6**, then returned Joe at
`(-18881,-3328,-1032)`. This establishes the selected file, rather than inferring
it from its label or from an installed-save fallback.

The occupied runtime files retain the handoff hashes:

| Slot | Label | SHA-256 |
| --- | --- | --- |
| 6 | DFGSDRG | `5da846d89e4fae206e87ac9016d0f006e6790c9d6547c285e4e73d2f79442e8a` |
| 7 | COURT | `880abe065c2fd9c5bd255550f93694216cd3e66e66888b4d7fe12aa9e84dca64` |
| 9 | Quick save | `a314c1287b937cf9f95f360fe3539b01c6ebd412d9629f55fa5333c41c3167c0` |

Retained unsuccessful reproduction attempts are separate from that match:
sandboxed i386 execution exited **159**; adding dummy SDL to this recording was
rejected for an extra startup environment key; an attempt without copied runtime
saves diverged after checkpoint **654**. None changed input metadata, replay
checks or user saves. The final exact replay does not claim successful key
acquisition: it reproduces the user's unsuccessful attempt and death-scene path.

## Original mechanism and source contracts

Original `OFFSETS`, `Files/ECSTATIC`, `Code/ECSTATIC.FAN`, representation/action
records and original `E2WIN95.EXE` instructions provide the contracts:

- Head **265**, representation **52/keyhd3**, maps its hit slots to action
  **334/keyhd3**. That short action dispatches stored callback **136**, meaning
  script **135/dav:keyhd3**, whose code is `PlayScene 83`. A successful ordinary
  Ctrl/Up sword attack at the head runs that original path.
- Scene **83/key3** owns the coordinated spike, head and key tracks. Key **264**
  starts at the authored elevated `(-18432,-3776,-620)` and ends at
  `(-18292,-3328,-1088)`. The unchanged generic pickup path then acquires it with
  Space in Joe's node **7**. No assumption that elevated contact should collect
  it is needed.
- Pike **259**, representation **53/pikerep**, uses action **336/pike_srk**.
  Script **137/dav:hdeth1** tests the negation of scene **83**'s active flag before
  starting scene **65/hdeth1**. The prior attempt's positive final health does
  not establish completion or release from that authored scene.
- Script **138/dav:h_doropn** requires its original facing condition and key
  **264** attached in the authored hand before starting scene **68/h_doropn**.
  The condition interpreter checks the actual node's attachment identity,
  distinguishing an empty hand, sword **3717**, and key **264**.
- Scene **68** attaches key **264** to door **266**, node **8**, and moves blocker
  **443** from `(-19456,-3328,-1792)` to `(-19456,-4032,-1792)` at its authored
  track boundary. The door scene ends at progress **273**. The blocker remains
  an original actor; it is not deleted to make passage succeed.

New `scripts/check-e2-tower-conditions.py` executes the complete extracted
production `FUN_0044e810` and original instructions **0x44e810–0x44f2fc** with an
explicit original stack-argument adapter. **2,720 cases per mode** compare scene
active/completed flags and negation, all facing quadrants, both hand nodes with
key/sword/empty attachments, result values and exact cursor advancement. Native
scene/actor storage is mapped; resource loading and script execution are outside
this fixture. It passes normal and ASan modes and is registered as
`debug.Original.TowerConditions` / `asan.Original.TowerConditions` in the suite.

Unchanged related original-code fixtures also pass: pickup query/caller
(**12,288 cases**), script cursor/wrapper/nested ownership, action pose events
(**3,072 cases**), object activation/visibility/preload (**10,240 cases per
mode**) and original box geometry (**1,024 cases / 12,288 faces per mode**).

## Native Debug/ASan acceptance

`scripts/probe-e2-tower-progression.py` and `scripts/e2_tower_steps.py` now provide
an input-only bounded fixture journey. They consume an explicit copied save set
and the current F5 render selection. Installed and supplied saves are copied
into each private runtime directory; only confirmed-empty private slot **5** and
its subsequently probe-owned bytes are writable. A writer breakpoint enforces
ownership, and source/installed/unowned-private file hashes are checked even on
failure. Recording is off; the five processes quit through actual menus.

Evidence is under `/tmp/e2-tower-20261028/debug-final/` and
`/tmp/e2-tower-20261028/asan-acceptance/`, including `report.json`, per-process
GDB logs, state/scene/attachment samples, raster before/after pages and frames.
The verified executable identities are:

| Build | SHA-256 | Main journey updates |
| --- | --- | ---: |
| SDL Debug | `07d09576e2e0ba1ae851c5164ec48cde4437864774dbaa5f238bce767e198947` | 797 |
| SDL ASan | `dd6977ef80a08b7feb684f201dce47b924962cc1dbe9c8392b12f80ec8bd56c0` | 787 |

Each configuration passes:

1. **Locked:** approach with the existing sword, then ordinary forward input.
   Scene **68** stays inactive, blocker Y stays **-3328**, and Joe cannot pass.
2. **Before acquisition:** save the loaded state, load it in the same process,
   and preserve the elevated key, closed blocker and original scene phases.
3. **Head/drop/pickup:** ordinary turning and Ctrl/Up hit the head; scene **83**
   completes the original key track; a bounded approach and Space attach the
   original key reciprocally to Joe node **7**. Health stays **69** through this
   stage. Save/Load preserves actor state, action/script ownership, scene flags
   and key attachment.
4. **Door/passage:** holding the key, approach from the original side and walk
   forward. Scene **68** transfers the key to door node **8**, moves the blocker
   to Y **-4032** and releases Joe to X **-19582**, beyond the doorway at
   X **-19456**. Health is **74** after the authored sequence. Save/Load preserves
   that door/key/blocker state and actual passage position.
5. **Fresh processes:** independently load each of the three saved stages,
   compare serialized actor/action/script/attachment/scene state at loader return,
   verify puzzle ownership after resume, and demonstrate ordinary turning.

Actual original pixel writes are observed separately for all four selected owners:
spike **259** flat/rounded, key **264** flat/rounded, head **265** rounded, and door
**266** flat/rounded. The ASan run observes respectively **23/13**, **27/67**,
**498**, and **7/30** changed pixels in its first accepted primitive calls. These
are bounded per-call writes, not total object area. Successive state/frame samples
record the key-drop animation, door rotation/attachment and repainting.
Both configurations retain F3 original/mixed/boxes cycles, unchanged gameplay
pages/poses during selection, original HUD/F1/F2, previews/menu layout and clean
native exit. Their ten native processes report exit zero without sanitizer errors.

An earlier natural approach probe (`natural-03`) missed a 130-unit pickup waypoint
at the observed collision boundary; this remains a failed navigation probe. The
accepted route stops within 280 units and lets the original facing/range/Space
pickup select the key. No actor or collision data is changed. The prior
`natural-04` exploratory route also successfully continued into camera **17**;
the accepted persistence route stops immediately beyond the door in camera **28**
to retain and verify the relevant loaded actors.

## Preservation, regression checks and remaining limits

All four SDL/X11 Debug/ASan builds pass. Independent regeneration matches all four
committed generated artifacts. The suite's **67** runner contracts pass after
registering the two new condition cases (241 catalogue entries). The initial
catalogue check exposed its expected hardcoded 239 count; it now expects 241 and
explicitly requires both tower cases.

Separate explicit recording tests use the final 51-owner/16-family F5 selection,
player/NPC meshes, **8 KiB** chunks and inspection. Debug and ASan each record the
bounded existing menu route and pass all five independent replay variants.
Evidence is in `debug-recording/report.json` and `asan-recording/report.json`.
These establish recording/inspection preservation; they do not constitute a new
recorded tower playthrough. The original tower recording has its separate exact
pinned-replay evidence above. Documentation-tree update/check and whitespace
validation complete the repository checks.

User runtime slots **6/7/9**, all installed saves and all unowned private saves
remain unchanged. No original game asset or source recording was edited. No
runtime logic, serialization or generator changes were introduced. The normal
human launch remains the single **Ecstatica Recompiled** F5 entry.

Human visual acceptance, other tower saves, unarmed head hits, alternative
approaches, trap death/retry completion and wider tower traversal remain
unqualified. The whole regression suite and broader acid/decorative/audio work
were not run or accepted here. Remaining variants and natural acid lifecycle
continue in Task 02; game sounds and music remain deferred.
