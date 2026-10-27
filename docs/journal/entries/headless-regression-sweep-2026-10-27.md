# Sequential invisible regression sweep — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Playable SDL runtime](../../implementations/playable-sdl-runtime/playable-sdl-runtime.md).
Runtime repairs: [Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Navigation and observers: [Task 10](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-10-build-goal-driven-regression-navigation.md).
Authorization and baseline: [Sweep handoff](headless-regression-sweep-handoff-2026-10-26.md).

## Execution policy

Run blocks 01–10 in order with `--display headless --workers 1 --execution shared`
and both Debug/ASan configurations. SDL uses `dummy`; agent recording stays off.
Every attempt has a separate directory under `.tmp/headless-regression-sweep/`.
Retain failures, inspect logical results and journey lifecycles, preserve required
assertions and finish with an integrated full sweep on final sources. The existing
staged, unstaged and untracked work is preserved; no staging, commit or push is
authorized by this sweep.

## Subsequent counterexample

The user's later visible-Debug/two-worker full run fails door approach and blocks
stability on matching source and executable hashes. The
[reliability continuation](regression-door-approach-reliability-2026-10-27.md)
supersedes current acceptance. The counts below describe one headless execution;
they do not establish repeatability across native AI/pacing outcomes.

## Historical single-run acceptance

`full-final-07/` completes the entire final-source selection: **144 PASS / 59
optional SKIPPED / 0 FAIL / 0 BLOCKED**, all **141 required** checks, **1795.66 s**
(**29 min 55.66 s**), exit **0**. Every one of the **203** catalogue cases appears
exactly once. All **24** native gameplay journeys quit normally and complete
inspection; no stopped-thread or watchdog diagnostic is retained. SDL is
**dummy**, one worker, sequential Debug/ASan, recording off. All **34** recorded
test-source hashes and both pinned/live executable identities match.

`validation.json` audits lifecycles, inspection and identities;
`integration-audit.json` audits exact catalogue ownership, required results,
checkpoint provenance, observed-branch provenance and JSON/JUnit agreement.
The scratch auditor initially treats a branch summary as a gameplay checkpoint;
it is corrected to verify its successful source trial and actual branch. No
suite result or source is changed by that auditor correction.

The following logical subsets are read from that same accepted full report.
They overlap through prerequisites and do not represent new standalone runs.
`block-audit.json` preserves their exact selections.

| Regression | Block | Required PASS | All PASS | Optional SKIPPED |
| --- | --- | ---: | ---: | ---: |
| 01 | `checks` | 39 | 39 | 0 |
| 02 | `startup` | 8 | 8 | 0 |
| 03 | `menus` | 54 | 54 | 48 |
| 04 | `movement` | 8 | 8 | 0 |
| 05 | `unarmed` | 14 | 14 | 0 |
| 06 | `workshop` | 16 | 16 | 0 |
| 07 | `swimming` | 22 | 22 | 2 |
| 08 | `potions` | 22 | 25 | 7 |
| 09 | `stability` | 16 | 16 | 0 |
| 10 | `replay` | 0 | 0 | 2 |

| Executable | SHA-256 |
| --- | --- |
| debug.Build | `4c6d47a8c9e306228ba41af4fc0e8c59103a6fb167f99e1cb4e873040189e94b` |
| asan.Build | `b91f57280b2acbcd9362bc947cf0bd3b42708133c8eca6654376e31e07ad043c` |

Final source identities are retained in `report.json.metadata.test_sources`:

| Source | SHA-256 |
| --- | --- |
| `E2Recomp_recon.c` | `8d2ca1884ce1b9a2a834e427bca5d6768deb54249040a0c2fe5dd87444c4dc78` |
| `GenerateRecon.js` | `2ef2629fc93b4f16c4cb35457b25673f44dd717894149765ff37bd8c8653b676` |
| `e2_gameplay_steps.py` | `b6daee0408af4307fc914f6594e3be18807cb5d2c212037e09ba40374570866e` |
| `e2_navigation.py` | `dbe8dbbaa39d753c2713ba431148c1928286a92517db248e72c777ba32fbedbc` |
| `check-e2-suite.py` | `e4ea231402bd69a935c27ee23786597da1cb7489dcf8f596867c19d1847a71ce` |
| `check-e2-navigation.py` | `70dd530a0cb777ceb712a67ba22fd9c43419ec1b522156358a6f9143a6c164f2` |

All **66 suite / 46 navigation = 112** contracts pass, as do all registered
normal/ASan original-code and host fixtures and exact four-artifact generation
parity. Reconstructed header/globals still match the pre-sweep baseline. Failed,
interrupted and superseded attempts below remain evidence on their recorded
source versions; they are not relabeled as successful final-source execution.

The **59** skips comprise **48** unfinished menu/rendering/audio/persistence
entries, **two** shore exits, **two** final potion death/expiry/cure entries,
**two** unavailable portable replay corpora and **five** unsampled optional
potion branches. Three naturally sampled branch summaries pass. Recordings
remain immutable and strict replay validation is unchanged.

This is bounded headless regression acceptance. Guard-293 actual damage, live
water-enemy damage, broader rendering/audio/persistence, longer stability and
new human F5 acceptance remain open. The earlier screenshot freeze is not
explained by these independently captured repairs. The extended unarmed-prefix
door **−100** deactivation still has no identified writer; compatible separate
journeys preserve required checks without claiming to repair that runtime gap.
That writer capture is the next bounded runtime diagnostic, not unfinished work
in this accepted catalogue. No files are staged, committed or pushed by the sweep.

## Progress

Paths below are relative to `.tmp/headless-regression-sweep/` and identify the
latest qualified report or the current failure. Unexecuted rows are not acceptance.
Rows 01–07 retain the menu-repair source baseline. Row 08 is requalified after
the integration's navigation repairs, and 09 follows the pose-event repair.
Final acceptance above covers every required case on final sources. These
per-block rows retain earlier source versions, including the potion run before
final contact settling; hashes are not silently updated to claim newer execution.

| Block | Report | Debug / ASan result | Diagnosis, repair and limits |
| --- | --- | --- | --- |
| 01 checks | `01-checks-after-menu/report.html` | **35/35 PASS**, **30.97 s** | Includes menu/surface fixtures; all 26 recorded source hashes match |
| 02 startup | `02-startup-after-menu/report.html` | **8/8 PASS**, six journeys; **207.12 s** | Both skip modes and natural intro after menu repairs; all 26 source hashes match |
| 03 menus | `03-menus-qualified-02/report.html` | **54 required PASS / 48 optional SKIPPED**, **54.06 s** | All three stages, original-backed repairs, two native exits and complete inspection; all 26 source hashes match |
| 04 movement | `04-movement-initial/report.html` | **8/8 PASS**, **119.12 s** | Both courtyard journeys exit natively and complete inspection; all 26 source hashes match |
| 05 unarmed | `05-unarmed-initial/report.html` | **14/14 PASS**, **226.95 s** | Four native journeys; actual smith damage and attributed guard hits; all 26 source hashes match |
| 06 workshop | `06-workshop-initial/report.html` | **16/16 PASS**, **180.61 s** | Sword attachment, four directions, smith death and door passage; two clean native journeys; 26 source hashes match |
| 07 swimming | `07-swimming-initial/report.html` | **22 required PASS / 2 optional SKIPPED**, **306.89 s** | Armed/unarmed swimming directions and water return; four clean native journeys; 26 source hashes match |
| 08 potions | `08-encounter-handoff-qualified-01/report.html` | **25 PASS / 7 optional SKIPPED**, all **22 required**; **562.07 s** | Live encounter handoff, readiness and actor-clearance planning; ten clean native journeys; all 34 source hashes match |
| 09 stability | `09-stability-qualified-01/report.html` | **16/16 PASS**, **356.62 s** | Original-backed terminal pose repair; two clean native exits/inspections, all 27 source hashes match |
| 10 replay | `10-replay-no-portable-corpus/report.html` | **2 optional SKIPPED** | Historical complete corpus rejected for an added SDL driver; failed diagnostic attempt retained separately |
| Full integration | `full-final-07/report.html` | **144 PASS / 59 optional SKIPPED**, all **141 required**, **1795.66 s**, exit **0** | All 24 native exits/inspections, 34 source hashes, executable identities, catalogue/checkpoint provenance and JSON/JUnit audits pass |

## Regression 01

`01-checks-initial/report.html` retains **3 PASS / 28 FAIL**, **21.15 s**, exit **1**.
All native i386 fixtures stop with `SIGSYS` at process launch in the restricted
execution sandbox, including the independent retention-worker binary. Generator
parity and Python suite/navigation contracts pass. This is an execution-environment
boundary, not evidence of 28 recovered-code faults.

The authorized bounded suite reruns with native execution permission in
`01-checks-native/`: **31 PASS / 0 FAIL / 0 BLOCKED / 0 SKIPPED**, **29.96 s**,
exit **0**. No source changes are needed. Subsequent native blocks use that same
execution permission. This block starts no gameplay process.

## Regression 02

`02-startup-initial/` passes all **8** logical results with **six** native menu
exits zero and completed inspections: early Space, delayed Space and natural
horseback intro in both configurations. All **21** recorded test-source hashes
match. No native signal, watchdog or allocation-exception diagnostic is captured.
This qualification predates the following menu repairs; final integration must
exercise startup again on the repaired executables.

## Regression 03 investigation

`03-menus-initial/` reproduces stale labels in all nine Debug option checks and
the first three ASan option checks. Debug pedestal Start Game fails its horseback
return assertion; gameplay restart segfaults in `FUN_0043a39c`. ASan Load stops
earlier in `FUN_0043ce58` with a stack-buffer overflow. Both journeys fail; the
required blocked results are retained separately from optional coverage gaps.

Original instructions establish these repairs, mirrored in the generator:

- `0x43d934`, `0x43d9a0`, `0x43da04` write option text pointers/flags into mapped
  requester items. Updating only hosted aliases leaves live labels stale. The
  recovered helpers now update the actual items as well as those aliases.
- `0x43a3f9` sign-extends Joe's **word** identity before indexing the restart
  actor flags. The reconstructed dword includes adjacent flags and indexes far
  outside that table. Restore the original width. Menu dispatch
  `0x4162d0/0x4162e4` calls StartGame during intros too; remove the earlier special
  action-progress reset, which cannot return the pedestal to horseback.
- `0x43d037` copies a contiguous **15-byte** `saved\\XXXX.ecs` filename, then
  fills bytes **6–9**. The four-byte Ghidra local cannot own those writes. Restore
  the whole filename and explicit path/stream ownership; slot labels retain
  their original **26-byte** reads, first-byte handling and close calls.
- Slot item construction must point into mapped `0x643540`/`0x643434` arrays.
  The first repaired ASan run exposes the former standalone-global pointers as a
  global-buffer overflow in `FUN_0043b9bc`. Correct those two builder pointers.
- The following ASan attempt reaches slot preview `FUN_0043c1b8` and exposes the
  same split filename local there. Original `0x43c22c–0x43c26b` establishes its
  contiguous 15-byte filename and actual open path too.

Retained focused attempts:

| Directory | Result | Boundary |
| --- | --- | --- |
| `03-menu-repair-focused-01` | **10 PASS / 1 FAIL / 1 BLOCKED**, **8.78 s** | Option labels and Debug pedestal restart pass; ASan exposes slot text pointer |
| `03-restart-load-focused-02` | **6 PASS / 1 FAIL / 3 BLOCKED**, **23.22 s** | Debug all-stage restarts pass; same ASan pointer fault; a generator anchor error prevented the intended new build, so this uses the preceding binary |
| `03-restart-load-focused-03` | **6 PASS / 1 FAIL / 3 BLOCKED**, **25.22 s** | Mapped slot text passes; ASan exposes preview filename overflow |
| `03-restart-load-focused-04` | **6 PASS / 1 FAIL / 3 BLOCKED**, **25.11 s** | ASan now reads an installed named save and exposes lost thumbnail surface/pitch inputs |
| `03-menus-qualified-01` | **33 PASS / 1 FAIL / 22 BLOCKED / 46 optional SKIPPED**, **30.39 s** | Debug required checks pass; ASan reveals zero base/pitch from compatibility Lock |
| `03-restart-load-focused-05` | **2 PASS / 8 BLOCKED**, **3.66 s**, two failed journeys | Real surface ownership exposes discarded unlock selector during startup |
| `03-restart-load-focused-06` | **2 PASS / 8 BLOCKED**, **1.66 s**, two failed journeys | Generator multiline-signature anchor failed; same preceding binary, not qualification; sources were regenerated before this failed attempt finished |
| `03-load-focused-07` | **3 PASS / 1 BLOCKED**, **3.66 s** | Debug Load passes; ASan exposes mode-change split descriptor |
| `03-load-focused-08` | **2 PASS / 2 BLOCKED**, **2.85 s** | Actual mode validation exposes discarded width argument in resolution wrapper |
| `03-load-focused-09` | **4/4 PASS**, **5.36 s** | Debug/ASan startup, native Load, native menu exits and completed inspections pass |

`check-e2-menu-contracts.py` compares **512** option-storage cases, **96**
word-identity/canary cases and **six** complete ten-slot scans against executable
original x86, normally and with ASan. Slot cases include missing, named and
first-CR records; CRT/register bridges and requester drawing are intercepted.
This proves label metadata, not functional saved-state loading/serialization or
thumbnail rendering. The fixture is registered for both configurations in 01;
the complete catalogue initially becomes **197** logical cases, still **22** shared
gameplay processes. Existing **61** suite / **38** navigator contracts pass.
Scratch regeneration matches all four generated artifacts. Reconstructed header,
globals and rename metadata remain unchanged from this turn's baseline.

## Slot previews and actual DirectDraw storage

The original installation contains ten `Saved/*.ECS` files, including named saves
and CR-prefixed empty slots. Restoring the actual filename therefore exercises
real header/thumbnail reads; those files are read only. `FUN_0043c1b8` now retains
the binary stream, discards the 26-byte name and two-byte version, and writes the
original **80×60 column-major** thumbnail using the returned surface/pitch.
Both label scanning and preview explicitly retain the original `rb` mode; bytes
CR and `0x1a` must not undergo text conversion. **30** original-x86 high-resolution
thumbnail/blank cases with padded pitch and whole-surface canaries pass normally
and with ASan. Low-resolution planar display fidelity remains unqualified.

The ASan native result then exposes the already documented
[Task 12 surface provider gap](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-12-recover-directdraw-surface-lock.md):
Lock slot **25**, Restore **27** and Unlock **32** are generic success no-ops.
At the failure, surface **1** returns base **0 / pitch 0**. The compatibility
provider now owns distinct surface objects/storage, actual aligned pitch,
descriptor output, lock/unlock ownership, restore, references, attached back
buffers and flip ownership. Physical surfaces remain separate from auxiliary
buffers 2/3 and presentation snapshots. Unsupported broader DirectDraw behavior,
renderer fidelity and arbitrary resolution switching are not accepted here.

Making that contract real exposes its original callers:

- Initial creation `0x458861–0x458928` uses contiguous **108-byte** descriptors,
  with primary flags/caps **0x21/0x218**, one back buffer, and a distinct
  **640×480** offscreen descriptor (**7/0x840**). Restore those initialized arrays.
- Mode change `0x458984–0x458b81` retains width/height, Release self, complete
  SetDisplayMode/CreateSurface/GetAttached/Palette arguments and the full
  descriptor. The source no longer reads across four-byte stack locals.
- `0x43ac60` selects high mode **640×480 / flag 1**; `0x43acec` selects low mode
  **320×200 / flag 0**. Both clear the scene pointer and submit palette
  **0x621330**. Lost scratch values formerly masked these contracts.
- Copy `0x417cd7/0x417ce8` unlocks its retained source/destination selectors;
  the reconstruction instead passed a row remainder/scratch value, which the
  generic no-op had hidden. Restore those two exact selectors.

`check-e2-ddraw-surfaces.py` passes **100** actual provider lifecycles in both
normal and ASan fixtures, covering distinct pixels, returned pitch, padding,
repeated locks, invalid ownership/base, restore lifetime, reference/attachment,
flip, release, auxiliary isolation and recovered high/low/high mode callers.
The existing original-x86 rectangle fixture also passes **2048** copy/ownership
and **256** dispatch cases in both modes. These compatibility fixtures are added
to 01: the catalogue is now **199** cases / **22** full shared gameplay processes.
Runtime C, compatibility source, generator and both new fixtures are included in
the suite's **26** source hashes. The compatibility stub file is handwritten;
reconstructed caller/preview repairs remain generator-owned.

Final menu qualification `03-menus-qualified-02/` passes every required check,
including all nine option toggles per configuration, each stage's Start Game,
Load/Save cancellation and gameplay cancel/resume/Quit. Both native processes
exit **0**, finish inspection and retain no signal/allocation/watchdog capture.
`validation.json` checks required statuses, all **26** source hashes and pinned/live
binary identities. The **48** optional skips comprise **42** unfinished effect
entries and **six** resolution-control entries. The actual saved game contents
are not loaded or rewritten. Regression 01 is requalified with the added fixtures
as **35/35 PASS**, **30.97 s**; 02 is being rechecked before advancing to 04.

Regression 02 requalification `02-startup-after-menu/` passes **8/8**, six clean
native menu exits and completed inspections, **207.12 s**, all **26** source hashes
matching. Regression 04 starts after inspecting those completed results.

## Regression 04

`04-movement-initial/` passes all **8** logical results in **119.12 s**. Both
controlled-population journeys execute controls/release and the required outward
and return courtyard route, quit natively with exit **0** and complete inspection.
`validation.json` verifies all **26** source hashes and pinned/live executable
identity. No native signal/allocation/watchdog diagnostic is retained. Regression
05 begins after reviewing that completed report.

## Regression 05

`05-unarmed-initial/` passes **14/14** in **226.95 s**. Both configurations execute
all basic/advanced unarmed directions, traversal and real unarmed smith **602**
damage **100→80**. Separate live receive-hit journeys require original melee
attribution and surviving health loss. All four processes exit zero through the
native menu and complete inspection; all **26** source hashes and pinned/live
identities match. No runtime, navigator, population or assertion change is needed.
The completed report is reviewed before starting Regression 06.

## Regression 06

`06-workshop-initial/` passes **16/16** in **180.61 s**. Both live-population
journeys retain movement/traversal prerequisites, actual sword pickup and
attachment, four armed directions, smith **602** death, door **980** destruction
and released passage beyond the opening. Both quit natively and finish inspection;
`validation.json` verifies required results, all **26** source hashes and
pinned/live identity. No additional repair is needed before Regression 07.

## Regression 07

`07-swimming-initial/` passes **22 required results** with **two optional shore-exit
skips** in **306.89 s**. Both builds execute sword-equipped and unarmed water
entry, all four original swimming combat directions, released movement and
outward/return water traversal. All four native journeys exit zero and complete
inspection; all **26** source hashes and pinned/live identities match. Shore
exit and water-enemy damage remain outside this acceptance. No navigator or
runtime change is needed before Regression 08.

## Regression 08

`08-potions-initial/` passes **26 results**, all **22 required**, with **six optional
skips** in **529.28 s**. All eight natural trials consume the potion and remove
the bottle; both potion-to-sword continuations retain removal while exercising
the sword. C/D setup uses actual original melee damage. Debug naturally samples
poison, invisibility and healing **85→100**; ASan samples poison in all four
trials. No type, health, RNG or timer injection is used. Optional skips comprise
four unobserved branch summaries and two unfinished final death/expiry/cure
cases. All **ten** processes quit natively with exit zero and finish inspection;
all **26** source hashes and pinned/live identities match. No new repair or
freeze/signal/allocation/watchdog diagnostic occurs. This does not explain the
earlier human screenshot freeze or accept final effect lifetime/cure. Regression
09 starts after reviewing this complete report.

## Regression 09 — Terminal pose-event ownership

`09-stability-initial/` retains **15 PASS / 1 FAIL**, **244.62 s**, exit **1**.
Debug completes mixed input, the **60-second** released observation, native Quit
and inspection (**168.93 s**). ASan passes every prerequisite through door passage,
then receives **SIGSEGV** in `FUN_0042b0f4` during `stability.active-input`, update
**3203**. Its journey fails after **72.41 s**. The captured `probe-stopped.json`
retains the signal, stacks, registers, locals and process maps.

The stack is `FUN_0042b0f4 ← FUN_0042b880 ← FUN_0042b338 ← FUN_0042ad60`.
Terminal event **0x16** copies three position words, increments its local actor
pointer by **six** bytes, then invokes root pose with no retained context. The
root helper instead reads an uninitialized stack-looking value, **-17096**, whose
address happens to be readable; its alleged child link is invalid. This is an
actor-input loss, not evidence that the child link belonged to the real actor.

Original `0x42bb5f–0x42bb7d` keeps the actor in **EBP**, performs the guarded three
word position copy and passes EBP unchanged in **EAX** to root pose. Related event
**0x17**, `0x42bb8c–0x42bbb6`, does the same for orientation without that preview
guard. A shared terminal-pose helper now retains the selected actor and event,
performs exactly those original writes, sets/restores the existing pose context
around the call and preserves the event link. No input route, health, RNG, clock,
population or gameplay assertion is changed; these are original action-event
writes, not a test assigning actor state to reach a goal.

The generator mirrors the repair with exact four-artifact parity. New normal/ASan
fixtures each compare **3072** original-x86 terminal events, including preview
guards, coordinate/rotation offsets, zero/foreign caller context, context clobber
and restoration, unshifted root actor and full event/actor memory canaries. Their
root leaf is intercepted to inspect the original EAX contract; existing actual
root-pose comparisons separately pass **1152** cases in each mode. Transformed
child world-to-local conversion remains outside that existing root fixture.
The new pose-event check is registered in both configurations: the catalogue
becomes **201** logical cases / **22** full shared gameplay processes and the
source manifest has **27** entries. Native stability requalification follows
targeted contracts; this fixture success alone is not gameplay acceptance.

Native `09-stability-qualified-01/` then passes **16/16** in **356.62 s**.
Both live-population journeys finish mixed input, the full **60-second** released
observation, native Quit and complete inspection. Debug/ASan journey durations
are **167.77 / 182.60 s**. The validation artifact verifies all **27** source
hashes and pinned/live binaries, with no stopped/stall diagnostic. The earlier
ASan terminal-event crash is repaired within this bounded route; extended game
stability and the earlier human freeze remain separate questions.

## Regression 10 — Immutable historical corpus and display policy

Read-only inventory finds **11** distinct complete human capture identities
across retained sessions and exported copies, with **18** paths in
`replay-candidates.json`. A separate local scan finds **seven** complete exported
copies among **12** replay metadata files. Every available complete candidate
omits `env.SDL_VIDEODRIVER`; none was recorded with SDL dummy. Completion here
means an end row and no incomplete marker; the native parser still verifies
integrity and startup compatibility.

The replay launcher formerly deleted the suite's SDL dummy setting while
restoring the recording's environment. The suite now forwards an explicit
`--video-driver` through `e2-debug.py`, `e2_scenarios.py` and `replay-e2.py`, applying
it after metadata restoration. Direct replay without this argument preserves
the recorded environment. Recording stays off, input and metadata remain
immutable, and native strict startup/completion/behavioral checks are unchanged.
The scenario report records this override. **63** suite contracts pass, including
both default and overridden launches, immutable copied/source files, and an
end-to-end scenario that correctly fails without completed inspection. That
launcher fixture explicitly uses incomplete synthetic input and establishes no
gameplay replay acceptance. Replay/scenario/inspection support sources and the
existing intro scenario join provenance: the final manifest has **33** files.

`10-replay-historical-01/` tries the smallest exported complete human recording,
`potion-no-effect-human-20261024/session/replay`, against both builds using
compatible replay and SDL dummy. It retains **2 Build PASS / 2 Replay FAIL**,
**1.45 s**. Both native parsers reject **extra startup environment
env.SDL_VIDEODRIVER** before gameplay. Compatibility mode permits executable
differences but does not waive this environment contract. All **33** source
hashes match; `replay-corpus-historical-01-identities.json` verifies the original
recording files are unchanged. These failed attempts are not accepted replay
and are not relabeled optional successes.

No available complete corpus meets the requested invisible execution policy
and native startup contract together. `10-replay-no-portable-corpus/` therefore
retains the existing **two optional CompleteCorpus skips**, exit zero. No parser
rule, recorded binary identity or end marker is rewritten to manufacture a pass.
Final integration uses those explicit optional gaps and keeps the supplied-corpus
failures separately reviewable.

## Integrated qualification

`full-final/` selects **201** logical cases, **22** shared gameplay processes and
**117** total execution units with both builds, `--display headless`,
`--workers 1` and recording off. Sources are frozen until the run finishes.
It passes source/tool/Debug native fixtures and the combined Debug workshop
journey, including actual unarmed contact, smith death, door passage and mixed
stability (**240.94 s**, native Quit and inspection complete).

Debug Potion A consumes/removes the bottle, then fails
`setup.PotionSwordApproach`: the historical corridor's point **[833, 4096,
-10493]** has nearby live actors, and six same-side local detours lead north
without reaching it. Navigation exhausts its replan budget after **1974** updates;
no native fault is captured. Nearby actors are observations, not proven collision
causes. The sword assertion is required **BLOCKED**, not a pass. Potion B passes
before the agent observes that failure and interrupts the suite. C's completed
checkpoints survive, but its interrupted lifecycle fails separately. Final report
is **35 PASS / 1 BLOCKED / 165 interrupted SKIPPED**, two failed journeys,
**564.92 s**, exit **130**. Those interrupted skips are not optional acceptance.

