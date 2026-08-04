#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_root="${E2R_CONTROL_MATRIX_TMP:-/tmp/e2-step03-control-matrix}"
skip_build="${E2R_SKIP_BUILD:-0}"
run_asan="${E2R_CONTROL_MATRIX_ASAN:-1}"

debug_exe="${E2R_CONTROL_MATRIX_DEBUG_EXE:-build/linux-clang32-debug/e2recomp}"
asan_exe="${E2R_CONTROL_MATRIX_ASAN_EXE:-build/linux-clang32-asan/e2recomp}"

keys=(up down left right)
vkeys=(0x26 0x28 0x25 0x27)
moves=(
    "move=\\[1,0,0,0,0,0,0,0,0\\]"
    "move=\\[0,0,0,0,0,0,0,1,0\\]"
    "move=\\[0,0,0,1,0,0,0,0,0\\]"
    "move=\\[0,0,0,0,1,0,0,0,0\\]"
)
dirs=(
    "_DAT_00479e78=0"
    "_DAT_00479e78=7"
    "_DAT_00479e78=3"
    "_DAT_00479e78=4"
)

cd "${repo_root}"

run_capture() {
    local log_file="$1"
    shift

    echo "+ $*"
    set +e
    SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}" \
    E2R_STARTUP_LOGO_DELAY_MS="${E2R_STARTUP_LOGO_DELAY_MS:-0}" \
        "$@" >"${log_file}" 2>&1
    local status=$?
    set -e

    if [[ ${status} -ne 0 ]]; then
        echo "Command failed with exit ${status}: $*" >&2
        echo "--- ${log_file} tail ---" >&2
        tail -n 100 "${log_file}" >&2 || true
        exit "${status}"
    fi
}

require_log() {
    local log_file="$1"
    local pattern="$2"
    local description="$3"

    if ! grep -Eq "${pattern}" "${log_file}"; then
        echo "Missing expected evidence (${description}) in ${log_file}" >&2
        echo "--- ${log_file} tail ---" >&2
        tail -n 140 "${log_file}" >&2 || true
        exit 1
    fi
}

reject_log() {
    local log_file="$1"
    local pattern="$2"
    local description="$3"

    if grep -Eq "${pattern}" "${log_file}"; then
        echo "Unexpected evidence (${description}) in ${log_file}" >&2
        echo "--- ${log_file} tail ---" >&2
        tail -n 140 "${log_file}" >&2 || true
        exit 1
    fi
}

run_matrix_row() {
    local label="$1"
    local exe="$2"
    local key="$3"
    local vkey="$4"
    local move_pattern="$5"
    local dir_pattern="$6"
    local log_file="${tmp_root}-${label}-${key}.log"
    local dump_prefix="${tmp_root}-${label}-${key}"

    run_capture "${log_file}" \
        "${exe}" \
        --inject-key-sequence-gameplay-surfaces \
        "${dump_prefix}" "space,${key}" 6 10000 20 1

    require_log "${log_file}" "gameplay-control wait satisfied" "${label} ${key} control-ready gate"
    require_log "${log_file}" "last_key=${vkey}" "${label} ${key} key dispatch"
    require_log "${log_file}" "${move_pattern}" "${label} ${key} movement latch"
    require_log "${log_file}" "${dir_pattern}" "${label} ${key} pending direction"
    require_log "${log_file}" "_DAT_00643650=0" "${label} ${key} requester state clear"
    require_log "${log_file}" "_DAT_0073cc3c=0x[1-9a-fA-F][0-9a-fA-F]+" "${label} ${key} scene pointer"
    require_log "${log_file}" "surface 3 nonblank=1" "${label} ${key} nonblank gameplay surface"
    if [[ "${label}" == "asan" ]]; then
        reject_log "${log_file}" "ERROR: AddressSanitizer|SUMMARY: AddressSanitizer" "${label} ${key} sanitizer report"
    fi
    echo "control matrix ${label}/${key}: passed (${log_file})"
}

echo "Repository: ${repo_root}"
echo "Temporary prefix: ${tmp_root}"

node --check E2Recomp/tools/GenerateRecon.js

if [[ "${skip_build}" != "1" ]]; then
    cmake --build --preset linux-clang32-debug
    if [[ "${run_asan}" != "0" ]]; then
        cmake --build build/linux-clang32-asan
    fi
fi

for i in "${!keys[@]}"; do
    run_matrix_row "debug" "${debug_exe}" "${keys[$i]}" "${vkeys[$i]}" "${moves[$i]}" "${dirs[$i]}"
done

if [[ "${run_asan}" != "0" ]]; then
    for i in "${!keys[@]}"; do
        run_matrix_row "asan" "${asan_exe}" "${keys[$i]}" "${vkeys[$i]}" "${moves[$i]}" "${dirs[$i]}"
    done
fi

echo "Control matrix passed."
