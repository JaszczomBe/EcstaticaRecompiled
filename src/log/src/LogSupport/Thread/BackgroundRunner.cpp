#include <iostream>
#include <LogSupport/Thread/BackgroundRunner.h>
#include <LogSupport/Thread/Name.h>

using namespace std;

namespace Ecstatica::Recompiled::LogSupport::Thread
{
    BackgroundRunner::BackgroundRunner(const std::string& name)
		:	stopFlag(false),
            runCount(-1),
            taskFunction(nullptr),
            name(name)
	{
	}

    BackgroundRunner::~BackgroundRunner()
	{
        Stop();
    }

	void BackgroundRunner::Start(std::unique_ptr<ITask> task, int count)
	{
		Stop();

		taskObject = std::move(task);
		runCount = count;
		
        stopFlag.store(false, std::memory_order_release);
        workerThread = std::thread(&BackgroundRunner::Run, this);
    }

    void BackgroundRunner::Start(TaskFunction task, int count)
	{
		Stop();

		taskObject.reset();
		taskFunction = task;
		runCount = count;
		
        stopFlag.store(false, std::memory_order_release);
        workerThread = std::thread(&BackgroundRunner::Run, this);
    }

    void BackgroundRunner::Stop()
	{
		stopFlag.store(true, std::memory_order_release);
        if (workerThread.joinable())
        {
            try
            {
                workerThread.join();
            }
            catch (const std::system_error& err)
            {
                std::cerr << "[BackgroundRunner] Failed to join thread '" << name << "': " << err.what() << std::endl;
            }
        }

		taskObject.reset();
		taskFunction = nullptr;
    }

	bool BackgroundRunner::IsRunning() const
	{
		return !stopFlag.load(std::memory_order_acquire);
	}

	void BackgroundRunner::Run()
	{
        Ecstatica::Recompiled::LogSupport::Thread::Name::SetThreadName(name);

		int count = 0;
        while (!stopFlag.load(std::memory_order_acquire)/*  && (runCount < 0 || count < runCount) */)
        {
			if(runCount > 0)
			if(count++ >= runCount)
				break;

            if(taskFunction)
			{
				if(!taskFunction())	// Exit if task function returns false
					break;
			}
			else if(taskObject)
			{
				if(!taskObject->Execute())
					break;
			}
			else
			{
				break;
			}
        }

		stopFlag.store(true, std::memory_order_release);
	}
}