The potion-to-sword setup now uses the existing read-only live scene-floor
planner from the actual post-drink position to the established sword staging
point **[-871, 4096, -10006]**, then retains actual sword pickup, reciprocal
attachment, attacks and consumed-bottle assertions. Guidance points are not
required gameplay gates. No actor, health, RNG, timer or population is changed;
the same **2400-update / six-replan / 55-second** navigation bounds remain.
The **63** suite contracts pass. Native Regression 08 requalification follows
before a fresh final integrated run.

The floor-only attempt `08-potions-scene-sword-01/` retains **6 PASS / 2 BLOCKED
/ 24 interrupted SKIPPED**, **134.26 s**, exit **130**. A live rat approaches a
planned point near **[1728,4096,-11200]**; six local detours still exhaust the
budget. The agent stops that run after observing the failure; the following
trial's interrupted startup owns the second blocked result. There is no captured
native fault.

The next setup opts into observed actor clearance and bounded scene replanning.
Original motion `0x448cb4` uses collision flag **0x1000**, state other than **11**
and a **three-quarter sum of radii**. The read-only planner uses those fields
initially with a **128-unit** steering margin, excludes Joe and the explicit sword target,
and records every candidate. These are conservative avoidance observations, not
proof that each actor caused a collision. Noncollision workshop props are not
misclassified by their labels. On stalled movement, the next observed snapshot
replaces the floor plan within the same **six** replans, **2400** updates and
**55 seconds**. Required sword gates and all gameplay assertions remain intact.
Other ground routes and swimming retain their existing policies.

