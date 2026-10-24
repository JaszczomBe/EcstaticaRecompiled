# Extended-gameplay alternate-target crash — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The latest human run crashes in `FUN_0042e684 ← FUN_00427584 ← FUN_0042a70c`.
This report supersedes the earlier extended-stability deferral. The repair
recovers the original updating actor and independent X/Z inputs; complete replay
and extended human gameplay acceptance remain open.

## Preserved failure and reproduction

Human session **20261024_161320_208** is finalized, retention protected and has
incomplete recording/inspection after SIGSEGV. Its pinned Debug executable is
SHA-256 **2c35ea654acec1902170f4f7c72c26422ab55fa5479d7b1350ec81fd848b0527**,
with debugger-start context revision **eff8ef3**. The receipt and stopped-thread
log are `.tmp/f5-investigations/session_20261024_161320_208_80c89921b7de{.json,.signal.log}`.

The documented bundle export and verification preserve it as
`.tmp/replay-bugs/extended-target-crash-20261024`. The bundle's export-time
context is **e2c4acd**, separately from the pinned executable's identity and
startup context. The original retention-protection marker remains in place.
Native replay and read-only GDB replay reproduce SIGSEGV at sequence
**2,260,310,849**, last matching checkpoint **204**, with the original stack.
Recording ends at the final clock event at that same sequence; there is no
completion marker or recorded continuation beyond the failure.

The exact stopped actor is **3820**, original name **w_pot1**, at
**(1728,4060,−12122)**, caller `local_6c = 0xaad37c`. The C arguments are
**11141344, 11195260**. Its candidate list reaches `psVar1 = 0xaab618`, while
its uninitialized `in_EAX` is NULL. The original installed actor-name directory
confirms the name; it does not establish wider potion interactions.

Earlier calls can return without dereferencing this missing actor when no
eligible candidate is present. In particular the same actor's call at sequence
**2,260,310,843** returns zero in the pinned image. This explains why a null
placeholder need not fail at its first invocation.

## Original contracts and repair

Original `/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` has SHA-256
**737e27ddfb76501ba6caf4f504b0c128854a36733526b17d30f635a1c255025b**.
Retained disassembly and original-code fixture provenance are in
`.tmp/extended-target-crash-20261024/`.

- **Caller:** `0x427cf2` loads the updating actor from `[EBP+0x2a]` into EDX.
  With actor byte **+0x146** bit **8** set, `0x427d03` copies EDX into EAX
  before calling the alternate selector. The C passed an unrelated packed
  temporary. Both explicit arguments now carry the updating actor; the upper
  return half retains the original preserved EDX actor.
- **Leaf actor:** `0x42e68d` retains incoming EAX in EDI and compares candidates
  against it. The reconstructed actor pointer now comes from `param_1`.
- **Vector:** `0x42e6dc..0x42e705` computes candidate-minus-owner integer X/Z.
  `0x42e718..0x42e71c` passes X from EBX in EAX and Z from ECX in EDX to the
  angle leaf. ECX survives for distance calculation. The repair calls the
  existing original-compared `E2R_PolygonAngle16(X,Z)` and explicitly retains Z.
  The prior C passed Z twice and then used an uninitialized `extraout_ECX`.

Candidate eligibility, 1024-unit component bounds, distance test, signed
16-bit facing difference and first-best list selection remain original-shaped.
There is no guessed null fallback. Narrow generator anchors mirror all three
changes. The existing sibling `FUN_0042e7dc` repair remains unchanged.

## Preserved animation-name regression

The initial worktree is clean at **e2c4acd**, rather than the dirty **eff8ef3**
state described in the request. `git diff eff8ef3 e2c4acd` shows the unexplained
C hunk was committed there: animation-name lookup/intern capacity is reduced
from **0x445c** to **0x1117**, and new-animation slot clearing is removed.
`GenerateRecon.js` still generates the documented original repair. The pinned
crash executable behaves like that original repair; its startup patch records
only documentation changes.

The C hunk is preserved exactly. The existing animation-name fixture fails the
new-slot ownership assertion on current source; isolated generated source passes
all **1,800** installed names, including **1,352** beyond the reduced byte bound.
Both repaired current-source Debug and ASan compatible replays diverge at
sequence **1,780,684,471**, last matching checkpoint **155**, reporting
`expected cursor_get actual clock` after a Space interaction. They do not reach
the reported late crash. That earlier difference is not replay acceptance.

Independent scratch generation before/after this repair proves the generator
change equals the hand repair. Header, globals and names match byte-for-byte;
the C residual contains exactly the three pre-existing animation-name hunks,
saved as `preserved-animation-name-drift.patch`. Full zero-drift generation parity
is therefore **not** claimed, and in-place regeneration is avoided to preserve
the user's hunk.

