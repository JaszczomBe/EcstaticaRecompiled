# Code formatting and style

<!-- docs-tree:parent -->
[Project README](../../README.md) · [Parent: Project documentation](../README.md)
<!-- /docs-tree:parent -->

Keep edits focused and follow the surrounding file's established style. The
repository has no enforced global formatter configuration; do not introduce
repository-wide formatting churn while repairing behavior.

| Code | Editing convention |
| --- | --- |
| Reconstructed C, headers and globals | Preserve generator output and original-shaped control flow; mirror runtime changes in the generator |
| Native/compatibility C | Follow existing four-space indentation and explicit ownership/width handling |
| C++ support libraries | Follow the surrounding two-space style and existing C ABI boundaries |
| Python tools | Four-space indentation, explicit argv lists for subprocesses, bounded execution and structured output |
| JavaScript generator | Preserve existing two-space style and narrow anchored transformations |
| JSON configuration | Two-space indentation, valid JSON and one ordinary VS Code launch entry |
| Markdown | Descriptive headings, blank lines around paragraphs/lists, relative repository links and tree navigation |

Keep host/UI behavior outside recovered game logic. Name fields and commands for
their actual meaning; distinguish update, presentation and replay coordinates.
Avoid speculative initialization of unresolved register values. Use precise
integer widths where original layout/arithmetic requires them.

## Verify formatting and generation

```sh
git diff --check
node --check E2Recomp/tools/GenerateRecon.js
python3 scripts/check-docs-tree.py
```

When the generator changes, regenerate and verify only the intended artifacts
change. Stop unrelated generated churn and repair the generator anchor. Do not
format vendored SDL or other upstream dependencies as part of project changes.
