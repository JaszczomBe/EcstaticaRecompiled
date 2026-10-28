# Recover HUD and display-mode ownership

<!-- docs-tree:parent -->
[Project README](../../../../../../README.md) · [Parent: Recover Original Game HUD](../step-11-recover-original-hud.md)
<!-- /docs-tree:parent -->

Status: implemented; bounded verification complete with recorded native branch limits
Parent Step: [Recover Original Game HUD](../step-11-recover-original-hud.md)
Last Updated: 2026-10-28

## Intended result

Restore original HUD graphics, especially the life bar, as the default. F1 selects
the original HUD; F2 selects the existing debug overlay. Implementation and fresh verification are recorded below and in the
[recovery journal](../../../../../journal/entries/original-hud-recovery-2026-10-28.md).

## First bounded action

Trace the original HUD lifecycle and its callers before changing flags or enabling
the suppressed draw provider. Establish argument ownership, resource names,
graphic slots, bar values and dimensions, palette/page ownership, dirty rectangle
restoration, intro gating and menu/save-load redraw order. Record original address
ranges and representative state-to-pixel comparisons. Separate facts established
by disassembly from unresolved decompiler output.

### Source entry points observed during handoff

These are inspection leads, not recovered contracts or new HUD acceptance:

| Location | Observed state and next investigation |
| --- | --- |
| `FUN_004559bc`, original entry `0x4559bc`, next entry `0x455e84` | Decompiled HUD updater gates on `DAT_0047a76c == 0` and actor-0 slot `_DAT_00630b60`; reads fields including `+0xee` and `+0x182` and calls the graphic provider. Map every bar/value and its real resource arguments from the original. |
| `FUN_004555b0`, `0x4555b0..0x455850` | Reconstructed 2D graphic registration/draw provider returns zero under `E2R_PROXY_MESH_BYPASS`. Its body retains unresolved register inputs. Recover the original name, slot, position and draw contracts before enabling it. |
| `FUN_00455094`, `FUN_00455294`, `FUN_004554cc`, `FUN_00455850`, `FUN_00455940` | Inspect graphic lifecycle/loading, temporary graphics, slot clearing and redraw helpers in original code. Do not infer full behavior from function names or current placeholder calls. |
| `FUN_00455e84` and generator `E2R_MirrorHudIconNames` / `E2R_ClearHudIconName*` | Current startup cleanup/name mirroring is repaired separately from rendering. Trace asset names and ownership; do not delete cleanup to force visible graphics. |
| `FUN_00455fe8` | Decompiled icon-page path references `graphics` / `iconpage.raw`, palette work and `FUN_004559bc`. Determine which UI belongs to the gameplay HUD versus the original icon/inventory screen. |
| `FUN_0044f508`, script opcode `0x75` | Existing reference connects completion of the pedestal intro to `DAT_0047a76c` clearing and HUD update. Confirm actual call/visibility timing from original and current execution. |
| `GenerateRecon.js`, `E2R_PROXY_MESH_BYPASS` guards in graphic opcodes `0x27`, `0x29`, `0x2a` | Existing diagnostic skips preserve operand spans while omitting visual leaves. Audit their relationship to HUD registration and other graphics; retain script progression and unrelated mesh bypasses. |
| `E2Recomp/platform/e2recomp_host_backend_sdl.c`, `e2r_sdl_actor_cues`, `e2r_cue_player_status`, `E2R_HostPresentIndexed8` | The current debug text/health/status view is painted after indexed pixels are converted. Cue drawing is coupled to `E2R_ACTOR_CYLINDERS` / `E2R_ACTOR_CUES`; separate HUD/debug mode from scene-rendering fallbacks and observations. |
| `E2Recomp/native/e2recomp_native_main.c`, actor cue snapshots; `e2recomp_replay_adapter.c` | Diagnostics observe player health at `+0xec`, actions and timer state. These observations are not proof of original HUD scaling or indicator meanings. Keep replay/inspection observability usable with debug overlay hidden. |
| SDL key mapping and `e2recomp_win32_compat.c` message/input handling | SDL already maps F1–F12 to virtual keys `0x70..0x7b`; audit original consumption and host handling. F12 already bookmarks/captures. Add F1/F2 policy without leaking key state into gameplay or menu actions. |
| `.vscode/launch.json` | The single F5 launch enables `E2R_ACTOR_CYLINDERS=1`, `E2R_PROXY_MESH_BYPASS=1`, original player/NPC meshes and action recovery. Default original HUD must work in this real launch; merely changing an environment flag must not hide objects or disable recovered actors. |

The original body remains in `E2Recomp/src/E2Recomp_decompiled.c`; recover it
against `/home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE`, not only generated C.
Use `scripts/e2_original.py` for bounded comparisons. Read the complete current
functions/generator patches; line numbers will change as recovery progresses.

