cmake_minimum_required(VERSION 3.20)

set(E2R_ENABLE_LOGGER ON CACHE BOOL
    "Enable the adapted C++ Ecstatica logger. Disable for layout-sensitive sanitizer probes.")
set(E2R_ENABLE_RUNTIME_OPTIONS ON CACHE BOOL
    "Enable Ecstatica runtime command-line options and writable data directory wiring.")

if(E2R_ENABLE_LOGGER)
    project(EcstaticaRecompiled LANGUAGES C CXX)
else()
    project(EcstaticaRecompiled LANGUAGES C)
endif()

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)
if(E2R_ENABLE_LOGGER)
    set(CMAKE_CXX_STANDARD 20)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    set(CMAKE_CXX_EXTENSIONS OFF)
endif()

set(ECSTATICA2_DATA_DIR "/home/rgrabowski/Games/Ecstatica2" CACHE PATH
    "Path to the full Ecstatica II CD data directory")
set(ECSTATICA2_DATA_LINK "${CMAKE_BINARY_DIR}/Ecstatica2" CACHE PATH
    "Symlink created at configure time for local Ecstatica II data")
set(ECSTATICA2_ORIGINAL_EXE "${ECSTATICA2_DATA_DIR}/E2WIN95.EXE" CACHE FILEPATH
    "Original Ecstatica II Win95 executable used for Ghidra analysis")
set(GHIDRA_HOME "" CACHE PATH
    "Optional Ghidra release directory containing support/analyzeHeadless")
set(GHIDRA_ANALYZE_HEADLESS "" CACHE FILEPATH
    "Optional direct path to Ghidra analyzeHeadless")
set(GHIDRA_PROJECT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/ghidra_project" CACHE PATH
    "Ghidra project directory for headless analysis")
set(GHIDRA_PROJECT_NAME "E2Win95Project" CACHE STRING
    "Ghidra project name for the original Ecstatica II executable")
set(GHIDRA_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/E2Recomp" CACHE PATH
    "Directory receiving exported decompilation artifacts")
set(E2R_HOST_BACKEND "x11" CACHE STRING
    "Host backend implementation: x11 or sdl")
set_property(CACHE E2R_HOST_BACKEND PROPERTY STRINGS x11 sdl)

if(EXISTS "${ECSTATICA2_DATA_DIR}")
    file(CREATE_LINK "${ECSTATICA2_DATA_DIR}" "${ECSTATICA2_DATA_LINK}"
         SYMBOLIC RESULT ECSTATICA2_LINK_RESULT)
    if(NOT ECSTATICA2_LINK_RESULT STREQUAL "0")
        message(FATAL_ERROR
            "Could not create Ecstatica II data symlink:\n"
            "  ${ECSTATICA2_DATA_LINK} -> ${ECSTATICA2_DATA_DIR}\n"
            "Result: ${ECSTATICA2_LINK_RESULT}")
    endif()
else()
    message(FATAL_ERROR
        "ECSTATICA2_DATA_DIR does not exist: ${ECSTATICA2_DATA_DIR}\n"
        "Set it with -DECSTATICA2_DATA_DIR=/path/to/Ecstatica2")
endif()

find_program(NODE_EXECUTABLE node)

if(E2R_HOST_BACKEND STREQUAL "x11")
    set(E2R_HOST_BACKEND_SOURCE E2Recomp/platform/e2recomp_host_backend.c)
