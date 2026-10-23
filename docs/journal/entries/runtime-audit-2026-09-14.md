# Runtime And Documentation Audit — 2026-09-14

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

## Scope And Provenance

Audited clean commit `43ddc8a` on `linux-e2-reconstructed-runtime` against the handoff, active implementation, related tasks, generator, native probes, compatibility code, original executable disassembly, and runtime output. The audit made no source changes. Documentation reconciliation followed in a separate pass; the repairs described below remain pending until their tasks are implemented.

All commands below run from the repository root. Probe artifacts live in `/tmp` and may disappear; the results and reproducer commands here are the durable evidence. Default debug and ASan use the X11 backend; the scene packet and GDB repro use SDL with the dummy driver. No manual F5 session, full menu sweep, or full modifier sweep was rerun.

## Follow-Up

The later Step 07 source passes restored generation, corrected canonical input, and repaired actor/action/motion ownership. The full debug/ASan wrapper, all 8 arrow rows, and default static SDL packet now pass; manual SDL was reported crash-free, but final-scene comparison remains pending. See the [runtime journal](runtime-crash-fixes.md) and [Step 07](../../implementations/playable-sdl-runtime/steps/step-07/step-07-restore-reproducible-runtime-baseline.md). Results below remain the original `43ddc8a` audit evidence.

The subsequent Step 08 pass recovers loader/current-actor and direct callback ownership and verifies first action-384 progress. Gated acceptance remains open: plain SDL misses scene-175 readiness, and ASan reaches a separate missing-scene message stack-use-after-return. [Task 04](../../implementations/playable-sdl-runtime/steps/step-08/tasks/task-04-recover-missing-scene-message-inputs.md) subsequently repaired that message-input failure and identified missing scene 40 (`mtorc4`). Gated SDL/ASan now expire in the scene wait without sanitizer errors; Task 05 owns the next position/scene-selection recovery. The trace's negative actor `rep_id` reads the high half of the runtime rep pointer; it is not proof of rep payload mutation.

## Results

| Check | Result at audited commit |
| --- | --- |
| Generator syntax | Passed |
| Default debug / ASan / SDL debug builds | All passed |
| Arrow matrix | Debug and ASan up/down/left/right passed (8/8) |
| Old regression wrapper | Exit 1: missing debug delayed movement latch after `num8`; ASan never ran |
| Default scene-175 automation | Exit 0 after sub-intro completion and 7000 ms settle |
| Gated action-index GDB probe | SIGSEGV in `FUN_0042ae80`; debugger exit code alone is not a runtime pass |
| Scratch generation | C differs by 155 removed/12 added lines; header/globals/names match |

### Build And Input Commands

```sh
node --check E2Recomp/tools/GenerateRecon.js
cmake --build --preset linux-clang32-debug
cmake --build build/linux-clang32-asan
cmake --build --preset linux-clang32-sdl-debug
E2R_SKIP_BUILD=1 E2R_CONTROL_MATRIX_TMP=/tmp/e2-audit-controls timeout 300 scripts/run-e2-control-matrix.sh
E2R_SKIP_BUILD=1 E2R_REGRESSION_TMP=/tmp/e2-audit-regression timeout 300 scripts/run-e2-runtime-regressions.sh
```

The three build trees were already configured. There is no ASan configure preset or CTest test preset in `CMakePresets.json`; a fresh checkout must configure its ASan tree separately.

The failed wrapper delivers key `0x68` and retains `move=[0,0,0,0,0,0,0,0,0]`. Canonical `VK_UP` is `0x26`; its matrix row latches the expected forward vector. The previous ASan scene-pointer caveat is historical and does not describe the current wrapper failure.

The native `e2r_wait_for_gameplay_frame` checks StartGame entry, `DAT_00479de8`, nonzero scene pointer, and optionally requester clear. It does not check completed `Start_sc`, visible geometry, or movement. Passing matrix rows therefore prove state delivery, not playable behavior.

### Default Scene Packet

```sh
SDL_VIDEODRIVER=dummy timeout 140 build/linux-clang32-sdl-debug/e2recomp --auto-scene175-visibility /tmp/e2-audit-scene175 120 7000
python3 scripts/e2r_visibility_sheet.py /tmp/e2-audit-scene175 --diff /tmp/e2-audit-scene175-diff.ppm
```

The runtime logs `actions=0 actors=81 reps=389 scenes=1205`, skips the first intro, completes `Start_sc`, preserves scene 175 over the scene-87 proposal, activates its record, then waits 7000 ms before capture.

```text
scene_ptr=0x67da4c scene_slot=175
selected_surface=3 selected_valid=1
surface3 hash=321e33d6
SDL present hash=914159a1
SDL window hash=5cf799a1 rect=0,80 640x480
current_actor=0xaa6bd8 action_ptr=0x0
render_rep_id=67 model=0xffffffff
slots17_24=-1,-1,384,384,384,384,384,384
render_tree=0x950d3c
current_actor_skip_active=0
```

