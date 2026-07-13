# Third-party tools

Ghidra is intentionally optional for normal compile/run work.

For headless decompilation exports, either install/unpack a Ghidra release and set:

```sh
export GHIDRA_HOME=/path/to/ghidra_VERSION_PUBLIC
```

or add the upstream source as a local submodule:

```sh
git submodule add --depth 1 https://github.com/NationalSecurityAgency/ghidra.git third_party/ghidra
git submodule update --init --depth 1 third_party/ghidra
```

The source submodule is large and still needs a Ghidra build before `analyzeHeadless`
is available. For day-to-day reverse engineering, a release distribution is usually
the quicker path.
