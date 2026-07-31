#include "LogSupport/Thread/Id.h"

#include <functional>
#include <thread>

namespace Ecstatica::Recompiled::LogSupport::Thread
{
    uint64_t ThisThreadId()
    {
        return static_cast<uint64_t>(std::hash<std::thread::id>{}(std::this_thread::get_id()));
    }
}