elseif(E2R_HOST_BACKEND STREQUAL "sdl")
    set(E2R_SDL_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/dep/SDL")
    if(NOT EXISTS "${E2R_SDL_SOURCE_DIR}/CMakeLists.txt")
        message(FATAL_ERROR
            "E2R_HOST_BACKEND=sdl requires the SDL submodule at dep/SDL.\n"
            "Initialize it with: git submodule update --init --recursive dep/SDL")
    endif()
    set(SDL_SHARED OFF CACHE BOOL "Build SDL shared library" FORCE)
    set(SDL_STATIC ON CACHE BOOL "Build SDL static library" FORCE)
    set(SDL_TEST_LIBRARY OFF CACHE BOOL "Build SDL test library" FORCE)
    set(SDL_TESTS OFF CACHE BOOL "Build SDL tests" FORCE)
    set(SDL_INSTALL OFF CACHE BOOL "Install SDL" FORCE)
    set(SDL_CCACHE OFF CACHE BOOL "Use ccache when building SDL" FORCE)
    add_subdirectory("${E2R_SDL_SOURCE_DIR}" dep/SDL-build EXCLUDE_FROM_ALL)
    set(E2R_HOST_BACKEND_SOURCE E2Recomp/platform/e2recomp_host_backend_sdl.c)
else()
    message(FATAL_ERROR
        "Unsupported E2R_HOST_BACKEND='${E2R_HOST_BACKEND}'. "
        "Use -DE2R_HOST_BACKEND=x11 or -DE2R_HOST_BACKEND=sdl.")
endif()

message(STATUS "E2R host backend: ${E2R_HOST_BACKEND}")
message(STATUS "E2R runtime options: ${E2R_ENABLE_RUNTIME_OPTIONS}")
message(STATUS "E2R logger: ${E2R_ENABLE_LOGGER}")

if(E2R_ENABLE_LOGGER AND NOT E2R_ENABLE_RUNTIME_OPTIONS)
    message(FATAL_ERROR "E2R_ENABLE_LOGGER requires E2R_ENABLE_RUNTIME_OPTIONS")
endif()

if(E2R_ENABLE_RUNTIME_OPTIONS)
    add_subdirectory(src/runtime)
    if(E2R_ENABLE_LOGGER)
        add_subdirectory(src/log)
    else()
        add_library(e2r_log_stub STATIC src/log/src/LogStub.c)
        target_include_directories(e2r_log_stub PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/log/include")
    endif()
endif()

add_custom_target(ghidra-export
    COMMAND "${CMAKE_COMMAND}" -E env
        "ECSTATICA2_DATA_DIR=${ECSTATICA2_DATA_DIR}"
        "GHIDRA_INPUT_EXE=${ECSTATICA2_ORIGINAL_EXE}"
        "GHIDRA_HOME=${GHIDRA_HOME}"
        "GHIDRA_ANALYZE_HEADLESS=${GHIDRA_ANALYZE_HEADLESS}"
        "GHIDRA_PROJECT_DIR=${GHIDRA_PROJECT_DIR}"
        "GHIDRA_PROJECT_NAME=${GHIDRA_PROJECT_NAME}"
        "GHIDRA_OUTPUT_DIR=${GHIDRA_OUTPUT_DIR}"
        "${CMAKE_CURRENT_SOURCE_DIR}/scripts/run-ghidra-export.sh"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    COMMENT "Exporting Ecstatica II decompilation artifacts with Ghidra"
    VERBATIM
)

if(NODE_EXECUTABLE)
    add_custom_target(ghidra-generate-recon
        COMMAND "${NODE_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/E2Recomp/tools/GenerateRecon.js"
                "${CMAKE_CURRENT_SOURCE_DIR}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        COMMENT "Regenerating reconstructed C artifacts from Ghidra export"
        VERBATIM
    )
else()
    add_custom_target(ghidra-generate-recon
        COMMAND "${CMAKE_COMMAND}" -E false
        COMMENT "Node.js is required to regenerate reconstructed C artifacts"
        VERBATIM
    )
endif()

add_executable(e2recomp
    E2Recomp/reconstructed/E2Recomp_recon.c
    E2Recomp/reconstructed/E2Recomp_globals.c
    E2Recomp/reconstructed/E2Recomp_data_init.c
    E2Recomp/reconstructed/E2Recomp_stubs.c
    ${E2R_HOST_BACKEND_SOURCE}
    E2Recomp/platform/e2recomp_win32_compat.c
    E2Recomp/native/e2recomp_native_main.c
)

target_include_directories(e2recomp PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/E2Recomp/reconstructed"
    "${CMAKE_CURRENT_SOURCE_DIR}/E2Recomp/src"
    "${CMAKE_CURRENT_SOURCE_DIR}/E2Recomp/platform"
)

if(E2R_ENABLE_LOGGER)
    set_target_properties(e2recomp PROPERTIES LINKER_LANGUAGE CXX)
endif()

target_compile_definitions(e2recomp PRIVATE
    E2RECOMP_DATA_DIR="${ECSTATICA2_DATA_LINK}"
)

if(E2R_ENABLE_RUNTIME_OPTIONS)
    target_compile_definitions(e2recomp PRIVATE E2R_ENABLE_RUNTIME_OPTIONS=1)
endif()

if(UNIX AND NOT APPLE)
    target_link_libraries(e2recomp PRIVATE dl m pthread)
endif()

if(E2R_ENABLE_RUNTIME_OPTIONS)
    if(E2R_ENABLE_LOGGER)
        target_link_libraries(e2recomp PRIVATE e2r_log)
    else()
        target_link_libraries(e2recomp PRIVATE e2r_log_stub)
    endif()
    target_link_libraries(e2recomp PRIVATE e2r_runtime)
endif()

if(E2R_HOST_BACKEND STREQUAL "sdl")
    target_link_libraries(e2recomp PRIVATE SDL3::SDL3)
    target_compile_definitions(e2recomp PRIVATE E2R_HOST_BACKEND_SDL=1)
endif()

if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(e2recomp PRIVATE
        -w
        -Wno-int-conversion
        -Wno-implicit-function-declaration
        -Wno-return-mismatch
        -fms-extensions
        -fno-builtin
    )
endif()
