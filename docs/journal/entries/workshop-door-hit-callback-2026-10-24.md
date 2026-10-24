# Workshop door hit callback — 2026-10-24

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

The user confirms pickup and sword swings after the
[attack repair](sword-attacks-and-attached-position-2026-10-24.md), then reports a
crash while bashing the left workshop door. Exact replay identifies a lost hit
script argument. The original selected-code/actor contract is restored in both
weapon-contact callback branches. Fresh Debug/ASan keyboard routes now damage,
collapse and deactivate this door, then walk through its opening with health 100.

## Captured failure

Human session `session_20261024_125515_737` pins Debug SHA-256
`c7c2001a5bc3499e693a25ef1112293108ad4beb88012743ef125fd9f1657a6e`.
Replay and inspection are incomplete after SIGSEGV. The verified bundle is
`.tmp/replay-bugs/door-contact-human-20261024`, also exported under
`/tmp/e2-door-contact-human-20261024`. Export used an inactive `/tmp` copy so the
original retained session was not mutated. The F5 receipt and debugger evidence
remain under `.tmp/f5-investigations/`.

Pinned replay and GDB reproduce the reported stack:

`FUN_0044f508 ← FUN_0044f32c ← FUN_0042efdc ← FUN_0042faf8 ← FUN_0042b880`.

The fault is at sequence **1,768,693,458**, last matching checkpoint **125**.
The attacker is Joe, through bone node `0x95379e`; the target is actor **980**,
original name **`kdorr`**, at **(-2368,4096,-10944)**. Its health has just fallen
from **100** to **60**, state **8**, and its hit script code is **147**. The
crash occurs on a hit before collapse, rather than on the final destructive hit.
Joe's attack script selector is **−1**, so this contact uses direct damage
followed by the target's hit callback.

The final human inspection also establishes that the workshop enemy **602**,
`korc2`, has health **−20**, state **11**, and no representation. Joe retains
health **100**, state **4**, equipped representation **9**, and sword **3717**
is attached and moving. This supplies recorded evidence of the user's smith
kill, beyond the earlier empty swing probes.

Evidence: `/tmp/e2-door-contact-exact.log`,
`/tmp/e2-door-contact-fault-gdb.log` and the preserved inspection bundle.

## Original contract and repair

Original `0x42f208..0x42f213` selects the attacker's script from actor offset
**0x138**. Original `0x42f44b..0x42f456` independently selects the target's hit
script from offset **0x136**. Both supply the selected record in **EAX**, owner
in **ECX**, target in **EDX**, target again as the stack child argument, and a
cleared node in **EBX**. The original `0x44f32c` wrapper forwards those inputs
into `0x44f508`.

The reconstructed contact calls retained actor arguments but dropped the
selected script record. They now use the existing `E2R_DispatchScriptRecord`
helper with the respective table entry, attacker owner, target, target and null
node. The helper scopes and restores the existing script contexts. Damage,
contact eligibility, script selection and door behavior remain original-shaped;
no door-specific state or health assignment is introduced.

Both repairs are mirrored with anchored replacements in `GenerateRecon.js`.
Syntax and independent scratch generation reproduce C, header, globals and names.
The area-contact helper `FUN_0042ea00` remains outside this recovered bone-contact
path and this acceptance claim.

Compatible replay of the repaired executable passes the crashing contact and
ends at the recovered recording's prefix boundary, still checkpoint **125**.
The published door health is now **60**. The run correctly reports incomplete
prefix exhaustion; it cannot supply subsequent strikes absent from the capture.
Fresh input supplies that integration evidence.

## Verification

| Check | Result |
| --- | --- |
| `check-e2-node-hit-query.py /path/to/E2WIN95.EXE [--asan]` | **16,384** existing direct/filter cases plus **16,384** scripted/direct combinations pass normally and under ASan; **37,188** callbacks match original selected code/owner/target/child/node, actor memory, HUD handoffs and restored native context |
| Four SDL/X11 Debug/ASan builds | Pass |
| Runtime baseline and arrow matrix | Pass; all **eight** control rows pass |
| SDL requester, OK, resumed update and Escape | Debug/ASan pass with independent output prefixes |
| Fresh left-door route | Debug/ASan acquire the sword, approach actor 980, hit it repeatedly, finish collapse/deactivation, release input and walk through the opening; Joe health **100**, state **4**, no modal or sanitizer error |

The fixture executes the original contact query and wrapper but intercepts the
script interpreter to compare its arguments. Sound and weapon-charge callbacks
remain excluded. The fresh runtime routes execute the actual hit and collapse
scripts, using only bounded SDL input and actor-state reads:

```sh
python3 scripts/probe-e2-player-motion.py \
  build/Debug/clang21-i386-sdl/e2recomp \
  --sword-pickup --bash-workshop-door \
  --intro-skip-action 1 --intro-skip-progress 83 \
  --background-spawns --burst-frames --timeout 260 \
  --output /tmp/e2-door-contact-final-debug
```

Use the ASan executable, 280-second timeout and a separate output prefix for the
counterpart. Recording is explicitly off. No actor coordinates, angles, health,
action, camera or attachment state are written. Door attacks are bounded by
**40 × 30** update batches, followed by released input, collapse completion and
an ordinary forward/release passage check.

Both runs observe door health **100 → 60 → 20 → −20**. Nonfatal hits select
action **370**, state **9**, then return to state **7**. The fatal hit selects
action **377**, state **5**, followed by state **11** with no representation.
Joe passes about **789** units beyond the door plane in Debug, ending at
**(-2075,4096,-11677)**, and **816** units in ASan, ending at
**(-2144,4096,-11729)**. Debug SDL frames before/after strikes and after passage
were visually inspected; passage changes camera **347 → 164**. These are
cylinder-mode behavior checks, not acceptance of original door meshes or visible
collapse animation fidelity. Diagnostic cues can still describe object records
whose representation has been removed.

Final executable SHA-256:

- Debug: `c2154b412502ed9ef09a5517657ac19cbfc60fb2d8f97fbb1515f12833296627`.
- ASan: `79be0ad67d870e973eeec74b9dbf5e76302c8844ce1e76a104b01661f3162ea5`.

Evidence prefixes are `/tmp/e2-door-contact-final-{debug,asan}`,
`/tmp/e2-door-contact-{fixture,fixture-asan,parity,baseline,controls}.log` and
`/tmp/e2-door-contact-requester-{debug,asan}-final`. Logs, JSON, original
instructions and selected state/frame packets are retained in
`.tmp/door-contact-20261024/final/`.

## Next acceptance and limits

Next is ordinary F5 repetition of left-door bashing, collapse and walking through
the opening. The human recording confirms one enemy death; automated probes
confirm one door's actual contact scripts and passage. Other destructible
objects, area attacks, broader combat, full meshes and armed swimming remain
unaccepted. The previously recorded ASan courtyard steering/floor-return limits
are unchanged and were not retested for this two-callback repair. No commit or
push was made.
