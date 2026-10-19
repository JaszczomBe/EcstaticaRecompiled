# Project Journal

This journal is the historical project memory for exploratory Linux runtime work. Keep it as an index and place detailed entries under [entries/](entries/).

## Entries

- [SDL arrow release, frame clock and target facing — 2026-10-19](entries/player-release-and-spin-2026-10-19.md): reproduces the actual SDL stuck-arrow release, restores real-tick waiting and the reported target-facing crash inputs; final fixtures/baselines pass, with motion-query steering still open.

- [Queued idle-action and floor-map ownership — 2026-10-19](entries/player-idle-action-2026-10-19.md): repairs a representation-pointer-as-action-ID caller that replaced the live floor grid on release; bounded Debug/ASan arrows and combined inputs retain valid height, with stopping and traversal still open.

- [Forward/turn caller actor ownership — 2026-10-16](entries/player-turn-callers-2026-10-16.md): reproduces the reported Up-after-rotation stack, repairs two direction-byte-as-actor calls, and verifies combined input while retaining the separate ASan gravity failure.

- [Player motion vectors and world query — 2026-10-16](entries/player-motion-query-2026-10-16.md): original-code recovery lets Up displace in both runtimes; corrected Debug arrows turn and release, while ASan exposes a watched release gravity-height failure.

- [Player representation and live keyboard inputs — 2026-10-16](entries/player-motion-inputs-2026-10-16.md): original-code selector/scan-table recovery lets Up reach movement event 0x13; Debug/ASan expose the next world-motion output/actor failure, with displacement still unproven.

- [Terminal root-pose ownership — 2026-10-16](entries/terminal-root-pose-2026-10-16.md): fixes the watched ASan event-link writer, compares original root-pose destinations, and records matching Debug/ASan terminal chains; motion remains unresolved with representation 67 bound.

- [Courtyard floor decoding — 2026-10-14](entries/courtyard-floor-decoder-2026-10-14.md): valid hosted byte reads restore the release view; NPC query/range inputs have original-x86 coverage; F5 explicitly defers background spawning while movement and terminal ASan events remain open.

- [Palette regression and release handoff — 2026-10-14](entries/palette-and-release-handoff-2026-10-14.md): restores fade inputs/colors, excludes the incorrectly signed ground descriptor, recovers the original no-view fallback and records the remaining death/menu handoff.

- [F5 diagnostic route — 2026-10-14](entries/f5-diagnostic-route-2026-10-14.md): aligns the editor launch, recovers event/script inputs, records a continuously visible pedestal cylinder and the remaining bad-height/immobile post-intro result.

- [Diagnostic cylinders — 2026-10-14](entries/diagnostic-cylinders-2026-10-14.md): read-only projected cylinders and state panel, opt-in polygon boundary, passing fixtures/regressions, real visible Joe during the pedestal action and the next event-0x3f node-removal failure.
- [Dirty-rectangle copy inputs — 2026-10-14](entries/rectangle-copy-2026-10-14.md): explicit copy inputs/page selection, mapped lock descriptor and unlock ownership; original-x86 comparisons and regressions pass; generic DirectDraw Lock supplies no destination storage/pitch.
- [Original-game video reference — 2026-10-14](entries/original-game-reference-2026-10-14.md): timestamped screen/actor log and contact sheet, stocks/release/HUD checkpoints, executable provenance, code correlations and missing reconstructed behavior.
- [Documentation review — 2026-10-14](entries/documentation-review-2026-10-14.md): checked latest source/handoff, corrected setup guidance, reverified generator and polygon/lighting comparisons, and scoped rectangle-copy recovery plus original-game captures.
- [Flat-polygon lighting — 2026-09-21](entries/polygon-lighting-2026-09-21.md): recovered normal/angle/rotation inputs and mapped byte reads; original-x86 comparisons pass; gated SDL now reaches framebuffer-copy failure.
- [Polygon inputs — 2026-09-21](entries/polygon-inputs-2026-09-21.md): explicit polygon/mode/reference arguments, temporary record storage, original-x86 routing comparisons and the next lighting/matrix failure.

- [Post-intro action-error requester — 2026-09-15](entries/post-intro-requester-2026-09-15.md): invisible modal diagnosis, recovered error text/OK routing, SDL Debug/ASan interaction proof and the exposed camera-87 transition.

- [Scene projection and actor recovery — 2026-09-15](entries/actor-cues-and-projection-2026-09-15.md): projected cues, original-x86 arithmetic checks, pose/matrix/event repairs, corrected child namespaces and the next geometry failure.

- [Runtime/documentation audit — 2026-09-14](entries/runtime-audit-2026-09-14.md): reverified baseline, generator drift, debug wrapper failure, actor visibility, action-384 repro, and task ownership.

- [Runtime crash fixes](entries/runtime-crash-fixes.md): call stacks, symptoms, fixes, and the next crash exposed by each repair.
- [Generated code repairs](entries/generated-code-repairs.md): source transformations in `E2Recomp/tools/GenerateRecon.js` that keep regenerated C aligned with hand fixes.
- [Linux portability](entries/linux-portability.md): CMake, VS Code, data symlink, 32-bit toolchain, and Win32 compatibility work.
- [Reverse engineering workflow](entries/reverse-engineering-workflow.md): Ghidra project/script usage and notes for validating reconstructed functions against the original executable.

## Conventions

Use [journal.template.md](../templates/journal.template.md) for new journal entries. Add a new entry file under `entries/` when a topic grows beyond one ownership area.
