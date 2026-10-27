# Game save/load recovery — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 10](../../implementations/playable-sdl-runtime/steps/step-10/step-10-recover-game-save-load.md).
Baseline: v0.2.0, `ae54e6f8e4dc`. Existing handoff changes remain intact, including
changes staged by the user during this work. No commit, push or tag change.

## Save preservation

The user explicitly requires preserving occupied original slots and using free
slots for tests. Read-only inspection finds occupied **0–4, 8, 9**, and empty
**5–7** (four bytes `CR LF CR LF`). All ten installed file sizes and SHA-256 hashes
are recorded in `build/evidence/save-load-2026-10-27/installed-before.json`.
Agent native trials copy every slot into their own runtime directory and select
only an originally empty slot. Tests must never use quick-save slot **9**.

Compatibility now routes `saved/NNNN.ecs` through `--data-dir/Saved`. Reads prefer
the runtime slot and fall back to installed data only when absent. Writes require
a configured writable directory and never fall back. Configuration rejects the
installed save directory itself. Writes reject symlinks and multiply linked
files before truncation. Slot dispositions preserve create/open/truncate intent;
read/write/close errors propagate through the compatibility boundary. Original
resources continue to use the original data directory.

## Original contracts recovered

| Original address | Contract |
| --- | --- |
| `0x43fadc..0x43fb54` | Load selection comes from the item's low seven bits, clears/sets highlight byte bit 3, reads preview, rejects empty/unreadable slots by setting selection to −1, redraws all ten items |
| `0x43fb58..0x43fc2a` | Save selection copies the ten original labels into editable 26-byte buffers and highlights the selected slot; confirmed editing (`0x643644 != 0`) writes the selected slot |
| `0x43c61c..0x43c630` | Load confirmation calls reader with EAX = selected nonnegative slot |
| `0x43c631..0x43c65c` | Save confirmation calls writer with EAX = slot, EDX = `0x643434 + slot * 26`; no separate overwrite prompt occurs here |
| `0x4161f0..0x41620f` | Quick-save reads/clears the live byte at `0x4c39af`, supplies slot **9** and the fixed quick-save label |
| `0x453920..0x45442f` | Writer takes EAX slot, EDX label; opens `saved/NNNN.ecs` as `wb`; normal return is CRT close result |
| `0x454430..0x4544a0` | Separate file-existence helper, not part of the writer |
| `0x4544a4..0x454fa1` | Reader takes EAX slot, opens `rb`, discards 26-byte label, accepts signed version ≥4; destructive reset starts at `0x454577` |
| `0x454fa4..0x454fe1` | Separate vector write/read helpers, not part of the loader |
| `0x417248` / `0x4171b8` | Big-endian 16-bit word write/read for resource/event records |
| `0x417308` / `0x4173c8` | Little-endian 16-bit word write/read for gameplay state |
| `0x454fe4..0x45507b` | Nine matrix words traversed by columns: offsets 0,6,12; 2,8,14; 4,10,16 |
| `0x441370` | Event record writes type, ID, then three parameters, each big endian |
| `0x441600` / `0x441444` | Big-endian 32-bit global write/read via two big-endian words |

The format is **4**, independently of FAN archive version 55. The writer's file
order is:

1. 25-byte padded label plus NUL, little-endian version 4, 80×60 column-major
   thumbnail. Both original low-resolution sampling and high-resolution surface
   sampling are retained.
2. Big-endian root/geometry/constraint/resource records and a zero event.
3. Referenced representations terminated by −1, referenced scenes terminated by
   −1, then active-actor state records terminated by −1.
4. Actor records include +0x82, three vectors +0x84/+0x8a/+0x90, +0x96/+0x98,
   +0xe8 and the original repeated +0x98, +0xea/+0xec/+0xee/+0xf0, +0xc6 matrix,
   +0x182/+0x186/+0x184, action IDs at +0x126/+0x12a, timer entries and action
   ownership/progress. Timers store a signed word difference from `0x636588`;
   load reconstructs expiration relative to its current tick. Attachments store
   owner actor and bone IDs, then rebuild reciprocal pointers.
5. 2500 cached words, 5000 actor-cache records (25 bytes each), visibility
   resources and descriptor flags terminated by −1.
6. Six global words, two big-endian dwords, 150 bytes, variable global records,
   optional settings words and little-endian trailer **0x1234**. The reader also
   accepts an older layout with the trailer immediately before settings.

The loader first recreates the root/geometry hierarchy through the original event
dispatcher, then loads referenced representations/scenes, restores active actor
state/action ownership/timers/attachments, fills inactive caches and visibility,
restores globals, and rebuilds presentation/current player. It does not restore
a memory dump or a replay. The old world has already been discarded if later
record reconstruction fails; no rollback is claimed.

## Recovered runtime behavior

