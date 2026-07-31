#pragma once

#include <memory>
#include <string>

namespace Ecstatica::Recompiled::Log
{
    std::shared_ptr<std::string> CaptureCallstack(bool symbolize = true, int max_frames = 64);
}
