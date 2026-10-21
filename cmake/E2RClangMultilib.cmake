# Clang on Debian can have the i386 C toolchain and the C++ runtime installed
# without the g++ multilib development links. Prefer the normal toolchain;
# discover the installed runtime/header fallback only when those links are absent.
if(CMAKE_SIZEOF_VOID_P EQUAL 4 AND CMAKE_C_COMPILER_ID STREQUAL "Clang")
    separate_arguments(e2r_cxx_flags NATIVE_COMMAND "${CMAKE_CXX_FLAGS}")
    execute_process(COMMAND "${CMAKE_CXX_COMPILER}" ${e2r_cxx_flags}
        -print-file-name=libstdc++.so OUTPUT_VARIABLE e2r_cxx_library
        OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
    if(NOT EXISTS "${e2r_cxx_library}")
        find_library(E2R_LIBSTDCXX_RUNTIME NAMES libstdc++.so.6
            PATHS "/usr/lib/${CMAKE_LIBRARY_ARCHITECTURE}"
                  "/lib/${CMAKE_LIBRARY_ARCHITECTURE}" NO_DEFAULT_PATH)
        if(NOT E2R_LIBSTDCXX_RUNTIME)
            message(FATAL_ERROR "Install g++-multilib for the i386 C++ logger, or configure with E2R_ENABLE_LOGGER=OFF.")
        endif()
        string(APPEND CMAKE_CXX_FLAGS " -nostdlib++")
        set(CMAKE_CXX_STANDARD_LIBRARIES "${E2R_LIBSTDCXX_RUNTIME}")
        list(APPEND CMAKE_TRY_COMPILE_PLATFORM_VARIABLES CMAKE_CXX_STANDARD_LIBRARIES)
        message(STATUS "E2R i386 C++ runtime fallback: ${E2R_LIBSTDCXX_RUNTIME}")
    endif()

    file(WRITE "${CMAKE_BINARY_DIR}/CMakeFiles/e2r-cxx-headers.cpp" "#include <bits/c++config.h>\n")
    execute_process(COMMAND "${CMAKE_CXX_COMPILER}" ${e2r_cxx_flags}
        -fsyntax-only "${CMAKE_BINARY_DIR}/CMakeFiles/e2r-cxx-headers.cpp"
        RESULT_VARIABLE e2r_cxx_headers_status OUTPUT_QUIET ERROR_QUIET)
    if(NOT e2r_cxx_headers_status EQUAL 0)
        # The compiler's native library path identifies its selected GCC version
        # and host triple; use that version's architecture configuration headers.
        execute_process(COMMAND "${CMAKE_CXX_COMPILER}" -print-file-name=libstdc++.so
            OUTPUT_VARIABLE e2r_native_cxx_library
            OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
        get_filename_component(e2r_gcc_dir "${e2r_native_cxx_library}" DIRECTORY)
        get_filename_component(e2r_gcc_version "${e2r_gcc_dir}" NAME)
        get_filename_component(e2r_gcc_triple_dir "${e2r_gcc_dir}" DIRECTORY)
        get_filename_component(e2r_gcc_triple "${e2r_gcc_triple_dir}" NAME)
        find_path(E2R_LIBSTDCXX_ARCH_INCLUDE bits/c++config.h
            PATHS "/usr/include/${e2r_gcc_triple}/c++/${e2r_gcc_version}"
            NO_DEFAULT_PATH)
        if(NOT E2R_LIBSTDCXX_ARCH_INCLUDE)
            message(FATAL_ERROR "Install g++-multilib for the i386 C++ headers, or configure with E2R_ENABLE_LOGGER=OFF.")
        endif()
        string(APPEND CMAKE_CXX_FLAGS " -isystem \"${E2R_LIBSTDCXX_ARCH_INCLUDE}\"")
        message(STATUS "E2R i386 C++ header fallback: ${E2R_LIBSTDCXX_ARCH_INCLUDE}")
    endif()
endif()