## Crash-boundary verification

Separate source/build trees under
`.tmp/extended-target-crash-20261024/canonical-source/` use the generated C,
including the original animation-name repair, without changing the worktree C
or the normal F5 launch. Their compatible Debug and ASan replays each match all
**204 checkpoints**. Both return from the formerly faulting call at sequence
**2,260,310,849**, selecting **0xaad1f0** while retaining actor **0xaad37c**.
The updating actor also selects that target at sequence **2,260,310,843**.
Both runs then correctly exit **75/INCOMPLETE** on prefix exhaustion, with no
sanitizer report. This crosses the failing instructions; it does not extend the
recording or prove complete replay or sustained gameplay.

| Check | Result |
| --- | --- |
| Expanded `check-e2-attack-target.py E2WIN95.EXE [--asan]` | **65,536** alternate selections (**47,924** selected / **17,612** empty) and **65,536** sibling attack-height selections pass in each mode; actual original angle code and caller tails, eligibility, independent X/Z, facing wrap, range boundaries, coincident/tied candidates, read-only actor memory and preserved registers |
| Generator syntax and scratch delta parity | Pass; only the preserved pre-existing animation-name drift remains |
| Four ordinary SDL/X11 Debug/ASan builds | Pass |
| Ordinary runtime baseline and control matrix | Pass, including all **eight** arrow rows |
| Ordinary SDL requester, OK, resumed update and Escape | Debug/ASan pass |
| Ordinary fresh SDL sword routes | Debug/ASan acquire sword **3717**, start all four Ctrl/arrow attacks, release and move, then survive **15.41 seconds** released, health **100**, state **4**, representation **9**, no sanitizer report |
| Read-only query observer on those sword routes | Debug **96** calls/returns; ASan **95** calls/returns; all selections empty, so these routes do not reproduce the nonempty failure case |

A longer fresh Debug trial reuses only the human recording's keyboard transitions
by inspection update counts: **179** transitions over **3,805** updates from the
first gameplay arrow. Clock and RNG remain live. It then releases keys, advances
**300** further updates and observes **15.40 seconds**. Joe retains health
**100**, state **4**, no modal, at **(604,4096,−11469)**. The observer verifies
**971** actor-preserving query returns, all empty. This is a bounded continuation
of fresh inputs, not a deterministic reproduction of the nonempty selector or
proof of the original recording's later route.

The corresponding isolated ASan trial also finishes the same **3,805-update**
input schedule, **300** extra updates and **15.40 seconds** released, without a
sanitizer report. Its path differs: final Joe is **(2204,4096,−16722)**, health
**85**, state **4**, no modal, with all keys/modifiers released. Health is **100**
at input end and after the extra updates, then falls during the observation;
this is survival with ongoing gameplay, not stationary idle acceptance. Its
**39** query calls/returns also select no target. Neither fresh route reproduces
the exact nonempty crash case; the original-code comparisons and strict prefix
observations establish that boundary.

All agent probes have explicit bounds, isolated runtime directories and recording
off. They use SDL keyboard events and read actor/query state; they do not assign
positions, actions, health, RNG, camera or attachment state. The first observer
variants deliberately required a nonempty selection and failed that coverage
assertion after surviving the route. Those failures remain retained; the final
reports distinguish query execution from nonempty selection.

## Executables, evidence and remaining work

Ordinary current-source SDL hashes:

- Debug: `a8f9eec65d784f84f667d8d417f9155d64d87a28930694cbf255133451ffa693`.
- ASan: `12963beaee167b1cfabbdd1a35db98137cbfee1f566512685a3c759a9079ea6c`.

Isolated generated SDL hashes:

- Debug: `0217e78fffb574f95688e37f8558226252a84eb470979400435d86b00e7bc52e`.
- ASan: `039bf8e3f9e095fdd8aaf7ba7002040bf6f26c8a903a6bff65baf02d93c23288`.

The evidence directory retains pinned/fixed GDB observations, fixture sources
and provenance, build/regression summaries, the exact source snapshots/delta,
fresh-input probe copies and selected state packets. Temporary detailed logs
use `/tmp/e2-extended-target-*`; the immutable crash bundle is separate.

Next human acceptance is a longer normal F5 run without this crash. Resolve the
preserved animation-name mismatch before extending current-build bottle-removal
or generation acceptance. Complete crashed-recording replay, sustained gameplay,
potion lifetime/cure, broader pickups, original meshes and the earlier courtyard
steering/floor-return limits remain open. No stage, commit or push is made.
