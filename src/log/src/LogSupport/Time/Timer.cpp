#include <iomanip>
#include <sstream>
#include "LogSupport/Time/Timer.h"

using namespace std;

namespace Ecstatica::Recompiled::LogSupport::Time
{

	Timer::Timer()
	{
		resultMili = 0;
		resultNano = 0;

		// isMeasuring = false;

#ifdef _WIN32
		QueryPerformanceFrequency(&frequency);
		tStart.QuadPart = 0;
		tEnd.QuadPart = 0;
#else
		clock_gettime(CLOCK_MONOTONIC, &tStart);
		tEnd = tStart;
#endif
	}

	void Timer::Start()
	{
#ifdef _WIN32
		QueryPerformanceCounter(&tStart);
#else
		clock_gettime(CLOCK_MONOTONIC, &tStart);
#endif
		// isMeasuring = true;
	}

	double Timer::Stop()
	{
#ifdef _WIN32
		QueryPerformanceCounter(&tEnd);
#else
		clock_gettime(CLOCK_MONOTONIC, &tEnd);
#endif

        // if(!isMeasuring)
		// 	return 0;

		// isMeasuring = false;

		const auto result = Mili_Internal();
		Nano_Internal();

		return result;
	}

	std::string Timer::ToString() const
	{
		std::ostringstream ostream;
        ostream << std::right << std::fixed << std::setprecision(3) << Mili() << " ms";

		return ostream.str();
	}

	double Timer::Mili() const
	{
		return resultMili;
	}

	double Timer::Nano() const
	{
		return resultNano;
	}

	double Timer::Mili_Internal()
	{
#ifdef _WIN32
		resultMili = (double)(tEnd.QuadPart - tStart.QuadPart) * 1000.0 / frequency.QuadPart;
#else
		resultMili = (double)(tEnd.tv_sec - tStart.tv_sec) * 1e3 + (double)(tEnd.tv_nsec - tStart.tv_nsec) * 1e-6;
#endif
		return resultMili;
	}

	double Timer::Nano_Internal()
	{
#ifdef _WIN32
		resultNano = (double)(tEnd.QuadPart - tStart.QuadPart) * 1e9 / frequency.QuadPart;
#else
		resultNano = (double)(tEnd.tv_sec - tStart.tv_sec) * 1e9 + (double)(tEnd.tv_nsec - tStart.tv_nsec);
#endif
		return resultNano;
	}

}