All **63 suite / 40 navigation** contracts pass, including clear path segments,
escape from an already crowded start, collision-field filtering, refreshed actor
positions, finite replans, input release and no attack/state injection. An
offline check of the captured workshop map finds a **21-point** route in **239**
expansions around **six** observed collision candidates. It requires converting
JSON script-policy object keys back to integers. The first offline invocation
omitted that conversion and falsely reported disconnection; the agent stopped
the already-started `08-potions-scene-sword-02/` at startup (**15.52 s**, exit
**130**) to investigate. That interruption is not a gameplay failure or native
qualification. The corrected captured-map check succeeds without a source
change, and `08-potions-scene-sword-03/` is the next qualification.

`08-potions-scene-sword-03/` passes Debug's complete potion-to-sword journey
(**59.64 s**) with native Quit and completed inspection. A single initial actor
clearance plan suffices; dynamic refresh still has contract evidence only at
that point. Trial C then fails the bottle guidance after actual melee damage:
Joe reaches **[472,4096,-11805]**, near the actual bottle at
**[428,4096,-11856]**, but continues pursuing historical point
**[300,4096,-11580]** beside observed rat **11**. That unchanged approach burns
all six local detours. The agent interrupts after observing the failure; D
already passes and ASan movement is interrupted. The report retains **15 PASS /
2 FAIL / 3 BLOCKED / 12 interrupted SKIPPED**, **297.25 s**, exit **130**. The
second FAIL is the explicit ASan interruption, not another native crash.