Both writer no-op patches are removed. The writer/loader, word/matrix helpers,
resource records, slot callbacks, short error requester and menu state repairs
are mirrored in `GenerateRecon.js`. Save selection enters original caret/name
editing; OK or confirmed editing writes the selected slot. Repeating Save replaces
that runtime slot without a separate overwrite prompt, matching original
`0x43c631..0x43c65c`. Load selection rejects empty previews. Original
`0x416308..0x41637a` reopens selection after an unselected confirmation; its EDX
comparison is against zero. The reconstructed unsigned selection global needs an
explicit signed comparison for the −1 sentinel. Cancel resumes gameplay.

Resource reconstruction temporarily owns the FAN parse stream only while reading
save records, then releases that context before nested resource loads. Actor
creation receives the record's explicit actor ID (`0x42ba2c`). The matrix reader
has explicit matrix/stream arguments. Hosted streams may be allocated above
`0x70000000` on i386: close now validates magic/registration before the legacy
address guard, propagates write/close errors, frees read storage, and clears a
matching parser context. Actual menu writes return close result **0**.

## Original-code and host fixtures

The `persistence` suite block includes these checks in Debug and ASan. Extracted
production C, original x86 ranges and intercepted dependencies are retained in
per-case `fixture.c` and `fixture.c.fixture.json` files. No fixture writes an
installed save.

| Check | Evidence and limit |
| --- | --- |
| `Original.SaveContracts` | 131,072 endian/width writes, 65,536 little-endian reads, 256 matrix write/read traversals against original bytes; sticky write failures |
| `Original.SaveWriter` | 24 complete original-x86 byte comparisons, low/high thumbnail sampling, nested geometry/constraints, script ownership, relative timers, attachment IDs, caches, visibility and trailer; intercepted CRT/surface calls, memory output |
| `Original.SaveSlotCallbacks` | 80 original-x86 selection, highlight, editable-label, empty-preview and confirmed dispatch cases; writer/preview intercepted |
| `Original.SaveRestoreTimers` | 210 original loader timer-block comparisons with counts 0/1/2/5/99, signed 16-bit differences and uint32 clock wrap; production timer allocator and an explicit known-register adapter |
| `Host.SaveStorage` | Actual routing/dispositions, binary reads, read-only write failure, installed-file and symlink/hardlink protection in synthetic private directories |
| `Host.SaveStreams` | Actual production stream lifecycle at forced high i386 addresses, all 256 byte values, double-close rejection, sticky write/close errors, read-buffer freeing and parser-context release |

These prove their bounded contracts. Native opening saves contain no pending
actor timers; nonempty timer reconstruction is original-code fixture evidence,
not a claim of native potion-effect expiry acceptance.

## Real menu round trips

The reusable command is:

```sh
python3 scripts/run-e2-suite.py --block persistence --configurations debug asan --game-data /path/to/Ecstatica2
```

`scripts/probe-e2-game-save-load.py` copies all ten installed saves privately,
chooses the first confirmed empty menu slot (here **5**) and installs a writer
breakpoint that stops before any unowned slot write. Recording is off, SDL input
is explicit, and each GDB/native process has a timeout and progress watchdog.
It compares the exact writer-entry state with the exact loader-return state,
before resumed gameplay can change it. The fresh process loads from the horseback
intro without assigning player/world state. Both processes finish through actual
menu Quit with native exit **0**. Reports hash-check every installed save and all
unowned private slots even after failure.

`persistence-suite-14` passes **18/18** cases in Debug/ASan, including **eight**
native process exits. The live opening route restores 14–15 active actors; the
controlled workshop route restores six actors and sword **3717**, owner Joe **0**,
bone **8**, with reciprocal ownership. Each same-process journey saves, changes
state and loads twice; the second Save replaces only its test-owned runtime
slot. Fresh-process restoration then uses that last save.

Comparisons cover active identities, serialized actor fields, matrix, action
references, script owner/progress/phase, relative timer chains and attachment
identity/reciprocity. Resumed checks observe changing location and animation
progress, attack input selecting its original animation, and the sword following
Joe after loading. The workshop route crosses cameras **347 → 348** after a
restore. Physical collision and resource/scene reconstruction stay on their
ordinary paths. Labels, version **4**, trailer **0x1234** and actual close results
are also checked. Full worlds, caches and inactive records are exercised by the
byte fixture and original reconstruction sequence; exhaustive world progression
is not established by these opening routes.

The final-runtime `persistence-suite-final-23` repeats those 18 core cases after
the confirmation-pointer repair described below. The permanent catalogue also
includes `Persistence.SaveFailure` in both configurations.

## File rejection and destructive-load boundary

Bounded private-slot tests (`--failure-case`) observe:

| Input | Observed behavior |
| --- | --- |
| Save-open failure | A directory blocks private slot 5; actual menu Save shows `Can't open file to save game`, OK resumes the existing world, movement and Quit succeed; no truncation |
| Unsupported signed version 3 | Actual Load shows `Can't load game` / `Game was saved in old version`; OK preserves the old world and resumes movement/Quit |
| Missing after preview | Remove only private slot 5 after selection, using a private installation facade with no slot-5 fallback; loader reaches `open failed` before discarding the old world |
| Truncated version-4 resource section | Loader reaches `truncated resource records` after the original destructive reset; active world/player are already cleared |

