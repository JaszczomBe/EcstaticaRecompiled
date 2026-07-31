#include "LogSupport/Thread/Waiter.h"

#include "Core/RTTestHooksInternal.h"

namespace Ecstatica::Recompiled::LogSupport::Thread
{

    Waiter::Waiter()
        : flag(true)
    {

    }

    void Waiter::Await()
    {
        flag = true;

        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [this](){ return !flag; });
    }

    bool Waiter::AwaitFor(std::chrono::milliseconds timeout)
    {
        flag = true;

        std::unique_lock<std::mutex> lock(mtx);
        return cv.wait_for(lock, timeout, [this](){ return !flag; });
    }

    void Waiter::StopWait()
    {
#if defined(UNDERTONE_LOG_ENABLE_RT_TEST_HOOKS)
        Ecstatica::Recompiled::Log::Test::AccessRTTestHooksState().waiterStopWaitCalls.fetch_add(
            1, std::memory_order_relaxed);
#endif
        {
            std::lock_guard<std::mutex> lock(mtx);
            flag = false;
        }
        cv.notify_all();
    }

}
