# Linux Portability

## Purpose

Track non-gameplay scaffolding needed to build and launch the reconstructed runtime on Linux with CMake, Clang, Ninja, and VS Code.

## Current Topics

- 32-bit Linux Clang preset and dependency notes.
- Automatic Ecstatica II data symlink under the CMake build tree.
- VS Code `tasks.json` and single F5 launch entry.
- Win32 compatibility stubs in `E2Recomp/platform`.
- Address-space mapping for legacy `0x00400000..0x00b00000` data/code expectations.

Use the Linux portability template in [journal.template.md](../../templates/journal.template.md) for new entries.
