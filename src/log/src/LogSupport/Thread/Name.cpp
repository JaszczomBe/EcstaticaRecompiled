#include "LogSupport/Thread/Id.h"

#include <string>
#include <unordered_map>
#include <mutex>
#include <stdexcept>

#if defined(__APPLE__) || defined(__linux__)
#include <pthread.h>
#endif

namespace Ecstatica::Recompiled::LogSupport::Thread::Name
{
    static thread_local std::string t_name;
    static std::unordered_map<uint64_t, std::string> g_names;
    static std::mutex g_mtx;

    /**
     * Sets the name of the current thread.
     * @param name The desired name for the thread (max 15 chars on Linux)
     * @return true if the operation was successful, false otherwise
     */
    bool SetThreadName(const std::string& name)
    {
        // Linux limits thread names to 16 chars (including null terminator)
        std::string threadName = name.substr(0, 15);
        t_name = threadName;
        // Record mapping for formatter lookups (by hashed id)
        {
            std::lock_guard<std::mutex> lk(g_mtx);
            g_names[Ecstatica::Recompiled::LogSupport::Thread::ThisThreadId()] = t_name;
        }

    #if defined(__APPLE__) || defined(__linux__)
        // Both macOS and Linux use pthread under the hood
        int result = pthread_setname_np(
        #ifdef __APPLE__
            threadName.c_str()
        #elif defined(__linux__)
            pthread_self(), threadName.c_str()
        #endif
        );
        return (result == 0);
    #else
        // Unsupported platform
        return false;
    #endif
    }

    void ClearCurrentThreadName()
    {
        t_name.clear();
        std::lock_guard<std::mutex> lk(g_mtx);
        g_names.erase(Ecstatica::Recompiled::LogSupport::Thread::ThisThreadId());
    }

    const std::string& GetThreadName()
    {
        if (!t_name.empty())
            return t_name;

    #if defined(__APPLE__) || defined(__linux__)
        char buf[64] = {0};
        #if defined(__APPLE__)
            if (pthread_getname_np(pthread_self(), buf, sizeof(buf)) == 0)
                t_name = buf;
        #else
            if (pthread_getname_np(pthread_self(), buf, sizeof(buf)) == 0)
                t_name = buf;
        #endif
    #endif
        if (!t_name.empty())
        {
            std::lock_guard<std::mutex> lk(g_mtx);
            g_names[Ecstatica::Recompiled::LogSupport::Thread::ThisThreadId()] = t_name;
        }
        return t_name;
    }

    std::string GetThreadNameById(uint64_t thread_id)
    {
        std::lock_guard<std::mutex> lk(g_mtx);
        auto it = g_names.find(thread_id);
        if (it != g_names.end()) return it->second;
        return std::string();
    }
} // namespace Ecstatica::Recompiled::LogSupport::Thread::Name
