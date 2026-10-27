# Tower actor eviction crash — 2026-10-27

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

Owner: [Step 09 population and interaction](../../implementations/playable-sdl-runtime/steps/step-09/tasks/task-09-recover-scene-population-and-interaction.md).
Preceding work: [enemy-play crash and dropped potion](enemy-play-crash-and-dropped-potion-2026-10-27.md).

## Human evidence and reproduction

The user accepts the preceding repairs and reports a longer journey ending in
a crash at the top of the tower. F5 session **20261027_214425_922** pins Debug
executable `e9ff01f146f65d3521b1d55fb3eb7776954af5141a86c642f97d86898209784e`.
The recording and inspection are complete. Its receipt reports process exit
**0**, without a signal; the runtime log nevertheless contains the fatal game
requester and stack. A clean OS exit is not successful gameplay acceptance.

The inactive session and matching executable are frozen under ignored
`.tmp/tower-crash/human-214425/`. All diagnostics below are bounded, use isolated
output and disable recording. Existing staged and unstaged work is preserved;
nothing is staged, committed or pushed.

`original-replay-01` reproduces the reported stack while loading actor
**264/key3** through the ordinary population scheduler. Its node allocation
exhausts the original **4000-slot** pool and calls `FUN_0045311c` to evict an old
inactive actor. The selected actor is **3030/trelim10**, pointer **0xaa79c4**,
last used at tick **8249**, current tick **49605**, replay sequence
**5174587075**. Selection is valid. `FUN_0045282c` then substitutes an unresolved
ECX value for that actor: `psVar4` points at host `e2r_memory_map_cache_mutex`.
Its incorrect identity triggers `FUN_00414e5c` and the unreadable-message fatal
requester. The original selector and pool size are retained.

## Original-backed repair

Original **0x452835** retains the actor in ECX across name formatting and recursive
calls. The recovered C now explicitly retains the input actor, checks the five
original rejection conditions, removes attached actors using the original
ownership relationships, unlinks the loaded-actor list, clears its name-table
slot and releases its nodes, vertices and polygons. Original **0x4528e6** recurses
on the actor attached to a bone; **0x452909** recurses on the owning actor of the
attachment bone. The old C incorrectly passed the actor being removed in both
places. Fatal presentation receives the original message and formatted actor
label as a real two-line list.

The comparison also exposes two errors in the existing root cleanup
`FUN_0043a800`: original **0x43a8eb → 0x453264** marks root **+2** as **0x8000**
and returns the root pointer in EAX. The old replacement marked **+4**, corrupting
the actor kind and leaving the root unavailable for reuse, and returned zero.
Both contracts are restored. Child nodes still receive their distinct original
free marker at **+4**. All repairs are mirrored in `GenerateRecon.js`.

## Verification and limits

`check-e2-actor-eviction.py` executes original removal, selection, cleanup and
node allocation instructions with bounded name/formatting/fatal interceptions.
Normal and ASan runs each pass **163 cases**, comparing full mapped pool/table
memory and return/EDX preservation. Cases include list positions, both attachment
directions together and separately, vertices/polygons, active and Joe-attached
protection, all five fatal conditions, and actual allocation from a completely
occupied node pool after eviction. Actor roots and child nodes occupy their
separate original pools. A failing comparison first exposes the wrong root free
field (`eviction-normal-03.log`); the expanded return comparison exposes the zero
return (`eviction-return-control-09.log`). Final checks are
`eviction-normal-10.log` and `eviction-asan-10.log`.

The new required **debug/asan.Original.ActorEviction** cases both pass through
the normal suite runner (`eviction-suite-13`, **2 PASS**, exit **0**). Three
affected catalogue/planning contracts pass; the catalogue now has **215** cases.
The existing ASan node-removal fixture passes **768** recursive child/polygon
cases. All four SDL/X11 Debug/ASan builds pass, all four generated artifacts match
independently (`parity-final-10`), and whitespace checks pass. Final source/binary
hashes are recorded in `final-identities.json`.

Final Debug replay `final-debug-replay-11` matches **1088 checkpoints**, reaches
the old failure, and observes actor 3030 removed from its name table, root flags
**7232 → 32768**, kind preserved at **7**. It then strictly diverges at sequence
**5174587078**: recorded requester state `DAT_0047a45e == 3014656`, repaired game
state **0**. The native replay exits **74**, rather than opening the fatal
requester. Checkpoints remain strict; this is deliberately not a complete replay
pass. A local observer mistakenly tries to inspect actor 264 after that exit and
raises a GDB memory error; it does not establish completed key loading.

Replay diagnostics select dummy SDL after startup identity validation and use
explicit binary compatibility mode for rebuilt images. They do not qualify the
desktop SDL backend. Preliminary Debug replays `fixed-debug-replay-02` and
`final-debug-replay-07` retain the same divergence and their source limits.
The obsolete ASan replay `final-asan-replay-08` is explicitly stopped to leave
CPU for the final-source attempt; no pass is claimed for it.

Final-source ASan replay `final-asan-replay-12` matches **887 checkpoints**, then
strictly diverges earlier in RNG fallback state at sequence **3602669250**:
expected **2679179113**, actual **1389909486**. It exits **74** without a sanitizer
report and never reaches the tower eviction. This is a retained replay
qualification limit, not ASan tower acceptance; the ASan original-code eviction
and pool-pressure comparisons do pass.

The strict replay cannot follow new gameplay beyond a recording that entered a
fatal requester. Full key interaction, further tower traversal, a new human F5
retest and the complete gameplay suite remain unqualified by these checks.

```sh
python3 scripts/check-e2-actor-eviction.py /path/to/E2WIN95.EXE
python3 scripts/check-e2-actor-eviction.py /path/to/E2WIN95.EXE --asan
python3 scripts/run-e2-suite.py --configurations debug asan --block checks --filter '*.Original.ActorEviction'
```
