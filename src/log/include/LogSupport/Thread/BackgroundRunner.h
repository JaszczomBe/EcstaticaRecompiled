#pragma once
#include <thread>
#include <atomic>
#include <memory>
#include <functional>
#include "ITask.h"

namespace Ecstatica::Recompiled::LogSupport::Thread
{
	// Task callback will be continously executed by BackgroundRunner until it returns false or runCount reaches 0
	using TaskFunction = std::function<bool()>;

    class BackgroundRunner
	{
		public:
			BackgroundRunner(const std::string& name = "BackgroundRunner");
            virtual ~BackgroundRunner();

			void Start(std::unique_ptr<ITask> task, int count = -1);
			void Start(TaskFunction task, int count = -1);
            void Stop();
			bool IsRunning() const;

        private:
            void Run();

        private:
            std::atomic<bool> 		stopFlag;
			int						runCount;			
            std::thread				workerThread;

			TaskFunction			taskFunction;
			std::unique_ptr<ITask>	taskObject;
            const std::string       name;
    };
}
