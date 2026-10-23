# Blacksmith Sword Location — 2026-10-20

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Task: [Step 09 Task 09](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).

## Selected Reference

The user supplies matching original/recompiled screenshots of the blacksmith interior and an F12 packet from the recompiled run. The original shows a sword beside the left workbench and the blacksmith by the forge. Neither is visibly represented at those positions in the diagnostic screenshot.

Use this sword as the first object target. The user explains that switches are sparse and quest gated, while doors are destroyed with sword attacks rather than opened through a generic interaction. Those are unsuitable first targets without additional progression/animation recovery. A potion remains an alternative; poisonous potions must not be treated as equivalent to healing potions.

The packet identifies **camera 347**, with Joe at **(-1295, 4096, -10019)**. Preserve the capture under `/tmp/e2-sword-camera347-user/`; `identification.json` records the source chunk and packet hashes. These temporary files are evidence, not repository assets.

## Original Archive Identification

Reading the user's original `Files/ECSTATIC` and name pools in `Code/ECSTATIC.FAN` establishes:

| Field | Original value |
| --- | --- |
| Script scene resource | **1909**, `nschwrt1` |
| Camera referenced by that scene | **347** |
| Scene child actor | **3717**, `nschwrt1` |
| Placement position | **(-972, 3884, -10208)** |
| Scene chunk archive offset | **0x0cb468** |
| Scene chunk length | **194 bytes** |

The scene root is the big-endian word sequence `(25, 1909, 347, 65535, 65535)` at chunk offset 54. Its child starts `(26, 65535, 0, 2, 3717)` at offset `0x80`. The position event at `0x94` is `(22, 0, -972, 3884, -10208)`. Both independent name pools label the corresponding resource `nschwrt1`. A read-only extraction asserts these records and names against the installed original data; no original game bytes are added to the repository.

The placement is about 374 world units horizontally from captured Joe. An approximate projection fitted from the packet's actor cues places the sword root near pixel `(160, 296)` and its floor point near `(162, 347)` in the 640×480 scene. This agrees with the sword beside the workbench in the original screenshot. The fitted projection is supporting inference, not an executed original projection comparison or pickup-behavior proof.

Other scenes referencing this camera include **251**, `blaksmit`, with child **602**, `korc2`, and **373**, `cyd_dor8`, with child **980**, `kdorr`. The missing blacksmith is therefore a separate original scene target from the sword and from wandering terrain creatures. Camera 347 must not be used as a script-resource ID.

## What F12 Establishes

The global active list contains Joe, wandering actors 9/75/12/26 and splash effect 3803. Sword actor 3717 and blacksmith actor 602 are absent from that list. Generic population is enabled; its script gate is zero.

This establishes absence from the captured active list, not absence from all loaded resource tables. The current F12 packet dumps the active actor list and the current actor's script-owner children; Joe has no script owner at this point. It does not census every loaded actor or every loaded/active script scene. The cylinder count cannot distinguish unloaded, inactive, hidden and differently rendered objects.

## Next Contract And Limits

Trace scene **1909** and actor **3717** through the actual original startup/terrain script, archive lookup, loaded tables, scene-child activation and presentation eligibility. Capture their loaded/active state before changing behavior. If existing diagnostics cannot establish that state, extend the read-only capture generically rather than injecting an object or starting a scene based on its camera number.

Repair the first demonstrated failed contract, then verify an appropriate diagnostic representation at this location before recovering the sword's original pickup behavior. Sword acquisition, equipped state, attacks, door destruction and original meshes/animations are separate milestones. This investigation changes documentation only; no runtime fix or interaction acceptance is claimed. Existing staged work remains staged, and this continuation remains unstaged.

The subsequent [activation continuation](blacksmith-sword-activation-2026-10-20.md) now establishes that the scene is preloaded and repairs its placement/visibility/loading path. It supersedes the loading uncertainty above with bounded Debug/ASan cylinder evidence; manual workshop re-entry and pickup remain open.