Bottle approach now retains the existing workshop join and then plans to the
**actual bottle actor position**, using the same actor-clearance refresh policy.
The initial 128-unit margin overconstrains the narrow bottle approach in captured
floor data. Final clearance adds **64 units**, paired with **60-unit** waypoint
tolerance; the original collision radius contract and actual interaction gates
are unchanged. The captured C snapshot yields an **11-point / 56-expansion**
connected plan to the real bottle. All **63 suite / 40 navigation** contracts
pass. `08-potions-scene-sword-04/` qualifies both bottle and sword approaches
before the next full run. No native runtime or generator change accompanies
these input-only navigation repairs.

`08-potions-scene-sword-04/` passes **26 results**, all **22 required**, with
**six optional skips**, **565.35 s** and exit zero. All **ten** Debug/ASan
journeys quit natively and complete inspection; all **33** source hashes and
pinned/live binary identities match. Both bottle and sword approaches succeed
without native scene refresh in this sample; bounded refresh remains covered by
contracts. Optional gaps are four unsampled random branch summaries and two
final potion lifetime/cure entries. The next integrated selection retains
**201** cases / **22** gameplay processes and starts in `full-final-02/` on
these frozen sources.

`full-final-02/` passes all source/tools/native fixtures, Debug's entire combined
workshop/stability journey (**240.72 s**) and all Debug potion trials. ASan's
combined workshop journey passes unarmed contact, then exhausts local sword
approach after **1377** updates. Joe starts west of the workbench at
**[-1890,4096,-10207]**; two nearby live rats and the workbench constrain the
center chase. His final observed position is **[-834,4096,-9999]**, about **250**
horizontal units from sword **3717**. There is no captured native fault. Later
combat/door/stability checks are required BLOCKED. Potion A completes before
interruption takes effect, but its sword continuation is blocked by that failed
prerequisite.

