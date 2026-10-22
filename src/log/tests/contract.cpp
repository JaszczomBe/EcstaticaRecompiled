#ifdef NDEBUG
#undef NDEBUG // Contract checks must execute in every build configuration.
#endif
#define UT_LOG_MIN_LEVEL Ecstatica::Recompiled::Log::Level::Off
#include "Log/Log.h"
#include "Log/Session/SessionRetention.h"
#include "Log/Sinks/FileSink.h"
#include "Log/Test/RTTestHooks.h"
#include "LogSupport/Thread/RealtimeContext.h"

#include <algorithm>
#include <atomic>
#include <cassert>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <new>

using namespace Ecstatica::Recompiled;
using namespace Ecstatica::Recompiled::Log;
namespace fs = std::filesystem;
static thread_local bool countAllocations;
static unsigned allocations;

void* operator new(std::size_t size)
{
    if (countAllocations) ++allocations;
    if (void* memory = std::malloc(size ? size : 1)) return memory;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

struct Capture : Sink
{
    std::mutex mutex;
    std::condition_variable wake;
    bool blocked = false, released = false, symbolize = false;
    FormatOptions format;
    std::vector<std::string> lines;
    std::vector<Record> stamps;
    void Write(const Record& record) override
    {
        std::unique_lock lock(mutex);
        if (record.message == "hold")
        {
            blocked = true;
            wake.notify_all();
            wake.wait(lock, [this] { return released; });
        }
        std::string text;
        if (symbolize) FormatLine(record, text, format);
        else text = record.message;
        lines.push_back(std::move(text));
        Record stamp{};
        stamp.seq = record.seq;
        stamp.timePointWall = record.timePointWall;
        stamp.timePointSteady = record.timePointSteady;
        stamps.push_back(stamp);
    }
    void Flush() override {}
    void SetFormatOptions(const FormatOptions& options) override { format = options; }
    FormatOptions GetFormatOptions() const override { return format; }
    void WaitBlocked()
    {
        std::unique_lock lock(mutex);
        assert(wake.wait_for(lock, std::chrono::seconds(5), [this] { return blocked; }));
    }
    void Release()
    {
        std::lock_guard lock(mutex);
        released = true;
        wake.notify_all();
    }
};

static Config QuietConfig()
{
    Config config;
    config.globalLevel = Level::Trace;
    config.callstackOnError = config.callstackOnFatal = false;
    return config;
}

extern "C" __attribute__((noinline)) void logger_origin_for_stack()
{
    UT_LOG(Level::Error, ModuleID::Runtime, "native source stack");
}

static void CoreContracts()
{
    auto& logger = Logger::Instance();
    for (int level = 0; level <= static_cast<int>(Level::Off); ++level)
    {
        auto sink = std::make_shared<Capture>();
        auto config = QuietConfig();
        config.globalLevel = static_cast<Level>(level);
        config.rateLimit = [](const Record&) { return false; };
        logger.Start(config);
        logger.ClearAllModuleOverrides();
        logger.ReplaceSinks({sink});
        logger.SetLevelForModule(ModuleID::Runtime, Level::Off);
        UT_LOG(Level::Info, ModuleID::Runtime, "compile-time gated");
        UT_LOG_FMT(Level::Error, ModuleID::Runtime, "error {}", 42);
        UT_LOG(Level::Fatal, ModuleID::Runtime, "fatal");
        logger.Stop();
        assert((sink->lines == std::vector<std::string>{"error 42", "fatal"}));
    }
    // Existing policy: Error respects module/submodule masks, Fatal bypasses them.
    for (bool submodule : {false, true})
    {
        auto sink = std::make_shared<Capture>();
        auto config = QuietConfig();
        if (!submodule) config.moduleDenyMask = ToMask(ModuleID::Runtime);
        logger.Start(config);
        logger.ClearAllModuleOverrides();
        logger.ReplaceSinks({sink});
        if (submodule) logger.SetSubmoduleMask(ModuleID::Runtime, ~SubmoduleMask(0), 2);
        UT_LOG_MASK_FMT(Level::Error, ModuleID::Runtime, 2, "masked {}", 7);
        UT_LOG_MASK(Level::Fatal, ModuleID::Runtime, 2, "fatal survives mask");
        logger.Stop();
        assert((sink->lines == std::vector<std::string>{"fatal survives mask"}));
    }
    {
        auto sink = std::make_shared<Capture>();
        logger.Start(QuietConfig());
        logger.ClearAllModuleOverrides();
        logger.ReplaceSinks({sink});
        logger.Log(Level::Info, ModuleID::Runtime, {}, "hold");
        sink->WaitBlocked();
        logger.Log(Level::Info, ModuleID::Runtime, {}, "older normal");
        UT_LOG(Level::Error, ModuleID::Runtime, "priority");
        sink->Release();
        logger.Stop();
        assert((sink->lines == std::vector<std::string>{"hold", "priority", "older normal"}));
        assert(sink->stamps[1].seq > sink->stamps[2].seq);
        assert(sink->stamps[1].timePointSteady >= sink->stamps[2].timePointSteady);
    }
    {
        auto sink = std::make_shared<Capture>();
        sink->symbolize = true;
        logger.Start(QuietConfig());
        logger.ClearAllModuleOverrides();
        logger.ReplaceSinks({sink});
        logger.Log(Level::Info, ModuleID::Runtime, {}, "hold");
        sink->WaitBlocked();
        std::string key = "actor", value = "Joe";
        Record::Field fields[] = {{key, value}};
        UT_LOGF_FMT(Level::Error, ModuleID::Runtime, fields, 1, "field event {}", 7);
        key.assign("gone"); value.assign("gone");
        sink->Release();
        logger.Stop();
        assert(sink->lines[1].find("field event 7 actor=Joe") != std::string::npos);
    }
    {
        auto sink = std::make_shared<Capture>();
        sink->symbolize = true;
        sink->format.includeStack = sink->format.stackShowSource = true;
        auto config = QuietConfig();
        config.callstackOnError = true;
        logger.Start(config);
        logger.ClearAllModuleOverrides();
        logger.ReplaceSinks({sink});
        logger_origin_for_stack();
        logger.Stop();
        assert(sink->lines.size() == 1);
        assert(sink->lines[0].find("logger_origin_for_stack") != std::string::npos);
        assert(sink->lines[0].find("contract.cpp") != std::string::npos);
    }
    std::cout << "PASS: critical severity/macro bypass, module/submodule masks, priority and native source stacks\n";
}

static void RealtimeContracts()
{
    auto& logger = Logger::Instance();
    auto sink = std::make_shared<Capture>();
    sink->symbolize = true;
    logger.Start(QuietConfig());
    logger.ReplaceSinks({sink});
    logger.Log(Level::Info, ModuleID::Runtime, {}, "hold");
    sink->WaitBlocked();
    Test::ResetRTTestHooks();
    char argument[] = "owned";
    unsigned accepted = 0;
    {
        LogSupport::Thread::RealtimeContext::Scope realtime;
        countAllocations = true;
        assert(WriteRealtimeLogf(Level::Debug, ModuleID::Runtime, {}, 0, 0, "deferred {} {}", argument, 'X'));
        UT_RT_LOG_MASK_FMT(Level::Error, ModuleID::Runtime, 2, "RT critical {}", "survives Off");
        argument[0] = '!';
        for (unsigned i = 0; i < 300; ++i)
            accepted += logger.LogRealtime(Level::Debug, ModuleID::Runtime, {}, "pool");
        countAllocations = false;
    }
    assert(allocations == 0);
    assert(accepted == 254);
    const auto hooks = Test::GetRTTestHooksSnapshot();
    assert(hooks.waiterStopWaitCalls == 0 && hooks.realtimeDropped == 46);
    sink->Release();
    logger.Stop();
    assert(sink->lines.size() == 257);
    assert(sink->lines[1].find("RT critical survives Off") != std::string::npos);
    assert(std::any_of(sink->lines.begin(), sink->lines.end(), [](const auto& line) {
        return line.find("deferred owned X") != std::string::npos;
    }));
    // Stopping/restarting returns every pooled node to service.
    logger.Start(QuietConfig());
    logger.ReplaceSinks({std::make_shared<Capture>()});
    assert(logger.LogRealtime(Level::Debug, ModuleID::Runtime, {}, "reused"));
    logger.Stop();
    std::cout << "PASS: RT pool exhaustion/reuse, zero producer allocations/wakeups and deferred argument ownership\n";
}

static void StorageContracts(const fs::path& root)
{
    fs::create_directories(root);
    {
        FileSink sink((root / "rotation.log").string(), true, 32);
        Record record{};
        record.level = Level::Info;
        record.message = "rotation-preserves-all-records";
        for (int i = 0; i < 4; ++i) sink.Write(record);
    }
    unsigned records = 0;
    for (const auto& entry : fs::directory_iterator(root))
        if (entry.path().extension() == ".log")
        {
            std::ifstream input(entry.path());
            std::string line;
            while (std::getline(input, line)) records += line.find("rotation-preserves-all-records") != std::string::npos;
        }
    assert(records == 4);
    auto logs = root / "sessions";
    Session::RetentionPolicy policy;
    policy.maxSessions = 1;
    policy.maxTotalSizeBytes = 1024 * 1024;
    Session::Metadata metadata{"EcstaticaRecompiled", "e2recomp.log", 32};
    auto first = Session::PrepareStartupSession(logs.string(), "e2recomp.log", policy, metadata);
    auto second = Session::PrepareStartupSession(logs.string(), "e2recomp.log", policy, metadata);
    assert(first.lease && second.lease && first.sessionDirectory != second.sessionDirectory);
    assert(second.cleanup.overBudget && fs::exists(first.sessionDirectory));
    second.lease.reset();
    auto cleanup = Session::CleanupSessions(logs.string(), policy);
    assert(cleanup.removedSessions == 1 && !fs::exists(second.sessionDirectory));
    assert(fs::exists(first.sessionDirectory));
    // The byte limit wins even with fewer than ten completed sessions.
    first.lease.reset();
    fs::resize_file(fs::path(first.sessionDirectory) / "session.meta", 2 * 1024 * 1024);
    cleanup = Session::CleanupSessions(logs.string(), policy);
    assert(cleanup.removedSessions == 1 && !fs::exists(first.sessionDirectory));
    auto legacy = logs / "session_20000101_000000_000";
    fs::create_directory(legacy);
    auto symlink = logs / "session_20000101_000000_001";
    fs::create_directory_symlink(legacy, symlink);
    policy.maxTotalSizeBytes = 1;
    std::ofstream(legacy / "large").write("oversize", 8);
    Session::CleanupSessions(logs.string(), policy);
    assert(fs::is_symlink(symlink));
    std::cout << "PASS: append-only rotation, exclusive active leases, hard count/size cleanup and symlink exclusion\n";
}

int main(int argc, char** argv)
{
    assert(argc == 2);
    CoreContracts();
    RealtimeContracts();
    StorageContracts(argv[1]);
}