The root render update list is empty and sampled local/projected vertices are zero. Scene-record children 319/322/318 have no actor instances but have scene/rep offsets. The selected image reproduces the static room baseline; the packet does not show the living player/enemies. Static scenery that resembles a person must not be classified as the rendered player without actor-state/pixel evidence.

### Action 384 Crash

```sh
SDL_VIDEODRIVER=dummy E2R_ACTION_INDEX_PROBE=1 E2R_RUNTIME_DIAG=1 timeout 140 gdb -q -batch \
  -ex 'set pagination off' -ex run -ex 'bt 8' -ex 'frame 0' -ex 'info locals' \
  --args build/linux-clang32-sdl-debug/e2recomp \
  --auto-scene175-visibility /tmp/e2-audit-action384 120 7000
```

Action 384 resolves at archive offset 9790200 and installs at `0xac263c`. `DAT_0047a470` is zero after parsing; `FUN_0045190c` subsequently writes it from a recovered `extraout_ECX_02`. The trace also reports a changed rep id after load. These are ownership clues requiring original-code confirmation.

```text
SIGSEGV at FUN_0042ae80: if (*in_EAX == 0)
in_EAX=0x5b59
FUN_0042ae80 <- FUN_00427584 <- FUN_0042a70c
             <- FUN_00426df8 <- FUN_0041007c
```

Original disassembly at `0x0042ae80` preserves incoming EAX/EDX/EBX into ECX/EDI/EBP, then dereferences EAX. The C declares uninitialized `in_EAX` and `unaff_EBX`. Recover explicit parameters and helper context rather than masking this with another pointer guard. Keep the index gated until the repaired path meets its acceptance checks.

```sh
objdump -d -Mintel --start-address=0x42ae80 --stop-address=0x42aef5 /home/rgrabowski/Games/Ecstatica2/E2WIN95.EXE
```

### Scratch Generator Comparison

This reproduces generation without overwriting committed reconstructed files. It copies the three inputs consumed by `GenerateRecon.js`, generates into a new scratch directory, compares all four outputs, and retains a C diff.

```sh
python3 - <<'PY'
from pathlib import Path
import difflib
import shutil
import subprocess
import tempfile

repo = Path.cwd()
audit = Path(tempfile.mkdtemp(prefix="e2-generator-audit-"))
for name in ("src/E2Recomp_decompiled.c", "metadata/functions.tsv", "metadata/symbols.tsv"):
    dst = audit / "E2Recomp" / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / "E2Recomp" / name, dst)
subprocess.run(["node", str(repo / "E2Recomp/tools/GenerateRecon.js"), str(audit)], check=True)
for generated in sorted((audit / "E2Recomp/reconstructed").iterdir()):
    committed = repo / "E2Recomp/reconstructed" / generated.name
    print(generated.name, "MATCH" if committed.read_bytes() == generated.read_bytes() else "DIFF")
old = (repo / "E2Recomp/reconstructed/E2Recomp_recon.c").read_text().splitlines(True)
new = (audit / "E2Recomp/reconstructed/E2Recomp_recon.c").read_text().splitlines(True)
(audit / "recon.diff").write_text("".join(difflib.unified_diff(old, new, fromfile="committed", tofile="regenerated")))
print("Evidence:", audit)
PY
```

At `43ddc8a`, missing mirrors principally remove actor-update exit logging, action lookup logging, actor model fields, rep-parser stop logging, and call sites. This is a diagnostic reproducibility defect; the audit did not establish that the diff changes intended game semantics. The action-index gate itself is mirrored. Do not regenerate over the committed diagnostic reference until scratch parity is restored.

## Documentation Corrections And Next Owners

1. The historical reconstruction milestone proves bounded state/surface behavior, not current visible gameplay.
2. The active implementation retracts “Joe visible” and replaces the stale ASan wrapper caveat with the observed debug numpad failure.
3. [Step 07](../../implementations/playable-sdl-runtime/steps/step-07/step-07-restore-reproducible-runtime-baseline.md) owns generator diagnostics and wrapper repairs; implementation is pending.
4. [Step 08](../../implementations/playable-sdl-runtime/steps/step-08/step-08-recover-scene-175-actors.md) owns action context, Joe geometry/rendering, and scene-backed child activation.
5. Remaining Step 03 control/camera classification is deferred until those prerequisites complete. Timing, audio, and packaging remain later steps.
6. Root/build READMEs now describe the experimental Linux/i386 runtime and link current setup/status. Historical Windows build instructions remain labeled as unverified by this audit.

## Artifact Index

Original ephemeral artifacts: `/tmp/e2-audit-controls.log`, `/tmp/e2-audit-regression.log`, `/tmp/e2-audit-scene175-state.txt`, `/tmp/e2-audit-scene175-s3.ppm`, `/tmp/e2-audit-action384-gdb.log`, and `/tmp/e2-audit-generator.diff`. Recreate them with the commands above, redirecting stdout/stderr to logs as needed.
