# Project Journal

This journal is the historical project memory for exploratory Linux runtime work. Keep it as an index and place detailed entries under [entries/](entries/).

## Entries

- [Post-pedestal deactivation callback — 2026-10-22](entries/post-pedestal-deactivation-callback-2026-10-22.md): exact replay reproduces the new fatal-script stack; original callback code/actor/node ownership is restored, compatible replay passes the failure boundary, and natural Debug/ASan intros plus 60-second idle observations pass. Debug's broader steering/floor-return check remains failing.

- [Natural intro attachment detach — 2026-10-22](entries/natural-intro-attachment-detach-2026-10-22.md): reproduces the reported no-input `FUN_0042db74` crash, recovers its event node/attached-actor contract from original instructions and verifies natural Debug intro completion plus idle survival; a separate script-deactivation fault retains full ASan's unaccepted status.

- [Replay NPC inputs and crash boundary recovery — 2026-10-22](entries/replay-npc-input-and-crash-boundary-recovery-2026-10-22.md): recovers original NPC target/angle/turn inputs and publishes changed clocks before game control resumes; a new Debug crash capture reaches the same helper across fresh replays and a debugger pause, while Debug/ASan clean menu routes pass and the old human capture remains explicitly divergent.

- [Human pedestal crash replay test — 2026-10-22](entries/pedestal-crash-replay-test-2026-10-22.md): preserves the actual crashed recording and exact executable; three fresh replays match checkpoints 1–16 but diverge in clock/cursor service ordering before the reported crash, so gameplay crash reproduction remains unaccepted.

- [Gameplay CSV recorder and replay prototype — 2026-10-22](entries/gameplay-csv-replay-prototype-2026-10-22.md): adds isolated capture/replay, shared artifact ownership, clock compression and strict checkpoints; Debug intro/menu replays and recovery pass, while movement and ASan replay fidelity remain explicitly unaccepted.

- [Logger cleanup and bounded session maintenance — 2026-10-21](entries/logger-cleanup-and-session-maintenance-2026-10-21.md): removes unused foreign integrations while preserving RT pooling, macros/masks, native stacks and filesystem wrappers; adds periodic retention with active-session leases and verifies critical-event priority and severity bypass.

- [Input log transitions and missing-sound severity — 2026-10-21](entries/input-log-transitions-and-missing-sound-severity-2026-10-21.md): gives input and missing sound separate Debug/Trace tags, logs key press/held/release changes and keeps protocol dumps opt-in; dispatcher checks prove repeated keys still reach the legacy handler.

- [Logger console severity and sessions — 2026-10-21](entries/logger-console-severity-and-sessions-2026-10-21.md): replaces legacy console formatting with the C++ logger, enables severity colors and per-run session directories, and drains controlled probe exits; Debug/ASan logging checks, native adapter launches and baselines pass.

- [Native F5 file-open heap corruption — 2026-10-21](entries/native-f5-file-open-heap-corruption-2026-10-21.md): reproduces the real desktop heap abort, catches its writer with a hardware watchpoint, restores the original CRT helper's second output destination and verifies native launch through the installed VS Code debug adapter.

- [Logger developer workflow — 2026-10-21](entries/logger-developer-workflow-2026-10-21.md): integrates automatic file logging with the selected-target F5 workflow, shared Debug/ASan runtime options, discovered C++ multilib support and complete variadic diagnostics; records launch checks, passing baselines and the remaining ASan traversal limit.

- [Workshop initialization and actor visibility — 2026-10-20](entries/workshop-initialization-and-actor-visibility-2026-10-20.md): reproduces and repairs the camera-350 object durability crash, restores visibility-query coordinates, distinguishes object cylinders and audits the unchanged original population cap; Debug/ASan view activation and populated courtyard returns pass.

- [Blacksmith sword activation — 2026-10-20](entries/blacksmith-sword-activation-2026-10-20.md): restores original placement caching, loose-archive visibility indexing and actor/action handoffs; sword 3717 activates and projects in Debug/ASan, with pickup and manual workshop re-entry still open.

- [Blacksmith sword location — 2026-10-20](entries/blacksmith-sword-location-2026-10-20.md): matches the user's camera-347 screenshots/F12 packet to original scene 1909 and actor 3717; selects a precise activation/presentation target while keeping loaded state and pickup unproven.

- [Startup skip feasibility — 2026-10-20](entries/startup-skip-feasibility-2026-10-20.md): enables the existing zero-logo-wait option in F5 after Debug/ASan readiness checks; distinguishes automatic horseback skipping from the required pedestal event sequence and records measured startup savings.

- [Stables node hit-query inputs — 2026-10-20](entries/stables-node-hit-query-2026-10-20.md): repairs the reported stable crash at the legacy polar helper and the adjacent lost facing coordinate; original-code filter/contact comparisons pass normally/ASan, with exact stable re-entry kept separate from bounded runtime regressions.

- [NPC endpoint and reverse-chain poses — 2026-10-20](entries/npc-pose-chain-recovery-2026-10-20.md): recovers original endpoint/IK/attachment inputs, inverse-sine initialization and event pose ownership; populated early-Space traversal and sustained NPC activity pass within the recorded route limits.

- [Early intro skip and population — 2026-10-20](entries/early-intro-skip-population-2026-10-20.md): reproduces the F5-only pedestal pair after early Space, restores original skip-script population initialization, and records the exposed NPC IK pose-event failure.

- [Direction freeze and modifier release — 2026-10-20](entries/direction-modifier-release-2026-10-20.md): reproduces frozen Up+Left/YROT after stale Shift/Alt release flags, repairs the compatibility bridge and records the user's no-freeze confirmation; a later native Debug NPC pose-event crash remains open.

- [General population and direction audit — 2026-10-19](entries/general-population-and-direction-audit-2026-10-19.md): enables original generic population in F5 after spawn/pose/queued-action recovery; populated Debug/ASan traversal passes, while the new physical direction/arrow report remains unresolved.

- [Intro skip FAN ownership — 2026-10-19](entries/intro-skip-fan-ownership-2026-10-19.md): repairs nested FAN/action selection, scene argument ownership and out-of-actor finalizer writes after the reported Space-skip crash; exact runtime reproduction remains unconfirmed.

- [Pedestal guard activation — 2026-10-19](entries/pedestal-guard-activation-2026-10-19.md): corrects the terrain-population overclaim; identifies original `St_gobsc` tracks `gob3`/`gob3b`, restores their cylinder activation and records remaining combat/model/sanitizer limits.

- [Scene population recovery — 2026-10-19](entries/scene-population-recovery-2026-10-19.md): restores bounded original actor loading, wandering inputs and lifetime ownership; keeps F5 deferral while attachment-event inputs and population traversal/interaction remain open.

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
