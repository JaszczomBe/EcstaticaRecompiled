# 2026-10-19 — Queued Idle-Action And Floor-Map Ownership

Area: Step 09 Task 06, player update `0x429bcc → 0x451880`, upstream of the release gravity write.

The observed ASan release-height failure is repaired. Both Debug and ASan now complete the bounded arrow and combined turn/Up probes at height 3328 in camera 175. Up release executes a queued action with further displacement; settled stopping, Down displacement, collision and scene traversal remain open. This does not establish full experimental sanitizer acceptance.

## First Producer And Original Contract

The unmodified starting runtime reproduces the earlier ASan failure (`/tmp/e2-gravity-before-asan`). Up displaces Joe, then release writes height -16000 and enters fallback resource 7, ultimately faulting in the root-pose child walk. A floor-call trace (`/tmp/e2-gravity-trace2-asan.log`) confirms the query receives actual position `9828,3328,-17363` and returns -16000. Its selected descriptor 4 contains `fd 01 00 80 00 00 08 fd`; `(128 - 253) << 7` supplies that height. Gravity consumes the query result as reconstructed; this trace does not justify a height clamp.

Watching the initial courtyard grid word at **0x686c0e** from the control-ready checkpoint finds the earlier producer. The initial cell is **27625** and its floor query returns **3328**. After Up release, `FUN_00447638` changes that word to **4** while decoding an unrelated FAN. Stack (`/tmp/e2-gravity-grid-asan.log`):

```text
FUN_00447638 → FUN_004453a4 → E2R_ParseArchiveFanResource
  → FUN_0045190c(param_2=12296)
  → FUN_00451880(param_2=representation_pointer)
  → FUN_00427584, queued default-action branch
```

The player update's `iVar7` still holds representation `+0x11e`. Its queued branch passes that pointer to a wrapper whose recovered action-ID argument is `param_2`. The pointer's low word becomes action 12296 in this run, and the resulting archive seek/parse replaces the live world grid before gravity executes. This is an action caller defect, not evidence that the live map should be retained across every legitimate resource load.

Original **0x429bcc..0x429bd5** reads the packed word at actor **+0x162**, sign-extends it and calls `0x451880`. The subsequent table lookup reloads the same actor field. The C caller now passes `(int)local_6c[0xb1]` as the action ID. The unused wrapper argument is zero. `GenerateRecon.js` reproduces that exact one-line repair through a unique anchored replacement. No gravity, floor selection, camera or host movement behavior changes.

## Original-Code Comparison

`scripts/check-e2-player-idle-caller.py` compiles the production queued branch and compares it with original `0x429bcc..0x429bec` instructions. **1,440 cases pass normally and under ASan**: three actor addresses, ten queued IDs through 32767, six poisoned stale representation/register values, four neighboring-word patterns, and absent/present action-table entries. The fixture compares loader IDs, call counts, selected action pointer and unchanged actor bytes. The loader is intercepted; this is caller coverage, not archive-loading or gameplay acceptance. No original instruction bytes are stored in the repository.

```sh
python3 scripts/check-e2-player-idle-caller.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
python3 scripts/check-e2-player-idle-caller.py /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE --asan
```

## Bounded Runtime Result

Both complete arrow probes, 60 update entries per phase, keep height 3328, representation 12, wait/modal zero and camera 175. All key-release held bytes are zero. Prefixes `/tmp/e2-gravity-after-{debug,asan}` contain JSON, logs and per-phase game/SDL/window packets.

| Runtime | Up held position / action | Up released position / action |
| --- | --- | --- |
| Debug | 9921,3328,-17392 / 8 | 9810,3328,-17366 / 1580 |
| ASan | 9828,3328,-17363 / 8 | 9463,3328,-17244 / 59 |

Release survives but has further displacement during its queued action. This supersedes the earlier immediate-stop observation: the old caller failed to load the actual queued action. The different bounded displacements are not timing/cadence parity. Down selects action 13; the Debug sample does not move, while the ASan sample changes Z by one unit. That is insufficient to claim usable backward locomotion.

All four combined-input probes also complete (`/tmp/e2-gravity-turn-{debug,asan}-{left,right}`, 20 entries per phase). They record 20 turn calls retaining Joe, clear both held keys, retain height 3328 and preserve facing on release. The new snapshot fields show queued action **1580** while Up is held and **-1** after release. Floor-cell reads stay on genuine courtyard entries 27625/27618 as Joe moves. The probe now records queued action and the cell under Joe through read-only memory access; no extra query call mutates game state.

```sh
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --output /tmp/e2-gravity-after-asan
python3 scripts/probe-e2-player-motion.py build/Debug/clang21-i386-sdl-asan/e2recomp \
  --turn-forward right --frames 20 --output /tmp/e2-gravity-turn-asan-right
```

These are zero-logo-delay crash probes using a timed Space followed by the actual courtyard release checkpoint. They do not reproduce the reference recording's two launches, separate logo taps or natural shortened horseback timing. Manual F5, a settled no-input interval, real-map stairs/blocked boundaries, adjacent-view crossing/return and 60 seconds after readiness remain unverified. Original models/HUD and automatic background spawning remain explicitly omitted; NPC activation is incomplete.

## Verification And Worktree

All four Debug X11/SDL builds pass. Relevant original-code fixtures pass normally/ASan: queued caller (1,440), root pose (1,152), action motion (1,920), interpolation (576), reset (96), representation/keys (10,368/256), polar/world query (394/92,160), and turn callers (1,296). The query fixture intercepts floor services; the runtime probes above supply the separate actual-map evidence.

The default wrapper (`/tmp/e2-gravity-regression.log`), all eight arrow-input baseline rows (`/tmp/e2-gravity-controls.log`) and both SDL requester drivers (`/tmp/e2-gravity-modal-{debug,asan}-driver.log`) pass. Generator syntax, in-place regeneration, independent four-artifact byte parity and whitespace checks pass. Comparing the starting artifact hashes confirms that only the intended caller line changed in reconstructed output during this continuation.

The starting index is unchanged (`/tmp/e2-gravity-start-index.txt`). Earlier staged and unstaged work is preserved; this continuation remains unstaged. No commits were made.

Next bounded action: trace queued release action 1580 (and its subsequent action selection) through completion and a settled no-input interval, then establish Down locomotion before genuine view traversal. Keep Task 02's complete control acceptance distinct from this closed map-replacement failure.
