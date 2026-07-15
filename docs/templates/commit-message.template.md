# Commit Message Template

Use this format for commits prepared from this exploratory Linux runtime work:

```text
[Tag] High level description:
 - bullet point 1
 - bullet point 2
 - bullet point n
```

## Tags

Prefer one narrow lowercase tag.

1. `[Build]` - CMake, presets, VS Code tasks, toolchain setup.
2. `[Linux]` - Linux compatibility or platform shims.
3. `[Runtime]` - reconstructed runtime crash fixes.
4. `[Ghidra]` - reverse engineering workflow or recovered facts from original binary analysis.
5. `[Docs]` - documentation, plans, templates, or journals.

## Rules

1. Keep the first line high-level and imperative or descriptive.
2. Use bullets for concrete changes and verification.
3. Mention generated-code mirroring when a reconstructed C fix is also added to `GenerateRecon.js`.
4. Do not mix unrelated runtime fixes and documentation-only cleanup unless the user explicitly wants one combined commit.
