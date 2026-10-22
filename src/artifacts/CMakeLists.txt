add_library(e2r_artifacts STATIC
    src/RunArtifacts.cpp
    ../log/src/Session/SessionRetention.cpp
    ../log/src/Paths/Paths.cpp
    ../log/src/LogSupport/IO/FileSystemIO.cpp)
target_include_directories(e2r_artifacts PUBLIC include ../log/include)
target_compile_features(e2r_artifacts PUBLIC cxx_std_20)
find_package(Threads REQUIRED)
target_link_libraries(e2r_artifacts PUBLIC Threads::Threads)
target_compile_options(e2r_artifacts PRIVATE -Wall -Wextra)
