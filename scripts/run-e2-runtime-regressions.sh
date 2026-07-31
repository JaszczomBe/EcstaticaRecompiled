#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_root="${E2R_REGRESSION_TMP:-/tmp/e2-step11-regression}"
skip_build="${E2R_SKIP_BUILD:-0}"
runtime_diag="${E2R_RUNTIME_DIAG:-0}"

debug_prefix="${tmp_root}-debug"
asan_prefix="${tmp_root}-asan"
debug_log="${debug_prefix}.log"
asan_log="${asan_prefix}.log"
runtime_diag_pattern="scene pointer write:|frame stage:|actor loop:|actor update:|start-game stage:|requester state write:|menu request flag write:|current pointer shape:|actor load (enter|exit|invalid id):|current actor invalid at 4c164:"

cd "${repo_root}"

run_capture() {
    local log_file="$1"
    shift

    echo "+ $*"
    set +e
    E2R_STARTUP_LOGO_DELAY_MS="${E2R_STARTUP_LOGO_DELAY_MS:-0}" "$@" >"${log_file}" 2>&1
    local status=$?
    set -e

    if [[ ${status} -ne 0 ]]; then
        echo "Command failed with exit ${status}: $*" >&2
        echo "--- ${log_file} tail ---" >&2
        tail -n 80 "${log_file}" >&2 || true
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
        tail -n 120 "${log_file}" >&2 || true
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
        tail -n 120 "${log_file}" >&2 || true
        exit 1
    fi
}

echo "Repository: ${repo_root}"
echo "Temporary prefix: ${tmp_root}"

node --check E2Recomp/tools/GenerateRecon.js

if [[ "${skip_build}" != "1" ]]; then
    cmake --build --preset linux-clang32-debug
    cmake --build --preset linux-clang32-asan
fi

run_capture "${debug_log}" \
    build/linux-clang32-debug/e2recomp \
    --inject-key-sequence-gameplay-surfaces \
    "${debug_prefix}" space,num8 6 10000 180 1

require_log "${debug_log}" "gameplay-control wait satisfied" "debug control-ready gate"
require_log "${debug_log}" "_DAT_00643650=0" "debug requester state clear"
require_log "${debug_log}" "move=\\[1,0,0,0,0,0,0,0,0\\]" "debug delayed movement latch"
require_log "${debug_log}" "surface 3 nonblank=1" "debug nonblank gameplay surface"
if [[ "${runtime_diag}" == "0" || -z "${runtime_diag}" ]]; then
    reject_log "${debug_log}" "${runtime_diag_pattern}" "debug opt-in runtime diagnostics"
fi

run_capture "${asan_log}" \
    build/linux-clang32-asan/e2recomp \
    --inject-key-sequence-gameplay-surfaces \
    "${asan_prefix}" space,num8 30 10000 60 1

require_log "${asan_log}" "start_game=1 .*DAT_0047a76c=1 .*_DAT_0073cc3c=0x[1-9a-fA-F][0-9a-fA-F]+" "ASan scene/control state"
require_log "${asan_log}" "_DAT_00643650=0" "ASan requester state clear"
require_log "${asan_log}" "move=\\[1,0,0,0,0,0,0,0,0\\]" "ASan delayed movement latch"
require_log "${asan_log}" "surface 3 nonblank=1" "ASan nonblank gameplay surface"
reject_log "${asan_log}" "ERROR: AddressSanitizer|SUMMARY: AddressSanitizer" "ASan report"
if [[ "${runtime_diag}" == "0" || -z "${runtime_diag}" ]]; then
    reject_log "${asan_log}" "${runtime_diag_pattern}" "ASan opt-in runtime diagnostics"
fi

echo "Runtime regressions passed."
echo "Debug log: ${debug_log}"
echo "ASan log: ${asan_log}"
