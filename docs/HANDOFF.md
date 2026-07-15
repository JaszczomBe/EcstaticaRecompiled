# EcstaticaRecompiled Handoff

This is the root documentation anchor for future context windows. Start here, then follow the active implementation or plan links below.

## Current Objective

Run the decompiled Ecstatica II reconstructed runtime on Linux using CMake and Clang, with development driven by repeatable builds, GDB/Ghidra evidence, and journaled exploratory fixes.

## Active Implementation

- [Run Reconstructed E2 On Linux](implementations/linux-e2-reconstructed-runtime/linux-e2-reconstructed-runtime.md)
- Current recommended step: [Resolve Post Main Loop Config Open Crash](implementations/linux-e2-reconstructed-runtime/steps/step-06/step-06-resolve-post-main-loop-config-open-crash.md) - continue only with a tightly scoped verification/frontier pass.
- Current runtime journal: [Runtime crash fixes](journal/entries/runtime-crash-fixes.md)

## Journal

- [Journal index](journal/journal.md)
- [Runtime crash fixes](journal/entries/runtime-crash-fixes.md)
- [Generated code repairs](journal/entries/generated-code-repairs.md)
- [Linux portability](journal/entries/linux-portability.md)
- [Reverse engineering workflow](journal/entries/reverse-engineering-workflow.md)

## Plans

- [Runtime Milestones](plans/runtime-milestones.md)

## Templates

- [Implementation workflow](templates/implementation-workflow.template.md)
- [Implementation plan template](templates/implementation-workflow.template/plan.template.md)
- [Implementation step template](templates/implementation-workflow.template/step.template.md)
- [Implementation task template](templates/implementation-workflow.template/task.template.md)
- [Journal template](templates/journal.template.md)
- [Commit message template](templates/commit-message.template.md)

## Current Runtime State

- Branch: `linux-e2-reconstructed-runtime`
- Current recommended step: [Resolve Post Main Loop Config Open Crash](implementations/linux-e2-reconstructed-runtime/steps/step-06/step-06-resolve-post-main-loop-config-open-crash.md) - verify the latest `FUN_00453920` no-op and record the next ASan frontier, without broad new investigation.
- Data path: `/home/rgrabowski/Games/Ecstatica2/`
- Build data symlink should resolve under build directories as `Ecstatica2`.
- Debug build command: `cmake --build --preset linux-clang32-debug`
- ASan build command: `cmake --build build/linux-clang32-asan`
- Run command from debug build: `./e2recomp --run-recon`
- Latest proven milestone: startup advances past the old post-main-loop `"e_config"` and CDPath/file-open blockers into menu/framebuffer and quick-save code paths under ASan.
- Latest verified ASan frontier before the final stop: `FUN_0045fd2c` writing through an invalid destination from `FUN_00453920`.
- Latest code change after that frontier: `FUN_00453920` is reduced to a hosted no-op and mirrored in `E2Recomp/tools/GenerateRecon.js`.
- Verification after the `FUN_00453920` no-op: `node --check E2Recomp/tools/GenerateRecon.js`, `cmake --build build/linux-clang32-debug`, and `cmake --build build/linux-clang32-asan` pass. ASan was not rerun after this final no-op by explicit stop request.

## Blank Context Startup Protocol

When a fresh context is given only this instruction:

```text
Read /home/rgrabowski/Work/EcstaticaRecompiled/docs/HANDOFF.md
```

it must read this file and follow the protocol below before making code changes.

First response requirements:

1. State the active next implementation step.
2. Summarize its scope in 3 bullets or fewer.
3. Summarize its acceptance criteria in 3 bullets or fewer.
4. State whether it is ready to proceed or needs the user to choose from task options.

Before substantial investigation or implementation, a fresh context must do one of these:

1. Outline the next implementation step it intends to execute, including scope, acceptance criteria, and verification.
2. Provide a short list of next task options for the user to choose from.

The user should confirm the scope before substantial investigation or implementation continues. If the user has already explicitly chosen a step in the current conversation, proceed with that step and restate the chosen scope briefly.

## Operating Rules

1. Read the active implementation before coding.
2. Read the relevant journal entries before changing reconstructed code.
3. Mirror hand fixes in `E2Recomp/tools/GenerateRecon.js` when they affect generated C.
4. Build and run after each runtime fix when feasible.
5. Add or update a journal entry when a fix advances the crash frontier.
6. Respect the active step usage budget: no more than 5% of weekly usage per day unless the user explicitly approves continuing.
7. Do not commit or push unless explicitly asked.

## Documentation Edit Policy

Most implementation and journal files are mutable working documents. Constant anchor files require explicit user permission before edits, and every proposed edit must include a valid reason.

Constant anchor files:

1. `docs/HANDOFF.md` - root context anchor for blank contexts.
2. `docs/templates/implementation-workflow.template.md` - workflow rules for implementation documentation.
3. `docs/templates/implementation-workflow.template/plan.template.md` - implementation plan shape.
4. `docs/templates/implementation-workflow.template/step.template.md` - implementation step shape.
5. `docs/templates/implementation-workflow.template/task.template.md` - implementation task shape.
6. `docs/templates/journal.template.md` - journal entry conventions.
7. `docs/templates/commit-message.template.md` - commit message convention.
8. `docs/plans/runtime-milestones.md` - current milestone ordering and project direction.

Mutable working files:

1. `docs/implementations/**`
2. `docs/journal/journal.md`
3. `docs/journal/entries/**`
4. `docs/style/**`
