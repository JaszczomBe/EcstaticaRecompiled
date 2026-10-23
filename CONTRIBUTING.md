# Contributing

<!-- docs-tree:parent -->
[Project README](README.md)
<!-- /docs-tree:parent -->

Use the root README to find the active implementation before starting work.
Read the current task and its acceptance limits, inspect `git status --short`,
and preserve existing changes. Discuss technical findings with concrete evidence
and follow the [code of conduct](CODE_OF_CONDUCT.md).

## Runtime changes

Keep host services in the compatibility/backend layers. Recover game behavior
from original instructions and explicit data ownership; avoid guessed guards or
forced final state. Prove the smallest repair, mirror it in the generator, and
verify the reconstructed diff remains scoped. Follow the
[handoff](docs/HANDOFF.md), [source workflow](E2Recomp/README.md) and
[formatting rules](docs/style/README.md).

## Validation and review

Build the affected configuration and run the relevant original-code fixtures,
runtime probes and regression checks. Keep timeouts, route names, binary identity,
observations and remaining limits with the result. The
[debugging guide](docs/debugging.md) explains replay and investigation artifacts.
Describe the concrete trigger, changed behavior and verification in reviews.
Do not treat a latch, sampled state, rendered frame or bounded survival as proof
of complete gameplay fidelity.

## Documentation

Update the owning implementation/task when its current state changes, add dated
evidence to the journal, and use the established templates. Add every new Markdown
file to the documentation tree and run its check. See
[documentation maintenance](docs/documentation.md). Commit and push only when
explicitly requested by the person directing the work.
