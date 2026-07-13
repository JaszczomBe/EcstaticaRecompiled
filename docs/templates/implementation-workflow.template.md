# Implementation Workflow

This document defines how to create and maintain markdown trees for complex implementation work in this repository.

## Repository Layout

```text
docs/
  HANDOFF.md
  templates/
    implementation-workflow.template.md
    implementation-workflow.template/
      plan.template.md
      step.template.md
      task.template.md
    journal.template.md
    commit-message.template.md
  journal/
    journal.md
    entries/
      <journal-files>.md
  plans/
    <target-design-or-roadmap>.md
  implementations/
    <implementation-name>/
      <implementation-name>.md
      steps/
        step-01/
          <step-file>.md
          tasks/
            <task-files>.md
      archive/
        completed-tasks/
        retired-steps/
  style/
```

## Document Roles

`docs/HANDOFF.md` is the only root anchor future context windows should need.

`docs/plans/*.md` contains target direction, milestone ordering, and durable project strategy.

`docs/implementations/<name>/<name>.md` contains the rollout truth for active work.

`steps/step-NN/*.md` contains a functional intermediate state that can be completed and verified.

Steps should be scoped so they can preferably be completed in one context window. If a step grows beyond that, split it before implementation continues.

`tasks/*.md` contains narrow execution units for one or a few context windows.

`docs/journal/journal.md` indexes historical evidence, while `docs/journal/entries/*.md` records crash evidence, repairs, and regressions discovered during implementation.

`docs/style/` is reserved for future language-specific coding style notes.

## Creation Rules

Before creating a new implementation tree:

1. Read [../HANDOFF.md](../HANDOFF.md).
2. Search `docs/implementations/` for an existing matching effort.
3. Search `docs/plans/` for related target direction.
4. Reuse the closest existing implementation unless the user explicitly asks for a separate branch of work.
5. Choose the smallest tree that preserves clarity: plan only, plan plus step, or plan plus step plus tasks.
6. Use companion templates from `docs/templates/implementation-workflow.template/` when creating implementation plans, steps, or tasks.

## Update Rules

1. Update `docs/HANDOFF.md` when the active implementation, next recommended step, or latest known crash changes.
2. Update the project journal whenever a runtime fix advances the crash frontier.
3. Update the parent implementation when a step is completed, retired, or materially re-scoped.
4. Keep templates generic; put project-specific state in plans, implementations, or journals.
5. A fresh context should outline the intended next step or offer task choices before starting substantial work.

## Documentation Edit Policy

Documentation files are either constant anchors or mutable working documents.

Constant anchors require explicit user permission before edits. The proposed edit must state a valid reason, such as correcting a stale root link, changing an approved workflow rule, or updating a user-approved milestone direction.

Constant anchor files:

1. `docs/HANDOFF.md`
2. `docs/templates/implementation-workflow.template.md`
3. `docs/templates/implementation-workflow.template/plan.template.md`
4. `docs/templates/implementation-workflow.template/step.template.md`
5. `docs/templates/implementation-workflow.template/task.template.md`
6. `docs/templates/journal.template.md`
7. `docs/templates/commit-message.template.md`
8. `docs/plans/runtime-milestones.md`

Mutable working files can be edited as needed while executing the active implementation:

1. `docs/implementations/**`
2. `docs/journal/journal.md`
3. `docs/journal/entries/**`
4. `docs/style/**`