### Existing reference evidence

- [Original-game recording analysis](../../../../../journal/entries/original-game-reference-2026-10-14.md)
  and its retained contact sheet show no HUD during restraint/release, then HUD
  appearing around recording time 33.4–33.5 seconds in the pedestal courtyard.
  Window switches and unknown input timing prevent treating that timestamp as a
  game timer, fixed delay or exact internal resource mapping.
- [Diagnostic health/status journal](../../../../../journal/entries/diagnostic-health-and-potion-status-2026-10-24.md)
  owns the temporary health/poison/invisibility observations and read-only display.
  That panel is the fallback to retain behind F2, not original-HUD acceptance.
- [Menu layout/font journal](../../../../../journal/entries/menu-layout-and-font-2026-10-28.md)
  owns current surface/palette/geometry and persistence evidence. Preserve its
  menu behavior and installed-file protection while recovering HUD draws.

## Incremental implementation and verification

1. Map the original HUD lifecycle, assets, current/max values and renderer/page
   contracts. Capture a bounded current counterexample showing the debug panel
   and omitted original HUD, with executable identity and recording disabled.
2. Recover the necessary 2D graphic registration/loading/draw/restore chain and
   original HUD updates. Start with the life bar, then recover the related HUD
   elements identified by original evidence. Keep character rendering, physics,
   scripts and object/equipment fallbacks intact.
3. Introduce a presentation-mode owner at the host/compatibility boundary, default
   original on process start. Wire F1/F2 as idempotent selections. Hide diagnostic
   panels/text/labels in original mode while retaining the existing F2 debug view.
   Preserve original HUD cinematic/modal gating and clean up pixels on switching.
4. Mirror every reconstructed repair in the generator, verify all four artifacts
   independently and build affected SDL/X11 Debug/ASan presets.
5. Verify real input switches F1 → F2 → F1, repeated keys/key release, menu
   cancellation and damage/healing redraws. Capture both indexed game pages and
   final SDL presentation because the debug overlay is added after conversion.
   Verify no ghosting, stale bar values, duplicate HUDs or lost controls.
6. Recheck accepted persistence as affected: same/fresh-process load, correct HUD
   values after restoration, automatic dismissal and untouched gameplay buffers
   after preview cancellation. Use private copies of confirmed free slots only,
   recording disabled, write ownership guards and installed/unowned file hashes.
7. Record new acceptance and remaining branches in this task, Step 11 and a dated
   journal. Keep existing broader gameplay/rendering limits explicit and leave
   sounds/music for their later selected turns.

## Review state

1. Planning state: agreed by user selection.
2. Implementation state: implemented with bounded original-code/native verification.
3. Original HUD defaults, process-local F1/F2 ownership, read-only original visual
   recovery and protected Save/Load verification pass. Retain native indicator,
   low-mode, human visual review and broader gameplay limits in Step 11.

## Recovered implementation and verification

The [recovery journal](../../../../../journal/entries/original-hud-recovery-2026-10-28.md)
records the original address/register map, all indicator fields/assets, graphic
lifecycle audit, host composition decision, counterexamples and fresh results.
The generated `E2R_GetOriginalHudState` reads the live actor-0 table and original
HUD gates; `E2R_DrawOriginalHudState` preserves recovered graphic selections,
coordinates, life scaling, poison-limit branches and magic grouping. The host
owns immutable assets, indexed clipping and display choice. Every repaint starts
from the selected game page, preventing ghost pixels without enabling unresolved
legacy graphics. `GenerateRecon.js` reproduces these visual leaves and the
original live-keyboard visibility repair; all four artifacts match independently.

Evidence root: `build/evidence/hud-2026-10-28`. Original normal/ASan comparisons
cover 600 selection, 1,056 life/poison, 212 held-magic and 512 keyboard decisions,
plus 96 sprite and 10,332 line raster cases. `final-debug-25` and `final-asan-26`
verify original-default processes, eight identical F1/F2/F1 restorations overall,
key repeats/releases/focus events, pixel-identical modal switching, repeated
private equipped Save/Load, fresh loading, movement and attacks. Sixteen preview
selections match both menu pages while preserving physical game pages. Four
native processes exit zero. Original/unowned private save hashes are unchanged.

The focused matrix passes 22 checks; generator parity and 67 runner contracts
pass separately. SDL/X11 Debug/ASan builds pass. Natural damage and Debug healing **70→100** verify actual life pixels.
ASan healing and higher indicator native conditions remain explicit limits.
Final integration passes **24/24** with parity and the 67 runner contracts;
individual potion outcomes and failed routes remain in the journal. Historical persistence/menu/full-suite results are not counted here.
The ordinary F5 launch remains the sole human gameplay launch and needs no new
flags. Sounds and music remain later work in the selected order.
