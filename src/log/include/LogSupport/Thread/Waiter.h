#pragma once

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <mutex>

namespace Ecstatica::Recompiled::LogSupport::Thread
{

    class Waiter
    {
    public:
        Waiter();

        void Await();
        bool AwaitFor(std::chrono::milliseconds timeout);
        void StopWait();

    private:
        std::atomic<bool> flag;
        std::mutex mtx;
        std::condition_variable cv;
    };

}
