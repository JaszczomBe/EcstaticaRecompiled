#pragma once

namespace Ecstatica::Recompiled::LogSupport::Thread
{
    class RealtimeContext
    {
    public:
        static void SetRealtimeThread(bool isRealtime)
        {
            isRealtimeThread = isRealtime;
        }

        class Scope
        {
        public:
            Scope()
                : previous(RealtimeContext::isRealtimeThread)
            {
                RealtimeContext::SetRealtimeThread(true);
            }

            ~Scope()
            {
                RealtimeContext::SetRealtimeThread(previous);
            }

        private:
            bool previous = false;
        };

        static bool IsRealtimeThread()
        {
            return isRealtimeThread;
        }

    private:
        inline static thread_local bool isRealtimeThread = false;
    };
}
