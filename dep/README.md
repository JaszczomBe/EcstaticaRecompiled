# Dependencies

## SDL

SDL is the source-inspectable host backend dependency for `E2R_HOST_BACKEND=sdl`.
Initialize it before configuring the SDL backend:

```sh
git submodule update --init --recursive dep/SDL
```

Current pinned release: SDL 3.4.12 (`release-3.4.12`).

The default X11 backend does not require SDL.

## Ghidra

Ghidra is intentionally optional for normal compile/run work.

For headless decompilation exports, either install/unpack a Ghidra release and set:

```sh
export GHIDRA_HOME=/path/to/ghidra_VERSION_PUBLIC
```

or add the upstream source as a local submodule:

```sh
git submodule add --depth 1 https://github.com/NationalSecurityAgency/ghidra.git dep/ghidra
git submodule update --init --depth 1 dep/ghidra
```

The source submodule is large and still needs a Ghidra build before `analyzeHeadless`
is available. For day-to-day reverse engineering, a release distribution is usually
the quicker path.
