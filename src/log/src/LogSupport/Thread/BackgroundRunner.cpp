#include "LogSupport/Thread/BackgroundRunner.h"
#include "LogSupport/Thread/Name.h"
#include <utility>

namespace Ecstatica::Recompiled::LogSupport::Thread
{
    BackgroundRunner::BackgroundRunner(std::string name) : name(std::move(name)) {}
    BackgroundRunner::~BackgroundRunner() { Stop(); }

    void BackgroundRunner::Start(TaskFunction task)
    {
        Stop();
        stopFlag.store(false, std::memory_order_release);
        workerThread = std::thread([this, task = std::move(task)] {
            Name::SetThreadName(name);
            while (!stopFlag.load(std::memory_order_acquire) && task()) {}
            stopFlag.store(true, std::memory_order_release);
        });
    }

    void BackgroundRunner::Stop()
    {
        stopFlag.store(true, std::memory_order_release);
        if (workerThread.joinable())
            workerThread.join();
    }
}
