#ifdef NDEBUG
#undef NDEBUG // Execute the contract assertions in every build configuration.
#endif
#include "Log/Session/SessionRetention.h"

#include <atomic>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <new>
#include <thread>

namespace fs = std::filesystem;
using namespace Ecstatica::Recompiled::Log::Session;

static std::atomic<bool> failAllocations{false};
static std::atomic<unsigned> failures{0}, reports{0};
static const auto mainThread = std::this_thread::get_id();

void* operator new(std::size_t size)
{
    if (failAllocations && std::this_thread::get_id() != mainThread)
    {
        ++failures;
        throw std::bad_alloc();
    }
    if (void* memory = std::malloc(size ? size : 1)) return memory;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

extern "C" void E2R_ArtifactsReport(const char*)
{
    ++reports;
    // The logger callback can also allocate. Its failure must not escape.
    throw std::bad_alloc();
}

int main(int argc, char** argv)
{
    assert(argc == 2);
    const fs::path root = argv[1];
    fs::create_directories(root);
    RetentionPolicy policy;
    policy.cleanupInterval = std::chrono::seconds(1);
    policy.maxSessions = 5;
    for (unsigned i = 0; i < 5; ++i)
        fs::create_directory(root / ("session_20990101_000000_00" + std::to_string(i)));
    Maintenance worker(root.string(), policy, {});
    failAllocations = true;
    for (unsigned i = 0; i < 100 && failures < 2; ++i)
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    failAllocations = false;
    assert(failures >= 2); // At least two cleanup cycles survived allocation failure.
    const auto older = root / "session_20000101_000000_000";
    fs::create_directory(older);
    for (unsigned i = 0; i < 100 && fs::exists(older); ++i)
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    assert(!fs::exists(older)); // Cleanup recovered when allocation became available.
    worker.Stop();
    assert(reports >= 3); // Error reports and recovered cleanup's throwing callback.
    std::puts("PASS: repeated cleanup allocation failure, throwing reporter, recovery and clean worker shutdown");
}
