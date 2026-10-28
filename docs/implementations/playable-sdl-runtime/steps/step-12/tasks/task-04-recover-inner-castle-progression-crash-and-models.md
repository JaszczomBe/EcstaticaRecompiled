# Recover Inner-Castle Progression Crash and Missing Models

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Item, Weapon, Door and Acid-Pool Models and Animations](../step-12-recover-object-models-and-animations.md)
<!-- /docs-tree:parent -->

Status: selected next continuation; human crash confirmed by saved debugger evidence; reproduction and fixes pending
Parent Step: [Object models and animations](../step-12-recover-object-models-and-animations.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-28

## Goal and priority

Continue from the user's extended tower/inner-castle gameplay: first reproduce
and repair the demonstrated `FUN_0042d61c` crash, then recover the missing original
models/effects on that route. This supersedes Task 03 as the immediate continuation;
its bounded key/door/persistence evidence remains valid within its recorded limits.
Remaining variants/acid work stays in Task 02; sounds and music stay deferred.

The [handoff journal](../../../../../journal/entries/inner-castle-progression-handoff-2026-10-28.md)
owns the latest session identity, crash coordinates, save inventory and human
observations. This handoff changes documentation only; it does not reproduce,
diagnose conclusively or fix the new crash.

## Human progression and presentation findings

The user reports obtaining magic armour, passing the gargoyles, obtaining the
tower prison key, meeting the wizardess and receiving instructions, then reaching
the tower top and collecting the magical mace. The user identifies the mace as
the weapon that can bash open the inner-castle gate; actually bashing that gate
was not reported as completed. On descent the user used two gold head levers,
then a dark head lever further along, opening both gates before the crash.
This is human progression evidence, not a verified replay or exhaustive fidelity
claim, and the last interaction is not yet proven to cause the crash.

| Reported object/sequence | Human observation to investigate |
| --- | --- |
| Teleport | No model, only a diagnostic box overlay. |
| Head switches/levers | No models, only diagnostic box overlays; two gold heads and a later dark head were used. |
| Magic armour | No model, only a box; collecting it adds another box overlay to Joe. Trace loose and equipped/attached ownership separately. |
| Gates near the armour | Incorrect rendering; distinguish original background, gate geometry, action, depth and repainting. |
| Wizardess | A model is visible but lacks details. Identify omitted children/equipment/materials from evidence rather than assuming a new character body. |
| Tower prison key | Spawned, but no model. This is a later key; do not assume Task 03's key **264** is the owner. |
| Magical mace | No model; magical blinking effects also appear only as boxes. Trace loose/held weapon and effect owners separately. |
| Tower stairwell strike on descent | A flash occurs, but no lightning or rubble is visible. Recover original scripted strike/debris ownership and lifetime, without substituting the already qualified intro lightning. |

The objective is preservation of original code and behavior, including possible
original-game defects. Missing detail or translucency alone does not authorize
cosmetic changes, forced opacity, easier pickups or replacement artwork. The
earlier partly translucent tower door remains unresolved under that boundary.

## Crash starting point

Session: `~/.ecstatica2/logs/session_20261028_173846_961/`.
Pinned Debug executable SHA-256:
`33c4ce05ad0722a60e3b748a52b502f06069f7b638c1af44ad862ebab02b6d2e`.
The investigation manifest is finalized and retention-protected, with last
signal **SIGSEGV**, status `terminated-by-debugger-or-signal`, no normal return
code, and both replay/inspection incomplete. Keep the incomplete markers and
unsealed tail; do not manufacture a completed recording or weaken checkpoints.

The saved debugger trace records sequence **9684450756**, last checkpoint
**3190**, and the main-thread stack:

```text
FUN_0042d61c:24944
FUN_0042b880:23657
FUN_0042b338:23020
FUN_0042ae80:22798
FUN_00427584:22085
FUN_0042a70c:22433
FUN_00426df8:19606
FUN_0041007c:4427
E2R_WinMainThunk:517
main:2904
```

Lines refer to the pinned source context, not stable identifiers after edits.
The trace has callee local `in_EAX=328/0x148`, caller
`FUN_0042b880(param_1=11284774,param_2=0xaaeab0)`, and selected
`unaff_ESI=0xa350fe`. Current C's event **0x23** invokes `FUN_0042d61c()` without
an explicit selected-node argument; its first dereference uses the unresolved
`in_EAX`. This is a lead for original register/owner recovery, not an established
repair or permission to insert a pointer guard. Resolve the actual actor, node,
event, action and original register contract before changing code.

Last published inspection reports camera **54**, frame **1450**, snapshot
**6184** and input-before Up press at sequence **9684450751**. These precede the
signal and do not identify the faulting actor. Earlier cameras and the loaded
save slot still need reconstruction from the recorded route/menu evidence.

## Next bounded action

1. Preserve the session, pinned executable/source patch and all current runtime
   saves in private read-only fixtures with SHA-256 inventory. The source session
   is already retention-protected; do not write source metadata or replay against
   user saves. Identify the actual loaded slot before choosing a reproduction.
2. Attempt the pinned crash-prefix replay using supported incomplete-recording
   handling and explicit bounds. Record the last matching checkpoint and exact
   signal/actor/event; a prefix match or divergence alone is not crash reproduction.
   If needed, use a protected copy of the appropriate save and bounded ordinary
   input. Retain unsuccessful attempts honestly.
3. Compare `0x42d61c`, event **0x23** in `0x42b880` and their helper contracts
   against original disassembly/Ghidra and bounded original-x86 fixtures. Recover
   the real argument/transform/list ownership. Mirror any reconstructed C repair
   in `GenerateRecon.js`, regenerate narrowly and verify independent parity.
4. Revisit the reproduced route under Debug/ASan, establish survival beyond the
   former crash with control intact, and verify original event effects rather
   than merely skipping the faulting call. Keep human route acceptance separate.
5. Map the eight presentation findings to actual original actors, attachments,
   representations, scenes, primitive/material/texture and event ownership.
   Qualify real pixels and changing poses/lifetimes before extending selective F5
   rendering. Preserve F3 fallbacks, character details and original HUD ownership.

## Preservation and acceptance

- **Runtime slot 5 is now occupied** by the user's **123** save. Slots **6/7/9**
  are also occupied. Never reuse the preceding tower probe's private-slot-5
  assumption against this source set. Choose a freshly verified free private
  slot, protect all unowned saves, and retain quick-save **9** unchanged.
- Accept the crash repair only with original-code comparison, fresh Debug/ASan
  reproduction/regression evidence and meaningful post-event progression.
  Do not force progression flags, bypass gates/traps, remove effects, teleport
  actors or change damage/physics/timing to make the route pass.
- Verify loose/equipped magic armour and mace ownership, key pickup, lever/gate
  transitions and natural strike/debris lifetimes. Asset previews are narrower
  evidence than naturally reached events; keep those limits visible.
- Retain original-format protected same/fresh-process Save/Load, independent
  F3/HUD/F1/F2, menus/Quit, recording and prior accepted tower progression.
  Use one normal **Ecstatica Recompiled** F5 launch for human investigation;
  agent probes use isolated storage, bounded input and recording off except
  explicit recording tests.
- Run affected SDL/X11 Debug/ASan builds, relevant original-code fixtures,
  generator parity and documentation-tree checks. Update this task and journal
  with new evidence; preserve all staged/unstaged work and do not commit/push
  unless separately requested.
