#pragma once

#include <string>

#ifdef _WIN32
	#include <Windows.h>
#else
	#include <time.h>
#endif

// TODO hide platform specifics

namespace Ecstatica::Recompiled::LogSupport::Time
{


	class Timer
	{
	public:
		Timer();

        void        Start();
        double      Stop();

        double      Mili() const;
        double      Nano() const;

		std::string ToString() const;

	private:
		double 		Mili_Internal();
		double 		Nano_Internal();

	private:
#ifdef _WIN32
		LARGE_INTEGER tStart;
		LARGE_INTEGER tEnd;
		LARGE_INTEGER frequency;
#else
		timespec tStart;
		timespec tEnd;
#endif
		// bool isMeasuring;

		double resultMili;
		double resultNano;
	};


}