The interrupt lands during atomic report replacement outside the runner's
execution interruption handler. Process exit is **130**, with raw report state
still `running`: **63 PASS / 1 FAIL / 5 BLOCKED / 26 SKIPPED**, **106** cases not
reported. `interruption-summary.json` preserves that distinction; no finalized
complete sweep is claimed. The raw report and temporary output are retained.

Original pickup query **0x42dc9c**, already covered by normal/ASan executable-x86
selection fixtures, selects within **one Joe radius** of a point **one radius
ahead**. The driver's former **220-unit center chase** is unnecessarily tight
for Joe's **256-unit** radius around the workbench. Sword readiness/approach now
uses **2R−64 = 448 units**, inside the original forward selection region with a
steering margin. It still faces the actual sword, sends bounded SDL Space input,
and requires actual reciprocal attachment, equipment, movement and subsequent
combat. It does not relax those assertions or edit actor state. Scene plans to
stand on the raised sword cannot establish a safe floor route; no floor/script
policy exception or new planner API is retained from that investigation.

All **63 suite / 40 navigation** contracts pass. The exact combined sequence
that exposed this integration boundary is requalified in
`06-09-shared-sword-range-01/`: **22** selected results / **two** native journeys,
both builds, all unarmed actions/contact, pickup, smith kill, door passage and
mixed stability. A fresh full run must follow this targeted qualification.

## Captured bitmap-record watchdog stall

`06-09-shared-sword-range-01/` fails before pickup: Debug stalls in unarmed
contact at update **3089**, loading action **1280** through the archive FAN
bitmap section. After **30.03 seconds** without progress, the watchdog sends
SIGINT and captures `FUN_0045384c ← FUN_00426a04 ← FUN_004451a8`. This is an
intentional watchdog interruption, not a spontaneous SIGINT or OOM diagnosis.
The stopped process reports about **4 GiB** resident memory. The earlier human
screenshot freeze remains unconfirmed; this is a separately captured stall.
ASan is then interrupted during unarmed contact before the new pickup approach.
The retained report is **10 PASS / 2 FAIL / 10 BLOCKED**, **166.96 s**, exit
**130**. Neither sword-range nor combined-route acceptance is established there.

The stopped bitmap parser's `piVar5` equals its stream **0xf1945008**, rather
than a record in original pool **0x86916c..0x8692fc**. `FUN_00426a04` has no C
return value despite its `undefined4` signature. Original **0x426a04–0x426a2d**
returns the allocated record in EAX after linking and stamping it. The recovered
wrapper now returns that actual record explicitly. The pool allocator's scan
also reads standalone hosted globals and scaled host-pointer offsets; original
**0x45384c–0x4538b4** scans exactly **20** mapped **20-byte** records using the
word at **+14**. Restore those mapped flags and original eviction/retry behavior,
removing the invented heap fallback at this boundary.

