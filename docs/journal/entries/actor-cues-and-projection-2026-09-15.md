# 2026-09-15 — Scene projection and actor recovery

Area: camera arithmetic, SDL diagnostic cues, scene activation and render inputs.

Symptom: the X/Z inset did not place Joe or enemies relative to the background, and intro/input probes left Joe at the same coordinates.

## Recovered projection

Original `0x415491..0x4154fb` initializes 65,536 sine/cosine entries at `0x59b590` / `0x5de590`; the reconstruction had left them zero. The original constants are `6.28318`, `1/65536`, and `16384.5`, with truncation toward zero. Rotation routines `0x422368`, `0x422460`, and `0x422538` preserve both input components before writing the pair; the decompilation reused overwritten components.

The vector helper `0x45de8b` takes input in EBX, a row-major Q14 matrix in ESI, and output in EDI. `E2R_TransformVector14` recovers this with explicit arguments, wrapping 32-bit sums and alias-safe input reads. Unrecovered no-argument `FUN_0045de8b` callers remain stubs; this is not complete renderer recovery.

`FUN_00422fd8` now receives output and world-position buffers explicitly, subtracts the mapped camera position, rotates, rejects depth below 128, and applies `0x423070` perspective. `E2R_Perspective14` shares the recovered arithmetic with host diagnostics, including Q4 screen coordinates, high-resolution scaling and overflow rejection. The directly adjacent projection callers now supply their real output buffers. `FUN_00422abc` reads the mapped camera words rather than disconnected host globals.

The SDL diagnostic constructs a private camera matrix from the active 28-byte camera record, then projects a ground cross and upright for each table-confirmed live actor. Cyan means Joe; amber means another live actor, not necessarily an enemy. Dimensions (upright 1024, cross radius 256 world units) are diagnostic, not recovered character bounds. These primitives have no background occlusion and modify only the RGB presentation surface. The large grid and fixed enemy-status icons are removed.

## Why the default scene still lacks a Joe marker

The final gate-off packet reaches camera slot 175, with Joe alone at `12800,256,-3584`, action duration/progress `1102/1102` and a null action pointer. Camera position is `5788,1856,-15334`, with angles `3328,-24064,256`. Joe's camera depth is **-3062**, behind the camera. The overlay therefore reports **0 VISIBLE / 1 BEHIND / 0 OFFSCREEN**, rather than inventing an in-frame location. The indexed framebuffer remains `321e33d6`.

Default action indexing remains disabled (`actions=0`). Input latches and the intro timer can advance without source-consistent live-position updates. Enabling the recovered action route now changes Joe's live position to `9184,3328,-17416` before a geometry crash; that is evidence of changed state, not correct final placement or playable movement.

## Pose, matrix destinations, and event metadata

1. Original `0x452540..0x45256b` preserves actor `+0x122` across pose restoration. Both `FUN_00426010` and `FUN_00426124` now take the actor explicitly, preserve entry context around nested node helpers, and their callers supply it. Activation clears actor `+0x90` and initializes actor `+0xc6`, rather than relying on lost register destinations.
2. With working trigonometry, a hardware watchpoint found `FUN_00421074` rotating the horse scene record and destroying its child-list head. Original `0x4210b8..0x421101` targets **actor + 6**. The recovered simple root branch now does so. Evidence: `/tmp/e2-scene-head-watch.log`.
3. Event dispatch read packed words at `0x636700..0x63683a`, while `FUN_00416cb4` initialized separate C globals. Restoring the original packed priority/flag table under `E2R_ACTION_INDEX_PROBE=1` fixes event `0x3f` routing into the wrong actor/requester path. The host-global assignments remain for unrecovered readers. The original initializer validates all 158 words, including reserved zeros.
4. A second watchpoint found `FUN_00423858` rotating **node + 0x136**, corrupting the attachment pointer at `+0x13a`. Original `0x423c34..0x423c6b` targets **node + 6** for all three simple-branch rotations. Correcting those destinations passes the attachment failure. Evidence: `/tmp/e2-attachment-watch.log`.

