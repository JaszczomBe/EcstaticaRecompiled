# Recover Object Rendering and Animation Contracts

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Item, Weapon, Door and Acid-Pool Models and Animations](../step-12-recover-object-models-and-animations.md)
<!-- /docs-tree:parent -->

Status: completed within the first eight-asset slice; wider Step 12 acceptance remains open
Parent Step: [Object models and animations](../step-12-recover-object-models-and-animations.md)
Parent Implementation: [Playable SDL Runtime](../../../playable-sdl-runtime.md)
Last Updated: 2026-10-28

## Goal

Map original assets and render/animation ownership for items, weapons, doors and
acid pools, then recover the first bounded object draw path. Start from the
existing character renderer and selective bypasses, without treating character
fixtures as acceptance of objects. Further class-specific work belongs in narrow
follow-on tasks under this step.

## Scope

1. Inventory one reachable representative of each requested class from original
   archives/scripts and live observations: resource/representation ID and name,
   scene/location, owner/attachment, primitive/material type and action/event
   ownership. Distinguish loose versus held weapons and door versus debris.
   Identify an actual acid pool; its identity and draw method are not yet mapped.
2. Trace dispatch, pose, raster inputs and page ownership through original
   disassembly/Ghidra. Audit bypasses, register-only parameters, local scratch
   records and shared callers before enabling a leaf or changing signatures.
3. Recover the smallest proven rendering slice, compare its original contract
   with bounded fixtures, and verify real native pixels across multiple frames
   and repaint/removal. Activate only that proven class; preserve other fallbacks.
4. Update this task and step with findings, commands, evidence and the next narrow
   class/path. Split additional tasks if shared raster repair grows in scope.

## Existing Source Map and Pitfalls

These are entry points observed in the current source and existing journals,
not newly recovered contracts or proof that a requested class uses every path.

| Entry point | Investigation purpose |
| --- | --- |
| `FUN_00424cbc` | Original mesh/primitive dispatch and selected leaf inputs |
| `FUN_00424e44 → FUN_00433d30` | Polygon/mode/reference selection; object raster bypass boundary |
| `FUN_00425018`, `FUN_00425538` | Box/rounded/ellipsoid leaves and their different bypass policies |
| `FUN_00423858`, `E2R_UseProxyMesh` | Full pose versus root-only fallback; player/NPC selection and owner node `+0x22` |
| `FUN_004211c8` | Physical-page redraw, restoration and graphic-slot overlap |
| `E2Recomp/tools/GenerateRecon.js` | Durable mirrors of existing dispatch, pose, raster and bypass repairs |
| `E2Recomp/platform/e2recomp_actor_markers.h`, SDL actor cues | Illustrative fallback classification/pixels; not original geometry or collision bounds |

The [enemy journal](../../../../../journal/entries/enemy-model-and-animation-2026-10-27.md)
records an earlier broad activation failure in
`FUN_00424e44 → FUN_00433d30 → FUN_00431a7c → FUN_00418b00`, with invalid surface
selector **−973722242**. Recover its real inputs if reached; do not guess a
surface index or globally enable unfinished raster paths. The
[player journal](../../../../../journal/entries/player-model-and-animation-2026-10-27.md)
retains projection/depth/pose evidence. Existing polygon-input, lighting and
DirectDraw tasks under Step 08 are prerequisites to inspect, with their explicit
limits; do not restart accepted character recovery.

Loose/held object and door evidence also exists in the
[sword-location journal](../../../../../journal/entries/blacksmith-sword-location-2026-10-20.md),
[dropped-potion repair](../../../../../journal/entries/enemy-play-crash-and-dropped-potion-2026-10-27.md)
and [door passage record](../../../../../journal/entries/workshop-door-passage-navigation-2026-10-26.md).
These establish resource/gameplay clues, not original object-pixel acceptance.
The initial handoff asserted no acid-pool asset ID, scene, animation method or
hazard contract; the current Review State below records the recovered map. Determine whether its visible effect uses geometry, textures,
sprites, palette changes or another original mechanism before choosing repairs.

