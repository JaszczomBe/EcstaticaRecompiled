# Keep personal data paths outside shared presets and disposable build caches.
# An explicit/nonempty cache value wins; empty caches may be initialized again.
set(ECSTATICA2_DATA_DIR "" CACHE PATH
    "Path to the full Ecstatica II CD data directory")
set(e2r_default_data_config "")
if(NOT "$ENV{HOME}" STREQUAL "")
    set(e2r_default_data_config "$ENV{HOME}/.ecstatica2/game-data-dir")
endif()
set(ECSTATICA2_DATA_CONFIG "${e2r_default_data_config}" CACHE FILEPATH
    "Optional local text file containing the original game-data directory")

if("${ECSTATICA2_DATA_DIR}" STREQUAL "")
    set(e2r_configured_data_dir "$ENV{ECSTATICA2_DATA_DIR}")
    if("${e2r_configured_data_dir}" STREQUAL "" AND EXISTS "${ECSTATICA2_DATA_CONFIG}")
        file(READ "${ECSTATICA2_DATA_CONFIG}" e2r_configured_data_dir)
        string(STRIP "${e2r_configured_data_dir}" e2r_configured_data_dir)
        message(STATUS "E2R game-data setting: ${ECSTATICA2_DATA_CONFIG}")
    endif()
    if(NOT "${e2r_configured_data_dir}" STREQUAL "")
        set(ECSTATICA2_DATA_DIR "${e2r_configured_data_dir}" CACHE PATH
            "Path to the full Ecstatica II CD data directory" FORCE)
    endif()
endif()
