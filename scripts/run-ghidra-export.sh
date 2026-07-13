#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

data_dir="${ECSTATICA2_DATA_DIR:-/home/rgrabowski/Games/Ecstatica2}"
input_exe="${GHIDRA_INPUT_EXE:-${data_dir}/E2WIN95.EXE}"
project_dir="${GHIDRA_PROJECT_DIR:-${repo_root}/ghidra_project}"
project_name="${GHIDRA_PROJECT_NAME:-E2Win95Project}"
out_dir="${GHIDRA_OUTPUT_DIR:-${repo_root}/E2Recomp}"

find_headless() {
    if [[ -n "${GHIDRA_ANALYZE_HEADLESS:-}" ]]; then
        printf '%s\n' "${GHIDRA_ANALYZE_HEADLESS}"
        return
    fi

    if [[ -n "${GHIDRA_HOME:-}" && -x "${GHIDRA_HOME}/support/analyzeHeadless" ]]; then
        printf '%s\n' "${GHIDRA_HOME}/support/analyzeHeadless"
        return
    fi

    local candidate
    for candidate in \
        "${repo_root}"/third_party/ghidra/support/analyzeHeadless \
        "${repo_root}"/third_party/ghidra/build/dist/ghidra_*_PUBLIC/support/analyzeHeadless \
        "${repo_root}"/third_party/ghidra/Ghidra/RuntimeScripts/Linux/support/analyzeHeadless
    do
        if [[ -x "${candidate}" ]]; then
            printf '%s\n' "${candidate}"
            return
        fi
    done

    if command -v analyzeHeadless >/dev/null 2>&1; then
        command -v analyzeHeadless
        return
    fi

    return 1
}

if [[ ! -f "${input_exe}" ]]; then
    echo "Missing Ghidra input executable: ${input_exe}" >&2
    echo "Set ECSTATICA2_DATA_DIR or GHIDRA_INPUT_EXE." >&2
    exit 1
fi

headless="$(find_headless || true)"
if [[ -z "${headless}" ]]; then
    cat >&2 <<EOF
Could not find Ghidra analyzeHeadless.

Use one of:
  export GHIDRA_HOME=/path/to/ghidra_RELEASE_PUBLIC
  export GHIDRA_ANALYZE_HEADLESS=/path/to/analyzeHeadless
  git submodule add --depth 1 https://github.com/NationalSecurityAgency/ghidra.git third_party/ghidra

If using the source submodule, build Ghidra first; the release distribution is faster for headless export.
EOF
    exit 1
fi

mkdir -p "${project_dir}" "${out_dir}"

echo "Ghidra headless: ${headless}"
echo "Input executable: ${input_exe}"
echo "Project: ${project_dir}/${project_name}"
echo "Export output: ${out_dir}"

"${headless}" "${project_dir}" "${project_name}" \
    -import "${input_exe}" \
    -overwrite \
    -scriptPath "${repo_root}/ghidra_scripts" \
    -postScript ExportDecomp.java "${out_dir}"