Original **0x453210–0x453262** passes the selected oldest record to disposal in
EAX. The reconstructed selection and parser's duplicate-name cleanup drop that
owner. Both now set/restore the existing cleanup context; `FUN_00452a94` binds
that actual node. Its original unlink, name-table clear, payload compaction and
free mark are preserved. No arbitrary allocation cap, clock/health edit, longer
watchdog or failure suppression is introduced. All five reconstructed repairs
are generator-owned; header, globals and rename metadata remain unchanged.

New normal/ASan fixtures each pass **14,208** original-x86 pool allocation,
explicit publication/return, selected eviction, compaction and repeated reuse
cases. They verify whole pool/table/arena and stream canaries plus cleanup
context restoration. The fatal path is intercepted, and bitmap payload
reservation/parser integration still requires native qualification. Scratch
generation matches all four artifacts; **63 suite / 40 navigation** contracts
pass. `Original.BitmapRecords` is registered for each build: catalogue **203**,
source manifest **34** files. Native combined-route qualification starts in
`06-09-bitmap-records-qualified-01/` before a fresh final integrated sweep.

That attempt passes both new bitmap fixtures and Debug's unarmed contact,
sword pickup, all sword directions and smith kill. The dedicated door phase
then fails **Target already inactive**: initial health is already **−100**.
The agent stops the run and ASan is interrupted during workshop traversal. The
retained report is **15 PASS / 2 FAIL / 7 BLOCKED**, **160.64 s**, exit **130**;
the second FAIL is that explicit interruption. This is not combined acceptance.

Navigation snapshots initially only bracket the health drop between workshop
entry and sword approach. Native inspection narrows it to snapshot **665**,
update **4680**, during sword pickup (Joe action **537**, health **75**), after
unarmed contact. No original writer is identified by those sampled observations.
The dedicated door assertion is kept intact. A bounded invisible diagnostic
`door-damage-watch-01/` enables the explicit `observe_door_health` observer,
watching the actual door word and writing at most **64** read-only health/stack
records. It replays ordinary setup/input through sword directions with recording
off and no state assignments. This diagnostic must identify the writer before
deciding between collateral gameplay, journey incompatibility and a runtime
ownership fault; its success alone cannot accept the omitted door/stability work.

`door-damage-watch-01/` completes its input sequence, native menu exit and
inspection without a door-health write. It therefore does **not** identify the
writer or explain the earlier deactivation. It does exercise the radius-derived
pickup approach and actual attachment, but is a diagnostic, not full acceptance.
Source inspection bounds the two reconstructed **−100** writers to water/fall
motion; the failed sampled capture has no writer stack, so a collision or
unarmed-damage cause is **not established**. This remains an explicit runtime
diagnostic gap; it is not claimed repaired by changing test planning.

The planner's asserted compatibility is nevertheless contradicted by the
observed combined prefix: the later dedicated door test requires a fresh active
door, and unarmed-contact → pickup can invalidate it. Unarmed directions/contact
now use their already declared independent shared route. The armed workshop,
smith, door and stability sequence retains its own fresh native process and
every actual prerequisite, including pickup and four attacks. Each selected
logical case is still owned once; repeated setup in the other journey receives
no extra logical credit. No actor, door, health or game state is reset by a probe.

Door/stability journeys retain an explicit bounded read-only health writer
observer, so another unexplained deactivation remains a failing required check
with a precise stack. A new suite contract models destructive carryover and
verifies separate lifecycles, preserved prerequisites and retained assertions.
**64 suite / 40 navigation** contracts pass. Catalogue remains **203** logical
cases, now **24** full shared gameplay processes; source manifest remains **34**.
`05-06-09-compatible-journeys-01/` qualifies the repaired cache fixture and both
real routes in Debug/ASan before a fresh final integration.

The conversation interruption ends `05-06-09-compatible-journeys-01/` during
Debug's released-input stability observation. Its raw report remains `running`
with four fixture/build passes; inspection is incomplete and no native suite
process remains when work resumes. `interruption-summary.json` records this
partial state without rewriting the raw report. The completed door phase has
three observed original melee writes, **100→60→20→−20**, with `FUN_0042efdc`
at the top of the writer stack. This is useful diagnostic evidence, not a
completed journey or qualification.

`05-06-09-compatible-journeys-02/` restarts the same **24** selected cases /
**four** native journeys on unchanged sources in a new directory after that
external interruption. The run remains sequential, invisible and recording-off.

## Moving smith strike guidance

`05-06-09-compatible-journeys-02/` fails Debug's smith kill after actual pickup
and all four sword actions. The first hit reduces smith **602** from **100→60**;
all subsequent samples remain **60** while native inspection shows the smith
retreating. The driver approaches/faces only once, then holds Ctrl+Up for its
entire **1200-update** strike budget. This is stale test-input guidance, not
evidence that recovered melee failed to inflict the first hit. The suite is
interrupted after inspection begins: **10 PASS / 1 FAIL / 3 BLOCKED / 10
interrupted SKIPPED**, **119.85 s**, exit **130**, two failed lifecycles. No
combined-route acceptance is claimed.

The smith driver now shares one bounded fixed-target navigator across strike
bouts, follows live position and faces the same actor before each bout. It keeps
the **1200-update** attack allowance (**20×60**), six navigation replans, existing
update/host bounds, final **150-update** settling and full health/death/state-11/
representation-removal assertions. A dead-but-settling target is observed with
released input rather than approached or attacked again. Door strikes retain
their existing policy. Samples now include player/target position and heading.
No recovered runtime, generator, population or game-state assignment changes.

A new contract models a target retreating **600 units** after each bout and
requires actual tracking to inflict subsequent damage. It rejects an intact
target, retained representation and replaced actor instance, and checks bounded
attack updates and released input. Its first fixture run lacks the fake GDB
stack-output method on expected assertion failures; adding that test double
method resolves the fixture error. **65 suite / 40 navigation** contracts pass.
`05-06-09-compatible-journeys-03/` qualifies the repair on frozen sources with
the same **24** logical cases / **four** native journeys before final integration.

The targeted qualification passes **24/24**, **503.24 s**, exit **0**. Both
workshop/stability journeys (**183.02 / 187.60 s**) and both independent unarmed
journeys (**60.08 / 62.72 s**) finish actual menu Quit and complete inspection.
All **34** recorded source hashes and pinned/live executable hashes match; no
native fault or watchdog diagnostic is retained. Door damage is original melee
**100→60→20→−20** in both builds. ASan also observes ordinary scene initialization
**100→0→100** within one update through `FUN_00420dcc ← FUN_0044d634(980)`; this
is native scene loading, not a probe state reset or the unexplained **−100**.
The earlier extended-prefix deactivation remains unproven.

## Final integrated qualification

The final source catalogue selects **203** logical cases (**141 required / 62
optional**), **121** execution units and **24** shared native gameplay journeys.
`full-final-03/` runs the entire selection on the frozen qualified sources with
both configurations, one worker, SDL dummy and recording off. No portable replay
corpus is supplied; historical rejected recordings remain immutable diagnostics.