## Out Of Scope

Sounds/music, synthetic geometry/animation, broad marker removal, physics or
damage changes, unbounded gameplay probes and writing installed saves.

## Acceptance Criteria

1. The four-class inventory identifies evidence and unresolved fields explicitly.
2. The first selected draw path has original register/memory/primitive/material
   contracts, generator mirroring and bounded normal/ASan comparisons.
3. Debug/ASan native captures show actual original object pixels, appropriate
   pose/action changes or documented static behavior, and clean repaint/removal.
   Fixture-only or marker-only results do not qualify native rendering.
4. Accepted characters, original HUD/F1/F2, object fallbacks and input remain usable.
   Affected persistence checks use private copies and freshly confirmed free
   slots; never use an occupied slot or quick-save slot 9.
5. Relevant builds, independent four-artifact parity and documentation checks
   pass; subsequent class work and remaining visual/gameplay limits are recorded.

## Verification

Use original `/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE` and external game
data with `scripts/e2_original.py`. For human investigation use the single
**Ecstatica Recompiled** F5 launch. For agents use bounded, isolated Debug/ASan
probes with recording off, unless a bounded recording/replay check is the stated
purpose. Compare physical/indexed/final SDL pixels and real resource/action IDs;
keep F1/F2 presentation choice independent of object rendering. Run affected
original-code/raster/attachment/surface regressions, SDL/X11 builds and generation
parity. Historical successful suite or replay runs do not satisfy this task.

## Review State

1. Original asset/owner inventory is recorded in the [recovery journal](../../../../../journal/entries/object-rendering-recovery-2026-10-28.md)
   and `scripts/e2_object_assets.py`. Verified IDs are **537** (potion), **3717**
   (loose/held sword), **980** (door) and **710/711/908/909/912** (acid/slime pools).
   The acid pool method is animated flattened ellipsoids/rounded bubble nodes,
   selected by original flags and actions **531/532/627**, with no polygon faces
   or sprite registration. Their scene is **350/mt_slim1**, camera **116**.
2. Implemented explicit selected root/bone ownership in `E2R_UseProxyMesh`,
   original high-resolution flat column/depth/Lock arguments in `FUN_00431a7c`,
   and box vertices/contiguous face tables in `FUN_00425018`. Every reconstructed
   change has a generator mirror; all four scratch-generated artifacts match.
3. Both configurations pass **3,072** original flat-polygon pixel/depth/rectangle
   cases and **1,024** box/**12,288** face-input comparisons, plus relevant
   character, lighting, ellipsoid pixel, routing, pickup, attachment and SDL
   marker checks. All four SDL/X11 Debug/ASan builds pass.
4. Fresh Debug/ASan native evidence covers potion pickup/removal then four sword
   directions, controlled door damage/removal/passage, animated pool preview and
   original/default/F1/F2 HUD with real-menu same/fresh-process Save/Load. All
   installed save hashes remain intact; test writes use private empty slot 5.
   Native chunked-recording contracts and 31 developer-launch cases per mode pass.
5. F5 enables only the eight listed assets and suppresses only their fallbacks.
   Unverified variants retain markers and bypasses. Two live door journeys failed
   on approach/combat; controlled passage does not replace them. Pool preview
   explicitly loads a remote scene and holds only camera selection under GDB;
   it does not prove natural traversal or hazard behavior. Human visual review,
   broader variants, textured and low-resolution paths remain open in
   [Task 02](task-02-qualify-object-variants-and-natural-acid-lifecycle.md).

## Change Log

### 2026-10-28

1. Recovered the original asset map, selected original geometry/actions and
   bounded Debug/ASan verification; recorded subsequent variant/lifecycle work.
2. Prepared the next context's first task after committed HUD/recording recovery.
