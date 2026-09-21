# Project Journal

This journal is the historical project memory for exploratory Linux runtime work. Keep it as an index and place detailed entries under [entries/](entries/).

## Entries

- [Scene projection and actor recovery — 2026-09-15](entries/actor-cues-and-projection-2026-09-15.md): projected cues, original-x86 arithmetic checks, pose/matrix/event repairs, corrected child namespaces and the next geometry failure.

- [Runtime/documentation audit — 2026-09-14](entries/runtime-audit-2026-09-14.md): reverified baseline, generator drift, debug wrapper failure, actor visibility, action-384 repro, and task ownership.

- [Runtime crash fixes](entries/runtime-crash-fixes.md): call stacks, symptoms, fixes, and the next crash exposed by each repair.
- [Generated code repairs](entries/generated-code-repairs.md): source transformations in `E2Recomp/tools/GenerateRecon.js` that keep regenerated C aligned with hand fixes.
- [Linux portability](entries/linux-portability.md): CMake, VS Code, data symlink, 32-bit toolchain, and Win32 compatibility work.
- [Reverse engineering workflow](entries/reverse-engineering-workflow.md): Ghidra project/script usage and notes for validating reconstructed functions against the original executable.

## Conventions

Use [journal.template.md](../templates/journal.template.md) for new journal entries. Add a new entry file under `entries/` when a topic grows beyond one ownership area.
