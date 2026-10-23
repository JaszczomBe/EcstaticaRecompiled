# Startup Skip Feasibility — 2026-10-20

<!-- docs-tree:parent -->
[Project README](../../../README.md) · [Parent: Project Journal](../journal.md)
<!-- /docs-tree:parent -->

The user requests shorter F5 startup and an assessment of whether an environment/command option can skip the logos and intros without disturbing recovered gameplay initialization. This continuation audits the existing paths, measures them and enables only the existing tested logo-delay setting. It does not add a full-intro shortcut.

## Available Now

`.vscode/launch.json`, **Ecstatica Recompiled**, now adds `E2R_STARTUP_LOGO_DELAY_MS=0`. `E2R_WaitStartupLogo` already supports this value; it removes only its `Sleep` loop. `FUN_0041007c` still runs the original logo loaders, palette/resource setup and game startup. Two logo waits are unconditional; the first publisher logo is conditional. The normal default is 5,000 ms per displayed logo. Brief loading/presentation can remain visible.

The existing manual horseback Space skip calls `E2R_RequestIntroSkip`, which validates the loaded horse/action state and dispatches original `dav:skipsc`. That script starts `Start_sc` and the guard companion `St_gobsc`, performs cleanup/preload work and enables terrain population through opcode 0x6a. This original route is the appropriate basis for future automatic skipping. Calling only `Start_sc` already caused the earlier missing-population bug.

There is currently no supported normal-launch `--skip-intro`/`E2R_SKIP_INTRO` option. `--run-recon` does not parse additional startup flags. Existing injection/scene-capture command modes are diagnostics with capture timeouts/process exits; they are unsuitable as an everyday F5 startup option.

## Measured Evidence

Temporary timing probes under `/tmp/e2-probe-startup-*.py` use the normal entry, observe the first horseback action, tap/release actual SDL Space, observe the restrained pedestal phase and wait for the original script release. Production runtime code is unchanged.

| Check | Horse ready | Joe released | Evidence prefix |
| --- | ---: | ---: | --- |
| Debug, existing 5,000 ms logo setting | 11.95 s | 28.43 s | `/tmp/e2-startup-current-debug` |
| Debug, zero logo wait | 0.84 s | 17.33 s | `/tmp/e2-startup-no-logos-debug` |
| ASan, zero logo wait | 1.33 s | 17.85 s | `/tmp/e2-startup-no-logos-asan` |

Times are measured from the GDB probe's run invocation and are not a VS Code build/startup benchmark. The Debug comparison saves approximately 11.1 seconds in this run. The zero-wait routes retain Joe at `9988,3328,-17408`, both original guards, open script population gate, live generated actors 77/78/79, zero modal/wait and cleared arrow/modifier state. No ASan report occurs. This establishes the wait-only setting's bounded safety; different wall-clock/RNG timing is not a promise of identical future NPC trajectories.

## Remaining Intros And Recommended Implementation

The remaining measured delay is roughly **16.4 seconds from the restrained pedestal checkpoint to release**. `E2R_RequestIntroSkip` explicitly treats `Start_sc` as wait-only and clears/ignores Space there. This sequence runs actor actions, release/placement events, scene ownership and script opcode 0x75 (`DAT_0047a76c=0` plus HUD update). Forcing the wait to zero or jumping Joe to a final position would omit those operations and is not a supported shortcut.

A small future opt-in environment option can automatically invoke the existing horseback skip when its real actor/action/resource preconditions hold, then stop doing anything after that one successful transition. Reuse the same validated handler and original `dav:skipsc`; avoid repeated/timed Space injections that could later reach gameplay/menu input. This removes the manual tap and the horseback portion, but still leaves the pedestal initialization.

A fuller developer fast-start is feasible as a separate recovery/verification slice: retain and execute the pedestal event sequence while accelerating only its startup simulation/presentation waits, then restore normal pacing before player input. The game clock is shared (`0x41cf5c → 0x4620db → GetTickCount`) and actions/population also use elapsed ticks, so a global speed multiplier or single huge delta is not established safe. Validate event ordering, Joe's final pose/motion/action ownership, guards, population enablement, clear input state, camera traversal and sustained Debug/ASan updates against the normal route. No such acceleration option is implemented or accepted here. A save/checkpoint shortcut is also not currently supported.

Original loaded records including `dav:skiph` were inspected read-only in `/tmp/e2-startup-code-audit-startup-codes.json`. The name alone does not establish a safe pedestal skip; no alternate script was invoked or selected on that assumption.

## Worktree

Only the launch setting and documentation change in this continuation. No reconstructed/generator source changes, commits or index writes were made. The starting index patch is preserved at `/tmp/e2-startup-launch-before-index.patch`; existing user work remains intact. To restore the visible logo waits, remove the setting or set it to `5000`.
