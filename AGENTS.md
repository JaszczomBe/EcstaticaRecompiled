# Agent working instructions

<!-- docs-tree:parent -->
[Project README](README.md)
<!-- /docs-tree:parent -->

Start at [README.md](README.md), the central project entry point. Follow its
documentation tree to the current capabilities, handoff, active implementation,
current step/task and relevant journal evidence before changing runtime behavior.

- Preserve unrelated staged and unstaged changes. Do not commit or push unless requested.
- Recover behavior from original disassembly/Ghidra and bounded original-code comparisons.
- Mirror reconstructed C repairs in `E2Recomp/tools/GenerateRecon.js`; verify generated parity without unrelated churn.
- Use the single **Ecstatica Recompiled** VS Code launch for normal human gameplay investigation. Agent probes retain explicit bounded input and recording policies.
- Follow [code formatting and style](docs/style/README.md) and [contribution workflow](CONTRIBUTING.md).
- Keep new Markdown connected to the README tree. Follow [documentation maintenance](docs/documentation.md), run `python3 scripts/check-docs-tree.py --update`, and check it again without `--update`.
- Record new acceptance evidence and limits in the owning implementation and journal. Historical probe success is not current gameplay acceptance.

Continue authorized work without another confirmation. The user's current task
takes precedence over repository workflow guidelines.
