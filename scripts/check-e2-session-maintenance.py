#!/usr/bin/env python3
"""Exercise the real retention worker with allocation and reporter failures."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--cxx', default='clang++-21')
parser.add_argument('--asan', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='e2-maintenance-') as directory:
    scratch = Path(directory)
    # Reuse the runtime's multilib fallback on installations without g++-multilib.
    (scratch/'CMakeLists.txt').write_text(f'''cmake_minimum_required(VERSION 3.25)
project(MaintenanceContract LANGUAGES C)
include("{root}/cmake/E2RClangMultilib.cmake")
enable_language(CXX)
set(CMAKE_CXX_STANDARD 20)
add_executable(contract
    "{root}/src/artifacts/tests/maintenance.cpp"
    "{root}/src/log/src/Session/SessionRetention.cpp"
    "{root}/src/log/src/Paths/Paths.cpp"
    "{root}/src/log/src/LogSupport/IO/FileSystemIO.cpp")
target_include_directories(contract PRIVATE "{root}/src/log/include" "{root}/src/artifacts/include")
target_compile_options(contract PRIVATE -O1 -g -pthread {'-fsanitize=address -fno-omit-frame-pointer' if args.asan else ''})
target_link_options(contract PRIVATE -pthread {'-fsanitize=address' if args.asan else ''})
''')
    subprocess.run(['cmake', '-S', str(scratch), '-B', str(scratch/'build'), '-G', 'Ninja',
        '-DCMAKE_C_COMPILER='+args.cc, '-DCMAKE_CXX_COMPILER='+args.cxx,
        '-DCMAKE_C_FLAGS=-m32', '-DCMAKE_CXX_FLAGS=-m32'], check=True, timeout=60)
    subprocess.run(['cmake', '--build', str(scratch/'build')], check=True, timeout=60)
    binary = scratch/'build/contract'
    subprocess.run([str(binary), str(scratch/'sessions-with-a-long-name')], check=True,
        timeout=15, env=os.environ | {'ASAN_OPTIONS':'detect_leaks=0'})