The first four observations are retained under `failure-*-16`. Empty selection
passes in `failure-empty-17` after correcting the probe's unsigned reading of −1.
ASan empty/unsupported/missing/truncated checks pass under `failure-asan-*-20`.
Missing/truncated probes stop at `E2R_LoadSaveFailure` and intentionally kill the
isolated process **before** the existing generic fatal cleanup. They do not claim
clean exit, graceful recovery or rollback for corrupt/missing files. Generic
fatal cleanup and arbitrary malformed-file handling remain unqualified. Files
saved by unrelated original game progressions are read-only references, not
native compatibility acceptance for every progression or version.

## Retained attempts and limits

Sandboxed i386 execution fails with SIGSYS/GDB startup 127. Bounded native checks
use the approved syscall-sandbox escalation. `native-debug-02` exposes an
unwanted startup quick-save: exported `DAT_004c39af` contains unrelated image
bytes, and its old caller forwards unresolved EAX as slot. Original
`0x4161f0/0x4161fb` establishes the live-byte read and explicit slot 9 repair. The
invalid path was rejected before writing. Its short-message crash led to recovery
of explicit EAX string ownership at `0x43cac0..0x43cb16`. Quick-save slot 9 is
source-backed only; native tests never use the user's occupied quick-save slot.

Early probes retain their failures: a premature loader assertion while the
nested menu was still running (`native-debug-04`), deletion of an already
completed GDB FinishBreakpoint (`05`), and a one-direction movement check blocked
at the pedestal (`native-world-debug-09`). The repaired probe waits for loader
return and bounds both forward/backward attempts. A live workshop navigation
trial exhausts its replan budget before Save (`native-equipment-debug-10`);
attachment acceptance uses the existing explicit noncombat-opening population
fixture instead. It does not grant invulnerability, move actors or restore state.

`native-equipment-debug-11`, `native-world-asan-12` and `native-close-debug-13`
retain intermediate successful round trips. The first independent four-artifact
parity checks pass; final fixture/native/build evidence follows below. Existing
further tower play, complete rendering, equipment polygons, full-game persistence,
active potion lifetime/cure and optimized/64-bit runtime limits remain recorded.
Historical full-suite success is not acceptance for every new change.

## Save-open ASan counterexample and repair

`failure-asan-save-open-20` finds a global-buffer-overflow while drawing the
short error requester's OK item. The hosted direct mouse handler makes OK the
selected editable field while retaining the save-name caret index (7). That
points beyond the three-byte `OK` string. Original non-editable click
`0x43b8cd..0x43b947` preserves the active field pointer across the confirmation
callback. The hosted slot-confirmation path now does the same; it leaves the
name field selected until the modal helper clears edit state. This repair is
mirrored in the generator. Both Debug and ASan error-dismiss/resume/Quit probes
pass in `failure-save-open-final-24` and `failure-asan-save-open-final-24`.
`Persistence.SaveFailure` retains the actual native regression in the suite.

## Build and source verification

All four affected presets build: SDL Debug/ASan and X11 Debug/ASan. Final logs
are `build-<preset>-final.log` beneath the evidence root. Independent scratch
generation in `generation-final-22` matches all four artifacts exactly, including
the intentional matrix-reader prototype change. A preceding generator attempt
used a function matcher that excludes plain `int` functions; it stopped before
writing artifacts (`generation-final-21`). The unique mouse-handler anchor fixes
that mismatch.

`affected-regressions-19` passes **24/24** selected checks: generation parity,
all **67** runner contracts, original menus, real DirectDraw surfaces, pickup/
detach/timer/cache contracts, delayed startup, gameplay Load/Save cancellation,
resumed movement and menu Quit in Debug/ASan. That run precedes only the narrow
confirmation-pointer repair, whose real confirmation/error paths are rechecked
above. It is not a full gameplay-suite or tower-play claim.

## Final qualification

On the final runtime, `persistence-suite-final-23` passes **18/18** core cases
(**88.79 s**, eight clean native exits). `persistence-error-suite-25` passes
**16/16** selected cases (**24.11 s**, the same fourteen prerequisites plus the
two new `Persistence.SaveFailure` regressions). Together they cover all **20**
distinct current persistence cases and **ten** clean native exits. Both reports
pin the same final SDL Debug/ASan binary hashes. Each configuration retains six
fixture sources and provenance records. Final runner contracts pass **67/67** in
`suite-contracts-final-25.log`; Python/JavaScript syntax, diff whitespace and
README documentation-tree checks pass.

`installed-after.json` matches every installed save's pre-implementation size
and SHA-256 hash, including all occupied slots and all three empty slots. Every
native report also verifies all unowned private slots unchanged. The final
`final-summary.json` records the twenty result names, four build hashes,
generated artifact hashes and installed-file hashes. No commit, push or tag
change was made. This is bounded implementation verification, not new human
acceptance of all original saves or broader gameplay. The next selected feature
is game sounds, followed by music.
