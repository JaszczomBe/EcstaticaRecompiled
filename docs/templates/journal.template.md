# Journal Templates And Conventions

## Handling Rules

- Keep [../HANDOFF.md](../HANDOFF.md) as the root context anchor, not a timeline.
- Add each entry to the journal entry subfile that owns the investigation target or fix target.
- Keep entries concise, but include enough evidence to reproduce the reasoning later.
- Record the next exposed crash or risk when a fix only moves the runtime forward.
- Prefer function names, source paths, original addresses, and exact build/run commands over broad descriptions.
- Split a new subfile when a topic starts to mix unrelated ownership areas.

## Runtime Crash Fix

```markdown
## YYYY-MM-DD - Short Title

Area: subsystem or function range

Symptom: observed crash/build/runtime behavior

Evidence: call stack, log line, address, or Ghidra finding

Change: what changed and where

Result: build/run outcome and the next exposed issue

Regression Risk: what may need revisiting
```

## Generated Code Repair

```markdown
## YYYY-MM-DD - Transformation Name

Target Function(s):

Generator Pattern:

Generated C Effect:

Reason:

Validation:
```

## Linux Portability

```markdown
## YYYY-MM-DD - Change

Area:

Problem:

Change:

Developer Workflow Impact:

Validation:
```

## Reverse Engineering Investigation

```markdown
## YYYY-MM-DD - Function Or Address Range

Question:

Original Address(es):

Reconstructed Function(s):

Ghidra Evidence:

Decision:

Follow-up:
```
