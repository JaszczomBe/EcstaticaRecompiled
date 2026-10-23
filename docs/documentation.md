# Documentation ownership and maintenance

<!-- docs-tree:parent -->
[Project README](../README.md) · [Parent: Project documentation](README.md)
<!-- /docs-tree:parent -->

`README.md` is the single central entry. Its branches lead to project docs,
reconstruction source/build guidance, dependencies, contribution rules and agent
instructions. Project Markdown has one navigation parent, with reciprocal links.
Cross-references are encouraged; they supplement the ownership tree.

## Sources of project truth

| Information | Owner |
| --- | --- |
| Entry and scope | Root README |
| Context recovery and durable runtime rules | Handoff |
| Current runtime acceptance, next step/task | Active runtime implementation and its linked step/task |
| Tool implementation state | Debugging tools implementation |
| Future direction | Milestone plan and planned implementation steps/tasks |
| Dated changes, evidence and regressions | Journal index and entries |
| Build/F5 commands | Build guide and actual VS Code configuration |
| Tools and schemas | Debugging and replay guides |
| Formatting and collaboration | Style guide, contribution guide and code of conduct |

Treat dated journal claims as historical evidence with their recorded limits.
Keep current commands in usage guides and current acceptance in implementation
documents. Do not create a competing source of changing runtime truth in the
handoff or an agent instruction file.

## Add or move a document

Choose its semantic branch: implementation to steps to tasks, journal to entries,
plans, templates, style or reference. Existing filenames remain stable so history
and cross-links keep working. `scripts/check-docs-tree.py` assigns each document's
navigation parent from that structure and refreshes missing child links and
breadcrumbs:

```sh
python3 scripts/check-docs-tree.py --update
python3 scripts/check-docs-tree.py
```

`python3 scripts/check-docs-tree-contracts.py` checks the maintenance tool itself,
including orphan/broken-link detection, cycles, repeatable updates and unchanged
upstream documents.

The check verifies root reachability, reciprocal project parent/child links,
cycles, and local project link targets. It includes Markdown in initialized
dependencies through the dependency documentation index. Upstream files remain
unchanged; their own link policies are maintained upstream. Build output, local
scratch/captures, `.git`, data and Python caches are outside the documentation tree.

For a new documentation category, add a descriptive index and extend the ownership
mapping in the checker. Do not edit the generated `docs-tree` navigation blocks
manually. Read source documents before changing state summaries; avoid inventing
missing historical evidence to satisfy a link check.

## Keep the tree useful

Update usage guides with user-facing workflow changes. Update the owning
implementation/task after verified behavior changes and add meaningful evidence
to the journal. Templates describe the same root/parent policy so new contexts
preserve it. Run the checker after documentation changes and initialize dependencies
before checking a complete checkout.
