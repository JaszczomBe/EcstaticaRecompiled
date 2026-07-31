add_library(e2r_runtime STATIC
    src/RuntimeArgs.c
)

target_include_directories(e2r_runtime PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(e2r_runtime PRIVATE -Wall -Wextra)
endif()