The next gated SDL/GDB stop is `FUN_00424dd8 → FUN_00424e44 → FUN_00433d30 → FUN_00431a7c`, reading `unaff_EBX + 4` with `unaff_EBX=1`. Audit the polygon helper's register ownership and parameter meanings before changing it. This belongs to Step 08 Task 02. No broad pointer guard or forced scene/position was added. An experimental node-camera recovery in `FUN_00424ed0` exposed another unrecovered render input and was reverted; its stub calls remain.

## Corrected child-resource evidence

Camera slots and script scene-resource IDs are separate namespaces. The old packet's `scene_id` was actually the camera X coordinate, and its lookup of resource 175 from camera slot 175 was unjustified. Diagnostics now emit `camera_x` and only list a table-confirmed resource reached through actor `+0x132`; the settled default packet has no such owner and reports that explicitly.

Activation tracing identifies `Start_sc` resource **0**, with children **261 / 0 / 3551**: 261 is hidden `spide_w3`, 0 is Joe, and 3551 has a secondary reference to 695 / `wdpile2`. The horse resource is 1564. The previously reported resource-175 children 319/322/318 are not established as the pedestal enemies. Recover resource roles and the post-intro owner before implementing enemy markers or instances.

## Verification and limits

All four Debug builds pass: X11, X11 ASan, SDL and SDL ASan. Generator syntax and all four artifacts match scratch regeneration. The original-machine-code comparison passes 4,096 deterministic cases across all rotations, Q14 vector transforms (including in-place), perspective and overflow handling, plus the packed event initializer:

```sh
python3 scripts/check-e2-projection.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_REGRESSION_TMP=/tmp/e2-cues-isolated-regression scripts/run-e2-runtime-regressions.sh
env -u DISPLAY E2R_SKIP_BUILD=1 E2R_CONTROL_MATRIX_TMP=/tmp/e2-cues-isolated-matrix scripts/run-e2-control-matrix.sh
SDL_VIDEODRIVER=dummy E2R_STARTUP_LOGO_DELAY_MS=0 E2R_ACTOR_CUES=1 timeout 45 build/Debug/clang21-i386-sdl/e2recomp --auto-scene175-visibility /tmp/e2-cues-final-default 35 7000
```

The isolated default regression wrapper passes Debug and ASan. An earlier desktop-connected wrapper failed its ASan state assertion after unrelated keyboard input entered the window; its log is retained at `/tmp/e2-cues-final-regression.log`. Use the isolated run above for the automated result. The final isolated arrow matrix passes all eight Debug/ASan rows (`/tmp/e2-cues-isolated-matrix.log`).

The default SDL packet exits 0 and confirms the real behind-camera result. A presentation-only GDB fixture injected two synthetic projected markers, producing visible cyan/amber crosses and uprights while retaining game-surface hash `321e33d6`; `/tmp/e2-cue-render-fixture.png` tests drawing only and is **not** evidence of living Joe or enemies. No fixture position is in production code.

The final gated SDL/GDB capture catches the geometry SIGSEGV above (`/tmp/e2-cues-final-gated.log`); GDB's shell exit 0 is not a successful game run. The gated headless ASan readiness probe exits 5, still in camera 1073 after 35 seconds (`/tmp/e2-cues-final-gated-asan.log`), without a sanitizer report. A separate default SDL ASan readiness probe exits 5 in camera 87. Neither establishes scene-175 ASan readiness. The new manual F5 visual check remains pending.

Regression risk: recovered math activates previously inert transform callers. The two watched destination fixes address confirmed corrupting writes, but other hidden-register renderer calls remain. Keep action indexing and its pool/event-metadata repairs gated until geometry, final placement, action progression and child activation are validated.

## Same-day F5 follow-up

The supplied 35-second recording confirms grid replacement and bounded default-route survival, completing Task 07’s manual cue check. Its apparent post-intro freeze is a blocking action-error requester, not proof that the intro timer stops. The [requester continuation](post-intro-requester-2026-09-15.md) restores visible text/OK routing and records updated regressions. Static hashes above describe the earlier pre-repair capture; the new dialog changes game pixels.