`full-final-03/` stops after Debug's later smith setup rejects an already dead
smith. Inspection records actual **100→60→20→−20**, state **5→11** and representation
removal during the prerequisite four directional attacks. Joe is performing
sword actions **7/15/14** beside the target, rather than the earlier unexplained
**−100** fall/deactivation pattern. The suite is interrupted: **29 PASS / 1 FAIL /
2 BLOCKED / 171 interrupted SKIPPED**, **167.88 s**, exit **130**. Potion A's logical
checks pass before its interrupted lifecycle; no integration acceptance is claimed.

The observer now watches smith **602** before directional attacks whenever a
smith-kill checkpoint is selected. It retains at most **64** read-only health
transitions with original melee stack/owner attribution and the original actor
pointer. An already completed kill may satisfy the later checkpoint only with
a positive recorded baseline and an observed fatal **positive→nonpositive** write
from `FUN_0042efdc` owned by Joe **0**, against the same instance, with no truncated
trace. Final nonpositive health, state **11** and representation removal remain
mandatory. Without that evidence an already dead target still fails. A living
target retains bounded live pursuit and actual strikes. This recognizes real
work already performed by required input; it does not manufacture a second fresh
target or accept sampled health loss as original-melee attribution.

A new observer/driver contract rejects other writers, other attackers, replaced
actors, truncated evidence, retained representation and unfinished death. All
**66 suite / 40 navigation** contracts pass. The final source change affects only
those two Python files; runtime/generator remain frozen. Regression 06 is
requalified in `06-smith-attribution-01/` before another full run.

`06-smith-attribution-01/` passes **16/16**, **152.87 s**, exit **0**, both clean
native exits and complete inspections, with all **34** source and executable
hashes matched. Debug records **100→60** during `combat.attack-up`, then
**60→20→−20** during the dedicated bounded kill. ASan records the entire
**100→60→20→−20** in `attack-up/left/right` and verifies the prior kill during
the later checkpoint. Every transition is attributed to Joe **0** through
`FUN_0042efdc`; neither trace is truncated. Thus both branches are exercised
natively, alongside door destruction/passage.

`full-final-04/` starts the unchanged **203-case / 24-journey / 34-source** final
selection after that accepted qualification. It retains the same invisible,
sequential, recording-off policy and optional portable-replay boundary.

`full-final-04/` captures another input/observation boundary in Debug: smith
health is **20** at the last bout sample, then Joe's still-completing original
melee delivers **20→−20** while pursuit advances **three** updates. The fixed
actor still has representation **87**, state **8**, while entering death; generic
navigation rejects it before the caller can observe completion. The fatal stack
is `FUN_0042efdc`, owner Joe **0**. This is a queued original strike after input
release, not a failed melee operation or unexplained deactivation. The suite is
stopped: **28 PASS / 1 FAIL / 3 BLOCKED / 171 interrupted SKIPPED**, **133.39 s**,
exit **130**. Potion A completes consumption before its interrupted continuation.

`Navigator.approach()` now permits an explicit completion observation only for
a **fixed `kill_enemy`** goal. Before treating a dead target as invalid, it may
return the same valid active actor when the caller verifies the recorded fatal
Joe-melee write and nonpositive health. Absent/replaced actors and other goals
retain their failures. The caller stops pursuit/attack input and waits for the
existing full death/removal assertion. It also resamples completion around facing
so a queued action cannot force another chase of a corpse. No native state is
assigned and all budgets remain. A deterministic contract delivers a fatal hit
during the first pursuit step; unattributed, replaced and absent variants fail,
with input released. **66 suite / 41 navigation** contracts pass.

`06-smith-pursuit-completion-01/` requalifies Regression 06 in both configurations
on these frozen final test sources before another integrated run.

`06-smith-pursuit-completion-01/` passes **16/16**, **176.68 s**, exit **0**.
Debug/ASan native journeys (**90.14 / 80.80 s**) finish menu Quit, complete
inspection and match all **34** source and executable hashes. No native fault
or stall diagnostic appears. `full-final-05/` starts the complete unchanged
**203-case / 24-journey** selection on those frozen sources.

`full-final-05/` passes Debug's complete workshop/stability journey (**194.88 s**)
and potion A/B/C, including real damage and potion-to-sword continuation. D then
exhausts its **2400-update** receive-hit setup without health loss. It pursues
guard **284**, uses five local detours, then spends its sixth replan reselecting
**293** when 284 disappears. At the final sample Joe is **[8030,4096,−17749]**,
guard 293 **[7764,4096,−18012]**, **119** units from the offset contact point.
Guard 293 remains original state **2 (retreat)** and action **350**, without
attributed damage. The first 64 melee samples are all from 284; the old shared
128-attempt count cannot establish whether 293 attacked later.

The suite is interrupted: **41 PASS / 1 FAIL / 4 BLOCKED / 157 SKIPPED**,
**621.44 s**, exit **130**, one failed gameplay journey. The explicit FAIL is
ASan's interrupted script-name fixture, not a new original-code discrepancy.
Skipped entries include declared optional gaps and unexecuted required work;
this is not accepted final integration.

Bounded diagnostic `08-receive-readiness-diagnostic-01/` adds read-only original
AI target **+0x1e** and readiness word **+0xea** to observations, and keeps the last
**32** melee samples/counter per eligible guard instead of allowing an early
guard to consume every retained sample. No navigation or eligibility behavior is
changed for this diagnostic. Original `FUN_00427584` labels state 2 retreat and
uses **+0xea ≥ 0x3001** together with a live opponent for attack transition; those
conditions still require live evidence before attributing the failed behavior.

The first diagnostic stops because its new per-opponent sample expression
contains literal `offset` instead of the formatted Python value. This is an
observer error, not a native fault: **3 PASS / 2 BLOCKED**, **31.07 s**. The
expression is corrected. `08-receive-readiness-diagnostic-02/` then obtains real
guard-284 damage but fails later bottle planning: **4 PASS / 1 FAIL**, **61.27 s**.
Its new counters record **129** original melee calls from 284. The initial
`+0x1e` label is corrected from AI target to **motion node**; it is not Joe's
actor pointer. No eligibility inference is based on that mislabeled field.

Original x86 **0x428725–0x428742** confirms that state-2 retreat cannot enter
attack with signed **+0xea ≤ 0x3000**. Live observations show readiness **0**;
already attacking state 7 remains eligible because its original branch does not
apply that retreat gate. The driver now rejects only that observed unready
retreat combination, preserving guard-293 eligibility when actually ready and
all fixed-target/reselection bounds. No actor identity is globally excluded.

