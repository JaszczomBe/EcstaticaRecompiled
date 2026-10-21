# Stables Node Hit-Query Inputs — 2026-10-20

The user reports a crash entering the stables, where the horse should be. The screenshot identifies camera 177, Joe at `2986,4096,-6646`, three live actors and no modal/script wait. The supplied stack is `0x427160 ← 0x42efdc ← 0x42faf8 ← 0x42b880`, through an NPC action update. This is the hit-query leaf beyond the [preceding node/pose handoff recovery](npc-pose-chain-recovery-2026-10-20.md); that recovery explicitly left general hit queries/combat unaccepted.

## Cause And Original Contract

`FUN_0042efdc` still called the legacy `FUN_00427160` with only delta Z and a distance buffer. Its uninitialized implicit EAX output pointer causes the reported write failure. The original instructions at `0x42f075..0x42f09d` supply four independent inputs:

- node world X/Z at `+0x18/+0x1c`, minus candidate root X/Z at `+0x84/+0x88`, narrowed to signed shorts;
- EAX points to the angle output at stack `+0x14`;
- EDX points to the separate distance output at stack `+0x10`.

The candidate radius test uses the distance, not the angle. The reconstructed caller now supplies both coordinates and distinct local outputs through the existing original-compared `E2R_NpcPolar16`. No radius/height rejection, actor state, damage rule or population gate is bypassed.

The next facing calculation at `0x42f15f..0x42f188` also lost delta X. It now supplies **candidate minus node-owner root X/Z**, retaining the original distinction between node position for proximity and owner position for facing. This uses the existing original-compared angle helper. Both repairs are mirrored in `GenerateRecon.js`; other legacy polar callers and broader scripted/weapon contacts remain separate work.

## Focused Regression

New `scripts/check-e2-node-hit-query.py` executes the complete original `0x42efdc` helper, original polar/angle instructions and the production reconstructed function against identical mapped actor records. The stable coordinates seed synthetic actors; this is not a claim that the exact live stable scene was reconstructed by the fixture.

Normal and ASan comparisons pass **16,384 cases and 23,129 contacts**, comparing every byte of actor/node memory and the player HUD handoff. Coverage includes missing/disabled representations, shared attachment ownership, owner-ID exclusions, radius equality, both exact height limits and just-inside values, disallowed actor states, existing hit flags, invulnerable actions, direct-contact facing/health changes, attached source owners, and player difficulty/scaling branches. Sound, scripted contacts and weapon-charge callbacks are deliberately outside this bounded test.

```sh
python3 scripts/check-e2-node-hit-query.py \
  /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
```

## Runtime Checks And Limits

The populated early-Space Debug and ASan courtyard regressions both complete `175 → 166 → 175` and another 60 seconds of continuing NPC updates, without a sanitizer report. Each records activity in all 140 observation intervals; resource IDs 77, 78, 79 and 81 move. Logs/censuses are `/tmp/e2-stables-regression-{debug,asan}.*`. The established pose fixture still passes under ASan.

A bounded Down-only actual-SDL navigation attempt stays near the pedestal in camera 175 and ends on its route assertion; it does not crash. A second attempt continues from the established courtyard crossing, reaching cameras 166 and 169 before circling back near the courtyard; its bounded Down continuation does not establish camera 177. Read-only tracing records two real node hit queries owned by resource 56 during this exploration. Neither attempt writes Joe's coordinates, facing or camera. These are navigation limits, not stable re-entry passes; exact manual stable re-entry remains pending.

All four SDL/X11 Debug/ASan builds and independent four-artifact generator parity pass. Runtime baselines, all eight control rows and both visible SDL requester checks pass; logs use `/tmp/e2-stables-{baseline,controls,requester-*}`. The starting staged patch remains byte-identical to `/tmp/e2-stables-start-index.patch`; prior unstaged pose work is retained. No commits were made.

This repairs the reported leaf's calling contract and its adjacent facing calculation. Horse presence, every stable interaction, scripted contacts, general combat and full experimental ASan remain unaccepted. A later failure deeper in those paths must be traced to its first original-code contract rather than suppressed.
