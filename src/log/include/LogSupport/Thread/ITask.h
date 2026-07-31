#pragma once

namespace Ecstatica::Recompiled::LogSupport::Thread
{

    class ITask
	{
	public:
		virtual			~ITask() = default;
		virtual bool	Execute() = 0;
    };

}