The failed guard-284 approach repeatedly aims through the opponent's collision
disc from behind. Receive-hit steering now moves radially out when crowded,
then follows bounded 45-degree outside segments before closing on the existing
front contact point. Clearance uses the original three-quarter combined radii
plus the existing 64-unit steering margin. Known successful front geometry and
actual attributed damage remain required; no combat/health state changes or
attacks by Joe are introduced. Existing six replans, 2400 updates and host caps
remain. The old behind-opponent contract now requires active safe steering
instead of prescribing forward movement through the collision disc.

The diagnostic's bottle failure has a connected floor-only path (**11 points /
56 expansions**) but observed actor **12** at **[772,4096,−11554]** blocks the
conservative approach to bottle **[428,4096,−11856]**. Both captured maps confirm
that distinction. When observed actors disconnect a floor route, the planner
now proves floor connectivity without them, releases input for **30 updates**
and refreshes actor observations within the same six-replan/update/host budget.
It never executes that floor-only diagnostic route. Static floor disconnection,
node-budget errors and persistent actor blockage still fail.

**66 suite / 44 navigation** contracts pass, including clearance-segment geometry,
readiness without identity exclusion, transient/persistent obstacle cases and
static-floor failure. `08-contact-clearance-focused-01/` qualifies real damage
and potion D in both builds before the full potion block and final integration.

`08-contact-clearance-focused-01/` passes Debug's real guard-284 damage, potion D
and native exit (**82.74 s**) but ASan has no eligible opponent after its required
movement prefix. Guard **284** disappears before the fixed corridor endpoint;
293 is retreating/unready on floor **3584**, while Joe reaches **4096**. The final
report is **8 PASS / 2 BLOCKED**, **121.33 s**, one failed lifecycle. Debug does
not need the new orbit or actor-clearance wait in that sample; those branches
retain contract evidence, not native exercise claims.

The receive-hit corridor now hands over to live pursuit at the first observed
eligible opponent within the existing **1800-unit** local range on the **same
actual floor**. It no longer insists on walking past that opponent to the tenth
historical waypoint. Selection and the handoff share the same eligibility
calculation; readiness, identity, population and fixed/reselection policies stay
intact. Reaching an encounter is not damage acceptance. Actual original melee
and surviving health loss remain required. A new contract rejects wrong-floor,
far and unready candidates while observing early handoff and input release.
**66 suite / 45 navigation** contracts pass.

`08-encounter-handoff-focused-01/` rechecks ASan's movement-prefix variant before
a fresh complete potion block and final integrated sweep.

`08-encounter-handoff-focused-01/` passes **5/5**, **108.87 s**, exit **0**,
ASan native journey **107.71 s**, completed inspection and all **34** source/
executable identities matched. It exercises **one** actual early encounter
handoff, **16** outside-disc steering steps and **three** released **30-update**
actor-clearance waits. Original guard **284** inflicts surviving **100→95** damage;
potion D then completes consumption. These branches now have bounded native
evidence, alongside their contracts. Guard-293 actual damage remains unqualified.

`08-encounter-handoff-qualified-01/` starts the complete **32-case** potion block
in both builds on the frozen sources. Its setup-only armed-route unit owns the
selected workshop/sword prerequisites without performing unselected swimming
checks; no swimming acceptance is inferred from that route name.

`08-encounter-handoff-qualified-01/` passes all **22 required** checks: **25 PASS /
7 optional SKIPPED**, **562.07 s**, exit **0**. All **ten** native journeys quit
normally, complete inspection and match pinned/live binaries plus all **34**
source hashes. Required actual damage, natural consumption/removal and sword
continuation pass in both configurations. Optional branch sampling and final
effect-lifetime limits remain explicit.

`full-final-06/` starts the complete **203-case / 24-journey / 121-execution-unit**
selection on these frozen final sources. SDL remains dummy, configurations
sequential, one worker, recording off. The final audit must verify every logical
case exactly once, all **141 required** passes, native exits/inspections, source
and executable identities and consistent JSON/JUnit results.

`full-final-06/` passes Debug's workshop/stability (**180.77 s**) and potion A/B,
then Debug C's real-damage checkpoint exhausts **2400** updates. The retained
per-guard observer now proves **264** original melee calls from guard **284**;
no health write reaches Joe. The front approach reports reached at update **447**
inside its old **240-unit** band, off the swing axis. The contact point lies
inside the original collision clearance; subsequent steering repeatedly closes
inward then moves outward (**591** outside-disc steps) as the guard moves west.
This is input geometry/settling failure, not absence of original attacks.

The explicit interrupt lands during report serialization outside the runner's
execution handler, leaving another partial raw `running` report. Process exit
is **130**; `interruption-summary.json` records its exact available rows/counts
without rewriting raw evidence. No completed integrated run is claimed.

Receive-hit now aims **three-quarter combined radii + 64** ahead of the opponent
(**448** with both observed radii **256**), outside original actor collision
clearance **384**. The approach band is at most a quarter Joe radius (**64**),
with one-eighth-radius waiting hysteresis (**32**, total **96**). It no longer
settles up to 240/340 units sideways from a point inside the collision disc.
The outside arc can now close to its front goal without being pulled back into
that disc. All original navigation/replan/host/update bounds stay intact. An
actual attributed hit during approach still completes the damage objective from
any valid geometry; nearness alone never does.

A new contract retains the captured off-axis pose as an uncompleted approach,
checks the outside-clearance goal and tighter wait band, and still rejects a
precisely aligned encounter without actual attributed damage. The previous
known-hit contract now credits that real hit during approach rather than
prescribing the old loose distance stop. **66 suite / 46 navigation** contracts
pass. `05-contact-settling-01/` requalifies actual damage after real movement in
both native builds; the complete integration must follow on these final sources.

`05-contact-settling-01/` passes **8/8**, **116.02 s**, exit **0**, with both
movement-prefix damage journeys (**61.34 / 52.77 s**) exiting natively and
completing inspection. All **34** source hashes and executable identities match.
The final contact-policy change affects receive-hit guidance only; prior full
potion qualification remains bounded to its earlier recorded navigator version.
`full-final-07/` now requalifies every required case, including all damaged potion
setups, on the frozen final sources.

## Final verification

`full-final-07/` is accepted: **144 PASS / 59 optional SKIPPED**, all **141
required** checks, **24** clean native exits/completed inspections, **1795.66 s**,
exit **0**. Lifecycle/hash, exact catalogue/checkpoint/branch provenance and
JSON/JUnit audits pass; every numbered block's required subset passes on final
sources. All **34** source identities and both pinned/live executables match.
Owning implementation/tasks, capabilities and gameplay documentation now record
that result and the remaining limits.

Documentation maintenance passes with **253** Markdown documents connected to
README, both update and read-only checks. Generator syntax and `git diff --check`
pass. Reconstructed header/globals remain at their pre-sweep hashes. Existing
staged/unstaged/untracked work is preserved; no staging, commit or push is done.
