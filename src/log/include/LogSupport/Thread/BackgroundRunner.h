#pragma once
#include <atomic>
#include <functional>
#include <string>
#include <thread>

namespace Ecstatica::Recompiled::LogSupport::Thread
{
    using TaskFunction = std::function<bool()>;

    // Named consumer worker; the task returns false when its work is finished.
    class BackgroundRunner
    {
    public:
        explicit BackgroundRunner(std::string name = "BackgroundRunner");
        ~BackgroundRunner();
        void Start(TaskFunction task);
        void Stop();
    private:
        std::atomic<bool> stopFlag{true};
        std::thread workerThread;
        const std::string name;
    };
}
