add_library(e2r_log STATIC
    dep/mpsc_queue/mpsc.c
    src/CBridge.cpp
    src/LogBootstrap.cpp
    src/Core/Format.cpp
    src/Core/Logger.cpp
    src/Core/LoggerInternal.cpp
    src/Core/LogWrite.cpp
    src/Debug/StackTrace_posix.cpp
    src/LogSupport/IO/FileSystemIO.cpp
    src/LogSupport/Thread/BackgroundRunner.cpp
    src/LogSupport/Thread/Id.cpp
    src/LogSupport/Thread/Name.cpp
    src/LogSupport/Thread/Waiter.cpp
    src/LogSupport/Time/Timer.cpp
    src/Modules/ModuleId.cpp
    src/Paths/Paths.cpp
    src/Sinks/FileSink.cpp
    src/Sinks/StderrSink.cpp
    src/Sinks/StdoutSink.cpp
)

target_include_directories(e2r_log PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${CMAKE_CURRENT_SOURCE_DIR}/dep/mpsc_queue"
)
target_include_directories(e2r_log PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/src"
)

target_compile_features(e2r_log PUBLIC cxx_std_20)
target_compile_definitions(e2r_log PUBLIC UT_LOG_USE_STD_FORMAT=1)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(e2r_log PRIVATE -Wall -Wextra)
endif()
