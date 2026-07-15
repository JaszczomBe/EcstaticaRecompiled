# Linux Portability

## Purpose

Track non-gameplay scaffolding needed to build and launch the reconstructed runtime on Linux with CMake, Clang, Ninja, and VS Code.

## Current Topics

- 32-bit Linux Clang preset and dependency notes.
- Automatic Ecstatica II data symlink under the CMake build tree.
- VS Code `tasks.json` and single F5 launch entry.
- Win32 compatibility stubs in `E2Recomp/platform`.
- Address-space mapping for legacy `0x00400000..0x00b00000` data/code expectations.

## Recent Entries

### 2026-07-14

1. Reframed Linux portability as the current proof platform rather than the final host abstraction.
2. Adopted a layered direction: reconstructed game logic remains original-shaped; Win32, DirectDraw, DirectSound, and CRT shims remain the game-facing compatibility surface; host-specific implementation should move behind a replaceable backend boundary.
3. Deferred SDL until the runtime has a stable loop, inspectable frame path, and clearer DirectDraw/DirectSound compatibility needs. SDL should back window, input, timing, presentation, and audio, not be called directly from reconstructed game logic.
4. Recorded the portability ladder as Linux/i386 first, backend-neutral host layer second, SDL-backed multi-platform work later, because fixed-address, 32-bit pointer, and legacy memory-layout assumptions still constrain true multi-platform support.

### 2026-07-13

1. The native Linux launcher now enters `E2RECOMP_DATA_DIR` before reconstructed startup, so relative game-data opens resolve through the build-tree `Ecstatica2` symlink.
2. `CreateFileA` now normalizes backslashes and resolves read-only file paths case-insensitively, matching the original Windows data-open behavior closely enough to open uppercase CD assets from lowercase reconstructed requests.
3. Top-level `CreateWindowExA` now dynamically loads X11 and maps a visible host window for the original Ecstatica II window request, with a headless HWND fallback when X11 is unavailable.
4. The Linux launcher now maps the legacy VGA-style `0xa0000..0x100000` address range used by startup blits.

Use the Linux portability template in [journal.template.md](../../templates/journal.template.md) for new entries.
